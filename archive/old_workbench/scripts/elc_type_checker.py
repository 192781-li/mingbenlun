#!/usr/bin/env python3
"""
践演λ-演算（Enactive λ-Calculus, EλC）类型检查器原型
基于践演论 v0.8 的类型规则

核心特性：
- 线性类型（Op不可复制）
- !-模态（Tr可复制）
- 运行权标注 Ag_A(t)
- 异化检测 alien(e,B)
- 明性标注 clarity
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

# ============================================================
# 类型定义
# ============================================================

class Type:
    pass

@dataclass
class TVar(Type):
    name: str

@dataclass
class Unit(Type):
    pass

@dataclass
class Tensor(Type):
    """张量积：并行操作"""
    left: Type
    right: Type

@dataclass
class LinArrow(Type):
    """线性蕴涵：操作干预"""
    domain: Type
    codomain: Type

@dataclass
class Bang(Type):
    """!-模态：轨迹/沉积（可复制）"""
    inner: Type

@dataclass
class Mu(Type):
    """归纳类型：有限操作"""
    var: str
    body: Type

@dataclass
class Nu(Type):
    """余归纳类型：无限操作"""
    var: str
    body: Type

@dataclass
class Agency(Type):
    """运行权类型：Ag_A(t) 表示t由A运行"""
    agent: str  # "self" 或操作者名
    inner: Type

@dataclass
class ClarityType(Type):
    """明性类型：Cl(t) 表示具有明性"""
    inner: Type

# ============================================================
# 项定义
# ============================================================

class Term:
    pass

@dataclass
class Var(Term):
    name: str

@dataclass
class UnitVal(Term):
    pass

@dataclass
class Lam(Term):
    """抽象：fn x => e"""
    param: str
    body: Term

@dataclass
class App(Term):
    """应用：e1 e2"""
    func: Term
    arg: Term

@dataclass
class Pair(Term):
    """并行组合：e1 * e2"""
    left: Term
    right: Term

@dataclass
class LetPair(Term):
    """let x*y = e1 in e2"""
    x: str
    y: str
    bound: Term
    body: Term

@dataclass
class Bang(Term):
    """轨迹化：!e"""
    inner: Term

@dataclass
class Derelict(Term):
    """从轨迹取一次：derelict e"""
    inner: Term

@dataclass
class Mu(Term):
    """有限递归：mu x.e"""
    var: str
    body: Term

@dataclass
class Nu(Term):
    """无限递归：nu x.e（需生产性保护）"""
    var: str
    body: Term

@dataclass
class Ag(Term):
    """运行权标注：ag(e, A)"""
    term: Term
    agent: str  # "self" 或操作者名

@dataclass
class Alien(Term):
    """异化标注：alien(e, B) — B夺走e的运行权"""
    term: Term
    agent: str

@dataclass
class Clarity(Term):
    """明性标注：clarity e"""
    term: Term

# ============================================================
# 类型检查器
# ============================================================

class TypeError(Exception):
    pass

class LinearContext:
    """线性上下文：追踪变量使用（Op类型变量只能用一次）"""
    def __init__(self):
        self.vars = {}  # name -> Type
        self.used = set()  # 已使用的线性变量
        self.bang_vars = set()  # !-模态变量（可重复使用）

    def add(self, name: str, ty: Type, bang: bool = False):
        self.vars[name] = ty
        if bang:
            self.bang_vars.add(name)

    def use(self, name: str) -> Type:
        if name not in self.vars:
            raise TypeError(f"未定义的变量: {name}")
        if name in self.used and name not in self.bang_vars:
            raise TypeError(f"线性变量 {name} 不能使用两次（Op不可复制）")
        self.used.add(name)
        return self.vars[name]

    def check_linear(self):
        """检查所有线性变量都被使用了（不能丢弃）"""
        for name in self.vars:
            if name not in self.used and name not in self.bang_vars:
                raise TypeError(f"线性变量 {name} 未被使用（Op不能丢弃）")

    def split(self):
        """分裂上下文（用于并行组合）"""
        ctx2 = LinearContext()
        return ctx2

def is_bang_type(ty: Type) -> bool:
    """判断类型是否是!-模态（Tr类型，可复制）"""
    return isinstance(ty, Bang)

def type_check(term: Term, ctx: LinearContext = None) -> Type:
    """类型检查主函数"""
    if ctx is None:
        ctx = LinearContext()

    if isinstance(term, Var):
        return ctx.use(term.name)

    elif isinstance(term, UnitVal):
        return Unit()

    elif isinstance(term, Lam):
        # 参数类型需要标注，这里简化为推断
        param_ty = TVar("?")  # 简化：实际应从标注获取
        ctx.add(term.param, param_ty)
        body_ty = type_check(term.body, ctx)
        return LinArrow(param_ty, body_ty)

    elif isinstance(term, App):
        func_ty = type_check(term.func, ctx)
        arg_ty = type_check(term.arg, ctx)
        if isinstance(func_ty, LinArrow):
            if not types_compatible(func_ty.domain, arg_ty):
                raise TypeError(
                    f"类型不匹配: 期望 {func_ty.domain}, 得到 {arg_ty}")
            return func_ty.codomain
        raise TypeError(f"不能应用非函数类型: {func_ty}")

    elif isinstance(term, Pair):
        left_ty = type_check(term.left, ctx)
        right_ty = type_check(term.right, ctx)
        return Tensor(left_ty, right_ty)

    elif isinstance(term, LetPair):
        bound_ty = type_check(term.bound, ctx)
        if isinstance(bound_ty, Tensor):
            ctx.add(term.x, bound_ty.left)
            ctx.add(term.y, bound_ty.right)
            return type_check(term.body, ctx)
        raise TypeError(f"解构需要张量积类型, 得到 {bound_ty}")

    elif isinstance(term, Bang):
        inner_ty = type_check(term.inner, ctx)
        return Bang(inner_ty)

    elif isinstance(term, Derelict):
        inner_ty = type_check(term.inner, ctx)
        if isinstance(inner_ty, Bang):
            return inner_ty.inner
        raise TypeError(f"derelict需要!-模态类型, 得到 {inner_ty}")

    elif isinstance(term, Mu):
        # mu x.e: x的类型是mu a.t
        ctx.add(term.var, TVar("mu_rec"))
        body_ty = type_check(term.body, ctx)
        return body_ty

    elif isinstance(term, Nu):
        # nu x.e: 需要生产性检查（简化版）
        ctx.add(term.var, TVar("nu_rec"))
        body_ty = type_check(term.body, ctx)
        if not is_productive(term.body):
            raise TypeError("nu递归必须是生产性的（每步必须有产出）")
        return body_ty

    elif isinstance(term, Ag):
        # ag(e, A): e由A运行
        inner_ty = type_check(term.term, ctx)
        return Agency(term.agent, inner_ty)

    elif isinstance(term, Alien):
        # alien(e, B): B夺走e的运行权
        inner_ty = type_check(term.term, ctx)
        if isinstance(inner_ty, Agency) and inner_ty.agent == "self":
            # 自我运行被异化：Ag_self(t) -> Ag_B(t)
            return Agency(term.agent, inner_ty.inner)
        elif isinstance(inner_ty, Agency):
            # 运行权传递：Ag_A(t) -> Ag_B(t)（定理1）
            return Agency(term.agent, inner_ty.inner)
        raise TypeError(f"异化需要运行权类型, 得到 {inner_ty}")

    elif isinstance(term, Clarity):
        # clarity e: e具有明性
        inner_ty = type_check(term.term, ctx)
        return ClarityType(inner_ty)

    else:
        raise TypeError(f"未知项: {term}")

def types_compatible(t1: Type, t2: Type) -> bool:
    """简化的类型兼容性检查"""
    if isinstance(t1, TVar) or isinstance(t2, TVar):
        return True  # 类型变量兼容一切
    if type(t1) != type(t2):
        return False
    if isinstance(t1, Unit):
        return True
    if isinstance(t1, Tensor):
        return (types_compatible(t1.left, t2.left) and
                types_compatible(t1.right, t2.right))
    if isinstance(t1, LinArrow):
        return (types_compatible(t1.domain, t2.domain) and
                types_compatible(t1.codomain, t2.codomain))
    if isinstance(t1, Bang):
        return types_compatible(t1.inner, t2.inner)
    if isinstance(t1, Agency):
        return t1.agent == t2.agent and types_compatible(t1.inner, t2.inner)
    if isinstance(t1, ClarityType):
        return types_compatible(t1.inner, t2.inner)
    return True

def is_productive(term: Term) -> bool:
    """生产性检查（简化版）：nu递归体必须以构造子（Pair/Lam/Bang等）开头"""
    if isinstance(term, (Pair, Lam, Bang, UnitVal)):
        return True
    if isinstance(term, App):
        return is_productive(term.func)
    return False

# ============================================================
# 异化检测器
# ============================================================

@dataclass
class AlienationReport:
    """异化检测报告"""
    term_description: str
    original_agent: str
    alienated_by: str
    has_clarity: bool
    can_persist: bool  # 异化是否能持续（定理9：有明性则不能持续）

def detect_alienation(term: Term) -> list[AlienationReport]:
    """检测项中的所有异化"""
    reports = []
    _detect_alienation_rec(term, False, reports)
    return reports

def _detect_alienation_rec(term: Term, under_clarity: bool, reports: list):
    if isinstance(term, Alien):
        inner_ty = type_check_safe(term.term)
        original = "self"
        if isinstance(inner_ty, Agency):
            original = inner_ty.agent
        reports.append(AlienationReport(
            term_description=str_term(term),
            original_agent=original,
            alienated_by=term.agent,
            has_clarity=under_clarity,
            can_persist=not under_clarity  # 定理9
        ))
        _detect_alienation_rec(term.term, under_clarity, reports)
    elif isinstance(term, Clarity):
        _detect_alienation_rec(term.term, True, reports)
    elif isinstance(term, App):
        _detect_alienation_rec(term.func, under_clarity, reports)
        _detect_alienation_rec(term.arg, under_clarity, reports)
    elif isinstance(term, Lam):
        _detect_alienation_rec(term.body, under_clarity, reports)
    elif isinstance(term, Pair):
        _detect_alienation_rec(term.left, under_clarity, reports)
        _detect_alienation_rec(term.right, under_clarity, reports)

def type_check_safe(term: Term) -> Optional[Type]:
    """安全类型检查（不抛异常）"""
    try:
        return type_check(term)
    except TypeError:
        return None

def str_term(term: Term) -> str:
    """项的字符串表示"""
    if isinstance(term, Var):
        return term.name
    if isinstance(term, Ag):
        return f"ag({str_term(term.term)}, {term.agent})"
    if isinstance(term, Alien):
        return f"alien({str_term(term.term)}, {term.agent})"
    if isinstance(term, Clarity):
        return f"clarity({str_term(term.term)})"
    if isinstance(term, Bang):
        return f"!{str_term(term.inner)}"
    if isinstance(term, Lam):
        return f"fn {term.param} => {str_term(term.body)}"
    if isinstance(term, App):
        return f"{str_term(term.func)} {str_term(term.arg)}"
    return str(term)

def str_type(ty: Type) -> str:
    """类型的字符串表示"""
    if isinstance(ty, TVar):
        return ty.name
    if isinstance(ty, Unit):
        return "1"
    if isinstance(ty, Tensor):
        return f"({str_type(ty.left)} * {str_type(ty.right)})"
    if isinstance(ty, LinArrow):
        return f"({str_type(ty.domain)} -> {str_type(ty.codomain)})"
    if isinstance(ty, Bang):
        return f"!{str_type(ty.inner)}"
    if isinstance(ty, Mu):
        return f"mu {ty.var}.{str_type(ty.body)}"
    if isinstance(ty, Nu):
        return f"nu {ty.var}.{str_type(ty.body)}"
    if isinstance(ty, Agency):
        return f"Ag_{ty.agent}({str_type(ty.inner)})"
    if isinstance(ty, ClarityType):
        return f"Cl({str_type(ty.inner)})"
    return str(ty)

# ============================================================
# 演示
# ============================================================

def demo():
    print("=" * 60)
    print("践演λ-演算（EλC）类型检查器 v0.1")
    print("=" * 60)

    # 示例1：基本线性类型
    print("\n--- 示例1：线性函数 ---")
    # fn x => x （恒等函数）
    id_term = Lam("x", Var("x"))
    ty = type_check(id_term)
    print(f"fn x => x : {str_type(ty)}")

    # 示例2：运行权标注
    print("\n--- 示例2：运行权标注 ---")
    # ag(self_labor, self) （工人自己运行自己的劳动）
    self_labor = Ag(Var("labor"), "self")
    ctx = LinearContext()
    ctx.add("labor", TVar("Work"))
    ty = type_check(self_labor, ctx)
    print(f"ag(labor, self) : {str_type(ty)}")

    # 示例3：异化
    print("\n--- 示例3：异化（运行权被夺走） ---")
    # alien(ag(labor, self), capital)
    alienated = Alien(Ag(Var("labor"), "self"), "capital")
    ctx2 = LinearContext()
    ctx2.add("labor", TVar("Work"))
    ty = type_check(alienated, ctx2)
    print(f"alien(ag(labor, self), capital) : {str_type(ty)}")
    print("  → 运行权从 self 转移到 capital（定理1：运行权传递）")

    # 示例4：明性反异化
    print("\n--- 示例4：明性使持续异化不可能（定理9） ---")
    # clarity(alien(ag(labor, self), capital))
    clear = Clarity(Alien(Ag(Var("labor"), "self"), "capital"))
    ctx3 = LinearContext()
    ctx3.add("labor", TVar("Work"))
    ty = type_check(clear, ctx3)
    print(f"clarity(alien(ag(labor, self), capital)) : {str_type(ty)}")

    reports = detect_alienation(clear)
    for r in reports:
        print(f"  检测到异化: {r.original_agent} → {r.alienated_by}")
        print(f"  明性: {'是' if r.has_clarity else '否'}")
        print(f"  异化能否持续: {'能' if r.can_persist else '不能（定理9）'}")

    # 示例5：线性变量不能复制
    print("\n--- 示例5：Op不可复制（公理E4） ---")
    # fn x => x * x （试图复制x——应该报错）
    try:
        bad = Lam("x", Pair(Var("x"), Var("x")))
        ctx4 = LinearContext()
        ctx4.add("x", TVar("t"))
        type_check(bad, ctx4)
        print("fn x => x * x : 类型错误（应该报错但没有）")
    except TypeError as e:
        print(f"fn x => x * x : 类型错误 ✓")
        print(f"  错误: {e}")

    # 示例6：!-模态可以复制
    print("\n--- 示例6：Tr（!-模态）可复制（公理E3） ---")
    # derelict(x) * derelict(x) （!类型可以多次使用）
    good = Pair(Derelict(Var("x")), Derelict(Var("x")))
    ctx5 = LinearContext()
    ctx5.add("x", Bang(TVar("t")), bang=True)
    ty = type_check(good, ctx5)
    print(f"derelict(x) * derelict(x) : {str_type(ty)} ✓")
    print("  （!-模态轨迹可以复制，活操作不能）")

    # 示例7：运行权链
    print("\n--- 示例7：运行权传递链（定理1） ---")
    # alien(alien(alien(ag(worker, self), manager), capitalist), capital)
    chain = Alien(
        Alien(
            Alien(Ag(Var("worker"), "self"), "manager"),
            "capitalist"
        ),
        "capital"
    )
    ctx6 = LinearContext()
    ctx6.add("worker", TVar("Work"))
    ty = type_check(chain, ctx6)
    print(f"alien(alien(alien(ag(worker,self),manager),capitalist),capital)")
    print(f"  : {str_type(ty)}")
    print("  → 运行权链: worker → manager → capitalist → capital")
    print("  → 最终运行权属于capital（定理4：反自指系统无主体）")

    print("\n" + "=" * 60)
    print("EλC类型检查器演示完成")
    print("=" * 60)

if __name__ == "__main__":
    demo()

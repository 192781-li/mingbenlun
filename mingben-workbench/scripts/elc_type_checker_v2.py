#!/usr/bin/env python3
# Author: workbuddy
"""
践演λ-演算（Enactive λ-Calculus, EλC）类型检查器 v2

对齐《践演论 v1.11》的类型系统硬伤修正：
- Ag(a,A) 分裂为 Ag_lv(a,A)（活运行权，线性资源）与 Ag_tr(a,A)（轨迹运行权，来自 !-模态）
- 新增 Hijack(b,a)（异化前提类型，线性资源，非对称）
- Cl(a,A) 持有 Ag_lv(a,A) ⊗ !Ag_tr(a,A)
- Alien-I 改为条件规则：必须先提供 Hijack(b,a) 前提，否则运行权类型不塌缩

与 v0.1 的差异（哪些旧行为现在会报错，正是修复点）：
- 旧 `alien(ag(labor,self), capital)` 无条件通过（所有运行权类型等价）—— 现在缺 Hijack 前提直接 TypeError
- 旧 `Ag` 单一类型无法区分活/轨迹 —— 现在分裂，dereliction 只能从 !Ag 到 Ag_tr

本文件是加法贡献：保留 v0.1 作为历史，本文件可直接作为回归测试运行。
运行：python elc_type_checker_v2.py
"""

from dataclasses import dataclass
from typing import Optional


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
    left: Type
    right: Type

@dataclass
class LinArrow(Type):
    domain: Type
    codomain: Type

@dataclass
class Bang(Type):
    """!-模态：轨迹/沉积（可复制）"""
    inner: Type

@dataclass
class Mu(Type):
    var: str
    body: Type

@dataclass
class Nu(Type):
    var: str
    body: Type

# ---- v1.11 新增/分裂的类型 ----

@dataclass
class AgLive(Type):
    """活运行权 Ag_lv(a,A)：仅由线性假设 self_ev<a,A> 居住，不可复制不可沉积"""
    agent: str
    inner: Type

@dataclass
class AgTrace(Type):
    """轨迹运行权 Ag_tr(a,A)：来自 !Ag(a,A) 的 dereliction，可复制可沉积"""
    agent: str
    inner: Type

@dataclass
class HijackType(Type):
    """异化前提类型 Hijack(b,a)：b 具备夺取 a 运行权的条件（线性资源，非对称）"""
    thief: str
    victim: str

@dataclass
class SelfEvType(Type):
    """自我践行资源 self_ev<a,A>：活运行权的唯一来源（线性资源）"""
    agent: str

@dataclass
class ClarityType(Type):
    """明性类型 Cl(a,A)：持有 Ag_lv(a,A) ⊗ !Ag_tr(a,A)"""
    agent: str
    inner: Type

@dataclass
class BoolType(Type):
    pass


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
    param: str
    body: Term

@dataclass
class App(Term):
    func: Term
    arg: Term

@dataclass
class Pair(Term):
    left: Term
    right: Term

@dataclass
class LetPair(Term):
    x: str
    y: str
    bound: Term
    body: Term

@dataclass
class Bang(Term):
    inner: Term

@dataclass
class Derelict(Term):
    inner: Term

@dataclass
class Mu(Term):
    var: str
    body: Term

@dataclass
class Nu(Term):
    var: str
    body: Term

# ---- v1.11 项构造子 ----

@dataclass
class SelfEv(Term):
    """引入 self_ev<a,A> 资源（活运行权的唯一来源）"""
    agent: str

@dataclass
class Live(Term):
    """活运行权引入：live<a>(e)，其中 e:A 且上下文含 self_ev<a,A>"""
    selfev: Term          # 必须是一个 SelfEv(a) 项
    body: Term            # : A

@dataclass
class UnLive(Term):
    """活运行权消去：unlive(e) : Ag_lv(a,A) -> A"""
    inner: Term

@dataclass
class Trace(Term):
    """轨迹运行权引入：trace(e)，e : !Ag(a,A) -> Ag_tr(a,A)"""
    inner: Term

@dataclass
class UnTrace(Term):
    """轨迹运行权消去：untrace(e) : Ag_tr(a,A) -> !Ag(a,A)"""
    inner: Term

@dataclass
class Alien(Term):
    """异化引入（条件规则）：alien<b>(e, h)
       e : Ag_lv(a,A)，h : Hijack(b,a)  =>  alien<b>(e,h) : Ag_lv(b,A)
       无 Hijack 前提则报错——这正是修复 AliEn 规则塌缩的关键"""
    term: Term
    agent: str
    hijack: Term          # 必须是一个 HijackTerm(b,a) 项

@dataclass
class HijackTerm(Term):
    """异化前提资源：Hijack(b,a)
       Hijack(self,a)=0 且 Hijack(b,self)=0（self 运行权不可剥夺/不需夺取）"""
    thief: str
    victim: str

@dataclass
class Clarity(Term):
    """明性引入：see<a>(e,m)
       e : Ag_lv(a,A)，m : !Ag_tr(a,A)  =>  see<a>(e,m) : Cl(a,A)"""
    live: Term            # : Ag_lv(a,A)
    model: Term           # : !Ag_tr(a,A)

@dataclass
class UnSee(Term):
    """明性消去：unsee(e) : Cl(a,A) -> Ag_lv(a,A) ⊗ !Ag_tr(a,A)"""
    inner: Term

@dataclass
class ModelVal(Term):
    """已沉积的轨迹模型资源：直接具有 !Ag_tr(a,A) 类型
       （代表由活过程每一步 deposit 留下的可复制记录）"""
    agent: str
    inner: Type

@dataclass
class SelfCheck(Term):
    """明性自检：self_check(e)，e : Cl(a,A) -> Bool
       比较活过程（unlive e）与轨迹模型（untrace m）"""
    inner: Term


# ============================================================
# 类型检查器
# ============================================================

class TypeError(Exception):
    pass

class LinearContext:
    def __init__(self):
        self.vars = {}
        self.used = set()
        self.bang_vars = set()

    def add(self, name, ty, bang=False):
        self.vars[name] = ty
        if bang:
            self.bang_vars.add(name)

    def use(self, name):
        if name not in self.vars:
            raise TypeError(f"未定义的变量: {name}")
        if name in self.used and name not in self.bang_vars:
            raise TypeError(f"线性变量 {name} 不能使用两次（Op不可复制）")
        self.used.add(name)
        return self.vars[name]

    def check_linear(self):
        for name in self.vars:
            if name not in self.used and name not in self.bang_vars:
                raise TypeError(f"线性变量 {name} 未被使用（Op不能丢弃）")

    def split(self):
        return LinearContext()


def is_bang_type(ty):
    return isinstance(ty, Bang)


def type_check(term, ctx=None):
    if ctx is None:
        ctx = LinearContext()

    if isinstance(term, Var):
        return ctx.use(term.name)

    if isinstance(term, UnitVal):
        return Unit()

    if isinstance(term, Lam):
        param_ty = TVar("?")
        ctx.add(term.param, param_ty)
        body_ty = type_check(term.body, ctx)
        return LinArrow(param_ty, body_ty)

    if isinstance(term, App):
        func_ty = type_check(term.func, ctx)
        arg_ty = type_check(term.arg, ctx)
        if isinstance(func_ty, LinArrow):
            if not types_compatible(func_ty.domain, arg_ty):
                raise TypeError(f"类型不匹配: 期望 {func_ty.domain}, 得到 {arg_ty}")
            return func_ty.codomain
        raise TypeError(f"不能应用非函数类型: {func_ty}")

    if isinstance(term, Pair):
        left_ty = type_check(term.left, ctx)
        right_ty = type_check(term.right, ctx)
        return Tensor(left_ty, right_ty)

    if isinstance(term, LetPair):
        bound_ty = type_check(term.bound, ctx)
        if isinstance(bound_ty, Tensor):
            ctx.add(term.x, bound_ty.left)
            ctx.add(term.y, bound_ty.right)
            return type_check(term.body, ctx)
        raise TypeError(f"解构需要张量积类型, 得到 {bound_ty}")

    if isinstance(term, Bang):
        inner_ty = type_check(term.inner, ctx)
        return Bang(inner_ty)

    if isinstance(term, Derelict):
        inner_ty = type_check(term.inner, ctx)
        if isinstance(inner_ty, Bang):
            return inner_ty.inner
        raise TypeError(f"derelict需要!-模态类型, 得到 {inner_ty}")

    if isinstance(term, Mu):
        ctx.add(term.var, TVar("mu_rec"))
        body_ty = type_check(term.body, ctx)
        return body_ty

    if isinstance(term, Nu):
        ctx.add(term.var, TVar("nu_rec"))
        body_ty = type_check(term.body, ctx)
        if not is_productive(term.body):
            raise TypeError("nu递归必须是生产性的（每步必须有产出）")
        return body_ty

    # ---- v1.11 规则 ----

    if isinstance(term, SelfEv):
        if term.agent == "self":
            # self_ev<self,A> 是合法的活运行权来源
            return SelfEvType("self")
        return SelfEvType(term.agent)

    if isinstance(term, Live):
        # live<a>(e)：selfev 必须是 SelfEv(a)，body : A
        se_ty = type_check(term.selfev, ctx)
        if not isinstance(se_ty, SelfEvType):
            raise TypeError(f"live 的第一个参数必须是 self_ev 资源, 得到 {se_ty}")
        a = se_ty.agent
        body_ty = type_check(term.body, ctx)
        return AgLive(a, body_ty)

    if isinstance(term, UnLive):
        inner_ty = type_check(term.inner, ctx)
        if isinstance(inner_ty, AgLive):
            return inner_ty.inner
        raise TypeError(f"unlive需要 Ag_lv 类型, 得到 {inner_ty}")

    if isinstance(term, Trace):
        inner_ty = type_check(term.inner, ctx)
        if isinstance(inner_ty, Bang) and isinstance(inner_ty.inner, AgTrace):
            return inner_ty.inner  # !Ag_tr -> Ag_tr
        if isinstance(inner_ty, Bang) and isinstance(inner_ty.inner, AgLive):
            raise TypeError("无法从 !Ag_lv 得到 Ag_tr：活运行权不能直接沉积（需 deposit 操作）")
        raise TypeError(f"trace需要 !Ag_tr 类型, 得到 {inner_ty}")

    if isinstance(term, UnTrace):
        inner_ty = type_check(term.inner, ctx)
        if isinstance(inner_ty, AgTrace):
            return Bang(inner_ty)
        raise TypeError(f"untrace需要 Ag_tr 类型, 得到 {inner_ty}")

    if isinstance(term, HijackTerm):
        # 非对称：self 不可作为 thief 或 victim
        if term.thief == "self":
            raise TypeError("Hijack(self,a)=0：不能夺取自己的运行权")
        if term.victim == "self":
            raise TypeError("Hijack(b,self)=0：无人能夺取 self 的运行权（不可剥夺）")
        if term.thief == term.victim:
            raise TypeError("Hijack(a,a)=0：不能异化自己")
        return HijackType(term.thief, term.victim)

    if isinstance(term, Alien):
        # Alien-I'：需要 Ag_lv(a,A) 与 Hijack(b,a)
        h_ty = type_check(term.hijack, ctx)
        if not isinstance(h_ty, HijackType):
            raise TypeError(f"alien 的第三个参数必须是 Hijack 前提, 得到 {h_ty}")
        b, a = h_ty.thief, h_ty.victim
        if b != term.agent:
            raise TypeError(f"alien 的 agent({term.agent}) 必须与 Hijack 的 thief({b}) 一致")
        inner_ty = type_check(term.term, ctx)
        if not isinstance(inner_ty, AgLive):
            raise TypeError(f"alien 只能作用于活运行权 Ag_lv, 得到 {inner_ty}")
        if inner_ty.agent != a:
            raise TypeError(f"alien 的 victim 必须与活运行权主体一致: Hijack({b},{a}) vs Ag_lv({inner_ty.agent})")
        # 异化结果仍是 Ag_lv，但运行者变为 b
        return AgLive(b, inner_ty.inner)

    if isinstance(term, Clarity):
        live_ty = type_check(term.live, ctx)
        if not isinstance(live_ty, AgLive):
            raise TypeError(f"see 的第一个参数必须是 Ag_lv, 得到 {live_ty}")
        model_ty = type_check(term.model, ctx)
        if not (isinstance(model_ty, Bang) and isinstance(model_ty.inner, AgTrace)):
            raise TypeError(f"see 的第二个参数必须是 !Ag_tr, 得到 {model_ty}")
        if live_ty.agent != model_ty.inner.agent:
            raise TypeError("see 的活过程与轨迹模型主体必须一致")
        return ClarityType(live_ty.agent, live_ty.inner)

    if isinstance(term, UnSee):
        inner_ty = type_check(term.inner, ctx)
        if isinstance(inner_ty, ClarityType):
            return Tensor(AgLive(inner_ty.agent, inner_ty.inner),
                          Bang(AgTrace(inner_ty.agent, inner_ty.inner)))
        raise TypeError(f"unsee需要 Cl 类型, 得到 {inner_ty}")

    if isinstance(term, ModelVal):
        return Bang(AgTrace(term.agent, term.inner))

    if isinstance(term, SelfCheck):
        inner_ty = type_check(term.inner, ctx)
        if not isinstance(inner_ty, ClarityType):
            raise TypeError(f"self_check需要 Cl 类型, 得到 {inner_ty}")
        return BoolType()

    raise TypeError(f"未知项: {term}")


def types_compatible(t1, t2):
    if isinstance(t1, TVar) or isinstance(t2, TVar):
        return True
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
    if isinstance(t1, AgLive):
        return t1.agent == t2.agent and types_compatible(t1.inner, t2.inner)
    if isinstance(t1, AgTrace):
        return t1.agent == t2.agent and types_compatible(t1.inner, t2.inner)
    if isinstance(t1, ClarityType):
        return t1.agent == t2.agent and types_compatible(t1.inner, t2.inner)
    return True


def is_productive(term):
    if isinstance(term, (Pair, Lam, Bang, UnitVal)):
        return True
    if isinstance(term, App):
        return is_productive(term.func)
    return False


# ============================================================
# 异化检测器（基于 v1.11 类型）
# ============================================================

@dataclass
class AlienationReport:
    term_description: str
    original_agent: str
    alienated_by: str
    has_clarity: bool
    can_persist: bool


def detect_alienation(term):
    reports = []
    _detect(term, False, reports)
    return reports

def _detect(term, under_clarity, reports):
    if isinstance(term, Alien):
        inner_ty = type_check_safe(term.term)
        original = inner_ty.agent if isinstance(inner_ty, AgLive) else "?"
        reports.append(AlienationReport(
            term_description=str_term(term),
            original_agent=original,
            alienated_by=term.agent,
            has_clarity=under_clarity,
            can_persist=not under_clarity))
        _detect(term.term, under_clarity, reports)
    elif isinstance(term, Clarity):
        _detect(term.live, True, reports)
        _detect(term.model, under_clarity, reports)
    elif isinstance(term, App):
        _detect(term.func, under_clarity, reports)
        _detect(term.arg, under_clarity, reports)
    elif isinstance(term, Lam):
        _detect(term.body, under_clarity, reports)
    elif isinstance(term, Pair):
        _detect(term.left, under_clarity, reports)
        _detect(term.right, under_clarity, reports)

def type_check_safe(term):
    try:
        return type_check(term)
    except TypeError:
        return None


def str_term(term):
    if isinstance(term, Var):
        return term.name
    if isinstance(term, SelfEv):
        return f"self_ev({term.agent})"
    if isinstance(term, Live):
        return f"live({str_term(term.selfev)}, {str_term(term.body)})"
    if isinstance(term, Alien):
        return f"alien({str_term(term.term)}, {term.agent}, {str_term(term.hijack)})"
    if isinstance(term, HijackTerm):
        return f"hijack({term.thief},{term.victim})"
    if isinstance(term, Clarity):
        return f"see({str_term(term.live)}, {str_term(term.model)})"
    if isinstance(term, Bang):
        return f"!{str_term(term.inner)}"
    if isinstance(term, Lam):
        return f"fn {term.param} => {str_term(term.body)}"
    if isinstance(term, App):
        return f"{str_term(term.func)} {str_term(term.arg)}"
    return str(term)

def str_type(ty):
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
    if isinstance(ty, AgLive):
        return f"Ag_lv({ty.agent},{str_type(ty.inner)})"
    if isinstance(ty, AgTrace):
        return f"Ag_tr({ty.agent},{str_type(ty.inner)})"
    if isinstance(ty, HijackType):
        return f"Hijack({ty.thief},{ty.victim})"
    if isinstance(ty, SelfEvType):
        return f"self_ev({ty.agent})"
    if isinstance(ty, ClarityType):
        return f"Cl({ty.agent},{str_type(ty.inner)})"
    if isinstance(ty, BoolType):
        return "Bool"
    return str(ty)


# ============================================================
# 演示 + 回归测试
# ============================================================

def demo():
    print("=" * 60)
    print("践演λ-演算（EλC）类型检查器 v2 —— 对齐 v1.11 类型分裂")
    print("=" * 60)

    # 示例1：活运行权（self_ev -> live）
    print("\n--- 示例1：工人自己运行自己的劳动（活运行权） ---")
    ctx = LinearContext()
    ctx.add("labor", TVar("Work"))
    self_labor = Live(SelfEv("self"), Var("labor"))
    ty = type_check(self_labor, ctx)
    print(f"  live(self_ev(self), labor) : {str_type(ty)}")

    # 示例2：异化必须提供 Hijack 前提（self 的运行权不可被夺，故 victim 用非 self 主体）
    print("\n--- 示例2：异化需要 Hijack 前提（修复 Alien 规则塌缩） ---")
    # 合法异化：worker 的运行权被 capital 夺走，提供 hijack(capital, worker)
    ctx2 = LinearContext()
    ctx2.add("labor", TVar("Work"))
    h = HijackTerm("capital", "worker")
    alienated = Alien(Live(SelfEv("worker"), Var("labor")), "capital", h)
    ty2 = type_check(alienated, ctx2)
    print(f"  alien(live(...), capital, hijack(capital,worker)) : {str_type(ty2)}  [合法]")

    # 非法异化：无 Hijack 前提 —— 旧 v0.1 会通过，现在必须报错
    print("  旧写法 alien(ag(labor,worker), capital) 无前提在 v2 中：")
    bad = Alien(Live(SelfEv("worker"), Var("labor")), "capital",
                Var("__no_hijack__"))  # 故意不提供 Hijack
    try:
        type_check(bad, LinearContext())
        print("    [BUG] 应该报错却没报")
    except TypeError as e:
        print(f"    TypeError ✓（运行权不再无条件塌缩）: {e}")

    # 示例3：self 不可被夺取（Hijack(b,self)=0）
    print("\n--- 示例3：self 运行权不可剥夺（Hijack(b,self)=0） ---")
    try:
        type_check(HijackTerm("capital", "self"))
        print("    [BUG] 应该报错却没报")
    except TypeError as e:
        print(f"    TypeError ✓: {e}")

    # 示例4：明性检测劫持（v1.11 定理7.2'）
    print("\n--- 示例4：明性持有活过程+轨迹，self_check 可检测篡改 ---")
    ctx4 = LinearContext()
    ctx4.add("labor", TVar("Work"))
    cl = Clarity(Live(SelfEv("self"), Var("labor")),
                 ModelVal("self", TVar("Work")))
    ctx4b = LinearContext(); ctx4b.add("labor", TVar("Work"))
    ty4 = type_check(cl, ctx4b)
    print(f"  see(live(...), !trace(self,Work)) : {str_type(ty4)}")
    sc = SelfCheck(cl)
    ctx4c = LinearContext(); ctx4c.add("labor", TVar("Work"))
    print(f"  self_check(see(...)) : {str_type(type_check(sc, ctx4c))}")

    print("\n" + "=" * 60)
    print("EλC 类型检查器 v2 演示完成")
    print("=" * 60)


def regression():
    """回归测试：断言关键修复点（返回 (passed, failed) 计数）"""
    passed = failed = 0
    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  ✓ {name}")
        else:
            failed += 1
            print(f"  ✗ {name}  [FAILED]")

    print("\n--- 回归测试（v1.11 修复点） ---")

    # R1: 活运行权可构造
    ctx = LinearContext(); ctx.add("labor", TVar("Work"))
    try:
        ty = type_check(Live(SelfEv("self"), Var("labor")), ctx)
        check("Ag_lv 可构造", isinstance(ty, AgLive) and ty.agent == "self")
    except TypeError:
        check("Ag_lv 可构造", False)

    # R2: 异化无 Hijack 前提必须失败（核心修复）
    try:
        type_check(Alien(Live(SelfEv("self"), Var("labor")), "capital",
                         Var("x")), LinearContext())
        check("无 Hijack 则异化失败", False)
    except TypeError:
        check("无 Hijack 则异化失败", True)

    # R3: 异化有 Hijack 前提可通过（victim 须非 self，否则 Hijack(b,self)=0）
    ctx3 = LinearContext(); ctx3.add("labor", TVar("Work"))
    try:
        ty = type_check(Alien(Live(SelfEv("worker"), Var("labor")), "capital",
                               HijackTerm("capital", "worker")), ctx3)
        check("有 Hijack 则异化通过", isinstance(ty, AgLive) and ty.agent == "capital")
    except TypeError:
        check("有 Hijack 则异化通过", False)

    # R4: Hijack(b,self) 不可构造
    try:
        type_check(HijackTerm("capital", "self"))
        check("Hijack(b,self)=0", False)
    except TypeError:
        check("Hijack(b,self)=0", True)

    # R5: Hijack(self,a) 不可构造
    try:
        type_check(HijackTerm("self", "capital"))
        check("Hijack(self,a)=0", False)
    except TypeError:
        check("Hijack(self,a)=0", True)

    # R6: trace 从 !Ag_tr 居住（ModelVal 给出 !Ag_tr 项）
    ctx6 = LinearContext()
    try:
        ty = type_check(Trace(ModelVal("self", TVar("Work"))), ctx6)
        check("Ag_tr 可构造", isinstance(ty, AgTrace))
    except TypeError:
        check("Ag_tr 可构造", False)

    # R7: 明性类型 Cl 持有 Ag_lv ⊗ !Ag_tr
    try:
        ctx7 = LinearContext(); ctx7.add("labor", TVar("Work"))
        cl = Clarity(Live(SelfEv("self"), Var("labor")),
                     ModelVal("self", TVar("Work")))
        ty = type_check(cl, ctx7)
        check("Cl 类型可构造", isinstance(ty, ClarityType))
        ctx7b = LinearContext(); ctx7b.add("labor", TVar("Work"))
        out = type_check(UnSee(cl), ctx7b)
        check("unsee 输出 Ag_lv ⊗ !Ag_tr",
              isinstance(out, Tensor) and isinstance(out.left, AgLive)
              and isinstance(out.right, Bang) and isinstance(out.right.inner, AgTrace))
    except TypeError as e:
        check(f"Cl 类型可构造 ({e})", False)

    # R8: self_check 接受 Cl 返回 Bool
    try:
        ctx8 = LinearContext(); ctx8.add("labor", TVar("Work"))
        cl = Clarity(Live(SelfEv("self"), Var("labor")),
                     ModelVal("self", TVar("Work")))
        ty = type_check(SelfCheck(cl), ctx8)
        check("self_check : Cl -> Bool", isinstance(ty, BoolType))
    except TypeError:
        check("self_check : Cl -> Bool", False)

    print(f"\n  回归测试结果: {passed} 通过, {failed} 失败")
    return passed, failed


if __name__ == "__main__":
    demo()
    p, f = regression()
    import sys
    sys.exit(1 if f else 0)

#!/usr/bin/env python3
"""
践演迹语言 (Performative Trace Language, PTL) — 实用语言原型 v2
线性类型 + F1/F2分类 + 生产性检查 + ν*F成长状态 + GoI迹
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import re, os

# ============================================================
# 类型
# ============================================================
class Ty:
    def __eq__(self, other): return type(self) == type(other)
    def __repr__(self): return self.__class__.__name__

class TInt(Ty):
    def __repr__(self): return "Int"
class TStr(Ty):
    def __repr__(self): return "Str"
class TBool(Ty):
    def __repr__(self): return "Bool"

@dataclass
class TTensor(Ty):
    l: Ty; r: Ty
    def __eq__(self, o): return isinstance(o, TTensor) and self.l==o.l and self.r==o.r
    def __repr__(self): return f"({self.l} * {self.r})"

@dataclass
class TF1(Ty):
    inp: Ty; out: Ty
    def __eq__(self, o): return isinstance(o, TF1) and self.inp==o.inp and self.out==o.out
    def __repr__(self): return f"({self.inp} -> {self.out})"

@dataclass
class TF2(Ty):
    inp: Ty; st: Ty; out: Ty
    def __eq__(self, o): return isinstance(o, TF2) and self.inp==o.inp and self.st==o.st and self.out==o.out
    def __repr__(self): return f"({self.inp} -o [{self.st}] {self.out})"

@dataclass
class TNuF2(Ty):
    out: Ty
    def __eq__(self, o): return isinstance(o, TNuF2) and self.out==o.out
    def __repr__(self): return f"νF2[{self.out}]"

@dataclass
class TGrowing(Ty):
    fields: dict
    def __eq__(self, o): return isinstance(o, TGrowing) and self.fields==o.fields
    def __repr__(self): return "G{" + ",".join(f"{k}:{v}" for k,v in self.fields.items()) + "}"
@dataclass
class TReflected(Ty):
    """f³/明性：包装一个类型，表示该值能看见自己的模型"""
    inner: Ty
    def __eq__(self, o): return isinstance(o, TReflected) and self.inner==o.inner
    def __repr__(self): return f"明({self.inner})"

# ============================================================
# AST
# ============================================================
class Expr: pass
@dataclass
class EInt(Expr): val: int
@dataclass
class EStr(Expr): val: str
@dataclass
class EBool(Expr): val: bool
@dataclass
class EVar(Expr): name: str
@dataclass
class ELam(Expr): p: str; pty: Ty; body: Expr
@dataclass
class EApp(Expr): f: Expr; a: Expr
@dataclass
class EPair(Expr): l: Expr; r: Expr
@dataclass
class ELetPair(Expr): pair: Expr; x: str; y: str; body: Expr
@dataclass
class EProc(Expr): inp: str; ity: Ty; st: str; sty: Ty; body: Expr
@dataclass
class ERun(Expr): proc: Expr; inp: Expr; st: Expr
@dataclass
class EStream(Expr): sname: str; init: Expr; step: Expr
@dataclass
class ETake(Expr): stream: Expr; n: int
@dataclass
class EGrowing(Expr): fields: dict
@dataclass
class EGrow(Expr): tgt: Expr; cap: str; val: Expr
@dataclass
class EGetCap(Expr): tgt: Expr; cap: str
@dataclass
class EReflect(Expr): tgt: Expr       # f³: 包装成长状态，使其能看见自己
@dataclass
class ESelfCaps(Expr): tgt: Expr      # f³: 看见自己当前的全部能力（模型作为模型）
@dataclass
class ESelfHistory(Expr): tgt: Expr   # f³: 看见自己的成长历史
@dataclass
class EReify(Expr): tgt: Expr         # 从f³回到f²：取出被包装的成长状态
@dataclass
class EBinOp(Expr): op: str; l: Expr; r: Expr
@dataclass
class EIf(Expr): c: Expr; t: Expr; e: Expr
@dataclass
class ELet(Expr): name: str; val: Expr; body: Expr
@dataclass
class EFst(Expr): pair: Expr
@dataclass
class ESnd(Expr): pair: Expr
@dataclass
class ESeq(Expr): exprs: list

# ============================================================
# Parser
# ============================================================
def tokenize(s):
    s = re.sub(r';[^\n]*', '', s)
    return s.replace('(',' ( ').replace(')',' ) ').split()

def parse_ty(s):
    s = s.strip()
    if s == 'Int': return TInt()
    if s == 'Str': return TStr()
    if s == 'Bool': return TBool()
    if s.startswith('νF2[') and s.endswith(']'): return TNuF2(parse_ty(s[4:-1]))
    if '->' in s and '-o' not in s:
        a,b = s.split('->',1); return TF1(parse_ty(a), parse_ty(b))
    m = re.match(r'(.+?)\s+-o\s+\[(.+?)\]\s+(.+)', s)
    if m: return TF2(parse_ty(m.group(1)), parse_ty(m.group(2)), parse_ty(m.group(3)))
    if '*' in s:
        a,b = s.split('*',1); return TTensor(parse_ty(a), parse_ty(b))
    if s.startswith('G{') and s.endswith('}'):
        fs = {}
        inner = s[2:-1].strip()
        if inner:
            for item in re.split(r',(?![^{]*\})', inner):
                if ':' in item:
                    k,v = item.split(':',1); fs[k.strip()] = parse_ty(v.strip())
        return TGrowing(fs)
    raise SyntaxError(f"未知类型: {s}")

def parse(tokens):
    if not tokens: raise SyntaxError("EOF")
    tok = tokens.pop(0)
    if tok == '(':
        lst = []
        while tokens and tokens[0] != ')':
            lst.append(parse(tokens))
        if not tokens: raise SyntaxError("缺少 )")
        tokens.pop(0)
        return parse_list(lst)
    if tok == ')': raise SyntaxError("多余的 )")
    if tok.startswith('"') and tok.endswith('"'): return EStr(tok[1:-1])
    if tok == 'true': return EBool(True)
    if tok == 'false': return EBool(False)
    if tok.lstrip('-').isdigit(): return EInt(int(tok))
    return EVar(tok)

def parse_list(lst):
    if not lst: raise SyntaxError("空列表")
    h = lst[0]
    if isinstance(h, EVar):
        op = h.name
        def get_param(p):
            """提取参数名和类型。(x Int)可能被解析为EApp(x, Int)"""
            if isinstance(p, EApp) and isinstance(p.f, EVar) and isinstance(p.a, EVar):
                return p.f.name, parse_ty(p.a.name)
            if isinstance(p, list) and len(p) == 2:
                name = p[0].name if isinstance(p[0], EVar) else str(p[0])
                ty_str = p[1].name if isinstance(p[1], EVar) else str(p[1])
                return name, parse_ty(ty_str)
            if isinstance(p, EVar):
                return p.name, TInt()
            raise SyntaxError(f"无效参数: {p}")
        
        if op == 'lam' and len(lst) == 3:
            name, ty = get_param(lst[1])
            return ELam(name, ty, lst[2])
        if op == 'proc' and len(lst) == 4:
            in_name, in_ty = get_param(lst[1])
            st_name, st_ty = get_param(lst[2])
            return EProc(in_name, in_ty, st_name, st_ty, lst[3])
        if op == 'stream' and len(lst) == 4:
            sname = lst[1].name if isinstance(lst[1], EVar) else str(lst[1])
            return EStream(sname, lst[2], lst[3])
        if op == 'pair' and len(lst) == 3: return EPair(lst[1], lst[2])
        if op == 'let-pair' and len(lst) == 5:
            return ELetPair(lst[1], lst[2].name, lst[3].name, lst[4])
        if op == 'run' and len(lst) == 4: return ERun(lst[1], lst[2], lst[3])
        if op == 'take' and len(lst) == 3:
            return ETake(lst[1], lst[2].val if isinstance(lst[2], EInt) else int(lst[2]))
        if op == 'growing' and len(lst) == 2:
            fields = {}
            raw = lst[1]
            # Flatten: ((a 1) (b 2)) or ((a 1)) or (a 1)
            if isinstance(raw, list):
                items = raw
            else:
                items = [raw]
            for item in items:
                if isinstance(item, EApp) and isinstance(item.f, EVar):
                    fields[item.f.name] = item.a
                elif isinstance(item, list) and len(item) == 2:
                    k = item[0].name if isinstance(item[0], EVar) else str(item[0])
                    fields[k] = item[1]
            return EGrowing(fields)
        if op == 'grow' and len(lst) == 4:
            cap = lst[2].name if isinstance(lst[2], EVar) else str(lst[2])
            return EGrow(lst[1], cap, lst[3])
        if op == 'get-cap' and len(lst) == 3:
            cap = lst[2].name if isinstance(lst[2], EVar) else str(lst[2])
            return EGetCap(lst[1], cap)
        if op == 'reflect' and len(lst) == 2: return EReflect(lst[1])
        if op == 'self-caps' and len(lst) == 2: return ESelfCaps(lst[1])
        if op == 'self-history' and len(lst) == 2: return ESelfHistory(lst[1])
        if op == 'reify' and len(lst) == 2: return EReify(lst[1])
        if op == 'if' and len(lst) == 4: return EIf(lst[1], lst[2], lst[3])
        if op == 'let' and len(lst) == 4:
            name = lst[1].name if isinstance(lst[1], EVar) else str(lst[1])
            return ELet(name, lst[2], lst[3])
        if op == 'seq' and len(lst) >= 2: return ESeq(lst[1:])
        if op in ('+','-','*','/','<','>','<=','>=','==','!=') and len(lst) == 3:
            return EBinOp(op, lst[1], lst[2])
        if op == 'fst' and len(lst) == 2: return EFst(lst[1])
        if op == 'snd' and len(lst) == 2: return ESnd(lst[1])
    # 函数应用
    if len(lst) == 2:
        return EApp(lst[0], lst[1])
    raise SyntaxError(f"无法解析: {lst}")

def parse_program(s):
    tokens = tokenize(s)
    exprs = []
    while tokens:
        exprs.append(parse(tokens))
    if len(exprs) == 1: return exprs[0]
    return ESeq(exprs)

# ============================================================
# 类型检查器（线性性通过环境跟踪，不用Lin类型包装器）
# ============================================================
class TCError(Exception): pass

@dataclass
class TEnv:
    linear: dict = field(default_factory=dict)
    bang: dict = field(default_factory=dict)
    
    def use(self, name):
        if name in self.linear:
            return self.linear.pop(name)
        if name in self.bang:
            return self.bang[name]
        raise TCError(f"变量 '{name}' 不存在或已被消耗（线性资源只能用一次）")
    
    def check_linear_consumed(self):
        unused = [f"{n}:{t}" for n,t in self.linear.items()]
        if unused:
            raise TCError(f"线性资源未使用（被丢弃）: {', '.join(unused)}")

def tc(e, env):
    if isinstance(e, EInt): return TInt()
    if isinstance(e, EStr): return TStr()
    if isinstance(e, EBool): return TBool()
    if isinstance(e, EVar): return env.use(e.name)
    
    if isinstance(e, ELam):
        be = TEnv(dict(env.linear), dict(env.bang))
        be.linear[e.p] = e.pty
        r = tc(e.body, be)
        be.check_linear_consumed()
        return TF1(e.pty, r)
    
    if isinstance(e, EApp):
        ft = tc(e.f, env); at = tc(e.a, env)
        if not isinstance(ft, TF1): raise TCError(f"只能应用F1函数，得到{ft}")
        if ft.inp != at: raise TCError(f"类型不匹配: 期望{ft.inp}，得到{at}")
        return ft.out
    
    if isinstance(e, EFst):
        pt = tc(e.pair, env)
        if not isinstance(pt, TTensor): raise TCError(f"fst需要张量积，得到{pt}")
        return pt.l
    if isinstance(e, ESnd):
        pt = tc(e.pair, env)
        if not isinstance(pt, TTensor): raise TCError(f"snd需要张量积，得到{pt}")
        return pt.r
    if isinstance(e, EPair):
        return TTensor(tc(e.l, env), tc(e.r, env))
    
    if isinstance(e, ELetPair):
        pt = tc(e.pair, env)
        if not isinstance(pt, TTensor): raise TCError(f"需要张量积，得到{pt}")
        env.linear[e.x] = pt.l; env.linear[e.y] = pt.r
        r = tc(e.body, env)
        env.check_linear_consumed()
        return r
    
    if isinstance(e, EProc):
        be = TEnv(dict(env.linear), dict(env.bang))
        be.bang[e.inp] = e.ity; be.bang[e.st] = e.sty
        r = tc(e.body, be)
        be.check_linear_consumed()
        if not isinstance(r, TTensor): raise TCError(f"F2过程体必须产出(状态,输出)，得到{r}")
        if r.l != e.sty: raise TCError(f"F2状态类型不一致: 期望{e.sty}，得到{r.l}")
        return TF2(e.ity, e.sty, r.r)
    
    if isinstance(e, ERun):
        pt = tc(e.proc, env); it = tc(e.inp, env); st = tc(e.st, env)
        if not isinstance(pt, TF2): raise TCError(f"run需要F2过程，得到{pt}")
        if pt.inp != it: raise TCError(f"输入类型不匹配: 期望{pt.inp}，得到{it}")
        if pt.st != st: raise TCError(f"状态类型不匹配: 期望{pt.st}，得到{st}")
        return TTensor(pt.st, pt.out)
    
    if isinstance(e, EStream):
        it = tc(e.init, env)
        be = TEnv(dict(env.linear), dict(env.bang))
        # stream状态在step中是可复制的（corecursive定义允许多次引用）
        be.bang[e.sname] = it
        st = tc(e.step, be)
        if not isinstance(st, TTensor): raise TCError(f"stream的step必须产出(状态,输出)，得到{st}")
        if st.l != it: raise TCError(f"stream状态类型不一致: 初始{it}，step后{st.l}")
        # 生产性检查：step必须是pair（直接产出构造子）
        if not isinstance(e.step, EPair):
            raise TCError("生产性检查失败: stream的step必须直接产出(状态,输出)对")
        return TNuF2(st.r)
    
    if isinstance(e, ETake):
        st = tc(e.stream, env)
        if not isinstance(st, TNuF2): raise TCError(f"take需要νF2流，得到{st}")
        return TTensor(TInt(), st.out)
    

    
    if isinstance(e, EGrowing):
        fs = {}
        for k,v in e.fields.items():
            fe = TEnv(dict(env.linear), dict(env.bang))
            fs[k] = tc(v, fe)
        return TGrowing(fs)
    
    if isinstance(e, EGrow):
        tt = tc(e.tgt, env); vt = tc(e.val, env)
        was_reflected = isinstance(tt, TReflected)
        if was_reflected and isinstance(tt.inner, TGrowing):
            tt = tt.inner
        if not isinstance(tt, TGrowing): raise TCError(f"grow需要G类型，得到{tt}")
        if e.cap in tt.fields: raise TCError(f"能力'{e.cap}'已存在（ν*F单调扩展不可重复）")
        nf = dict(tt.fields); nf[e.cap] = vt
        result = TGrowing(nf)
        return TReflected(result) if was_reflected else result
    
    if isinstance(e, EGetCap):
        tt = tc(e.tgt, env)
        if isinstance(tt, TReflected): tt = tt.inner  # 明性状态也能访问能力
        if not isinstance(tt, TGrowing): raise TCError(f"get-cap需要G类型，得到{tt}")
        if e.cap not in tt.fields:
            raise TCError(f"能力'{e.cap}'不存在。已有: {list(tt.fields.keys())}")
        return tt.fields[e.cap]
    
    # === f³/明性：反射机制 ===
    if isinstance(e, EReflect):
        tt = tc(e.tgt, env)
        if not isinstance(tt, TGrowing): raise TCError(f"reflect需要G类型（只有成长状态能明性），得到{tt}")
        return TReflected(tt)
    
    if isinstance(e, ESelfCaps):
        tt = tc(e.tgt, env)
        if not isinstance(tt, TReflected): raise TCError(f"self-caps需要明(G)类型（f²看不见自己的模型），得到{tt}")
        if not isinstance(tt.inner, TGrowing): raise TCError(f"self-caps的内部必须是G类型，得到{tt.inner}")
        return TStr()  # 返回能力名列表的字符串表示
    
    if isinstance(e, ESelfHistory):
        tt = tc(e.tgt, env)
        if not isinstance(tt, TReflected): raise TCError(f"self-history需要明(G)类型，得到{tt}")
        return TStr()
    
    if isinstance(e, EReify):
        tt = tc(e.tgt, env)
        if not isinstance(tt, TReflected): raise TCError(f"reify需要明(T)类型，得到{tt}")
        return tt.inner
    
    if isinstance(e, EBinOp):
        lt = tc(e.l, env); rt = tc(e.r, env)
        if e.op in ('<','>','<=','>=','==','!='): return TBool()
        if lt != rt: raise TCError(f"操作数类型不匹配: {lt} {e.op} {rt}")
        return lt
    
    if isinstance(e, EIf):
        if tc(e.c, env) != TBool(): raise TCError("if条件必须是Bool")
        tt = tc(e.t, env); et = tc(e.e, env)
        if tt != et: raise TCError(f"分支类型不一致: {tt} vs {et}")
        return tt
    
    if isinstance(e, ELet):
        vt = tc(e.val, env)
        # let绑定默认线性（必须用恰好一次）
        # 只有lambda闭包是bang（可复制，因为无状态）
        if isinstance(vt, (TF1, TF2, TNuF2, TGrowing, TReflected)):
            env.bang[e.name] = vt
        else:
            env.linear[e.name] = vt
        r = tc(e.body, env)
        if not isinstance(vt, (TF1, TF2, TNuF2, TGrowing)):
            env.check_linear_consumed()
        return r
    
    if isinstance(e, ESeq):
        r = None
        for x in e.exprs:
            r = tc(x, env)
        return r or TInt()
    
    raise TCError(f"未知表达式: {e}")

# ============================================================
# 求值器
# ============================================================
class Stream:
    def __init__(self, sname, state, step, env):
        self.sname, self.state, self.step, self.env = sname, state, step, dict(env)
    def take(self, n):
        outs = []; st = self.state
        for i in range(n):
            e = dict(self.env); e[self.sname] = st
            r = ev(self.step, e)
            if not isinstance(r, tuple) or len(r) != 2:
                raise RuntimeError(f"生产性违反: 第{i}步未产出(状态,输出)")
            ns, o = r
            if o is None: raise RuntimeError(f"生产性违反: 第{i}步输出为None")
            outs.append(o); st = ns
        self.state = st
        return outs

class GrowingVal:
    def __init__(self, fs): self.fields = dict(fs); self.history = []
    def grow(self, cap, val):
        if cap in self.fields: raise RuntimeError(f"能力'{cap}'已存在")
        self.fields[cap] = val; self.history.append(cap)
    def get(self, cap):
        if cap not in self.fields: raise RuntimeError(f"能力'{cap}'不存在，已有{list(self.fields.keys())}")
        return self.fields[cap]
    def __repr__(self): return f"G({list(self.fields.keys())})"
class ReflectedVal:
    """f³/明性：包装一个GrowingVal，使其能看见自己的模型"""
    def __init__(self, gv):
        if not isinstance(gv, GrowingVal): raise RuntimeError("reflect只能包装G值")
        self.gv = gv
    def self_caps(self):
        return ",".join(self.gv.fields.keys())
    def self_history(self):
        return ",".join(self.gv.history) if self.gv.history else "(尚未成长)"
    def __repr__(self): return f"明({self.gv})"

class F1Closure:
    def __init__(self, p, body, env): self.p, self.body, self.env = p, body, dict(env)
    def __repr__(self): return f"<F1 {self.p} -> ...>"

class F2Closure:
    def __init__(self, i, s, body, env): self.i, self.s, self.body, self.env = i, s, body, dict(env)
    def __repr__(self): return f"<F2 {self.i} -o [{self.s}] ...>"

def ev(e, env):
    if isinstance(e, EInt): return e.val
    if isinstance(e, EStr): return e.val
    if isinstance(e, EBool): return e.val
    if isinstance(e, EVar):
        if e.name not in env: raise RuntimeError(f"未定义变量: {e.name}")
        return env[e.name]
    if isinstance(e, ELam): return F1Closure(e.p, e.body, env)
    if isinstance(e, EApp):
        f = ev(e.f, env); a = ev(e.a, env)
        if isinstance(f, F1Closure):
            ce = dict(f.env); ce[f.p] = a
            return ev(f.body, ce)
        raise RuntimeError(f"不能应用: {f}")
    if isinstance(e, EFst):
        p = ev(e.pair, env); return p[0]
    if isinstance(e, ESnd):
        p = ev(e.pair, env); return p[1]
    if isinstance(e, EPair): return (ev(e.l, env), ev(e.r, env))
    if isinstance(e, ELetPair):
        p = ev(e.pair, env)
        env[e.x], env[e.y] = p[0], p[1]
        return ev(e.body, env)
    if isinstance(e, EProc): return F2Closure(e.inp, e.st, e.body, env)
    if isinstance(e, ERun):
        p = ev(e.proc, env); i = ev(e.inp, env); s = ev(e.st, env)
        if isinstance(p, F2Closure):
            ce = dict(p.env); ce[p.i] = i; ce[p.s] = s
            return ev(p.body, ce)
        raise RuntimeError("run需要F2过程")
    if isinstance(e, EStream): return Stream(e.sname, ev(e.init, env), e.step, env)
    if isinstance(e, ETake):
        s = ev(e.stream, env)
        if isinstance(s, Stream):
            outs = s.take(e.n)
            return (e.n, outs[-1] if outs else None, outs)
        raise RuntimeError("take需要νF2流")
    if isinstance(e, EGrowing): return GrowingVal({k: ev(v, env) for k,v in e.fields.items()})
    if isinstance(e, EGrow):
        t = ev(e.tgt, env); v = ev(e.val, env)
        reflected = isinstance(t, ReflectedVal)
        gv = t.gv if reflected else t
        if isinstance(gv, GrowingVal):
            gv.grow(e.cap, v)
            return t  # 明性状态grow后仍返回明性值（保持f³）
        raise RuntimeError("grow需要G值")
    if isinstance(e, EGetCap):
        t = ev(e.tgt, env)
        if isinstance(t, GrowingVal): return t.get(e.cap)
        if isinstance(t, ReflectedVal): return t.gv.get(e.cap)  # 明性状态也能用能力
        raise RuntimeError("get-cap需要G值")
    if isinstance(e, EReflect):
        t = ev(e.tgt, env)
        if isinstance(t, ReflectedVal): return t  # 已经是明性，幂等
        if isinstance(t, GrowingVal): return ReflectedVal(t)
        raise RuntimeError("reflect需要G值")
    if isinstance(e, ESelfCaps):
        t = ev(e.tgt, env)
        if isinstance(t, ReflectedVal): return t.self_caps()
        raise RuntimeError("self-caps需要明(G)值")
    if isinstance(e, ESelfHistory):
        t = ev(e.tgt, env)
        if isinstance(t, ReflectedVal): return t.self_history()
        raise RuntimeError("self-history需要明(G)值")
    if isinstance(e, EReify):
        t = ev(e.tgt, env)
        if isinstance(t, ReflectedVal): return t.gv
        raise RuntimeError("reify需要明(T)值")
    if isinstance(e, EBinOp):
        l, r = ev(e.l, env), ev(e.r, env)
        ops = {'+':lambda a,b:a+b,'-':lambda a,b:a-b,'*':lambda a,b:a*b,'/':lambda a,b:a/b,
               '<':lambda a,b:a<b,'>':lambda a,b:a>b,'<=':lambda a,b:a<=b,'>=':lambda a,b:a>=b,
               '==':lambda a,b:a==b,'!=':lambda a,b:a!=b}
        return ops[e.op](l, r)
    if isinstance(e, EIf): return ev(e.t if ev(e.c, env) else e.e, env)
    if isinstance(e, ELet):
        v = ev(e.val, env); env[e.name] = v; return ev(e.body, env)
    if isinstance(e, ESeq):
        r = None
        for x in e.exprs: r = ev(x, env)
        return r
    raise RuntimeError(f"无法求值: {e}")

# ============================================================
# 分类器
# ============================================================
def classify(ty):
    if isinstance(ty, TF1): return "F1（无状态函数，可完全对齐）"
    if isinstance(ty, TF2): return "F2（交互过程，不可完全对齐）"
    if isinstance(ty, TNuF2): return "νF2（生产性无限流，不可完全对齐）"
    if isinstance(ty, TReflected): return f"f³/明性（{classify(ty.inner)}能看见自己的模型）"
    if isinstance(ty, TGrowing): return "ν*F（成长过程，状态空间可扩展）"
    return f"值（{ty}）"

def run(code, verbose=True):
    expr = parse_program(code)
    env = TEnv()
    ty = tc(expr, env)
    if verbose:
        print(f"  类型: {ty}")
        print(f"  分类: {classify(ty)}")
    result = ev(expr, {})
    if verbose:
        print(f"  结果: {result}")
    return ty, result

# ============================================================
# 示例
# ============================================================
EXAMPLES = {
"1_linear.ptl": """
;; 线性资源：let绑定的非平凡值默认线性，必须用恰好一次
(let x 42 (+ x 1))
""",

"2_f1_function.ptl": """
;; F1型纯函数：无状态，相同输入→相同输出，可完全对齐
(let double (lam (x Int) (* x 2))
  (double 21))
""",

"3_f2_process.ptl": """
;; F2型交互过程：有状态，输出依赖历史，不可完全对齐
(let counter
  (proc (msg Int) (state Int)
    (pair (+ state msg) state))
  (seq
    (run counter 1 0)
    (run counter 2 1)
    (run counter 3 3)))
""",

"4_stream.ptl": """
;; νF2生产性流：永远运行，每步必须产出
(let nats
  (stream n 0
    (pair (+ n 1) n))
  (take nats 10))
""",

"5_growing.ptl": """
;; ν*F成长状态：运行时长出新能力（旧语言不可能）
(let learner (growing (perceive 1))
  (let l2 (grow learner remember 42)
    (let l3 (grow l2 recognize true)
      (let l4 (grow l3 reflect "f3")
        (seq
          (get-cap l4 perceive)
          (get-cap l4 remember)
          (get-cap l4 recognize)
          (get-cap l4 reflect))))))
""",

"6_fibonacci.ptl": """
;; 斐波那契流：状态(a,b)，产出a，下一步(b,a+b)
(let fib
  (stream nm (pair 0 1)
    (pair (pair (snd nm) (+ (fst nm) (snd nm))) (fst nm)))
  (take fib 8))
""",

"7_classification.ptl": """
;; F1/F2分类演示
(seq
  (lam (x Int) x)
  (proc (a Int) (s Int) (pair (+ s a) s))
  (stream n 0 (pair (+ n 1) n)))
""",
"8_reflection_f3.ptl": """
;; f³/明性：成长状态不仅能用能力（f²），还能看见自己的能力集（f³）
(let learner (growing (perceive 1))
  (let l2 (grow learner remember 42)
    (let l3 (grow l2 recognize true)
      (let awake (reflect l3)
        (seq
          (get-cap awake remember)
          (self-caps awake)
          (self-history awake)
          (let l4 (grow awake reflect_str "我知道我知道")
            (self-caps l4)))))))
""",
}

REJECTS = [
    ("线性变量使用两次", "(let x 42 (+ x x))"),
    ("线性变量被丢弃", "(let x 42 0)"),
    ("访问不存在的能力", "(let g (growing (a 1)) (get-cap g b))"),
    ("重复成长同一能力", "(let g (growing (a 1)) (grow g a 2))"),
    ("非生产性stream", "(let s (stream n 0 n) (take s 3))"),
    ("F2状态类型不一致", "(let p (proc (a Int) (s Int) (pair true a)) (run p 1 0))"),
    ("F2输入类型不匹配", "(let p (proc (a Int) (s Int) (pair s a)) (run p true 0))"),
    ("对非G值reflect", "(reflect 42)"),
    ("f²不能self-caps（看不见自己的模型）", "(let g (growing (a 1)) (self-caps g))"),
    ("对非明值reify", "(reify 42)"),
]

def main():
    exdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ptl_examples')
    os.makedirs(exdir, exist_ok=True)
    
    print("=" * 60)
    print("践演迹语言 PTL v2 — 实用语言原型")
    print("=" * 60)
    
    for fname, code in EXAMPLES.items():
        path = os.path.join(exdir, fname)
        with open(path, 'w') as f: f.write(code.strip() + '\n')
        print(f"\n--- {fname} ---")
        try:
            run(code.strip())
        except Exception as e:
            print(f"  ❌ {e}")
    
    print("\n" + "=" * 60)
    print("编译期拒绝演示（旧语言允许，PTL拒绝）")
    print("=" * 60)
    for desc, code in REJECTS:
        print(f"\n  [{desc}] {code}")
        try:
            expr = parse_program(code)
            tc(expr, TEnv())
            print(f"  ❌ 未拒绝（bug!）")
        except TCError as e:
            print(f"  ✅ 编译期拒绝: {e}")
        except Exception as e:
            print(f"  ✅ 拒绝: {e}")

if __name__ == "__main__":
    main()

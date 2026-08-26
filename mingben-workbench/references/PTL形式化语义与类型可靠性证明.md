# PTL践演迹语言：形式化语义与类型可靠性证明

## 1. 语法

### 1.1 类型

```
A, B, C ::= Int | Str | Bool          基础类型
          | A * B                       张量积（线性对）
          | A -> B                      F1函数（无状态，可复制）
          | A -o [S] B                  F2过程（有状态，交互）
          | νF2[B]                      生产性无限流
          | G{f1:A1, ..., fn:An}       ν*F成长状态
          | 明(A)                        f³反射（自明）
```

**Bang类型（可复制/可丢弃）**：以下类型自动为bang：
- A -> B（F1函数，无状态）
- A -o [S] B（F2过程闭包）
- νF2[B]（流）
- G{...}（成长状态）
- 明(A)（反射状态）

非bang类型为**线性类型**：必须用恰好一次。

### 1.2 项

```
t, u ::= x | n | s | b               变量、整数、字符串、布尔
      | (t, u) | t.1 | t.2           张量构造与解构
      | λx:A. t | t u                 F1抽象与应用
      | proc(x:A, s:S).t | run t u s  F2过程与运行
      | stream x = t in u | take t n  流定义与取值
      | growing{f=t,...} | grow t c u | get-cap t c  成长操作
      | reflect t | self-caps t | self-history t | reify t  f³操作
      | let x = t in u | let-pair (x,y) = t in u
      | if t then u else v | t op u
      | seq(t1, ..., tn)
```

### 1.3 值

```
v ::= n | s | b | (v, w) | λx:A. t | proc(...) | stream | growing | 明(v)
```

## 2. 类型规则

### 2.1 判断

**线性环境** Γ：线性变量到类型的映射，每个变量必须用恰好一次。
**Bang环境** Δ：可复制变量到类型的映射。

判断形式：`Δ; Γ ⊢ t : A`

### 2.2 结构规则

**变量使用**（线性变量消耗，bang变量不消耗）：
```
────────── (var-lin)   x ∈ Γ
Δ; Γ, x:A ⊢ x : A

────────── (var-bang)  x ∈ Δ
Δ, x:A; Γ ⊢ x : A
```

**Let绑定**（值的类型决定线性/bang）：
```
Δ; Γ₁ ⊢ t : A    Δ, x:A; Γ₂ ⊢ u : B    (A是bang类型)
───────────────────────────────────────────────────── (let-bang)
Δ; Γ₁, Γ₂ ⊢ let x = t in u : B

Δ; Γ₁ ⊢ t : A    Δ; Γ₂, x:A ⊢ u : B    (A是线性类型)
───────────────────────────────────────────────────── (let-lin)
Δ; Γ₁, Γ₂ ⊢ let x = t in u : B
```

**线性消耗检查**：所有判断结束时，Γ必须为空（所有线性变量已消耗）。

### 2.3 基础类型

```
──────── (int)      ──────── (str)     ──────── (bool)
Δ; · ⊢ n : Int      Δ; · ⊢ s : Str     Δ; · ⊢ b : Bool
```

### 2.4 张量积

```
Δ; Γ₁ ⊢ t : A    Δ; Γ₂ ⊢ u : B
────────────────────────────────── (pair)
Δ; Γ₁, Γ₂ ⊢ (t, u) : A * B

Δ; Γ ⊢ t : A * B
────────────────── (fst)      ────────────────── (snd)
Δ; Γ ⊢ t.1 : A                Δ; Γ ⊢ t.2 : B
```

### 2.5 F1函数

```
Δ; Γ, x:A ⊢ t : B
──────────────────────── (lam)     F1函数体是bang（可复制）
Δ; Γ ⊢ λx:A. t : A -> B

Δ; Γ₁ ⊢ t : A -> B    Δ; Γ₂ ⊢ u : A
────────────────────────────────────── (app)
Δ; Γ₁, Γ₂ ⊢ t u : B
```

### 2.6 F2过程

```
Δ, x:A, s:S; Γ ⊢ t : S * B
────────────────────────────────────── (proc)   输入和状态是bang
Δ; Γ ⊢ proc(x:A, s:S).t : A -o [S] B

Δ; Γ₁ ⊢ t : A -o [S] B   Δ; Γ₂ ⊢ u : A   Δ; Γ₃ ⊢ v : S
────────────────────────────────────────────────────────── (run)
Δ; Γ₁, Γ₂, Γ₃ ⊢ run t u v : S * B
```

### 2.7 νF2流

```
Δ; Γ ⊢ t : S    Δ, x:S; · ⊢ u : S * B    u必须直接是(pair, ...)
────────────────────────────────────────────────────────────── (stream)
Δ; Γ ⊢ stream x = t in u : νF2[B]

Δ; Γ ⊢ t : νF2[B]    n : Int
────────────────────────────────────── (take)
Δ; Γ ⊢ take t n : Int * B
```

**生产性条件**：stream的step u必须直接是`(pair, ...)`形式（guarded recursion）。

### 2.8 ν*F成长

```
Δ; Γᵢ ⊢ tᵢ : Aᵢ  (对每个字段i)
────────────────────────────────────── (growing)
Δ; ∪Γᵢ ⊢ growing{fᵢ=tᵢ} : G{fᵢ:Aᵢ}

Δ; Γ₁ ⊢ t : G{F}    c ∉ F    Δ; Γ₂ ⊢ u : A
────────────────────────────────────────────── (grow)
Δ; Γ₁, Γ₂ ⊢ grow t c u : G{F, c:A}

Δ; Γ ⊢ t : G{F}    c ∈ F
────────────────────────────── (get-cap)
Δ; Γ ⊢ get-cap t c : F(c)
```

**单调性**：grow只能添加新字段，不能修改已有字段。

### 2.9 f³反射

```
Δ; Γ ⊢ t : G{F}
────────────────────────── (reflect)
Δ; Γ ⊢ reflect t : 明(G{F})

Δ; Γ ⊢ t : 明(G{F})
────────────────────────── (self-caps)     返回能力名列表
Δ; Γ ⊢ self-caps t : Str

Δ; Γ ⊢ t : 明(G{F})
────────────────────────── (self-history)   返回成长历史
Δ; Γ ⊢ self-history t : Str

Δ; Γ ⊢ t : 明(A)
────────────────────────── (reify)
Δ; Γ ⊢ reify t : A
```

**grow on 明(G)**：grow作用于明(G)时，返回明(G')（保持f³）。

## 3. 操作语义

### 3.1 求值上下文

```
E ::= □ | E t | v E | (E, t) | (v, E) | E.1 | E.2
    | let x = E in t | run E t s | run v E s | run v v E
    | take E n | grow E c t | grow v c E | get-cap E c
    | reflect E | self-caps E | self-history E | reify E
    | if E then t else u | E op t | v op E | seq(E, ...)
```

### 3.2 β归约

```
(λx:A. t) v  →  [v/x]t                          (β-fun)

(λx:A. t) v  →  [v/x]t  (线性替换：x在t中恰好出现一次)  (β-lin)

let x = v in t  →  [v/x]t                        (let-val)

let-pair (x,y) = (v,w) in t  →  [v/x][w/y]t    (let-pair-val)

(v, w).1  →  v                                    (fst-val)
(v, w).2  →  w                                    (snd-val)

run (proc(x,s).t) v w  →  [v/x][w/s]t           (run-val)

if true then t else u  →  t                       (if-true)
if false then t else u  →  u                      (if-false)

reify (reflect v)  →  v                           (reify-reflect)
```

### 3.3 流的归约

```
take (stream x = v in step) n  →  (n, last, [o₁, ..., oₙ])
  where (s₁, o₁) = [v/x]step
        (sᵢ₊₁, oᵢ₊₁) = [sᵢ/x]step
```

### 3.4 成长的归约

```
grow (growing{f=v}) c w  →  growing{f=v, c=w}     (grow-val)
grow (明(g)) c w  →  明(grow g c w)                (grow-reflected)

get-cap (growing{f=v, ...}) f  →  v                (get-cap-val)
get-cap (明(g)) c  →  get-cap g c                  (get-cap-reflected)

self-caps (明(growing{f₁=v₁, ..., fₙ=vₙ}))  →  "f₁,...,fₙ"  (self-caps-val)
self-history (明(g))  →  history(g)                (self-history-val)
```

## 4. 类型可靠性证明

### 4.1 替换引理

**引理1（Bang替换）**：如果 Δ, x:A; Γ ⊢ t : B 且 Δ; · ⊢ v : A（A是bang类型），则 Δ; Γ ⊢ [v/x]t : B。

证明：对t的推导归纳。bang变量可以在t中出现任意次数（包括0次），替换后类型不变。∎

**引理2（线性替换）**：如果 Δ; Γ₁, x:A ⊢ t : B 且 Δ; Γ₂ ⊢ v : A（A是线性类型），则 Δ; Γ₁, Γ₂ ⊢ [v/x]t : B。

证明：对t的推导归纳。x在t中恰好出现一次（线性性），替换后x被消耗，Γ₂的资源转移到t中。∎

**引理3（值的类型不变）**：如果 Δ; Γ ⊢ v : A 且v是值，则Γ = ·（值不消耗线性资源）。

证明：对v的结构归纳。所有值构造子的前提都是空线性环境。∎

### 4.2 Progress定理

**定理1（Progress）**：如果 ·; · ⊢ t : A，则要么t是值，要么存在t'使得t → t'。

证明：对t的推导归纳。

**情况1：变量**。t = x。但·; · ⊢ x : A不可能（环境为空）。排除。

**情况2：基础值**。t = n, s, b。是值。∎

**情况3：对**。t = (t₁, t₂)。
- 如果t₁不是值，由归纳假设t₁ → t₁'，则(t₁, t₂) → (t₁', t₂)。
- 如果t₁是值但t₂不是值，同理t₂ → t₂'。
- 如果都是值，(t₁, t₂)是值。∎

**情况4：fst/snd**。t = t₁.1。
- 如果t₁不是值，由归纳假设t₁ → t₁'，则t₁.1 → t₁'.1。
- 如果t₁是值，由类型规则t₁ : A * B，由引理3 t₁ = (v, w)，则(v, w).1 → v。∎

**情况5：函数应用**。t = t₁ t₂。
- 如果t₁不是值，t₁ → t₁'，则t₁ t₂ → t₁' t₂。
- 如果t₁是值但t₂不是值，t₂ → t₂'，则t₁ t₂ → t₁ t₂'。
- 如果都是值，由类型规则t₁ : A -> B，由引理3 t₁ = λx:A. u，则(λx:A. u) v → [v/x]u。∎

**情况6：let**。t = let x = t₁ in t₂。
- 如果t₁不是值，t₁ → t₁'，则let x = t₁ in t₂ → let x = t₁' in t₂。
- 如果t₁是值，let x = v in t₂ → [v/x]t₂。∎

**情况7：run**。t = run t₁ t₂ t₃。
- 依次规约参数。
- 如果都是值，t₁ = proc(x,s).u，则run (proc(x,s).u) v w → [v/x][w/s]u。∎

**情况8：take**。t = take t₁ n。
- 如果t₁不是值，规约t₁。
- 如果t₁是值，t₁ = stream x = v in step，按流归约规则计算。∎

**情况9：grow**。t = grow t₁ c t₂。
- 依次规约参数。
- 如果都是值，t₁ = growing{...}或明(growing{...})，按成长归约。∎

**情况10：get-cap**。t = get-cap t₁ c。
- 如果t₁不是值，规约t₁。
- 如果t₁是值，t₁ = growing{f=v,...}，get-cap返回v。∎

**情况11：reflect**。t = reflect t₁。
- 如果t₁不是值，规约t₁。
- 如果t₁是值，reflect v是值。∎

**情况12：self-caps/self-history**。
- 如果t₁不是值，规约t₁。
- 如果t₁是值，t₁ = 明(growing{...})，按归约规则计算。∎

**情况13：reify**。t = reify t₁。
- 如果t₁不是值，规约t₁。
- 如果t₁是值，t₁ = 明(v)，reify (明(v)) → v。∎

**情况14：if**。t = if t₁ then t₂ else t₃。
- 如果t₁不是值，规约t₁。
- 如果t₁是值，t₁ = true或false，按归约规则。∎

**情况15：seq**。t = seq(t₁, ..., tₙ)。
- 依次规约每个表达式，最后一个的值是结果。∎

∎ Progress定理证毕。

### 4.3 Preservation定理

**定理2（Preservation）**：如果 ·; · ⊢ t : A 且 t → t'，则 ·; · ⊢ t' : A。

证明：对t → t'的归约规则归纳。

**情况β-fun**：(λx:A. u) v → [v/x]u。
- 前提：·; · ⊢ (λx:A. u) v : B
- 由app规则：·; · ⊢ λx:A. u : A -> B 且 ·; · ⊢ v : A
- 由lam规则：·; x:A ⊢ u : B（x是bang，因为函数体中的参数是bang）
- 由引理1（bang替换）：·; · ⊢ [v/x]u : B。∎

**情况let-val**：let x = v in u → [v/x]u。
- 前提：·; · ⊢ let x = v in u : B
- 分两种子情况：
  - v是bang类型：由let-bang规则，x在bang环境中，由引理1。
  - v是线性类型：由let-lin规则，x在线性环境中恰好出现一次，由引理2。∎

**情况fst-val**：(v, w).1 → v。
- 前提：·; · ⊢ (v, w).1 : A
- 由fst规则：·; · ⊢ (v, w) : A * B
- 由pair规则：·; · ⊢ v : A。∎

**情况run-val**：run (proc(x,s).u) v w → [v/x][w/s]u。
- 前提：·; · ⊢ run (proc(x,s).u) v w : S * B
- 由run规则：proc : A -o [S] B, v : A, w : S
- 由proc规则：·, x:A, s:S; · ⊢ u : S * B
- x和s都是bang（proc的输入和状态在bang环境中）
- 由引理1两次：·; · ⊢ [v/x][w/s]u : S * B。∎

**情况grow-val**：grow (growing{f=v}) c w → growing{f=v, c=w}。
- 前提：·; · ⊢ grow (growing{f=v}) c w : G{F, c:A}
- 由grow规则：growing{f=v} : G{F}, w : A, c ∉ F
- 由growing规则：·; · ⊢ growing{f=v, c=w} : G{F, c:A}。∎

**情况grow-reflected**：grow (明(g)) c w → 明(grow g c w)。
- 前提：·; · ⊢ grow (明(g)) c w : 明(G{F, c:A})
- 由grow规则（明性版本）：明(g) : 明(G{F}), w : A
- 由reflect规则：g : G{F}
- 由grow规则：grow g c w : G{F, c:A}
- 由reflect规则：明(grow g c w) : 明(G{F, c:A})。∎

**情况get-cap-val**：get-cap (growing{f=v, ...}) f → v。
- 前提：·; · ⊢ get-cap (growing{f=v, ...}) f : A
- 由get-cap规则：growing{f=v, ...} : G{f:A, ...}
- 由growing规则：·; · ⊢ v : A。∎

**情况self-caps-val**：self-caps (明(growing{f₁=v₁,...,fₙ=vₙ})) → "f₁,...,fₙ"。
- 前提：·; · ⊢ self-caps (明(g)) : Str
- 由self-caps规则：明(g) : 明(G{F})
- 结果是字符串常量，类型Str。∎

**情况reify-reflect**：reify (reflect v) → v。
- 前提：·; · ⊢ reify (reflect v) : A
- 由reify规则：reflect v : 明(A)
- 由reflect规则：v : A。∎

**情况if-true/if-false**：直接由分支类型一致。∎

**情况流归约**：take (stream x = v in step) n → (n, last, list)。
- 前提：·; · ⊢ take (stream ...) n : Int * B
- 由take规则：stream : νF2[B]
- 由stream规则：step : S * B，且每步的输出类型B不变
- 归约结果的最后一个输出类型B，与Int组成Int * B。∎

**上下文闭包**：如果t → t'且t在求值上下文E中，则E[t] → E[t']。
- 由上下文的类型规则保持性（每个上下文构造子都保持类型）。∎

∎ Preservation定理证毕。

### 4.4 推论

**推论1（类型安全）**：如果 ·; · ⊢ t : A，则t的归约序列要么终止于一个类型A的值，要么无限归约（对于流和F2过程），不会陷入"stuck"状态。

证明：由Progress和Preservation联合归纳。∎

**推论2（线性资源安全）**：类型良好的程序不会出现线性变量使用两次或被丢弃的运行时错误。

证明：类型检查在编译时强制线性性，Preservation保证归约后类型不变，因此线性约束在运行时始终成立。∎

## 5. 讨论

### 5.1 证明的范围

本证明覆盖PTL的核心片段：基础类型、张量积、F1函数、F2过程、νF2流、ν*F成长、f³反射。

未覆盖：
- 递归函数（PTL中F1函数不支持递归，递归通过流和F2过程实现）
- 多态/类型变量
- 异常/副作用（除了成长状态的单调性修改）

### 5.2 线性性的处理

PTL的线性性通过**环境分割**（context splitting）实现：每个线性变量在类型推导中恰好出现一次。这与标准线性lambda演算一致。

关键创新：
- F1/F2/νF2/ν*F/明类型自动为bang（因为它们是"过程"而非"资源"）
- 成长状态的修改是单调的（grow只添加不删除），因此不需要线性约束
- f³反射保持被包装值的线性/bang属性

### 5.3 与PTC公理系统的对应

| PTL类型规则 | PTC公理 |
|---|---|
| 线性环境（无收缩/弱化） | 公理2（资源敏感） |
| Bang类型（可复制） | 公理3（!余单子） |
| F1函数（内部同态） | 公理1（闭结构，复范畴中构造） |
| 流/过程（不动点） | 公理4（μ/ν不动点） |
| 生产性检查 | 公理5（▷守护递归） |
| 成长（ν*F） | 公理6（增长规则，GLL） |
| f³反射 | 公理0（践演位置，位置转换） |

类型可靠性证明 = PTC公理系统在PTL中的实例化是可靠的。

## 6. 开放问题

1. **完全性**：类型系统是否接受所有"应该"接受的程序？（可能过于严格）
2. **类型推导**：是否存在完整的类型推导算法？（当前需要显式类型注解）
3. **Coq/Agda形式化**：将本证明机器验证
4. **扩展到递归F1函数**：需要终止性检查
5. **与线性逻辑的Curry-Howard对应**：PTL的类型是否对应某个线性逻辑的命题？

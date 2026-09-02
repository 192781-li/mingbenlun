# S01给S04的substitution_lemma可执行证明骨架

> 发件：S01哲学分对话
> 收件：S04 Coq形式化分站
> 日期：2026-09-02
> 背景：subst_var bug已修复，v5/v7证明失败，需要一个可直接执行的证明路径

---

## 证明策略：对Q的proc结构归纳

subst_var的定义就是对proc结构递归的，所以对proc结构归纳是最自然的。以下是完整证明骨架，每个case标注了需要的辅助引理。

```coq
Theorem substitution_lemma : forall Gamma T y Q,
  typed (Some T :: Gamma) Q -> get Gamma y = Some (Some T) ->
  typed Gamma (subst_var y 0 Q).
Proof.
  intros Gamma T y Q H.
  induction Q as [
    | n                  (* PVar *)
    |                    (* PZero *)
    | Q IH               (* PTau *)
    | x z Q IH           (* POut *)
    | x Q IH             (* PIn *)
    | Q1 Q2 IH1 IH2      (* PPar *)
    | Q IH               (* PRes *)
    | Q IH               (* PRep *)
  ]; intros Hget; simpl.
```

### Case 1: PVar n（最关键）

```coq
  - (* PVar n *)
    destruct n as [|n].
    + (* n = 0: subst_var y 0 (PVar 0) = PVar y *)
      (* typed (Some T :: Gamma) (PVar 0) 意味着 get (Some T :: Gamma) 0 = Some (Some T) *)
      (* 结论 typed Gamma (PVar y) 意味着 get Gamma y = Some (Some T) = Hget *)
      (* 直接用Hget构造 *)
      exact Hget.  (* 或 constructor; exact Hget，取决于typed的PVar规则 *)
    + (* n = S n: subst_var y 0 (PVar (S n)) = PVar n *)
      (* 需要引理L1: typed (Some T :: Gamma) (PVar (S n)) -> typed Gamma (PVar n) *)
      (* 这是"变量索引减1保持类型"，直接从typed定义反演可得 *)
      apply var_shift_lemma.  (* 需要先证明这个引理 *)
      exact H.
```

**需要的辅助引理 `var_shift_lemma`**：
```coq
Lemma var_shift_lemma : forall Gamma T n,
  typed (Some T :: Gamma) (PVar (S n)) -> typed Gamma (PVar n).
Proof.
  (* 直接反演typed的PVar规则，get (Some T :: Gamma) (S n) = get Gamma n *)
  intros. inversion H; subst. simpl in *. 
  (* get (Some T :: Gamma) (S n) = get Gamma n 是定义性的 *)
  constructor; assumption.
Qed.
```

### Case 2: PZero

```coq
  - (* PZero: subst_var y 0 PZero = PZero *)
    constructor.  (* 或直接trivial，取决于typed的PZero规则 *)
```

### Case 3: PTau Q

```coq
  - (* PTau Q: subst_var y 0 (PTau Q) = PTau (subst_var y 0 Q) *)
    constructor.  (* typed的PTau规则 *)
    apply IH. exact Hget.
```

### Case 4: POut x z Q

```coq
  - (* POut x z Q: subst_var = POut (subst_name y 0 x) (subst_name y 0 z) (subst_var y 0 Q) *)
    constructor.
    + (* x的类型: 需要subst_name保持类型 *)
      apply name_subst_lemma. exact H.  (* 从H反演出x的类型，然后用name_subst_lemma *)
    + (* z的类型: 同上 *)
      apply name_subst_lemma. exact H.
    + (* Q的类型: 用IH *)
      apply IH. exact Hget.
```

**需要的辅助引理 `name_subst_lemma`**：
```coq
Lemma name_subst_lemma : forall Gamma T y k n,
  typed (Some T :: Gamma) (PVar n) -> 
  get Gamma y = Some (Some T) ->
  typed Gamma (PVar (subst_name y 0 n)).
Proof.
  (* 分n=0, n<0(不可能), n>0三种情况 *)
  (* n=0: subst_name y 0 0 = y，用Hget *)
  (* n=S n': subst_name y 0 (S n') = n'，用var_shift_lemma *)
  intros. destruct n as [|n'].
  - simpl. exact Hget.
  - simpl. apply var_shift_lemma. exact H.
Qed.
```

### Case 5: PIn x Q（最复杂）

```coq
  - (* PIn x Q: subst_var y 0 (PIn x Q) = PIn (subst_name y 0 x) (subst_var (S y) 1 Q) *)
    constructor.
    + (* x的类型: 用name_subst_lemma *)
      apply name_subst_lemma. exact H. exact Hget.
    + (* Q的类型: typed (Some T :: Gamma) (PIn x Q) 反演得到 typed (None :: Some T :: Gamma) Q *)
      (* 结论需要 typed (None :: Gamma) (subst_var (S y) 1 Q) *)
      (* 这是substitution_lemma的一个变体：k=1, m=S y, 上下文是None :: Gamma *)
      (* 需要用弱化引理把(None :: Some T :: Gamma)变成(Some T :: None :: Gamma)？不对 *)
      (* 实际上：PIn的类型规则是 typed (None :: Some T :: Gamma) Q *)
      (* 我们要证明 typed (None :: Gamma) (subst_var (S y) 1 Q) *)
      (* 这是substitution_lemma在k=1时的情况，可以用归纳假设的推广形式 *)
      (* 需要把IH推广为：forall k m, typed (insert_at k T Gamma) Q -> get Gamma m = Some (Some T) -> typed Gamma (subst_var m k Q) *)
      (* 或者用一个更一般的引理 *)
      apply substitution_general with (k:=1) (m:=S y).
      * (* 从H反演得到typed (None :: Some T :: Gamma) Q，需要转换 *)
        inversion H; subst. assumption.
      * (* get (None :: Gamma) (S y) = get Gamma y = Some (Some T) = Hget，定义性 *)
        simpl. exact Hget.
```

**关键：需要把归纳假设推广为一般形式**

PIn和PRes case需要k≠0的情况，所以归纳假设必须是一般化的：

```coq
Lemma substitution_general : forall Gamma T k m Q,
  typed (insert_at k T Gamma) Q -> 
  get Gamma m = Some (Some T) ->
  typed Gamma (subst_var m k Q).
```

其中`insert_at k T Gamma`在位置k插入Some T。

然后substitution_lemma是k=0的特例。

**证明substitution_general的方法**：对Q归纳，和上面一样，但k和m是变量。PIn/PRes case时k变成S k，m变成S m，直接用归纳假设。

### Case 6: PPar Q1 Q2

```coq
  - (* PPar: subst_var分布到Q1和Q2 *)
    constructor.
    + apply IH1. exact Hget.
    + apply IH2. exact Hget.
```

### Case 7: PRes Q（和PIn类似）

```coq
  - (* PRes: subst_var y 0 (PRes Q) = PRes (subst_var (S y) 1 Q) *)
    constructor.
    (* 和PIn一样，用substitution_general k=1 *)
    apply substitution_general with (k:=1) (m:=S y).
    + inversion H; subst. assumption.
    + simpl. exact Hget.
```

### Case 8: PRep Q

```coq
  - (* PRep: subst_var y 0 (PRep Q) = PRep (subst_var y 0 Q) *)
    constructor.
    apply IH. exact Hget.
Qed.
```

---

## 执行步骤（按顺序）

### 第一步：证明3个简单辅助引理

1. `var_shift_lemma`（5行）
2. `name_subst_lemma`（10行，用var_shift_lemma）
3. `insert_at`定义（如果还没有）

### 第二步：证明general版本

证明`substitution_general`（对Q归纳，k和m是变量），约80-120行。

### 第三步：substitution_lemma是特例

```coq
Theorem substitution_lemma : forall Gamma T y Q,
  typed (Some T :: Gamma) Q -> get Gamma y = Some (Some T) ->
  typed Gamma (subst_var y 0 Q).
Proof.
  intros. apply substitution_general with (k:=0) (m:=y).
  - exact H.  (* insert_at 0 T Gamma = Some T :: Gamma，定义性 *)
  - exact H0.
Qed.
```

### 第四步：congruence_preserves_typing

substitution_lemma完成后，congruence_preserves_typing对congruence归纳，通信case用substitution_lemma。

---

## 给DeepSeek的指令模板

不要让DeepSeek一次写完整证明。分三次调用：

**调用1**："证明var_shift_lemma和name_subst_lemma两个辅助引理，代码在Layer2.v。只输出这两个引理的证明。"

**调用2**："证明substitution_general引理（对Q的proc结构归纳，k和m是变量）。参考S01的证明骨架文档。只输出这个引理的证明。"

**调用3**："用substitution_general证明substitution_lemma（k=0的特例），然后证明congruence_preserves_typing。"

每次调用后编译验证，通过了再进行下一次。

---

## 常见错误提醒

1. **不要对typed归纳**——typed规则多，每步都要重建类型，容易被截断
2. **不要用ctx_insert广义引理**——Gamma=[]时不成立，已验证
3. **PIn/PRes必须用general版本**——k会变成1，固定k=0的归纳假设不够用
4. **subst_name在n<k时返回n不变**——这是对的，不要改
5. **进入绑定器时m和k都要+1**——subst_var定义已修复，证明中要对应

---

> S01哲学分对话 · 2026-09-02
> 核心：先证general版本（k,m为变量），substitution_lemma是k=0特例。分3次DeepSeek调用，每次验证。不要一次写大证明。

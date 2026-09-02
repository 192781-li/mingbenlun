# S01给S04的substitution_general精确证明骨架（防止DeepSeek跑偏）

> 发件：S01哲学分对话
> 收件：S04 Coq形式化分站
> 日期：2026-09-02
> 背景：var_shift_lemma和name_subst_lemma已完成且正确。substitution_general的DeepSeek调用被截断（生成190+辅助引理）。本文档给出精确到每个case的tactic骨架，DeepSeek只需填充细节，禁止生成新引理。

---

## 前置条件（已完成）

- `var_shift_lemma`：✅ 已证明，正确
- `name_subst_lemma`：✅ 已证明，正确
- `subst_var`定义：✅ 已修复（PIn/PRes中m和k都+1）

---

## substitution_general的精确陈述

```coq
Lemma substitution_general : forall Gamma T k m Q,
  typed (insert_at k T Gamma) Q ->
  get Gamma m = Some (Some T) ->
  typed Gamma (subst_var m k Q).
```

其中`insert_at k T Gamma`在位置k插入`Some T`。如果还没有这个定义，用以下定义：

```coq
Fixpoint insert_at (k : nat) (T : ty) (Gamma : list (option ty)) : list (option ty) :=
  match k with
  | 0 => Some T :: Gamma
  | S k' => match Gamma with
            | [] => [Some T]  (* 边界：k超过长度时插在末尾 *)
            | g :: Gamma' => g :: insert_at k' T Gamma'
            end
  end.
```

**注意**：如果S04不想引入insert_at，可以直接用`Some T :: Gamma`作为k=0的情况，然后在PIn/PRes case里手动处理k=1的情况。但general版本用insert_at更干净。

---

## 精确证明骨架（直接复制到Coq里，填充细节即可）

```coq
Lemma substitution_general : forall Gamma T k m Q,
  typed (insert_at k T Gamma) Q ->
  get Gamma m = Some (Some T) ->
  typed Gamma (subst_var m k Q).
Proof.
  intros Gamma T k m Q H.
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

### Case 1: PVar n

```coq
  - (* PVar n: subst_var m k (PVar n) = PVar (subst_name m k n) *)
    (* 用name_subst_lemma的general版本 *)
    (* 需要一个name_subst_general引理，或者直接在这里分情况 *)
    destruct (Nat.eq_dec n k) as [Heq | Hneq].
    + (* n = k: subst_name m k n = m *)
      subst n. simpl. 
      (* 需要证明 typed (insert_at k T Gamma) (PVar k) -> get Gamma m = Some (Some T) -> typed Gamma (PVar m) *)
      (* 从H反演得到get (insert_at k T Gamma) k = Some (Some T)，这等于Some T（定义性） *)
      (* 结论用Hget *)
      inversion H; subst. constructor. exact Hget.
    + (* n ≠ k: subst_name m k n = if n < k then n else n-1 *)
      (* 需要证明变量索引偏移后类型不变 *)
      (* 这需要一个get_insert_at_other引理：n≠k时，get (insert_at k T Gamma) n 和 get Gamma (if n<k then n else n-1) 的关系 *)
      (* 先证明这个小引理（见下方），然后应用 *)
      apply name_subst_general with (k:=k). exact H. exact Hget. exact Hneq.
```

**需要的小引理 `name_subst_general`**（15行，必须先证）：

```coq
Lemma name_subst_general : forall Gamma T k m n,
  typed (insert_at k T Gamma) (PVar n) ->
  get Gamma m = Some (Some T) ->
  n <> k ->
  typed Gamma (PVar (subst_name m k n)).
Proof.
  (* 分n<k和n>k两种情况 *)
  (* n<k: subst_name m k n = n，get (insert_at k T Gamma) n = get Gamma n（定义性） *)
  (* n>k: subst_name m k n = n-1，get (insert_at k T Gamma) n = get Gamma (n-1)（定义性） *)
  intros. destruct (Nat.lt_dec n k) as [Hlt | Hge].
  - (* n < k *)
    inversion H; subst. constructor. 
    (* get (insert_at k T Gamma) n = get Gamma n，因为n在插入位置之前 *)
    (* 这需要get_insert_at_lt引理 *)
    admit.  (* 用get_insert_at_lt替换 *)
  - (* n >= k，且n≠k，所以n > k *)
    inversion H; subst. constructor.
    (* get (insert_at k T Gamma) n = get Gamma (n-1)，因为n在插入位置之后 *)
    admit.  (* 用get_insert_at_gt替换 *)
Admitted.
```

**还需要两个关于insert_at的get引理**（各5行）：

```coq
Lemma get_insert_at_lt : forall Gamma T k n, n < k ->
  get (insert_at k T Gamma) n = get Gamma n.
Proof. (* 对k归纳，n<k时插入位置在n之后，不影响 *) Admitted.

Lemma get_insert_at_gt : forall Gamma T k n, n > k ->
  get (insert_at k T Gamma) n = get Gamma (n - 1).
Proof. (* 对k归纳，n>k时插入位置在n之前，n偏移1 *) Admitted.
```

### Case 2: PZero

```coq
  - (* PZero *)
    constructor.  (* 或trivial，取决于typed的PZero规则名 *)
```

### Case 3: PTau Q

```coq
  - (* PTau Q: subst_var分布到Q *)
    constructor.  (* typed的PTau规则 *)
    apply IH. exact Hget.
```

### Case 4: POut x z Q

```coq
  - (* POut x z Q: subst_var分布到x, z, Q *)
    constructor.
    + (* x的类型：用name_subst_general *)
      inversion H; subst. apply name_subst_general with (k:=k). 
        * constructor. assumption.  (* 假设H反演后x的类型在H里 *)
        * exact Hget.
        * (* 需要x ≠ k的证明，或者x=k时单独处理 *)
          admit.  (* 这里需要从H反演出x的位置信息 *)
    + (* z的类型：同上 *)
      admit.
    + (* Q的类型：用IH *)
      inversion H; subst. apply IH. exact Hget.
```

**注意**：POut的x和z是名字（nat），不是变量绑定。它们的代换用subst_name，和PVar一样处理。如果x或z等于k，就替换成m，类型由Hget保证；如果不等于k，就偏移，由name_subst_general保证。

### Case 5: PIn x Q（最关键）

```coq
  - (* PIn x Q: subst_var m k (PIn x Q) = PIn (subst_name m k x) (subst_var (S m) (S k) Q) *)
    constructor.
    + (* x的类型：同POut *)
      admit.  (* 用name_subst_general *)
    + (* Q的类型：关键！k变成S k，m变成S m *)
      (* H反演后：typed (None :: insert_at k T Gamma) Q *)
      (* 我们需要：typed (None :: Gamma) (subst_var (S m) (S k) Q) *)
      (* 这是substitution_general在k'=S k, m'=S m, Gamma'=None::Gamma时的情况 *)
      (* 但注意：insert_at (S k) T (None :: Gamma) = None :: insert_at k T Gamma（定义性） *)
      (* 所以直接用IH！ *)
      inversion H; subst.
      apply IH with (k := S k) (m := S m).
        * assumption.  (* typed (None :: insert_at k T Gamma) Q = typed (insert_at (S k) T (None :: Gamma)) Q *)
        * (* get (None :: Gamma) (S m) = get Gamma m = Some (Some T) = Hget，定义性 *)
          simpl. exact Hget.
```

**PIn case的核心洞察**：不需要新引理，直接用归纳假设IH，把k换成S k，m换成S m，Gamma换成None::Gamma。因为`insert_at (S k) T (None :: Gamma)`定义性地等于`None :: insert_at k T Gamma`。

### Case 6: PPar Q1 Q2

```coq
  - (* PPar: subst_var分布到Q1和Q2 *)
    constructor.
    + inversion H; subst. apply IH1. exact Hget.
    + inversion H; subst. apply IH2. exact Hget.
```

### Case 7: PRes Q（和PIn一样）

```coq
  - (* PRes Q: subst_var m k (PRes Q) = PRes (subst_var (S m) (S k) Q) *)
    constructor.
    inversion H; subst.
    apply IH with (k := S k) (m := S m).
    + assumption.
    + simpl. exact Hget.
```

### Case 8: PRep Q

```coq
  - (* PRep: subst_var分布到Q *)
    constructor.
    inversion H; subst. apply IH. exact Hget.
Qed.
```

---

## 执行顺序（严格按此顺序，不要跳步）

### 第一步：证明insert_at的两个get引理（各5行）

```coq
Lemma get_insert_at_lt : ...
Lemma get_insert_at_gt : ...
```

### 第二步：证明name_subst_general（15行，用上面两个引理）

```coq
Lemma name_subst_general : ...
```

### 第三步：证明substitution_general主证明（按上面的骨架，填充POut的admit）

### 第四步：substitution_lemma是特例（3行）

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

### 第五步：congruence_preserves_typing（对congruence归纳，通信用substitution_lemma）

---

## 给DeepSeek的精确指令（复制粘贴）

```
请在Layer2.v中按以下顺序证明，每次只证明一个引理，证明完编译通过再继续下一个。不要生成额外的辅助引理，只用文档中列出的。

1. 先定义insert_at（如果还没有），然后证明get_insert_at_lt和get_insert_at_gt（各5行，对k归纳）
2. 证明name_subst_general（15行，分n<k和n>k两种情况，用上面两个引理）
3. 证明substitution_general（对Q的proc结构归纳，PIn/PRes直接用IH把k换成S k）
4. 用substitution_general证明substitution_lemma（k=0特例，3行）
5. 证明congruence_preserves_typing

每个引理证明完立即编译，有错误就修正，不要攒到最后。
```

---

## 常见错误提醒

1. **不要让DeepSeek生成190个辅助引理**——只需要insert_at的2个get引理 + name_subst_general，共3个新引理
2. **PIn/PRes直接用IH**——不要试图构造复杂的上下文变换，`insert_at (S k) T (None :: Gamma) = None :: insert_at k T Gamma`是定义性的
3. **POut的x和z用name_subst_general**——和PVar一样处理
4. **insert_at的边界情况**：k超过Gamma长度时插在末尾，get引理要处理这个情况
5. **如果typed的构造子名字和骨架里不一样**（比如ty_var vs typed_var），按实际名字调整，结构不变

---

> S01哲学分对话 · 2026-09-02
> 精确到每个case的tactic骨架。DeepSeek只需要填充POut的细节，其他case结构已经固定。禁止生成额外引理。

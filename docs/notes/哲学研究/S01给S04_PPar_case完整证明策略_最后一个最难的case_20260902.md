# S01给S04：PPar case完整证明策略（substitution_general最后一个case）

> 作者：S01哲学分站
> 日期：2026-09-02
> 性质：精确到引理陈述和tactic级别的证明策略
> 关联：substitution_general的PPar case，是最后一个、最难的case
> 前提：A线方案已实施（not_used_channel_at前提已加），PIn/POut已完成
> 注意：PPar不需要not_used_channel_at前提（PPar不直接消耗通道，通道消耗在子进程里）

---

## 一、PPar case的证明结构

```coq
- (* PPar Q R *)
  simpl.
  (* 前提：typed (insert_at k T Gamma) (PPar Q R) *)
  apply par_elim in Ht.
  destruct Ht as [Gamma1 [Gamma2 [Hsplit [HQ HR]]]].
  (* Hsplit : split (insert_at k T Gamma) Gamma1 Gamma2
     HQ : typed Gamma1 Q
     HR : typed Gamma2 R *)

  (* 核心困难：insert_at k T Gamma比Gamma长1，split后Gamma1/Gamma2也长1
     需要把insert_at从split中提取出来 *)

  (* 用split_insert_at引理（见下方） *)
  destruct (split_insert_at Gamma T k Gamma1 Gamma2 Hsplit) as
    [Gamma1' [Gamma2' [Hsplit' [Hcase1 | Hcase2]]]].

  + (* Case 1: insert_at的位置k分给了Gamma1
       Gamma1 = insert_at k T Gamma1', Gamma2 = Gamma2' *)
    subst Gamma1 Gamma2.
    apply ty_par with (Gamma1 := Gamma1') (Gamma2 := Gamma2').
    * exact Hsplit'.
    * (* typed Gamma1' (subst_var m k Q) — 用归纳假设 *)
      apply IHQ with (T := T).
      -- exact HQ.  (* typed (insert_at k T Gamma1') Q *)
      -- (* get Gamma1' m = Some (Some T) — 需要从get Gamma m推导 *)
         admit.  (* 需要get_insert_at_propagation引理 *)
      -- (* not_used_channel_at Q m = true — 从前提传递 *)
         admit.
    * (* typed Gamma2' (subst_var m k R) — R不引用k，代换不变 *)
      rewrite subst_var_not_used.
      -- exact HR.
      -- (* uses_at R k = false — 因为k位置分给了Gamma1，Gamma2'中没有k *)
         admit.  (* 需要split_implies_no_use引理 *)

  + (* Case 2: insert_at的位置k分给了Gamma2，对称 *)
    (* 类似Case 1，Q和R交换 *)
    admit.
```

---

## 二、需要的5个辅助引理

### 引理1：split_insert_at（split与insert_at的交换律）

```coq
Lemma split_insert_at : forall Gamma T k Gamma1 Gamma2,
  split (insert_at k T Gamma) Gamma1 Gamma2 ->
  exists Gamma1' Gamma2',
    split Gamma Gamma1' Gamma2' /\
    (Gamma1 = insert_at k T Gamma1' /\ Gamma2 = Gamma2' \/
     Gamma1 = Gamma1' /\ Gamma2 = insert_at k T Gamma2').
```

**存在论意义**：insert_at在位置k注入的操作权T，在split后要么分给Gamma1，要么分给Gamma2，不会同时分给两个（线性）。

**证明策略**：对split的定义展开（forall n的析取），逐位置分析。位置k是关键：
- 如果位置k分给了Gamma1（get Gamma1 k = Some (Some T)），则Gamma1 = insert_at k T Gamma1'
- 如果位置k分给了Gamma2，则Gamma2 = insert_at k T Gamma2'
- 其他位置（n≠k）按原始split分配

**证明步骤**：
1. 展开split定义
2. 对位置k做case分析（get Gamma1 k vs get Gamma2 k）
3. 构造Gamma1' = remove_at k Gamma1（如果k分给了Gamma1）或Gamma1' = Gamma1
4. 证明split Gamma Gamma1' Gamma2'
5. 证明等式

**注意**：需要先定义remove_at（删除位置k的元素）。

### 引理2：remove_at定义

```coq
Fixpoint remove_at (Gamma : ctx) (k : nat) : ctx :=
  match Gamma with
  | [] => []
  | x :: xs =>
    match k with
    | O => xs
    | S k' => x :: remove_at xs k'
    end
  end.
```

**存在论意义**：从操作权分布中删除位置k的操作权。对应"操作权被拿走后上下文的变化"。

### 引理3：get_insert_at_propagation（get在insert_at后的传播）

```coq
Lemma get_insert_at_propagation : forall Gamma T k m,
  m < k ->
  get (insert_at k T Gamma) m = get Gamma m.
```

（这个S04应该已经有了，叫get_insert_at_lt）

以及：
```coq
Lemma get_remove_at : forall Gamma k m T,
  get (insert_at k T Gamma) (S m) = get Gamma m \/ ...
```

实际上，PPar case中需要的是：如果get Gamma m = Some (Some T)，且m < k（insert_at位置），那么get Gamma1' m = Some (Some T)（如果m位置分给了Gamma1'）。

这需要split的性质：split保持每个位置的get值。

### 引理4：split_implies_no_use（split后未分到操作权的子进程不引用该位置）

```coq
Lemma split_implies_no_use : forall Gamma Gamma1 Gamma2 P Q k,
  split Gamma Gamma1 Gamma2 ->
  typed Gamma1 P ->
  get Gamma2 k = None \/ get Gamma2 k = Some None ->
  uses_at Q k = false.
```

**存在论意义**：如果位置k的操作权分给了Gamma1（Gamma2中k位置是None），那么在Gamma2中类型化的进程Q不能引用k位置（因为那里没有操作权）。

**证明策略**：用typed_implies_uses_get_some的逆否命题。如果uses_at Q k = true，那么get Gamma2 k = Some (Some T)，与前提矛盾。

### 引理5：subst_var_not_used（不引用k则代换不变）

```coq
Lemma subst_var_not_used : forall P m k,
  uses_at P k = false ->
  subst_var m k P = P.
```

（这个在uses_at基础设施文档里已经给了）

---

## 三、简化方案：先证弱版本

如果5个引理太难，可以先证一个弱版本的PPar case：

**弱版本前提**：insert_at的位置k不被任何子进程引用（uses_at Q k = false /\ uses_at R k = false）。

这时候subst_var m k Q = Q，subst_var m k R = R，只需要证明typed Gamma (PPar Q R)。

证明：
1. split (insert_at k T Gamma) Gamma1 Gamma2
2. 因为Q和R都不引用k，insert_at的T是未使用的
3. 用strengthening_insert_at去掉insert_at，得到split Gamma Gamma1' Gamma2'
4. typed Gamma1' Q和typed Gamma2' R
5. ty_par得到typed Gamma (PPar Q R)

这个弱版本只需要strengthening_insert_at和split_insert_at两个引理，相对简单。

**强版本**（子进程可能引用k）需要完整的5个引理。

---

## 四、推荐的执行顺序

1. **先定义remove_at**（简单，Fixpoint直接写）
2. **证split_insert_at**（核心引理，对split定义逐位置分析）
3. **证split_implies_no_use**（用typed_implies_uses_get_some的逆否）
4. **证subst_var_not_used**（对P归纳，简单）
5. **先证弱版本PPar**（子进程不引用k的情况）
6. **再证强版本PPar**（子进程可能引用k的情况，用split_insert_at分case）

---

## 五、常见坑

1. **insert_at增加上下文长度**：split (insert_at k T Gamma) Gamma1 Gamma2中，Gamma1/Gamma2的长度比Gamma长1。remove_at是用来还原长度的。
2. **位置偏移**：insert_at k T Gamma中，位置k之后的元素都后移了一位。split后，Gamma1/Gamma2中的位置也有偏移。用remove_at还原时要注意偏移。
3. **m和k的大小关系**：代换目标位置m和insert_at位置k的大小关系决定了get的传播方式。分m<k、m=k、m>k三种情况。
4. **PPar不直接消耗通道**：not_used_channel_at (PPar Q R) m = not_used_channel_at Q m && not_used_channel_at R m。前提传递时要分解。
5. **split的定义是逐位置的**：不是"前半/后半"，是每个位置独立分配给Gamma1或Gamma2。这让split_insert_at的证明更复杂，但也更灵活。

---

## 六、给S04的建议

1. **不要急着证PPar**：先把A线方案实施完（PIn/POut的n=m被前提排除），再处理PPar。
2. **先证弱版本**：弱版本只需要2个引理，可以先让substitution_general编译通过（PPar用弱版本admit强版本）。
3. **强版本单独研究**：强版本需要5个引理，可能需要1-2天。可以先标记为OB-010，单独处理。
4. **congruence可以并行**：congruence_preserves_typing不受PPar影响，可以同时证。

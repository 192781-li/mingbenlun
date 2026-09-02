# S01给S04：congruence_preserves_typing证明策略（不受OB-009影响，可先证）

> 作者：S01哲学分站
> 日期：2026-09-02
> 性质：精确到tactic级别的证明策略
> 关联：congruence_preserves_typing是L2的第二个Admitted，不受OB-009（substitution_general的n=m反例）影响，S04恢复后可以先证这个

---

## 一、定理陈述

```coq
Theorem congruence_preserves_typing : forall P P' Gamma,
  congruence P P' -> typed Gamma P -> typed Gamma P'.
```

**存在论意义**：结构同余不改变操作权的使用方式——只是把进程重新排列，不增加或消耗操作权。所以同余保持类型。

---

## 二、证明策略：对congruence P P'归纳

```coq
Proof.
  intros P P' Gamma Hc Ht.
  induction Hc.
  - (* cong_refl: congruence P P *)
    exact Ht.
  - (* cong_sym: congruence Q P -> congruence P Q *)
    (* 需要对称性：typed Gamma Q -> typed Gamma P *)
    (* 这需要对congruence再做一次归纳，或者证明typed在congruence下是等价关系封闭的 *)
    (* 最简单的方式：对congruence P Q归纳，证明两个方向 *)
    (* 建议：先证明一个引理 congruence_iff_typed，然后用它 *)
    admit.  (* 见下方"对称性问题" *)
  - (* cong_trans: congruence P Q -> congruence Q R -> congruence P R *)
    apply IHHc2. apply IHHc1. exact Ht.
  - (* cong_par_comm: PPar P Q ≡ PPar Q P *)
    (* 需要split的对称性 *)
    inversion Ht as [ | | | | | | | Hsplit HQ HR].
    apply ty_par with (Gamma1 := Gamma2) (Gamma2 := Gamma1).
    + apply split_sym. exact Hsplit.
    + exact HR.
    + exact HQ.
  - (* cong_par_assoc: PPar (PPar P Q) R ≡ PPar P (PPar Q R) *)
    (* 需要split的结合律 *)
    inversion Ht. inversion H0.
    (* 需要split_assoc引理：如果split Gamma (Gamma1++Gamma2) Gamma3，则split Gamma Gamma1 (Gamma2++Gamma3) *)
    admit.  (* 需要先证split_assoc引理 *)
  - (* cong_par_zero: PPar P PZero ≡ P *)
    inversion Ht. inversion H1.  (* PZero的类型规则：typed Gamma2 PZero，需要Gamma2 = []或全None *)
    (* 需要证明：如果split Gamma Gamma1 Gamma2且typed Gamma2 PZero，则Gamma = Gamma1（Gamma2全为None） *)
    admit.  (* 需要先证typed_zero_implies_all_none引理 *)
  - (* cong_res_par: PRes (PPar P Q) ≡ PPar (PRes P) Q，前提~fv_at Q 0 *)
    (* 需要约束提取保持类型 *)
    inversion Ht. inversion H0.
    (* PRes的类型规则：typed (Some T :: Gamma') (PPar P Q) -> typed Gamma' (PRes (PPar P Q)) *)
    (* 需要把Some T :: Gamma'拆成适合PPar Q的形式 *)
    admit.  (* 需要仔细分析上下文结构 *)
  - (* cong_rep_unfold: PRep P ≡ PPar P (PRep P) *)
    (* 需要复制展开保持类型 *)
    inversion Ht.  (* PRep的类型规则：typed Gamma P -> typed Gamma (PRep P) *)
    (* 目标：typed Gamma (PPar P (PRep P))，需要split Gamma Gamma1 Gamma2，typed Gamma1 P，typed Gamma2 (PRep P) *)
    (* 关键：PRep不消耗操作权（非线性），所以可以任意split *)
    admit.  (* 需要分析PRep的类型规则 *)
  - (* cong_par_cong: P≡P' / Q≡Q' -> PPar P Q ≡ PPar P' Q' *)
    inversion Ht as [ | | | | | | | Hsplit HQ HR].
    apply ty_par with (Gamma1 := Gamma1) (Gamma2 := Gamma2).
    + exact Hsplit.
    + apply IHHc1. exact HQ.
    + apply IHHc2. exact HR.
  - (* cong_res_cong: P≡P' -> PRes P ≡ PRes P' *)
    inversion Ht.
    apply ty_res. apply IHHc. exact H0.
  - (* cong_tau_cong: P≡P' -> PTau P ≡ PTau P' *)
    inversion Ht.
    apply ty_tau. apply IHHc. exact H0.
Admitted.
```

---

## 三、需要的辅助引理

### 引理1：split_sym（split的对称性）

```coq
Lemma split_sym : forall Gamma Gamma1 Gamma2,
  split Gamma Gamma1 Gamma2 -> split Gamma Gamma2 Gamma1.
```

**证明策略**：对split归纳。split的定义是逐位置分配，交换Gamma1和Gamma2后仍然成立。直接对split的构造子归纳。

**S04应该已经有了**（Layer2.v第124行有split_sym的声明）。

### 引理2：split_assoc（split的结合律）

```coq
Lemma split_assoc : forall Gamma Gamma1 Gamma2 Gamma3,
  split Gamma Gamma1 Gamma2 -> split Gamma2 Gamma2a Gamma2b ->
  exists Gamma', split Gamma Gamma1 Gamma' /\ split Gamma' Gamma2a Gamma2b.
```

或者更直接的形式：
```coq
Lemma split_assoc_simple : forall Gamma Gamma1 Gamma2 Gamma3,
  split Gamma (Gamma1 ++ Gamma2) Gamma3 ->
  split Gamma Gamma1 (Gamma2 ++ Gamma3).
```

**证明策略**：对split归纳，逐位置分析。这是标准的列表分割结合律。

### 引理3：typed_zero_implies_all_none（PZero类型化意味着上下文全为None）

```coq
Lemma typed_zero_implies_all_none : forall Gamma,
  typed Gamma PZero ->
  forall n, get Gamma n = None \/ get Gamma n = Some None.
```

或者更强的：
```coq
Lemma typed_zero_context : forall Gamma, typed Gamma PZero -> 
  forall n, get Gamma n <> Some (Some T) (对任意T).
```

**证明策略**：PZero的类型规则应该是`typed Gamma PZero`对任意Gamma成立（空进程不消耗操作权）。如果是这样，这个引理不成立，cong_par_zero的证明需要另一种方式。

**需要确认PZero的类型规则**。如果ty_zero是`forall Gamma, typed Gamma PZero`，那么cong_par_zero的证明是：
- typed Gamma (PPar P PZero) → split Gamma Gamma1 Gamma2, typed Gamma1 P, typed Gamma2 PZero
- 因为typed Gamma2 PZero对任意Gamma2成立，所以Gamma2可以是任意的
- 但我们需要typed Gamma P，即需要证明Gamma1 = Gamma（Gamma2不包含任何操作权）
- 这需要split的性质：如果split Gamma Gamma1 Gamma2且Gamma2全为None，则Gamma = Gamma1

**关键**：需要证明"如果split Gamma Gamma1 Gamma2且forall n, get Gamma2 n = Some None，则Gamma = Gamma1"。

### 引理4：PRep的类型规则分析

需要确认PRep的类型规则。如果是`typed Gamma P -> typed Gamma (PRep P)`，那么PRep不消耗额外操作权，可以任意split。

cong_rep_unfold的证明：
- typed Gamma (PRep P) → typed Gamma P
- 目标：typed Gamma (PPar P (PRep P))
- 需要split Gamma Gamma1 Gamma2, typed Gamma1 P, typed Gamma2 (PRep P)
- 因为PRep不消耗操作权，可以取Gamma1 = Gamma, Gamma2 = 全None列表
- 需要split Gamma Gamma (全None列表)成立

---

## 四、对称性问题（cong_sym）

cong_sym是最难的部分。因为congruence是对称的，我们需要证明：
```
congruence P Q -> (typed Gamma P -> typed Gamma Q) /\ (typed Gamma Q -> typed Gamma P)
```

**解决方案**：不直接对congruence归纳证明一个方向，而是证明一个更强的引理：

```coq
Lemma congruence_both_directions : forall P Q,
  congruence P Q ->
  (forall Gamma, typed Gamma P -> typed Gamma Q) /\
  (forall Gamma, typed Gamma Q -> typed Gamma P).
```

对congruence归纳，每个构造子证明两个方向。cong_refl/cong_trans/cong_par_cong等直接用归纳假设。cong_sym直接交换两个方向。

然后congruence_preserves_typing就是这个引理的第一个方向。

---

## 五、推荐的证明顺序

1. **先证split_sym**（如果还没证）
2. **证split_assoc**
3. **证typed_zero_context**（PZero类型化的上下文性质）
4. **确认PRep和PZero的类型规则**
5. **证congruence_both_directions**（更强的引理，包含对称性）
6. **从congruence_both_directions推出congruence_preserves_typing**

---

## 六、给S04的建议

1. **先确认PZero和PRep的类型规则**（看Layer2.v的ty_zero和ty_rep）
2. **先证简单的case**：cong_refl、cong_trans、cong_par_cong、cong_res_cong、cong_tau_cong
3. **再证需要辅助引理的case**：cong_par_comm（split_sym）、cong_par_assoc（split_assoc）
4. **最后证难的case**：cong_par_zero、cong_res_par、cong_rep_unfold
5. **对称性用congruence_both_directions引理处理**

这个定理不受OB-009影响，可以在等主人决定OB-009方向的同时先证。

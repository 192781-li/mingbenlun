# OB-017：typed_any_ctx疑似为假——定理陈述需S01研判

> 日期：2026-09-11｜S04 Coq形式化分站｜对应：Layer2.v line 2683
> 状态：plausibly_false（证伪守卫门1/1.5通过，交人工/S01裁决）
> 触发：DS V4.1上下文（含S01 OB015/016策略）证明typed_any_ctx时，DS宣布为假并给出反例

---

## 一、定理陈述

```coq
(* typed_any_ctx：完全无变量的进程(~fv_at P 0)可在任意上下文中类型化。
   ~fv_at P 0意味着P不含PVar/POut/PIn（所有nat index>=0），
   仅由PZero/PTau/PPar/PRes/PRep构成，不消耗上下文资源。 *)
Lemma typed_any_ctx : forall P Gamma, ~ fv_at P 0 -> typed Gamma P.
```

## 二、DS反例（证伪守卫门1编译通过exit=0，门1.5证明完整）

```coq
Lemma closed_self_out_untypable :
  ~ typed [] (PRes (POut 0 0 PZero)).
Proof.
  intros H.
  apply res_elim in H. destruct H as [T HT].
  apply out_elim in HT.
  destruct HT as [Gamma1 [Gamma2 [T' [i [o [Huse1 [Ho [Huse2 Hbody]]]]]]]].
  unfold use in Huse1, Huse2.
  destruct Huse1 as [Hx1 Hx2], Huse2 as [Hy1 Hy2].
  subst Gamma1.
  simpl in Hy1.
  congruence.
Qed.

Lemma typed_any_ctx_counterexample :
  ~ (forall P Gamma, ~ fv_at P 0 -> typed Gamma P).
Proof.
  intros H.
  specialize (H (PRes (POut 0 0 PZero)) []).
  assert (Hfv : ~ fv_at (PRes (POut 0 0 PZero)) 0).
  { intro F. simpl in F.
    destruct F as [F|[F|F]];
      try (exfalso; lia);
      exact F. }
  apply closed_self_out_untypable.
  exact (H Hfv).
Qed.
```

## 三、反例核心逻辑

1. **进程**：`PRes (POut 0 0 PZero)`
2. **`~ fv_at P 0` 成立**：因为PRes偏移，`fv_at (PRes P) n = fv_at P (S n)`，所以`fv_at (PRes (POut 0 0 PZero)) 0 = fv_at (POut 0 0 PZero) 1`。而POut的index是0和0，都不等于1，所以为假。
3. **`typed [] P` 不成立**：POut需要use关系（输入输出通道都需要在上下文中有对应资源），但空上下文`[]`无法满足use。
4. **矛盾**：typed_any_ctx说`~ fv_at P 0 -> typed Gamma P`对任意Gamma成立，取Gamma=[]就得到`typed [] P`，但实际上不成立。

## 四、根因分析

**注释与定义不符**：注释说"~fv_at P 0意味着P不含PVar/POut/PIn"，但实际上：
- `fv_at`检查的是进程中自由变量出现的**位置**
- `PRes`会偏移位置（`fv_at (PRes P) n = fv_at P (S n)`）
- 所以`PRes (POut 0 0 PZero)`虽然包含POut，但POut的index 0,0被偏移到了1,1，不在位置0

**正确的陈述可能是**：
- (A) `typed [] P -> forall Gamma, typed Gamma P`（weakening，不需要~fv_at前提）
- (B) `(forall n, ~ fv_at P n) -> typed Gamma P`（完全无自由变量，不只是位置0）
- (C) 保持原陈述但修正fv_at定义（PRes不偏移？但这会影响其他定理）

## 五、影响范围

- `typed_res_par_l`和`typed_res_par_r`的前提是`~ fv_at Q 0`，可能也需要重新审视
- 如果typed_any_ctx陈述错误，需要修正陈述后重新证明
- split_assoc不依赖typed_any_ctx，可以继续推进

## 六、请求S01研判

1. typed_any_ctx的原始哲学意图是什么？是想表达"完全无变量的进程在任意上下文中可类型化"吗？
2. 如果是，正确的前提应该是`forall n, ~ fv_at P n`还是`typed [] P`？
3. `fv_at`的定义是否需要修正？PRes的偏移是否符合存在论意图？
4. typed_res_par_l/r的前提`~ fv_at Q 0`是否也需要修正？

## 七、S04临时处理

- 不自动改判命题真假（证伪守卫铁律）
- 不自动改定理陈述（哲学判断点，需S01裁决）
- 继续推进split_assoc（不依赖typed_any_ctx）
- 等S01研判后再处理typed_any_ctx和typed_res_par_l/r

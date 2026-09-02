# S01给S04的简洁证明策略建议（substitution_lemma）

> 发件：S01哲学分对话
> 收件：S04 Coq形式化分站
> 日期：2026-09-02
> 背景：subst_var bug已修复，v5广义引理方案被截断，已有11个辅助引理

---

## 核心建议：不要从头写大证明，分小块证明

DeepSeek v5被截断的原因是证明太长（16384 tokens）。不要让DeepSeek一次写完整的substitution_lemma证明，而是分小块：

### 策略：对proc结构归纳，每步单独验证

```coq
Lemma substitution_lemma : forall Gamma T Q y,
  typed (Some T :: Gamma) Q ->
  get Gamma y = Some (Some T) ->
  typed Gamma (subst_var y 0 Q).
Proof.
  intros Gamma T Q.
  induction Q as [
    | x y0 Q IH        (* POut *)
    | x Q IH           (* PIn *)
    | Q1 Q2 IH1 IH2    (* PPar *)
    | Q IH             (* PRes *)
    | Q IH             (* PTau *)
    | Q IH             (* PRep *)
    |                  (* PZero *)
    | n                (* PVar *)
  ]; intros Hty Hget.
  (* 每个case单独处理，处理完一个就检查 *)
```

### 各case的处理要点

1. **PVar n**：最关键的case
   - n=0时：subst_var y 0 (PVar 0) = PVar y，类型由Hget保证
   - n=S n'时：subst_var y 0 (PVar (S n')) = PVar n'，类型由Hty反演得到

2. **POut x y0 Q**：subst_var分布到x、y0、Q，用IH处理Q，x和y0用subst_name的引理

3. **PIn x Q**：subst_var进入绑定器，变成subst_var (S y) 1 Q。需要弱化引理（在Gamma前插入None保持类型），然后用IH

4. **PPar Q1 Q2**：分布到Q1和Q2，用IH1和IH2

5. **PRes Q**：类似PIn，进入绑定器

6. **PTau Q / PRep Q**：直接用IH

7. **PZero**：trivial

### 关键辅助引理（已有11个，检查是否包含以下）

- `subst_name_typed`：名字代换保持类型（POut/PIn的x和y0）
- `weakening_lemma`：弱化引理（上下文插入None保持类型，PIn/PRes需要）
- `get_shift`：上下文偏移后的get关系

如果这3个引理在已有的11个中，证明会非常简洁（预计100-150行）。

### 为什么对proc归纳比对typed归纳好

- proc只有8个构造子，typed可能有更多规则
- subst_var的定义就是对proc递归的，归纳证明和定义同构
- 不需要在每步重建类型推导（typed归纳的痛点）
- 每个case独立，DeepSeek可以一次写2-3个case，不会被截断

### 执行建议

1. 先让DeepSeek只写PVar和PZero两个case（最简单），验证基本思路
2. 通过后再加PPar、PTau、PRep（直接用IH）
3. 最后处理POut、PIn、PRes（需要辅助引理）
4. 每加2-3个case就编译验证，不要一次写完
5. 如果某个case卡住，单独把这个case抛给S01做哲学研判

### congruence_preserves_typing

substitution_lemma完成后，congruence_preserves_typing通常可以直接用substitution_lemma证明——归约上下文的代换就是substitution_lemma的应用。

---

> S01哲学分对话 · 2026-09-02
> 核心：分小块证明，不要一次写大证明。对proc归纳，每2-3个case验证一次。已有的11个辅助引理应该足够。

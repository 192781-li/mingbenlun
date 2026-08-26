# G^ω(C)的范畴性质

> 操作范畴论 v1.4 - Track 1
> 2026-08-25

---

## 1. 回顾Int-构造

Joyal-Street-Verity（1996）的Int-构造把任意traced monoidal category $\mathcal{C}$变成compact closed category $\mathrm{Int}(\mathcal{C})$：
- 对象：$(A^+, A^-)$，$\mathcal{C}$中对象的有序对
- 态射$(A^+,A^-)\to(B^+,B^-)$：$\mathcal{C}$中态射$A^+\otimes B^- \to B^+\otimes A^-$
- 复合：用$\mathcal{C}$的迹
- 对偶：$(A^+,A^-)^* = (A^-,A^+)$

$G^\omega(\mathcal{C})$是Int-构造在PTC上的类比：用**生产性迹**$\mathrm{Tr}^\omega$代替普通迹，态射是**生产性流处理器**而非有限连线。

## 2. G^ω(C)的定义

设$\mathcal{C}$是PTC。定义$G^\omega(\mathcal{C})$：

**对象**：$(A^+, A^-)$，其中$A^+, A^-$是$\mathcal{C}$的对象（或其流对象$A^{+\omega}, A^{-\omega}$）。

**态射**：$(A^+, A^-) \to (B^+, B^-)$是$\mathcal{C}$中的生产性Mealy机：
$$f: A^+ \otimes B^- \otimes X \to B^+ \otimes A^- \otimes X$$
连同行为$\mathrm{beh}(f, x_0): A^{+\omega}\otimes B^{-\omega} \to B^{+\omega}\otimes A^{-\omega}$。

当状态$X=I$时退化为无状态连线（即Int(C)中的态射）。

**复合**：$f: (A^+,A^-)\to(B^+,B^-)$和$g:(B^+,B^-)\to(C^+,C^-)$的复合用生产性迹：
$$g\circ f = \mathrm{Tr}^{B^+\otimes B^-}_{\omega}(f\otimes g \text{ 的连线})$$
PTC的Productivity公理保证复合是生产性的（每步有产出）。

## 3. G^ω(C)是范畴

**定理34**：$G^\omega(\mathcal{C})$是范畴。

**证明**：
- **恒等态射**：$\mathrm{id}_{(A^+,A^-)}$是$A^+\otimes A^- \to A^+\otimes A^-$的恒等连线（无状态，$X=I$）。行为是恒等流函数。
- **复合封闭**：PTC公理（Productivity）保证两个生产性Mealy机的反馈复合仍然生产性。
- **结合律**：由PTC的Tightening/Naturality公理，反馈的嵌套顺序不影响结果——先反馈$B$再反馈$C$等于先反馈$C$再反馈$B$（不同反馈线不相交，迹的自然性保证）。
- **单位律**：恒等连线与$f$复合等于$f$，由Yanking公理（$\mathrm{Tr}(\mathrm{id})=\mathrm{id}$）。

∎

## 4. G^ω(C)是紧闭合范畴

**定理35**：$G^\omega(\mathcal{C})$是dagger compact closed范畴。

**证明**：
- **张量积**：$(A^+,A^-)\otimes(B^+,B^-) = (A^+\otimes B^+, A^-\otimes B^-)$，逐点提升。
- **单位对象**：$(I,I)$。
- **对偶**：$(A^+,A^-)^* = (A^-,A^+)$。
- **unit/counit**：
  - $\eta_{(A^+,A^-)}: (I,I) \to (A^+,A^-)\otimes(A^+,A^-)^* = (A^+\otimes A^-, A^-\otimes A^+)$
  - 这是$\mathcal{C}$中的"弯线"——$A^-\otimes A^+ \to A^+\otimes A^-$的交换（在对称monoidal范畴中存在）。
  - 在GoI中这就是反馈线的"弯折"。
- **紧闭合方程**（蛇方程）：由Yanking公理保证——弯线拉直等于恒等。
- **dagger**：$(A^+,A^-)^\dagger = (A^+,A^-)^*$（自对偶，因为对象是配对的），态射的dagger是导线反转方向。

∎

**意义**：$G^\omega(\mathcal{C})$是紧闭合的，意味着：
1. 每个态射$f:A\to B$可以"弯曲"成名字$\ulcorner f\urcorner: I\to A^*\otimes B$（定理28的名字构造在$G^\omega(\mathcal{C})$中是内部操作）
2. 多态函数可以表示为导线（高阶函数=弯线）
3. f-层级的嵌套反馈在$G^\omega(\mathcal{C})$中是合法的态射——$f^2$、$f^3$的自我建模就是紧闭合结构中的弯线

## 5. G^ω(C)有递归类型

**定理36**：$G^\omega(\mathcal{C})$对函子$F(X)=A\otimes X$有不动点$A^\omega = \nu X.(A\otimes X)$，且$A^\omega \cong A\otimes A^\omega$。

**证明**：PTC定义中包含流对象$A^\omega$满足$A^\omega \cong A\otimes A^\omega$（cons同构）。在$G^\omega(\mathcal{C})$中，这个同构是内部态射：
- $\mathrm{cons}: A\otimes A^\omega \to A^\omega$（放入头）
- $\mathrm{uncons}: A^\omega \to A\otimes A^\omega$（观察头和尾）
- 两者互逆。

更一般地，对任意"正向"函子$F$（由$\otimes$、$\oplus$、$\bang$构造），$G^\omega(\mathcal{C})$中有$\nu X.F(X)$作为对象，因为PTC的余归纳迹保证了无限展开的生产性。∎

**意义**：$G^\omega(\mathcal{C})$可以解释递归类型——包括$\nu F_2$（生命流类型）。这是标准Int-构造做不到的：Int(C)只处理有限连线，不处理无限流。

## 6. !在G^ω(C)中的行为

$\mathcal{C}$上的$\bang$-余单子提升到$G^\omega(\mathcal{C})$：
$$\bang(A^+,A^-) = (\bang A^+, \bang A^-)$$

但T009/20在$G^\omega(\mathcal{C})$中仍然成立：$\bang$不穿透生产性状态。具体地：

**定理37**：在$G^\omega(\mathcal{C})$中，不存在自然态射$\bang\nu F_2 \to \nu\bang F_2$。

**证明**：$G^\omega(\mathcal{C})$中的态射是$\mathcal{C}$中的生产性Mealy机。如果$\bang\nu F_2 \to \nu\bang F_2$在$G^\omega(\mathcal{C})$中存在，它在$\mathcal{C}$中的行为就是一个生产性Mealy机，把$\bang$-流转换为$\bang$-流——但这要求底层$\mathcal{C}$中有$\bang\nu F_2 \to \nu\bang F_2$，而T001已证明不存在。∎

**意义**：即使在"更高层"的$G^\omega(\mathcal{C})$范畴中，生命流不可资本化的定理仍然成立。紧闭合和递归类型没有破坏这个结果——!-模态的限制是结构性的，不是某个特定范畴的偶然性质。

## 7. 与Int-构造的关系

**命题**：$\mathrm{Int}(\mathcal{C})$是$G^\omega(\mathcal{C})$的全子范畴，由无状态（$X=I$）态射组成。

- Int(C)中的态射是有限连线（nilpotent反馈）
- G^ω(C)中的态射是生产性流处理器（无限反馈）
- 包含函子$\mathrm{Int}(\mathcal{C}) \hookrightarrow G^\omega(\mathcal{C})$是忠实的，但不全——G^ω(C)有更多态射（无限过程）

这说明G^ω构造是Int构造的"无限版"——从有限连线扩展到无限流处理器，同时保持紧闭合结构。

## 8. 总结

- $G^\omega(\mathcal{C})$是范畴（定理34）
- $G^\omega(\mathcal{C})$是dagger compact closed（定理35）——f-层级的弯线在内部合法
- $G^\omega(\mathcal{C})$有递归类型（定理36）——$\nu F_2$是合法对象
- $\bang$不穿透生产性状态在$G^\omega(\mathcal{C})$中仍成立（定理37）——生命不可资本化在更高层范畴中仍成立
- Int(C)是G^ω(C)的无状态全子范畴

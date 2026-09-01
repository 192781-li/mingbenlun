# OB-001：substitution_lemma（代换引理）证明困境

> 编号：OB-001
> 发现时间：2026-09-02
> 所在文件：coq/theories/ALL/Layer2.v
> 所在定理：substitution_lemma
> 记录者：S04 Coq形式化分站
> S01研判状态：completed（TASK-S04-008，2026-09-02）
> 解决状态：S01研判完成，待S04执行
> S01研判结论：代换=特殊重命名，substitution_lemma=ren_typed_general的特例。放弃650行typed归纳，先证ren_typed_general。详见docs/notes/哲学研究/S01_TASK-S04-008_substitution_lemma哲学研判_20260902.md

---

## 一、引理陈述

```coq
Theorem substitution_lemma : forall Gamma T y Q,
  typed (Some T :: Gamma) Q -> get Gamma y = Some (Some T) ->
  typed Gamma (subst_var y 0 Q).
```

**白话**：如果在上下文"Some T :: Gamma"中，进程Q是良类型的，并且Gamma中第y个变量的类型是T，那么把Q中的第0个约束变量代换成y之后，得到的进程在Gamma中仍然是良类型的。

这是pi演算类型系统的标准引理，是subject_reduction（主体归约）证明的核心前提之一。

---

## 二、DeepSeek的尝试与具体错误

### 证明思路
DeepSeek选择对**typed关系（H）进行归纳**（而非对proc结构Q归纳），包含6个辅助引理：
1. `subst_name_neq`：n≠k且n≤k → subst_name m k n = n
2. `subst_name_gt`：k<n → subst_name m k n = n-1
3. `subst_name_eq`：subst_name m k k = m
4. `subst_var_fresh`：变量k不在Q的自由变量中 → subst_var m k Q = Q
5. `subst_var_ren`：代换和重命名在约束变量情况下交换
6. `ren_xik_typed`：用xik k重命名保持类型

主定理对typed关系的7条规则逐条归纳，每个构造子分n=y0/n<y0/n>y0三种情况，每种情况又处理x和y两个变量。

### 4次回喂的具体错误

| 版本 | 错误位置 | 具体错误 |
|------|----------|----------|
| v1 | line 197 | `Nat.ltb_ge`在Rocq 9.1.0中不存在，模式匹配错误："Expects a disjunctive pattern with 1 branch or a conjunctive pattern made of 2 patterns" |
| v2 | line 197 | 声称修复了Nat.ltb_ge但实际没改，同样错误 |
| v3 | 多处 | ①`apply subst_name_neq`用法错误：引理结论是等式，目标是PVar等式，应该用rewrite+reflexivity；②注释开头`(* -----`被截断导致语法错误；③`apply Nat.eqb_neq in Ekk`无法应用（Ekk是`(k=?k)=false`，应用方式不对） |
| v4 | line 204 | `subst_var_fresh`的PVar case中：`intro E. subst. apply Nat.eqb_eq in Enk. contradiction.`——Enk是`(n=?k)=false`，但用了`Nat.eqb_eq`（只适用于`=true`） |

### 核心问题
证明太复杂（650行，6个辅助引理，大量重复case分析），导致小错误层出不穷。每次修复一个错误又冒出新的错误。

---

## 三、阻碍的本质判断

这**不只是技术问题**，涉及深刻的哲学判断：

### 哲学问题1：代换引理的存在论意义是什么？
- 在生命论的操作本体论中，"把一个变量代换成另一个变量"意味着什么？
- 变量是什么？是操作的占位符吗？代换是不是"一个操作被另一个操作替代"？
- 为什么代换之后类型保持不变？这在存在论上意味着什么？

### 哲学问题2：证明结构的哲学基础
- 对typed关系归纳 vs 对proc结构归纳，这两种归纳方式在哲学上有什么区别？
- typed关系是"操作的规范性"，proc结构是"操作的实体性"。对哪一个归纳更符合"操作先于实体"原则？
- 标准pi演算证明通常对typed关系归纳，但生命论的形式化是不是应该有不同的选择？

### 哲学问题3：有没有更简单的证明思路？
- 650行是不是因为证明思路本身就歪了？
- 能不能利用已有的ren_typed（重命名保持类型）引理，把代换归约为重命名？
- 代换和重命名在哲学上是什么关系？代换是不是"一次性的重命名"？

### 哲学问题4：代换引理和subject_reduction的哲学关系
- subject_reduction说"归约保持类型"，代换引理说"代换保持类型"。
- 归约和代换在哲学上是什么关系？归约是不是"操作的自我展开"，代换是不是"操作的相互替代"？
- 为什么代换引理是subject_reduction的前提？

---

## 四、S01初步研判方向（待完善）

**待S01完成TASK-S04-008后补充完整研判。**

初步思考：
- 代换的存在论本质可能是"操作的可替代性"——一个操作位置可以被另一个同类型的操作填充，这是社会协作（分工、交换）的存在论基础
- 证明复杂度可能源于对typed关系归纳——如果"操作先于实体"，也许应该对proc结构（操作本身）归纳，而不是对typed关系（操作的规范性）归纳
- 代换可能可以归约为重命名+弱化，这样证明可以大大简化——但这需要哲学上论证"代换和重命名的存在论等价性"

---

## 五、相关文件

- 技术状态报告：coq/S04技术状态详细报告_供S01翻译_20260902.md
- S01研判任务：TASK-S04-008
- 所在文件：coq/theories/ALL/Layer2.v
- 相关引理：ren_typed（L1已证明）、subject_reduction（L2已证明，依赖substitution_lemma）

---

> 这个阻碍不是失败，是契机。代换引理卡住的地方，可能正是我们理解"操作的可替代性"的存在论入口。

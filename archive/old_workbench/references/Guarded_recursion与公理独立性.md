# Guarded Recursion连接与PTC公理独立性

> 操作范畴论 v1.7 - Track 2 & 3
> 2026-08-25

---

# Track 2: 与Guarded Recursion的连接

## 1. Nakano的later模态

Nakano（2000）引入了"later"模态$\rhd$（也记为$\bullet$或$\triangleright$）用于保证递归定义的生产性：

- $\rhd A$：类型$A$的值"晚一步"可用
- 流类型：$\mathrm{Stream}\ A = A \times \rhd(\mathrm{Stream}\ A)$——头立即可用，尾"晚一步"
- 生产性：递归调用必须在$\rhd$下（guarded），保证每步都能产出头元素

这与我们的PTC高度对应：

| PTC/GoI | Guarded Recursion |
|---|---|
| 流对象$A^\omega = \nu X.(A\otimes X)$ | $\mathrm{Stream}\ A = A \times \rhd(\mathrm{Stream}\ A)$ |
| 生产性迹$\mathrm{Tr}^\omega$（每步产出） | guarded fixed point（$\rhd$-guarded recursion） |
| Mealy机$A\otimes X\to B\otimes X$ | 因果流函数（每个输出只依赖之前的输入） |
| cons/hd/tl | head/tail构造子 |
| Productivity公理 | guardedness条件（递归调用在$\rhd$下） |

## 2. 核心对应

**生产性=guardedness。** 在PTC中，生产性迹要求反馈回路每步都产生输出——不能等无限久才有结果。在guarded recursion中，$\rhd$-guarded要求递归调用"晚一步"，保证每步都能产出。这是同一个条件的两种表述：

- PTC：$U_{22}$的迭代$\sum U_{22}^n$每步产生有界输出
- Guarded：递归类型的展开每步暴露一个构造子（cons）

**!与later的交互。** 一个自然的问题：$\bang\rhd A \cong \rhd\bang A$吗？

- $\bang\rhd A \to \rhd\bang A$：如果数据晚一步可用，那么晚一步数据可用——成立（$\bang$是函子，与$\rhd$交换）
- $\rhd\bang A \to \bang\rhd A$：如果晚一步有可复制数据，能否现在就复制"晚一步的数据"？——这要求预知未来，在因果系统中不成立

这与T009（!不穿透生产性状态）对应：$\bang$不能把"晚一步才有的线性状态"变成"现在就有的可复制数据"。

## 3. 意义

这个连接表明：
1. PTC的Productivity公理不是孤立发明，与类型论中guarded recursion的生产性条件是同一个概念
2. 可以导入guarded recursion的已有结果：
   - 步索引逻辑关系（step-indexed logical relations）可用于证明PTC中Mealy机的性质
   - Clock quantifiers（Atkey-McBride）可处理多时钟流
   - Guarded recursion的范畴论语义（topos of trees，Møgelberg 2014）提供PTC的额外模型
3. PTC特有的新贡献：!-模态与生产性的交互（T009）——guarded recursion文献中没有研究$\rhd$与线性模态$\bang$的交互，这是我们的新结果

---

# Track 3: PTC公理独立性

## 4. PTC四条公理

回顾PTC公理：
1. **Yanking**：$\mathrm{Tr}^\omega(\mathrm{id})=\mathrm{id}$（直反馈线信号直接穿过）
2. **Tightening**：迹的自然性（反馈与外部映射交换）
3. **Composition**：生产性Mealy机的反馈复合仍生产性
4. **Productivity**：迹每步产生有界输出

## 5. 独立性分析

**Composition可从Tightening+Yanking推出。**

在标准traced monoidal category中，复合的结合律从tightening和yanking推出（Joyal-Street-Verity 1996）。PTC中Mealy机的复合用生产性迹定义，其结合律同样从tightening/naturality推出。因此Composition不是独立公理。

**Productivity是独立的新公理。**

标准traced monoidal category不要求生产性——它要求nilpotency（有限反馈，$U_{22}^n=0$）或vanishing（反馈线被消除）。Productivity要求无限反馈每步有产出，这是标准迹公理不蕴含的。反例：取$U_{22}=0$（反馈线无信号），标准迹存在（$\mathrm{Tr}(U)=U_{11}$），但不生产（没有反馈输出）。

**Yanking独立。** 没有yanking，迹可能引入延迟（信号绕一圈才出来）或衰减。Yanking保证零延迟直反馈。

**Tightening独立。** 没有tightening，迹可能不自然——反馈行为可能依赖于输入输出线的编号而非结构。

## 6. 修正的PTC公理集

PTC的独立公理为三条：
1. **SMC + 流对象**：对称幺半范畴，带流对象$A^\omega\cong A\otimes A^\omega$和cons/hd/tl
2. **迹公理**：Yanking + Tightening（标准traced monoidal公理）
3. **Productivity**：生产性Mealy机的反馈复合每步产生有界输出（新公理）

Composition是定理而非公理。

## 7. 与标准迹的关系

| 性质 | 标准迹（nilpotent） | 生产性迹（productive） |
|---|---|---|
| 反馈终止 | $U_{22}^n=0$（有限步后无信号） | 不终止，但每步有输出 |
| 迹公式 | $U_{11}+U_{12}(\sum_{n=0}^{k}U_{22}^n)U_{21}$（有限和） | $U_{12}(\sum_{n=0}^{\infty}U_{22}^n)U_{21}$（无限和，逐点收敛） |
| 对应 | $\mu$（有限/归纳） | $\nu$（无限/余归纳） |
| 典型模型 | 有限自动机 | 流处理器/量子演化/生命过程 |

生产性迹是标准迹从"有限反馈"到"无限生产性反馈"的推广。PTC = SMC + 流对象 + 迹公理 + Productivity。

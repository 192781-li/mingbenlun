# 相干空间PTC实例

> 操作范畴论 v1.8 - Track 1
> 2026-08-25

---

## 1. 相干空间回顾

Girard（1987）的相干空间：

- **相干空间** $A = (|A|, \subset_A)$：web $|A|$是token集合，$\subset_A$是自反对称的相干关系
- **clique**：子集$x\subseteq|A|$，其中任意两个token相干
- **线性映射** $A\multimap B$：$A^*\otimes B$中的clique（$A^*$把相干换成不相干）
- **张量积**：$|A\otimes B|=|A|\times|B|$，$(a,b)\subset(a',b')$ iff $a\subset_A a'$且$b\subset_B b'$
- **!模态**：$|!A|$是$|A|$中token的有限多重集，相干性逐点定义

## 2. Coh^ω的构造

**流相干空间**：$A^\omega$的web为$\mathbb{N}\times|A|$（带时间戳的token），相干性：
$$(n,a)\subset_{A^\omega}(m,a') \iff n=m \Rightarrow a\subset_A a'$$
不同时间的token总是相干的（它们不冲突），同一时间的token必须在$A$中相干。

clique$x\subseteq|A^\omega|$是一个时间索引的clique族$\{x_n\}_{n\in\mathbb{N}}$，每个$x_n$是$A$的clique——这正是$A$的clique流。

**Mealy机**：因果线性映射$A^\omega\multimap B^\omega$，即$(A^\omega)^*\otimes B^\omega$中的clique，满足因果性（第$n$个输出只依赖前$n$个输入）。

**生产性迹**：与Rel^ω相同的反馈构造，但要求结果是clique。

## 3. 关键定理

**定理53（生产性迹保持clique）**：如果$U$是$(A\otimes X)^\omega\multimap(B\otimes X)^\omega$的因果clique，且反馈生产（每步产生输出），则$\mathrm{Tr}^\omega_X(U)$是$A^\omega\multimap B^\omega$的clique。

**证明**：
对每一步$n$，$U$在第$n$步的分量$U_n$是$(A\otimes X)\multimap(B\otimes X)$的线性映射（clique）。反馈复合在第$n$步的结果是：
$$b_n = U_{11,n}(a_n) + U_{12,n}\left(\sum_{k=0}^{n-1} U_{22,n-1-k}\cdots U_{22,k}(U_{21,k}(a_k))\right)$$

这是线性映射的复合与张量积。线性映射在复合和张量积下封闭（clique的复合是clique，这是线性逻辑范畴论语义的基本性质）。因此每步的$b_n$是$B$的clique。

不同时间步的输出自动相干（$A^\omega$的定义），故$\{b_n\}$构成$B^\omega$的clique。∎

## 4. PTC公理验证

- **SMC**：相干空间和线性映射构成$\mathbf{Coh}$，是线性逻辑的模型，SMC结构标准 ✓
- **流对象**：$A^\omega$有cons/hd/tl，cons是线性映射 ✓
- **Mealy机**：因果线性映射 ✓
- **Yanking**：恒等映射是clique ✓
- **Tightening**：线性映射的自然性 ✓
- **Composition**：因果clique的反馈复合是因果clique（定理53） ✓
- **Productivity**：生产性条件保证每步有输出，clique封闭由定理53保证 ✓

## 5. !在Coh^ω中

相干空间的!模态有标准定义（有限多重集clique）。T009在Coh^ω中成立：!不穿透生产性状态。这是因为!要求有限多重集（可复制），而生产性流是无限的、线性的——无限流不能被有限多重集表示。

## 6. 三个PTC实例的比较

| 实例 | 线性状态 | !-模态 | 生产性条件 | 领域 |
|---|---|---|---|---|
| Rel^ω | 流（序列关系） | 有限多重集（关系收缩） | 因果性 | 经典计算 |
| Hilb^ω | 量子态流 | 经典对象（可复制基） | 幂有界反馈 | 量子力学 |
| Coh^ω | clique流 | 有限多重集clique | 因果性+clique封闭 | 证明论/类型论 |

三个实例中，!不穿透生产性交互状态都成立。这从三个不同领域（计算、物理、逻辑）验证了同一个结构事实。

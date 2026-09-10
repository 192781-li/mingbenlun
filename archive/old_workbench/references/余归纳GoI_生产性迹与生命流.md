# 余归纳GoI：无限生产性过程的动态语义

> 操作范畴论 v0.9
> 2026-08-25

---

## 1. 动机

标准GoI（Girard 1989, Abramsky 1996）在traced monoidal范畴中解释线性逻辑证明：
- 证明 = 算子/连线（wiring）
- cut = 反馈
- 消去cut = 反馈迭代收敛（nilpotency：$(f_{11})^n=0$）

nilpotency对应**有限计算**（$\mu$，归纳，终止）。但生命过程$\nu F_2$是无限的——反馈永不终止，每步却有产出。需要一个余归纳版本的GoI，正确性条件从nilpotency替换为productivity。

---

## 2. 流处理器范畴

在$\mathbf{Rel}$（集合与关系）中构造。

**定义2.1**（流）：对集合$A$，$A^\omega$是$A$上的无限序列集合，$A^*$是有限序列集合。

**定义2.2**（因果流处理器）：从$A$到$B$的流处理器是三元组$(X,R,x_0)$：
- $X$：状态集合
- $R \subseteq (A\times X)\times(B\times X)$：转移关系
- $x_0\in X$：初始状态

它诱导一个因果关系$\llbracket R\rrbracket \subseteq A^\omega\times B^\omega$：
$$(a_0a_1a_2\ldots,\ b_0b_1b_2\ldots)\in\llbracket R\rrbracket$$
当且仅当存在状态序列$x_0,x_1,x_2,\ldots\in X$使得对所有$n\geq0$：
$$((a_n,x_n),(b_n,x_{n+1}))\in R.$$

这是一个余归纳定义：它定义了无限行为，而不要求终止。

**定义2.3**（生产性）：流处理器$(X,R,x_0)$是**生产性的**，如果对所有$(a,x)\in A\times X$，存在$(b,x')\in B\times X$使得$((a,x),(b,x'))\in R$。

**定理2.1**（生产性保证完全性）：如果$R$是生产性的，则对每个输入流$a_\bullet\in A^\omega$，存在至少一个输出流$b_\bullet\in B^\omega$使得$(a_\bullet,b_\bullet)\in\llbracket R\rrbracket$。

**证明**：余归纳构造。给定$a_\bullet$和$x_0$，由生产性，存在$(b_0,x_1)$使得$((a_0,x_0),(b_0,x_1))\in R$。再由生产性，存在$(b_1,x_2)$使得$((a_1,x_1),(b_1,x_2))\in R$。如此继续，构造出完整的$b_\bullet$和$x_\bullet$。∎

**定义2.4**（流处理器的复合）：给定$P=(X,R,x_0):A\to B$和$Q=(Y,S,y_0):B\to C$，定义复合$P;Q=(X\times Y,T,(x_0,y_0)):A\to C$：
$$((a,(x,y)),(c,(x',y')))\in T \iff \exists b\in B:\ ((a,x),(b,x'))\in R\ \text{且}\ ((b,y),(c,y'))\in S.$$

**定理2.2**（复合保持生产性）：如果$R$和$S$都是生产性的，则$T$是生产性的。

**证明**：给定$(a,(x,y))$，由$R$生产性，$\exists(b,x')$使$((a,x),(b,x'))\in R$。由$S$生产性，$\exists(c,y')$使$((b,y),(c,y'))\in S$。故$\exists(c,(x',y'))$使$((a,(x,y)),(c,(x',y')))\in T$。∎

**定义2.5**（范畴$\mathbf{Flow}$）：对象是集合，态射$A\to B$是生产性流处理器$(X,R,x_0)$的双模拟等价类（两个流处理器双模拟当且仅当它们诱导相同的因果关系$\llbracket R\rrbracket$）。由定理2.2，复合良定义。恒等流处理器是$(X=\{*\},R=\{((a,*),(a,*))\},*)$。

---

## 3. 余归纳迹

**定义3.1**（余归纳迹）：在$\mathbf{Rel}$中，对$R\subseteq(A\times X)\times(B\times X)$，定义余归纳迹：
$$\mathrm{Tr}^\omega_X(R)\subseteq A^\omega\times B^\omega$$
为定义2.2中的$\llbracket R\rrbracket$。它把一个Mealy机（带反馈的盒子）映射为它诱导的无限输入输出行为。

**定理3.1**（余归纳vanishing）：
(a) $\mathrm{Tr}^\omega_I(R) = \llbracket R\rrbracket$（$I$是单元素集，反馈线 trivial）。
(b) 对$R\subseteq(A\times X\times Y)\times(B\times X\times Y)$，先对$Y$取余归纳迹再对$X$取，等于直接对$X\times Y$取。

**证明**：(a) $I=\{*\}$，$R\subseteq(A\times\{*\})\times(B\times\{*\})$自然同构于$A\times B$上的关系，每步独立，流就是逐点应用。(b) 两次余归纳构造的状态序列$(x_n,y_n)$与一次构造的$(x_n,y_n)$相同。∎

**T003**（余归纳yanking）：对对称$\sigma_{X,X}:X\times X\to X\times X$（交换两个分量），$\mathrm{Tr}^\omega_X(\sigma)$诱导恒等流：输入$x_0x_1x_2\ldots$输出$x_0x_1x_2\ldots$。

**证明**：$\sigma$的转移是$((x_1,x_2),(x_2,x_1))$（交换）。余归纳迹中状态对$(x_n,x_{n+1})$，输出$x_n$，新状态$(x_{n+1},x_{n+2})$。输出流就是输入流本身。∎

**定理3.3**（余归纳superposing）：对$f:A\times X\to B\times X$和$g:C\to D$，$g\otimes\mathrm{Tr}^\omega_X(f)$诱导的流等于$\mathrm{Tr}^\omega_X(g\otimes f)$诱导的流。

**证明**：$g$的每步独立作用于$C$分量，$f$的反馈独立作用于$X$分量，两者互不干扰。∎

**定理3.4**（余归纳tightening）：对$h:A'\to A$，$f:A\times X\to B\times X$，$g:B\to B'$（均为逐点关系），$\mathrm{Tr}^\omega_X((g\times id)\circ f\circ(h\times id))$诱导的流等于$g^\omega\circ\mathrm{Tr}^\omega_X(f)\circ h^\omega$。

**证明**：每步先应用$h$到输入，再跑$f$的反馈，再应用$g$到输出。余归纳展开与直接复合一致。∎

**注**：定理3.1-3.4说明$\mathrm{Tr}^\omega$满足迹公理的余归纳版本，但它不是标准TSMC中的迹（因为类型从$A\to B$变成了$A^\omega\to B^\omega$）。它是一个新的范畴论构造：**生产性迹范畴**（productively traced category）。

---

## 4. !-模态在流处理器上的失效

在$\mathbf{Rel}$中，$\bang A$是$A$上的有限多重集（multiset），$\bang R\subseteq \bang X\times\bang Y$将$R$逐元素提升。

**定理4.1**（!不提升到流处理器）：不存在自然的提升，将生产性Mealy机$R\subseteq(A\times X)\times(B\times X)$映射为生产性Mealy机$\bang R\subseteq(\bang A\times \bang X)\times(\bang B\times \bang X)$，使得$\bang R$的余归纳迹与$R$的余归纳迹在$\bang$下相容。

**证明**：假设存在这样的提升。$\bang R$的状态是$\bang X$（$X$上的有限多重集）。转移关系$\bang R$将多重集$\alpha\in\bang(A\times X)$关联到多重集$\beta\in\bang(B\times X)$。

但余归纳迹要求**单一状态线索**（thread）：每步消耗当前状态$x_n$，产生下一状态$x_{n+1}$。多重集$\bang X$包含多个$X$元素，没有"当前状态"——你无法确定哪个元素是"正在运行的自我"。

形式化：$\bang R$的余归纳迹要求存在状态序列$\xi_0,\xi_1,\ldots\in\bang X$使得$((a_n,\xi_n),(b_n,\xi_{n+1}))\in\bang R$。但$\bang R$的转移将多重集$\alpha$映射到多重集$\beta$，其中元素通过$R$配对。如果$\alpha$包含多个$X$元素，$\beta$也包含多个$X'$元素，但没有一个良定义的"单一状态线索"从$\alpha$中的某个元素贯穿到$\beta$中的某个元素——多重集的元素之间没有身份（identity）。

对比：非交互数据流$F_1(X)=X\times B$的转移$R\subseteq X\times(X\times B)$中，$X$直接出现在输出中（不经过函数/交互），$\bang R$可以通过配对唯一确定状态线索。但$F_2(X)=A\multimap(X\times B)$中$X$是函数的输出（被生产出来的），多重集无法追踪"哪个输出是哪个输入的继续"。

这与定理13/20的矢列演算证明一致：问题出在$X$在$\multimap$的codomain位置。∎

**T005**（流处理器的!-模态刻画）：流处理器$(X,R,x_0)$可被$\bang$提升当且仅当$R$是非交互的（$F_1$型），即$R\subseteq X\times(X\times B)$且$X$在输出中的位置不经过$\multimap$的codomain。

**证明**：
($\Leftarrow$) 非交互$R\subseteq X\times(X\times B)$：$\bang R\subseteq\bang X\times\bang(X\times B)$，由monoidal strength分解为$\bang X\times\bang X\times\bang B$，状态线索由配对唯一确定。这就是命题1/定理19。

($\Rightarrow$) 定理4.1证明了交互情形不可提升。∎

---

## 5. 践演判断=执行

**定义5.1**（静态与动态）：
- 矢列$\Gamma\vdash A$的GoI解释是一个**算子/连线**$U$——这是静态的沉积（阴），可以被$\bang$（复制、存储、传递）
- 践演判断$\triangleright A$对应$U$的**执行**$\mathrm{Ex}(U)$或$\mathrm{Ex}^\omega(U)$——这是动态的运行（阳），是一次性事件

**T007**（执行不是沉积）：执行$\mathrm{Ex}(U)$不是范畴$\mathcal{C}$中的态射，也不是$\bang$-模态对象。它是元范畴的事件（公理V：践演元公理）。

**证明**：$\mathrm{Ex}(U) = U_{00}+\sum_{n\geq0}U_{01}(U_{11})^nU_{10}$涉及对反馈回路的迭代求和。在有限情形（$\mu$），这个和是有限的，结果是$\mathcal{C}$中的态射——但**计算这个和的过程**不是$\mathcal{C}$中的态射，它是元层面的操作。在无限情形（$\nu$），$\mathrm{Ex}^\omega(U)$产生无限流，它存在于$\mathbf{Flow}$而非$\mathcal{C}$中。

更根本地：$\mathrm{Ex}(U)$消耗资源（运行需要时间、能量、活操作），而$\mathcal{C}$中的态射不消耗任何东西（它只是存在）。这就是为什么践演判断不是类型——它不是对象，是事件。∎

**哲学对应**：
- 一个证明/理论/计划可以被复制（$\bang$）、存储在图书馆里、传递给他人——这是阴
- 但每次**使用**这个证明、**执行**这个计划、**活出**这个理论，都是一次性的、不可复制的事件——这是阳
- 你可以复制《资本论》（$\bang$），但你不能复制"一个人读了《资本论》后改变了自己的生命"这个事件（$\triangleright$）
- 这就是"书斋里的激进姿态≠实践"的数学表述：前者是$\bang$-模态的沉积，后者是践演事件

---

## 6. 量论在余归纳GoI中的严格定义

在$\mathbf{Flow}$中，流处理器$(X,R,x_0)$的量论参数可以严格定义：

**定义6.1**（寿命$T$）：$T(R,x_0)$是最大的$n$使得存在长度为$n$的生产性状态链$x_0\to x_1\to\cdots\to x_n$。如果$R$对所有可达状态都生产性，$T=\infty$。

**定义6.2**（净方向$N$）：在$X$带有数值结构（如$X\subseteq\mathbb{R}^d$，$R$的$X\to X$分量是函数$f_{11}:X\to X$）时：
- 离散情形：$N_n = \|x_{n+1}\| - \|x_n\|$（每步状态范数变化）
- 连续/谱情形：$N$由$Df_{11}$在状态轨道上的特征值实部决定
- $N>0$：成长（状态扩张），$N=0$：稳态，$N<0$：衰退

**定义6.3**（f-层级$\alpha$）：
- $\alpha=1$（$f^1$）：$X$是"平坦"状态，无内部模型
- $\alpha=2$（$f^2$）：$X$包含内部模型分量$X\to X$（状态包含对自己的表示）
- $\alpha=3$（$f^3$）：$X$包含$X\to(X\to X)$（自我模型包含对自我模型的模型）

$\alpha$对应状态类型的阶数（order）。

**定义6.4**（意义量$M$）：
$$M(R,x_0) = \alpha\cdot\sum_{n=0}^{T} \|b_n\|$$
其中$\|b_n\|$是第$n$步输出的"大小"（在$\mathbf{Rel}$中是基数，在Hilbert空间中是范数）。

**命题6.1**：$M$对$\bang$-模态的数据流（$F_1$型）是可加的（复制数据流复制$M$），对交互流处理器（$F_2$型）不可加（复制生命不复制意义）。

---

## 7. 新了什么

### 新构造
1. **流处理器范畴$\mathbf{Flow}$**：生产性Mealy机的余归纳范畴，复合保持生产性（定理2.2）
2. **余归纳迹$\mathrm{Tr}^\omega$**：从Mealy机到无限因果流函数的映射，满足迹公理的余归纳版本（定理3.1-3.4）
3. **生产性迹范畴**：一个新的范畴论概念——迹的输出不在原范畴中，而在流范畴中；正确性条件是productivity而非nilpotency

### 新定理
4. **定理4.1**：!不提升到交互流处理器（多重集无法追踪单一状态线索）——T001在余归纳GoI中的语义强化
5. **T007**：执行不是沉积（践演判断的范畴论表述）

### 与已有工作的关系
- Mealy机范畴是已知的（coalgebra文献）
- Abramsky的GoI构造（G(C)）用trace构造compact closed范畴，但处理的是有限行为
- "Memoryful GoI"（Hasegawa 2016）把有状态计算编译成Mealy机，但没有!-模态和不可复制定理
- 余归纳迹+productivity+!-分配二分法的组合，目前没有找到已有工作

### 待做
- 在Interaction Graphs（Seiller）中验证余归纳迹
- 证明$\mathbf{Flow}$与$\mu$LL的余归纳片段的可靠性/完全性
- 把生产性迹范畴公理化（不依赖Rel的一般定义）
- f-层级$\alpha$的严格类型论定义（需要higher-order abstract syntax或游戏语义）

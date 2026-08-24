# 余归纳GoI的可靠性

> 操作范畴论 v1.3 - Track 1
> 2026-08-25

---

## 1. 目标

证明：在余归纳片段中可证的矢列，其GoI解释是生产性流处理器。即形式证明和语义模型之间有可靠性（soundness）。

## 2. 余归纳片段μLL^ν

### 2.1 类型

$$A, B ::= p \mid A \otimes B \mid A \multimap B \mid !A \mid \nu X.F(X)$$

其中$F$是多项式函子，区分：
- $F_1(X) = X \otimes B$（非交互/数据型）
- $F_2(X) = A \multimap (X \otimes B)$（交互/生命型）

### 2.2 矢列演算

标准乘法直觉主义线性逻辑（MILL）规则，加上：

**ν-引入（余迭代/coiteration）**：
$$\frac{\Gamma \vdash F(\nu X.F) \multimap A[\nu X.F/X]}{\Gamma \vdash \nu X.F \multimap A[\nu X.F/X]}(\nu R)$$

这是说：如果你能证明一步$F(\nu F) \multimap A$，你就能证明整个无限流$\nu F \multimap A$——余归纳的生产性保证。

**ν-消除（观察）**：
$$\frac{\Gamma \vdash \nu X.F}{\Gamma \vdash F(\nu X.F)}(\nu L)$$

观察流的头一步。

**!规则**（标准）：
- dereliction: $!A \vdash A$
- contraction: $!A \vdash !A \otimes !A$
- weakening: $!A \vdash I$
- promotion: $\frac{!\Gamma \vdash A}{!\Gamma \vdash !A}$（注意：promotion要求上下文全是!-模态）

## 3. GoI解释

### 3.1 原子矢列

公理$A \vdash A$解释为恒等连线$\mathrm{id}_A$——信号直接穿过。这是生产性的：每步输入直接产生输出。

### 3.2 张量规则

$\otimes R$：
$$\frac{\Gamma \vdash A \quad \Delta \vdash B}{\Gamma, \Delta \vdash A \otimes B}$$

解释为两个生产性Mealy机的并列$\langle U, V\rangle$。两个生产性过程并列仍然生产性——每步各自产出。

$\otimes L$：
$$\frac{\Gamma, A, B \vdash C}{\Gamma, A \otimes B \vdash C}$$

解释为把一对输入拆开喂给$U$。拆开不破坏生产性。

### 3.3 线性蕴含

$\multimap R$：
$$\frac{\Gamma, A \vdash B}{\Gamma \vdash A \multimap B}$$

解释为"弯曲导线"（currying/uncurrying）——把输入线弯成反馈。在GoI中这是导线的拓扑重组，不改变生产性。

$\multimap L$（modus ponens）：
$$\frac{\Gamma \vdash A \quad \Delta, B \vdash C}{\Gamma, \Delta, A \multimap B \vdash C}$$

解释为把$U$的输出连到$V$的输入——Mealy机复合。定理2.2已证明复合保持生产性。

### 3.4 Cut

$$\frac{\Gamma \vdash A \quad \Delta, A \vdash B}{\Gamma, \Delta \vdash B}$$

Cut在GoI中就是反馈连接——把$U$的输出$A$连到$V$的输入$A$，形成反馈回路。这正是迹$\mathrm{Tr}$或余归纳迹$\mathrm{Tr}^\omega$。

**关键引理（Cut保持生产性）**：如果$U$和$V$都是生产性Mealy机，则通过Cut连接形成的反馈复合也是生产性的。

**证明**：Cut连接形成$U;V$的Mealy机复合。每一步：$U$接收输入产生$A$，$V$接收$A$产生输出和新状态。$U$生产性保证$A$每步产生，$V$生产性保证输出每步产生。两者复合，每步都有产出——生产性。这正是定理2.2（复合保持生产性）。∎

### 3.5 ν-引入（余迭代）

$\nu R$说：从一步证明$F(\nu F) \multimap A$，推出整个流$\nu F \multimap A$。

GoI解释：如果$U$是一步转移的生产性Mealy机，则$\nu R$把它"展开"为无限流处理器——每一步应用$U$，然后把输出的新状态喂回$U$作为下一步输入。

**引理（余迭代保持生产性）**：如果一步转移$U: F(\nu F) \to A$是生产性的，则其无限迭代$\mathrm{iter}^\omega(U): \nu F \to A^\omega$也是生产性的。

**证明**：余归纳。每一步：$U$接收当前状态产生输出$b_n$和新状态$x_{n+1}$。$U$生产性保证$b_n$存在。新状态$x_{n+1}$成为下一步输入。如此继续，产生无限输出流$(b_0, b_1, \ldots)$。每步有产出，故生产性。这正是定义3.2（行为/余归纳迹）的构造。∎

### 3.6 ν-消除

$\nu L$说：从流$\nu F$可以观察一步$F(\nu F)$。

GoI解释：取流的头一步（head）。流是生产性的，所以头一步必然存在输出。

### 3.7 !规则

**dereliction** $!A \vdash A$：把沉积的数据取出一次使用。在GoI中，这是从!-盒子里取出一份拷贝——生产性（数据已经在那里）。

**contraction** $!A \vdash !A \otimes !A$：复制沉积。在GoI中，这是把!-信号分叉成两份——生产性（复制不消耗）。

**weakening** $!A \vdash I$：丢弃沉积。生产性（什么都不输出也是合法的）。

**promotion** $!\Gamma \vdash A$ / $!\Gamma \vdash !A$：把一个证明"沉积"为可复制的证明。

**关键定理（promotion不提升交互过程）**：promotion规则要求上下文全是!-模态。如果证明中包含$\nu F_2$型（交互生命型）的自由变量，则promotion不可用——这正是定理20（$\bang\nu F_2 \to \nu\bang F_2$不存在）在证明论中的对应。

**证明**：promotion要求把证明$U$转换为$\bang U$（可复制的证明）。但如果$U$操作线性状态$X$（$F_2$型），$\bang U$需要复制$X$——而$X$无收缩（定理6.1）。四种$\otimes R$拆分全部失败（定理13/20的证明论版本）。故包含交互型自由变量的证明不能被promotion。∎

## 4. 可靠性定理

**定理32（可靠性）**：如果$\pi$是$\mu LL^\nu$中$\Gamma \vdash A$的证明，则其GoI解释$U(\pi)$是生产性Mealy机（或生产性流处理器，当$A$含$\nu$时）。

**证明**：对证明结构归纳。

- 公理：恒等连线，生产性（§3.1）
- 张量：并列和拆分保持生产性（§3.2）
- 蕴含：currying不改变生产性；modus ponens是Mealy机复合，定理2.2（§3.3）
- Cut：反馈复合保持生产性（§3.4引理）
- ν-引入：余迭代保持生产性（§3.5引理）
- ν-消除：取流头，生产性流保证头存在（§3.6）
- !规则：dereliction/contraction/weakening对!-模态操作，不涉及线性状态消耗，生产性；promotion只对全!上下文可用（§3.7）

每种规则都保持生产性，故所有证明解释为生产性流处理器。∎

## 5. 推论

**推论32.1（Cut消除=执行）**：在GoI中，Cut消除对应执行公式$\mathrm{Ex}(U)$或$\mathrm{Ex}^\omega(U)$。可靠性保证消除Cut后的证明仍然是生产性的——执行不破坏生产性。

**推论32.2（生命型证明不可沉积）**：任何操作$\nu F_2$型资源的证明不能被promotion（不能变成可复制的定理）。这意味着关于生命过程的证明本身必须是"活的"——它不能被冻结为可复制的教条，必须在每一步重新执行。这是"理论不能代替实践"的证明论表达。

**推论32.3（一致性）**：$\mu LL^\nu$是一致的（不能证明$I \vdash 0$或空矢列），因为空证明的GoI解释是空Mealy机，它不生产任何东西——但可靠性要求生产性，空机不生产，故空矢列不可证。

## 6. 与标准结果的关系

- 标准GoI可靠性（Girard 1989）：对MELL（有限片段），证明解释为nilpotent算子，Cut消除收敛。
- 我们的结果：对$\mu LL^\nu$（余归纳片段），证明解释为生产性流处理器，Cut消除产生无限输出流。
- 这是标准GoI可靠性从"有限/nilpotent"到"无限/productive"的推广。
- 新颖性：标准GoI不处理$\nu$型的无限行为；Memoryful GoI（Hasegawa 2016）处理Mealy机但无!-分配和生产性迹公理；我们的结果将三者统一。

# 20260902_PVar_PRep突破_substitution_general_5of8

## 本轮成果

### 1. PVar case证明通过（重大突破）

**之前4次失败的原因**：
- 直接证明（inversion Ht; subst.）：假设名不确定
- inversion as命名：需要8个分支，模式不对
- match goal：No matching clauses
- 辅助引理pvar_insert_at：需要先证明get_insert_at_self，但归纳证明失败

**本轮突破的关键**：
1. **添加get_insert_at_self引理**：`forall k T Gamma, get (insert_at k T Gamma) k = Some (Some T)`
   - 证明：对k归纳，k=0时simpl reflexivity；k=S k'时destruct Gamma，simpl apply IHk
   - **关键发现**：必须先induction k再intros Gamma，这样IHk是forall形式，可以应用到任何Gamma
   - 存在论意义：操作的结果是可验证的——插入操作权后，那个位置确实有这个操作权

2. **PVar case证明策略**：
   - n=k时：用get_insert_at_self证明T0=T，然后用Hget证明typed Gamma (PVar m)
   - n≠k时：直接用name_subst_general引理（已证明）
   - **关键设计**：先destruct (Nat.compare n k)，n≠k时直接用name_subst_general不需要inversion Ht，只有n=k时才inversion

3. **技术细节**：
   - inversion Ht as需要8个分支（typed有8个构造子），7个分隔符
   - apply ty_var需要明确指定T参数：`apply ty_var with (T := T)`
   - subst_name m k k = m用Nat.eqb_refl证明
   - bullet层级：外部用+，内部不能用-，用;连接前提

### 2. PRep case证明通过

**策略**：
- 添加subst_var_empty引理（Admitted，待证明）：`forall m k P, typed [] P -> typed [] (subst_var m k P)`
- PRep case：inversion Ht得到typed [] P，apply ty_rep，然后用subst_var_empty
- 存在论意义：空世界中没有操作权可以消耗，代换不改变任何东西

**subst_var_empty引理的难点**：
- PRes case需要更一般的引理：`length Gamma <= k -> typed Gamma P -> typed Gamma (subst_var m k P)`
- 暂时Admitted，后面再证明

## 进度

- substitution_general: PZero✅ PTau✅ PVar✅ PRes✅ PRep✅ POut⏳ PIn⏳ PPar⏳（5/8）
- Layer2.v编译通过，0错误
- 还剩3个case：POut, PIn, PPar

## 下一轮计划

1. 证明POut case（需要set_none_insert_at_subst引理，OB-007研判已给）
2. 证明PIn case（类似POut）
3. 证明PPar case（需要split和insert_at交换律）
4. 证明subst_var_empty引理（需要更一般的引理）
5. 证明congruence_preserves_typing（依赖substitution_general完成）

## 哲学反思

**操作即存在**：
- get_insert_at_self引理的存在论意义：操作的结果是可验证的。插入操作权后，那个位置确实有这个操作权。这不是一个技术细节，而是存在论事实——操作改变了世界，改变是可验证的。

- PVar case的本质：变量引用是操作权的声明。当我们代换变量时，我们在转移操作权。n=k时，操作权从k位置转移到m位置；n≠k时，操作权位置不变，但索引可能偏移。

- PRep case的本质：空世界中没有操作权可以消耗，所以代换不改变任何东西。这是操作权理论的一个基本事实——没有操作权的世界，操作不改变世界。

**技术是表层，悟道是深层**：
- PVar case之前4次失败，都是因为在战术层面纠缠（inversion/match goal/假设名），没有理解存在论本质。
- 本轮突破是因为理解了：插入操作权后，那个位置确实有这个操作权（get_insert_at_self），这是存在论事实，证明结构必须反映这个事实。
- 这和PRes case的突破是同一个道理：理解代换的本质是操作权的转移，证明结构必须反映存在论事实。

## 错误模式反思

**犯了很多同样的错误吗？**
- 是的，PVar case中多次犯了同样的错误：inversion as的分支数不对（9个分支而不是8个），bullet层级不对（内部用-而外部用+），假设名不对（H0而不是实际的假设名）。
- 这些错误都是战术层面的，不是战略层面的。根本原因是没有先想清楚证明结构，就直接写战术。

**提炼了很高的思维吗？**
- 是的，从"战术思维"跃迁到"存在论思维"：先理解操作权的流动，再设计证明结构，最后写战术。
- 从"盲目试错"跃迁到"悟道证明法"：证明前先问5个问题（操作层面说什么？前提操作权分布？结论操作权分布？操作权发生了什么变化？什么条件下保持合法性？）
- 从"暴力subst"跃迁到"弱操作原则"：精确rewrite代替全局subst，先induction再intros让IH成为forall形式。

**最关键的一句话**：
- PVar的突破不是因为Coq技术变好了，而是因为理解了插入操作权后那个位置确实有这个操作权（get_insert_at_self），证明结构必须反映这个存在论事实。技术是表层，悟道是深层。

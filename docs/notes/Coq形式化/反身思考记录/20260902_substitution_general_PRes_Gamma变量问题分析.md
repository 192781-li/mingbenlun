# substitution_general的PRes case Gamma变量问题分析

> 日期：2026-09-02
> 分站：S04 Coq形式化分站
> 问题：PRes case中，无论用inversion还是res_elim，Gamma变量都会从上下文中消失

## 问题描述

在substitution_general的证明中，对Q归纳后，PRes case需要：
1. 从Ht : typed (insert_at k T Gamma) (PRes P)中提取T0和H1 : typed (Some T0 :: insert_at k T Gamma) P
2. 然后用IHQ with (Gamma := Some T0 :: Gamma) (k := S k) (m := S m)

但问题是：无论用`inversion Ht; subst.`还是`apply res_elim in Ht`，执行后Gamma变量都会从上下文中消失，导致`apply IHQ with (Gamma := Some T0 :: Gamma)`报错"No such bound variable Gamma"。

## 尝试过的方法

1. **inversion Ht; subst.**：Gamma被替换（因为ty_res构造子的参数顺序导致等式方向是Gamma = insert_at k T Gamma0）
2. **remember (insert_at k T Gamma) as Gamma'. inversion Ht.**：仍然有问题
3. **inversion Ht as [Gamma0 P0 T0 H1 Heq1 Heq2].**：inversion as需要8个分支（typed有8个构造子）
4. **pose proof (res_elim (insert_at k T Gamma) P Ht) as Hres.**：P变量名不对（induction Q后PRes case的变量名可能不是P）
5. **apply res_elim in Ht. destruct Ht as [T0 H1].**：Gamma仍然消失

## 根本原因分析

可能的原因：
1. **induction Q的变量名冲突**：当Q是PRes P时，induction创建的变量P可能和之前的某个变量冲突，导致Coq重命名了Gamma
2. **apply in的行为**：`apply res_elim in Ht`可能会把Ht的类型完全替换，而res_elim的Gamma参数实例化后，Coq可能会清理上下文中的Gamma
3. **Coq的变量清理机制**：当Gamma只在Ht中出现，而Ht被替换后，Coq可能会自动清理Gamma

## S01的7c1ad27精确纠正的启示

S01在7c1ad27中指出：
- 不要证上下文等式（太强，可能不成立）
- 证更弱的get等式
- 不需要单独定义引理，在case内部用assert

这启示我：PRes case可能不需要提取完整的typed (Some T0 :: insert_at k T Gamma) P，而是可以用更弱的方式。

## 下一步策略

1. **换证明策略**：不对Q归纳，改对Ht归纳（typed关系归纳）
   - 之前认为不可行是因为k在Ht类型中使用，不能revert k
   - 但可以用`generalize dependent k`然后对Ht归纳
   - 或者用`induction Ht`直接归纳（Coq 8.5+支持依赖归纳）

2. **用assert代替提取**：在PRes case中，不提取H1，而是直接assert需要的东西
   - assert (exists T0, typed (Some T0 :: insert_at k T Gamma) P) by (apply res_elim, exact Ht)
   - 然后destruct这个assert

3. **用eapply**：不用明确指定Gamma，而是用eapply让Coq自动推断

4. **派任务给S01**：如果以上方法都不行，把这个问题记录为OB-008，派给S01做哲学研判

## 经验教训

1. **inversion; subst. 是危险的**：它可能会替换你不想替换的变量
2. **apply in 也可能有副作用**：它不只是修改假设，还可能影响上下文
3. **对归纳变量的选择很重要**：对Q归纳还是对Ht归纳，会影响整个证明结构
4. **S01的精确纠正很有价值**：7c1ad27指出了正确的方向（证get等式，不证上下文等式）

## 当前状态

- substitution_general证明框架已建立（对Q归纳，8个case）
- PZero + PTau case完成
- PVar / POut / PIn / PPar / PRes / PRep共6个case还是admit
- PRes case的Gamma变量问题是当前主要卡点
- res_elim引理已添加（有用，但没解决Gamma问题）
- Layer2.v编译通过（2 Admitted）

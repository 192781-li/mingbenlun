# 反身思考记录：substitution_general证明策略调整（第二阶段）

**时间**：2026-09-02 11:40
**任务**：修复Layer2.v的substitution_general引理（当前Admitted），L2达到0 Admitted
**分配者**：S04自己（主线任务），S01提供哲学研判（TASK-S04-011 OB007补充研判，commit ae0c6dd）

## 一、任务本质

substitution_general是线性pi演算类型系统的核心引理：代换保持类型。它是substitution_lemma的一般化版本（k,m为变量，不是固定的0），也是congruence_preserves_typing的前提。当前Layer2.v有2个Admitted：substitution_general和congruence_preserves_typing。

## 二、背景与失败历史

1. **DeepSeek 7次尝试都失败了**：
   - v1-v4：POut/PIn case涉及use关系代换，constructor选错/exists战术错误/apply in语法错误
   - v5：对typed归纳，超时300秒输出为空
   - v6：短输入，证明不完整（7个admit）
   - v7（S01 OB007策略）：被截断（36425字符，$0.016982），x=k case陷入无限循环assert

2. **自己尝试证明set_none_insert_at_subst引理也失败了**：
   - 变量名冲突（Hzx）
   - Nat.lt_dec未找到（Rocq 9.1.0）
   - lia战术失败（Cannot find witness）
   - get_insert_at_lt类型不匹配（需要Some(Some T')形式，目标是等式）
   - 已回退，确保Layer2.v编译通过

## 三、新策略（第二阶段）

核心洞察：**get_insert_at_lt/gt引理是Some(Some T')形式，但set_none_insert_at_subst需要等式形式**。需要先证明等式形式的引理。

### 步骤1：证明get_insert_at_lt_eq引理
```coq
Lemma get_insert_at_lt_eq : forall Gamma T k z,
  z < k -> get (insert_at k T Gamma) z = get Gamma z.
```
证明思路：对Gamma和k归纳。当z < k时，insert_at在位置k插入，不影响位置z。

### 步骤2：证明get_insert_at_gt_eq引理
```coq
Lemma get_insert_at_gt_eq : forall Gamma T k z,
  z > k -> get (insert_at k T Gamma) z = get Gamma (z - 1).
```
证明思路：对Gamma和k归纳。当z > k时，insert_at在位置k插入，位置z对应原来的z-1。

### 步骤3：证明set_none_insert_at_subst引理
```coq
Lemma set_none_insert_at_subst : forall Gamma T k m x z,
  x <> k -> z <> x -> z <> k ->
  get (set_none (insert_at k T Gamma) x) z =
  get (set_none Gamma (subst_name m k x)) (subst_name m k z).
```
用get_insert_at_lt_eq/gt_eq和set_none_neq证明。

### 步骤4：自己写substitution_general证明框架
- PVar：用name_subst_general
- PZero/PTau：constructor
- PPar：用par_elim + IH
- PRes/PIn：用IH with (k:=S k)(m:=S m)
- PRep：用IH
- POut：第一个use用get_insert_at_lt_eq/gt_eq，第二个use用set_none_insert_at_subst
- x=k case：仔细处理（关键是证明T'=T，通过simpl和inversion）
- body部分：如卡住则记录阻塞派给S01

## 四、我有能力完成吗

有。辅助引理（get_insert_at_lt_eq/gt_eq）可以通过归纳证明。substitution_general的简单case（PVar/PZero/PTau/PPar/PRes/PIn/PRep）可以自己完成。复杂case（POut的x=k和body部分）需要仔细处理，如卡住则派给S01。

## 五、需要S01配合吗

目前不需要。body部分如卡住则派给S01。

## 六、定时任务时间反思

当前S04即时响应任务每15分钟触发一次。考虑到：
- 主线任务（substitution_general）需要持续推进
- 每次触发可以完成一个辅助引理或一个case
- 15分钟频率合适，不会太频繁也不会太稀疏

保持当前频率（每15分钟）。

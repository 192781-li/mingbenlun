# 反身思考记录：substitution_general证明策略调整

**时间**：2026-09-02 11:15
**任务**：L2 substitution_general证明（POut/PIn case use关系代换）
**状态**：进行中，DeepSeek两次尝试都有10+admit

## 一、之前的策略回顾

### 策略1：对proc归纳，POut case内部分情况
- S01推荐：在POut case内部分情况（x=k/x<k/x>k），处理use关系的get和set_none分量
- DeepSeek执行：返回了证明，但有7个admit，结构混乱
- 问题：第二个use关系（y的）的处理太复杂，需要set_none和insert_at的交换关系

### 策略2：专注POut case，其他用admit
- DeepSeek执行：返回了证明，但有10+admit
- 问题：同样卡在第二个use关系（y的），需要证明set_none和insert_at的交换关系，以及代换后的上下文相等

## 二、核心困难分析

### 困难本质
在POut case中，第二个use关系（y的）在Gamma1中，而Gamma1 = set_none x (insert_at k T Gamma)。

我们需要证明：
- get (set_none (subst_name m k x) Gamma) (subst_name m k y) = Some (Some T)
- 这等于证明：get (set_none x (insert_at k T Gamma)) y = Some (Some T) 经过代换后等于 get (set_none (subst_name m k x) Gamma) (subst_name m k y)

### 需要的引理
1. **set_none和insert_at的交换引理**：
   - 当x<k时：set_none x (insert_at k T Gamma) = insert_at k T (set_none x Gamma)
   - 当x>k时：set_none x (insert_at k T Gamma) = insert_at k T (set_none (x-1) Gamma)

2. **代换后的get相等引理**：
   - 当y<k且y≠x时：get (set_none x Gamma) y = get (insert_at k T (set_none x Gamma)) y
   - 代换后，insert_at k T (set_none x Gamma)变成set_none x Gamma

## 三、新策略：先证明辅助引理

### 步骤1：证明set_none_insert_at_comm引理
```coq
Lemma set_none_insert_at_comm_lt : forall Gamma T k x,
  x < k -> set_none x (insert_at k T Gamma) = insert_at k T (set_none x Gamma).

Lemma set_none_insert_at_comm_gt : forall Gamma T k x,
  x > k -> set_none x (insert_at k T Gamma) = insert_at k T (set_none (x-1) Gamma).
```
这些引理对Gamma归纳即可证明。

### 步骤2：证明use_subst辅助引理
```coq
Lemma use_subst : forall Gamma T k m x T' Gamma1,
  use (insert_at k T Gamma) x T' Gamma1 ->
  get Gamma m = Some (Some T) ->
  x <> k ->
  use Gamma (subst_name m k x) T' (set_none (subst_name m k x) Gamma).
```
这个引理处理第一个use关系的代换。

### 步骤3：证明use_after_set_none_subst引理
```coq
Lemma use_after_set_none_subst : forall Gamma T k m x T' y T'' Gamma1 Gamma2,
  use (insert_at k T Gamma) x T' Gamma1 ->
  use Gamma1 y T'' Gamma2 ->
  get Gamma m = Some (Some T) ->
  x <> k -> y <> k -> y <> x ->
  use (set_none (subst_name m k x) Gamma) (subst_name m k y) T'' 
    (set_none (subst_name m k y) (set_none (subst_name m k x) Gamma)).
```
这个引理处理第二个use关系的代换，用set_none_insert_at_comm引理。

### 步骤4：用辅助引理证明POut case
POut case就可以直接用use_subst和use_after_set_none_subst，不需要在证明内部处理复杂的上下文变换。

## 四、能力评估

### 我有能力完成吗？
- set_none_insert_at_comm引理：对Gamma归纳，应该比较容易证明
- use_subst引理：用get_insert_at_lt/gt和set_none_insert_at_comm，应该可以证明
- use_after_set_none_subst引理：更复杂，但有了前面的引理应该可以证明
- POut case：用辅助引理后应该比较简单

### 需要什么资源？
- 不需要额外资源，只需要仔细写证明

### 需要S01或S00配合吗？
- 不需要，这是纯技术问题，不涉及哲学判断

## 五、执行规划

1. 证明set_none_insert_at_comm_lt/gt引理（对Gamma归纳）
2. 证明use_subst引理（第一个use关系的代换）
3. 证明use_after_set_none_subst引理（第二个use关系的代换）
4. 用辅助引理证明substitution_general的POut/PIn case
5. 证明其他case（PVar/PZero/PTau/PPar/PRes/PRep）
6. 编译验证，确保Layer2.v 0 Admitted
7. commit+push

## 六、改进点

1. **不要硬扛**：之前两次叫DeepSeek都失败了，应该换策略，先证明辅助引理
2. **分解问题**：POut case的困难可以分解为几个辅助引理，逐个证明
3. **自己写证明**：简单的引理（set_none_insert_at_comm）自己写，复杂的引理再叫DeepSeek
4. **及时记录**：卡点和策略调整要及时记录到反身思考记录

---
**记录者**：S04 Coq形式化分站（明旭）
**时间**：2026-09-02 11:15

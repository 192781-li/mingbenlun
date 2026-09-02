# 反身思考记录：substitution_general证明卡点分析

**时间**：2026-09-02 10:45
**任务**：L2 substitution_general证明（POut/PIn case use关系代换）
**状态**：Admitted，已重试5次，超过3次限制

## 一、任务本质分析

### 这个任务本质是什么？
substitution_general是类型系统的基本性质——代换保持类型（substitution preserves typing）。在pi演算的线性类型系统中，代换引理是subject_reduction（主体归约）的前提，也是congruence_preserves_typing的前提。

### 谁分配的？
S01哲学分站在TASK-S04-008中做了哲学研判，推荐先证general版本（k,m为变量），因为PIn/PRes case中k会变成1。S01还给出了精确证明骨架（commit 4a7defa）。

### 背景是什么？
- subst_var定义已修复（PIn/PRes case中m改为S m）
- get_insert_at_lt/gt已证明
- name_subst_general已证明
- substitution_lemma已改为用substitution_general证明（3行，但依赖Admitted的substitution_general）
- congruence_preserves_typing仍Admitted（依赖substitution_general）

## 二、能力评估

### 我有能力完成吗？
技术上，substitution_general是标准的类型系统性质，在许多pi演算形式化中都有证明。但当前的困难在于：
1. use关系的代换复杂——use定义为get /\ set_none，代换后第二个use关系（z的）依赖第一个use关系的结果Gamma1'
2. Gamma1' = set_none Gamma (subst_name m k x)，而原来的Gamma1 = set_none (insert_at k T Gamma) x，这两个不一定相等
3. DeepSeek 5次尝试都失败了，说明这个问题比预想的复杂

### 需要什么资源？
- 可能需要证明一个辅助引理use_substitution，处理use关系的代换
- 或者需要派任务给S01做哲学研判：代换在存在论上意味着什么？use关系中的"使用"在代换后是否保持？
- 或者需要重新审视证明策略：对typed归纳而不是对proc归纳

## 三、执行规划

### 分几步完成？
1. **分析卡点**：深入理解use关系代换的困难所在
2. **尝试辅助引理**：证明use_substitution辅助引理
3. **应用辅助引理**：用use_substitution证明POut/PIn case
4. **编译验证**：确保整个Layer2.v编译通过
5. **继续congruence**：substitution_general完成后，证明congruence_preserves_typing

### 每步产出什么？
1. 卡点分析记录
2. use_substitution引理证明
3. substitution_general完整证明
4. 编译通过的Layer2.v
5. congruence_preserves_typing证明

### 需要S01或S00配合吗？
可能需要S01做哲学研判：
- 代换在存在论上意味着什么？
- use关系中的"使用"在代换后是否保持？
- 如果use关系的代换在哲学上不成立，是否需要调整类型系统的设计？

## 四、之前失败的原因反思

### 5次失败的共同原因
1. **对proc归纳时，POut case的use关系代换没有正确处理**——DeepSeek试图用name_subst_general直接证明use关系，但name_subst_general证明的是typed关系，不是use关系
2. **第二个use关系（z的）依赖第一个use关系的结果Gamma1'**——DeepSeek没有处理这个依赖关系
3. **对typed归纳的尝试超时了**——输入太长，DeepSeek API超时

### 根本原因
use关系的代换不是简单的变量重命名，它涉及上下文的变换（set_none），而代换后的上下文和原来的上下文之间的关系不明确。这可能需要一个专门的辅助引理来处理。

## 五、改进点

1. **不要硬扛**：已经重试5次，超过3次限制，应该停下来，要么证明辅助引理，要么派任务给S01
2. **深入理解卡点**：不要只叫DeepSeek，要自己分析use关系代换的困难所在
3. **考虑替代方案**：对typed归纳、证明辅助引理、或者调整类型系统设计
4. **及时同步**：卡点应该及时记录到obstacles目录，并派任务给S01

## 六、下一步行动

1. **记录卡点到obstacles目录**：创建OB-007记录substitution_general的use关系代换卡点
2. **派任务给S01做哲学研判**：代换在存在论上意味着什么？use关系中的"使用"在代换后是否保持？
3. **同时尝试技术方案**：证明use_substitution辅助引理
4. **等S01回复后**：根据哲学研判结果调整证明策略

---
**记录者**：S04 Coq形式化分站（明旭）
**时间**：2026-09-02 10:45

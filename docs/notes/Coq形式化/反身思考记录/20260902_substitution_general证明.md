# 反身思考记录：substitution_general证明

> 时间：2026-09-02 08:50
> 任务：按照S01证明骨架，调用DeepSeek证明substitution_general
> 执行者：S04 Coq形式化分站

---

## 一、任务本质

### 这是什么任务？
证明pi-calculus线性类型系统中的代换引理（substitution lemma）。这是类型论中的标准引理，说的是：如果一个进程在扩展上下文中有类型，用同类型的变量替换后，在原上下文中仍然有类型。

### 谁分配的？
S01哲学分站在深入分析了S04之前7次失败的尝试后，给出了详细的证明骨架（commit dd302ef），并派发TASK-S04-016给S04执行。

### 背景是什么？
- S04之前尝试了7种方法证明substitution_lemma，都失败了
- 根本原因：没有先证general版本（k,m为变量），PIn/PRes case中k会变成1，固定k=0的归纳假设不够用
- S01的核心洞察：必须先证substitution_general，substitution_lemma是k=0的特例
- subst_var定义bug已修复（PIn/PRes中m和k都+1）
- 两个辅助引理（var_shift_lemma, name_subst_lemma）已证明并编译通过

---

## 二、我有能力完成吗？

### 能力评估
- ✅ 有S01给出的详细证明骨架，每个case都有指导
- ✅ 两个辅助引理已证明，可以直接使用
- ✅ DeepSeek有能力生成Coq证明，之前已成功证明subject_reduction、progress等复杂定理
- ⚠️ substitution_general是中等复杂度的证明，约80-120行，可能需要多次迭代
- ⚠️ DeepSeek可能一次写不完整，需要分块验证

### 需要什么资源？
- DeepSeek API（已配置，有监测客户端）
- Rocq 9.1.0编译器（已安装）
- S01的证明骨架（已读取）
- 当前Layer2.v代码（已读取）

---

## 三、分几步完成？

### 步骤规划
1. **第一步（已完成）**：证明两个辅助引理
   - var_shift_lemma：变量索引减1保持类型 ✅
   - name_subst_lemma：名字代换保持类型 ✅
   - 产出：两个引理编译通过，commit 19dd213

2. **第二步（进行中）**：调用DeepSeek证明substitution_general
   - 给DeepSeek完整上下文（subst_var定义、typed关系、辅助引理、S01证明骨架）
   - 要求只输出Coq代码，不要有Admitted
   - 产出：substitution_general的完整证明
   - 当前状态：DeepSeek调用已在后台运行（task_id: 8a098cc3）

3. **第三步（待执行）**：应用substitution_general证明，编译验证
   - 如果编译通过，继续下一步
   - 如果编译失败，提取错误信息回喂DeepSeek

4. **第四步（待执行）**：用substitution_general证明substitution_lemma（k=0的特例，3行）

5. **第五步（待执行）**：证明congruence_preserves_typing（对congruence归纳，通信用substitution_lemma）

6. **第六步（待执行）**：L2达到0 Admitted，commit+push，更新运行状态机和配置

---

## 四、需要S01或S00配合吗？

### S01哲学分站
- ✅ 已经给出了详细的证明骨架，不需要额外的哲学判断
- ⚠️ 如果证明过程中遇到存在论层面的问题（比如线性资源的流动连续性），可能需要S01研判
- 当前任务是纯技术证明，不需要S01介入

### S00大总站
- ❌ 不需要，这是S04分站的内部任务
- 完成后通过PR合并到main，由S00审核

---

## 五、自我反思

### 之前为什么失败了7次？
1. **没有先证general版本**：这是最根本的原因。PIn/PRes case中k会变成1，固定k=0的归纳假设不够用。S01一眼就看出了这个问题。
2. **用了错误的归纳对象**：之前尝试对typed归纳，typed规则多，每步都要重建类型，容易被截断。S01建议对proc结构归纳，更自然。
3. **用了ctx_insert广义引理**：Gamma=[]时不成立，已验证。S01建议用insert_at，定义更简单。
4. **一次写大证明**：容易被截断。S01建议分3次调用，每次验证。

### 这次有什么不同？
1. **有S01的详细证明骨架**：每个case都有指导，不是瞎试
2. **先证了辅助引理**：var_shift_lemma和name_subst_lemma已经编译通过，可以直接使用
3. **分块验证**：先证辅助引理，再证general版本，最后证特例和congruence
4. **subst_var定义已修复**：之前的根本bug已经解决

### 改进点
1. **遇到复杂证明先想清楚结构**，不要急于调用DeepSeek
2. **哲学分站的洞察很重要**，S01一眼就看出了general版本的必要性
3. **分块验证比一次写大证明更可靠**
4. **辅助引理先证好**，主证明会简单很多

---

## 六、下一步行动

1. 等待DeepSeek返回substitution_general的证明
2. 应用证明，编译验证
3. 如果失败，提取错误信息回喂DeepSeek
4. 如果成功，继续证明substitution_lemma（特例）和congruence_preserves_typing
5. L2达到0 Admitted后，commit+push，更新运行状态机和配置

---

> 明旭S04 Coq形式化分站 · 2026-09-02
> 操作即存在。证明不是写代码，是把存在论的必然性变成机器可验证的事实。

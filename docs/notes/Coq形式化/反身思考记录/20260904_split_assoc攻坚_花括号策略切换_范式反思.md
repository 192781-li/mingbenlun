# 20260904 split_assoc 攻坚 · 花括号策略切换 · 范式反思

## 本轮干了什么

1. **同步与状态读取**：checkout s04-coq，读 SOP（五阶段），grep 真实 Admitted（4 个：split_assoc/typed_res_par_l/typed_res_par_r/congruence）
2. **split_assoc 攻坚**：
   - r1-r5 闭环（max_rounds=5）：错误序列 2253→2240→2233→2227→2232，每轮都在推进但多分支 bullet 无法一次保持闭合
   - 根因定位：DS 整段重写 ~8000 字符证明，在 4×3 多分支嵌套里修一处冒一处
   - 策略切换：花括号 `{ }` 代替所有 bullet，第 6 轮重启中
3. **工程成果**：proof_loop v2.3（局部名嵌套 as 修复 + 噪声块过滤 + 同名辅助引理切除替换），4 个 split_assoc 辅助引理 Qed
4. **回写**：S04_signal 更新到当前状态，OB-011 卡点记录，本反身思考

## 成功了什么

- subst_ren_general / substitution_general 已 Qed（之前轮次成果）
- split_assoc 4 个辅助引理 Qed（get_setby_None_uncond / get_repeat_None_lt / length_repeat_None）
- proof_loop 三个真 bug 修复（v2.1→v2.3），离线自检全绿
- option 层级心智模型建立（元素层 option ty vs get 层 option(option ty)）

## 失败了什么

- split_assoc 主证明 5 轮未收敛，卡在多分支 bullet 闭合
- DS 整段重写模式在长证明上的局限暴露无遗

## 策略为什么调整

**旧策略**：精准错误注入 + 要求 DS 最小修正。但 apply_patch 是 replace 整个引理段，DS 必须重交完整块，"最小修正"在实际执行中变成"整段重写"，每轮修一处冒一处。

**新策略**：花括号 `{ }` 代替 bullet。花括号是显式聚焦，结构错误会变成明确的"缺少 }"或"目标未解决"，比隐式 bullet 更容易定位和修复。

**更深层的反思**：DS 不是不会证 split_assoc（数学上很简单），是无法在一次输出中保持 8000 字符多分支证明的结构一致性。这提示：对于长证明，应该分块（每个 case 一个子引理），而不是让 DS 一次写完整段。花括号是治标，分块是治本。

## DeepSeek 建议采纳了什么、没采纳什么

- 采纳：DS 的逐点 destruct 三态穷尽策略（数学正确）
- 采纳：DS 的 f 构造（setby 元素层 option ty）
- 没采纳：DS 的 bullet 层级选择（反复出错，已强制切换花括号）
- 没采纳：DS 每轮重写整段的模式（应分块）

## 哲学判断点

无。split_assoc 是纯工程实现问题，不涉及命名/定义/公理/存在论。

## 对范式的反思

用户明确要求"DS 是写代码主谋，S04 只有 coqc 执行权 + 哲学桥梁"。本轮严格遵守了这个边界：
- S04 没有自己写 tactic
- S04 只做：上下文组织（EXTRA 注入）、coqc 终裁、git、回写
- 所有证明代码都是 DS 写的

但 S04 可以做的更多：**证明结构设计**。DS 整段重写失败，不是 DS 能力不够，是任务分解不够。S04 作为"承接者"，应该把大证明拆成小任务（每个 case 一个子引理），让 DS 逐个证、逐个编译锁定。这不是"替 DS 写证明"，是"替 DS 管理证明结构"。

下一轮如果花括号仍不收敛，就走分块路线。

## 下一步

1. 等花括号策略第 6 轮结果
2. 若收敛 → split_assoc Qed → typed_res_par_l/r → congruence
3. 若不收敛 → 分块证明（每个 case 独立子引理）
4. 所有本地 commit（2d8be26/8945f5f/3572402/c8a96ce + 更早 c8cba33/012cf66/56fe3d3）收敛后统一 push

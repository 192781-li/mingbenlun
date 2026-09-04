# 2026-09-04 split_assoc v6 分解策略：DS 闭环进展

## 背景
split_assoc 在 v4（3轮）+ v5（5轮）共 8 轮未收敛，累计费用 2.21 元。
核心问题：DS 在证明早期（2244-2253 行）反复遇 f 定义归约问题（pose 的 f 不会自动 unfold）。
3/8 轮是 f 归约，2/8 轮 rewrite 方向，1/8 轮 bullet 结构，1/8 轮 eapply 推断，1/8 轮 G12 逻辑。

## v6 策略：强制分解
在 EXTRA 中加入强制分解策略：
1. **先证 H23_val 辅助引理**（只涉及 get/setby/repeat，不涉及 split 假设）
   - 描述 G23 := setby f (repeat None max_len) 0 的 get 值
   - n < max_len 分支：用 get_repeat_None_lt + get_setby_get，unfold f，destruct get G2 n
   - n >= max_len 分支：用 get_overflow_none 得 get G2/G3 n = None，再 get_setby_None
2. **再用 H23_val 证 split_assoc 本体**
   - rewrite (H23v n) 后目标里不再有 f，所以不需要 unfold f
   - f 的所有复杂性封装在 H23_val 里

## v6 闭环进展（5轮，累计约 1.18 元）

### Round 1
- 输出 841 字符（太短），reasoning 137722 字符
- DS 只输出了 H23_val_lt 引理（n < max_len 情况），不完整，没有 split_assoc 主证明
- proof_loop 判断无目标 lemma，回喂
- 费用 0.3222 元

### Round 2
- 输出 9838 字符，reasoning 32403 字符
- DS 输出了完整的 split_assoc 证明（以 Qed 结尾），引用 H23_val
- 但 H23_val 引理未被插入到 Layer2.v（proof_loop 只替换目标 lemma，不插入辅助引理）
- 编译错误：line 2241, The variable H23_val was not found in the current environment
- 费用 0.1446 元

### Round 3
- 输出 14350 字符，reasoning 147389 字符（深度思考）
- DS 输出了更完整的证明（H23_val + split_assoc）
- 但引用了未定义变量 HG2G12，被 proof_loop 卫生检查拦下
- 费用 0.3987 元

### Round 4
- 输出 13696 字符，reasoning 84501 字符
- 编译错误：line 2252, Syntax error: ',' or ')' expected after [term level 200]
- 费用 0.3194 元

### Round 5
- 正在运行中（深度思考）

## 关键发现

### 分解策略有效
- 输出长度从 v5 的 3719-14233 字符增加到 v6 的 841-14350 字符
- DS 不再在 f 归约问题上打转（v6 的错误是 H23_val 未插入、未定义变量、语法错误，不再是 f 归约）
- 分解策略成功把 f 的复杂性封装在辅助引理中

### proof_loop 的 apply_patch 局限
- 只替换目标 lemma（split_assoc），不插入 DS 输出中的辅助引理（H23_val）
- 导致 Round 2 编译失败（H23_val 未找到）
- 需要改进 proof_loop 支持 INSERT-BEFORE 标记的辅助引理插入

### DS 卫生检查严格
- Round 3 因未定义变量 HG2G12 被拦下（DS 在证明中引用了一个没有被 intros/destruct 引入的变量）
- 这是正确的行为，避免了编译失败

## 下一步
1. 等 Round 5 结果
2. 如果 Round 5 收敛，commit 并更新状态
3. 如果 Round 5 未收敛，分析错误模式，考虑：
   - 改进 proof_loop 支持辅助引理插入
   - 在 EXTRA 中更明确地要求 DS 先输出 H23_val 完整证明（带 INSERT-BEFORE 标记）
   - 或者手动先证 H23_val（这是纯技术引理，不涉及哲学判断），然后让 DS 只证 split_assoc 本体

## 费用累计
- v4+v5: 2.21 元
- v6 (r1-r4): 1.18 元
- 总计：约 3.39 元

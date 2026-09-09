# split_assoc 根本原因发现：DS 证明结构性不完整（4/9 分支）

## 时间
2026-09-04

## 背景
split_assoc 是 Layer2 最后 4 个 Admitted 之一。之前 DS r3 给出了完整证明（14788 字符），执行方应用到 Layer2 后进行了大量机械修正（36 处 rewrite/discriminate 替换、14 处 congruence 替换、2 处 Hs1r/Hs2r 分支逻辑修复），但编译始终逐行报错，始终无法收敛。

## 根本原因发现
今天仔细分析 DS r3 原始证明的结构后发现：

\\\coq
destruct (get G2 n) as [[a|]|] eqn:EG2;   (* 3 种情况 *)
destruct (get G3 n) as [[b|]|] eqn:EG3.   (* 3 种情况 *)
\\\

这创建 **9 个分支**（3×3），但 DS 每个目标只写了 **4 个** \*\ 分支，**省略了 5 个**：
- G2=Some None 的全部 3 个分支
- G2=Some(Some a), G3=Some None 的 1 个分支
- G2=None, G3=Some None 的 1 个分支

**后果**：bullet 结构混乱，后续分支中 \Hs1\/\Hs1l\ 变量不存在（\Hs1l not found\），所有机械修正都无法解决——因为缺的是整个分支，不是某个 tactic 错误。

## 错误反思
### 反复犯的同样错误
在单个 tactic 层面死磕（rewrite 方向、congruence、inversion 各种替换），没有跳出来检查证明的整体结构是否完整。

### 思维提升
以后遇到"逐行报错、机械修正触及瓶颈"时，必须先停下来检查：
1. 证明的分支结构是否完整？（destruct 创建了 N 个分支，实际处理了几个？）
2. 变量作用域是否正确？（某个分支中变量不存在，说明 bullet 结构有问题）
3. 是 tactic 错误还是结构性缺失？

### 关键经验
- \destruct (get G n) as [[a|]|]\ 会把上下文中所有 \get G n\ 替换为构造子，后续假设中不再含 \get G n\ 子项
- G3s/G2s/G12s 分支（= Some None）需要 inversion 而非 discriminate
- Hs1r/Hs2r 分支不能忽略左合取支 \get G2 n = get G12 n\
- simpl 会改变 Hs1 类型导致 destruct as 模式不匹配

## 下一步
已将 split_assoc 回退为 Admitted，更新 run_split_assoc.py 的 EXTRA 明确指出 9 分支问题，重新调用 DS V4 闭环生成完整证明。DS 正在后台运行中（上下文 51230 token，deepseek-v4-pro 思考模式）。

## 自我总结
这次干得怎么样？——最终找到了根本原因，但花了太多时间在机械修正上。改进：以后遇到机械修正超过 3 处仍不收敛，必须停下来检查证明结构完整性，不要在 tactic 层面死磕。

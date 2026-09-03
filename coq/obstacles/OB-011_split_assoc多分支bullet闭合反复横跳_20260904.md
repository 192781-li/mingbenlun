# OB-011 split_assoc 主证明多分支 bullet 闭合反复横跳

**编号**：OB-011
**日期**：2026-09-04
**状态**：处理中（已切花括号策略）
**所在文件/定理**：coq/theories/ALL/Layer2.v，Lemma split_assoc（约 2201 行）
**阻碍本质**：纯技术（工程实现），不涉及哲学判断

## 阻碍描述

split_assoc 命题：`forall G G12 G3 G1 G2, split G G12 G3 -> split G12 G1 G2 -> exists G23, split G G1 G23 /\ split G23 G2 G3`

DS 采用逐点 destruct 三态穷尽策略（对每个 n，资源在 G3/G1/G2 三种情形），证明骨架正确，f 构造正确，4 个辅助引理已 Qed。但主证明在多分支嵌套 bullet 结构上反复横跳，5 轮未收敛。

## 错误序列（5 轮）

| 轮次 | 错误行 | 错误内容 |
|------|--------|----------|
| r1 | 2253 | `The variable H1e was not found in the current environment`（destruct 模式变量名不匹配） |
| r2 | 2240 | `Found no subterm matching get (setby f G 0) n`（rewrite 目标不存在） |
| r3 | 2233 | `Wrong bullet --: Current bullet ++ is not finished`（bullet ++ 未闭合） |
| r4 | 2227 | `Found no subterm matching ?M1354 + 0 in HG23`（change 子项不匹配） |
| r5 | 2232 | `Wrong bullet *: Current bullet -- is not finished`（bullet -- 未闭合） |

## 根因分析

DS 每次重写整段 ~8000 字符证明，在 4×3 多分支嵌套（destruct Hs1 × destruct Hs2 × split 两子目标 × destruct H2e/H3e）里，修一个分支的 tactic 时容易破坏另一个分支的 bullet 闭合。bullet 层级（- + * ++ --）是隐式的，DS 无法在一次重写中同时保持所有分支闭合。

## 已尝试

1. 精准错误注入（每轮把上一轮错误写进 EXTRA，要求最小修正）→ DS 仍整段重写，每轮修一处冒一处
2. max_rounds 4→5 → 仍未收敛
3. option 层级铁表 + setby f 元素层构造注入 → 辅助引理 Qed，但主证明 bullet 问题持续

## 当前策略（第 6 轮）

**花括号 `{ }` 代替所有 bullet 层级**：每个子目标用 `{ ... }` 显式聚焦，不依赖 bullet 隐式层级。EXTRA 强制要求 DS 用花括号，绝对不再用 `- + * ++ --`。

## 涉及的哲学问题

无。这是纯工程实现问题（Coq 证明脚本结构），不涉及命名/定义/公理/存在论判断。

## 策略演进（共 11 轮）

| 策略 | 轮次 | 结果 | 错误 |
|------|------|------|------|
| bullet 整段重写 | r1-r5 | 未收敛 | 2253 H1e未绑定 → 2240 rewrite不存在 → 2233 bullet++ → 2227 change子项 → 2232 bullet-- |
| 花括号{}代替bullet | r6-r8 | 未收敛 | 2232/2233/2235 `This proof is focused, but cannot be unfocused this way` |
| assert拆分（两个独立assert） | r9-r11 | 进行中 | 待结果 |

## 根因深化

DS 无论用 bullet 还是花括号，在 4×3 多分支嵌套整段重写中都无法一次保持结构闭合。assert 拆分把大证明拆成两个独立 assert（split G G1 G23 和 split G23 G2 G3），每个 assert 结构短，理论上应能收敛。

## 后续

- 若 assert 拆分 3 轮内收敛 → split_assoc Qed → typed_res_par_l/r → congruence
- 若仍不收敛 → S04 自己写证明骨架（destruct 结构 + assert 拆分），DS 只填每个分支的 tactic 内容；或派 S01 研判是否换证明策略（如对 n 归纳、或用更高阶 split 引理构造）

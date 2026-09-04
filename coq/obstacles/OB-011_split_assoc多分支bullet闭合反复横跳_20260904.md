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
| assert拆分 | r9 | **重大突破** | DS发现原见证G23=setby f G 0为假！反例G=[] G2=G3=[None]时setby返回[]但需要[Some None] |
| 见证修正（pad+setby） | r10-r12 | 进行中 | G23改为setby f (repeat None (Nat.max lenG2 lenG3)) 0，待结果 |

## 根本突破（r9）

DS 在 assert 拆分策略的 r1 中，没有继续写证明，而是指出了**根本问题**：原指定的见证 `G23 := setby f G 0` 本身是假的！

**反例**：G=[], G12=[], G3=[None], G1=[], G2=[None]
- 前提 split G G12 G3 和 split G12 G1 G2 都成立
- 但 setby f [] 0 = []（空列表上 setby 返回空）
- split [] [None] [None] 不成立（位置0：get [] 0=None ≠ get [None] 0=Some None）

**根因**：setby f G 0 只能在 G 的已有位置上修改，不能扩展 G 的长度。当 G 比 G2/G3 短时，G23 不够长，无法包含 G2/G3 的资源。

**修正（第一版，已发现不足）**：G23 = setby f (repeat (None:option ty) (Nat.max (length G2) (length G3))) 0
- 先建一个长度为 max(len G2, len G3) 的全 None 列表作基底
- 再用 f（优先取 G2 元素，否则取 G3 元素，否则 None）逐位置 setby

**见证修正策略 r1 的新发现（DS 反例有内部矛盾但揭示更深问题）**：
DS 在 r1 中给出第二个反例 G=[], G12=[None], G3=[], G1=[None], G2=[None]，声称命题为假。但反例的第三个 split 写为 `split G23 [None] [None]`（G3=[None]），与前提 G3=[] 不一致。实际 G3=[] 时 G23=[] 是见证（split [] [None] [] 成立），所以该反例不成立。

但 DS 的尝试揭示了更深刻的问题：**G23 的构造需要同时满足两个 split，简单 pad+setby 不对**。
- 当 G1 在位空（Some None）但 G 越界（None）时，split G G1 G23 要求 G23 侧越界（None），不能在位空（Some None）
- 当 G2 和 G3 都在位空（Some None）时，split G23 G2 G3 要求 G23 侧在位空（Some None），不能越界（None）
- 这两个条件看似矛盾，但从 split 前提可推出 G=G1∪G2∪G3，当 G1/G2/G3 都在位空时 G 也在位空不越界，所以矛盾情况不存在
- 正确的 G23 构造需要更精细的方法，不能简单 pad 到 max_len

**教训**：前 8 轮（bullet 5 + 花括号 3）全在错误见证上白费功夫。DS 的深度思考（reasoning 87695 字符）最终发现了根本问题，而不是继续在表面结构上修修补补。这验证了"DS 要有自己的明性、先想清楚再动手"的价值。

## 后续

## 最新进展（见证修正策略 r3 后）

见证修正策略 r3（第二轮闭环）DS 终于交了完整主证明（24812 字符输出，其中修正版 14788 字符），但因输出中含 3 个 `Lemma split_assoc`（2 个完整证明 + 1 个分析文字提及）被 proof_loop 卫生检查拦下。执行方手动提取修正版应用到 Layer2.v。

应用后编译错误序列：
1. **2253 `Found no subterm matching "get G3 n" in G3n`**：DS 用 `[ rewrite EG3 in G3n; discriminate | rewrite EG3 in G3s; discriminate ]` 分支语法，但 G3n 中可能不含 `get G3 n` 子项（方向/简化问题）。执行方机械替换为 `rewrite G3n in EG3; discriminate`（EG3 一定含 `get G3 n`），G3/G2 分支共 36 处全部修正。
2. **2264 `Found no subterm matching "get G12 n" in EG2`**（当前唯一错误）：G12 分支逻辑错误——DS 用 `_` 忽略了 Hs2r 左合取支 `get G2 n = get G12 n`，导致 EG2（关于 G2）和 G12n（关于 G12）是关于不同变量的等式，无法直接矛盾。修法：保留并命名该等式（如 HG2G12），用 `rewrite <- HG2G12 in EG2` 把 EG2 转成关于 G12 的等式，再与 G12n 矛盾。

第三轮闭环已启动，EXTRA 精准指出 G12 分支逻辑错误，要求 DS 只修这一处。

## 后续

- 第三轮闭环修 G12 分支后应收敛 → split_assoc Qed → typed_res_par_l/r → congruence
- 若仍不收敛 → 派 S01 研判 split_assoc 命题陈述与 G23 构造的数学正确性


## 2026-09-04 最新发现：DS证明结构性不完整

### 根本原因
DS r3修正版证明（split_assoc_r3_fixed.v，14788字符）中，
\\coq
destruct (get G2 n) as [[a|]|] eqn:EG2;
destruct (get G3 n) as [[b|]|] eqn:EG3.
\创建**9个分支**（G2: Some(Some a)/Some None/None × G3: Some(Some b)/Some None/None），
但DS每个目标只写了**4个**\*\分支，省略了5个：
- G2=Some None的3个分支
- G2=Some(Some a), G3=Some None的1个分支
- G2=None, G3=Some None的1个分支

### 后果
bullet结构混乱，后续分支中Hs1/Hs1l变量不存在（\Hs1l not found\），
所有机械修正（rewrite方向/congruence/inversion/discriminate替换）都无法解决，
因为根本问题是分支缺失，不是单个tactic错误。

### 解决方案
必须让DS重新生成包含全部9个分支的完整证明，不能再用不完整的r3版本。
调用DS时需明确指出：\destruct (get G2 n) as [[a|]|]; destruct (get G3 n) as [[b|]|]\创建9个分支，必须全部处理。

### 已验证的机械修正（供新证明参考）
- ewrite EG3 in G3n; discriminate\ → \discriminate G3n\（G3n中get G3 n已被destruct替换）
- G3s/G2s/G12s分支需要\inversion\而非\discriminate\（Some(Some x)=Some None，需先injection）
- Hs1r/Hs2r分支不能忽略左合取支\get G2 n = get G12 n\，需保留为HG2G12用于连接
- 目标中\get G2 n\已被destruct替换为\Some(Some a)\，rewrite方向需注意
- simpl会改变Hs1类型导致destruct as模式不匹配，G2=None分支应避免simpl

## 2026-09-04 v7 闭环（分解策略：H23_val 辅助引理 + split_assoc 主证明）

### 策略
先证 H23_val 辅助引理（描述 G23=setby f (repeat None max_len) 0 的 get 值，只涉及 get/setby/repeat），再用 `rewrite (H23v n)` 证 split_assoc 本体，目标里不再有 f。

### v7 5 轮错误模式

| 轮次 | 输出字符 | 错误行 | 错误内容 | 根因 |
|------|----------|--------|----------|------|
| r1 | 8026 | 2241 | `The variable H23_val was not found` | **输出格式问题**：DS 把 H23_val 引理写在 markdown 正文中（不在 ```coq 代码块），extract_coq_blocks 未提取 |
| r2 | 12523 | 2275 | H23_val 引理 inversion 错误 | H23_val 引理本身证明错误 |
| r3 | 7727 | 2242 | `Unable to unify "None" with "Some None"` | H23_val 引理中 get G2 n=Some None, get G3 n=None 时 f 返回 None，DS 错误假设返回 Some None |
| r4 | 11148 | 2282 | `Illegal application: Hs1 cannot be applied to n` | split_assoc 主证明中把假设名 Hs1 当作函数应用 |
| r5 | 9409 | 2281 | `Found no subterm matching "get G3 n" in H3` | split_assoc 主证明中 rewrite 目标不存在 |

### 分析
- r1 的输出格式问题在 r2 已修正（H23_val 被成功插入到 Layer2.v 2221 行）
- r2-r3 是 H23_val 辅助引理本身的证明错误
- r4-r5 是 split_assoc 主证明的错误
- DS 在 H23_val 引理和 split_assoc 主证明之间来回切换，每轮都有不同错误，但没有收敛
- v7 累计费用：1.0731 元
- v4+v5+v6+v7 总费用：约 4.88 元

### 下一步
- 恢复 Layer2 干净状态（已完成）
- 考虑重新设计 H23_val 引理的陈述（当前类型可能有问题）
- 或者换一种分解策略（不用 H23_val，直接证 split_assoc）
- 或者给 DS 更明确的指导（H23_val 引理的正确类型和证明策略）
- 已 signal 通知 S01 研判 split_assoc 命题陈述与 G23 构造的数学正确性


---

## 最终结论（2026-09-04 傍晚，证伪双门推翻"假命题"误判）

- v8 DS 交 `split_assoc_false` 声称本引理为假，S04 一度盲信停机——**此判断错误**。
- **门1（反例独立编译）**：split_assoc_false 剥离后单独 coqc，exit=1；错误在右支 `Hright: None=get G23 0` 被 symmetry/exact 误用于目标 `Some None=get G23 0`——把 G3=[] 的越界空 None 与 G2=[None] 的在位空 Some None 混为一谈（option 双层错层）。
- **门2（反向候选解）**：DS 给的参数 G=[],G12=[None],G3=[],G1=[None],G2=[None] 下，取 **G23=[]**，`exists []; split; unfold split; intros [|n]; simpl; auto` 使 `split [] [None] G23 /\ split G23 [None] []` 编译通过（exit=0）。"不存在 G23"不成立。
- **裁定：split_assoc 为真**（明性分划结合律）。回到证明为真路线；v6/v7 的 H23_val 分解策略需在为真路线下重新核对，排除"假命题误判期"的认识污染。
- 固化：`scripts/s04_deepseek/falsification_guard.py`（双门+事故回归）、结晶016、教训L035、八点固化文档。本卡点状态：命题真假已决（真），剩余纯证明技术问题。

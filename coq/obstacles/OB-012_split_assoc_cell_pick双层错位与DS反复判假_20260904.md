# OB-012 split_assoc_cell_pick 的 option 双层错位，及 DS 对已证真命题反复"判假/空转"

- 记录时间：2026-09-04 16:40
- 所在文件/定理：coq/theories/ALL/Layer2.v · Lemma split_assoc_cell_pick（服务于 split_assoc 主定理在位支）
- 状态：**进行中**（J1-a split_assoc_cell 已 Qed；主定理完整证明已就位、真实 Admitted=0；仅 pick 一处类型错，换路修复闭环 run_j1c_fix2.py 后台进行）
- 性质判定：**表层纯技术（option 双层枚举错位），但伴随一个需 S01 知晓的认知现象——DS 三次对"已被机器证实为真"的命题产出判假倾向**

## 1. coqc 原始错误（原样）
```
File ".\Layer2.v", line 2372, characters 38-42:
Error:
In environment
g, g3, g2 : option (option ty)
Hne : g2 <> None \/ g3 <> None
He3' : g3 = Some None
He2' : g2 = None
Hpick : fcell g2 g3 = Some None
The term "He2'" has type "g2 = None" while it is expected to have type
 "g2 = Some None".
```
根因（结晶010）：option(option ty) 三态 None(越界之寂)/Some None(在位之寂)/Some(Some T)(真实发用)；DS 在手写 pick 四命名大分支时，把假设 `g2=None`（越界）错当目标位需要的 `g2=Some None`（在位空），跨层 exact。

## 2. DS 的多轮尝试与失败形态（DeepSeek 干渠留痕）
1. 小步流水线首轮（run_j1，round1）：只交 cell_split + split_assoc_cell(exists 版)，**一次 Qed、coqc exit0、0.10 元**——证明"小引理小步快跑"有效。
2. 同闭环 round2：交主定理时 reasoning 87551 字符、content 仅 124 字符（光想不写）；round3 直接产出 split_assoc_false 判假，被证伪双门门1(反例独立编译 exit1)推翻；round4-6 反复**重复提交 Definition cell_split**，撞 `cell_split already exists`(line2315)，把自己 round5 已写出的完整主定理证明一并拖累到无法编译。
   → S04 回滚到备份 bak_r2（干净+cell 引理 Qed），再机械应用 DS 完整草稿（fcell/pick/length_setby/cell_split_none_end+主定理），coqc 抓出本 OB 的唯一类型错。
3. 修复闭环 run_j1c_fix round1：reasoning **169658 字符**、自然语言宣称命题假(nl:false-claim，无否定引理物证)，双门门1判 refuted_claim 推翻；round2 单请求阻塞约 15 分钟纯 IO 等待 → 触发 5 分钟熔断停止。
4. 换路 run_j1c_fix2（进行中）：禁止判假、禁止整体重写四命名大分支，改"析取 -> 同步代入 + g2/g3 三态 destruct as [[a|]|] + cbn 暴力枚举"。

## 3. 阻碍本质
- 纯技术部分：有限枚举引理的手写分支命名易在 option 双层上错位；解法是更机械的三态枚举，让 cbn/auto 消格，而非人脑逐格命名等式。
- 认知/哲学部分（请 S01 留意，非阻塞）：split_assoc 为真已被 split_assoc_cell 的 Qed 与 J0 类型检查**机器证实**，但 DS 仍三次（旧 r3、fix r1、超长 r2）滑向"判假/怀疑"。存在论上这是"明性分划结合律"——两种寂然空位（越界 None 与在位 Some None）的区分恰恰是结合律成立的条件，DS 直觉上把两种"寂"混同，才会反复误以为存在反例。这反向印证结晶010/012：空壳可收摄、但双层不可错位。

## 4. 演进与定论（17:30 更新）

### 4.1 pick 假已被独立 coqc 机器证实（_guard_pick_false.v，exit=0）
反例格 g=None,g12=None,g1=Some None,g2=None,g3=Some None：三前提全真而结论假。fcell"g2 优先否则 g3 兜底"在该格错取 g3=Some None，正确应取 g=None。**fcell/pick 路线废弃删除。**

### 4.2 换用 choose（已 Qed 落袋）
按已 Qed 的 split_assoc_cell 四格见证定义 choose（左-左取 g2、其余取 g）+ is_empty_get + choose_correct（等价 pick 但为真），DS round1 一次 coqc exit=0 固化。讲透"为什么真/正确选择规则"后 DS 不再判主命题假——**明性引导有效**。

### 4.3 新卡点（真数学结构，非 DS 空转）：G23 必须按前缀长度构造
DS 用固定长度 L=max(length G)(length G2) 的 setby 表造 G23，并追求过强等式 get G23 n=choose_val n；为此造了 choose_none_iff，但其 iff 反向为假（左-左格 g2=None 时 g 仍可在位）。
根因：在"g 越界 None、g1 在位空 Some None"格，逐位见证须取**越界 None**，而固定长度表在 n<L 位只能给出在位 Some x，给不出越界 None；把 None 软化为 Some None 在该格也失败（cell_split None(Some None)(Some None) 两支皆要求 Some None=None）。
正解（S04 已验证方向为真）：需要 None 的位必为**后缀**——split 前提排除"G2 独在位而 G/G12/G1 全越界"的交错（此时 H2 的 cell_split 不成立），故 G23 按"choose 最后在位位+1"的前缀长度构造，在位位取 choose 值、越界后缀自然 None。在位位用 choose_correct，越界位 cell_split None None None 自反。详见 J1e 任务书。

### 4.4 暴露出 DS 的两个工艺坏习惯（要固化为明性纪律）
1. 一遇局部 tactic 错就绕开、另造抽象引理（fcell→pick→choose_none_iff 连环），且新引理方向常为假却不先自检；
2. 倾向把自己绑死在过强等式上，忽略 cell_split 空位析取与 ctx 在位位的前缀结构。
对应纪律：写新引理前先用最小 guard 枚举判真假；优先拼装已 Qed 零件；追求"命题成立"而非"字面相等"。

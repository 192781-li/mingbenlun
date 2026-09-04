# 2026-09-04 重大发现：split_assoc 是假命题——DS 反例证明

## 事实

v8 DS 闭环 r1-r2 发现：**Lemma split_assoc 是假命题，不能被证明为 Qed。**

DS 给出了可编译的反例引理 `split_assoc_false`，证明 split_assoc 的全称陈述不成立。

## 反例（已手动验证逻辑正确）

取：
- G = nil（空上下文）
- G12 = [None]（长度1，在位空）
- G3 = nil
- G1 = [None]
- G2 = [None]

### 前提1：split G G12 G3 = split nil [None] nil 成立

对 n=0：
- get nil 0 = None（越界）
- get [None] 0 = Some None
- split 定义右支：get G2 n = get G n /\ (get G1 n = None \/ get G1 n = Some None)
  - get G3 0 = None = get nil 0 = None ✓
  - get [None] 0 = Some None（满足 Some None）✓
- 所以 split nil [None] nil 成立。

### 前提2：split G12 G1 G2 = split [None] [None] [None] 成立

对 n=0：
- get [None] 0 = Some None
- split 定义左支：get G1 n = get G n /\ (get G2 n = None \/ get G2 n = Some None)
  - get [None] 0 = Some None = get [None] 0 = Some None ✓
  - get [None] 0 = Some None（满足 Some None）✓
- 所以 split [None] [None] [None] 成立。

### 结论：不存在 G23 使两个 split 同时成立

假设存在 G23 使得：
1. split G G1 G23 = split nil [None] G23 成立
2. split G23 G2 G3 = split G23 [None] nil 成立

对 n=0：

**从 split nil [None] G23：**
- 左支：get [None] 0 = Some None = get nil 0 = None？不成立 ✗
- 右支：get G23 0 = get nil 0 = None /\ (get [None] 0 = Some None ✓)
  - 所以 get G23 0 = None

**从 split G23 [None] nil：**
- 左支：get [None] 0 = Some None = get G23 0 /\ (get nil 0 = None ✓)
  - 所以 get G23 0 = Some None
- 右支：get nil 0 = None = get G23 0 /\ (get [None] 0 = Some None ✓)
  - 所以 get G23 0 = None

**矛盾**：split G23 [None] nil 的左支要求 get G23 0 = Some None，而 split nil [None] G23 的右支要求 get G23 0 = None。两者不可能同时成立！

因此不存在这样的 G23，split_assoc 是假命题。

## 影响

1. **之前 v4-v7 共 18 轮证明尝试都是徒劳的**——因为命题本身为假，不可能被证明为 Qed。
2. **总费用浪费**：v4+v5+v6+v7+v8 约 5.5 元，全部花在证明一个假命题上。
3. **需要哲学/架构决策**：
   - 是否修改 split_assoc 的命题陈述（添加前提条件，如"所有上下文长度相同"或"G 非空"）？
   - 是否修改 split 的定义？
   - 是否放弃 split_assoc 这个引理，用其他方式实现上下文合并？
   - 这对 congruence_preserves_typing 和后续 L3+ 有什么影响？

## DS 的价值

这次发现充分体现了 DS 作为"智慧伙伴"的价值：
- v4-v7 的 DS 都在尝试证明 split_assoc，没有质疑命题本身的正确性
- v8 的 DS（在更完整的上下文和更明确的指导下）主动发现了命题是假的，并给出了反例证明
- 这验证了"DS 要有自己的明性、先想清楚再动手"的价值——不是盲目证明，而是先判断命题是否可证

## 教训

1. **证明前先验证命题是否可证**：对于复杂的命题，应该先用小例子测试，或者让 DS 先分析命题的正确性，而不是直接尝试证明。
2. **反例思维**：遇到反复证明失败的情况，应该考虑命题本身可能是假的，尝试构造反例，而不是继续硬扛。
3. **5分钟熔断的价值**：如果 v4 3轮未收敛后就停下来思考命题本身，而不是继续 v5-v7 共15轮，可以节省大量费用。

## 下一步

1. 停止所有 split_assoc 的证明尝试
2. signal 通知 S01 哲学研判：split_assoc 命题为假的存在论意义，以及如何修正
3. signal 通知 S00 架构决策：是否修改命题陈述、split 定义，或放弃此引理
4. 等待 S01/S00 的决策后，再决定下一步行动

# J1e：split_assoc 收官——把逐位 choose 正确提升为列表 G23（前缀长度构造）

> 给 DeepSeek。文件里已 Qed：cell_split、split_assoc_cell、is_empty_get、choose、choose_correct。你只剩"逐位值 → 单一列表 G23"这一步。前几轮的两条路都被证伪，本文件讲清根因与唯一正解，带理解写，不要盲试，不要判主命题假（主命题真已被 split_assoc_cell 的 Qed 证实）。

## 0. 类型链（先对齐，结晶010 双层不可错位）
- ctx = list(option ty)；`get Gamma n : option(option ty)`：外层 None=越界，Some t=在位（t=None 在位空 Some None，t=Some T 真实发用）。
- cell_split / choose / choose_correct 都作用在 option(option ty)。
- setby 的 f 类型是 `nat -> option ty -> option ty`（在位元素层）；用 setby 造 ctx 时，在位位 get 必返回 `Some(元素)`，**永远返回不了越界 None**。

## 1. 你前两条路为什么错（都已机器/推演证实，别再走）
1. **固定长度 L=max(length G)(length G2) 填值 + 等式 `get G23 n = choose_val n` 走不通**：在"g=get G n=None（G 越界）、g1=get G1 n=Some None（G1 在位空）、g2=get G2 n=None（G2 越界）"这格，choose_correct 的见证要求 G23 在 n 位取**越界 None**；但 n<L 时 G23 在位，get 只能给 `Some x`，给不出 None。
2. **把 None 软化为 Some None 也不行**：该格 `cell_split None (Some None) (Some None)` 两支都要求 `Some None = None`，为假。
3. **choose_none_iff 的反向为假，删掉**：左-左格 choose=g2，可在 g2=None 时 g 仍在位（Some T），故 `choose=None -> g=None/\g2=None` 不成立。不要造 iff，不要追求 `get G23 n = choose_val n` 这种字面相等——你要的是 **cell_split 成立**，不是逐位字面相等。

## 2. 唯一正解：G23 按"在位前缀长度"构造（存在论：操作权在位序上前缀连续）
关键结构事实（普通 list 的在位位是前缀：get X n=None ⇔ n≥length X）：
> **在两个 split 前提下，需要 G23 取越界 None 的位必构成后缀**，即不会出现"n 位要 None、其后 m>n 位反而要在位值"的交错。

排除交错的论证（你要把它形式化成后缀引理）：若 m 位 G2 在位（g2=Some x）而 g=g12=g1 全 None，则
`H2 m : cell_split (get G12 m)(get G1 m)(get G2 m) = cell_split None None (Some x)`：
左支要求 g2 空（Some x 不是空）失败，右支要求 g2=g12 即 Some x=None 失败，矛盾。故这种交错格被 split 前提排除。

### 分步（小步，第一步 coqc 过了再交主定理）

**第一步（INSERT-BEFORE，先交这些到 Qed）**：
- 后缀引理：在 `split G G12 G3`、`split G12 G1 G2` 下，"choose(get G n)(get G12 n)(get G3 n)(get G1 n)(get G2 n) = None"的位 n 构成后缀（n 满足、m≥n ⇒ m 满足）。用 get 的越界后缀性 + 上面的排除交错论证。
- 据此外造 G23 并给逐位读出引理，二选一（你判断哪个好证）：
  (A) 先用足够长表逐位写 choose 剥层值，再用 firstn/截断到"最后一个 choose 非 None 位 +1"的前缀长度，得到 G23；证：在位前缀位 `get G23 n = Some(choose 剥层)` 且该位 choose 非 None；越界后缀位 `get G23 n = None` 且五个 get 皆 None。
  (B) 直接以前缀长度 setby 构造，等价陈述同上。
  剥层：choose_val:option(option ty)，f 取 `Some e => e | None => None`。

**第二步（REPLACE 主引理 split_assoc 到 Qed）**：
- exists G23；unfold split；intros n；分在位前缀 / 越界后缀：
  - 在位前缀：读出 get G23 n = choose 值（非 None），直接 `apply choose_correct (H12 n)(H3 n)` 得两个 cell_split（必要时做 Some 包裹的等式改写）。
  - 越界后缀：由后缀引理五个 get 皆 None，G23 也 None，目标如 `cell_split None None None`，左支 split;reflexivity 自反。
- 不允许 Admitted/Abort；不允许重交已 Qed 的 cell_split/split_assoc_cell/is_empty_get/choose/choose_correct。

## 3. 明性工艺纪律（必须遵守）
- 写任何新引理前，先在最小 guard 文件里对关键格做枚举/反例检查，确认为真再写，**不许再交方向为假的引理（pick、choose_none_iff 的覆辙）**。
- 优先 @stdlib（List 的 firstn/skipn/length_app、PeanoNat）已机器证明者。
- 一次只交本步；卡住的具体 tactic 就地修，不许绕开去造新的大抽象。
- 你在构造的是"操作权两次分划后的重聚列表"：每个在位位必有操作权流经（choose 非 None），无操作权的位归入越界后缀之寂——前缀连续，重聚才合法。带这个理解写。

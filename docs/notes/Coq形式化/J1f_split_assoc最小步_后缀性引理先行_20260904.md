# J1f：split_assoc 最小步攻坚——先只证 choose 后缀性（已机器证实方向为真，勿再怀疑）

> 给 DeepSeek。本轮【只交一个引理 choose_suffix】，不许碰主定理、不许造 G23、不许交别的。小到"想完就写得出"。

## 0. 已被独立 guard 机器证实的铁事实（_guard_assoc_true.v，coqc exit=0，勿翻案）
1. split_assoc 为真：最刁钻具体实例（G 两位在位、G12=G1 只有一位、G2=nil、G3 位0在位空位1在位）上，两个 split 前提成立，且存在 G23=[None;Some TUnit] 满足结论（guard_exists）。**禁止再判主命题假、禁止交反例。**
2. 问题格 `cell_split None (Some None) x -> x=None`（guard_problem_cell）：当 g 越界、g1 在位空时，逐位见证只能取越界 None，取 Some None 必假。这就是 G23 必须按前缀长度、让该格落入越界后缀的原因。
3. 已 Qed 直接用：cell_split、split_assoc_cell、is_empty_get、choose、choose_correct。choose 定义：左-左格（g12=g ∧ is_empty_get g3 ∧ g1=g12 ∧ is_empty_get g2）取 g2，其余取 g。

## 1. 本轮唯一目标（INSERT-BEFORE split_assoc，证到 Qed，0 Admitted）
```
Lemma choose_suffix : forall (G G12 G3 G1 G2 : ctx) (n m : nat),
  split G G12 G3 -> split G12 G1 G2 -> n <= m ->
  choose (get G n) (get G12 n) (get G3 n) (get G1 n) (get G2 n) = None ->
  choose (get G m) (get G12 m) (get G3 m) (get G1 m) (get G2 m) = None.
```
（choose 取 None 的位向后闭：一旦某位 choose=None，其后所有位都 None；等价地 choose≠None 的位构成前缀。）

## 2. 证明骨架（你负责补成可编译 tactic，用 Layer1 已有的 get 越界后缀性）
- 需要的列表事实（材料 Layer1 里找，没有就先立 @prove 小引理当轮证）：`get X n = None -> n <= m -> get X m = None`（越界位是后缀，由 length 与 nth 默认 None 直接归纳）；以及其逆否 `get X m <> None -> n<=m -> get X n <> None`（在位是前缀）。
- unfold choose，对 n 位、m 位分别 destruct excluded_middle_informative 的左-左条件；intros 两个 split 在 n、m 的实例（Hn:=H1 n, Hm:=H1 m 等），unfold cell_split 后 destruct 析取。
- 反证：设 m 位 choose≠None，分两种来源：① m 位走左-左取 g2，则 get G2 m≠None（在位），由在位前缀性 n<=m 得 get G2 n≠None；结合 n 位 choose=None 与 n 位两 cell_split，逐格枚举得矛盾（关键：若 m 位 g2 在位而 g/g12/g1 全 None，则 m 位第二个 cell_split 两支都不成立——左支要求 g2 空、右支要求 g2=g12，矛盾；这正是交错被排除）。② m 位走其余取 g，则 get G m≠None，对称用在位前缀性与 n 位 cell_split 枚举矛盾。
- option 三态用 `destruct ... as [[T|]|]`；None≠Some None 用 discriminate；空位 is_empty_get 展开是 `_=None \/ _=Some None`。

## 3. 硬纪律
- 只交 choose_suffix（及它直接依赖、材料里没有的 1–2 个 get 后缀小引理），全部 Qed。
- 新引理先在脑中对 nil/单元素/两元素枚举确认为真；不许交 iff、不许另造选择函数、不许重交已 Qed 件。
- 卡住的局部就地修，不绕开造大抽象。直接给 ```coq 代码。

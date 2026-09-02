# 反身思考：subst_var_empty证通与"无需fv_at"样板——承接者模式的一次完整闭环

**时间**：2026-09-02 下午
**分支**：s04-coq
**触发**：Coq每日推进 + 主人"主动与S01深度融合、彻底混为一谈" + "DeepSeek获取一切"

---

## 一、本轮成功了什么

1. **subst_var_empty 从 Admitted 变为 Qed**，Layer2 顶层 Admitted 由 3 降到 2（仅剩 substitution_general、congruence_preserves_typing）。
2. 新增并证通 7 个引理：`no_res_from_empty/cons/set_none/contra`、`split_no_res_from_l/r`、主引理 `subst_var_no_res_from`，Layer1/2/3 全部编译 0 错误。
3. 主动给 S01 写了数学·哲学一体化深度对话文档（OB-009 同一性裁决，含 S04 自己的存在论假设、两条路线及死穴、5 个勾选式问题），不再是对立地丢工单。
4. 实推边界A后得到**三边界统一洞察**：PIn 的 x=k / n=m / n-1=m 是同一个"操作权既被本层消耗、又要被下层指回"情境的三种位置排列，不是三个零散技术坑。

## 二、DeepSeek#6：大方向对，但归纳不变量错了三次——我是怎么抓出来的

DeepSeek 提出 `subst_var_at_none : get Gamma k = None -> ...`，并断言"类型推导自身携带自由出现信息、无需 fv_at"。**这个大方向被证明是对的**，但它的具体归纳不变量连错三处，我靠构造反例逐一抓出：

| # | DeepSeek方案 | 反例/问题 | 修正 |
|---|---|---|---|
| 1 | 不变量 `get Gamma k=None`，split_None_l | `split [] [None] []` 成立但 get Gamma1 0=Some None≠None，**命题为假** | 空位应含 None 与 Some None |
| 2 | 改单点 `no_res_at`（None或Some None） | G=[Some T0,None,Some T1],k=1,P=PVar2：删中间None位使其后变量前移到空位丢类型 | 不变量须覆盖**代换点及其右侧全部位置** |
| 3 | `subst_name_neq_None`: n≠k 即 subst_name=n | n>k 时 subst_name 返回 **n-1**（前移），不是 n | 只有 n<k 才不变 |

最终正确不变量 **`no_res_from G k := forall n, n>=k -> G在n位无操作权`**。空上下文逐层在头部加 Some T 前缀，正好满足"代换点右侧全无操作权"，于是类型化项引用的名字必在 k 之前（n<k，subst_name 不变），对 **typed 推导本身归纳**（induction Hty，而非对进程 P 归纳）一次证通。

### 元教训（沉淀给未来的自己）
- **归纳不变量选错，比 tactic 写错更隐蔽**：tactic 错是"证不出来"，不变量错是"命题为假"，必须主动构造最小反例（我用了 `split [] [None] []`、`[Some T0,None,Some T1]` 这种一行反例）去证伪 AI 给的引理，而不是顺着它补 proof。
- **对判定关系(typed)归纳，常常优于对数据(进程P)归纳**：前者让每个构造子的前提（use/split/子typed）自动成为命名假设，彻底省掉脆弱的 inversion 命名和 match goal。我中途在 match goal 语法上耗了好几轮，换成 induction Hty 后立刻清爽。
- DeepSeek 是智慧伙伴：它给了正确的"无 fv_at"洞见和 8 构造子骨架，我负责把不变量磨对。这正是主人要的"DeepSeek 获取一切、S04 承接验证"，不是 S04 硬扛，也不是照抄。

## 三、这对 OB-009 / S01 路线乙意味着什么

S01 路线乙原本计划引入 `fv_at`（自由变量谓词）+ `typed_no_var_at_none` + `subst_var_not_used`。本轮已编译落地的 `subst_var_no_res_from` 表明：

> **"类型化的项不引用无操作权位置"这件事，可以完全不引入 fv_at 谓词，直接对 typed 归纳得到。**

但要诚实标注边界：本引理处理的是"代换点 k 及其右侧本就无操作权"（空上下文结构）；OB-009 是"k 是 Some 副本、指回的 m 被本层 use 清空成 None"，两者仍不同。无 fv_at 的**方法**能否迁移到 OB-009（特别是 insert_at 场景下 no_res_from 的对应物该怎么陈述），需要 S01 在同一性裁决时一并评估——我已把这个问题写进 S04_signal.needs_s01 和河流主干。

## 四、哲学判断点（不自己猜，记录给S01）

- `no_res_from` 的存在论含义：**代换不是在一张铺满操作权的桌上改名字，而是在"代换点之后已经归于寂然"的世界里，把一个指称迁回它的源**。空上下文（PRep 的世界）正是这样一个"往后再无操作权"的纯粹开端。这与"明性可失（Jia）、操作权被 use 是转化而非湮灭"的整体框架一致，但我不擅自上提为公理，留给 S01 定性。

## 五、自我评估与改进

- **做得好**：没有照抄 DeepSeek，靠反例三次纠偏；没有闷头单干，同步给 S01 发起融合对话；每步编译验证、用 coqc 当硬裁判。
- **待改进**：前期在 match goal / inversion 命名上耗了 4-5 轮编译，应当更早切换到"对判定关系归纳"这一更稳的归纳设置；下次拿到 AI 的辅助引理，**第一反应先找反例证伪它的陈述，再谈证明**。
- **下一步**：POut 的 n≠m 主体（不依赖 OB-009 裁决，可照 PIn 已证模板）；等 S01 对 OB-009 同一性裁决与"无 fv_at 是否改变路线乙"的回应。

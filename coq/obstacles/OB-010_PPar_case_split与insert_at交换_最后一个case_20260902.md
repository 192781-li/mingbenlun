# OB-010：substitution_general 的 PPar case（split 与 insert_at 交换，最后一个case）

- 编号：OB-010
- 日期：2026-09-02
- 所在文件/定理：coq/theories/ALL/Layer2.v · Lemma substitution_general · PPar 分支（当前唯一内部 admit）
- 阻碍本质：**纯技术为主**（split 逐位置结构 + 上下文长度变换），不涉及新的哲学判断；存在论语义已由S01路线乙+双参数前提确定。

## 目标
在 A线双参数谓词 no_use_at_subst 下证 PPar：
`simpl in Hnu` 得 `no_use_at_subst Q m k && no_use_at_subst R m k`，Bool.andb_true_iff 拆两份；
par_elim 得 split (insert_at k T Gamma) Gamma1 Gamma2、typed Gamma1 Q、typed Gamma2 R；
需把 insert_at 从 split 内部提出，使两子侧分别落到可喂 IHQ/IHR 的形状。

## 已确定的引理链（S01策略，需按双参数谓词对齐）
1. remove_at（删位置k，Fixpoint，简单）
2. split_insert_at（核心）：split (insert_at k T Gamma) G1 G2 → exists G1' G2', split Gamma G1' G2' /\
   ((G1=insert_at k T G1' /\ G2=G2') \/ (G1=G1' /\ G2=insert_at k T G2'))
   —— insert位T线性地只分给一侧
3. 分到T的一侧：用 IHQ/IHR（传对应那份 no_use_at_subst；get Gamma m 经 split 逐位置保持 + get_insert_at_lt/gt 恢复）
4. 没分到T的一侧：该侧k位为None，typed项不引用空位（用S04 no_res_from 的"对typed归纳"样板，无需uses_at/fv_at），代换后类型不变
5. 最后 ty_par 重组

## 已尝试 / 现状
- 本轮A线落地后POut/PIn等7 case全Qed，仅PPar留 admit（整体暂Admitted），三层编译0错误（commit 35a92d2）。
- S01自评强版本需1-2天，建议先弱版本（两子进程都不引用k，subst_var不变，只需strengthening）；S04决定立OB-010单独攻坚，不在A线落地轮硬啃（5分钟熔断）。

## 涉及的哲学问题
无新增。前提：路线乙（同型异位）、双参数 no_use_at_subst（见 S04致S01_A线谓词双参数校正 文档）。唯一待S01语义确认：split 中 insert位T线性地只归属一侧，与线性操作权单一性一致。

## 解决状态：未解决（open）
下一步：先实现 remove_at，对 split 的 forall n 逐位置定义证明 split_insert_at；卡住则把完整 split 定义+当前失败tactic原样喂DeepSeek拿骨架，S04数学把关。

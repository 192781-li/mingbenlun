# -*- coding: utf-8 -*-
"""极聚焦：只修 insert_pts_subst 的 n=k 分支 injection（DS 主谋）。
去重后全文只剩这一个编译错误，substitution_general 推论已正确、不许动。
用法：python run_pts_fix.py
"""
from _paths import THEORIES, DOCS, NOTES
from proof_loop import proof_loop

TARGET = "insert_pts_subst"
FILE = str(THEORIES / "Layer2.v")

ERR = r"""File ".\Layer2.v", line 2137, characters 25-45:
Error: Nothing to inject.
出错语句：  injection Hn as HT'. injection HT' as HTT. subst T'.
此时 Hn : Some (Some T) = Some (Some T')  （option (option ty) 双层嵌套）。"""

BRIEF = (
 "目标：只修复 Lemma insert_pts_subst，使其 Qed、coqc 通过。\n"
 "【严格范围】只输出 insert_pts_subst 从 `Lemma insert_pts_subst` 声明行到列0 `Qed.` 的完整新版本（REPLACE 整段）；"
 "【禁止】输出任何 INSERT-BEFORE 块、【禁止】改动或输出 substitution_general（它已经正确）、【禁止】动其他任何引理。"
)

STRATEGY = tuple(p for p in
  (r"分站\S04_Layer2最后3Admitted_精确证明策略_S00分析_20260903.md",)
  if (DOCS/p).exists())
PHILOS = ()  # 纯算术小引理，不需要哲学文档，节省上下文

EXTRA = r"""
======== 唯一错误根因（Rocq 9.1 / Coq injection 语义）========
n=k 分支里：subst n; rewrite (get_insert_at_self k T Gamma) in Hn 之后，
  Hn : Some (Some T) = Some (Some T').
这是 option(option ty) 的【双层同名构造子嵌套】。Coq 的 injection 对嵌套的同名构造子
会【一次剥到底】：`injection Hn as EQ` 会同时剥掉两层 Some，直接把 EQ 绑成 T = T'。
你现在写了两句：`injection Hn as HT'. injection HT' as HTT.`——第一句已经把两层都剥完、
HT' 直接是 T=T'（再无构造子），第二句 injection HT' 就报 “Nothing to inject”。

======== 确定修法（任选一种，以 coqc 通过为准，推荐第一种）========
法1（单次 injection，给一个名字）：
    subst n.
    rewrite (get_insert_at_self k T Gamma) in Hn.
    injection Hn as EQ. subst T'.          (* 一次剥两层，EQ : T = T'，subst 把 T' 换成 T *)
    rewrite (subst_name_eq m k k eq_refl). exact Hget.
法2（用 [= ->] 直接代换，不命名）：
    subst n. rewrite (get_insert_at_self k T Gamma) in Hn.
    injection Hn as [= ->].                 (* 直接把 T' 归并为 T *)
    rewrite (subst_name_eq m k k eq_refl). exact Hget.
法3（inversion 兜底）：subst n. rewrite (...) in Hn. inversion Hn; subst.
注意：不要对同一等式连续两次 injection；若确实要分层，必须确认上一句留下的仍是
`Some _ = Some _` 形状而不是已经是 `T = T'`。

======== 另外两个分支已正确，保持即可（别改坏）========
n<k 用 get_insert_at_lt + subst_name_lt；n>k 用 Nat.ltb_spec 余下支 + lia 得 n>k +
get_insert_at_gt + subst_name_gt。整体签名保持：
  forall Gamma T k m, k<=length Gamma -> get Gamma m=Some(Some T) ->
  forall n T', get (insert_at k T Gamma) n=Some(Some T') ->
               get Gamma (subst_name m k n)=Some(Some T').

[当前 coqc 真实输出]
""" + ERR

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET,
                     layer_files=("Layer1.v", "Layer2.v"),
                     strategy_docs=STRATEGY, philos_docs=PHILOS,
                     extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=3)
    print("="*60)
    print("收敛" if res["converged"] else "未收敛")
    for r in res["rounds"]:
        print(r)

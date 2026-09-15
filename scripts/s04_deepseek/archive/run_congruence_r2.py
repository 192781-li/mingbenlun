# -*- coding: utf-8 -*-
"""congruence 第二轮：站在 r1 已验证结构上补全最后 4 个引理（proof_loop v2 新机制）。
r1 已 Qed：split_refl_nil/split_nil_r/split_sym'/typed_par_comm/typed_par_assoc_l/r/
           typed_par_zero_l/r/typed_rep_unfold_l/r + 主定理 Hmain 双向合取骨架。
待补到 Qed：split_assoc、typed_head_insert、typed_res_par_l、typed_res_par_r。
干净基线=966bcf0（congruence 为 Proof.Admitted.）。一轮交齐、无 Abort/admit。
用法：python run_congruence_r2.py
"""
import io, re
from _paths import THEORIES, DOCS, NOTES
from proof_loop import proof_loop

TARGET = "congruence_preserves_typing"
FILE = str(THEORIES / "Layer2.v")
R1_DRAFT = r"C:\Users\lison\Doubao\chats\2026-09-02\new-chat-57\Layer2_congruence_r1_draft.v"

def load_r1_segment():
    with io.open(R1_DRAFT, encoding="utf-8") as f:
        src = f.read()
    m1 = re.search(r"(?m)^Lemma split_refl_nil\b", src)
    m2 = re.search(r"(?m)^Theorem congruence_preserves_typing\b", src)
    end = re.search(r"(?ms)^Theorem congruence_preserves_typing\b.*?^Qed\.", src)
    seg = src[m1.start():end.end()] if (m1 and m2 and end) else "(r1草稿读取失败)"
    return seg

R1 = load_r1_segment()

BRIEF = (
 "目标：让 Theorem congruence_preserves_typing 完整 Qed，并把它依赖的全部辅助引理一次性以 "
 "INSERT-BEFORE: congruence_preserves_typing 的成品代码块给出（每个都 Lemma..Qed.）。"
 "当前文件是干净基线（该定理为 Proof.Admitted.）。请【一轮交齐】：所有辅助引理块 + 主定理 REPLACE 块，"
 "全部 Qed，不许 Abort、不许 admit/Admitted、不许只留名字。保持主定理签名 "
 "forall P P' Gamma, congruence P P' -> typed Gamma P -> typed Gamma P' 不变。"
)

STRATEGY = tuple(p for p in
  (r"分站\S04_Layer2最后3Admitted_精确证明策略_S00分析_20260903.md",)
  if (DOCS/p).exists())
PHILOS = tuple(p for p in (
  r"哲学研究\S01给S04的证明智慧手册_生命论方法论如何写Coq证明_20260902.md",
  r"哲学研究\S04致S01_OB009深度对话_线性操作权同一性与代换指回_数学哲学一体化_20260902.md",
) if (NOTES/p).exists())

EXTRA = r"""
======== 上一轮(r1)已验证结构：7 个引理已 Qed、主定理骨架已对，直接沿用，不要重造、不要改名 ========
下面是 r1 写过的完整段落。其中【已 Qed】的引理请原样沿用（可直接复制为 INSERT 块）：
split_refl_nil、split_nil_r（用库中已有 ctx_ext，勿用不存在的 ctx_ext_length）、split_sym'、
typed_par_comm、typed_par_assoc_l/r、typed_par_zero_l/r、typed_rep_unfold_l/r；
主定理 Hmain 双向合取（对 congruence 归纳、每构造子 split 正反两方向）结构正确，沿用。
【仅剩 4 个仍是 Admitted 的硬骨头，本轮必须补成 Qed】：split_assoc、typed_head_insert、
typed_res_par_l、typed_res_par_r。

==== r1 原文开始 ====
""" + R1 + r"""
==== r1 原文结束 ====

======== 4 个硬骨头的精确提示（材料A有 split/setby/ctx_ext/fv_at/ty_* 全部定义，先核对签名）========
1) split_assoc : split G G12 G3 -> split G12 G1 G2 -> exists G23, split G G1 G23 /\ split G23 G2 G3。
   split 是逐位置三选一（位置 n 归左/归右/都空）。对【位置 n 逐位置构造 G23】（用 setby 定义
   G23 在 n 的取值：综合 G2 与 G3 在该位置的归属），再按 split 的逐位置语义分情况验证两边；
   或对 G 归纳。不要用 excluded_middle 空转（r1 卡在这里）。先在材料A确认 split/setby/get 的定义式。
2) typed_head_insert : typed G P -> typed (Some T :: G) P（弱化）。对 typed P 归纳；
   难点在 ty_par：头部多一个资源位，需要先证一个 split 层面的“头部插空”小引理
   （split G G1 G2 -> split (Some U::G) (Some U::G1) G2 之类，名字/形状以 split 定义为准），
   ty_res/ty_rep 等按构造子顺推。先证这个 split 小引理再推 typed。
3) typed_res_par_l/r（带 ~ fv_at Q 0）：核心是“Q 不使用位置0，故 PRes 的那个 T 可以在 P/Q 的
   split 重划中让给 P 侧”。先用 par_elim 拆，再结合 fv_at 的定义证明 Q 所在子上下文位置0为空，
   据此重配 split（需要什么 split 移位小引理就先证什么），再用 ty_res/ty_par 双向重建。
   两个方向都要，别只给一个。

======== 输出纪律（proof_loop v2 会机械校验，违反就回喂、不改文件）========
- 主定理用到的每个自定义引理，本轮全部以独立 INSERT-BEFORE 成品块交齐到 Qed；
- 禁止 Abort. 废块、禁止同名引理重复多份、禁止只在主定理里留一个名字却不给证明；
- 只允许使用材料A中真实存在、或你本轮给出完整定义/证明的名字；确属 Coq 库的引理打
  (* @stdlib names: .. *) 并确保 Require Import；文献思路打 @cite 但仍须本库 Qed；
- 不要改动 subst_ren_general/substitution_general/insert_pts_subst 等所有已 Qed 内容；
- 本轮只新增辅助引理 + 替换 congruence_preserves_typing；其后 progress 等内容不动。
- Rocq 9.1：nat 长度式先 unfold length;cbn 再 lia；经典逻辑可用（库已开 ClassicalEpsilon 类），
  但存在性证明要给出具体见证项，不能用经典逻辑规避构造。
"""

if __name__ == "__main__":
    print("r1段长度:", len(R1), "字符")
    res = proof_loop(BRIEF, FILE, TARGET,
                     layer_files=("Layer1.v","Layer2.v"),
                     strategy_docs=STRATEGY, philos_docs=PHILOS,
                     extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=6)
    print("="*60)
    print("收敛" if res["converged"] else "未收敛（保留 .bak 与错误链）")
    for r in res["rounds"]:
        print(r)

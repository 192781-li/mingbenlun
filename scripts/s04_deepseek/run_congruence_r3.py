# -*- coding: utf-8 -*-
"""congruence 第三轮：采纳 DS 自己发现的数学修正，消除碎片化，一次交齐。
关键修正：typed_head_insert 在线性系统是【假命题】，改用 typed_empty_closed(空上下文弱化)。
用法：python run_congruence_r3.py
"""
import io, re
from _paths import THEORIES, DOCS, NOTES
from proof_loop import proof_loop

TARGET = "congruence_preserves_typing"
FILE = str(THEORIES / "Layer2.v")
R1_DRAFT = r"C:\Users\lison\Doubao\chats\2026-09-02\new-chat-57\Layer2_congruence_r1_draft.v"

def load_r1_segment():
    src = io.open(R1_DRAFT, encoding="utf-8").read()
    m1 = re.search(r"(?m)^Lemma split_refl_nil\b", src)
    end = re.search(r"(?ms)^Theorem congruence_preserves_typing\b.*?^Qed\.", src)
    return src[m1.start():end.end()] if (m1 and end) else "(r1读取失败)"

R1 = load_r1_segment()

BRIEF = (
 "目标：在干净基线上让 Theorem congruence_preserves_typing 完整 Qed，并一次性交齐它依赖的全部辅助引理。"
 "【输出顺序固定、这是完成标志】：先给若干 (* INSERT-BEFORE: congruence_preserves_typing *) 辅助引理块"
 "（每块 Lemma..Qed.，全部 Qed）；你的【最后一个代码块必须是 Theorem congruence_preserves_typing 从声明行到列0 Qed. 的完整主定理】。"
 "不允许只给辅助引理就结束、不允许在中途停笔——没有最后那个主定理完整块，本轮视为未完成。"
 "主定理签名保持 forall P P' Gamma, congruence P P' -> typed Gamma P -> typed Gamma P'。"
)

STRATEGY = tuple(p for p in
  (r"分站\S04_Layer2最后3Admitted_精确证明策略_S00分析_20260903.md",)
  if (DOCS/p).exists())
PHILOS = tuple(p for p in
  (r"哲学研究\S01给S04的证明智慧手册_生命论方法论如何写Coq证明_20260902.md",)
  if (NOTES/p).exists())

EXTRA = r"""
======== 【已确认数学修正，必须照做】========
r1 里的 `typed_head_insert : typed G P -> typed (Some T::G) P` 是【假命题】，不要再证它。
反例：typed [Some T] (PVar 0) 成立，但 typed (Some U::[Some T]) (PVar 0) 不成立（PVar 0 改指 U）。
线性系统里“头部任意插入一条资源”的弱化不成立。cong_rep_unfold 真正需要的是空上下文弱化：
    Lemma typed_empty_closed : forall G P, typed [] P -> typed G P.
它成立（空上下文可类型化的进程不依赖任何具体位置资源）。对 typed 归纳证明：
  ty_var 情形在空上下文中 get [] n 恒 None、不可能成立，矛盾消去；
  ty_par 情形用 split 的空侧性质（split G G [] 之类，r1 的 split_refl_nil/split_nil_r 可复用）；
  ty_rep 前提本就是 typed [] P，直接用；其余构造子顺推。以材料A的 typed 构造子为准。
然后 typed_rep_unfold_l 改为：inversion 得 typed [] P 后，用 typed_empty_closed 把它弱化为 typed G P，
再 ty_par（另一侧 ty_rep）。typed_rep_unfold_r 沿用 r1。

======== 【不要每轮重造基础设施】========
r1 已 Qed、直接沿用（不要改名、不要重证、不要换一套等价物）：
split_refl_nil、split_nil_r（用库中 ctx_ext，勿用不存在的 ctx_ext_length）、split_sym'、
typed_par_comm、typed_par_assoc_l/r、typed_par_zero_l/r、typed_rep_unfold_r，以及主定理 Hmain 双向合取骨架。
材料A已有 ctx_ext/setby/get/split_* 等，先检索复用；只有确无现成时才新增引理，且必须当轮 Qed。
不要再发明 make_ctx/split_G_nil/split_G_empty 等新基础设施（前几轮因此碎片化，禁止）。

======== 本轮真正要新证的清单（就这些，逐个 Qed）========
1) split_assoc : split G G12 G3 -> split G12 G1 G2 -> exists G23, split G G1 G23 /\ split G23 G2 G3。
   对位置 n 用 setby 逐位置构造 G23（综合 G2/G3 在该位归属），再按 split 逐位置语义验证；给具体见证项，
   不靠 excluded_middle 空转。typed_par_assoc_l/r 依赖它。
2) typed_empty_closed（如上，替代假命题 typed_head_insert）。
3) typed_res_par_l / typed_res_par_r（带 ~ fv_at Q 0）：par_elim 拆后，由 fv_at 定义说明 Q 所在子上下文
   的位置0为空，把 PRes 的 T 在 split 重划中让给 P 侧，双向用 ty_res/ty_par 重建；需要什么 split 移位
   小引理就先证什么（当轮 Qed）。

======== r1 原文（已Qed部分直接沿用，主定理Hmain骨架沿用，只替换假命题/补4块）========
""" + R1 + r"""
======== r1 原文结束 ========

======== 输出纪律（proof_loop v2 机械校验）========
- 最后一块必须是主定理 congruence_preserves_typing 的完整 Theorem..Qed.；
- 每个辅助引理当轮 Qed，禁止 Abort./admit/Admitted、禁止同名重复、禁止只留名字；
- 只用材料A真实存在或本轮完整定义的名字；库引理打 (* @stdlib names: .. *)；
- 不改 subst_ren_general/substitution_general/insert_pts_subst 等所有已 Qed 内容，主定理之后内容不动。
- Rocq 9.1：长度式先 unfold length;cbn 再 lia。
"""

if __name__ == "__main__":
    print("r1段:", len(R1), "字符")
    res = proof_loop(BRIEF, FILE, TARGET,
                     layer_files=("Layer1.v","Layer2.v"),
                     strategy_docs=STRATEGY, philos_docs=PHILOS,
                     extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=6)
    print("="*60); print("收敛" if res["converged"] else "未收敛")
    for r in res["rounds"]: print(r)

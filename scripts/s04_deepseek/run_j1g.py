# -*- coding: utf-8 -*-
"""J1g step1：Some 优先选择层最小步——本轮只交 (A) pick_prefix 定义 + (B) pick_prefix_correct，
纯逐位三态枚举，快速落袋；(C) 后缀引理与主定理下一轮。split_assoc 保持 Admitted。"""
from _paths import THEORIES
from proof_loop import proof_loop

TARGET = "pick_prefix_correct"
FILE = str(THEORIES / "Layer2.v")

BRIEF = (
    "严格按随附《J1g_split_assoc_Some优先选择_机器定案》执行。split_assoc 主命题已被独立 guard 机器证实为真，严禁判假/交反例。"
    "本轮【只交两件、最小步、快速 Qed】：(A) Definition pick_prefix（Some 优先逐位选择，替换'左-左取g2'的错误 choose：在同时满足两个 cell_split 的候选里优先取在位值 Some _，全越界才取 None）；"
    "(B) Lemma pick_prefix_correct（对五个 option(option ty) 三态穷举，证它满足 cell_split g g1 (pick..) /\\ cell_split (pick..) g2 g3）。"
    "【本轮不要交 (C) 后缀引理、不要构造 G23、不要碰主定理】，那是下一轮。直接依赖的 get 小事实可当轮立 @prove。"
    "不许替换 Lemma split_assoc（保持 Admitted）、不删已 Qed 的 choose、不 iff。option 三态 destruct as [[T|]|]，分清 None 越界 / Some None 在位空。直接给代码，不要长段自然语言。"
)
PHILOS = ("Coq形式化/J1g_split_assoc_Some优先选择_机器定案_20260904.md",
          "Coq形式化/J1f_split_assoc最小步_后缀性引理先行_20260904.md")

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v", "Layer2.v"),
                     philos_docs=PHILOS, model="deepseek-v4-pro", max_rounds=4)
    print("=" * 60); print("收敛" if res["converged"] else "未收敛"); print(res)

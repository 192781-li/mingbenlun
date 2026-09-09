# -*- coding: utf-8 -*-
"""J1c 修复闭环：split_assoc 已是完整证明、真实 Admitted=0，仅 split_assoc_cell_pick
有一个 option 双层(None 越界 vs Some None 在位)类型错。让 DS 只修 pick，coqc 终裁。"""
from _paths import THEORIES
from proof_loop import proof_loop

TARGET = "split_assoc"
FILE = str(THEORIES / "Layer2.v")

BRIEF = (
    "当前 Layer2 已包含且【不要重新交付】：Definition cell_split、Lemma split_assoc_cell(已Qed)、"
    "Definition fcell、Lemma length_setby、Lemma cell_split_none_end，以及 Lemma split_assoc 的完整证明(已无 Admitted)。\n"
    "现在整文件 coqc 只剩【一个】类型错误，位于 Lemma split_assoc_cell_pick 内部，原文：\n"
    "  File Layer2.v, line 2372: The term \"He2'\" has type \"g2 = None\" while it is expected to have type \"g2 = Some None\".\n"
    "根因（结晶010：option 双层不可错位）：g 层是 option(option ty)，三态为 None(越界之寂) / Some None(在位之寂) / Some(Some T)(真实发用)；"
    "你在 pick 的某个 destruct 分支里把假设 He2' : g2 = None（越界）错当成了需要的 g2 = Some None（在位），二者不相等、不能 exact。\n"
    "任务：用 REPLACE 只给 Lemma split_assoc_cell_pick 从 Lemma 行到 Qed. 的完整修正版，"
    "系统排查它的每一个析取分支，严格区分 None 与 Some None，该用哪条等式就用哪条、必要时对 g2/g3 再 destruct as [[a|]|] 三分支，"
    "保证每个 cell_split 目标左右两侧的层级完全对齐，0 Admitted、0 Abort。\n"
    "【严禁】重交 cell_split/split_assoc_cell/fcell/length_setby/cell_split_none_end 的定义；"
    "【尽量不要】改动 split_assoc 主定理，仅当 pick 的签名或返回结构被迫调整时才做最小联动，并在输出里说明。"
    "只输出需要 REPLACE 的 split_assoc_cell_pick 完整块（若必须联动主定理，再附 split_assoc 的 REPLACE 块）。"
)
PHILOS = ("Coq形式化/J1_split_assoc冻结蓝图与逐位判定任务书_20260904.md",)

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v", "Layer2.v"),
                     philos_docs=PHILOS, model="deepseek-v4-pro", max_rounds=4)
    print("=" * 60)
    print("收敛" if res["converged"] else "未收敛")
    print(res)

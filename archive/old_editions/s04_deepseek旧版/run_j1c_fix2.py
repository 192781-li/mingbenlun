# -*- coding: utf-8 -*-
"""J1c 修复闭环·换路：pick 引理不再手写四命名大分支，改为析取代入后 option 三态暴力枚举。
强约束：split_assoc 为真已被机器证实(split_assoc_cell 已 Qed/J0 类型检查)，禁止判假、禁止长篇空转。"""
from _paths import THEORIES
from proof_loop import proof_loop

TARGET = "split_assoc"
FILE = str(THEORIES / "Layer2.v")

BRIEF = (
    "【事实前提，不得质疑】split_assoc 为真已经被机器证实：Lemma split_assoc_cell 已在本文件 Qed，"
    "J0 阶段见证的类型也已 coqc 检查通过。你的唯一任务是修好 Lemma split_assoc_cell_pick 里的一个分支类型错，"
    "禁止讨论或宣称该命题/引理为假，禁止输出任何 false/反例/不可证结论（此类输出一律视为错误），直接给代码、不要长篇分析。\n"
    "当前唯一错误原文：The term \"He2'\" has type \"g2 = None\" while it is expected to have type \"g2 = Some None\"。"
    "根因：option(option ty) 三态 None(越界)/Some None(在位空)/Some(Some a)(发用) 中，你把越界 None 与在位 Some None 混作一层。\n"
    "【换路要求】不要再用上一版那种手写 He2'/He3' 命名、逐格 exact 的四命名大分支（你在里面反复错位）。改用更机械、不易错的枚举法：\n"
    " 1) 先 unfold cell_split；intros 后 destruct H1 as [[-> He3]|[-> He12]], H2 as [[-> He2]|[-> He1]] 用析取同步把 g12 直接代入（能用 -> 就别命名再 subst）；\n"
    " 2) 每个大支内部，对仍自由的 g2/g3 统一 destruct ... as [[a|]|] 做三态枚举；\n"
    " 3) unfold fcell 后 cbn 化简 match；被 Hne 排除的矛盾格用 exfalso + destruct Hne + congruence/discriminate 清掉；\n"
    " 4) 其余格按化简结果 left/right 选析取、split、auto/ reflexivity/ congruence 收尾，确保每一格等式左右的 option 层完全对齐（None 对 None、Some None 对 Some None）。\n"
    "只输出 Lemma split_assoc_cell_pick 从 Lemma 行到 Qed. 的【一个 REPLACE 完整块】，0 Admitted/0 Abort。\n"
    "【冻结】不要重交 cell_split/split_assoc_cell/fcell/length_setby/cell_split_none_end，不要改 split_assoc 主定理（pick 签名保持不变，主定理无需联动）。"
)
PHILOS = ("Coq形式化/J1_split_assoc冻结蓝图与逐位判定任务书_20260904.md",)

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v", "Layer2.v"),
                     philos_docs=PHILOS, model="deepseek-v4-pro", max_rounds=4)
    print("=" * 60); print("收敛" if res["converged"] else "未收敛"); print(res)

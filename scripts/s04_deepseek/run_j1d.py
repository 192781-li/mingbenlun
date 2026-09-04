# -*- coding: utf-8 -*-
"""J1d：弃假引理 fcell/pick，按已Qed的split_assoc_cell四格见证重证split_assoc主定理。
小步：第一步只交 choose + choose正确性引理(insert_only沉淀)，第二步再交主定理。"""
from _paths import THEORIES
from proof_loop import proof_loop

TARGET = "split_assoc"
FILE = str(THEORIES / "Layer2.v")

BRIEF = (
    "严格按随附《J1d_split_assoc主定理正确路线》任务书执行，先完整读它。两条铁事实：split_assoc 主命题为真(已被 split_assoc_cell 的 Qed 机器证实，禁止再判假/交反例)；"
    "你之前的 fcell/split_assoc_cell_pick 已被独立 coqc 反例证伪，禁止再用。\n"
    "本轮【只做任务书第一步】：用 INSERT-BEFORE 在 split_assoc 之前交 (a) 正确的逐位选择函数 choose(左-左格取 g2，其余三格取 g，规则见任务书表格)，"
    "(b) choose 正确性引理：cell_split g g12 g3 -> cell_split g12 g1 g2 -> cell_split g g1 (choose ...) /\\ cell_split (choose ...) g2 g3，"
    "按已 Qed 的 split_assoc_cell 同样的四格 destruct 证明，必真且应很短，全部到 Qed、0 Admitted。\n"
    "本轮【不要】交 split_assoc 主定理(第二步再交)，不要重交 cell_split/split_assoc_cell，不要 fcell/pick。直接给代码。"
)
PHILOS = ("Coq形式化/J1d_split_assoc主定理正确路线_弃fcell用Qed见证_20260904.md",
          "Coq形式化/J1_split_assoc冻结蓝图与逐位判定任务书_20260904.md")

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v", "Layer2.v"),
                     philos_docs=PHILOS, model="deepseek-v4-pro", max_rounds=6)
    print("=" * 60); print("收敛" if res["converged"] else "未收敛"); print(res)

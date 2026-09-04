# -*- coding: utf-8 -*-
"""J1 看板工序：split_assoc 逐位判定【小步流水线】。
首轮只交 cell_split 定义 + split_assoc_cell 有限小引理(INSERT-BEFORE)，
proof_loop 的 insert_only 分步交机制会 coqc 固化后，第二轮再让 DS 交主定理。
用法：python run_j1_split_assoc.py"""
from _paths import THEORIES
from proof_loop import proof_loop

TARGET = "split_assoc"
FILE = str(THEORIES / "Layer2.v")

BRIEF = (
    "目标是最终消掉 Layer2 的 split_assoc，但【本轮只做第一步 J1-a，先不要给 split_assoc 主定理的新版本】。\n"
    "本轮只在 split_assoc 之前用 INSERT-BEFORE 交付以下两段，并都完整 Qed（0 Admitted、0 Abort）：\n"
    "(1) Definition cell_split (g a b : option (option ty)) : Prop :=\n"
    "      (a = g /\\ (b = None \\/ b = Some None)) \\/ (b = g /\\ (a = None \\/ a = Some None)).\n"
    "(2) Lemma split_assoc_cell : forall (g g12 g3 g1 g2 : option (option ty)),\n"
    "      cell_split g g12 g3 -> cell_split g12 g1 g2 ->\n"
    "      exists g23 : option (option ty), cell_split g g1 g23 /\\ cell_split g23 g2 g3.\n"
    "证法（纯有限枚举，约 9–20 行，不要想主定理）：intros g g12 g3 g1 g2 H1 H2；"
    "先 destruct H1 as [(-> & [->|->]) | (-> & [->|->])]、H2 同形，用析取同步代入把 g12/g3/g1/g2 的等式一次性钉死，"
    "矛盾格 discriminate、重复格合并；对剩下的有限格 exists 一个 g23（选择：g2 为 Some(Some x) 取它，否则取 g3，皆空取 None 或 Some None 使两个 cell_split 同时成立），"
    "再 left/right 选析取，auto / discriminate / injection 收尾。option 双层：None 与 Some None 是不同 get 层值，Some(Some x)=Some None 用 injection。\n"
    "【本轮严禁输出 split_assoc 的证明替换块】，只交上面两个 INSERT-BEFORE 片段；系统确认辅助引理 coqc 通过后，下一轮再让你交主定理。完整背景见随附 J1 任务书。"
)

PHILOS = ("Coq形式化/J1_split_assoc冻结蓝图与逐位判定任务书_20260904.md",)

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v", "Layer2.v"),
                     philos_docs=PHILOS,
                     model="deepseek-v4-pro", max_rounds=6)
    print("=" * 60)
    print("收敛" if res["converged"] else "未收敛（保留 .bak 与错误链，board block 并流转 S01）")
    print(res)

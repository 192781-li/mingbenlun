# -*- coding: utf-8 -*-
"""J1f step1：最小步，只证 choose_suffix（choose取None位向后闭=非None位是前缀）。
split_assoc 仍 Admitted 不阻止编译；目标段 choose_suffix 无 admit 即收敛。"""
from _paths import THEORIES
from proof_loop import proof_loop

TARGET = "choose_suffix"
FILE = str(THEORIES / "Layer2.v")

BRIEF = (
    "严格按随附《J1f_split_assoc最小步_后缀性引理先行》执行。本轮【只交一个新引理 choose_suffix】(INSERT-BEFORE Lemma split_assoc)，"
    "连同它直接依赖、材料里没有的 1-2 个 get 越界后缀小引理，全部 Qed、0 Admitted。"
    "不许碰/替换 split_assoc 主引理(它保持 Admitted)，不许造 G23，不许重交已 Qed 的 cell_split/split_assoc_cell/is_empty_get/choose/choose_correct。"
    "方向已被独立 guard 机器证实为真(任务书第0节)，禁止判假/交反例。按任务书第2节骨架补成可编译 tactic，option 三态 destruct as [[T|]|]。直接给代码。"
)
PHILOS = ("Coq形式化/J1f_split_assoc最小步_后缀性引理先行_20260904.md",
          "Coq形式化/J1e_split_assoc前缀长度见证构造_20260904.md")

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v", "Layer2.v"),
                     philos_docs=PHILOS, model="deepseek-v4-pro", max_rounds=4)
    print("=" * 60); print("收敛" if res["converged"] else "未收敛"); print(res)

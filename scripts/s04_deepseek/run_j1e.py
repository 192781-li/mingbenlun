# -*- coding: utf-8 -*-
"""J1e：前缀长度构造 G23，收官 split_assoc。第一步交后缀引理+逐位读出(insert_only)，第二步主定理。"""
from _paths import THEORIES
from proof_loop import proof_loop

TARGET = "split_assoc"
FILE = str(THEORIES / "Layer2.v")

BRIEF = (
    "严格按随附《J1e_split_assoc前缀长度见证构造》执行，先完整读它并对齐 option 双层类型。已 Qed 零件：cell_split/split_assoc_cell/is_empty_get/choose/choose_correct，直接用，禁止重交。\n"
    "两条已证伪死路不许再走：固定长度表+字面等式 get G23 n=choose_val n；choose_none_iff(其反向为假，若文件里残留请删除)。\n"
    "本轮【只做 J1e 第一步】(INSERT-BEFORE，全部 Qed、0 Admitted)：(1) 后缀引理——两 split 前提下 choose(逐位get) 为 None 的位构成后缀，用 J1e 第2节的排除交错论证；"
    "(2) 按在位前缀长度构造 G23(firstn/截断或等价)，并证逐位读出：在位前缀位 get G23 n=Some(choose剥层)且 choose 非 None；越界后缀位 get G23 n=None 且五个 get 皆 None。\n"
    "本轮【不要】REPLACE 主引理 split_assoc(第二步再交)。写新引理前先在脑中对关键格枚举确认为真。直接给代码，不要判主命题假。"
)
PHILOS = ("Coq形式化/J1e_split_assoc前缀长度见证构造_20260904.md",
          "Coq形式化/J1d_split_assoc主定理正确路线_弃fcell用Qed见证_20260904.md",
          "Coq形式化/J1_split_assoc冻结蓝图与逐位判定任务书_20260904.md")

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v", "Layer2.v"),
                     philos_docs=PHILOS, model="deepseek-v4-pro", max_rounds=8)
    print("=" * 60); print("收敛" if res["converged"] else "未收敛"); print(res)

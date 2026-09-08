# -*- coding: utf-8 -*-
"""S04 当前证明目标的一键入口。随任务推进改 TARGET / brief / strategy_docs。
用法：python run_current.py [目标引理名]   （不传则用默认 TARGET）
"""
import sys
from _paths import THEORIES
from proof_loop import proof_loop

TARGET = sys.argv[1] if len(sys.argv) > 1 else "subst_ren_general"
FILE = str(THEORIES / "Layer2.v")

BRIEF = {
 "subst_ren_general":
   "证出 subst_ren_general 的最后一个 case：并行组合 PPar（对进程 Q 归纳版本，当前该 case 为 admit，"
   "其余 7 个 case 已 Qed）。代换=非单射重命名 subst_var=ren(subst_name m k)；碰撞对靠已 Qed 的 "
   "typed_strengthen_unused / typed_strengthen_collisions 紧缩冗余位后，仿 Layer1.ren_typed 的 ty_par。"
   "请给出该 Lemma 从 Lemma 行到 Qed. 的完整新版本；若需辅助引理，用 INSERT-BEFORE 标记并完整证明。",
}.get(TARGET, f"请完整证出 {TARGET}（当前为 Admitted/admit），给从声明行到 Qed. 的完整新版本。")

# S00 策略仅作参考，其"m≥k 时 rho 单射"为假，碰撞统一用 collision_other——已在 extra_notes 勘误
STRATEGY = (r"分站\S04_Layer2最后3Admitted_精确证明策略_S00分析_20260903.md",)
EXTRA = ("已知勘误：S00 策略中'm≥k 时 rho 单射'不成立，碰撞统一按 collision_other / rho_inj_except_m 处理；"
         "对 typed 归纳走不通（IH 源被构造子 index 锁死），当前采用对进程 Q 归纳。")

if __name__ == "__main__":
    import os
    sd = tuple(p for p in STRATEGY if (THEORIES.parents[0] / "docs" / "协作机制" / p).exists())
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v","Layer2.v"),
                     strategy_docs=sd, extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=5)
    print("="*60)
    print("收敛" if res["converged"] else "未收敛（已保留全部 .bak 与错误链，标 blocked 流转 S01）")
    print(res)

# -*- coding: utf-8 -*-
"""Layer2 目标1：subst_ren_general 完整 Qed（DS 主谋闭环）。
S04 只做承接：把 Layer1+2 全文、S00 策略、生命论哲学、当前 coqc 错误全量交给 DS，
proof_loop 自动 备份->替换->coqc->错误回喂，直到目标段编译通过且无 admit。
用法：python run_subst_ren.py
"""
import os, sys
from _paths import THEORIES, DOCS, NOTES
from proof_loop import proof_loop

TARGET = "subst_ren_general"
FILE = str(THEORIES / "Layer2.v")

# 第一轮喂入的真实编译错误基线（之后由 proof_loop 自动用最新 coqc 输出覆盖）
ERR = r"""File ".\Layer2.v", line 1427, characters 2-115:
Warning: Unused introduction pattern: pz
File ".\Layer2.v", line 1455, characters 28-33:
Error: The variable Gamma was not found in the current environment."""

BRIEF = (
 "目标：让 Lemma subst_ren_general（Layer2.v 约1419-1561行）整体 Qed、可编译，"
 "并补完其中 PPar case（当前1542行为 admit）。这是对进程 Q 归纳、源上下文 D 与目标上下文 G 双上下文版本：\n"
 "  intros D Q. revert D. induction Q as [...]; intros D HTD m k G Hpts Hnu; simpl in *.\n"
 "即归纳假设/前提里【源上下文叫 D，目标上下文叫 G】，环境中根本没有名为 Gamma 的变量。\n"
 "当前第一个编译错误（必须先修）：POut 分支 line1455 `rewrite (set_none_neq Gamma x y Hyx)`、"
 "以及 1468/1474/1478、PIn 1516、PRes 1550 等处误把【源上下文 D】写成了 Gamma；请逐处改回 D（目标侧仍是 G）。\n"
 "PPar 分支：代换=非单射重命名 ren(subst_name m k)，碰撞对 {k,m} 靠已 Qed 的 "
 "typed_strengthen_unused / typed_strengthen_collisions / split_strengthen / use_strengthen "
 "把未被使用一侧的冗余位收摄后，仿 Layer1.ren_typed 的 ty_par（Layer1.v 约356-391行）构造；"
 "也可参考本文件已完整 Qed 的 subst_var_keep_free、free_split_l/free_split_r、substitution_none_strengthen 的 PPar 写法。\n"
 "输出协议：给出 subst_ren_general 从 `Lemma subst_ren_general` 声明行到列0 `Qed.` 的【完整新版本】（不是片段、不是省略号）；"
 "若确需新辅助引理，单独用 ```coq 块并在块首加注释 (* INSERT-BEFORE: subst_ren_general *)，且必须完整证明、不得使用材料A中不存在的名字。"
)

STRATEGY = tuple(p for p in
  (r"分站\S04_Layer2最后3Admitted_精确证明策略_S00分析_20260903.md",)
  if (DOCS/p).exists())

PHILOS = tuple(p for p in (
  r"哲学研究\S01给S04的证明智慧手册_生命论方法论如何写Coq证明_20260902.md",
  r"哲学研究\S04致S01_OB009深度对话_线性操作权同一性与代换指回_数学哲学一体化_20260902.md",
  r"哲学研究\S01对S04_substitution_general卡点研判_use关系代换_20260902.md",
  r"哲学研究\S01给S04_substitution_general精确证明骨架_防止DeepSeek跑偏_20260902.md",
) if (NOTES/p).exists())

EXTRA = (
 "勘误1：S00 策略文档称'm≥k 时 rho=subst_name m k 单射'，此断言为假；碰撞统一用 collision_other / rho_inj_except_m，"
 "不要假设 m≥k 单射。勘误2：对 typed 归纳走不通（IH 源被构造子 index 锁死，induction H in D / dependent induction 均失败），"
 "本引理已确定走对进程 Q 归纳，不要退回对 typed 归纳。"
 "注意：本文件 substitution_general、congruence_preserves_typing 仍各自含 admit，那是后续目标，【本轮不要改它们】，只让 subst_ren_general 这一段 Qed。"
)

if __name__ == "__main__":
    print("strategy_docs:", STRATEGY)
    print("philos_docs:", PHILOS)
    # 直接把基线错误作为第一轮 coqc_error：通过 monkeypatch proof_loop 内部首轮变量更简单的方式是
    # proof_loop 不接受初始 error，故这里用 extra_notes 携带错误全文，首轮 DS 同样可见。
    res = proof_loop(BRIEF, FILE, TARGET,
                     layer_files=("Layer1.v", "Layer2.v"),
                     strategy_docs=STRATEGY, philos_docs=PHILOS,
                     extra_notes=EXTRA + "\n\n[当前 coqc 真实输出]\n" + ERR,
                     model="deepseek-v4-pro", max_rounds=6)
    print("="*60)
    print("收敛" if res["converged"] else "未收敛（保留 .bak 与错误链，标 blocked 流转 S01）")
    for r in res["rounds"]:
        print(r)

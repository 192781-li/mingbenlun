# -*- coding: utf-8 -*-
"""S04 当前证明目标的一键入口。随任务推进改 TARGET / brief / strategy_docs。
用法：python run_current.py [目标引理名]   （不传则用默认 TARGET）

V4.1 上下文升级：DS获取一切——悟道/河流/S01研判/运行指令全部喂入，
不再只喂Layer全文+一个S00策略。哲学智慧是证明的方向，数学对错仍以coqc为准。
"""
import sys
from _paths import THEORIES, DOCS, NOTES
from proof_loop import proof_loop

TARGET = sys.argv[1] if len(sys.argv) > 1 else "subject_reduction"
FILE = str(THEORIES / "Layer2.v")

BRIEF = {
 "subst_ren_general":
   "证出 subst_ren_general 的最后一个 case：并行组合 PPar（对进程 Q 归纳版本，当前该 case 为 admit，"
   "其余 7 个 case 已 Qed）。代换=非单射重命名 subst_var=ren(subst_name m k)；碰撞对靠已 Qed 的 "
   "typed_strengthen_unused / typed_strengthen_collisions 紧缩冗余位后，仿 Layer1.ren_typed 的 ty_par。"
   "请给出该 Lemma 从 Lemma 行到 Qed. 的完整新版本；若需辅助引理，用 INSERT-BEFORE 标记并完整证明。",
"subject_reduction":
   "证出 subject_reduction（主题归约保持类型：typed Gamma P / reduce Gamma P Q -> typed Gamma Q），"
   "Layer3 line580 的 subject_reduction_self/alien 依赖它。先按结晶022 对最小进程枚举/预检锁定为真，"
   "按结晶021 把每步化归切成带假设小引理；给从声明行到 Qed. 的完整新版本，辅助引理用 INSERT-BEFORE 完整证明。",
}.get(TARGET, f"请完整证出 {TARGET}（当前为 Admitted/admit），给从声明行到 Qed. 的完整新版本。")

# ========== 材料B：策略/状态文档（相对于 docs/协作机制/）==========
# S00策略仅作参考，其"m≥k 时 rho 单射"为假，碰撞统一用 collision_other——已在 extra_notes 勘误
STRATEGY = (
    r"分站\S04_运行指令.md",                              # 唯一权威SOP（五阶段+铁律）
    r"分站\S04_L2收官攻坚计划_鞍钢宪法三结合_20260904.md",  # L2收官计划
    r"分站\S04_Layer2最后3Admitted_精确证明策略_S00分析_20260903.md",  # S00策略（部分已勘误）
    r"智慧河流\河流主干.md",                               # S01研判时间线
    r"智慧河流\河流状态.md",                               # 当前卡点+case进度
    r"智慧河流\S04启动必读_一页纸摘要.md",                 # 启动必读
    r"智慧河流\智慧结晶库.md",                             # 全部结晶（含021/022），证明前必读
)

# ========== 材料C：生命论哲学智慧（相对于 docs/notes/）==========
# 让DS理解存在论主线——操作权如何流动、每个定义的哲学内涵、S01的证明方法论
PHILOS = (
    r"哲学研究\S01给S04的证明智慧手册_生命论方法论如何写Coq证明_20260902.md",  # 核心！S01的证明方法论
    r"哲学研究\S01给S04_substitution_general精确证明骨架_防止DeepSeek跑偏_20260902.md",
    r"哲学研究\S01对S04_substitution_general卡点研判_use关系代换_20260902.md",
    r"哲学研究\S01给S04_DeepSeek逐个证明指令包_4个引理一次只证一个_20260902.md",
    r"哲学研究\S01_OB001补充_ren_typed单射性障碍与代换的存在论本质_20260902.md",
    # 2026-09-10 S01最新研判（针对OB-015/016，精确到tactic级别）
    r"Coq形式化\S01给S04_OB015_OB016贯穿证明策略_choose路线_20260910.md",
    r"Coq形式化\S01给S04_split_assoc基例OB-015根因与修复规格_20260910.md",
    r"Coq形式化\S01给S04_L3-L8哲学预判总纲_证明强度渐进策略_20260910.md",
)

EXTRA = ("已知勘误：S00 策略中'm≥k 时 rho 单射'不成立，碰撞统一按 collision_other / rho_inj_except_m 处理；"
         "对 typed 归纳走不通（IH 源被构造子 index 锁死），当前采用对进程 Q 归纳。"
         "材料B/C中的策略与哲学智慧是方向参考，数学对错以材料A(Layer全文)和coqc编译为准。"
         "【结晶021·强制】destruct (f ..) eqn:E 会把目标里藏在未展开定义体中的同名 f 一并替换成构造子，"
         "导致之后 rewrite E 失配；凡依赖某等式化归的步骤，必须抽成带假设 H、不 destruct 的独立小引理，"
         "主上下文只 apply，禁止在 destruct eqn 后的大上下文里硬 rewrite；反复失配先插 idtac 打印真实目标，"
         "rewrite 常数等式前先 Opaque，递增下标归纳先 revert k，合取用 destruct as 不用 .1/.2。"
         "【结晶022·强制】若你开始怀疑命题为假或三轮不收敛，先不要判假：存在性中间块通常不是现成实体、"
         "而是按归属规则逐位重新聚拢（遇空位截断）构造；派单前 S04 已/应做有限枚举，0 反例即命题为真，"
         "问题在证明路线与引理强度，不在真假。")

if __name__ == "__main__":
    import os
    sd = tuple(p for p in STRATEGY if (DOCS / p).exists())
    pd = tuple(p for p in PHILOS if (NOTES / p).exists())
    print(f"[上下文] 策略文档 {len(sd)}/{len(STRATEGY)} 个，哲学智慧 {len(pd)}/{len(PHILOS)} 个")
    for p in sd: print(f"  [策略] {p}")
    for p in pd: print(f"  [哲学] {p}")
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v","Layer2.v"),
                     strategy_docs=sd, philos_docs=pd, extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=5)
    print("="*60)
    print("收敛" if res["converged"] else "未收敛（已保留全部 .bak 与错误链，标 blocked 流转 S01）")
    print(res)

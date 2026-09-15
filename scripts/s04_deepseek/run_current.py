# -*- coding: utf-8 -*-
"""S04 当前证明目标的一键入口。随任务推进改 TARGET / brief / strategy_docs。
用法：python run_current.py [目标引理名]   （不传则用默认 TARGET）

V4.2 上下文精简（2026-09-15）：DS 不睁眼瞎——材料只保留"当前一条最简证明链"。
- 材料B：当前证明链卡（核心，DS 先读）+ 行为手册（条件反射/tactic工艺）+ 河流状态；
  已收官战场（substitution/choose/split_assoc 旧研判、S00旧策略、L2旧计划、河流主干流水、
  启动一页纸）不再每轮灌，文件留库不删；结晶库全文已由 s04_context 在 system 前缀提供，不在此重复。
- 材料C：只留通用证明方法论 + 与当前目标相关的哲学预判。
哲学智慧是方向，数学对错以 Layer 全文与 coqc 为准。
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
   "勘误：'m>=k 时 rho 单射'不成立，碰撞统一按 collision_other / rho_inj_except_m；"
   "对 typed 归纳走不通（IH 源被构造子 index 锁死）时改对进程 Q 归纳。"
   "请给出该 Lemma 从 Lemma 行到 Qed. 的完整新版本；若需辅助引理，用 INSERT-BEFORE 标记并完整证明。",
 "subject_reduction":
   "先读材料B的《当前证明链_subject_reduction》，严格按 J1->J2->J3，不要另起炉灶、不要重证已 Qed 零件。"
   "现状：Layer1/2 自有定理 0 Admitted、整层 coqc exit=0；Layer2 目前没有 subject_reduction 本体"
   "（旧 SUMMARY 注释称 FULLY PROVED 不属实，以代码为准），Layer3 line580/592 等它。"
   "J1 先证 congruence_preserves_typing（唯一缺口，congruence 11 构造子；cong_sym 方向反转，"
   "用成对加强归纳同时证正反两方向；cong_res_par 直接调已 Qed 的 typed_res_par_l/r，cong_par_assoc 用 split_assoc）。"
   "J2 再证 subject_reduction（对 reduce 六构造子归纳；red_comm 是空真分支，直接 exfalso + 已 Qed 的 "
   "no_parallel_channel_sharing，不要做任何 comm 代换；red_par_l/r 用 par_elim+ty_par+IH，red_cong 用 J1；"
   "旧六分支骨架见 coq/theories/ALL/backup_9.0.1/Layer2.v 218-251，其所需零件当前全部已 Qed）。"
   "每个引理给从声明行到 Qed. 的完整新版本，辅助引理用 INSERT-BEFORE 完整证明到 Qed，不留名字。",
}.get(TARGET, f"请完整证出 {TARGET}（当前为 Admitted/admit），给从声明行到 Qed. 的完整新版本。")

# ========== 材料B：当前证明链 + 条件反射工艺 + 状态（相对于 docs/协作机制/）==========
# V4.2：只喂当前目标用得上的；结晶库在 system 前缀不重复；旧战场留库不每轮灌
STRATEGY = (
    r"分站\当前证明链_subject_reduction.md",                    # 核心：当前目标最简施工链（DS 先读）
    r"分站\S04_行为手册_提前规避与条件反射_v1.0.md",             # 条件反射/tactic工艺/红线（v2.0 精炼版）
    r"智慧河流\河流状态.md",                                     # 当前卡点与全局进度
)

# ========== 材料C：通用方法论 + 当前相关哲学预判（相对于 docs/notes/）==========
# 已收官的 substitution/choose/split_assoc/OB001/OB015 旧研判不再每轮喂（教训已入结晶库）
PHILOS = (
    r"哲学研究\S01给S04的证明智慧手册_生命论方法论如何写Coq证明_20260902.md",  # 通用证明方法论
    r"Coq形式化\S01给S04_L3-L8哲学预判总纲_证明强度渐进策略_20260910.md",      # subject_reduction->L3 相关
)

EXTRA = ("材料B/C是方向参考，数学对错以材料A(Layer全文)和coqc编译为准；先读材料B的当前证明链卡，按其工序，勿重复已Qed零件。"
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

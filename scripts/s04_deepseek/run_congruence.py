# -*- coding: utf-8 -*-
"""Layer2 目标3（最后一个 Admitted）：congruence_preserves_typing 完整 Qed。
11 构造子；cong_sym 方向反转 -> 用 Hmain 双向合取对 congruence 归纳（S00 3.3 方案）。
DS 主谋，S04 承接 coqc 终裁。用法：python run_congruence.py
"""
from _paths import THEORIES, DOCS, NOTES
from proof_loop import proof_loop

TARGET = "congruence_preserves_typing"
FILE = str(THEORIES / "Layer2.v")

ERR = r"""当前：Theorem congruence_preserves_typing 在约2165行以 `Proof. Admitted.` 收尾。
目标：整体 Qed、该定理段内 0 admit、coqc 全绿（其余文件已全绿，不要破坏）。"""

BRIEF = (
 "目标：让 Theorem congruence_preserves_typing 完整 Qed、定理段 0 admit、coqc 全绿，"
 "并保持其类型签名 forall P P' Gamma, congruence P P' -> typed Gamma P -> typed Gamma P' 逐字不变"
 "（subject_reduction 依赖它）。需要的结构保持引理用独立 ```coq 块给出、块首加 "
 "(* INSERT-BEFORE: congruence_preserves_typing *)，全部完整证明到 Qed，不许 admit。"
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

EXTRA = r"""
======== congruence 的 11 个构造子（材料A约180-193，以此为准）========
cong_refl(P~P) / cong_sym(对称,方向反转) / cong_trans(传递) /
cong_par_comm(PPar P Q ~ PPar Q P) / cong_par_assoc(结合) / cong_par_zero(PPar P PZero ~ P) /
cong_res_par(~fv_at Q 0 -> PRes(PPar P Q) ~ PPar(PRes P) Q) / cong_rep_unfold(PRep P ~ PPar P(PRep P)) /
cong_par_cong / cong_res_cong / cong_tau_cong（三个同余闭包）。

======== 主方案：双向合取加强版，一次归纳解决 cong_sym（S00 3.3）========
不要直接 induction Hc（cong_sym 处 IH 方向反了）。先在证明内立：
  Hmain : forall P Q, congruence P Q -> forall Gamma,
           (typed Gamma P -> typed Gamma Q) /\ (typed Gamma Q -> typed Gamma P).
对 Hc: congruence P Q 归纳，每个构造子都 split 出正反两方向：
  - cong_refl：两支都 exact 自身；
  - cong_sym：直接交换 IHHc 合取的两支；
  - cong_trans：正向 IHHc1 正向再接 IHHc2 正向，反向反向链逆序；
  - cong_par_comm/assoc/zero/res_par/rep_unfold：正反方向分别用对应“结构保持引理”及其逆
    （这些等式都是对称的，引理最好直接证成双向，或证两个单向）；
  - cong_par_cong/res_cong/tau_cong：用 IHHc（必要时两支都用）配合 ty_par/ty_res/ty_tau 重建。
最后用 Hmain 取出正向即得原目标。

======== 已就位、直接用（行号以材料A为准，勿重证、勿改名）========
- split_sym（Layer2 约418，split 交换）；par_elim（约436，typed(PPar P Q)->存在 split+两子typed）；
  split_get_l/split_get_r（Layer1 约121/132）；类型规则 ty_zero/ty_par/ty_res/ty_tau/ty_rep（Layer1）。
- 库里【没有】 split 的结合律 split_assoc、空列表 split_nil_r、以及 typed [] P -> typed G P 的
  weakening（弱化）引理——若结构引理需要，就自己先证成小引理（都是 ctx 列表算术/归纳，10-20 行），
  全部 Qed，不许留 admit，也不许编造材料A中不存在的名字（用前先在材料A全文核对签名）。

======== 五个结构等式保持引理的注意点 ========
- par_comm：par_elim 拆出 split G G1 G2 与两子推导，用 split_sym 交换后 ty_par 重建，双向同理。
- par_assoc：需要 split 的结合/重配（先证 split_assoc 类小引理）。
- par_zero：PZero 只能由 ty_zero 类型化、其上下文为 []，用 split 与空列表引理 split_nil_r 收回。
- res_par：带前提 ~ fv_at Q 0（名字以材料A fv_at 定义为准），把 PRes 在 PPar 内外挪动，
  两边 typed 互推；留意 PRes 对应 ty_res、PPar 对应 ty_par 的上下文重建顺序。
- rep_unfold：ty_rep 的前提是 typed [] P（空上下文）。要从 typed G (PRep P) 推 typed G (PPar P (PRep P))，
  需要把 typed [] P 弱化到某个子上下文（weakening），另一半 PRep P 用 ty_rep；反向用 par_elim + ty_rep 形状收回。
  弱化引理若库中没有请先证（对 typed 归纳，空/任意上下文保持）。

======== 反重复堆积（上一目标血泪教训，务必遵守）========
每个辅助引理名在你的整次回答里【只允许出现一个代码块、只给一份】，输出前自检：
不要把同一引理反复 INSERT；主定理 congruence_preserves_typing 只给一个 REPLACE 完整版本。
若某个引理上一轮已给、这轮只改它，就只输出改后的那一份，不要顺带重复别的引理。

======== 冻结约束 ========
1. subst_ren_general / substitution_general / insert_pts_subst / strengthening 引理群等
   【所有已 Qed 内容一字不改】；本轮只“新增辅助引理 + 替换 congruence_preserves_typing 这一段”。
2. 定理签名保持 forall P P' Gamma；subject_reduction 及其后内容不动。
3. 全段不许 admit/Admitted；Rocq 9.1、经典逻辑、无 funext；nat 长度式先 unfold length;cbn 再 lia。
4. inversion ...; subst 时不要误清后续要用的归纳假设 IHHc。

[当前状态]
""" + ERR

if __name__ == "__main__":
    print("strategy_docs:", STRATEGY)
    print("philos_docs:", PHILOS)
    res = proof_loop(BRIEF, FILE, TARGET,
                     layer_files=("Layer1.v", "Layer2.v"),
                     strategy_docs=STRATEGY, philos_docs=PHILOS,
                     extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=6)
    print("="*60)
    print("收敛" if res["converged"] else "未收敛（保留 .bak 与错误链）")
    for r in res["rounds"]:
        print(r)

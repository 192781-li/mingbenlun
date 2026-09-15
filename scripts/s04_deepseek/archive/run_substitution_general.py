# -*- coding: utf-8 -*-
"""Layer2 目标2：substitution_general 整体 Qed（DS 主谋闭环）。

上一目标 subst_ren_general 已完整 Qed（0 admit, coqc 绿, commit 9ef0e97）。
本目标利用 subst_var_eq_ren（subst_var m k Q = ren (subst_name m k) Q）
把 substitution_general 变成 subst_ren_general 的简洁推论：只需先补一个
insert_at 的“资源保持”小引理（纯 get/insert_at 算术，不涉及进程），
即可整体导出，删掉现有 7-case 长归纳与 PPar admit。S04 只承接。
用法：python run_substitution_general.py
"""
from _paths import THEORIES, DOCS, NOTES
from proof_loop import proof_loop

TARGET = "substitution_general"
FILE = str(THEORIES / "Layer2.v")

ERR = r"""当前 substitution_general（约2126-2374）：7 个 case 已写，但 PPar 是 `admit.`，
整段以 `Admitted.` 收尾。目标是让它整体 Qed、目标段 0 admit、coqc 全绿。"""

BRIEF = (
 "目标：让 Lemma substitution_general 整体 Qed、目标段 0 admit、coqc 全绿，"
 "并【保持它的类型签名逐字不变】（下游 substitution_lemma 依赖它）。\n"
 "主路径（首选，最简洁优美）：你上一目标刚证出的 subst_ren_general 已 Qed，配合已 Qed 的 "
 "subst_var_eq_ren : subst_var m k Q = ren (subst_name m k) Q，把 substitution_general 变成它的直接推论，"
 "从而删除现在这一整段 7-case 归纳和 PPar admit。\n"
 "输出协议：给出 substitution_general 从 `Lemma substitution_general` 声明行到列0 `Qed.` 的完整新版本；"
 "若需要资源小引理，单独用一个 ```coq 块给出、块首加注释 (* INSERT-BEFORE: substitution_general *)，"
 "并完整证明、不使用材料A中不存在的名字。"
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
======== 已就位、可直接用的引理（名字/行号以材料A全文为准）========
- subst_ren_general（本文件，刚 Qed）精确签名：
    forall (D:ctx)(Q:proc), typed D Q -> forall (m k:nat)(G:ctx),
      (forall n T', get D n = Some (Some T') ->
                  get G (subst_name m k n) = Some (Some T')) ->
      no_use_at_subst Q m k = true -> typed G (ren (subst_name m k) Q).
- subst_var_eq_ren（约160，已 Qed）：forall m k P,
    subst_var m k P = ren (subst_name m k) P.
- insert_at 算术三件套（已 Qed，名字以全文为准）：
    get_insert_at_self（约553）: get (insert_at k T Gamma) k = Some (Some T)
    get_insert_at_lt  （约666）: n<k -> get (insert_at k T Gamma) n = get Gamma n
    get_insert_at_gt  （约702）: n>k -> get (insert_at k T Gamma) n = get Gamma (n-1)
    subst_name_lt : n<k -> subst_name m k n = n ；subst_name_gt : n>k -> subst_name m k n = n-1
    subst_name_eq : subst_name m k k = m。

======== 主路径：先补资源小引理，再整体导出 ========
第1步，证一个纯算术资源引理（不归纳进程，只对 n 相对 k 三分），形状：
    Lemma insert_pts_subst（名字你定）: forall Gamma T k m,
      k <= length Gamma -> get Gamma m = Some (Some T) ->
      forall n T', get (insert_at k T Gamma) n = Some (Some T') ->
                   get Gamma (subst_name m k n) = Some (Some T').
  证明按 n 与 k 分三支：
    n=k：用 get_insert_at_self 知 T'=T，且 subst_name m k k=m，结论即前提 get Gamma m=Some(Some T)；
    n<k：get_insert_at_lt 得 get Gamma n，subst_name_lt 得 rho n=n，重合；
    n>k：get_insert_at_gt 得 get Gamma (n-1)，subst_name_gt 得 rho n=n-1，重合。
  （Rocq9.1：对 nat 的比较优先 Nat.ltb_spec / Nat.compare 三分；需要 length 处先 unfold length;cbn 再 lia。）

第2步，把 substitution_general 重写为推论（保持原签名与参数顺序）：
  intros Gamma T k m Q Hkle Ht Hget Hnu.
  rewrite (subst_var_eq_ren m k Q).
  eapply subst_ren_general with (D := insert_at k T Gamma) (G := Gamma).
  - exact Ht.
  - exact (insert_pts_subst Gamma T k m Hkle Hget).   (* 资源前提，类型对齐 *)
  - exact Hnu.
  具体 with/实参顺序以 subst_ren_general 签名为准，必要时用 apply 而非 eapply、显式给全。

======== 退路（仅当主路径确实受阻才用）========
若整体导出遇到无法快速解决的障碍，则保留现有 7 个 case，只把 PPar 的 admit 补成完整证明：
仿 subst_ren_general 的 PPar（typed_strengthen_collisions 收摄碰撞位 + split_proj 重划 +
rho_inj_except_m 显式 5 前提），最后让整段以 Qed. 收尾。但优先用主路径（更短、消除重复）。

======== 冻结约束 ========
1. substitution_general 的【类型签名一字不改】，下游 substitution_lemma（约2376）及之后所有内容不动。
2. subst_ren_general 一字不改（已 Qed）。
3. congruence_preserves_typing 的 Admitted 是下一目标，本轮【不要动】。
4. 不使用材料A中不存在的引理名；Bool 引理带 Bool. 前缀；经典逻辑无 funext。
5. 目标只是 substitution_general 这一段 Qed，不要顺手重排别的定理。

[当前状态]
""" + ERR

if __name__ == "__main__":
    print("strategy_docs:", STRATEGY)
    print("philos_docs:", PHILOS)
    res = proof_loop(BRIEF, FILE, TARGET,
                     layer_files=("Layer1.v", "Layer2.v"),
                     strategy_docs=STRATEGY, philos_docs=PHILOS,
                     extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=5)
    print("="*60)
    print("收敛" if res["converged"] else "未收敛（保留 .bak 与错误链）")
    for r in res["rounds"]:
        print(r)

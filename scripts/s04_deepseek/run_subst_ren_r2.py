# -*- coding: utf-8 -*-
"""Layer2 目标1 第二轮聚焦闭环：subst_ren_general（DS 主谋）。

第一轮闭环(run_subst_ren.py)跑满6轮未收敛，错误链显示 DS 已突破 PPar 深层，
却在两处【确定的 tactic 级问题】上打地鼠。本脚本把六轮错误链 + 两处精确根因
+ Layer1.ren_typed 成功模板 + 冻结约束，以确定的好形式全量交给 DS，一次修对。
S04 只做承接：不替 DS 写证明，只做 coqc 执行、根因定位、上下文组织。
用法：python run_subst_ren_r2.py
"""
from _paths import THEORIES, DOCS, NOTES
from proof_loop import proof_loop

TARGET = "subst_ren_general"
FILE = str(THEORIES / "Layer2.v")

# 当前（r6 落盘版）第一个真实编译错误
ERR = r"""File ".\Layer2.v", line 1428, characters 2-115:
Warning: Unused introduction pattern: pz   (无害 warning，不用管)
File ".\Layer2.v", line 1455, characters 51-52:
Error: The variable o was not found in the current environment."""

BRIEF = (
 "目标：让 Lemma subst_ren_general（Layer2.v，对进程 Q 归纳、源 D / 目标 G 双上下文版本）"
 "整体 Qed、目标段 0 admit、coqc 全绿。\n"
 "【重要】当前文件就是你前 6 轮迭代后的版本：PVar/PZero/PTau/PRes/PRep 已正确，"
 "PPar 的 strengthening/split_proj 主体也已正确，PPar 的 admit 已消。你现在只剩【两处确定的 "
 "tactic 级错误】（见末尾根因诊断），本轮是精准修复，不是推倒重写——不要重写你已写对的部分。\n"
 "输出协议：给出 subst_ren_general 从 `Lemma subst_ren_general` 声明行到列0 `Qed.` 的【完整新版本】"
 "（不是片段、不是省略号）；不得使用材料A中不存在的名字；本轮不要新增辅助引理（现有引理已足够）。"
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
================ 六轮错误链（你在两处根因上打地鼠，本轮一次都修掉）================
r1 line1548 variable P0 not found（已自行修复，勿再犯）
r2 line1588 / r3 line1589  `eapply rho_inj_except_m; eassumption` -> No applicable tactic
r4 line1444 `subst o` -> No such hypothesis: o
r5 line1454 / r6 line1455  `(o := o)` -> The variable o was not found
coqc 遇到第一个错误就停：r4 之后错误前移到 POut，并不代表 r2/r3 的 rho_inj 已修好——
当前文件里那处 eapply 仍在，POut 修完它还会再爆，所以【两处本轮必须同时修】。

================ 根因1：POut/PIn 的“无参数 subst.”吃掉了 bool 标志位及其等式假设 ================
构造子精确签名（Layer1.v）：
  ty_out : forall Gamma x y P i o T Gamma1 Gamma2,
     use Gamma x (TChan i o T) Gamma1 -> (o = true) ->
     use Gamma1 y T Gamma2 -> typed Gamma2 P -> typed Gamma (POut x y P).
  ty_in  : forall Gamma x P i o T Gamma1,
     use Gamma x (TChan i o T) Gamma1 -> (i = true) ->
     typed (Some T :: Gamma1) P -> typed Gamma (PIn x P).
即 ty_out 第2个前提是 (o=true)（你 inversion 绑成 Ho），ty_in 第2前提是 (i=true)（绑成 Hi）。

本引理是对【进程 Q 归纳】后再 `inversion HTD as [... i o T ... Ho ...]. subst.`。
这个【无参数 subst.】看到 Ho : o = true，就把 o 全局替换成 true、并删掉 Ho；
PIn 的 Hi : i = true 同理，把 i 吃掉、删 Hi。
于是 subst. 之后：
  - POut：o 与 Ho 都不存在了（i 仍在，因为没有关于 i 的等式），你却写 (o:=o)、exact Ho、TChan i o T -> 必报 not found（r4/r5/r6 全死在这）。
  - PIn：i 与 Hi 都不存在了（o 仍在）。

对照成功模板 Layer1.ren_typed：POut 在 Layer1.v 268-285、PIn 在 324-355。
它是对【typed 推导 H 做 induction】，构造子字段直接成为活假设、不产生等式、不做 subst，
所以 i/o/Ho/Hi 全在，能写 (i:=i)(o:=o)、第2前提 exact Ho/Hi。两条路径唯一差异就在这个 subst。

【采用方案甲，全引理一致，不要混用方案乙】
方案甲=inversion 后【删掉无参数 subst.】，改为只 subst 结构项、显式列举、绝不碰 i/o/Ho/Hi：
  POut：inversion HTD as [?|?|?|Gamma x0 y0 P0 i o T Gamma1 Gamma2 Huse1 Ho Huse2 H|...].
        接着 subst Gamma x0 y0 P0 Gamma1 Gamma2.（i o T Ho Huse1 Huse2 H 全部保留）
        之后照 ren_typed：eapply ty_out with (...(i:=i)(o:=o)(T:=T)...)，
        第1前提 use、第2前提 exact Ho、第3前提 use、第4前提 IHP；TChan i o T 原样合法。
  PIn ：inversion HTD as [...|Gamma x0 P0 i o T Gamma1 Huse Hi H|...].
        subst Gamma x0 P0 Gamma1.（i o T Hi 保留），(i:=i)(o:=o)，第2前提 exact Hi。
注意：原代码里单独一行的 `subst Gamma1 Gamma2.`/`subst Gamma1.` 可以并进上面的显式 subst，不要重复 subst 已不存在的名字。

================ 根因2：PPar 里 rho_inj_except_m 不能 eapply...;eassumption ================
精确签名（Layer2.v 1119-1122）：
  rho_inj_except_m : forall m k x y,
     x <> k -> y <> k ->
     subst_name m k x <> m -> subst_name m k y <> m ->
     subst_name m k x = subst_name m k y -> x = y.
五个前提按序：x<>k, y<>k, rho x<>m, rho y<>m, rho x=rho y  =>  x=y。
你 PPar 反证中目标是 m0 = n，手上假设齐全：
  Hm0_nk : m0<>k ; Hn_nk : n<>k ;
  Hm0_not_rhom : subst_name m k m0 <> m ; Hn_not_rhom : subst_name m k n <> m ;
  Em0 : subst_name m k m0 = subst_name m k n
  （Em0 来自 destruct img1：img1 G1 xi z := exists m0, has G1 m0 /\ xi m0 = z，这里 z = subst_name m k n，xi 实参就是 subst_name m k，故 Em0 正是第5前提）。
`eapply rho_inj_except_m` 会先留下 ?x ?y evar，而 eassumption【不会】为匹配假设去反向实例化这些 evar，
所以报 No applicable tactic（r2/r3）。【确定写法】显式给全部参数、不用 eassumption：
  exact (rho_inj_except_m m k m0 n Hm0_nk Hn_nk Hm0_not_rhom Hn_not_rhom Em0).
前提顺序必须严格等于签名；若 Em0 类型里函数以 xi/带括号形式显示，先用 change 或 subst 化到
subst_name m k m0 = subst_name m k n 再 exact。

================ 冻结约束（违反即错）================
1. PVar/PZero/PTau/PRes/PRep 五个 case 已正确，一个字符都不要改。
2. PPar 只把 rho_inj 那一处 `eapply ...; eassumption` 换成上面的显式 exact；
   typed_strengthen_collisions / split_proj / proj1/proj2 / strengthened_* 整体结构保持不动。
3. 不要改 substitution_general、congruence_preserves_typing（那是后续目标，各自带 admit，与本轮无关）。
4. 勘误：S00 文档“m>=k 时 rho 单射”为假，碰撞统一 collision_other/rho_inj_except_m；不要退回对 typed 归纳。
5. line1428 unused pz 是无害 warning，不必消除，别为它改结构。

[当前 coqc 真实输出]
""" + ERR

if __name__ == "__main__":
    print("strategy_docs:", STRATEGY)
    print("philos_docs:", PHILOS)
    res = proof_loop(BRIEF, FILE, TARGET,
                     layer_files=("Layer1.v", "Layer2.v"),
                     strategy_docs=STRATEGY, philos_docs=PHILOS,
                     extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=4)
    print("="*60)
    print("收敛" if res["converged"] else "未收敛（保留 .bak 与错误链）")
    for r in res["rounds"]:
        print(r)

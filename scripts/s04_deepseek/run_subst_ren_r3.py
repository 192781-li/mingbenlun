# -*- coding: utf-8 -*-
"""Layer2 目标1 第三轮聚焦闭环：subst_ren_general（DS 主谋）。

第二轮 4 轮后错误收敛到单点 line1446 `Cannot find any non-recursive equality
over Gamma1`：DS 采用方案甲（显式 subst 列表以保留 bool 标志位 i/o/Ho/Hi），
方向完全正确，但 subst 列表里误混入了 ty_out/ty_in 的【普通参数】Gamma1/Gamma2
——它们不是归纳类型索引，inversion 不产生关于它们的等式，显式 subst 一个无等式
名字才会报这个错。本轮把这最后一步钉死，并保留 rho_inj 显式写法。S04 只承接。
用法：python run_subst_ren_r3.py
"""
from _paths import THEORIES, DOCS, NOTES
from proof_loop import proof_loop

TARGET = "subst_ren_general"
FILE = str(THEORIES / "Layer2.v")

ERR = r"""File ".\Layer2.v", line 1428, characters 2-115:
Warning: Unused introduction pattern: pz   (无害)
File ".\Layer2.v", line 1446, characters 4-38:
Error: Cannot find any non-recursive equality over Gamma1.
（PIn 分支 1511 `subst Gamma x0 P0 Gamma1.` 同病，只是 POut 先报错没走到）"""

BRIEF = (
 "目标：让 Lemma subst_ren_general 整体 Qed、目标段 0 admit、coqc 全绿。\n"
 "当前文件是你前两轮迭代后的版本，离通过只差【一个 subst 列表错误】+【一处 eapply 改 exact】，"
 "本轮是毫米级精准修复，严禁推倒重写、严禁改动已正确的 case。\n"
 "输出协议：给出 subst_ren_general 从 `Lemma subst_ren_general` 声明行到列0 `Qed.` 的完整新版本，"
 "不省略、不新增辅助引理、不使用材料A中不存在的名字。"
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
======== 你上一版方向对了，只剩这一个 subst 错误（line1446 / 1511）========
你现在写的是：
  POut: inversion ... as [...|Gamma x0 y0 P0 i o T Gamma1 Gamma2 Huse1 Ho Huse2 H|...].
        subst Gamma x0 y0 P0 Gamma1 Gamma2.      (* 报错在 Gamma1 *)
  PIn : inversion ... as [...|Gamma x0 P0 i o T Gamma1 Huse Hi H|...].
        subst Gamma x0 P0 Gamma1.                (* 同样会在 Gamma1 报错 *)

【Coq 行为关键事实，必须记住】
- 无参数 `subst.` 会解掉环境里所有等式，对“没有等式的名字”静默跳过；
- 但【显式】`subst 名字` 要求环境中必须存在一条关于该名字的非递归等式，否则就报
  “Cannot find any non-recursive equality over <名字>”。
- inversion HTD 只对 typed 的【索引】（结论里的源上下文、进程项）产生等式：
  Gamma=D、x0=x、y0=y、P0=P（PIn 是 Gamma=D、x0=x、P0=P）。
- 而 Gamma1/Gamma2 是 ty_out/ty_in 的【普通参数】（只出现在前提 use ... Gamma1 里，
  不是结论索引），inversion【不会】产生 Gamma1=... 的等式，所以绝不能 subst Gamma1/Gamma2。

【确定修法：只从 subst 列表删掉 Gamma1/Gamma2，其余一律不动】
  POut 改成：  subst Gamma x0 y0 P0.
  PIn  改成：  subst Gamma x0 P0.
因为你走的是“保留标志位”路线，删掉这两个名字后：
  i、o、T、Ho、Hi、Huse1/Huse、Gamma1、Gamma2 全部保留为活假设，
  所以你下面这些【原样正确、一个字都别改】：
    eapply ty_out with (...(i:=i)(o:=o)(T:=T)...)、第2前提 exact Ho、TChan i o T；
    eapply ty_in  with (...(i:=i)(o:=o)(T:=T)...)、第2前提 exact Hi、TChan i o T。
  （Gamma1/Gamma2 不需要被 subst：你已在 eapply ... with (Gamma1:=...) (Gamma2:=...)
    里显式给出目标值；use 假设展开后的 get 分量只依赖已 subst 成 D 的源，不依赖 Gamma1。）
不要再退回无参数 `subst.`（它会把 Ho:o=true / Hi:i=true 一起解掉，导致 o/i not found，那是更早的坑）；
也不要用方案乙（改成 true 字面量/reflexivity），就用上面这两行最小修法。

======== 根因2：PPar 的 rho_inj_except_m 必须显式 exact（过了1446就会走到）========
签名（Layer2 1119）：
  rho_inj_except_m : forall m k x y,
    x<>k -> y<>k -> subst_name m k x<>m -> subst_name m k y<>m ->
    subst_name m k x = subst_name m k y -> x = y.
把 `eapply rho_inj_except_m; eassumption`（报 No applicable tactic，因 eapply 留下 ?x ?y
evar，eassumption 不会反向实例化 evar）改成显式给全 5 个前提：
  exact (rho_inj_except_m m k m0 n Hm0_nk Hn_nk Hm0_not_rhom Hn_not_rhom Em0).
前提顺序严格等于签名；Em0 来自 destruct img1，正是 rho m0 = rho n。

======== 若过了 subst 后 PPar 报 “No product even after head-reduction” ========
这是 IHP/IHQ 应用时把非函数项当函数（实参个数/顺序错）。IHP 的类型是
  forall D, typed D P -> forall m k G,
    (forall n T', get D n=Some(Some T') -> get G (subst_name m k n)=Some(Some T')) ->
    no_use_at_subst P m k = true -> typed G (ren (subst_name m k) P).
PPar 两侧应形如：apply (IHP D1' HP' m k G1' <资源intros闭包> HnuP)，共 7 个实参
（D1'、HP'、m、k、G1'、资源前提、nouse）；IHQ 同构。逐个对齐，别多给别少给。

======== 冻结约束 ========
PVar/PZero/PTau/PRes/PRep 一字不改；PPar 只改 rho_inj 那一处（必要时对齐 IHP/IHQ 实参）；
不要改 substitution_general / congruence_preserves_typing；
“m>=k 时 rho 单射”为假，不要用；line1428 unused pz 是无害 warning，不必消。

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

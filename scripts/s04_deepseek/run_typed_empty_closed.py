# -*- coding: utf-8 -*-
"""聚焦闭环：typed_empty_closed（空上下文弱化，替代假命题 typed_head_insert）。
用法：python run_typed_empty_closed.py
"""
from _paths import THEORIES, NOTES
from proof_loop import proof_loop

TARGET = "typed_empty_closed"
FILE = str(THEORIES / "Layer2.v")
PHILOS = tuple(p for p in
  (r"哲学研究\S01给S04的证明智慧手册_生命论方法论如何写Coq证明_20260902.md",) if (NOTES/p).exists())

BRIEF = (
 "只证明 Lemma typed_empty_closed（替换其 Admitted 占位）：forall G P, typed [] P -> typed G P。"
 "需要的小引理先自证到 Qed，再给主引理完整 Qed 版本，一个回答内一次交齐；不要其他引理、不要 admit/Abort。"
)

EXTRA = r"""
======== 命题含义（明性：这是真命题，而 typed G P -> typed (Some T::G) P 是假命题，别搞反方向）========
空上下文可类型化的进程不依赖任何具体位置资源，故可弱化到任意上下文 G。

======== 证明路线（已分析，照此落成可编译代码）========
关键：归纳前先 generalize 目标上下文，因为 ty_par/ty_res 会改变目标上下文：
  intros G P H; revert G; induction H; intros G.
逐构造子（以材料A typed 的构造子为准）：
- ty_zero：ty_zero 直接给出 typed G PZero。
- ty_var：前提 get [] x = Some(Some T)，但 get 对空表恒为 None，discriminate 消去。
- ty_tau：用归纳假设后 ty_tau。
- ty_out/ty_in：前提含 use [] x ..，即 get [] x = Some ..，空表为 None，矛盾消去。
- ty_par：两个归纳假设分别把 typed [] P、typed [] Q 弱化到 typed G P、typed G Q；
  再用 ty_par 取 Gamma1:=G, Gamma2:=[]，需要 split G G []——用已证的 split_refl_nil（若名字不同在材料A检索 split G G [] 的现成引理）。
- ty_res：归纳假设把 typed (Some T::[]) P 弱化为 typed (Some T::G) P，再 ty_res。
- ty_rep：前提本就是 typed [] P，ty_rep 直接对任意 G 成立。
option 双层、use 的定义以材料A为准；归纳假设里目标上下文被 revert 后是函数形态，注意 intros 的名字。

======== 纪律 ========
- 先补必需小引理（Qed），再给 typed_empty_closed 完整 Qed，一次交齐；
- 交付前逐行核对引用名都在材料A或本块有着落；库引理打 (* @stdlib names: .. *)；结尾 Qed.。
"""

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v","Layer2.v"),
                     philos_docs=PHILOS, extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=3)
    print("="*60); print("收敛" if res["converged"] else "未收敛")
    for r in res["rounds"]: print(r)

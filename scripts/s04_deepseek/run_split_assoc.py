# -*- coding: utf-8 -*-
"""聚焦闭环：只证 split_assoc 一个引理（替换其 Admitted 占位）。
已用逐位置语义分析出唯一正确的低复杂度路线，交给 DS 落成可编译代码。
用法：python run_split_assoc.py
"""
from _paths import THEORIES, DOCS, NOTES
from proof_loop import proof_loop

TARGET = "split_assoc"
FILE = str(THEORIES / "Layer2.v")
STRATEGY = tuple(p for p in
  (r"分站\S04_Layer2最后3Admitted_精确证明策略_S00分析_20260903.md",) if (DOCS/p).exists())
PHILOS = tuple(p for p in
  (r"哲学研究\S01给S04的证明智慧手册_生命论方法论如何写Coq证明_20260902.md",) if (NOTES/p).exists())

BRIEF = (
 "只证明 Lemma split_assoc 这一个引理，给出它从 Lemma 行到列0 Qed. 的完整新版本以替换占位。"
 "不要输出任何其他引理、不要长段解释、不要 admit/Admitted/Abort。本轮唯一目标就是让 split_assoc 编译通过。"
)

EXTRA = r"""
======== split 的精确定义（Layer1，逐位置、位置之间相互独立）========
Definition split Gamma Gamma1 Gamma2 := forall n,
  (get Gamma1 n = get Gamma n /\ (get Gamma2 n = None \/ get Gamma2 n = Some None))
  \/ (get Gamma2 n = get Gamma n /\ (get Gamma1 n = None \/ get Gamma1 n = Some None)).
即每个位置 n：资源要么归 Gamma1（此时 Gamma2 在 n 为空 None/Some None），要么归 Gamma2（Gamma1 空）。
现成模板 split_sym 的证法就是：unfold split; intro n; specialize (Hs n); destruct Hs，逐位置处理，【不对列表归纳】。

======== 本题的逐位置语义分析（已替你分析完，照此构造，不要走 excluded_middle/列表归纳的老路）========
前提 Hs1: split G G12 G3，Hs2: split G12 G1 G2。固定任意位置 n，specialize (Hs1 n),(Hs2 n)，
二者各左右两支，组合只有三种【有效】情形（第四种自相矛盾，用 discriminate/injection 消去）：
- 情形A 资源在 G3：Hs1 n 走右支（G12 n 空、G3 n=G n）；G12 n 空时由 Hs2 n 得 G1 n 空且 G2 n 空。
- 情形B1 资源在 G1：Hs1 n 左支（G12 n=G n、G3 n 空）且 Hs2 n 左支（G1 n=G12 n=G n、G2 n 空）。
- 情形B2 资源在 G2：Hs1 n 左支（G12 n=G n、G3 n 空）且 Hs2 n 右支（G2 n=G12 n=G n、G1 n 空）。
要找的 G23 在 n 位取值：A->G3 n(=G n)；B1->空；B2->G2 n(=G n)。即 G23 是 G2 与 G3 的逐位置并（二者由两个 split 保证同位互斥）。

======== G23 的显式构造（用现成 setby/get_setby_get，不要用 excluded_middle_informative）========
setby f Gamma k 沿列表逐位作用，get_setby_get : get Gamma n=Some u -> get (setby f Gamma k) n = Some (f (k+n) u)。
取
  G23 := setby (fun n t => match get G2 n with Some (Some a) => Some (Some a) | _ => get G3 n end) G 0.
（闭包捕获 G2 G3：G2 该位有资源就取 G2，否则取 G3。）
然后 exists G23; split; 两个目标都是 unfold split; intro n; specialize Hs1 n,Hs2 n;
按上面 A/B1/B2 destruct；在 G n 有值处用 get_setby_get 改写 G23 的 get，空位置（get G n=None）
两支假设本身就迫使各侧为 None，化简后用 tauto/auto/左右支+split+assumption 收。
注意 option (option ty) 是双层：None / Some None / Some (Some T)，destruct 时分层别漏；
injection 对双层 option 一次剥到底（不要连续两次 injection）。

======== 先练功：把这几个 setby/get 小引理一次性练齐（材料里只有 get_setby_get，其余你要先自证）========
- 已有可直接用：get_setby_get : get Gamma n = Some u -> get (setby f Gamma k) n = Some (f (k+n) u)。
- 【材料里没有、上一版你误当成已有（这是幻觉）】get_setby_None，必须先自己证：
    Lemma get_setby_None : forall Gamma f k n, get Gamma n = None -> get (setby f Gamma k) n = None.
  证法：对 Gamma 归纳；get Gamma n=None 即 n 越界（n>=length Gamma），setby 保持长度与结构，越界位仍为 None；
  destruct n/列表后 simpl，用归纳假设或 reflexivity。k+n 处先 lia 或 rewrite Nat.add_0_r。
- 若还需要“某位置 G2/G3 为空”的等式小引理，也一并先证到 Qed，不要在主证明里抛没着落的名字。

======== 纪律 ========
- 先给上述小引理的完整 Qed 块（INSERT-BEFORE: split_assoc），再给 split_assoc 主引理完整 Qed 块，一个回答内一次交齐；
- 只输出这些 coq 块；不许 induction G 来证 split_assoc 本体（位置独立，按 n 逐点 destruct），但 get_setby_None 这类列表引理可以对列表归纳；不许 excluded_middle；
- 用到的库引理若材料中确无，打 (* @stdlib names: .. *)，否则必须自证；
- 交付前自己逐行核对每个引用名都有着落，结尾必须 Qed.，整块可直接 coqc 通过。
"""

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v","Layer2.v"),
                     strategy_docs=STRATEGY, philos_docs=PHILOS, extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=3)
    print("="*60); print("收敛" if res["converged"] else "未收敛")
    for r in res["rounds"]: print(r)

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
 "证明 Lemma split_assoc（替换其 Admitted 占位），并先自证它需要的辅助引理 get_setby_None。"
 "严格按分块协议输出：①每个辅助引理【单独一个】```coq 代码块，且该块第一行写注释 (* INSERT-BEFORE: split_assoc *)；"
 "②split_assoc 主引理【单独一个】```coq 代码块，从 `Lemma split_assoc` 到列0 `Qed.`；"
 "③绝不要把两个 Lemma 放进同一个 coq 块。不要 admit/Admitted/Abort，不要长解释。"
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

======== option 层级铁事实（上一版就在这里错，line2172：option 构造子出现在需要 ty 处，务必刻死）========
- ctx := list (option ty)。所以【列表元素】g 的类型是 option ty，只有两层构造：None | Some (T:ty)。
  match 列表元素 g 只能写：match g with Some T => .. | None => .. end；destruct g as [T|]。
  绝不能写 Some (Some _)，也不能 destruct g as [[T|]|]——那是把 g 错当成 option(option ty)。
- 只有 get 的【返回值】才是 option(option ty)：None（越界）| Some None（在位但空）| Some (Some T)（资源）。
  对 get G n 的结果 destruct 才用 [[T|]|]。把“列表元素”和“get 返回值”这两个类型严格分开。

======== 唯一指定路线，禁止另起炉灶（上一版走过的弯路，不要再犯）========
- 用上面 setby + get_setby_get/get_setby_None 的逐位置路线。
- 【禁止】再定义 merge_ctx 或任何“递归合并两个 ctx 的 Fixpoint”——上一版这么做且在 match 列表元素时多套一层 option 导致类型错，已废弃。
- split_assoc 本体【不对列表归纳、不用 excluded_middle】；只有 get_setby_None 这类列表小引理对列表归纳。

======== 先练功：把 setby/get 小引理一次性练齐（材料里只有 get_setby_get，其余先自证）========
- 已有可直接用：get_setby_get : get Gamma n = Some u -> get (setby f Gamma k) n = Some (f (k+n) u)。
- 【材料里没有、上一版你误当成已有（幻觉）】get_setby_None，必须先自己证（单独 INSERT-BEFORE 块）：
    Lemma get_setby_None : forall Gamma f k n, get Gamma n = None -> get (setby f Gamma k) n = None.
  证法：对 Gamma 归纳；get Gamma n=None 即 n 越界（n>=length Gamma），setby 保持长度与结构，越界位仍 None；
  destruct n/列表后 simpl，用归纳假设或 reflexivity；k+n 处 rewrite Nat.add_0_r / lia。
- 若还需要“某位置 G2/G3 为空”的等式小引理，也一并先证到 Qed（各自独立 INSERT-BEFORE 块），不要在主证明里抛没着落的名字。

======== 输出纪律（与执行方解析器严格对齐，错格式等于没交）========
- 每个辅助引理单独一个 ```coq 块，块内第一行写 (* INSERT-BEFORE: split_assoc *)，其后是 Lemma..Proof..Qed.；
- split_assoc 主引理单独一个 ```coq 块（不要 INSERT 标记，直接 Lemma split_assoc..Qed.），会整体替换占位；
- 一个 coq 块只放一个 Lemma；不许 induction G 证本体；不许 excluded_middle；
- 库引理若材料确无打 (* @stdlib names: .. *)，否则必须自证；
- 交付前自己当 coqc 逐行核对：每个引用名有着落、option 层级正确、每块以 Qed. 结尾、可直接编译 0 错误。

======== 当前状态（重要，别推倒重来）========
材料A里已有你上一版的 split_assoc 完整证明与三个辅助引理（get_setby_None_uncond/get_repeat_None_lt/length_repeat_None），
逐点结构是对的，只剩编译错误（如 repeat None len 里 None 推断不出类型——元素是 option ty，应写 repeat (None:option ty) len；
类似隐式参数推断不出的地方都显式标类型）。请基于材料末尾的 coqc 错误做【最小修正】，保留已正确的证明结构，
给出修正后的完整 Lemma 块（辅助引理用 INSERT-BEFORE 块、split_assoc 用独立主块）；不要改路线、不要删正确引理。
"""

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v","Layer2.v"),
                     strategy_docs=STRATEGY, philos_docs=PHILOS, extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=4)
    print("="*60); print("收敛" if res["converged"] else "未收敛")
    for r in res["rounds"]: print(r)

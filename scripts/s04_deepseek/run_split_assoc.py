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

======== 当前状态（重要，从零写主证明，别再走老路）========
4 个辅助引理 get_setby_None_uncond / get_repeat_None_lt / length_repeat_None / get_setby_None 已全部 Qed 且编译通过，
【直接用、不要重发、不要再新造任何辅助引理】（你上轮抽的 get_setby_merge_spec 把 get 层 match 和 Some(元素) 混层，已删除，禁止再抽这类引理）。
材料A里 split_assoc 已有你上一版(r4)的完整证明（三态穷尽思路正确、f 是正确的无类型标注 pose、bullet 层级已闭合、4个辅助引理已 Qed），
现在 coqc 的【唯一】错误是：line 2224 `Found no subterm matching "get G n" in the current goal.`
该行代码是：`-- rewrite H1. rewrite H12. rewrite EG. reflexivity.`
根因（执行方观察，供你参考，最终以你判断为准）：这是 Hs1 left / Hs2 left 分支（资源在 G1），目标经 left.split 后第一支是某侧等式；
你先 rewrite H1 再 rewrite H12，这两步把目标里的 get G n 提前替换掉了，导致第三步 rewrite EG（EG: get G n = Some(Some T)）找不到子项。
请检查这一支（以及后续所有类似分支）的 rewrite 顺序与方向：要么先 rewrite EG 把 get G n 化成 Some(Some T)，要么用 symmetry 调整等式方向，要么改用 exact/rewrite <-。
你这一轮：以材料A里现有 r4 证明为基础，重交【一个】完整 Lemma split_assoc..Qed. 块，只修 2224 这一处及连带的同类 rewrite 顺序问题；
不要重写已正确的 f 定义、三态穷尽骨架、bullet 结构，也不要重发/新造辅助引理。

setby/get 精确事实（Layer1）：
  Fixpoint setby (f:nat->option ty->option ty) Gamma k := match Gamma with []=>[] | t::G'=>f k t::setby f G'(S k) end.
  Lemma get_setby_get : get Gamma n = Some u -> get (setby f Gamma k) n = Some (f (k+n) u).  (* u:option ty 元素层；右侧 Some(元素层值) *)
f 必须返回【元素层 option ty】，且因为是新建局部定义，用 pose。【pose 类型标注语法已用 coqc 验证，严格照这个写法】：
  pose (f := fun (n:nat) (_:option ty) =>
               match get G2 n with Some (Some a) => Some a
               | _ => match get G3 n with Some v => v | None => None end end).
  exists (setby f G 0).
严禁 set(f:T:=..)（set 不接受名字:类型:=）；也严禁 pose (f : T := ..)（pose 同样不接受名字后类型）；
也不要写 fun...end : T 这种“后置返回标注”，它会被 Coq 误绑到内层 match 导致分支被要求成函数类型。
返回类型让 Coq 从分支自动推断（三个分支都是 option ty，自会推出 nat->option ty->option ty），只需给形参 (n:nat)(_:option ty) 标注。

【你前几轮唯一卡住点：f 的 match 在证明里没归约掉（2230/2226 Unable to unify Some None with Some (match...)）。标准手法，严格照做】
要证逐位置等式时，get G23 n 经 get_setby_get 变成 Some (f n u)，两边都是 Some(元素层值)，只需证括号内元素层相等。
绝不能让一个【尚未 destruct 完】的 match 去硬 reflexivity。正确顺序：
  1) unfold f（或 cbn delta [f]）让 f 的 match 显形；
  2) 对 get G2 n 做 destruct as [[a|]|]（get 层三态：Some(Some a)资源 / Some None 在位空 / None 越界）；
  3) 必要时对 get G3 n 同样 destruct as [[b|]|]；
  4) 用 specialize 后的 Hs1/Hs2（它们描述同一 n 位 G/G12/G3 与 G12/G1/G2 的分配）配合 discriminate/injection 消去与线性 split 矛盾的组合；
  5) 每个幸存分支里 f 的 match 已落到确定构造子（Some a / v / None），此时 cbn 后 reflexivity（或 rewrite 对应假设再 reflexivity）。
一句话：先把两个 get 都三态拆开、用 split 假设砍掉矛盾支，match 自然坍缩成构造子，再 reflexivity；不要对着含 match 的目标直接 reflexivity/eauto。

硬性自检：
1) bullet 层级（- + * ++ **）前后一致、每层闭合，交前按缩进走一遍每个分支都收尾（不许 Current bullet not finished）。
2) 逐个 Some/None 标注元素层还是 get 层（系统铁律第8条）；f 每个分支返回元素层 option ty。
3) 只交 split_assoc 一个块、从 Lemma 到 Qed.；不重发辅助、不新造辅助；不用裸 congruence tactic（与 Inductive congruence 同名，需要闭合用 reflexivity/f_equal/lia）。"""

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v","Layer2.v"),
                     strategy_docs=STRATEGY, philos_docs=PHILOS, extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=5)
    print("="*60); print("收敛" if res["converged"] else "未收敛")
    for r in res["rounds"]: print(r)

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

======== 当前状态（2026-09-04 根本原因发现，必须从零写完整9分支证明）========
4 个辅助引理 get_setby_None_uncond / get_repeat_None_lt / length_repeat_None / get_setby_None 已全部 Qed 且编译通过，
【直接用、不要重发、不要再新造任何辅助引理】。
当前 split_assoc 在 Layer2.v 中是 Admitted 占位（之前的r3证明因结构性缺陷已被回退）。

【根本原因——你之前的r3证明只处理了4/9个分支，这是致命的结构性缺陷】
在主证明中你写了：
  destruct (get G2 n) as [[a|]|] eqn:EG2;   (* 3种情况：Some(Some a)/Some None/None *)
  destruct (get G3 n) as [[b|]|] eqn:EG3.   (* 3种情况 *)
这创建【9个分支】（3×3），但你每个目标只写了【4个】* 分支，省略了5个：
  - G2=Some None 的全部3个分支（G3=Some(Some b)/Some None/None）
  - G2=Some(Some a), G3=Some None 的1个分支
  - G2=None, G3=Some None 的1个分支
后果：bullet结构混乱，后续分支中Hs1/Hs1l变量不存在（"Hs1l not found"），所有机械修正都无法解决——因为缺的是整个分支，不是某个tactic错误。

【本轮要求：必须处理全部9个分支，一个都不能少】
9个分支的证明策略：
  1. G2=Some(Some a), G3=Some(Some b)：矛盾（G2和G3都有资源，split要求其中一个为空），exfalso+discriminate/injection
  2. G2=Some(Some a), G3=Some None：valid或矛盾，取决于Hs1/Hs2组合；G3在位空(Some None)等价于空，资源在G2
  3. G2=Some(Some a), G3=None：valid，资源在G1（split G G1 G23右支）
  4. G2=Some None, G3=Some(Some b)：valid，G2在位空等价于空，资源在G3
  5. G2=Some None, G3=Some None：矛盾或valid，取决于具体位置；两个都在位空
  6. G2=Some None, G3=None：valid或矛盾，G2在位空等价于空
  7. G2=None, G3=Some(Some b)：valid，资源在G3（split G G1 G23左支）
  8. G2=None, G3=Some None：valid或矛盾，G3在位空等价于空
  9. G2=None, G3=None：不可能（n<max_len意味着G2或G3至少一个有资源），exfalso+lia
注意：Some None（在位空）和None（越界）在split的空判断中是等价的（split定义里写的是"= None \/ = Some None"），所以涉及Some None的分支可以用split假设直接处理。

【已验证的机械修正经验（供你写证明时参考，避免重蹈覆辙）】
- destruct (get G3 n) as [[b|]|] 会把上下文中所有 get G3 n 替换为构造子，所以后续假设中 get G3 n 已不存在，直接用 discriminate/inversion 处理构造子等式，不要 rewrite EG3 in G3n（会报"Found no subterm"）
- G3s/G2s/G12s 分支（= Some None）需要 inversion 而非 discriminate（Some(Some x)=Some None 需先 injection 再 discriminate）
- Hs1r/Hs2r 分支【不能忽略】左合取支 get G2 n = get G12 n，必须保留为 HG2G12 用于连接 EG2 和 G12n
- 目标中 get G2 n 已被 destruct 替换为 Some(Some a)，rewrite 方向要注意（用 <- 从右往左）
- simpl 会改变 Hs1 类型导致 destruct as 模式不匹配，G2=None 分支应避免 simpl
- bullet 层级必须前后一致、每层闭合，交前按缩进走一遍每个分支都收尾

setby/get 精确事实（Layer1）：
  Fixpoint setby (f:nat->option ty->option ty) Gamma k := match Gamma with []=>[] | t::G'=>f k t::setby f G'(S k) end.
  Lemma get_setby_get : get Gamma n = Some u -> get (setby f Gamma k) n = Some (f (k+n) u).  (* u:option ty 元素层；右侧 Some(元素层值) *)
f 必须返回【元素层 option ty】，且因为是新建局部定义，用 pose。【pose 类型标注语法已用 coqc 验证，严格照这个写法】：
  pose (f := fun (n:nat) (_:option ty) =>
               match get G2 n with Some (Some a) => Some a
               | _ => match get G3 n with Some v => v | None => None end end).
  let max_len := Nat.max (length G2) (length G3) in
  exists (setby f (repeat (None:option ty) max_len) 0).
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


======== 2026-09-04 V4闭环3轮错误模式（必须避免重蹈覆辙）========
3轮DS输出都给出了完整无admit的证明，但编译都在证明早期（2245-2251行）失败：
- r1错误：line 2245 rewrite方向反了——写了rewrite HG12（类型get G12 n=get G n）在假设get G1 n=get G12 n上，应该用rewrite <- HG12或先symmetry。
  【铁律】rewrite前先看等式方向：H:A=B，rewrite H把A换成B，rewrite <- H把B换成A。目标/假设里是A还是B，决定用哪个方向。
- r2错误：line 2247 bullet结构混乱——Current bullet + is not finished。destruct Hs1 as [Hs1l|Hs1r]; destruct Hs2 as [Hs2l|Hs2r]创建4个分支，必须用4个--（或-）分支逐一收尾，不能跳。
  【铁律】每加一层destruct就多一层bullet，交前按缩进走一遍每个分支都有收尾tactic（exact/reflexivity/discriminate/exfalso+...）。
- r3错误：line 2251 f的match没归约——环境里f:=fun...match get G2 n with...，目标里含Some (f n u)，直接reflexivity会报Unable to unify。必须先unfold f或cbn delta [f]，再destruct get G2 n让match坍缩。
  【铁律】f是pose的局部定义，Coq不会自动unfold。涉及f的等式必须先unfold f，再destruct get G2/G3 n，match才会坍缩成构造子，然后才能reflexivity。


======== 2026-09-04 强制分解策略（8轮未收敛后的根本性调整）========
之前8轮DS都在证明早期（2244-2253行）遇f定义归约问题，根本原因是split假设和f的match
交织在一起，复杂度太高。【强制分解为两步，不许一步到位】：

第一步：先证辅助引理 H23_val（单独一个Lemma，INSERT-BEFORE: split_assoc）：
  Lemma H23_val : forall G2 G3 f max_len n,
    f = (fun (n:nat) (_:option ty) => match get G2 n with Some (Some a) => Some a | _ => match get G3 n with Some v => v | None => None end end) ->
    get (setby f (repeat (None:option ty) max_len) 0) n =
    match get G2 n with Some (Some a) => Some (Some a) | _ => get G3 n end.
  这个引理【只涉及get/setby/repeat，不涉及split假设】，证明时：
  - destruct (Nat.ltb n max_len) eqn:Elt
  - n < max_len分支：用get_repeat_None_lt得get (repeat None max_len) n = Some None，
    再用get_setby_get改写，unfold f，destruct (get G2 n) as [[a|]|]，每个分支reflexivity
  - n >= max_len分支：用get_overflow_none得get G2 n = None和get G3 n = None，
    再用get_setby_None，reflexivity
  【这个引理必须先单独Qed，编译通过后才能开始证split_assoc本体】

第二步：用H23_val证split_assoc本体：
  - pose f, set max_len, pose G23 := setby f (repeat None max_len) 0
  - exists G23
  - assert (H23v := H23_val G2 G3 f max_len) （应用已证的辅助引理）
  - split. 两个目标都是unfold split; intro n; specialize Hs1 n; specialize Hs2 n;
    rewrite (H23v n)（用辅助引理把get G23 n替换成match表达式，【此时目标里不再有f！】）
  - 然后destruct (get G n) as [[g|]|]，再destruct Hs1, Hs2，逐分支处理
  - 【关键】因为rewrite (H23v n)后目标里已经没有f了，所以不需要unfold f，
    也不会遇到f的match归约问题！这就是分解的意义。


======== 2026-09-04 v8 关键修正（H23_val引理类型错误，v7 r3的unify错误根因）========
【v7 5轮错误模式】：
- r1: H23_val输出格式问题（DS把引理写在markdown正文不在coq代码块）→ r2已修正
- r2: H23_val引理inversion错误
- r3: H23_val引理unify错误（Unable to unify "None" with "Some None"）← 【根因：H23_val类型陈述错误】
- r4: split_assoc主证明Illegal application（Hs1被当作函数应用）
- r5: split_assoc主证明rewrite目标不存在

【H23_val类型错误的详细分析】：
当前H23_val右边写的是：
  match get G2 n with Some (Some a) => Some (Some a) | _ => get G3 n end.
但这是【错误的】！

f的定义：
  f n None = match get G2 n with
    | Some (Some a) => Some a
    | _ => match get G3 n with
           | Some v => v
           | None => None   (* ← 关键：G3越界时f返回None元素层值 *)
           end
    end.

当n < max_len时，get (repeat None max_len) n = Some None，
由get_setby_get得：get (setby f (repeat None max_len) 0) n = Some (f n None).

【关键情形】get G2 n = Some None, get G3 n = None：
- f n None = None（G2在位空走_分支，G3越界走None分支，返回None）
- 左边 get(setby f...)n = Some None
- 当前右边：match Some None with Some(Some a)=>... | _=> get G3 n end = None
- 左边Some None ≠ 右边None → unify失败！

【正确的H23_val右边】（当n < max_len时）：
  match get G2 n with
  | Some (Some a) => Some (Some a)
  | _ => match get G3 n with
         | Some v => Some v       (* G3有值，Some(元素层值) *)
         | None => Some None      (* ← 关键修正：G3越界时是Some None，不是None！ *)
         end
  end.

【n >= max_len的情形】：
此时get G2 n = None且get G3 n = None（越界），get(setby f...)n = None（越界）。
所以H23_val必须【加上n < max_len的前提】，或者分别处理两种情况。

【v8 强制要求的H23_val正确类型】（推荐方案A）：
  Lemma H23_val : forall (G2 G3 : ctx) (f : nat -> option ty -> option ty) (max_len n : nat),
    n < max_len ->
    f = (fun (n:nat) (_:option ty) => match get G2 n with Some (Some a) => Some a | _ => match get G3 n with Some v => v | None => None end end) ->
    get (setby f (repeat (None:option ty) max_len) 0) n =
    match get G2 n with
    | Some (Some a) => Some (Some a)
    | _ => match get G3 n with
           | Some v => Some v
           | None => Some None
           end
    end.
  证明：destruct (get G2 n) as [[a|]|]; destruct (get G3 n) as [[b|]|]; 9个分支，每个unfold f后reflexivity（f的match和右边的match同步坍缩）。

【split_assoc主证明中使用H23_val的正确方式】：
- pose f, set max_len, exists (setby f (repeat None max_len) 0)
- split. 两个目标都是unfold split; intro n; specialize Hs1 n; specialize Hs2 n
- 【关键】分两种情况：destruct (Nat.ltb n max_len) eqn:Hlt
  - n < max_len分支：rewrite (H23_val G2 G3 f max_len n Hlt Hf_eq)，然后目标里不再有f，destruct (get G n) as [[g|]|]，再destruct Hs1, Hs2逐分支处理
  - n >= max_len分支：此时get G2 n = None且get G3 n = None（越界），由split假设可推出get G n = None且get G1 n = None，直接用get_setby_None或lia处理
- 【铁律】不许在split_assoc本体里直接unfold f或destruct f的match——f的所有复杂性都封装在H23_val里。

【v8 输出纪律】：
1. 必须先输出H23_val引理（带n < max_len前提），再输出split_assoc证明
2. H23_val引理必须以 (* INSERT-BEFORE: split_assoc *) 开头，完整Lemma+Proof+Qed
3. 两个引理分开放在不同的coq代码块中
4. 先写H23_val，在脑子里模拟coqc验证通过（9个分支都reflexivity），再写split_assoc
5. split_assoc证明中用destruct (Nat.ltb n max_len)分情况，n < max_len用H23_val，n >= max_len用越界性质
6. 硬性自检：H23_val右边最后一个分支是Some None（不是None，不是get G3 n）；split_assoc中n >= max_len分支有处理
"""

if __name__ == "__main__":
    res = proof_loop(BRIEF, FILE, TARGET, layer_files=("Layer1.v","Layer2.v"),
                     strategy_docs=STRATEGY, philos_docs=PHILOS, extra_notes=EXTRA,
                     model="deepseek-v4-pro", max_rounds=5)
    print("="*60); print("收敛" if res["converged"] else "未收敛")
    for r in res["rounds"]: print(r)

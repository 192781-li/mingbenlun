From Stdlib Require Import List PeanoNat Lia.
Import ListNotations.

Inductive ty : Set := TBase | TFun (a b:ty) | TPar (a b:ty).
Definition ctx := list (option ty).

Fixpoint get (Gamma:ctx)(n:nat): option (option ty) :=
  match Gamma with
  | [] => None
  | t::G' => match n with 0 => Some t | S n => get G' n end
  end.
Fixpoint setby (f:nat->option ty->option ty)(Gamma:ctx)(k:nat):ctx :=
  match Gamma with []=>[] | t::G'=> f k t :: setby f G' (S k) end.

Definition split (G A B:ctx):Prop := forall n,
  (get A n = get G n /\ (get B n=None \/ get B n=Some None))
\/(get B n = get G n /\ (get A n=None \/ get A n=Some None)).

Definition cell_split (g a b:option(option ty)):Prop :=
  (a=g/\(b=None\/b=Some None)) \/ (b=g/\(a=None\/a=Some None)).

Definition blank_merge (g2 g3:option(option ty)):option(option ty) :=
  match g2 with Some None=>Some None
  | _=> match g3 with Some None=>Some None | _=>None end end.

Definition merge_cell (g g1 g2 g3:option(option ty)):option(option ty) :=
  match g2 with
  | Some(Some a)=>Some(Some a)
  | _=> match g3 with
        | Some(Some b)=>Some(Some b)
        | _=> match g with
              | None=> match g1 with Some None=>None | _=>blank_merge g2 g3 end
              | _=>blank_merge g2 g3 end end end.

Lemma get_none_overflow: forall G n, get G n=None -> n>=length G.
Proof.
  intros G n; revert G; induction n; intros G H;
  destruct G as [|t G']; simpl in *.
  - lia. - discriminate. - lia.
  - apply IHn in H; lia.
Qed.
Lemma get_overflow_none: forall Gm n, n>=length Gm -> get Gm n=None.
Proof.
  intros Gm; induction Gm as [|t Gm' IH]; intros n H;
  destruct n as [|n]; simpl in *.
  - reflexivity. - reflexivity. - exfalso; lia. - apply IH; lia.
Qed.
Lemma split_get_l: forall G A B n T, split G A B -> get A n=Some(Some T)->get G n=Some(Some T).
Proof. intros G A B n T Hs H1. specialize (Hs n); destruct Hs as [[Hg _]|[_ Hd]];
 [rewrite Hg in H1;exact H1|destruct Hd as [Hd|Hd];rewrite Hd in H1;discriminate]. Qed.
Lemma split_get_r: forall G A B n T, split G A B -> get B n=Some(Some T)->get G n=Some(Some T).
Proof. intros G A B n T Hs H1. specialize (Hs n); destruct Hs as [[_ Hd]|[Hg _]];
 [destruct Hd as [Hd|Hd];rewrite Hd in H1;discriminate|rewrite Hg in H1;exact H1]. Qed.

(* merge_cell 作参数的逐位结合（32 可达组合穷举） *)
Lemma cell_assoc: forall g g12 g3 g1 g2,
  cell_split g g12 g3 -> cell_split g12 g1 g2 ->
  cell_split g g1 (merge_cell g g1 g2 g3)
  /\ cell_split (merge_cell g g1 g2 g3) g2 g3.
Proof.
  intros g g12 g3 g1 g2 H13 H12. unfold cell_split in *.
  destruct H13 as [(h12&[k3|k3])|(h3&[k12|k12])];
  destruct H12 as [(h1&[k2|k2])|(h2&[k1|k1])];
  subst; destruct g as [[T|]|]; cbn [merge_cell blank_merge]; try discriminate;
  split;
  ((left; split; [reflexivity|]; now (left; reflexivity) || now (right; reflexivity))
   || (right; split; [reflexivity|]; now (left; reflexivity) || now (right; reflexivity))).
Qed.

(* option 层判据：merge 选 Some v 或安全截断 None，两侧 cell_split 都成立 *)
Lemma cell_step: forall g g12 g3 g1 g2,
  cell_split g g12 g3 -> cell_split g12 g1 g2 ->
  match merge_cell g g1 g2 g3 with
  | Some v => cell_split g g1 (Some v) /\ cell_split (Some v) g2 g3
  | None => cell_split g g1 None /\ cell_split None g2 g3
  end.
Proof.
  intros. destruct (merge_cell g g1 g2 g3) as [v|] eqn:Em.
  - generalize (cell_assoc g g12 g3 g1 g2 H H0). rewrite Em. tauto.
  - generalize (cell_assoc g g12 g3 g1 g2 H H0). rewrite Em. tauto.
Qed.

(* merge=None 只有两类：两子皆越界，或 G 越界且 G1 在位空位（让位） *)
Lemma merge_none_case: forall g g1 g2 g3,
  merge_cell g g1 g2 g3 = None ->
  (g2=None /\ g3=None) \/ (g=None /\ g1=Some None).
Proof.
  intros; destruct g2 as [[a|]|], g3 as [[b|]|],
                  g as [[c|]|], g1 as [[d|]|];
  cbn [merge_cell blank_merge] in H; try discriminate; auto.
Qed.

(* 让位位（父越界、G1在位空位）：G2/G3 至少一侧越界，不可能都在位 *)
Lemma k_side: forall g g12 g3 g1 g2,
  g=None -> g1=Some None ->
  cell_split g g12 g3 -> cell_split g12 g1 g2 -> g2=None \/ g3=None.
Proof.
  intros; subst. unfold cell_split in *.
  destruct g2 as [[x|]|], g3 as [[y|]|];
    try (left; reflexivity); try (right; reflexivity);
    exfalso; repeat match goal with H:_/\_|-_=>destruct H | H:_\/_|-_=>destruct H end;
    subst; discriminate.
Qed.

(* 父在 n 越界，则经两层 split 的所有孙位 G1/G2/G3 都不可能有真实资源 *)
Lemma gc_blank: forall G G12 G3 G1 G2 n,
  split G G12 G3 -> split G12 G1 G2 -> get G n=None ->
  (get G1 n=None\/get G1 n=Some None) /\
  (get G2 n=None\/get G2 n=Some None) /\
  (get G3 n=None\/get G3 n=Some None).
Proof.
  intros G G12 G3 G1 G2 n H1 H2 nG.
  assert (b1: get G1 n=None\/get G1 n=Some None).
  { destruct (get G1 n) as [[x|]|] eqn:E1; auto; exfalso.
    apply split_get_l with (G:=G12)(A:=G1)(B:=G2)(n:=n)(T:=x) in H2; [|exact E1].
    apply split_get_l with (G:=G)(A:=G12)(B:=G3)(n:=n)(T:=x) in H1; [|exact H2]. congruence. }
  assert (b2: get G2 n=None\/get G2 n=Some None).
  { destruct (get G2 n) as [[x|]|] eqn:E2; auto; exfalso.
    apply split_get_r with (G:=G12)(A:=G1)(B:=G2)(n:=n)(T:=x) in H2; [|exact E2].
    apply split_get_l with (G:=G)(A:=G12)(B:=G3)(n:=n)(T:=x) in H1; [|exact H2]. congruence. }
  assert (b3: get G3 n=None\/get G3 n=Some None).
  { destruct (get G3 n) as [[x|]|] eqn:E3; auto; exfalso.
    apply split_get_r with (G:=G)(A:=G12)(B:=G3)(n:=n)(T:=x) in H1; [|exact E3]. congruence. }
  auto.
Qed.

(* ===== 从前缀 k 起可安全截断：merge 在 k 为 None，则 n>=k 用越界 None 两侧都成立 ===== *)
Lemma trunc_tail: forall G G12 G3 G1 G2 k,
  split G G12 G3 -> split G12 G1 G2 ->
  merge_cell (get G k)(get G1 k)(get G2 k)(get G3 k)=None ->
  forall n, n>=k ->
    cell_split (get G n)(get G1 n) None /\ cell_split None (get G2 n)(get G3 n).
Proof.
  intros G G12 G3 G1 G2 k H1 H2 Hmk n Hnk.
  assert (c1:=H1 n); assert (c2:=H2 n); assert (c1k:=H1 k); assert (c2k:=H2 k).
  unfold cell_split in *.
  apply merge_none_case in Hmk.
  destruct Hmk as [(E2k&E3k)|(EGk&E1k)].
  - (* 情形A: G2,G3 在 k 皆越界 -> n 位皆越界 *)
    assert (n2: get G2 n=None) by (apply get_none_overflow in E2k; apply get_overflow_none; lia).
    assert (n3: get G3 n=None) by (apply get_none_overflow in E3k; apply get_overflow_none; lia).
    split.
    + destruct c1 as [(a1&_)|(a2&ab12)], c2 as [(b1&_)|(b2&bb1)].
      * left; split; [exact (eq_trans b1 a1)|left; reflexivity].
      * right; split; [rewrite n2 in b2; rewrite <-b2 in a1; exact a1|exact bb1].
      * right; split; [rewrite n3 in a2; exact a2|rewrite b1; exact ab12].
      * right; split; [rewrite n3 in a2; exact a2|exact bb1].
    + left; split; [exact n2|left; exact n3].
  - (* 情形B: 让位 G 越界、G1 在位空位 -> n 位 G 越界 *)
    assert (nG: get G n=None) by (apply get_none_overflow in EGk; apply get_overflow_none; lia).
    assert (side: get G2 k=None \/ get G3 k=None).
    { eapply k_side; [exact EGk|exact E1k|exact c1k|exact c2k]. }
    destruct (gc_blank G G12 G3 G1 G2 n H1 H2 nG) as (b1&b2&b3).
    split.
    + right; split; [exact (eq_sym nG)|]. destruct b1 as [b|b]; [left|right]; exact b.
    + destruct side as [s2|s3].
      * assert (n2: get G2 n=None) by (apply get_none_overflow in s2; apply get_overflow_none; lia).
        left; split; [exact n2|]. destruct b3 as [b|b]; [left|right]; exact b.
      * assert (n3: get G3 n=None) by (apply get_none_overflow in s3; apply get_overflow_none; lia).
        right; split; [exact n3|]. destruct b2 as [b|b]; [left|right]; exact b.
Qed.

(* ===== 递归构造 G23：从 K 往 0，遇 merge=None 即截断 ===== *)
Fixpoint build_g23 (G G1 G2 G3:ctx)(k rem:nat):ctx :=
  match rem with
  | 0 => []
  | S rem' =>
      let m := merge_cell (get G k)(get G1 k)(get G2 k)(get G3 k) in
      let tail := build_g23 G G1 G2 G3 (S k) rem' in
      match m with Some v => v::tail | None => [] end
  end.

(* K=max(length G2,length G3) 之外，G2/G3 皆越界，用 None 两侧成立 *)
Lemma tail_past_K: forall G G12 G3 G1 G2 n,
  split G G12 G3 -> split G12 G1 G2 ->
  n>=length G2 -> n>=length G3 ->
  cell_split (get G n)(get G1 n) None /\ cell_split None (get G2 n)(get G3 n).
Proof.
  intros G G12 G3 G1 G2 n H1 H2 h2 h3.
  assert (n2:get G2 n=None) by (apply get_overflow_none; lia).
  assert (n3:get G3 n=None) by (apply get_overflow_none; lia).
  assert (c1:=H1 n); assert (c2:=H2 n). unfold cell_split in *. split.
  - destruct c1 as [(a1&_)|(a2&ab12)], c2 as [(b1&_)|(b2&bb1)].
    * left; split; [exact (eq_trans b1 a1)|left; reflexivity].
    * right; split; [rewrite n2 in b2; rewrite <-b2 in a1; exact a1|exact bb1].
    * right; split; [rewrite n3 in a2; exact a2|rewrite b1; exact ab12].
    * right; split; [rewrite n3 in a2; exact a2|exact bb1].
  - left; split; [exact n2|left; exact n3].
Qed.

(* length(build_g23 k rem) <= rem，供区间外越界用 *)
Lemma length_build_le: forall G G1 G2 G3 k rem,
  length (build_g23 G G1 G2 G3 k rem) <= rem.
Proof.
  intros G G1 G2 G3 k rem. revert k. induction rem as [|rem' IH].
  - intros k; cbn; lia.
  - intros k. cbn. destruct (merge_cell (get G k)(get G1 k)(get G2 k)(get G3 k)) as [v|].
    + cbn. apply le_n_S. exact (IH (S k)).
    + cbn; lia.
Qed.

(* 固定 merge_cell 不被 cbn 顺带展开，使 rewrite Em 可定位 *)
Opaque merge_cell.

(* 三个步长引理：把 build_g23 的逐层 get 化成交界等式，供归纳调用 *)
Lemma step_head: forall (G G1 G2 G3:ctx)(k rem':nat)(v:option ty),
  merge_cell (get G k)(get G1 k)(get G2 k)(get G3 k) = Some v ->
  get (build_g23 G G1 G2 G3 k (S rem')) 0 = Some v.
Proof. intros. cbn [build_g23]. rewrite H. cbn [get]. reflexivity. Qed.

Lemma step_some: forall (G G1 G2 G3:ctx)(k rem' n:nat)(v:option ty),
  merge_cell (get G k)(get G1 k)(get G2 k)(get G3 k) = Some v ->
  n >= S k ->
  get (build_g23 G G1 G2 G3 k (S rem')) (n-k) =
  get (build_g23 G G1 G2 G3 (S k) rem') (n-S k).
Proof.
  intros. cbn [build_g23]. rewrite H. cbn [get].
  replace (n-k) with (S (n-S k)) by lia. reflexivity.
Qed.

Lemma step_none: forall (G G1 G2 G3:ctx)(k rem':nat),
  merge_cell (get G k)(get G1 k)(get G2 k)(get G3 k) = None ->
  build_g23 G G1 G2 G3 k (S rem') = [].
Proof. intros. cbn [build_g23]. rewrite H. reflexivity. Qed.

(* 区间归纳：K=max(length G2,length G3)，B=build_g23 k rem（K=k+rem），区间内/外逐位成立 *)
Lemma build_correct: forall G G12 G3 G1 G2 K,
  split G G12 G3 -> split G12 G1 G2 -> K=max (length G2)(length G3) ->
  forall k rem, K=k+rem ->
  (forall n, k<=n -> n<K ->
      cell_split (get G n)(get G1 n)(get (build_g23 G G1 G2 G3 k rem)(n-k))
   /\ cell_split (get (build_g23 G G1 G2 G3 k rem)(n-k))(get G2 n)(get G3 n)) /\
  (forall n, n>=K ->
      cell_split (get G n)(get G1 n) None /\ cell_split None (get G2 n)(get G3 n)).
Proof.
  intros G G12 G3 G1 G2 K H1 H2 HK. intros k rem. revert k.
  induction rem as [|rem' IH].
  - (* rem=0: k=K，区间内空，区间外 tail_past_K *)
    intros k Hk. split.
    + intros n hle hlt; exfalso; rewrite Hk in hlt; lia.
    + intros n hn. apply tail_past_K with (G:=G)(G12:=G12)(G3:=G3)(G1:=G1)(G2:=G2)(n:=n);
        auto; lia.
  - intros k Hk.
    destruct (IH (S k) ltac:(lia)) as [IHin IHout].
    destruct (merge_cell (get G k)(get G1 k)(get G2 k)(get G3 k)) as [v|] eqn:Em.
    + (* merge=Some v: B=v::tail，用步长引理逐层化归到 (S k) 层 *)
      split.
      * intros n hle hlt.
        destruct (Nat.eq_dec n k) as [eq|ne].
        { subst n. replace (k-k) with 0 by lia.
          rewrite (step_head G G1 G2 G3 k rem' v Em).
          assert (cs:=cell_step (get G k)(get G12 k)(get G3 k)(get G1 k)(get G2 k)(H1 k)(H2 k)).
          rewrite Em in cs. exact cs. }
        { rewrite (step_some G G1 G2 G3 k rem' n v Em ltac:(lia)).
          apply IHin; lia. }
      * (* 区间外结论本就是 None，直接用 (S k) 层区间外 *)
        intros n hn. apply IHout; lia.
    + (* merge=None: B=[]，n>=k 全部由 trunc_tail 覆盖 *)
      split.
      * intros n hle hlt. rewrite (step_none G G1 G2 G3 k rem' Em). cbn [get].
        apply trunc_tail with (G:=G)(G12:=G12)(G3:=G3)(G1:=G1)(G2:=G2)(k:=k);
          [exact H1|exact H2|exact Em|lia].
      * intros n hn. apply IHout; lia.
Qed.

(* ===== 主定理：资源分划结合律 ===== *)
Theorem split_assoc: forall G G12 G3 G1 G2,
  split G G12 G3 -> split G12 G1 G2 ->
  exists G23, split G G1 G23 /\ split G23 G2 G3.
Proof.
  intros G G12 G3 G1 G2 H1 H2.
  set (K:=max (length G2)(length G3)).
  assert (BC:=build_correct G G12 G3 G1 G2 K H1 H2 eq_refl 0 K ltac:(lia)).
  destruct BC as [inL outR].
  exists (build_g23 G G1 G2 G3 0 K). split.
  - (* split G G1 G23 *)
    intros n; unfold split; destruct (Nat.ltb n K) eqn:Lt.
    + apply Nat.ltb_lt in Lt.
      destruct (inL n (Nat.le_0_l n) Lt) as [c1 _].
      rewrite Nat.sub_0_r in c1; unfold cell_split in c1; exact c1.
    + apply Nat.ltb_ge in Lt.
      assert (ov: get (build_g23 G G1 G2 G3 0 K) n=None).
      { apply get_overflow_none. apply Nat.le_trans with (m:=K).
        apply length_build_le. exact Lt. }
      destruct (outR n Lt) as [o1 _]. unfold cell_split in o1. rewrite ov; exact o1.
  - (* split G23 G2 G3 *)
    intros n; unfold split; destruct (Nat.ltb n K) eqn:Lt.
    + apply Nat.ltb_lt in Lt.
      destruct (inL n (Nat.le_0_l n) Lt) as [_ c2].
      rewrite Nat.sub_0_r in c2; unfold cell_split in c2; exact c2.
    + apply Nat.ltb_ge in Lt.
      assert (ov: get (build_g23 G G1 G2 G3 0 K) n=None).
      { apply get_overflow_none. apply Nat.le_trans with (m:=K).
        apply length_build_le. exact Lt. }
      destruct (outR n Lt) as [_ o2]. unfold cell_split in o2. rewrite ov; exact o2.
Qed.

Check split_assoc.

(* =====================================================================
   ALL_Layer2.v
   Layer 2: operational semantics + subject reduction
   Dependencies: Layer1.v (syntax, typing, renaming)
   ===================================================================== *)
From Stdlib Require Import List PeanoNat Lia ClassicalEpsilon.
Require Import ALL.Layer1.
Import ListNotations.

(* ---------------------------------------------------------------------
   1. Free variable detection
   --------------------------------------------------------------------- *)
Fixpoint fv_at (P : proc) (k : nat) : Prop :=
  match P with
  | PVar n     => n >= k
  | PZero      => False
  | PTau Q     => fv_at Q k
  | POut x y Q => x >= k \/ y >= k \/ fv_at Q k
  | PIn x Q    => x >= k \/ fv_at Q (S k)
  | PPar Q R   => fv_at Q k \/ fv_at R k
  | PRes Q     => fv_at Q (S k)
  | PRep Q     => fv_at Q k
  end.

Definition fv (P : proc) : Prop := fv_at P 0.
Definition closed (P : proc) : Prop := ~ fv P.

(* not_free_in：进程P不引用位置u（bool版本）。
   存在论意义：操作权不流经位置u，该位置无明性，可收摄（strengthening）。
   PIn/PRes进绑定器后偏移S u，与subst_var/fv_at一致。 *)
Fixpoint not_free_in (P : proc) (u : nat) : bool :=
  match P with
  | PZero => true
  | PTau Q => not_free_in Q u
  | PVar x => negb (Nat.eqb x u)
  | POut x y Q => negb (Nat.eqb x u) && negb (Nat.eqb y u) && not_free_in Q u
  | PIn x Q => negb (Nat.eqb x u) && not_free_in Q (S u)
  | PPar Q R => not_free_in Q u && not_free_in R u
  | PRes Q => not_free_in Q (S u)
  | PRep Q => not_free_in Q u
  end.

(* ---------------------------------------------------------------------
   2. Substitution
   --------------------------------------------------------------------- *)
Definition subst_name (m : nat) (k : nat) (n : nat) : nat :=
  if n =? k then m else if n <=? k then n else n - 1.

(* subst_name三种情况的辅助引理——存在论：名字在代换下的三种命运 *)
Lemma subst_name_eq : forall m k n, n = k -> subst_name m k n = m.
Proof.
  intros m k n H. unfold subst_name. rewrite H. rewrite Nat.eqb_refl. reflexivity.
Qed.

Lemma subst_name_lt : forall m k n, n < k -> subst_name m k n = n.
Proof.
  intros m k n Hlt. unfold subst_name.
  destruct (n =? k) eqn:Heq.
  - apply Nat.eqb_eq in Heq; lia.
  - destruct (n <=? k) eqn:Hle.
    + reflexivity.
    + apply Nat.leb_gt in Hle; lia.
Qed.

Lemma subst_name_gt : forall m k n, n > k -> subst_name m k n = n - 1.
Proof.
  intros m k n Hgt. unfold subst_name.
  destruct (n =? k) eqn:Heq.
  - apply Nat.eqb_eq in Heq; lia.
  - destruct (n <=? k) eqn:Hle.
    + apply Nat.leb_le in Hle; lia.
    + reflexivity.
Qed.

Fixpoint subst_var (m : nat) (k : nat) (P : proc) : proc :=
  match P with
  | PVar n     => PVar (subst_name m k n)
  | PZero      => PZero
  | PTau Q     => PTau (subst_var m k Q)
  | POut x y Q => POut (subst_name m k x) (subst_name m k y) (subst_var m k Q)
  | PIn x Q    => PIn (subst_name m k x) (subst_var (S m) (S k) Q)
  | PPar Q R   => PPar (subst_var m k Q) (subst_var m k R)
  | PRes Q     => PRes (subst_var (S m) (S k) Q)
  | PRep Q     => PRep (subst_var m k Q)
  end.

(* ---------------------------------------------------------------------
   2.1 no_use_at_subst (OB-009 A线前提，S04数学把关后的正确陈述)
   存在论：代换是把注入位k的引用重定向到源位m。若某引用（use消耗或PVar引用）
   在代换后恰好落在 m，则该引用会与另一侧的引用碰撞——线性类型系统不允许两个
   并行子进程引用同一操作权位（S04反例：PPar(PVar k)(PVar c)代换后变成
   PPar(PVar m)(PVar m)，split无法分配）。
   故代换定理要求：代换(m,k)之后，m 从未被任何引用（use或PVar）落在。
   关键(纠正S01单参数版的索引错位)：引用位置x在insert上下文，m在原始Gamma，
   二者隔了插入位k，故不能只比较 x=m；必须比较【代换后的名字】subst_name m k x
   是否=m（涵盖 x=k / x=m<k / x=m+1>k 三种落m情形）。递归结构与subst_var
   严格镜像：PIn/PRes进绑定器用(S m)(S k)，POut不进绑定器仍m k、且通道与
   发送值两个位置都查，PVar也查（S04反例修正：PVar碰撞同样导致split破产）。
   --------------------------------------------------------------------- *)
Fixpoint no_use_at_subst (P : proc) (m k : nat) : bool :=
  match P with
  | PZero      => true
  | PTau Q     => no_use_at_subst Q m k
  | PVar n     => negb (Nat.eqb (subst_name m k n) m)
  | POut x y Q => negb (Nat.eqb (subst_name m k x) m)
                  && negb (Nat.eqb (subst_name m k y) m)
                  && no_use_at_subst Q m k
  | PIn x Q    => negb (Nat.eqb (subst_name m k x) m)
                  && no_use_at_subst Q (S m) (S k)
  | PPar Q R   => no_use_at_subst Q m k && no_use_at_subst R m k
  | PRes Q     => no_use_at_subst Q (S m) (S k)
  | PRep Q     => no_use_at_subst Q m k
  end.

(* ====== subst_var 与 ren 的桥接（OB-010 via-renaming 路线） ====== *)
(* upren 与 subst_name 在绑定器提升下逐点相等：名字在代换下穿越绑定器 *)
Lemma upren_subst_name_pt : forall m k n,
  upren (subst_name m k) n = subst_name (S m) (S k) n.
Proof.
  intros m k n. destruct n as [|n'].
  - reflexivity.
  - unfold subst_name. simpl.
    destruct (n' =? k) eqn:E.
    + apply Nat.eqb_eq in E. subst n'. reflexivity.
    + destruct (n' <=? k) eqn:E2.
      * apply Nat.leb_le in E2. destruct (S n' <=? S k) eqn:E3; [reflexivity | lia].
      * apply Nat.leb_gt in E2. destruct (S n' <=? S k) eqn:E3; [lia |].
        simpl. f_equal. lia.
Qed.

(* 绑定器提升：subst_name 在 S 位置上的平移——穿越一个绑定层 *)
Lemma subst_name_succ : forall m k n,
  subst_name (S m) (S k) (S n) = S (subst_name m k n).
Proof.
  intros m k n. unfold subst_name. simpl.
  destruct (n =? k) eqn:E.
  - apply Nat.eqb_eq in E. subst n. simpl. reflexivity.
  - destruct (n <=? k) eqn:E2.
    + apply Nat.leb_le in E2. simpl. reflexivity.
    + apply Nat.leb_gt in E2. simpl. lia.
Qed.

(* 逐点相等的重命名函数给出相同结果——操作权流动不因名字而变 *)
Lemma ren_ext : forall (f g : nat -> nat) P, (forall n, f n = g n) ->
  ren f P = ren g P.
Proof.
  intros f g P. revert f g. induction P; intros f g H; simpl.
  - f_equal. apply H.
  - reflexivity.
  - f_equal. exact (IHP f g H).
  - f_equal; [apply H | apply H | exact (IHP f g H)].
  - f_equal; [apply H |
      apply (IHP (upren f) (upren g)); intros q; destruct q; simpl; auto].
  - f_equal; [exact (IHP1 f g H) | exact (IHP2 f g H)].
  - f_equal. apply (IHP (upren f) (upren g)); intros q; destruct q; simpl; auto.
  - f_equal. exact (IHP f g H).
Qed.

(* subst_var 本质就是沿 subst_name 的重命名——代换即重命名的特例 *)
Lemma subst_var_eq_ren : forall m k P,
  subst_var m k P = ren (subst_name m k) P.
Proof.
  intros m k P. revert m k. induction P; intros a b; simpl.
  - reflexivity.
  - reflexivity.
  - f_equal. exact (IHP a b).
  - f_equal. exact (IHP a b).
  - f_equal. rewrite (IHP (S a) (S b)).
      apply ren_ext. intros q. symmetry. apply upren_subst_name_pt.
  - f_equal; [exact (IHP1 a b) | exact (IHP2 a b)].
  - f_equal. rewrite (IHP (S a) (S b)). apply ren_ext. intros q. symmetry. apply upren_subst_name_pt.
  - f_equal. exact (IHP a b).
Qed.

Definition comm_subst (y : nat) (Q : proc) : proc := subst_var y 0 Q.

(* ---------------------------------------------------------------------
   3. Structural congruence
   --------------------------------------------------------------------- *)
Inductive congruence : proc -> proc -> Prop :=
  | cong_refl  : forall P, congruence P P
  | cong_sym   : forall P Q, congruence P Q -> congruence Q P
  | cong_trans : forall P Q R, congruence P Q -> congruence Q R -> congruence P R
  | cong_par_comm  : forall P Q, congruence (PPar P Q) (PPar Q P)
  | cong_par_assoc : forall P Q R, congruence (PPar (PPar P Q) R) (PPar P (PPar Q R))
  | cong_par_zero  : forall P, congruence (PPar P PZero) P
  | cong_res_par   : forall P Q, ~ fv_at Q 0 ->
      congruence (PRes (PPar P Q)) (PPar (PRes P) Q)
  | cong_rep_unfold : forall P, congruence (PRep P) (PPar P (PRep P))
  | cong_par_cong   : forall P P' Q Q', congruence P P' -> congruence Q Q' ->
      congruence (PPar P Q) (PPar P' Q')
  | cong_res_cong   : forall P P', congruence P P' -> congruence (PRes P) (PRes P')
  | cong_tau_cong   : forall P P', congruence P P' -> congruence (PTau P) (PTau P').

(* ---------------------------------------------------------------------
   4. Reduction relation
   --------------------------------------------------------------------- *)
Inductive reduce : proc -> proc -> Prop :=
  | red_tau : forall P, reduce (PTau P) P
  | red_comm : forall x y P Q,
      reduce (PPar (POut x y P) (PIn x Q)) (PPar P (comm_subst y Q))
  | red_par_l : forall P P' Q, reduce P P' -> reduce (PPar P Q) (PPar P' Q)
  | red_par_r : forall P Q Q', reduce Q Q' -> reduce (PPar P Q) (PPar P Q')
  | red_res   : forall P P', reduce P P' -> reduce (PRes P) (PRes P')
  | red_cong  : forall P Q P' Q',
      congruence P P' -> congruence Q Q' -> reduce P' Q' -> reduce P Q.

Inductive reduce_star : proc -> proc -> Prop :=
  | rstar_refl : forall P, reduce_star P P
  | rstar_step : forall P Q R, reduce P Q -> reduce_star Q R -> reduce_star P R.

(* ---------------------------------------------------------------------
   5. Values
   --------------------------------------------------------------------- *)
Inductive is_value : proc -> Prop :=
  | val_zero : is_value PZero
  | val_var  : forall x, is_value (PVar x)
  | val_out  : forall x y P, is_value (POut x y P)
  | val_in   : forall x P, is_value (PIn x P)
  | val_res  : forall P, is_value P -> is_value (PRes P)
  | val_rep  : forall P, is_value (PRep P)
  | val_par  : forall P Q, is_value P -> is_value Q -> is_value (PPar P Q).

(* ---------------------------------------------------------------------
   5.5 Strengthening（明性收摄）
   存在论：操作权不流经的位置无明性，可收摄（set_none），不影响typed。
   哲学研判（S01, 2026-09-03）：strengthening完全合法，与路线乙（同型异位）相容。
   --------------------------------------------------------------------- *)

(* set_none交换引理：x <> u时，先set_none x再set_none u = 先set_none u再set_none x *)
Lemma set_none_comm : forall C x u, x <> u ->
  set_none (set_none C x) u = set_none (set_none C u) x.
Proof.
  intros C. revert C. induction C as [| t C IH].
  - intros x u Hxu. reflexivity.
  - intros x u Hxu. destruct x as [|x']; destruct u as [|u']; simpl.
    + exfalso. apply Hxu. reflexivity.
    + reflexivity.
    + reflexivity.
    + f_equal. apply IH. intro E. apply Hxu. lia.
Qed.

(* use在strengthening下保持：x <> u时，use C x T C1 → use (set_none C u) x T (set_none C1 u) *)
Lemma use_strengthen : forall C x T C1 u,
  use C x T C1 -> x <> u -> use (set_none C u) x T (set_none C1 u).
Proof.
  intros C x T C1 u [Hget Hc1] Hxu.
  unfold use. split.
  - rewrite set_none_neq by exact Hxu. exact Hget.
  - rewrite Hc1. rewrite set_none_comm by exact Hxu. reflexivity.
Qed.

(* set_none后位置u的值只能是None或Some None（不可能是Some(Some T)） *)
Lemma set_none_at_self_empty : forall Gamma u,
  get (set_none Gamma u) u = None \/ get (set_none Gamma u) u = Some None.
Proof.
  intros Gamma u. destruct (Nat.lt_decidable u (length Gamma)) as [Hlt | Hnlt].
  - right. rewrite set_none_self by exact Hlt. reflexivity.
  - left. revert u Hnlt. induction Gamma as [| t Gamma IH].
    + intros u Hnlt. simpl. reflexivity.
    + intros u Hnlt. destruct u as [|u'].
      * simpl in Hnlt. lia.
      * simpl. apply (IH u'). intro H. assert (H' : S u' < S (length Gamma)) by lia. exact (Hnlt H').
Qed.

(* 基础引理：get Gamma n = None 时 n >= length Gamma（越界） *)
Lemma get_none_overflow : forall Gamma n, get Gamma n = None -> n >= length Gamma.
Proof.
  intros Gamma n H. revert n H. induction Gamma as [| t Gamma IH]; intros n H.
  - simpl in *. lia.
  - simpl in H. destruct n as [|n']; [discriminate |].
    specialize (IH n' H). unfold length in *. cbn in *. lia.
Qed.

(* 推论：n < length Gamma 时 get Gamma n 不可能是 None *)
Lemma get_not_none : forall Gamma n, n < length Gamma -> get Gamma n <> None.
Proof.
  intros Gamma n Hlt H. apply get_none_overflow in H. lia.
Qed.

(* 基础引理：n >= length Gamma 时 get Gamma n = None *)
Lemma get_overflow_none : forall Gamma n, n >= length Gamma -> get Gamma n = None.
Proof.
  intros Gamma n H. revert n H. induction Gamma as [| t Gamma IH]; intros n H.
  - simpl. reflexivity.
  - destruct n as [|n']; [unfold length in H; cbn in H; lia |].
    simpl. assert (H' : n' >= length Gamma).
    { unfold length in H; cbn in H.
      destruct (Nat.lt_decidable (length Gamma) n') as [Hlt | Hnlt].
      { lia. }
      { destruct (Nat.eq_dec (length Gamma) n') as [Heq | Hneq2].
        { lia. }
        { exfalso.
          destruct (Nat.lt_decidable n' (length Gamma)) as [Hgt | Hngt].
          { apply Nat.succ_lt_mono in Hgt.
            assert (Heq : S (length Gamma) = S n').
            { apply Nat.le_antisymm. exact H. exact (Nat.lt_le_incl _ _ Hgt). }
            exact (Nat.lt_neq _ _ Hgt (eq_sym Heq)). }
          { assert (Hle1 : n' <= length Gamma). { rewrite <- Nat.nlt_ge. exact Hnlt. }
            assert (Hle2 : length Gamma <= n'). { rewrite <- Nat.nlt_ge. exact Hngt. }
            assert (Heq : n' = length Gamma) by (exact (Nat.le_antisymm _ _ Hle1 Hle2)).
            exact (Hneq2 (eq_sym Heq)). } } } }
    exact (IH n' H').
Qed.

(* 基础引理：set_none 不改变上下文长度 *)
Lemma length_set_none : forall Gamma k, length (set_none Gamma k) = length Gamma.
Proof.
  intros Gamma k. revert k. induction Gamma as [|t Gamma IH]; intros k.
  - reflexivity.
  - destruct k as [|k']; simpl; [reflexivity | rewrite IH; reflexivity].
Qed.

(* 基础引理：在位置u处，若 get Gamma u = get C u，则 set_none 后在u处仍相等 *)
Lemma set_none_eq_at_self : forall Gamma C u,
  get Gamma u = get C u -> get (set_none Gamma u) u = get (set_none C u) u.
Proof.
  intros Gamma C u Heq.
  destruct (Nat.lt_decidable u (length C)) as [Hlt | Hnlt].
  - (* u < length C：两边都是 Some None *)
    assert (Hc : get C u <> None) by (apply get_not_none; exact Hlt).
    assert (HltG : u < length Gamma).
    { destruct (Nat.lt_decidable u (length Gamma)) as [HltG | HnltG].
      - exact HltG.
      - exfalso. apply Hc. rewrite <- Heq. apply get_overflow_none. unfold ge. rewrite <- Nat.nlt_ge. exact HnltG. }
    rewrite (set_none_self C u Hlt). rewrite (set_none_self Gamma u HltG). reflexivity.
  - (* u >= length C：两边都是 None *)
    assert (Hc_none : get C u = None).
    { apply get_overflow_none. unfold ge. rewrite <- Nat.nlt_ge. exact Hnlt. }
    assert (Hg_none : get Gamma u = None) by (rewrite Heq; exact Hc_none).
    assert (HnltG : u >= length Gamma) by (apply get_none_overflow; exact Hg_none).
    assert (Hlen1 : length (set_none C u) = length C) by (apply length_set_none).
    assert (H1 : get (set_none C u) u = None).
    { apply get_overflow_none. rewrite Hlen1. unfold ge. rewrite <- Nat.nlt_ge. exact Hnlt. }
    assert (Hlen2 : length (set_none Gamma u) = length Gamma) by (apply length_set_none).
    assert (H2 : get (set_none Gamma u) u = None).
    { apply get_overflow_none. rewrite Hlen2. exact HnltG. }
    rewrite H2, H1. reflexivity.
Qed.

(* split在strengthening下保持：set_none后split结构不变（u位变None，None可分给任意侧） *)
Lemma split_strengthen : forall C Gamma1 Gamma2 u,
  split C Gamma1 Gamma2 ->
  split (set_none C u) (set_none Gamma1 u) (set_none Gamma2 u).
Proof.
  intros C Gamma1 Gamma2 u Hs.
  unfold split in *. intros n.
  destruct (Nat.eq_dec n u) as [Heq | Hneq].
  - (* n = u *)
    subst n.
    destruct (Hs u) as [Hl | Hr].
    + left. split.
      * destruct Hl as [Heq1 _]. exact (set_none_eq_at_self Gamma1 C u Heq1).
      * exact (set_none_at_self_empty Gamma2 u).
    + right. split.
      * destruct Hr as [Heq2 _]. exact (set_none_eq_at_self Gamma2 C u Heq2).
      * exact (set_none_at_self_empty Gamma1 u).
  - (* n <> u：set_none不影响位置n *)
    specialize (Hs n).
    rewrite !set_none_neq by exact Hneq.
    exact Hs.
Qed.

(* typed_strengthen_unused：进程P不使用位置u，则set_none C u后P仍类型化。
   对typed归纳，8个case全部tactic级给出。 *)
Lemma typed_strengthen_unused : forall C P u,
  typed C P -> not_free_in P u = true -> typed (set_none C u) P.
Proof.
  intros C P u Hty. revert u. induction Hty as [
    | Gamma x T H
    | Gamma P IH
    | Gamma x y P i o T Gamma1 Gamma2 H1 H2 H3 IH
    | Gamma x P i o T Gamma1 H1 H2 IH
    | Gamma P Q Gamma1 Gamma2 Hs IH1 IH2
    | Gamma P T IH
    | Gamma P IH
  ]; intros u Hnf.
  - (* ty_zero *)
    simpl in Hnf. apply ty_zero.
  - (* ty_var x T *)
    simpl in Hnf. rewrite Bool.negb_true_iff in Hnf. apply Nat.eqb_neq in Hnf.
    apply ty_var with (T:=T). rewrite set_none_neq by exact Hnf. exact H.
  - (* ty_tau P *)
    simpl in Hnf. apply ty_tau. apply IHIH. exact Hnf.
  - (* ty_out x y P i o T Gamma1 Gamma2 *)
    simpl in Hnf. rewrite !Bool.andb_true_iff in Hnf. destruct Hnf as [[Hnx Hny] HnfP].
    apply Bool.negb_true_iff in Hnx. apply Nat.eqb_neq in Hnx.
    apply Bool.negb_true_iff in Hny. apply Nat.eqb_neq in Hny.
    eapply ty_out with (i:=i)(o:=o)(T:=T)(Gamma1:=set_none Gamma1 u)(Gamma2:=set_none Gamma2 u).
    + apply use_strengthen with (u:=u). exact H1. exact Hnx.
    + exact H2.
    + apply use_strengthen with (u:=u). exact H3. exact Hny.
    + apply IHIH. exact HnfP.
  - (* ty_in x P i o T Gamma1 *)
    simpl in Hnf. rewrite Bool.andb_true_iff in Hnf. destruct Hnf as [Hnx HnfP].
    apply Bool.negb_true_iff in Hnx. apply Nat.eqb_neq in Hnx.
    eapply ty_in with (i:=i)(o:=o)(T:=T)(Gamma1:=set_none Gamma1 u).
    + apply use_strengthen with (u:=u). exact H1. exact Hnx.
    + exact H2.
    + simpl in HnfP. apply IHIH with (u := S u) in HnfP. simpl in HnfP. exact HnfP.
  - (* ty_par P Q Gamma1 Gamma2 *)
    simpl in Hnf. rewrite Bool.andb_true_iff in Hnf. destruct Hnf as [HnfP HnfQ].
    eapply ty_par with (Gamma1:=set_none Gamma1 u)(Gamma2:=set_none Gamma2 u).
    + apply split_strengthen. exact Hs.
    + apply IH2. exact HnfP.
    + apply IHHty1. exact HnfQ.
  - (* ty_res P T *)
    simpl in Hnf. apply ty_res with (T:=T).
      apply IHIH with (u := S u) in Hnf. simpl in Hnf. exact Hnf.
  - (* ty_rep P *)
    simpl in Hnf. apply ty_rep.
      assert (Htmp := IHIH u Hnf). simpl in Htmp. exact Htmp.
Qed.

(* ---------------------------------------------------------------------
   6. Auxiliary lemmas
   --------------------------------------------------------------------- *)
Lemma split_sym : forall Gamma Gamma1 Gamma2,
  split Gamma Gamma1 Gamma2 -> split Gamma Gamma2 Gamma1.
Proof.
  intros Gamma Gamma1 Gamma2 Hs. unfold split. intro n.
  specialize (Hs n). destruct Hs as [[H1 H2] | [H1 H2]];
    [right; split; [exact H1 | exact H2] | left; split; [exact H1 | exact H2]].
Qed.

Lemma use_set_none : forall Gamma x T Gamma',
  use Gamma x T Gamma' -> get Gamma' x = Some None.
Proof.
  intros Gamma x T Gamma' [Hx HGamma']. subst Gamma'.
  apply set_none_self. apply get_Some_lt in Hx. exact Hx.
Qed.

(* Key lemma: in linear type system, a channel cannot be used by both
   an output and an input in parallel composition. This makes red_comm
   vacuously true. *)
Lemma par_elim : forall Gamma P Q, typed Gamma (PPar P Q) ->
  exists Gamma1 Gamma2, split Gamma Gamma1 Gamma2 /\ typed Gamma1 P /\ typed Gamma2 Q.
Proof.
  intros Gamma P Q H. inversion H; subst.
  do 2 eexists. repeat split; eassumption.
Qed.

Lemma out_elim : forall Gamma x y P, typed Gamma (POut x y P) ->
  exists Gamma1 Gamma2 T i o, use Gamma x (TChan i o T) Gamma1 /\ o = true /\ use Gamma1 y T Gamma2 /\ typed Gamma2 P.
Proof.
  intros Gamma x y P H. inversion H; subst.
  do 5 eexists. split; [eassumption | split; [try reflexivity; try eassumption | split; [eassumption | eassumption]]].
Qed.

Lemma in_elim : forall Gamma x P, typed Gamma (PIn x P) ->
  exists Gamma1 T i o, use Gamma x (TChan i o T) Gamma1 /\ i = true /\ typed (Some T :: Gamma1) P.
Proof.
  intros Gamma x P H. inversion H; subst.
  do 4 eexists. split; [eassumption | split; [try reflexivity; try eassumption | eassumption]].
Qed.

Lemma res_elim : forall Gamma P, typed Gamma (PRes P) ->
  exists T, typed (Some T :: Gamma) P.
Proof.
  intros Gamma P H. inversion H; subst.
  eexists. eassumption.
Qed.
Lemma no_parallel_channel_sharing : forall Gamma x y P Q,
  ~ typed Gamma (PPar (POut x y P) (PIn x Q)).
Proof.
  intros Gamma x y P Q H.
  apply par_elim in H. destruct H as [Gamma1 [Gamma2 [Hs [HP HQ]]]].
  apply out_elim in HP. destruct HP as [Gamma1' [Gamma2' [T [i [o [Huse1 [Ho [Huse2 Hbody]]]]]]]].
  apply in_elim in HQ. destruct HQ as [Gamma2'' [T' [i' [o' [Huse [Hi Hbody']]]]]].
  unfold use in Huse1, Huse. destruct Huse1 as [Hx1 _], Huse as [Hx2 _].
  unfold split in Hs. specialize (Hs x).
  destruct Hs as [[Hg1 [Hg2 | Hg2]] | [Hg2 [Hg1 | Hg1]]].
  - rewrite Hg2 in Hx2. discriminate.
  - rewrite Hg2 in Hx2. injection Hx2 as Hx2'. discriminate.
  - rewrite Hg1 in Hx1. discriminate.
  - rewrite Hg1 in Hx1. injection Hx1 as Hx1'. discriminate.
Qed.

(* ---------------------------------------------------------------------
   6.5 辅助引理：代换引理的基础设施
   --------------------------------------------------------------------- *)

(* var_shift_lemma: 变量索引减1保持类型
   哲学含义：进入绑定器后，外部变量的索引偏移不改变其类型 *)
Lemma var_shift_lemma : forall Gamma T n,
  typed (Some T :: Gamma) (PVar (S n)) -> typed Gamma (PVar n).
Proof.
  intros Gamma T n H.
  inversion H; subst.
  simpl in *.
  eapply ty_var.
  eassumption.
Qed.

(* name_subst_lemma: 名字代换保持类型
   哲学含义：迹的替换不改变分类——同类型的迹可以互换 *)
Lemma name_subst_lemma : forall Gamma T y n,
  typed (Some T :: Gamma) (PVar n) ->
  get Gamma y = Some (Some T) ->
  typed Gamma (PVar (subst_name y 0 n)).
Proof.
  intros Gamma T y n H Hget.
  destruct n as [|n'].
  - (* n = 0: subst_name y 0 0 = y *)
    simpl. apply ty_var with (T := T). exact Hget.
  - (* n = S n': subst_name y 0 (S n') = n' *)
    unfold subst_name. simpl. rewrite Nat.sub_0_r.
    apply var_shift_lemma with (T := T) (n := n'). exact H.
Qed.

(* ---------------------------------------------------------------------
   6.6 insert_at: 在上下文的指定位置插入类型
   --------------------------------------------------------------------- *)

(* insert_at k T Gamma: 在位置k插入Some T
   哲学含义：代换的一般化——在任意位置插入同类型的迹
   来源：S01精确证明骨架 *)
Fixpoint insert_at (k : nat) (T : ty) (Gamma : ctx) : ctx :=
  match k with
  | 0 => Some T :: Gamma
  | S k' => match Gamma with
    | [] => None :: insert_at k' T []  (* 补None，保持位置正确 *)
    | g :: Gamma' => g :: insert_at k' T Gamma'
    end
  end.

(* insert_none_at：在位置k插入None（解决set_none_insert_at_eq的类型问题）
   存在论意义：插入一个已消耗的操作权位置，用于描述"消耗插入的操作权"后的状态 *)
Fixpoint insert_none_at (k : nat) (Gamma : ctx) : ctx :=
  match k with
  | 0 => None :: Gamma
  | S k' => match Gamma with
    | [] => None :: insert_none_at k' []
    | g :: Gamma' => g :: insert_none_at k' Gamma'
    end
  end.

(* insert_at和(::)的交换律：先insert_at再加头部 = 先加头部再insert_at(S k)
   这是OB-008的核心引理，解决PRes case的Gamma变量替换问题
   存在论意义：世界的扩展(::)和资源的插入(insert_at)是可交换的操作 *)
Lemma insert_at_cons_comm : forall (T T' : ty) (k : nat) (Gamma : ctx),
  Some T' :: insert_at k T Gamma = insert_at (S k) T (Some T' :: Gamma).
Proof.
  intros T T' k Gamma.
  induction k.
  - simpl. reflexivity.
  - destruct Gamma as [| g Gamma']; simpl; reflexivity.
Qed.

(* get_insert_at_self: 插入位置k的操作权确实是T
   这是PVar case的核心引理，n=k时用它证明T0=T
   存在论意义：插入操作权后，那个位置确实有这个操作权——操作的结果是可验证的 *)
Lemma get_insert_at_self : forall k T Gamma,
  get (insert_at k T Gamma) k = Some (Some T).
Proof.
  intros k T.
  induction k.
  - intros Gamma. simpl. reflexivity.
  - intros Gamma. destruct Gamma as [| g Gamma']; simpl; apply IHk.
Qed.

(* set_none_insert_at_lt: x < k时，set_none和insert_at可交换
   存在论意义：在插入位置之前消耗操作权，不影响插入的位置 *)
Lemma set_none_insert_at_lt : forall k T Gamma x,
  x < k -> set_none (insert_at k T Gamma) x = insert_at k T (set_none Gamma x).
Proof.
  intros k T.
  induction k.
  - intros Gamma x Hlt. exfalso. lia.
  - intros Gamma x Hlt.
    destruct x as [| x'].
    + destruct Gamma as [| g Gamma']; simpl; reflexivity.
    + destruct Gamma as [| g Gamma']; simpl.
      * (* Gamma = [] *)
        assert (H : set_none (insert_at k T []) x' = insert_at k T (set_none [] x')).
        { apply IHk. lia. }
        simpl in H. f_equal. exact H.
      * (* Gamma = g :: Gamma' *)
        f_equal. apply IHk. lia.
Qed.

(* set_none_insert_at_eq: x = k时，消耗的正是插入的操作权
   注意：原陈述set_none (insert_at k T Gamma) k = Gamma是错的！
   因为insert_at增加了列表长度，set_none后长度不变，所以不可能等于Gamma。
   正确的形式需要重新考虑，暂时Admitted。
   存在论意义：插入操作权后立即消耗它，回到原来的上下文（但长度可能不同） *)
Lemma set_none_insert_at_eq : forall k T Gamma,
  set_none (insert_at k T Gamma) k = insert_none_at k Gamma.
Proof.
  (* DeepSeek第四次：定义insert_none_at辅助函数解决类型问题。
     手算验证：Gamma=[a0,a1,a2], k=1:
     insert_at 1 T [a0,a1,a2]=[a0,Some T,a1,a2]
     set_none [... ] 1=[a0,None,a1,a2]
     insert_none_at 1 [a0,a1,a2]=[a0,None,a1,a2] ✅ *)
  intros k.
  induction k.
  - intros T Gamma. simpl. reflexivity.
  - intros T Gamma.
    destruct Gamma as [| g Gamma'].
    + (* Gamma = []：simpl后需要f_equal + IHk *)
      simpl. f_equal. apply IHk.
    + (* Gamma = g :: Gamma' *)
      simpl. f_equal. apply IHk.
Qed.

(* set_none_insert_at_gt: x > k时，set_none在insert_at之后，位置偏移
   存在论意义：在插入位置之后消耗操作权，插入的操作权不受影响 *)
(* 辅助引理：当x > k时，set_none在insert_at k T []的x位置不改变（因为x位置本来就是None） *)
Lemma set_none_insert_at_nil_gt : forall k T x,
  x > k -> set_none (insert_at k T []) x = insert_at k T [].
Proof.
  intros k T x Hgt.
  generalize dependent x.
  induction k; intros x Hgt.
  - destruct x; simpl.
    + lia.
    + reflexivity.
  - destruct x; simpl.
    + lia.
    + rewrite IHk; try lia. reflexivity.
Qed.

Lemma set_none_insert_at_gt : forall k T Gamma x,
  x > k -> set_none (insert_at k T Gamma) x = insert_at k T (set_none Gamma (x - 1)).
Proof.
  (* DeepSeek第四次完整证明：k=0时证明x-0=x，k=S k',Gamma=[]时用set_none_insert_at_nil_gt *)
  intros k T.
  induction k.
  - intros Gamma x Hgt.
    destruct Gamma as [| g Gamma'].
    + simpl. destruct x; simpl; try lia. reflexivity.
    + simpl. destruct x; simpl.
      * lia.
      * assert (H : x - 0 = x) by lia. rewrite H. reflexivity.
  - intros Gamma x Hgt.
    destruct Gamma as [| g Gamma'].
    + (* Gamma = []：simpl后先f_equal，再apply set_none_insert_at_nil_gt *)
      simpl.
      destruct x as [| x'].
      * lia.
      * f_equal.
        apply set_none_insert_at_nil_gt.
        lia.
    + (* Gamma = g :: Gamma'：先destruct x，x=S x'时再destruct x'（因为x'>k>=0），然后simpl+f_equal+IHk *)
      destruct x as [| x'].
      * lia.
      * (* x = S x'，x' > k *)
        destruct x' as [| x''].
        -- (* x' = 0，但x' > k >= 0，矛盾 *)
           exfalso. lia.
        -- (* x' = S x''，set_none (g::Gamma') (S x'') = g :: set_none Gamma' x'' *)
           simpl.
           f_equal.
           (* IHk需要set_none Gamma' (S x''-1)，目标是set_none Gamma' x''，
              先建立IHk结论，再用S x''-1=x''改写 *)
           assert (Hih : set_none (insert_at k T Gamma') (S x'') =
                        insert_at k T (set_none Gamma' (S x'' - 1))).
           { apply IHk with (x := S x''). lia. }
           assert (Hsub : S x'' - 1 = x'') by lia.
           rewrite Hsub in Hih.
           exact Hih.
Qed.

(* get_insert_at_lt: n < k时，插入位置在n之后，不影响位置n
   注意：仅当get返回Some (Some T')时成立，排除Gamma=[]的边界情况 *)
Lemma get_insert_at_lt : forall Gamma T k n T',
  n < k -> get (insert_at k T Gamma) n = Some (Some T') ->
  get Gamma n = Some (Some T').
Proof.
  intros Gamma0 T.
  induction Gamma0 as [| g Gamma' IHGamma].
  { (* Gamma0 = [] *)
    intros k n T' Hlt Hget.
    revert n T' Hlt Hget.
    induction k as [| k' IHk'].
    { intros n T' Hlt. inversion Hlt. }
    { intros n T' Hlt Hget.
      destruct n as [| n'].
      { simpl in Hget. inversion Hget. }
      { simpl in Hget.
        eapply IHk' with (n := n').
        { apply le_S_n in Hlt. exact Hlt. }
        { exact Hget. }
      }
    }
  }
  { (* Gamma0 = g :: Gamma' *)
    intros k n T' Hlt Hget.
    destruct k as [| k'].
    { inversion Hlt. }
    { destruct n as [| n'].
      { simpl in Hget. simpl. exact Hget. }
      { simpl in Hget.
        eapply IHGamma with (n := n').
        { apply le_S_n in Hlt. exact Hlt. }
        { exact Hget. }
      }
    }
  }
Qed.

Lemma get_insert_at_gt : forall Gamma T k n T',
  n > k -> get (insert_at k T Gamma) n = Some (Some T') ->
  get Gamma (n - 1) = Some (Some T').
Proof.
  intros Gamma0 T.
  induction Gamma0 as [| g Gamma' IHGamma].
  { (* Gamma0 = [] *)
    intros k n T' Hgt Hget.
    revert n T' Hgt Hget.
    induction k as [| k' IHk'].
    { intros n T' Hgt Hget. destruct n as [| n'].
      { inversion Hgt. }
      { simpl in Hget. inversion Hget. }
    }
    { intros n T' Hgt Hget.
      destruct n as [| n'].
      { inversion Hgt. }
      { simpl in Hget.
        eapply IHk' with (n := n').
        { apply le_S_n in Hgt. exact Hgt. }
        { exact Hget. }
      }
    }
  }
  { (* Gamma0 = g :: Gamma' *)
    intros k n T' Hgt Hget.
    destruct k as [| k'].
    { destruct n as [| n'].
      { inversion Hgt. }
      { destruct n' as [| n''].
        { simpl in Hget. simpl. exact Hget. }
        { simpl in Hget. simpl. exact Hget. }
      }
    }
    { destruct n as [| n'].
      { inversion Hgt. }
      { apply le_S_n in Hgt.
        destruct n' as [| n''].
        { inversion Hgt. }
        { simpl in Hget. simpl.
          replace n'' with (S n'' - 1) by (destruct n''; simpl; auto).
          eapply IHGamma with (k := k') (n := S n'').
          { exact Hgt. }
          { exact Hget. }
        }
      }
    }
  }
Qed.

(* name_subst_general: 名字代换的一般化版本
   n ≠ k时，变量索引偏移后类型不变
   哲学含义：迹的替换不改变分类——同类型的迹可以互换 *)
Lemma name_subst_general : forall Gamma T k m n,
  typed (insert_at k T Gamma) (PVar n) ->
  get Gamma m = Some (Some T) ->
  n <> k ->
  typed Gamma (PVar (subst_name m k n)).
Proof.
  intros Gamma T k m n H Hget Hne.
  inversion H; subst.
  destruct (Nat.compare n k) eqn:Hcmp.
  - (* n = k，矛盾 *)
    assert (Heq : n = k). { apply Nat.compare_eq_iff. exact Hcmp. }
    contradiction.
  - (* n < k *)
    assert (Hlt : n < k). { apply Nat.compare_lt_iff. exact Hcmp. }
    assert (Hget' : get Gamma n = Some (Some T0)).
    { eapply get_insert_at_lt; eauto. }
    assert (Hsub : subst_name m k n = n).
    { unfold subst_name.
      destruct (n =? k) eqn:E.
      + apply Nat.eqb_eq in E. contradiction.
      + destruct (n <=? k) eqn:E2.
        * reflexivity.
        * apply Nat.leb_gt in E2. lia.
    }
    rewrite Hsub.
    apply ty_var with (T := T0). exact Hget'.
  - (* n > k *)
    assert (Hgt : n > k). { apply Nat.compare_gt_iff. exact Hcmp. }
    assert (Hget' : get Gamma (n - 1) = Some (Some T0)).
    { eapply get_insert_at_gt; eauto. }
    assert (Hsub : subst_name m k n = n - 1).
    { unfold subst_name.
      destruct (n =? k) eqn:E.
      + apply Nat.eqb_eq in E. contradiction.
      + destruct (n <=? k) eqn:E2.
        * apply Nat.leb_le in E2. lia.
        * reflexivity.
    }
    rewrite Hsub.
    apply ty_var with (T := T0). exact Hget'.
Qed.

(* 空上下文代换引理：在空上下文下合法的进程，代换后仍然合法
   这是PRep case的核心引理
   存在论意义：空世界中没有操作权可以消耗，代换不改变任何东西 *)
(* ===== no_res_from：代换位置k及其之后全无操作权，则代换保持类型化 =====
   存在论：代换是"撤去k位、把对k的指称迁回m、其后之名依次前移"。
   若k及其之后本就没有操作权（空上下文逐层加Some前缀正是此结构），
   则类型化之操作所引用之名必在k之前（n<k，subst_name不变），代换不改类型。
   关键：不需要显式fv_at谓词——类型推导自身携带"引用了哪些位置"。 ===== *)

Definition no_res_from (Gamma : ctx) (k : nat) : Prop :=
  forall n, n >= k -> get Gamma n = None \/ get Gamma n = Some None.

Lemma no_res_from_empty : forall k, no_res_from [] k.
Proof. intros k n _. left. reflexivity. Qed.

Lemma no_res_from_cons : forall (t : option ty) G k,
  no_res_from G k -> no_res_from (t :: G) (S k).
Proof.
  intros t G k H n hn. destruct n as [|n'].
  - lia.
  - simpl. apply H. lia.
Qed.

Lemma no_res_from_set_none : forall G k x,
  x < k -> no_res_from G k -> no_res_from (set_none G x) k.
Proof.
  intros G k x Hxk H n hn.
  rewrite (set_none_neq G x n); [ apply H; exact hn | lia ].
Qed.

Lemma no_res_from_contra : forall G k n T,
  no_res_from G k -> n >= k -> get G n = Some (Some T) -> False.
Proof.
  intros G k n T H hn Hg.
  specialize (H n hn). destruct H as [H | H]; rewrite Hg in H; discriminate.
Qed.

Lemma split_no_res_from_l : forall G G1 G2 k,
  split G G1 G2 -> no_res_from G k -> no_res_from G1 k.
Proof.
  intros G G1 G2 k Hs H n hn.
  unfold split in Hs. specialize (Hs n).
  destruct Hs as [[Hg _] | [_ Hd]].
  - rewrite Hg. apply H. exact hn.
  - exact Hd.
Qed.

Lemma split_no_res_from_r : forall G G1 G2 k,
  split G G1 G2 -> no_res_from G k -> no_res_from G2 k.
Proof.
  intros G G1 G2 k Hs H n hn.
  unfold split in Hs. specialize (Hs n).
  destruct Hs as [[_ Hd] | [Hg _]].
  - exact Hd.
  - rewrite Hg. apply H. exact hn.
Qed.

Lemma subst_var_no_res_from : forall (Gamma : ctx) (m k : nat) (P : proc),
  no_res_from Gamma k -> typed Gamma P -> typed Gamma (subst_var m k P).
Proof.
  intros Gamma m k P Hk Hty.
  generalize dependent k. generalize dependent m.
  induction Hty; intros m k Hk.
  - (* ty_zero *) simpl. apply ty_zero.
  - (* ty_var x *) simpl.
    assert (hlt : x < k).
    { destruct (Nat.ltb x k) eqn:El.
      - apply Nat.ltb_lt; exact El.
      - apply Nat.ltb_ge in El. exfalso.
        eapply no_res_from_contra; [exact Hk|exact El|exact H]. }
    rewrite (subst_name_lt m k x hlt). eapply ty_var. exact H.
  - (* ty_tau *) simpl. apply ty_tau. apply (IHHty m k). exact Hk.
  - (* ty_out x y *) simpl.
    assert (Hc1 := H). unfold use in Hc1. destruct Hc1 as [Hxg Heq1].
    assert (Hc2 := H1). unfold use in Hc2. destruct Hc2 as [Hyg Heq2].
    subst Gamma1 Gamma2.
    assert (hxk : x < k).
    { destruct (Nat.ltb x k) eqn:Elx.
      - apply Nat.ltb_lt; exact Elx.
      - apply Nat.ltb_ge in Elx. exfalso.
        eapply no_res_from_contra;[exact Hk|exact Elx|exact Hxg]. }
    assert (Hk1 : no_res_from (set_none Gamma x) k).
    { apply no_res_from_set_none; [exact hxk|exact Hk]. }
    assert (hyk : y < k).
    { destruct (Nat.ltb y k) eqn:Ely.
      - apply Nat.ltb_lt; exact Ely.
      - apply Nat.ltb_ge in Ely. exfalso.
        eapply no_res_from_contra;[exact Hk1|exact Ely|exact Hyg]. }
    assert (Hk2 : no_res_from (set_none (set_none Gamma x) y) k).
    { apply no_res_from_set_none; [exact hyk|exact Hk1]. }
    rewrite (subst_name_lt m k x hxk).
    rewrite (subst_name_lt m k y hyk).
    eapply ty_out with (i:=i)(o:=o)(T:=T)
      (Gamma1:=set_none Gamma x)(Gamma2:=set_none (set_none Gamma x) y).
    + exact H. + exact H0. + exact H1.
    + apply (IHHty m k). exact Hk2.
  - (* ty_in x *) simpl.
    assert (Hc1 := H). unfold use in Hc1. destruct Hc1 as [Hxg Heq1]. subst Gamma1.
    assert (hxk : x < k).
    { destruct (Nat.ltb x k) eqn:Elx.
      - apply Nat.ltb_lt; exact Elx.
      - apply Nat.ltb_ge in Elx. exfalso.
        eapply no_res_from_contra;[exact Hk|exact Elx|exact Hxg]. }
    assert (Hk1 : no_res_from (set_none Gamma x) k).
    { apply no_res_from_set_none; [exact hxk|exact Hk]. }
    rewrite (subst_name_lt m k x hxk).
    eapply ty_in with (i:=i)(o:=o)(T:=T)(Gamma1:=set_none Gamma x).
    + exact H. + exact H0.
    + apply (IHHty (S m) (S k)).
      exact (no_res_from_cons (Some T) (set_none Gamma x) k Hk1).
  - (* ty_par *) simpl.
    assert (Hk1 : no_res_from Gamma1 k) by (eapply split_no_res_from_l; eassumption).
    assert (Hk2 : no_res_from Gamma2 k) by (eapply split_no_res_from_r; eassumption).
    eapply ty_par with (Gamma1:=Gamma1)(Gamma2:=Gamma2).
    + exact H.
    + apply (IHHty1 m k). exact Hk1.
    + apply (IHHty2 m k). exact Hk2.
  - (* ty_res *) simpl. apply ty_res with (T:=T).
    apply (IHHty (S m) (S k)).
    exact (no_res_from_cons (Some T) Gamma k Hk).
  - (* ty_rep *) simpl. apply ty_rep.
    exact (IHHty m k (no_res_from_empty k)).
Qed.

Lemma subst_var_empty : forall m k P, typed [] P -> typed [] (subst_var m k P).
Proof.
  intros m k P H.
  apply (subst_var_no_res_from [] m k P (no_res_from_empty k) H).
Qed.

Lemma andb3_true : forall b1 b2 b3 : bool,
  andb (andb b1 b2) b3 = true -> b1 = true /\ b2 = true /\ b3 = true.
Proof.
  intros b1 b2 b3 H.
  apply Bool.andb_true_iff in H. destruct H as [H12 H3].
  apply Bool.andb_true_iff in H12. destruct H12 as [H1 H2].
  auto.
Qed.

Lemma negb_eqb_true_neq : forall a b : nat,
  negb (Nat.eqb a b) = true -> a <> b.
Proof.
  intros a b H.
  apply Bool.negb_true_iff in H.
  apply Nat.eqb_neq. exact H.
Qed.

(* =====================================================================
   OB-010 PPar 地基：remove_at 与 insert_at/insert_none_at 的互逆
   存在论内涵：并行组合把一份世界 split 成两侧；代换前要把"插入的迹"
   从两侧各自撤除(remove_at)，再按那一位是"实有操作权(Some T)"还是
   "寂然之位(None)"复原——撤除与插入互为逆操作，操作权的分合可严格往返。
   ===================================================================== *)

(* remove_at：删去位置k，其后操作权整体前移一位 *)
Fixpoint remove_at (k : nat) (G : ctx) : ctx :=
  match G, k with
  | [], _ => []
  | _ :: G', 0 => G'
  | g :: G', S k' => g :: remove_at k' G'
  end.

(* 外延：等长且逐位置get相等，则两上下文同一（操作世界由其每一位唯一决定） *)
Lemma ctx_ext : forall G1 G2,
  length G1 = length G2 -> (forall n, get G1 n = get G2 n) -> G1 = G2.
Proof.
  intros G1. induction G1 as [|a G1' IH]; intros [|b G2'] Hlen Hget.
  - reflexivity.
  - simpl in Hlen. discriminate.
  - simpl in Hlen. discriminate.
  - simpl in Hlen. injection Hlen as Hlen'. f_equal.
    + specialize (Hget 0). simpl in Hget. injection Hget as Hab. exact Hab.
    + apply IH; [exact Hlen'|]. intros n. specialize (Hget (S n)). simpl in Hget. exact Hget.
Qed.

Lemma length_remove_at : forall k G, k < length G -> length (remove_at k G) = length G - 1.
Proof.
  intros k. induction k; intros G Hk.
  - destruct G as [|g G']; [simpl in Hk; lia|]. simpl. lia.
  - destruct G as [|g G']; [simpl in Hk; lia|].
    simpl in Hk. simpl. rewrite IHk by lia. lia.
Qed.

Lemma length_insert_at : forall k T D, k <= length D -> length (insert_at k T D) = length D + 1.
Proof.
  intros k. induction k; intros T D Hk.
  - simpl. lia.
  - destruct D as [|d D']; [simpl in Hk; lia|].
    simpl in Hk. simpl. f_equal. apply IHk. lia.
Qed.

Lemma length_insert_none_at : forall k D, k <= length D -> length (insert_none_at k D) = length D + 1.
Proof.
  intros k. induction k; intros D Hk.
  - simpl. lia.
  - destruct D as [|d D']; [simpl in Hk; lia|].
    simpl in Hk. simpl. f_equal. apply IHk. lia.
Qed.

(* n<k：remove_at 不触及n之前的位 *)
Lemma get_remove_at_lt : forall G k n, n < k -> get (remove_at k G) n = get G n.
Proof.
  intros G. induction G as [|g G' IH]; intros k n Hlt.
  - destruct k; simpl; reflexivity.
  - destruct k as [|k']; [lia|]. destruct n as [|n']; [simpl; reflexivity|].
    simpl. apply IH. lia.
Qed.

(* n>=k：remove_at 后原 n+1 位移到 n *)
Lemma get_remove_at_ge : forall G k n, n >= k -> get (remove_at k G) n = get G (n + 1).
Proof.
  intros G. induction G as [|g G' IH]; intros k n Hge.
  - destruct k; simpl; reflexivity.
  - destruct k as [|k'].
    + simpl. replace (n + 1) with (S n) by lia. simpl. reflexivity.
    + destruct n as [|n']; [lia|]. simpl. apply IH. lia.
Qed.

(* 实有位复原：k位持有Some T，则 G 恰为"在remove后k位插回T"（对k归纳，无需split给长度） *)
Lemma insert_remove_at_id : forall k T G,
  get G k = Some (Some T) -> G = insert_at k T (remove_at k G).
Proof.
  intros k. induction k; intros T G Hk.
  - destruct G as [|g G']; [simpl in Hk; discriminate|].
    simpl in Hk. injection Hk as Hg. subst g. simpl. reflexivity.
  - destruct G as [|g G']; [simpl in Hk; discriminate|].
    simpl in Hk. specialize (IHk T G' Hk). simpl. f_equal. exact IHk.
Qed.

(* 寂然位复原：k位存着Some None，则 G 恰为"在remove后k位插回None" *)
Lemma insert_none_remove_id : forall k G,
  get G k = Some None -> G = insert_none_at k (remove_at k G).
Proof.
  intros k. induction k; intros G Hk.
  - destruct G as [|g G']; [simpl in Hk; discriminate|].
    simpl in Hk. injection Hk as Hg. subst g. simpl. reflexivity.
  - destruct G as [|g G']; [simpl in Hk; discriminate|].
    simpl in Hk. specialize (IHk G' Hk). simpl. f_equal. exact IHk.
Qed.

(* insert_at 逐位置取回（前提 k<=length G：注入位在世界之内，不在尾部悬空补None）：
   n<k 时同原 n 位；n>k 时对应原 n-1 位 *)
Lemma get_insert_at_lt_eq : forall k T G n, k <= length G -> n < k ->
  get (insert_at k T G) n = get G n.
Proof.
  intros k. induction k; intros T G n Hlen Hn; [lia|].
  destruct G as [|g G']; [simpl in Hlen; lia|].
  simpl in Hlen.
  destruct n as [|n']; [simpl; reflexivity|]. simpl. apply IHk; lia.
Qed.

Lemma get_insert_at_gt_eq : forall k T G n, k <= length G -> n > k ->
  get (insert_at k T G) n = get G (n - 1).
Proof.
  intros k T G n Hlen Hn. revert k n Hlen Hn. induction G as [|g G' IH]; intros k n Hlen Hn.
  - assert (k = 0) by (simpl in Hlen; lia). subst k. destruct n; [lia|]. simpl.
    destruct n; simpl; reflexivity.
  - destruct k as [|k'].
    + destruct n; [lia|]. simpl. destruct n; simpl; reflexivity.
    + destruct n; [lia|].
      simpl in Hlen. simpl in Hn.
      assert (Hgt : n > k') by lia.
      assert (Hlen' : k' <= length G') by lia.
      specialize (IH k' n Hlen' Hgt) as Hih.
      destruct n as [|a]; [exfalso; lia|].
      simpl. replace (S a - 1) with a in Hih by lia. rewrite Hih. reflexivity.
Qed.

(* split 与 remove_at 的交换：在 insert_at 后的世界 split 成两侧，
   各自撤除插入位 k，便回到原始 Gamma 的 split。逐位置对接：
   n<k 用原位置 n，n>=k 用后移一位的 n+1（insert 在 n+1 处恰存 Gamma n）。 *)
Lemma split_remove_at_both : forall Gamma T k G1 G2,
  k <= length Gamma ->
  split (insert_at k T Gamma) G1 G2 ->
  split Gamma (remove_at k G1) (remove_at k G2).
Proof.
  intros Gamma T k G1 G2 Hlen Hs. unfold split. intros n.
  unfold split in Hs.
  destruct (Nat.ltb n k) eqn:El.
  - (* n < k：看 insert 世界的 n 位 *)
    apply Nat.ltb_lt in El.
    specialize (Hs n). destruct Hs as [[L1 L2] | [R1 R2]].
    + rewrite (get_insert_at_lt_eq k T Gamma n Hlen El) in L1. left. split.
      * rewrite get_remove_at_lt by lia. exact L1.
      * rewrite get_remove_at_lt by lia. exact L2.
    + rewrite (get_insert_at_lt_eq k T Gamma n Hlen El) in R1. right. split.
      * rewrite get_remove_at_lt by lia. exact R1.
      * rewrite get_remove_at_lt by lia. exact R2.
  - (* n >= k：看 insert 世界的 n+1 位（其值为 Gamma n） *)
    apply Nat.ltb_ge in El.
    assert (Hgt : n + 1 > k) by lia.
    specialize (Hs (n + 1)). destruct Hs as [[L1 L2] | [R1 R2]].
    + rewrite (get_insert_at_gt_eq k T Gamma (n+1) Hlen Hgt) in L1.
      replace ((n + 1) - 1) with n in L1 by lia. left. split.
      * rewrite get_remove_at_ge by lia. exact L1.
      * rewrite get_remove_at_ge by lia. exact L2.
    + rewrite (get_insert_at_gt_eq k T Gamma (n+1) Hlen Hgt) in R1.
      replace ((n + 1) - 1) with n in R1 by lia. right. split.
      * rewrite get_remove_at_ge by lia. exact R1.
      * rewrite get_remove_at_ge by lia. exact R2.
Qed.

(* 资源保持：insert世界n位的资源，经rho后在目标世界同型在位——操作权不丢失 *)
Lemma subst_rho_pts : forall Gamma T k m n T', k <= length Gamma ->
  get Gamma m = Some (Some T) ->
  get (insert_at k T Gamma) n = Some (Some T') ->
  get Gamma (subst_name m k n) = Some (Some T').
Proof.
  intros Gamma T k m n T' Hkle Hm Hn.
  destruct (Nat.ltb_spec n k) as [Hlt | Hge].
  - rewrite subst_name_lt by lia.
    rewrite (get_insert_at_lt_eq k T Gamma n Hkle Hlt) in Hn. exact Hn.
  - destruct (Nat.eqb_spec n k) as [Heq | Hne].
    + subst n. rewrite subst_name_eq by reflexivity.
      rewrite get_insert_at_self in Hn. injection Hn as E. subst T'. exact Hm.
    + assert (Hg : n > k) by lia.
      rewrite subst_name_gt by lia.
      rewrite (get_insert_at_gt_eq k T Gamma n Hkle Hg) in Hn. exact Hn.
Qed.

(* 局部单射：rho唯一非单射点是k与碰撞位c（rho值=m）；
   排除k本身、排除像为m者后，rho在剩余位置单射——no_use正是提供后一排除 *)
Lemma rho_inj_except_m : forall m k x y,
  x <> k -> y <> k ->
  subst_name m k x <> m -> subst_name m k y <> m ->
  subst_name m k x = subst_name m k y -> x = y.
Proof.
  intros m k x y Hxk Hyk Hnx Hny Heq.
  destruct (Nat.ltb_spec x k); destruct (Nat.ltb_spec y k).
  - rewrite subst_name_lt in Heq by lia.
    rewrite subst_name_lt in Heq by lia. lia.
  - exfalso. rewrite subst_name_lt in Heq by lia.
    rewrite subst_name_gt in Heq by lia. lia.
  - exfalso. rewrite subst_name_gt in Heq by lia.
    rewrite subst_name_lt in Heq by lia. lia.
  - rewrite subst_name_gt in Heq by lia.
    rewrite subst_name_gt in Heq by lia. lia.
Qed.

(* =====================================================================
   not_free_in 与 strengthening（明性收摄）——ty_par 的最后一块地基
   存在论：操作权未被进程引用的位置，其上没有明性需要保持；主动收摄
   （set_none 清空）该位置不改变类型化。这是主人"明性可不保持"的精确形式化。
   ===================================================================== *)

(* 辅助：u >= length G 时 set_none G u = G（越界则无操作权可收摄） *)
Lemma set_none_keep : forall G u, u >= length G -> set_none G u = G.
Proof.
  intros G. revert G. induction G as [| g G' IH]; intros u H.
  - simpl. reflexivity.
  - destruct u as [| u'].
    + simpl in H. lia.
    + simpl. f_equal. apply IH with (u := u'). simpl in H. lia.
Qed.

(* 辅助：u >= length G 时 get G u = None（越界无操作权） *)
Lemma get_overflow : forall G u, u >= length G -> get G u = None.
Proof.
  intros G. revert G. induction G as [| g G' IH]; intros u H.
  - simpl. reflexivity.
  - destruct u as [| u'].
    + simpl in H. lia.
    + simpl. apply IH with (u := u'). simpl in H. lia.
Qed.

(* 辅助：u < length G -> get G u <> None（界内必有值） *)
Lemma get_not_none_lt : forall G u, u < length G -> get G u <> None.
Proof.
  intros G u H. revert G H. induction u as [| u' IH]; intros G H.
  - destruct G as [| g G'].
    + simpl in H. lia.
    + simpl. discriminate.
  - destruct G as [| g G'].
    + simpl in H. lia.
    + simpl in H. assert (Hlt : u' < length G') by lia.
      apply (IH G') in Hlt. simpl. exact Hlt.
Qed.

(* 辅助：get G u = None -> u >= length G（越界才返回空） *)
Lemma get_none_ge : forall G u, get G u = None -> u >= length G.
Proof.
  intros G u H. destruct (Nat.ltb u (length G)) eqn:Hlt.
  - apply Nat.ltb_lt in Hlt.
    assert (Hne : get G u <> None) by (apply get_not_none_lt; exact Hlt).
    exfalso. apply Hne. exact H.
  - apply Nat.ltb_ge in Hlt. exact Hlt.
Qed.

(* 辅助：set_none 在自身位置的值只能是 None 或 Some None（空无即寂然） *)
Lemma get_set_none_null : forall G u,
  get (set_none G u) u = None \/ get (set_none G u) u = Some None.
Proof.
  intros G u. destruct (Nat.ltb u (length G)) eqn:H.
  - apply Nat.ltb_lt in H. right. rewrite (set_none_self G u H). reflexivity.
  - apply Nat.ltb_ge in H. left. rewrite (set_none_keep G u H).
    rewrite (get_overflow G u H). reflexivity.
Qed.

(* 辅助：若两上下文在 u 位值相等，则 set_none 后在 u 位值仍相等 *)
Lemma get_set_none_cong : forall G1 G2 u,
  get G1 u = get G2 u -> get (set_none G1 u) u = get (set_none G2 u) u.
Proof.
  intros G1 G2 u H. destruct (Nat.ltb u (length G1)) eqn:H1; destruct (Nat.ltb u (length G2)) eqn:H2.
  - apply Nat.ltb_lt in H1. apply Nat.ltb_lt in H2.
    rewrite set_none_self by exact H1. rewrite set_none_self by exact H2. reflexivity.
  - apply Nat.ltb_lt in H1. apply Nat.ltb_ge in H2.
    exfalso. rewrite (get_overflow G2 u H2) in H.
    apply (get_none_ge G1 u) in H. lia.
  - apply Nat.ltb_ge in H1. apply Nat.ltb_lt in H2.
    exfalso. rewrite (get_overflow G1 u H1) in H.
    apply eq_sym in H. apply (get_none_ge G2 u) in H. lia.
  - apply Nat.ltb_ge in H1. apply Nat.ltb_ge in H2.
    rewrite (set_none_keep G1 u H1). rewrite (set_none_keep G2 u H2). exact H.
Qed.

(* set_none 与 split 交换：两侧同时收摄同一位置，整体 split 关系不变
   存在论：收摄是全局操作，不改变资源的分合结构 *)
Lemma split_set_none : forall C G1 G2 u,
  split C G1 G2 -> split (set_none C u) (set_none G1 u) (set_none G2 u).
Proof.
  intros C G1 G2 u Hs. unfold split. intros n.
  unfold split in Hs. specialize (Hs n).
  destruct (Nat.eqb_spec n u) as [Heq | Hne].
  - subst n. destruct Hs as [[H1 [H2|H2]] | [H1 [H2|H2]]].
    + left. split.
      * exact (get_set_none_cong G1 C u H1).
      * exact (get_set_none_null G2 u).
    + left. split.
      * exact (get_set_none_cong G1 C u H1).
      * exact (get_set_none_null G2 u).
    + right. split.
      * exact (get_set_none_cong G2 C u H1).
      * exact (get_set_none_null G1 u).
    + right. split.
      * exact (get_set_none_cong G2 C u H1).
      * exact (get_set_none_null G1 u).
  - rewrite (set_none_neq C u n Hne).
    rewrite (set_none_neq G1 u n Hne).
    rewrite (set_none_neq G2 u n Hne).
    exact Hs.
Qed.

(* 桥接引理：no_use_at_subst 保证进程不引用任何"rho 值为 m"的位置。
   存在论：代换后坍缩到 m 的碰撞位，进程的操作权本就不流经，故该位可收摄。
   PIn/PRes 进绑定器，rho 升级为 subst_name(Sm)(Sk)、位置偏移 S u。 *)
Lemma nouse_excludes_rhom : forall (P : proc) (m k u : nat),
  no_use_at_subst P m k = true ->
  subst_name m k u = m ->
  not_free_in P u = true.
Proof.
  induction P as [ n | | P0 IHP0 | x y P0 IHP0 | x P0 IHP0 | P0 IHP0 Q0 IHQ0 | P0 IHP0 | P0 IHP0 ];
    intros m k u Hnu Hrhom; simpl in Hnu; simpl.
  - (* PVar n *)
    apply Bool.negb_true_iff in Hnu. apply Nat.eqb_neq in Hnu.
    apply Bool.negb_true_iff. apply Nat.eqb_neq.
    intro E. subst n. exact (Hnu Hrhom).
  - (* PZero *) reflexivity.
  - (* PTau *) exact (IHP0 m k u Hnu Hrhom).
  - (* POut x y P0：&& 左结合 (A&&B)&&C *)
    apply Bool.andb_true_iff in Hnu. destruct Hnu as [Hxy Hnub].
    apply Bool.andb_true_iff in Hxy. destruct Hxy as [Hnx Hny].
    apply Bool.negb_true_iff in Hnx. apply Nat.eqb_neq in Hnx.
    apply Bool.negb_true_iff in Hny. apply Nat.eqb_neq in Hny.
    apply Bool.andb_true_iff. split.
    + apply Bool.andb_true_iff. split.
      * apply Bool.negb_true_iff. apply Nat.eqb_neq.
        intro E. subst x. exact (Hnx Hrhom).
      * apply Bool.negb_true_iff. apply Nat.eqb_neq.
        intro E. subst y. exact (Hny Hrhom).
    + exact (IHP0 m k u Hnub Hrhom).
  - (* PIn x P0：body 进绑定器，位置偏移 S u，rho 升级 *)
    apply Bool.andb_true_iff in Hnu. destruct Hnu as [Hnx Hnub].
    apply Bool.negb_true_iff in Hnx. apply Nat.eqb_neq in Hnx.
    apply Bool.andb_true_iff. split.
    + apply Bool.negb_true_iff. apply Nat.eqb_neq.
      intro E. subst x. exact (Hnx Hrhom).
    + eapply IHP0. exact Hnub. rewrite subst_name_succ. rewrite Hrhom. reflexivity.
  - (* PPar P0 Q0 *)
    apply Bool.andb_true_iff in Hnu. destruct Hnu as [HnP HnQ].
    apply Bool.andb_true_iff. split.
    + exact (IHP0 m k u HnP Hrhom).
    + exact (IHQ0 m k u HnQ Hrhom).
  - (* PRes P0：进绑定器 *)
    eapply IHP0. exact Hnu. rewrite subst_name_succ. rewrite Hrhom. reflexivity.
  - (* PRep P0 *) exact (IHP0 m k u Hnu Hrhom).
Qed.

(* 碰撞位刻画：rho=subst_name m k 唯一把两个位置映到 m——注入位 k 与另一碰撞位 c。
   c 的取法：m<k 时 c=m（走 lt 支，rho m=m）；m>=k 时 c=S m（走 gt 支，rho(S m)=m）。
   存在论：非单射只可能发生在这两个"汇于 m"的位置，其余位置 rho 皆单射。 *)
Definition collision_other (m k : nat) : nat := if m <? k then m else S m.

Lemma rho_collision_k : forall m k, subst_name m k k = m.
Proof. intros. apply subst_name_eq. reflexivity. Qed.

Lemma rho_collision_other : forall m k, subst_name m k (collision_other m k) = m.
Proof.
  intros m k. unfold collision_other. destruct (m <? k) eqn:E.
  - apply Nat.ltb_lt in E. rewrite (subst_name_lt m k m) by lia. reflexivity.
  - apply Nat.ltb_ge in E. rewrite (subst_name_gt m k (S m)) by lia. simpl. lia.
Qed.

(* 任一满足 rho u=m 的位置，必是 k 或另一碰撞位 c——碰撞位恰好两个 *)
Lemma rhom_classify : forall m k u, subst_name m k u = m ->
  u = k \/ u = collision_other m k.
Proof.
  intros m k u H.
  destruct (Nat.ltb_spec u k) as [Hlt | Hge].
  - (* u < k：rho u = u，故 u=m；而 m=u<k，碰撞位 c=m=u *)
    rewrite (subst_name_lt m k u Hlt) in H.
    right. unfold collision_other.
    destruct (Nat.ltb_spec m k) as [Hmk | Hmnk].
    + simpl. exact H.
    + exfalso. lia.
  - destruct (Nat.eqb_spec u k) as [Heq | Hne].
    + (* u = k *) left. exact Heq.
    + (* u > k：rho u = u-1 = m，故 u=S m；而 m>=k，碰撞位 c=S m=u *)
      assert (Hgt : u > k) by lia.
      rewrite (subst_name_gt m k u Hgt) in H.
      right. unfold collision_other.
      destruct (Nat.ltb_spec m k) as [Hmk | Hmnk].
      * exfalso. lia.
      * simpl. lia.
Qed.

(* 打包收摄：把源上下文 C 在两个碰撞位 k、c 都收摄（set_none），
   前提是进程 P 不引用它们（由 no_use + nouse_excludes_rhom 保证）。
   收摄后的源在"有资源的位置"上 rho 必单射——这是 ty_par 重划的基石。 *)
Lemma typed_strengthen_collisions : forall (C : ctx) (P : proc) m k,
  typed C P -> no_use_at_subst P m k = true ->
  typed (set_none (set_none C k) (collision_other m k)) P.
Proof.
  intros C P m k Hty Hnu.
  apply typed_strengthen_unused.
  - apply typed_strengthen_unused with (u := k).
    + exact Hty.
    + apply (nouse_excludes_rhom P m k k Hnu). apply rho_collision_k.
  - apply (nouse_excludes_rhom P m k (collision_other m k) Hnu).
    apply rho_collision_other.
Qed.

(* --- ty_par 专用辅助引理群：收摄后的源在"有资源位置"上恢复 rho 单射 --- *)

(* 收摄位本身永远不可能持有实有操作权 Some(Some T)：它要么被置为 Some None，
   要么本就越界为 None——明性收摄的位不再是资源位 *)
Lemma get_set_none_self_not_some : forall C k T,
  get (set_none C k) k <> Some (Some T).
Proof.
  induction C; intros k T.
  - simpl. discriminate.
  - destruct k as [|k'].
    + simpl. intro E. injection E as E'. discriminate.
    + simpl. exact (IHC k' T).
Qed.

(* 两个碰撞位 k 与 c 必不相同 *)
Lemma collision_distinct : forall m k, k <> collision_other m k.
Proof.
  intros m k. unfold collision_other.
  destruct (Nat.ltb_spec m k) as [Hlt | Hge]; lia.
Qed.

(* 收摄只可能把实有位置为 None/Some None，绝不可能凭空改变其他实有位：
   收摄后仍是 Some(Some T) 的位，收摄前也是 *)
Lemma set_none_preserves_some : forall C u n T,
  get (set_none C u) n = Some (Some T) -> get C n = Some (Some T).
Proof.
  intros C u n T H. destruct (Nat.eqb_spec n u).
  - subst n. exfalso. exact (get_set_none_self_not_some C u T H).
  - rewrite (set_none_neq C u n n0) in H. exact H.
Qed.

(* 关键：在收摄掉两个碰撞位的源中，凡"有资源"的位置 n 必有 rho n <> m。
   否则 n 是碰撞位（rhom_classify），而碰撞位已被收摄，不可能 has——矛盾。
   这正是"收摄后恢复局部单射"的核心。 *)
Lemma strengthened_has_not_rhom : forall C m k n,
  has (set_none (set_none C k) (collision_other m k)) n ->
  subst_name m k n <> m.
Proof.
  intros C m k n Hhas Hrhom.
  apply rhom_classify in Hrhom. unfold has in Hhas.
  destruct Hhas as [T Hget]. destruct Hrhom as [Ek | Ec].
  - subst n.
    rewrite (set_none_neq (set_none C k) (collision_other m k) k
             (collision_distinct m k)) in Hget.
    exact (get_set_none_self_not_some C k T Hget).
  - subst n. exact (get_set_none_self_not_some (set_none C k)
                      (collision_other m k) T Hget).
Qed.

(* split 的两侧在同一位置不可能都持有实有操作权（线性：一份资源不能两侧共有） *)
Lemma split_disjoint_some : forall Gamma G1 G2 n T1 T2,
  split Gamma G1 G2 ->
  get G1 n = Some (Some T1) -> get G2 n = Some (Some T2) -> False.
Proof.
  intros Gamma G1 G2 n T1 T2 Hs H1 H2.
  unfold split in Hs. specialize (Hs n).
  destruct Hs as [[_ Hd] | [_ Hd]].
  - destruct Hd as [Hd | Hd]; rewrite Hd in H2;
      [discriminate | injection H2 as E; discriminate].
  - destruct Hd as [Hd | Hd]; rewrite Hd in H1;
      [discriminate | injection H1 as E; discriminate].
Qed.

(* 收摄后的两侧仍保持线性互斥：收摄不凭空产生资源，故仍不能同时持有 *)
Lemma strengthened_disjoint : forall Gamma G1 G2 m k n T1 T2,
  split Gamma G1 G2 ->
  get (set_none (set_none G1 k) (collision_other m k)) n = Some (Some T1) ->
  get (set_none (set_none G2 k) (collision_other m k)) n = Some (Some T2) ->
  False.
Proof.
  intros Gamma G1 G2 m k n T1 T2 Hs H1 H2.
  apply set_none_preserves_some in H1. apply set_none_preserves_some in H1.
  apply set_none_preserves_some in H2. apply set_none_preserves_some in H2.
  exact (split_disjoint_some Gamma G1 G2 n T1 T2 Hs H1 H2).
Qed.

(* =====================================================================
   subst_ren_general：代换定理的最一般形式（源任意，逐行同构 Layer1.ren_typed）
   源 D 经 rho=subst_name m k 到目标 Gamma；资源保持 Hpts + no_use 局部单射。
   PPar 用 split_proj 重划，源块 Ga/Gb 直接作子进程源（无需 insert 形状）。
   ===================================================================== *)
(* REPLACE: Lemma subst_ren_general ... Admitted. *)
(* REPLACE: from the declaration "Lemma subst_ren_general" down to the Qed. of this lemma only. *)
(* REPLACE: from the declaration "Lemma subst_ren_general" down to the Qed. of this lemma only. *)
(* 修正版：源上下文统一为 D，目标上下文统一为 G；并补上 POut/PIn 中 i/o 的 true 归约。 *)
(* REPLACE: from the declaration "Lemma subst_ren_general" down to the Qed. of this lemma only. *)
(* REPLACE: from the declaration "Lemma subst_ren_general" down to the Qed. of this lemma only. *)
Lemma subst_ren_general : forall (D : ctx) (Q : proc),
  typed D Q -> forall (m k : nat) (G : ctx),
  (forall n T', get D n = Some (Some T') ->
               get G (subst_name m k n) = Some (Some T')) ->
  no_use_at_subst Q m k = true ->
  typed G (ren (subst_name m k) Q).
Proof.
  intros D Q. revert D.
  induction Q as [n | | P IHP | x y P IHP | x P IHP | P IHP Q IHQ | P IHP | P IHP];
  intros D HTD m k G Hpts Hnu; simpl in *.
  - (* PVar n = ty_var *)
    inversion HTD as [?|Gamma x T Hget|? ? ?|? ? ? ? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ?|? ? ? ?|? ? ?]. subst.
    eapply ty_var. apply Hpts. exact Hget.
  - (* PZero = ty_zero *)
    inversion HTD as [Gamma|? ? ? ?|? ? ?|? ? ? ? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ?|? ? ? ?|? ? ?]. subst.
    apply ty_zero.
  - (* PTau P = ty_tau *)
    inversion HTD as [?|? ? ? ?|Gamma P0 H|? ? ? ? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ?|? ? ? ?|? ? ?]. subst.
    apply ty_tau. exact (IHP D H m k G Hpts Hnu).
  - (* POut x y P = ty_out *)
    inversion HTD as [?|? ? ? ?|? ? ?|Gamma x0 y0 P0 i o T Gamma1 Gamma2 Huse1 Ho Huse2 H|? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ?|? ? ? ?|? ? ?].
    subst Gamma x0 y0 P0.
    assert (Hxy : x <> y). { eapply use_neq; eassumption. }
    assert (Hyx : y <> x). { intro E; apply Hxy; symmetry; exact E. }
    unfold use in Huse1, Huse2. destruct Huse1 as [Hx1 Hx2], Huse2 as [Hy1 Hy2].
    rewrite Hx2 in Hy1.
    rewrite Hy2 in H.
    rewrite Hx2 in H.
    apply Bool.andb_true_iff in Hnu. destruct Hnu as [H1 Hnub].
    apply Bool.andb_true_iff in H1. destruct H1 as [Hnux Hnuy].
    apply Bool.negb_true_iff in Hnux. apply Nat.eqb_neq in Hnux.
    apply Bool.negb_true_iff in Hnuy. apply Nat.eqb_neq in Hnuy.
    eapply ty_out with (x := subst_name m k x) (y := subst_name m k y)
      (P := ren (subst_name m k) P) (i := i) (o := o) (T := T)
      (Gamma1 := set_none G (subst_name m k x))
      (Gamma2 := set_none (set_none G (subst_name m k x)) (subst_name m k y)).
    + unfold use. split; [| reflexivity]. exact (Hpts x (TChan i o T) Hx1).
    + exact Ho.
    + unfold use. split; [| reflexivity].
      assert (HyDelta : get G (subst_name m k y) = Some (Some T)).
      { rewrite (set_none_neq D x y Hyx) in Hy1.
        exact (Hpts y T Hy1). }
      assert (Hxi : subst_name m k x <> subst_name m k y).
      { intro E.
        assert (Rkk : subst_name m k k = m).
        { exact (subst_name_eq m k k (eq_refl : k = k)). }
        assert (Hxk : x <> k) by (intro F; subst x; exact (Hnux Rkk)).
        assert (Hyk : y <> k) by (intro F; subst y; exact (Hnuy Rkk)).
        apply Hxy.
        exact (rho_inj_except_m m k x y Hxk Hyk Hnux Hnuy E). }
      assert (Hxi' : subst_name m k y <> subst_name m k x) by
        (intro E; apply Hxi; symmetry; exact E).
      rewrite (set_none_neq G (subst_name m k x) (subst_name m k y) Hxi'). exact HyDelta.
    + apply (IHP (set_none (set_none D x) y) H m k 
        (set_none (set_none G (subst_name m k x)) (subst_name m k y))).
      * intros n T' Hn.
        assert (Hny : n <> y).
        { intro F; subst n.
          apply (get_set_none_self_not_some (set_none D x) y T').
          exact Hn. }
        assert (Hnx : n <> x).
        { intro F; subst n.
          rewrite (set_none_neq (set_none D x) y x Hxy) in Hn.
          apply (get_set_none_self_not_some D x T').
          exact Hn. }
        rewrite (set_none_neq (set_none D x) y n Hny) in Hn.
        rewrite (set_none_neq D x n Hnx) in Hn.
        assert (HnDelta : get G (subst_name m k n) = Some (Some T')) by exact (Hpts n T' Hn).
        assert (Hxinx : subst_name m k n <> subst_name m k x).
        { intro E.
          assert (Rkk : subst_name m k k = m).
          { exact (subst_name_eq m k k (eq_refl : k = k)). }
          assert (Hnk : n <> k) by
            (intro F; subst n; rewrite Rkk in E; exact (Hnux (eq_sym E))).
          assert (Hxk : x <> k) by (intro F; subst x; exact (Hnux Rkk)).
          assert (Hrnnm : subst_name m k n <> m) by (rewrite E; exact Hnux).
          apply Hnx. exact (rho_inj_except_m m k n x Hnk Hxk Hrnnm Hnux E). }
        assert (Hxiny : subst_name m k n <> subst_name m k y).
        { intro E.
          assert (Rkk : subst_name m k k = m).
          { exact (subst_name_eq m k k (eq_refl : k = k)). }
          assert (Hnk : n <> k) by
            (intro F; subst n; rewrite Rkk in E; exact (Hnuy (eq_sym E))).
          assert (Hyk : y <> k) by (intro F; subst y; exact (Hnuy Rkk)).
          assert (Hrnnm : subst_name m k n <> m) by (rewrite E; exact Hnuy).
          apply Hny. exact (rho_inj_except_m m k n y Hnk Hyk Hrnnm Hnuy E). }
        rewrite (set_none_neq (set_none G (subst_name m k x)) (subst_name m k y) (subst_name m k n) Hxiny).
        rewrite (set_none_neq G (subst_name m k x) (subst_name m k n) Hxinx).
        exact HnDelta.
      * exact Hnub.
  - (* PIn x P = ty_in *)
    inversion HTD as [?|? ? ? ?|? ? ?|? ? ? ? ? ? ? ? ? ? ? ? ?|Gamma x0 P0 i o T Gamma1 Huse Hi H|? ? ? ? ? ? ? ?|? ? ? ?|? ? ?].
    subst Gamma x0 P0.
    unfold use in Huse. destruct Huse as [Hx1 Hx2].
    rewrite Hx2 in H.
    apply Bool.andb_true_iff in Hnu. destruct Hnu as [Hnux Hnub].
    apply Bool.negb_true_iff in Hnux. apply Nat.eqb_neq in Hnux.
    replace (ren (upren (subst_name m k)) P)
      with (ren (subst_name (S m) (S k)) P)
      by (symmetry; apply ren_ext with (f:=upren (subst_name m k)) (g:=subst_name (S m) (S k));
          intros q; exact (upren_subst_name_pt m k q)).
    eapply ty_in with (x := subst_name m k x) (P := ren (subst_name (S m) (S k)) P)
      (i := i) (o := o) (T := T)
      (Gamma1 := set_none G (subst_name m k x)).
    + unfold use. split; [| reflexivity]. exact (Hpts x (TChan i o T) Hx1).
    + exact Hi.
    + apply (IHP (Some T :: set_none D x) H (S m) (S k) (Some T :: set_none G (subst_name m k x))).
      * intros n T' Hn. destruct n as [|n].
        -- simpl in *. exact Hn.
        -- simpl in Hn.
           assert (Hnx : n <> x).
           { intro F; subst n; rewrite set_none_self in Hn;
             [injection Hn as Hc; discriminate | apply get_Some_lt in Hx1; exact Hx1]. }
           rewrite (set_none_neq D x n Hnx) in Hn.
           assert (Hr : subst_name m k n <> subst_name m k x).
           { intro E.
             assert (Hnk : n <> k) by
               (intro F; subst n; pose (Rk := subst_name_eq m k k (eq_refl : k = k));
                rewrite Rk in E; exact (Hnux (eq_sym E))).
             assert (Hxk : x <> k) by
               (intro F; subst x; pose (Rk := subst_name_eq m k k (eq_refl : k = k));
                exact (Hnux Rk)).
             assert (Hrnnm : subst_name m k n <> m) by (rewrite E; exact Hnux).
             assert (Hnx2 : n = x) by exact (rho_inj_except_m m k n x Hnk Hxk Hrnnm Hnux E).
             contradiction. }
           rewrite subst_name_succ. simpl.
           rewrite (set_none_neq G (subst_name m k x) (subst_name m k n) Hr).
           exact (Hpts n T' Hn).
      * exact Hnub.
  - (* PPar P Q = ty_par *)
    simpl in Hnu.
    apply Bool.andb_true_iff in Hnu. destruct Hnu as [HnuP HnuQ].
    inversion HTD as [?|? ? ? ?|? ? ?|? ? ? ? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ? ? ?|D0 P0 Q0 D1 D2 Hs HP HQ|? ? ? ?|? ? ?]. subst D0 P0 Q0.
    pose (D1' := set_none (set_none D1 k) (collision_other m k)).
    pose (D2' := set_none (set_none D2 k) (collision_other m k)).
    assert (HP' : typed D1' P) by (apply typed_strengthen_collisions with (C:=D1)(m:=m)(k:=k); assumption).
    assert (HQ' : typed D2' Q) by (apply typed_strengthen_collisions with (C:=D2)(m:=m)(k:=k); assumption).
    destruct (split_proj D1' (subst_name m k) G) as [Hs' [Hp1 Hp2]].
    eapply ty_par with (Gamma1:=proj1 D1' (subst_name m k) G) (Gamma2:=proj2 D1' (subst_name m k) G).
    + exact Hs'.
    + apply (IHP D1' HP' m k (proj1 D1' (subst_name m k) G)).
      * intros n T' Hn1.
        assert (HnD1 : get D1 n = Some (Some T')).
        { apply set_none_preserves_some in Hn1. apply set_none_preserves_some in Hn1. exact Hn1. }
        assert (HnD : get D n = Some (Some T')) by (eapply split_get_l; [exact Hs | exact HnD1]).
        assert (Hpt : get G (subst_name m k n) = Some (Some T')) by (apply Hpts; exact HnD).
        assert (Hhas1 : has D1' n) by (exists T'; exact Hn1).
        rewrite (Hp1 n Hhas1). exact Hpt.
      * exact HnuP.
    + apply (IHQ D2' HQ' m k (proj2 D1' (subst_name m k) G)).
      * intros n T' Hn2.
        assert (HnD2 : get D2 n = Some (Some T')).
        { apply set_none_preserves_some in Hn2. apply set_none_preserves_some in Hn2. exact Hn2. }
        assert (HnD : get D n = Some (Some T')) by (eapply split_get_r; [exact Hs | exact HnD2]).
        assert (Hpt : get G (subst_name m k n) = Some (Some T')) by (apply Hpts; exact HnD).
        assert (Hhas2 : has D2' n) by (exists T'; exact Hn2).
        assert (Hn_not_rhom : subst_name m k n <> m) by (apply strengthened_has_not_rhom with (C:=D2)(m:=m)(k:=k); exact Hhas2).
        assert (Hni : ~ img1 D1' (subst_name m k) (subst_name m k n)).
        { intro Him. destruct Him as [m0 [Am0 Em0]].
          assert (Hm0_not_rhom : subst_name m k m0 <> m) by (apply strengthened_has_not_rhom with (C:=D1)(m:=m)(k:=k); exact Am0).
          assert (Hm0_nk : m0 <> k) by (intro Eq; subst m0; apply Hm0_not_rhom; apply rho_collision_k).
          assert (Hn_nk : n <> k) by (intro Eq; subst n; apply Hn_not_rhom; apply rho_collision_k).
          assert (Hm0_nc : m0 <> collision_other m k) by (intro Eq; subst m0; apply Hm0_not_rhom; apply rho_collision_other).
          assert (Hn_nc : n <> collision_other m k) by (intro Eq; subst n; apply Hn_not_rhom; apply rho_collision_other).
          assert (Hinj : m0 = n) by
            (exact (rho_inj_except_m m k m0 n Hm0_nk Hn_nk Hm0_not_rhom Hn_not_rhom Em0)).
          subst m0.
          destruct Am0 as [T0 Hm0get].
          eapply strengthened_disjoint with (Gamma:=D)(G1:=D1)(G2:=D2)(m:=m)(k:=k)(n:=n)(T1:=T0)(T2:=T').
          * exact Hs.
          * exact Hm0get.
          * exact Hn2.
        }
        rewrite (Hp2 n Hni). exact Hpt.
      * exact HnuQ.
  - (* PRes P = ty_res *)
    inversion HTD as [?|? ? ? ?|? ? ?|? ? ? ? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ?|Gamma P0 T H|? ? ?]. subst.
    replace (ren (upren (subst_name m k)) P)
      with (ren (subst_name (S m) (S k)) P)
      by (symmetry; apply ren_ext with (f:=upren (subst_name m k)) (g:=subst_name (S m) (S k));
          intros n; exact (upren_subst_name_pt m k n)).
    apply (ty_res G (ren (subst_name (S m) (S k)) P) T).
    apply (IHP (Some T :: D) H (S m) (S k) (Some T :: G)).
    + intros n T' Hn. destruct n as [|n'].
      * simpl in Hn. injection Hn as E. subst T'. simpl. reflexivity.
      * simpl in Hn. rewrite subst_name_succ. simpl. exact (Hpts n' T' Hn).
    + exact Hnu.
  - (* PRep P = ty_rep *)
    inversion HTD as [?|? ? ? ?|? ? ?|? ? ? ? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ?|? ? ? ?|Gamma P0 H]. subst.
    apply (ty_rep G (ren (subst_name m k) P)).
    apply (IHP [] H m k []).
    + intros n T' Hn. simpl in Hn. discriminate.
    + exact Hnu.
Qed.
(* =====================================================================
   None版strengthening的基础设施（DS#10骨架 + S04数学把关）
   空绑定 insert_none_at 的 get/set_none/cons 套件，平行于 insert_at 版。
   存在论：在"寂然之位"(None)插入空无，类型化者本就不引用它，
   故撤除该位只是名字重排，不消耗任何操作权。
   ===================================================================== *)

Lemma get_insert_none_at_self : forall k D,
  k <= length D -> get (insert_none_at k D) k = Some None.
Proof.
  intros k. induction k; intros D Hk.
  - simpl. reflexivity.
  - destruct D as [|d D']; [simpl in Hk; lia|].
    simpl in Hk. simpl. apply IHk. lia.
Qed.

Lemma get_insert_none_at_lt : forall k D n,
  k <= length D -> n < k -> get (insert_none_at k D) n = get D n.
Proof.
  intros k. induction k; intros D n Hk Hn; [lia|].
  destruct D as [|d D']; [simpl in Hk; lia|].
  simpl in Hk. destruct n as [|n']; [simpl; reflexivity|].
  simpl. apply IHk; lia.
Qed.

Lemma get_insert_none_at_gt : forall k D n,
  k <= length D -> n > k -> get (insert_none_at k D) n = get D (n - 1).
Proof.
  intros k. induction k; intros D n Hk Hn.
  - destruct n; [lia|]. simpl. destruct n; simpl; reflexivity.
  - destruct D as [|d D']; [simpl in Hk; lia|].
    simpl in Hk. destruct n; [lia|].
    simpl. assert (Hn' : n > k) by lia.
    assert (Hk' : k <= length D') by lia.
    specialize (IHk D' n Hk' Hn').
    destruct n; [exfalso; lia|]. simpl.
    replace (S n - 1) with n in IHk by lia. exact IHk.
Qed.

Lemma set_none_insert_none_lt : forall k D x,
  x < k -> set_none (insert_none_at k D) x = insert_none_at k (set_none D x).
Proof.
  intros k. induction k; intros D x Hx.
  - exfalso. lia.
  - destruct x as [|x'].
    + destruct D as [|d D']; simpl; reflexivity.
    + destruct D as [|d D']; simpl; f_equal; apply IHk; lia.
Qed.

Lemma set_none_insert_none_eq : forall k D,
  set_none (insert_none_at k D) k = insert_none_at k D.
Proof.
  intros k. induction k; intros D.
  - simpl. reflexivity.
  - destruct D as [|d D']; simpl; f_equal; apply IHk.
Qed.

Lemma set_none_insert_none_nil_gt : forall k x, x > k ->
  set_none (insert_none_at k []) x = insert_none_at k [].
Proof.
  intros k. induction k; intros x Hx.
  - destruct x; [lia|]. simpl. destruct x; simpl; reflexivity.
  - destruct x; [lia|]. simpl. f_equal. apply IHk. lia.
Qed.

Lemma set_none_insert_none_gt : forall k D x,
  x > k -> set_none (insert_none_at k D) x = insert_none_at k (set_none D (x - 1)).
Proof.
  intros k. induction k.
  - intros D x Hgt. destruct D as [|d D'].
    + simpl. destruct x; simpl; try lia; reflexivity.
    + simpl. destruct x; simpl.
      * lia.
      * assert (H : x - 0 = x) by lia. rewrite H. reflexivity.
  - intros D x Hgt. destruct D as [|d D'].
    + simpl. destruct x as [|x']; [lia|]. f_equal.
      apply set_none_insert_none_nil_gt. lia.
    + destruct x as [|x']; [lia|]. destruct x' as [|x'']; [exfalso; lia|].
      simpl. f_equal.
      assert (Hih : set_none (insert_none_at k D') (S x'') =
                    insert_none_at k (set_none D' (S x'' - 1))).
      { apply IHk with (x := S x''). lia. }
      assert (Hsub : S x'' - 1 = x'') by lia. rewrite Hsub in Hih. exact Hih.
Qed.

Lemma insert_none_at_cons_comm : forall (T : ty) (k : nat) (D : ctx),
  Some T :: insert_none_at k D = insert_none_at (S k) (Some T :: D).
Proof.
  intros T k. induction k; intros D; simpl; reflexivity.
Qed.

(* =====================================================================
   substitution_none_strengthen：空绑定strengthening（DS#10骨架，S04落地）
   typed(insert_none_at k D) Q -> typed D(subst_var m k Q)，带 k<=length D。
   空位是Some None，Q不引用/消耗k位 => n=k支全矛盾；无get T、无no_use。
   存在论：撤除一个从未被持有的寂然之位，存在者只是整体下移一位。
   ===================================================================== *)
Lemma split_remove_none_both : forall D k G1 G2,
  k <= length D ->
  split (insert_none_at k D) G1 G2 ->
  split D (remove_at k G1) (remove_at k G2).
Proof.
  intros D k G1 G2 Hlen Hs. unfold split. intros n. unfold split in Hs.
  destruct (Nat.ltb n k) eqn:El.
  - apply Nat.ltb_lt in El.
    specialize (Hs n). destruct Hs as [[L1 L2] | [R1 R2]].
    + rewrite (get_insert_none_at_lt k D n Hlen El) in L1. left; split;
      rewrite get_remove_at_lt by lia; [exact L1 | exact L2].
    + rewrite (get_insert_none_at_lt k D n Hlen El) in R1. right; split;
      rewrite get_remove_at_lt by lia; [exact R1 | exact R2].
  - apply Nat.ltb_ge in El. assert (Hgt : n + 1 > k) by lia.
    specialize (Hs (n + 1)). destruct Hs as [[L1 L2] | [R1 R2]].
    + rewrite (get_insert_none_at_gt k D (n + 1) Hlen Hgt) in L1.
      replace ((n + 1) - 1) with n in L1 by lia. left; split;
      rewrite get_remove_at_ge by lia; [exact L1 | exact L2].
    + rewrite (get_insert_none_at_gt k D (n + 1) Hlen Hgt) in R1.
      replace ((n + 1) - 1) with n in R1 by lia. right; split;
      rewrite get_remove_at_ge by lia; [exact R1 | exact R2].
Qed.

(* =====================================================================
   subst_var_keep_free：若 k 及以上没有任何真实操作权(Some(Some T))，
   则 typed G Q 中被引用/消耗的名字都 < k，subst_var m k 是恒等。
   用于 PPar 空侧 split 出的较短上下文（k位越界None）。
   存在论：寂然之位以上本无存在者，名字的重定向触及不到空无，故自身保持。
   ===================================================================== *)

(* 在自身位置 set_none 后，该位绝不可能是真实操作权 *)

Lemma get_None_ge : forall G k, get G k = None -> forall n, n >= k -> get G n = None.
Proof.
  induction G; intros k Hk n Hn.
  - simpl. reflexivity.
  - destruct k; [simpl in Hk; discriminate |]. destruct n; [lia |]. simpl.
    apply IHG with (k := k); [exact Hk | lia].
Qed.


Lemma get_None_length : forall G k, get G k = None -> k >= length G.
Proof.
  induction G; intros k H.
  - simpl. lia.
  - destruct k; [simpl in H; discriminate |]. simpl in H.
    apply IHG in H. simpl. lia.
Qed.

Lemma remove_at_ge_id : forall G k, k >= length G -> remove_at k G = G.
Proof.
  induction G; intros k Hk.
  - destruct k; simpl; reflexivity.
  - destruct k; [simpl in Hk; lia |]. simpl. f_equal. apply IHG. simpl in Hk. lia.
Qed.

Lemma get_set_none_at_ne : forall G n T,
  get (set_none G n) n <> Some (Some T).
Proof.
  induction G; intros n T.
  - destruct n; simpl; discriminate.
  - destruct n; simpl; [discriminate | apply IHG].
Qed.

Lemma free_set_none : forall G k x,
  (forall n T, n >= k -> get G n <> Some (Some T)) ->
  (forall n T, n >= k -> get (set_none G x) n <> Some (Some T)).
Proof.
  intros G k x Hf n T Hnk Hc.
  destruct (Nat.eq_dec n x).
  - subst n. exact (get_set_none_at_ne G x T Hc).
  - rewrite set_none_neq in Hc by tauto. exact (Hf n T Hnk Hc).
Qed.

Lemma free_cons_S : forall G k T0,
  (forall n T, n >= k -> get G n <> Some (Some T)) ->
  (forall n T, n >= S k -> get (Some T0 :: G) n <> Some (Some T)).
Proof.
  intros G k T0 Hf n T Hnk Hc.
  destruct n; [lia |]. simpl in Hc. exact (Hf n T ltac:(lia) Hc).
Qed.

Lemma free_split_l : forall G G1 G2 k, split G G1 G2 ->
  (forall n T, n >= k -> get G n <> Some (Some T)) ->
  (forall n T, n >= k -> get G1 n <> Some (Some T)).
Proof.
  intros G G1 G2 k Hs Hf n T Hnk Hc.
  unfold split in Hs. specialize (Hs n).
  destruct Hs as [[L1 L2] | [R1 R2]].
  - rewrite L1 in Hc. exact (Hf n T Hnk Hc).
  - destruct R2 as [E | E]; rewrite E in Hc; discriminate.
Qed.

Lemma free_split_r : forall G G1 G2 k, split G G1 G2 ->
  (forall n T, n >= k -> get G n <> Some (Some T)) ->
  (forall n T, n >= k -> get G2 n <> Some (Some T)).
Proof.
  intros G G1 G2 k Hs Hf n T Hnk Hc.
  unfold split in Hs. specialize (Hs n).
  destruct Hs as [[L1 L2] | [R1 R2]].
  - destruct L2 as [E | E]; rewrite E in Hc; discriminate.
  - rewrite R1 in Hc. exact (Hf n T Hnk Hc).
Qed.

Lemma subst_var_keep_free : forall G k m Q,
  (forall n T, n >= k -> get G n <> Some (Some T)) ->
  typed G Q -> typed G (subst_var m k Q).
Proof.
  intros G k m Q. generalize dependent G. generalize dependent k. generalize dependent m.
  induction Q; intros m k G Hf Ht.
  - (* PVar *)
    simpl.
    inversion Ht as [| G0 x T0 Hg | | | | | |]; subst G0 x.
    destruct (Nat.ltb n k) eqn:E;
      [apply Nat.ltb_lt in E | apply Nat.ltb_ge in E; exfalso; exact (Hf n T0 E Hg)].
    rewrite (subst_name_lt m k n E). apply ty_var with (T := T0). exact Hg.
  - (* PZero *) simpl. apply ty_zero.
  - (* PTau *)
    simpl. inversion Ht; subst. apply ty_tau. exact (IHQ m k G Hf H1).
  - (* POut *)
    simpl.
    inversion Ht as [| | | G0 x0 y0 P0 i0 o0 T0 G1 G2 Hu1 Ho Hu2 Hb | | | |].
    subst G0 x0 y0 P0.
    unfold use in Hu1, Hu2. destruct Hu1 as [Hg1 Hs1]. destruct Hu2 as [Hg2 Hs2].
    destruct (Nat.ltb n k) eqn:En;
      [apply Nat.ltb_lt in En | apply Nat.ltb_ge in En; exfalso; exact (Hf n (TChan i0 o0 T0) En Hg1)].
    destruct (Nat.ltb n0 k) eqn:E0;
      [apply Nat.ltb_lt in E0 |
       apply Nat.ltb_ge in E0; exfalso; rewrite Hs1 in Hg2;
       rewrite (set_none_neq G n n0 ltac:(lia)) in Hg2; exact (Hf n0 T0 E0 Hg2)].
    rewrite (subst_name_lt m k n En). rewrite (subst_name_lt m k n0 E0).
    assert (Hg2' : get (set_none G n) n0 = Some (Some T0)).
    { rewrite <- Hs1. exact Hg2. }
    rewrite Hs2, Hs1 in Hb.
    eapply ty_out with (Gamma1 := set_none G n) (Gamma2 := set_none (set_none G n) n0).
    ** unfold use; split; [exact Hg1 | reflexivity].
    ** exact Ho.
    ** unfold use; split; [exact Hg2' | reflexivity].
    ** apply IHQ. 2: exact Hb. do 2 apply free_set_none. exact Hf.
  - (* PIn *)
    simpl.
    inversion Ht as [| | | | G0 x0 P0 i0 o0 T0 G1 Huse Hi Hb | | |].
    subst G0 x0 P0.
    unfold use in Huse. destruct Huse as [Hg Hs].
    destruct (Nat.ltb n k) eqn:En;
      [apply Nat.ltb_lt in En | apply Nat.ltb_ge in En; exfalso; exact (Hf n (TChan i0 o0 T0) En Hg)].
    rewrite (subst_name_lt m k n En).
    rewrite Hs in Hb.
    eapply ty_in with (i := i0) (o := o0) (T := T0) (Gamma1 := set_none G n).
    ** unfold use; split; [exact Hg | reflexivity].
    ** exact Hi.
    ** apply IHQ. 2: exact Hb. apply free_cons_S. apply free_set_none. exact Hf.
  - (* PPar *)
    simpl.
    inversion Ht as [| | | | | G0 Pa Pb G1 G2 Hsp Ha Hb | |]. subst G0 Pa Pb.
    eapply ty_par; [exact Hsp | |].
    + exact (IHQ1 m k G1 (free_split_l G G1 G2 k Hsp Hf) Ha).
    + exact (IHQ2 m k G2 (free_split_r G G1 G2 k Hsp Hf) Hb).
  - (* PRes *)
    simpl. apply res_elim in Ht. destruct Ht as [T0 H1].
    apply ty_res with (T := T0).
    apply (IHQ (S m) (S k) (Some T0 :: G)).
    + apply free_cons_S. exact Hf.
    + exact H1.
  - (* PRep *)
    simpl. inversion Ht; subst. apply ty_rep.
    apply subst_var_empty with (m := m) (k := k). exact H1.
Qed.

Lemma substitution_none_strengthen : forall D k m Q,
  k <= length D ->
  typed (insert_none_at k D) Q ->
  typed D (subst_var m k Q).
Proof.
  intros D k m Q.
  generalize dependent D. generalize dependent k. generalize dependent m.
  induction Q; intros m k D Hlen Ht.
  - (* PVar *)
    simpl.
    inversion Ht as [| G0 x T0 Hget0 | | | | | |]; subst G0 x.
    destruct (Nat.compare n k) eqn:Hcmp.
    + (* n=k：k位是None，矛盾 *)
      assert (Heq : n = k) by (apply Nat.compare_eq_iff; exact Hcmp). subst n.
      rewrite (get_insert_none_at_self k D Hlen) in Hget0. discriminate.
    + (* n<k *)
      assert (Hlt : n < k) by (apply Nat.compare_lt_iff; exact Hcmp).
      rewrite (subst_name_lt m k n Hlt).
      apply ty_var with (T := T0).
      rewrite <- (get_insert_none_at_lt k D n Hlen Hlt). exact Hget0.
    + (* n>k *)
      assert (Hgt : n > k) by (apply Nat.compare_gt_iff; exact Hcmp).
      rewrite (subst_name_gt m k n Hgt).
      apply ty_var with (T := T0).
      rewrite <- (get_insert_none_at_gt k D n Hlen Hgt). exact Hget0.
  - (* PZero *) simpl. apply ty_zero.
  - (* PTau *)
    simpl. inversion Ht; subst. apply ty_tau.
    exact (IHQ m k D Hlen H1).
  - (* POut *)
    simpl.
    inversion Ht as [| | | G0 x0 y0 P0 i0 o0 T0 G1 G2 Hu1 Ho Hu2 Hb | | | |].
    subst G0 x0 y0 P0.
    unfold use in Hu1, Hu2.
    destruct Hu1 as [Hgx Hs1]. destruct Hu2 as [Hgy Hs2].
    destruct (Nat.eq_dec n k) as [Hnek | Hnnek].
    + (* 通道 n=k：k位None矛盾 *)
      subst n. rewrite (get_insert_none_at_self k D Hlen) in Hgx. discriminate.
    + destruct (Nat.ltb n k) eqn:Hnltb.
      * (* 通道 n<k *)
        apply Nat.ltb_lt in Hnltb.
        assert (Hgn : get D n = Some (Some (TChan i0 o0 T0)))
          by (rewrite <- (get_insert_none_at_lt k D n Hlen Hnltb); exact Hgx).
        rewrite (set_none_insert_none_lt k D n Hnltb) in Hs1.
        assert (Hln1 : k <= length (set_none D n)) by (rewrite length_set_none; lia).
        destruct (Nat.eq_dec n0 k) as [Hyek | Hynek].
        -- (* 值 n0=k：矛盾 *)
          subst n0. rewrite Hs1 in Hgy.
          rewrite (get_insert_none_at_self k (set_none D n) Hln1) in Hgy. discriminate.
        -- destruct (Nat.ltb n0 k) eqn:Hyltb.
           ++ (* 值 n0<k *)
              apply Nat.ltb_lt in Hyltb.
              rewrite Hs1 in Hgy, Hs2.
              assert (Hgn0 : get (set_none D n) n0 = Some (Some T0))
                by (rewrite <- (get_insert_none_at_lt k (set_none D n) n0 Hln1 Hyltb); exact Hgy).
              rewrite (set_none_insert_none_lt k (set_none D n) n0 Hyltb) in Hs2.
              rewrite Hs2 in Hb.
              assert (Hln2 : k <= length (set_none (set_none D n) n0))
                by (repeat rewrite length_set_none; lia).
              rewrite (subst_name_lt m k n Hnltb). rewrite (subst_name_lt m k n0 Hyltb).
              eapply ty_out with (Gamma1 := set_none D n)
                                (Gamma2 := set_none (set_none D n) n0).
              ** unfold use; split; [exact Hgn | reflexivity].
              ** exact Ho.
              ** unfold use; split; [exact Hgn0 | reflexivity].
              ** exact (IHQ m k (set_none (set_none D n) n0) Hln2 Hb).
           ++ (* 值 n0>k *)
              apply Nat.ltb_ge in Hyltb. assert (Hygt : n0 > k) by lia.
              rewrite Hs1 in Hgy, Hs2.
              assert (Hgn0 : get (set_none D n) (n0 - 1) = Some (Some T0))
                by (rewrite <- (get_insert_none_at_gt k (set_none D n) n0 Hln1 Hygt); exact Hgy).
              rewrite (set_none_insert_none_gt k (set_none D n) n0 Hygt) in Hs2.
              rewrite Hs2 in Hb.
              assert (Hln2 : k <= length (set_none (set_none D n) (n0 - 1)))
                by (repeat rewrite length_set_none; lia).
              rewrite (subst_name_lt m k n Hnltb). rewrite (subst_name_gt m k n0 Hygt).
              eapply ty_out with (Gamma1 := set_none D n)
                                (Gamma2 := set_none (set_none D n) (n0 - 1)).
              ** unfold use; split; [exact Hgn | reflexivity].
              ** exact Ho.
              ** unfold use; split; [exact Hgn0 | reflexivity].
              ** exact (IHQ m k (set_none (set_none D n) (n0 - 1)) Hln2 Hb).
      * (* 通道 n>k *)
        apply Nat.ltb_ge in Hnltb. assert (Hngt : n > k) by lia.
        assert (Hgn : get D (n - 1) = Some (Some (TChan i0 o0 T0)))
          by (rewrite <- (get_insert_none_at_gt k D n Hlen Hngt); exact Hgx).
        rewrite (set_none_insert_none_gt k D n Hngt) in Hs1.
        assert (Hln1 : k <= length (set_none D (n - 1))) by (rewrite length_set_none; lia).
        destruct (Nat.eq_dec n0 k) as [Hyek | Hynek].
        -- subst n0. rewrite Hs1 in Hgy.
           rewrite (get_insert_none_at_self k (set_none D (n - 1)) Hln1) in Hgy. discriminate.
        -- destruct (Nat.ltb n0 k) eqn:Hyltb.
           ++ (* 值 n0<k *)
              apply Nat.ltb_lt in Hyltb.
              rewrite Hs1 in Hgy, Hs2.
              assert (Hgn0 : get (set_none D (n - 1)) n0 = Some (Some T0))
                by (rewrite <- (get_insert_none_at_lt k (set_none D (n - 1)) n0 Hln1 Hyltb); exact Hgy).
              rewrite (set_none_insert_none_lt k (set_none D (n - 1)) n0 Hyltb) in Hs2.
              rewrite Hs2 in Hb.
              assert (Hln2 : k <= length (set_none (set_none D (n - 1)) n0))
                by (repeat rewrite length_set_none; lia).
              rewrite (subst_name_gt m k n Hngt). rewrite (subst_name_lt m k n0 Hyltb).
              eapply ty_out with (Gamma1 := set_none D (n - 1))
                                (Gamma2 := set_none (set_none D (n - 1)) n0).
              ** unfold use; split; [exact Hgn | reflexivity].
              ** exact Ho.
              ** unfold use; split; [exact Hgn0 | reflexivity].
              ** exact (IHQ m k (set_none (set_none D (n - 1)) n0) Hln2 Hb).
           ++ (* 值 n0>k *)
              apply Nat.ltb_ge in Hyltb. assert (Hygt : n0 > k) by lia.
              rewrite Hs1 in Hgy, Hs2.
              assert (Hgn0 : get (set_none D (n - 1)) (n0 - 1) = Some (Some T0))
                by (rewrite <- (get_insert_none_at_gt k (set_none D (n - 1)) n0 Hln1 Hygt); exact Hgy).
              rewrite (set_none_insert_none_gt k (set_none D (n - 1)) n0 Hygt) in Hs2.
              rewrite Hs2 in Hb.
              assert (Hln2 : k <= length (set_none (set_none D (n - 1)) (n0 - 1)))
                by (repeat rewrite length_set_none; lia).
              rewrite (subst_name_gt m k n Hngt). rewrite (subst_name_gt m k n0 Hygt).
              eapply ty_out with (Gamma1 := set_none D (n - 1))
                                (Gamma2 := set_none (set_none D (n - 1)) (n0 - 1)).
              ** unfold use; split; [exact Hgn | reflexivity].
              ** exact Ho.
              ** unfold use; split; [exact Hgn0 | reflexivity].
              ** exact (IHQ m k (set_none (set_none D (n - 1)) (n0 - 1)) Hln2 Hb).
  - (* PIn *)
    simpl.
    inversion Ht as [| | | | G0 x0 P0 i0 o0 T0 G1 Huse Hi Hb | | |].
    unfold use in Huse. destruct Huse as [Hgx Hs1].
    subst G0 x0 P0.
    destruct (Nat.eq_dec n k) as [Hnek | Hnnek].
    + subst n. rewrite (get_insert_none_at_self k D Hlen) in Hgx. discriminate.
    + destruct (Nat.ltb n k) eqn:Hnltb.
      * (* n<k *)
        apply Nat.ltb_lt in Hnltb.
        assert (Hgn : get D n = Some (Some (TChan i0 o0 T0)))
          by (rewrite <- (get_insert_none_at_lt k D n Hlen Hnltb); exact Hgx).
        rewrite (set_none_insert_none_lt k D n Hnltb) in Hs1.
        assert (Hln1 : k <= length (set_none D n)) by (rewrite length_set_none; lia).
        rewrite (subst_name_lt m k n Hnltb).
        eapply ty_in with (i := i0) (o := o0) (T := T0) (Gamma1 := set_none D n).
        ** unfold use; split; [exact Hgn | reflexivity].
        ** exact Hi.
        ** rewrite Hs1 in Hb. rewrite insert_none_at_cons_comm in Hb.
           apply (IHQ (S m) (S k) (Some T0 :: set_none D n)).
           -- simpl. lia.
           -- exact Hb.
      * (* n>k *)
        apply Nat.ltb_ge in Hnltb. assert (Hngt : n > k) by lia.
        assert (Hgn : get D (n - 1) = Some (Some (TChan i0 o0 T0)))
          by (rewrite <- (get_insert_none_at_gt k D n Hlen Hngt); exact Hgx).
        rewrite (set_none_insert_none_gt k D n Hngt) in Hs1.
        assert (Hln1 : k <= length (set_none D (n - 1))) by (rewrite length_set_none; lia).
        rewrite (subst_name_gt m k n Hngt).
        eapply ty_in with (i := i0) (o := o0) (T := T0) (Gamma1 := set_none D (n - 1)).
        ** unfold use; split; [exact Hgn | reflexivity].
        ** exact Hi.
        ** rewrite Hs1 in Hb. rewrite insert_none_at_cons_comm in Hb.
           apply (IHQ (S m) (S k) (Some T0 :: set_none D (n - 1))).
           -- simpl. lia.
           -- exact Hb.
  - (* PPar：k位Some None线性分到一侧(持有,insert_none_remove_id+IH)，
          另一侧要么也是Some None(同法)、要么越界None(短上下文keep_free恒等)。
          存在论：并行的两侧各自撤除寂然之位，再于原世界D重新并起。 *)
    simpl.
    inversion Ht as [| | | | | G0 Pa Pb Ga Gb Hsp Ha Hb | |]; subst G0 Pa Pb.
    assert (Hsp0 := Hsp).
    apply (split_remove_none_both D k Ga Gb Hlen) in Hsp0.
    unfold split in Hsp. specialize (Hsp k).
    rewrite (get_insert_none_at_self k D Hlen) in Hsp.
    destruct Hsp as [[La Lb] | [Ra Rb]].
    + (* Ga 持有 k 位 Some None *)
      assert (KGa : k < length Ga) by (eapply get_Some_lt; exact La).
      assert (Ega : Ga = insert_none_at k (remove_at k Ga)).
      { apply insert_none_remove_id. exact La. }
      assert (HlenA : k <= length (remove_at k Ga)).
      { rewrite length_remove_at by lia. lia. }
      rewrite Ega in Ha.
      destruct Lb as [GbN | GbS].
      * (* Gb 越界 None：短上下文，代换恒等 *)
        assert (KGb : k >= length Gb) by (apply get_None_length; exact GbN).
        assert (Egb : remove_at k Gb = Gb) by (apply remove_at_ge_id; lia).
        eapply ty_par with (Gamma1 := remove_at k Ga) (Gamma2 := remove_at k Gb).
        -- exact Hsp0.
        -- exact (IHQ1 m k (remove_at k Ga) HlenA Ha).
        -- rewrite Egb. apply subst_var_keep_free with (k := k).
           ++ intros n T Hn Hc.
              assert (N : get Gb n = None) by exact (get_None_ge Gb k GbN n Hn).
              rewrite N in Hc. discriminate.
           ++ exact Hb.
      * (* Gb 也是 Some None：同持有侧 *)
        assert (KGb : k < length Gb) by (eapply get_Some_lt; exact GbS).
        assert (Egb : Gb = insert_none_at k (remove_at k Gb)).
        { apply insert_none_remove_id. exact GbS. }
        assert (HlenB : k <= length (remove_at k Gb)).
        { rewrite length_remove_at by lia. lia. }
        rewrite Egb in Hb.
        eapply ty_par with (Gamma1 := remove_at k Ga) (Gamma2 := remove_at k Gb).
        -- exact Hsp0.
        -- exact (IHQ1 m k (remove_at k Ga) HlenA Ha).
        -- exact (IHQ2 m k (remove_at k Gb) HlenB Hb).
    + (* Gb 持有 k 位 Some None（对称）：Ra 是 Gb 持有位，Rb 是 Ga 空侧析取 *)
      assert (KGb : k < length Gb) by (eapply get_Some_lt; exact Ra).
      assert (Egb : Gb = insert_none_at k (remove_at k Gb)).
      { apply insert_none_remove_id. exact Ra. }
      assert (HlenB : k <= length (remove_at k Gb)).
      { rewrite length_remove_at by lia. lia. }
      rewrite Egb in Hb.
      destruct Rb as [GaN | GaS].
      * (* Ga 越界 None *)
        assert (KGa : k >= length Ga) by (apply get_None_length; exact GaN).
        assert (Ega : remove_at k Ga = Ga) by (apply remove_at_ge_id; lia).
        eapply ty_par with (Gamma1 := remove_at k Ga) (Gamma2 := remove_at k Gb).
        -- exact Hsp0.
        -- rewrite Ega. apply subst_var_keep_free with (k := k).
           ++ intros n T Hn Hc.
              assert (N : get Ga n = None) by exact (get_None_ge Ga k GaN n Hn).
              rewrite N in Hc. discriminate.
           ++ exact Ha.
        -- exact (IHQ2 m k (remove_at k Gb) HlenB Hb).
      * (* Ga 也是 Some None *)
        assert (KGa : k < length Ga) by (eapply get_Some_lt; exact GaS).
        assert (Ega : Ga = insert_none_at k (remove_at k Ga)).
        { apply insert_none_remove_id. exact GaS. }
        assert (HlenA : k <= length (remove_at k Ga)).
        { rewrite length_remove_at by lia. lia. }
        rewrite Ega in Ha.
        eapply ty_par with (Gamma1 := remove_at k Ga) (Gamma2 := remove_at k Gb).
        -- exact Hsp0.
        -- exact (IHQ1 m k (remove_at k Ga) HlenA Ha).
        -- exact (IHQ2 m k (remove_at k Gb) HlenB Hb).
  - (* PRes *)
    simpl. apply res_elim in Ht. destruct Ht as [T0 H1].
    rewrite insert_none_at_cons_comm in H1.
    apply ty_res with (T := T0).
    apply (IHQ (S m) (S k) (Some T0 :: D)).
    + simpl. lia.
    + exact H1.
  - (* PRep *)
    simpl. inversion Ht; subst. apply ty_rep.
    apply subst_var_empty with (m := m) (k := k). exact H1.
Qed.

Lemma insert_pts_subst : forall Gamma T k m,
  k <= length Gamma -> get Gamma m = Some (Some T) ->
  forall n T', get (insert_at k T Gamma) n = Some (Some T') ->
               get Gamma (subst_name m k n) = Some (Some T').
Proof.
  intros Gamma T k m Hkle Hget n T' Hn.
  destruct (Nat.eq_dec n k) as [Heq | Hne].
  - subst n.
    rewrite (get_insert_at_self k T Gamma) in Hn.
    injection Hn as EQ. subst T'.
    rewrite (subst_name_eq m k k eq_refl). exact Hget.
  - destruct (Nat.ltb_spec n k) as [Hlt | Hge].
    + assert (Hn' : get Gamma n = Some (Some T')).
      { exact (get_insert_at_lt Gamma T k n T' Hlt Hn). }
      rewrite (subst_name_lt m k n Hlt).
      exact Hn'.
    + assert (Hgt : n > k) by lia.
      assert (Hn' : get Gamma (n - 1) = Some (Some T')).
      { exact (get_insert_at_gt Gamma T k n T' Hgt Hn). }
      rewrite (subst_name_gt m k n Hgt).
      exact Hn'.
Qed.
Lemma substitution_general : forall Gamma T k m Q,
  k <= length Gamma ->
  typed (insert_at k T Gamma) Q ->
  get Gamma m = Some (Some T) ->
  no_use_at_subst Q m k = true ->
  typed Gamma (subst_var m k Q).
Proof.
  intros Gamma T k m Q Hkle Ht Hget Hnu.
  rewrite (subst_var_eq_ren m k Q).
  apply (subst_ren_general (insert_at k T Gamma) Q Ht m k Gamma).
  - exact (insert_pts_subst Gamma T k m Hkle Hget).
  - exact Hnu.
Qed.
(* ===== congruence 辅助引理占位（规格据 S00 策略/r1；证明由聚焦闭环逐个补） ===== *)
Lemma get_setby_None_uncond : forall Gamma f k n,
  get Gamma n = None -> get (setby f Gamma k) n = None.
Proof.
  induction Gamma as [|u0 Gamma IH]; intros f k n Hn; simpl in *.
  - reflexivity.
  - destruct n as [|n].
    + simpl in Hn. discriminate.
    + apply IH with (f:=f) (k:=S k). exact Hn.
Qed.


Lemma get_repeat_None_lt : forall len n,
  n < len -> get (repeat (None : option ty) len) n = Some None.
Proof.
  intros len n. revert len. induction n; intros len Hlt.
  - destruct len; [lia|]. simpl. reflexivity.
  - destruct len; [lia|]. simpl. apply IHn. lia.
Qed.

Lemma length_repeat_None : forall len,
  length (repeat (None : option ty) len) = len.
Proof.
  induction len; simpl; auto.
Qed.

Lemma get_setby_None : forall Gamma f k n,
  get Gamma n = None -> get (setby f Gamma k) n = None.
Proof.
  induction Gamma as [|u0 Gamma IH]; intros f k n Hn; simpl in *.
  - reflexivity.
  - destruct n as [|n].
    + simpl in Hn. discriminate.
    + apply IH with (f:=f) (k:=S k). exact Hn.
Qed.


(* =====================================================================
   split_assoc（明性分划结合律）——为真路线的逐位准备事实
   曾被 DS v8 误判为假（交 split_assoc_false 反例），已被证伪双门
   falsification_guard 以 coqc 推翻：反例独立编译 exit=1（option 双层
   错层），反例参数下取 G23=[] 即使结论 Qed。见结晶016 与
   S04研判_split_assoc哲学命题与结晶贯穿核对_20260904。
   下列两个小引理是逐位归属的基础事实，不是反例。
   ===================================================================== *)

Lemma split_nil_nil_None_hold :
  split [] [] [None] /\ split [] [] [None].
Proof.
  split; unfold split; intros [|n]; simpl; auto.
Qed.

Lemma split_empty_None_None_false :
  ~ split [] [None] [None].
Proof.
  intros H. unfold split in H. specialize (H 0). simpl in H.
  destruct H as [[Hl _] | [Hr _]]; discriminate.
Qed.

(* H23_val：逐位构造中间场域 G23 的核心工具引理（为真路线）。
   存在论含义：G23 第 n 位 = G2 在该位有真实发用 Some(Some a) 则持之，
   否则承接 G3 该位（G3 越界的 None 在此补成在位空 Some None）。
   中间块不是现成实体，是"G2 优先、G3 兜底"逐位重新聚拢的产物，正是
   split_assoc 中 exists G23 的见证构造。空位形态可选、可收摄（结晶012：
   明性可不保持），故重组不被空位阻塞。 *)
Lemma H23_val : forall (G2 G3 : ctx) (f : nat -> option ty -> option ty) (max_len n : nat),
    n < max_len ->
    f = (fun (n:nat) (_:option ty) =>
           match get G2 n with
           | Some (Some a) => Some a
           | _ => match get G3 n with
                  | Some v => v
                  | None => None
                  end
           end) ->
    get (setby f (repeat (None:option ty) max_len) 0) n =
    match get G2 n with
    | Some (Some a) => Some (Some a)
    | _ => match get G3 n with
           | Some v => Some v
           | None => Some None
           end
    end.
Proof.
  intros G2 G3 f max_len n Hnlt Hf.
  rewrite Hf.
  assert (Hget : get (repeat (None : option ty) max_len) n = Some None).
  { apply get_repeat_None_lt. exact Hnlt. }
  rewrite (get_setby_get (repeat (None:option ty) max_len)
    (fun n _ => match get G2 n with
                | Some (Some a) => Some a
                | _ => match get G3 n with
                       | Some v => v
                       | None => None
                       end
                end) 0 n None Hget).
  replace (0 + n) with n by lia.
  destruct (get G2 n) as [[a|]|] eqn:EG2.
  - simpl. reflexivity.
  - destruct (get G3 n) as [[b|]|] eqn:EG3; simpl; reflexivity.
  - destruct (get G3 n) as [[b|]|] eqn:EG3; simpl; reflexivity.
Qed.

(* =====================================================================
   split_assoc —— 明性分划的结合律（Layer2 并行语义的地基）

   【大白话】一整片操作权场域 G 要分给三个并行生命过程 P/Q/R。可以先切
   (G1,G2)|G3（前提 split G G12 G3；再 split G12 G1 G2），也可以先切
   G1|(G2,G3)（结论 exists G23, split G G1 G23 且 split G23 G2 G3）。
   本定理断言：第一种切法做得到，第二种就一定做得到——中间块 G23 必能
   逐位重新聚拢，且两种切法下每份真实发用 Some(Some T) 归谁完全一致，
   与下刀次序、括号方式无关。

   【存在论命题】多者并行共在的客观性：多个生命同时发用、各据其明而互不
   夺资源，其合法性属于各自的发用与资源归属本身，不属于外部如何捆绑。
   中间聚合块可自由解散重组（寂然空位 None 越界 / Some None 在位二态在
   "无操作权流经"上等价、冗余明性可收摄），唯一被严格保持的是真实资源的
   逐位归属。这是 ty_par 可嵌套、并行成为良定义存在方式的前提；后续
   congruence/交换/一切多进程理论皆压于此。

   【为真路线】见证 G23 = setby f (repeat None L) 0，f 逐位 G2 优先、
   G3 兜底（工具引理 H23_val 已 Qed）；两个 split 皆逐位 unfold，按 get
   三态（None 越界 / Some None 在位空 / Some(Some T) 实有）分情况。

   【DS 误判的精确数学根因】把 G3=[] 越界的 None 与 G2=[None] 在位的
   Some None 错当同一层而要求相等（违反结晶010：跨上下文层比较先做层级
   核对）；取 G23=[] 让该位越界即消解。改判真假必过证伪双门（结晶016），
   coqc 是唯一终裁（结晶014）。

   证明由 DeepSeek 主谋闭环产出（结晶014：S04 不自写 tactic），当前保留
   Admitted 作为 Layer2 唯一待证目标。
   ===================================================================== *)
(* ============================================================
   split_assoc 完整证明（S04 手动例外，2026-09-15；独立范本 TEST_split.v
   已 coqc exit=0，Python 有限枚举 2383 可达实例 0 反例）。
   路线：merge_cell 逐位四规则 -> build_g23 从 k 起遇 None 截断地构造
   中间块 G23 -> build_correct 区间归纳（区间内用步长引理化归到 S k
   层、区间外结论本就是 None）-> 主定理按 n<K / n>=K 分情况。
   ============================================================ *)

(* 单个位置的三分划判据：a 持 g 而 b 空（越界 None 或在位空 Some None），
   或 b 持 g 而 a 空——正是 split 在某一位的展开 *)
Definition cell_split (g a b:option(option ty)):Prop :=
  (a=g/\(b=None\/b=Some None)) \/ (b=g/\(a=None\/a=Some None)).

(* 两个在位空位合并仍为在位空，其余归 None（merge_cell 的兜底） *)
Definition blank_merge (g2 g3:option(option ty)):option(option ty) :=
  match g2 with Some None=>Some None
  | _=> match g3 with Some None=>Some None | _=>None end end.

(* 逐位聚拢规则：G2/G3 任一侧有真实发用则持之；皆空时，若父越界且 G1
   在位空位则让位为越界 None，否则按在位空/越界收束。32 组合穷举 0 失败 *)
Definition merge_cell (g g1 g2 g3:option(option ty)):option(option ty) :=
  match g2 with
  | Some(Some a)=>Some(Some a)
  | _=> match g3 with
        | Some(Some b)=>Some(Some b)
        | _=> match g with
              | None=> match g1 with Some None=>None | _=>blank_merge g2 g3 end
              | _=>blank_merge g2 g3 end end end.

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
    apply split_get_l with (Gamma:=G12)(Gamma1:=G1)(Gamma2:=G2)(n:=n)(T:=x) in H2; [|exact E1].
    apply split_get_l with (Gamma:=G)(Gamma1:=G12)(Gamma2:=G3)(n:=n)(T:=x) in H1; [|exact H2]. congruence. }
  assert (b2: get G2 n=None\/get G2 n=Some None).
  { destruct (get G2 n) as [[x|]|] eqn:E2; auto; exfalso.
    apply split_get_r with (Gamma:=G12)(Gamma1:=G1)(Gamma2:=G2)(n:=n)(T:=x) in H2; [|exact E2].
    apply split_get_l with (Gamma:=G)(Gamma1:=G12)(Gamma2:=G3)(n:=n)(T:=x) in H1; [|exact H2]. congruence. }
  assert (b3: get G3 n=None\/get G3 n=Some None).
  { destruct (get G3 n) as [[x|]|] eqn:E3; auto; exfalso.
    apply split_get_r with (Gamma:=G)(Gamma1:=G12)(Gamma2:=G3)(n:=n)(T:=x) in H1; [|exact E3]. congruence. }
  auto.
Qed.

(* 从前缀 k 起可安全截断：merge 在 k 为 None，则 n>=k 用越界 None 两侧都成立 *)
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
  - assert (n2: get G2 n=None) by (apply get_none_overflow in E2k; apply get_overflow_none; lia).
    assert (n3: get G3 n=None) by (apply get_none_overflow in E3k; apply get_overflow_none; lia).
    split.
    + destruct c1 as [(a1&_)|(a2&ab12)], c2 as [(b1&_)|(b2&bb1)].
      * left; split; [exact (eq_trans b1 a1)|left; reflexivity].
      * right; split; [rewrite n2 in b2; rewrite <-b2 in a1; exact a1|exact bb1].
      * right; split; [rewrite n3 in a2; exact a2|rewrite b1; exact ab12].
      * right; split; [rewrite n3 in a2; exact a2|exact bb1].
    + left; split; [exact n2|left; exact n3].
  - assert (nG: get G n=None) by (apply get_none_overflow in EGk; apply get_overflow_none; lia).
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

(* 递归构造 G23：从 k 起、rem 位，遇 merge=None 即截断 *)
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

(* length(build_g23 k rem) <= rem；归纳下标递增，induction 前 revert k *)
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

(* 区间归纳：K=max(length G2,length G3)，B=build_g23 k rem（K=k+rem），
   区间内逐位 cell_split、区间外（n>=K）两侧皆 None *)
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
  - intros k Hk. split.
    + intros n hle hlt; exfalso; rewrite Hk in hlt; lia.
    + intros n hn. apply tail_past_K with (G:=G)(G12:=G12)(G3:=G3)(G1:=G1)(G2:=G2)(n:=n);
        auto; lia.
  - intros k Hk.
    destruct (IH (S k) ltac:(lia)) as [IHin IHout].
    destruct (merge_cell (get G k)(get G1 k)(get G2 k)(get G3 k)) as [v|] eqn:Em.
    + split.
      * intros n hle hlt.
        destruct (Nat.eq_dec n k) as [eq|ne].
        { subst n. replace (k-k) with 0 by lia.
          rewrite (step_head G G1 G2 G3 k rem' v Em).
          assert (cs:=cell_step (get G k)(get G12 k)(get G3 k)(get G1 k)(get G2 k)(H1 k)(H2 k)).
          rewrite Em in cs. exact cs. }
        { rewrite (step_some G G1 G2 G3 k rem' n v Em ltac:(lia)).
          apply IHin; lia. }
      * intros n hn. apply IHout; lia.
    + split.
      * intros n hle hlt. rewrite (step_none G G1 G2 G3 k rem' Em). cbn [get].
        apply trunc_tail with (G:=G)(G12:=G12)(G3:=G3)(G1:=G1)(G2:=G2)(k:=k);
          [exact H1|exact H2|exact Em|lia].
      * intros n hn. apply IHout; lia.
Qed.

Lemma split_assoc : forall G G12 G3 G1 G2,
  split G G12 G3 -> split G12 G1 G2 ->
  exists G23, split G G1 G23 /\ split G23 G2 G3.
Proof.
  intros G G12 G3 G1 G2 H1 H2.
  set (K:=max (length G2)(length G3)).
  assert (BC:=build_correct G G12 G3 G1 G2 K H1 H2 eq_refl 0 K ltac:(lia)).
  destruct BC as [inL outR].
  exists (build_g23 G G1 G2 G3 0 K). split.
  - intros n; unfold split; destruct (Nat.ltb n K) eqn:Lt.
    + apply Nat.ltb_lt in Lt.
      destruct (inL n (Nat.le_0_l n) Lt) as [c1 _].
      rewrite Nat.sub_0_r in c1; unfold cell_split in c1; exact c1.
    + apply Nat.ltb_ge in Lt.
      assert (ov: get (build_g23 G G1 G2 G3 0 K) n=None).
      { apply get_overflow_none. apply Nat.le_trans with (m:=K).
        apply length_build_le. exact Lt. }
      destruct (outR n Lt) as [o1 _]. unfold cell_split in o1. rewrite ov; exact o1.
  - intros n; unfold split; destruct (Nat.ltb n K) eqn:Lt.
    + apply Nat.ltb_lt in Lt.
      destruct (inL n (Nat.le_0_l n) Lt) as [_ c2].
      rewrite Nat.sub_0_r in c2; unfold cell_split in c2; exact c2.
    + apply Nat.ltb_ge in Lt.
      assert (ov: get (build_g23 G G1 G2 G3 0 K) n=None).
      { apply get_overflow_none. apply Nat.le_trans with (m:=K).
        apply length_build_le. exact Lt. }
      destruct (outR n Lt) as [_ o2]. unfold cell_split in o2. rewrite ov; exact o2.
Qed.
(* ---------------------------------------------------------------------
   10. Progress
   --------------------------------------------------------------------- *)

(* General progress theorem: every well-typed term is either a value or
   can reduce. This holds for ANY context, not just empty ones, because
   variables (PVar) and output prefixes (POut) are themselves values —
   they cannot reduce on their own, only in parallel with a matching
   input (red_comm, which is vacuous in our linear system). *)
Theorem progress_general : forall Gamma P,
  typed Gamma P -> is_value P \/ exists P', reduce P P'.
Proof.
  intros Gamma P H.
  induction H as [
    Gamma
    | Gamma x T Hget
    | Gamma P H IH
    | Gamma x y P i o T Gamma1 Gamma2 Huse1 Ho Huse2 H IH
    | Gamma x P i o T Gamma1 Huse Hi H IH
    | Gamma P Q Gamma1 Gamma2 Hs HP IHP HQ IHQ
    | Gamma P T H IH
    | Gamma P H IH
  ].
  - (* ty_zero *)
    left. apply val_zero.
  - (* ty_var *)
    left. apply val_var.
  - (* ty_tau *)
    right. exists P. apply red_tau.
  - (* ty_out *)
    left. apply val_out.
  - (* ty_in *)
    left. apply val_in.
  - (* ty_par *)
    destruct IHP as [Hv1 | [P' Hr1]].
    + (* P is value *)
      destruct IHQ as [Hv2 | [Q' Hr2]].
      * (* both are values *)
        left. apply val_par. exact Hv1. exact Hv2.
      * (* Q can reduce *)
        right. exists (PPar P Q'). apply red_par_r. exact Hr2.
    + (* P can reduce *)
      right. exists (PPar P' Q). apply red_par_l. exact Hr1.
  - (* ty_res *)
    destruct IH as [Hv | [P' Hr]].
    + left. apply val_res. exact Hv.
    + right. exists (PRes P'). apply red_res. exact Hr.
  - (* ty_rep *)
    left. apply val_rep.
Qed.

(* Progress for empty context is the special case of progress_general. *)
Theorem progress : forall P, typed [] P ->
  is_value P \/ exists P', reduce P P'.
Proof.
  intros P H. apply progress_general with (Gamma := []). exact H.
Qed.

(* =====================================================================
   LAYER 2 SUMMARY
   - Operational semantics: structural congruence + reduction relation
   - Substitution: subst_var, comm_subst (defined)
   - Subject Reduction: FULLY PROVED
     Core insight: red_comm is vacuously true because linear split
     prevents channel sharing between parallel components.
   - substitution_lemma, congruence_preserves_typing, progress:
     admitted for next iteration (standard technical lemmas)
   ===================================================================== *)


(* =====================================================================
   J3: typed_res_par_l/r —— 限制-并行交换下 typed 保持
   对应 cong_res_par: ~ fv_at Q 0 -> congruence (PRes (PPar P Q)) (PPar (PRes P) Q)
   ===================================================================== *)

(* weaken_none_head：上下文头位置为在位空位(None)时，替换为任意类型不影响类型化。
   存在论：头位置无操作权流经（明性收摄），填入新操作权不改变既有进程的类型结构。
   对typed归纳，8个case。ty_out/ty_par中split两侧头亦空，可分别弱化。
   ty_res中偏移到S 0，递归弱化。 *)
(* weaken_none_head：上下文头位置为在位空位(None)时，替换为任意类型不影响类型化。
   存在论：头位置无操作权流经（明性收摄），填入新操作权不改变既有进程的类型结构。
   证明路线：ren_typed 配恒等重命名 + ren_id；不重证 typed 归纳。 *)
(* weaken_none_head：上下文头位置为在位空位(None)时，替换为任意类型不影响类型化。
   存在论：头位置无操作权流经（明性收摄），填入新操作权不改变既有进程的类型结构。
   证明路线：ren_typed 配恒等重命名；恒等重命名引理在证明内部完成，避免引用后置的 ren_id。 *)
Lemma weaken_none_head : forall Gamma' P T,
  typed (None :: Gamma') P -> typed (Some T :: Gamma') P.
Proof.
  intros Gamma' P T H.
  assert (Hid : ren (fun n : nat => n) P = P).
  {
    clear H T.
    induction P as [n | | P IH | x y P IH | x P IH | P IH Q IHQ | P IH | P IH].
    - simpl. reflexivity.                                  (* PVar *)
    - simpl. reflexivity.                                  (* PZero *)
    - simpl. rewrite IH. reflexivity.                      (* PTau *)
    - simpl. rewrite IH. reflexivity.                      (* POut *)
    - simpl.                                               (* PIn *)
      assert (Hup : ren (upren (fun n : nat => n)) P = ren (fun n : nat => n) P).
      { apply ren_ext. intros [|q]; reflexivity. }
      rewrite Hup. rewrite IH. reflexivity.
    - simpl. rewrite IH. rewrite IHQ. reflexivity.        (* PPar *)
    - simpl.                                               (* PRes *)
      assert (Hup : ren (upren (fun n : nat => n)) P = ren (fun n : nat => n) P).
      { apply ren_ext. intros [|q]; reflexivity. }
      rewrite Hup. rewrite IH. reflexivity.
    - simpl. rewrite IH. reflexivity.                      (* PRep *)
  }
  assert (Hinj : forall n m, has (None :: Gamma') n -> has (None :: Gamma') m ->
                (fun n : nat => n) n = (fun n : nat => n) m -> n = m).
  { intros n m Hn Hm E. exact E. }
  assert (Hpts : forall n T', get (None :: Gamma') n = Some (Some T') ->
                 get (Some T :: Gamma') ((fun n : nat => n) n) = Some (Some T')).
  {
    intros n T' Hg.
    destruct n as [|n].
    + simpl in Hg. discriminate.
    + exact Hg.
  }
  pose proof (ren_typed (None :: Gamma') P H (fun n : nat => n)
                (Some T :: Gamma') Hinj Hpts) as Hr.
  rewrite Hid in Hr.
  exact Hr.
Qed.
(* weaken_nil：空上下文中类型化的进程，在单元素上下文中仍类型化。
   空上下文无任何资源可用，填入头不影响。是weaken_none_head的越界版。 *)

Lemma upren_id_pt : forall n, upren (fun n : nat => n) n = n.
Proof.
  intros [|n]; reflexivity.
Qed.

Lemma ren_id : forall P, ren (fun n : nat => n) P = P.
Proof.
  induction P as [n | | P IH | x y P IH | x P IH | P IH Q IHQ | P IH | P IH].
  - simpl. reflexivity. (* PVar *)
  - simpl. reflexivity. (* PZero *)
  - simpl. rewrite IH. reflexivity. (* PTau *)
  - simpl. rewrite IH. reflexivity. (* POut *)
  - simpl. (* PIn *)
    assert (Hup : ren (upren (fun n : nat => n)) P = ren (fun n : nat => n) P).
    { apply ren_ext. intro q. apply upren_id_pt. }
    rewrite Hup. rewrite IH. reflexivity.
  - simpl. rewrite IH. rewrite IHQ. reflexivity. (* PPar *)
  - simpl. (* PRes *)
    assert (Hup : ren (upren (fun n : nat => n)) P = ren (fun n : nat => n) P).
    { apply ren_ext. intro q. apply upren_id_pt. }
    rewrite Hup. rewrite IH. reflexivity.
  - simpl. rewrite IH. reflexivity. (* PRep *)
Qed.

Lemma weaken_nil : forall P T, typed [] P -> typed [Some T] P.
Proof.
  intros P T H.
  assert (Hinj : forall n m, has [] n -> has [] m ->
    (fun n : nat => n) n = (fun n : nat => n) m -> n = m).
  { intros n m Hn Hm E. destruct Hn as [T' Hget]. simpl in Hget. discriminate. }
  assert (Hpts : forall n T', get [] n = Some (Some T') ->
    get [Some T] ((fun n : nat => n) n) = Some (Some T')).
  { intros n T' Hn. simpl in Hn. discriminate. }
  pose proof (ren_typed [] P H (fun n : nat => n) [Some T] Hinj Hpts) as Hr.
  rewrite ren_id in Hr.
  exact Hr.
Qed.
(* typed_any_ctx：空上下文可类型化的进程可在任意上下文中类型化。
   原陈述~fv_at P 0 -> typed Gamma P为假（OB-017反例PRes(POut 0 0 PZero)），
   修正为typed [] P -> typed Gamma P（同时要求闭合+内部线性良序）。
   证明照抄weaken_nil，用ren_typed把空上下文重命名到任意Gamma。 *)
Lemma typed_any_ctx : forall P Gamma, typed [] P -> typed Gamma P.
Proof.
  intros P Gamma H.
  assert (Hinj : forall n m, has [] n -> has [] m ->
    (fun n : nat => n) n = (fun n : nat => n) m -> n = m).
  { intros n m Hn Hm E. destruct Hn as [T' Hget]. simpl in Hget. discriminate. }
  assert (Hpts : forall n T', get [] n = Some (Some T') ->
    get Gamma ((fun n : nat => n) n) = Some (Some T')).
  { intros n T' Hn. simpl in Hn. discriminate. }
  pose proof (ren_typed [] P H (fun n : nat => n) Gamma Hinj Hpts) as Hr.
  rewrite ren_id in Hr.
  exact Hr.
Qed.

(* =====================================================================
   typed_res_par_l：限制-并行交换下 typed 保持
   ===================================================================== *)

(* 辅助引理：~fv_at P u 蕴含 not_free_in P u = true。
   操作论：进程在位置 u 没有自由引用，u 位可收摄。 *)
Lemma not_free_in_fv : forall P u, ~ fv_at P u -> not_free_in P u = true.
Proof.
  induction P as [n| | P IH | x y P IH | x P IH | P IHP Q IHQ | P IH | P IH];
    intros u H; simpl.
  - apply Bool.negb_true_iff. apply Nat.eqb_neq. intro E.
    apply H. subst n. simpl; apply Nat.le_refl.
  - reflexivity.
  - apply IH. intro F. apply H. exact F.
  - apply Bool.andb_true_iff. split.
    + apply Bool.andb_true_iff. split.
      * apply Bool.negb_true_iff. apply Nat.eqb_neq. intro E.
        apply H. left. subst x. simpl; apply Nat.le_refl.
      * apply Bool.negb_true_iff. apply Nat.eqb_neq. intro E.
        apply H. right. left. subst y. simpl; apply Nat.le_refl.
    + apply IH. intro F. apply H. right. right. exact F.
  - apply Bool.andb_true_iff. split.
    + apply Bool.negb_true_iff. apply Nat.eqb_neq. intro E.
      apply H. left. subst x. simpl; apply Nat.le_refl.
    + apply IH. intro F. apply H. right. exact F.
  - apply Bool.andb_true_iff. split.
    + apply IHP. intro F. apply H. left. exact F.
    + apply IHQ. intro F. apply H. right. exact F.
  - apply IH. intro F. apply H. exact F.
  - apply IH. intro F. apply H. exact F.
Qed.

(* 辅助引理：~fv_at P k 时，subst_var m k P = P。
   拓扑论：没有自由穿越 k 位的引用，代换不改变进程。 *)
Lemma subst_var_id_fv_closed : forall m k P, ~ fv_at P k -> subst_var m k P = P.
Proof.
  intros m k P; revert m k.
  induction P as [n| | P IH | x y P IH | x P IH | P IHP Q IHQ | P IH | P IH];
    intros m k H; simpl.
  - assert (Hlt : n < k).
    { destruct (Nat.ltb n k) eqn:E.
      - apply Nat.ltb_lt; exact E.
      - apply Nat.ltb_ge in E. exfalso. apply H. exact E. }
    rewrite (subst_name_lt m k n Hlt). reflexivity.
  - reflexivity.
  - f_equal. apply IH. intro F. apply H. exact F.
  - assert (Hx : x < k).
    { destruct (Nat.ltb x k) eqn:E.
      - apply Nat.ltb_lt; exact E.
      - apply Nat.ltb_ge in E. exfalso. apply H. left. exact E. }
    assert (Hy : y < k).
    { destruct (Nat.ltb y k) eqn:E.
      - apply Nat.ltb_lt; exact E.
      - apply Nat.ltb_ge in E. exfalso. apply H. right. left. exact E. }
    f_equal.
    + rewrite (subst_name_lt m k x Hx); reflexivity.
    + rewrite (subst_name_lt m k y Hy); reflexivity.
    + apply IH. intro F. apply H. right. right. exact F.
  - assert (Hx : x < k).
    { destruct (Nat.ltb x k) eqn:E.
      - apply Nat.ltb_lt; exact E.
      - apply Nat.ltb_ge in E. exfalso. apply H. left. exact E. }
    f_equal.
    + rewrite (subst_name_lt m k x Hx); reflexivity.
    + apply (IH (S m) (S k)). intro F. apply H. right. exact F.
  - f_equal.
    + apply IHP. intro F. apply H. left. exact F.
    + apply IHQ. intro F. apply H. right. exact F.
  - f_equal. apply (IH (S m) (S k)). intro F. apply H. exact F.
  - f_equal. apply IH. intro F. apply H. exact F.
Qed.

(* REPLACE: Lemma typed_res_par_l ... Admitted. *)
Lemma typed_res_par_l : forall Gamma P Q, ~ fv_at Q 0 ->
  typed Gamma (PRes (PPar P Q)) -> typed Gamma (PPar (PRes P) Q).
Proof.
  intros Gamma P Q Hclosed Hty.
  (* PRes：反转取得内部 PPar 的类型化前提 *)
  inversion Hty as [?|? ? ? ?|? ? ?|? ? ? ? ? ? ? ? ? ? ? ? ?|
                    ? ? ? ? ? ? ? ? ? ?|? ? ? ? ? ? ? ?|? ? T Hpar|? ? ?]; subst.
  (* PPar：反转取得 split 与两侧类型化；直接构造子反演，不经过 exists 的 par_elim *)
  inversion Hpar as [?|? ? ? ?|? ? ?|? ? ? ? ? ? ? ? ? ? ? ? ?|
                     ? ? ? ? ? ? ? ? ? ?|G0 P0 Q0 G1 G2 Hs HP HQ|? ?|? ? ?]; subst.

  assert (Hs' : split Gamma (remove_at 0 G1) (remove_at 0 G2)).
  {
    apply (split_remove_at_both Gamma T 0 G1 G2).
    - lia.
    - exact Hs.
  }

  assert (HPres : typed (remove_at 0 G1) (PRes P)).
  {
    destruct G1 as [|g1 G1tail].
    - (* G1 为空：P 可在空上下文类型化；加回一个悬空头 *)
      apply (ty_res [] P TUnit).
      apply (weaken_nil P TUnit). exact HP.
    - destruct g1 as [Tg|].
      + (* 头位置原本持 Tg：PRes P 继续借用 Tg *)
        apply (ty_res G1tail P Tg). exact HP.
      + (* 头位置原本为在位空：可任意填类型，这里填 TUnit *)
        apply (ty_res G1tail P TUnit).
        apply (weaken_none_head G1tail P TUnit). exact HP.
  }

  assert (HQ' : typed (remove_at 0 G2) Q).
  {
    destruct G2 as [|g2 G2tail].
    - (* G2 为空：Q 原本就在空上下文类型化，remove_at 0 [] = [] *)
      exact HQ.
    - destruct g2 as [Tg|].
      + (* 头位置持 Tg：由于 Q 不引用位置 0，可先收摄该头，再撤除 *)
        assert (Hnf : not_free_in Q 0 = true) by
          (apply (not_free_in_fv Q 0); exact Hclosed).
        pose proof (typed_strengthen_unused (Some Tg :: G2tail) Q 0 HQ Hnf) as HQs.
        assert (Hin : typed (insert_none_at 0 G2tail) Q) by
          (simpl in HQs; exact HQs).
        assert (HLen : 0 <= length G2tail) by lia.
        pose proof (substitution_none_strengthen G2tail 0 0 Q HLen Hin) as Hsub.
        rewrite (subst_var_id_fv_closed 0 0 Q Hclosed) in Hsub.
        exact Hsub.
      + (* 头位置原来就是在位空：直接撤除 *)
        assert (Hin : typed (insert_none_at 0 G2tail) Q) by
          (simpl; exact HQ).
        assert (HLen : 0 <= length G2tail) by lia.
        pose proof (substitution_none_strengthen G2tail 0 0 Q HLen Hin) as Hsub.
        rewrite (subst_var_id_fv_closed 0 0 Q Hclosed) in Hsub.
        exact Hsub.
  }

  apply (ty_par Gamma (PRes P) Q (remove_at 0 G1) (remove_at 0 G2)
            Hs' HPres HQ').
Qed.
(* END REPLACE *)
(* REPLACE: Lemma typed_res_par_r ... Admitted. *)
(* 辅助：右侧整体加一个空位 None，保持 split。
   存在论：在并行右侧前缀一个寂然空位，整体与左侧同步前插 Some T，
   操作权逐位后移一位，资源归属不变。 *)
Lemma split_cons_l_cons_none_r : forall Gamma Gamma1 Gamma2 T,
  split Gamma Gamma1 Gamma2 ->
  split (Some T :: Gamma) (Some T :: Gamma1) (None :: Gamma2).
Proof.
  intros Gamma Gamma1 Gamma2 T Hsplit.
  unfold split.
  intros [|n].
  - left. split; [reflexivity | right; reflexivity].
  - simpl.
    unfold split in Hsplit.
    specialize (Hsplit n).
    destruct Hsplit as [[H1 H2] | [H1 H2]].
    + left. split; [exact H1 | exact H2].
    + right. split; [exact H1 | exact H2].
Qed.

(* 辅助：闭进程在任意可类型化上下文中，可把整个上下文收摄删除到空。
   步骤：头位资源 set_none 为空 -> 用 substitution_none_strengthen 削掉
   头部 None -> 闭性让 subst_var 恒等 -> 递归处理尾巴。 *)
Lemma typed_closed_to_empty : forall G Q,
  ~ fv_at Q 0 -> typed G Q -> typed [] Q.
Proof.
  intros G. induction G as [|g G' IHG]; intros Q Hcl Hty.
  - exact Hty.
  - assert (Hnf : not_free_in Q 0 = true).
    { apply not_free_in_fv. exact Hcl. }
    assert (Hty' : typed (None :: G') Q).
    { exact (typed_strengthen_unused (g :: G') Q 0 Hty Hnf). }
    assert (Hlen : 0 <= length G') by lia.
    pose proof (substitution_none_strengthen G' 0 0 Q Hlen Hty') as Hsub.
    rewrite (subst_var_id_fv_closed 0 0 Q Hcl) in Hsub.
    apply (IHG Q Hcl Hsub).
Qed.

(* REPLACE: Lemma typed_res_par_r ... Admitted. *)
(* =====================================================================
   typed_res_par_r（限制-并行交换的逆向方向）
   ===================================================================== *)

(* 在位置 k 处插入一个空槽：k 之前的名字不变，k 及之后的名字整体后移一位。
   存在论：进入绑定器后，所有自由名字坐标上抬；没有自由穿越 k 的引用时，
   这个移位对进程是恒等。 *)


(* 若进程在 k 及其以上没有自由变量，则 shift_at k 的重命名不改变进程。
   存在论：操作权不流经的坐标，整体穿入一个空槽位，进程纹丝不动。 *)

(* 闭进程 Q 的类型化可以在头部添加一个死槽 None。
   存在论：Q 没有任何自由操作权穿越 0 位，故在 0 位加一个空无不改变其类型结构。 *)

(* 若 split Gamma D1 D2，则在头部加资源 T 给 D1、给 D2 加空槽后仍 split。 *)

(* REPLACE: Lemma typed_res_par_r ... Admitted. *)
(* REPLACE: Lemma ren_shift_at_fv_id ... Qed. *)

(* END REPLACE *)

(* REPLACE: from "Definition shift_at" down to "Qed." of typed_res_par_r *)
Definition shift_at (k n : nat) : nat :=
  if n <? k then n else S n.

Lemma upren_shift_at : forall k n,
  upren (shift_at k) n = shift_at (S k) n.
Proof.
  intros k n. unfold upren, shift_at.
  destruct n as [|n'].
  - destruct (0 <? S k) eqn:E; [reflexivity |].
    apply Nat.ltb_ge in E. lia.
  - simpl.
    destruct (n' <? k) eqn:E.
    + assert (F : S n' <? S k = true).
      { apply Nat.ltb_lt. apply Nat.ltb_lt in E. lia. }
      rewrite F. reflexivity.
    + assert (F : S n' <? S k = false).
      { apply Nat.ltb_ge. apply Nat.ltb_ge in E. lia. }
      rewrite F. reflexivity.
Qed.

Lemma shift_at_0_S : forall n, shift_at 0 n = S n.
Proof.
  intros n. unfold shift_at.
  destruct (n <? 0) eqn:E.
  - apply Nat.ltb_lt in E. lia.
  - reflexivity.
Qed.

Lemma ren_shift_at_fv_id : forall P k, ~ fv_at P k -> ren (shift_at k) P = P.
Proof.
  induction P as [n | | P IHP | x y P IHP | x P IHP | P IHP Q IHQ | P IHP | P IHP];
    intros k H.
  - (* PVar n *)
    simpl. unfold shift_at.
    destruct (n <? k) eqn:E.
    + reflexivity.
    + apply Nat.ltb_ge in E. exfalso. apply H. simpl. exact E.
  - (* PZero *)
    simpl. reflexivity.
  - (* PTau *)
    simpl. f_equal. apply IHP. intro F. apply H. simpl. exact F.
  - (* POut x y P *)
    simpl.
    assert (Hx : x < k). {
      destruct (x <? k) eqn:E.
      - apply Nat.ltb_lt; exact E.
      - apply Nat.ltb_ge in E. exfalso. apply H. left. exact E.
    }
    assert (Hy : y < k). {
      destruct (y <? k) eqn:E.
      - apply Nat.ltb_lt; exact E.
      - apply Nat.ltb_ge in E. exfalso. apply H. right. left. exact E.
    }
    f_equal.
    + unfold shift_at. destruct (x <? k) eqn:E; [reflexivity | apply Nat.ltb_ge in E; lia].
    + unfold shift_at. destruct (y <? k) eqn:E; [reflexivity | apply Nat.ltb_ge in E; lia].
    + apply IHP. intro F. apply H. right. right. exact F.
  - (* PIn x P *)
    simpl.
    assert (Hx : x < k). {
      destruct (x <? k) eqn:E.
      - apply Nat.ltb_lt; exact E.
      - apply Nat.ltb_ge in E. exfalso. apply H. left. exact E.
    }
    f_equal.
    + unfold shift_at. destruct (x <? k) eqn:E; [reflexivity | apply Nat.ltb_ge in E; lia].
    + assert (HPbody : ~ fv_at P (S k)).
      { intro F. apply H. right. exact F. }
      assert (Hstep : ren (upren (shift_at k)) P = ren (shift_at (S k)) P).
      { apply ren_ext. intros q. apply upren_shift_at. }
      rewrite Hstep.
      apply IHP. exact HPbody.
  - (* PPar P Q *)
    simpl. f_equal.
    + apply IHP. intro F. apply H. left. exact F.
    + apply IHQ. intro F. apply H. right. exact F.
  - (* PRes P *)
    simpl. f_equal.
    assert (HPbody : ~ fv_at P (S k)).
    { intro F. apply H. simpl. exact F. }
    assert (Hstep : ren (upren (shift_at k)) P = ren (shift_at (S k)) P).
    { apply ren_ext. intros q. apply upren_shift_at. }
    rewrite Hstep.
    apply IHP. exact HPbody.
  - (* PRep P *)
    simpl. f_equal. apply IHP. intro F. apply H. simpl. exact F.
Qed.

Lemma typed_closed_shift_none : forall D Q,
  ~ fv_at Q 0 -> typed D Q -> typed (None :: D) Q.
Proof.
  intros D Q Hcl Hty.
  assert (Hren : ren (shift_at 0) Q = Q)
    by (apply ren_shift_at_fv_id; exact Hcl).
  assert (Hinj : forall n m, has D n -> has D m ->
           shift_at 0 n = shift_at 0 m -> n = m).
  { intros n m Hn Hm E.
    rewrite shift_at_0_S in E.
    injection E as E.
    exact E. }
  assert (Hpts : forall n T', get D n = Some (Some T') ->
           get (None :: D) (shift_at 0 n) = Some (Some T')).
  { intros n T' Hget. rewrite shift_at_0_S. simpl. exact Hget. }
  pose proof (ren_typed D Q Hty (shift_at 0) (None :: D) Hinj Hpts) as Hr.
  rewrite Hren in Hr.
  exact Hr.
Qed.

Lemma split_cons_none : forall Gamma D1 D2 T,
  split Gamma D1 D2 -> split (Some T :: Gamma) (Some T :: D1) (None :: D2).
Proof.
  intros Gamma D1 D2 T Hs.
  unfold split. intros [|n].
  - left. split; [reflexivity | right; reflexivity].
  - unfold split in Hs. specialize (Hs n).
    destruct Hs as [[H1 H2] | [H1 H2]].
    + left. split; [simpl; exact H1 | simpl; exact H2].
    + right. split; [simpl; exact H1 | simpl; exact H2].
Qed.

Lemma typed_res_par_r : forall Gamma P Q, ~ fv_at Q 0 ->
  typed Gamma (PPar (PRes P) Q) -> typed Gamma (PRes (PPar P Q)).
Proof.
  intros Gamma P Q Hclosed Hty.
  destruct (par_elim Gamma (PRes P) Q Hty) as [D1 [D2 [Hs [HPres HQ]]]].
  destruct (res_elim D1 P HPres) as [T HP].
  assert (Hs' : split (Some T :: Gamma) (Some T :: D1) (None :: D2))
    by (apply split_cons_none; exact Hs).
  assert (HQ' : typed (None :: D2) Q)
    by (apply typed_closed_shift_none; assumption).
  apply (ty_res Gamma (PPar P Q) T).
  eapply ty_par with (Gamma1 := Some T :: D1) (Gamma2 := None :: D2).
  - exact Hs'.
  - exact HP.
  - exact HQ'.
Qed.
(* END REPLACE *)

(* =====================================================================
   J1 · congruence_preserves_typing
   新增辅助：并行的左合并升降（typed_split_weaken_l）与单侧 set_none 分裂保持
   ===================================================================== *)



(* =====================================================================
   J1 · congruence_preserves_typing
   新增辅助：并行的左合并升降（typed_split_weaken_l）与单侧 set_none 分裂保持
   ===================================================================== *)

Lemma split_self_nil : forall Gamma, split Gamma Gamma [].
Proof.
  intros Gamma n. left. split.
  - reflexivity.
  - left. reflexivity.
Qed.

Lemma split_set_none_l_some : forall G G1 G2 x T,
  split G G1 G2 -> get G1 x = Some (Some T) ->
  split (set_none G x) (set_none G1 x) G2.
Proof.
  intros G G1 G2 x T Hs Hx.
  unfold split. intros n.
  unfold split in Hs.
  destruct (Nat.eq_dec n x) as [EQ | NEQ].
  - subst n.
    specialize (Hs x).
    destruct Hs as [[Hg Hempty] | [Hg2 H1empty]].
    + left. split.
      * apply (set_none_eq_at_self G1 G x Hg).
      * exact Hempty.
    + exfalso.
      destruct H1empty as [Hnone | Hsome];
        [rewrite Hnone in Hx; discriminate | rewrite Hsome in Hx; discriminate].
  - rewrite (set_none_neq G x n NEQ).
    rewrite (set_none_neq G1 x n NEQ).
    exact (Hs n).
Qed.

Lemma typed_split_weaken_l : forall G1 P,
  typed G1 P -> forall G G2, split G G1 G2 -> typed G P.
Proof.
  intros G1 P Hty.
  induction Hty as [
    Gamma
  | Gamma x T Hget
  | Gamma P0 Ht IH
  | Gamma x y P0 i o T G1a G1b Huse1 Ho Huse2 Hbody IHbody
  | Gamma x P0 i o T G1a Huse Hi Hbody IHbody
  | Gamma P0 Q0 G1a G1b Hs HP IHP HQ IHQ
  | Gamma P0 T Hbody IHbody
  | Gamma P0 Hempty
  ];
  intros G G2 Hsp.
  - (* ty_zero *)
    apply ty_zero.
  - (* ty_var *)
    apply ty_var with (T := T).
    eapply split_get_l; [exact Hsp | exact Hget].
  - (* ty_tau *)
    apply ty_tau.
    apply (IH G G2 Hsp).
  - (* ty_out *)
    assert (Hxy : x <> y) by (eapply use_neq; eassumption).
    assert (Hyx : y <> x) by (intro E; apply Hxy; symmetry; exact E).
    unfold use in Huse1, Huse2.
    destruct Huse1 as [Hg1x HA].
    destruct Huse2 as [HgAy HB].
    subst G1a. subst G1b.
    assert (Hgx : get G x = Some (Some (TChan i o T))).
    { eapply split_get_l; [exact Hsp | exact Hg1x]. }
    assert (Hs1 : split (set_none G x) (set_none Gamma x) G2).
    { apply (split_set_none_l_some G Gamma G2 x (TChan i o T) Hsp Hg1x). }
    assert (HgyG : get G y = Some (Some T)).
    { rewrite (set_none_neq Gamma x y Hyx) in HgAy.
      eapply split_get_l; [exact Hsp | exact HgAy]. }
    assert (Hgy : get (set_none G x) y = Some (Some T)).
    { rewrite (set_none_neq G x y Hyx). exact HgyG. }
    assert (Hs2 : split (set_none (set_none G x) y)
                        (set_none (set_none Gamma x) y) G2).
    { apply (split_set_none_l_some (set_none G x) (set_none Gamma x) G2 y T Hs1 HgAy). }
    eapply ty_out with (Gamma1 := set_none G x)
                       (Gamma2 := set_none (set_none G x) y).
    + unfold use. split; [exact Hgx | reflexivity].
    + exact Ho.
    + unfold use. split; [exact Hgy | reflexivity].
    + exact (IHbody (set_none (set_none G x) y) G2 Hs2).
  - (* ty_in *)
    unfold use in Huse. destruct Huse as [Hgx HA]. subst G1a.
    assert (HgG : get G x = Some (Some (TChan i o T))).
    { eapply split_get_l; [exact Hsp | exact Hgx]. }
    assert (Hs1 : split (set_none G x) (set_none Gamma x) G2).
    { apply (split_set_none_l_some G Gamma G2 x (TChan i o T) Hsp Hgx). }
    assert (Hcons : split (Some T :: set_none G x)
                          (Some T :: set_none Gamma x) (None :: G2)).
    { apply (split_cons_none (set_none G x) (set_none Gamma x) G2 T Hs1). }
    eapply ty_in with (Gamma1 := set_none G x).
    + unfold use. split; [exact HgG | reflexivity].
    + exact Hi.
    + exact (IHbody (Some T :: set_none G x) (None :: G2) Hcons).
  - (* ty_par *)
    destruct (split_assoc G Gamma G2 G1a G1b Hsp Hs) as [X [HX1 HX2]].
    eapply ty_par with (Gamma1 := G1a) (Gamma2 := X).
    + exact HX1.
    + exact HP.
    + apply (IHQ X G2 HX2).
  - (* ty_res *)
    assert (Hcons : split (Some T :: G) (Some T :: Gamma) (None :: G2)).
    { apply (split_cons_none G Gamma G2 T Hsp). }
    apply (ty_res G P0 T).
    exact (IHbody (Some T :: G) (None :: G2) Hcons).
  - (* ty_rep *)
    apply (ty_rep G P0 Hempty).
Qed.

(* =====================================================================
   成对加强归纳：congruence 正反两方向同时保持 typed
   ===================================================================== *)
Lemma congruence_preserves_typing_pair : forall Gamma P P',
  congruence P P' ->
  (typed Gamma P -> typed Gamma P') /\ (typed Gamma P' -> typed Gamma P).
Proof.
  intros Gamma P P' H.
  revert Gamma.
  induction H as
    [ P
    | P Q H0 IH0
    | P Q R H0 IH0 H1 IH1
    | P Q
    | P Q R
    | P
    | P Q Hnf
    | P
    | P P' Q Q' H0 IH0 H1 IH1
    | P P' H0 IH0
    | P P' H0 IH0 ];
  intros Gamma.
  - (* cong_refl *)
    split; intros Hty; exact Hty.
  - (* cong_sym *)
    destruct (IH0 Gamma) as [IHf IHb].
    split; [exact IHb | exact IHf].
  - (* cong_trans *)
    destruct (IH0 Gamma) as [IHf0 IHb0].
    destruct (IH1 Gamma) as [IHf1 IHb1].
    split.
    + intros HP_. apply IHf1. apply IHf0. exact HP_.
    + intros HR_. apply IHb0. apply IHb1. exact HR_.
  - (* cong_par_comm *)
    split.
    + intros Hty.
      destruct (par_elim Gamma P Q Hty) as [G1 [G2 [Hs [HP HQ]]]].
      eapply ty_par with (Gamma1 := G2) (Gamma2 := G1).
      * apply split_sym. exact Hs.
      * exact HQ.
      * exact HP.
    + intros Hty.
      destruct (par_elim Gamma Q P Hty) as [G1 [G2 [Hs [HQ HP]]]].
      eapply ty_par with (Gamma1 := G2) (Gamma2 := G1).
      * apply split_sym. exact Hs.
      * exact HP.
      * exact HQ.
  - (* cong_par_assoc *)
    split.
    + intros Hty.
      destruct (par_elim Gamma (PPar P Q) R Hty) as [G12 [G3 [Hs13 [HPQ HR]]]].
      destruct (par_elim G12 P Q HPQ) as [G1 [G2 [Hs12 [HP HQ]]]].
      destruct (split_assoc Gamma G12 G3 G1 G2 Hs13 Hs12) as [G23 [HsL HsR]].
      eapply ty_par with (Gamma1 := G1) (Gamma2 := G23).
      * exact HsL.
      * exact HP.
      * eapply ty_par with (Gamma1 := G2) (Gamma2 := G3).
        -- exact HsR.
        -- exact HQ.
        -- exact HR.
    + intros Hty.
      destruct (par_elim Gamma P (PPar Q R) Hty) as [G1 [G23 [HsL [HP HQR]]]].
      destruct (par_elim G23 Q R HQR) as [G2 [G3 [HsR [HQ HR]]]].
      pose proof (split_sym Gamma G1 G23 HsL) as HsL_sym.
      pose proof (split_sym G23 G2 G3 HsR) as HsR_sym.
      destruct (split_assoc Gamma G23 G1 G3 G2 HsL_sym HsR_sym) as [G12 [Ha Hb]].
      assert (Hb_sym : split G12 G1 G2) by (apply split_sym; exact Hb).
      assert (Ha_sym : split Gamma G12 G3) by (apply split_sym; exact Ha).
      eapply ty_par with (Gamma1 := G12) (Gamma2 := G3).
      * exact Ha_sym.
      * apply (ty_par G12 P Q G1 G2 Hb_sym HP HQ).
      * exact HR.
  - (* cong_par_zero *)
    split.
    + intros Hty.
      destruct (par_elim Gamma P PZero Hty) as [G1 [G2 [Hs [HP _]]]].
      exact (typed_split_weaken_l G1 P HP Gamma G2 Hs).
    + intros Hty.
      assert (Hs : split Gamma Gamma []) by (apply split_self_nil).
      eapply ty_par with (Gamma1 := Gamma) (Gamma2 := []).
      * exact Hs.
      * exact Hty.
      * apply ty_zero.
  - (* cong_res_par *)
    split; intros Hty.
    + exact (typed_res_par_l Gamma P Q Hnf Hty).
    + exact (typed_res_par_r Gamma P Q Hnf Hty).
  - (* cong_rep_unfold *)
    split.
    + intros Hty.
      assert (Hempty : typed [] P).
      { inversion Hty; subst. eassumption. }
      assert (Hs : split Gamma Gamma []) by (apply split_self_nil).
      eapply ty_par with (Gamma1 := Gamma) (Gamma2 := []).
      * exact Hs.
      * apply (typed_any_ctx P Gamma Hempty).
      * apply (ty_rep [] P Hempty).
    + intros Hty.
      destruct (par_elim Gamma P (PRep P) Hty) as [G1 [G2 [Hs [HP HQ]]]].
      assert (Hempty : typed [] P).
      { inversion HQ; subst. eassumption. }
      apply (ty_rep Gamma P Hempty).
  - (* cong_par_cong *)
    split.
    + intros Hty.
      destruct (par_elim Gamma P Q Hty) as [G1 [G2 [Hs [HP HQ]]]].
      destruct (IH0 G1) as [IH0fG1 _].
      destruct (IH1 G2) as [IH1fG2 _].
      eapply ty_par with (Gamma1 := G1) (Gamma2 := G2).
      * exact Hs.
      * apply IH0fG1. exact HP.
      * apply IH1fG2. exact HQ.
    + intros Hty.
      destruct (par_elim Gamma P' Q' Hty) as [G1 [G2 [Hs [HP' HQ']]]].
      destruct (IH0 G1) as [_ IH0bG1].
      destruct (IH1 G2) as [_ IH1bG2].
      eapply ty_par with (Gamma1 := G1) (Gamma2 := G2).
      * exact Hs.
      * apply IH0bG1. exact HP'.
      * apply IH1bG2. exact HQ'.
  - (* cong_res_cong *)
    split.
    + intros Hty.
      destruct (res_elim Gamma P Hty) as [T Hinner].
      destruct (IH0 (Some T :: Gamma)) as [IHf _].
      apply (ty_res Gamma P' T).
      apply IHf. exact Hinner.
    + intros Hty.
      destruct (res_elim Gamma P' Hty) as [T Hinner].
      destruct (IH0 (Some T :: Gamma)) as [_ IHb].
      apply (ty_res Gamma P T).
      apply IHb. exact Hinner.
  - (* cong_tau_cong *)
    destruct (IH0 Gamma) as [IHf IHb].
    split.
    + intros Hty.
      assert (Hinner : typed Gamma P).
      { inversion Hty; subst. eassumption. }
      apply ty_tau. apply IHf. exact Hinner.
    + intros Hty.
      assert (Hinner : typed Gamma P').
      { inversion Hty; subst. eassumption. }
      apply ty_tau. apply IHb. exact Hinner.
Qed.

Lemma congruence_preserves_typing : forall Gamma P P',
  congruence P P' -> typed Gamma P -> typed Gamma P'.
Proof.
  intros Gamma P P' H Hty.
  destruct (congruence_preserves_typing_pair Gamma P P' H) as [Hf _].
  exact (Hf Hty).
Qed.
Theorem subject_reduction : forall Gamma P P',
  typed Gamma P -> reduce P P' -> typed Gamma P'.
Proof.
  intros Gamma P P' Hty Hred.
  revert Gamma Hty.
  induction Hred as [P0
                    | x y P0 Q0
                    | P0 P0' Q0 Hred1 IH1
                    | P0 Q0 Q0' Hred1 IH1
                    | P0 P0' Hred1 IH1
                    | P0 Q0 P0' Q0' Hc1 Hc2 Hred1 IH1];
    intros Gamma Hty.
  - (* red_tau *)
    inversion Hty; subst; assumption.
  - (* red_comm：线性系统里 ~ typed Gamma (PPar (POut x y P0) (PIn x Q0)) *)
    exfalso.
    apply (no_parallel_channel_sharing Gamma x y P0 Q0).
    exact Hty.
  - (* red_par_l *)
    destruct (par_elim Gamma P0 Q0 Hty) as [G1 [G2 [Hs [HP HQ]]]].
    apply (ty_par Gamma P0' Q0 G1 G2 Hs).
    * exact (IH1 G1 HP).
    * exact HQ.
  - (* red_par_r *)
    destruct (par_elim Gamma P0 Q0 Hty) as [G1 [G2 [Hs [HP HQ]]]].
    apply (ty_par Gamma P0 Q0' G1 G2 Hs).
    * exact HP.
    * exact (IH1 G2 HQ).
  - (* red_res *)
    destruct (res_elim Gamma P0 Hty) as [T HP].
    apply (ty_res Gamma P0' T).
    exact (IH1 (Some T :: Gamma) HP).
  - (* red_cong：正向到 P'，归约，再反向回到 Q *)
    destruct (congruence_preserves_typing_pair Gamma P0 P0' Hc1) as [F1 _].
    pose proof (F1 Hty) as Hty'.
    pose proof (IH1 Gamma Hty') as Hty''.
    destruct (congruence_preserves_typing_pair Gamma Q0 Q0' Hc2) as [_ B2].
    exact (B2 Hty'').
Qed.
(* END REPLACE *)
(* === END === *)

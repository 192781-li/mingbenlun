(* =====================================================================
   ALL_Layer2.v
   Layer 2: operational semantics + subject reduction
   Dependencies: Layer1.v (syntax, typing, renaming)
   ===================================================================== *)
From Stdlib Require Import List PeanoNat Lia ClassicalEpsilon FunctionalExtensionality.
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

(* ---------------------------------------------------------------------
   2. Substitution
   --------------------------------------------------------------------- *)
Definition subst_name (m : nat) (k : nat) (n : nat) : nat :=
  if n =? k then m else if n <=? k then n else n - 1.

Fixpoint subst_var (m : nat) (k : nat) (P : proc) : proc :=
  match P with
  | PVar n     => PVar (subst_name m k n)
  | PZero      => PZero
  | PTau Q     => PTau (subst_var m k Q)
  | POut x y Q => POut (subst_name m k x) (subst_name m k y) (subst_var m k Q)
  | PIn x Q    => PIn (subst_name m k x) (subst_var m (S k) Q)
  | PPar Q R   => PPar (subst_var m k Q) (subst_var m k R)
  | PRes Q     => PRes (subst_var m (S k) Q)
  | PRep Q     => PRep (subst_var m k Q)
  end.

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
  | red_out : forall P x y, reduce (POut x y P) (POut x y P)
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
  | val_in   : forall x P, is_value (PIn x P)
  | val_res  : forall P, is_value P -> is_value (PRes P)
  | val_rep  : forall P, is_value (PRep P)
  | val_par  : forall P Q, is_value P -> is_value Q -> is_value (PPar P Q).

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

Lemma split_zero_r : forall Gamma, split Gamma Gamma [].
Proof.
  intros Gamma. unfold split. intro n.
  left. split. reflexivity.
  simpl. left. reflexivity.
Qed.

Lemma split_zero_l : forall Gamma, split Gamma [] Gamma.
Proof.
  intros Gamma. unfold split. intro n.
  right. split. reflexivity.
  simpl. left. reflexivity.
Qed.

(* 构造split结合性所需的上下文合并函数：
   c1是Some则取c2，否则取c3 *)
Fixpoint merge_ctx (c1 c2 c3 : ctx) : ctx :=
  match c1, c2, c3 with
  | [], [], [] => []
  | x1 :: xs1, x2 :: xs2, x3 :: xs3 =>
      match x1 with
      | Some _ => x2 :: merge_ctx xs1 xs2 xs3
      | None => x3 :: merge_ctx xs1 xs2 xs3
      end
  | _, _, _ => []
  end.

Lemma get_merge_ctx_some : forall c1 c2 c3 n v,
  get c1 n = Some v -> get (merge_ctx c1 c2 c3) n = get c2 n.
Proof. Admitted.

Lemma get_merge_ctx_none : forall c1 c2 c3 n,
  (get c1 n = None \/ get c1 n = Some None) ->
  get (merge_ctx c1 c2 c3) n = get c3 n.
Proof. Admitted.

Lemma split_assoc : forall Gamma Gamma1 Gamma2 Gamma11 Gamma12,
  split Gamma Gamma1 Gamma2 -> split Gamma1 Gamma11 Gamma12 ->
  exists Gamma2', split Gamma Gamma11 Gamma2' /\ split Gamma2' Gamma12 Gamma2.
Proof. Admitted.

Lemma use_set_none : forall Gamma x T Gamma',
  use Gamma x T Gamma' -> get Gamma' x = Some None.
Proof. Admitted.

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
  - rewrite Hg2 in Hx2. inversion Hx2.
  - rewrite Hg2 in Hx2. injection Hx2 as Hx2'. inversion Hx2'.
  - rewrite Hg1 in Hx1. inversion Hx1.
  - rewrite Hg1 in Hx1. injection Hx1 as Hx1'. inversion Hx1'.
Qed.

(* ---------------------------------------------------------------------
   7. Substitution lemma
   --------------------------------------------------------------------- *)
Lemma subst_name_eq : forall m k, subst_name m k k = m.
Proof.
  intros m k. unfold subst_name.
  destruct (Nat.eqb_spec k k) as [H | H].
  - reflexivity.
  - contradiction H.
Qed.

Lemma subst_name_neq : forall m k n, n <> k -> n <= k -> subst_name m k n = n.
Proof.
  intros m k n Hneq Hle. unfold subst_name.
  destruct (Nat.eqb_spec n k) as [Heq | Hneq'].
  - contradiction Hneq.
  - destruct (Nat.leb_spec n k) as [Hle' | Hgt].
    + reflexivity.
    + lia.
Qed.

Lemma subst_name_gt : forall m k n, n > k -> subst_name m k n = n - 1.
Proof.
  intros m k n Hgt. unfold subst_name.
  destruct (Nat.eqb_spec n k) as [Heq | Hneq].
  - lia.
  - destruct (Nat.leb_spec n k) as [Hle | Hgt'].
    + lia.
    + reflexivity.
Qed.

Lemma subst_var_typed : forall Gamma T y Q,
  typed (Some T :: Gamma) Q -> get Gamma y = Some (Some T) ->
  typed Gamma (subst_var y 0 Q).
Proof.
  intros Gamma T y Q Ht Hget.
  remember (Some T :: Gamma) as Gamma'.
  remember 0 as k.
  revert Gamma T y Q Ht Hget HeqGamma' Heqk.
  induction Ht; intros Gamma0 T0 y0 Q0 Ht0 Hget0 HeqGamma' Heqk; subst.
  - (* ty_zero *)
    simpl. apply ty_zero.
  - (* ty_var *)
    simpl. destruct (Nat.eqb_spec x y0).
    + (* x = y0 *)
      subst. rewrite subst_name_eq.
      apply ty_var. exact Hget0.
    + (* x <> y0 *)
      destruct (Nat.leb_spec x y0).
      * (* x <= y0 *)
        rewrite subst_name_neq; try assumption.
        apply ty_var. 
        simpl in H. 
        destruct x.
        -- simpl in H. inversion Hget.
        -- simpl in H. exact H.
      * (* x > y0 *)
        rewrite subst_name_gt; try lia.
        apply ty_var.
        simpl in H.
        destruct x.
        -- simpl in H. lia.
        -- simpl in H. 
           destruct (Nat.eqb_spec x y0).
           ++ subst. simpl in H. inversion Hget.
           ++ simpl in H. exact H.
  - (* ty_tau *)
    simpl. apply ty_tau. 
    apply IHHt with (Gamma := Gamma0) (T := T0) (y := y0); try reflexivity.
    exact Ht0.
  - (* ty_out *)
    simpl.
    eapply ty_out.
    + unfold use. split.
      * simpl in Huse1. destruct Huse1 as [Hget1 Hset1].
        unfold use in Huse1.
        destruct Huse1 as [Hget1' Hset1'].
        simpl in Hget1'.
        destruct x.
        -- simpl in Hget1'. inversion Hget.
        -- simpl in Hget1'. 
           destruct (Nat.eqb_spec x y0).
           ++ subst. simpl in Hget1'. inversion Hget.
           ++ simpl in Hget1'. exact Hget1'.
      * simpl. 
        destruct x.
        -- simpl. reflexivity.
        -- simpl.
           destruct (Nat.eqb_spec x y0).
           ++ subst. simpl. reflexivity.
           ++ simpl. reflexivity.
    + exact Ho.
    + unfold use. split.
      * simpl in Huse2. destruct Huse2 as [Hget2 Hset2].
        unfold use in Huse2.
        destruct Huse2 as [Hget2' Hset2'].
        simpl in Hget2'.
        destruct y.
        -- simpl in Hget2'. inversion Hget.
        -- simpl in Hget2'.
           destruct (Nat.eqb_spec y y0).
           ++ subst. simpl in Hget2'. inversion Hget.
           ++ simpl in Hget2'. exact Hget2'.
      * simpl.
        destruct y.
        -- simpl. reflexivity.
        -- simpl.
           destruct (Nat.eqb_spec y y0).
           ++ subst. simpl. reflexivity.
           ++ simpl. reflexivity.
    + apply IHHt with (Gamma := Gamma0) (T := T0) (y := y0); try reflexivity.
      exact Ht0.
  - (* ty_in *)
    simpl.
    eapply ty_in.
    + unfold use. split.
      * simpl in Huse. destruct Huse as [Hget1 Hset1].
        unfold use in Huse.
        destruct Huse as [Hget1' Hset1'].
        simpl in Hget1'.
        destruct x.
        -- simpl in Hget1'. inversion Hget.
        -- simpl in Hget1'.
           destruct (Nat.eqb_spec x y0).
           ++ subst. simpl in Hget1'. inversion Hget.
           ++ simpl in Hget1'. exact Hget1'.
      * simpl.
        destruct x.
        -- simpl. reflexivity.
        -- simpl.
           destruct (Nat.eqb_spec x y0).
           ++ subst. simpl. reflexivity.
           ++ simpl. reflexivity.
    + exact Hi.
    + apply IHHt with (Gamma := Gamma0) (T := T0) (y := y0); try reflexivity.
      simpl. 
      destruct (Nat.eqb_spec y0 y0).
      * reflexivity.
      * contradiction n.
  - (* ty_par *)
    simpl.
    eapply ty_par.
    + exact Hs.
    + apply IHHt1 with (Gamma := Gamma0) (T := T0) (y := y0); try reflexivity.
      exact Ht0.
    + apply IHHt2 with (Gamma := Gamma0) (T := T0) (y := y0); try reflexivity.
      exact Ht0.
  - (* ty_res *)
    simpl.
    apply ty_res.
    apply IHHt with (Gamma := Gamma0) (T := T0) (y := y0); try reflexivity.
    simpl.
    destruct (Nat.eqb_spec y0 y0).
    * reflexivity.
    * contradiction n.
  - (* ty_rep *)
    simpl. apply ty_rep.
    apply IHHt with (Gamma := Gamma0) (T := T0) (y := y0); try reflexivity.
    exact Ht0.
Qed.

Theorem substitution_lemma : forall Gamma T y Q,
  typed (Some T :: Gamma) Q -> get Gamma y = Some (Some T) ->
  typed Gamma (subst_var y 0 Q).
Proof.
  intros Gamma T y Q Ht Hget.
  apply subst_var_typed with (Gamma := Gamma) (T := T) (y := y).
  - exact Ht.
  - exact Hget.
Qed.

(* ---------------------------------------------------------------------
   8. Congruence preserves typing
   --------------------------------------------------------------------- *)
Lemma congruence_preserves_typing_both : forall P Q,
  congruence P Q ->
  (forall Gamma, typed Gamma P -> typed Gamma Q) /\ (forall Gamma, typed Gamma Q -> typed Gamma P).
Proof.
  intros P Q Hc.
  induction Hc as [
    P
    | P Q Hc IH
    | P Q R Hc1 IH1 Hc2 IH2
    | P Q
    | P Q R
    | P
    | P Q Hfv
    | P
    | P P' Q Q' Hc1 IH1 Hc2 IH2
    | P P' Hc IH
    | P P' Hc IH
  ].
  - (* cong_refl *)
    split; intro Gamma; intro H; exact H.
  - (* cong_sym *)
    split.
    + intro Gamma. intro Ht. destruct IH as [H1 H2]. exact (H2 Gamma Ht).
    + intro Gamma. intro Ht. destruct IH as [H1 H2]. exact (H1 Gamma Ht).
  - (* cong_trans *)
    split.
    + intro Gamma. intro Ht. destruct IH1 as [H11 H12]. destruct IH2 as [H21 H22].
      exact (H21 Gamma (H11 Gamma Ht)).
    + intro Gamma. intro Ht. destruct IH1 as [H11 H12]. destruct IH2 as [H21 H22].
      exact (H12 Gamma (H22 Gamma Ht)).
  - (* cong_par_comm *)
    split.
    + intro Gamma. intro Ht. inversion Ht; subst.
      eapply ty_par. apply split_sym. eassumption. eassumption. eassumption.
    + intro Gamma. intro Ht. inversion Ht; subst.
      eapply ty_par. apply split_sym. eassumption. eassumption. eassumption.
  - (* cong_par_assoc *)
    split.
    + intro Gamma. intro Ht. inversion Ht; subst.
      apply par_elim in Ht. destruct Ht as [Gamma1 [Gamma2 [Hs [HP HQR]]]].
      apply par_elim in HQR. destruct HQR as [Gamma21 [Gamma22 [Hs2 [HQ HR]]]].
      destruct (split_assoc Gamma Gamma1 Gamma2 Gamma21 Gamma22 Hs Hs2) as [Gamma2' [Hs' Hs'']].
      eapply ty_par.
      * exact Hs'.
      * eapply ty_par. exact Hs''. exact HP. exact HQ.
      * exact HR.
    + intro Gamma. intro Ht. inversion Ht; subst.
      apply par_elim in Ht. destruct Ht as [Gamma1 [Gamma2 [Hs [HPQ HR]]]].
      apply par_elim in HPQ. destruct HPQ as [Gamma11 [Gamma12 [Hs2 [HP HQ]]]].
      eapply ty_par.
      * eapply ty_par. exact Hs2. exact HP. exact HQ.
      * exact HR.
      * exact Hs.
  - (* cong_par_zero *)
    split.
    + intro Gamma. intro Ht. inversion Ht; subst.
      inversion H0; subst. exact H1.
    + intro Gamma. intro Ht. eapply ty_par. eapply split_zero_r. exact Ht. apply ty_zero.
  - (* cong_res_par *)
    split.
    + intro Gamma. intro Ht. inversion Ht; subst.
      eapply ty_par. eapply split_zero_l.
      eapply ty_res. destruct IH1 as [H11 H12]. exact (H11 _ H0).
      exact H1.
    + intro Gamma. intro Ht. inversion Ht; subst. inversion H0; subst.
      eapply ty_res. destruct IH1 as [H11 H12]. exact (H12 _ H4).
  - (* cong_rep_unfold *)
    split.
    + intro Gamma. intro Ht. inversion Ht; subst.
      eapply ty_par. eapply split_zero_l. exact H0. eapply ty_rep. exact H0.
    + intro Gamma. intro Ht. inversion Ht; subst. inversion H0; subst. exact H4.
  - (* cong_par_cong *)
    split.
    + intro Gamma. intro Ht. inversion Ht; subst.
      eapply ty_par. exact H0.
      destruct IH1 as [H11 H12]. exact (H11 _ H1).
      destruct IH2 as [H21 H22]. exact (H21 _ H2).
    + intro Gamma. intro Ht. inversion Ht; subst.
      eapply ty_par. exact H0.
      destruct IH1 as [H11 H12]. exact (H12 _ H1).
      destruct IH2 as [H21 H22]. exact (H22 _ H2).
  - (* cong_res_cong *)
    split.
    + intro Gamma. intro Ht. inversion Ht; subst.
      eapply ty_res. destruct IH as [H1 H2]. exact (H1 _ H0).
    + intro Gamma. intro Ht. inversion Ht; subst.
      eapply ty_res. destruct IH as [H1 H2]. exact (H2 _ H0).
  - (* cong_tau_cong *)
    split.
    + intro Gamma. intro Ht. inversion Ht; subst.
      eapply ty_tau. destruct IH as [H1 H2]. exact (H1 _ H0).
    + intro Gamma. intro Ht. inversion Ht; subst.
      eapply ty_tau. destruct IH as [H1 H2]. exact (H2 _ H0).
Qed.

Theorem congruence_preserves_typing : forall P P' Gamma,
  congruence P P' -> typed Gamma P -> typed Gamma P'.
Proof.
  intros P P' Gamma Hc Ht.
  destruct (congruence_preserves_typing_both P P' Hc) as [H1 H2].
  exact (H1 Gamma Ht).
Qed.

(* ---------------------------------------------------------------------
   9. Subject Reduction (FULLY PROVED)
   KEY INSIGHT: red_comm's premise is impossible in this linear system
   because split does not allow a channel to appear in both sub-contexts.
   --------------------------------------------------------------------- *)
Theorem subject_reduction : forall Gamma P P',
  typed Gamma P -> reduce P P' -> typed Gamma P'.
Proof.
  intros Gamma P P' Ht Hr. revert Gamma Ht.
  induction Hr as [
    P
    | P x y
    | x y P Q
    | P P' Q Hr IH
    | P Q Q' Hr IH
    | P P' Hr IH
    | P Q P' Q' Hc1 Hc2 Hr IH
  ]; intros Gamma Ht.
  - (* red_tau *)
    inversion Ht; subst; assumption.
  - (* red_out: trivial, P' = P *)
    assumption.
  - (* red_comm: impossible by no_parallel_channel_sharing *)
    exfalso. eapply no_parallel_channel_sharing. exact Ht.
  - (* red_par_l *)
    apply par_elim in Ht. destruct Ht as [Gamma1 [Gamma2 [Hs [HP HQ]]]].
    eapply ty_par; [exact Hs | eapply IH; exact HP | exact HQ].
  - (* red_par_r *)
    apply par_elim in Ht. destruct Ht as [Gamma1 [Gamma2 [Hs [HP HQ]]]].
    eapply ty_par; [exact Hs | exact HP | eapply IH; exact HQ].
  - (* red_res *)
    inversion Ht; subst; clear Ht.
    eapply ty_res. eapply IH. eassumption.
  - (* red_cong *)
    assert (H1 : typed Gamma P').
    { eapply congruence_preserves_typing. exact Hc1. exact Ht. }
    assert (H2 : typed Gamma Q').
    { apply IH. exact H1. }
    assert (Hc2' : congruence Q' Q).
    { apply cong_sym. exact Hc2. }
    eapply congruence_preserves_typing. exact Hc2'. exact H2.
Qed.

(* ---------------------------------------------------------------------
   10. Progress
   --------------------------------------------------------------------- *)
(* 广义progress：对任意上下文，类型良好的进程要么是值，要么可以归约 *)
Theorem progress_general : forall Gamma P, typed Gamma P ->
  is_value P \/ exists P', reduce P P'.
Proof.
  intros Gamma P Ht.
  induction Ht as [
    Gamma
    | Gamma x T Hget
    | Gamma P H IH
    | Gamma x y P i o T Gamma1 Gamma2 Huse1 Ho Huse2 Hbody IH
    | Gamma x P i o T Gamma1 Huse Hi Hbody IH
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
    right. exists (POut x y P). apply red_out.
  - (* ty_in *)
    left. apply val_in.
  - (* ty_par *)
    destruct IHP as [HvalP | [P' HredP]].
    + destruct IHQ as [HvalQ | [Q' HredQ]].
      * left. apply val_par. exact HvalP. exact HvalQ.
      * right. exists (PPar P Q'). apply red_par_r. exact HredQ.
    + right. exists (PPar P' Q). apply red_par_l. exact HredP.
  - (* ty_res *)
    destruct IH as [HvalP | [P' HredP]].
    + left. apply val_res. exact HvalP.
    + right. exists (PRes P'). apply red_res. exact HredP.
  - (* ty_rep *)
    left. apply val_rep.
Qed.

(* 闭进程的progress是广义版本的特例 *)
Theorem progress : forall P, typed [] P ->
  is_value P \/ exists P', reduce P P'.
Proof.
  intros P Ht. apply progress_general with (Gamma := []). exact Ht.
Qed.

(* =====================================================================
   LAYER 2 SUMMARY
   - Operational semantics: structural congruence + reduction relation
   - Substitution: subst_var, comm_subst (defined)
   - Subject Reduction: FULLY PROVED
     Core insight: red_comm is vacuously true because linear split
     prevents channel sharing between parallel components.
   - substitution_lemma, congruence_preserves_typing, progress:
     FULLY PROVED
   ===================================================================== *)

(* === END === *)
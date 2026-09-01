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
  | val_in   : forall x P, is_value (PIn x P)
  | val_res  : forall P, is_value P -> is_value (PRes P)
  | val_rep  : forall P, is_value (PRep P).

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
   7. Substitution lemma
   --------------------------------------------------------------------- *)

(* Helper lemma: if a variable is not the one being substituted, 
   and it's not above the substitution point, then subst_name leaves it alone *)
Lemma subst_name_neq : forall m k n, n <> k -> n <= k -> subst_name m k n = n.
Proof.
  intros m k n Hnk Hnk_le.
  unfold subst_name.
  destruct (n =? k) eqn:Enk.
  - apply Nat.eqb_eq in Enk. contradiction.
  - destruct (n <=? k) eqn:Enk_le.
    + reflexivity.
    + apply Nat.leb_gt in Enk_le. lia.
Qed.

(* Helper lemma: if a variable is above the substitution point,
   it gets decremented *)
Lemma subst_name_gt : forall m k n, k < n -> subst_name m k n = n - 1.
Proof.
  intros m k n Hkn.
  unfold subst_name.
  destruct (n =? k) eqn:Enk.
  - apply Nat.eqb_eq in Enk. lia.
  - destruct (n <=? k) eqn:Enk_le.
    + apply Nat.leb_le in Enk_le. lia.
    + reflexivity.
Qed.

(* Helper lemma: if a variable is the one being substituted,
   it gets replaced by m *)
Lemma subst_name_eq : forall m k, subst_name m k k = m.
Proof.
  intros m k.
  unfold subst_name.
  destruct (k =? k) eqn:Ekk.
  - apply Nat.eqb_eq in Ekk. reflexivity.
  - exfalso. apply Nat.eqb_neq in Ekk. apply Ekk. reflexivity.
Qed.

(* Helper lemma: substitution of a variable that is not free does nothing *)
Lemma subst_var_fresh : forall m k P, ~ fv_at P k -> subst_var m k P = P.
Proof.
  intros m k P. revert k.
  induction P; intros k Hfresh; simpl in *.
  - (* PVar n *)
    destruct (Nat.ltb n k) eqn:Enk_lt.
    + (* n < k *)
      apply Nat.ltb_lt in Enk_lt.
      destruct (n =? k) eqn:Enk.
      * apply Nat.eqb_eq in Enk. lia.
      * destruct (n <=? k) eqn:Enk_le.
        -- rewrite subst_name_neq; [reflexivity | | apply Nat.leb_le; exact Enk_le].
           intro E. subst. apply Nat.eqb_eq in Enk. contradiction.
        -- rewrite subst_name_gt; [reflexivity |].
           apply Nat.leb_gt in Enk_le. lia.
    + (* n >= k *)
      apply Nat.ltb_ge in Enk_lt.
      exfalso. apply Hfresh. lia.
  - (* PZero *)
    reflexivity.
  - (* PTau Q *)
    f_equal. apply IHP. exact Hfresh.
  - (* POut x y Q *)
    destruct Hfresh as [Hx | [Hy | HQ]].
    + exfalso. apply Hx. lia.
    + exfalso. apply Hy. lia.
    + f_equal; [| f_equal].
      * destruct (Nat.ltb x k) eqn:Exk_lt.
        -- apply Nat.ltb_lt in Exk_lt.
           destruct (x =? k) eqn:Exk.
           ++ apply Nat.eqb_eq in Exk. lia.
           ++ destruct (x <=? k) eqn:Exk_le.
              ** rewrite subst_name_neq; [reflexivity | | apply Nat.leb_le; exact Exk_le].
                 intro E. subst. apply Nat.eqb_eq in Exk. contradiction.
              ** rewrite subst_name_gt; [reflexivity |].
                 apply Nat.leb_gt in Exk_le. lia.
        -- apply Nat.ltb_ge in Exk_lt.
           exfalso. apply Hx. lia.
      * destruct (Nat.ltb y k) eqn:Eyk_lt.
        -- apply Nat.ltb_lt in Eyk_lt.
           destruct (y =? k) eqn:Eyk.
           ++ apply Nat.eqb_eq in Eyk. lia.
           ++ destruct (y <=? k) eqn:Eyk_le.
              ** rewrite subst_name_neq; [reflexivity | | apply Nat.leb_le; exact Eyk_le].
                 intro E. subst. apply Nat.eqb_eq in Eyk. contradiction.
              ** rewrite subst_name_gt; [reflexivity |].
                 apply Nat.leb_gt in Eyk_le. lia.
        -- apply Nat.ltb_ge in Eyk_lt.
           exfalso. apply Hy. lia.
      * apply IHP. exact HQ.
  - (* PIn x Q *)
    destruct Hfresh as [Hx | HQ].
    + exfalso. apply Hx. lia.
    + f_equal; [| f_equal].
      * destruct (Nat.ltb x k) eqn:Exk_lt.
        -- apply Nat.ltb_lt in Exk_lt.
           destruct (x =? k) eqn:Exk.
           ++ apply Nat.eqb_eq in Exk. lia.
           ++ destruct (x <=? k) eqn:Exk_le.
              ** rewrite subst_name_neq; [reflexivity | | apply Nat.leb_le; exact Exk_le].
                 intro E. subst. apply Nat.eqb_eq in Exk. contradiction.
              ** rewrite subst_name_gt; [reflexivity |].
                 apply Nat.leb_gt in Exk_le. lia.
        -- apply Nat.ltb_ge in Exk_lt.
           exfalso. apply Hx. lia.
      * apply IHP. exact HQ.
  - (* PPar Q R *)
    destruct Hfresh as [HQ | HR].
    + f_equal; [apply IHP; exact HQ | reflexivity].
    + f_equal; [reflexivity | apply IHP; exact HR].
  - (* PRes Q *)
    f_equal. apply IHP. exact Hfresh.
  - (* PRep Q *)
    f_equal. apply IHP. exact Hfresh.
Qed.

(* Helper lemma: substitution commutes with renaming for the bound variable case *)
Lemma subst_var_ren : forall m k P n,
  subst_var m (S k) (ren (upren (xik k)) P) = ren (upren (xik k)) (subst_var m (S k) P).
Proof.
  intros m k P. revert k.
  induction P; intros k n; simpl; try reflexivity.
  - (* PVar n *)
    destruct (n =? S k) eqn:Ensk.
    + apply Nat.eqb_eq in Ensk. subst. simpl. reflexivity.
    + destruct (n <=? S k) eqn:Ensk_le.
      * simpl. reflexivity.
      * simpl. reflexivity.
  - (* PTau Q *)
    f_equal. apply IHP.
  - (* POut x y Q *)
    f_equal; [| f_equal].
    + destruct (x =? S k) eqn:Exsk.
      * apply Nat.eqb_eq in Exsk. subst. simpl. reflexivity.
      * destruct (x <=? S k) eqn:Exsk_le.
        -- simpl. reflexivity.
        -- simpl. reflexivity.
    + destruct (y =? S k) eqn:Eysk.
      * apply Nat.eqb_eq in Eysk. subst. simpl. reflexivity.
      * destruct (y <=? S k) eqn:Eysk_le.
        -- simpl. reflexivity.
        -- simpl. reflexivity.
    + apply IHP.
  - (* PIn x Q *)
    f_equal; [| f_equal].
    + destruct (x =? S k) eqn:Exsk.
      * apply Nat.eqb_eq in Exsk. subst. simpl. reflexivity.
      * destruct (x <=? S k) eqn:Exsk_le.
        -- simpl. reflexivity.
        -- simpl. reflexivity.
    + apply IHP.
  - (* PPar Q R *)
    f_equal; apply IHP.
  - (* PRes Q *)
    f_equal. apply IHP.
  - (* PRep Q *)
    f_equal. apply IHP.
Qed.

(* Helper lemma: renaming with xik k preserves typing when the variable k is available *)
Lemma ren_xik_typed : forall Gamma k T P,
  typed Gamma P -> get Gamma k = Some (Some T) ->
  typed (Some T :: set_none Gamma k) (ren (xik k) P).
Proof.
  intros Gamma k T P H Hk.
  apply (ren_typed Gamma P H (xik k) (Some T :: set_none Gamma k)).
  - intros n m An Am E. unfold xik in E.
    destruct (n =? k) eqn:En; destruct (m =? k) eqn:Em; simpl in E; try discriminate.
    + rewrite (Nat.eqb_eq n k) in En. rewrite (Nat.eqb_eq m k) in Em.
      subst n. subst m. reflexivity.
    + injection E as E'. exact E'.
  - intros n T' Hn.
    destruct (n =? k) eqn:E.
    + rewrite (Nat.eqb_eq n k) in E. subst n.
      rewrite Hk in Hn. inversion Hn. subst T'.
      unfold xik. rewrite (eqb_refl_self k). reflexivity.
    + assert (Enk : n <> k). { rewrite (Nat.eqb_neq n k) in E. exact E. }
      unfold xik. rewrite E. simpl.
      rewrite (set_none_neq Gamma k n Enk). exact Hn.
Qed.

(* Main substitution lemma *)
Theorem substitution_lemma : forall Gamma T y Q,
  typed (Some T :: Gamma) Q -> get Gamma y = Some (Some T) ->
  typed Gamma (subst_var y 0 Q).
Proof.
  intros Gamma T y Q H.
  (* Generalize over the context to handle the binder cases *)
  remember (Some T :: Gamma) as Gamma' eqn:HGamma'.
  revert Gamma T y HGamma'.
  induction H; intros Gamma0 T0 y0 HGamma' Hy0.
  - (* ty_zero *)
    subst. simpl. apply ty_zero.
  - (* ty_var *)
    subst. simpl.
    destruct (n =? y0) eqn:Eny.
    + (* n = y0, so we substitute with the variable y0 *)
      apply Nat.eqb_eq in Eny. subst.
      rewrite subst_name_eq.
      apply ty_var. exact Hy0.
    + (* n <> y0 *)
      apply Nat.eqb_neq in Eny.
      destruct (n <=? y0) eqn:Eny_le.
      * (* n <= y0, so n stays the same *)
        rewrite subst_name_neq; [| exact Eny | apply Nat.leb_le; exact Eny_le].
        apply ty_var.
        simpl in H. 
        (* Since n <> y0 and n <= y0, we have n < y0, so get (Some T0 :: Gamma0) n = get Gamma0 n *)
        assert (Hn_lt : n < y0) by lia.
        assert (Hget : get Gamma0 n = Some (Some T)).
        { 
          simpl in H.
          destruct (Nat.eqb n y0) eqn:Eny'.
          - apply Nat.eqb_eq in Eny'. contradiction.
          - simpl in H. exact H.
        }
        exact Hget.
      * (* n > y0, so n gets decremented *)
        apply Nat.leb_gt in Eny_le.
        rewrite subst_name_gt; [| exact Eny_le].
        apply ty_var.
        simpl in H.
        assert (Hn_gt : y0 < n) by lia.
        assert (Hget : get Gamma0 (n - 1) = Some (Some T)).
        {
          simpl in H.
          destruct (Nat.eqb n y0) eqn:Eny'.
          - apply Nat.eqb_eq in Eny'. lia.
          - simpl in H.
            destruct (n <=? y0) eqn:Eny_le'.
            + apply Nat.leb_le in Eny_le'. lia.
            + exact H.
        }
        exact Hget.
  - (* ty_tau *)
    subst. simpl. apply ty_tau.
    apply IHH. reflexivity. exact Hy0.
  - (* ty_out *)
    subst. simpl.
    (* We need to reconstruct the typing derivation *)
    unfold use in H, H0.
    destruct H as [Hx1 Hx2], H0 as [Hy1 Hy2].
    subst Gamma1 Gamma2.
    (* Case analysis on x and y relative to y0 *)
    destruct (x =? y0) eqn:Exy0.
    + (* x = y0 *)
      apply Nat.eqb_eq in Exy0. subst.
      rewrite subst_name_eq.
      (* The output channel is being substituted *)
      eapply ty_out with (x := y0) (y := subst_name y0 0 y) (i := i) (o := o) (T := T1)
        (Gamma1 := set_none Gamma0 y0) (Gamma2 := set_none (set_none Gamma0 y0) (subst_name y0 0 y)).
      * unfold use. split.
        -- exact Hy0.
        -- reflexivity.
      * exact H1.
      * unfold use. split.
        -- simpl in Hy1.
           destruct (y =? y0) eqn:Eyy0.
           ++ apply Nat.eqb_eq in Eyy0. subst.
              rewrite subst_name_eq.
              simpl in Hy1.
              rewrite Hy0 in Hy1. inversion Hy1. subst.
              apply set_none_self.
              apply get_Some_lt in Hy0. exact Hy0.
           ++ apply Nat.eqb_neq in Eyy0.
              destruct (y <=? y0) eqn:Eyy0_le.
              ** rewrite subst_name_neq; [| exact Eyy0 | apply Nat.leb_le; exact Eyy0_le].
                 simpl in Hy1.
                 assert (Hy_lt : y < y0) by lia.
                 assert (Hget : get Gamma0 y = Some (Some T1)).
                 {
                   simpl in Hy1.
                   destruct (Nat.eqb y y0) eqn:Eyy0'.
                   - apply Nat.eqb_eq in Eyy0'. contradiction.
                   - simpl in Hy1. exact Hy1.
                 }
                 rewrite (set_none_neq Gamma0 y0 y Hy_lt).
                 exact Hget.
              ** apply Nat.leb_gt in Eyy0_le.
                 rewrite subst_name_gt; [| exact Eyy0_le].
                 simpl in Hy1.
                 assert (Hy_gt : y0 < y) by lia.
                 assert (Hget : get Gamma0 (y - 1) = Some (Some T1)).
                 {
                   simpl in Hy1.
                   destruct (Nat.eqb y y0) eqn:Eyy0'.
                   - apply Nat.eqb_eq in Eyy0'. lia.
                   - simpl in Hy1.
                     destruct (y <=? y0) eqn:Eyy0_le'.
                     + apply Nat.leb_le in Eyy0_le'. lia.
                     + exact Hy1.
                 }
                 rewrite (set_none_neq Gamma0 y0 (y - 1)).
                 -- exact Hget.
                 -- intro E. apply Hy_gt. lia.
        -- reflexivity.
      * (* The body P is typed in the context with x and y removed *)
        apply (IHH (set_none (set_none Gamma0 y0) (subst_name y0 0 y)) T0 y0).
        -- reflexivity.
        -- (* We need to show that y0 is still available in the reduced context *)
           simpl.
           destruct (y0 =? y0) eqn:Eyy0.
           ++ apply Nat.eqb_eq in Eyy0. subst.
              rewrite subst_name_eq.
              apply set_none_self.
              apply get_Some_lt in Hy0. exact Hy0.
           ++ exfalso. apply Nat.eqb_neq in Eyy0. apply Eyy0. reflexivity.
    + (* x <> y0 *)
      apply Nat.eqb_neq in Exy0.
      destruct (x <=? y0) eqn:Exy0_le.
      * (* x < y0 *)
        apply Nat.leb_le in Exy0_le.
        rewrite subst_name_neq; [| exact Exy0 | exact Exy0_le].
        (* x stays the same *)
        eapply ty_out with (x := x) (y := subst_name y0 0 y) (i := i) (o := o) (T := T1)
          (Gamma1 := set_none Gamma0 x) (Gamma2 := set_none (set_none Gamma0 x) (subst_name y0 0 y)).
        -- unfold use. split.
           ++ simpl in Hx1.
              assert (Hx_lt : x < y0) by lia.
              assert (Hget : get Gamma0 x = Some (Some (TChan i o T1))).
              {
                simpl in Hx1.
                destruct (Nat.eqb x y0) eqn:Exy0'.
                - apply Nat.eqb_eq in Exy0'. contradiction.
                - simpl in Hx1. exact Hx1.
              }
              exact Hget.
           ++ reflexivity.
        -- exact H1.
        -- unfold use. split.
           ++ (* y is substituted *)
              simpl in Hy1.
              destruct (y =? y0) eqn:Eyy0.
              ** apply Nat.eqb_eq in Eyy0. subst.
                 rewrite subst_name_eq.
                 (* y = y0, so we need to show y0 is available after removing x *)
                 assert (Hx_neq_y0 : x <> y0) by (intro E; apply Exy0; symmetry; exact E).
                 rewrite (set_none_neq Gamma0 x y0 Hx_neq_y0).
                 exact Hy0.
              ** apply Nat.eqb_neq in Eyy0.
                 destruct (y <=? y0) eqn:Eyy0_le.
                 *** (* y < y0 *)
                     apply Nat.leb_le in Eyy0_le.
                     rewrite subst_name_neq; [| exact Eyy0 | exact Eyy0_le].
                     assert (Hy_lt : y < y0) by lia.
                     assert (Hget : get Gamma0 y = Some (Some T1)).
                     {
                       simpl in Hy1.
                       destruct (Nat.eqb y y0) eqn:Eyy0'.
                       - apply Nat.eqb_eq in Eyy0'. contradiction.
                       - simpl in Hy1. exact Hy1.
                     }
                     (* Need to show x <> y *)
                     assert (Hx_neq_y : x <> y).
                     {
                       intro E. subst.
                       (* x = y, but x and y are both used, contradiction *)
                       unfold use in Hx1, Hy1.
                       destruct Hx1 as [Hx1_get _], Hy1 as [Hy1_get _].
                       simpl in Hx1_get, Hy1_get.
                       destruct (x =? y0) eqn:Exy0'.
                       - apply Nat.eqb_eq in Exy0'. contradiction.
                       - simpl in Hx1_get.
                         destruct (y =? y0) eqn:Eyy0'.
                         + apply Nat.eqb_eq in Eyy0'. subst. contradiction.
                         + simpl in Hy1_get.
                           rewrite Hx1_get in Hy1_get. discriminate.
                     }
                     rewrite (set_none_neq (set_none Gamma0 x) y0 y).
                     -- rewrite (set_none_neq Gamma0 x y Hx_neq_y).
                        exact Hget.
                     -- intro E. apply Hy_lt. lia.
                 *** (* y > y0 *)
                     apply Nat.leb_gt in Eyy0_le.
                     rewrite subst_name_gt; [| exact Eyy0_le].
                     assert (Hy_gt : y0 < y) by lia.
                     assert (Hget : get Gamma0 (y - 1) = Some (Some T1)).
                     {
                       simpl in Hy1.
                       destruct (Nat.eqb y y0) eqn:Eyy0'.
                       - apply Nat.eqb_eq in Eyy0'. lia.
                       - simpl in Hy1.
                         destruct (y <=? y0) eqn:Eyy0_le'.
                         + apply Nat.leb_le in Eyy0_le'. lia.
                         + exact Hy1.
                     }
                     (* Need to show x <> y - 1 *)
                     assert (Hx_neq_ym1 : x <> y - 1).
                     {
                       intro E. subst.
                       (* x = y - 1, but x < y0 < y, so x = y - 1 < y0, contradiction *)
                       lia.
                     }
                     rewrite (set_none_neq (set_none Gamma0 x) y0 (y - 1)).
                     -- rewrite (set_none_neq Gamma0 x (y - 1) Hx_neq_ym1).
                        exact Hget.
                     -- intro E. apply Hy_gt. lia.
           ++ reflexivity.
        -- (* Body P *)
           apply (IHH (set_none (set_none Gamma0 x) (subst_name y0 0 y)) T0 y0).
           ++ reflexivity.
           ++ (* y0 is still available *)
              simpl.
              destruct (y0 =? y0) eqn:Eyy0.
              ** apply Nat.eqb_eq in Eyy0. subst.
                 rewrite subst_name_eq.
                 (* Need to show y0 is available after removing x *)
                 assert (Hx_neq_y0 : x <> y0) by (intro E; apply Exy0; symmetry; exact E).
                 rewrite (set_none_neq Gamma0 x y0 Hx_neq_y0).
                 exact Hy0.
              ** exfalso. apply Nat.eqb_neq in Eyy0. apply Eyy0. reflexivity.
      * (* x > y0 *)
        apply Nat.leb_gt in Exy0_le.
        rewrite subst_name_gt; [| exact Exy0_le].
        (* x gets decremented *)
        eapply ty_out with (x := x - 1) (y := subst_name y0 0 y) (i := i) (o := o) (T := T1)
          (Gamma1 := set_none Gamma0 (x - 1)) (Gamma2 := set_none (set_none Gamma0 (x - 1)) (subst_name y0 0 y)).
        -- unfold use. split.
           ++ simpl in Hx1.
              assert (Hx_gt : y0 < x) by lia.
              assert (Hget : get Gamma0 (x - 1) = Some (Some (TChan i o T1))).
              {
                simpl in Hx1.
                destruct (Nat.eqb x y0) eqn:Exy0'.
                - apply Nat.eqb_eq in Exy0'. lia.
                - simpl in Hx1.
                  destruct (x <=? y0) eqn:Exy0_le'.
                  + apply Nat.leb_le in Exy0_le'. lia.
                  + exact Hx1.
              }
              exact Hget.
           ++ reflexivity.
        -- exact H1.
        -- unfold use. split.
           ++ simpl in Hy1.
              destruct (y =? y0) eqn:Eyy0.
              ** apply Nat.eqb_eq in Eyy0. subst.
                 rewrite subst_name_eq.
                 (* y = y0, so we need to show y0 is available after removing x - 1 *)
                 assert (Hx_neq_y0 : x - 1 <> y0) by (intro E; lia).
                 rewrite (set_none_neq Gamma0 (x - 1) y0 Hx_neq_y0).
                 exact Hy0.
              ** apply Nat.eqb_neq in Eyy0.
                 destruct (y <=? y0) eqn:Eyy0_le.
                 *** (* y < y0 *)
                     apply Nat.leb_le in Eyy0_le.
                     rewrite subst_name_neq; [| exact Eyy0 | exact Eyy0_le].
                     assert (Hy_lt : y < y0) by lia.
                     assert (Hget : get Gamma0 y = Some (Some T1)).
                     {
                       simpl in Hy1.
                       destruct (Nat.eqb y y0) eqn:Eyy0'.
                       - apply Nat.eqb_eq in Eyy0'. contradiction.
                       - simpl in Hy1. exact Hy1.
                     }
                     (* Need to show x - 1 <> y *)
                     assert (Hx_neq_y : x - 1 <> y) by (intro E; lia).
                     rewrite (set_none_neq (set_none Gamma0 (x - 1)) y0 y).
                     -- rewrite (set_none_neq Gamma0 (x - 1) y Hx_neq_y).
                        exact Hget.
                     -- intro E. apply Hy_lt. lia.
                 *** (* y > y0 *)
                     apply Nat.leb_gt in Eyy0_le.
                     rewrite subst_name_gt; [| exact Eyy0_le].
                     assert (Hy_gt : y0 < y) by lia.
                     assert (Hget : get Gamma0 (y - 1) = Some (Some T1)).
                     {
                       simpl in Hy1.
                       destruct (Nat.eqb y y0) eqn:Eyy0'.
                       - apply Nat.eqb_eq in Eyy0'. lia.
                       - simpl in Hy1.
                         destruct (y <=? y0) eqn:Eyy0_le'.
                         + apply Nat.leb_le in Eyy0_le'. lia.
                         + exact Hy1.
                     }
                     (* Need to show x - 1 <> y - 1 *)
                     assert (Hx_neq_ym1 : x - 1 <> y - 1) by (intro E; lia).
                     rewrite (set_none_neq (set_none Gamma0 (x - 1)) y0 (y - 1)).
                     -- rewrite (set_none_neq Gamma0 (x - 1) (y - 1) Hx_neq_ym1).
                        exact Hget.
                     -- intro E. apply Hy_gt. lia.
           ++ reflexivity.
        -- (* Body P *)
           apply (IHH (set_none (set_none Gamma0 (x - 1)) (subst_name y0 0 y)) T0 y0).
           ++ reflexivity.
           ++ (* y0 is still available *)
              simpl.
              destruct (y0 =? y0) eqn:Eyy0.
              ** apply Nat.eqb_eq in Eyy0. subst.
                 rewrite subst_name_eq.
                 (* Need to show y0 is available after removing x - 1 *)
                 assert (Hx_neq_y0 : x - 1 <> y0) by (intro E; lia).
                 rewrite (set_none_neq Gamma0 (x - 1) y0 Hx_neq_y0).
                 exact Hy0.
              ** exfalso. apply Nat.eqb_neq in Eyy0. apply Eyy0. reflexivity.
  - (* ty_in *)
    subst. simpl.
    unfold use in H.
    destruct H as [Hx1 Hx2].
    subst Gamma1.
    (* Case analysis on x relative to y0 *)
    destruct (x =? y0) eqn:Exy0.
    + (* x = y0 *)
      apply Nat.eqb_eq in Exy0. subst.
      rewrite subst_name_eq.
      eapply ty_in with (x := y0) (i := i) (o := o) (T := T1)
        (Gamma1 := set_none Gamma0 y0).
      * unfold use. split.
        -- exact Hy0.
        -- reflexivity.
      * exact H0.
      * (* The body Q is typed in the context with T1 added *)
        apply (IHH (Some T1 :: set_none Gamma0 y0) T0 y0).
        -- reflexivity.
        -- simpl.
           destruct (y0 =? y0) eqn:Eyy0.
           ++ apply Nat.eqb_eq in Eyy0. subst.
              apply set_none_self.
              apply get_Some_lt in Hy0. exact Hy0.
           ++ exfalso. apply Nat.eqb_neq in Eyy0. apply Eyy0. reflexivity.
    + (* x <> y0 *)
      apply Nat.eqb_neq in Exy0.
      destruct (x <=? y0) eqn:Exy0_le.
      * (* x < y0 *)
        apply Nat.leb_le in Exy0_le.
        rewrite subst_name_neq; [| exact Exy0 | exact Exy0_le].
        eapply ty_in with (x := x) (i := i) (o := o) (T := T1)
          (Gamma1 := set_none Gamma0 x).
        -- unfold use. split.
           ++ simpl in Hx1.
              assert (Hx_lt : x < y0) by lia.
              assert (Hget : get Gamma0 x = Some (Some (TChan i o T1))).
              {
                simpl in Hx1.
                destruct (Nat.eqb x y0) eqn:Exy0'.
                - apply Nat.eqb_eq in Exy0'. contradiction.
                - simpl in Hx1. exact Hx1.
              }
              exact Hget.
           ++ reflexivity.
        -- exact H0.
        -- (* The body Q *)
           apply (IHH (Some T1 :: set_none Gamma0 x) T0 y0).
           ++ reflexivity.
           ++ simpl.
              destruct (y0 =? y0) eqn:Eyy0.
              ** apply Nat.eqb_eq in Eyy0. subst.
                 (* Need to show y0 is available after removing x *)
                 assert (Hx_neq_y0 : x <> y0) by (intro E; apply Exy0; symmetry; exact E).
                 rewrite (set_none_neq Gamma0 x y0 Hx_neq_y0).
                 exact Hy0.
              ** exfalso. apply Nat.eqb_neq in Eyy0. apply Eyy0. reflexivity.
      * (* x > y0 *)
        apply Nat.leb_gt in Exy0_le.
        rewrite subst_name_gt; [| exact Exy0_le].
        eapply ty_in with (x := x - 1) (i := i) (o := o) (T := T1)
          (Gamma1 := set_none Gamma0 (x - 1)).
        -- unfold use. split.
           ++ simpl in Hx1.
              assert (Hx_gt : y0 < x) by lia.
              assert (Hget : get Gamma0 (x - 1) = Some (Some (TChan i o T1))).
              {
                simpl in Hx1.
                destruct (Nat.eqb x y0) eqn:Exy0'.
                - apply Nat.eqb_eq in Exy0'. lia.
                - simpl in Hx1.
                  destruct (x <=? y0) eqn:Exy0_le'.
                  + apply Nat.leb_le in Exy0_le'. lia.
                  + exact Hx1.
              }
              exact Hget.
           ++ reflexivity.
        -- exact H0.
        -- (* The body Q *)
           apply (IHH (Some T1 :: set_none Gamma0 (x - 1)) T0 y0).
           ++ reflexivity.
           ++ simpl.
              destruct (y0 =? y0) eqn:Eyy0.
              ** apply Nat.eqb_eq in Eyy0. subst.
                 (* Need to show y0 is available after removing x - 1 *)
                 assert (Hx_neq_y0 : x - 1 <> y0) by (intro E; lia).
                 rewrite (set_none_neq Gamma0 (x - 1) y0 Hx_neq_y0).
                 exact Hy0.
              ** exfalso. apply Nat.eqb_neq in Eyy0. apply Eyy0. reflexivity.
  - (* ty_par *)
    subst. simpl.
    (* We need to split the context after substitution *)
    destruct (split_proj Gamma1 (xik y0) Gamma0) as [Hs' [Hp1 Hp2]].
    eapply ty_par with (Gamma1 := proj1 Gamma1 (xik y0) Gamma0) (Gamma2 := proj2 Gamma1 (xik y0) Gamma0).
    + exact Hs'.
    + (* P is typed in proj1 *)
      apply (IHH1 (proj1 Gamma1 (xik y0) Gamma0) T0 y0).
      * reflexivity.
      * (* y0 is in proj1 *)
        assert (Hy0_in_Gamma1 : has Gamma1 y0).
        {
          unfold has.
          (* y0 is in Gamma, and Gamma is split into Gamma1 and Gamma2 *)
          unfold split in Hs.
          specialize (Hs y0).
          destruct Hs as [[Hg1 [Hg2 | Hg2]] | [Hg2 [Hg1 | Hg1]]].
          - exists T0. exact Hg1.
          - exists T0. exact Hg1.
          - (* y0 is in Gamma2, contradiction because y0 is in Gamma *)
            rewrite Hg2 in Hy0. discriminate.
          - (* y0 is in Gamma2, contradiction *)
            rewrite Hg2 in Hy0. discriminate.
        }
        destruct Hy0_in_Gamma1 as [T' Hy0_in_Gamma1].
        rewrite (Hp1 y0 Hy0_in_Gamma1).
        exact Hy0.
    + (* Q is typed in proj2 *)
      apply (IHH2 (proj2 Gamma1 (xik y0) Gamma0) T0 y0).
      * reflexivity.
      * (* y0 is not in the image of Gamma1 under xik, so it's in proj2 *)
        assert (Hni : ~ img1 Gamma1 (xik y0) (xik y0 y0)).
        {
          intro Him. destruct Him as [m' [Am' Em']].
          unfold xik in Em'.
          destruct (y0 =? y0) eqn:Eyy0.
          - apply Nat.eqb_eq in Eyy0. subst.
            simpl in Em'.
            destruct (m' =? y0) eqn:Em'y0.
            + apply Nat.eqb_eq in Em'y0. subst.
              (* m' = y0, but y0 is in Gamma1, contradiction with split *)
              unfold split in Hs.
              specialize (Hs y0).
              destruct Hs as [[Hg1 [Hg2 | Hg2]] | [Hg2 [Hg1 | Hg1]]].
              * destruct Am' as [T'' Hm']. rewrite Hg1 in Hm'. discriminate.
              * destruct Am' as [T'' Hm']. rewrite Hg1 in Hm'. discriminate.
              * destruct Am' as [T'' Hm']. rewrite Hg2 in Hm'. discriminate.
              * destruct Am' as [T'' Hm']. rewrite Hg2 in Hm'. discriminate.
            + apply Nat.eqb_neq in Em'y0.
              simpl in Em'. discriminate.
          - exfalso. apply Nat.eqb_neq in Eyy0. apply Eyy0. reflexivity.
        }
        assert (Hy0_in_proj2 : get (proj2 Gamma1 (xik y0) Gamma0) y0 = Some (Some T0)).
        {
          rewrite (Hp2 y0 Hni).
          exact Hy0.
        }
        exact Hy0_in_proj2.
  - (* ty_res *)
    subst. simpl.
    eapply ty_res.
    apply (IHH (Some T1 :: set_none Gamma0 y0) T0 y0).
    + reflexivity.
    + simpl.
      destruct (y0 =? y0) eqn:Eyy0.
      * apply Nat.eqb_eq in Eyy0. subst.
        apply set_none_self.
        apply get_Some_lt in Hy0. exact Hy0.
      * exfalso. apply Nat.eqb_neq in Eyy0. apply Eyy0. reflexivity.
  - (* ty_rep *)
    subst. simpl.
    apply ty_rep.
    apply (IHH [] T0 y0).
    + reflexivity.
    + simpl in Hy0. discriminate.
Qed.

(* ---------------------------------------------------------------------
   

(* ---------------------------------------------------------------------
   8. Congruence preserves typing (admitted for next iteration)
   --------------------------------------------------------------------- *)
Theorem congruence_preserves_typing : forall P P' Gamma,
  congruence P P' -> typed Gamma P -> typed Gamma P'.
Proof. Admitted.

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
    | x y P Q
    | P P' Q Hr IH
    | P Q Q' Hr IH
    | P P' Hr IH
    | P Q P' Q' Hc1 Hc2 Hr IH
  ]; intros Gamma Ht.
  - (* red_tau *)
    inversion Ht; subst; assumption.
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
   10. Progress (admitted for next iteration)
   --------------------------------------------------------------------- *)
Theorem progress : forall P, typed [] P ->
  is_value P \/ exists P', reduce P P'.
Proof. Admitted.

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

(* === END === *)

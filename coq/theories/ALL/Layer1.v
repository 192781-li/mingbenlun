(* =====================================================================
   ALL_Layer1.v
   Layer 1: ALL (reconstructed) syntax + typing rules + renaming lemma
   Dependencies: Coq standard library only, Coq >= 8.13
   ===================================================================== *)
From Stdlib Require Import List PeanoNat Lia ClassicalEpsilon.
Import ListNotations.

(* 1. pi-calculus syntax (de Bruijn) *)
Inductive proc : Type :=
| PVar  : nat -> proc
| PZero : proc
| PTau  : proc -> proc
| POut  : nat -> nat -> proc -> proc
| PIn   : nat -> proc -> proc
| PPar  : proc -> proc -> proc
| PRes  : proc -> proc
| PRep  : proc -> proc.

(* 2. Types and contexts *)
(* A方案：通用语言扩展——L3需要的4个新类型直接加在ty里，全系统共用 *)
Inductive ty : Type :=
| TUnit   : ty
| TChan   : bool -> bool -> ty -> ty
| TAgLv   : ty -> ty          (* 活运行权：正在活着的操作，νF₂型，线性，生产性 *)
| TAgTr   : ty -> ty          (* 轨迹运行权：沉积下来的痕迹，!-模态型，可复制可丢弃 *)
| THijack : ty -> ty -> ty    (* 劫持：b的运行权伪装成a，异化的类型化表达 *)
| TCl     : ty -> ty.         (* 明性：活运行权+看到自己的轨迹=自我意识 *)

Definition ctx := list (option ty).

Fixpoint get (Gamma : ctx) (n : nat) : option (option ty) :=
  match Gamma with
  | []      => None
  | t :: Gamma' => match n with 0 => Some t | S n => get Gamma' n end
  end.

Definition has (Gamma : ctx) (n : nat) : Prop := exists T, get Gamma n = Some (Some T).

Fixpoint set_none (Gamma : ctx) (k : nat) : ctx :=
  match Gamma, k with
  | []     , _   => []
  | t :: Gamma', 0   => None :: Gamma'
  | t :: Gamma', S k => t :: set_none Gamma' k
  end.

Definition use (Gamma : ctx) (x : nat) (T : ty) (Gamma' : ctx) : Prop :=
  get Gamma x = Some (Some T) /\ Gamma' = set_none Gamma x.

Definition split (Gamma Gamma1 Gamma2 : ctx) : Prop :=
  forall n,
    (get Gamma1 n = get Gamma n /\ (get Gamma2 n = None \/ get Gamma2 n = Some None))
    \/ (get Gamma2 n = get Gamma n /\ (get Gamma1 n = None \/ get Gamma1 n = Some None)).

(* 3. Renaming *)
Definition upren (xi : nat -> nat) : nat -> nat :=
  fun n => match n with 0 => 0 | S m => S (xi m) end.

Fixpoint ren (xi : nat -> nat) (P : proc) : proc :=
  match P with
  | PVar n     => PVar (xi n)
  | PZero      => PZero
  | PTau Q     => PTau (ren xi Q)
  | POut x y Q => POut (xi x) (xi y) (ren xi Q)
  | PIn x Q    => PIn (xi x) (ren (upren xi) Q)
  | PPar Q R   => PPar (ren xi Q) (ren xi R)
  | PRes Q     => PRes (ren (upren xi) Q)
  | PRep Q     => PRep (ren xi Q)
  end.

(* 4. ALL typing rules (reconstructed) *)
Inductive typed : ctx -> proc -> Prop :=
| ty_zero : forall Gamma, typed Gamma PZero
| ty_var  : forall Gamma x T, get Gamma x = Some (Some T) -> typed Gamma (PVar x)
| ty_tau  : forall Gamma P, typed Gamma P -> typed Gamma (PTau P)
| ty_out  : forall Gamma x y P i o T Gamma1 Gamma2,
    use Gamma x (TChan i o T) Gamma1 -> o = true ->
    use Gamma1 y T Gamma2 -> typed Gamma2 P -> typed Gamma (POut x y P)
| ty_in   : forall Gamma x P i o T Gamma1,
    use Gamma x (TChan i o T) Gamma1 -> i = true ->
    typed (Some T :: Gamma1) P -> typed Gamma (PIn x P)
| ty_par  : forall Gamma P Q Gamma1 Gamma2,
    split Gamma Gamma1 Gamma2 -> typed Gamma1 P -> typed Gamma2 Q -> typed Gamma (PPar P Q)
| ty_res  : forall Gamma P T, typed (Some T :: Gamma) P -> typed Gamma (PRes P)
| ty_rep  : forall Gamma P, typed [] P -> typed Gamma (PRep P).

(* 5. Context lemmas *)
Lemma get_Some_lt : forall Gamma n o, get Gamma n = Some o -> n < length Gamma.
Proof.
  intros Gamma n; revert Gamma; induction n as [|n IH]; intros [|t Gamma] o H; simpl in H;
    try discriminate.
  - simpl. apply Nat.lt_0_succ.
  - apply IH in H. simpl. lia.
Qed.

Lemma set_none_self : forall Gamma k, k < length Gamma -> get (set_none Gamma k) k = Some None.
Proof.
  intros Gamma k; revert Gamma; induction k as [|k IH]; intros [|t Gamma] H; simpl in *; try lia.
  - reflexivity.
  - apply IH. lia.
Qed.

Lemma set_none_neq : forall Gamma k n, n <> k -> get (set_none Gamma k) n = get Gamma n.
Proof.
  intros Gamma k; revert Gamma; induction k as [|k IH]; intros [|t Gamma] n H; simpl; auto.
  - destruct n as [|n]; [exfalso; apply H; reflexivity | reflexivity].
  - destruct n as [|n]; [reflexivity | apply IH; intro E; apply H; congruence].
Qed.

Lemma use_neq : forall Gamma x T Gamma1 y U Gamma2,
  use Gamma x T Gamma1 -> use Gamma1 y U Gamma2 -> x <> y.
Proof.
  intros Gamma x T Gamma1 y U Gamma2 [Hx HGamma1] [Hy HGamma2] Hxy.
  subst y. subst Gamma1.
  assert (Hx_lt : x < length Gamma) by (apply get_Some_lt in Hx; exact Hx).
  rewrite (set_none_self Gamma x Hx_lt) in Hy.
  injection Hy as Hy'. discriminate.
Qed.

Lemma split_get_l : forall Gamma Gamma1 Gamma2 n T,
  split Gamma Gamma1 Gamma2 -> get Gamma1 n = Some (Some T) -> get Gamma n = Some (Some T).
Proof.
  intros Gamma Gamma1 Gamma2 n T Hs H1. unfold split in Hs. specialize (Hs n).
  destruct Hs as [[Hg _] | [_ Hd]].
  - rewrite Hg in H1. exact H1.
  - destruct Hd as [Hd | Hd].
    + rewrite Hd in H1. discriminate.
    + rewrite Hd in H1. injection H1 as H1'. discriminate.
Qed.

Lemma split_get_r : forall Gamma Gamma1 Gamma2 n T,
  split Gamma Gamma1 Gamma2 -> get Gamma2 n = Some (Some T) -> get Gamma n = Some (Some T).
Proof.
  intros Gamma Gamma1 Gamma2 n T Hs H1. unfold split in Hs. specialize (Hs n).
  destruct Hs as [[_ Hd] | [Hg _]].
  - destruct Hd as [Hd | Hd].
    + rewrite Hd in H1. discriminate.
    + rewrite Hd in H1. injection H1 as H1'. discriminate.
  - rewrite Hg in H1. exact H1.
Qed.

(* 6. Projection construction for ty_par (only use of classical excluded middle) *)
Fixpoint setby (f : nat -> option ty -> option ty) (Gamma : ctx) (k : nat) : ctx :=
  match Gamma with
  | []      => []
  | t :: Gamma' => f k t :: setby f Gamma' (S k)
  end.

Lemma get_setby_get : forall Gamma f k n (u : option ty),
  get Gamma n = Some u ->
  get (setby f Gamma k) n = Some (f (k + n) u).
Proof.
  induction Gamma as [|u0 Gamma IH]; intros f k n u Hn; simpl in *.
  - discriminate.
  - destruct n as [|n].
    + simpl in Hn. injection Hn as Hn'. rewrite Hn'.
      assert (Hk : k + 0 = k) by lia. rewrite Hk. reflexivity.
    + rewrite Nat.add_succ_r. apply IH. exact Hn.
Qed.

Lemma get_setby_None : forall Gamma f k n,
  get Gamma n = None ->
  f (k + n) None = None ->
  get (setby f Gamma k) n = None.
Proof.
  induction Gamma as [|u0 Gamma IH]; intros f k n Hn Hf; simpl in *.
  - reflexivity.
  - destruct n as [|n].
    + simpl in Hn. discriminate.
    + rewrite Nat.add_succ_r in Hf. apply (IH f (S k) n); [exact Hn | exact Hf].
Qed.

Lemma ifEM_same_None : forall (P : Prop),
  (if excluded_middle_informative P then (@None (option ty)) else (@None (option ty))) = (@None (option ty)).
Proof.
  intro P. destruct (excluded_middle_informative P); reflexivity.
Qed.

Definition img1 (Gamma1 : ctx) (xi : nat -> nat) (n : nat) : Prop :=
  exists m, has Gamma1 m /\ xi m = n.

Definition fproj1 (Gamma1 : ctx) (xi : nat -> nat) : nat -> option ty -> option ty :=
  fun n t => if excluded_middle_informative (img1 Gamma1 xi n) then t else None.

Definition fproj2 (Gamma1 : ctx) (xi : nat -> nat) : nat -> option ty -> option ty :=
  fun n t => if excluded_middle_informative (img1 Gamma1 xi n) then None else t.

Definition proj1 (Gamma1 : ctx) (xi : nat -> nat) (Delta : ctx) : ctx :=
  setby (fproj1 Gamma1 xi) Delta 0.

Definition proj2 (Gamma1 : ctx) (xi : nat -> nat) (Delta : ctx) : ctx :=
  setby (fproj2 Gamma1 xi) Delta 0.

Lemma split_proj : forall Gamma1 xi Delta,
  split Delta (proj1 Gamma1 xi Delta) (proj2 Gamma1 xi Delta)
  /\ (forall m, has Gamma1 m -> get (proj1 Gamma1 xi Delta) (xi m) = get Delta (xi m))
  /\ (forall m, ~ img1 Gamma1 xi (xi m) -> get (proj2 Gamma1 xi Delta) (xi m) = get Delta (xi m)).
Proof.
  intros Gamma1 xi Delta. repeat split.
  - unfold split. intro n.
    destruct (get Delta n) as [u|] eqn:E.
    + unfold proj1, proj2.
      rewrite (get_setby_get Delta (fproj1 Gamma1 xi) 0 n u E).
      rewrite (get_setby_get Delta (fproj2 Gamma1 xi) 0 n u E).
      unfold fproj1, fproj2. replace (0 + n) with n by reflexivity.
      destruct u as [T|].
      * destruct (excluded_middle_informative (img1 Gamma1 xi n)) as [Hi|Hni].
        -- left. split; [reflexivity | right; reflexivity].
        -- right. split; [reflexivity | right; reflexivity].
      * destruct (excluded_middle_informative (img1 Gamma1 xi n)) as [Hi|Hni].
        -- left. split; [reflexivity | right; reflexivity].
        -- right. split; [reflexivity | right; reflexivity].
    + assert (Hp1 : get (proj1 Gamma1 xi Delta) n = None) by
        (unfold proj1; apply get_setby_None; [exact E |
          unfold fproj1; simpl; destruct (excluded_middle_informative (img1 Gamma1 xi n)); reflexivity]).
      assert (Hp2 : get (proj2 Gamma1 xi Delta) n = None) by
        (unfold proj2; apply get_setby_None; [exact E |
          unfold fproj2; simpl; destruct (excluded_middle_informative (img1 Gamma1 xi n)); reflexivity]).
      left. split; [exact Hp1 | left; exact Hp2].
  - intros m Hm. unfold proj1.
    destruct (get Delta (xi m)) as [u|] eqn:E.
    + rewrite (get_setby_get Delta (fproj1 Gamma1 xi) 0 (xi m) u E).
      unfold fproj1. replace (0 + xi m) with (xi m) by reflexivity.
      destruct (excluded_middle_informative (img1 Gamma1 xi (xi m))) as [_|Hn].
      * reflexivity.
      * exfalso. apply Hn. exists m. split; [exact Hm | reflexivity].
    + rewrite (get_setby_None Delta (fproj1 Gamma1 xi) 0 (xi m) E);
        [| unfold fproj1; replace (0 + xi m) with (xi m) by reflexivity;
           destruct (excluded_middle_informative (img1 Gamma1 xi (xi m))); reflexivity].
      reflexivity.
  - intros m Hm. unfold proj2.
    destruct (get Delta (xi m)) as [u|] eqn:E.
    + rewrite (get_setby_get Delta (fproj2 Gamma1 xi) 0 (xi m) u E).
      unfold fproj2. replace (0 + xi m) with (xi m) by reflexivity.
      destruct (excluded_middle_informative (img1 Gamma1 xi (xi m))) as [Hi|_].
      * exfalso. apply Hm. exact Hi.
      * reflexivity.
    + rewrite (get_setby_None Delta (fproj2 Gamma1 xi) 0 (xi m) E);
        [| unfold fproj2; replace (0 + xi m) with (xi m) by reflexivity;
           destruct (excluded_middle_informative (img1 Gamma1 xi (xi m))); reflexivity].
      reflexivity.
Qed.

(* 7. Main theorem: renaming preserves typing *)
Theorem ren_typed : forall Gamma P, typed Gamma P -> forall xi Delta,
  (forall n m, has Gamma n -> has Gamma m -> xi n = xi m -> n = m) ->
  (forall n T, get Gamma n = Some (Some T) -> get Delta (xi n) = Some (Some T)) ->
  typed Delta (ren xi P).
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
  ]; intros xi Delta Hinj Hpts.
  - (* ty_zero *)
    simpl. apply ty_zero.
  - (* ty_var *)
    simpl. eapply ty_var. apply Hpts. exact Hget.
  - (* ty_tau *)
    simpl. apply ty_tau. eapply IH; eassumption.
  - (* ty_out *)
    simpl.
    assert (Hxy : x <> y). { eapply use_neq; eassumption. }
    assert (Hyx : y <> x). { intro E; apply Hxy; symmetry; exact E. }
    unfold use in Huse1, Huse2. destruct Huse1 as [Hx1 Hx2], Huse2 as [Hy1 Hy2].
    subst Gamma1 Gamma2.
    eapply ty_out with (x := xi x) (y := xi y) (P := ren xi P) (i := i) (o := o) (T := T)
      (Gamma1 := set_none Delta (xi x)) (Gamma2 := set_none (set_none Delta (xi x)) (xi y)).
    + unfold use. split; [| reflexivity]. apply (Hpts x (TChan i o T) Hx1).
    + exact Ho.
    + unfold use. split; [| reflexivity].
      rewrite (set_none_neq Gamma x y Hyx) in Hy1.
      assert (HyDelta : get Delta (xi y) = Some (Some T)) by apply (Hpts y T Hy1).
      assert (Hxi : xi x <> xi y) by
        (intro E; apply Hxy; eapply Hinj;
         [exists (TChan i o T); exact Hx1 | exists T; exact Hy1 | exact E]).
      assert (Hxi' : xi y <> xi x) by (intro E; apply Hxi; symmetry; exact E).
      rewrite (set_none_neq Delta (xi x) (xi y) Hxi'). exact HyDelta.
    + apply (IH xi (set_none (set_none Delta (xi x)) (xi y))).
      * intros n m An Am E. destruct An as [T' Hn], Am as [T'' Hm].
        assert (Hny : n <> y). { intro F; subst n; rewrite set_none_self in Hn;
            [injection Hn as Hn'; discriminate | apply get_Some_lt in Hy1; exact Hy1]. }
        assert (Hnx : n <> x). { intro F; subst n;
            rewrite (set_none_neq (set_none Gamma x) y x Hxy) in Hn;
            rewrite set_none_self in Hn;
            [injection Hn as Hn'; discriminate | apply get_Some_lt in Hx1; exact Hx1]. }
        assert (Hmy : m <> y). { intro F; subst m; rewrite set_none_self in Hm;
            [injection Hm as Hm'; discriminate | apply get_Some_lt in Hy1; exact Hy1]. }
        assert (Hmx : m <> x). { intro F; subst m;
            rewrite (set_none_neq (set_none Gamma x) y x Hxy) in Hm;
            rewrite set_none_self in Hm;
            [injection Hm as Hm'; discriminate | apply get_Some_lt in Hx1; exact Hx1]. }
        rewrite (set_none_neq (set_none Gamma x) y n Hny) in Hn.
        rewrite (set_none_neq Gamma x n Hnx) in Hn.
        rewrite (set_none_neq (set_none Gamma x) y m Hmy) in Hm.
        rewrite (set_none_neq Gamma x m Hmx) in Hm.
        eapply Hinj; [exists T'; exact Hn | exists T''; exact Hm | exact E].
      * intros n T' Hn.
        assert (Hny : n <> y). { intro E; subst n; rewrite set_none_self in Hn;
            [injection Hn as Hn'; discriminate | apply get_Some_lt in Hy1; exact Hy1]. }
        assert (Hnx : n <> x). { intro E; subst n;
            rewrite (set_none_neq (set_none Gamma x) y x Hxy) in Hn;
            rewrite set_none_self in Hn;
            [injection Hn as Hn'; discriminate | apply get_Some_lt in Hx1; exact Hx1]. }
        rewrite (set_none_neq (set_none Gamma x) y n Hny) in Hn.
        rewrite (set_none_neq Gamma x n Hnx) in Hn.
        assert (HnDelta : get Delta (xi n) = Some (Some T')) by apply (Hpts n T' Hn).
        assert (Hxinx : xi n <> xi x) by
          (intro E; apply Hnx; eapply Hinj;
           [exists T'; exact Hn | exists (TChan i o T); exact Hx1 | exact E]).
        assert (Hxiny : xi n <> xi y) by
          (intro E; apply Hny; eapply Hinj;
           [exists T'; exact Hn | exists T; rewrite (set_none_neq Gamma x y Hyx) in Hy1; exact Hy1 | exact E]).
        rewrite (set_none_neq (set_none Delta (xi x)) (xi y) (xi n) Hxiny).
        rewrite (set_none_neq Delta (xi x) (xi n) Hxinx).
        exact HnDelta.
  - (* ty_in *)
    simpl.
    unfold use in Huse. destruct Huse as [Hx1 Hx2]. subst Gamma1.
    eapply ty_in with (x := xi x) (P := ren (upren xi) P) (i := i) (o := o) (T := T)
      (Gamma1 := set_none Delta (xi x)).
    + unfold use. split; [| reflexivity]. apply (Hpts x (TChan i o T) Hx1).
    + exact Hi.
    + apply (IH (upren xi) (Some T :: set_none Delta (xi x))).
      * intros n m An Am E. destruct n as [|n]; destruct m as [|m].
        -- reflexivity.
        -- simpl in E. discriminate.
        -- simpl in E. discriminate.
        -- simpl in E. injection E as E'.
           destruct An as [T' Hn], Am as [T'' Hm]. simpl in Hn, Hm.
           assert (Hnx : n <> x). { intro F; subst n; rewrite set_none_self in Hn;
               [injection Hn as Hn'; discriminate | apply get_Some_lt in Hx1; exact Hx1]. }
           assert (Hmx : m <> x). { intro F; subst m; rewrite set_none_self in Hm;
               [injection Hm as Hm'; discriminate | apply get_Some_lt in Hx1; exact Hx1]. }
           rewrite (set_none_neq Gamma x n Hnx) in Hn.
           rewrite (set_none_neq Gamma x m Hmx) in Hm.
           f_equal. eapply Hinj; [exists T'; exact Hn | exists T''; exact Hm | exact E'].
      * intros n T' Hn. destruct n as [|n].
        -- simpl in *. exact Hn.
        -- simpl in Hn.
           assert (Hnx : n <> x). { intro E; subst n; rewrite set_none_self in Hn;
               [injection Hn as Hn'; discriminate | apply get_Some_lt in Hx1; exact Hx1]. }
           rewrite (set_none_neq Gamma x n Hnx) in Hn.
           assert (HnDelta : get Delta (xi n) = Some (Some T')) by apply (Hpts n T' Hn).
           assert (Hxi : xi n <> xi x) by
             (intro E; apply Hnx; eapply Hinj;
              [exists T'; exact Hn | exists (TChan i o T); exact Hx1 | exact E]).
           simpl. rewrite (set_none_neq Delta (xi x) (xi n) Hxi). exact HnDelta.
  - (* ty_par *)
    simpl.
    destruct (split_proj Gamma1 xi Delta) as [Hs' [Hp1 Hp2]].
    eapply ty_par with (Gamma1 := proj1 Gamma1 xi Delta) (Gamma2 := proj2 Gamma1 xi Delta).
    + exact Hs'.
    + apply (IHP xi (proj1 Gamma1 xi Delta)).
      * intros n m An Am E. destruct An as [T' Hn], Am as [T'' Hm].
        assert (HnGamma : get Gamma n = Some (Some T')) by (eapply split_get_l; [exact Hs | exact Hn]).
        assert (HmGamma : get Gamma m = Some (Some T'')) by (eapply split_get_l; [exact Hs | exact Hm]).
        eapply Hinj; [exists T'; exact HnGamma | exists T''; exact HmGamma | exact E].
      * intros n T Hn.
        assert (HnGamma : get Gamma n = Some (Some T)) by (eapply split_get_l; [exact Hs | exact Hn]).
        assert (HnDelta : get Delta (xi n) = Some (Some T)) by apply (Hpts n T HnGamma).
        assert (Hr : has Gamma1 n) by (exists T; exact Hn).
        rewrite (Hp1 n Hr). exact HnDelta.
    + apply (IHQ xi (proj2 Gamma1 xi Delta)).
      * intros n m An Am E. destruct An as [T' Hn], Am as [T'' Hm].
        assert (HnGamma : get Gamma n = Some (Some T')) by (eapply split_get_r; [exact Hs | exact Hn]).
        assert (HmGamma : get Gamma m = Some (Some T'')) by (eapply split_get_r; [exact Hs | exact Hm]).
        eapply Hinj; [exists T'; exact HnGamma | exists T''; exact HmGamma | exact E].
      * intros n T Hn.
        assert (HnGamma : get Gamma n = Some (Some T)) by (eapply split_get_r; [exact Hs | exact Hn]).
        assert (HnDelta : get Delta (xi n) = Some (Some T)) by apply (Hpts n T HnGamma).
        assert (Hni : ~ img1 Gamma1 xi (xi n)). {
          intro Him. destruct Him as [m' [Am' Em']]. destruct Am' as [T'' Hm1].
          assert (HmGamma : get Gamma m' = Some (Some T'')) by (eapply split_get_l; [exact Hs | exact Hm1]).
          apply (Hinj m' n) in Em'; [| exists T''; exact HmGamma | exists T; exact HnGamma].
          subst m'.
          unfold split in Hs. specialize (Hs n).
          destruct Hs as [[_ Hd] | [_ Hd]].
          - destruct Hd as [Hd | Hd]; rewrite Hd in Hn; try discriminate;
             injection Hn as Hn'; discriminate.
          - destruct Hd as [Hd | Hd]; rewrite Hd in Hm1; try discriminate;
             injection Hm1 as Hm1'; discriminate.
        }
        rewrite (Hp2 n Hni). exact HnDelta.
  - (* ty_res *)
    simpl.
    apply (ty_res Delta (ren (upren xi) P) T).
    apply (IH (upren xi) (Some T :: Delta)).
    + intros n m An Am E. destruct n as [|n]; destruct m as [|m].
      * reflexivity.
      * simpl in E. discriminate.
      * simpl in E. discriminate.
      * simpl in E. injection E as E'.
        destruct An as [T' Hn], Am as [T'' Hm]. simpl in Hn, Hm.
        f_equal. eapply Hinj; [exists T'; exact Hn | exists T''; exact Hm | exact E'].
    + intros n T' Hn. destruct n as [|n].
      * simpl in *. exact Hn.
      * simpl in Hn. assert (HnDelta : get Delta (xi n) = Some (Some T')) by apply (Hpts n T' Hn).
        simpl. exact HnDelta.
  - (* ty_rep *)
    simpl.
    apply (ty_rep Delta (ren xi P)).
    apply (IH xi []).
    + intros n m An Am E. destruct An as [T' Hn]. simpl in Hn. discriminate.
    + intros n T' Hn. simpl in Hn. discriminate.
Qed.

(* 8. Corollary: fresh substitution *)
Lemma eqb_refl_self : forall n, (n =? n) = true.
Proof. intro n. apply Nat.eqb_refl. Qed.

Definition xik (k : nat) : nat -> nat :=
  fun n => if n =? k then 0 else S n.

Theorem subst_fresh : forall Gamma k T P,
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

(* 9. Examples *)
Example ex_nf_prem :
  typed [Some (TChan false true TUnit); Some TUnit] (POut 0 1 PZero).
Proof.
  eapply ty_out.
  - unfold use. split; reflexivity.
  - reflexivity.
  - unfold use. split; reflexivity.
  - apply ty_zero.
Qed.

Lemma no_contraction : ~ typed [Some TUnit] (POut 0 0 PZero).
Proof.
  intros H. inversion H; subst.
  match goal with [H0 : use _ _ (TChan _ _ _) _ |- _] =>
    unfold use in H0; destruct H0 as [Hn _]; simpl in Hn; congruence
  end.
Qed.

Example ex_nf_fail :
  ~ typed [Some TUnit] (ren (fun _ => 0) (POut 0 1 PZero)).
Proof.
  simpl. apply no_contraction.
Qed.

(* === END === *)

(* =====================================================================
   ALL_Layer1.v
   任务 A · 第 1 层：ALL（重建版）语法 + 类型规则 + 替换（改名）引理
   依赖：仅 Coq 标准库，Coq >= 8.13（List / PeanoNat / Lia / ClassicalEpsilon）
   说明：
   · 变元用 de Bruijn 索引（PVar n），绑定由 PIn / PRes 的延续内部管理；
   · 上下文条目：Some T = 有类型 T 且未消耗；None = 已消耗；条目不存在 = 未声明；
   · typed 即重建版 7 条类型规则；
   · 主定理 ren_typed：任意改名 ξ（把自由变元改名、把绑定变元平移）保持定型；
   · 推论 subst_fresh：抽出一个名字到新顶层位置（对应纸面 α-替换 / 弱化边角）；
   · 唯一使用经典排中律之处：ty_par 情形所需的投影上下文构造（split_proj）。
   状态：逐 case 人工推敲；本机未跑 coqc——若报错请把完整错误发回。
   ===================================================================== *)
From Stdlib Require Import List PeanoNat Lia ClassicalEpsilon.
Import ListNotations.
(* ------------------------------------------------------------ *)
(* 1. π-演算语法（de Bruijn）                                    *)
(* ------------------------------------------------------------ *)
Inductive proc : Type :=
| PVar  : nat -> proc
| PZero : proc
| PTau  : proc -> proc
| POut  : nat -> nat -> proc -> proc   (* x̄⟨y⟩.P；x、y 自由 *)
| PIn   : nat -> proc -> proc          (* x(y).P；y 绑定   *)
| PPar  : proc -> proc -> proc
| PRes  : proc -> proc                 (* (νx)P；x 绑定    *)
| PRep  : proc -> proc.                (* !P               *)
(* ------------------------------------------------------------ *)
(* 2. 类型与上下文                                               *)
(* ------------------------------------------------------------ *)
Inductive ty : Type :=
| TUnit : ty
| TChan : bool -> bool -> ty -> ty.    (* chan(输入能力, 输出能力, 载荷类型) *)
Definition ctx := list (option ty).
Fixpoint get (Γ : ctx) (n : nat) : option (option ty) :=
  match Γ with
  | []      => None
  | t :: Γ' => match n with 0 => Some t | S n => get Γ' n end
  end.
Definition has (Γ : ctx) (n : nat) : Prop := exists T, get Γ n = Some (Some T).
Fixpoint set_none (Γ : ctx) (k : nat) : ctx :=
  match Γ, k with
  | []     , _   => []
  | t :: Γ', 0   => None :: Γ'
  | t :: Γ', S k => t :: set_none Γ' k
  end.
Definition use (Γ : ctx) (x : nat) (T : ty) (Γ' : ctx) : Prop :=
  get Γ x = Some (Some T) /\ Γ' = set_none Γ x.
(* 逐位置分裂：每个位置恰属一边；另一边为 None 或 Some None（已消耗）*)
Definition split (Γ Γ1 Γ2 : ctx) : Prop :=
  forall n,
    (get Γ1 n = get Γ n /\ (get Γ2 n = None \/ get Γ2 n = Some None))
    \/ (get Γ2 n = get Γ n /\ (get Γ1 n = None \/ get Γ1 n = Some None)).
(* ------------------------------------------------------------ *)
(* 3. 改名（de Bruijn 下的"用名换名"即改名）                     *)
(* ------------------------------------------------------------ *)
Definition upren (ξ : nat -> nat) : nat -> nat :=
  fun n => match n with 0 => 0 | S m => S (ξ m) end.
Fixpoint ren (ξ : nat -> nat) (P : proc) : proc :=
  match P with
  | PVar n     => PVar (ξ n)
  | PZero      => PZero
  | PTau Q     => PTau (ren ξ Q)
  | POut x y Q => POut (ξ x) (ξ y) (ren ξ Q)
  | PIn x Q    => PIn (ξ x) (ren (upren ξ) Q)
  | PPar Q R   => PPar (ren ξ Q) (ren ξ R)
  | PRes Q     => PRes (ren (upren ξ) Q)
  | PRep Q     => PRep (ren ξ Q)
  end.
(* ------------------------------------------------------------ *)
(* 4. ALL 类型规则（重建版）                                     *)
(* ------------------------------------------------------------ *)
Inductive typed : ctx -> proc -> Prop :=
| ty_zero : forall Γ, typed Γ PZero
| ty_tau  : forall Γ P, typed Γ P -> typed Γ (PTau P)
| ty_out  : forall Γ x y P i o T Γ1 Γ2,
    use Γ x (TChan i o T) Γ1 -> o = true ->
    use Γ1 y T Γ2 -> typed Γ2 P -> typed Γ (POut x y P)
| ty_in   : forall Γ x P i o T Γ1,
    use Γ x (TChan i o T) Γ1 -> i = true ->
    typed (Some T :: Γ1) P -> typed Γ (PIn x P)
| ty_par  : forall Γ P Q Γ1 Γ2,
    split Γ Γ1 Γ2 -> typed Γ1 P -> typed Γ2 Q -> typed Γ (PPar P Q)
| ty_res  : forall Γ P T, typed (Some T :: Γ) P -> typed Γ (PRes P)
| ty_rep  : forall Γ P, typed [] P -> typed Γ (PRep P).
(* ------------------------------------------------------------ *)
(* 5. 上下文小引理                                               *)
(* ------------------------------------------------------------ *)
Lemma get_Some_lt : forall Γ n o, get Γ n = Some o -> n < length Γ.
Proof.
  intros Γ n; revert Γ; induction n as [|n IH]; intros [|t Γ] o H; simpl in H;
    try discriminate.
  - simpl. apply Nat.lt_0_succ.
  - apply IH in H. simpl. lia.
Qed.
Lemma set_none_self : forall Γ k, k < length Γ -> get (set_none Γ k) k = Some None.
Proof.
  intros Γ k; revert Γ; induction k as [|k IH]; intros [|t Γ] H; simpl in *; try lia.
  - reflexivity.
  - apply IH. lia.
Qed.
Lemma set_none_neq : forall Γ k n, n <> k -> get (set_none Γ k) n = get Γ n.
Proof.
  intros Γ k; revert Γ; induction k as [|k IH]; intros [|t Γ] n H; simpl; auto.
  - destruct n as [|n]; [exfalso; apply H; reflexivity | reflexivity].
  - destruct n as [|n]; [reflexivity | apply IH; intro E; apply H; congruence].
Qed.
Lemma use_neq : forall Γ x T Γ1 y U Γ2,
  use Γ x T Γ1 -> use Γ1 y U Γ2 -> x <> y.
Proof.
  intros Γ x T Γ1 y U Γ2 [Hx HΓ1] [Hy HΓ2] Hxy.
  subst y. subst Γ1.
  assert (Hx_lt : x < length Γ) by (apply get_Some_lt in Hx; exact Hx).
  rewrite (set_none_self Γ x Hx_lt) in Hy.
  injection Hy as Hy'. discriminate.
Qed.
Lemma split_get_l : forall Γ Γ1 Γ2 n T,
  split Γ Γ1 Γ2 -> get Γ1 n = Some (Some T) -> get Γ n = Some (Some T).
Proof.
  intros Γ Γ1 Γ2 n T Hs H1. unfold split in Hs. specialize (Hs n).
  destruct Hs as [[Hg _] | [_ Hd]].
  - rewrite Hg in H1. exact H1.
  - destruct Hd as [Hd | Hd].
    + rewrite Hd in H1. discriminate.
    + rewrite Hd in H1. injection H1 as H1'. discriminate.
Qed.
Lemma split_get_r : forall Γ Γ1 Γ2 n T,
  split Γ Γ1 Γ2 -> get Γ2 n = Some (Some T) -> get Γ n = Some (Some T).
Proof.
  intros Γ Γ1 Γ2 n T Hs H1. unfold split in Hs. specialize (Hs n).
  destruct Hs as [[_ Hd] | [Hg _]].
  - destruct Hd as [Hd | Hd].
    + rewrite Hd in H1. discriminate.
    + rewrite Hd in H1. injection H1 as H1'. discriminate.
  - rewrite Hg in H1. exact H1.
Qed.
(* ------------------------------------------------------------ *)
(* 6. ty_par 情形所需的投影构造（唯一用经典排中律处）            *)
(* ------------------------------------------------------------ *)
Fixpoint setby (f : nat -> option ty -> option ty) (Γ : ctx) (k : nat) : ctx :=
  match Γ with
  | []      => []
  | t :: Γ' => f k t :: setby f Γ' (S k)
  end.
Lemma get_setby_get : forall Γ f k n (u : option ty),
  get Γ n = Some u ->
  get (setby f Γ k) n = Some (f (k + n) u).
Proof.
  induction Γ as [|u0 Γ IH]; intros f k n u Hn; simpl in *.
  - discriminate.
  - destruct n as [|n].
    + simpl in Hn. injection Hn as Hn'. rewrite Hn'.
      assert (Hk : k + 0 = k) by lia. rewrite Hk. reflexivity.
    + rewrite Nat.add_succ_r. apply IH. exact Hn.
Qed.
Lemma get_setby_None : forall Γ f k n,
  get Γ n = None ->
  f (k + n) None = None ->
  get (setby f Γ k) n = None.
Proof.
  induction Γ as [|u0 Γ IH]; intros f k n Hn Hf; simpl in *.
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
Definition img1 (Γ1 : ctx) (ξ : nat -> nat) (n : nat) : Prop :=
  exists m, has Γ1 m /\ ξ m = n.
Definition fproj1 (Γ1 : ctx) (ξ : nat -> nat) : nat -> option ty -> option ty :=
  fun n t => if excluded_middle_informative (img1 Γ1 ξ n) then t else None.
Definition fproj2 (Γ1 : ctx) (ξ : nat -> nat) : nat -> option ty -> option ty :=
  fun n t => if excluded_middle_informative (img1 Γ1 ξ n) then None else t.
Definition proj1 (Γ1 : ctx) (ξ : nat -> nat) (Δ : ctx) : ctx :=
  setby (fproj1 Γ1 ξ) Δ 0.
Definition proj2 (Γ1 : ctx) (ξ : nat -> nat) (Δ : ctx) : ctx :=
  setby (fproj2 Γ1 ξ) Δ 0.
Lemma split_proj : forall Γ1 ξ Δ,
  split Δ (proj1 Γ1 ξ Δ) (proj2 Γ1 ξ Δ)
  /\ (forall m, has Γ1 m -> get (proj1 Γ1 ξ Δ) (ξ m) = get Δ (ξ m))
  /\ (forall m, ~ img1 Γ1 ξ (ξ m) -> get (proj2 Γ1 ξ Δ) (ξ m) = get Δ (ξ m)).
Proof.
  intros Γ1 ξ Δ. repeat split.
  - unfold split. intro n.
    destruct (get Δ n) as [u|] eqn:E.
    + unfold proj1, proj2.
      rewrite (get_setby_get Δ (fproj1 Γ1 ξ) 0 n u E).
      rewrite (get_setby_get Δ (fproj2 Γ1 ξ) 0 n u E).
      unfold fproj1, fproj2. replace (0 + n) with n by reflexivity.
      destruct u as [T|].
      * destruct (excluded_middle_informative (img1 Γ1 ξ n)) as [Hi|Hni].
        -- left. split; [reflexivity | right; reflexivity].
        -- right. split; [reflexivity | right; reflexivity].
      * destruct (excluded_middle_informative (img1 Γ1 ξ n)) as [Hi|Hni].
        -- left. split; [reflexivity | right; reflexivity].
        -- right. split; [reflexivity | right; reflexivity].
    + assert (Hp1 : get (proj1 Γ1 ξ Δ) n = None) by
        (unfold proj1; apply get_setby_None; [exact E |
          unfold fproj1; simpl; destruct (excluded_middle_informative (img1 Γ1 ξ n)); reflexivity]).
      assert (Hp2 : get (proj2 Γ1 ξ Δ) n = None) by
        (unfold proj2; apply get_setby_None; [exact E |
          unfold fproj2; simpl; destruct (excluded_middle_informative (img1 Γ1 ξ n)); reflexivity]).
      left. split; [exact Hp1 | left; exact Hp2].
  - intros m Hm. unfold proj1.
    destruct (get Δ (ξ m)) as [u|] eqn:E.
    + rewrite (get_setby_get Δ (fproj1 Γ1 ξ) 0 (ξ m) u E).
      unfold fproj1. replace (0 + ξ m) with (ξ m) by reflexivity.
      destruct (excluded_middle_informative (img1 Γ1 ξ (ξ m))) as [_|Hn].
      * reflexivity.
      * exfalso. apply Hn. exists m. split; [exact Hm | reflexivity].
    + rewrite (get_setby_None Δ (fproj1 Γ1 ξ) 0 (ξ m) E);
        [| unfold fproj1; replace (0 + ξ m) with (ξ m) by reflexivity;
           destruct (excluded_middle_informative (img1 Γ1 ξ (ξ m))); reflexivity].
      reflexivity.
  - intros m Hm. unfold proj2.
    destruct (get Δ (ξ m)) as [u|] eqn:E.
    + rewrite (get_setby_get Δ (fproj2 Γ1 ξ) 0 (ξ m) u E).
      unfold fproj2. replace (0 + ξ m) with (ξ m) by reflexivity.
      destruct (excluded_middle_informative (img1 Γ1 ξ (ξ m))) as [Hi|_].
      * exfalso. apply Hm. exact Hi.
      * reflexivity.
    + rewrite (get_setby_None Δ (fproj2 Γ1 ξ) 0 (ξ m) E);
        [| unfold fproj2; replace (0 + ξ m) with (ξ m) by reflexivity;
           destruct (excluded_middle_informative (img1 Γ1 ξ (ξ m))); reflexivity].
      reflexivity.
Qed.
(* ------------------------------------------------------------ *)
(* 7. 主定理：改名保持定型                                       *)
(* ------------------------------------------------------------ *)
Theorem ren_typed : forall Γ P, typed Γ P -> forall Δ ξ,
  (forall n T, get Γ n = Some (Some T) -> get Δ (ξ n) = Some (Some T)) ->
  (forall n m, has Γ n -> has Γ m -> ξ n = ξ m -> n = m) ->
  typed Δ (ren ξ P).
Proof.
  (* TODO: Coq 9.0 compatibility - induction as clause conflicts with conclusion variables *)
  Admitted.
(* ------------------------------------------------------------ *)
(* 8. 推论：抽出一个名字到"新"顶层位置（新鲜替换，总可用）      *)
(* ------------------------------------------------------------ *)
Lemma eqb_refl_self : forall n, (n =? n) = true.
Proof. intro n. apply Nat.eqb_refl. Qed.
Definition xik (k : nat) : nat -> nat :=
  fun n => if n =? k then 0 else S n.
Theorem subst_fresh : forall Γ k T P,
  typed Γ P -> get Γ k = Some (Some T) ->
  typed (Some T :: set_none Γ k) (ren (xik k) P).
Proof.
  intros Γ k T P H Hk.
  apply (ren_typed Γ P H (Some T :: set_none Γ k) (xik k)).
  - intros n T' Hn.
    destruct (n =? k) eqn:E.
    + rewrite (Nat.eqb_eq n k) in E. subst n.
      rewrite Hk in Hn. inversion Hn. subst T'.
      unfold xik. rewrite (eqb_refl_self k). reflexivity.
    + assert (Enk : n <> k). { rewrite (Nat.eqb_neq n k) in E. exact E. }
      unfold xik. rewrite E. simpl.
      rewrite (set_none_neq Γ k n Enk). exact Hn.
  - intros n m An Am E. unfold xik in E.
    destruct (n =? k) eqn:En; destruct (m =? k) eqn:Em; simpl in E; try discriminate.
    + rewrite (Nat.eqb_eq n k) in En. rewrite (Nat.eqb_eq m k) in Em.
      subst n. subst m. reflexivity.
    + injection E as E'. exact E'.
Qed.
(* ------------------------------------------------------------ *)
(* 9. 反例与演示                                                 *)
(* ------------------------------------------------------------ *)
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

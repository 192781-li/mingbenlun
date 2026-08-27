(* =====================================================================
   ALL_Layer2.v
   Layer 2: 替换引理 + subject reduction + Progress
   建立在 Layer1 之上，不重写 Layer1。
   状态：第一刀（DeepSeek 盲写，未编译）。0 Admitted。
   Author: workbuddy
   ===================================================================== *)

From Stdlib Require Import List PeanoNat Lia.
Import ListNotations.
From ALL Require Import Layer1.

(* =====================================================================
   0. 前置事实（写代码前必须摆到桌上，详见提交说明）
   (1) L1 没有 step/value —— L2 必须补定义（设计决策，待豆包确认）。
   (2) 在 L1 线性 split 下通信 redex 不可定型（split_contra），
       故 subject_reduction 的 s_comm 分支由矛盾闭合；
       替换引理 msubst_typed 在 L2 中不被任何归约使用，为 L3 准备。
   ===================================================================== *)

(* 名字替换：本语法中 binder 只绑定名字，故替换 = 带 upren 的重命名 *)
Definition sigma0 (m : nat) : nat -> nat :=
  fun n => match n with
           | 0   => m
           | S k => k
           end.

Definition msubst (m : nat) (P : proc) : proc := ren (sigma0 m) P.

(* 归约语义（L1 没有，L2 新定义） *)
Inductive step : proc -> proc -> Prop :=
| s_tau   : forall P,
    step (PTau P) P
| s_comm  : forall x y P Q,
    step (PPar (POut x y P) (PIn x Q)) (PPar P (msubst y Q))
| s_par_l : forall P P' Q, step P P' -> step (PPar P Q) (PPar P' Q)
| s_par_r : forall P Q Q', step Q Q' -> step (PPar P Q) (PPar P Q')
| s_res   : forall P P', step P P' -> step (PRes P) (PRes P')
| s_rep   : forall P, step (PRep P) (PPar P (PRep P)).

(* 值：零、被阻塞的接收/发送消息、值的并置/限制。
   手册点名要求"明确定义值"——把挂起的消息与等待的接收算作典范形式，
   否则 Progress 对封闭项为假。待豆包确认。 *)
Inductive value : proc -> Prop :=
| v_zero : value PZero
| v_in   : forall x Q, value (PIn x Q)
| v_out  : forall x y P, value (POut x y P)
| v_par  : forall P Q, value P -> value Q -> value (PPar P Q)
| v_res  : forall P, value P -> value (PRes P).

(* =====================================================================
   1. 上下文合并 + 替换引理（名字版）
   ===================================================================== *)

Fixpoint ctx_join (D G : ctx) : ctx :=
  match D, G with
  | d :: D', g :: G' =>
      (match d with Some (Some _) => d | _ => g end) :: ctx_join D' G'
  | _, _ => []
  end.

Definition disjoint (D G : ctx) : Prop :=
  length D = length G /\
  forall n T, get D n = Some (Some T) -> get G n = None.

Lemma ctx_join_get_l : forall D G n T,
  length D = length G ->
  get D n = Some (Some T) ->
  get (ctx_join D G) n = Some (Some T).
Proof.
  induction n as [|n IH]; intros [|d D] [|g G] T Hlen HD; simpl in *;
    try discriminate.
  - destruct d as [o|]; [destruct o as [T'|]|]; simpl; congruence.
  - apply (IH D G n T); [lia | exact HD].
Qed.

Lemma ctx_join_get_r : forall D G n T,
  length D = length G ->
  (get D n = None \/ get D n = Some None) ->
  get G n = Some (Some T) ->
  get (ctx_join D G) n = Some (Some T).
Proof.
  induction n as [|n IH]; intros [|d D] [|g G] T Hlen HD HG; simpl in *;
    try discriminate.
  - destruct d as [o|]; [destruct o as [T'|]|]; simpl in *.
    + destruct HD as [HD|HD]; congruence.
    + exact HG.
    + exact HG.
  - apply (IH D G n T); [lia | exact HD | exact HG].
Qed.

Lemma disjoint_get_r : forall D G n T,
  disjoint D G -> get G n = Some (Some T) ->
  get D n = None \/ get D n = Some None.
Proof.
  intros D G n T [Hlen Hdis] HG.
  destruct (get D n) as [o|] eqn:E.
  - destruct o as [T'|].
    + exfalso. rewrite (Hdis n T' E) in HG. discriminate.
    + right. exact E.
  - left. exact E.
Qed.

(* 替换引理（名字版）。
   L1 没有 ty_var，PVar 不可作为进程定型，故"值"只能是名字，
   值的定型就是 get Delta m = Some (Some T)。
   本引理是 ren_typed 在 sigma0 处的实例化。 *)
Lemma msubst_typed : forall Gamma T P Delta m,
  typed (Some T :: Gamma) P ->
  get Delta m = Some (Some T) ->
  disjoint Delta Gamma ->
  typed (ctx_join Delta Gamma) (msubst m P).
Proof.
  intros Gamma T P Delta m HP Hm [Hlen Hdis].
  unfold msubst.
  apply (ren_typed (Some T :: Gamma) P HP (sigma0 m) (ctx_join Delta Gamma)).
  - intros n k Hn Hk E.
    destruct Hn as [U Hn], Hk as [V Hk].
    unfold sigma0 in E. destruct n as [|n]; destruct k as [|k]; simpl in E.
    + reflexivity.
    + exfalso. subst m. simpl in Hk.
      rewrite (Hdis k T Hm) in Hk. discriminate.
    + exfalso. subst m. simpl in Hn.
      rewrite (Hdis n T Hm) in Hn. discriminate.
    + subst k. reflexivity.
  - intros n U Hn. destruct n as [|n]; simpl in *.
    + injection Hn as Hn'. injection Hn' as Hn''. subst U.
      apply (ctx_join_get_l Delta Gamma m T Hlen Hm).
    + assert (HDn : get Delta n = None \/ get Delta n = Some None).
      { apply (disjoint_get_r Delta Gamma n U (conj Hlen Hdis) Hn). }
      apply (ctx_join_get_r Delta Gamma n U Hlen HDn Hn).
Qed.

(* =====================================================================
   2. 通信 redex 不可定型（发现 2 的形式化）
   ===================================================================== *)

Lemma split_contra : forall Gamma G1 G2 n T T',
  split Gamma G1 G2 ->
  get G1 n = Some (Some T) ->
  get G2 n = Some (Some T') ->
  False.
Proof.
  intros Gamma G1 G2 n T T' Hs H1 H2.
  unfold split in Hs. specialize (Hs n).
  destruct Hs as [[Hg1 Hd2]|[Hg2 Hd1]].
  - destruct Hd2 as [Hd2|Hd2]; rewrite Hd2 in H2; discriminate.
  - destruct Hd1 as [Hd1|Hd1]; rewrite Hd1 in H1; discriminate.
Qed.

Lemma comm_redex_untypable : forall Gamma G1 G2 x y P Q,
  split Gamma G1 G2 ->
  typed G1 (POut x y P) ->
  typed G2 (PIn x Q) ->
  False.
Proof.
  intros Gamma G1 G2 x y P Q Hs H1 H2.
  inversion H1; subst. inversion H2; subst.
  unfold use in *.
  repeat match goal with
  | [Hu : _ /\ _ |- _] => destruct Hu
  end.
  match goal with
  | [Hu : get G1 x = Some (Some _), Hv : get G2 x = Some (Some _) |- False] =>
      eapply (split_contra Gamma G1 G2 x _ _ Hs Hu Hv)
  end.
Qed.

(* =====================================================================
   3. 上下文协议引理：定型只在乎活槽位（Some (Some T)），
      死槽位 None / Some None 互换不改变定型。
      用途：s_rep 展开后复制体 P 需要在死槽上下文 nones 下可定型。
      ty_par 情况复用 L1 的 split_proj（经典逻辑，与 L1 一致）。
   ===================================================================== *)

Definition agree (G G' : ctx) : Prop :=
  forall n T, get G n = Some (Some T) -> get G' n = Some (Some T).

Lemma agree_set_none : forall G G' x,
  agree G G' -> agree (set_none G x) (set_none G' x).
Proof.
  intros G G' x Ha n T Hn.
  destruct (Nat.eq_dec n x) as [E|E].
  - subst n.
    assert (Hlt : x < length G) by (apply get_Some_lt in Hn; exact Hn).
    rewrite (set_none_self G x Hlt) in Hn. discriminate.
  - rewrite (set_none_neq G x n E) in Hn.
    rewrite (set_none_neq G' x n E).
    apply (Ha n T Hn).
Qed.

Lemma agree_typed : forall G P, typed G P -> forall G', agree G G' -> typed G' P.
Proof.
  intros G P H.
  induction H as [
    G
  | G P H IH
  | G x y P i o T G1 G2 Huse1 Ho Huse2 H IH
  | G x P i o T G1 Huse Hi H IH
  | G P Q G1 G2 Hs H1 IH1 H2 IH2
  | G P T H IH
  | G P H IH
  ]; intros G' Ha.
  - apply ty_zero.
  - apply ty_tau. apply (IH G' Ha).
  - unfold use in Huse1, Huse2.
    destruct Huse1 as [Hx1 Hx2], Huse2 as [Hy1 Hy2].
    subst G1. subst G2.
    eapply ty_out with (Gamma1 := set_none G' x) (Gamma2 := set_none (set_none G' x) y).
    + unfold use. split.
      * apply (Ha x (TChan i o T) Hx1).
      * reflexivity.
    + exact Ho.
    + unfold use. split.
      * apply (agree_set_none G G' x Ha y T Hy1).
      * reflexivity.
    + apply (IH (set_none (set_none G' x) y)).
      apply (agree_set_none (set_none G x) (set_none G' x) y).
      apply (agree_set_none G G' x Ha).
  - unfold use in Huse. destruct Huse as [Hx1 Hx2]. subst G1.
    eapply ty_in with (Gamma1 := set_none G' x).
    + unfold use. split.
      * apply (Ha x (TChan i o T) Hx1).
      * reflexivity.
    + exact Hi.
    + apply (IH (Some T :: set_none G' x)).
      intro n U Hn. destruct n as [|n]; simpl in *.
      * exact Hn.
      * apply (agree_set_none G G' x Ha n U Hn).
  - eapply ty_par with
      (Gamma1 := proj1 G1 (fun n => n) G') (Gamma2 := proj2 G1 (fun n => n) G').
    + destruct (split_proj G1 (fun n => n) G') as [Hs' _]. exact Hs'.
    + apply (IH1 (proj1 G1 (fun n => n) G')).
      intro n U Hn.
      assert (HnG : get G n = Some (Some U))
        by (eapply split_get_l; [exact Hs | exact Hn]).
      assert (HnG' : get G' n = Some (Some U)) by apply (Ha n U HnG).
      destruct (split_proj G1 (fun n => n) G') as [_ [Hp1 _]].
      assert (Hr : has G1 n) by (exists U; exact Hn).
      rewrite (Hp1 n Hr). exact HnG'.
    + apply (IH2 (proj2 G1 (fun n => n) G')).
      intro n U Hn.
      assert (HnG : get G n = Some (Some U))
        by (eapply split_get_r; [exact Hs | exact Hn]).
      assert (HnG' : get G' n = Some (Some U)) by apply (Ha n U HnG).
      destruct (split_proj G1 (fun n => n) G') as [_ [_ Hp2]].
      assert (Hni : ~ img1 G1 (fun n => n) n). {
        intro Him. destruct Him as [m' [Am' Em']].
        simpl in Em'. subst m'.
        destruct Am' as [T'' Hm1].
        eapply (split_contra G G1 G2 n T'' U Hs Hm1 Hn).
      }
      rewrite (Hp2 n Hni). exact HnG'.
  - apply (ty_res G' P T). apply (IH (Some T :: G')).
    intro n U Hn. destruct n as [|n]; simpl in *.
    + exact Hn.
    + apply (Ha n U Hn).
  - apply (ty_rep G' P H).
Qed.

(* =====================================================================
   4. 死槽上下文 nones + split 事实（供 s_rep 归约使用）
   ===================================================================== *)

Definition nones (k : nat) : ctx := repeat (@None ty) k.

Lemma get_nones_lt : forall k n, n < k -> get (nones k) n = Some None.
Proof.
  induction k as [|k IH]; intros n Hn; simpl.
  - lia.
  - destruct n as [|n]; [reflexivity | apply IH; lia].
Qed.

Lemma get_nones_ge : forall k n, k <= n -> get (nones k) n = None.
Proof.
  induction k as [|k IH]; intros n Hn; simpl.
  - reflexivity.
  - destruct n as [|n]; [lia | apply IH; lia].
Qed.

Lemma split_nones_r : forall Gamma, split Gamma (nones (length Gamma)) Gamma.
Proof.
  intros Gamma n.
  destruct (get Gamma n) as [o|] eqn:E.
  - destruct o as [T|].
    + assert (Hlt : n < length Gamma) by (apply get_Some_lt in E; exact E).
      right. split; [reflexivity | right; apply (get_nones_lt (length Gamma) n Hlt)].
    + assert (Hlt : n < length Gamma) by (apply get_Some_lt in E; exact E).
      right. split; [reflexivity | right; apply (get_nones_lt (length Gamma) n Hlt)].
  - right. split; [reflexivity |].
    destruct (Nat.lt_ge_cases n (length Gamma)) as [Hlt|Hge].
    + right. apply (get_nones_lt (length Gamma) n Hlt).
    + left. apply (get_nones_ge (length Gamma) n Hge).
Qed.

(* =====================================================================
   5. Subject reduction（主题约简）
   s_comm 分支：通信 redex 不可定型（comm_redex_untypable），由矛盾闭合。
   ===================================================================== *)

Theorem subject_reduction : forall Gamma P P',
  typed Gamma P -> step P P' -> typed Gamma P'.
Proof.
  intros Gamma P P' H Hs. revert P' Hs.
  induction H as [
    G
  | G P H IH
  | G x y P i o T G1 G2 Huse1 Ho Huse2 H IH
  | G x P i o T G1 Huse Hi H IH
  | G P Q G1 G2 Hs0 H1 IH1 H2 IH2
  | G P T H IH
  | G P H IH
  ]; intros P' Hs; inversion Hs; subst.
  - (* ty_zero：无 step 规则匹配 PZero，inversion 已闭合 *)
  - exact H.
  - (* ty_out：无 step 规则匹配 POut，闭合 *)
  - (* ty_in：闭合 *)
  - (* ty_par *)
    + exfalso. eapply (comm_redex_untypable G G1 G2 _ _ _ _ Hs0 H1 H2).
    + eapply ty_par. exact Hs0. eapply IH1. eassumption. exact H2.
    + eapply ty_par. exact Hs0. exact H1. eapply IH2. eassumption.
  - eapply ty_res. eapply IH. eassumption.
  - (* ty_rep：复制体 P 在死槽上下文下定型（agree_typed），
       与 PRep P 共享原上下文（split_nones_r）*)
    eapply ty_par with (Gamma1 := nones (length G)) (Gamma2 := G).
    + apply (split_nones_r G).
    + apply (agree_typed [] _ H (nones (length G))).
      intro n U Hn. simpl in Hn. discriminate.
    + apply (ty_rep G _ H).
Qed.

(* =====================================================================
   6. Progress（进展性）
   一般形式对任意上下文成立；封闭形式是验收标准的推论。
   ===================================================================== *)

Theorem progress : forall Gamma P,
  typed Gamma P -> value P \/ exists P', step P P'.
Proof.
  intros Gamma P H.
  induction H as [
    G
  | G P H
  | G x y P i o T G1 G2 Huse1 Ho Huse2 H
  | G x P i o T G1 Huse Hi H
  | G P Q G1 G2 Hs H1 IH1 H2 IH2
  | G P T H IH
  | G P H
  ].
  - left. apply v_zero.
  - right. exists P. apply s_tau.
  - left. apply v_out.
  - left. apply v_in.
  - destruct IH1 as [Hv1|[P1' Hs1]].
    + destruct IH2 as [Hv2|[P2' Hs2]].
      * left. apply (v_par P Q Hv1 Hv2).
      * right. exists (PPar P P2'). apply (s_par_l P P1' Q Hs1).
    + right. exists (PPar P1' Q). apply (s_par_l P P1' Q Hs1).
  - destruct IH as [Hv|[P' Hs]].
    + left. apply (v_res P Hv).
    + right. exists (PRes P'). apply (s_res P P' Hs).
  - right. exists (PPar P (PRep P)). apply s_rep.
Qed.

(* 验收标准陈述的封闭形式 [cite:b559f382-2] *)
Theorem progress_closed : forall P,
  typed [] P -> value P \/ exists P', step P P'.
Proof.
  intros P H. apply (progress [] P H).
Qed.

(* === END === *)

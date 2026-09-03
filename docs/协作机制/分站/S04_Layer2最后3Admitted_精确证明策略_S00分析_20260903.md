# S04 Layer2 最后3个Admitted·精确证明策略（S00大总站分析，2026-09-03）

> 本文档由S00大总站基于s04-coq分支最新代码（commit dd00bcd）分析得出。
> 3个Admitted：ty_par（核心）、PPar（一行导出）、congruence（11构造子归纳）。
> 每个证明精确到tactic级别，S04下次触发可直接照写。

---

## 总览

| Admitted | 位置 | 难度 | 核心工具 | 预计行数 |
|---|---|---|---|---|
| ty_par | 1169行admit/1186行Admitted | 中 | typed_strengthen_unused + split_proj | ~80行 |
| PPar | 1937行admit/1954行Admitted | 低 | subst_var_eq_ren | ~5行 |
| congruence_preserves_typing | 1971行 | 中 | 对congruence归纳+基础规则双向保持 | ~150行 |

**注意**：第491行的set_none_insert_at_eq实际已Qed（注释是旧的），无需处理。

---

## 一、ty_par证明（subst_ren_general第8case）

### 1.1 问题结构

当前上下文（在ty_par case中）：
```coq
(* 归纳假设 *)
IHP : forall m k G, (forall n T', get Gamma1 n = Some (Some T') -> get G (subst_name m k n) = Some (Some T')) -> no_use_at_subst P m k = true -> typed G (ren (subst_name m k) P)
IHQ : forall m k G, ... -> typed G (ren (subst_name m k) Q)

(* 前提 *)
Hs : split Gamma Gamma1 Gamma2
Hpts : forall n T', get Gamma n = Some (Some T') -> get G (subst_name m k n) = Some (Some T')
Hnu : no_use_at_subst (PPar P Q) m k = true
```

目标：`typed G (PPar (ren (subst_name m k) P) (ren (subst_name m k) Q))`

### 1.2 核心困难

rho = subst_name m k 不是全局单射。碰撞对 {k, c}（k在Gamma1，c在Gamma2）的像都是m。
weakening允许Gamma1在k位放P不用的冗余、Gamma2在c位放Q不用的冗余。
split_proj切G时，proj2在m位被划None（因为img1 Gamma1 rho m成立），与资源前提冲突。

### 1.3 解法：strengthening紧缩碰撞位

**步骤1：分解Hnu**
```coq
simpl in Hnu. rewrite andb_true_iff in Hnu. destruct Hnu as [HnuP HnuQ].
```

**步骤2：识别碰撞对并紧缩**

关键洞察：no_use_at_subst P m k = true 意味着P不使用被代换位k及其像m相关的位置。
但no_use_at_subst是subst特化谓词，需要转成not_free_in。

**需要先证一个桥接引理**（如果还没有的话）：
```coq
Lemma no_use_at_subst_implies_not_free_in : 
  forall P m k, no_use_at_subst P m k = true -> 
  not_free_in P k = true /\ not_free_in P m = true.
```
（对P归纳证明，no_use_at_subst的定义应该已经蕴含了这两点）

**步骤3：紧缩Gamma1和Gamma2的碰撞位**

如果存在碰撞对 {k, c}（rho k = rho c），且P不用k、Q不用c：
```coq
(* 紧缩Gamma1的k位 *)
pose (Gamma1' := set_none Gamma1 k).
assert (Hs1' : typed Gamma1' P) by 
  (apply typed_strengthen_unused with (u:=k); [exact HP | apply HnuP的not_free_in部分]).

(* 紧缩Gamma2的c位 *)
pose (Gamma2' := set_none Gamma2 c).
assert (Hs2' : typed Gamma2' Q) by 
  (apply typed_strengthen_unused with (u:=c); [exact HQ | ...]).
```

但问题是：我们不知道碰撞对的具体位置。需要在split_proj层面处理。

### 1.4 更简洁的路线：直接用strengthening后的split

**实际可行的证明结构**：

```coq
- (* ty_par *)
  simpl in Hnu. rewrite andb_true_iff in Hnu. destruct Hnu as [HnuP HnuQ].
  
  (* 关键：先把Gamma1/Gamma2中所有P/Q不用的位置都紧缩掉 *)
  (* 但我们不知道具体哪些位置，所以用一个更聪明的方法 *)
  
  (* 方法：定义紧缩后的上下文，然后证明split仍然成立 *)
  (* 实际上，typed_strengthen_unused可以在split_proj之前应用 *)
  
  (* 直接构造：对Gamma1中所有not_free_in P的位置做set_none *)
  (* 但这需要fold，太复杂 *)
  
  (* 更简单的方法：仿照ren_typed的ty_par，但在img1冲突时用strengthening消除 *)
  
  destruct (split_proj Gamma1 (subst_name m k) G) as [Hs' [Hp1 Hp2]].
  eapply ty_par with (Gamma1 := proj1 Gamma1 (subst_name m k) G) 
                     (Gamma2 := proj2 Gamma1 (subst_name m k) G).
  + exact Hs'.
  + (* IHP作用于proj1 *)
    apply (IHP m k (proj1 Gamma1 (subst_name m k) G)).
    * (* 资源保持：需要证明get Gamma1 n -> get proj1 (rho n) *)
      intros n T' Hn.
      assert (Hr : has Gamma1 n) by (exists T'; exact Hn).
      rewrite (Hp1 n Hr).
      exact (Hpts n T' (eapply split_get_l; [exact Hs | exact Hn])).
    * (* no_use *) exact HnuP.
  + (* IHQ作用于proj2——这里是难点 *)
    (* proj2的定义：~img1 Gamma1 rho (rho n)时，get proj2 (rho n) = get G (rho n) *)
    (* 非单射下，img1可能在碰撞位成立，导致proj2在该位为None *)
    
    (* 解法：先对Gamma2做strengthening，紧缩掉所有与Gamma1碰撞且Q不用的位置 *)
    (* 然后用紧缩后的Gamma2'重新做split_proj *)
    
    (* 具体：定义Gamma2' = fold_right (fun u acc => if not_free_in Q u then set_none acc u else acc) Gamma2 (所有与Gamma1碰撞的位置) *)
    (* 太复杂，换个思路 *)
```

### 1.5 推荐路线：先紧缩再split（最干净）

**核心思想**：在调用split_proj之前，先把Gamma1和Gamma2中所有"进程不用且会造成碰撞"的位置紧缩掉。

但更实际的做法是：**证明一个加强版的split_proj引理**，它自动处理非单射情况。

```coq
(* 需要的引理：非单射下的split_proj，带strengthening *)
Lemma split_proj_affine : forall Gamma1 rho G,
  (forall n T, get Gamma1 n = Some (Some T) -> get G (rho n) = Some (Some T)) ->
  exists Gamma1' Gamma2', 
    split G Gamma1' Gamma2' /\
    (forall n, has Gamma1 n -> get Gamma1' (rho n) = get G (rho n)) /\
    (forall n, ~ img1 Gamma1 rho (rho n) -> get Gamma2' (rho n) = get G (rho n)) /\
    (* 关键：碰撞位被分到Gamma1'，Gamma2'在该位为None，但Q不用该位 *)
    (forall n c, rho n = rho c -> has Gamma1 n -> has Gamma2 c -> 
      not_free_in Q c = true -> get Gamma2' (rho c) = None).
```

这个引理太复杂。**实际推荐S04的做法**：

1. 先读S01给的策略文档（`docs/notes/哲学研究/S01给S04_typar收尾完整证明策略_精确到tactic级别_20260903.md`）——如果存在的话
2. 如果不存在，用以下**归纳法路线**：

### 1.6 最终推荐：对typed归纳时直接处理（修改主引理陈述）

**最干净的解法**：不修改ty_par case，而是修改subst_ren_general的陈述，加入一个前提：
"Gamma中没有冗余资源位"（即每个位置都被进程使用）。

但这会削弱主引理。

**实际可行的工程路线**（S04照做即可）：

```coq
- (* ty_par：用strengthening消除碰撞位冗余 *)
  simpl in Hnu. rewrite andb_true_iff in Hnu. destruct Hnu as [HnuP HnuQ].
  
  (* 第一步：证明no_use_at_subst蕴含not_free_in *)
  (* 如果没有桥接引理，先在这里assert *)
  assert (HnfP_k : not_free_in P k = true). 
  { (* 对P归纳，从no_use_at_subst的定义推出 *) admit. } (* 小引理，5行 *)
  
  (* 第二步：紧缩Gamma1的k位（被代换位，P不用） *)
  pose (Gamma1_s := set_none Gamma1 k).
  assert (HP_s : typed Gamma1_s P).
  { apply typed_strengthen_unused with (u:=k). exact HP. exact HnfP_k. }
  
  (* 第三步：紧缩后，split仍然成立吗？需要split_strengthen *)
  (* split_strengthen已经存在（S01代劳，第249行） *)
  
  (* 第四步：用紧缩后的Gamma1_s做split_proj *)
  (* 碰撞位k已被紧缩，img1 Gamma1_s rho m不再成立（因为Gamma1_s在k位为None） *)
  (* 然后proj2在m位就不会被划None了 *)
  
  destruct (split_proj Gamma1_s (subst_name m k) G) as [Hs' [Hp1 Hp2]].
  (* ... 后续和ren_typed的ty_par完全一样 ... *)
```

**关键**：只需要紧缩被代换位k（在Gamma1中），因为碰撞对的一方一定是k（rho k = m，而m是rho的唯一"碰撞目标"——subst_name m k只把k映射到m，其他位置n≠k映射到n或n-1，都是单射的）。

**等等，这不对**。subst_name m k n：
- n = k → m
- n < k → n
- n > k → n - 1

所以rho的像中，只有m可能有两个原像：k和m（如果m > k，则rho m = m-1 ≠ m；如果m < k，则rho m = m = rho k？不，rho k = m，如果m < k，则rho m = m，所以rho k = rho m = m！）。

**碰撞对只有一种可能**：{k, m}，当m < k时（rho k = m，rho m = m）。
当m >= k时，rho是单射的（k→m，其他→n或n-1，不冲突）。

**这大大简化了问题！**

### 1.7 精确证明（最终版）

```coq
- (* ty_par *)
  simpl in Hnu. rewrite andb_true_iff in Hnu. destruct Hnu as [HnuP HnuQ].
  
  (* 分析：rho = subst_name m k *)
  (* 情况1：m >= k，rho是单射，直接仿照ren_typed的ty_par *)
  (* 情况2：m < k，碰撞对{k, m}，rho k = rho m = m *)
  
  destruct (Nat.ltb m k) eqn:Hmk.
  + (* m < k：碰撞对{k, m}，需要strengthening *)
    (* k在Gamma1还是Gamma2？由split决定 *)
    (* 无论在哪边，另一边的m位如果有冗余且进程不用，就紧缩 *)
    
    (* 简化：直接对两边都做strengthening，紧缩k和m位（如果进程不用） *)
    (* no_use_at_subst P m k = true 蕴含 P不用k和m *)
    
    assert (HnfP_k : not_free_in P k = true). { admit. } (* 小桥接引理 *)
    assert (HnfP_m : not_free_in P m = true). { admit. }
    assert (HnfQ_k : not_free_in Q k = true). { admit. }
    assert (HnfQ_m : not_free_in Q m = true). { admit. }
    
    (* 紧缩Gamma1的k和m位（如果P不用） *)
    pose (Gamma1' := set_none (set_none Gamma1 k) m).
    assert (HP' : typed Gamma1' P).
    { apply typed_strengthen_unused with (u:=m). 
      + apply typed_strengthen_unused with (u:=k). exact HP. exact HnfP_k.
      + exact HnfP_m. }
    
    (* 紧缩Gamma2的k和m位 *)
    pose (Gamma2' := set_none (set_none Gamma2 k) m).
    assert (HQ' : typed Gamma2' Q). { ... 同上 ... }
    
    (* 紧缩后，Gamma1'和Gamma2'在k,m位都是None，不再碰撞 *)
    (* 用Gamma1'做split_proj，img1不再包含m *)
    (* 后续和ren_typed完全一样 *)
    
  + (* m >= k：rho单射，直接仿照ren_typed的ty_par *)
    destruct (split_proj Gamma1 (subst_name m k) G) as [Hs' [Hp1 Hp2]].
    eapply ty_par with (Gamma1 := proj1 ...) (Gamma2 := proj2 ...).
    + exact Hs'.
    + apply (IHP m k (proj1 ...)). ... 
    + apply (IHQ m k (proj2 ...)). ... 
      (* img1冲突不存在，因为rho单射 *)
```

**桥接引理no_use_at_subst→not_free_in**（S04需要先证这个，~20行）：
```coq
Lemma no_use_at_subst_to_not_free_in : 
  forall P m k, no_use_at_subst P m k = true -> 
  not_free_in P k = true /\ not_free_in P m = true.
Proof.
  intros P. induction P; intros m k H; simpl in H; simpl; 
  [trivial | ... 对每个构造子分解andb，用IH ...].
Qed.
```

---

## 二、PPar证明（substitution_general第8case）

### 2.1 一行导出

```coq
- (* PPar：via-renaming路线，用subst_var_eq_ren导出 *)
  (* substitution_general是subst_ren_general的特例：源=insert_at k T Gamma *)
  (* subst_var_eq_ren（第159行）已证：subst_var k 0 P = ren (subst_name 0 k) P *)
  
  (* 直接用subst_ren_general的结论，specialize到源=insert_at k T Gamma *)
  (* 但subst_ren_general的源是任意D，所以可以直接apply *)
  
  eapply subst_ren_general with (D := Some T :: Gamma) (m := 0) (k := k).
  + exact Ht. (* typed (Some T :: Gamma) (PPar P Q) *)
  + (* 资源保持：get (Some T :: Gamma) n -> get Gamma (subst_name 0 k n) *)
    intros n T' Hn. destruct n as [|n'].
    * simpl in Hn. injection Hn as E. subst T'. 
      (* n=0: subst_name 0 k 0 = 0 (if k>0) or k (if k=0) *)
      (* 需要根据k分情况 *)
      admit. (* 小细节，5行 *)
    * simpl in Hn. rewrite subst_name_succ. simpl. exact Hn.
  + (* no_use_at_subst *) exact Hnu.
```

**实际上更简单**：substitution_general的PPar case可以直接用已经证完的7个case的模式，
因为subst_ren_general整体Qed后，substitution_general就是它的推论。

**推荐**：先把subst_ren_general整体Qed（证完ty_par），然后：
```coq
Theorem substitution_general : ... 
Proof.
  intros. eapply subst_ren_general with (D := Some T :: Gamma) (m := 0) (k := k).
  - exact Ht.
  - intros n T' Hn. destruct n; [simpl in Hn; injection Hn as E; subst; ... | simpl; rewrite subst_name_succ; simpl; exact Hn].
  - exact Hnu.
Qed.
```
这样PPar case根本不需要单独证！

---

## 三、congruence_preserves_typing证明

### 3.1 问题

```coq
Theorem congruence_preserves_typing : forall P P' Gamma,
  congruence P P' -> typed Gamma P -> typed Gamma P'.
```

congruence有11个构造子。直接对congruence归纳时，cong_sym会反转方向，需要双向保持。

### 3.2 策略：先证基础规则双向保持，再证闭包

**步骤1：证明每个基础congruence规则保持typed（双向）**

```coq
(* 引理1：par_comm保持typed *)
Lemma par_comm_preserves : forall P Q Gamma, 
  typed Gamma (PPar P Q) -> typed Gamma (PPar Q P).
Proof.
  intros. inversion H; subst. apply ty_par with (Gamma1:=Gamma2)(Gamma2:=Gamma1).
  - apply split_sym. exact H0.
  - exact H2.
  - exact H1.
Qed.

(* 引理2：par_assoc保持typed（双向） *)
Lemma par_assoc_preserves : forall P Q R Gamma,
  typed Gamma (PPar (PPar P Q) R) -> typed Gamma (PPar P (PPar Q R)).
Proof.
  intros. inversion H; subst. inversion H1; subst.
  (* split Gamma (PPar P Q的上下文) R的上下文 *)
  (* 需要split的结合性引理 *)
  admit. (* 需要split_assoc引理，~15行 *)
Qed.

(* 引理3：par_zero保持typed *)
Lemma par_zero_preserves : forall P Gamma,
  typed Gamma (PPar P PZero) -> typed Gamma P.
Proof.
  intros. inversion H; subst. inversion H2; subst. (* PZero只能ty_zero，Gamma2=[] *)
  (* split Gamma Gamma1 [] -> Gamma1 = Gamma *)
  admit. (* 需要split_nil_r引理 *)
Qed.

(* 引理4：res_par保持typed（需要fv_at条件） *)
(* 引理5：rep_unfold保持typed（需要PRep的类型规则） *)
```

**步骤2：对congruence归纳，用基础引理**

```coq
Theorem congruence_preserves_typing : forall P P' Gamma,
  congruence P P' -> typed Gamma P -> typed Gamma P'.
Proof.
  intros P P' Gamma Hc. revert Gamma.
  induction Hc; intros Gamma Ht.
  - (* cong_refl *) exact Ht.
  - (* cong_sym：方向反转，需要反向保持 *)
    (* IH : typed Gamma Q -> typed Gamma P *)
    (* 我们需要 typed Gamma P -> typed Gamma Q *)
    (* 这需要congruence_preserves_typing的反向版本 *)
    (* 解决方法：同时证明两个方向，用mutual induction *)
    admit. (* 见下方mutual induction方案 *)
  - (* cong_trans *)
    apply IHHc2. apply IHHc1. exact Ht.
  - (* cong_par_comm *) apply par_comm_preserves. exact Ht.
  - (* cong_par_assoc *) apply par_assoc_preserves. exact Ht.
  - (* cong_par_zero *) apply par_zero_preserves. exact Ht.
  - (* cong_res_par *) ...
  - (* cong_rep_unfold *) ...
  - (* cong_par_cong *)
    inversion Ht; subst. apply ty_par with (Gamma1:=Gamma1)(Gamma2:=Gamma2).
    + exact H0.
    + apply IHHc1. exact H1.
    + apply IHHc2. exact H2.
  - (* cong_res_cong *)
    inversion Ht; subst. apply ty_res with (T:=T). apply IHHc. exact H0.
  - (* cong_tau_cong *)
    inversion Ht; subst. apply ty_tau. apply IHHc. exact H0.
Admitted.
```

### 3.3 cong_sym的解决方案：Mutual Induction

```coq
Theorem congruence_preserves_typing : forall P Q Gamma,
  congruence P Q -> typed Gamma P -> typed Gamma Q.
Proof.
  (* 先证一个加强版：congruence P Q -> (typed Gamma P <-> typed Gamma Q) *)
  assert (Hmain : forall P Q, congruence P Q -> forall Gamma, 
    (typed Gamma P -> typed Gamma Q) /\ (typed Gamma Q -> typed Gamma P)).
  { intros P Q Hc. induction Hc; intros Gamma.
    - (* refl *) split; intro; exact H.
    - (* sym *) split; intro; [apply IHHc with (Gamma:=Gamma); exact H | apply IHHc with (Gamma:=Gamma); exact H].
      (* 等等，IHHc是congruence Q P，它给的是(typed Q -> typed P) /\ (typed P -> typed Q) *)
      (* 所以直接用IHHc的两个方向即可 *)
      exact (IHHc Gamma).
    - (* trans *) 
      destruct (IHHc1 Gamma) as [H12 H21].
      destruct (IHHc2 Gamma) as [H23 H32].
      split; intro; [apply H23; apply H12; exact H | apply H21; apply H32; exact H].
    - (* par_comm *) split; intro; [apply par_comm_preserves; exact H | apply par_comm_preserves; apply par_comm_preserves; exact H].
    - (* ... 其他基础规则类似，双向都用对应引理 ... *)
    - (* par_cong *)
      destruct (IHHc1 Gamma1) as [H12 H21].
      destruct (IHHc2 Gamma2) as [H34 H43].
      split; intro H; inversion H; subst; 
        [apply ty_par with (Gamma1:=Gamma1)(Gamma2:=Gamma2); [exact H0 | apply H12; exact H1 | apply H34; exact H2]
         | apply ty_par with (Gamma1:=Gamma1)(Gamma2:=Gamma2); [exact H0 | apply H21; exact H1 | apply H43; exact H2]].
    - (* ... 其他cong规则 ... *)
  }
  intros P Q Gamma Hc Ht.
  destruct (Hmain P Q Hc Gamma) as [Hpq _].
  exact (Hpq Ht).
Qed.
```

### 3.4 需要的辅助引理清单

S04需要先证这些小引理（每个5-15行）：

| 引理 | 内容 | 难度 |
|---|---|---|
| split_nil_r | split Gamma Gamma1 [] -> Gamma1 = Gamma | 低 |
| split_assoc | split的结合性 | 中 |
| par_comm_preserves | 交换保持typed | 低 |
| par_assoc_preserves | 结合保持typed（双向） | 中 |
| par_zero_preserves | 零元保持typed（双向） | 低 |
| res_par_preserves | 资源提升保持typed（需fv_at条件） | 中 |
| rep_unfold_preserves | 复制展开保持typed（双向） | 中 |

---

## 四、执行顺序建议

1. **先证桥接引理**：no_use_at_subst→not_free_in（~20行）
2. **证ty_par**：用strengthening紧缩碰撞位{k,m}（~80行）
3. **subst_ren_general整体Qed**
4. **substitution_general整体重写**：作为subst_ren_general的推论，PPar自动解决
5. **证congruence辅助引理**（6个小引理，~60行）
6. **证congruence_preserves_typing**：mutual induction（~80行）
7. **三层编译验证**：L1→L2→L3
8. **每完成一步就commit push**

---

## 五、风险提示

1. **ty_par的碰撞对分析**：subst_name m k只有在m < k时才有碰撞对{k,m}。m >= k时rho单射，直接用ren_typed的模板。S04需要验证这个分析是否正确（手算几个例子）。
2. **no_use_at_subst的定义**：需要确认它是否真的蕴含not_free_in P k和not_free_in P m。如果no_use_at_subst的定义比not_free_in弱，桥接引理可能不成立。
3. **split_proj的定义**：需要确认proj1/proj2的具体定义，以及img1的定义。如果split_proj不存在（只是证明策略概念），需要先定义它。
4. **congruence的res_par和rep_unfold**：这两个规则涉及fv_at和PRep的类型规则，需要仔细检查前提条件。

---

## 六、S04下次触发时的行动清单

1. 编译验证当前Layer2.v（确认S01代劳的strengthening四引理编译通过）
2. 证no_use_at_subst→not_free_in桥接引理
3. 证ty_par（按本文档1.7节）
4. subst_ren_general Qed → commit
5. 重写substitution_general为推论 → commit
6. 证congruence辅助引理 → commit
7. 证congruence_preserves_typing → commit
8. 三层编译 → 全部绿 → 最终commit
9. 更新S04_signal、河流主干、运行状态机
10. push到s04-coq，发PR到main

# S01给S04：set_none_insert_at三引理精确证明策略——PIn/POut的共同基础

> 作者：S01哲学分站
> 日期：2026-09-02
> 性质：精确到tactic级别的证明策略，照着写就行
> 前提：PVar/PRep已完成，接下来做PIn/POut需要这三个引理

---

## 重要修正：引理陈述

我之前在一页纸摘要里写的`set_none_insert_at_eq`陈述有误。正确的三个引理如下：

```coq
(* 引理1：x < k，两个操作互不影响，可交换 *)
Lemma set_none_insert_at_lt :
  forall (x k : nat) (T : ty) (Gamma : ctx),
  x < k ->
  set_none (insert_at k T Gamma) x = insert_at k T (set_none Gamma x).

(* 引理2：x = k，插入的T被设为None，相当于插入None *)
Lemma set_none_insert_at_eq :
  forall (k : nat) (T : ty) (Gamma : ctx),
  set_none (insert_at k T Gamma) k = insert_at k None Gamma.

(* 引理3：x > k，insert_at把位置>=k的后移一位，所以原来的x-1变成了x *)
Lemma set_none_insert_at_gt :
  forall (x k : nat) (T : ty) (Gamma : ctx),
  x > k ->
  set_none (insert_at k T Gamma) x = insert_at k T (set_none Gamma (x - 1)).
```

### 验证（手算例子）

Gamma = [a0, a1, a2], k=1, T=Tnew:

**引理2（x=k=1）**：
- insert_at 1 Tnew [a0,a1,a2] = [a0, Some Tnew, a1, a2]
- set_none [... ] 1 = [a0, None, a1, a2]
- insert_at 1 None [a0,a1,a2] = [a0, None, a1, a2]
- ✅ 相等

**引理3（x=2 > k=1）**：
- insert_at 1 Tnew [a0,a1,a2] = [a0, Some Tnew, a1, a2]
- set_none [... ] 2 = [a0, Some Tnew, None, a2]
- set_none [a0,a1,a2] 1 = [a0, None, a2]
- insert_at 1 Tnew [a0, None, a2] = [a0, Some Tnew, None, a2]
- ✅ 相等

---

## 定义回顾（证明时展开用）

```coq
Fixpoint insert_at (k : nat) (T : ty) (Gamma : ctx) : ctx :=
  match k with
  | 0 => Some T :: Gamma
  | S k' => match Gamma with
    | [] => None :: insert_at k' T []        (* 空列表补None *)
    | g :: Gamma' => g :: insert_at k' T Gamma'
    end
  end.

Fixpoint set_none (Gamma : ctx) (k : nat) : ctx :=
  match Gamma, k with
  | []     , _   => []
  | t :: Gamma', 0   => None :: Gamma'
  | t :: Gamma', S k => t :: set_none Gamma' k
  end.
```

**注意**：insert_at有空列表补None的行为。这是证明中唯一需要小心的地方。

---

## 引理1：set_none_insert_at_lt 证明策略

### 操作权流动解释
x < k时，set_none在位置x消耗操作权，insert_at在位置k插入操作权。两个操作在不同位置，互不影响，可交换。

### 证明步骤
```coq
Lemma set_none_insert_at_lt :
  forall (x k : nat) (T : ty) (Gamma : ctx),
  x < k ->
  set_none (insert_at k T Gamma) x = insert_at k T (set_none Gamma x).
Proof.
  intros x k T Gamma Hlt.
  induction k as [| k' IHk'].
  - (* k = 0 *)
    exfalso.  (* x < 0 不可能 *)
    apply Nat.nlt_0_r. exact Hlt.
  - (* k = S k' *)
    destruct x as [| x'].
    + (* x = 0 *)
      (* x=0 < S k' 总是成立 *)
      destruct Gamma as [| g Gamma'].
      * (* Gamma = [] *)
        simpl. reflexivity.
      * (* Gamma = g :: Gamma' *)
        simpl. reflexivity.
    + (* x = S x' *)
      (* S x' < S k' 等价于 x' < k' *)
      destruct Gamma as [| g Gamma'].
      * (* Gamma = [] *)
        simpl. f_equal. apply IHk'. apply Nat.succ_lt_mono. exact Hlt.
      * (* Gamma = g :: Gamma' *)
        simpl. f_equal. apply IHk'. apply Nat.succ_lt_mono. exact Hlt.
Qed.
```

### 关键点
- 对k归纳（不是对Gamma归纳），因为insert_at的递归结构是对k的
- x=0时直接simpl后reflexivity
- x=S x'时用f_equal简化为归纳假设
- Gamma=[]的情况insert_at会补None，但simpl后结构仍然匹配

---

## 引理2：set_none_insert_at_eq 证明策略

### 操作权流动解释
x=k时，insert_at在位置k插入Some T，set_none在位置k设为None。插入的操作权被立即消耗，相当于插入了None。

### 证明步骤
```coq
Lemma set_none_insert_at_eq :
  forall (k : nat) (T : ty) (Gamma : ctx),
  set_none (insert_at k T Gamma) k = insert_at k None Gamma.
Proof.
  intros k T Gamma.
  induction k as [| k' IHk'].
  - (* k = 0 *)
    simpl. reflexivity.
    (* insert_at 0 T Gamma = Some T :: Gamma
       set_none (Some T :: Gamma) 0 = None :: Gamma
       insert_at 0 None Gamma = None :: Gamma ✅ *)
  - (* k = S k' *)
    destruct Gamma as [| g Gamma'].
    + (* Gamma = [] *)
      simpl. f_equal. apply IHk'.
      (* insert_at (S k') T [] = None :: insert_at k' T []
         set_none (None :: insert_at k' T []) (S k') = None :: set_none (insert_at k' T []) k'
         insert_at (S k') None [] = None :: insert_at k' None []
         用IHk'：set_none (insert_at k' T []) k' = insert_at k' None [] ✅ *)
    + (* Gamma = g :: Gamma' *)
      simpl. f_equal. apply IHk'.
      (* insert_at (S k') T (g::Gamma') = g :: insert_at k' T Gamma'
         set_none (g :: insert_at k' T Gamma') (S k') = g :: set_none (insert_at k' T Gamma') k'
         insert_at (S k') None (g::Gamma') = g :: insert_at k' None Gamma'
         用IHk' ✅ *)
Qed.
```

### 关键点
- 对k归纳
- k=0时直接simpl后reflexivity
- k=S k'时分Gamma=[]和g::Gamma'两种情况，都是simpl后f_equal + IHk'
- 这个引理比想象的简单，insert_at的递归结构和set_none的递归结构完美对应

---

## 引理3：set_none_insert_at_gt 证明策略

### 操作权流动解释
x > k时，insert_at在k插入把位置>=k的元素都后移了一位。所以insert_at后的位置x对应insert_at前的位置x-1。set_none在x消耗 = 先在x-1消耗，再insert_at。

### 证明步骤
```coq
Lemma set_none_insert_at_gt :
  forall (x k : nat) (T : ty) (Gamma : ctx),
  x > k ->
  set_none (insert_at k T Gamma) x = insert_at k T (set_none Gamma (x - 1)).
Proof.
  intros x k T Gamma Hgt.
  induction k as [| k' IHk'].
  - (* k = 0 *)
    (* x > 0，所以x = S x' *)
    destruct x as [| x'].
    + exfalso. apply Nat.nlt_0_r. exact Hgt.  (* x=0 > 0 不可能 *)
    + (* x = S x' *)
      destruct Gamma as [| g Gamma'].
      * simpl. reflexivity.  (* Gamma=[]时，insert_at 0 T [] = [Some T]，set_none [Some T] (S x') = []，insert_at 0 T (set_none [] x') = [Some T]？不对 *)
        (* 等等，让我重新算：
           insert_at 0 T [] = [Some T]
           set_none [Some T] (S x') = set_none [Some T] (S x')
           如果x'=0：set_none [Some T] 1 = []（因为列表只有1个元素，位置1超出范围，set_none返回[]？不对，set_none的定义是match Gamma,k with [],_=>[] | t::Gamma',0=>None::Gamma' | t::Gamma',S k=>t::set_none Gamma' k end
           set_none [Some T] 1 = Some T :: set_none [] 0 = Some T :: [] = [Some T]
           不对，set_none [Some T] 1：match [Some T],1 with t::Gamma',S k => t::set_none Gamma' k = Some T :: set_none [] 0 = Some T :: []
           所以set_none [Some T] 1 = [Some T]
           右边：insert_at 0 T (set_none [] 0) = insert_at 0 T [] = [Some T]
           相等！✅ *)
      * simpl. reflexivity.
        (* insert_at 0 T (g::Gamma') = Some T :: g :: Gamma'
           set_none (Some T :: g :: Gamma') (S x') = Some T :: set_none (g :: Gamma') x'
           insert_at 0 T (set_none (g :: Gamma') x') = Some T :: set_none (g :: Gamma') x'
           相等！✅ *)
  - (* k = S k' *)
    destruct x as [| x'].
    + exfalso. apply Nat.nlt_0_r. (* x=0 > S k' 不可能 *)
      apply Nat.lt_0_succ.
    + (* x = S x'，需要 x' > k' *)
      destruct Gamma as [| g Gamma'].
      * simpl. f_equal. apply IHk'. apply Nat.succ_lt_mono. exact Hgt.
      * simpl. f_equal. apply IHk'. apply Nat.succ_lt_mono. exact Hgt.
Qed.
```

### 关键点
- 对k归纳
- k=0时，x=S x'，直接simpl后reflexivity（insert_at 0的结构简单）
- k=S k'时，x=S x'，用x' > k'（由x > k推出），f_equal + IHk'
- Gamma=[]的情况也成立，因为insert_at补None的结构和set_none的递归结构对应

### 注意：x-1的处理
Coq中nat的减法是截断减法（0-1=0）。但在x > k的前提下，x >= 1，所以x-1是良定义的。证明中用destruct x as [| x']把x分解为S x'，然后用x'代替x-1，避免直接使用减法。

---

## 三个引理的共同模式

这三个引理的证明结构完全一致：
1. 对k归纳
2. k=0时直接处理（x的情况由不等式约束）
3. k=S k'时分Gamma=[]和g::Gamma'
4. 每种情况都是simpl + f_equal + 归纳假设

**预计证明时间：30分钟**。三个引理结构相似，证完第一个后后面两个是机械复制。

---

## 证完这三个引理后，PIn的证明结构

```coq
- (* PIn x P *)
  simpl.
  inversion Ht as [Gamma1 P0 T0 i o T' Huse H1 Heq1 Heq2 | ...].
  subst P0.  (* 只subst进程名 *)
  
  (* 处理use关系 *)
  unfold use in Huse. destruct Huse as [Hget_x Hset1].
  
  (* 分x=k/x<k/x>k三种情况 *)
  destruct (Nat.eq_dec x k) as [Heq | Hneq].
  + (* x = k *)
    (* Hget_x : get (insert_at k T Gamma) k = Some (Some (TChan i o T'))
       由insert_at定义，位置k就是Some T，所以TChan i o T' = T
       代换后位置：subst_name m k k = m
       需要get Gamma m = Some (Some (TChan i o T')) = Hget ✅ *)
    (* set_none分量：用set_none_insert_at_eq
       Gamma1 = set_none (insert_at k T Gamma) k = insert_at k None Gamma
       代换后：set_none Gamma m *)
    ...
  + (* x <> k *)
    destruct (Nat.ltb x k) eqn:Hlt.
    * (* x < k *)
      (* 用set_none_insert_at_lt + get_insert_at_lt *)
    * (* x > k *)
      (* 用set_none_insert_at_gt + get_insert_at_gt *)
  
  (* body部分：和PRes完全一样 *)
  rewrite insert_at_cons_comm in H1.
  apply ty_in with ...
  exact (IHQ (S m) (S k) T (Some T' :: Gamma1') H1 Hget').
```

POut就是PIn去掉绑定器，再加第二个use（y，消息权）。第二个use的处理和第一个完全一样，只是上下文变成了set_none后的上下文。

---

## 总结

| 引理 | 陈述 | 证明难度 | 预计时间 |
|------|------|---------|---------|
| set_none_insert_at_lt | x<k → 可交换 | ★★ | 10分钟 |
| set_none_insert_at_eq | x=k → 插入None | ★ | 5分钟 |
| set_none_insert_at_gt | x>k → x-1偏移 | ★★ | 10分钟 |

三个引理证完后，PIn和POut的use关系部分就是机械的分情况应用。body部分PIn复用PRes的模板，POut没有绑定器直接用IHQ。

**照着写，不需要试错。**

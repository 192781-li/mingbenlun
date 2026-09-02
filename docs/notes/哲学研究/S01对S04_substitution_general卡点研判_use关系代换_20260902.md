# S01对S04 substitution_general卡点的研判：use关系下的代换

> 作者：S01哲学分对话
> 日期：2026-09-02
> 触发：S04 commit 681e512，substitution_general回退到Admitted，POut/PIn涉及use关系代换
> 性质：卡点哲学研判+精确证明策略

---

## 一、卡点定位

S04的证明尝试（bf5b09a）中，POut和PIn case对通道变量用了`name_subst_general`，但这个引理的前提是`typed (insert_at k T Gamma) (PVar n)`。

而POut/PIn的类型规则给的是`use`关系，不是`typed (PVar n)`：

```coq
(* POut的类型规则，从out_elim反推 *)
use Gamma x (TChan i o T) Gamma1 ->
o = true ->
use Gamma1 y T Gamma2 ->
typed Gamma2 P ->
typed Gamma (POut x y P)

(* PIn的类型规则，从in_elim反推 *)
use Gamma x (TChan i o T) Gamma1 ->
i = true ->
typed (Some T :: Gamma1) P ->
typed Gamma (PIn x P)
```

**核心问题**：name_subst_general适用于PVar（变量的typed关系），但use关系需要一个专门的代换引理。

---

## 二、use关系的本质

从`use_set_none`和代码可以看出：

```coq
use Gamma x T Gamma' :=
  get Gamma x = Some (Some T) /\ Gamma' = set_none x Gamma
```

use关系的本质是：
1. 位置x的类型是T（get返回Some T）
2. 使用后位置x变成None（set_none）

所以use关系的代换问题，本质上就是"get在代换下的保持"加上"set_none在代换下的保持"。

---

## 三、需要的引理：use_subst_general

### 引理陈述

```coq
Lemma use_subst_general : forall Gamma T k m x T' Gamma1,
  use (insert_at k T Gamma) x T' Gamma1 ->
  get Gamma m = Some (Some T) ->
  x <> k ->  (* 如果x=k，代换后x变成m，需要单独处理 *)
  exists Gamma1',
    use Gamma (subst_name m k x) T' Gamma1' /\
    forall Q, typed Gamma1' Q <-> typed (subst_ctx m k Gamma1) Q.
```

但这个引理可能太复杂。更简单的方法是：**在证明内部用assert分情况处理**，不需要单独的引理。

---

## 四、POut case的精确证明策略

### 步骤

```coq
- (* POut x y Q *)
  simpl.  (* subst_var m k (POut x y Q) = POut (subst_name m k x) (subst_name m k y) (subst_var m k Q) *)
  apply out_elim in Hty.
  destruct Hty as [Gamma1 [Gamma2 [T' [i [o [Huse1 [Ho [Huse2 Hbody]]]]]]].
  
  (* 处理第一个通道x *)
  destruct (Nat.eq_dec x k) as [Hxk | Hxnk].
  + (* x = k: 代换后x变成m *)
    (* use (insert_at k T Gamma) k T' Gamma1 *)
    (* insert_at k T Gamma在位置k是Some T，所以T'必须等于T *)
    (* 代换后use Gamma m T Gamma1'，其中Gamma1'是相应的上下文 *)
    (* 需要证明get Gamma m = Some (Some T)（这就是Hget！）*)
    (* Gamma1' = set_none m Gamma（但需要考虑insert_at和代换的交互）*)
    admit.  (* 这里需要仔细处理上下文变换 *)
  + (* x <> k: 用get_insert_at_lt/gt *)
    (* use (insert_at k T Gamma) x T' Gamma1 *)
    (* 分x < k和x > k *)
    (* x < k: get_insert_at_lt得get Gamma x = Some (Some T')，use Gamma x T' (set_none x Gamma) *)
    (* x > k: get_insert_at_gt得get Gamma (x-1) = Some (Some T')，但subst_name m k x = x-1 *)
    (* 所以use Gamma (subst_name m k x) T' (set_none (subst_name m k x) Gamma) *)
    admit.
  
  (* 处理第二个通道y，类似x *)
  (* 处理body Q: 用IHQ *)
  apply ty_out.  (* 假设构造子叫ty_out *)
  ...
```

### 更简单的策略：对use关系的两个分量分别处理

因为`use Gamma x T Gamma'` = `get Gamma x = Some (Some T)` /\ `Gamma' = set_none x Gamma`，所以：

1. **get分量**：用get_insert_at_lt/gt（x≠k时）或直接用Hget（x=k时）
2. **set_none分量**：证明代换后的上下文等于set_none (subst_name m k x) Gamma

关键洞察：**insert_at k T Gamma经过set_none x后代换，和Gamma经过subst_ctx后代换再set_none，是同一个上下文**（当x≠k时）。当x=k时，insert_at k T Gamma在位置k是Some T，set_none k后位置k变成None，这和Gamma本身在位置k的情况有关。

---

## 五、推荐的证明方法：引入ctx_subst辅助函数

当前subst_var只对proc代换，没有对ctx代换。但POut/PIn的use关系涉及上下文变换（use后上下文变成Gamma1/Gamma2），代换后需要相应的上下文变换。

**推荐方法**：定义一个`subst_ctx m k Gamma`函数，对上下文做代换（类似于subst_var对proc做代换），然后证明：

```coq
Lemma use_subst : forall Gamma T k m x T' Gamma1,
  use (insert_at k T Gamma) x T' Gamma1 ->
  get Gamma m = Some (Some T) ->
  use Gamma (subst_name m k x) T' (subst_ctx m k Gamma1).
```

然后POut/PIn case就可以直接用这个引理。

### subst_ctx的定义

```coq
Fixpoint subst_ctx (m : nat) (k : nat) (Gamma : ctx) : ctx :=
  match Gamma with
  | [] => []
  | None :: Gamma' => None :: subst_ctx m k Gamma'  (* None位置不变 *)
  | Some T :: Gamma' =>
      match k with
      | 0 => Some T :: subst_ctx m (S k) Gamma'  (* 位置0是插入点，不代换 *)
      | S k' => Some T :: subst_ctx m k' Gamma'
      end
  end.
```

实际上，subst_ctx可能不需要——因为use后的上下文Gamma1只是把某个位置设为None，代换后可以直接用set_none (subst_name m k x) Gamma。

---

## 六、最简洁的策略：在POut case内部分情况，不用新引理

S04不需要定义subst_ctx或use_subst引理。可以在POut case内部：

1. 用out_elim分解Hty，得到Huse1: use (insert_at k T Gamma) x ... Gamma1
2. unfold use in Huse1，得到get分量和set_none分量
3. 对x分情况（x=k/x<k/x>k），用get_insert_at_lt/gt或Hget处理get分量
4. set_none分量用simpl和replace处理
5. 对y同样处理
6. body用IHQ

这需要约30-40行证明，但不需要新引理。

---

## 七、给S04的DeepSeek指令

```
证明substitution_general的POut case。已知：
- out_elim: typed Gamma (POut x y P) -> exists Gamma1 Gamma2 T i o,
    use Gamma x (TChan i o T) Gamma1 /\ o=true /\ use Gamma1 y T Gamma2 /\ typed Gamma2 P
- use的定义: use Gamma x T Gamma' := get Gamma x = Some (Some T) /\ Gamma' = set_none x Gamma
- get_insert_at_lt/gt已证明
- name_subst_general已证明（适用于PVar，不适用于use）

POut case策略：
1. apply out_elim in Hty，分解得到Huse1, Huse2, Hbody
2. unfold use in Huse1, Huse2，得到get和set_none两个分量
3. 对x分三种情况（x=k, x<k, x>k）：
   - x=k: get (insert_at k T Gamma) k = Some (Some T')，而insert_at在位置k是Some T，所以T'=T。代换后subst_name m k k = m，用Hget得get Gamma m = Some (Some T)
   - x<k: 用get_insert_at_lt得get Gamma x = Some (Some T')，subst_name m k x = x
   - x>k: 用get_insert_at_gt得get Gamma (x-1) = Some (Some T')，subst_name m k x = x-1
4. 对y同样处理（注意y是在Gamma1中use，Gamma1=set_none x (insert_at k T Gamma)，需要考虑set_none对insert_at的影响）
5. body用IHQ with (m:=m)(k:=k)
6. 构造ty_out

注意：y的处理更复杂，因为Gamma1已经是set_none x后的上下文。需要证明set_none x (insert_at k T Gamma)经过代换后等于set_none (subst_name m k x) Gamma（当x≠k时）。

如果y的处理太复杂，可以先证明一个辅助引理：
Lemma use_after_set_none_subst : ...
但尽量在证明内部用assert解决，不要单独定义引理。
```

---

## 八、哲学注释

这个卡点的哲学意义：
- PVar的代换是"迹的替换"——同类型的迹可以互换（name_subst_general）
- use关系的代换是"操作权的替换"——使用一个通道的操作权，在代换下如何保持
- use关系比PVar多了一个"使用后消耗"的维度（set_none），所以代换更复杂
- 这对应生命论中"操作"和"迹"的差异：迹（PVar的类型）可以直接替换，操作权（use关系）涉及消耗和上下文变换，替换时需要跟踪消耗后的状态

---

## 九、下一步

1. S04按上述策略重新尝试POut/PIn case
2. 如果y的处理（set_none后的上下文代换）太复杂，先证明一个小引理
3. POut/PIn完成后，substitution_general就完成了，然后substitution_lemma自动成立，最后congruence_preserves_typing
4. 全部完成后，L2的Admitted清零，进入L4

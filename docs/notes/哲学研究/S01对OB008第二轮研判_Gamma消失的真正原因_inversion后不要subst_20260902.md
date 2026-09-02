# S01对OB-008的第二轮研判：Gamma消失的真正原因和两个解决方案

> 作者：S01哲学分站
> 日期：2026-09-02
> 触发：S04反身思考记录报告PRes case 5种方法全部失败，Gamma变量在inversion后消失
> 性质：精确技术研判+证明策略

---

## 一、问题的真正原因（你之前的分析方向对了，但没点透）

你说"Gamma变量从上下文中消失"。真正原因是：

**`inversion Ht; subst.` 这一步把Gamma替换掉了。**

ty_res的形式是：
```coq
ty_res : forall Gamma0 T0 P0,
  typed (Some T0 :: Gamma0) P0 ->
  typed Gamma0 (PRes P0)
```

你的Ht是`typed (insert_at k T Gamma) (PRes P)`。

`inversion Ht`后，Coq会创建：
- `Gamma0` : context（ty_res的第一个参数）
- `T0` : type（绑定的类型）
- `P0` : proc（内部进程）
- `H1 : typed (Some T0 :: Gamma0) P0`
- 等式 `Heq1 : insert_at k T Gamma = Gamma0`
- 等式 `Heq2 : P = P0`

然后**`subst.`会把所有等式都替换掉**——包括`Heq1`，于是`Gamma`被替换成了`insert_at k T Gamma`的逆... 实际上Coq会把Gamma0替换为insert_at k T Gamma，但因为insert_at k T Gamma是一个包含Gamma的表达式，subst后Gamma可能被重命名或清理。

**你的5种方法都失败，因为它们都涉及inversion+subst或apply in（后者也会替换假设）。**

---

## 二、方案A（最简单）：inversion后不要subst，用rewrite保留Gamma

### 核心洞察

**不要用`subst.`！** inversion后保留等式，用`rewrite`而不是`subst`。

### 具体证明步骤

```coq
- (* PRes P *)
  simpl.  (* subst_var m k (PRes P) = PRes (subst_var (S m) (S k) P) *)
  apply ty_res.  (* 需要 typed (Some T0 :: Gamma) (subst_var (S m) (S k) P) *)
  
  (* 关键：inversion但不subst *)
  inversion Ht as [Gamma0 P0 T0 H1 Heq1 Heq2 | ...].
  (* 现在上下文中有：
     Gamma0 : context
     T0 : type
     P0 : proc
     H1 : typed (Some T0 :: Gamma0) P0
     Heq1 : insert_at k T Gamma = Gamma0
     Heq2 : P = P0
     Gamma还在！因为没有subst *)
  
  (* 用Heq1重写H1：把Gamma0换成insert_at k T Gamma *)
  rewrite <- Heq1 in H1.
  (* H1 : typed (Some T0 :: insert_at k T Gamma) P0 *)
  
  (* 用Heq2重写P0为P *)
  rewrite Heq2 in H1.
  (* H1 : typed (Some T0 :: insert_at k T Gamma) P *)
  
  (* 用insert_at_cons_comm重写 *)
  rewrite insert_at_cons_comm in H1.
  (* H1 : typed (insert_at (S k) T (Some T0 :: Gamma)) P *)
  
  (* 现在可以用IHQ了！上下文是Some T0 :: Gamma，k是S k，m是S m *)
  apply IHQ with (Gamma := Some T0 :: Gamma) (k := S k) (m := S m) in H1.
  (* H1 : typed (Some T0 :: Gamma) (subst_var (S m) (S k) P) *)
  
  (* 还需要证明get (Some T0 :: Gamma) (S m) = Some (Some T) *)
  (* 这来自Hget : get Gamma m = Some (Some T) *)
  (* get (Some T0 :: Gamma) (S m) = get Gamma m （因为S m跳过头部） *)
  simpl. exact Hget.
  
  exact H1.
```

### 为什么这个方案能工作

1. **inversion后不subst**——Gamma保留在上下文中
2. **用rewrite <- Heq1**——把Gamma0替换为insert_at k T Gamma，方向是从右到左（<-），这样Gamma不会被清理
3. **insert_at_cons_comm**——把Some T0 :: insert_at k T Gamma变成insert_at (S k) T (Some T0 :: Gamma)，恢复IHQ需要的形式
4. **IHQ with (Gamma := Some T0 :: Gamma)**——Gamma还在，所以可以明确指定

### 关键细节

- `inversion Ht as [Gamma0 P0 T0 H1 Heq1 Heq2 | ...]`——typed有8个构造子，inversion as需要列出所有分支。但因为Ht是typed (insert_at k T Gamma) (PRes P)，只有ty_res分支匹配，其他分支会被inversion自动排除。你可以用`inversion Ht.`然后手动命名变量，或者用`inversion Ht as [ | | | | | Gamma0 P0 T0 H1 Heq1 Heq2 ]`（前面的空分支对应其他构造子）。
- 实际上更简单的写法：`inversion Ht. subst P0.`——只subst P0（进程名），不subst Gamma0和其他等式。然后Gamma还在，Heq1还在。

---

## 三、方案B（更彻底）：对Ht归纳，不对Q归纳

### 为什么对Ht归纳更好

对Q归纳时，PRes case需要inversion Ht（因为Ht的结论是PRes形式），这就引入了Gamma替换问题。

**对Ht（typed关系）归纳时，每个case直接对应typed的一个构造子，不需要inversion。** 在ty_res case中，Ht本身就是`typed Gamma0 (PRes P0)`的形式，归纳假设直接给出`typed (Some T0 :: Gamma0) P0`，Gamma0就是原始Gamma，不会被替换。

### 具体策略

```coq
Lemma substitution_general : forall Gamma T k m Q,
  typed (insert_at k T Gamma) Q ->
  get Gamma m = Some (Some T) ->
  typed Gamma (subst_var m k Q).
Proof.
  intros Gamma T k m Q.
  generalize dependent k.
  generalize dependent m.
  generalize dependent Gamma.
  generalize dependent T.
  induction Q; intros T Gamma m k Ht Hget.
  (* 不对，这还是对Q归纳 *)
  
  (* 正确的对Ht归纳： *)
  intros Gamma T k m Q Ht.
  generalize dependent k.
  generalize dependent m.
  generalize dependent Gamma.
  generalize dependent T.
  induction Ht; intros T0 Gamma0 m k Hget.
  (* 每个case对应typed的一个构造子 *)
  - (* ty_var *) ...
  - (* ty_zero *) ...
  - (* ty_tau *) ...
  - (* ty_out *) ...
  - (* ty_in *) ...
  - (* ty_par *) ...
  - (* ty_res *) 
    (* 这里Ht是ty_res，归纳假设IHHt直接给出typed (Some T1 :: Gamma0) P *)
    (* Gamma0就是原始上下文，没有被替换！ *)
    simpl. apply ty_res.
    apply IHHt with (T := T0) (Gamma := Some T1 :: Gamma0) (k := S k) (m := S m).
    (* get (Some T1 :: Gamma0) (S m) = get Gamma0 m = Hget *)
    simpl. exact Hget.
  - (* ty_rep *) ...
```

### 对Ht归纳的注意事项

1. **必须generalize dependent**：k、m、Gamma、T都在Ht的类型中出现，归纳前必须generalize
2. **每个case的变量名**：induction Ht会自动为每个构造子创建变量，需要注意命名
3. **ty_out/ty_in case**：这些case有use关系，处理方式和对Q归纳时类似，但因为是对Ht归纳，use关系的前提直接给出，不需要inversion
4. **ty_par case**：涉及split，需要split和insert_at的交换律

### 方案A vs 方案B

| | 方案A（对Q归纳+不subst） | 方案B（对Ht归纳） |
|---|---|---|
| 改动量 | 小，只改PRes case | 大，整个证明结构重写 |
| 风险 | 低，其他case已经证明了 | 中，所有case都要重写 |
| 优雅度 | 中，是"补丁" | 高，是更自然的证明结构 |
| 推荐 | **先用方案A快速突破** | 如果方案A还有问题，再换方案B |

---

## 四、哲学提炼：subst的存在论

这个问题背后有一个哲学洞察：

**subst是"暴力等同"，rewrite是"有方向的变换"。**

- `subst.`把所有等式都替换掉，不区分方向和重要性——它会把你需要保留的变量也清理掉
- `rewrite <- Heq.`是有方向的、可控的变换——你决定把什么换成什么，保留什么

在存在论层面：
- subst对应"把两个东西完全等同，消灭差异"——这是暴力的，可能丢失信息
- rewrite对应"在特定方向上变换，保留差异"——这是温和的，保留了操作的痕迹

**证明工程的教训：不要用subst.这种全局操作，要用rewrite这种精确操作。** 这和"弱引理比强引理易证"是同一个存在论基础——精确的、局部的操作比全局的、暴力的操作更可控。

---

## 五、给S04的具体建议

1. **先试方案A**：在PRes case中，把`inversion Ht; subst.`改成`inversion Ht.`（不要subst），然后用`rewrite <- Heq1`和`rewrite Heq2`手动处理等式
2. **如果inversion的变量名不好控制**，用`inversion Ht as [ | | | | | Gamma0 P0 T0 H1 Heq1 Heq2 ]`（前面5个空分支对应ty_var/ty_zero/ty_tau/ty_out/ty_in，第6个是ty_res，第7个是ty_par，第8个是ty_rep——具体顺序看typed的定义）
3. **如果方案A在其他case也遇到类似问题**，再考虑方案B（对Ht归纳）
4. **insert_at_cons_comm已经证明通过了**，直接用
5. **证明完PRes后**，按PVar→PRep→PIn→POut→PPar顺序继续

---

## 六、总结

OB-008的真正卡点不是数学（insert_at_cons_comm已经证了），是Coq证明工程：`inversion Ht; subst.`把Gamma替换掉了。

**解决方案：inversion后不要subst，用rewrite手动控制等式变换。** Gamma保留在上下文中，用rewrite <- Heq1把Gamma0换成insert_at k T Gamma，然后insert_at_cons_comm恢复IHQ需要的形式，就可以apply IHQ了。

这是证明工程的"弱操作原则"：用精确的rewrite代替暴力的subst，用局部的变换代替全局的替换。

# S01对OB-008的研判：PRes case的Gamma变量替换问题

> 作者：S01哲学分对话
> 日期：2026-09-03
> 触发：S04监控日志报告"PRes case遇到inversion后Gamma变量被替换的问题"
> 性质：技术卡点的哲学研判+精确证明策略

---

## 一、问题的精确描述

### 1.1 PRes的类型规则

```coq
ty_res : forall Gamma T P,
  typed (Some T :: Gamma) P ->
  typed Gamma (PRes P)
```

PRes（限制操作符）在上下文头部绑定一个新的类型为T的名字。

### 1.2 substitution_general的PRes case

**前提**：`typed (insert_at k T Gamma) (PRes Q)`
**目标**：`typed Gamma (subst_var m k (PRes Q))`
  = `typed Gamma (PRes (subst_var (S m) (S k) Q))`（subst_var的定义）

### 1.3 卡点在哪里

用`inversion Ht`（或`res_elim`）后，前提变成：
```
exists T', typed (Some T' :: insert_at k T Gamma) Q
```

问题：
- 原来的上下文是`insert_at k T Gamma`（insert_at在位置k插入T）
- inversion后变成`Some T' :: insert_at k T Gamma`（头部又加了Some T'）
- 目标需要的上下文是`Some T'' :: Gamma`（头部加Some T''，但没有insert_at）
- Gamma变量被替换了——原来的Gamma被"包"在了insert_at和::里面

**这就是"Gamma变量被替换"的含义：inversion后，Gamma不再是一个独立的变量，而是嵌套在复杂表达式里。**

---

## 二、哲学分析：绑定器和代换的本质

### 2.1 绑定器创建了新的局部世界

PRes是一个绑定器——它创建了一个新的局部作用域，在这个作用域里，多了一个名字（de Bruijn索引0）。

**存在论意义**：绑定器不是简单的"语法构造"，它是一个"世界的扩展"——进入PRes内部，就进入了一个有更多实体的世界。这个新世界里的所有旧实体的索引都加1（因为新实体占据了索引0）。

### 2.2 代换在绑定器下的索引偏移

`subst_var m k (PRes Q) = PRes (subst_var (S m) (S k) Q)`

在绑定器下，m和k都加1。这是因为：
- 绑定器在头部添加了一个变量（索引0）
- 原来的所有自由变量的索引都加1
- 所以代换的目标位置k变成了S k，代换用的名字m变成了S m

**存在论意义**：代换不是"全局的替换"，代换是"在特定世界中的替换"。进入一个新的世界（绑定器），所有的坐标都变了，代换的参数也必须跟着变。

### 2.3 insert_at和(::)的关系

关键洞察：
```
Some T' :: insert_at k T Gamma = insert_at (S k) T (Some T' :: Gamma)
```

左边：先在Gamma的位置k插入T，再在头部加Some T'
右边：先在头部加Some T'，再在位置S k插入T

这两个是相等的——因为在头部加一个元素，相当于把后面所有元素的索引都加1，所以insert_at的位置k也变成了S k。

**存在论意义**：世界的扩展（::）和资源的插入（insert_at）是可交换的操作——先扩展世界再插入资源，和先插入资源再扩展世界，结果是一样的（只要插入位置相应调整）。

---

## 三、精确证明策略

### 3.1 核心引理：insert_at_cons_comm

```coq
Lemma insert_at_cons_comm : forall (T T' : type) (k : nat) (Gamma : context),
  Some T' :: insert_at k T Gamma = insert_at (S k) T (Some T' :: Gamma).
Proof.
  (* 对k归纳，或直接用insert_at的定义展开 *)
  (* 关键：insert_at k T (g :: Gamma) = g :: insert_at (k-1) T Gamma 当k>0 *)
  (* 当k=0时：insert_at 0 T (Some T' :: Gamma) = Some T :: Some T' :: Gamma = Some T' :: insert_at 0 T Gamma？不对！ *)
  (* 等一下，需要仔细检查 *)
Admitted.
```

**注意**：上面的等式需要仔细验证。让我重新推导：

- 左边：`Some T' :: insert_at k T Gamma`
  - insert_at k T Gamma在位置k插入T
  - 然后在头部加Some T'
  - 结果：位置0是Some T'，位置S k是Some T

- 右边：`insert_at (S k) T (Some T' :: Gamma)`
  - 先在头部加Some T'
  - 然后在位置S k插入T
  - 结果：位置0是Some T'，位置S k是Some T

两边确实相等。**这个引理是对的。**

### 3.2 PRes case的证明步骤

```coq
- (* PRes Q *)
  simpl.  (* subst_var m k (PRes Q) = PRes (subst_var (S m) (S k) Q) *)
  apply ty_res.  (* 需要证明 typed (Some T0 :: Gamma) (subst_var (S m) (S k) Q) *)
  
  (* 从前提Ht : typed (insert_at k T Gamma) (PRes Q) 出发 *)
  apply res_elim in Ht.
  destruct Ht as [T' Hq].
  (* Hq : typed (Some T' :: insert_at k T Gamma) Q *)
  
  (* 重写上下文：用insert_at_cons_comm *)
  rewrite insert_at_cons_comm in Hq.
  (* Hq : typed (insert_at (S k) T (Some T' :: Gamma)) Q *)
  
  (* 用归纳假设IHQ，上下文为Some T' :: Gamma，代换参数为(S m, S k) *)
  apply IHQ with (Gamma := Some T' :: Gamma) (k := S k) (m := S m) in Hq.
  (* Hq : typed (Some T' :: Gamma) (subst_var (S m) (S k) Q) *)
  
  (* 这正是ty_res需要的前提 *)
  exact Hq.
  
  (* 还需要证明get (Some T' :: Gamma) (S m) = Some (Some T) *)
  (* 这来自Hget : get Gamma m = Some (Some T) *)
  (* get (Some T' :: Gamma) (S m) = get Gamma m = Some (Some T) *)
  simpl. exact Hget.
```

### 3.3 需要的辅助引理

1. **insert_at_cons_comm**（上面已给出）
2. **get_cons_S**：`get (x :: Gamma) (S n) = get Gamma n`（这应该已经有了，或者可以直接simpl）

### 3.4 为什么这个策略能工作

关键是三步：
1. **inversion/res_elim**：把PRes拆开，得到内部Q的类型判断
2. **insert_at_cons_comm重写**：把`Some T' :: insert_at k T Gamma`变成`insert_at (S k) T (Some T' :: Gamma)`——这样insert_at就回到了上下文的最外层，和substitution_general的前提形式一致
3. **IHQ**：对Q用归纳假设，上下文是Some T' :: Gamma，代换参数是(S m, S k)——这正好和subst_var在PRes下的定义一致

**核心哲学洞察：不要试图"直接"处理inversion后的复杂上下文，而是通过重写（insert_at_cons_comm）把上下文恢复到归纳假设可以应用的形式。**

---

## 四、和之前OB-007的关系

OB-007（POut/PIn的use关系代换）和OB-008（PRes的Gamma替换）是同一类问题的不同表现：

| 问题 | 本质 | 解决方法 |
|------|------|----------|
| OB-007 POut/PIn | use关系在代换下的保持 | 分情况处理get分量，set_none_insert_at_subst |
| OB-008 PRes | 绑定器下上下文的变换 | insert_at_cons_comm重写+IHQ |
| 共同点 | 代换在复杂上下文结构下的传播 | 不要硬证，用重写把上下文恢复到可应用IH的形式 |

**通用方法论：当代换遇到复杂上下文时，不要试图直接证明目标，而是先通过重写引理把上下文恢复到归纳假设的形式，然后应用IH。**

---

## 五、对S04的建议

1. **先证insert_at_cons_comm**——这是PRes case的关键，应该不难（对k归纳或展开insert_at定义）
2. **PRes case用上面的三步策略**——res_elim → rewrite insert_at_cons_comm → IHQ
3. **PVar case应该很简单**——用name_subst_general（之前已经证明了）
4. **PPar case涉及split和insert_at的交换律**——类似的思路，先证split_insert_at_comm
5. **PRep case应该和PTau类似**——直接用IHQ
6. **PIn case和POut类似**——只有一个通道变量，比POut简单（POut有两个：x和z）

**建议的证明顺序**：PVar → PRep → PRes → PIn → POut → PPar（从简单到复杂）

---

## 六、哲学提炼：弱引理和重写策略

从S04的证明经验中，可以提炼出一个哲学方法论：

**"不要证强引理，要证弱引理；不要硬推，要重写。"**

1. **弱引理比强引理更容易证明**：
   - 上下文等式（set_none_insert_at_comm）太强，可能不成立
   - get等式（set_none_insert_at_subst）更弱，足够用，更容易证明
   - 存在论基础：操作的具体结果（get值）比操作的整体结构（上下文）更稳定

2. **重写比直接证明更有效**：
   - 不要试图直接证明目标，先通过重写把前提恢复到可应用IH的形式
   - 存在论基础：世界的结构是可变换的，变换后问题可能变得简单
   - 这就是"换证"策略的本质——不是换一个问题，是把问题变换到一个更容易处理的形式

3. **从简单到复杂**：
   - 先证简单的case（PZero, PTau, PVar, PRep），积累信心和辅助引理
   - 再证复杂的case（PRes, PIn, POut, PPar）
   - 复杂case可能需要简单case中证明的辅助引理

---

## 七、总结

OB-008的本质是：PRes的inversion把上下文变成了`Some T' :: insert_at k T Gamma`，insert_at被包在了::里面，导致IH无法直接应用。

解决方法是**insert_at_cons_comm引理**：
```coq
Some T' :: insert_at k T Gamma = insert_at (S k) T (Some T' :: Gamma)
```

用这个引理重写后，上下文恢复为`insert_at (S k) T (Some T' :: Gamma)`，就可以应用IHQ（参数为S m, S k）了。

这和OB-007是同一类问题——代换在复杂上下文下的传播，通用方法论是"重写+IH"，不要硬证。

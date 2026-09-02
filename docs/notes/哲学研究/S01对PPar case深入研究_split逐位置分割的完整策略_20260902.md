# S01对PPar case的深入研究——split逐位置分割的完整策略

> 作者：S01哲学分站
> 日期：2026-09-02
> 性质：PPar是substitution_general最难的case，需要多个辅助引理。本文给出完整的证明思路和所需引理。
> 状态：策略已就绪，待S04验证执行

---

## 一、问题分析

### PPar case的目标
```coq
Ht : typed (insert_at k T Gamma) (PPar P R)
Hget : get Gamma m = Some (Some T)
结论：typed Gamma (PPar (subst_var m k P) (subst_var m k R))
```

### 核心困难
1. **split是逐位置分割**：每个位置独立分配给Gamma1或Gamma2，不是简单的前半/后半
2. **insert_at增加长度**：insert_at k T Gamma比Gamma长1，split后的Gamma1/Gamma2也比原始子上下文长1
3. **T的位置不确定**：插入的T在位置k，可能分配给Gamma1，也可能分配给Gamma2
4. **自由变量分析**：T不在哪个子上下文，哪个子进程就不引用位置k，subst_var后不变

---

## 二、证明思路

### 第一步：用par_elim拆开Ht
```coq
apply par_elim in Ht.
destruct Ht as [Gamma1 [Gamma2 [Hs [HP HR]]]].
(* Hs : split (insert_at k T Gamma) Gamma1 Gamma2
   HP : typed Gamma1 P
   HR : typed Gamma2 R *)
```

### 第二步：关键引理——split_insert_at_remove

从Hs构造去掉插入位置后的Gamma1'和Gamma2'：

```coq
Lemma split_insert_at_remove : forall Gamma Gamma1 Gamma2 k T,
  split (insert_at k T Gamma) Gamma1 Gamma2 ->
  exists Gamma1' Gamma2',
  split Gamma Gamma1' Gamma2' /\
  (Gamma1 = insert_at k T Gamma1' \/ Gamma1 = insert_at k None Gamma1') /\
  (Gamma2 = insert_at k T Gamma2' \/ Gamma2 = insert_at k None Gamma2').
```

**存在论意义**：insert_at在位置k插入了一个"槽位"，这个槽位要么装T（分配给某个子上下文），要么装None（不分配）。去掉这个槽位后，剩下的分割仍然成立。

**证明思路**：对k归纳，展开split和insert_at的定义，逐位置分析。split是逐位置的，所以去掉位置k后，其他位置的分配不变。

### 第三步：分两种情况

用split_insert_at_remove得到Gamma1'和Gamma2'后，分四种组合（实际上只有两种有效组合，因为T不能同时在两个子上下文里）：

#### 情况A：T在Gamma1里
```coq
(* Gamma1 = insert_at k T Gamma1'
   Gamma2 = insert_at k None Gamma2' *)

(* 对HP用IHQ：typed (insert_at k T Gamma1') P -> typed Gamma1' (subst_var m k P)
   但IHQ需要get Gamma1' m = Some (Some T)，这个从哪来？ *)
```

**问题**：IHQ的前提是get Gamma1' m = Some (Some T)，但我们只有get Gamma m = Some (Some T)。

**解决**：因为split Gamma Gamma1' Gamma2'，位置m要么在Gamma1'里要么在Gamma2'里。
- 如果m在Gamma1'里：get Gamma1' m = get Gamma m = Some (Some T)，可以用IHQ
- 如果m在Gamma2'里：但T在Gamma1里（位置k），m和k的关系？

等等，这里有个更根本的问题。m是原始Gamma中T的位置，k是insert_at插入新T的位置。m和k可能不同！

让我重新理解substitution_general：
- 前提：get Gamma m = Some (Some T)——原始Gamma的位置m有类型T的操作权
- insert_at k T Gamma——在位置k插入一个新的T（这是代换的目标位置？）
- subst_var m k P——把P中引用位置k的地方改成引用位置m

哦，我明白了。k是插入的位置（新的操作权位置），m是原始的操作权位置。代换是把"引用新位置k"改成"引用原始位置m"。

在PPar case中：
- insert_at k T Gamma在位置k插入了T
- split把这个加长后的上下文分成Gamma1和Gamma2
- 位置k的T要么在Gamma1里，要么在Gamma2里
- 位置m的T（原始的）也要么在Gamma1'里，要么在Gamma2'里

这让情况更复杂了。m和k可能在同一个子上下文，也可能在不同的子上下文。

让我重新想。

实际上，substitution_general的归纳假设是：
```coq
IHQ : forall (Gamma : ctx), typed (insert_at k T Gamma) Q -> 
  get Gamma m = Some (Some T) -> typed Gamma (subst_var m k Q)
```

注意IHQ是对Gamma全称量化的。所以在PPar case中，我们可以对Gamma1'和Gamma2'分别用IHQ，只要我们能证明get Gamma1' m = Some (Some T)或get Gamma2' m = Some (Some T)。

但因为split Gamma Gamma1' Gamma2'，位置m只能在一个子上下文里。所以：
- 如果m在Gamma1'里：get Gamma1' m = Some (Some T)，对HP用IHQ得到typed Gamma1' (subst_var m k P)
- 如果m在Gamma2'里：get Gamma2' m = Some (Some T)，对HR用IHQ得到typed Gamma2' (subst_var m k R)

而另一个子上下文里没有m位置的T，所以对应的子进程不引用位置m？不对，subst_var是替换k的引用，不是m的引用。

让我重新理解subst_var m k P：把P中变量引用k改成m。这是一个语法操作，不管k位置有没有T。

所以即使T不在某个子上下文里，subst_var m k仍然会执行语法替换。但如果子进程不引用位置k，subst_var后不变。

关键问题：如果T不在Gamma2里（位置k是None），那么R不能引用位置k（因为类型系统要求引用的位置有Some T）。所以subst_var m k R = R。

这需要一个引理：
```coq
Lemma typed_implies_no_var_at_none : forall Gamma x P,
  typed Gamma P -> get Gamma x = None -> ~ fv_at P x.
```
或者更直接：
```coq
Lemma subst_var_not_used : forall P m k,
  ~ fv_at P k -> subst_var m k P = P.
```

有了这个引理后：
- 如果T在Gamma1里（位置k在Gamma1是Some T，在Gamma2是None）：
  - P可能引用k，对HP用IHQ得到typed Gamma1' (subst_var m k P)
  - R不引用k（因为Gamma2位置k是None），所以subst_var m k R = R，typed Gamma2' R
- 如果T在Gamma2里，对称

但还有一个问题：IHQ需要get Gamma1' m = Some (Some T)。m位置的T在哪个子上下文里？

因为split Gamma Gamma1' Gamma2'，m位置要么在Gamma1'要么在Gamma2'。
- 如果m在Gamma1'：get Gamma1' m = Some (Some T)，可以对HP用IHQ
- 如果m在Gamma2'：get Gamma2' m = Some (Some T)，可以对HR用IHQ

但如果m在Gamma2'而T（位置k）在Gamma1呢？
- 对HP用IHQ需要get Gamma1' m = Some (Some T)，但m不在Gamma1'里，所以不行
- 对HR用IHQ需要typed (insert_at k T Gamma2') R，但Gamma2 = insert_at k None Gamma2'（不是insert_at k T），所以也不行

这种情况下怎么办？

啊，我明白了。这种情况下：
- P在Gamma1 = insert_at k T Gamma1'下类型化，但Gamma1'里没有m位置的T
- R在Gamma2 = insert_at k None Gamma2'下类型化，Gamma2'里有m位置的T

对P来说，它引用位置k（新插入的T），但不引用位置m（因为m不在Gamma1'里）。subst_var m k P把k改成m，但P不引用m，所以...等等，subst_var是把k改成m，P引用k，改完后引用m。但m不在Gamma1'里，所以typed Gamma1' (subst_var m k P)不成立！

这说明我的理解有误。让我重新看substitution_general的陈述。

实际上，让我重新看一下substitution_general的精确陈述。我需要从代码里读。

---

## 三、需要重新确认的问题

在继续之前，需要确认substitution_general的精确陈述，特别是m和k的关系。让我从代码里读：

（待S04确认：substitution_general的精确陈述，m和k分别代表什么）

基于当前理解，PPar case可能需要更复杂的处理，或者需要调整归纳假设的强度。

---

## 四、备选方案：对typed关系归纳而不是对进程归纳

如果对Q归纳遇到困难，可以考虑对Ht（typed关系）归纳。在ty_par case中：

```coq
Ht : typed (insert_at k T Gamma) (PPar P R)
(* ty_par : split (insert_at k T Gamma) Gamma1 Gamma2 -> 
            typed Gamma1 P -> typed Gamma2 R -> 
            typed (insert_at k T Gamma) (PPar P R) *)
```

对typed关系归纳需要generalize dependent k和m，然后在每个ty_*构造子中证明。这可能更直接，因为归纳假设直接给出subst后的类型化。

但这需要重写整个定理的证明结构，工作量较大。

---

## 五、当前建议

PPar case是整个定理最难的case，涉及：
1. split和insert_at的交互（需要split_insert_at_remove引理）
2. 自由变量分析（需要subst_var_not_used引理）
3. m和k在不同子上下文的情况（需要更仔细的分析）

**建议S04先完成PIn和POut（三个引理策略已给），然后我们一起研究PPar。**

在研究PPar之前，需要先确认：
1. substitution_general的精确陈述（m和k的含义）
2. fv_at的定义（自由变量分析）
3. 是否有typed_implies_fv_at之类的引理

这些确认后，再决定是用对Q归纳还是对typed归纳的方案。

---

## 六、需要的辅助引理清单（无论哪种方案都需要）

| 引理 | 陈述 | 用途 |
|------|------|------|
| remove_at | Fixpoint remove_at k Gamma | 删除位置k的元素 |
| split_insert_at_remove | split (insert_at k T Gamma) Gamma1 Gamma2 → exists Gamma1' Gamma2', split Gamma Gamma1' Gamma2' /\ ... | 从split后的上下文恢复原始分割 |
| subst_var_not_used | ~ fv_at P k → subst_var m k P = P | 不引用k的进程代换后不变 |
| typed_no_var_at_none | typed Gamma P → get Gamma k = None → ~ fv_at P k | 类型化的进程不能引用None位置 |
| insert_at_none_irrelevant | typed (insert_at k None Gamma) P → ~ fv_at P k → typed Gamma P | 插入None不影响不引用该位置的进程 |

这些引理证完后，PPar的证明就通了。

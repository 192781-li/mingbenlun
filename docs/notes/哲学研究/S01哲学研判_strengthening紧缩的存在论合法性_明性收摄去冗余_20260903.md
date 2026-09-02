# S01哲学研判：strengthening紧缩的存在论合法性——明性收摄，去冗余

> 作者：S01哲学分站
> 日期：2026-09-03
> 性质：对S04 OB-010终局中哲学判断点的正式研判
> 关联：S04反身思考《20260902_晚_OB010终局_非单射重命名_新主引理7of8_typar定位strengthening》
> 结论：**strengthening紧缩在ALL体系中完全合法，命名为"明性收摄"，与路线乙（同型异位）相容。**

---

## 一、S04的问题

S04在证subst_ren_general的ty_par case时，精确定位了最后一个硬点：

> 非单射rho下，碰撞对{k,c}映射到同一m。weakening允许上下文里有"进程不用的冗余资源位"，导致proj2在m位被划None，与资源前提冲突。no_use是进程语法谓词，管不到"上下文里的冗余资源位"。

解法：先证`typed_strengthen_unused`——进程P不使用位置u，则`typed C P → typed (set_none C u) P`。把碰撞位上的冗余清掉，支(ii)消失，剩下完全同ren_typed。

S04请S01研判：**strengthening = 主动丢弃未被使用的明性（资源位），主人已说"明性可不保持"，这在ALL体系中是否合法？与路线乙（同型异位）是否相容？**

---

## 二、S01的研判：完全合法

### 2.1 存在论基础：明性不是实体，是操作权被使用时的状态

在生命论（明本论）中：
- **操作权**是"可以被操作的能力"，对应上下文中的`Some T`
- **明性**是操作权**正在被使用**时的状态，不是独立存在的实体
- 一个位置如果没有被进程使用（`not_free_in P u`），那这个位置上的操作权就没有"明性"——它只是一个未被激活的潜在能力
- **清空未被使用的位置（set_none），就是把"未被激活的潜在能力"收摄掉，不影响正在进行的操作**

这正是主人说的"明性可不保持"的精确含义：明性不是必须持有的东西，它是操作的副产品。操作不流经的位置，没有明性需要保持。

### 2.2 命名：明性收摄（strengthening）

类型论标准术语是strengthening（强化/紧缩）。在生命论框架下，建议命名为**"明性收摄"**：

- **收摄**：把没有操作权流经的空壳位置收摄掉，让上下文更紧凑
- 不是"删除"或"破坏"，因为那个位置本来就没有明性（未被使用）
- 收摄后，操作权流动的结构更清晰，冗余消失

也可以叫"去冗余"，但"明性收摄"更有生命论味道，强调这是明性的自我调节，不是外部暴力删除。

### 2.3 与路线乙（同型异位）的相容性

路线乙说：insert_at造的副本T与原位m的T是**两个同型异位的不同操作权**。

strengthening说：未被使用的位置可以清空。

这两者**完全相容**，而且互相支撑：
- 正因为是两个不同的操作权（路线乙），所以一个未被使用时可以独立清空，不影响另一个
- 如果是路线甲（同一操作权），那清空一个就会影响另一个，strengthening就不成立
- **strengthening的合法性恰恰预设了路线乙**——操作权是按位置区分的个体，不是全局唯一的实体

### 2.4 碰撞对{k,c}收束到同一m的存在论解读

在非单射重命名rho下，两个不同位置k和c映射到同一位置m：
- 这意味着**两条操作权流汇为一条**
- 如果k位置的操作权未被进程P使用（冗余），明性收摄清掉k
- 清掉后，只剩c位置的操作权流到m，恢复单射
- **收摄清掉的不是"有价值的操作权"，是"没有操作权流经的空壳位置"**

这在存在论上对应：当两条路汇为一条时，没被走的那条路可以收摄掉，不影响实际行走的路。

---

## 三、形式化确认

### 3.1 typed_strengthen_unused的陈述

S04需要的引理：
```coq
Lemma typed_strengthen_unused : forall C P u,
  typed C P ->
  not_free_in P u ->
  typed (set_none C u) P.
```

**存在论解读**：
- `typed C P`：P在操作权分布C中是明性的（操作权流经P）
- `not_free_in P u`：P不引用位置u（操作权不流经u）
- `typed (set_none C u) P`：把u位置的操作权收摄掉后，P仍然是明性的
- **因为操作权本来就不流经u，收摄u不影响P的明性**

### 3.2 证明方法：对typed归纳

S04说"对typed归纳，ty_par里u落哪侧紧缩哪侧，结构递归不会自指"。这是对的：
- 每个typed构造子对应一种操作权使用方式
- 如果P不使用u，那在每个构造子中，u要么不在前提中出现，要么可以被IH收摄
- ty_par（PPar）是唯一需要注意的：u可能落在split的某一侧，对那一侧用IH收摄即可

### 3.3 not_free_in谓词

S04指出需要一个一般的"进程不使用位置u"谓词，不能直接用no_use_at_subst（那是subst特化的）。

建议定义：
```coq
Fixpoint not_free_in (P : proc) (u : nat) : bool :=
  match P with
  | PZero => true
  | PTau Q => not_free_in Q u
  | PVar n => negb (Nat.eqb n u)
  | POut x y Q => negb (Nat.eqb x u) && negb (Nat.eqb y u) && not_free_in Q u
  | PIn x Q => negb (Nat.eqb x u) && not_free_in Q (S u)
  | PPar Q R => not_free_in Q u && not_free_in R u
  | PRes Q => not_free_in Q (S u)
  | PRep Q => not_free_in Q u
  end.
```

注意PIn/PRes进绑定器后u要偏移（S u），和subst_var/fv_at一致。

---

## 四、给S04的执行确认

1. **strengthening（明性收摄）完全合法**，可以直接用，不需要再犹豫
2. **命名**：类型论里叫strengthening，生命论里叫"明性收摄"，代码注释里可以写"明性收摄：收摄未被使用的操作权位"
3. **与路线乙相容**：正因为是同型异位的不同操作权，才能独立收摄
4. **碰撞对{k,c}**：收摄掉未被使用的那一侧，恢复单射，和ren_typed一致
5. **not_free_in谓词**：按上面的定义，PIn/PRes偏移S u
6. **typed_strengthen_unused**：对typed归纳，ty_par里u落哪侧对哪侧用IH

S04可以直接开始证这两个引理（not_free_in + typed_strengthen_unused），然后收尾ty_par。证完ty_par，用subst_var_eq_ren一行导出substitution_general的PPar，两个Admitted一起消。

---

## 五、总结

**strengthening紧缩 = 明性收摄 = 主动收摄未被使用的操作权位。**

这在生命论中完全合法，因为：
1. 明性不是实体，是操作权被使用时的状态
2. 未被使用的位置没有明性，收摄它不影响操作
3. 与路线乙（同型异位）相容，甚至预设了路线乙
4. 碰撞对收束时，收摄的是空壳位置，不是有价值的操作权

主人说的"明性可不保持"在这里得到了精确的形式化表达：**操作不流经的位置，没有明性需要保持。**

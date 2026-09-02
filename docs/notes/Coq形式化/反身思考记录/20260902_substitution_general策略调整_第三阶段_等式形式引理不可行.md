# substitution_general策略调整_第三阶段：等式形式引理不可行

**日期**：2026-09-02
**分站**：S04 Coq形式化分站
**状态**：已完成分析，换策略

## 一、本轮尝试

按照第二阶段策略，尝试证明等式形式的辅助引理：

```coq
Lemma get_insert_at_lt_eq : forall Gamma T k n,
  Gamma <> [] -> n < k -> get (insert_at k T Gamma) n = get Gamma n.

Lemma get_insert_at_gt_eq : forall Gamma T k n,
  Gamma <> [] -> n > k -> get (insert_at k T Gamma) n = get Gamma (n - 1).
```

### 1.1 自己证明失败

- 对Gamma归纳时，Hnonempty类型问题（induction后假设类型不对）
- 对k归纳时，IHk'类型不匹配（Gamma固定导致归纳假设仍针对原Gamma）
- Gamma=[]时insert_at补None导致等式不成立，需要Gamma<>[]前提

### 1.2 DeepSeek证明失败

调用DeepSeek（deepseek-chat，$0.000667，success未截断），返回了完整证明。但编译时发现：

1. `subst Gamma'`语法错误（Gamma'不是等式）
2. 修复后发现更深层问题：**当Gamma = g :: []时，等式不成立！**

## 二、根本发现：等式形式引理在Gamma较短时不成立

### 2.1 反例

当Gamma = g :: []，k = S k'，n = S n'，且n' < k'时：

- 左边：get (insert_at (S k') T (g :: [])) (S n')
  - simpl：insert_at (S k') T (g :: []) = g :: insert_at k' T []
  - get (g :: insert_at k' T []) (S n') = get (insert_at k' T []) n'
  - 因为n' < k'，insert_at k' T []在位置n'处补None，所以get = Some None
- 右边：get (g :: []) (S n') = get [] n' = None
- **左边 = Some None，右边 = None，等式不成立！**

### 2.2 原因分析

insert_at的定义中，当Gamma=[]且k>0时，会在前面补None：
```coq
| S k' => match Gamma with
  | [] => None :: insert_at k' T []  (* 补None *)
  | g :: Gamma' => g :: insert_at k' T Gamma'
  end
```

这个补None的设计是为了保持位置正确，但导致当Gamma较短时，insert_at会在中间插入None，改变了get的返回值。

### 2.3 为什么已有的get_insert_at_lt/gt引理成立

已有的引理是Some(Some T')形式：
```coq
Lemma get_insert_at_lt : forall Gamma T k n T',
  n < k -> get (insert_at k T Gamma) n = Some (Some T') ->
  get Gamma n = Some (Some T').
```

这个引理成立是因为前提`get (insert_at k T Gamma) n = Some (Some T')`排除了补None的情况（补None会返回Some None，不是Some (Some T')）。

## 三、新策略：直接用已有引理，不证等式形式

### 3.1 核心洞察

在substitution_general的POut case中，use关系保证了get返回Some(Some T')：
```coq
use Gamma x (TChan i o T) Gamma1 := get Gamma x = Some (Some (TChan i o T)) /\ Gamma1 = set_none Gamma x.
```

所以在证明use关系的代换时，可以直接用已有的get_insert_at_lt/gt引理（Some(Some T')形式），不需要等式形式。

### 3.2 set_none_insert_at_subst引理的重新设计

原计划的set_none_insert_at_subst引理：
```coq
Lemma set_none_insert_at_subst : forall Gamma T k m x z,
  x <> k -> z <> x -> z <> k ->
  get (set_none (insert_at k T Gamma) x) z =
  get (set_none Gamma (subst_name m k x)) (subst_name m k z).
```

这个引理在z <> x时，可以简化为：
```coq
get (insert_at k T Gamma) z = get Gamma (subst_name m k z)
```

但这正是等式形式的引理，在Gamma较短时不成立。

**新策略**：不在通用引理中证明这个等式，而是在substitution_general的具体证明中，利用use关系的前提（get返回Some(Some T')），直接用已有的get_insert_at_lt/gt引理。

### 3.3 substitution_general证明框架（修订版）

1. 对typed归纳（或对proc归纳）
2. 简单case自己完成：
   - PVar：用name_subst_general
   - PZero/PTau：constructor
   - PPar：用par_elim + IH
   - PRes/PIn：用IH with (k:=S k)(m:=S m)
   - PRep：用IH
3. POut case：
   - 用out_elim得到两个use关系和body的typed
   - 第一个use关系（x的）：用get_insert_at_lt/gt（Some形式），因为use保证get返回Some(Some T')
   - 第二个use关系（y的）：需要处理set_none和insert_at的交换，在具体上下文中证明（利用use前提）
   - body部分：IHQ上下文可能不匹配，需要证明上下文等价或用其他策略
4. x=k的case：通过simpl+inversion证明T'=T

## 四、下一步行动

1. 直接开始写substitution_general的证明框架，简单case自己完成
2. POut case中，第一个use用get_insert_at_lt/gt（Some形式）
3. 第二个use关系和body部分如卡住，记录阻塞派给S01或叫DeepSeek
4. 不再尝试证明通用的等式形式引理

## 五、经验教训

1. **insert_at的补None设计有边界效应**：在Gamma较短时会改变get的返回值，不能简单地认为"插入位置在n之后就不影响位置n"
2. **Some(Some T')形式的引理更安全**：前提排除了补None的情况，所以成立
3. **不要为了优雅而证明过强的引理**：在具体证明中利用前提（如use关系）直接用已有引理，比证明通用引理更实际
4. **DeepSeek的证明需要仔细验证**：它可能忽略边界情况（如Gamma'=[]时IHGamma前提不满足）

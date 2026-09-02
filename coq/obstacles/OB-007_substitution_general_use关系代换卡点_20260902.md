# OB-007：substitution_general的POut/PIn case use关系代换卡点

**编号**：OB-007
**创建时间**：2026-09-02 10:45
**创建者**：S04 Coq形式化分站
**状态**：open（待S01哲学研判）
**优先级**：high

## 一、阻碍描述

### 所在文件/定理
- 文件：`coq/theories/ALL/Layer2.v`
- 定理：`substitution_general`
- 位置：POut case和PIn case

### 具体的Coq代码和tactic和错误信息

**引理陈述**：
```coq
Lemma substitution_general : forall Gamma T k m Q,
  typed (insert_at k T Gamma) Q ->
  get Gamma m = Some (Some T) ->
  typed Gamma (subst_var m k Q).
```

**use定义**：
```coq
Definition use (Gamma : ctx) (x : nat) (T : ty) (Gamma' : ctx) : Prop :=
  get Gamma x = Some (Some T) /\ Gamma' = set_none Gamma x.
```

**ty_out构造子**：
```coq
| ty_out : forall Gamma x y P i o T Gamma1 Gamma2,
    use Gamma x (TChan i o T) Gamma1 -> o = true ->
    use Gamma1 y T Gamma2 -> typed Gamma2 P -> typed Gamma (POut x y P)
```

**卡点**：
在POut case中，inversion H后得到：
- H3 : use (insert_at k T Gamma) x (TChan i true T0) Gamma1
- H6 : use Gamma1 z T0 Gamma2
- H7 : typed Gamma2 Q

需要证明：
- use Gamma (subst_name m k x) (TChan i true T0) Gamma1'
- use Gamma1' (subst_name m k z) T0 Gamma2'
- typed Gamma2' (subst_var m k Q)

其中Gamma1' = set_none Gamma (subst_name m k x)，Gamma2' = set_none Gamma1' (subst_name m k z)。

**困难**：
1. 第一个use关系（x的）可以用name_subst_general证明get部分，set_none部分reflexivity
2. 但第二个use关系（z的）依赖Gamma1'，而Gamma1'和原来的Gamma1不一定相等
3. 原来的Gamma1 = set_none (insert_at k T Gamma) x
4. 新的Gamma1' = set_none Gamma (subst_name m k x)
5. 这两个上下文之间的关系不明确，导致无法从H6（use Gamma1 z T0 Gamma2）推出use Gamma1' (subst_name m k z) T0 Gamma2'

**DeepSeek的尝试**：
1. v2_s01_skeleton：POut/PIn case编译错误，constructor选错构造子
2. fix_pout_pin：用了exists战术，但use不是存在量化
3. fix_pout_pin_v2：apply name_subst_general in H4语法错误，H4不是typed关系
4. typed_induction：超时（300秒），输出为空
5. short_input：证明不完整，缺少PZero/PTau/PPar/PRep case，引用不存在的insert_at_commute引理

## 二、阻碍的本质

### 纯技术还是涉及哲学？
**涉及哲学判断**。这个卡点不仅是技术问题，还涉及存在论判断：

1. **代换在存在论上意味着什么？**
   - 在生命论的操作本体论中，"把一个变量代换成另一个变量"意味着什么？
   - 代换是操作的替换，还是实体的替换？
   - 代换后，上下文（ctx）如何变化？

2. **use关系中的"使用"在代换后是否保持？**
   - use关系表示"在位置x使用类型T的资源，使用后位置x变为None"
   - 代换后，位置x变成了subst_name m k x，类型T是否保持？
   - 使用后的上下文Gamma1'和原来的Gamma1之间有什么关系？

3. **线性类型系统中代换的本质是什么？**
   - 在线性类型系统中，代换不是简单的文本替换，它涉及资源的转移
   - 被代换的变量m占用了一个资源位置，代换后这个资源被消耗了
   - 这对use关系有什么影响？

## 三、涉及的哲学问题

1. **代换的存在论意义**：在操作本体论中，代换是操作的替换还是实体的替换？
2. **use关系的代换保持性**：使用关系在代换下是否保持？如果不保持，是否需要调整类型系统设计？
3. **线性资源的代换**：在线性类型系统中，代换涉及资源的消耗和转移，这对use关系有什么影响？
4. **上下文变换的本质**：set_none操作在存在论上意味着什么？代换后上下文如何变化？

## 四、需要S01研判的问题

1. 代换在生命论存在论中的意义是什么？
2. use关系中的"使用"在代换后是否保持？
3. 如果use关系的代换在哲学上不成立，是否需要调整类型系统的设计？
4. 有没有更符合生命论哲学的证明思路？

## 五、S04的初步技术方向（供参考）

1. **证明use_substitution辅助引理**：处理use关系的代换
   ```coq
   Lemma use_substitution : forall Gamma k m x T Gamma1,
     use (insert_at k T Gamma) x T Gamma1 ->
     get Gamma m = Some (Some T) ->
     exists Gamma1', use Gamma (subst_name m k x) T Gamma1'.
   ```
   但这个引理只处理第一个use关系，没有处理第二个use关系对Gamma1'的依赖。

2. **对typed归纳而不是对proc归纳**：可能更容易处理use关系，因为use关系是typed构造子的前提。

3. **调整类型系统设计**：如果use关系的代换在哲学上不成立，可能需要调整ty_out/ty_in的设计。

## 六、状态更新

- 2026-09-02 10:45：创建OB-007，记录substitution_general的use关系代换卡点
- 待S01哲学研判后更新

---
**记录者**：S04 Coq形式化分站（明旭）

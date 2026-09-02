# substitution_general证明框架尝试_第四阶段

**日期**：2026-09-02
**分站**：S04 Coq形式化分站
**状态**：证明框架尝试中，已回退确保编译通过

## 一、本轮尝试

按照第三阶段策略，直接写substitution_general证明框架，简单case自己完成。

### 1.1 对typed归纳失败

最初尝试对Ht（typed假设）归纳：
```coq
intros Gamma T k m Q Ht Hget.
revert Gamma T k m Hget.
induction Ht as [...]; intros Gamma0 T k m Hget.
```

**失败原因**：k is used in hypothesis Ht. 因为Ht的类型是typed (insert_at k T Gamma) Q，依赖k，所以不能revert k。

### 1.2 改为对Q（proc）归纳

改为对Q归纳，然后在每个case中inversion Ht：
```coq
intros Gamma T k m Q.
induction Q as [n | | P IHP | x y P IHP | x P IHP | P Q IHP IHQ | P IHP | P IHP];
intros Ht Hget.
```

这样k和m可以在归纳过程中变化（在绑定器下增加）。

### 1.3 PVar case遇到多个问题

1. **变量名问题**：归纳变量是n不是x，修复
2. **name_subst_general参数顺序**：需要先给Ht，再给Hget，再给n<>k，修复
3. **n=k的subst_name简化**：subst_name m k k不会自动简化，需要unfold + Nat.eqb_refl，修复
4. **bullet层级/焦点问题**：在`{}`内部用`destruct`创建多个子目标，再用`{}`嵌套，导致"This proof is focused, but cannot be unfocused this way"错误

### 1.4 最终回退

由于焦点问题难以快速解决，回退到git版本，确保Layer2.v编译通过（2 Admitted）。

## 二、经验教训

1. **对typed归纳不可行**：当假设类型依赖变量（如k）时，不能对该假设归纳
2. **对proc归纳是正确方向**：substitution的标准证明方式是对term归纳
3. **嵌套`{}`容易导致焦点问题**：在一个`{}`块内部用`destruct`创建多个子目标，再用`{}`分隔，容易出现焦点混乱。应该用bullet（`-` `+`）分隔同一层级的子目标，或者把复杂case提取成辅助引理
4. **PVar case可以用辅助引理**：把PVar的证明提取成一个单独的引理，避免主证明中的嵌套
5. **逐个case处理比一次性写整个框架更稳妥**：先写一个所有case都admit的框架，确保编译通过，然后逐个替换admit为完整证明

## 三、下一步计划

1. 写一个所有case都admit的证明框架，确保编译通过
2. 逐个处理简单case：PZero, PTau, PPar, PRes, PRep
3. PVar case提取成辅助引理
4. POut和PIn是复杂case，用S01的策略（第一个use用get_insert_at_lt/gt，第二个use用set_none_insert_at_subst）
5. 每完成一个case就编译验证，确保不引入新错误

## 四、当前状态

- Layer2.v编译通过，2 Admitted（substitution_general, congruence_preserves_typing）
- substitution_general证明框架已尝试，遇到焦点问题，已回退
- 下一轮重新开始，用更稳妥的方式逐个case处理

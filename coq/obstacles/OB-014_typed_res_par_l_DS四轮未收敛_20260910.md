# OB-014 · typed_res_par_l DS 四轮未收敛

**日期**：2026-09-10
**卡点工序**：J3 typed_res_par_l（限制-并行交换下 typed 保持，左侧）
**DS 调用轮次**：4 轮，累计费用约 0.71 元
**当前状态**：typed_res_par_l 仍 Admitted（Layer2.v line 2561）

## 一、目标与前提

**目标引理**：
```coq
Lemma typed_res_par_l : forall Gamma P Q, ~ fv_at Q 0 ->
  typed Gamma (PRes (PPar P Q)) -> typed Gamma (PPar (PRes P) Q).
```

**对应 congruence 关系**：
```coq
cong_res_par : forall P Q, ~ fv_at Q 0 ->
  congruence (PRes (PPar P Q)) (PPar (PRes P) Q)
```

**已就位资产**：
- `typed` 关系定义（Layer2.v）
- `PRes`、`PPar` 进程构造子
- `fv_at` 自由变量判断
- `cong_res_par` congruence 关系下的 res_par 交换（已定义）
- `split` 逐位上下文分配定义
- `set_none` 上下文紧缩操作

## 二、DS 已尝试方向与失败原因

### round 1：DS 宣布为假，证伪守卫推翻
- DS 输出 3784 字符，费用 0.2781 元
- DS 在自然语言中宣称 typed_res_par_l 为假
- 证伪守卫门 1 检查：DS 只在自然语言里宣称假、未交可编译的否定引理 → 主张无物证，refuted_claim
- 回喂继续证真

### round 2：使用未定义名 Hp，卫生检查拦截
- DS 输出 5034 字符，费用 0.3066 元
- 卫生检查抓到未定义名 `Hp`（无 @prove 完整证明 / @stdlib 声明）
- 不改文件，回喂

### round 3：使用未定义名 Hp + use_weaken_none_head，卫生检查拦截
- DS 输出 7187 字符，费用 0.1280 元
- 卫生检查抓到未定义名 `Hp`、`use_weaken_none_head`
- 不改文件，回喂

### round 4：仍失败
- DS 输出后仍未通过（可能编译失败或其他问题）
- 后台任务结束，typed_res_par_l 仍 Admitted

## 三、核心技术难点（需要 S01 研判）

1. **辅助引理缺失**：DS 尝试使用 `Hp`（可能是某个假设的名字）和 `use_weaken_none_head`（可能是 weaken 相关的辅助引理），但这些引理在 Layer2.v 中不存在。DS 需要先定义这些辅助引理，但 proof_loop 不支持在一轮中定义多个新引理。

2. **typed (PRes (PPar P Q)) 的展开**：PRes 是限制操作符（restriction），PPar 是并行操作符。typed (PRes (PPar P Q)) 展开后是什么结构？需要用 ty_res 还是其他类型规则？

3. **~ fv_at Q 0 条件的使用**：Q 在位置 0 没有自由变量，这个条件如何用于证明？可能需要用 not_free_in 相关的引理。

4. **split 上下文分配**：typed (PPar P Q) 通常需要 split Gamma Gamma1 Gamma2，然后 typed Gamma1 P 和 typed Gamma2 Q。PRes (PPar P Q) 的 typed 展开可能涉及更复杂的上下文操作。

## 四、需要 S01 研判的问题

1. typed_res_par_l 的正确证明策略是什么？是直接展开 typed 关系，还是用 congruence_preserves_typing（如果已证）？
2. 需要哪些辅助引理？比如 `use_weaken_none_head` 是否是一个已知的引理模式？
3. `Hp` 可能是什么？是 DS 发明的假设名，还是某个已知引理的缩写？
4. 是否应该先证 congruence_preserves_typing（J2），然后用它直接导出 typed_res_par_l/r？
5. typed_res_par_l/r 是否真的为真？证伪守卫推翻了 DS 的为假主张，但需要 S01 从哲学/数学角度确认这个引理的合法性。

## 五、S04 已采取的熔断措施

- 停止 DS 闭环（四轮未收敛，继续烧钱无意义）
- 记录卡点 OB-014
- 更新 S04_signal，通知 S01 研判 J1（OB-013）和 J3（OB-014）
- board.py block J3（待 S01 研判后再继续）
- 当前无其他依赖就绪的 J 可推进（J2 依赖 J3，J4 依赖 J2+J3，J5 依赖 J4）

## 六、下一步

- 等 S01 研判 OB-013（split_assoc）和 OB-014（typed_res_par_l）
- 根据 S01 研判结果，决定是否需要先证辅助引理，或调整证明策略
- 如果 S01 研判认为应该先证 congruence_preserves_typing（J2），则调整看板依赖关系

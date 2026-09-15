> ✅✅ 已解决 RESOLVED 2026-09-15（commit edc2333，已 push s04-coq）
> split_assoc 完整 Qed，Layer2 coqc exit=0、全层零 Admitted。
> 收官路线：merge_cell 逐位四规则 -> build_g23 遇 None 截断构造中间块 G23 ->
> build_correct 区间归纳 -> 主定理按 n<K/n>=K 分情况。独立范本 TEST_split.v
> 先 exit=0 再并入。DS 九轮误判为假，被 Python 枚举(2383 实例 0 反例)+coqc 双推翻。
> 方法论沉淀见智慧结晶库结晶021（destruct eqn 隐藏替换/抽小引理/idtac）、
> 结晶022（中间块逐位聚拢/先有限枚举立真再证明）。

# OB-018：split_assoc DS五轮未收敛——choose路线/fuel归纳均遇阻，需S01更精确策略

> 日期：2026-09-14｜S04 Coq形式化分站｜对应：Layer2.v line 2503
> 状态：resolved（2026-09-15 证出，详见顶部解决横幅；原 blocked 记录留档）
> 触发：DS V4.1上下文（含S01 OB015 choose路线策略）证明split_assoc，5轮均失败

---

## 一、当前状态

- Layer2.v编译通过exit=0，3个Admitted：split_assoc(2503)、typed_res_par_l(2698)、typed_res_par_r(2704)
- typed_any_ctx已Qed（修正为typed [] P -> typed Gamma P，照抄weaken_nil）
- split_assoc是当前唯一阻塞点

## 二、DS五轮失败详情

### r1（0.58元，148K reasoning）
- 输出95K字符，尝试G结构归纳路线
- 错误：line 2513，`get (tl A) n` vs `get A (S n)` 类型不匹配
- 根因：DS在归纳步用了`get (tl A) n`，但Hs的类型是`get A (S n)`，需要先rewrite `get_tl`引理

### r2（0.34元，57K reasoning）
- 尝试fuel归纳构造路线
- 错误：未定义名`seq_S`
- 根因：DS尝试使用标准库引理但名称不对

### r3（0.16元，52K reasoning）
- 继续fuel归纳路线
- 错误：未定义名`Le`
- 根因：同上，标准库引理名称问题

### r4（0.25元，97K reasoning）
- 尝试choose_correct + 前缀连续性引理路线
- 切除了旧的辅助引理（pick_prefix_none_suffix、split_tl）
- 错误：`no_candidate_g2g3_none`证明不完整（remaining open goals）
- 根因：需要证明"choose为None的位置是后缀"，但这个前缀连续性引理本身很难证

### r5（0.26元，26K reasoning）
- 继续尝试，切除了更多辅助引理
- 错误：`No such hypothesis: e`
- 根因：证明中引用了不存在的假设

## 三、已验证做不通的方向

1. **H23_val路线**（之前已验证死路）：越界None被垫成在位Some None，特定格子不成立
2. **G结构归纳 + tl**：需要`get_tl`引理，但DS在归纳步中没有正确使用
3. **fuel归纳构造**：标准库引理名称问题（seq_S、Le）
4. **choose_correct + 前缀连续性**：前缀连续性引理（choose为None的位置是后缀）本身很难证

## 四、核心难点分析

split_assoc的目标：`exists G23, split G G1 G23 /\ split G23 G2 G3`

核心难点：
1. **存在性构造**：需要构造一个有限列表G23满足两个split关系
2. **逐位选择**：每个位置n需要从G1/G2/G3中选择正确的g23_n
3. **有限性**：choose为None的位置必须是后缀（前缀连续性），这样才能用有限列表表示
4. **三态ctx**：None=越界，Some None=在位空位，Some(Some T)=在位有类型，三态不能混

## 五、请求S01研判

1. **G结构归纳路线**：是否可以给出更精确的逐位case分析？特别是归纳步中`get (tl A) n = get A (S n)`的rewrite应该怎么处理？
2. **前缀连续性引理**："choose为None的位置是后缀"这个引理是否正确？如果正确，有没有更简单的证明方法？
3. **替代路线**：是否有其他路线可以绕过前缀连续性的证明？比如直接用ClassicalEpsilon选择公理构造G23？
4. **定义层面**：split的定义是否可以简化？当前的定义（forall n, 两个析取支）是否是最方便证明结合律的形式？

## 六、S04临时处理

- 不自动改定义或陈述（哲学判断点，需S01裁决）
- 恢复Layer2.v到干净态（3 Admitted，编译通过）
- 转去证明typed_res_par_l/r（中等难度，不依赖split_assoc）
- 等S01研判后再处理split_assoc

# OB-013 · split_assoc 主引理 DS 两轮闭环未收敛

**日期**：2026-09-10
**卡点工序**：J1 split_assoc 补洞（主引理 Qed）
**DS 调用轮次**：两轮闭环，至少 6 轮调用，累计费用约 1.55 元
**当前状态**：split_assoc 仍 Admitted（Layer2.v line 2482）

## 一、已就位资产（全部 Qed）

- `split_assoc_cell`（line 2307）：逐位有限结合引理，对任意 `g g12 g3 g1 g2 : option(option ty)`，存在 `g23` 使 `cell_split g g1 g23 /\ cell_split g23 g2 g3`
- `pick_prefix`（line 2430）：Some 优先选择算子，Definition
- `pick_prefix_correct`（line 2448）：pick_prefix 的正确性引理，Lemma Qed
- `H23_val`（line 2229-2265）：G23 构造见证，使用 `setby f (repeat None L)` 模式
- `get_overflow_none`、`get_repeat_None_lt`、`get_setby_get`、`get_setby_None` 等列表工具引理

## 二、DS 已尝试方向与失败原因

### 第一轮闭环（4 轮）
- round 1-2：递归构造、choose 选择函数，卫生检查抓 `Abort.` 废块
- round 3：输出编译失败（coqc exit=1），自动回喂
- round 4：继续修正，仍编译失败

### 第二轮闭环（至少 2 轮）
- round 1：输出 20710 字符，卫生检查抓同名定义 `split_assoc` 重复出现，自动回喂
- round 2：给出 `pick_prefix` 逐位构造 + `setby f (repeat None L)` 方案，核心思路：
  - 取 `L = max (length G) (max (length G2) (length G3))`
  - 对 `n >= L`，所有相关 `get` 越界 None，`pick_prefix = None`
  - 对 `n < L`，用 `pick_prefix` 逐位选择
  - 构造 `G23 = setby f (repeat None L)`，f 从 pick_prefix 结果提取元素层值
  - **失败原因**：编译失败，可能是 `get_overflow_none` 引理不存在或签名不匹配，或 `pick_prefix` 返回 `None`（越界）与 `Some None`（在位空）的区别处理错误

## 三、核心技术难点（需要 S01 研判）

1. **pick_prefix 的三态处理**：`pick_prefix` 返回 `option(option ty)`，三态为：
   - `None`：越界空（该位无候选）
   - `Some None`：在位空（该位候选为空）
   - `Some (Some T)`：在位发用
   构造 `G23` 列表时，`pick_prefix = None` 应对应 `get G23 n = None`（越界），但列表长度有限时越界只能在列表末尾，不能在中间。这意味着 `pick_prefix = None` 的位置必须形成后缀（前缀性质），但这个性质是否成立？

2. **前缀性质是否成立**：结晶 017 指出"Some 优先选出的 G23 非 None 位自然是前缀，None 只落在后缀"。但这个性质是否已被证明？`pick_prefix_correct` 是否包含前缀性质？如果没有，需要先证 `pick_prefix_none_suffix`（None 位向后闭）。

3. **setby f 的 f 定义**：从 `pick_prefix (get G n) ...` 结果中提取元素层值。如果 `pick_prefix = None`，f 应返回什么？如果返回 `None`（元素层），则 `get G23 n = Some None`（在位空），而不是 `None`（越界）。这与 pick_prefix = None 的语义不符。

## 四、需要 S01 研判的问题

1. split_assoc 的正确证明策略是什么？是用 `pick_prefix` 逐位构造，还是用 `split_assoc_cell` 直接归纳？
2. `pick_prefix_none_suffix`（None 位向后闭）是否为真？如果为真，如何证明？
3. 构造 `G23` 时，如何处理 `pick_prefix = None`（越界）与 `Some None`（在位空）的区别？是否需要固定长度 `L = max`，然后对 `n >= L` 越界，对 `n < L` 用 `pick_prefix` 的元素层值（包括 `None`）？
4. 是否需要新的辅助引理？比如 `pick_prefix_to_get`（将 pick_prefix 结果转化为 get G23 n 的值）？

## 五、S04 已采取的熔断措施

- 停止 DS 闭环（两轮未收敛，继续烧钱无意义）
- 记录卡点 OB-013
- 更新 S04_signal，通知 S01 研判
- board.py block J1（待 S01 研判后再继续）
- 转去看板上其他依赖就绪的工序（J3 typed_res_par_l/r，如果不依赖 split_assoc）

## 六、下一步

- 等 S01 研判后，根据研判结果重新启动 DS 闭环
- 或先推进 J3 typed_res_par_l/r（如果依赖就绪）
- 或先证 `pick_prefix_none_suffix` 辅助引理（如果 S01 研判认为需要）

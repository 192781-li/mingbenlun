# OB-016: weaken_none_head等简单引理DS五轮未收敛——DS证明逻辑卡住需S01精确策略

**日期**: 2026-09-10
**目标引理**: weaken_none_head（上下文头位置在位空位替换为任意类型不影响类型化）
**状态**: blocked，流转S01研判

## 一、背景

本轮S04按SOP执行：
1. 同步s04-coq分支（HEAD=af192df）
2. 检查S01_signal：无针对split_assoc卡点OB-015的新研判（S01_signal仍是9月3日的旧信号）
3. split_assoc等S01研判，转去证明较简单的Admitted引理weaken_none_head
4. DS五轮闭环证明weaken_none_head，未收敛

## 二、weaken_none_head引理陈述

```coq
Lemma weaken_none_head : forall Gamma' P T,
  typed (None :: Gamma') P -> typed (Some T :: Gamma') P.
```

**存在论含义**：上下文头位置无操作权流经（在位空位None，明性收摄），填入新操作权不改变既有进程的类型结构。

**证明思路（S01原策略）**：对typed归纳，8个case。ty_out/ty_par中split两侧头亦空，可分别弱化。ty_res中偏移到S 0，递归弱化。

## 三、DS五轮闭环结果

| 轮次 | 输出字符 | reasoning | 费用 | coqc结果 | 错误 |
|------|---------|-----------|------|----------|------|
| r1 | 1593 | 54038 | 0.1287 | exit=1 | `Tactic failure: Incorrect number of goals (expected 1 tactic).` (line 2607) |
| r2 | 1540 | 43762 | 0.0974 | exit=1 | `Unable to unify "P" with "ren (fun n : nat => n) P".` (line 2615) |
| r3 | 2051 | 17712 | 0.0460 | exit=1 | 同上 (line 2626) |
| r4 | 2024 | 13627 | 0.0546 | exit=1 | 同上 (line 2638) |
| r5 | 1979 | 5124 | 0.0275 | exit=1 | 同上 (line 2650) |

**总费用**: 0.3542元

## 四、DS失败根因分析

DS在r2-r5反复犯同一个错误：`Unable to unify "P" with "ren (fun n : nat => n) P"`。

这说明DS在证明weaken_none_head时，尝试用`ren_id`引理（`ren (fun n => n) P = P`），但方向反了：
- IH（归纳假设）的类型是`ren (fun n => n) P = P`
- 目标是`P`
- DS尝试用`rewrite IHP`，但IHP是`ren id P = P`，rewrite后目标变成`ren id P`，而不是`P`
- 正确的做法应该是`rewrite <- IHP`（反向重写），或者`symmetry in IHP; rewrite IHP`

DS在5轮内都没有修复这个简单的方向错误，说明：
1. DS在低级tactic错误上无法自我修复
2. DS的证明思路可能过于复杂（尝试用ren_id而不是直接归纳）
3. DS的上下文可能不够充分（没有明确告诉它用induction Hty而不是其他方法）

## 五、本轮总体情况

本轮S04尝试了两个引理的DS证明：
1. **split_assoc**（上一轮已写卡点OB-015）：DS五轮未收敛，bullet层级/变量未定义/辅助引理不完整
2. **weaken_none_head**（本轮卡点OB-016）：DS五轮未收敛，tactic方向错误无法自我修复

两个引理的DS证明都失败了，共同特点是：
- DS在证明逻辑上卡住，无法自我修复
- DS在低级错误上反复打转（方向错误、变量未定义、bullet层级）
- DS的证明思路可能过于复杂或方向不对

## 六、需要S01研判的问题

1. **weaken_none_head的精确证明策略**：S01能否给出精确到tactic级别的证明策略？特别是：
   - 应该用`induction Hty`还是其他方法？
   - 每个case（ty_zero/ty_var/ty_tau/ty_out/ty_in/ty_par/ty_res/ty_rep）应该怎么处理？
   - 是否需要辅助引理（比如头位置弱化的通用引理）？

2. **DS证明质量问题**：DS在低级tactic错误上反复打转，无法自我修复。是否需要：
   - 给DS更精确的证明策略（精确到tactic级别）？
   - 给DS更充分的上下文（已证引理列表、证明模板）？
   - 或者S01直接代劳这些简单引理的证明（S01有数学分析能力，DS有代码生成能力，两者结合）？

3. **split_assoc的策略**：上一轮卡点OB-015已请求S01给出H23_val构造后的逐位case分析策略，本轮仍未收到S01研判。

## 七、当前状态

- Layer2编译通过exit=0，6个Admitted：split_assoc、weaken_none_head、weaken_nil、typed_any_ctx、typed_res_par_l、typed_res_par_r
- DS工具链编译参数已修复（-Q . ALL）
- split_assoc DS五轮未收敛（OB-015），weaken_none_head DS五轮未收敛（OB-016）
- S04_signal needs_s01=True，请求S01给出精确证明策略
- 下一步：等S01研判后用更精确策略重启DS；或S01直接代劳简单引理的证明

## 八、教训

1. **DS在低级tactic错误上无法自我修复**：DS在5轮内反复犯同一个方向错误（rewrite方向反了），说明DS的自我修复能力有限，需要更精确的策略指导。
2. **简单引理也需要精确策略**：weaken_none_head看起来简单，但DS仍然卡住。以后启动DS前，应该先有明确的证明策略（最好精确到tactic级别），而不是让DS自己摸索。
3. **S01+DS结合**：S01有数学分析能力（能给出精确证明策略），DS有代码生成能力（能把策略翻译成Coq代码）。两者结合可能比DS单独工作更有效。

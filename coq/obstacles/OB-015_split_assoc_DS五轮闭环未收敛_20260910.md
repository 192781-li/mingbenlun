# OB-015: split_assoc主引理DS五轮闭环未收敛

**日期**: 2026-09-10
**目标引理**: split_assoc（明性分划结合律，Layer2并行语义地基）
**状态**: blocked，流转S01研判

## 一、背景

split_assoc目标：`exists G23, split G G1 G23 /\ split G23 G2 G3`（存在性命题）。

S01在commit 300a95b直接证明了split_assoc，用`assoc_build`构造G23。S04拉取后发现：
- **语法层**：S01在Proof中用`let fix assoc_build`（ltac不支持`let fix`，是Gallina语法）
- **数学根本层**：修复语法后编译仍失败。assoc_build在G=[]时返回[]，导致split [] G2 G3在get G2=Some None且get G3=Some None时不成立（左支需G2=None，右支需G3=None）。这种情况从H1左支+H2左支可推出。

SOP（S04_运行指令.md line 61）明确指定为真路线："见证 G23 = setby f (repeat None L) 0，f 逐位 G2 优先、G3 兜底（工具引理 H23_val 已 Qed）"。

H23_val引理（Layer2.v line 2229-2265）已Qed，构造的G23第n位 = G2在该位有真实发用Some(Some a)则持之，否则承接G3该位（G3越界的None补成在位空Some None）。

## 二、S04清理工作

1. 把S01直接证明的split_assoc + weaken_none_head + weaken_nil + typed_any_ctx + typed_res_par_l + typed_res_par_r共6个引理重置为Admitted（保留引理陈述+注释说明原因）
2. Layer2编译通过exit=0，commit eec201a
3. 发现DS工具链coqc编译参数错误：用`-R .. ALL`导致逻辑名变成`ALL.ALL.Layer1`（应为`-Q . ALL`，逻辑名`ALL.Layer1`）
4. 修复proof_loop.py/preflight.py/falsification_guard.py中的编译参数，commit d86fd91

## 三、DS五轮闭环结果（编译参数修复后）

用`python scripts/s04_deepseek/run_current.py split_assoc`启动DS主谋闭环，5轮均未收敛：

| 轮次 | 输出字符 | reasoning | 费用 | coqc结果 | 错误 |
|------|---------|-----------|------|----------|------|
| r1 | 9602 | 164653 | 0.3423 | 未改文件 | 卫生检查：Abort废块+同名定义重复(build_G23/build_rev/get_rev_ctx) |
| r2 | 5830 | 33912 | 0.1153 | exit=1 | `[Focus] Wrong bullet +: Current bullet + is not finished.` (line 2532) |
| r3 | 3098 | 14119 | 0.0706 | exit=1 | `The variable g1 was not found in the current environment.` (line 2533) |
| r4 | 3855 | 16579 | 0.0802 | exit=1 | `The variable g was not found in the current environment.` (line 2539) |
| r5 | 3191 | 13687 | 0.0770 | exit=1 | `Attempt to save an incomplete proof (there are remaining open goals).` (line 2543, split_assoc_z) |

**总费用**: 0.6854元

## 四、DS证明思路分析

DS尝试用以下构造：
- `build_G23`: 构造中间场域（G2优先、G3兜底）
- `build_rev` / `get_rev_ctx`: 可能是反向构造辅助
- `f_assoc`: 逐位函数
- `split_assoc_z`: 辅助引理

DS的思路方向是对的（用逐位构造G23），但实现有多个问题：
1. bullet层级混乱（+/-混用）
2. 变量未定义（g1, g在induction后未正确引入）
3. 辅助引理split_assoc_z证明不完整（remaining open goals）
4. DS在5轮内无法自我修复这些问题

## 五、需要S01研判的问题

1. **H23_val构造后的逐位case分析策略**：H23_val已Qed，证明了get G23 n的正确性。但split_assoc需要证明两个split（split G G1 G23和split G23 G2 G3），每个split都是逐位的cell_split析取。S01能否给出更精确的逐位case分析策略？特别是：
   - 当get G2 n = Some(Some a)时，G23持之，此时split G G1 G23的左支/右支如何选择？
   - 当get G2 n = None或Some None时，G23承接G3，此时两个split如何匹配？

2. **是否需要更强的辅助引理**：DS尝试了split_assoc_z等辅助引理但证明不完整。S01能否设计一组更易证的辅助引理（比如逐位cell_split的结合引理）？

3. **induction策略选择**：DS用了induction G，但G=[]分支是根本性难点（assoc_build在此失败）。用H23_val构造后，G=[]分支是否仍然困难？是否应该用不依赖G长度的逐位证明（forall n, cell_split ...）而非induction G？

## 六、当前状态

- Layer2编译通过exit=0，6个Admitted：split_assoc（当前唯一优先目标）、weaken_none_head、weaken_nil、typed_any_ctx、typed_res_par_l、typed_res_par_r
- DS工具链编译参数已修复（-Q . ALL）
- split_assoc DS五轮闭环未收敛，标blocked流转S01
- 下一步：等S01研判后，用更精确的策略重新启动DS，或转去证明其他Admitted引理（weaken_none_head等较简单的）

## 七、教训

1. **DS工具链编译参数必须提前验证**：之前5轮DS失败全部是因为`-R .. ALL`导致的库路径错误，浪费了约1元费用。以后启动DS前必须先手动验证coqc编译命令正确。
2. **DS闭环5轮是硬上限**：DS在bullet层级/变量未定义等低级错误上无法自我修复，5轮不收敛就应该熔断，不要硬扛。
3. **S01直接证明必须经过coqc验证**：S01直接证明的6个引理都有语法错误，以后S01的证明必须先编译验证再入库。

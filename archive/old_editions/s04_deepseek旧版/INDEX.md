# s04_deepseek 旧版脚本归档

> 归档时间：2026-09-09 S05整理
> 来源：scripts/s04_deepseek/
> 原因：这些是证明过程中的迭代版本（r2/r3/fix/fix2/step1）和测试脚本，已被最新版替代，归档保留历史。

## 归档文件清单（10个）

| 文件 | 类型 | 说明 |
|---|---|---|
| run_congruence_r2.py | 迭代版 | congruence证明第2轮 |
| run_congruence_r3.py | 迭代版 | congruence证明第3轮 |
| run_j1c_fix.py | 修复版 | j1c修复 |
| run_j1c_fix2.py | 修复版 | j1c修复第2版 |
| run_j1f_step1.py | 分步版 | j1f第1步 |
| run_pts_fix.py | 修复版 | pts修复 |
| run_subst_ren_r2.py | 迭代版 | subst_ren第2轮 |
| run_subst_ren_r3.py | 迭代版 | subst_ren第3轮 |
| _test_cutall.py | 测试 | cutall测试 |
| _test_defspan.py | 测试 | defspan测试 |

## 当前有效脚本（在 scripts/s04_deepseek/）

剩余22个为最新版证明脚本和工具，包括：
- 核心引擎：proof_loop.py、falsification_guard.py、preflight.py、ds_v4.py
- 证明脚本：run_congruence.py、run_split_assoc.py、run_substitution_general.py、run_subst_ren.py
- 专项：run_j1d.py、run_j1e.py、run_j1g.py、run_j1_split_assoc.py、run_typed_empty_closed.py
- 工具：board.py、check_phil.py、s04_context.py、s04_git.py、_paths.py、_insert_j1g_placeholder.py
- 测试：test_guard.py
- 文档：README.md

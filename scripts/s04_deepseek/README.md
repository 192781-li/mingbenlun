# S04 DeepSeek 工具链（V4 新范式）

> DeepSeek 是写代码的主行动者；这套脚本是 S04（明序）的"手"——只负责组织全量上下文、调用、备份、coqc 验证、错误原样回喂、留痕。
> 上位规范：`docs/协作机制/分站/S04_DeepSeek_V4新范式调用规范.md`；SOP：`docs/协作机制/分站/S04_运行指令.md`。

## 文件
| 文件 | 职责 |
|---|---|
| `_paths.py` | 统一路径/key/coqc 定位。仓库根按本目录向上两级自动识别；可用环境变量覆盖：`MINGBEN_REPO`、`DEEPSEEK_API_KEY`/`DEEPSEEK_KEY_FILE`、`COQC_BIN_DIR`、`COQLIB`、`DS_V4_TRACE_DIR` |
| `ds_v4.py` | V4 客户端：v4-flash/v4-pro、thinking 开关、人民币计费、reasoning 存档、length 自动续写+去接缝、JSON trace + 代谢 CSV |
| `s04_context.py` | 四层全量上下文（system+结晶库 / Layer 全文+策略 / 历史 / 本轮任务+错误），稳定前置以命中缓存 |
| `proof_loop.py` | agentic 闭环：出码→编造引理拦截→备份→整段替换→coqc→错误回喂，绿且无 admit 才收敛 |
| `run_current.py` | 当前待证目标的一键入口（随任务推进更新 target） |

## 前置
1. Python 3.8+（仅标准库，无需 pip 安装）。
2. key：设置环境变量 `DEEPSEEK_API_KEY`，或把 key 放到仓库根 `.deepseek_key`（该文件勿提交）。
3. coqc：默认 `C:\Rocq-Platform~9.1~2026.01`，换机器用 `COQC_BIN_DIR`/`COQLIB` 覆盖。

## 用法
```bash
# 在本目录下运行（模块间用同目录 import）
cd scripts/s04_deepseek
python _paths.py            # 离线：检查路径/key 是否就位（不花钱）
python s04_context.py       # 离线：审计全量上下文体量与关键引理是否齐全（不花钱）
python proof_loop.py        # 离线：补丁协议自检（不花钱）
python ds_v4.py --live      # 真实最小自测（会花几分钱；不带 --live 不发起调用）
python run_current.py       # 对当前目标跑 agentic 证明闭环
```

## 留痕位置
- 每次调用 trace（含 reasoning）：`ds_v4_traces/`（运行产物，已在 .gitignore，不入库）。
- 费用代谢：`docs/协作机制/明旭的记忆/明旭_API代谢日志.csv`。
- 过程时间线：`docs/协作机制/智慧河流/DeepSeek干渠.md`。
- 改文件前整文件备份：`LayerN.v.bak_r轮次`（确认收敛后可清理，勿提交）。

## 补丁协议（DS 必须遵守，proof_loop 据此落盘）
- 目标引理：给出从 `Lemma/Theorem 名字` 行到列0 `Qed.` 的**完整新版本**（整段替换）。
- 需要新增的辅助引理：单独代码块，块首加 `(* INSERT-BEFORE: 目标名 *)`，会插到目标引理前。
- 只允许引用 Layer 全文真实存在的定义/引理，否则 `check_referenced_lemmas` 拦截并回喂，不改文件。

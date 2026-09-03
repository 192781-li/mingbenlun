# -*- coding: utf-8 -*-
"""S04 DeepSeek 工具链的统一路径解析（工程化：不写死任何机器/对话目录）。

目录约定：本文件位于 <repo>/scripts/s04_deepseek/_paths.py，故仓库根 = 向上两级。
所有路径都可用环境变量覆盖，便于换机器/换仓库。
"""
import os
from pathlib import Path

REPO = Path(os.environ.get("MINGBEN_REPO", Path(__file__).resolve().parents[2]))
THEORIES = REPO / "coq" / "theories" / "ALL"
DOCS = REPO / "docs" / "协作机制"
RIVER = DOCS / "智慧河流"
CRYSTAL = RIVER / "智慧结晶库.md"
CHANNEL = RIVER / "DeepSeek干渠.md"
METABOLISM_CSV = DOCS / "明旭的记忆" / "明旭_API代谢日志.csv"
TRACE_DIR = Path(os.environ.get("DS_V4_TRACE_DIR", REPO / "ds_v4_traces"))
TRACE_DIR.mkdir(parents=True, exist_ok=True)

# Rocq/Coq：默认本机 Rocq 9.1，可用环境变量覆盖
COQBIN = os.environ.get("COQC_BIN_DIR", r"C:\Rocq-Platform~9.1~2026.01\bin")
COQLIB = os.environ.get("COQLIB", r"C:\Rocq-Platform~9.1~2026.01\lib\coq")
COQC = os.path.join(COQBIN, "coqc.exe")

# API key：优先环境变量；否则在候选位置找 .deepseek_key（按需自行追加，不硬编码某一次对话目录）
_KEY_CANDIDATES = [
    Path(os.environ["DEEPSEEK_KEY_FILE"]) if os.environ.get("DEEPSEEK_KEY_FILE") else None,
    REPO / ".deepseek_key",
    Path.home() / ".deepseek_key",
]
def read_api_key():
    env = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if env:
        return env
    for c in _KEY_CANDIDATES:
        if c and c.exists():
            return c.read_text(encoding="utf-8").strip()
    raise RuntimeError(
        "未找到 DeepSeek API key：请设置环境变量 DEEPSEEK_API_KEY，"
        "或把 key 放到仓库根 .deepseek_key / 用户目录 ~/.deepseek_key，"
        "或用 DEEPSEEK_KEY_FILE 指定文件路径。")

if __name__ == "__main__":
    print("REPO      =", REPO)
    print("THEORIES  =", THEORIES, "存在" if THEORIES.exists() else "缺失!!")
    print("CRYSTAL   =", CRYSTAL, "存在" if CRYSTAL.exists() else "缺失!!")
    print("TRACE_DIR =", TRACE_DIR)
    try:
        k = read_api_key(); print("API key   = 已找到，长度", len(k))
    except RuntimeError as e:
        print("API key   =", e)

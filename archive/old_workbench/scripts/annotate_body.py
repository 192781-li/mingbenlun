#!/usr/bin/env python3
"""给推导链总览正文段落补充类型标注——按行号匹配，避免引号问题"""
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "生命论_模块化" / "00_推导链总览.md"
lines = path.read_text(encoding="utf-8").split("\n")

# 行号 -> 标注（1-based）。在该行末尾追加标注。
# 只标注尚未有类型标注的行。
TYPE_TAGS = ["【践演】", "【概念】", "【经验】", "【决断】", "【元】"]

line_annotations = {
    # 前14步中缺少标注的正文
    27: "【概念】",      # 自指不是有或没有...
    55: "【概念】",      # 四规定性在不同层次...
    76: "【概念+经验】",  # f¹生命受前三层约束...
    86: "【概念】",      # 自由不是没有约束...
    97: "【概念】",      # 自指操作在f¹以上...
    125: "【概念】",     # 反自指和外部破坏不同...
    150: "【决断】",     # 从异化双维度推出解放...
    190: "【元】",       # 三者是中介关系...
    195: "【元】",       # 禁止用由此可见...
    199: "【概念+决断】", # 操作长出自指...
    205: "【经验+决断】", # 约38亿年前...
    # 全稿部分
    300: "【概念】",     # 哲学僵尸设想的反驳
    302: "【概念+经验】", # 审慎边界
    306: "【概念+经验】", # 感作为生命之力的己化，强度...
    320: "【概念】",     # 强度回答感有多猛烈...
    322: "【概念+经验】", # 决定感质量的四重耦合条件
    334: "【概念+决断】", # 提高感的质量...
    345: "【元】",       # 外推边界...
}

count = 0
for line_no, tag in line_annotations.items():
    idx = line_no - 1
    if idx >= len(lines):
        print(f"[超界] 行{line_no}")
        continue
    line = lines[idx]
    # 跳过已有标注的行
    if any(t in line for t in TYPE_TAGS):
        print(f"[跳过] 行{line_no} 已有标注")
        continue
    # 在行末（换行前）追加标注
    lines[idx] = line.rstrip() + tag
    count += 1

path.write_text("\n".join(lines), encoding="utf-8")
print(f"已标注 {count} 处")

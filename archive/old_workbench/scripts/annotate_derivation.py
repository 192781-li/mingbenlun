#!/usr/bin/env python3
"""给推导链总览全稿部分补充推理类型标注"""
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "生命论_模块化" / "00_推导链总览.md"
text = path.read_text(encoding="utf-8")

# (原文片段, 标注后片段)
annotations = [
    ("**1. 践演坐实起点：有操作在发生。**",
     "**1. 践演坐实起点：有操作在发生。**【践演】"),
    ("**2. 存在即操作，操作先于实体**",
     "**2. 存在即操作，操作先于实体**【概念】"),
    ("**1. 涌现的定义**",
     "**1. 涌现的定义**【概念】"),
    ("**2. 生命的四规定性（第三人称结构性解析）**",
     "**2. 生命的四规定性（第三人称结构性解析）**【概念】"),
    ("**3. 感：生命之力的己化**",
     "**3. 感：生命之力的己化**【概念】"),
    ("## 六、体系现存待补缺口",
     "## 六、体系现存待补缺口【元】"),
    ("### 科学理论支撑小结",
     "### 科学理论支撑小结【经验】"),
]

count = 0
for old, new in annotations:
    if old in text and new not in text:
        text = text.replace(old, new, 1)
        count += 1
    elif new in text:
        pass
    else:
        print(f"[未找到] {old[:50]}")

path.write_text(text, encoding="utf-8")
print(f"已标注 {count} 处")

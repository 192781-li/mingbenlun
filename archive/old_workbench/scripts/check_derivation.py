#!/usr/bin/env python3
"""
推导链形式化检查脚本 v2
启发式检查，只标记可疑项，不做最终判决。
"""

import re
import sys
from pathlib import Path

DERIVATION_PATH = Path(__file__).parent.parent.parent / "生命论_模块化" / "00_推导链总览.md"

LAYER_MARKERS = {"在": "存在论", "社": "社会分析", "规": "规范立场", "元": "元方法"}
TYPE_MARKERS = ["践演", "概念", "经验", "决断"]

# 高可疑跳跃词（"所以""因此"在概念分析中太常见，只标记更可疑的）
SUSPICIOUS_JUMPS = ["由此可见", "不言而喻", "显而易见", "毋庸置疑", "无可置疑"]

# 经验超界：必然词，但排除否定和限定语境
NECESSITY_PATTERNS = [
    r"(?<!不)必然(?!性)",   # "必然"但不是"不必然""必然性"
    r"绝不会",
    r"永远不会",
    r"不可能(?!有)",        # "不可能"但不是"不可能有"（描述可能性）
]

# 决断伪装：规范词，但排除描述性用法
DECISION_PATTERNS = [
    (r"我们必须(?!是)", "规范主张'我们必须'"),
    (r"应该革命", "规范主张'应该革命'"),
    (r"应当推翻", "规范主张'应当推翻'"),
]


def parse_steps(content):
    steps = []
    current_title = None
    current_lines = []

    for line in content.split("\n"):
        step_match = re.match(r"^## 第.+步[：:](.+)", line)
        if step_match:
            if current_title:
                steps.append((current_title, "\n".join(current_lines)))
            current_title = step_match.group(1).strip()
            current_lines = [line]
        elif current_title:
            current_lines.append(line)

    if current_title:
        steps.append((current_title, "\n".join(current_lines)))
    return steps


def extract_markers(title_line):
    """从标题行提取层和类型标记，支持【在·践演】格式"""
    layers = set()
    types = set()
    # 匹配 【在·践演】 【社·经验】 【规·决断】 【元】 等
    for m in re.finditer(r"【([^】]+)】", title_line):
        parts = re.split(r"[·→\-+]", m.group(1))
        for p in parts:
            p = p.strip()
            if p in LAYER_MARKERS:
                layers.add(LAYER_MARKERS[p])
            if p in TYPE_MARKERS:
                types.add(p)
    return layers, types


def check_annotations(steps):
    errors = []
    for title, body in steps:
        first_line = body.split("\n")[0]
        layers, types = extract_markers(first_line)

        if not layers:
            errors.append(f"[缺层标记] {title}")
        # 元方法层不需要类型标记（它是关于方法的方法，不是推导步骤）
        if not types and "元方法" not in layers:
            errors.append(f"[缺类型标记] {title}")
    return errors


def check_suspicious_jumps(steps):
    """只标记高可疑跳跃词"""
    errors = []
    for title, body in steps:
        first_line = body.split("\n")[0]
        layers, _ = extract_markers(first_line)

        for word in SUSPICIOUS_JUMPS:
            if word in body:
                idx = body.find(word)
                context = body[max(0, idx - 30):idx + len(word) + 30].replace("\n", " ")
                # 排除"提及"而非"使用"的情况（如"禁止用'由此可见'"）
                before = body[max(0, idx - 10):idx]
                if "禁止" in before or "避免" in before or "不要用" in before:
                    continue
                # 多层标注的步骤允许跨层
                if len(layers) > 1:
                    continue
                errors.append(f"[可疑跳跃] {title} → '{word}': ...{context}...")
    return errors


def check_experience_overreach(steps):
    errors = []
    for title, body in steps:
        first_line = body.split("\n")[0]
        _, types = extract_markers(first_line)

        if "经验" in types:
            for pattern in NECESSITY_PATTERNS:
                for m in re.finditer(pattern, body):
                    idx = m.start()
                    context = body[max(0, idx - 25):idx + len(m.group()) + 25].replace("\n", " ")
                    errors.append(f"[经验超界可疑] {title} → '{m.group()}': ...{context}...")
    return errors


def check_decision_disguise(steps):
    errors = []
    for title, body in steps:
        first_line = body.split("\n")[0]
        layers, types = extract_markers(first_line)
        is_normative = "规范立场" in layers or "决断" in types

        if not is_normative:
            for pattern, desc in DECISION_PATTERNS:
                for m in re.finditer(pattern, body):
                    idx = m.start()
                    context = body[max(0, idx - 25):idx + len(m.group()) + 25].replace("\n", " ")
                    errors.append(f"[决断伪装可疑] {title} → {desc}: ...{context}...")
    return errors


def main():
    if not DERIVATION_PATH.exists():
        print(f"推导链文件不存在: {DERIVATION_PATH}")
        return 1

    content = DERIVATION_PATH.read_text(encoding="utf-8")
    steps = parse_steps(content)

    print(f"推导链检查：共 {len(steps)} 步")

    all_errors = []
    all_errors.extend(check_annotations(steps))
    all_errors.extend(check_suspicious_jumps(steps))
    all_errors.extend(check_experience_overreach(steps))
    all_errors.extend(check_decision_disguise(steps))

    if all_errors:
        print(f"发现 {len(all_errors)} 个可疑项（启发式，需人工判断）：")
        for e in all_errors:
            print(f"  ⚠ {e}")
        return 1
    else:
        print("✓ 全部通过：标注完整、无高可疑跳跃、无经验超界、无决断伪装")
        return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
正文-概念图交叉检查
1. 图中每个概念是否在正文中出现
2. 正文中使用的单字母变量（拉丁/希腊）是否都在图中
3. 正文中加粗定义的术语是否在图中
"""

import json
import re
import sys
from pathlib import Path

GRAPH_PATH = Path(__file__).parent.parent / "references" / "concept_graph.json"
MODULES_DIR = Path(__file__).parent.parent.parent / "生命论_模块化"

# 已知的非概念单字母（常见代词、连词等）
STOP_LETTERS = set("的了是在我他她它你你们我们他们这那和与及或但而也都就又被把让给从向到对为以于")

# 已知的合法变量（在图中或已确认）
KNOWN_VARS = {
    "S", "f", "P", "G", "V", "t", "E",  # 存在论
    "T", "M", "N", "α", "σ", "O", "W", "l", "C", "R", "A", "K", "Ω",  # 量论
    "f⁰", "f¹", "f²", "f³", "f⁴", "f⁰·⁵",  # 层级
    "F1", "F2", "F3", "F",  # 实践论层级标签
    "dV/dt", "S=f(S)", "S=f(E)",  # 公式
    # 外部科学引用中的变量（非生命论概念）
    "B", "D", "H", "J", "X", "Z", "b", "c", "p", "x", "ψ",  # 物理/化学/英文引用
}


def load_graph():
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_text():
    """加载所有模块文件的文本"""
    texts = {}
    for md_file in sorted(MODULES_DIR.rglob("*.md")):
        texts[md_file.name] = md_file.read_text(encoding="utf-8")
    all_text = "\n".join(texts.values())
    return all_text, texts


def check_concepts_in_text(concepts, all_text):
    """检查1: 图中概念是否在正文中出现"""
    missing = []
    for name in concepts:
        if name not in all_text:
            # 尝试模糊匹配（l_prime → l′）
            alt = name.replace("_prime", "′")
            if alt not in all_text:
                missing.append(name)
    return missing


def check_vars_in_graph(all_text):
    """检查2: 正文中的单字母变量是否在图中"""
    # 先移除代码块、URL、英文句子（减少误报）
    cleaned = re.sub(r"`[^`]*`", "", all_text)  # 移除行内代码
    cleaned = re.sub(r"https?://\S+", "", cleaned)  # 移除URL
    cleaned = re.sub(r"\[.*?\]", "", cleaned)  # 移除引用标记

    # 匹配拉丁字母变量（在数学/公式语境中）
    latin_vars = set()
    for m in re.finditer(r"(?<![a-zA-Zα-ωΑ-Ω])([A-Za-z])(?![a-zA-Zα-ωΑ-Ω])", cleaned):
        v = m.group(1)
        if v in STOP_LETTERS:
            continue
        # 检查是否在公式/变量语境中
        line_start = cleaned.rfind("\n", 0, m.start()) + 1
        line_end = cleaned.find("\n", m.end())
        if line_end == -1:
            line_end = len(cleaned)
        line = cleaned[line_start:line_end]
        # 必须在包含数学符号或"公式/系数/变量/比率"的行中
        math_context = any(c in line for c in ["=", "×", "÷", "+", "−", "-", "/", "→", "∞", "≤", "≥", "<", ">"])
        var_context = any(w in line for w in ["公式", "系数", "比率", "变量", "函数", "f(", "S="])
        if not (math_context or var_context):
            continue
        latin_vars.add(v)

    # 匹配希腊字母变量（在公式语境中）
    greek_vars = set()
    for m in re.finditer(r"[α-ωΑ-Ω](?:′|ₑ|ₘ)?", cleaned):
        v = m.group(0)
        line_start = cleaned.rfind("\n", 0, m.start()) + 1
        line_end = cleaned.find("\n", m.end())
        if line_end == -1:
            line_end = len(cleaned)
        line = cleaned[line_start:line_end]
        if any(c in line for c in ["=", "×", "÷", "+", "−", "-", "/", "→", "∞", "公式", "系数", "比率"]):
            greek_vars.add(v)

    # 匹配 f^N 层级标记
    f_levels = set(re.findall(r"f[⁰¹²³⁴⁵⁶⁷⁸⁹·.]+", cleaned))
    # 匹配 F1/F2/F3 实践标签
    f_practice = set(re.findall(r"F[123]", cleaned))

    all_used = latin_vars | greek_vars | f_levels | f_practice
    known = set(KNOWN_VARS)
    graph_data = load_graph()
    for name in graph_data["concepts"]:
        if len(name) <= 2:
            known.add(name)

    missing_vars = all_used - known
    missing_vars = {v for v in missing_vars if len(v) <= 4 and not v.isdigit()}
    return missing_vars


def check_bold_terms(all_text):
    """检查3: 正文中加粗定义的术语"""
    # 匹配 **术语** 模式
    bold_terms = re.findall(r"\*\*([^*\n]{2,15})\*\*", all_text)
    # 统计频率
    from collections import Counter
    freq = Counter(bold_terms)
    # 出现3次以上的加粗术语可能是核心概念
    frequent = {t: c for t, c in freq.items() if c >= 3}
    return frequent


def main():
    graph = load_graph()
    concepts = graph["concepts"]
    all_text, texts = load_all_text()

    print(f"正文-概念图交叉检查：{len(concepts)} 个概念，{len(texts)} 个文件")

    errors = []

    # 检查1
    missing = check_concepts_in_text(concepts, all_text)
    if missing:
        errors.append(f"图中有 {len(missing)} 个概念在正文中未找到: {', '.join(missing)}")
    else:
        print("✓ 图中所有概念在正文中均有出现")

    # 检查2
    missing_vars = check_vars_in_graph(all_text)
    if missing_vars:
        errors.append(f"正文中有 {len(missing_vars)} 个变量未在图中定义: {', '.join(sorted(missing_vars))}")
    else:
        print("✓ 正文中所有变量均在图中或已知列表中")

    # 检查3（信息性，不算错误）
    frequent = check_bold_terms(all_text)
    graph_concept_names = set(concepts.keys())
    potentially_missing = []
    for term, count in sorted(frequent.items(), key=lambda x: -x[1]):
        # 检查是否在图中（简单子串匹配）
        in_graph = any(term in name or name in term for name in graph_concept_names)
        if not in_graph and count >= 5:
            potentially_missing.append(f"{term}({ count}次)")

    if errors:
        print(f"\n发现 {len(errors)} 个问题：")
        for e in errors:
            print(f"  ✗ {e}")
        if potentially_missing:
            print(f"\nℹ 高频加粗术语（可能需要加入图，仅供参考）：")
            for t in potentially_missing[:15]:
                print(f"  - {t}")
        return 1
    else:
        if potentially_missing:
            print(f"\nℹ 高频加粗术语（可能需要加入图，仅供参考）：")
            for t in potentially_missing[:15]:
                print(f"  - {t}")
        print("\n✓ 交叉检查通过")
        return 0


if __name__ == "__main__":
    sys.exit(main())

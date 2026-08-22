#!/usr/bin/env python3
"""
生命论推导形式化检查 v0.1
检查1：推理类型标注完整性（践演/概念/经验/决断）
检查2：跨层跳跃检测（在→社→规之间的跳跃是否有显式中介）
检查3：经验命题超界检测（经验概括推出必然结论）

只标记不判决。输出可疑段落清单供人工复核。
"""
import re
import sys
from pathlib import Path

# ── 文件路径 ──
WORKSPACE = Path(__file__).resolve().parents[2]
DERIVATION = WORKSPACE / "生命论_模块化" / "00_推导链总览.md"

# ── 标注类型 ──
TYPE_TAGS = ["践演", "概念", "经验", "决断"]
LAYER_TAGS = ["在", "社", "规"]

# ── 跨层跳跃可疑词 ──
JUMP_WORDS = ["由此可见", "因此", "所以", "不言而喻", "显而易见", "毋庸置疑",
              "毫无疑问", "显然", "故而", "由此推出", "必然得出", "不难看出"]

# ── 经验超界可疑模式：经验语境中出现必然判断 ──
NECESSITY_WORDS = ["必然", "一定", "不可能", "绝不会", "永远不会", "注定", "不可避免"]
EXPERIENCE_CONTEXTS = ["历史上", "经验", "实际上", "事实上", "研究表明", "证据显示",
                       "苏联", "历史告诉我们", "实践证明", "现实中"]

# ── 决断伪装可疑模式 ──
DISGUISE_PATTERNS = [
    r"存在论证明.*必须",
    r"从操作存在论推出",
    r"由此可见.*应该",
    r"因此.*必须",
    r"存在论.*要求我们",
]


def read_file(path: Path) -> str:
    if not path.exists():
        print(f"[错误] 文件不存在: {path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def split_into_paragraphs(text: str):
    """按空行切段，保留行号"""
    lines = text.split("\n")
    paragraphs = []
    current = []
    start_line = 1
    for i, line in enumerate(lines, 1):
        if line.strip() == "":
            if current:
                paragraphs.append((start_line, "\n".join(current)))
                current = []
        else:
            if not current:
                start_line = i
            current.append(line)
    if current:
        paragraphs.append((start_line, "\n".join(current)))
    return paragraphs


def check_1_type_annotation(paragraphs):
    """检查1：推理类型标注完整性"""
    issues = []
    # 找"第X步"开头的段落及其子段落
    current_step = None
    for line_no, para in paragraphs:
        step_match = re.match(r"^##\s*第(.+?)步[：:](.+)", para)
        if step_match:
            current_step = step_match.group(0)[:60]
            # 检查步骤标题行是否有类型标注（支持【在·践演】【概念+经验】【元】等格式）
            has_type = bool(re.search(r"【[^】]*(践演|概念|经验|决断|元)[^】]*】", para))
            if not has_type:
                issues.append({
                    "line": line_no,
                    "severity": "提示",
                    "check": "检查1",
                    "issue": f"步骤标题缺少推理类型标注: {current_step}",
                    "text": para[:120]
                })
            continue
        # 跳过非正文
        if para.startswith("#") or para.startswith(">") or para.startswith("|") or para.startswith("```"):
            continue
        # 检查包含命题内容的段落（有句号、长度>30的正文段落）
        if len(para) > 30 and ("。" in para or "：" in para):
            # 支持组合标签如【概念+经验】、【在·践演】和【元】
            has_type = bool(re.search(r"【[^】]*(践演|概念|经验|决断|元)[^】]*】", para))
            # 列表项以 - 开头的也要检查
            is_list = para.lstrip().startswith("-") or para.lstrip().startswith("*")
            if not has_type and not is_list:
                # 只标记非列表的独立段落（列表项可能在父段落已标注）
                issues.append({
                    "line": line_no,
                    "severity": "提示",
                    "check": "检查1",
                    "issue": "正文段落缺少推理类型标注",
                    "text": para[:120].replace("\n", " ")
                })
    return issues


def check_2_cross_layer_jumps(paragraphs):
    """检查2：跨层跳跃检测"""
    issues = []
    for line_no, para in paragraphs:
        if para.startswith("#") or para.startswith("```"):
            continue
        for word in JUMP_WORDS:
            if word in para:
                # 检查该段落是否同时涉及不同层
                has_zai = "存在论" in para or "操作" in para or "自指" in para or "阴阳" in para
                has_she = "阶级" in para or "资本" in para or "国家" in para or "历史" in para or "社会" in para
                has_gui = "应该" in para or "必须" in para or "解放" in para or "革命" in para or "站在" in para

                cross_count = sum([has_zai and (has_she or has_gui),
                                   has_she and has_gui])
                if cross_count > 0:
                    # 白名单：已有显式中介标注则跳过
                    if "⊩ₑ" in para or "⊩ₘ" in para or "中介" in para:
                        continue
                    # 白名单：纯存在论内部推导（无社会/规范层实质关键词）
                    she_kw = ["阶级", "资本", "国家", "革命", "解放", "劳动者", "剥削", "统治"]
                    gui_kw = ["应该", "立场", "站在", "正义", "自由人联合体"]
                    if not any(k in para for k in she_kw) and not any(k in para for k in gui_kw):
                        continue
                    issues.append({
                        "line": line_no,
                        "severity": "可疑",
                        "check": "检查2",
                        "issue": f"跨层跳跃词「{word}」连接不同层，需确认是否有显式中介(⊩ₑ/⊩ₘ)",
                        "text": para[:150].replace("\n", " ")
                    })
    return issues


def check_3_experience_overreach(paragraphs):
    """检查3：经验命题超界检测"""
    issues = []
    for line_no, para in paragraphs:
        if para.startswith("#") or para.startswith("```"):
            continue
        # 如果段落标注为【经验】或包含经验语境
        is_experience = "【经验】" in para or any(ctx in para for ctx in EXPERIENCE_CONTEXTS)
        if is_experience:
            for nec_word in NECESSITY_WORDS:
                if nec_word in para:
                    # 排除否定用法："不是必然""并非必然""不保证必然"等
                                    # 排除否定用法："不是必然""并非必然""不保证必然"等
                    neg_patterns = [
                        rf"不{nec_word}", rf"并非{nec_word}", rf"不是{nec_word}",
                        rf"不能{nec_word}", rf"不等于{nec_word}", rf"不保证{nec_word}",
                        rf"非{nec_word}", rf"没有{nec_word}",
                    ]
                    if any(re.search(p, para) for p in neg_patterns):
                        continue
                        issues.append({
                            "line": line_no,
                            "severity": "可疑",
                            "check": "检查3",
                            "issue": f"经验语境中出现必然判断「{nec_word}」，可能经验超界",
                            "text": para[:150].replace("\n", " ")
                        })
    return issues


def check_4_decision_disguise(paragraphs):
    """检查4：决断伪装检测"""
    issues = []
    for line_no, para in paragraphs:
        if para.startswith("#") or para.startswith("```"):
            continue
        for pattern in DISGUISE_PATTERNS:
            if re.search(pattern, para):
                has_decision_tag = "【决断】" in para or "【元】" in para
                if not has_decision_tag:
                    issues.append({
                        "line": line_no,
                        "severity": "可疑",
                        "check": "检查4",
                        "issue": f"可能存在决断伪装（规范判断未标注【决断】）",
                        "text": para[:150].replace("\n", " ")
                    })
    return issues


def check_5_self_refutation(paragraphs):
    """检查5：践演自洽启发式"""
    issues = []
    dogmatic_words = ["不容置疑", "唯一正确", "绝对真理", "不可挑战", "永远正确",
                      "必须无条件", "不容讨论", "终极真理"]
    for line_no, para in paragraphs:
        if para.startswith("#") or para.startswith("```"):
            continue
        # 批判教条的段落是否本身在用教条语气
        if any(w in para for w in ["教条", "独断", "经文", "僵化"]):
            for dw in dogmatic_words:
                if dw in para:
                    issues.append({
                        "line": line_no,
                        "severity": "可疑",
                        "check": "检查5",
                        "issue": f"批判教条/独断的段落自身使用了独断语气「{dw}」",
                        "text": para[:150].replace("\n", " ")
                    })
    return issues


def check_6_nature_to_ought(paragraphs):
    """检查6：本性→应该跳跃检测
    搜索"出于本性""人之为人""必然选择""最优选择"等存在论/本性表述，
    如果后面跟着规范判断（应该/必须/要），且没有显式【决断】或⊩ₘ中介，标记可疑。
    原理：从"本性是X"到"应该X"中间站着一个活人，这是决断不是演绎。
    """
    issues = []
    nature_words = ["本性", "人之为人", "出于本性", "本质上", "从根本上",
                    "必然选择", "最优选择", "合乎本性", "天生", "与生俱来",
                    "人的本质", "作为人", "为人之本", "本性上", "本然"]
    norm_words = ["应该", "必须", "应当", "需要", "要去", "要选择",
                  "要追求", "要实现", "要解放", "要站在", "要反对"]

    for line_no, para in paragraphs:
        if para.startswith("#") or para.startswith("```"):
            continue
        has_nature = any(w in para for w in nature_words)
        has_norm = any(w in para for w in norm_words)
        if has_nature and has_norm:
            has_decision = "【决断】" in para or "⊩ₘ" in para or "中介" in para
            is_conditional = "如果" in para and ("就" in para or "则" in para)
            is_pure_description = not any(w in para for w in ["应该", "必须", "应当"])
            if not has_decision and not is_conditional and not is_pure_description:
                nature_hit = next((w for w in nature_words if w in para), "?")
                norm_hit = next((w for w in norm_words if w in para), "?")
                issues.append({
                    "line": line_no,
                    "severity": "可疑",
                    "check": "检查6",
                    "issue": f"本性→应该跳跃：「{nature_hit}」推出「{norm_hit}」，需确认是否有显式决断中介(⊩ₘ)",
                    "text": para[:150].replace("\n", " ")
                })
    return issues


def main():
    text = read_file(DERIVATION)
    paragraphs = split_into_paragraphs(text)

    print("=" * 70)
    print("生命论推导形式化检查 v0.1")
    print(f"文件: {DERIVATION}")
    print(f"段落数: {len(paragraphs)}")
    print("=" * 70)

    all_issues = []
    all_issues.extend(check_1_type_annotation(paragraphs))
    all_issues.extend(check_2_cross_layer_jumps(paragraphs))
    all_issues.extend(check_3_experience_overreach(paragraphs))
    all_issues.extend(check_4_decision_disguise(paragraphs))
    all_issues.extend(check_5_self_refutation(paragraphs))
    all_issues.extend(check_6_nature_to_ought(paragraphs))

    # 按检查分组统计
    stats = {}
    for issue in all_issues:
        key = f"{issue['check']} ({issue['severity']})"
        stats[key] = stats.get(key, 0) + 1

    print("\n【统计】")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v} 处")
    print(f"  总计: {len(all_issues)} 处\n")

    # 输出详细结果
    for check_name in ["检查1", "检查2", "检查3", "检查4", "检查5", "检查6"]:
        check_issues = [i for i in all_issues if i["check"] == check_name]
        if not check_issues:
            continue
        print(f"\n{'─' * 70}")
        print(f"  {check_name} ({len(check_issues)} 处)")
        print(f"{'─' * 70}")
        for issue in check_issues:
            print(f"\n  [行{issue['line']}] [{issue['severity']}] {issue['issue']}")
            print(f"    原文: {issue['text']}")

    print("\n" + "=" * 70)
    print("检查完毕。以上均为启发式标记，需人工复核。")
    print("形式化是手电筒，不是法庭。")
    print("=" * 70)

    # 输出机器可读结果
    import json
    report_path = WORKSPACE / "mingben-workbench" / "references" / "formalization_check_report.json"
    report_path.write_text(json.dumps(all_issues, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    main()

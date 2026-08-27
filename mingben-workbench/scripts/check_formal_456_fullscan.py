#!/usr/bin/env python3
"""
形式化检查4/5/6 全书扫描
- 检查4：决断伪装检测（规范判断未标注【决断】）
- 检查5：践演自洽启发式（批判教条的段落自身是否用教条语气）
- 检查6：本性→应该跳跃检测（存在论表述推出规范判断，缺决断中介）

只标记不判决，输出可疑段落清单。
扫描生命论_模块化/下所有.md文件。
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

BOOK_DIR = Path(__file__).parent.parent.parent / "生命论_模块化"
REPORT_DIR = Path(__file__).parent.parent / "references"

# ── 决断伪装可疑模式 ──
DISGUISE_PATTERNS = [
    r"存在论证明",
    r"从操作存在论推出",
    r"因此必须",
    r"由此必须",
    r"所以必须",
    r"应当",
    r"必须要",
    r"要去.*?革命",
    r"要去.*?解放",
    r"必须.*?站在",
    r"必须.*?反对",
]

# ── 检查5：独断语气词 ──
DOGMATIC_WORDS = [
    "不容置疑", "唯一正确", "绝对真理", "不可挑战", "永远正确",
    "必须无条件", "不容讨论", "终极真理", "毫无疑问", "毋庸置疑",
    "铁律", "金科玉律", "放之四海而皆准",
]

# ── 检查6：本性侧触发词 ──
NATURE_WORDS = [
    "本性", "人之为人", "出于本性", "本质上", "从根本上",
    "必然选择", "最优选择", "合乎本性", "天生", "与生俱来",
    "人的本质", "作为人", "为人之本", "本性上", "本然",
    "生命的本质", "人的本性",
]

# ── 检查6：规范侧触发词 ──
NORM_WORDS = [
    "应该", "必须", "应当", "需要", "要去", "要选择",
    "要追求", "要实现", "要解放", "要站在", "要反对",
    "应当要", "必须要",
]

# ── 跳过的文件（参考资料、附录、练习等非正文） ──
SKIP_DIRS = ["10_参考资料", "12_附录", "09_练习"]
SKIP_FILES = ["AGENTS.md", "manifest.txt", "auto_merge.py", "build_all.sh",
              "build.sh", "deep_check.py", "pipeline.sh", "quality_check.py",
              "renumber.py", "replace.sh", "smart_merge.py"]


def should_skip(filepath):
    """判断是否跳过该文件"""
    parts = filepath.parts
    for sd in SKIP_DIRS:
        if sd in parts:
            return True
    if filepath.name in SKIP_FILES:
        return True
    if filepath.suffix != ".md":
        return True
    return False


def split_into_paragraphs(text):
    """将文本按段落分割，返回(行号, 段落)列表"""
    paragraphs = []
    lines = text.split("\n")
    current_para = []
    start_line = 0
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped == "":
            if current_para:
                para_text = "\n".join(current_para)
                if para_text.strip():
                    paragraphs.append((start_line, para_text))
                current_para = []
        else:
            if not current_para:
                start_line = i
            current_para.append(line)
    
    if current_para:
        para_text = "\n".join(current_para)
        if para_text.strip():
            paragraphs.append((start_line, para_text))
    
    return paragraphs


def check_4_decision_disguise(line_no, para):
    """检查4：决断伪装检测"""
    issues = []
    if para.startswith("#") or para.startswith("```"):
        return issues
    for pattern in DISGUISE_PATTERNS:
        if re.search(pattern, para):
            has_decision_tag = "【决断】" in para or "【元】" in para
            if not has_decision_tag:
                issues.append({
                    "line": line_no,
                    "severity": "可疑",
                    "check": "检查4",
                    "issue": "可能存在决断伪装（规范判断未标注【决断】）",
                    "text": para[:200].replace("\n", " ")
                })
                break  # 一段只标记一次
    return issues


def check_5_self_refutation(line_no, para):
    """检查5：践演自洽启发式"""
    issues = []
    if para.startswith("#") or para.startswith("```"):
        return issues
    # 批判教条的段落是否本身在用教条语气
    if any(w in para for w in ["教条", "独断", "经文", "僵化", "迷信", "盲从"]):
        for dw in DOGMATIC_WORDS:
            if dw in para:
                issues.append({
                    "line": line_no,
                    "severity": "可疑",
                    "check": "检查5",
                    "issue": f"批判教条/独断的段落自身使用了独断语气「{dw}」",
                    "text": para[:200].replace("\n", " ")
                })
                break
    return issues


def check_6_nature_to_ought(line_no, para):
    """检查6：本性→应该跳跃检测"""
    issues = []
    if para.startswith("#") or para.startswith("```"):
        return issues
    
    has_nature = any(w in para for w in NATURE_WORDS)
    has_norm = any(w in para for w in NORM_WORDS)
    
    if has_nature and has_norm:
        has_decision = "【决断】" in para or "⊩ₘ" in para or "中介" in para
        is_conditional = "如果" in para and ("就" in para or "则" in para)
        is_pure_description = not any(w in para for w in ["应该", "必须", "应当"])
        
        if not has_decision and not is_conditional and not is_pure_description:
            nature_hit = next((w for w in NATURE_WORDS if w in para), "?")
            norm_hit = next((w for w in NORM_WORDS if w in para), "?")
            issues.append({
                "line": line_no,
                "severity": "可疑",
                "check": "检查6",
                "issue": f"本性→应该跳跃：「{nature_hit}」推出「{norm_hit}」，需确认是否有显式决断中介(⊩ₘ)",
                "text": para[:200].replace("\n", " ")
            })
    return issues


def scan_file(filepath):
    """扫描单个文件"""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": str(e), "issues": []}
    
    paragraphs = split_into_paragraphs(text)
    all_issues = []
    
    for line_no, para in paragraphs:
        all_issues.extend(check_4_decision_disguise(line_no, para))
        all_issues.extend(check_5_self_refutation(line_no, para))
        all_issues.extend(check_6_nature_to_ought(line_no, para))
    
    return {"paragraphs": len(paragraphs), "issues": all_issues}


def main():
    print("=" * 70)
    print("生命论形式化检查4/5/6 全书扫描")
    print(f"扫描目录: {BOOK_DIR}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 收集所有md文件
    all_files = sorted(BOOK_DIR.rglob("*.md"))
    target_files = [f for f in all_files if not should_skip(f)]
    
    print(f"\n找到 {len(all_files)} 个.md文件，跳过 {len(all_files)-len(target_files)} 个（参考资料/附录/练习/脚本）")
    print(f"实际扫描 {len(target_files)} 个文件\n")
    
    # 扫描
    results = {}
    total_issues = 0
    total_paragraphs = 0
    
    for filepath in target_files:
        rel_path = filepath.relative_to(BOOK_DIR)
        result = scan_file(filepath)
        results[str(rel_path)] = result
        if "issues" in result:
            total_issues += len(result["issues"])
        if "paragraphs" in result:
            total_paragraphs += result["paragraphs"]
    
    # 统计
    stats = {"检查4": 0, "检查5": 0, "检查6": 0}
    for fpath, result in results.items():
        for issue in result.get("issues", []):
            stats[issue["check"]] = stats.get(issue["check"], 0) + 1
    
    print("【统计】")
    print(f"  扫描段落总数: {total_paragraphs}")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v} 处")
    print(f"  总计: {total_issues} 处可疑标记\n")
    
    # 按检查类型输出详细结果
    for check_name in ["检查4", "检查5", "检查6"]:
        check_issues = []
        for fpath, result in results.items():
            for issue in result.get("issues", []):
                if issue["check"] == check_name:
                    check_issues.append((fpath, issue))
        
        if check_issues:
            print(f"\n{'='*70}")
            print(f"【{check_name}】共 {len(check_issues)} 处")
            print("=" * 70)
            for fpath, issue in check_issues:
                print(f"\n  文件: {fpath}")
                print(f"  行号: {issue['line']}")
                print(f"  问题: {issue['issue']}")
                print(f"  原文: {issue['text']}")
                print("  " + "-" * 50)
    
    # 输出JSON报告
    report = {
        "scan_time": datetime.now().isoformat(),
        "book_dir": str(BOOK_DIR),
        "files_scanned": len(target_files),
        "paragraphs_total": total_paragraphs,
        "stats": stats,
        "total_issues": total_issues,
        "results": results,
    }
    
    json_path = REPORT_DIR / "check456_fullscan_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nJSON报告已保存: {json_path}")
    
    # 输出可读的Markdown报告
    md_path = REPORT_DIR / "check456_fullscan_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 形式化检查4/5/6 全书扫描报告\n\n")
        f.write(f"- 扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- 扫描文件数: {len(target_files)}\n")
        f.write(f"- 扫描段落数: {total_paragraphs}\n")
        f.write(f"- 可疑标记总数: {total_issues}\n\n")
        f.write("## 统计\n\n")
        f.write("| 检查 | 数量 |\n|------|------|\n")
        for k, v in sorted(stats.items()):
            f.write(f"| {k} | {v} |\n")
        f.write(f"| **总计** | **{total_issues}** |\n\n")
        
        for check_name in ["检查4", "检查5", "检查6"]:
            check_issues = []
            for fpath, result in results.items():
                for issue in result.get("issues", []):
                    if issue["check"] == check_name:
                        check_issues.append((fpath, issue))
            
            if check_issues:
                f.write(f"## {check_name}（{len(check_issues)}处）\n\n")
                f.write("> 以下为启发式标记，需人工复核，不代表确有问题。\n\n")
                for i, (fpath, issue) in enumerate(check_issues, 1):
                    f.write(f"### {i}. {fpath} 第{issue['line']}行\n\n")
                    f.write(f"**问题**: {issue['issue']}\n\n")
                    f.write(f"**原文**: {issue['text']}\n\n")
                    f.write("---\n\n")
    
    print(f"Markdown报告已保存: {md_path}")
    
    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

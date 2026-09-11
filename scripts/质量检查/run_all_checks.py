#!/usr/bin/env python3
"""
明旭质量门禁 v1.2 — 统一入口
硬门禁（必须通过，否则禁止发布）：
  1. 合订本专项：卷完整性、篇序、控制字符、编码、标题层级
  2. 术语铁律（仅检查生命论_模块化/，排除archive/）
软检查（生成报告，不阻止发布）：
  质量门禁、过度宣称、循环论证、明性守卫、元监督
用法：python3 scripts/质量检查/run_all_checks.py [--strict] [--soft]
  --strict: 软检查有error也阻止发布
  --soft: 同时运行软检查（质量门禁/过度宣称/循环论证/明性守卫），默认只跑硬门禁以提速
"""
import os
import sys
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parent.parent.parent
BOOK_DIR = REPO / "生命论_模块化"
BUILD_DIR = REPO / "build_output"

class C:
    GREEN = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"
    BLUE = "\033[94m"; BOLD = "\033[1m"; END = "\033[0m"

def run(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(REPO))
        return r.returncode, r.stdout + r.stderr
    except Exception as e:
        return -1, str(e)

# ═══════════════════════════════════════════
# 硬门禁 1: 合订本专项检查
# ═══════════════════════════════════════════
def hard_check_combined_book():
    issues = []
    md_path = BUILD_DIR / "生命论_合订本.md"
    html_path = BUILD_DIR / "生命论_合订本.html"

    if not md_path.exists():
        # CI环境不构建合订本，跳过专项检查
        return True, ["跳过（build_output不存在，CI环境不构建合订本）"]

    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()

    # 控制字符
    ctrl = [c for c in md if ord(c) < 32 and c not in "\n\r\t"]
    if ctrl:
        issues.append(f"存在{len(ctrl)}个控制字符(退格等)，会导致pandoc解析异常")

    # 卷完整性
    expected = ["卷首 命经","第一卷","第二卷","第三卷","第四卷","第五卷",
                "第六卷","第七卷","第八卷","第九卷","第十卷","第十一卷","附录"]
    for vol in expected:
        if f"# {vol}" not in md:
            issues.append(f"缺少卷: {vol}")

    # 待入全本
    if "待入全本" in md:
        issues.append(f"存在{md.count('待入全本')}处'待入全本'标注未清理")

    # HTML检查
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        h2s = re.findall(r'<h2[^>]*>([^<]*)</h2>', html)
        nl = sum(1 for h in h2s if "\n" in h)
        if nl: issues.append(f"{nl}个H2标题被折行")
        if "charset" not in html.lower(): issues.append("HTML缺charset")
        if not html.startswith("\ufeff"): issues.append("HTML缺UTF-8 BOM")
        # 卷数
        h1s = re.findall(r'<h1[^>]*>([^<]*)</h1>', html)
        if len(h1s) < 13:
            issues.append(f"HTML只有{len(h1s)}个H1， expected >=13")
    else:
        issues.append("合订本HTML不存在")

    return len(issues) == 0, issues

# ═══════════════════════════════════════════
# 硬门禁 2: 术语铁律（仅检查正文，排除archive）
# ═══════════════════════════════════════════
def hard_check_iron_rule():
    """扫描生命论_模块化/下的正文，检查'物质自己会活'裸用"""
    issues = []
    pattern = re.compile(r'物质[^。\n]{0,10}(自己会活|是活的|本身会活|自己活|也会活|能活|活了)')
    for md in BOOK_DIR.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except:
            continue
        for i, line in enumerate(text.split("\n"), 1):
            if pattern.search(line):
                # 排除引用铁律本身的情况
                if any(k in line for k in ["绝不说", "禁止", "铁律", "不能说", "≠", "不是"]):
                    continue
                rel = md.relative_to(REPO)
                issues.append(f"{rel}:{i} {line.strip()[:60]}")
    return len(issues) == 0, issues

# ═══════════════════════════════════════════
# 软检查包装
# ═══════════════════════════════════════════
def soft_check(name, cmd):
    code, output = run(cmd)
    errors = 0
    warnings = 0
    # 提取error/warning数
    for m in re.finditer(r'(错误|error|ERROR)[^0-9]{0,5}(\d+)', output, re.I):
        errors += int(m.group(2))
    for m in re.finditer(r'(警告|warning|WARNING)[^0-9]{0,5}(\d+)', output, re.I):
        warnings += int(m.group(2))
    summary = f"错误{errors}, 警告{warnings}"
    return errors == 0, warnings, summary, output[:200]

def main():
    strict = "--strict" in sys.argv
    run_soft = "--soft" in sys.argv
    print(f"\n{C.BOLD}{C.BLUE}═══ 明旭质量门禁 v1.2 ═══{C.END}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    mode = "严格(软检查error也阻止)" if strict else "标准(硬门禁阻止)"
    if run_soft:
        mode += " + 软检查"
    print(f"模式: {mode}")
    print()

    # ═══ 硬门禁 ═══
    print(f"{C.BOLD}── 硬门禁（必须通过）──{C.END}")
    hard_results = {}

    print(f"  [1/2] 合订本专项检查...", end=" ", flush=True)
    ok, issues = hard_check_combined_book()
    hard_results["合订本专项"] = (ok, issues)
    print(f"{C.GREEN}✅{C.END}" if ok else f"{C.RED}❌{C.END}")
    if not ok:
        for iss in issues: print(f"      {C.RED}- {iss}{C.END}")

    print(f"  [2/2] 术语铁律(正文)...", end=" ", flush=True)
    ok, issues = hard_check_iron_rule()
    hard_results["术语铁律"] = (ok, issues)
    print(f"{C.GREEN}✅{C.END}" if ok else f"{C.RED}❌{C.END}")
    if not ok:
        for iss in issues[:5]: print(f"      {C.RED}- {iss}{C.END}")
        if len(issues) > 5: print(f"      {C.RED}... 共{len(issues)}处{C.END}")

    # ═══ 软检查（默认不跑，加 --soft 才跑，以提速）═══
    soft_results = {}
    if run_soft:
        print(f"\n{C.BOLD}── 软检查（参考，不阻止发布）──{C.END}")
        soft_checks = [
            ("质量门禁", ["python3", "scripts/质量检查/quality_gate.py"]),
            ("过度宣称", ["python3", "scripts/质量检查/overclaim_checker.py"]),
            ("循环论证", ["python3", "scripts/质量检查/circular_reasoning_detector.py"]),
            ("明性守卫", ["python3", "scripts/质量检查/mingxing_guard.py"]),
        ]
        for name, cmd in soft_checks:
            print(f"  {name}...", end=" ", flush=True)
            ok, warnings, summary, _ = soft_check(name, cmd)
            soft_results[name] = (ok, warnings, summary)
            if ok:
                print(f"{C.GREEN}✅{C.END} ({summary})")
            else:
                print(f"{C.YELLOW}⚠️{C.END} ({summary})")
    else:
        print(f"\n{C.YELLOW}（软检查已跳过，加 --soft 运行）{C.END}")

    # ═══ 汇总 ═══
    print(f"\n{C.BOLD}── 汇总 ──{C.END}")
    hard_pass = all(ok for ok, _ in hard_results.values())
    soft_errors = any(not ok for ok, _, _ in soft_results.values())

    for name, (ok, issues) in hard_results.items():
        print(f"  {C.GREEN}✅{C.END if ok else C.RED}❌{C.END} {name}")
    for name, (ok, w, s) in soft_results.items():
        icon = f"{C.GREEN}✅{C.END}" if ok else f"{C.YELLOW}⚠️{C.END}"
        print(f"  {icon} {name} ({s})")

    print()
    if hard_pass and (not strict or not soft_errors):
        print(f"{C.GREEN}{C.BOLD}🎉 硬门禁全部通过，可以发布{C.END}")
        if soft_errors:
            print(f"{C.YELLOW}⚠️  软检查有错误，建议修复但不阻止{C.END}")
        sys.exit(0)
    else:
        print(f"{C.RED}{C.BOLD}❌ 硬门禁未通过，禁止发布{C.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()

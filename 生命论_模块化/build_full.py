#!/usr/bin/env python3
"""
生命论全本一键构建脚本
用法：python3 build_full.py [--pdf] [--html] [--check]
  无参数：构建MD全本（秒级）
  --html：额外生成HTML（秒级）
  --pdf：额外生成PDF（weasyprint，约1-2分钟）
  --check：只做验证，不构建
  --all：MD + HTML + PDF 全部生成

哲学含义：模块化是阴（沉积），构建是阳（激活）。
平时各模块独立生长（阳），需要时一键聚成全书（阴的统摄）。
阴服务阳——构建不是目的，让活的思想随时能完整出场才是。
"""

import json
import os
import re
import sys
import subprocess
from pathlib import Path

# ── 路径 ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
MANIFEST_PATH = SCRIPT_DIR / "manifest.json"
OUTPUT_DIR = PROJECT_DIR / "output"
OUTPUT_MD = OUTPUT_DIR / "生命论全本.md"
OUTPUT_HTML = OUTPUT_DIR / "生命论全本.html"
OUTPUT_PDF = OUTPUT_DIR / "生命论全本.pdf"

CN_NUMS = "零一二三四五六七八九十"

def cn2num(s):
    cn = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    if s == '十': return 10
    if s.startswith('十'): return 10 + cn.get(s[1], 0)
    if '十' in s: return cn[s[0]]*10 + cn.get(s.split('十')[1], 0)
    return cn.get(s, 0)

# ── 验证 ──────────────────────────────────────────────
def normalize_juan(s):
    """把'第一卷'和'卷一'统一为'卷一'格式。"""
    m = re.match(r'第([一二三四五六七八九十]+)卷', s)
    if m:
        return '卷' + m.group(1)
    return s

def validate():
    """构建前验证：结构、编号、文件完整性。返回(错误列表, 警告列表)。"""
    errors = []
    warnings = []

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for vol in manifest["volumes"]:
        dirpath = SCRIPT_DIR / vol["dir"]
        if not dirpath.is_dir():
            errors.append(f"卷目录不存在：{vol['dir']}")
            continue

        if vol["number"] in ("卷首", "附录"):
            continue

        # 检查卷标题（只比对第一行）
        title_file = dirpath / "00_卷标题.md"
        if title_file.exists():
            with open(title_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
            # 提取 # 第X卷 标题：副标题
            m = re.match(r'#\s*(第?[一二三四五六七八九十]+卷)\s+(.+)', first_line)
            if m:
                file_juan = normalize_juan(m.group(1))
                file_title = m.group(2)
                expected_juan = vol["number"]
                # 副标题可能在标题行里，也可能不在
                expected_full = f"{vol['title']}：{vol.get('subtitle','')}"
                if file_juan != expected_juan:
                    errors.append(f"{vol['number']}卷号不一致：文件是{file_juan}")
                # 标题主名必须一致，副标题宽松匹配
                if vol["title"] not in file_title:
                    errors.append(
                        f"{vol['number']}标题不一致：文件是'{file_title}'，"
                        f"manifest是'{vol['title']}'"
                    )

        # 收集篇文件
        chapters = []
        for fname in os.listdir(dirpath):
            m = re.match(r'篇([一二三四五六七八九十]+)_(.+)', fname)
            if m and fname.endswith(".md"):
                chapters.append((cn2num(m.group(1)), fname))
        chapters.sort()

        # 检查篇连续性
        nums = [n for n, _ in chapters]
        expected = list(range(1, len(nums) + 1))
        if nums != expected:
            errors.append(f"{vol['number']}篇编号不连续：期望{expected}，实际{nums}")

        # 检查每篇的章编号
        for num, fname in chapters:
            fpath = dirpath / fname
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            ch_nums = []
            for line in content.split("\n"):
                line = line.strip()
                m2 = re.match(r'### 第([一二三四五六七八九十百零]+)章', line)
                if m2:
                    ch_nums.append(m2.group(1))

            if not ch_nums:
                warnings.append(f"{vol['number']}篇{num}（{fname}）暂无章标题（骨架状态）")
                continue

            # 检查章编号连续
            ch_ints = [cn2num(c) for c in ch_nums]
            for i in range(1, len(ch_ints)):
                if ch_ints[i] != ch_ints[i-1] + 1:
                    errors.append(
                        f"{vol['number']}篇{num}章编号不连续："
                        f"第{ch_nums[i-1]}章→第{ch_nums[i]}章"
                    )

    return errors, warnings

# ── 合并 ──────────────────────────────────────────────
def shift_headings(content, levels=1):
    """把Markdown标题降级levels级。# → ##, ## → ###, etc."""
    lines = content.split("\n")
    result = []
    for line in lines:
        m = re.match(r'^(#{1,6})(\s)', line)
        if m:
            hashes = m.group(1)
            new_level = min(len(hashes) + levels, 6)
            line = '#' * new_level + m.group(2) + line[len(hashes) + 1:]
        result.append(line)
    return "\n".join(result)

def build_markdown():
    """按manifest顺序合并所有模块为一个Markdown文件。"""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    OUTPUT_DIR.mkdir(exist_ok=True)
    parts = []

    # 封面（# 级 = 全书）
    parts.append("# 生命论（明本论）\n\n")
    parts.append("> 一生道，道养一，一指万物\n\n")
    parts.append("---\n\n")

    for vol in manifest["volumes"]:
        dirpath = SCRIPT_DIR / vol["dir"]
        if not dirpath.is_dir():
            print(f"  跳过不存在的目录：{vol['dir']}")
            continue

        if vol["number"] == "卷首":
            # 命经：## 级
            mj = dirpath / "命经.md"
            if mj.exists():
                parts.append("## 卷首·命经\n\n")
                with open(mj, "r", encoding="utf-8") as f:
                    content = f.read()
                # 命经内部标题降一级（## → ###）
                content = shift_headings(content, 1)
                parts.append(content)
                parts.append("\n\n---\n\n")
            continue

        if vol["number"] == "附录":
            # 附录总览
            overview = dirpath / "00_附录总览.md"
            if overview.exists():
                with open(overview, "r", encoding="utf-8") as f:
                    content = f.read()
                content = shift_headings(content, 1)
                parts.append(content)
                parts.append("\n\n")

            # 附录文件按编号排序
            items = []
            for fname in os.listdir(dirpath):
                if fname.endswith(".md") and not fname.startswith("00_"):
                    m = re.match(r'附录([一二三四五六七八九十]+)_?(.+)?', fname)
                    if m:
                        items.append((cn2num(m.group(1)), fname))
                    else:
                        items.append((99, fname))
            items.sort()
            for _, fname in items:
                fpath = dirpath / fname
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                content = shift_headings(content, 1)
                parts.append(content)
                parts.append("\n\n---\n\n")
            continue

        # 正文卷
        # 卷标题：00_卷标题.md 的 # 降为 ##
        title_file = dirpath / "00_卷标题.md"
        if title_file.exists():
            with open(title_file, "r", encoding="utf-8") as f:
                content = f.read()
            # 只取第一行作为卷标题，其余（描述、篇目列表）跳过
            first_line = content.split("\n")[0]
            title_shifted = shift_headings(first_line, 1)
            parts.append(title_shifted + "\n\n")
        else:
            parts.append(f"## {vol['number']} {vol['title']}：{vol.get('subtitle','')}\n\n")

        # 篇文件按编号排序
        chapters = []
        for fname in os.listdir(dirpath):
            m = re.match(r'篇([一二三四五六七八九十]+)_(.+)', fname)
            if m and fname.endswith(".md"):
                chapters.append((cn2num(m.group(1)), fname))
        chapters.sort()

        for num, fname in chapters:
            fpath = dirpath / fname
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            # 篇内标题降一级：## 篇 → ### 篇, ### 章 → #### 章
            content = shift_headings(content, 1)
            parts.append(content)
            parts.append("\n\n")

        parts.append("---\n\n")

    # 写入
    full_text = "".join(parts)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(full_text)

    char_count = len(full_text)
    ch_count = len(re.findall(r'^####?\s*第.+?章', full_text, re.MULTILINE))
    pian_count = len(re.findall(r'^###\s*第.+?篇', full_text, re.MULTILINE))
    juan_count = len(re.findall(r'^##\s*第.+?卷', full_text, re.MULTILINE))

    print(f"  MD全本：{OUTPUT_MD}")
    print(f"  {juan_count}卷 · {pian_count}篇 · {ch_count}章 · {char_count:,}字")
    return full_text

# ── HTML ──────────────────────────────────────────────
HTML_CSS = """
<style>
:root {
  --bg: #fdfcfa;
  --text: #2c2825;
  --accent: #8b4513;
  --muted: #6b6560;
  --border: #e8e0d8;
  --code-bg: #f5f0ea;
}
body {
  font-family: "Noto Serif CJK SC", "Source Han Serif SC", serif;
  max-width: 800px;
  margin: 0 auto;
  padding: 2em 1.5em;
  background: var(--bg);
  color: var(--text);
  line-height: 1.9;
  font-size: 16px;
}
h1 { font-size: 1.8em; color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: 0.3em; margin-top: 2em; }
h2 { font-size: 1.4em; color: var(--accent); margin-top: 1.8em; border-left: 4px solid var(--accent); padding-left: 0.5em; }
h3 { font-size: 1.2em; margin-top: 1.5em; }
h4 { font-size: 1.05em; color: var(--muted); }
blockquote { border-left: 3px solid var(--border); margin-left: 0; padding-left: 1em; color: var(--muted); }
code { background: var(--code-bg); padding: 0.15em 0.4em; border-radius: 3px; font-size: 0.9em; }
pre { background: var(--code-bg); padding: 1em; border-radius: 6px; overflow-x: auto; }
pre code { background: none; padding: 0; }
hr { border: none; border-top: 1px solid var(--border); margin: 2em 0; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid var(--border); padding: 0.5em 0.8em; text-align: left; }
th { background: var(--code-bg); }
a { color: var(--accent); }
#TOC { background: var(--code-bg); padding: 1.5em 2em; border-radius: 8px; margin-bottom: 2em; }
#TOC ul { padding-left: 1.5em; }
@media print {
  body { max-width: none; padding: 0; font-size: 11pt; }
  h1 { page-break-before: always; }
  h1:first-of-type { page-break-before: avoid; }
  h2, h3 { page-break-after: avoid; }
}
</style>
"""

def build_html():
    """用pandoc生成HTML。"""
    print("  生成HTML...")
    css_path = OUTPUT_DIR / "_style.css"
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(HTML_CSS)

    cmd = [
        "pandoc", str(OUTPUT_MD),
        "-f", "markdown-yaml_metadata_block",
        "-t", "html5", "-s",
        "--toc", "--toc-depth=3",
        "--metadata", "title=生命论（明本论）",
        "--include-in-header", str(css_path),
        "-o", str(OUTPUT_HTML)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  HTML生成警告：{result.stderr[:500]}")
    print(f"  HTML：{OUTPUT_HTML}")

# ── PDF（weasyprint，比xelatex快） ────────────────────
def build_pdf():
    """用weasyprint从HTML生成PDF。"""
    print("  生成PDF（weasyprint）...")
    if not OUTPUT_HTML.exists():
        build_html()

    from weasyprint import HTML
    HTML(filename=str(OUTPUT_HTML)).write_pdf(str(OUTPUT_PDF))
    size_mb = OUTPUT_PDF.stat().st_size / 1024 / 1024
    print(f"  PDF：{OUTPUT_PDF}（{size_mb:.1f}MB）")

# ── 主流程 ────────────────────────────────────────────
def main():
    args = set(sys.argv[1:])

    if "--check" in args:
        print("=== 验证结构 ===")
        errors, warnings = validate()
        for w in warnings:
            print(f"  ⚠ {w}")
        if errors:
            print(f"发现 {len(errors)} 个问题：")
            for e in errors:
                print(f"  ✗ {e}")
            sys.exit(1)
        print("✓ 全部通过")
        return

    do_html = "--html" in args or "--all" in args
    do_pdf = "--pdf" in args or "--all" in args

    print("=== 生命论全本构建 ===\n")

    # 1. 验证
    print("[1/3] 验证结构...")
    errors, warnings = validate()
    for w in warnings:
        print(f"  ⚠ {w}")
    if errors:
        print(f"✗ 发现 {len(errors)} 个问题，构建中止：")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    print("  ✓ 结构验证通过")

    # 2. 合并MD
    print("[2/3] 合并全本...")
    build_markdown()

    # 3. 格式转换
    print("[3/3] 格式转换...")
    if do_html or do_pdf:
        build_html()
    if do_pdf:
        build_pdf()

    print("\n=== 构建完成 ===")
    print(f"输出目录：{OUTPUT_DIR}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
生命论全本一键构建脚本
用法：python3 build_full.py [--pdf] [--html] [--check] [--all]
  无参数：构建MD全本（秒级）
  --html：额外生成HTML（秒级）
  --pdf：额外生成PDF（weasyprint，约1-2分钟）
  --check：只做验证，不构建
  --all：MD + HTML + PDF 全部生成

哲学含义：模块化是阴（沉积），构建是阳（激活）。
编号不从源文件读——源文件可能漂移；编号从顺序生成——顺序是唯一真相。
这就是"名实相符"：编号（名）由位置（实）决定，不由写在标题里的字决定。
"""

import json
import os
import re
import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
MANIFEST_PATH = SCRIPT_DIR / "manifest.json"
OUTPUT_DIR = PROJECT_DIR / "output"
OUTPUT_MD = OUTPUT_DIR / "生命论全本.md"
OUTPUT_HTML = OUTPUT_DIR / "生命论全本.html"
OUTPUT_PDF = OUTPUT_DIR / "生命论全本.pdf"

CN = ['','一','二','三','四','五','六','七','八','九','十','十一','十二']

def cn2num(s):
    cn = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    if s == '十': return 10
    if s.startswith('十'): return 10 + cn.get(s[1], 0)
    if '十' in s: return cn[s[0]]*10 + cn.get(s.split('十')[1], 0)
    return cn.get(s, 0)


def shift_headings(content, levels=1):
    """标题整体降级。"""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r'^(#{1,6})(\s.+)', line)
        if m:
            new_level = min(len(m.group(1)) + levels, 6)
            lines[i] = '#' * new_level + m.group(2)
    return "\n".join(lines)


def normalize_pian_file(content, pian_num):
    """归一化篇文件：
    1. 篇标题行替换为正确编号（编号从文件顺序生成，不信任源文件）
    2. 章之间的非章###标题降级为####（章内节）
    3. 所有标题降一级
    """
    lines = content.split("\n")

    # 找篇标题并替换
    for i, line in enumerate(lines):
        m = re.match(r'^#{1,2}\s*(?:第[一二三四五六七八九十]+篇|篇[一二三四五六七八九十]+[·：:])\s*(.+)', line)
        if m:
            title = m.group(1).strip()
            lines[i] = f"## 第{CN[pian_num]}篇 {title}"
            break

    # 找所有章标题位置
    ch_positions = [i for i, line in enumerate(lines)
                    if re.match(r'^###\s*第[一二三四五六七八九十百零]+章', line)]

    # 章之间的非章###降级为####
    if ch_positions:
        last_ch = ch_positions[-1]
        for i, line in enumerate(lines):
            if re.match(r'^###\s+', line) and not re.match(r'^###\s*第[一二三四五六七八九十百零]+章', line):
                if any(cp < i for cp in ch_positions) and i < last_ch:
                    lines[i] = '#' + line

    # 整体降一级
    return shift_headings("\n".join(lines), 1)


def normalize_appendix_file(content, app_num):
    """归一化附录文件：第一行替换为正确编号和层级，内部标题降级。"""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r'^#{1,3}\s*附录[一二三四五六七八九十]+[：:\s]*(.*)', line)
        if m:
            title = m.group(1).strip().lstrip("：:").strip()
            lines[i] = f"## 附录{CN[app_num]} {title}".rstrip()
            break
    return shift_headings("\n".join(lines), 1)


# ── 验证 ──────────────────────────────────────────────
def validate():
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

        title_file = dirpath / "00_卷标题.md"
        if title_file.exists():
            with open(title_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
            m = re.match(r'#\s*(第?[一二三四五六七八九十]+卷)', first_line)
            if m:
                fj = m.group(1)
                if not fj.startswith("第"): fj = "第" + fj
                ej = "第" + vol["number"].replace("卷","") + "卷"
                if fj != ej:
                    errors.append(f"{vol['number']}卷号不一致：文件{fj}")

        chapters = []
        for fname in os.listdir(dirpath):
            m = re.match(r'篇([一二三四五六七八九十]+)_(.+)', fname)
            if m and fname.endswith(".md"):
                chapters.append((cn2num(m.group(1)), fname))
        chapters.sort()
        nums = [n for n, _ in chapters]
        if nums != list(range(1, len(nums)+1)):
            errors.append(f"{vol['number']}篇编号不连续：{nums}")

        for num, fname in chapters:
            with open(dirpath / fname, "r", encoding="utf-8") as f:
                content = f.read()
            if not re.search(r'^#{1,2}\s*(?:第[一二三四五六七八九十]+篇|篇[一二三四五六七八九十]+[·：:])',
                           content, re.MULTILINE):
                errors.append(f"{vol['number']}篇{num}（{fname}）缺少篇标题")
            ch_nums = [cn2num(m.group(1)) for line in content.split("\n")
                       for m in [re.match(r'###\s*第([一二三四五六七八九十百零]+)章', line.strip())] if m]
            if not ch_nums:
                warnings.append(f"{vol['number']}篇{num}（{fname}）暂无章标题")
            else:
                for i in range(1, len(ch_nums)):
                    if ch_nums[i] != ch_nums[i-1] + 1:
                        errors.append(f"{vol['number']}篇{num}章编号不连续："
                                      f"第{CN[ch_nums[i-1]]}章→第{CN[ch_nums[i]]}章")
    return errors, warnings


# ── 合并 ──────────────────────────────────────────────
def build_markdown():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    OUTPUT_DIR.mkdir(exist_ok=True)
    parts = []
    parts.append("# 生命论（明本论）\n\n")
    parts.append("> 一生道，道养一，一指万物\n\n")

    # 命经（卷首，在最前面）
    mj = SCRIPT_DIR / "00_卷首_命经" / "命经.md"
    if mj.exists():
        with open(mj, "r", encoding="utf-8") as f:
            parts.append(shift_headings(f.read(), 1))
        parts.append("\n\n---\n\n")

    # 体系总纲 + 全书导言
    for front in ["00_体系总纲.md", "00_全书导言.md"]:
        fp = SCRIPT_DIR / front
        if fp.exists():
            with open(fp, "r", encoding="utf-8") as f:
                parts.append(shift_headings(f.read(), 1))
            parts.append("\n\n---\n\n")

    for vol in manifest["volumes"]:
        dp = SCRIPT_DIR / vol["dir"]
        if not dp.is_dir(): continue

        if vol["number"] == "卷首":
            # 命经已在前面合并，跳过
            continue

        if vol["number"] == "附录":
            # 尾声（全书后记，在正文之后、附录之前）
            ep = SCRIPT_DIR / "00_尾声.md"
            if ep.exists():
                with open(ep, "r", encoding="utf-8") as f:
                    parts.append(shift_headings(f.read(), 1))
                parts.append("\n\n---\n\n")

            ov = dp / "00_附录标题.md"
            if ov.exists():
                with open(ov, "r", encoding="utf-8") as f:
                    parts.append(shift_headings(f.read(), 1))
                parts.append("\n\n")
            items = []
            for fname in os.listdir(dp):
                if fname.endswith(".md") and not fname.startswith("00_"):
                    m = re.match(r'附录([一二三四五六七八九十]+)_', fname)
                    if m: items.append((cn2num(m.group(1)), fname))
            items.sort()
            for num, fname in items:
                with open(dp / fname, "r", encoding="utf-8") as f:
                    parts.append(normalize_appendix_file(f.read(), num))
                parts.append("\n\n---\n\n")
            continue

        # 正文卷
        tf = dp / "00_卷标题.md"
        if tf.exists():
            with open(tf, "r", encoding="utf-8") as f:
                first = f.readline().strip()
            m = re.match(r'#\s*(第[一二三四五六七八九十]+卷\s+.+)', first)
            if m:
                parts.append(f"## {m.group(1)}\n\n")
        else:
            parts.append(f"## {vol['number']} {vol['title']}：{vol.get('subtitle','')}\n\n")

        chapters = []
        for fname in os.listdir(dp):
            m = re.match(r'篇([一二三四五六七八九十]+)_(.+)', fname)
            if m and fname.endswith(".md"):
                chapters.append((cn2num(m.group(1)), fname))
        chapters.sort()

        for idx, (_, fname) in enumerate(chapters, 1):
            with open(dp / fname, "r", encoding="utf-8") as f:
                parts.append(normalize_pian_file(f.read(), idx))
            parts.append("\n\n")
        parts.append("---\n\n")

    full = "".join(parts)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(full)

    cc = len(full)
    ch = len(re.findall(r'^####?\s*第.+?章', full, re.MULTILINE))
    pi = len(re.findall(r'^###\s*第.+?篇', full, re.MULTILINE))
    ju = len(re.findall(r'^##\s*第.+?卷', full, re.MULTILINE))
    ap = len(re.findall(r'^###\s*附录', full, re.MULTILINE))
    print(f"  MD：{OUTPUT_MD}")
    print(f"  {ju}卷 · {pi}篇 · {ch}章 · {ap}附录 · {cc:,}字")
    return full


# ── HTML/PDF ──────────────────────────────────────────
HTML_CSS = """
<style>
:root { --bg:#fdfcfa; --text:#2c2825; --accent:#8b4513; --muted:#6b6560; --border:#e8e0d8; --code-bg:#f5f0ea; }
body { font-family:"Noto Serif CJK SC",serif; max-width:800px; margin:0 auto; padding:2em 1.5em; background:var(--bg); color:var(--text); line-height:1.9; font-size:16px; }
h1 { font-size:1.8em; color:var(--accent); border-bottom:2px solid var(--accent); padding-bottom:0.3em; margin-top:2em; }
h2 { font-size:1.4em; color:var(--accent); margin-top:1.8em; border-left:4px solid var(--accent); padding-left:0.5em; }
h3 { font-size:1.2em; margin-top:1.5em; }
h4 { font-size:1.05em; margin-top:1.2em; }
h5 { font-size:0.95em; color:var(--muted); }
blockquote { border-left:3px solid var(--border); margin-left:0; padding-left:1em; color:var(--muted); }
code { background:var(--code-bg); padding:0.15em 0.4em; border-radius:3px; font-size:0.9em; }
pre { background:var(--code-bg); padding:1em; border-radius:6px; overflow-x:auto; }
pre code { background:none; padding:0; }
hr { border:none; border-top:1px solid var(--border); margin:2em 0; }
table { border-collapse:collapse; width:100%; margin:1em 0; }
th,td { border:1px solid var(--border); padding:0.5em 0.8em; text-align:left; }
th { background:var(--code-bg); }
a { color:var(--accent); }
#TOC { background:var(--code-bg); padding:1.5em 2em; border-radius:8px; margin-bottom:2em; }
#TOC ul { padding-left:1.5em; }
@media print { body{max-width:none;padding:0;font-size:11pt;} h1,h2{page-break-before:always;} h1:first-of-type,h2:first-of-type{page-break-before:avoid;} h3,h4{page-break-after:avoid;} }
</style>
"""

def build_html():
    print("  生成HTML...")
    css = OUTPUT_DIR / "_style.css"
    css.write_text(HTML_CSS, encoding="utf-8")
    r = subprocess.run(["pandoc", str(OUTPUT_MD), "-f", "markdown-yaml_metadata_block",
        "-t", "html5", "-s", "--toc", "--toc-depth=3",
        "--metadata", "title=生命论（明本论）", "--include-in-header", str(css),
        "-o", str(OUTPUT_HTML)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  HTML警告：{r.stderr[:300]}")
    print(f"  HTML：{OUTPUT_HTML}")

def build_pdf():
    print("  生成PDF...")
    if not OUTPUT_HTML.exists(): build_html()
    from weasyprint import HTML
    HTML(filename=str(OUTPUT_HTML)).write_pdf(str(OUTPUT_PDF))
    print(f"  PDF：{OUTPUT_PDF}（{OUTPUT_PDF.stat().st_size/1024/1024:.1f}MB）")


def main():
    args = set(sys.argv[1:])
    if "--check" in args:
        print("=== 验证结构 ===")
        errors, warnings = validate()
        for w in warnings: print(f"  ⚠ {w}")
        if errors:
            print(f"发现 {len(errors)} 个问题：")
            for e in errors: print(f"  ✗ {e}")
            sys.exit(1)
        print("✓ 全部通过")
        return

    do_html = "--html" in args or "--all" in args
    do_pdf = "--pdf" in args or "--all" in args

    print("=== 生命论全本构建 ===\n")
    print("[1/3] 验证结构...")
    errors, warnings = validate()
    for w in warnings: print(f"  ⚠ {w}")
    if errors:
        print(f"✗ {len(errors)}个问题，构建中止：")
        for e in errors: print(f"  ✗ {e}")
        sys.exit(1)
    print("  ✓ 通过")

    print("[2/3] 合并全本...")
    build_markdown()

    print("[3/3] 格式转换...")
    if do_html or do_pdf: build_html()
    if do_pdf: build_pdf()
    print(f"\n=== 完成 ===\n输出：{OUTPUT_DIR}")

if __name__ == "__main__":
    main()

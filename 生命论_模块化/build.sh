#!/bin/bash
# 生命论模块化构建脚本
# 用法：bash build.sh [--pdf-only|--html-only|--check]
#   无参数：构建HTML + PDF
#   --html-only：只构建HTML（秒级）
#   --pdf-only：只构建PDF（5-10分钟）
#   --check：只做质量检查，不构建
# 改完任意模块后直接跑此脚本即可

set -e
cd "$(dirname "$0")/.."
WORKSPACE=$(pwd)
MODDIR="生命论_模块化"
OUTPUT_MD="生命论合订本_最新.md"
OUTPUT_HTML="生命论（明本论）合订本.html"
OUTPUT_PDF="生命论（明本论）合订本_出版级排版.pdf"

# 质量检查函数
quality_check() {
    echo "[质检] 运行质量检查..."
    python3 - "$OUTPUT_MD" << 'PYEOF'
import sys, re

with open(sys.argv[1], 'rb') as f:
    data = f.read()

errors = []

# 1. null字节检查
null_count = data.count(b'\x00')
if null_count > 0:
    errors.append(f"发现 {null_count} 个null字节（稀疏文件问题）")

text = data.decode('utf-8', errors='replace')

# 2. 章节编号连续性
chapters = []
for m in re.finditer(r'^### 第(.+?)章\s+(.+)$', text, re.MULTILINE):
    chapters.append((m.group(1), m.group(2)))

cn = {'零':0,'一':1,'二':2,'两':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
def cn2int(s):
    result = 0
    if '百' in s:
        parts = s.split('百')
        result += cn.get(parts[0], 1) * 100
        s = parts[1] if len(parts) > 1 else ''
        if s.startswith('零'): s = s[1:]
    if '十' in s:
        parts = s.split('十')
        if parts[0]: result += cn[parts[0]] * 10
        else: result += 10
        if len(parts) > 1 and parts[1]: result += cn[parts[1]]
    elif s:
        result += cn.get(s, 0)
    return result

nums = [cn2int(c[0]) for c in chapters]
seen = set()
for n in nums:
    if n in seen:
        errors.append(f"章节编号重复：第{n}章")
    seen.add(n)
for i in range(1, len(nums)):
    if nums[i] != nums[i-1] + 1:
        errors.append(f"编号不连续：第{nums[i-1]}章→第{nums[i]}章")

# 3. 重复章节标题
titles = [c[1] for c in chapters]
from collections import Counter
for title, count in Counter(titles).items():
    if count > 1:
        errors.append(f"章节标题重复：{title}（{count}次）")

# 4. 已知错字检查
typos = ['置氧', '辨证法', '生命必胜']
for typo in typos:
    # 排除"生命必胜"在解释"为什么不说必胜"的语境
    if typo == '生命必胜':
        for line in text.split('\n'):
            if '生命必胜' in line and '而不是' not in line and '不说' not in line and '从' not in line and '改为' not in line:
                errors.append(f"可能残留'生命必胜'：{line[:60]}")
    elif typo in text:
        errors.append(f"发现错字：{typo}")

# 5. manifest完整性检查
import os
# build.sh在moddir中运行，输出到上一级；moddir就是build.sh所在目录
moddir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), '生命论_模块化')
if not os.path.isdir(moddir):
    moddir = '生命论_模块化'
manifest_path = os.path.join(moddir, 'manifest.txt')
if os.path.exists(manifest_path):
    with open(manifest_path, 'r') as mf:
        manifest_files = set()
        for line in mf:
            line = line.strip()
            if line and not line.startswith('#'):
                manifest_files.add(line)
    # 扫描子目录中所有md文件（根目录的00_修订记/00_总序/00_推导链是固定文件，不在manifest中）
    skip_files = {'AGENTS.md', 'README.md'}
    actual_files = set()
    for root, dirs, files in os.walk(moddir):
        for fn in files:
            if fn.endswith('.md') and fn not in skip_files:
                rel = os.path.relpath(os.path.join(root, fn), moddir)
                # 根目录的三个固定文件不在manifest中
                if '/' not in rel and rel.startswith('00_'):
                    continue
                actual_files.add(rel)
    missing = actual_files - manifest_files
    for m in sorted(missing):
        errors.append(f"文件未加入manifest.txt：{m}")
    ghost = manifest_files - actual_files
    for g in sorted(ghost):
        errors.append(f"manifest中文件不存在：{g}")

# 6. 字数统计
char_count = len(text)
print(f"  总字节：{len(data):,}")
print(f"  总字符：{char_count:,}")
print(f"  总章数：{len(chapters)}")

if errors:
    print(f"\n[质检] 发现 {len(errors)} 个问题：")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)
else:
    print("[质检] 全部通过 ✓")
PYEOF
}

# --check 模式：只检查
if [ "$1" = "--check" ]; then
    echo "=== 生命论质量检查 ==="
    quality_check
    exit 0
fi

echo "=== 生命论构建系统 ==="

# 0. 删除旧输出文件（防止稀疏文件null字节问题）
echo "[0/4] 清理旧文件..."
rm -f "$OUTPUT_MD" "$OUTPUT_HTML" "$OUTPUT_PDF" /tmp/html_full.md /tmp/pdf_full.md

# 1. 用Python合并模块（比cat更可靠，避免编码和稀疏文件问题）
echo "[1/4] 合并模块..."
python3 - "$MODDIR" "$OUTPUT_MD" << 'PYEOF'
import sys, os
moddir, output = sys.argv[1], sys.argv[2]
with open(output, 'w', encoding='utf-8') as out:
    # 修订记与体系总纲
    with open(os.path.join(moddir, '00_修订记与体系总纲.md'), 'r', encoding='utf-8') as f:
        out.write(f.read())
    out.write('\n\n---\n\n')
    # 总序
    with open(os.path.join(moddir, '00_总序与导论.md'), 'r', encoding='utf-8') as f:
        out.write(f.read())
    out.write('\n\n---\n\n')
    # 推导链总览
    with open(os.path.join(moddir, '00_推导链总览.md'), 'r', encoding='utf-8') as f:
        out.write(f.read())
    out.write('\n\n---\n\n')
    # manifest中的文件
    with open(os.path.join(moddir, 'manifest.txt'), 'r', encoding='utf-8') as f:
        for line in f:
            fpath = line.strip()
            if not fpath or fpath.startswith('#'):
                continue
            full = os.path.join(moddir, fpath)
            if not os.path.exists(full):
                print(f"  警告：文件不存在 {fpath}")
                continue
            with open(full, 'r', encoding='utf-8') as mf:
                out.write(mf.read())
            out.write('\n\n')
PYEOF
echo "  合并完成：$(wc -c < "$OUTPUT_MD") 字节"

# 2. 质量检查
quality_check

# 3. 生成HTML
if [ "$1" != "--pdf-only" ]; then
    echo "[2/4] 生成HTML..."
    cat > /tmp/html_cover.md << 'COVER'
<div class="book-cover">
<p class="title">生命论</p>
<p class="subtitle">（明本论）</p>
<p class="cover-desc">——从操作出发的存在论革命<br>与旧哲学总清算</p>
<p class="version">全本·九卷 + 附录六种<br>2026年8月</p>
</div>

---

COVER
    cat /tmp/html_cover.md "$OUTPUT_MD" > /tmp/html_full.md
    pandoc /tmp/html_full.md \
        -f markdown-yaml_metadata_block -t html5 -s \
        --toc --toc-depth=2 \
        --include-in-header=html_header.html \
        --metadata title="生命论（明本论）" \
        -o "$OUTPUT_HTML"
    echo "  HTML完成：$OUTPUT_HTML ($(du -h "$OUTPUT_HTML" | cut -f1))"
fi

# 4. 生成PDF
if [ "$1" != "--html-only" ]; then
    echo "[3/4] 生成PDF（xelatex，约5-10分钟）..."
    cat > /tmp/pdf_cover.md << 'COVER'
\begin{titlepage}
\centering
\vspace*{3cm}
{\sffamily\bfseries\fontsize{42pt}{50pt}\selectfont 生命论\par}
\vspace{0.5cm}
{\sffamily\bfseries\fontsize{28pt}{36pt}\selectfont （明本论）\par}
\vspace{2cm}
{\sffamily\fontsize{18pt}{24pt}\selectfont ——从操作出发的存在论革命\par}
{\sffamily\fontsize{18pt}{24pt}\selectfont 与旧哲学总清算\par}
\vspace{3cm}
{\sffamily\fontsize{16pt}{22pt}\selectfont 全本·九卷 + 附录六种\par}
\vspace{1cm}
{\sffamily\fontsize{14pt}{20pt}\selectfont 2026年8月\par}
\vfill
\end{titlepage}

\setcounter{tocdepth}{1}
\pagenumbering{roman}
\tableofcontents

\clearpage
\pagenumbering{arabic}
\setcounter{page}{1}

COVER
    cat /tmp/pdf_cover.md "$OUTPUT_MD" > /tmp/pdf_full.md
    pandoc /tmp/pdf_full.md \
        -f markdown-yaml_metadata_block \
        -o "$OUTPUT_PDF" \
        --pdf-engine=xelatex \
        --include-in-header=publish_style.tex \
        -V documentclass=book \
        -V classoption=oneside,11pt \
        -V CJKmainfont="Noto Serif CJK SC"
    echo "  PDF完成：$OUTPUT_PDF ($(du -h "$OUTPUT_PDF" | cut -f1))"
fi

# 清理临时文件
rm -f /tmp/html_cover.md /tmp/html_full.md /tmp/pdf_cover.md /tmp/pdf_full.md

echo "[4/4] 构建完成。"

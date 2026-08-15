#!/bin/bash
# 多格式构建：PDF / HTML / EPUB / DOCX / TXT / MD
# 用法：bash build_all.sh [格式名...]  无参数=全部
set -e
cd "$(dirname "$0")/.."
MODDIR="生命论_模块化"
OUTDIR="生命论_输出"
mkdir -p "$OUTDIR"

echo "[0] 合并模块..."
bash "$MODDIR/build.sh" --html-only > /dev/null 2>&1
FULL_MD="生命论合订本_最新.md"

if [ $# -eq 0 ]; then TARGETS="pdf html epub docx txt md"; else TARGETS="$*"; fi

want() { echo "$TARGETS" | grep -qw "$1"; }

# ---- 封面 ----
cat > /tmp/cover.html.md << 'COVER'
<div class="book-cover">
<p class="title">生命论</p>
<p class="subtitle">（明本论）</p>
<p class="cover-desc">——从操作出发的存在论革命<br>与旧哲学总清算</p>
<p class="version">完美版·全九卷 + 附录六种<br>2026年8月</p>
</div>

---

COVER

cat > /tmp/cover.tex.md << 'COVER'
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
{\sffamily\fontsize{16pt}{22pt}\selectfont 完美版·全九卷 + 附录六种\par}
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

# ---- PDF ----
if want pdf; then
  echo "[1/6] PDF..."
  cat /tmp/cover.tex.md "$FULL_MD" > /tmp/full_pdf.md
  pandoc /tmp/full_pdf.md -f markdown-yaml_metadata_block \
    -o "$OUTDIR/生命论（明本论）.pdf" --pdf-engine=xelatex \
    --include-in-header=publish_style.tex \
    -V documentclass=book -V classoption=oneside,11pt \
    -V CJKmainfont="Noto Serif CJK SC" 2>&1 | tail -1
  echo "  -> PDF"
fi

# ---- HTML ----
if want html; then
  echo "[2/6] HTML..."
  cat /tmp/cover.html.md "$FULL_MD" > /tmp/full_html.md
  pandoc /tmp/full_html.md -f markdown-yaml_metadata_block -t html5 -s \
    --toc --toc-depth=2 --include-in-header=html_header.html \
    --metadata title="生命论（明本论）" \
    -o "$OUTDIR/生命论（明本论）.html"
  echo "  -> HTML"
fi

# ---- EPUB ----
if want epub; then
  echo "[3/6] EPUB..."
  cat /tmp/cover.html.md "$FULL_MD" > /tmp/full_epub.md
  pandoc /tmp/full_epub.md -f markdown-yaml_metadata_block -t epub3 \
    --toc --toc-depth=2 --metadata title="生命论（明本论）" \
    --metadata author="明本论" --metadata lang="zh-CN" \
    -o "$OUTDIR/生命论（明本论）.epub" 2>&1
  echo "  -> EPUB"
fi

# ---- DOCX ----
if want docx; then
  echo "[4/6] DOCX..."
  pandoc "$FULL_MD" -f markdown-yaml_metadata_block -t docx \
    --toc --toc-depth=2 --metadata title="生命论（明本论）" \
    -o "$OUTDIR/生命论（明本论）.docx" 2>&1
  echo "  -> DOCX"
fi

# ---- TXT ----
if want txt; then
  echo "[5/6] TXT..."
  pandoc "$FULL_MD" -f markdown-yaml_metadata_block -t plain --wrap=none \
    -o "$OUTDIR/生命论（明本论）.txt" 2>&1
  echo "  -> TXT"
fi

# ---- MD ----
if want md; then
  echo "[6/6] MD..."
  cp "$FULL_MD" "$OUTDIR/生命论（明本论）.md"
  echo "  -> MD"
fi

echo ""
echo "=== 构建完成 ==="
ls -lhS "$OUTDIR/" 2>/dev/null | awk 'NR>1{print "  "$5, $9}'

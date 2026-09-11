#!/usr/bin/env python3
"""合订本转HTML v2 — 用pandoc转换，精美排版，带目录锚点，单文件
生成前自动跑硬门禁，不通过则中止。"""
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun")
MD = REPO / "build_output/生命论_合订本.md"
OUT = REPO / "build_output/生命论_合订本.html"

# 生成前硬门禁：不通过则中止
print("🔍 运行硬门禁检查...")
gate = subprocess.run(
    [sys.executable, str(REPO / "scripts/质量检查/run_all_checks.py")],
    capture_output=True, text=True, cwd=str(REPO)
)
print(gate.stdout[-500:] if gate.stdout else "")
if gate.returncode != 0:
    print("❌ 硬门禁未通过，中止HTML生成")
    sys.exit(1)
print("✅ 硬门禁通过，开始生成HTML\n")

CSS = """
:root{--gold:#b8860b;--gold-light:#d4a574;--bg:#faf8f5;--text:#2c2416;--muted:#6b5d4f;--border:#e0d5c5}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Noto Serif SC","Source Han Serif SC","Songti SC",Georgia,serif;background:var(--bg);color:var(--text);line-height:1.9;font-size:17px;max-width:860px;margin:0 auto;padding:40px 24px 100px}
h1{font-size:2em;color:var(--gold);border-bottom:2px solid var(--gold);padding-bottom:.3em;margin:2em 0 .8em}
h2{font-size:1.5em;color:var(--gold);margin:1.8em 0 .8em;border-left:4px solid var(--gold);padding-left:.5em}
h3{font-size:1.25em;color:var(--text);margin:1.5em 0 .6em}
h4,h5,h6{font-size:1.1em;margin:1.2em 0 .5em;color:var(--muted)}
p{margin:.8em 0;text-align:justify}
ul,ol{margin:.8em 0;padding-left:2em}
li{margin:.3em 0}
blockquote{border-left:3px solid var(--gold-light);background:#f5f0e8;margin:1em 0;padding:.8em 1.2em;color:var(--muted)}
blockquote p{margin:.3em 0}
hr{border:none;border-top:1px solid var(--border);margin:2em 0}
a{color:var(--gold);text-decoration:none}
a:hover{text-decoration:underline}
code{background:#eee;padding:2px 6px;border-radius:3px;font-size:.9em}
strong{color:var(--gold)}
table{border-collapse:collapse;margin:1em 0;width:100%}
th,td{border:1px solid var(--border);padding:8px 12px;text-align:left}
th{background:#f0e8d8;color:var(--gold)}
.cover{text-align:center;padding:80px 0 60px;border-bottom:2px solid var(--gold);margin-bottom:2em}
.cover h1{border:none;font-size:2.8em;margin-bottom:.2em;color:var(--gold)}
.cover .sub{color:var(--muted);font-size:1.1em;margin-top:.8em}
.cover .meta{color:var(--muted);font-size:.95em;margin-top:2em;line-height:2}
.toc{background:#fff;border:1px solid var(--border);border-radius:8px;padding:24px 28px;margin:2em 0}
.toc h2{border:none;margin-top:0;font-size:1.3em}
.toc ul{padding-left:1.5em}
.toc > ul{padding-left:0;list-style:none}
.toc > ul > li{margin:.6em 0;font-weight:600;color:var(--gold)}
.toc > ul > li > ul{font-weight:400;color:var(--text)}
.toc > ul > li > ul > li{margin:.2em 0}
.back-top{position:fixed;bottom:30px;right:30px;background:var(--gold);color:#fff;width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:20px;opacity:.7;transition:opacity .2s;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,.2)}
.back-top:hover{opacity:1}
@media(max-width:600px){body{font-size:15px;padding:20px 16px}h1{font-size:1.6em}.cover h1{font-size:2em}}
"""

result = subprocess.run(
    ["pandoc", str(MD), "-f", "markdown-yaml_metadata_block-tex_math_dollars-tex_math_single_backslash", "-t", "html",
     "--standalone", "--toc", "--toc-depth=2", "--wrap=none"],
    capture_output=True, text=True
)
full_html = result.stdout
import re
m = re.search(r"<body>(.*)</body>", full_html, re.DOTALL)
body = m.group(1) if m else full_html
# 去掉pandoc自动生成的标题块（避免与封面重复）
body = re.sub(r'<header id="title-block-header">.*?</header>', '', body, flags=re.DOTALL)
body = body.replace('<nav id="TOC"', '<nav class="toc" id="TOC"')

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>生命论（明本论）· 合订本 v1.1</title>
<style>{CSS}</style>
</head>
<body>
<div class="cover">
<div class="cover-title">生命论（明本论）</div>
<div class="sub">合订本 v1.1 · 干净全本</div>
<div class="meta">
作者：北原慢热<br>
生成时间：2026-09-10<br>
来源：<a href="https://github.com/192781-li/mingbenlun">github.com/192781-li/mingbenlun</a><br>
12卷+卷首+尾声，119篇，约60万字
</div>
</div>
{body}
<div class="back-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</div>
</body>
</html>"""

OUT.parent.mkdir(exist_ok=True)
OUT.write_bytes(b"\xef\xbb\xbf" + html.encode("utf-8"))
print(f"HTML生成完成: {len(html):,} 字符, {OUT.stat().st_size//1024}KB")
print(f"输出: {OUT}")

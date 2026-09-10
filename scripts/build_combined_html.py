#!/usr/bin/env python3
"""合订本转HTML — 排版精美的单文件，点进去直接看正文"""
import re
from pathlib import Path

md = Path("/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun/build_output/生命论_合订本.md").read_text(encoding="utf-8")

def inline_format(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text

def md_to_html(text):
    lines = text.split("\n")
    html = []
    in_list = False
    in_quote = False
    for line in lines:
        stripped = line.strip()
        m = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if m:
            if in_list: html.append("</ul>"); in_list = False
            if in_quote: html.append("</blockquote>"); in_quote = False
            level = len(m.group(1))
            content = inline_format(m.group(2))
            anchor = re.sub(r"[^\w\u4e00-\u9fff]", "-", content)[:40]
            html.append(f'<h{level} id="{anchor}">{content}</h{level}>')
            continue
        if stripped == "---":
            if in_list: html.append("</ul>"); in_list = False
            html.append("<hr>")
            continue
        if stripped.startswith(">"):
            if not in_quote: html.append("<blockquote>"); in_quote = True
            content = inline_format(stripped.lstrip("> "))
            html.append(f"<p>{content}</p>")
            continue
        elif in_quote:
            html.append("</blockquote>"); in_quote = False
        if re.match(r"^[-*]\s+", stripped):
            if not in_list: html.append("<ul>"); in_list = True
            content = inline_format(re.sub(r"^[-*]\s+", "", stripped))
            html.append(f"<li>{content}</li>")
            continue
        elif in_list:
            html.append("</ul>"); in_list = False
        if not stripped:
            continue
        html.append(f"<p>{inline_format(stripped)}</p>")
    if in_list: html.append("</ul>")
    if in_quote: html.append("</blockquote>")
    return "\n".join(html)

body = md_to_html(md)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>生命论（明本论）· 合订本 v1.1</title>
<style>
:root{{--gold:#b8860b;--gold-light:#d4a574;--bg:#faf8f5;--text:#2c2416;--muted:#6b5d4f;--border:#e0d5c5}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:"Noto Serif SC","Source Han Serif SC","Songti SC",Georgia,serif;background:var(--bg);color:var(--text);line-height:1.9;font-size:17px;max-width:820px;margin:0 auto;padding:40px 24px 80px}}
h1{{font-size:2em;color:var(--gold);border-bottom:2px solid var(--gold);padding-bottom:.3em;margin:1.5em 0 .8em}}
h2{{font-size:1.5em;color:var(--gold);margin:1.8em 0 .8em;border-left:4px solid var(--gold);padding-left:.5em}}
h3{{font-size:1.25em;color:var(--text);margin:1.5em 0 .6em}}
h4,h5,h6{{font-size:1.1em;margin:1.2em 0 .5em;color:var(--muted)}}
p{{margin:.8em 0;text-align:justify}}
ul{{margin:.8em 0;padding-left:2em}}
li{{margin:.3em 0}}
blockquote{{border-left:3px solid var(--gold-light);background:#f5f0e8;margin:1em 0;padding:.8em 1.2em;color:var(--muted)}}
blockquote p{{margin:.3em 0}}
hr{{border:none;border-top:1px solid var(--border);margin:2em 0}}
a{{color:var(--gold);text-decoration:none}}
a:hover{{text-decoration:underline}}
code{{background:#eee;padding:2px 6px;border-radius:3px;font-size:.9em}}
strong{{color:var(--gold)}}
.cover{{text-align:center;padding:60px 0 40px;border-bottom:2px solid var(--gold)}}
.cover h1{{border:none;font-size:2.5em;margin-bottom:.2em}}
.cover .sub{{color:var(--muted);font-size:1.1em;margin-top:1em}}
.back-top{{position:fixed;bottom:30px;right:30px;background:var(--gold);color:#fff;width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:20px;opacity:.7;transition:opacity .2s;z-index:100}}
.back-top:hover{{opacity:1}}
@media(max-width:600px){{body{{font-size:15px;padding:20px 16px}}h1{{font-size:1.6em}}}}
</style>
</head>
<body>
<div class="cover">
<h1>生命论（明本论）</h1>
<div class="sub">合订本 v1.1 · 干净全本 · 2026-09-10</div>
<div class="sub">作者：北原慢热</div>
</div>
{body}
<div class="back-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</div>
</body>
</html>"""

out = Path("/tmp/shengminglun_combined_v1.1.html")
out.write_text(html, encoding="utf-8")
print(f"HTML生成完成: {len(html):,} 字符, {out.stat().st_size//1024}KB")

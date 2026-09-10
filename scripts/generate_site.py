#!/usr/bin/env python3
"""生命论全本静态网站生成器"""
import os, re, markdown
from pathlib import Path

REPO = Path("/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun")
SRC = REPO / "生命论_模块化"
OUT = REPO / "site"

CSS = """
:root{--gold:#d4a574;--gold-dark:#8a6d2f;--bg:#faf8f5;--text:#2c2416;--muted:#6b5d4f;--border:#e0d5c5;--accent:#c44040}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Noto Serif SC","Source Han Serif SC",Georgia,serif;background:var(--bg);color:var(--text);line-height:1.8;font-size:17px}
.topbar{position:sticky;top:0;background:rgba(250,248,245,.95);backdrop-filter:blur(10px);border-bottom:1px solid var(--border);padding:12px 20px;z-index:100;display:flex;justify-content:space-between;align-items:center}
.topbar a{color:var(--gold-dark);text-decoration:none;font-weight:600}
.topbar .title{font-size:1.1em;color:var(--gold-dark)}
.progress{position:fixed;top:0;left:0;height:3px;background:var(--gold);width:0;z-index:200;transition:width .1s}
.container{max-width:800px;margin:0 auto;padding:40px 24px 80px}
.index-container{max-width:900px}
h1{font-size:2em;margin-bottom:.5em;color:var(--gold-dark);border-bottom:2px solid var(--gold);padding-bottom:.3em}
h2{font-size:1.5em;margin:1.5em 0 .8em;color:var(--gold-dark)}
h3{font-size:1.25em;margin:1.2em 0 .6em;color:var(--text)}
h4{font-size:1.1em;margin:1em 0 .5em}
p{margin:.8em 0}
blockquote{border-left:4px solid var(--gold);padding:8px 20px;margin:1em 0;background:#f5f0e8;color:var(--muted);font-style:italic}
code{background:#f0ebe0;padding:2px 6px;border-radius:3px;font-size:.9em}
pre{background:#2c2416;color:#e0d5c5;padding:16px;border-radius:6px;overflow-x:auto;margin:1em 0}
pre code{background:none;padding:0}
table{border-collapse:collapse;width:100%;margin:1em 0}
th,td{border:1px solid var(--border);padding:8px 12px;text-align:left}
th{background:#f5f0e8;color:var(--gold-dark)}
ul,ol{margin:.8em 0;padding-left:2em}
li{margin:.3em 0}
hr{border:none;border-top:1px solid var(--border);margin:2em 0}
a{color:var(--gold-dark);text-decoration:none}
a:hover{text-decoration:underline}
.toc-list{list-style:none;padding:0}
.toc-list li{margin:.4em 0}
.toc-list .volume{font-weight:600;color:var(--gold-dark);font-size:1.1em;margin-top:1em}
.toc-list .chapter{padding-left:1.5em;font-size:.95em}
.toc-list .chapter a{color:var(--text)}
.nav-links{display:flex;justify-content:space-between;margin-top:3em;padding-top:1em;border-top:1px solid var(--border)}
.nav-links a{color:var(--gold-dark);font-weight:600}
.hero{text-align:center;padding:60px 20px 40px}
.hero h1{border:none;font-size:2.5em;margin-bottom:.2em}
.hero .subtitle{color:var(--muted);font-size:1.1em;font-style:italic}
.hero .meta{margin-top:1em;color:var(--muted);font-size:.9em}
.volume-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px;margin:2em 0}
.volume-card{border:1px solid var(--border);border-radius:8px;padding:20px;background:#fff;transition:box-shadow .2s}
.volume-card:hover{box-shadow:0 4px 12px rgba(0,0,0,.1)}
.volume-card h3{margin:0 0 .5em;color:var(--gold-dark)}
.volume-card p{font-size:.9em;color:var(--muted);margin:0}
@media(max-width:600px){body{font-size:16px}.container{padding:20px 16px 60px}.hero h1{font-size:1.8em}.volume-grid{grid-template-columns:1fr}}
"""

JS = """
window.addEventListener('scroll',()=>{
  const h=document.documentElement;
  const pct=(h.scrollTop/(h.scrollHeight-h.clientHeight))*100;
  document.querySelector('.progress').style.width=pct+'%';
});
"""

def get_volume_order():
    """获取卷的顺序和名称"""
    volumes = []
    for d in sorted(SRC.iterdir()):
        if d.is_dir() and d.name[0].isdigit():
            volumes.append(d)
    return volumes

def md_to_html(md_text):
    """markdown转HTML"""
    return markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'toc'])

def extract_title(md_text, filename):
    """从markdown提取标题"""
    for line in md_text.split('\n')[:10]:
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
        if line.startswith('## '):
            return line[3:].strip()
    return filename.replace('.md', '')

def generate_index(volumes):
    """生成首页"""
    cards = ""
    toc = ""
    for vol in volumes:
        vol_name = vol.name
        # 提取卷名
        parts = vol_name.split('_', 2)
        vol_num = parts[0] if len(parts) > 0 else ""
        vol_title = parts[2] if len(parts) > 2 else vol_name
        
        chapters = []
        for f in sorted(vol.glob("*.md")):
            title = extract_title(f.read_text(encoding='utf-8'), f.name)
            rel = f.relative_to(SRC).with_suffix('.html')
            chapters.append((title, str(rel)))
        
        # 卷首页
        vol_index = vol / "index.md"
        vol_link = f"{vol_name}/index.html" if vol_index.exists() else (chapters[0][1] if chapters else "#")
        
        cards += f'<div class="volume-card"><h3><a href="{vol_link}">{vol_name}</a></h3><p>{len(chapters)}篇</p></div>\n'
        
        toc += f'<li class="volume"><a href="{vol_link}">{vol_name}</a></li>\n'
        for title, link in chapters:
            toc += f'<li class="chapter"><a href="{link}">{title}</a></li>\n'
    
    # 00级文件（总纲、导言等）
    root_files = ""
    for f in sorted(SRC.glob("00_*.md")):
        title = extract_title(f.read_text(encoding='utf-8'), f.name)
        rel = f.name.replace('.md', '.html')
        root_files += f'<li class="chapter"><a href="{rel}">{title}</a></li>\n'
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>生命论（明本论）</title>
<style>{CSS}</style>
</head>
<body>
<div class="progress"></div>
<div class="topbar"><span class="title">生命论（明本论）</span><a href="index.html">目录</a></div>
<div class="container index-container">
<div class="hero">
<h1>生命论</h1>
<p class="subtitle">从"在感"出发，推导出人的解放何以可能</p>
<p class="meta">北原慢热 著 · 11卷+附录 · 共{sum(len(list(v.glob("*.md"))) for v in volumes)}篇</p>
</div>
<h2>全本目录</h2>
{root_files}
<ul class="toc-list">
{toc}
</ul>
<h2>按卷浏览</h2>
<div class="volume-grid">
{cards}
</div>
</div>
<script>{JS}</script>
</body>
</html>"""
    return html

def generate_page(md_file, volumes, all_files):
    """生成单个页面"""
    md_text = md_file.read_text(encoding='utf-8')
    title = extract_title(md_text, md_file.name)
    content = md_to_html(md_text)
    
    # 计算相对路径深度
    rel = md_file.relative_to(SRC)
    depth = len(rel.parts) - 1
    prefix = "../" * depth
    
    # 上一篇/下一篇
    flat_files = []
    for f in sorted(SRC.glob("00_*.md")):
        flat_files.append(f)
    for vol in volumes:
        for f in sorted(vol.glob("*.md")):
            flat_files.append(f)
    
    idx = flat_files.index(md_file) if md_file in flat_files else -1
    prev_link = ""
    next_link = ""
    if idx > 0:
        prev_f = flat_files[idx-1]
        prev_rel = prev_f.relative_to(SRC).with_suffix('.html')
        prev_title = extract_title(prev_f.read_text(encoding='utf-8'), prev_f.name)
        prev_link = f'<a href="{prefix}{prev_rel}">← {prev_title}</a>'
    if idx < len(flat_files) - 1:
        next_f = flat_files[idx+1]
        next_rel = next_f.relative_to(SRC).with_suffix('.html')
        next_title = extract_title(next_f.read_text(encoding='utf-8'), next_f.name)
        next_link = f'<a href="{prefix}{next_rel}">{next_title} →</a>'
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 生命论</title>
<style>{CSS}</style>
</head>
<body>
<div class="progress"></div>
<div class="topbar"><span class="title">生命论（明本论）</span><a href="{prefix}index.html">目录</a></div>
<div class="container">
{content}
<div class="nav-links">
{prev_link}
{next_link}
</div>
</div>
<script>{JS}</script>
</body>
</html>"""
    return html

def main():
    volumes = get_volume_order()
    print(f"找到 {len(volumes)} 卷")
    
    # 清空输出目录
    if OUT.exists():
        import shutil
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    
    # 生成首页
    (OUT / "index.html").write_text(generate_index(volumes), encoding='utf-8')
    print("生成首页")
    
    # 生成00级文件
    count = 0
    for f in sorted(SRC.glob("00_*.md")):
        html = generate_page(f, volumes, None)
        out_file = OUT / f.name.replace('.md', '.html')
        out_file.write_text(html, encoding='utf-8')
        count += 1
    
    # 生成各卷页面
    for vol in volumes:
        out_vol = OUT / vol.name
        out_vol.mkdir(exist_ok=True)
        for f in sorted(vol.glob("*.md")):
            html = generate_page(f, volumes, None)
            out_file = out_vol / f.name.replace('.md', '.html')
            out_file.write_text(html, encoding='utf-8')
            count += 1
    
    print(f"生成 {count} 个页面")
    print(f"网站输出到: {OUT}")

if __name__ == "__main__":
    main()

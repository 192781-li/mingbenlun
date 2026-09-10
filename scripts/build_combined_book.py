#!/usr/bin/env python3
"""生命论合订本生成器 — 按卷顺序合并所有Markdown，自动过滤研究笔记元注释"""
import os
import re
from pathlib import Path
from datetime import datetime

REPO = Path("/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun")
BOOK_DIR = REPO / "生命论_模块化"
OUT = REPO / "build_output"
OUT.mkdir(exist_ok=True)

def strip_meta_notes(content):
    """移除过程性状态标注（状态：待入全本/待核实），保留原话/展开/语境等思想内容。
    源文件保留完整元注释，合订本输出时只去掉状态行，内容融入全本。"""
    lines = content.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        # 只去掉状态标注行，保留原话/展开/语境/核心/出处等内容
        if re.match(r'^[-*]\s+\*\*状态\*\*', stripped) and ("待入全本" in stripped or "待核实" in stripped):
            continue
        if re.match(r'^>\s*\*\*状态\*\*', stripped) and ("待入全本" in stripped or "待核实" in stripped):
            continue
        result.append(line)
    return "\n".join(result)

# 卷顺序（目录名）
VOLUMES = [
    "00_卷首_命经",
    "01_卷一_存在论",
    "02_卷二_操作论",
    "03_卷三_认识论",
    "04_卷四_实践论",
    "05_卷五_群己论",
    "06_卷六_异化论",
    "07_卷七_解放论",
    "08_卷八_格物论",
    "09_卷九_人文论",
    "10_卷十_传统论",
    "11_卷十一_践演论",
    "12_附录",
]

# 卷首文件（根目录下的）
FRONT_MATTER = [
    "00_全书导言.md",
    "00_体系总纲.md",
    "00_推导链总览.md",
]

def collect_md_files(directory):
    """收集目录下所有md文件，按文件名排序"""
    files = []
    for f in sorted(directory.glob("*.md")):
        if f.is_file():
            files.append(f)
    return files

def normalize_headings(content, is_volume_title=False):
    """统一标题层级：卷标题文件保持H1，其他文件若首标题为H1则整体降一级。
    确保合订本中：卷=H1，篇=H2，章=H3，节=H4。"""
    if is_volume_title:
        return content
    lines = content.split("\n")
    # 检测第一个标题的层级
    first_level = None
    for line in lines:
        m = re.match(r"^(#{1,6})\s", line.strip())
        if m:
            first_level = len(m.group(1))
            break
    if first_level is None or first_level >= 2:
        return content  # 已经是H2+，不需要改
    # 首标题是H1，全部降一级
    result = []
    for line in lines:
        m = re.match(r"^(#{1,5})\s", line)
        if m:
            line = "#" + line  # 加一个#，H1→H2, H2→H3...
        result.append(line)
    return "\n".join(result)

def build_combined():
    parts = []
    total_chars = 0
    total_files = 0
    
    # 封面
    date_str = datetime.now().strftime("%Y-%m-%d")
    parts.append(f"""# 生命论（明本论）· 合订本

> 生成时间：{date_str}
> 作者：北原慢热
> 来源：https://github.com/192781-li/mingbenlun
> 本合订本由S05信息分站自动生成，按卷顺序合并全部正文。
> 已自动过滤研究笔记元注释（原话/展开/语境/状态等），输出干净全本。
> 标题层级统一：卷=H1，篇=H2，章=H3，节=H4。

---

# 目录

""")
    
    # 生成目录
    toc_lines = []
    for vol in VOLUMES:
        vol_dir = BOOK_DIR / vol
        if vol_dir.exists():
            title = vol.split("_", 2)[-1] if "_" in vol else vol
            toc_lines.append(f"- **{title}**")
            for f in collect_md_files(vol_dir):
                name = f.stem
                if name.startswith("00_"):
                    continue  # 卷标题文件不列入目录
                toc_lines.append(f"  - {name}")
    parts.append("\n".join(toc_lines))
    parts.append("\n---\n")
    
    # 卷首文件（降级为H2）
    for fm in FRONT_MATTER:
        fp = BOOK_DIR / fm
        if fp.exists():
            content = fp.read_text(encoding="utf-8")
            content = strip_meta_notes(content)
            content = normalize_headings(content)
            parts.append(content)
            parts.append("\n\n---\n")
            total_chars += len(content)
            total_files += 1
    
    # 各卷
    for vol in VOLUMES:
        vol_dir = BOOK_DIR / vol
        if not vol_dir.exists():
            continue
        print(f"  处理: {vol}")
        
        for f in collect_md_files(vol_dir):
            content = f.read_text(encoding="utf-8")
            content = strip_meta_notes(content)
            # 00_卷标题.md保持H1，其他文件降级
            is_vol_title = f.name.startswith("00_")
            content = normalize_headings(content, is_volume_title=is_vol_title)
            parts.append(content)
            parts.append("\n\n")
            total_chars += len(content)
            total_files += 1
    
    # 尾声
    tail = BOOK_DIR / "00_尾声.md"
    if tail.exists():
        content = tail.read_text(encoding="utf-8")
        content = strip_meta_notes(content)
        content = normalize_headings(content)
        parts.append(content)
        total_chars += len(content)
        total_files += 1
    
    combined = "".join(parts)
    
    # 写Markdown版
    md_path = OUT / "生命论_合订本.md"
    md_path.write_text(combined, encoding="utf-8")
    
    # 写TXT版（去除markdown标记）
    txt = combined
    txt = txt.replace("**", "").replace("##", "").replace("#", "")
    txt_path = OUT / "生命论_合订本.txt"
    txt_path.write_text(txt, encoding="utf-8")
    
    print(f"\n=== 合订本生成完成 ===")
    print(f"合并文件数: {total_files}")
    print(f"总字符数: {total_chars:,}")
    print(f"Markdown版: {md_path} ({md_path.stat().st_size // 1024}KB)")
    print(f"TXT版: {txt_path} ({txt_path.stat().st_size // 1024}KB)")

if __name__ == "__main__":
    build_combined()

#!/usr/bin/env python3
"""
全本合订本生成器
把生命论_模块化/下的markdown按卷合并成英文文件名的单文件，方便AI读取。
"""
import os
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent.parent
BOOK_DIR = REPO_ROOT / "生命论_模块化"
OUTPUT_DIR = REPO_ROOT / "book_combined"

VOL_MAP = {
    "00_卷首_命经": "vol00_mingjing",
    "01_卷一_存在论": "vol01_cunzailun",
    "03_卷三_认识论": "vol02_renshilun",
    "05_卷五_群己论": "vol03_qunjilun",
    "06_卷六_异化论": "vol04_yihualun",
    "07_卷七_解放论": "vol05_jiefanglun",
    "04_卷四_实践论": "vol06_shijianlun",
    "08_卷八_格物论": "vol07_gewulun",
    "09_卷九_人文论": "vol08_renwenlun",
    "10_卷十_传统论": "vol09_chuantonglun",
    "11_卷十一_践演论": "vol10_shuxuejichu",
}

VOL_TITLES = {
    "vol00_mingjing": "卷首·命经",
    "vol01_cunzailun": "卷一·存在论",
    "vol02_renshilun": "卷二·认识论",
    "vol03_qunjilun": "卷三·群己论",
    "vol04_yihualun": "卷四·异化论",
    "vol05_jiefanglun": "卷五·解放论",
    "vol06_shijianlun": "卷六·实践论",
    "vol07_gewulun": "卷七·格物论",
    "vol08_renwenlun": "卷八·人文论",
    "vol09_chuantonglun": "卷九·传统论",
    "vol10_shuxuejichu": "卷十·数学基础",
}

def combine_volume(vol_dir, output_file, vol_title):
    """合并一卷的所有md文件"""
    parts = [f"# {vol_title}\n\n> 合订本，生成于{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n"]
    
    # 先加卷标题
    title_file = vol_dir / "00_卷标题.md"
    if title_file.exists():
        content = title_file.read_text(encoding='utf-8', errors='ignore').strip()
        if content:
            parts.append(content + "\n\n---\n")
    
    # 再加各篇（按文件名排序）
    pian_files = sorted([f for f in vol_dir.glob('篇*.md') if f.is_file()])
    for pf in pian_files:
        content = pf.read_text(encoding='utf-8', errors='ignore').strip()
        if content:
            parts.append(f"\n\n{content}\n\n---\n")
    
    output_file.write_text('\n'.join(parts), encoding='utf-8')
    return len('\n'.join(parts)), len(pian_files)

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    index_lines = [
        "# 生命论（明本论）全本索引\n",
        f"> 生成于{datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        "> 本索引列出全本各卷的合订本文件，AI可直接读取对应文件。\n",
        "> GitHub raw链接格式：https://raw.githubusercontent.com/192781-li/mingbenlun/main/book_combined/<文件名>\n\n",
        "| 卷 | 文件名 | 篇数 | 大小 |\n",
        "|---|---|---|---|\n",
    ]
    
    for vol_name, en_name in VOL_MAP.items():
        vol_dir = BOOK_DIR / vol_name
        if not vol_dir.exists():
            continue
        output_file = OUTPUT_DIR / f"{en_name}.md"
        size, pian_count = combine_volume(vol_dir, output_file, VOL_TITLES[en_name])
        size_kb = f"{size/1024:.1f} KB"
        index_lines.append(f"| {VOL_TITLES[en_name]} | {en_name}.md | {pian_count} | {size_kb} |\n")
        print(f"✓ {VOL_TITLES[en_name]}: {pian_count}篇, {size_kb}")
    
    # 加根目录文件
    root_files = []
    for f in BOOK_DIR.glob('*.md'):
        if f.is_file():
            root_files.append(f)
            content = f.read_text(encoding='utf-8', errors='ignore')
            out = OUTPUT_DIR / f"root_{f.name}"
            out.write_text(content, encoding='utf-8')
    
    if root_files:
        index_lines.append("\n## 根目录文件\n\n")
        index_lines.append("| 文件 | 大小 |\n|---|---|\n")
        for f in root_files:
            size = f.stat().st_size
            index_lines.append(f"| {f.name} | {size/1024:.1f} KB |\n")
    
    index_file = OUTPUT_DIR / "INDEX.md"
    index_file.write_text(''.join(index_lines), encoding='utf-8')
    print(f"\n✓ 索引: {index_file.name}")
    print(f"✓ 共{len(VOL_MAP)}卷合订本")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闪光点原材料提取脚本
扫描生命论_模块化/下的所有.md文件，提取【闪光点#XX·原材料·待作者重写】标记的引用块，
保存到docs/flashpoints/，按卷/篇分类，建索引文件，然后从正文里删除这些引用块。
"""

import os
import re
from pathlib import Path

BASE = Path(r"C:\Users\lison\Desktop\mingbenlun_fresh")
SOURCE_DIR = BASE / "生命论_模块化"
OUTPUT_DIR = BASE / "docs" / "flashpoints"

# 闪光点标记正则
FLASHPOINT_PATTERN = re.compile(r'【闪光点#(\d+)·原材料·待作者重写】')

def extract_flashpoints_from_file(filepath):
    """从一个文件中提取所有闪光点引用块，返回(闪光点列表, 清理后的内容)"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    flashpoints = []
    cleaned_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        # 检查这行是否包含闪光点标记
        match = FLASHPOINT_PATTERN.search(line)
        if match and line.strip().startswith('>'):
            fp_id = match.group(1)
            # 提取整个引用块：从当前行开始，连续的>行
            block_lines = []
            while i < len(lines) and (lines[i].strip().startswith('>') or lines[i].strip() == ''):
                # 如果是空行，检查后面是否还有>行，如果没有就停止
                if lines[i].strip() == '':
                    # 看后面是否还有>行
                    j = i + 1
                    has_more_quote = False
                    while j < len(lines) and lines[j].strip() == '':
                        j += 1
                    if j < len(lines) and lines[j].strip().startswith('>'):
                        # 后面还有引用块，可能是同一个闪光点的继续
                        # 但为了安全，我们只提取连续的>行，空行停止
                        break
                    else:
                        break
                block_lines.append(lines[i])
                i += 1
            
            # 把引用块内容提取出来（去掉>前缀）
            content = ''.join(block_lines)
            # 提取标题（第一行的**内容**）
            title_match = re.search(r'\*\*(.+?)\*\*', content)
            title = title_match.group(1) if title_match else f"闪光点#{fp_id}"
            
            flashpoints.append({
                'id': fp_id,
                'title': title,
                'content': content,
                'source_file': str(filepath.relative_to(BASE)),
                'line_number': len(cleaned_lines) + 1
            })
            # 不把这些行加入cleaned_lines
            # 跳过引用块后面的空行（如果有）
            while i < len(lines) and lines[i].strip() == '':
                i += 1
        else:
            cleaned_lines.append(line)
            i += 1
    
    return flashpoints, ''.join(cleaned_lines)

def main():
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_flashpoints = []
    files_modified = 0
    
    # 遍历所有.md文件
    for md_file in sorted(SOURCE_DIR.rglob('*.md')):
        # 跳过参考资料目录
        if '参考资料' in str(md_file) or '北原慢热实录' in str(md_file):
            continue
        
        flashpoints, cleaned_content = extract_flashpoints_from_file(md_file)
        
        if flashpoints:
            print(f"提取 {len(flashpoints)} 个闪光点: {md_file.relative_to(BASE)}")
            all_flashpoints.extend(flashpoints)
            
            # 写回清理后的文件
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            files_modified += 1
    
    # 按卷/篇分类保存
    # 先按来源文件分组
    from collections import defaultdict
    by_file = defaultdict(list)
    for fp in all_flashpoints:
        by_file[fp['source_file']].append(fp)
    
    # 为每个来源文件创建对应的原材料文件
    for source_file, fps in sorted(by_file.items()):
        # 转换路径：生命论_模块化/卷X_XXX/篇Y_XXX.md -> docs/flashpoints/卷X_XXX/篇Y_XXX.md
        rel_path = Path(source_file)
        # 去掉"生命论_模块化/"前缀
        parts = rel_path.parts
        if parts[0] == '生命论_模块化':
            rel_parts = parts[1:]
        else:
            rel_parts = parts
        
        output_file = OUTPUT_DIR / Path(*rel_parts)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 闪光点原材料：{rel_parts[-1].replace('.md', '')}\n\n")
            f.write(f"> 来源：{source_file}\n\n")
            f.write("---\n\n")
            for fp in sorted(fps, key=lambda x: int(x['id'])):
                f.write(f"## 闪光点#{fp['id']}：{fp['title']}\n\n")
                f.write(f"> 来源位置：第{fp['line_number']}行\n\n")
                f.write(fp['content'])
                f.write("\n---\n\n")
    
    # 建索引文件
    with open(OUTPUT_DIR / 'INDEX.md', 'w', encoding='utf-8') as f:
        f.write("# 闪光点原材料索引\n\n")
        f.write(f"> 共提取 {len(all_flashpoints)} 个闪光点，来自 {files_modified} 个文件\n\n")
        f.write("---\n\n")
        f.write("## 按编号索引\n\n")
        f.write("| 编号 | 标题 | 来源文件 | 原材料文件 |\n")
        f.write("|---|---|---|---|\n")
        for fp in sorted(all_flashpoints, key=lambda x: int(x['id'])):
            # 计算原材料文件路径
            rel_path = Path(fp['source_file'])
            parts = rel_path.parts
            if parts[0] == '生命论_模块化':
                rel_parts = parts[1:]
            else:
                rel_parts = parts
            raw_file = Path(*rel_parts)
            f.write(f"| #{fp['id']} | {fp['title']} | {fp['source_file']} | [{raw_file}]({raw_file.as_posix()}) |\n")
        
        f.write("\n---\n\n")
        f.write("## 按卷/篇索引\n\n")
        for source_file, fps in sorted(by_file.items()):
            rel_path = Path(source_file)
            parts = rel_path.parts
            if parts[0] == '生命论_模块化':
                rel_parts = parts[1:]
            else:
                rel_parts = parts
            raw_file = Path(*rel_parts)
            f.write(f"### {'/'.join(rel_parts)}\n")
            f.write(f"- 原材料文件：[{raw_file}]({raw_file.as_posix()})\n")
            for fp in sorted(fps, key=lambda x: int(x['id'])):
                f.write(f"- 闪光点#{fp['id']}：{fp['title']}\n")
            f.write("\n")
    
    print(f"\n=== 完成 ===")
    print(f"提取闪光点：{len(all_flashpoints)} 个")
    print(f"修改文件：{files_modified} 个")
    print(f"原材料库：{OUTPUT_DIR}")
    print(f"索引文件：{OUTPUT_DIR / 'INDEX.md'}")

if __name__ == '__main__':
    main()

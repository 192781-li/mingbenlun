#!/usr/bin/env python3
"""
统一全本章号：每篇从"第一章"开始重新编号。
跳过明显的子节标题（附：、数字编号、事实/分析/判据等）。
用法：python3 renumber_chapters.py <目录> [--dry-run]
"""
import re
import sys
import os
from pathlib import Path

# 中文数字
CN_NUMS = ['一','二','三','四','五','六','七','八','九','十',
           '十一','十二','十三','十四','十五','十六','十七','十八','十九','二十',
           '二十一','二十二','二十三','二十四','二十五','二十六','二十七','二十八','二十九','三十',
           '三十一','三十二','三十三','三十四','三十五','三十六','三十七','三十八','三十九','四十',
           '四十一','四十二','四十三','四十四','四十五','四十六','四十七','四十八','四十九','五十',
           '五十一','五十二','五十三','五十四','五十五','五十六','五十七','五十八','五十九','六十',
           '六十一','六十二','六十三','六十四','六十五','六十六','六十七','六十八','六十九','七十',
           '七十一','七十二','七十三','七十四','七十五','七十六','七十七','七十八','七十九','八十',
           '八十一','八十二','八十三','八十四','八十五','八十六','八十七','八十八','八十九','九十',
           '九十一','九十二','九十三','九十四','九十五','九十六','九十七','九十八','九十九','一百']

def cn_num(n):
    if n <= 100:
        return CN_NUMS[n-1]
    # 简单处理100以上
    if n < 200:
        return '一百' + CN_NUMS[n-101] if n > 100 else '一百'
    return str(n)

def is_chapter_heading(line):
    """判断是否是章标题（需要编号）"""
    if not line.startswith('### '):
        return False
    title = line[4:].strip()
    # 跳过明显的子节
    skip_patterns = [
        r'^附[：:]',           # 附：xxx
        r'^\d+\.\d+',          # 4.1 xxx
        r'^\d+\s',             # 1 xxx (数字开头)
        r'^事实$',             # 事实
        r'^生命论分析$',       # 生命论分析
        r'^判据$',             # 判据
        r'^类型系统',          # 类型系统（7类类型）
        r'^项（',              # 项（15类项）
        r'^求值规则',          # 求值规则
        r'^生产性',            # 生产性（守护递归）
        r'^Progress定理',      # Progress定理
        r'^Preservation定理',   # Preservation定理
        r'^可靠性的哲学含义',   # 可靠性的哲学含义
        r'^这个对应的含义',      # 这个对应的含义
        r'^量子实例的严格验证',  # 量子实例的严格验证
        r'^余归纳GoI',          # 余归纳GoI
        r'^GoI给生命论的启示',  # GoI给生命论的启示
        r'^未解决的猜想',        # 未解决的猜想
        r'^方向\d+',            # 方向1：xxx
        r'^f[¹²³]：',           # f¹：xxx
        r'^G\^',                # G^ω(C)的构造
        r'^紧闭合的哲学含义',    # 紧闭合的哲学含义
        r'^定理陈述',            # 定理陈述
        r'^证明思路',            # 证明思路
        r'^哲学含义',            # 哲学含义
        r'^\d+个示例',           # 8个示例+10个拒绝测试
        r'^N的三态',             # N的三态
        r'^慢性死亡定理',         # 慢性死亡定理
        r'^三种情形',            # 三种情形
        r'^这就是',              # 这就是"怎么测量..."
        r'^定理20的三层含义',     # 定理20的三层含义
        r'^2\.\d',               # 2.1 线性逻辑
        r'^公理0的特殊性',        # 公理0的特殊性
        r'^第一层', r'^第二层', r'^第三层', r'^第四层', r'^第五层',  # 第一层：xxx
        r'^4\.\d',               # 4.1 元规律
        r'^五步操作法',           # 五步操作法
        r'^一个例子',             # 一个例子
        r'^典型案例库',           # 典型案例库
        r'^学者战斗序列',          # 学者战斗序列
        r'^反生命的本质',          # 反生命的本质
        r'^永不投降的战士',        # 永不投降的战士
        r'^文学中的种子',          # 文学中的种子
        r'^公式作为基层明性的武器', # 公式作为基层明性的武器
        r'^两个世界理论',          # 两个世界理论
        r'^神秘学的定位',          # 神秘学的定位
        r'^尾声',                 # 尾声
        r'^法权是文明的明性',      # 法权是文明的明性
    ]
    for pat in skip_patterns:
        if re.match(pat, title):
            return False
    return True

def extract_old_number(title):
    """提取标题中已有的章号，返回(旧编号, 剩余标题)"""
    # 匹配"第X章"格式
    m = re.match(r'^第([一二三四五六七八九十百零\d]+)章\s*(.*)', title)
    if m:
        return m.group(1), m.group(2)
    return None, title

def process_file(filepath, dry_run=False):
    """处理单个文件，重新编号章标题"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    chapter_count = 0
    changes = []
    
    for i, line in enumerate(lines):
        if is_chapter_heading(line):
            chapter_count += 1
            old_num, title_rest = extract_old_number(line[4:].strip())
            new_heading = f'### 第{cn_num(chapter_count)}章 {title_rest}\n'
            
            if old_num is not None and old_num == cn_num(chapter_count):
                continue  # 编号已经正确
            
            if dry_run:
                changes.append(f'  L{i+1}: {line.strip()} → {new_heading.strip()}')
            else:
                lines[i] = new_heading
                changes.append(f'  L{i+1}: {line.strip()} → {new_heading.strip()}')
    
    if not dry_run and changes:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    return chapter_count, changes

def main():
    if len(sys.argv) < 2:
        print("用法: python3 renumber_chapters.py <目录> [--dry-run]")
        sys.exit(1)
    
    directory = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    if not os.path.isdir(directory):
        print(f"错误: 目录不存在: {directory}")
        sys.exit(1)
    
    total_chapters = 0
    files_processed = 0
    
    # 遍历所有.md文件
    for root, dirs, files in os.walk(directory):
        # 跳过附录和参考资料目录
        if '附录' in root or '参考资料' in root or '练习' in root:
            continue
        for fname in sorted(files):
            if fname.endswith('.md') and not fname.startswith('00_'):
                filepath = os.path.join(root, fname)
                rel_path = os.path.relpath(filepath, directory)
                chapter_count, changes = process_file(filepath, dry_run)
                if chapter_count > 0:
                    files_processed += 1
                    total_chapters += chapter_count
                    print(f'\n[{rel_path}] {chapter_count}章')
                    for c in changes:
                        print(c)
    
    print(f'\n=== 总计 ===')
    print(f'处理文件: {files_processed}')
    print(f'章总数: {total_chapters}')
    if dry_run:
        print('(dry-run模式，未实际修改)')

if __name__ == '__main__':
    main()

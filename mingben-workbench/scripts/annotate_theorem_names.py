#!/usr/bin/env python3
"""自动在核心定理名称引用后加T00X标注（修复版：从后往前替换）"""
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent

# 名称→TID的映射（按长度降序排列，避免短名称先匹配）
NAME_TO_TID = [
    ("自由只能在实践中确立", "T002"),
    ("完美自我遮蔽不动点", "T017"),
    ("明性是异化的右逆", "T006"),
    ("Hilb外部基定理", "T013"),
    ("生命不可资本化", "T001"),
    ("生命不可复制", "T001"),
    ("self_check检测异化", "T010"),
    ("明性反转异化", "T008"),
    ("一般不可克隆", "T009"),
    ("不可克隆定理", "T009"),
    ("异化链定理", "T014"),
    ("持续感染源", "T018"),
    ("永生感染源", "T018"),
    ("异化压缩", "T007"),
    ("明性幂等", "T005"),
    ("steering不等式", "T016"),
    ("明性余单", "T006"),
    ("革命级联", "T011"),
    ("Π₂-完全性", "T003"),
    ("Π₂完全性", "T003"),
    ("量子测量=异化", "T013"),
    ("量子测量＝异化", "T013"),
    ("异化=时钟量化", "T012"),
    ("异化＝时钟量化", "T012"),
]

# 公式模式（不加标注）
FORMULA_CONTEXTS = [
    '!νF', '!(νF)', '!不保持', '!不保', '!不穿透',
    'S_A', '⊬', 'AGENCY', 'Π₂',
]

EXCLUDE_DIRS = {'.git', 'backup', '__pycache__', 'node_modules', '.venv'}
EXCLUDE_FILE_PATTERNS = [
    r'enactics_v\d+\.\d+\.md$',
    r'_report\.md$', r'_report\.json$', r'_scan\.json$',
    r'overclaim', r'audit', r'attack', r'round\d',
    r'old_refs_migration', r'cross_refs', r'name_refs',
    r'theorem_registry\.json',
]

def should_exclude(rel_path):
    name = Path(rel_path).name
    for pattern in EXCLUDE_FILE_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return True
    return False

def is_skippable(content, pos, matched_len):
    """检查是否应该跳过（公式/标题/已有标注）"""
    end = pos + matched_len
    matched = content[pos:end]
    
    # 检查是否在标题行
    line_start = content.rfind('\n', 0, pos) + 1
    line_end = content.find('\n', pos)
    if line_end == -1:
        line_end = len(content)
    line = content[line_start:line_end]
    if line.startswith('#'):
        return True
    
    # 检查是否在行内代码中
    before = content[:pos]
    if before.count('`') % 2 == 1:
        return True
    
    # 检查是否在$...$中
    if before.count('$') % 2 == 1:
        return True
    
    # 检查匹配文本是否在公式上下文中
    for fc in FORMULA_CONTEXTS:
        if fc in matched:
            return True
    
    # 检查前后是否已有T00X标注
    after = content[end:end+30]
    if re.search(r'T0\d{2}', after[:20]):
        return True
    before_short = content[max(0,pos-20):pos]
    if re.search(r'T0\d{2}', before_short):
        return True
    
    # 检查后面是否紧跟括号（已有注释）
    if end < len(content) and content[end] in '（(':
        close = content.find('）' if content[end] == '（' else ')', end)
        if close != -1 and close - end < 50:
            inner = content[end+1:close]
            if re.search(r'T0\d{2}', inner):
                return True
    
    return False

def annotate_file(md_file):
    """在文件中添加T00X标注"""
    rel_path = str(md_file.relative_to(REPO_ROOT))
    if should_exclude(rel_path):
        return 0
    
    try:
        content = md_file.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return 0
    
    # 第一步：收集所有匹配（位置, 长度, tid）
    insertions = []  # (end_pos, tid)
    for name, tid in NAME_TO_TID:
        for m in re.finditer(re.escape(name), content):
            pos = m.start()
            matched_len = len(name)
            if not is_skippable(content, pos, matched_len):
                insertions.append((pos + matched_len, tid))
    
    if not insertions:
        return 0
    
    # 第二步：按位置从后往前排序，去重（同一位置只插一次）
    insertions.sort(key=lambda x: -x[0])
    deduped = []
    prev_pos = -1
    for pos, tid in insertions:
        if pos != prev_pos:
            deduped.append((pos, tid))
            prev_pos = pos
    
    # 第三步：从后往前插入
    count = 0
    for pos, tid in deduped:
        content = content[:pos] + f'（{tid}）' + content[pos:]
        count += 1
    
    if count > 0:
        md_file.write_text(content, encoding='utf-8')
    
    return count

def main():
    print("=== 核心定理名称自动标注T00X（修复版）===")
    print()
    
    total = 0
    changed_files = []
    
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith('.md'):
                md_file = Path(root) / f
                count = annotate_file(md_file)
                if count > 0:
                    rel_path = str(md_file.relative_to(REPO_ROOT))
                    changed_files.append((rel_path, count))
                    total += count
    
    print(f"总计标注: {total}处")
    print(f"修改文件: {len(changed_files)}个")
    print()
    for rel_path, count in sorted(changed_files, key=lambda x: -x[1])[:20]:
        print(f"  {rel_path}: {count}处")

if __name__ == '__main__':
    main()

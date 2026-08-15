#!/usr/bin/env python3
"""
生命论自动合并工具
用法：
  python3 auto_merge.py <新文件.md> [--no-build] [--dry-run]

功能：
  1. 自动解析新文件中的所有章节（### 第X章 标题）
  2. 与现有模块对比：已存在→替换，新章节→插入并自动顺延后续编号
  3. 自动更新受影响的模块文件
  4. 自动更新章节索引
  5. 自动构建HTML（秒级）
  6. 输出变更报告
"""
import re, os, sys, json, subprocess
from pathlib import Path
from copy import deepcopy

BASE = Path(__file__).parent
WORKSPACE = BASE.parent
MODDIR = BASE

# ========== 中文数字转换 ==========
CN_NUM = {'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
          '百':100,'千':1000,'两':2}

def cn2int(s):
    """中文数字转int，支持到九百九十九"""
    if not s: return 0
    if s.isdigit(): return int(s)
    result = 0
    temp = 0
    for ch in s:
        if ch not in CN_NUM: return None
        n = CN_NUM[ch]
        if n >= 10:
            if temp == 0: temp = 1
            result += temp * n
            temp = 0
        else:
            temp = n
    result += temp
    return result

def int2cn(n):
    """int转中文数字，支持到999"""
    if n < 10:
        return '零一二三四五六七八九'[n]
    if n < 20:
        return '十' + ('零一二三四五六七八九'[n-10] if n > 10 else '')
    if n < 100:
        tens, ones = divmod(n, 10)
        return '零一二三四五六七八九'[tens] + '十' + ('零一二三四五六七八九'[ones] if ones else '')
    if n < 1000:
        hundreds, rest = divmod(n, 100)
        tens, ones = divmod(rest, 10)
        s = '零一二三四五六七八九'[hundreds] + '百'
        if tens == 0 and ones == 0: return s
        if tens == 0: return s + '零' + '零一二三四五六七八九'[ones]
        if ones == 0: return s + '零一二三四五六七八九'[tens] + '十'
        return s + '零一二三四五六七八九'[tens] + '十' + '零一二三四五六七八九'[ones]
    return str(n)

# ========== 章节解析 ==========
CHAPTER_RE = re.compile(r'^###\s*(第([一二三四五六七八九十百零两\d]+)章)\s*(.*?)$', re.MULTILINE)
PIAN_RE = re.compile(r'^##\s*(第[一二三四五六七八九十]+篇)\s*(.*?)$', re.MULTILINE)
JUAN_RE = re.compile(r'^#\s*(第[一二三四五六七八九]卷)\s*(.*?)$', re.MULTILINE)

def parse_chapters(text):
    """解析文本中的所有章节，返回 [{num, title, content, start, end}]"""
    chapters = []
    matches = list(CHAPTER_RE.finditer(text))
    for i, m in enumerate(matches):
        num = cn2int(m.group(2))
        title = m.group(3).strip()
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        content = text[start:end].rstrip() + '\n'
        chapters.append({'num': num, 'title': title, 'content': content, 'start': start, 'end': end})
    return chapters

def parse_pian(text):
    """解析篇结构，返回篇标题及其章节范围"""
    pians = []
    matches = list(PIAN_RE.finditer(text))
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        pians.append({'title': m.group(0).strip(), 'start': start, 'end': end, 'text': text[start:end]})
    return pians

# ========== 模块索引 ==========
def load_manifest():
    with open(BASE / 'manifest.txt', 'r', encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip()]

def save_manifest(m):
    with open(BASE / 'manifest.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(m) + '\n')

def read_module(relpath):
    with open(BASE / relpath, 'r', encoding='utf-8') as f:
        return f.read()

def write_module(relpath, content):
    with open(BASE / relpath, 'w', encoding='utf-8') as f:
        f.write(content)

def build_full_text():
    """合并所有模块为完整文本"""
    parts = [read_module('00_总序与导论.md')]
    for rel in load_manifest():
        parts.append(read_module(rel))
    return '\n\n'.join(parts)

def find_module_for_chapter(ch_num):
    """找到包含指定章节号的模块文件"""
    for rel in load_manifest():
        text = read_module(rel)
        chs = parse_chapters(text)
        for ch in chs:
            if ch['num'] == ch_num:
                return rel, chs
    return None, None

def find_pian_module(juan_dir, pian_title_keyword):
    """在指定卷目录下找包含指定篇的模块"""
    manifest = load_manifest()
    for rel in manifest:
        if rel.startswith(juan_dir):
            text = read_module(rel)
            if pian_title_keyword in text:
                return rel
    return None

# ========== 核心合并逻辑 ==========
def merge_new_chapter(new_ch, dry_run=False):
    """
    合并一个新章节。
    - 章节号已存在且标题相同：替换内容（修订）
    - 章节号已存在但标题不同：插入新章节，该位置及后续顺延+1
    - 章节号不存在：插入到正确位置，后续章节顺延+1
    返回变更描述
    """
    num = new_ch['num']
    title = new_ch['title']
    
    # 找这个章节号是否已存在
    existing_rel, existing_chs = find_module_for_chapter(num)
    
    if existing_rel:
        # 检查是替换还是插入：标题相同→替换，标题不同→插入
        old_title = None
        for ch in existing_chs:
            if ch['num'] == num:
                old_title = ch['title']
                break
        
        if old_title == title:
            # 替换已有章节（同标题=修订）
            text = read_module(existing_rel)
            for ch in existing_chs:
                if ch['num'] == num:
                    text = text[:ch['start']] + new_ch['content'].rstrip() + '\n' + text[ch['end']:]
                    break
            if not dry_run:
                write_module(existing_rel, text)
            return f"替换：第{int2cn(num)}章 「{old_title}」（模块：{existing_rel}）"
        # 标题不同→插入新章节，旧章节顺延（继续往下走插入逻辑）
    
    # 新章节：找到该插入哪个模块
    # 找第一个编号 > num 的章节所在模块
    insert_rel = None
    insert_before_ch = None
    for rel in load_manifest():
        text = read_module(rel)
        chs = parse_chapters(text)
        for ch in chs:
            if ch['num'] > num:
                insert_rel = rel
                insert_before_ch = ch
                break
        if insert_rel:
            break
    
    if not insert_rel:
        # 章节号比所有都大，追加到最后一个有章节的模块
        for rel in reversed(load_manifest()):
            text = read_module(rel)
            chs = parse_chapters(text)
            if chs:
                insert_rel = rel
                break
    
    if not insert_rel:
        return f"错误：找不到第{int2cn(num)}章的插入位置"
    
    # 1. 先把所有 >= num 的章节编号+1（降序处理，防止标题碰撞）
    # 先收集所有模块中需要顺延的章节号
    all_ch_nums = set()
    ch_locations = {}  # num -> rel (该章节标题所在模块)
    for rel in load_manifest():
        text = read_module(rel)
        for ch in parse_chapters(text):
            if ch['num'] >= num:
                all_ch_nums.add(ch['num'])
                ch_locations[ch['num']] = rel

    renumbered = []
    # 降序处理：先改大的号，避免"第X章"和"第X+1章"碰撞
    for n in sorted(all_ch_nums, reverse=True):
        old_cn = int2cn(n)
        new_cn = int2cn(n + 1)
        old_header = f"### 第{old_cn}章"
        new_header = f"### 第{new_cn}章"
        # 在所有模块中替换（标题+交叉引用）
        for rel in load_manifest():
            text = read_module(rel)
            modified = False
            # 如果这个模块包含该章节的标题，精确替换标题一次
            if ch_locations.get(n) == rel:
                if old_header in text:
                    text = text.replace(old_header, new_header, 1)
                    modified = True
            # 替换所有交叉引用（标题已改，不会重复替换）
            old_ref = f"第{old_cn}章"
            new_ref = f"第{new_cn}章"
            if old_ref in text:
                text = text.replace(old_ref, new_ref)
                modified = True
            if modified and not dry_run:
                write_module(rel, text)
        renumbered.append(f"第{old_cn}章→第{new_cn}章")

    # 2. 在目标模块中插入新章节（重新读取文件，不用旧坐标）
    text = read_module(insert_rel)
    target_header = f"### 第{int2cn(num + 1)}章"
    idx = text.find(target_header)
    if idx >= 0:
        text = text[:idx] + new_ch['content'].rstrip() + '\n\n' + text[idx:]
        inserted = True
    else:
        # 追加到模块末尾
        text = text.rstrip() + '\n\n' + new_ch['content'].rstrip() + '\n'
    if not dry_run:
        write_module(insert_rel, text)
    
    msg = f"新增：第{int2cn(num)}章「{title}」插入到 {insert_rel}"
    if renumbered:
        msg += f"\n  顺延：{len(renumbered)} 章编号+1"
    return msg

def merge_new_file(filepath, dry_run=False):
    """合并一个新文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        new_text = f.read()
    
    new_chapters = parse_chapters(new_text)
    if not new_chapters:
        return "错误：新文件中未找到任何章节（### 第X章 标题）"
    
    changes = []
    for ch in new_chapters:
        msg = merge_new_chapter(ch, dry_run=dry_run)
        changes.append(msg)
    
    return '\n'.join(changes)

# ========== 校验 ==========
def validate():
    """校验章节编号连续性"""
    full = build_full_text()
    chs = parse_chapters(full)
    nums = sorted([ch['num'] for ch in chs])
    issues = []
    for i, n in enumerate(nums):
        if i > 0 and n != nums[i-1] + 1:
            issues.append(f"编号跳跃：第{int2cn(nums[i-1])}章→第{int2cn(n)}章")
    # 检查重复
    seen = set()
    for n in nums:
        if n in seen:
            issues.append(f"编号重复：第{int2cn(n)}章")
        seen.add(n)
    return issues, len(chs)

# ========== 主入口 ==========
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：python3 auto_merge.py <新文件.md> [--dry-run]")
        print("      python3 auto_merge.py --validate")
        print("      python3 auto_merge.py --index")
        sys.exit(1)
    
    if sys.argv[1] == '--validate':
        issues, total = validate()
        print(f"共 {total} 章")
        if issues:
            print("发现问题：")
            for i in issues: print(f"  ⚠ {i}")
        else:
            print("✓ 章节编号连续，无重复")
        sys.exit(0)
    
    if sys.argv[1] == '--index':
        full = build_full_text()
        chs = parse_chapters(full)
        for ch in sorted(chs, key=lambda x: x['num']):
            print(f"  第{int2cn(ch['num']):>4s}章  {ch['title']}")
        print(f"\n共 {len(chs)} 章")
        sys.exit(0)
    
    dry_run = '--dry-run' in sys.argv
    new_file = sys.argv[1]
    if not os.path.exists(new_file):
        # 尝试在workspace找
        new_file = str(WORKSPACE / new_file)
        if not os.path.exists(new_file):
            print(f"错误：找不到文件 {sys.argv[1]}")
            sys.exit(1)
    
    print(f"=== 自动合并：{os.path.basename(new_file)} ===\n")
    result = merge_new_file(new_file, dry_run=dry_run)
    print(result)
    
    if dry_run:
        print("\n[dry-run] 未实际修改文件")
        sys.exit(0)
    
    # 校验
    print("\n=== 校验 ===")
    issues, total = validate()
    print(f"共 {total} 章")
    if issues:
        for i in issues: print(f"  ⚠ {i}")
    else:
        print("✓ 编号连续无重复")
    
    # 构建HTML
    if '--no-build' not in sys.argv:
        print("\n=== 构建HTML ===")
        r = subprocess.run(['bash', str(BASE / 'build.sh'), '--html-only'],
                         capture_output=True, text=True, cwd=str(WORKSPACE))
        print(r.stdout)
        if r.returncode != 0:
            print("构建错误：", r.stderr)

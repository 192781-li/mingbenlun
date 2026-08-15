#!/usr/bin/env python3
"""明本质量门控：检查章节编号、交叉引用、空章节、格式、重复、术语、概念覆盖、乱码。"""
import re, sys, hashlib
from collections import Counter

def cn2int(s):
    digits = {'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
    units = {'十':10,'百':100,'千':1000}
    if not s: return 0
    result = 0; current = 0
    for c in s:
        if c in digits: current = digits[c]
        elif c in units:
            if current == 0: current = 1
            result += current * units[c]; current = 0
    result += current
    return result

def int2cn(n):
    digits = '零一二三四五六七八九'
    if n < 10: return digits[n]
    if n == 10: return '十'
    if n < 20: return '十' + (digits[n%10] if n%10 else '')
    if n < 100:
        return digits[n//10] + '十' + (digits[n%10] if n%10 else '')
    if n < 1000:
        r = digits[n//100] + '百'; rest = n % 100
        if rest == 0: return r
        if rest < 10: return r + '零' + digits[rest]
        if rest < 20: return r + '一' + int2cn(rest)
        return r + int2cn(rest)
    if n < 10000:
        r = digits[n//1000] + '千'; rest = n % 1000
        if rest == 0: return r
        if rest < 100: return r + '零' + int2cn(rest)
        return r + int2cn(rest)
    return str(n)

def check(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    lines = text.split('\n')
    errors = []; warnings = []

    # 1. 章节编号
    chapters = []
    for i, line in enumerate(lines, 1):
        m = re.match(r'^###?\s*第([零一二三四五六七八九十百千]+)章', line)
        if m:
            num = cn2int(m.group(1))
            chapters.append((num, i, line.strip()))

    for i in range(1, len(chapters)):
        prev_num, prev_line, prev_title = chapters[i-1]
        num, line_no, title = chapters[i]
        if num != prev_num + 1:
            errors.append(f"章节跳跃: {prev_title.split()[0] if prev_title.split() else '第'+int2cn(prev_num)+'章'}→{title.split()[0] if title.split() else '第'+int2cn(num)+'章'} (行{prev_line})")

    # 2. 交叉引用
    chapter_nums = {n for n, _, _ in chapters}
    refs = re.findall(r'第([零一二三四五六七八九十百千]+)章', text)
    for ref in refs:
        ref_num = cn2int(ref)
        if ref_num not in chapter_nums and ref_num <= len(chapters) + 5:
            warnings.append(f"交叉引用可能无效: 第{ref}章")

    # 3. 空章节
    for i, (num, line_no, title) in enumerate(chapters):
        end = chapters[i+1][1]-1 if i+1 < len(chapters) else len(lines)
        body_lines = [l for l in lines[line_no:end] if l.strip()]
        body_text = ''.join(body_lines)
        if len(body_lines) < 1 or len(body_text) < 20:
            warnings.append(f"空章节或过短: {title}")

    # 4. 未闭合的加粗/斜体
    for i, line in enumerate(lines, 1):
        if line.count('**') % 2 != 0:
            warnings.append(f"未闭合加粗 行{i}: {line.strip()[:50]}")

    # 5. 标题层级跳跃
    for i, line in enumerate(lines, 1):
        m = re.match(r'^(#{1,6})\s', line)
        if m and i > 1:
            prev_level = 0
            for j in range(i-2, -1, -1):
                pm = re.match(r'^(#{1,6})\s', lines[j])
                if pm: prev_level = len(pm.group(1)); break
            if prev_level and len(m.group(1)) > prev_level + 1:
                warnings.append(f"标题层级跳跃 行{i}: {line.strip()[:50]}")

    # 6. 重复段落（MD5）
    para_hashes = Counter()
    for para in re.split(r'\n\s*\n', text):
        p = para.strip()
        if len(p) > 50:
            para_hashes[hashlib.md5(p.encode()).hexdigest()] += 1
    for h, count in para_hashes.items():
        if count > 1:
            errors.append(f"重复段落出现{count}次 (MD5:{h[:8]})")

    # 7. 术语一致性
    for i, line in enumerate(lines, 1):
        if '道在日常' in line and '道在日常操作之外' not in line and '道在日常生活' not in line:
            warnings.append(f"术语变体 行{i}: '道在日常' 建议用 '道在日用': {line.strip()[:60]}")

    # 8. 核心概念覆盖（仅对全本检查，单篇模块不要求覆盖所有概念）
    if len(chapters) >= 50:
        core_concepts = ['自指', '操作', '明性', '反自指', '解放', '阶级', '异化', '自由人联合体', '道在日用', '阳主阴从', '四规定性', '负熵',
                         '己化', '感', '应', '践演坐实', '视角涌现', '经文劫持', 'f³', '耗散结构', '自创生']
        missing = [c for c in core_concepts if c not in text]
        if missing:
            warnings.append(f"核心概念缺失: {', '.join(missing)}")

    # 9. 乱码
    garbled = re.findall(r'[\ufffd\u0000-\u0008\u000b\u000c\u000e-\u001f]', text)
    if garbled:
        errors.append(f"乱码字符: {len(garbled)}个")

    # 输出
    print(f"=== 质量门控检查: {path} ===")
    print(f"章节数: {len(chapters)}")
    print(f"字数: {len(text)}")
    print()
    if errors:
        print(f"❌ 错误 ({len(errors)}):")
        for e in errors[:20]: print(f"  - {e}")
    if warnings:
        print(f"⚠️  警告 ({len(warnings)}):")
        for w in warnings[:20]: print(f"  - {w}")
    if not errors and not warnings:
        print("✅ 全部通过")
    return len(errors) == 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: quality_gate.py <markdown文件>"); sys.exit(1)
    ok = check(sys.argv[1])
    sys.exit(0 if ok else 1)

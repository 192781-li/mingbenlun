#!/usr/bin/env python3
"""
生命论质量检查工具
用法：python3 quality_check.py [--fix]

检查项：
  1. 章节编号连续性
  2. 交叉引用有效性（"第X章"指向的章节是否存在）
  3. 空章节（只有标题没有正文）
  4. 术语一致性
  5. 特殊字符/乱码
  6. 篇-章归属合理性
"""
import re, sys
from auto_merge import (cn2int, int2cn, parse_chapters, build_full_text,
                        CHAPTER_RE, MODDIR)

def check_chapter_numbering(chapters):
    """检查章节编号连续性"""
    issues = []
    nums = sorted([ch['num'] for ch in chapters])
    seen = set()
    for n in nums:
        if n in seen:
            issues.append(('错误', f'章节编号重复：第{int2cn(n)}章'))
        seen.add(n)
    for i in range(1, len(nums)):
        if nums[i] != nums[i-1] + 1:
            issues.append(('错误', f'编号跳跃：第{int2cn(nums[i-1])}章→第{int2cn(nums[i])}章'))
    return issues

def check_cross_references(text, chapters):
    """检查交叉引用"""
    issues = []
    valid_nums = {ch['num'] for ch in chapters}
    # 找所有"第X章"引用（不在标题行中的）
    for m in re.finditer(r'第([一二三四五六七八九十百零两]+)章', text):
        ref_num = cn2int(m.group(1))
        if ref_num is None:
            continue
        # 检查是否是标题行
        line_start = text.rfind('\n', 0, m.start()) + 1
        line = text[line_start:text.find('\n', m.end())]
        if line.strip().startswith('###'):
            continue  # 这是章节标题本身，不是引用
        if ref_num not in valid_nums:
            # 找上下文
            ctx_start = max(0, m.start() - 20)
            ctx_end = min(len(text), m.end() + 20)
            ctx = text[ctx_start:ctx_end].replace('\n', ' ')
            issues.append(('警告', f'引用不存在的章节：第{int2cn(ref_num)}章（上下文：...{ctx}...）'))
    return issues

def check_empty_chapters(chapters):
    """检查空章节"""
    issues = []
    for ch in chapters:
        # 去掉标题行，看正文是否足够
        content = ch['content']
        body = re.sub(r'^###\s*第[一二三四五六七八九十百零两]+章\s*[^\n]*\n', '', content).strip()
        if len(body) < 50:
            issues.append(('警告', f'章节内容过短（{len(body)}字）：第{int2cn(ch["num"])}章「{ch["title"]}」'))
    return issues

def check_terms(text):
    """术语一致性检查"""
    issues = []
    # 应该统一的术语
    term_pairs = [
        (r'明性论', '明性论'),  # 正确
        (r'明本论', '明本论'),
        (r'操作权', '操作权'),
        (r'反自指', '反自指'),
        (r'自指操作', '自指操作'),
    ]
    # 检查常见不一致
    inconsistencies = [
        (r'S\s*=\s*f\s*\(\s*S\s*\)', 'S=f(S)'),
        (r'阳主阴丛', '阳主阴从'),  # 常见错字
        (r'阴主阳丛', '阴主阳从'),
        (r'存在既操作', '存在即操作'),
        (r'明本训', '明本训'),
    ]
    for pattern, correct in inconsistencies:
        matches = re.findall(pattern, text)
        if matches and pattern != correct:
            issues.append(('警告', f'可能的术语不一致：发现"{matches[0]}"，建议统一为"{correct}"'))
    return issues

def check_special_chars(text):
    """检查乱码和特殊字符"""
    issues = []
    # 检查常见乱码字符
    bad_chars = ['\ufffd', '\u0000']
    for bc in bad_chars:
        if bc in text:
            count = text.count(bc)
            issues.append(('错误', f'发现乱码字符 {repr(bc)}，共{count}处'))
    # 检查混合编码
    if '\r\n' in text:
        issues.append(('警告', '文件使用Windows换行符(\\r\\n)，建议统一为\\n'))
    return issues

def check_pian_chapter_structure():
    """检查篇-章结构"""
    issues = []
    from auto_merge import load_manifest, read_module, PIAN_RE
    manifest = load_manifest()
    for rel in manifest:
        text = read_module(rel)
        pians = list(PIAN_RE.finditer(text))
        chapters = list(CHAPTER_RE.finditer(text))
        if pians and chapters:
            # 每篇应该至少有一章
            for i, pm in enumerate(pians):
                pian_end = pians[i+1].start() if i+1 < len(pians) else len(text)
                pian_chs = [cm for cm in chapters if pm.start() <= cm.start() < pian_end]
                if not pian_chs:
                    issues.append(('警告', f'{rel} 中「{pm.group(0).strip()}」没有章节'))
    return issues

def main():
    print('=== 生命论质量检查 ===\n')

    full_text = build_full_text()
    chapters = parse_chapters(full_text)

    all_issues = []
    all_issues.extend(check_chapter_numbering(chapters))
    all_issues.extend(check_cross_references(full_text, chapters))
    all_issues.extend(check_empty_chapters(chapters))
    all_issues.extend(check_terms(full_text))
    all_issues.extend(check_special_chars(full_text))
    all_issues.extend(check_pian_chapter_structure())

    errors = [i for i in all_issues if i[0] == '错误']
    warnings = [i for i in all_issues if i[0] == '警告']

    print(f'总章节数：{len(chapters)}')
    print(f'总字数：{len(full_text)}')
    print()

    if errors:
        print(f'❌ 错误（{len(errors)}）：')
        for level, msg in errors:
            print(f'  ✗ {msg}')
        print()

    if warnings:
        print(f'⚠️  警告（{len(warnings)}）：')
        for level, msg in warnings[:20]:
            print(f'  ! {msg}')
        if len(warnings) > 20:
            print(f'  ... 还有{len(warnings)-20}条警告')
        print()

    if not all_issues:
        print('✅ 所有检查通过')

    return len(errors)

if __name__ == '__main__':
    sys.exit(main())

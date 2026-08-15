#!/usr/bin/env python3
"""深度质量检查：交叉引用、术语、重复、格式、概念链"""
import re, sys, hashlib
from collections import Counter, defaultdict
from auto_merge import build_full_text, parse_chapters, cn2int, int2cn, CHAPTER_RE

text = build_full_text()
chapters = parse_chapters(text)
issues = []

# ========== 1. 交叉引用详细检查 ==========
print("=" * 60)
print("1. 交叉引用检查")
print("=" * 60)
valid_nums = {ch['num'] for ch in chapters}
ref_pattern = re.compile(r'第([一二三四五六七八九十百零两]+)章')
ref_count = 0
bad_refs = []
for m in ref_pattern.finditer(text):
    line_start = text.rfind('\n', 0, m.start()) + 1
    line_end = text.find('\n', m.end())
    line = text[line_start:line_end if line_end > 0 else len(text)]
    if line.strip().startswith('###'):
        continue
    ref_num = cn2int(m.group(1))
    if ref_num is None:
        continue
    ref_count += 1
    if ref_num not in valid_nums:
        ctx = text[max(0,m.start()-30):min(len(text),m.end()+30)].replace('\n',' ')
        bad_refs.append((ref_num, ctx))

print(f"  共发现 {ref_count} 处章节引用")
if bad_refs:
    for num, ctx in bad_refs:
        print(f"  ✗ 引用不存在的第{int2cn(num)}章: ...{ctx}...")
        issues.append(f"无效引用：第{int2cn(num)}章")
else:
    print("  ✓ 所有引用均有效")

# ========== 2. 核心术语一致性 ==========
print("\n" + "=" * 60)
print("2. 核心术语一致性")
print("=" * 60)
terms = {
    'S=f(S)': [r'S\s*=\s*f\s*\(\s*S\s*\)', r'S＝f（S）'],
    '操作权': [r'操作权'],
    '反自指': [r'反自指'],
    '自指操作': [r'自指操作'],
    '明性': [r'明性'],
    '阳主阴从': [r'阳主阴从', r'阳主阴丛'],
    '阴主阳从': [r'阴主阳从', r'阴主阳丛'],
    '存在即操作': [r'存在即操作', r'存在既操作'],
    '解放三阶': [r'解放三阶'],
    '四规定性': [r'四规定性'],
    '六阶段': [r'六阶段'],
    '自由人联合体': [r'自由人联合体'],
    '人人如龙': [r'人人如龙'],
    '道在日用': [r'道在日用', r'道在日常(?!操作)'],
    '明本训': [r'明本训'],
    '结构性痛苦综合征': [r'结构性痛苦综合征'],
    '胶球': [r'胶球'],
    '本自足': [r'本自足'],
}
for term, patterns in terms.items():
    total = 0
    variants = Counter()
    for p in patterns:
        matches = re.findall(p, text)
        total += len(matches)
        if matches:
            variants[p] = len(matches)
    status = "✓" if len(variants) <= 1 else "⚠"
    print(f"  {status} {term}: {total}处", end="")
    if len(variants) > 1:
        print(f" 变体: {dict(variants)}")
        issues.append(f"术语变体：{term}")
    else:
        print()

# ========== 3. 重复段落检查 ==========
print("\n" + "=" * 60)
print("3. 重复段落检查")
print("=" * 60)
paras = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 80]
para_hashes = defaultdict(list)
for i, p in enumerate(paras):
    h = hashlib.md5(p.encode()).hexdigest()
    para_hashes[h].append(i)
dupes = {h: idxs for h, idxs in para_hashes.items() if len(idxs) > 1}
if dupes:
    for h, idxs in dupes.items():
        sample = paras[idxs[0]][:80]
        print(f"  ⚠ 重复段落（{len(idxs)}次）: {sample}...")
        issues.append(f"重复段落：{sample[:40]}...")
else:
    print("  ✓ 无完全重复段落")

# 高相似句子检查
sentences = re.split(r'[。！？\n]', text)
sentences = [s.strip() for s in sentences if len(s.strip()) > 40]
sent_starts = Counter()
for s in sentences:
    key = s[:30]
    sent_starts[key] += 1
common = [(k, v) for k, v in sent_starts.items() if v > 3]
if common:
    print(f"  ⚠ 高重复句首（>3次）:")
    for k, v in sorted(common, key=lambda x: -x[1])[:10]:
        print(f"    {v}次: {k}...")
else:
    print("  ✓ 无高重复句首")

# ========== 4. 格式问题 ==========
print("\n" + "=" * 60)
print("4. 格式问题")
print("=" * 60)
# 连续空行
multi_blank = len(re.findall(r'\n{4,}', text))
print(f"  {'⚠' if multi_blank else '✓'} 连续3行以上空行: {multi_blank}处")
if multi_blank: issues.append(f"连续空行{multi_blank}处")

# 行首空格
leading_space = len(re.findall(r'\n +\S', text))
print(f"  {'⚠' if leading_space else '✓'} 行首多余空格: {leading_space}处")

# 中英文之间缺空格（这个不强制，中文排版不需要）
# 检查未闭合的加粗
unclosed_bold = 0
for line in text.split('\n'):
    stars = line.count('**')
    if stars % 2 != 0:
        unclosed_bold += 1
print(f"  {'⚠' if unclosed_bold else '✓'} 未闭合加粗标记: {unclosed_bold}行")
if unclosed_bold: issues.append(f"未闭合加粗{unclosed_bold}处")

# 检查标题层级跳跃
headers = [(len(m.group(1)), m.group(2).strip()) for m in re.finditer(r'^(#{1,4})\s+(.+)$', text, re.MULTILINE)]
level_issues = 0
prev_level = 0
for level, title in headers:
    if prev_level > 0 and level > prev_level + 1 and level <= 3:
        level_issues += 1
    prev_level = level
print(f"  {'⚠' if level_issues else '✓'} 标题层级跳跃: {level_issues}处")

# ========== 5. 章节内容质量 ==========
print("\n" + "=" * 60)
print("5. 章节内容质量")
print("=" * 60)
short_chs = []
for ch in chapters:
    body = re.sub(r'^###\s*第[一二三四五六七八九十百零两]+章\s*[^\n]*\n', '', ch['content']).strip()
    if len(body) < 100:
        short_chs.append((ch['num'], ch['title'], len(body)))
if short_chs:
    for num, title, length in short_chs:
        print(f"  ⚠ 第{int2cn(num)}章「{title}」仅{length}字")
        issues.append(f"短章节：第{int2cn(num)}章")
else:
    print("  ✓ 所有章节内容充实（>100字）")

# 章节标题重复
titles = [ch['title'] for ch in chapters]
title_dupes = [(t, c) for t, c in Counter(titles).items() if c > 1]
if title_dupes:
    for t, c in title_dupes:
        print(f"  ⚠ 标题重复：「{t}」出现{c}次")
        issues.append(f"重复标题：{t}")
else:
    print("  ✓ 章节标题无重复")

# ========== 6. 核心概念链完整性 ==========
print("\n" + "=" * 60)
print("6. 核心概念链覆盖")
print("=" * 60)
concept_chain = [
    '你在活着', '操作', '自指', 'S=f(S)', '阴阳', '阳主阴从',
    '四规定性', '边界生成性', '内生目的', '操作再生性', '环境互动性',
    '明性', '反自指', '窃权', '惯性锁死', '名实遮蔽', '生命耗散',
    '负反馈锁死', '系统崩溃', '解放三阶', '解蔽', '收权', '立序',
    '自由人联合体', '人人如龙', '道在日用',
    '广义熵增', '广义负熵',
    '胶球', '本自足',
]
missing = []
for concept in concept_chain:
    count = text.count(concept)
    if count == 0:
        missing.append(concept)
        print(f"  ✗ 缺失：{concept}")
        issues.append(f"概念缺失：{concept}")
if not missing:
    print(f"  ✓ 全部{len(concept_chain)}个核心概念均有覆盖")

# ========== 7. 哲学家/思想家引用 ==========
print("\n" + "=" * 60)
print("7. 重要思想家引用统计")
print("=" * 60)
thinkers = ['马克思', '恩格斯', '列宁', '黑格尔', '康德', '海德格尔', '尼采',
            '福柯', '德里达', '阿尔都塞', '巴迪欧', '斯宾诺莎', '笛卡尔',
            '休谟', '洛克', '卢梭', '韦伯', '涂尔干', '费尔巴哈',
            '叔本华', '萨特', '加缪', '弗洛伊德', '拉康',
            '孔子', '孟子', '老子', '庄子', '王阳明', '王船山',
            '释迦', '慧能', '罗尔斯', '诺齐克', '哈耶克', '米塞斯',
            '波普尔', '库恩', '费耶阿本德', '波兰尼',
            '毛泽东', '邓小平',
            '奈格里', '哈特', '哈贝马斯', '卢卡奇', '葛兰西']
for t in thinkers:
    c = text.count(t)
    if c > 0:
        print(f"  {t}: {c}次")

# ========== 8. 数字/数据检查 ==========
print("\n" + "=" * 60)
print("8. 关键数据一致性")
print("=" * 60)
# 38亿年
v1 = len(re.findall(r'38\s*亿', text))
print(f"  生命起源'38亿年': {v1}处")
# 2026年
v2 = len(re.findall(r'2026\s*年', text))
print(f"  '2026年': {v2}处")
# 六阶段
v3 = len(re.findall(r'六阶段|六个阶段', text))
print(f"  '六阶段/六个阶段': {v3}处")
# 三阶
v4 = len(re.findall(r'解放三阶|三阶路径', text))
print(f"  '解放三阶': {v4}处")

# ========== 总结 ==========
print("\n" + "=" * 60)
print("总结")
print("=" * 60)
print(f"总章节：{len(chapters)}")
print(f"总字数：{len(text)}")
print(f"发现问题：{len(issues)}")
if issues:
    print("\n问题清单：")
    for i, iss in enumerate(issues, 1):
        print(f"  {i}. {iss}")
else:
    print("\n✅ 全部检查通过")

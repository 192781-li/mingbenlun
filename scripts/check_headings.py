#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_headings.py —— 生命论标题层级硬检查

保质核心：确保卷篇章标题层级绝对正确，不再出现混乱。

检查项：
1. H1（# ）只能出现在 00_卷标题.md / 00_附录标题.md / 封面 中
2. 每个篇文件有且仅有一个 H2（## ）
3. H2 必须与文件名篇号匹配（第一篇/篇零/附录一等）
4. H3（### ）编号必须是 X.Y 格式，或为无编号特殊章（引言/小结/余论等）
5. 每篇 H3 从 1.1 开始编号（子篇独立编号）
6. 无控制字符、无"待入全本"占位

用法：
  python3 scripts/check_headings.py          # 检查全部，输出报告
  python3 scripts/check_headings.py --fix    # 自动修复可修复的问题（H2标题）
  python3 scripts/check_headings.py --quiet  # 只输出错误，不输出详情

退出码：0=全部通过，1=有错误
"""
import argparse, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK_DIR = os.path.join(REPO, "生命论_模块化")

# 允许的无编号H3标题
UNNUMBERED_H3 = {"引言", "导言", "序", "小结", "总结", "余论", "结语", "跋", "附录", "参考文献"}

# H2篇号模式（从文件名提取）
VOL_TITLE_FILES = {"00_卷标题.md", "00_附录标题.md"}
# 特殊文件：命经（文言文体裁，H1+H2段落结构），不检查标题层级
SPECIAL_FILES = {"01_命经.md"}


def extract_pian_from_filename(filename):
    """从文件名提取篇号，返回 (篇号类型, 篇号文字)
    例：01_篇一_xxx.md -> ('normal', '第一篇')
        01a_篇一之二_xxx.md -> ('sub', '第一篇之二')
        00_篇零_xxx.md -> ('zero', '篇零')
        00a_篇零之二_xxx.md -> ('zero_sub', '篇零之二')
        01_附录一_xxx.md -> ('appendix', '附录一')
        01_命经.md -> ('mingjing', '命经')
    """
    base = os.path.basename(filename)
    # 去掉数字前缀
    m = re.match(r'^\d+[a-z]?_(.+)$', base)
    if not m:
        return None, None
    name_part = m.group(1)
    # 去掉.md
    name_part = re.sub(r'\.md$', '', name_part)
    # 取第一个_之前的部分作为篇名标识
    pian_name = name_part.split('_')[0]

    if pian_name.startswith('篇零之二'):
        return 'zero_sub', '篇零之二'
    if pian_name.startswith('篇零'):
        return 'zero', '篇零'
    if pian_name.startswith('附录'):
        return 'appendix', pian_name
    if pian_name == '命经':
        return 'mingjing', '命经'
    # 篇一、篇二... 篇一之二、篇二之三...
    m2 = re.match(r'篇([一二三四五六七八九十]+)(之[二三四五六七八九十]+)?', pian_name)
    if m2:
        if m2.group(2):
            return 'sub', f'第{m2.group(1)}篇{m2.group(2)}'
        return 'normal', f'第{m2.group(1)}篇'
    return None, None


def check_file(filepath, errors, warnings):
    """检查单个文件的标题层级。"""
    rel = os.path.relpath(filepath, REPO)
    basename = os.path.basename(filepath)

    # 特殊文件（命经等文言文体裁）跳过所有标题检查
    if basename in SPECIAL_FILES:
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        errors.append(f"{rel}: 无法读取文件: {e}")
        return

    lines = content.split('\n')
    h1_count = 0
    h2_count = 0
    h2_text = ""
    h3_list = []

    for i, line in enumerate(lines, 1):
        # 控制字符检查
        if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', line):
            errors.append(f"{rel}:{i}: 含控制字符")

        # H1
        if re.match(r'^# ', line):
            h1_count += 1
            if basename not in VOL_TITLE_FILES and '封面' not in basename:
                errors.append(f"{rel}:{i}: 篇文件中出现H1（# ），应为H2（## ）。内容: {line[:50]}")

        # H2
        if re.match(r'^## ', line):
            h2_count += 1
            h2_text = line[3:].strip()

        # H3
        if re.match(r'^### ', line):
            h3_text = line[4:].strip()
            h3_list.append((i, h3_text))

    # 待入全本检查
    if '待入全本' in content:
        count = content.count('待入全本')
        warnings.append(f"{rel}: 含 {count} 处'待入全本'占位标记")

    # 卷标题文件跳过H2检查
    if basename in VOL_TITLE_FILES:
        if h1_count != 1:
            errors.append(f"{rel}: 卷标题文件应有1个H1，实际{h1_count}个")
        return

    pian_type, pian_num = extract_pian_from_filename(filepath)

    # H2数量检查
    if h2_count == 0:
        errors.append(f"{rel}: 缺少H2（## ）篇标题")
    elif h2_count > 1:
        errors.append(f"{rel}: 有 {h2_count} 个H2，应有且仅有1个")

    # H2篇号匹配检查
    if h2_count == 1 and pian_num and pian_num != '命经':
        if not h2_text.startswith(pian_num):
            errors.append(f"{rel}: H2标题'{h2_text[:40]}' 与文件名篇号'{pian_num}'不匹配")

    # H3编号检查
    if h3_list:
        numbered = []
        for lineno, text in h3_list:
            # 检查是否是X.Y格式
            m = re.match(r'^(\d+)\.(\d+)\s', text)
            if m:
                numbered.append((lineno, int(m.group(1)), int(m.group(2)), text))
            elif text.split()[0] if text.split() else "" in UNNUMBERED_H3:
                pass  # 无编号特殊章，允许
            else:
                # 检查是否是"第X章"旧格式
                if re.match(r'^第[一二三四五六七八九十]+章', text):
                    errors.append(f"{rel}:{lineno}: H3使用旧格式'第X章'，应改为X.Y数字编号。内容: {text[:40]}")
                elif not text.startswith(('引言', '导言', '小结', '总结', '余论', '结语')):
                    warnings.append(f"{rel}:{lineno}: H3无编号且非特殊章，建议补X.Y编号。内容: {text[:40]}")

        # 检查编号从1.1开始
        if numbered:
            first = numbered[0]
            if first[1] != 1 or first[2] != 1:
                # 允许前面有无编号的引言
                has_intro_before = any(
                    h3_list[j][1].split()[0] in UNNUMBERED_H3
                    for j in range(h3_list.index((first[0], first[3])) if (first[0], first[3]) in h3_list else 0)
                )
                if not has_intro_before and first[1] != 1:
                    errors.append(f"{rel}:{first[0]}: H3编号从{first[1]}.{first[2]}开始，应从1.1开始（子篇独立编号）")


def main():
    ap = argparse.ArgumentParser(description='生命论标题层级硬检查')
    ap.add_argument('--fix', action='store_true', help='自动修复可修复的问题')
    ap.add_argument('--quiet', action='store_true', help='只输出错误')
    args = ap.parse_args()

    errors = []
    warnings = []
    file_count = 0

    for root, dirs, files in os.walk(BOOK_DIR):
        # 只检查卷目录（NN_卷X_xxx）和卷首目录下的篇文件
        rel_dir = os.path.relpath(root, BOOK_DIR)
        # 跳过根目录下的辅助文件（体系总纲、全书导言、AGENTS.md等）
        if rel_dir == '.':
            continue
        # 跳过项目文档目录
        if '项目文档' in root:
            continue
        for f in files:
            if f.endswith('.md'):
                filepath = os.path.join(root, f)
                file_count += 1
                check_file(filepath, errors, warnings)

    print(f"检查了 {file_count} 个文件")
    print(f"错误: {len(errors)} 个")
    print(f"警告: {len(warnings)} 个")
    print()

    if errors:
        print("=== 错误（必须修复）===")
        for e in errors:
            print(f"  ❌ {e}")
        print()

    if warnings and not args.quiet:
        print("=== 警告（建议修复）===")
        for w in warnings:
            print(f"  ⚠️  {w}")
        print()

    if errors:
        print(f"❌ 标题检查未通过：{len(errors)} 个错误")
        sys.exit(1)
    else:
        print(f"✅ 标题检查通过：{file_count} 个文件全部合规")
        if warnings:
            print(f"   （有 {len(warnings)} 个警告，建议后续处理）")
        sys.exit(0)


if __name__ == '__main__':
    main()

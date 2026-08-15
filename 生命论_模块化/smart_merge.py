#!/usr/bin/env python3
"""
生命论智能合并管道
用法：
  python3 smart_merge.py <新文件> [选项]

自动识别新内容类型并处理：
  - 含 ### 第X章 → 按章合并（新增/替换/自动顺延编号）
  - 含 ## 第X篇 → 按篇合并
  - 含 # 第X卷 → 按卷合并
  - 无标题编号 → 按关键词匹配最近章节追加

选项：
  --dry-run     只预览不修改
  --no-build    不自动构建
  --format      只做格式规范化（标题层级、加粗、引用块）
  --report      输出变更报告
"""
import re, os, sys, subprocess
from pathlib import Path
from auto_merge import (cn2int, int2cn, parse_chapters, parse_pian,
                        load_manifest, save_manifest, read_module, write_module,
                        build_full_text, validate, merge_new_chapter,
                        CHAPTER_RE, PIAN_RE, JUAN_RE, MODDIR, WORKSPACE)

def normalize_format(text):
    """格式规范化：统一标题层级、加粗关键句、引用块"""
    lines = text.split('\n')
    out = []
    for line in lines:
        # 统一章节标题格式
        m = re.match(r'^#{1,4}\s*(第[一二三四五六七八九十百零两\d]+[章节])\s*(.*)', line)
        if m:
            level = 3 if '章' in m.group(1) else (2 if '篇' in m.group(1) else 1)
            line = '#' * level + ' ' + m.group(1) + ' ' + m.group(2)
        out.append(line)
    return '\n'.join(out)

def detect_type(text):
    """识别新内容类型"""
    has_juan = bool(JUAN_RE.search(text))
    has_pian = bool(PIAN_RE.search(text))
    has_chapter = bool(CHAPTER_RE.search(text))
    if has_juan: return '卷'
    if has_pian: return '篇'
    if has_chapter: return '章'
    return '片段'

def merge_pian(new_text, dry_run=False):
    """合并一篇内容"""
    pm = PIAN_RE.search(new_text)
    if not pm:
        return "错误：未识别到篇标题"
    pian_title = pm.group(0).strip()
    pian_name = pm.group(2).strip()

    # 找是否已有此篇
    for rel in load_manifest():
        text = read_module(rel)
        if pian_name in text and PIAN_RE.search(text):
            # 替换整篇
            old_pians = parse_pian(text)
            for op in old_pians:
                if pian_name in op['title']:
                    text = text[:op['start']] + new_text.strip() + '\n' + text[op['end']:]
                    if not dry_run:
                        write_module(rel, text)
                    return f"替换篇：{pian_title}（模块：{rel}）"

    # 新篇：根据篇中的章节号确定属于哪一卷
    chapters = parse_chapters(new_text)
    if chapters:
        first_num = chapters[0]['num']
        # 找该章节号应属于的卷
        for rel in load_manifest():
            text = read_module(rel)
            chs = parse_chapters(text)
            if chs and any(ch['num'] >= first_num for ch in chs):
                juan_dir = rel.split('/')[0]
                # 在该卷最后一篇后追加
                safe_name = re.sub(r'[\\/:*?"<>|]', '_', pian_name)[:30]
                new_file = f"{juan_dir}/篇_{safe_name}.md"
                if not dry_run:
                    write_module(new_file, new_text.strip() + '\n')
                    manifest = load_manifest()
                    # 插入到该卷最后一个文件后
                    insert_idx = 0
                    for i, r in enumerate(manifest):
                        if r.startswith(juan_dir):
                            insert_idx = i + 1
                    manifest.insert(insert_idx, new_file)
                    save_manifest(manifest)
                return f"新增篇：{pian_title} → {new_file}"
    return f"新增篇：{pian_title}（未能自动确定卷归属，请手动放置）"

def merge_juan(new_text, dry_run=False):
    """合并一卷内容"""
    jm = JUAN_RE.search(new_text)
    juan_title = jm.group(0).strip()
    juan_name = jm.group(2).strip()
    juan_num = jm.group(1)

    # 找是否已有此卷
    for rel in load_manifest():
        text = read_module(rel)
        if juan_name in text and JUAN_RE.search(text):
            # 替换整卷所有模块
            juan_dir = rel.split('/')[0]
            # 删除旧模块
            manifest = load_manifest()
            old_files = [r for r in manifest if r.startswith(juan_dir)]
            if not dry_run:
                for of in old_files:
                    os.remove(MODDIR / of)
                manifest = [r for r in manifest if not r.startswith(juan_dir)]
                # 写入新模块
                pians = parse_pian(new_text)
                new_files = []
                # 卷标题
                first_pian_start = pians[0]['start'] if pians else len(new_text)
                write_module(f"{juan_dir}/00_卷标题.md", new_text[:first_pian_start].strip() + '\n')
                new_files.append(f"{juan_dir}/00_卷标题.md")
                for p in pians:
                    pname = re.search(r'第[一二三四五六七八九十]+篇\s*(.*)', p['title'])
                    safe = re.sub(r'[\\/:*?"<>|]', '_', pname.group(1) if pname else '未命名')[:30]
                    pf = f"{juan_dir}/篇_{safe}.md"
                    write_module(pf, p['text'].strip() + '\n')
                    new_files.append(pf)
                # 更新manifest
                insert_idx = 0
                for i, r in enumerate(manifest):
                    if r.startswith(juan_dir):
                        insert_idx = i
                        break
                for nf in reversed(new_files):
                    manifest.insert(insert_idx, nf)
                save_manifest(manifest)
            return f"替换卷：{juan_title}（{len(old_files)}个旧模块→新模块）"
    return f"新卷：{juan_title}（需手动创建卷目录）"

def smart_merge(filepath, dry_run=False, do_format=False, do_build=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    if do_format:
        text = normalize_format(text)
        if not dry_run:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
        print("格式规范化完成")

    content_type = detect_type(text)
    print(f"内容类型：{content_type}")
    print()

    changes = []
    if content_type == '章':
        for ch in parse_chapters(text):
            changes.append(merge_new_chapter(ch, dry_run=dry_run))
    elif content_type == '篇':
        changes.append(merge_pian(text, dry_run=dry_run))
    elif content_type == '卷':
        changes.append(merge_juan(text, dry_run=dry_run))
    else:
        return "错误：无法识别内容类型，请确保包含标准的卷/篇/章标题"

    for c in changes:
        print(c)

    if dry_run:
        print("\n[dry-run] 未实际修改")
        return

    # 校验
    print("\n=== 校验 ===")
    issues, total = validate()
    print(f"共 {total} 章")
    if issues:
        for i in issues: print(f"  ⚠ {i}")
    else:
        print("✓ 编号连续无重复")

    # 构建
    if do_build:
        print("\n=== 构建HTML ===")
        r = subprocess.run(['bash', str(MODDIR / 'build.sh'), '--html-only'],
                         capture_output=True, text=True, cwd=str(WORKSPACE))
        print(r.stdout)
        if r.returncode != 0:
            print("构建错误：", r.stderr)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    args = sys.argv[2:]
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        filepath = str(WORKSPACE / filepath)
        if not os.path.exists(filepath):
            print(f"错误：找不到文件 {sys.argv[1]}")
            sys.exit(1)
    smart_merge(filepath,
                dry_run='--dry-run' in args,
                do_format='--format' in args,
                do_build='--no-build' not in args)

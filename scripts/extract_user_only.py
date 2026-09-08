#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
严格提取：只保留"用户"说的话，整块丢弃"智能体"（含其思考过程与回复）。
这是金句工程最关键的修正——金句只收北原慢热本人的原话。
输入：批量导出的对话md（**用户(时间)：** / **智能体(时间)：** 交替）
输出：金句提取_纯用户原话.json
"""
import os
import re
import json
import glob
from collections import Counter

ROOT = '.'
OUT_JSON = 'docs/raw_materials/金句提取_纯用户原话.json'

# 角色块开头：**用户(2026/06/12 03:13:03)：**
ROLE_RE = re.compile(r'^\*\*(用户|智能体|我|豆包|assistant|user|human)[^()：:]*(\([^)]*\))?\s*[：:]\*\*\s*$')
USER_NAMES = {'用户', '我', 'user', 'human'}

# 对话文件目录
CONV_DIRS = [
    'docs/raw_materials/硬核对话记录/批量导出_20260829',
    'docs/raw_materials/硬核对话记录/批量导出_20260830',
    'docs/raw_materials/硬核对话记录',
]

# 明确排除的非对话/AI文档
EXCLUDE = ['检索结果', '综合保存', '清点与身份', '时间线与内容演变']


def split_user_blocks(text):
    """按角色切块，只返回用户块文本列表，每块带时间戳。"""
    lines = text.split('\n')
    blocks = []
    cur_role = None
    cur_time = None
    buf = []

    def flush():
        if cur_role in USER_NAMES and buf:
            content = '\n'.join(buf).strip()
            if content:
                blocks.append((cur_time, content))

    for ln in lines:
        m = ROLE_RE.match(ln.strip())
        if m:
            flush()
            cur_role = m.group(1)
            cur_time = (m.group(2) or '').strip('()')
            buf = []
        else:
            buf.append(ln)
    flush()
    return blocks


def split_sentences(block):
    """把一个用户块切成候选句（保留口语断句）。"""
    # 按换行、句号、问号、叹号切，但保留内容
    parts = re.split(r'[\n。！？!?；;]+', block)
    out = []
    for p in parts:
        p = p.strip().lstrip('> ').strip()
        p = re.sub(r'\*\*', '', p)
        if p:
            out.append(p)
    return out


def is_quality(t):
    """质量过滤：剔除事务性、过短、链接、纯引用等。"""
    if len(t) < 10:
        return False
    if t.startswith(('[图', '[📎', 'http', 'www', '#', '|', '---', '```')):
        return False
    if re.fullmatch(r'[\d\s\.\-:：/]+', t):  # 纯数字/时间
        return False
    if re.search(r'(学号|座位号|身份证|验证码|怎么填|填什么|几点了|天气|订票|快递)', t) and len(t) < 40:
        return False
    # 剔除明显是转贴的AI内容（用户引用AI的情况少见，保守剔除格式特征）
    if t.startswith(('摘要', '关键词', '参考文献', 'Abstract')):
        return False
    return True


def main():
    files = []
    for d in CONV_DIRS:
        files += glob.glob(os.path.join(d, '**', '*.md'), recursive=True)
    files = sorted(set(f for f in files if not any(e in f for e in EXCLUDE)))

    all_quotes = []
    per_file = Counter()
    for fp in files:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception:
            continue
        blocks = split_user_blocks(text)
        src = os.path.basename(fp)
        n = 0
        for ts, block in blocks:
            for sent in split_sentences(block):
                if is_quality(sent):
                    all_quotes.append({'text': sent, 'source': src, 'time': ts})
                    n += 1
        per_file[src] = n

    # 去重
    seen = set()
    uniq = []
    for q in all_quotes:
        k = q['text']
        if k in seen:
            continue
        seen.add(k)
        uniq.append(q)

    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({'total': len(uniq), 'quotes': uniq}, f, ensure_ascii=False, indent=2)

    print(f'扫描对话文件 {len(files)} 个')
    print(f'用户原话候选（去重后）{len(uniq)} 条 -> {OUT_JSON}\n')
    print('=== 每文件用户原话数（前25）===')
    for s, n in per_file.most_common(25):
        print(f'{n:5d}  {s}')


if __name__ == '__main__':
    main()

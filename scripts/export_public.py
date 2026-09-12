#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_public.py —— 双库分层·公开成果库白名单导出器（S00）

铁律：默认全部私有，只有 docs/协作机制/PUBLIC_MANIFEST.txt 列出的内容才导出。
- 只允许从【干净的 main】导出，避免把在途改动或错分支内容外泄。
- --dry-run（默认）：只算清单、体积、敏感扫描，不写盘。
- --to DIR：把白名单文件镜像同步到 DIR；只清理“上一次由本脚本导出、本次已不在清单”的文件，
  绝不触碰 DIR 里其他东西；并写 EXPORT_INFO.txt 记录母本 sha 与时间，便于溯源。
- BLOCK（手机/身份证/邮箱/密钥）命中直接拦下、不自动救；内部协作词先做“导出时净化”：
  只剥离文首生产过程元信息头、统一作者署名，正文一字不动、母本原文件不改；净化后正文
  仍含内部词的（协作过程织入正文）继续拦下转人工。单一事实源始终是母本，公开库只是投影。
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, 'docs', '协作机制', 'PUBLIC_MANIFEST.txt')
STAMP = '.export_manifest.txt'  # 目标目录里记录“上次导出了哪些文件”

# ---------- 敏感规则 ----------
# 手机号：前不贴数字/字母/点，后不贴数字或 @（排除邮箱内的数字前缀）
RE_PHONE = re.compile(r'(?<![\dA-Za-z.])(1[3-9]\d{9})(?!\d|@)')
# 身份证：必须含合法出生年月日(19/20xx + 月 + 日)，且不被 URL 路径字符(. / - 字母)包裹，排除长数字串误报
RE_IDCARD = re.compile(
    r'(?<![\dA-Za-z./-])\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?![\dA-Za-z./-])')
RE_EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
RE_SECRET = re.compile(
    r'(?i)(token|secret|passwd?|api[_-]?key|private[_-]?key|credential|access[_-]?key)'
    r'\s*[:=]\s*["\']?[A-Za-z0-9_\-/+=]{8,}')
BLOCK_PATTERNS = [('手机号', RE_PHONE), ('身份证', RE_IDCARD), ('邮箱', RE_EMAIL), ('密钥', RE_SECRET)]

REVIEW_TERMS = ['定时任务', 'cron', '分站', 'S00', 'S01', 'S02', 'S03', 'S04', 'S05', 'S06',
                'worktree', '明旭', 'open_id', 'chat_id', '北原慢热', '飞书', 'Doubao/chats',
                '192781-li', 'PR#', 'issue']
RE_REVIEW = re.compile('|'.join(re.escape(t) for t in REVIEW_TERMS))

# 第二层“洁净门”：白名单候选文件若含以下内部协作/原始过程痕迹，默认拦下不导出（清洗后才放）
INTERNAL_TERMS = ['S00', 'S01', 'S02', 'S03', 'S04', 'S05', 'S06', '分站', '明旭', '大总站',
                  '定时任务', 'cron', 'worktree', 'open_id', 'chat_id', '飞书',
                  'Doubao/chats', '192781-li', '大乱炖', '<thinking>',
                  '用户原话', 'PR#', '三遍法', 'workbuddy', 'doubaocdn', '李松翰']
RE_INTERNAL = re.compile('|'.join(re.escape(t) for t in INTERNAL_TERMS))
# “多智能体系统”是正常学术词，不拦；只拦原始对话记录里的“（智能体 2026/06/14 …）”时间戳痕迹
# 投稿模板残留字段（外部作者通信/收稿/作者简介）是强过程特征，拦
INTERNAL_REGEX = [re.compile(r'智能体\s*\d{4}[/年-]'), re.compile(r'[（(]\s*智能体'),
                  re.compile(r'通信邮箱|作者单位|收稿日期|作者简介')]
# 注：deepseek/豆包/doubao 是正文合法讨论对象（如“DeepSeek 干渠”），故意不硬拦
# 文件名/路径层面的内部代号：内容净化管不到文件名，路径命中一律拦下（改名后才放）
PATH_INTERNAL = re.compile(r'S0[0-6]|分站|明旭|大总站|大乱炖|定时任务|worktree')
SIGNATURE_TERM = '北原慢热'  # 作者笔名，允许公开，仅计数告知

TEXT_EXT = {'.md', '.txt', '.json', '.html', '.csv', '.py', '.yml', '.yaml',
            '.js', '.css', '.tex', '.v', '.sh'}


def git(*args):
    r = subprocess.run(['git', '-C', REPO] + list(args), capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def ensure_clean_main():
    _, branch, _ = git('branch', '--show-current')
    _, status, _ = git('status', '--porcelain')
    return branch == 'main' and status == '', branch, status


def load_manifest():
    includes, excludes = [], []
    with open(MANIFEST, encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('!'):
                excludes.append(line[1:].strip())
            else:
                includes.append(line.rstrip('/'))
    return includes, excludes


def glob_to_regex(pat):
    """支持 ** 跨目录、* 不跨 /、? 单字符。"""
    rx = '^'
    i = 0
    while i < len(pat):
        c = pat[i]
        if c == '*' and i + 1 < len(pat) and pat[i + 1] == '*':
            rx += '.*'
            i += 2
            if i < len(pat) and pat[i] == '/':
                i += 1  # **/ 吃掉斜杠
            continue
        if c == '*':
            rx += '[^/]*'
        elif c == '?':
            rx += '.'
        else:
            rx += re.escape(c)
        i += 1
    return rx + '$'


def compile_excludes(excludes):
    regs, prefixes = [], []
    for e in excludes:
        if e.endswith('/**'):
            prefixes.append(e[:-3].rstrip('/') + '/')
        elif '*' in e or '?' in e:
            regs.append(re.compile(glob_to_regex(e)))
        else:
            prefixes.append(e.rstrip('/') + '/')
    return regs, prefixes


def is_excluded(path, regs, prefixes):
    p = path + '/'
    for pre in prefixes:
        if p.startswith(pre) or path == pre.rstrip('/'):
            return True
    for r in regs:
        if r.match(path):
            return True
    return False


def expand_include(rule):
    ap = os.path.join(REPO, rule)
    if os.path.isfile(ap):
        return [rule]
    if os.path.isdir(ap):
        out = []
        for root, _, files in os.walk(ap):
            for fn in files:
                out.append(os.path.relpath(os.path.join(root, fn), REPO))
        return out
    out = []
    for m in glob.glob(os.path.join(REPO, rule), recursive=True):
        if os.path.isfile(m):
            out.append(os.path.relpath(m, REPO))
    return out


def select_files():
    inc, exc = load_manifest()
    regs, prefixes = compile_excludes(exc)
    selected = set()
    missing = []
    for rule in inc:
        files = expand_include(rule)
        if not files and not any(ch in rule for ch in '*?'):
            missing.append(rule)
        selected.update(files)
    final = sorted(p for p in selected if not is_excluded(p, regs, prefixes))
    return final, missing


# ---------- 导出时净化（只擦“文首元信息头”，绝不改写正文论证；母本原文件一字不动）----------
# 作者类元信息行统一替换为笔名（只保留一次）
AUTHOR_LINE = re.compile(r'^\s*(?:>)?[-*|\s]*(?:作者|著者|思考者)\s*[:：].*$')
# 标题里的内部分站前缀，如 “# S01 哲学研判：xxx” -> “# xxx”
TITLE_PREFIX = re.compile(r'^(\s*#{1,4}\s*)(?:S0\d|大总站|明旭)[^：:\n]{0,14}[：:]\s*')
# 元信息行形态：> 引用行、**标签**：行
META_QUOTE = re.compile(r'^\s*>')
META_LABEL = re.compile(r'^\s*[-*|\s]*\*\*[^*\n*]{1,14}\*\*\s*[:：]')
# 文首元信息行命中以下“内部生产痕迹”即整行剥离（仅作用于正文开始之前的头部区）
HEAD_DROP = re.compile(
    r'S0[0-6]|分站|明旭|大总站|定时任务|cron|DeepSeek|deepseek|workbuddy|doubao|豆包|doubaocdn|'
    r'核验|巡检|激活|触发|指令包|本主对话|长谈|对话产出|答题训练|AGENTS|协作机制|mingbenlun|'
    r'PR#|三遍法|用户原话|飞书|worktree|编制|记录人|记录者|执行者|研判分站|研究分站|'
    r'审查分站|收件|发件|验收|归档')
# 注：“整理者/作者裁定”等词不入 DROP——文首可能用它们定义正文沿用的【原】【显】图例，删了读者看不懂


def _head_end(lines, cap=40):
    """正文起点：从首行起连续的“头部元信息形态”结束处。头部形态含标题(#)、空行、
    > 引用、**标签**：行、---、以及 <!-- ... --> HTML 注释元数据块（可跨行）。
    不按“第一个 ##”判定（有文件直接用 ## 当大标题）；首行即普通正文则 he=0。"""
    i, in_comment = 0, False
    while i < min(cap, len(lines)):
        s = lines[i].strip()
        if in_comment:
            if '-->' in s:
                in_comment = False
            i += 1
            continue
        if s.startswith('<!--'):
            if '-->' not in s:
                in_comment = True
            i += 1
            continue
        if not s or s.startswith('#') or s.startswith('>') or s == '---' or META_LABEL.match(lines[i]):
            i += 1
            continue
        break
    return i


def sanitize_text(txt):
    """只净化文首元信息头：①整块剥离 <!-- --> 内部元数据并补一行中性署名；
    ②标题去内部分站前缀；③作者行统一笔名（只一次）；④剥离含生产痕迹的 > / **标签** 行。
    正文（head_end 之后）一字不动。返回 (净化文本, 是否改动)。"""
    lines = txt.split('\n')
    he = _head_end(lines)
    out, changed, author_done = [], False, False
    i = 0
    while i < len(lines):
        line = lines[i]
        if i < he and line.strip().startswith('<!--'):  # HTML注释元数据块整块剥离
            j, blob, closed = i, [], False
            limit = min(len(lines), he + 40)
            while j < limit:
                blob.append(lines[j])
                if '-->' in lines[j]:
                    j += 1
                    closed = True
                    break
                j += 1
            if not closed:  # 未闭合注释：安全降级，保留原文交内容门判定
                out.append(line)
                i += 1
                continue
            if not author_done and any(('作者' in b or '著者' in b) for b in blob):
                out.append('> 作者：' + SIGNATURE_TERM)
                author_done = True
            changed, i = True, j
            continue
        if i < he:
            mt = TITLE_PREFIX.match(line)
            if mt:  # 标题去内部分站前缀
                line = TITLE_PREFIX.sub(mt.group(1), line, count=1)
                changed = True
            if AUTHOR_LINE.match(line):  # 作者行统一为笔名，只留一次
                if not author_done:
                    out.append('> 作者：' + SIGNATURE_TERM)
                    author_done = True
                changed = True
                i += 1
                continue
            is_meta = bool(META_QUOTE.match(line) or META_LABEL.match(line))
            if is_meta and HEAD_DROP.search(line):
                changed = True
                i += 1
                continue  # 含内部生产痕迹的元信息行整行剥离
        out.append(line)
        i += 1
    res, blank = [], 0  # 3+ 连续空行压成 2
    for ln in out:
        if ln.strip() == '':
            blank += 1
            if blank <= 2:
                res.append(ln)
        else:
            blank = 0
            res.append(ln)
    return '\n'.join(res), changed


def mask(line, m):
    return line[max(0, m.start() - 8):m.start()] + '【命中】' + line[m.end():m.end() + 8]


def scan(files):
    block_hits, review_hits = [], {}
    for rel in files:
        ext = os.path.splitext(rel)[1].lower()
        if ext not in TEXT_EXT:
            continue
        ap = os.path.join(REPO, rel)
        try:
            with open(ap, encoding='utf-8', errors='ignore') as f:
                for ln, line in enumerate(f, 1):
                    for name, rx in BLOCK_PATTERNS:
                        m = rx.search(line)
                        if m:
                            block_hits.append((rel, ln, name, mask(line.strip(), m)[:60]))
                    for term in RE_REVIEW.findall(line):
                        review_hits.setdefault(term, set()).add(rel)
        except OSError:
            pass
    return block_hits, review_hits


def partition(files, block_hits):
    """第二层洁净门：白名单候选先做文首元信息净化（母本不动），再按净化后内容过滤。
    硬敏感（手机/证/邮箱/密钥）不自动救，直接拦下；内部协作词在净化后文本上复检，
    正文仍残留的（协作过程织入正文）继续拦下转人工。
    返回 (clean, held=[(rel,reasons)], 含署名文件数 sig, {rel: 净化后文本})。"""
    block_by = {}
    for rel, ln, name, frag in block_hits:
        block_by.setdefault(rel, []).append(f'{name}:{ln}')
    clean, held, sig, san_map = [], [], 0, {}
    for rel in files:
        block = set(block_by.get(rel, []))
        if PATH_INTERNAL.search(rel):  # 文件名/路径含内部代号，拦下转人工改名
            block.add('文件名含内部代号')
        ext = os.path.splitext(rel)[1].lower()
        if ext not in TEXT_EXT:
            if block:
                held.append((rel, sorted(block)))
            else:
                clean.append(rel)
            continue
        try:
            txt = open(os.path.join(REPO, rel), encoding='utf-8', errors='ignore').read()
        except OSError:
            txt = ''
        san, changed = sanitize_text(txt)
        reasons = set(block)  # 硬敏感不自动救
        if not block:
            for t in INTERNAL_TERMS:
                if t in san:
                    reasons.add(t)
            for rx in INTERNAL_REGEX:
                if rx.search(san):
                    reasons.add('原始对话记录')
                    break
        if reasons:
            held.append((rel, sorted(reasons)))
        else:
            clean.append(rel)
            if changed:
                san_map[rel] = san
            if SIGNATURE_TERM in san:
                sig += 1
    return clean, held, sig, san_map


def human(n):
    for u in ['B', 'KB', 'MB', 'GB']:
        if n < 1024 or u == 'GB':
            return f'{n:.1f}{u}'
        n /= 1024


def group_stats(files, san_map=None):
    san_map = san_map or {}
    groups = {}
    size = 0
    for rel in files:
        if rel in san_map:
            size += len(san_map[rel].encode('utf-8'))
        else:
            size += os.path.getsize(os.path.join(REPO, rel))
        key = '/'.join(rel.split('/')[:2]) if rel.startswith('docs/') else rel.split('/')[0]
        groups[key] = groups.get(key, 0) + 1
    return size, sorted(groups.items(), key=lambda x: -x[1])


def main():
    ap = argparse.ArgumentParser(description='公开成果库白名单导出器')
    ap.add_argument('--to', help='导出目标目录（不给则只 dry-run）')
    ap.add_argument('--allow-sensitive', action='store_true', help='存在 BLOCK 命中也强行导出（默认不允许）')
    a = ap.parse_args()

    ok, branch, status = ensure_clean_main()
    _, head, _ = git('rev-parse', '--short', 'HEAD')
    if not ok:
        print(f'[拒绝导出] 必须在干净的 main 上。当前分支={branch}，未提交={len(status.splitlines())} 处。')
        return 1
    if not os.path.isfile(MANIFEST):
        print(f'[拒绝] 找不到白名单：{MANIFEST}')
        return 1

    files, missing = select_files()
    block_hits, _review = scan(files)
    export_files, held, sig, san_map = partition(files, block_hits)
    size, groups = group_stats(export_files, san_map)

    print(f'母本 main @ {head}')
    print(f'白名单候选 {len(files)} 个 → 洁净门放行 {len(export_files)} 个（{human(size)}）；'
          f'拦下待清洗 {len(held)} 个；其中导出时自动净化文首元信息头 {len(san_map)} 篇（母本不动）；'
          f'放行集中含署名“{SIGNATURE_TERM}”的文件 {sig} 个')
    for k, n in groups:
        print(f'  放行 {n:4d}  {k}')
    if missing:
        print('[警告] 以下白名单规则未匹配到任何文件：')
        for m in missing:
            print('   -', m)
    reason_count = {}
    for rel, rs in held:
        for r in rs:
            reason_count[r] = reason_count.get(r, 0) + 1
    print('\n洁净门拦下（回母本清洗后才会导出，本次不放行）：')
    for r, n in sorted(reason_count.items(), key=lambda x: -x[1]):
        print(f'  {n:4d} 个文件含 “{r}”')
    for rel, ln, name, frag in block_hits[:20]:
        print(f'  [BLOCK/{name}] {rel}:{ln}  {frag}')

    if not a.to:
        print('\n[dry-run] 未写盘。确认后用 --to <目录> 实际导出（只导放行集）。')
        return 0

    repo_real = os.path.realpath(REPO)
    dst = os.path.realpath(os.path.abspath(a.to))
    # 按路径段判断，避免 mingbenlun-open 因字符串前缀 mingbenlun 被误判为仓库内部
    if dst == repo_real or dst.startswith(repo_real + os.sep):
        print('[拒绝] 导出目标不能在母本仓库内部。')
        return 1
    os.makedirs(dst, exist_ok=True)
    stamp = os.path.join(dst, STAMP)
    prev = set()
    if os.path.isfile(stamp):
        with open(stamp, encoding='utf-8') as f:
            prev = {l.strip() for l in f if l.strip()}
    cur = set(export_files)
    # 只删除“上次导出过、这次已不在放行集”的文件，绝不碰目标目录其他内容
    for old in prev - cur:
        op = os.path.join(dst, old)
        if os.path.isfile(op):
            os.remove(op)
    copied = 0
    for rel in export_files:
        s, d = os.path.join(REPO, rel), os.path.join(dst, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        if rel in san_map:  # 文本文件写“净化后”版本，母本原文件不动
            with open(d, 'w', encoding='utf-8') as f:
                f.write(san_map[rel])
        else:
            shutil.copy2(s, d)
        copied += 1
    # 清理导出后遗留的空目录
    for root, dirs, fs in os.walk(dst, topdown=False):
        if root != dst and not os.listdir(root):
            os.rmdir(root)
    with open(stamp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(cur)))
    with open(os.path.join(dst, 'EXPORT_INFO.txt'), 'w', encoding='utf-8') as f:
        f.write(f'导出自母本 mingbenlun main {head}\n导出时间 {time.strftime("%Y-%m-%d %H:%M:%S")}\n'
                f'文件数 {len(export_files)}，体积 {human(size)}\n本目录为白名单+洁净门投影，请勿手改；改内容回母本后重新导出。\n')
    print(f'\n[完成] 已镜像导出 {copied} 个文件到 {dst}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

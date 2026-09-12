#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_public.py —— 双库分层·公开成果库白名单导出器（S00）

铁律：默认全部私有，只有 docs/协作机制/PUBLIC_MANIFEST.txt 列出的内容才导出。
- 只允许从【干净的 main】导出，避免把在途改动或错分支内容外泄。
- --dry-run（默认）：只算清单、体积、敏感扫描，不写盘。
- --to DIR：把白名单文件镜像同步到 DIR；只清理“上一次由本脚本导出、本次已不在清单”的文件，
  绝不触碰 DIR 里其他东西；并写 EXPORT_INFO.txt 记录母本 sha 与时间，便于溯源。
- 敏感扫描两级：
  BLOCK（手机/身份证/邮箱/密钥，命中默认拒绝导出）；
  REVIEW（内部代号/协作词，列出供人工确认，不硬拦）。
本脚本不做任何内容改写；需脱敏的内容回母本修改后重导（单一事实源）。
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
INTERNAL_TERMS = ['S00', 'S01', 'S02', 'S03', 'S04', 'S05', 'S06', '分站', '明旭',
                  '定时任务', 'cron', 'worktree', 'open_id', 'chat_id', '飞书',
                  'Doubao/chats', '192781-li', '大乱炖', '<thinking>',
                  '用户原话', 'PR#', '三遍法']
RE_INTERNAL = re.compile('|'.join(re.escape(t) for t in INTERNAL_TERMS))
# “多智能体系统”是正常学术词，不拦；只拦原始对话记录里的“（智能体 2026/06/14 …）”时间戳痕迹
INTERNAL_REGEX = [re.compile(r'智能体\s*\d{4}[/年-]'), re.compile(r'[（(]\s*智能体')]
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
    """第二层洁净门：白名单候选再按内容过滤。
    返回 (可导出 clean, 拦下 held=[(rel,reasons)], 含作者署名的文件数 sig)。"""
    block_by = {}
    for rel, ln, name, frag in block_hits:
        block_by.setdefault(rel, []).append(f'{name}:{ln}')
    clean, held, sig = [], [], 0
    for rel in files:
        reasons = set(block_by.get(rel, []))
        if os.path.splitext(rel)[1].lower() in TEXT_EXT:
            try:
                txt = open(os.path.join(REPO, rel), encoding='utf-8', errors='ignore').read()
            except OSError:
                txt = ''
            for t in INTERNAL_TERMS:
                if t in txt:
                    reasons.add(t)
            for rx in INTERNAL_REGEX:
                if rx.search(txt):
                    reasons.add('原始对话记录')
                    break
            if SIGNATURE_TERM in txt:
                sig += 1
        if reasons:
            held.append((rel, sorted(reasons)))
        else:
            clean.append(rel)
    return clean, held, sig


def human(n):
    for u in ['B', 'KB', 'MB', 'GB']:
        if n < 1024 or u == 'GB':
            return f'{n:.1f}{u}'
        n /= 1024


def group_stats(files):
    groups = {}
    size = 0
    for rel in files:
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
    export_files, held, sig = partition(files, block_hits)
    size, groups = group_stats(export_files)

    print(f'母本 main @ {head}')
    print(f'白名单候选 {len(files)} 个 → 洁净门放行 {len(export_files)} 个（{human(size)}）；'
          f'拦下待清洗 {len(held)} 个；放行集中含署名“{SIGNATURE_TERM}”的文件 {sig} 个')
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

    dst = os.path.abspath(a.to)
    if os.path.abspath(dst).startswith(REPO):
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
s00_patrol.py —— S00 大总站巡检工作台

把"检查库里新东西"从手工拼证据变成一条命令。
默认只读，不改动任何文件；sync --apply 才会添加文件（只增不删不改）。

子命令：
  report          跑全部检查，生成巡检报告到 docs/协作机制/巡检报告/
  sync --dry-run  列出各分站分支里 main 没有的共享文档（默认，不改动）
  sync --apply    真正同步：把白名单内 main 没有的共享文档添加到 main（只增不删不改）
  all             report + sync --dry-run

检查项：
  1. 分站分支集成状态（领先/落后）
  2. 结晶库（main编号连续 + 跨分支同号异义 + 分支独有）
  3. 定时任务注册表（内部一致 + 平台快照对账，若有快照文件）
  4. 分站档案完整性
  5. 未合并 PR / 最近 CI 运行（gh 可用时）
  6. 工作区未提交改动
  7. 关键目录文件数
  8. 分站独立 worktree 隔离一致性（L041：主仓库固定 main、S01-S06 各绑长期分支）

共享文档白名单（sync 只处理这些，且只添加 main 没有的文件）：
  - docs/协作机制/智慧河流/        （append-only，合并仍走 river_sync.sh pull）
  - docs/协作机制/分站/*_to_*.md   （分站间通道）
  - docs/notes/Coq形式化/S01给S04_*.md
  - docs/notes/哲学研究/            （S01 哲学产出）
  - docs/高考数学/                  （S06 成果）

原则：只检测报告、只添加缺失；冲突/裁决交人，不自动合并、不删除、不覆盖。
"""
import argparse, datetime, json, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIONS = {
    'S01': 's01-philosophy', 'S02': 's02-gaokao-arts', 'S03': 's03-divination',
    'S04': 's04-coq', 'S05': 's05-info', 'S06': 's06-math',
}
CRYSTAL = 'docs/协作机制/智慧河流/智慧结晶库.md'
NETCONF = 'docs/协作机制/明旭的记忆/定时任务网络配置.json'
PROFILE_DIR = 'docs/协作机制/分站'
REPORT_DIR = 'docs/协作机制/巡检报告'
SNAPSHOT_FILE = 'docs/协作机制/明旭的记忆/平台快照_latest.json'
# 分站独立 worktree 根目录（《分站独立工作区Worktree使用规范_20260912》固定路径，教训 L041/PR#100）
WORKTREE_BASE = '/home/user/mingxu-worktrees'

# 共享文档白名单：sync 只添加这些路径下 main 没有的文件
SHARED_WHITELIST = [
    'docs/协作机制/智慧河流/',
    'docs/协作机制/分站/',          # 只同步 *_to_*.md 通道，见 filter
    'docs/notes/Coq形式化/S01给S04_',
    'docs/notes/哲学研究/',
    'docs/高考数学/',
]

issues = []  # (level, check, msg)


def git(*args):
    # -c core.quotepath=false 确保中文路径不被八进制转义，否则 startswith 白名单匹配会失效
    r = subprocess.run(['git', '-C', REPO, '-c', 'core.quotepath=false'] + list(args),
                       capture_output=True, text=True)
    return r.stdout.strip()


def git_show(ref, path):
    r = subprocess.run(['git', '-C', REPO, 'show', f'{ref}:{path}'],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ''


def err(c, m): issues.append(('ERROR', c, m))
def warn(c, m): issues.append(('WARN', c, m))


def crystal_map(text):
    d = {}
    for m in re.finditer(r'^## 结晶(\d{3})[：:](.+)$', text, flags=re.M):
        d[m.group(1)] = m.group(2).strip()
    return d


# ===================== 检查项 =====================

def check_branches():
    rows = []
    for st, br in STATIONS.items():
        if not git('rev-parse', '--verify', f'origin/{br}'):
            rows.append((st, br, '-', '-', '远端分支不存在'))
            warn('branches', f'origin/{br}（{st}）不存在')
            continue
        a = git('rev-list', '--count', f'main..origin/{br}')
        b = git('rev-list', '--count', f'origin/{br}..main')
        try:
            ai, bi = int(a), int(b)
        except ValueError:
            ai, bi = 0, 0
        status = '✅ 同步' if ai == 0 and bi == 0 else ('⚠️ 待集成' if ai > 10 else '有差异')
        rows.append((st, br, ai, bi, status))
        if ai > 10:
            warn('branches', f'{st}({br}) 领先 main {ai}，积压较多待集成')
    return rows


def check_crystals():
    main_txt = open(os.path.join(REPO, CRYSTAL), encoding='utf-8').read()
    main_map = crystal_map(main_txt)
    nums = sorted(main_map.keys())
    adjudicated = set(re.findall(r'^\|\s*结晶(\d{3})', main_txt, flags=re.M))
    info = {'main_count': len(main_map), 'main_range': f'{nums[0]}..{nums[-1]}' if nums else '-'}
    # 编号连续
    if nums:
        for i in range(1, len(nums) + 1):
            if f'{i:03d}' not in main_map:
                err('crystals', f'main 结晶编号不连续：缺 {i:03d}')
                break
    dup = [n for n in set(nums) if nums.count(n) > 1]
    if dup:
        err('crystals', f'main 结晶重复编号：{dup}')
    # 跨分支
    clashes, unique = [], []
    for st, br in STATIONS.items():
        bmap = crystal_map(git_show(f'origin/{br}', CRYSTAL))
        for n, t in bmap.items():
            if n in main_map:
                if main_map[n][:12] != t[:12]:
                    if n in adjudicated:
                        clashes.append((st, br, n, '已裁决待同步'))
                    else:
                        clashes.append((st, br, n, '未裁决！'))
                        err('crystals', f'{br} 结晶{n} 同号异义且未裁决')
            else:
                unique.append((st, br, n, t[:30]))
    info['clashes'] = clashes
    info['unique'] = unique
    return info


def check_registry():
    """定时任务对账。cron状态唯一权威=平台快照，注册表只存分站映射和任务队列。"""
    conf = json.load(open(os.path.join(REPO, NETCONF), encoding='utf-8'))
    stations = conf.get('stations', {})
    # 从平台快照读 cron 状态（唯一权威）
    snap_ref = conf.get('cron_snapshot_ref', SNAPSHOT_FILE)
    snap_path = os.path.join(REPO, snap_ref)
    if not os.path.exists(snap_path):
        err('registry', f'平台快照不存在: {snap_ref}')
        return {'version': conf.get('version'), 'jobs': 0, 'active': 0, 'stopped': 0, 'stations': len(stations), 'snapshot': '缺失'}
    snap = json.load(open(snap_path, encoding='utf-8'))
    jobs = snap.get('active', []) + snap.get('stopped', [])
    info = {'version': conf.get('version'), 'snapshot_version': snap.get('version'),
            'exported_at': snap.get('exported_at'), 'jobs': len(jobs),
            'active': len(snap.get('active', [])),
            'stopped': len(snap.get('stopped', [])),
            'stations': len(stations)}
    # ID唯一
    ids = [j.get('id') for j in jobs]
    for i in set(ids):
        if ids.count(i) > 1:
            err('registry', f'快照中 ID {i} 重复')
    # station合法
    for j in jobs:
        if j.get('station') not in stations:
            err('registry', f'任务 {j.get("id")} 的 station={j.get("station")} 不在 stations')
    # active与stopped不重叠
    active_ids = {j.get('id') for j in snap.get('active', [])}
    stopped_ids = {j.get('id') for j in snap.get('stopped', [])}
    overlap = active_ids & stopped_ids
    if overlap:
        err('registry', f'ID 同时在 active 和 stopped: {overlap}')
    # stations.cron_job_id在快照里
    job_ids = {j.get('id') for j in jobs}
    for st, info_ in stations.items():
        cid = info_.get('cron_job_id')
        if cid and cid not in job_ids:
            err('registry', f'stations.{st}.cron_job_id={cid} 不在平台快照（幽灵）')
    info['snapshot'] = f'已加载（{snap.get("exported_at","?")}导出，{len(jobs)}任务）'
    return info


def check_profiles():
    stations = json.load(open(os.path.join(REPO, NETCONF), encoding='utf-8')).get('stations', {})
    files = os.listdir(os.path.join(REPO, PROFILE_DIR)) if os.path.isdir(os.path.join(REPO, PROFILE_DIR)) else []
    missing = []
    for st in stations:
        if st == 'S00':
            continue
        if not any(st in f and '身份档案' in f for f in files):
            missing.append(st)
            err('profiles', f'分站 {st} 缺身份档案')
    return missing


def check_pr_ci():
    info = {'prs': [], 'ci': '未检查(gh不可用)'}
    if subprocess.run(['which', 'gh'], capture_output=True).returncode != 0:
        return info
    r = subprocess.run(['gh', 'pr', 'list', '--state', 'open', '--json',
                        'number,title,author,createdAt'], capture_output=True, text=True, cwd=REPO)
    if r.returncode == 0 and r.stdout.strip():
        try:
            info['prs'] = json.loads(r.stdout)
        except Exception:
            pass
    r2 = subprocess.run(['gh', 'run', 'list', '--limit', '5', '--json',
                         'name,status,conclusion,createdAt'], capture_output=True, text=True, cwd=REPO)
    if r2.returncode == 0 and r2.stdout.strip():
        try:
            info['ci'] = json.loads(r2.stdout)
        except Exception:
            pass
    return info


def check_workspace():
    s = git('status', '--short')
    return [line for line in s.split('\n') if line.strip()]


def check_dirs():
    dirs = ['docs', 'scripts', 'docs/raw_materials', 'docs/协作机制',
            'docs/notes', '生命论_模块化']
    out = {}
    for d in dirs:
        p = os.path.join(REPO, d)
        if os.path.isdir(p):
            n = sum(len(files) for _, _, files in os.walk(p))
            out[d] = n
    return out


def parse_worktrees():
    """解析 `git worktree list --porcelain`，返回 [{path,head,branch,detached}]。"""
    out = git('worktree', 'list', '--porcelain')
    wts, cur = [], {}
    for line in out.splitlines():
        if not line.strip():
            if cur:
                wts.append(cur)
                cur = {}
            continue
        if line.startswith('worktree '):
            cur['path'] = line[9:].strip()
        elif line.startswith('HEAD '):
            cur['head'] = line[5:].strip()
        elif line.startswith('branch '):
            ref = line[7:].strip()
            cur['branch'] = ref[11:] if ref.startswith('refs/heads/') else ref
        elif line.startswith('detached'):
            cur['detached'] = True
    if cur:
        wts.append(cur)
    return wts


def check_worktrees():
    """分站独立 worktree 隔离一致性（教训 L041、PR#100、Worktree 使用规范）。

    期望态：主仓库（协调中心，REPO）固定 main；S01–S06 各有
    WORKTREE_BASE/sXX 且绑定各自长期分支。
    定级：分站 worktree 缺失/目录丢失/绑错分支 = ERROR（隔离失效会回到 HEAD 互踩，
    report 的硬错误退出码 1 可在夜间巡检拦截）；主仓库未固定 main、期望表外的额外或
    失效登记 = WARN（不阻断，提示 prune/回归 main）。
    """
    rows = []
    expected = [('协调中心', REPO, 'main')]
    for st, br in STATIONS.items():
        expected.append((st, os.path.join(WORKTREE_BASE, st.lower()), br))

    raw = git('worktree', 'list', '--porcelain')
    if not raw:
        err('worktrees', 'git worktree list 无输出，无法核验 worktree 隔离状态')
        return rows
    by_path = {w.get('path'): w for w in parse_worktrees()}

    seen = set()
    for name, path, want_br in expected:
        w = by_path.get(path)
        if w is None:
            if name == '协调中心':
                continue  # 脚本就运行在主仓库内，主仓库不可能不在列
            err('worktrees', f'{name} 独立 worktree 缺失：{path} 未登记（隔离失效，见 L041/Worktree规范）')
            rows.append((name, path, '—', want_br, '❌ 缺失'))
            continue
        seen.add(path)
        actual = 'detached' if w.get('detached') else w.get('branch', '?')
        alive = os.path.isdir(path)
        if name == '协调中心':
            if not alive:
                warn('worktrees', f'主仓库目录不可达：{path}')
                state = '⚠️ 目录不可达'
            elif actual != 'main':
                warn('worktrees', f'主仓库(协调中心)未固定 main，当前 {actual}，应 git checkout main')
                state = '⚠️ 未固定main'
            else:
                state = '✅ main'
        else:
            if not alive:
                err('worktrees', f'{name} worktree 有登记但目录已丢失：{path}')
                state = '❌ 目录丢失'
            elif actual == want_br:
                state = '✅ 隔离'
            elif actual.startswith(name.lower() + '-') or actual.startswith(name.lower() + '_'):
                # 在自己 worktree 内切了本站临时分支：不破坏隔离，只提示干完回归长期分支
                warn('worktrees', f'{name} worktree 停在本站临时分支 {actual}，干完回长期分支 {want_br}')
                state = '⚠️ 临时分支'
            else:
                # 绑了他站长期分支/无关分支=串台，隔离真失效
                err('worktrees', f'{name} worktree 绑错/串台：应 {want_br}，实 {actual}')
                state = '❌ 绑错'
        rows.append((name, path, actual, want_br, state))

    # 反向核查：期望表之外的额外 worktree（可能是残留/失效登记）
    for p, w in by_path.items():
        if p in seen or p == REPO:
            continue
        tag = 'detached' if w.get('detached') else w.get('branch', '?')
        warn('worktrees', f'存在期望表外的 worktree：{p}（{tag}），确认是否残留，必要时 git worktree prune')
    return rows


def check_cultural_archive():
    """文化内容归位检查（结晶025、教训L038）"""
    result = {
        'archive_exists': False,
        'large_files_total': 0,
        'large_files_indexed': 0,
        'large_files_missing': [],
        'dirs_checked': 0,
        'dirs_missing': [],
    }
    archive_path = os.path.join(REPO, 'docs/notes/文化/文化品味总档案.md')
    if not os.path.exists(archive_path):
        err('cultural', '文化品味总档案不存在')
        return result
    result['archive_exists'] = True
    with open(archive_path, 'r', encoding='utf-8') as f:
        archive_text = f.read()

    # 检查>20KB的md文件是否在总档案中被引用
    for root, dirs, files in os.walk(os.path.join(REPO, 'docs')):
        for fn in files:
            if not fn.endswith('.md'):
                continue
            fp = os.path.join(root, fn)
            size = os.path.getsize(fp)
            if size > 20 * 1024:
                rel = os.path.relpath(fp, REPO)
                result['large_files_total'] += 1
                basename = os.path.basename(rel).replace('.md', '')
                key = basename[:10]
                if key and key in archive_text:
                    result['large_files_indexed'] += 1
                else:
                    result['large_files_missing'].append((rel, size))

    # 检查22个必查目录
    must_dirs = [
        'docs/notes/音乐', 'docs/notes/文化', 'docs/notes/哲学研究',
        'docs/notes/历史政治', 'docs/notes/理论研究', 'docs/notes/讨论记录',
        'docs/notes/资料提取', 'docs/notes/工具自动化', 'docs/体系研究',
        'docs/术数研究', 'docs/语义论', 'docs/对话与闪光', 'docs/学习训练',
        'docs/阅读笔记', 'docs/reference_materials/北原慢热实录',
        'docs/reference_materials/北原慢热原创', 'docs/reference_materials/思想史',
        'docs/reference_materials/杂项', 'docs/reference_materials/视频资料',
        'docs/reference_materials/万宜电台', 'docs/visualizations',
    ]
    for d in must_dirs:
        result['dirs_checked'] += 1
        if not os.path.isdir(os.path.join(REPO, d)):
            result['dirs_missing'].append(d)

    if result['large_files_missing']:
        warn('cultural', f'{len(result["large_files_missing"])}个>20KB文件可能未在文化品味总档案中登记')
    return result


# ===================== 报告生成 =====================

def generate_report(now):
    branches = check_branches()
    crystals = check_crystals()
    registry = check_registry()
    profiles = check_profiles()
    prci = check_pr_ci()
    ws = check_workspace()
    dirs = check_dirs()
    cultural = check_cultural_archive()
    worktrees = check_worktrees()

    ne = sum(1 for l, _, _ in issues if l == 'ERROR')
    nw = sum(1 for l, _, _ in issues if l == 'WARN')

    lines = []
    lines.append(f'# S00 巡检报告 {now.strftime("%Y-%m-%d %H:%M")}')
    lines.append('')
    lines.append('## 一、总览')
    lines.append(f'- 检查时间：{now.strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append(f'- 当前分支：{git("branch", "--show-current")}')
    lines.append(f'- main HEAD：{git("rev-parse", "--short", "main")}')
    lines.append(f'- 结果：**{ne} 错误，{nw} 警告**' +
                 ('（无硬错误）' if ne == 0 else ''))
    lines.append(f'- 工作区未提交：{len(ws)} 项')
    lines.append('')

    lines.append('## 二、分站分支集成状态')
    lines.append('| 分站 | 分支 | 领先main | 落后main | 状态 |')
    lines.append('|---|---|---|---|---|')
    for st, br, a, b, s in branches:
        lines.append(f'| {st} | {br} | {a} | {b} | {s} |')
    lines.append('')

    lines.append('## 三、结晶库')
    lines.append(f'- main：{crystals["main_count"]} 条，编号 {crystals["main_range"]}')
    if crystals['clashes']:
        lines.append('- 跨分支同号异义：')
        for st, br, n, tag in crystals['clashes']:
            lines.append(f'  - {br} 结晶{n}（{tag}）')
    else:
        lines.append('- 跨分支同号异义：无')
    if crystals['unique']:
        lines.append(f'- 分支独有结晶（待集成）：{len(crystals["unique"])} 条')
        for st, br, n, t in crystals['unique'][:10]:
            lines.append(f'  - {br} 结晶{n}：{t}')
    lines.append('')

    lines.append('## 四、定时任务网络')
    lines.append(f'- 注册表版本：v{registry["version"]}')
    lines.append(f'- 任务：{registry["jobs"]} 个（active {registry["active"]} / stopped {registry["stopped"]}）')
    lines.append(f'- 分站：{registry["stations"]} 个')
    lines.append(f'- 平台快照：{registry["snapshot"]}')
    lines.append('')

    lines.append('## 五、分站档案')
    lines.append('- 缺失：' + (', '.join(profiles) if profiles else '无（齐全）'))
    lines.append('')

    lines.append('## 六、未合并 PR 与 CI')
    if prci['prs']:
        lines.append(f'- 未合并 PR：{len(prci["prs"])} 个')
        for p in prci['prs']:
            lines.append(f'  - #{p["number"]} {p["title"]}（{p.get("author",{}).get("login","?")}）')
    else:
        lines.append('- 未合并 PR：无')
    ci = prci['ci']
    if isinstance(ci, list):
        lines.append('- 最近 CI 运行：')
        for c in ci[:5]:
            lines.append(f'  - {c["name"]}：{c.get("conclusion") or c.get("status")}（{c.get("createdAt","")[:10]}）')
    else:
        lines.append(f'- CI：{ci}')
    lines.append('')

    lines.append('## 七、关键目录文件数')
    for d, n in dirs.items():
        lines.append(f'- {d}/：{n} 个文件')
    lines.append('')

    lines.append('## 八、文化内容归位巡检')
    lines.append(f'- 文化品味总档案：{"存在" if cultural["archive_exists"] else "不存在"}')
    lines.append(f'- >20KB文件：{cultural["large_files_total"]}个，已登记{cultural["large_files_indexed"]}个')
    if cultural['large_files_missing']:
        lines.append(f'- 可能未登记：{len(cultural["large_files_missing"])}个')
        for rel, size in cultural['large_files_missing'][:10]:
            lines.append(f'  - {rel}（{size//1024}KB）')
    else:
        lines.append('- 可能未登记：无')
    lines.append(f'- 必查目录：{cultural["dirs_checked"]}个，缺失{len(cultural["dirs_missing"])}个')
    if cultural['dirs_missing']:
        for d in cultural['dirs_missing'][:5]:
            lines.append(f'  - 缺失：{d}')
    lines.append('')

    lines.append('## 九、分站 worktree 隔离一致性（L041）')
    lines.append('| 单元 | 工作区路径 | 当前分支 | 应绑分支 | 状态 |')
    lines.append('|---|---|---|---|---|')
    for name, path, actual, want, state in worktrees:
        lines.append(f'| {name} | {path} | {actual} | {want} | {state} |')
    lines.append('')

    if ws:
        lines.append('## 八、工作区未提交改动')
        for w in ws:
            lines.append(f'- {w}')
        lines.append('')

    if issues:
        lines.append('## 十、问题清单（需处理）')
        for lvl, chk, msg in issues:
            mark = '❌' if lvl == 'ERROR' else '⚠️ '
            lines.append(f'- {mark} [{chk}] {msg}')
        lines.append('')

    lines.append('---')
    lines.append(f'*本报告由 scripts/s00_patrol.py report 自动生成。只检测报告，不自动改动；裁决权在 S00/人。*')

    return '\n'.join(lines) + '\n', ne, nw


# ===================== 共享文档同步 =====================

def is_shared(path):
    """判断路径是否在共享白名单内（且是文件不是目录）"""
    if path.endswith('/'):
        return False
    # 分站目录只同步 *_to_*.md 通道
    if path.startswith('docs/协作机制/分站/'):
        return bool(re.search(r'_to_\w+\.md$', path))
    for prefix in SHARED_WHITELIST:
        if path.startswith(prefix):
            return True
    return False


def find_missing_shared():
    """找出各分站分支里、main 没有的、在白名单内的文件"""
    main_files = set(git('ls-tree', '-r', '--name-only', 'main').split('\n'))
    missing = []  # (station, branch, path)
    for st, br in STATIONS.items():
        if not git('rev-parse', '--verify', f'origin/{br}'):
            continue
        branch_files = git('ls-tree', '-r', '--name-only', f'origin/{br}').split('\n')
        for f in branch_files:
            if not f or f in main_files:
                continue
            if is_shared(f):
                missing.append((st, br, f))
    return missing


def sync_shared(apply=False):
    missing = find_missing_shared()
    if not missing:
        print('✅ 白名单内共享文档已全部在 main，无缺失')
        return 0
    print(f'发现 {len(missing)} 个 main 缺失的共享文档（白名单内，只增不删不改）：')
    by_branch = {}
    for st, br, f in missing:
        by_branch.setdefault(br, []).append(f)
        print(f'  [{br}] {f}')
    if not apply:
        print('\n（dry-run，未改动。加 --apply 真正添加到 main）')
        return 0
    # 真正添加：从各分支 checkout 这些文件
    added = 0
    for br, files in by_branch.items():
        for f in files:
            r = subprocess.run(['git', '-C', REPO, 'checkout', f'origin/{br}', '--', f],
                               capture_output=True, text=True)
            if r.returncode == 0:
                added += 1
                print(f'  + 添加：{f}（来自 {br}）')
            else:
                print(f'  ✗ 失败：{f} — {r.stderr.strip()[:80]}')
    print(f'\n完成：添加 {added} 个文件。请 review 后 commit（走 PR，main 受保护）。')
    return added


# ===================== 主入口 =====================

def main():
    ap = argparse.ArgumentParser(description='S00 大总站巡检工作台')
    sub = ap.add_subparsers(dest='cmd')
    sub.add_parser('report', help='生成巡检报告（只读）')
    sp = sub.add_parser('sync', help='共享文档同步（默认 dry-run）')
    sp.add_argument('--apply', action='store_true', help='真正添加到 main（默认只列出）')
    sub.add_parser('all', help='report + sync --dry-run')
    a = ap.parse_args()

    cmd = a.cmd or 'all'
    now = datetime.datetime.now()

    if cmd in ('report', 'all'):
        os.makedirs(os.path.join(REPO, REPORT_DIR), exist_ok=True)
        report, ne, nw = generate_report(now)
        fname = f'{now.strftime("%Y%m%d_%H%M")}_巡检报告.md'
        fpath = os.path.join(REPO, REPORT_DIR, fname)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f'✅ 巡检报告已生成：{REPORT_DIR}/{fname}')
        print(f'   结果：{ne} 错误，{nw} 警告')
        # 终端打印问题摘要
        if issues:
            print('\n问题摘要：')
            for lvl, chk, msg in issues:
                mark = '❌' if lvl == 'ERROR' else '⚠️ '
                print(f'  {mark} [{chk}] {msg[:90]}')

    if cmd in ('sync', 'all'):
        print()
        sync_shared(apply=getattr(a, 'apply', False))

    # report 模式有硬错误时退出码1，便于CI/夜间巡检拦截
    if cmd in ('report', 'all') and any(l == 'ERROR' for l, _, _ in issues):
        sys.exit(1)


if __name__ == '__main__':
    main()

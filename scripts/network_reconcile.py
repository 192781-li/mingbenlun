#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
network_reconcile.py —— 明本论分站网络对账机关（S00大总站）

定位：沉积的"记录"（注册表/编号/档案）与活的"实际"（平台任务/分支产出）
必然漂移；本脚本是绕不过的对账闸门，只检测、报告、给非零退出码，
**不自动修改**（裁决权在 S00/人，避免脚本乱改）。

四类检查：
  1. crystals  结晶库：main 编号连续唯一；跨分支"同号异义"；分支独有结晶
  2. branches  各分站分支 ahead/behind main（集成漂移）
  3. profiles  网络配置 stations 与 分站身份档案文件一一对应
  4. registry  定时任务注册表内部一致（ID唯一/站点合法/active与stopped不矛盾/task状态合法）

平台对账：脚本无法直接调 cron 平台。S00 巡检时把 list_cron_jobs 的真实结果
存成快照 JSON（--cron-snapshot path.json，格式 [{"id","status","schedule"}...]），
本脚本比对注册表 cron_jobs 与快照，报出 ID 缺失/状态不符/幽灵登记。

用法：
  python3 network_reconcile.py                # 全量检查（用本地已有 remote refs）
  python3 network_reconcile.py --fetch        # 先 git fetch 再查
  python3 network_reconcile.py --only crystals
  python3 network_reconcile.py --cron-snapshot snap.json
  python3 network_reconcile.py --json
退出码：0=无问题；1=发现漂移（供夜间巡检/CI 拦截）
"""
import argparse, json, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATION_BRANCHES = {
    'S01': 's01-philosophy', 'S02': 's02-gaokao-arts', 'S03': 's03-divination',
    'S04': 's04-coq', 'S05': 's05-info', 'S06': 's06-math',
}
CRYSTAL = 'docs/协作机制/智慧河流/智慧结晶库.md'
NETCONF = 'docs/协作机制/明旭的记忆/定时任务网络配置.json'
PROFILE_DIR = 'docs/协作机制/分站'

issues = []   # (level, check, msg)  level: ERROR/WARN


def git(*args, check=False):
    r = subprocess.run(['git', '-C', REPO] + list(args),
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout


def err(check, msg): issues.append(('ERROR', check, msg))
def warn(check, msg): issues.append(('WARN', check, msg))


def read_git_file(ref, path):
    r = subprocess.run(['git', '-C', REPO, 'show', f'{ref}:{path}'],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ''


def crystal_map(text):
    """返回 {编号: 标题}"""
    out = {}
    for m in re.finditer(r'^## 结晶(\d{3})[：:](.+)$', text, flags=re.M):
        out[m.group(1)] = m.group(2).strip()
    return out


def check_crystals():
    main_txt = open(os.path.join(REPO, CRYSTAL), encoding='utf-8').read()
    main_map = crystal_map(main_txt)
    # 已在 main 文首"编号裁决说明"里裁决过的旧号（分支旧号→main新号），
    # 这些在分支 pull main 前会持续报"同号异义"，属已知待同步，降级为 WARN。
    adjudicated = set(re.findall(r'^\|\s*结晶(\d{3})', main_txt, flags=re.M))
    # 1) main 自身：唯一 + 连续
    nums = sorted(main_map.keys())
    dup = [n for n in set(nums) if nums.count(n) > 1]
    if dup:
        err('crystals', f'main 结晶库出现重复编号 {dup}')
    if nums:
        for i in range(1, len(nums) + 1):
            expect = f'{i:03d}'
            if expect not in main_map:
                err('crystals', f'main 结晶编号不连续：缺 {expect}（现有 {nums[0]}..{nums[-1]}）')
                break
    # 2) 跨分支：同号异义 + 分支独有
    for st, br in STATION_BRANCHES.items():
        btxt = read_git_file(f'origin/{br}', CRYSTAL)
        if not btxt:
            continue
        bmap = crystal_map(btxt)
        for n, title in bmap.items():
            if n in main_map:
                if main_map[n][:12] != title[:12]:
                    if n in adjudicated:
                        warn('crystals', f'{br} 结晶{n} 为已裁决旧号（main已顺延重编号），'
                                        f'待该分支 pull main 后消除')
                    else:
                        err('crystals', f'{br} 结晶{n} 与 main 同号异义且未见裁决：'
                                       f'分支「{title[:24]}」vs main「{main_map[n][:24]}」'
                                       f'——分支应改用临时号、由S00合main时分配正式号')
            else:
                warn('crystals', f'{br} 独有结晶{n}「{title[:30]}」尚未合入 main（T002同步）')


def check_branches():
    # 分站在自己分支长期干活是常态（尤其S04的.v证明代码不回流main），
    # 领先/落后只作"集成提示"WARN，不判 ERROR；硬错误由结晶/注册表检查负责。
    for st, br in STATION_BRANCHES.items():
        exists = git('rev-parse', '--verify', f'origin/{br}').strip()
        if not exists:
            warn('branches', f'远端分支 origin/{br}（{st}）不存在')
            continue
        ahead = git('rev-list', '--count', f'main..origin/{br}').strip()
        behind = git('rev-list', '--count', f'origin/{br}..main').strip()
        try:
            a, b = int(ahead), int(behind)
        except ValueError:
            continue
        if a > 0:
            extra = '，积压较多，S00需安排集成共享文档' if a > 10 else ''
            warn('branches', f'{st}({br}) 领先 main {a} / 落后 {b}{extra}')


def check_profiles():
    conf = json.load(open(os.path.join(REPO, NETCONF), encoding='utf-8'))
    stations = conf.get('stations', {})
    if not os.path.isdir(os.path.join(REPO, PROFILE_DIR)):
        err('profiles', f'分站档案目录不存在：{PROFILE_DIR}')
        return
    files = os.listdir(os.path.join(REPO, PROFILE_DIR))
    for st in stations:
        if st == 'S00':
            continue
        if not any(st in f and '身份档案' in f for f in files):
            err('profiles', f'网络配置含分站 {st}，但 {PROFILE_DIR} 下缺其身份档案')


def check_registry(snapshot=None):
    """定时任务对账。cron状态唯一权威=平台快照文件，注册表只存分站映射和任务队列。
    snapshot: 可选，传入新导出的平台快照JSON路径，与库内快照对比（验证是否最新）。
    """
    conf = json.load(open(os.path.join(REPO, NETCONF), encoding='utf-8'))
    stations = conf.get('stations', {})
    station_names = set(stations.keys())

    # 从平台快照读 cron 状态（唯一权威）
    snap_ref = conf.get('cron_snapshot_ref', 'docs/协作机制/明旭的记忆/平台快照_latest.json')
    snap_path = os.path.join(REPO, snap_ref)
    if not os.path.exists(snap_path):
        err('registry', f'平台快照不存在: {snap_ref}')
        return
    snap = json.load(open(snap_path, encoding='utf-8'))
    jobs = snap.get('active', []) + snap.get('stopped', [])

    # ID 唯一
    ids = [j.get('id') for j in jobs]
    for i in set(ids):
        if ids.count(i) > 1:
            err('registry', f'快照中 ID {i} 重复 {ids.count(i)} 次')
    # station 合法
    for j in jobs:
        if j.get('station') not in station_names:
            err('registry', f'定时任务 {j.get("id")} 的 station={j.get("station")} 不在 stations 列表')
    # active 与 stopped 不矛盾（快照内 active/stopped 分两组，检查ID不重叠）
    active_ids = {j.get('id') for j in snap.get('active', [])}
    stopped_ids = {j.get('id') for j in snap.get('stopped', [])}
    overlap = active_ids & stopped_ids
    if overlap:
        err('registry', f'ID 同时出现在 active 和 stopped: {overlap}')
    # task_queue 状态合法（注册表里保留，非cron状态）
    legal = {'pending', 'in_progress', 'completed', 'blocked', 'done'}
    for t in conf.get('task_queue', []):
        if isinstance(t, dict) and str(t.get('status', '')).lower() not in legal:
            warn('registry', f'task_queue {t.get("id")} 状态非法：{t.get("status")}')
    # stations.cron_job_id 必须能在快照找到（分站→任务映射对账）
    job_ids = {j.get('id') for j in jobs}
    for st, info in stations.items():
        cid = info.get('cron_job_id')
        if cid and cid not in job_ids:
            err('registry', f'stations.{st}.cron_job_id={cid} 在平台快照中找不到（幽灵登记）')
    # 新导出快照对账（如果传入了 --cron-snapshot，验证库内快照是否最新）
    if snapshot:
        new_snap = json.load(open(snapshot, encoding='utf-8'))
        # 兼容两种格式：直接是列表，或带 active/stopped 字段
        if isinstance(new_snap, list):
            new_jobs = new_snap
        else:
            new_jobs = new_snap.get('active', []) + new_snap.get('stopped', [])
        new_ids = {str(j.get('id')) for j in new_jobs}
        old_ids = {str(j.get('id')) for j in jobs}
        if new_ids != old_ids:
            added = new_ids - old_ids
            removed = old_ids - new_ids
            if added:
                err('registry', f'平台新任务未在库内快照: {added}（请重新导出快照）')
            if removed:
                warn('registry', f'库内快照有任务但平台已不存在: {removed}（可能已删除，需确认）')
        # 状态对比
        new_status = {str(j.get('id')): j.get('status') for j in new_jobs}
        for j in jobs:
            jid = str(j.get('id'))
            if jid in new_status and j.get('status') != new_status[jid]:
                err('registry', f'{jid} 状态不符：库内快照={j.get("status")}，平台={new_status[jid]}（请重新导出）')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--only', choices=['crystals', 'branches', 'profiles', 'registry'])
    ap.add_argument('--cron-snapshot')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    if a.fetch:
        git('fetch', 'origin', '-q')

    runs = {
        'crystals': check_crystals,
        'branches': check_branches,
        'profiles': check_profiles,
        'registry': lambda: check_registry(a.cron_snapshot),
    }
    todo = [a.only] if a.only else list(runs)
    for name in todo:
        runs[name]()

    if a.json:
        print(json.dumps([{'level': l, 'check': c, 'msg': m}
                          for l, c, m in issues], ensure_ascii=False, indent=2))
    else:
        if not issues:
            print('✅ 网络对账通过：结晶编号/分支集成/分站档案/任务注册表均无漂移')
        for l, c, m in issues:
            mark = '❌' if l == 'ERROR' else '⚠️ '
            print(f'{mark} [{c}] {m}')
        ne = sum(1 for l, _, _ in issues if l == 'ERROR')
        nw = sum(1 for l, _, _ in issues if l == 'WARN')
        print(f'\n合计：{ne} 错误，{nw} 警告')
    sys.exit(1 if any(l == 'ERROR' for l, _, _ in issues) else 0)


if __name__ == '__main__':
    main()

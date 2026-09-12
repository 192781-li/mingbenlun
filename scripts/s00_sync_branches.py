#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
s00_sync_branches.py —— 分站分支积压自动检测与同步工具

自动检测各分站分支领先 main 的独有产出，过滤掉工作目录/Coq代码/CI产物，
列出需要同步到 main 的文件清单，支持一键同步并开 PR。

用法：
  # 只检测，列出各分站需要同步的文件（不操作）
  python3 scripts/s00_sync_branches.py

  # 实际同步所有分站的独有产出，commit 并开 PR
  python3 scripts/s00_sync_branches.py --apply

  # 只同步指定分站
  python3 scripts/s00_sync_branches.py --apply --station s01

  # 同步并自动合并（CI通过后立即merge，需pr_workflow.py）
  python3 scripts/s00_sync_branches.py --apply --auto-merge

设计原则：
  - 只同步 main 上没有的文件（不覆盖 main 已有文件，避免冲突）
  - 白名单目录自动同步（智慧河流/分站通道/哲学研究/高考数学/文科学习/术数研究等）
  - 排除目录不同步（mingben-workbench/、site/、s04_monitor_logs/、archive/等）
  - Coq .v 文件不同步（S00不碰Coq代码）
  - 基础配置文件（.github/、.gitignore、README等）默认不同步，需用户确认
"""
import argparse, os, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 分站分支映射
STATIONS = {
    's01': 's01-philosophy',
    's02': 's02-gaokao-arts',
    's03': 's03-divination',
    's04': 's04-coq',
    's05': 's05-info',
    's06': 's06-gaokao-math',
}

# 白名单：这些目录下的独有文件自动同步
WHITELIST_DIRS = [
    'docs/协作机制/智慧河流/',
    'docs/协作机制/分站通道/',
    'docs/notes/哲学研究/',
    'docs/notes/Coq形式化/S01给S04_',
    'docs/高考数学/',
    'docs/文科学习/',
    'docs/术数研究/',
    'docs/协作机制/巡检报告/',
]

# 排除目录：这些目录下的文件不同步（分站工作目录/CI产物/归档）
EXCLUDE_DIRS = [
    'mingben-workbench/',
    'site/',
    's04_monitor_logs/',
    's01_temp_docs/',
    'archive/',
    'mingbenlun_local/',
    'tools/实时留痕工具包/',
]

# 排除文件模式
EXCLUDE_PATTERNS = [
    '.v',           # Coq证明代码
    '.vo',          # Coq编译产物
    '.glob',        # Coq依赖文件
    '.aux',         # Coq辅助文件
]

# 基础配置文件：默认不同步，需用户确认（因为可能与main上的版本冲突）
CONFIG_DIRS = [
    '.github/',
    '.gitignore',
    'README.md',
    'LICENSE',
    'CONTRIBUTING.md',
    'SECURITY.md',
    'NEW_AGENT_ONBOARDING.md',
    'scripts/',
]


def git(*args, check=True):
    """运行git命令，返回stdout。"""
    cmd = ['git', '-C', REPO, '-c', 'core.quotepath=false'] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败: {r.stderr.strip()[:200]}")
    return r.stdout.strip()


def info(msg):
    print(f"[sync_branches] {msg}", flush=True)


def warn(msg):
    print(f"[sync_branches][警告] {msg}", flush=True)


def get_lead_count(branch):
    """获取某分支领先main的commit数。"""
    try:
        return int(git('rev-list', '--count', f'origin/main..origin/{branch}'))
    except Exception:
        return 0


def get_unique_files(branch):
    """获取某分支独有的文件（main上没有的，或内容不同的）。
    返回 main上不存在的文件列表（只同步新增，不覆盖已有）。
    """
    # 用git diff --name-only --diff-filter=A获取main上没有的新增文件
    # 这样不会覆盖main上已有的文件
    out = git('diff', '--name-only', '--diff-filter=A', 'origin/main', f'origin/{branch}')
    files = [f for f in out.split('\n') if f.strip()]
    return files


def should_sync(filepath):
    """判断一个文件是否应该同步到main。
    返回 (should_sync, reason)
    """
    # 检查排除模式
    for pat in EXCLUDE_PATTERNS:
        if filepath.endswith(pat):
            return False, f"排除模式 {pat}"

    # 检查排除目录
    for d in EXCLUDE_DIRS:
        if filepath.startswith(d) or f'/{d}' in filepath:
            return False, f"排除目录 {d}"

    # 检查白名单目录
    for d in WHITELIST_DIRS:
        if filepath.startswith(d):
            return True, f"白名单 {d}"

    # 检查基础配置文件
    for d in CONFIG_DIRS:
        if filepath.startswith(d):
            return False, f"基础配置（需人工确认）{d}"

    # 其他docs/下的文件：默认同步（研究产出）
    if filepath.startswith('docs/'):
        return True, "docs/研究产出"

    # 其他：默认不同步
    return False, "未分类（需人工确认）"


def analyze_station(station, branch):
    """分析一个分站的独有产出，返回需要同步的文件列表和统计。"""
    lead = get_lead_count(branch)
    if lead == 0:
        return {'lead': 0, 'unique_files': [], 'to_sync': [], 'skipped': [], 'branch': branch}

    unique_files = get_unique_files(branch)
    to_sync = []
    skipped = []

    for f in unique_files:
        sync, reason = should_sync(f)
        if sync:
            to_sync.append(f)
        else:
            skipped.append((f, reason))

    return {
        'lead': lead,
        'unique_files': unique_files,
        'to_sync': to_sync,
        'skipped': skipped,
        'branch': branch,
    }


def sync_files(station, branch, files):
    """把指定文件从分站分支checkout到main工作区。"""
    if not files:
        return 0
    # 分批checkout，避免命令行过长
    batch_size = 50
    synced = 0
    for i in range(0, len(files), batch_size):
        batch = files[i:i+batch_size]
        try:
            git('checkout', f'origin/{branch}', '--', *batch)
            synced += len(batch)
        except Exception as e:
            warn(f"checkout批次失败: {str(e)[:100]}")
            # 逐个尝试
            for f in batch:
                try:
                    git('checkout', f'origin/{branch}', '--', f)
                    synced += 1
                except Exception:
                    warn(f"  跳过: {f}")
    return synced


def create_pr(title, body):
    """创建PR。返回PR URL。"""
    # 先commit
    git('add', '-A')
    git('commit', '-m', title)
    # 建分支
    branch_name = f"s00-sync-branches-{os.popen('date +%Y%m%d-%H%M').read().strip()}"
    git('checkout', '-b', branch_name)
    git('push', '-u', 'origin', branch_name)
    # 开PR
    r = subprocess.run(
        ['gh', 'pr', 'create', '--base', 'main', '--head', branch_name,
         '--title', title, '--body', body],
        capture_output=True, text=True, cwd=REPO
    )
    if r.returncode != 0:
        raise RuntimeError(f"开PR失败: {r.stderr.strip()[:200]}")
    return r.stdout.strip(), branch_name


def merge_with_retry(branch_name, max_retries=5, max_rebase=2):
    """等CI通过后合并PR，处理时序问题和分支落后问题。
    - CI通过后等5秒再merge（GitHub状态检查同步延迟）
    - 报"status check expected"时等5秒重试，最多max_retries次
    - 报"head branch not up to date"时自动merge origin/main追平，强推，重新等CI，最多max_rebase次
    返回 True/False
    """
    import time
    rebase_count = 0

    while rebase_count <= max_rebase:
        # 等CI
        ci_passed = False
        for i in range(30):
            time.sleep(8)
            r = subprocess.run(['gh', 'pr', 'checks', branch_name],
                               capture_output=True, text=True, cwd=REPO)
            out = r.stdout
            if 'pending' not in out and 'fail' not in out and out.strip():
                ci_passed = True
                info(f"CI全过（第{i+1}次检查），等5秒同步状态检查")
                time.sleep(5)
                break
            info(f"  等CI... 第{i+1}次")

        if not ci_passed:
            warn("CI超时未通过，放弃自动合并")
            return False

        # 尝试merge，带重试
        for attempt in range(max_retries):
            r = subprocess.run(
                ['gh', 'pr', 'merge', branch_name, '--merge', '--delete-branch'],
                capture_output=True, text=True, cwd=REPO
            )
            if r.returncode == 0:
                info("合并成功！")
                return True

            err = r.stderr.strip()
            # 状态检查同步延迟：重试
            if 'status check' in err.lower() and 'expected' in err.lower():
                info(f"  状态检查同步中，等5秒重试（第{attempt+1}/{max_retries}次）")
                time.sleep(5)
                continue
            # 分支落后：追平后重新等CI
            if 'not up to date' in err.lower() or 'head branch' in err.lower():
                if rebase_count >= max_rebase:
                    warn(f"分支落后且已追平{max_rebase}次，放弃自动合并，请手动处理")
                    return False
                info(f"  分支落后于main，自动追平（第{rebase_count+1}次）...")
                git('checkout', branch_name)
                git('merge', 'origin/main', '--no-edit')
                git('push', '--force-with-lease', 'origin', branch_name)
                rebase_count += 1
                break  # 跳出merge重试循环，重新等CI
            # 其他错误
            warn(f"合并失败: {err[:150]}")
            return False
        else:
            # merge重试耗尽
            warn(f"合并重试{max_retries}次仍失败，放弃自动合并")
            return False

    return False


def main():
    ap = argparse.ArgumentParser(description='分站分支积压自动检测与同步工具')
    ap.add_argument('--apply', action='store_true', help='实际同步并开PR（默认只检测）')
    ap.add_argument('--station', help='只处理指定分站（s01/s02/s03/s04/s05/s06）')
    ap.add_argument('--auto-merge', action='store_true', help='同步后调用pr_workflow.py自动合并（需CI通过）')
    ap.add_argument('--include-config', action='store_true', help='包含基础配置文件（.github/、scripts/等，默认排除）')
    a = ap.parse_args()

    # 确定要处理的分站
    if a.station:
        if a.station not in STATIONS:
            print(f"未知分站: {a.station}，可选: {', '.join(STATIONS.keys())}")
            sys.exit(1)
        stations_to_check = [(a.station, STATIONS[a.station])]
    else:
        stations_to_check = list(STATIONS.items())

    # 如果包含基础配置，把CONFIG_DIRS从排除列表移除
    if a.include_config:
        global CONFIG_DIRS
        CONFIG_DIRS = []

    info("=== 分站分支积压检测 ===")
    print()

    all_to_sync = {}  # station -> [files]
    total_lead = 0

    for station, branch in stations_to_check:
        result = analyze_station(station, branch)
        total_lead += result['lead']

        if result['lead'] == 0:
            info(f"{station} ({branch}): 领先 0，已同步")
            continue

        info(f"{station} ({branch}): 领先 {result['lead']} commit，独有文件 {len(result['unique_files'])} 个")
        print(f"  需要同步: {len(result['to_sync'])} 个")
        for f in result['to_sync'][:10]:
            print(f"    ✓ {f}")
        if len(result['to_sync']) > 10:
            print(f"    ... 还有 {len(result['to_sync']) - 10} 个")

        print(f"  已跳过: {len(result['skipped'])} 个")
        skip_reasons = {}
        for _, reason in result['skipped']:
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
        for reason, count in sorted(skip_reasons.items(), key=lambda x: -x[1]):
            print(f"    ✗ {reason}: {count} 个")
        print()

        if result['to_sync']:
            all_to_sync[station] = result['to_sync']

    if not all_to_sync:
        info("所有分站无需同步（或领先commit为0）。完成。")
        sys.exit(0)

    total_to_sync = sum(len(f) for f in all_to_sync.values())
    info(f"合计需要同步: {total_to_sync} 个文件（来自 {len(all_to_sync)} 个分站）")

    if not a.apply:
        print()
        info("dry-run 模式，未执行同步。")
        info("加 --apply 实际同步并开PR。")
        sys.exit(0)

    # 实际同步
    print()
    info("=== 执行同步 ===")
    git('checkout', 'main')
    git('fetch', 'origin', '-q')
    git('reset', '--hard', 'origin/main')

    total_synced = 0
    for station, files in all_to_sync.items():
        branch = STATIONS[station]
        info(f"同步 {station}: {len(files)} 个文件...")
        synced = sync_files(station, branch, files)
        total_synced += synced
        info(f"  已同步 {synced}/{len(files)} 个")

    if total_synced == 0:
        warn("没有文件被同步，退出。")
        sys.exit(1)

    # 开PR
    title = f"S00: 分站分支积压同步（{', '.join(all_to_sync.keys())}，{total_synced}个文件）"
    body = f"自动同步各分站独有产出来源：\n\n"
    for station, files in all_to_sync.items():
        body += f"### {station} ({STATIONS[station]}) - {len(files)}个文件\n"
        for f in files[:20]:
            body += f"- {f}\n"
        if len(files) > 20:
            body += f"- ... 还有 {len(files) - 20} 个\n"
        body += "\n"
    body += "由 scripts/s00_sync_branches.py --apply 自动生成。"

    info(f"开PR: {title}")
    pr_url, branch_name = create_pr(title, body)
    info(f"PR已创建: {pr_url}")
    print(f"\nPR URL: {pr_url}")
    print(f"分支: {branch_name}")

    if a.auto_merge:
        info("自动合并（带时序重试和分支追平）...")
        success = merge_with_retry(branch_name)
        if not success:
            warn("自动合并未完成，请手动合并上述PR")
        # 切回main
        git('checkout', 'main')
        git('fetch', 'origin', '-q')
        git('reset', '--hard', 'origin/main')

    info("=== 完成 ===")
    info(f"同步了 {total_synced} 个文件，来自 {len(all_to_sync)} 个分站")
    info(f"当前在 main，已同步到最新: {git('rev-parse', '--short', 'HEAD')}")


if __name__ == '__main__':
    main()

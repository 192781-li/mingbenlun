#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
s05_pr.py —— S05信息分站一键PR脚本

把"rebase main → push → 开PR → 等CI → 合并"包成一条命令。
专门解决 S05 长期在 s05-info 分支工作、每次发PR都要手动rebase+等CI+合并的问题。

用法：
  # 最常用：当前在 s05-info 有未提交改动，一条命令走完
  python3 scripts/s05_pr.py --title "S05: 今日巡检+目录地图更新"

  # 已经commit了，直接发PR
  python3 scripts/s05_pr.py --title "标题"

  # 只开PR不自动合并
  python3 scripts/s05_pr.py --title "标题" --no-merge

  # 预览不执行
  python3 scripts/s05_pr.py --title "标题" --dry-run

流程：
  1. 确认在 s05-info 分支
  2. 有未提交改动则自动 commit
  3. git fetch origin main
  4. git rebase origin/main（冲突时停下来报告，不自动解决）
  5. git push --force-with-lease
  6. 开 PR（s05-info → main）
  7. 轮询 CI（每8秒查一次，最多8分钟）
  8. CI全过 → 立即 squash merge
  9. merge被挡（分支不是最新）→ 自动rebase→push→重新等CI→重试（最多3次）
  10. 成功后 git pull 同步

与 pr_workflow.py 的区别：
  - pr_workflow.py 是"从main建临时分支"模式（S00用）
  - s05_pr.py 是"长期分支"模式（S05用），直接操作 s05-info
  - rebase 代替 merge，保持线性历史，无 merge commit 噪音

安全：
  - CI 有 fail 立即停止，不 merge
  - rebase 冲突时不自动解决，停下来报冲突等人工
  - 不碰 Coq .v 文件
  - --dry-run 只打印计划不执行
"""
import argparse, datetime, os, subprocess, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANCH = "s05-info"
BASE = "main"


def run(cmd, check=True, capture=True):
    r = subprocess.run(cmd, capture_output=capture, text=True, cwd=REPO)
    if check and r.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(cmd)}\n{r.stderr.strip()[:300]}")
    return r.stdout.strip()


def git(*args, check=True):
    return run(['git', '-C', REPO, '-c', 'core.quotepath=false'] + list(args), check=check)


def gh(*args, check=True):
    return run(['gh'] + list(args), check=check)


def info(msg):
    print(f"[s05_pr] {msg}", flush=True)


def warn(msg):
    print(f"[s05_pr][警告] {msg}", flush=True)


def err(msg):
    print(f"[s05_pr][错误] {msg}", flush=True)


def get_current_branch():
    return git('branch', '--show-current')


def has_uncommitted():
    return bool(git('status', '--short').strip())


def get_ci_status(pr_number):
    out = gh('pr', 'checks', str(pr_number), check=False)
    all_pass = False
    has_fail = False
    pending = 0
    details = []
    for line in out.split('\n'):
        line = line.strip()
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 2:
            name, status = parts[0], parts[1]
            details.append(f"{name}: {status}")
            if status == 'pass':
                pass
            elif status in ('fail', 'failure', 'cancelled'):
                has_fail = True
            elif status == 'pending':
                pending += 1
    if not has_fail and pending == 0 and details:
        all_pass = True
    return all_pass, has_fail, pending, details


def wait_for_ci(pr_number, timeout_sec=480, interval=8):
    info(f"等待 CI 通过（最多 {timeout_sec//60} 分钟，每 {interval} 秒查一次）...")
    start = time.time()
    while time.time() - start < timeout_sec:
        all_pass, has_fail, pending, details = get_ci_status(pr_number)
        if has_fail:
            err(f"CI 失败！详情：{'; '.join(details)}")
            return False
        if all_pass:
            info(f"CI 全过！立即合并。详情：{'; '.join(details)}")
            return True
        elapsed = int(time.time() - start)
        info(f"  CI 运行中（{elapsed}s，pending={pending}）...")
        time.sleep(interval)
    err(f"CI 等待超时（{timeout_sec}s）")
    return False


def try_merge(pr_number):
    r = subprocess.run(
        ['gh', 'pr', 'merge', str(pr_number), '--squash', '--delete-branch'],
        capture_output=True, text=True, cwd=REPO
    )
    if r.returncode == 0:
        return 'merged', r.stdout.strip()
    stderr = r.stderr.strip()
    if 'not up to date' in stderr or 'not mergeable' in stderr:
        return 'blocked', stderr
    if 'Required status check' in stderr and 'is expected' in stderr:
        return 'retryable', stderr
    raise RuntimeError(f"merge 失败: {stderr[:300]}")


def merge_with_retry(pr_number, max_timing_retry=5):
    time.sleep(3)
    for i in range(max_timing_retry):
        status, msg = try_merge(pr_number)
        if status == 'merged':
            return 'merged', msg
        if status == 'blocked':
            return 'blocked', msg
        warn(f"merge 时序错误（第{i+1}次），等5秒重试：{msg[:80]}")
        time.sleep(5)
    return 'failed', f"时序重试{max_timing_retry}次后仍失败"


def rebase_to_latest():
    """rebase origin/main 到当前分支。返回True成功，False有冲突。"""
    info(f"rebase origin/{BASE} 到 {BRANCH}...")
    try:
        git('rebase', f'origin/{BASE}')
    except RuntimeError as e:
        if 'CONFLICT' in str(e) or 'conflict' in str(e):
            err(f"rebase 冲突！需要人工解决。")
            info("解决冲突后运行：git add <文件> && git rebase --continue")
            info("或者放弃rebase：git rebase --abort")
            return False
        raise
    info("rebase 成功，历史已线性化。")
    return True


def main():
    ap = argparse.ArgumentParser(description='S05一键PR脚本（rebase→push→PR→等CI→合并）')
    ap.add_argument('--title', required=True, help='PR标题（同时用作commit message）')
    ap.add_argument('--body', help='PR正文')
    ap.add_argument('--no-merge', action='store_true', help='只开PR不自动合并')
    ap.add_argument('--retry', type=int, default=3, help='merge被挡时自动rebase重试次数（默认3）')
    ap.add_argument('--dry-run', action='store_true', help='只打印计划不执行')
    a = ap.parse_args()

    # 检查 gh
    if subprocess.run(['which', 'gh'], capture_output=True).returncode != 0:
        err("gh CLI 不可用，请先安装并登录 gh")
        sys.exit(1)

    current = get_current_branch()
    uncommitted = has_uncommitted()

    info(f"当前分支: {current}")
    info(f"未提交改动: {'有' if uncommitted else '无'}")
    info(f"工作分支: {BRANCH} → {BASE}")
    info(f"标题: {a.title}")
    info(f"自动合并: {'否（只开PR）' if a.no_merge else '是'}")

    if current != BRANCH:
        warn(f"当前在 {current}，不是 {BRANCH}。将自动切换到 {BRANCH}。")
        git('checkout', BRANCH)

    if a.dry_run:
        info("dry-run，不执行。以上是计划。")
        sys.exit(0)

    # 1. 有未提交改动则 commit
    if uncommitted:
        info("有未提交改动，自动 commit...")
        git('add', '-A')
        git('commit', '-m', a.title)
        info("commit 完成。")

    # 2. fetch + rebase
    info(f"fetch origin/{BASE}...")
    git('fetch', 'origin', BASE)

    if not rebase_to_latest():
        err("rebase 冲突，停止。请人工解决后重新运行。")
        sys.exit(1)

    # 3. push（rebase后需要force-with-lease）
    info(f"push {BRANCH}（force-with-lease）...")
    git('push', '--force-with-lease', 'origin', BRANCH)

    # 4. 开 PR
    body = a.body or f"自动生成的 PR。\n\n标题：{a.title}\n由 scripts/s05_pr.py 自动创建。"
    info("创建 PR...")
    pr_url = gh('pr', 'create', '--base', BASE, '--head', BRANCH,
                '--title', a.title, '--body', body)
    pr_number = pr_url.rstrip('/').split('/')[-1]
    info(f"PR 已创建: {pr_url} (#{pr_number})")

    if a.no_merge:
        info("--no-merge，只开 PR 不自动合并。完成。")
        print(f"\nPR URL: {pr_url}")
        sys.exit(0)

    # 5. 轮询 CI + 合并（带重试）
    for attempt in range(1, a.retry + 1):
        info(f"=== 第 {attempt}/{a.retry} 次尝试 ===")

        if not wait_for_ci(pr_number):
            err("CI 未通过，停止。请查看 PR 页面修复。")
            print(f"\nPR URL: {pr_url}")
            sys.exit(1)

        status, msg = merge_with_retry(pr_number)
        if status == 'merged':
            info("合并成功！")
            break
        elif status == 'blocked':
            warn(f"merge 被挡（分支不是最新）。{msg[:100]}")
            if attempt < a.retry:
                git('fetch', 'origin', BASE)
                if not rebase_to_latest():
                    err("rebase 冲突，停止。请人工解决。")
                    print(f"\nPR URL: {pr_url}")
                    sys.exit(1)
                git('push', '--force-with-lease', 'origin', BRANCH)
                info("重新等待 CI...")
                continue
            else:
                err(f"重试 {a.retry} 次后仍被挡，停止。请人工处理。")
                print(f"\nPR URL: {pr_url}")
                sys.exit(1)
        else:
            err(f"merge 失败：{msg[:100]}")
            print(f"\nPR URL: {pr_url}")
            sys.exit(1)
    else:
        err("未成功合并。")
        sys.exit(1)

    # 6. 同步本地
    info("同步本地到最新...")
    git('fetch', 'origin')
    git('reset', '--hard', f'origin/{BRANCH}')

    info("=== 完成 ===")
    info(f"PR #{pr_number} 已合并到 {BASE}")
    info(f"当前在 {BRANCH}，已同步到最新")
    print(f"\nPR URL: {pr_url}")
    print(f"合并后 HEAD: {git('rev-parse', '--short', 'HEAD')}")


if __name__ == '__main__':
    main()

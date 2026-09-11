#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pr_workflow.py —— PR 半自动化工作流

把"建分支→push→开PR→等CI→合并"包成一条命令。CI 一通过就立即合并，
专门解决 dependabot 等其他提交抢在前面导致"分支不是最新"的问题。

用法：
  # 最常用：当前在 main 有未提交改动，一条命令走完
  python3 scripts/pr_workflow.py --title "S00: 修复xxx"

  # 指定分支名和正文
  python3 scripts/pr_workflow.py --title "标题" --branch my-feature --body "正文"

  # 只开PR不自动合并（等人工review）
  python3 scripts/pr_workflow.py --title "标题" --no-merge

  # 当前已经在特性分支上且已commit，直接开PR+等CI+合并
  python3 scripts/pr_workflow.py --title "标题"

流程：
  1. 检查 gh 可用、在 git 仓库
  2. 有未提交改动则自动 commit（用 --title 作为 commit message）
  3. 基于当前 HEAD 创建 PR 分支（如果当前在 main）
  4. push 分支
  5. gh pr create 开 PR
  6. 轮询 CI（每 8 秒查一次，最多等 8 分钟）
  7. CI 全过 → 立即 merge（--merge --delete-branch）
  8. 如果 merge 被挡（分支不是最新）→ 自动 merge origin/<base> 到 PR 分支
     → 重新 push → 重新等 CI → 重试（默认最多 3 次）
  9. 成功后切回 base，pull，删除本地 PR 分支
  10. 输出 PR URL 和最终结果

安全：
  - CI 有 fail 立即停止，不 merge
  - merge 冲突时不自动解决，停下来报冲突等人工
  - 不碰 Coq .v、不碰哲学研判（内容层面脚本不管）
  - --dry-run 只打印计划不执行
"""
import argparse, datetime, os, subprocess, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd, check=True, capture=True):
    """运行命令，返回 stdout。check=False 时不抛异常。"""
    r = subprocess.run(cmd, capture_output=capture, text=True, cwd=REPO)
    if check and r.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(cmd)}\n{r.stderr.strip()[:300]}")
    return r.stdout.strip()


def git(*args, check=True):
    return run(['git', '-C', REPO, '-c', 'core.quotepath=false'] + list(args), check=check)


def gh(*args, check=True):
    return run(['gh'] + list(args), check=check)


def info(msg):
    print(f"[pr_workflow] {msg}", flush=True)


def warn(msg):
    print(f"[pr_workflow][警告] {msg}", flush=True)


def err(msg):
    print(f"[pr_workflow][错误] {msg}", flush=True)


def get_current_branch():
    return git('branch', '--show-current')


def has_uncommitted():
    return bool(git('status', '--short').strip())


def get_ci_status(pr_number):
    """返回 (all_pass, has_fail, pending_count, details)"""
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
    """轮询CI，返回True=全过，False=失败或超时"""
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
    """尝试merge，返回True成功，False被挡（分支不是最新）"""
    r = subprocess.run(
        ['gh', 'pr', 'merge', str(pr_number), '--merge', '--delete-branch'],
        capture_output=True, text=True, cwd=REPO
    )
    if r.returncode == 0:
        return True, r.stdout.strip()
    stderr = r.stderr.strip()
    if 'not up to date' in stderr or 'not mergeable' in stderr:
        return False, stderr
    # 其他错误
    raise RuntimeError(f"merge 失败: {stderr[:300]}")


def rebase_to_latest(branch, base):
    """把 origin/<base> merge 到 PR 分支，然后push。返回True成功。"""
    info(f"合并 origin/{base} 到 {branch} 以追平最新...")
    try:
        git('checkout', branch)
        git('merge', f'origin/{base}', '--no-edit')
    except RuntimeError as e:
        if 'CONFLICT' in str(e) or 'conflict' in str(e):
            err(f"合并冲突！需要人工解决。错误：{str(e)[:200]}")
            return False
        raise
    git('push', '--force-with-lease', 'origin', branch)
    info("已追平最新并重新 push。")
    return True


def main():
    ap = argparse.ArgumentParser(description='PR 半自动化工作流')
    ap.add_argument('--title', required=True, help='PR 标题（同时用作 commit message）')
    ap.add_argument('--branch', help='PR 分支名（默认自动生成 s00-pr-YYYYMMDD-HHMM）')
    ap.add_argument('--body', help='PR 正文（默认从 commit message 生成）')
    ap.add_argument('--base', default='main', help='基础分支（默认 main）')
    ap.add_argument('--no-merge', action='store_true', help='只开 PR 不自动合并')
    ap.add_argument('--retry', type=int, default=3, help='merge 被挡时自动追平重试次数（默认 3）')
    ap.add_argument('--dry-run', action='store_true', help='只打印计划不执行')
    a = ap.parse_args()

    # 检查 gh
    if subprocess.run(['which', 'gh'], capture_output=True).returncode != 0:
        err("gh CLI 不可用，请先安装并登录 gh")
        sys.exit(1)

    current = get_current_branch()
    uncommitted = has_uncommitted()

    # 生成分支名
    branch = a.branch or f"s00-pr-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}"

    info(f"当前分支: {current}")
    info(f"未提交改动: {'有' if uncommitted else '无'}")
    info(f"PR 分支: {branch}")
    info(f"基础分支: {a.base}")
    info(f"标题: {a.title}")
    info(f"自动合并: {'否（只开PR）' if a.no_merge else '是'}")

    if a.dry_run:
        info("dry-run，不执行。以上是计划。")
        sys.exit(0)

    # 1. 有未提交改动则 commit
    if uncommitted:
        info("有未提交改动，自动 commit...")
        git('add', '-A')
        git('commit', '-m', a.title)
        info("commit 完成。")

    # 2. 创建分支（如果当前在 base）
    if current == a.base:
        info(f"基于 {a.base} 创建分支 {branch}...")
        git('checkout', '-b', branch)
    elif current != branch:
        warn(f"当前在 {current}，不是 {a.base} 也不是 {branch}。将直接使用当前分支 {current} 开 PR。")
        branch = current

    # 3. push
    info(f"push 分支 {branch}...")
    git('push', '-u', 'origin', branch)

    # 4. 开 PR
    body = a.body or f"自动生成的 PR。\n\n标题：{a.title}\n由 scripts/pr_workflow.py 自动创建。"
    info("创建 PR...")
    pr_url = gh('pr', 'create', '--base', a.base, '--head', branch,
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

        # 等 CI
        if not wait_for_ci(pr_number):
            err("CI 未通过，停止。请查看 PR 页面修复。")
            print(f"\nPR URL: {pr_url}")
            sys.exit(1)

        # 尝试 merge
        merged, msg = try_merge(pr_number)
        if merged:
            info("合并成功！")
            break
        else:
            warn(f"merge 被挡（分支不是最新）。{msg[:100]}")
            if attempt < a.retry:
                if not rebase_to_latest(branch, a.base):
                    err("追平最新时遇到冲突，停止。请人工解决后重新合并。")
                    print(f"\nPR URL: {pr_url}")
                    sys.exit(1)
                info("重新等待 CI...")
                continue
            else:
                err(f"重试 {a.retry} 次后仍被挡，停止。请人工处理。")
                print(f"\nPR URL: {pr_url}")
                sys.exit(1)
    else:
        err("未成功合并。")
        sys.exit(1)

    # 6. 切回 base，pull，清理本地分支
    info("切回 base 并同步...")
    git('checkout', a.base)
    git('fetch', 'origin')
    git('reset', '--hard', f'origin/{a.base}')

    # 删除本地 PR 分支（如果存在且不是当前分支）
    if branch != a.base:
        git('branch', '-D', branch, check=False)

    info("=== 完成 ===")
    info(f"PR #{pr_number} 已合并到 {a.base}")
    info(f"当前在 {a.base}，已同步到最新")
    print(f"\nPR URL: {pr_url}")
    print(f"合并后 HEAD: {git('rev-parse', '--short', 'HEAD')}")


if __name__ == '__main__':
    main()

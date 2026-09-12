#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pr_health.py —— 开放 PR 体检（只读，不改任何东西）

S00 合门人决策工具。对每个 open PR 机械算出：
  - behind/ahead：相对 origin/main 落后/领先多少提交
  - ahead==0 即"内容已全部在 main"——重复空 PR，建议直接关闭（#86 那类）
  - behind>0 且 ahead>0——过期，需追平后再合（#75 那类，用 pr_workflow.py --integrate）
  - CI pass/fail/pending 计数
并给出一个机械标签，替代人眼逐个翻 PR 页面。

用法：
  python3 scripts/pr_health.py              # 体检全部 open PR，打印表格
  python3 scripts/pr_health.py --json       # 输出 JSON
  python3 scripts/pr_health.py --fetch      # 先 git fetch origin（默认也会 fetch 一次）

退出码：0 正常；2 没有 open PR；3 gh 不可用。
"""
import argparse, json, subprocess, sys

REPO = __file__.rsplit('/', 1)[0].rsplit('/', 1)[0]


def run(cmd, check=True):
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} 失败: {r.stderr.strip()[:200]}")
    return r.stdout.strip()


def gh_available():
    return subprocess.run(['which', 'gh'], capture_output=True).returncode == 0


def list_open_prs():
    out = run(['gh', 'pr', 'list', '--state', 'open', '--json',
               'number,title,headRefName,baseRefName,mergeable,url'])
    return json.loads(out) if out else []


def behind_ahead(head, base='main'):
    """返回 (behind, ahead)：PR 落后 base 数 / PR 独有提交数。取不到返回 (None,None)。
    本仓库 remote.origin.fetch 只跟踪 main，其他分支不建 origin/<head>，故 head 用 FETCH_HEAD。"""
    try:
        run(['git', 'fetch', 'origin'], check=False)          # 更新 origin/<base>（只抓 main）
        run(['git', 'fetch', 'origin', head], check=False)    # 远程 head 落到 FETCH_HEAD
        line = run(['git', 'rev-list', '--left-right', '--count',
                    f'origin/{base}...FETCH_HEAD'])
        b, a = line.split()
        return int(b), int(a)
    except Exception:
        return None, None


def ci_summary(number):
    """统计某 PR 的 CI：返回 (pass, fail, pending, 原始状态列表)。"""
    r = subprocess.run(['gh', 'pr', 'checks', str(number)], cwd=REPO,
                       capture_output=True, text=True)
    p = f = q = 0
    rows = []
    for ln in r.stdout.splitlines():
        cols = ln.split('\t')
        if len(cols) < 2:
            continue
        st = cols[1].strip().lower()
        rows.append(st)
        if st == 'pass':
            p += 1
        elif st in ('fail', 'failure'):
            f += 1
        else:
            q += 1
    return p, f, q, rows


def classify(ahead, behind, ci_fail, ci_pending):
    if ahead == 0:
        return '重复空PR·内容已在main·建议关闭'
    if ci_fail:
        return 'CI失败·待修复'
    if behind and behind > 0:
        if ci_pending:
            return '过期且CI在跑·追平后重判'
        return '过期·需 --integrate 追平再合'
    if ci_pending:
        return '最新·CI在跑·等绿'
    return '最新且CI绿·可直接合'


def main():
    ap = argparse.ArgumentParser(description='开放 PR 体检（只读）')
    ap.add_argument('--json', action='store_true', help='输出 JSON')
    ap.add_argument('--base', default='main', help='对比基线，默认 main')
    a = ap.parse_args()

    if not gh_available():
        print('gh CLI 不可用，无法读取 PR。', file=sys.stderr)
        sys.exit(3)

    run(['git', 'fetch', 'origin'], check=False)
    prs = list_open_prs()
    if not prs:
        print('当前没有 open PR。')
        sys.exit(2)

    records = []
    for pr in sorted(prs, key=lambda x: x['number']):
        n = pr['number']
        head = pr.get('headRefName', '')
        behind, ahead = behind_ahead(head, a.base)
        cp, cf, cq, _ = ci_summary(n)
        tag = classify(ahead, behind, cf, cq) if ahead is not None else '分支对比失败·需人工'
        records.append({
            'number': n, 'title': pr.get('title', ''), 'head': head,
            'base': pr.get('baseRefName', a.base), 'behind': behind, 'ahead': ahead,
            'ci_pass': cp, 'ci_fail': cf, 'ci_pending': cq,
            'mergeable': pr.get('mergeable'), 'tag': tag, 'url': pr.get('url', ''),
        })

    if a.json:
        print(json.dumps(records, ensure_ascii=False, indent=2))
        return

    print(f"开放 PR 共 {len(records)} 个（基线 {a.base}）")
    print('=' * 88)
    for r in records:
        ba = f"behind {r['behind']}/ahead {r['ahead']}" if r['ahead'] is not None else '对比失败'
        ci = f"CI √{r['ci_pass']} ×{r['ci_fail']} …{r['ci_pending']}"
        print(f"#{r['number']}  [{r['head']} → {r['base']}]  {ba}；{ci}")
        print(f"    {r['title'][:60]}")
        print(f"    判定：{r['tag']}")
        print(f"    {r['url']}")
        print('-' * 88)
    # 汇总提示
    dup = [r['number'] for r in records if r['ahead'] == 0]
    stale = [r['number'] for r in records if r['ahead'] and r['behind']]
    if dup:
        print(f"重复空 PR（建议关闭）：{dup}")
    if stale:
        print(f"过期需追平（python3 scripts/pr_workflow.py --integrate <号>）：{stale}")


if __name__ == '__main__':
    main()

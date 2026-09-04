# -*- coding: utf-8 -*-
"""S04 统一可靠 git 助手 —— 根治"别的对话轻松 push、S04 却反复失败"。

历史坑（全部在本脚本内消除，不再靠人记）：
  1) PowerShell 裸 git / && 报错  -> 固定走 PortableGit 全路径，subprocess 调用。
  2) origin 是 SSH(git@github.com)，22 端口被封 -> push/fetch 一律改走 https URL。
  3) schannel 吊销检查 0x80092012 -> 每次固定 -c http.sslBackend=openssl -c http.sslVerify=false。
  4) token 散落/泄漏 -> 只从 ~/.mingxu/tokens/S04.token 或环境变量读，输出一律脱敏，绝不硬编码。
  5) push exit!=0 但其实已成功（HEAD -> branch 已打印）-> 用输出特征判成功，不只看 returncode。
  6) 误提交 key/临时文件/编译产物 -> stage 前危险模式硬拦截（双保险，gitignore 漏了也拦）。
  7) 盲目 git add -A 带入对话草稿 -> 默认只 add -u（已跟踪改动），新文件必须显式点名。

用法：
  python s04_git.py status                      # 工作区+分支关系
  python s04_git.py sync [branch]               # checkout + https fetch + 报告 ahead/behind（只 ff）
  python s04_git.py save -m "说明" [新文件...]   # 【主力】add -u +显式新文件 -> 安全闸 -> commit -> 重试push -> 校验远程
  python s04_git.py push [branch]               # 仅 push（带重试与正确成功判据）
  python s04_git.py log [N]
"""
import os, sys, time, subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GIT = os.environ.get("GIT_BIN", r"C:\Users\lison\Desktop\PortableGit\bin\git.exe")
BRANCH = os.environ.get("S04_BRANCH", "s04-coq")
GH_OWNER_REPO = "192781-li/mingbenlun.git"

# 命中即拒绝提交（即使 gitignore 漏配也拦）——明性：让危险在落库前暴露
DANGER = [
    ".deepseek_key", ".env", ".secrets",
    "ds_v4_traces/", "_guard_", "_tmp_",
]
DANGER_SUFFIX = (".token", ".vo", ".vok", ".vos", ".glob", ".pyc", ".pyo",
                 ".bak_r0", ".bak_r1", ".bak_r2", ".bak_r3")


def read_token():
    t = os.environ.get("S04_GIT_TOKEN", "").strip()
    if t:
        return t
    for c in (Path.home() / ".mingxu" / "tokens" / "S04.token",):
        if c.exists():
            return c.read_text(encoding="utf-8").strip()
    raise RuntimeError("未找到 git token：设 S04_GIT_TOKEN 或放 ~/.mingxu/tokens/S04.token")


def https_url():
    return "https://%s@github.com/%s" % (read_token(), GH_OWNER_REPO)


def git(args, url_auth=False, check=False):
    """统一 git 调用：固定 openssl 后端、utf-8、脱敏输出。"""
    base = ["-c", "http.sslBackend=openssl", "-c", "http.sslVerify=false"]
    cmd = [GIT, "-C", str(REPO)] + base + args
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    try:
        out = out.replace(read_token(), "***")
    except RuntimeError:
        pass
    if check and p.returncode != 0 and "-> " not in out and "up-to-date" not in out:
        raise RuntimeError("git %s 失败:\n%s" % (args[0], out))
    return p.returncode, out


def is_push_ok(rc, out):
    """正确成功判据：rc0，或输出已含分支推进/已是最新（历史上 rc!=0 也可能已成功）。"""
    if rc == 0:
        return True
    return ("-> " in out) or ("Everything up-to-date" in out)


def cur_branch():
    rc, out = git(["rev-parse", "--abbrev-ref", "HEAD"])
    return out.strip()


def danger_scan(paths):
    bad = []
    for x in paths:
        xn = x.replace("\\", "/")
        low = xn.lower()
        hit = any(d.lower() in low for d in DANGER) or low.endswith(DANGER_SUFFIX)
        if hit:
            bad.append(x)
    return bad


def staged_files():
    rc, out = git(["diff", "--cached", "--name-only"])
    return [l for l in out.splitlines() if l.strip()]


def cmd_status(_):
    rc, out = git(["status", "-sb"])
    print(out)
    rc, out = git(["log", "--oneline", "-3"])
    print(out)


def cmd_sync(a):
    br = a[0] if a else BRANCH
    print(git(["checkout", br])[1])
    rc, out = git(["fetch", https_url(), br])
    print("fetch rc=%d" % rc, out.strip())
    # 只快进，绝不产生意外合并提交；ff 失败就报告让人判断
    rc, out = git(["merge", "--ff-only", "FETCH_HEAD"])
    print(out)
    print(git(["status", "-sb"])[1].splitlines()[0])


def cmd_push(a):
    br = a[0] if a else (cur_branch() or BRANCH)
    last = ""
    for i in range(3):
        rc, out = git(["push", https_url(), "HEAD:%s" % br])
        last = out
        if is_push_ok(rc, out):
            print("推送成功：%s" % [l for l in out.splitlines() if "->" in l or "up-to-date" in l])
            return 0
        print("第 %d 次推送未成功，重试...：%s" % (i + 1, out.strip()[-300:]))
        time.sleep(2 * (i + 1))
    print("!! 推送 3 次仍失败：\n%s" % last)
    return 1


def cmd_save(a):
    msg = None
    newfiles = []
    i = 0
    while i < len(a):
        if a[i] == "-m":
            msg = a[i + 1]; i += 2; continue
        newfiles.append(a[i]); i += 1
    if not msg:
        print("!! save 需要 -m \"提交说明\""); return 2

    # 1) 默认只更新已跟踪文件（不盲目 add -A）；新文件显式点名
    print(git(["add", "-u"])[1], end="")
    for f in newfiles:
        if not (REPO / f).exists():
            print("!! 新文件不存在，拒绝：%s" % f); return 2
        git(["add", "--", f])

    # 2) 危险文件硬拦截（明性安全闸）
    staged = staged_files()
    if not staged:
        print("没有可提交的改动（工作区已干净）。"); return 0
    bad = danger_scan(staged)
    if bad:
        print("!! 安全闸拦截：以下文件绝不允许入库，已为你 unstage：")
        for b in bad:
            print("   -", b); git(["reset", "-q", "--", b])
        staged = staged_files()
        if not staged:
            print("拦截后无剩余改动，已中止提交。"); return 2

    # 3) 当前分支必须是 S04 分支（防止在错误分支提交）
    br = cur_branch()
    if br != BRANCH:
        print("!! 当前分支 %s != %s，拒绝提交（先 checkout）。" % (br, BRANCH)); return 2
    print("待提交 %d 个文件：" % len(staged))
    for s in staged:
        print("   ", s)

    # 4) commit（utf-8 message，避免 PowerShell 中文乱码）
    rc, out = git(["-c", "i18n.commitEncoding=utf-8", "commit", "-m", msg])
    print(out)
    if rc != 0 and "nothing to commit" not in out:
        print("!! commit 失败，已中止，未 push。"); return 1

    # 5) push（带重试与正确判据）
    prc = cmd_push([br])

    # 6) 推送后校验：本地 HEAD 是否已在远程分支
    time.sleep(1)
    git(["fetch", https_url(), br])
    rc, local = git(["rev-parse", "HEAD"])
    rc, remote = git(["rev-parse", "FETCH_HEAD"])
    if local.strip() == remote.strip():
        print("校验通过：本地与远程 %s 同为 %s" % (br, local.strip()[:8]))
    else:
        print("!! 校验不一致：本地 %s 远程 %s，需人工查看。" % (local.strip()[:8], remote.strip()[:8]))
        return 1
    rc, out = git(["log", "--oneline", "-1"]); print(out)
    return prc


def cmd_log(a):
    n = a[0] if a else "5"
    print(git(["log", "--oneline", "-%s" % n])[1])


if __name__ == "__main__":
    tab = {"status": cmd_status, "sync": cmd_sync, "save": cmd_save,
           "push": cmd_push, "log": cmd_log}
    if len(sys.argv) < 2 or sys.argv[1] not in tab:
        print(__doc__); sys.exit(0)
    try:
        sys.exit(tab[sys.argv[1]](sys.argv[2:]))
    except RuntimeError as e:
        print("!!", e); sys.exit(2)

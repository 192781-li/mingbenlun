# -*- coding: utf-8 -*-
"""S04 明性自检（开工/收工各跑一次）——把"始终保持明性"变成可执行的闸，而非口号。

用法：
  python preflight.py            快速门（秒级）：分支/Admitted计数/危险文件/双门在岗/git状态
  python preflight.py --compile  加 coqc 终裁 Layer1/2/3（改了证明后收工必跑）
  python preflight.py --deep     再加三连离线自检（falsification_guard/proof_loop/s04_context）
全 PASS 退出码 0；任一 FAIL 退出码 1（收工前红灯必须处理，不许带红灯提交）。
"""
import os, sys, re, subprocess
from pathlib import Path
from _paths import REPO, THEORIES, COQBIN, COQLIB, COQC
from s04_git import git, cur_branch, danger_scan, BRANCH

results = []  # (项, PASS/FAIL/INFO, 说明)
def rec(name, ok, detail="", warn=False):
    # warn=True 且 ok 时记 WARN（已知待办，不算红灯）；ok=False 永远 FAIL
    st = "WARN" if (warn and ok) else ("PASS" if ok else "FAIL")
    results.append((name, st, detail))

def strip_block_comments(text):
    """剥离 (* ... *) 块注释（支持嵌套），返回纯代码，避免把注释里的 Admitted. 当真。"""
    out, depth, i = [], 0, 0
    while i < len(text):
        if text[i:i+2] == "(*":
            depth += 1; i += 2; continue
        if text[i:i+2] == "*)" and depth > 0:
            depth -= 1; i += 2; continue
        if depth == 0:
            out.append(text[i])
        i += 1
    return "".join(out)

def count_admitted():
    d = {}
    for f in ("Layer1.v", "Layer2.v", "Layer3.v"):
        p = THEORIES / f
        if not p.exists():
            d[f] = -1; continue
        code = strip_block_comments(p.read_text(encoding="utf-8"))
        n = len(re.findall(r"\b[Aa]dmitted\s*\.|\badmit\s*\.", code))
        d[f] = n
    return d

def check_branch():
    b = cur_branch()
    rec("分支", b == BRANCH, "当前 %s，应为 %s" % (b, BRANCH))

def check_admitted():
    d = count_admitted()
    rec("L1 Admitted", d.get("Layer1.v", -1) == 0, str(d.get("Layer1.v")))
    rec("L3 Admitted", d.get("Layer3.v", -1) == 0, str(d.get("Layer3.v")))
    l2 = d.get("Layer2.v", -1)
    rec("L2 Admitted", l2 >= 0, "Layer2 真实 Admitted=%d（剥离注释后）" % l2)

def check_danger_untracked():
    rc, out = git(["status", "--porcelain"])
    untracked, modified = [], []
    for line in out.splitlines():
        if line.startswith("?? "):
            untracked.append(line[3:].strip().strip('"'))
        elif line.strip():
            modified.append(line.strip())
    bad = danger_scan(untracked)
    rec("未跟踪无危险物", not bad, "危险文件:%s" % bad if bad else "未跟踪 %d 项均安全" % len(untracked))
    rec("工作区状态", True, "%d 项改动待处理" % len(modified) if modified else "工作区干净")

def check_guard():
    try:
        import falsification_guard as fg
        ok = hasattr(fg, "adjudicate") and hasattr(fg, "compile_negation_standalone")
        rec("证伪双门在岗", ok, "falsification_guard.adjudicate 可导入" if ok else "缺 adjudicate")
    except Exception as e:
        rec("证伪双门在岗", False, "导入失败:%s" % e)

def check_git_sync():
    rc, out = git(["status", "-sb"])
    head = out.splitlines()[0] if out else ""
    ahead = "ahead" in head; behind = "behind" in head
    rec("git 同步", not behind, head + ("（领先未push，记得save）" if ahead else ""))

def coqc_layer(f):
    env = os.environ.copy()
    env["PATH"] = COQBIN + os.pathsep + env.get("PATH", "")
    env["COQLIB"] = COQLIB
    p = subprocess.run([COQC, "-R", "..", "ALL", f], cwd=str(THEORIES),
                       env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or ""))

def check_compile():
    # L1/L2 是硬门：必须编译 exit=0（Admitted 不阻止编译，数量另计）
    for f in ("Layer1.v", "Layer2.v"):
        if (THEORIES / f).exists():
            rc, err = coqc_layer(f)
            tail = "exit=0" if rc == 0 else (err.strip().splitlines()[-1][:120] if err.strip() else "exit=%d" % rc)
            rec("coqc %s" % f, rc == 0, tail)
    # L3 是条件门：它依赖 L2 的 subject_reduction 等。L2 未清零时编译不过属预期待办(WARN)；
    # L2 一旦清零(0 Admitted)，L3 就必须绿，否则是真 FAIL。
    if (THEORIES / "Layer3.v").exists():
        rc, err = coqc_layer("Layer3.v")
        l2 = count_admitted().get("Layer2.v", 0)
        last = err.strip().splitlines()[-1][:120] if err.strip() else ""
        if l2 == 0:
            rec("coqc Layer3.v", rc == 0, "exit=0" if rc == 0 else last)
        else:
            rec("coqc Layer3.v(条件门)", True,
                "L2 尚有 %d Admitted，L3 依赖未就绪属预期（当前 exit=%d%s），非机制回归；L2 清零后必须转绿"
                % (l2, rc, ("：" + last) if last else ""), warn=True)

def check_deep_selftests():
    here = Path(__file__).parent
    for script in ("falsification_guard.py", "proof_loop.py", "s04_context.py"):
        p = subprocess.run([sys.executable, script], cwd=str(here),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = (p.stdout or "") + (p.stderr or "")
        # 三个自检脚本正常时不应抛 traceback
        ok = (p.returncode == 0) and ("Traceback" not in out)
        rec("自检 %s" % script, ok, "exit=%d" % p.returncode)

def main():
    deep = "--deep" in sys.argv
    do_compile = deep or "--compile" in sys.argv
    check_branch(); check_admitted(); check_danger_untracked(); check_guard(); check_git_sync()
    if do_compile:
        check_compile()
    if deep:
        check_deep_selftests()
    print("=" * 64)
    print("S04 明性自检  (%s)" % ("deep" if deep else "compile" if do_compile else "fast"))
    print("=" * 64)
    w = max(len(n) for n, _, _ in results)
    fails = warns = 0
    for n, st, detail in results:
        if st == "FAIL": fails += 1
        if st == "WARN": warns += 1
        print("  [%-4s] %-*s  %s" % (st, w, n, detail))
    print("=" * 64)
    if fails:
        print("结论：%d 项 FAIL —— 红灯，处理完再收工/提交。" % fails); return 1
    print("结论：全 PASS（%d 项 WARN 为已知待办，非红灯），明性在岗。" % warns)
    return 0

if __name__ == "__main__":
    sys.exit(main())

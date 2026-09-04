# -*- coding: utf-8 -*-
"""S04 L2收官看板状态机——自动流程"看板取活、完工回填、绑定真值"，杜绝凭记忆/重启空转。

用法：
  python board.py next            # 按依赖给出当前唯一该做的工序（没有则明确说"无可做"，不空转烧DS）
  python board.py status          # 打印所有工序状态/依赖/轮次预算
  python board.py start J1        # 标记某工序 in_progress
  python board.py done J1 [备注]  # 标记完成并回填（配合 coqc 已 Qed 才允许）
  python board.py block J1 原因   # 标记阻塞
  python board.py check           # 看板 baseline 与 Layer 文件真实 Admitted 一致性（绑定 coqc 真值）

铁律：只有 coqc 真实 Qed（preflight 可见）才能 done；done 立即写盘固化，下一轮绝不从 r1 空转。
"""
import io, json, sys, re, datetime
from pathlib import Path
from _paths import REPO, THEORIES

BOARD = REPO / "docs" / "协作机制" / "明旭的记忆" / "S04_L2收官工序看板.json"


def load():
    return json.loads(BOARD.read_text(encoding="utf-8"))


def save(d):
    tmp = BOARD.with_suffix(".json.tmp")
    io.open(tmp, "w", encoding="utf-8", newline="\n").write(
        json.dumps(d, ensure_ascii=False, indent=2))
    tmp.replace(BOARD)


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def status_of(d, jid):
    for j in d["jobs"]:
        if j["id"] == jid:
            return j["status"]
    return None


def deps_ready(d, j):
    return all(status_of(d, dep) == "done" for dep in j.get("depends", []))


def strip_comments(t):
    out, depth, i = [], 0, 0
    while i < len(t):
        if t[i:i+2] == "(*":
            depth += 1; i += 2; continue
        if t[i:i+2] == "*)" and depth > 0:
            depth -= 1; i += 2; continue
        if depth == 0:
            out.append(t[i])
        i += 1
    return "".join(out)


def real_admitted(fname):
    p = THEORIES / fname
    if not p.exists():
        return None
    code = strip_comments(p.read_text(encoding="utf-8"))
    return len(re.findall(r"\b[Aa]dmitted\s*\.", code))


def cmd_next(_):
    d = load()
    todo = [j for j in d["jobs"] if j["status"] in ("pending", "in_progress", "blocked")]
    # in_progress 优先（续做，不另开）
    prog = [j for j in todo if j["status"] == "in_progress"]
    cand = prog or [j for j in todo if j["status"] == "pending" and deps_ready(d, j)]
    blocked = [j for j in todo if j["status"] == "blocked"]
    if not cand:
        undone = [j["id"] for j in todo]
        if not undone:
            print("看板全部 done：L2 已清零、L3 已转绿，收官完成。")
            return 0
        wait = [(j["id"], j["depends"]) for j in todo if j["status"] == "pending" and not deps_ready(d, j)]
        print("当前无可立即开工工序（不空转、不烧 DS）。")
        for jid, dep in wait:
            print("  等待依赖：%s <- %s" % (jid, dep))
        for j in blocked:
            print("  阻塞中：%s %s" % (j["id"], j.get("note", "")))
        return 0
    j = cand[0]
    print("== 当前工序 %s：%s ==" % (j["id"], j["name"]))
    print("target :", j["target"])
    print("owner  :", j["owner"])
    print("depends:", j.get("depends", []) or "无", "| 已就位" if deps_ready(d, j) else "")
    print("DS轮次预算:", j.get("ds_round_budget"))
    print("质量门 :", j.get("gate"))
    if j.get("already_have"):
        print("已有资产:", j["already_have"])
    if j.get("brief_hint"):
        print("打法提示:", j["brief_hint"])
    return 0


def cmd_status(_):
    d = load()
    print("看板状态 @", d.get("updated"), "|", d.get("status"))
    for j in d["jobs"]:
        mark = {"done": "✓", "in_progress": "▶", "blocked": "✗", "pending": "·"}.get(j["status"], "?")
        print("  %s %-3s %-28s %-12s 轮次预算%s %s" % (
            mark, j["id"], j["name"], j["status"], j.get("ds_round_budget", ""),
            ("| " + j["note"]) if j.get("note") else ""))
    done = sum(1 for j in d["jobs"] if j["status"] == "done")
    print("进度：%d/%d 工序完成" % (done, len(d["jobs"])))


def cmd_set(kind, args):
    if not args:
        print("需要工序号，如 J1"); return 2
    jid = args[0]; note = " ".join(args[1:])
    d = load()
    for j in d["jobs"]:
        if j["id"] == jid:
            if kind == "done":
                # done 前绑定真值：J1 要求 Layer2 admitted 下降；J5 要求 L3 0 问题——这里只做提示，硬裁由 preflight
                j["status"] = "done"; j["finished_at"] = now()
                if note:
                    j["note"] = note
                j.setdefault("history", []).append({"at": now(), "to": "done", "note": note})
                save(d); print("%s -> done（%s），已固化，下一轮不再重做。" % (jid, now())); return 0
            j["status"] = {"start": "in_progress", "block": "blocked"}[kind]
            j.setdefault("history", []).append({"at": now(), "to": j["status"], "note": note})
            if note:
                j["note"] = note
            save(d); print("%s -> %s %s" % (jid, j["status"], note)); return 0
    print("未找到工序", jid); return 2


def cmd_check(_):
    d = load()
    base = d["current_baseline"]
    ok = True
    for layer, fname in (("Layer1", "Layer1.v"), ("Layer2", "Layer2.v"), ("Layer3", "Layer3.v")):
        real = real_admitted(fname)
        claimed = base.get(layer, {}).get("admitted")
        match = (real == claimed)
        ok &= match
        print("  %s 看板claimed Admitted=%s  实际剥离注释=%s  %s" % (
            layer, claimed, real, "一致" if match else "!!不一致，更新看板baseline"))
    print("看板与代码真值", "一致" if ok else "不一致（以 coqc 为准修正看板）")
    return 0 if ok else 1


if __name__ == "__main__":
    tab = {"next": cmd_next, "status": cmd_status, "check": cmd_check}
    if len(sys.argv) < 2 or sys.argv[1] not in tab and sys.argv[1] not in ("start", "done", "block"):
        print(__doc__); sys.exit(0)
    a = sys.argv[1]
    if a in tab:
        sys.exit(tab[a](sys.argv[2:]))
    sys.exit(cmd_set({"start": "start", "done": "done", "block": "block"}[a], sys.argv[2:]))

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生命论概念协奏自动检索器 —— 七维定位法的可执行实现
=====================================================

配套文档：docs/体系研究/生命论概念协奏坐标系_七维定位法_20260911.md
坐标数据：scripts/concept_resonance/concept_coords.json

原理：
  每个概念在 7 根正交轴上有坐标（可多值）。给定一段新内容的坐标，
  逐轴计算与库中每个概念的重合，按轴权重加权求和；并识别三种"强协奏"：
    [跨尺度] 同操作关系型(R)、尺度不同   —— 同构跨尺度
    [跨人称] 关系/阶段/类型同、人称不同 —— 同一现象的三身互译
    [逆向治] 同一关系轴、方向相反       —— 如 具脸(pos) 对治 去脸(neg)

用法：
  # 1) 列出全部轴与概念
  python resonance_search.py --list

  # 2) 以库里已有概念为锚，找它的协奏近亲（最常用）
  python resonance_search.py --concept 不忍
  python resonance_search.py --concept 大跃退 --top 6

  # 3) 自由坐标查询：新讨论先打坐标，再找协奏（各轴可多值，可只给部分轴）
  python resonance_search.py -p P1 -f f3 -r R1 -s L0 L3 -t Tj --phase 解 -c K现象 K判准
  python resonance_search.py -r R6 --dir neg            # 例：找所有"去脸"类负向机制
  python resonance_search.py -r R7 --phase 蔽           # 例：名实遮蔽落在"蔽"环的概念

  # 4) 机器可读输出
  python resonance_search.py --concept 不忍 --json

轴参数：
  -p/--person P1|P2|P3            人称位
  -f/--flevel f1|f2|f3            明性递归层
  -r/--relation R1..R8            操作关系型
  -s/--scale  L0..L4|LF           尺度
  -t/--time   Ts|Tj|Tp|Td|Tt      时间形态
  --phase     生|蔽|解|行|中       生蔽解行
  -c/--ctype  K判准 K机制 ...      命题类型
  --dir       pos|neg|neu         方向
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(HERE, "concept_coords.json")

# 轴的内部字段名、CLI参数名、显示名
AXES = [
    ("person", "person", "人称位"),
    ("flevel", "flevel", "f层"),
    ("relation", "relation", "关系型"),
    ("scale", "scale", "尺度"),
    ("time", "time", "时间"),
    ("phase", "phase", "生蔽解行"),
    ("ctype", "ctype", "命题类型"),
]

# 操作关系型的"反治对"：一方是问题，另一方是对治（不同R码也构成逆向协奏）
COUNTER_PAIR = {"R2": "R8", "R5": "R8", "R3": "R4"}


def load_db(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def axis_label(db, field, code):
    return db["axes"][field]["values"].get(code, code)


def score_one(query, concept, weights):
    """返回 (总分, 命中明细list, 强协奏标记list, 参与轴数, 命中轴数)。"""
    detail = []
    strong = []
    n_axes = 0
    n_hit = 0
    total = 0.0

    for field, _arg, label in AXES:
        qvals = query.get(field, [])
        if not qvals:
            continue
        n_axes += 1
        cvals = concept.get(field, [])
        inter = [v for v in qvals if v in cvals]
        if inter:
            w = weights.get(field, 1.0)
            total += w
            n_hit += 1
            detail.append(f"{label}:{'/'.join(inter)}")

    qr, cr = set(query.get("relation", [])), set(concept.get("relation", []))
    qs, cs = set(query.get("scale", [])), set(concept.get("scale", []))
    # 强协奏1：同构跨尺度——关系型有重合，且对方带来查询里没有的新尺度层
    if qr & cr and cs and (cs - qs):
        total += 1.5
        strong.append("同构跨尺度")
    # 强协奏2：跨人称互译（关系/阶段/类型至少一项重合，但人称不重合且双方都标了人称）
    qp, cp = set(query.get("person", [])), set(concept.get("person", []))
    other_overlap = bool(
        (set(query.get("phase", [])) & set(concept.get("phase", [])))
        or (set(query.get("ctype", [])) & set(concept.get("ctype", [])))
        or (qr & cr)
    )
    if qp and cp and not (qp & cp) and other_overlap:
        total += 1.0
        strong.append("跨人称互译")
    # 强协奏3：逆向对治——同一关系轴方向相反，或互为反治对(R2↔R8等)
    qdir, cdir = query.get("dir"), concept.get("dir")
    opposite = (qdir and cdir and qdir != cdir and {qdir, cdir} == {"pos", "neg"})
    same_axis_opposite = bool(qr & cr) and opposite
    counter = False
    for q in qr:
        pair = COUNTER_PAIR.get(q)
        if pair and pair in cr and opposite:
            counter = True
    if same_axis_opposite or counter:
        total += 1.0
        strong.append("逆向对治")

    return round(total, 2), detail, strong, n_axes, n_hit


def search(db, query, top=None, exclude=None, hard_filter_dir=False):
    weights = db["meta"].get("axis_weights", {})
    rows = []
    for c in db["concepts"]:
        if exclude and c["name"] == exclude:
            continue
        # dir仅在自由查询显式指定时做硬过滤；以概念为锚浏览时不过滤（要保留它对治的负向概念）
        if hard_filter_dir and query.get("dir") and c.get("dir") and query["dir"] != c["dir"]:
            continue
        sc, detail, strong, n_axes, n_hit = score_one(query, c, weights)
        if n_axes > 0 and n_hit > 0:
            rows.append({
                "name": c["name"], "loc": c.get("loc", ""), "score": sc,
                "coverage": f"{n_hit}/{n_axes}", "detail": detail,
                "strong": strong, "dir": c.get("dir", ""),
            })
    rows.sort(key=lambda x: (-x["score"], x["name"]))
    return rows[:top] if top else rows


def coords_of(db, name):
    for c in db["concepts"]:
        if c["name"] == name or name in c["name"]:
            return c
    # 模糊匹配
    cand = [c["name"] for c in db["concepts"] if name in c["name"]]
    return None, cand


def print_rows(db, rows):
    if not rows:
        print("（无匹配：可检查坐标代码是否正确，或该坐标组合在库中尚属新结构——那正是需要造新概念的信号）")
        return
    for i, r in enumerate(rows, 1):
        tag = ("【" + "+".join(r["strong"]) + "】") if r["strong"] else ""
        dirmap = {"pos": "↑正向", "neg": "↓负向", "neu": "·中性", "": ""}
        print(f"{i:>2}. {r['score']:>4}  {r['name']}  {dirmap.get(r['dir'],'')} {tag}")
        print(f"     覆盖{r['coverage']}  命中: {'，'.join(r['detail'])}")
        if r["loc"]:
            print(f"     出处: {r['loc']}")


def cmd_list(db):
    print("=== 七轴取值 ===")
    for field, _a, label in AXES:
        vals = "，".join(f"{k}={v}" for k, v in db["axes"][field]["values"].items())
        print(f"[{label}] {vals}")
    print(f"\n=== 库内概念 {len(db['concepts'])} 条 ===")
    for c in db["concepts"]:
        r = "/".join(c.get("relation", [])) or "-"
        print(f"- {c['name']}  (R:{r}; {c.get('loc','')})")


def build_query(args):
    q = {}
    if args.person: q["person"] = args.person
    if args.flevel: q["flevel"] = args.flevel
    if args.relation: q["relation"] = args.relation
    if args.scale: q["scale"] = args.scale
    if args.time: q["time"] = args.time
    if args.phase: q["phase"] = args.phase
    if args.ctype: q["ctype"] = args.ctype
    if args.dir: q["dir"] = args.dir
    return q


def main():
    ap = argparse.ArgumentParser(description="生命论概念协奏自动检索器（七维定位法）")
    ap.add_argument("--db", default=DEFAULT_DB, help="坐标JSON路径")
    ap.add_argument("--list", action="store_true", help="列出全部轴与概念")
    ap.add_argument("--concept", help="以库内概念为锚检索其协奏近亲")
    ap.add_argument("--top", type=int, default=10, help="返回前N条（默认10）")
    ap.add_argument("--json", action="store_true", help="机器可读JSON输出")
    ap.add_argument("-p", "--person", nargs="+")
    ap.add_argument("-f", "--flevel", nargs="+")
    ap.add_argument("-r", "--relation", nargs="+")
    ap.add_argument("-s", "--scale", nargs="+")
    ap.add_argument("-t", "--time", nargs="+")
    ap.add_argument("--phase", nargs="+")
    ap.add_argument("-c", "--ctype", nargs="+")
    ap.add_argument("--dir", choices=["pos", "neg", "neu"])
    args = ap.parse_args()

    db = load_db(args.db)

    if args.list:
        cmd_list(db)
        return

    if args.concept:
        anchor = coords_of(db, args.concept)
        if isinstance(anchor, tuple):
            print(f"未找到概念「{args.concept}」。相近：{anchor[1]}", file=sys.stderr)
            sys.exit(1)
        query = {f: anchor.get(f, []) for f, _a, _l in AXES}
        query["dir"] = anchor.get("dir")
        if args.json:
            rows = search(db, query, top=args.top, exclude=anchor["name"])
            print(json.dumps({"anchor": anchor["name"], "results": rows}, ensure_ascii=False, indent=2))
            return
        print(f"锚概念：{anchor['name']}（{anchor.get('loc','')}）→ 协奏近亲：\n")
        rows = search(db, query, top=args.top, exclude=anchor["name"])
        print_rows(db, rows)
        return

    query = build_query(args)
    if not any(query.get(f) for f, _a, _l in AXES):
        ap.print_help()
        sys.exit(0)
    if args.json:
        rows = search(db, query, top=args.top, hard_filter_dir=True)
        print(json.dumps({"query": query, "results": rows}, ensure_ascii=False, indent=2))
    else:
        print(f"查询坐标：{json.dumps(query, ensure_ascii=False)}\n")
        print_rows(db, search(db, query, top=args.top, hard_filter_dir=True))


if __name__ == "__main__":
    main()

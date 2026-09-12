#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生命论概念协奏坐标库 —— 自检/质量门脚本
=============================================

每次扩库或修改坐标后必跑：
  python validate_coords.py
  python validate_coords.py --json   # 机器可读输出

检查项：
  E 错误（必须修）：
    E1 JSON 解析失败
    E2 概念缺 name / loc 字段
    E3 概念名重复
    E4 轴代码非法（不在 axes 定义中）
    E5 dir 非法（不在 pos/neg/neu/空）
    E6 结构轴全空（relation/person/flevel 都没值，无法检索）

  W 警告（建议修）：
    W1 K形式 命题但尺度不含 LF（形式层概念应落在形式尺度）
    W2 R6(去脸↔具脸) 但 dir=neu（R6是方向轴，应标 pos/neg）
    W3 全部轴只给了1个值且无 time/scale（坐标过稀，检索区分度低）
    W4 loc 字段过短（<3字，可能未填出处）

  I 信息（覆盖度报告）：
    各轴各取值的概念数，帮你发现稀疏区
"""
import argparse
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(HERE, "concept_coords.json")

STRUCTURAL_AXES = ("relation", "person", "flevel")
ALL_AXES = ("person", "flevel", "relation", "scale", "time", "phase", "ctype")
VALID_DIR = {"pos", "neg", "neu", ""}


def load_db(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate(db):
    errors = []
    warnings = []
    concepts = db.get("concepts", [])
    axes_def = db.get("axes", {})

    # E1: 基本结构
    if not isinstance(concepts, list) or not concepts:
        errors.append(("E1", "全局", "concepts 为空或不是列表"))
        return errors, warnings, {}

    # E3: 重名检查
    names = [c.get("name", "") for c in concepts]
    dup = {n for n in names if names.count(n) > 1}
    for n in dup:
        errors.append(("E3", n, "概念名重复"))

    # 逐概念检查
    for idx, c in enumerate(concepts):
        name = c.get("name", f"<第{idx+1}条无名>")

        # E2: 必填字段
        if not c.get("name"):
            errors.append(("E2", name, "缺 name 字段"))
        if not c.get("loc"):
            errors.append(("E2", name, "缺 loc 字段"))
        elif len(str(c["loc"])) < 3:
            warnings.append(("W4", name, f"loc 过短: '{c['loc']}'"))

        # E4: 轴代码合法性
        for axis in ALL_AXES:
            vals = c.get(axis, [])
            if not isinstance(vals, list):
                errors.append(("E4", name, f"{axis} 不是列表: {vals!r}"))
                continue
            valid_codes = set(axes_def.get(axis, {}).get("values", {}).keys())
            for v in vals:
                if v not in valid_codes:
                    errors.append(("E4", name, f"{axis} 含非法代码 '{v}'（合法: {sorted(valid_codes)}）"))

        # E5: dir 合法性
        d = c.get("dir", "")
        if d not in VALID_DIR:
            errors.append(("E5", name, f"dir 非法: '{d}'（合法: pos/neg/neu/空）"))

        # E6: 结构轴全空
        if not any(c.get(a) for a in STRUCTURAL_AXES):
            errors.append(("E6", name, "relation/person/flevel 全空，无法参与结构检索"))

        # W1: K形式 应含 LF
        if "K形式" in c.get("ctype", []) and "LF" not in c.get("scale", []):
            warnings.append(("W1", name, "ctype含K形式但scale不含LF"))

        # W2: R6 应标方向
        if "R6" in c.get("relation", []) and c.get("dir") == "neu":
            warnings.append(("W2", name, "relation含R6(去脸↔具脸方向轴)但dir=neu"))

        # W3: 坐标过稀
        total_vals = sum(len(c.get(a, [])) for a in ALL_AXES)
        if total_vals <= 2:
            warnings.append(("W3", name, f"坐标过稀（仅{total_vals}个取值），检索区分度低"))

    # 覆盖度报告
    coverage = {}
    for axis in ALL_AXES:
        counter = Counter()
        for c in concepts:
            for v in c.get(axis, []):
                counter[v] += 1
        coverage[axis] = dict(counter)
    dir_counter = Counter(c.get("dir", "(空)") for c in concepts)
    coverage["dir"] = dict(dir_counter)

    return errors, warnings, coverage


def print_report(errors, warnings, coverage, db):
    n = len(db.get("concepts", []))
    print(f"=== 坐标库自检报告 ===")
    print(f"概念总数: {n}")
    print(f"错误: {len(errors)}  警告: {len(warnings)}")
    print()

    if errors:
        print("--- 错误（必须修）---")
        for code, name, msg in errors:
            print(f"  [{code}] {name}: {msg}")
        print()

    if warnings:
        print("--- 警告（建议修）---")
        for code, name, msg in warnings:
            print(f"  [{code}] {name}: {msg}")
        print()

    print("--- 覆盖度报告 ---")
    axis_labels = {a: db["axes"][a]["label"] for a in ALL_AXES if a in db.get("axes", {})}
    for axis in ALL_AXES:
        label = axis_labels.get(axis, axis)
        cov = coverage.get(axis, {})
        vals = db["axes"].get(axis, {}).get("values", {})
        parts = []
        for code in vals:
            cnt = cov.get(code, 0)
            mark = "⚠️0" if cnt == 0 else str(cnt)
            parts.append(f"{code}={mark}")
        print(f"  [{label}] " + "  ".join(parts))
    print(f"  [方向] " + "  ".join(f"{k}={v}" for k, v in coverage.get("dir", {}).items()))

    # 稀疏轴告警
    print()
    sparse = []
    for axis in ALL_AXES:
        for code, cnt in coverage.get(axis, {}).items():
            if cnt == 0:
                sparse.append(f"{axis}.{code}")
    if sparse:
        print(f"⚠️ 零覆盖取值（{len(sparse)}个）: {', '.join(sparse)}")
        print("   → 这些轴值在库中尚无概念，扩库时可优先补")
    else:
        print("✅ 所有轴取值均有概念覆盖")

    print()
    if not errors:
        print("✅ 自检通过（无错误）")
    else:
        print(f"❌ 自检未通过，{len(errors)}个错误需修复")


def main():
    ap = argparse.ArgumentParser(description="概念协奏坐标库自检")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    args = ap.parse_args()

    try:
        db = load_db(args.db)
    except Exception as e:
        print(f"E1 JSON解析失败: {e}", file=sys.stderr)
        sys.exit(1)

    errors, warnings, coverage = validate(db)

    if args.json:
        print(json.dumps({
            "total": len(db.get("concepts", [])),
            "errors": [{"code": c, "name": n, "msg": m} for c, n, m in errors],
            "warnings": [{"code": c, "name": n, "msg": m} for c, n, m in warnings],
            "coverage": coverage,
            "passed": len(errors) == 0,
        }, ensure_ascii=False, indent=2))
    else:
        print_report(errors, warnings, coverage, db)

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

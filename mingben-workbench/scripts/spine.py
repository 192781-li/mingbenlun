#!/usr/bin/env python3
"""
生命论逻辑脊柱生成器。
从 concept_graph.json 按依赖关系自动生成核心概念链。
用法：python3 scripts/spine.py
任何总结体系的场合，先跑本脚本，禁止凭记忆复述核心结构。
"""
import json
from pathlib import Path

GRAPH_PATH = Path(__file__).parent.parent / "references" / "concept_graph.json"

def main():
    g = json.load(open(GRAPH_PATH, encoding="utf-8"))
    concepts = g["concepts"]
    layer_order = g.get("layer_order", [])

    # 按层分组，层内按依赖拓扑排序
    by_layer = {}
    for cid, c in concepts.items():
        layer = c.get("layer", "未分类")
        by_layer.setdefault(layer, []).append(cid)

    # 拓扑排序（同层内）
    def topo_sort(ids):
        visited = set()
        order = []
        def visit(n):
            if n in visited:
                return
            visited.add(n)
            for dep in concepts[n].get("depends_on", []):
                if dep in ids:
                    visit(dep)
            order.append(n)
        for n in ids:
            visit(n)
        return order

    print("=" * 60)
    print("生命论逻辑脊柱（从 concept_graph.json 自动生成）")
    print("=" * 60)

    for layer in layer_order:
        if layer not in by_layer:
            continue
        ids = topo_sort(by_layer[layer])
        print(f"\n【{layer}】")
        for i, cid in enumerate(ids, 1):
            c = concepts[cid]
            deps = c.get("depends_on", [])
            dep_str = f" ← {', '.join(deps)}" if deps else ""
            print(f"  {i}. {cid}{dep_str}")
            print(f"     {c.get('description', '')}")

    print("\n" + "=" * 60)
    print("四规定性明细：")
    for item in ["边界生成性", "内生目的性", "操作再生性", "环境互动性"]:
        print(f"  - {item}")
    print("\n感应做能明细：")
    for item, desc in [("感", "第一人称内向面，四规定性闭包的内在向度"),
                        ("应", "第二人称呼答，感与感之间"),
                        ("做", "第三人称操作面，感引发的趋利避害"),
                        ("能", "f³自觉，改造约束的能力")]:
        print(f"  - {item}：{desc}")
    print("=" * 60)

if __name__ == "__main__":
    main()

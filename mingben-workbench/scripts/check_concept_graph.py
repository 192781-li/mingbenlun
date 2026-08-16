#!/usr/bin/env python3
"""
生命论概念依赖图检查脚本
检查规则：
1. 每个概念必须能追溯到根节点'操作'
2. 除S=f(S)（自指）外不允许循环依赖
3. 量论概念不能被存在论概念依赖（阴不压阳）
4. 规范立场概念不能被存在论概念依赖（存在论不依赖决断）
5. 每个概念必须有layer和type标注
6. 依赖的概念必须在图中存在
"""

import json
import sys
from pathlib import Path

GRAPH_PATH = Path(__file__).parent.parent / "references" / "concept_graph.json"

# 层的依赖方向：高层可以依赖低层，低层不能依赖高层
# 存在论 < 认识论 < 社会分析 < 规范立场
# 量论可以依赖存在论/认识论/社会分析，但不能被存在论依赖
LAYER_RANK = {
    "存在论": 0,
    "认识论": 1,
    "社会分析": 2,
    "规范立场": 3,
    "量论": 4,
}

# 存在论概念不能依赖这些层
ONTOLOGY_FORBIDDEN_LAYERS = {"认识论", "社会分析", "规范立场", "量论"}


def load_graph():
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def check_completeness(concepts):
    """检查5: 每个概念有layer和type，依赖目标存在"""
    errors = []
    valid_layers = set(LAYER_RANK.keys())
    valid_types = {"践演", "概念", "经验", "决断"}

    for name, data in concepts.items():
        if "layer" not in data:
            errors.append(f"[缺失layer] {name}")
        elif data["layer"] not in valid_layers:
            errors.append(f"[非法layer] {name}: {data['layer']}")

        if "type" not in data:
            errors.append(f"[缺失type] {name}")
        elif data["type"] not in valid_types:
            errors.append(f"[非法type] {name}: {data['type']}")

        for dep in data.get("depends_on", []):
            if dep not in concepts:
                errors.append(f"[悬空依赖] {name} → {dep}（目标不在图中）")

    return errors


def check_root_traceability(concepts, root):
    """检查1: 每个概念必须能追溯到根节点"""
    errors = []

    def can_reach_root(name, visited=None):
        if visited is None:
            visited = set()
        if name == root:
            return True
        if name in visited:
            return False  # 循环，在别处检查
        visited.add(name)
        deps = concepts[name].get("depends_on", [])
        if not deps:
            return False
        return any(can_reach_root(d, visited.copy()) for d in deps)

    for name in concepts:
        if name == root:
            continue
        if not can_reach_root(name):
            errors.append(f"[无根] {name} 无法追溯到根节点'{root}'")

    return errors


def check_circular_deps(concepts, allowed_circular):
    """检查2: 除允许的循环外，不允许循环依赖"""
    errors = []
    allowed = set()
    for cycle in allowed_circular:
        allowed.update(cycle)

    # DFS找循环
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {name: WHITE for name in concepts}
    stack = []

    def dfs(name):
        color[name] = GRAY
        stack.append(name)
        for dep in concepts[name].get("depends_on", []):
            if dep not in concepts:
                continue  # 悬空依赖在别处报
            if dep in allowed and name in allowed:
                continue  # 允许的循环
            if color[dep] == GRAY:
                cycle_start = stack.index(dep)
                cycle = stack[cycle_start:] + [dep]
                errors.append(f"[循环依赖] {' → '.join(cycle)}")
            elif color[dep] == WHITE:
                dfs(dep)
        stack.pop()
        color[name] = BLACK

    for name in concepts:
        if color[name] == WHITE:
            dfs(name)

    return errors


def check_layer_direction(concepts):
    """检查3+4: 层的依赖方向"""
    errors = []

    for name, data in concepts.items():
        my_layer = data.get("layer")
        if my_layer not in LAYER_RANK:
            continue

        for dep in data.get("depends_on", []):
            if dep not in concepts:
                continue
            dep_layer = concepts[dep].get("layer")
            if dep_layer not in LAYER_RANK:
                continue

            my_rank = LAYER_RANK[my_layer]
            dep_rank = LAYER_RANK[dep_layer]

            # 存在论不能依赖更高层
            if my_layer == "存在论" and dep_layer in ONTOLOGY_FORBIDDEN_LAYERS:
                errors.append(
                    f"[阴压阳] 存在论概念'{name}'依赖了{dep_layer}概念'{dep}'"
                )

            # 一般规则：不能依赖更高层（量论除外，量论可以依赖任何层）
            # 但认识论可以依赖存在论，社会分析可以依赖存在论和认识论
            # 规范立场可以依赖存在论、认识论、社会分析
            # 量论可以依赖任何层
            if my_layer != "量论" and dep_rank > my_rank:
                # 检查是否是合法的跨层
                # 认识论依赖社会分析？不合法
                # 社会分析依赖规范立场？不合法
                # 存在论依赖任何更高层？已在上面检查
                if my_layer == "认识论" and dep_layer in {"社会分析", "规范立场"}:
                    errors.append(
                        f"[层序倒挂] {my_layer}概念'{name}'依赖了{dep_layer}概念'{dep}'"
                    )
                elif my_layer == "社会分析" and dep_layer == "规范立场":
                    errors.append(
                        f"[层序倒挂] {my_layer}概念'{name}'依赖了{dep_layer}概念'{dep}'"
                    )

    return errors


def check_type_consistency(concepts):
    """额外检查：践演类型的概念不应该有依赖（它是起点）"""
    errors = []
    for name, data in concepts.items():
        if data.get("type") == "践演" and data.get("depends_on"):
            errors.append(
                f"[践演有依赖] {name}标注为践演但依赖了{data['depends_on']}，践演应是无前提的起点"
            )
    return errors


def check_ontology_no_normative(concepts):
    """存在论概念不能依赖决断类型的概念"""
    errors = []
    for name, data in concepts.items():
        if data.get("layer") == "存在论":
            for dep in data.get("depends_on", []):
                if dep in concepts and concepts[dep].get("type") == "决断":
                    errors.append(
                        f"[存在论依赖决断] '{name}'依赖了决断类型概念'{dep}'"
                    )
    return errors


def main():
    graph = load_graph()
    concepts = graph["concepts"]
    root = graph["metadata"]["root"]
    allowed_circular = graph.get("allowed_circular", [])

    all_errors = []
    all_errors.extend(check_completeness(concepts))
    all_errors.extend(check_root_traceability(concepts, root))
    all_errors.extend(check_circular_deps(concepts, allowed_circular))
    all_errors.extend(check_layer_direction(concepts))
    all_errors.extend(check_type_consistency(concepts))
    all_errors.extend(check_ontology_no_normative(concepts))

    print(f"概念依赖图检查：共 {len(concepts)} 个概念")
    if all_errors:
        print(f"发现 {len(all_errors)} 个问题：")
        for e in all_errors:
            print(f"  ✗ {e}")
        return 1
    else:
        print("✓ 全部通过：无根概念、无循环依赖、层序正确、类型一致")
        return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
形式化检查6：概念依赖完整性
1. 每个概念必须能追溯到"操作"根节点（无悬空概念）
2. 不能有非法循环依赖（S=f(S)是起点，合法）
3. 量论概念不能被存在论概念依赖（阴不压阳）
"""

import json
import sys
from pathlib import Path

GRAPH_PATH = Path(__file__).parent.parent / "references" / "concept_graph.json"

def load_graph():
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def check_root_traceability(concepts, root="操作"):
    """检查1：每个概念都能追溯到根节点"""
    issues = []
    
    def can_reach(concept, visited=None):
        if visited is None:
            visited = set()
        if concept == root:
            return True
        if concept in visited:
            return False  # 循环，到不了根
        if concept not in concepts:
            return False  # 悬空引用
        visited.add(concept)
        for dep in concepts[concept].get("depends_on", []):
            if can_reach(dep, visited.copy()):
                return True
        return False
    
    for name in concepts:
        if name == root:
            continue
        if not can_reach(name):
            issues.append(f"[悬空概念] '{name}' 无法追溯到根节点'{root}'")
    
    return issues

def check_circular_deps(concepts):
    """检查2：非法循环依赖（S=f(S)自指循环是合法的）"""
    issues = []
    
    # 合法的自指：概念直接依赖自身（S=f(S)）
    # 非法的循环：A→B→A（两个不同概念互相依赖）
    def find_cycles(name, path, visited, in_path):
        if name in in_path:
            cycle_start = path.index(name)
            cycle = path[cycle_start:] + [name]
            # 过滤掉单概念自指（A→A），那是合法的
            if len(cycle) > 2:
                return [cycle]
            return []
        if name in visited or name not in concepts:
            return []
        
        visited.add(name)
        in_path.add(name)
        path.append(name)
        
        cycles = []
        for dep in concepts[name].get("depends_on", []):
            if dep == name:
                continue  # 自指，合法
            cycles.extend(find_cycles(dep, path, visited, in_path))
        
        path.pop()
        in_path.remove(name)
        return cycles
    
    all_cycles = set()
    for name in concepts:
        cycles = find_cycles(name, [], set(), set())
        for c in cycles:
            key = tuple(sorted(c))
            if key not in all_cycles:
                all_cycles.add(key)
                issues.append(f"[循环依赖] {' → '.join(c)}")
    
    return issues

def check_layer_order(concepts):
    """检查3：层级顺序
    硬伤规则（阴不压阳）：
    - 存在论(0)不能依赖任何更高层（认识论/社会分析/规范立场/量论）
    - 量论(3)不能依赖规范立场(2)（测量工具不能被决断污染）
    - 认识论(1)不能依赖规范立场(2)（认识不能被决断污染）
    合理依赖（不报错）：
    - 规范立场(2)依赖量论(3)：决断引用数据做支撑，合理
    - 社会分析(1)依赖量论(3)：分析引用数据，合理
    - 同层依赖：合理
    """
    issues = []
    
    LAYER_ORDER = {
        "存在论": 0,
        "认识论": 1,
        "社会分析": 1,
        "规范立场": 2,
        "量论": 3,
    }
    
    for name, info in concepts.items():
        my_layer = info.get("layer", "")
        my_order = LAYER_ORDER.get(my_layer, 99)
        
        for dep_name in info.get("depends_on", []):
            if dep_name not in concepts:
                issues.append(f"[缺失引用] '{name}' 依赖未定义概念 '{dep_name}'")
                continue
            dep_layer = concepts[dep_name].get("layer", "")
            dep_order = LAYER_ORDER.get(dep_layer, 99)
            
            # 硬伤1：存在论依赖任何更高层
            if my_order == 0 and dep_order > 0:
                issues.append(
                    f"[阴压阳] 存在论概念 '{name}' 依赖 {dep_layer}概念 '{dep_name}'，"
                    f"存在论不能被高层污染"
                )
            # 硬伤2：量论依赖规范立场
            elif my_order == 3 and dep_order == 2:
                issues.append(
                    f"[量论被决断污染] 量论概念 '{name}' 依赖规范立场概念 '{dep_name}'，"
                    f"测量工具必须中立"
                )
            # 硬伤3：认识论依赖规范立场
            elif my_order == 1 and dep_order == 2 and dep_layer == "规范立场":
                issues.append(
                    f"[认识被决断污染] 认识论概念 '{name}' 依赖规范立场概念 '{dep_name}'"
                )
    
    return issues

def check_dangling_refs(concepts):
    """检查4：依赖引用的概念是否都存在"""
    issues = []
    for name, info in concepts.items():
        for dep in info.get("depends_on", []):
            if dep not in concepts:
                issues.append(f"[悬空引用] '{name}' 依赖的 '{dep}' 不在概念图中")
    return issues

def main():
    graph = load_graph()
    concepts = graph["concepts"]
    root = graph.get("metadata", {}).get("root", "操作")
    
    print(f"概念依赖图：共 {len(concepts)} 个概念，根节点：{root}")
    print("=" * 60)
    
    all_issues = []
    
    print("\n【检查1】根节点追溯性...")
    issues = check_root_traceability(concepts, root)
    all_issues.extend(issues)
    if issues:
        for i in issues:
            print(f"  {i}")
    else:
        print("  ✓ 所有概念均可追溯到根节点")
    
    print("\n【检查2】循环依赖...")
    issues = check_circular_deps(concepts)
    all_issues.extend(issues)
    if issues:
        for i in issues:
            print(f"  {i}")
    else:
        print("  ✓ 无非法循环依赖")
    
    print("\n【检查3】层级顺序（量论不压存在论）...")
    issues = check_layer_order(concepts)
    all_issues.extend(issues)
    if issues:
        for i in issues:
            print(f"  {i}")
    else:
        print("  ✓ 层级顺序正确，无阴压阳")
    
    print("\n【检查4】悬空引用...")
    issues = check_dangling_refs(concepts)
    all_issues.extend(issues)
    if issues:
        for i in issues:
            print(f"  {i}")
    else:
        print("  ✓ 无悬空引用")
    
    print("\n" + "=" * 60)
    if all_issues:
        print(f"发现 {len(all_issues)} 个问题：")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("✓ 全部通过，概念依赖图完整无硬伤。")
    
    # 输出JSON报告
    report = {
        "check": "concept_dependency_integrity",
        "total_concepts": len(concepts),
        "root": root,
        "issues_count": len(all_issues),
        "issues": all_issues,
    }
    report_path = Path(__file__).parent.parent / "references" / "check6_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存：{report_path}")
    
    return len(all_issues)

if __name__ == "__main__":
    sys.exit(main())

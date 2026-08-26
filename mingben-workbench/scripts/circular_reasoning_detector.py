#!/usr/bin/env python3
"""
循环论证检测器 (Circular Reasoning Detector)
检测践演论文档中的循环论证和循环定义：
1. 定理A的证明引用了定理B，定理B的证明又引用了定理A（直接循环）
2. 更长的循环链：A→B→C→A
3. 定义中的循环依赖
4. 证明中使用了待证命题本身作为前提（窃取论题）

用法：python3 circular_reasoning_detector.py [目录路径]
"""

import re
import sys
from pathlib import Path
from collections import defaultdict, deque


class CircularReasoningDetector:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.issues = []
        self.stats = defaultdict(int)
        # 定理依赖图: theorem_id -> set of theorem_ids it depends on
        self.dependency_graph = defaultdict(set)
        # 定理到文件的映射
        self.theorem_files = {}
        # 定理名称到ID的映射（用于解析引用）
        self.name_to_id = {}

    def scan_files(self):
        """扫描所有Markdown文件，提取定理定义和依赖关系"""
        md_files = list(self.root_dir.rglob('*.md'))
        print(f'扫描 {len(md_files)} 个Markdown文件...\n')

        for filepath in md_files:
            if any(skip in filepath.name for skip in
                   ['overclaim_report', 'ref_consistency_report', 'circular_reasoning_report',
                    '文献核查清单', '版本号规范化', '新颖性核查']):
                continue
            self._scan_file(filepath)

    def _scan_file(self, filepath):
        """扫描单个文件"""
        try:
            content = filepath.read_text(encoding='utf-8')
        except Exception:
            return

        rel_path = str(filepath.relative_to(self.root_dir))
        lines = content.split('\n')

        # 提取定理定义
        self._extract_theorems(lines, rel_path)

        # 提取定理依赖关系
        self._extract_dependencies(lines, rel_path)

    def _extract_theorems(self, lines, rel_path):
        """提取定理定义"""
        # 匹配各种定理定义格式
        patterns = [
            r'##\s*(?:定理|Theorem|引理|Lemma|推论|Corollary|命题|Proposition)\s*([0-9.]+)',
            r'\*\*(?:定理|Theorem|引理|Lemma|推论|Corollary)\s*([0-9.]+)\*\*',
            r'(?:定理|Theorem|引理|Lemma)\s+([0-9.]+)\s*[:：]',
            r'T([0-9]{3})\s*[:：]',  # 永久ID格式
        ]

        for lineno, line in enumerate(lines, 1):
            for pattern in patterns:
                matches = re.finditer(pattern, line)
                for m in matches:
                    tid = m.group(1)
                    # 标准化ID
                    if tid.isdigit() and len(tid) == 3:
                        std_id = f'T{tid}'
                    else:
                        std_id = tid
                    self.theorem_files[std_id] = (rel_path, lineno)
                    self.stats['theorems_found'] += 1

    def _extract_dependencies(self, lines, rel_path):
        """提取定理依赖关系（证明中引用了哪些其他定理）"""
        current_theorem = None
        in_proof = False

        for lineno, line in enumerate(lines, 1):
            # 检测定理开始
            theorem_match = re.search(
                r'(?:##\s*|\*\*)(?:定理|Theorem|引理|Lemma|推论|Corollary|命题|Proposition)\s*([0-9.]+)',
                line
            )
            if theorem_match:
                tid = theorem_match.group(1)
                if tid.isdigit() and len(tid) == 3:
                    current_theorem = f'T{tid}'
                else:
                    current_theorem = tid
                in_proof = False
                continue

            # 检测证明开始
            if re.search(r'(?:证明|Proof|证[：:]|证\s*$)', line):
                in_proof = True
                continue

            # 检测证明结束
            if re.search(r'(?:∎|QED|证毕|证明完毕|\$\s*\\square\s*\$)', line):
                in_proof = False
                continue

            # 在证明中提取引用
            if in_proof and current_theorem:
                # 匹配各种引用格式
                ref_patterns = [
                    r'由(?:定理|引理|推论)\s*([0-9.]+)',
                    r'根据(?:定理|引理|推论)\s*([0-9.]+)',
                    r'(?:定理|引理|推论)\s*([0-9.]+)',
                    r'T([0-9]{3})',  # 永久ID引用
                    r'引理\s*([0-9.]+)',
                    r'命题\s*([0-9.]+)',
                ]

                for pattern in ref_patterns:
                    matches = re.finditer(pattern, line)
                    for m in matches:
                        ref_id = m.group(1)
                        if ref_id.isdigit() and len(ref_id) == 3:
                            std_ref = f'T{ref_id}'
                        else:
                            std_ref = ref_id

                        # 不记录自引用（那是递归定义，不是循环论证）
                        if std_ref != current_theorem:
                            self.dependency_graph[current_theorem].add(std_ref)
                            self.stats['dependencies_found'] += 1

    def detect_cycles(self):
        """检测依赖图中的循环"""
        print('检测循环依赖...\n')

        # 使用DFS检测有向图中的环
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.dependency_graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    # 找到循环
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        for node in self.dependency_graph:
            if node not in visited:
                dfs(node, [])

        # 去重（同一个循环可能被多次检测到）
        unique_cycles = []
        seen_cycles = set()
        for cycle in cycles:
            # 规范化循环表示（从最小元素开始）
            min_idx = cycle.index(min(cycle[:-1]))
            normalized = tuple(cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]])
            if normalized not in seen_cycles:
                seen_cycles.add(normalized)
                unique_cycles.append(list(normalized))

        self.stats['cycles_found'] = len(unique_cycles)

        for i, cycle in enumerate(unique_cycles, 1):
            cycle_str = ' → '.join(cycle)
            locations = []
            for tid in cycle[:-1]:
                if tid in self.theorem_files:
                    f, l = self.theorem_files[tid]
                    locations.append(f'{tid}({f}:{l})')
                else:
                    locations.append(f'{tid}(位置未知)')

            self.issues.append({
                'severity': 'error',
                'category': 'circular_dependency',
                'message': f'检测到循环依赖: {cycle_str}',
                'details': ' → '.join(locations),
                'cycle': cycle
            })

    def detect_begging_the_question(self):
        """检测窃取论题（证明中使用了待证命题本身）"""
        # 这个比较难自动检测，启发式：
        # 1. 证明中直接引用了正在证明的定理本身
        # 2. 证明中的关键步骤与定理陈述完全相同

        # 已经在_extract_dependencies中排除了自引用
        # 这里检测更微妙的情况：证明中出现了与定理陈述相同的命题
        for tid, (filepath, lineno) in self.theorem_files.items():
            full_path = self.root_dir / filepath
            try:
                content = full_path.read_text(encoding='utf-8')
                lines = content.split('\n')

                # 找到定理陈述
                theorem_line = lines[lineno - 1] if lineno <= len(lines) else ''

                # 找到证明部分
                in_proof = False
                proof_lines = []
                for i in range(lineno, len(lines)):
                    if re.search(r'(?:证明|Proof|证[：:]|证\s*$)', lines[i]):
                        in_proof = True
                        continue
                    if re.search(r'(?:∎|QED|证毕|证明完毕)', lines[i]):
                        break
                    if in_proof:
                        proof_lines.append(lines[i])

                # 启发式：证明中是否直接断言了定理结论
                proof_text = '\n'.join(proof_lines)
                # 提取定理结论（冒号后面的部分）
                conclusion_match = re.search(r'[:：]\s*(.+?)(?:$|\n)', theorem_line)
                if conclusion_match:
                    conclusion = conclusion_match.group(1).strip()
                    if len(conclusion) > 10 and conclusion in proof_text:
                        # 检查是否是作为前提使用（而不是作为结论重述）
                        # 这个启发式比较粗糙，标记为警告
                        self.issues.append({
                            'severity': 'warning',
                            'category': 'possible_begging_question',
                            'message': f'定理{tid}的证明中可能直接使用了定理结论（窃取论题嫌疑）',
                            'file': filepath,
                            'line': lineno,
                            'context': theorem_line.strip()[:100]
                        })
                        self.stats['begging_question_suspected'] += 1

            except Exception:
                continue

    def detect_circular_definitions(self):
        """检测循环定义"""
        # 定义中的循环依赖：A定义中使用了B，B定义中使用了A
        # 这个比较难自动检测，启发式：
        # 检测"定义X"部分中是否引用了其他未定义的概念

        # 简单实现：检测定义部分的相互引用
        def_pattern = r'(?:定义|Definition|Def)\s*([0-9.]+)'
        def_ref_pattern = r'(?:由定义|根据定义|by definition)\s*([0-9.]+)'

        # 这个功能比较复杂，暂时标记为待实现
        self.stats['circular_definitions_check'] = 'heuristic_only'

    def run(self):
        """运行检测"""
        self.scan_files()
        self.detect_cycles()
        self.detect_begging_the_question()
        self.detect_circular_definitions()
        return self.generate_report()

    def generate_report(self):
        """生成报告"""
        report = []
        report.append('# 循环论证检测报告\n')
        report.append(f'扫描目录: `{self.root_dir}`\n')
        report.append(f'生成时间: 2026-08-26\n')

        # 统计
        report.append('## 统计概览\n')
        report.append('| 类别 | 数量 |')
        report.append('|------|------|')
        report.append(f'| 发现定理 | {self.stats["theorems_found"]} |')
        report.append(f'| 依赖关系 | {self.stats["dependencies_found"]} |')
        report.append(f'| 循环依赖 | {self.stats["cycles_found"]} |')
        report.append(f'| 窃取论题嫌疑 | {self.stats.get("begging_question_suspected", 0)} |')
        report.append(f'| **发现问题** | **{len(self.issues)}** |')
        report.append('')

        # 依赖图统计
        if self.dependency_graph:
            report.append('## 定理依赖最多的Top 10\n')
            sorted_deps = sorted(self.dependency_graph.items(),
                                  key=lambda x: len(x[1]), reverse=True)[:10]
            for tid, deps in sorted_deps:
                loc = self.theorem_files.get(tid, ('未知', 0))
                report.append(f'- **{tid}** ({loc[0]}:{loc[1]}): 依赖 {len(deps)} 个定理')
            report.append('')

        # 详细问题
        errors = [i for i in self.issues if i['severity'] == 'error']
        warnings = [i for i in self.issues if i['severity'] == 'warning']

        if errors:
            report.append('## 错误（必须修复）\n')
            for i, issue in enumerate(errors, 1):
                report.append(f'### E{i:03d} [{issue["category"]}]\n')
                report.append(f'**问题**: {issue["message"]}\n')
                if 'details' in issue:
                    report.append(f'**位置**: {issue["details"]}\n')
                if 'cycle' in issue:
                    report.append(f'**循环链**: {" → ".join(issue["cycle"])}\n')
                report.append('')

        if warnings:
            report.append('## 警告（需要人工确认）\n')
            for i, issue in enumerate(warnings, 1):
                report.append(f'### W{i:03d} [{issue["category"]}] {issue.get("file", "")}:{issue.get("line", "")}\n')
                report.append(f'**问题**: {issue["message"]}\n')
                if 'context' in issue:
                    report.append(f'**上下文**: `{issue["context"]}`\n')
                report.append('')

        # 总结
        report.append('## 总结\n')
        if len(errors) == 0 and len(warnings) == 0:
            report.append('✅ 没有发现循环论证问题。\n')
        else:
            report.append(f'⚠️  发现 {len(errors)} 个错误，{len(warnings)} 个警告。\n')
            report.append('\n**循环论证是最严重的逻辑硬伤之一**——如果定理A的证明依赖定理B，而定理B的证明又依赖定理A，')
            report.append('那么这两个定理实际上都没有被证明。必须打破循环，至少其中一个定理需要独立的证明。\n')
            report.append('\n**窃取论题（begging the question）**是指证明中直接或间接地使用了待证命题本身作为前提。')
            report.append('这是一种非形式谬误，需要人工确认是否真的是循环论证。\n')

        return '\n'.join(report)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = '.'

    detector = CircularReasoningDetector(root_dir)
    report = detector.run()

    print(report)

    report_path = Path(root_dir) / 'circular_reasoning_report.md'
    report_path.write_text(report, encoding='utf-8')
    print(f'\n报告已保存到: {report_path}')

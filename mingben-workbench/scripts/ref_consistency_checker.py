#!/usr/bin/env python3
"""
引用一致性检查器 (Reference Consistency Checker)
检查践演论文档中的定理引用是否一致：
1. T001格式的永久ID引用是否在注册表中存在
2. 旧格式引用（定理X/公理X/引理X）提醒改为永久ID
3. 注册表中定理的状态一致性

用法：python3 ref_consistency_checker.py [目录路径] [注册表路径]
"""

import re
import sys
import json
from pathlib import Path
from collections import defaultdict


class RefConsistencyChecker:
    def __init__(self, root_dir, registry_path):
        self.root_dir = Path(root_dir)
        self.registry_path = Path(registry_path)
        self.issues = []
        self.stats = defaultdict(int)
        self.valid_ids = set()
        self.id_info = {}
        self._load_registry()

    def _load_registry(self):
        """加载定理注册表"""
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            for key, value in registry.items():
                if key.startswith('_'):
                    continue
                self.valid_ids.add(key)
                self.id_info[key] = value
            print(f'加载注册表: {len(self.valid_ids)} 个定理ID')
        except Exception as e:
            print(f'警告: 无法加载注册表: {e}')

    def check_file(self, filepath):
        """检查单个文件"""
        try:
            content = filepath.read_text(encoding='utf-8')
        except Exception as e:
            self.issues.append({
                'file': str(filepath),
                'line': 0,
                'severity': 'error',
                'category': 'io',
                'message': f'无法读取文件: {e}'
            })
            return

        lines = content.split('\n')
        for lineno, line in enumerate(lines, 1):
            # 跳过代码块
            if line.strip().startswith('```'):
                continue
            self._check_permanent_id(filepath, lineno, line)
            self._check_old_ref(filepath, lineno, line)

    def _check_permanent_id(self, filepath, lineno, line):
        """检查T001格式的永久ID引用是否存在"""
        # 匹配T001, T002等格式（后面不跟数字）
        pattern = r'\bT(\d{3})\b'
        matches = list(re.finditer(pattern, line))
        for m in matches:
            tid = f'T{m.group(1)}'
            self.stats['permanent_id_ref'] += 1
            if tid not in self.valid_ids:
                self.stats['invalid_id_ref'] += 1
                self.issues.append({
                    'file': str(filepath.relative_to(self.root_dir)),
                    'line': lineno,
                    'severity': 'error',
                    'category': 'invalid_id',
                    'message': f'引用了不存在的定理ID "{tid}"。请检查拼写或在注册表中添加。',
                    'context': line.strip()[:100]
                })

    def _check_old_ref(self, filepath, lineno, line):
        """检查旧格式引用（定理X/公理X/引理X）"""
        patterns = [
            (r'定理\s*(\d+(?:\.\d+)*)', '定理'),
            (r'公理\s*(\d+(?:\.\d+)*)', '公理'),
            (r'引理\s*(\d+(?:\.\d+)*)', '引理'),
            (r'推论\s*(\d+(?:\.\d+)*)', '推论'),
            (r'定义\s*(\d+(?:\.\d+)*)', '定义'),
            (r'命题\s*(\d+(?:\.\d+)*)', '命题'),
        ]
        for pattern, typ in patterns:
            matches = list(re.finditer(pattern, line))
            for m in matches:
                # 排除LaTeX引用格式（\ref{...}）
                if '\\ref' in line or '\\eqref' in line:
                    continue
                self.stats['old_ref'] += 1
                ref_text = m.group()
                self.issues.append({
                    'file': str(filepath.relative_to(self.root_dir)),
                    'line': lineno,
                    'severity': 'info',
                    'category': 'old_ref',
                    'message': f'使用可变编号 "{ref_text}"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。',
                    'context': line.strip()[:100]
                })

    def check_registry_consistency(self):
        """检查注册表内部一致性"""
        for tid, info in self.id_info.items():
            # 检查related中的ID是否存在
            if 'related' in info:
                for ref_id in info['related']:
                    if ref_id not in self.valid_ids:
                        self.issues.append({
                            'file': str(self.registry_path),
                            'line': 0,
                            'severity': 'warning',
                            'category': 'registry_invalid_ref',
                            'message': f'注册表中 {tid} 的related引用了不存在的ID "{ref_id}"。',
                            'context': tid
                        })

            # 检查状态字段是否合法
            valid_status = {'conjecture', 'paper_proof', 'coq_verified',
                           'literature_checked', 'expert_endorsed'}
            if 'status' in info and info['status'] not in valid_status:
                self.issues.append({
                    'file': str(self.registry_path),
                    'line': 0,
                    'severity': 'warning',
                    'category': 'registry_invalid_status',
                    'message': f'注册表中 {tid} 的status "{info["status"]}" 不合法。合法值: {valid_status}',
                    'context': tid
                })

            # 检查新颖性字段是否合法
            valid_novelty = {'new_theorem', 'new_proof', 'new_application',
                            'new_interpretation', 'known_result'}
            if 'novelty' in info and info['novelty'] not in valid_novelty:
                self.issues.append({
                    'file': str(self.registry_path),
                    'line': 0,
                    'severity': 'warning',
                    'category': 'registry_invalid_novelty',
                    'message': f'注册表中 {tid} 的novelty "{info["novelty"]}" 不合法。合法值: {valid_novelty}',
                    'context': tid
                })

    def run(self):
        """运行检查"""
        md_files = list(self.root_dir.rglob('*.md'))
        print(f'扫描 {len(md_files)} 个Markdown文件...\n')

        for filepath in md_files:
            if 'overclaim_report' in filepath.name or 'ref_consistency_report' in filepath.name:
                continue
            self.check_file(filepath)

        self.check_registry_consistency()
        return self.generate_report()

    def generate_report(self):
        """生成报告"""
        report = []
        report.append('# 引用一致性检查报告\n')
        report.append(f'扫描目录: `{self.root_dir}`\n')
        report.append(f'注册表: `{self.registry_path}`\n')
        report.append(f'生成时间: 2026-08-26\n')

        # 统计
        report.append('## 统计概览\n')
        report.append('| 类别 | 数量 |')
        report.append('|------|------|')
        report.append(f'| 注册表中定理ID | {len(self.valid_ids)} |')
        report.append(f'| 永久ID引用(T001格式) | {self.stats["permanent_id_ref"]} |')
        report.append(f'| 无效ID引用 | {self.stats["invalid_id_ref"]} |')
        report.append(f'| 旧格式引用(定理X) | {self.stats["old_ref"]} |')
        report.append(f'| **发现问题** | **{len(self.issues)}** |')
        report.append('')

        # 按严重程度分类
        errors = [i for i in self.issues if i['severity'] == 'error']
        warnings = [i for i in self.issues if i['severity'] == 'warning']
        infos = [i for i in self.issues if i['severity'] == 'info']

        report.append('## 严重程度分布\n')
        report.append(f'- 错误 (error): {len(errors)}')
        report.append(f'- 警告 (warning): {len(warnings)}')
        report.append(f'- 信息 (info): {len(infos)}')
        report.append('')

        # 注册表状态统计
        report.append('## 定理状态分布\n')
        status_count = defaultdict(int)
        for tid, info in self.id_info.items():
            status_count[info.get('status', 'unknown')] += 1
        for status, count in sorted(status_count.items()):
            report.append(f'- {status}: {count}')
        report.append('')

        # 新颖性分布
        report.append('## 新颖性分布\n')
        novelty_count = defaultdict(int)
        for tid, info in self.id_info.items():
            novelty_count[info.get('novelty', 'unknown')] += 1
        for novelty, count in sorted(novelty_count.items()):
            report.append(f'- {novelty}: {count}')
        report.append('')

        # Coq验证状态
        coq_verified = sum(1 for info in self.id_info.values() if info.get('coq_verified'))
        report.append(f'## Coq验证状态\n')
        report.append(f'- 已Coq验证: {coq_verified}/{len(self.valid_ids)}')
        report.append(f'- 未验证: {len(self.valid_ids) - coq_verified}')
        report.append('')

        # 文献核查状态
        lit_checked = sum(1 for info in self.id_info.values() if info.get('literature_checked'))
        report.append(f'## 文献核查状态\n')
        report.append(f'- 已查文献: {lit_checked}/{len(self.valid_ids)}')
        report.append(f'- 未核查: {len(self.valid_ids) - lit_checked}')
        report.append('')

        # 详细问题
        if errors:
            report.append('## 错误（必须修复）\n')
            for i, issue in enumerate(errors, 1):
                report.append(f'### E{i:03d} [{issue["category"]}] {issue["file"]}:{issue["line"]}\n')
                report.append(f'**问题**: {issue["message"]}\n')
                if 'context' in issue:
                    report.append(f'**上下文**: `{issue["context"]}`\n')
                report.append('')

        if warnings:
            report.append('## 警告（需要处理）\n')
            for i, issue in enumerate(warnings, 1):
                report.append(f'### W{i:03d} [{issue["category"]}] {issue["file"]}:{issue["line"]}\n')
                report.append(f'**问题**: {issue["message"]}\n')
                if 'context' in issue:
                    report.append(f'**上下文**: `{issue["context"]}`\n')
                report.append('')

        if infos:
            report.append(f'## 信息（建议改进，共{len(infos)}条）\n')
            report.append('旧格式引用（定理X/公理X等）建议逐步改为永久ID（T001格式）。\n')
            # 只显示前20条
            for i, issue in enumerate(infos[:20], 1):
                report.append(f'{i}. [{issue["category"]}] {issue["file"]}:{issue["line"]} — {issue["message"][:80]}')
            if len(infos) > 20:
                report.append(f'\n... 还有 {len(infos) - 20} 条，详见完整报告。')
            report.append('')

        # 总结
        report.append('## 总结\n')
        if len(errors) == 0 and len(warnings) == 0:
            report.append('✅ 没有发现引用一致性问题。\n')
        else:
            report.append(f'⚠️  发现 {len(errors)} 个错误，{len(warnings)} 个警告，{len(infos)} 条建议。\n')
            report.append('\n**核心原则**: 所有定理引用使用永久ID（T001格式），一旦确定永不改变。')
            report.append('旧格式引用（定理X/公理X）会随版本变化而失效，必须逐步迁移到永久ID。\n')

        return '\n'.join(report)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='引用一致性检查器')
    parser.add_argument('root_dir', nargs='?', default='.', help='扫描目录（默认当前目录）')
    parser.add_argument('--registry', '-r', default=None, help='定理注册表路径')
    parser.add_argument('--quiet', action='store_true', help='安静模式，不输出到控制台')
    parser.add_argument('--output', '-o', default=None, help='报告输出路径')
    args = parser.parse_args()
    
    root_dir = args.root_dir
    quiet = args.quiet
    
    if args.registry:
        registry_path = args.registry
    else:
        # 默认注册表路径
        script_dir = Path(__file__).parent
        default_registry = script_dir.parent / 'references' / 'theorem_registry.json'
        if default_registry.exists():
            registry_path = str(default_registry)
        else:
            registry_path = str(Path(root_dir) / 'theorem_registry.json')

    checker = RefConsistencyChecker(root_dir, registry_path)
    report = checker.run()

    if not quiet:
        print(report)

    if args.output:
        report_path = Path(args.output)
    else:
        script_dir = Path(__file__).parent
        default_output = script_dir.parent / 'references' / 'ref_consistency_report.md'
        if default_output.parent.exists():
            report_path = default_output
        else:
            report_path = Path(root_dir) / 'ref_consistency_report.md'
    
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding='utf-8')
    if not quiet:
        print(f'\n报告已保存到: {report_path}')
    
    sys.exit(0)

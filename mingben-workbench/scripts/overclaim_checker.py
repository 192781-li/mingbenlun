#!/usr/bin/env python3
"""
越级陈述检查器 (Overclaim Checker)
检查践演论文档中的越级陈述：
1. ≅（同构）是否有双向态射+互逆证明
2. 绝对化表述（必然/一定/任何/所有/永远/完全/彻底）是否有证明支撑
3. 新颖性声称（新的/首次/没有人/文献中没有）是否有文献核查
4. 定理引用是否使用永久ID（T001格式）而非可变编号

用法：python3 overclaim_checker.py [目录路径]
"""

import re
import sys
import os
import json
from pathlib import Path
from collections import defaultdict

# ============ 配置 ============

# 同构符号及其弱版替代
ISOMORPHISM_PATTERNS = [
    (r'≅', '同构≅', '需要双向态射+互逆证明，否则应降级为⇒/↠/≈/retraction'),
    (r'\\cong', 'LaTeX同构\\cong', '需要双向态射+互逆证明'),
    (r'\\simeq', 'LaTeX等价\\simeq', '需要等价关系证明'),
    (r'iff\b', '当且仅当iff', '需要双向证明'),
    (r'当且仅当', '当且仅当', '需要双向证明'),
]

# 绝对化表述
ABSOLUTE_PATTERNS = [
    r'必然', r'一定', r'任何', r'所有', r'永远', r'完全', r'彻底',
    r'绝不', r'从不', r'总是', r'全部', r'每一个', r'任意',
    r'不可能', r'必然不', r'永远不', r'完全不',
    r'任何.*都', r'所有.*都', r'每.*都',
]

# 新颖性声称
NOVELTY_PATTERNS = [
    r'新的定理', r'首次', r'第一次', r'没有人', r'文献中没有',
    r'之前没有', r'从未被', r'创新', r'突破', r'革命性',
    r'我们发现', r'我们证明了.*新',
]

# 可变定理编号模式（应该用T001永久ID）
OLD_THEME_REF_PATTERNS = [
    r'定理\s*\d+', r'公理\s*\d+', r'引理\s*\d+',
    r'推论\s*\d+', r'定义\s*\d+', r'命题\s*\d+',
]

# 证明标记（如果附近有这些词，认为有证明支撑）
PROOF_MARKERS = [
    r'证明', r'证\b', r'Proof', r'QED', r'∎', r'证毕',
    r'由定理', r'由引理', r'由定义', r'因为', r'由于',
    r'结构归纳', r'归纳', r'反证', r'构造',
]

# ============ 检查器 ============

class OverclaimChecker:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.issues = []
        self.stats = defaultdict(int)

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

            self._check_isomorphism(filepath, lineno, line, lines)
            self._check_absolute(filepath, lineno, line, lines)
            self._check_novelty(filepath, lineno, line, lines)
            self._check_old_ref(filepath, lineno, line)

    def _has_proof_nearby(self, lines, lineno, window=5):
        """检查附近是否有证明标记"""
        start = max(0, lineno - window - 1)
        end = min(len(lines), lineno + window)
        nearby = '\n'.join(lines[start:end])
        for marker in PROOF_MARKERS:
            if re.search(marker, nearby):
                return True
        return False

    def _check_isomorphism(self, filepath, lineno, line, lines):
        """检查同构符号"""
        for pattern, name, advice in ISOMORPHISM_PATTERNS:
            matches = list(re.finditer(pattern, line))
            for m in matches:
                self.stats['isomorphism'] += 1
                # 检查附近是否有证明
                if not self._has_proof_nearby(lines, lineno):
                    self.issues.append({
                        'file': str(filepath.relative_to(self.root_dir)),
                        'line': lineno,
                        'severity': 'warning',
                        'category': 'isomorphism',
                        'message': f'{name} "{m.group()}" 附近没有证明标记。{advice}',
                        'context': line.strip()[:100]
                    })

    def _check_absolute(self, filepath, lineno, line, lines):
        """检查绝对化表述"""
        for pattern in ABSOLUTE_PATTERNS:
            matches = list(re.finditer(pattern, line))
            for m in matches:
                self.stats['absolute'] += 1
                # 绝对化表述需要更强的证明支撑
                if not self._has_proof_nearby(lines, lineno, window=8):
                    self.issues.append({
                        'file': str(filepath.relative_to(self.root_dir)),
                        'line': lineno,
                        'severity': 'info',
                        'category': 'absolute',
                        'message': f'绝对化表述 "{m.group()}" 附近没有证明标记。请确认是否有严格证明支撑，或改为"在X条件下"。',
                        'context': line.strip()[:100]
                    })

    def _check_novelty(self, filepath, lineno, line, lines):
        """检查新颖性声称"""
        for pattern in NOVELTY_PATTERNS:
            matches = list(re.finditer(pattern, line))
            for m in matches:
                self.stats['novelty'] += 1
                # 检查是否有文献核查标记
                if not self._has_proof_nearby(lines, lineno, window=10):
                    self.issues.append({
                        'file': str(filepath.relative_to(self.root_dir)),
                        'line': lineno,
                        'severity': 'warning',
                        'category': 'novelty',
                        'message': f'新颖性声称 "{m.group()}" 没有文献核查标记。请确认查过文献，并标注是新定理/新证明/新应用/新解释还是已知结果。',
                        'context': line.strip()[:100]
                    })

    def _check_old_ref(self, filepath, lineno, line):
        """检查是否使用可变定理编号而非永久ID"""
        for pattern in OLD_THEME_REF_PATTERNS:
            matches = list(re.finditer(pattern, line))
            for m in matches:
                self.stats['old_ref'] += 1
                self.issues.append({
                    'file': str(filepath.relative_to(self.root_dir)),
                    'line': lineno,
                    'severity': 'info',
                    'category': 'old_ref',
                    'message': f'使用可变编号 "{m.group()}"，建议改为永久ID格式（如T006）。永久ID一旦确定永不改变。',
                    'context': line.strip()[:100]
                })

    def run(self):
        """运行检查"""
        md_files = list(self.root_dir.rglob('*.md'))
        print(f'扫描 {len(md_files)} 个Markdown文件...\n')

        for filepath in md_files:
            # 跳过这个检查器自己的报告
            if 'overclaim_report' in filepath.name:
                continue
            self.check_file(filepath)

        return self.generate_report()

    def generate_report(self):
        """生成报告"""
        report = []
        report.append('# 越级陈述检查报告\n')
        report.append(f'扫描目录: `{self.root_dir}`\n')
        report.append(f'生成时间: 2026-08-26\n')

        # 统计
        report.append('## 统计概览\n')
        report.append('| 类别 | 数量 |')
        report.append('|------|------|')
        report.append(f'| 同构符号(≅) | {self.stats["isomorphism"]} |')
        report.append(f'| 绝对化表述 | {self.stats["absolute"]} |')
        report.append(f'| 新颖性声称 | {self.stats["novelty"]} |')
        report.append(f'| 可变定理编号 | {self.stats["old_ref"]} |')
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

        # 详细问题
        if warnings:
            report.append('## 警告（需要处理）\n')
            for i, issue in enumerate(warnings, 1):
                report.append(f'### W{i:03d} [{issue["category"]}] {issue["file"]}:{issue["line"]}\n')
                report.append(f'**问题**: {issue["message"]}\n')
                report.append(f'**上下文**: `{issue["context"]}`\n')
                report.append('')

        if infos:
            report.append('## 信息（建议改进）\n')
            for i, issue in enumerate(infos, 1):
                report.append(f'### I{i:03d} [{issue["category"]}] {issue["file"]}:{issue["line"]}\n')
                report.append(f'**问题**: {issue["message"]}\n')
                report.append(f'**上下文**: `{issue["context"]}`\n')
                report.append('')

        if errors:
            report.append('## 错误（必须修复）\n')
            for i, issue in enumerate(errors, 1):
                report.append(f'### E{i:03d} [{issue["category"]}] {issue["file"]}:{issue["line"]}\n')
                report.append(f'**问题**: {issue["message"]}\n')
                report.append('')

        # 总结
        report.append('## 总结\n')
        if len(self.issues) == 0:
            report.append('✅ 没有发现越级陈述问题。文档严格性良好。\n')
        else:
            report.append(f'⚠️  发现 {len(self.issues)} 个问题需要处理。\n')
            report.append('\n**核心原则**: 全线把≅降级为⇒/↠/≈/双模拟，先证弱版，能升回的再升。')
            report.append('绝对化表述需要严格证明支撑，新颖性声称需要文献核查。\n')

        return '\n'.join(report)


# ============ 主程序 ============

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='越级陈述检查器')
    parser.add_argument('root_dir', nargs='?', default='.', help='扫描目录（默认当前目录）')
    parser.add_argument('--quiet', action='store_true', help='安静模式，不输出到控制台')
    parser.add_argument('--output', '-o', default=None, help='报告输出路径（默认: 扫描目录/overclaim_report.md）')
    args = parser.parse_args()
    
    root_dir = args.root_dir
    quiet = args.quiet

    checker = OverclaimChecker(root_dir)
    report = checker.run()

    # 输出到控制台
    if not quiet:
        print(report)

    # 保存到文件
    if args.output:
        report_path = Path(args.output)
    else:
        # 默认保存到 mingben-workbench/references/ 目录
        script_dir = Path(__file__).parent
        default_output = script_dir.parent / 'references' / 'overclaim_report.md'
        if default_output.parent.exists():
            report_path = default_output
        else:
            report_path = Path(root_dir) / 'overclaim_report.md'
    
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding='utf-8')
    if not quiet:
        print(f'\n报告已保存到: {report_path}')
    
    # 退出码：0=成功（无论有没有问题，只要报告生成了就算成功）
    # 检查器的目的是发现问题并生成报告，不是阻止提交
    sys.exit(0)

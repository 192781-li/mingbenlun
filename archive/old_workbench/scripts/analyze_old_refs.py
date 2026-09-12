#!/usr/bin/env python3
"""分析旧引用分布：区分历史版本文件和当前活跃文件"""
import os
import re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent

OLD_REF_PATTERNS = [
    (r'定理\s*(\d+(?:\.\d+)?)', '定理'),
    (r'公理\s*(\d+(?:\.\d+)?)', '公理'),
    (r'定义\s*(\d+(?:\.\d+)?)', '定义'),
    (r'引理\s*(\d+(?:\.\d+)?)', '引理'),
    (r'推论\s*(\d+(?:\.\d+)?)', '推论'),
    (r'命题\s*(\d+(?:\.\d+)?)', '命题'),
]

EXCLUDE_DIRS = {'.git', 'backup', '__pycache__', 'node_modules', '.venv'}

def classify_file(rel_path):
    """分类文件：历史版本/报告/工具/当前文档"""
    name = Path(rel_path).name
    # 历史版本文件（v0.1-v1.x的enactics版本）
    if re.match(r'enactics_v\d+\.\d+\.md', name):
        return '历史版本'
    # 审计/报告文件
    if 'report' in name.lower() or '审计' in name or '攻击' in name or '核查' in name:
        return '报告/审计'
    # 脚本/工具相关
    if rel_path.startswith('mingben-workbench/scripts/') or rel_path.startswith('coq/'):
        return '工具/代码'
    # 全书正文
    if rel_path.startswith('生命论_模块化/'):
        return '全书正文'
    # 参考资料
    if rel_path.startswith('mingben-workbench/references/'):
        return '参考资料'
    return '其他'

def main():
    file_refs = defaultdict(lambda: defaultdict(int))  # {file: {ref: count}}
    file_categories = defaultdict(int)
    
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if not f.endswith('.md'):
                continue
            md_file = Path(root) / f
            rel_path = str(md_file.relative_to(REPO_ROOT))
            try:
                content = md_file.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            
            category = classify_file(rel_path)
            count = 0
            for pattern, ref_type in OLD_REF_PATTERNS:
                matches = re.findall(pattern, content)
                count += len(matches)
                for num in matches:
                    ref = f'{ref_type}{num}'
                    file_refs[rel_path][ref] += 1
            
            if count > 0:
                file_categories[category] += count
    
    print("=== 旧引用按文件类别分布 ===")
    total = sum(file_categories.values())
    for cat, count in sorted(file_categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}次 ({count*100//total}%)")
    print(f"  总计: {total}次")
    print()
    
    # 列出"当前文档"和"全书正文"中的旧引用
    print("=== 需要迁移的文件（全书正文+参考资料中的活跃文档）===")
    active_files = []
    for rel_path, refs in sorted(file_refs.items()):
        cat = classify_file(rel_path)
        if cat in ('全书正文', '参考资料', '其他'):
            total_refs = sum(refs.values())
            active_files.append((rel_path, cat, total_refs, refs))
    
    active_files.sort(key=lambda x: -x[2])
    active_total = sum(f[2] for f in active_files)
    print(f"  共{len(active_files)}个文件, {active_total}次引用")
    print()
    for rel_path, cat, count, refs in active_files[:30]:
        top_refs = sorted(refs.items(), key=lambda x: -x[1])[:5]
        top_str = ', '.join(f'{r}({c})' for r, c in top_refs)
        print(f"  [{cat}] {rel_path}: {count}次 — {top_str}")

if __name__ == '__main__':
    main()

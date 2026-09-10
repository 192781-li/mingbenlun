#!/usr/bin/env python3
"""扫描全书中的卷篇交叉引用"""
import os
import re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent
BOOK_DIR = REPO_ROOT / "生命论_模块化"

# 卷篇引用模式
REF_PATTERNS = [
    r'卷[一二三四五六七八九十\d]+篇[一二三四五六七八九十\d]+',
    r'第[一二三四五六七八九十\d]+卷第[一二三四五六七八九十\d]+篇',
    r'卷[一二三四五六七八九十\d]+\s*篇[一二三四五六七八九十\d]+',
]

EXCLUDE_DIRS = {'.git', 'backup', '__pycache__'}

def find_md_files():
    md_files = []
    for root, dirs, files in os.walk(BOOK_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith('.md'):
                md_files.append(Path(root) / f)
    return sorted(md_files)

def scan_refs():
    all_refs = defaultdict(list)
    for md_file in find_md_files():
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        rel_path = str(md_file.relative_to(REPO_ROOT))
        for pattern in REF_PATTERNS:
            matches = re.findall(pattern, content)
            for ref in matches:
                all_refs[ref].append(rel_path)
    return all_refs

def main():
    print("=== 卷篇交叉引用扫描 ===")
    all_refs = scan_refs()
    total = sum(len(files) for files in all_refs.values())
    print(f"  唯一引用: {len(all_refs)}")
    print(f"  总出现次数: {total}")
    print()
    print("=== Top 30 ===")
    for ref, files in sorted(all_refs.items(), key=lambda x: -len(x[1]))[:30]:
        print(f"  {ref}: {len(files)}次")
    # 保存报告
    report = {
        "total_unique": len(all_refs),
        "total_occurrences": total,
        "refs": {ref: {"count": len(files), "files": sorted(set(files))} for ref, files in all_refs.items()}
    }
    import json
    report_file = REPO_ROOT / "mingben-workbench" / "references" / "cross_refs_scan.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n报告已写入: {report_file}")

if __name__ == "__main__":
    main()

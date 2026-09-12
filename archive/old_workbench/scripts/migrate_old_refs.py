#!/usr/bin/env python3
"""
旧格式引用迁移工具
用法: python migrate_old_refs.py [--apply]
功能:
  1. 扫描所有Markdown文件中的旧格式引用（定理X、公理X、定义X等）
  2. 生成待迁移清单（JSON）
  3. --apply模式下，根据映射表批量替换
"""
import os
import re
import sys
import json
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent
REPORT_FILE = REPO_ROOT / "mingben-workbench" / "references" / "old_refs_migration_report.json"
MAPPING_FILE = REPO_ROOT / "mingben-workbench" / "references" / "old_refs_mapping.json"

# 旧格式引用模式
OLD_REF_PATTERNS = [
    (r'定理\s*(\d+(?:\.\d+)?)', '定理'),
    (r'公理\s*(\d+(?:\.\d+)?)', '公理'),
    (r'定义\s*(\d+(?:\.\d+)?)', '定义'),
    (r'引理\s*(\d+(?:\.\d+)?)', '引理'),
    (r'推论\s*(\d+(?:\.\d+)?)', '推论'),
    (r'命题\s*(\d+(?:\.\d+)?)', '命题'),
    (r'Theorem\s+(\d+(?:\.\d+)?)', 'Theorem'),
    (r'Lemma\s+(\d+(?:\.\d+)?)', 'Lemma'),
    (r'Axiom\s+(\d+(?:\.\d+)?)', 'Axiom'),
    (r'Definition\s+(\d+(?:\.\d+)?)', 'Definition'),
]

# 排除的目录和文件
EXCLUDE_DIRS = {'.git', 'backup', '__pycache__', 'node_modules', '.venv'}
EXCLUDE_FILES = {'old_refs_migration_report.json', 'old_refs_mapping.json'}

def find_md_files():
    """查找所有Markdown文件"""
    md_files = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith('.md') and f not in EXCLUDE_FILES:
                md_files.append(Path(root) / f)
    return sorted(md_files)

def scan_old_refs():
    """扫描所有旧格式引用"""
    all_refs = defaultdict(lambda: defaultdict(list))  # {type: {number: [files]}}
    
    for md_file in find_md_files():
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        
        rel_path = str(md_file.relative_to(REPO_ROOT))
        
        for pattern, ref_type in OLD_REF_PATTERNS:
            matches = re.findall(pattern, content)
            for num in matches:
                all_refs[ref_type][num].append(rel_path)
    
    return all_refs

def generate_report(all_refs):
    """生成迁移报告"""
    report = {
        "generated_at": __import__('datetime').datetime.now().isoformat(),
        "summary": {
            "total_types": len(all_refs),
            "total_unique_refs": sum(len(nums) for nums in all_refs.values()),
            "total_occurrences": sum(len(files) for nums in all_refs.values() for files in nums.values()),
        },
        "refs": {}
    }
    
    for ref_type, nums in sorted(all_refs.items()):
        report["refs"][ref_type] = {}
        for num, files in sorted(nums.items(), key=lambda x: [int(p) if p.isdigit() else p for p in x[0].split('.')]):
            report["refs"][ref_type][num] = {
                "count": len(files),
                "files": sorted(set(files))
            }
    
    return report

def load_mapping():
    """加载映射表"""
    if MAPPING_FILE.exists():
        return json.loads(MAPPING_FILE.read_text(encoding='utf-8'))
    return {}

def apply_migration(mapping):
    """根据映射表批量替换"""
    total_replacements = 0
    changed_files = []
    
    for md_file in find_md_files():
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        
        original_content = content
        file_replacements = 0
        
        for old_ref, new_id in mapping.items():
            # old_ref格式如 "定理20"、"公理3"
            if old_ref in content:
                count = content.count(old_ref)
                content = content.replace(old_ref, new_id)
                file_replacements += count
        
        if content != original_content:
            md_file.write_text(content, encoding='utf-8')
            total_replacements += file_replacements
            changed_files.append({
                "file": str(md_file.relative_to(REPO_ROOT)),
                "replacements": file_replacements
            })
    
    return total_replacements, changed_files

def main():
    apply_mode = "--apply" in sys.argv
    
    print("=== 旧格式引用迁移工具 ===")
    print()
    
    # 扫描
    print("--- 扫描旧格式引用 ---")
    all_refs = scan_old_refs()
    
    total_unique = sum(len(nums) for nums in all_refs.values())
    total_occurrences = sum(len(files) for nums in all_refs.values() for files in nums.values())
    
    print(f"  扫描到 {total_unique} 个唯一旧格式引用")
    print(f"  总出现次数: {total_occurrences}")
    print()
    
    for ref_type, nums in sorted(all_refs.items()):
        print(f"  {ref_type}: {len(nums)} 个编号, {sum(len(f) for f in nums.values())} 次出现")
    print()
    
    # 生成报告
    report = generate_report(all_refs)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"报告已写入: {REPORT_FILE}")
    print()
    
    if apply_mode:
        # 应用迁移
        mapping = load_mapping()
        if not mapping:
            print("❌ 映射表为空，无法应用迁移。")
            print(f"   请先创建映射表: {MAPPING_FILE}")
            print("   格式: {\"定理20\": \"T006\", \"公理3\": \"公理III\", ...}")
            return 1
        
        print(f"--- 应用迁移 ({len(mapping)} 条映射) ---")
        total, changed = apply_migration(mapping)
        print(f"  总替换次数: {total}")
        print(f"  修改文件数: {len(changed)}")
        for f in changed[:10]:
            print(f"    - {f['file']}: {f['replacements']} 处")
        if len(changed) > 10:
            print(f"    ... 还有 {len(changed)-10} 个文件")
    else:
        print("提示: 使用 --apply 参数应用迁移")
        print(f"  映射表位置: {MAPPING_FILE}")
        print("  格式: {\"定理20\": \"T006\", \"公理3\": \"公理III\", ...}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

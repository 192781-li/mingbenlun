#!/usr/bin/env python3
"""检查卷篇引用是否有效"""
import os
import re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent
BOOK_DIR = REPO_ROOT / "生命论_模块化"

# 中文数字转阿拉伯数字
CN_NUM = {'一':1, '二':2, '三':3, '四':4, '五':5, '六':6, '七':7, '八':8, '九':9, '十':10}

def cn_to_num(s):
    if s.isdigit():
        return int(s)
    if s in CN_NUM:
        return CN_NUM[s]
    return None

def get_existing_refs():
    """获取当前目录中所有有效的卷篇引用"""
    existing = set()
    for vol_dir in BOOK_DIR.iterdir():
        if vol_dir.is_dir() and vol_dir.name.startswith(('00_', '01_', '02_', '03_', '04_', '05_', '06_', '07_', '08_', '09_', '10_', '11_')):
            vol_name = vol_dir.name
            # 提取卷号
            vol_match = re.match(r'(\d+)_卷([一二三四五六七八九十\d]+)', vol_name)
            if vol_match:
                vol_num = cn_to_num(vol_match.group(2))
                if vol_num:
                    for md_file in vol_dir.glob('篇*.md'):
                        # 提取篇号
                        pian_match = re.match(r'篇([一二三四五六七八九十\d]+)', md_file.name)
                        if pian_match:
                            pian_num = cn_to_num(pian_match.group(1))
                            if pian_num:
                                existing.add((vol_num, pian_num))
    return existing

def scan_refs():
    """扫描所有卷篇引用"""
    all_refs = defaultdict(list)
    pattern = r'卷([一二三四五六七八九十\d]+)篇([一二三四五六七八九十\d]+)'
    for root, dirs, files in os.walk(BOOK_DIR):
        dirs[:] = [d for d in dirs if d not in {'.git', 'backup', '__pycache__'}]
        for f in files:
            if f.endswith('.md'):
                md_file = Path(root) / f
                try:
                    content = md_file.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    continue
                rel_path = str(md_file.relative_to(REPO_ROOT))
                for match in re.finditer(pattern, content):
                    vol = cn_to_num(match.group(1))
                    pian = cn_to_num(match.group(2))
                    if vol and pian:
                        all_refs[(vol, pian)].append(rel_path)
    return all_refs

def main():
    print("=== 卷篇引用有效性检查 ===")
    existing = get_existing_refs()
    print(f"  当前有效卷篇: {len(existing)}个")
    for v, p in sorted(existing):
        print(f"    卷{v}篇{p}")
    print()
    
    all_refs = scan_refs()
    total = sum(len(files) for files in all_refs.values())
    print(f"  扫描到引用: {len(all_refs)}个唯一, {total}次出现")
    print()
    
    # 检查无效引用
    invalid = {}
    valid = {}
    for ref, files in all_refs.items():
        if ref in existing:
            valid[ref] = files
        else:
            invalid[ref] = files
    
    print(f"=== 有效引用: {len(valid)}个, {sum(len(f) for f in valid.values())}次 ===")
    print(f"=== 无效引用: {len(invalid)}个, {sum(len(f) for f in invalid.values())}次 ===")
    print()
    if invalid:
        print("无效引用详情:")
        for ref, files in sorted(invalid.items(), key=lambda x: -len(x[1])):
            print(f"  卷{ref[0]}篇{ref[1]}: {len(files)}次, 文件: {files[:3]}")
    
    # 保存报告
    import json
    report = {
        "existing_refs": [f"卷{v}篇{p}" for v, p in sorted(existing)],
        "valid_refs": {f"卷{v}篇{p}": len(files) for (v,p), files in valid.items()},
        "invalid_refs": {f"卷{v}篇{p}": {"count": len(files), "files": sorted(set(files))} for (v,p), files in invalid.items()}
    }
    report_file = REPO_ROOT / "mingben-workbench" / "references" / "cross_refs_validity.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n报告已写入: {report_file}")

if __name__ == "__main__":
    main()

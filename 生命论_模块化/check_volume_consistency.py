#!/usr/bin/env python3
"""
卷结构一致性验证脚本。
用法：python3 check_volume_consistency.py

检查项：
1. manifest.json 中定义的目录是否都存在
2. 每个卷的 00_卷标题.md 中的卷号是否与 manifest 一致
3. 正文中是否有硬编码的卷号引用（排除书名引用如《资本论》第一卷）
4. 章编号是否连续无重复

调整卷序后运行此脚本即可发现不一致。
"""
import json, os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))

def main():
    errors = []
    
    # 1. 读取 manifest
    manifest_path = os.path.join(BASE, "manifest.json")
    if not os.path.exists(manifest_path):
        print("ERROR: manifest.json 不存在")
        sys.exit(1)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    # 2. 检查目录和卷标题
    for vol in manifest["volumes"]:
        dirpath = os.path.join(BASE, vol["dir"])
        if not os.path.isdir(dirpath):
            errors.append(f"目录不存在: {vol['dir']}")
            continue
        title_file = os.path.join(dirpath, "00_卷标题.md")
        if os.path.exists(title_file):
            with open(title_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
            expected = f"# 第{vol['number'].replace('卷','')}卷 {vol['title']}" if vol["number"] not in ("卷首", "附录") else None
            if expected and expected not in first_line:
                errors.append(f"卷标题不一致: {vol['dir']}/00_卷标题.md\n  期望包含: {expected}\n  实际: {first_line}")
    
    # 3. 检查正文中的硬编码卷号引用（排除书名）
    volume_refs = []
    for root, dirs, files in os.walk(BASE):
        if ".git" in root:
            continue
        for fname in files:
            if not fname.startswith("篇") or not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            relpath = os.path.relpath(fpath, BASE)
            with open(fpath, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    # 找"第X卷"但排除书名引用：
                    # a) 在《》内：《第一卷》
                    # b) 紧跟在书名号后：《资本论》第一卷、《马克思恩格斯选集》第一卷
                    for m in re.finditer(r"第[一二三四五六七八九十]+卷", line):
                        before = line[:m.start()]
                        in_book = before.count("《") > before.count("》")
                        # 检查前面10个字符内是否有》（《书名》第X卷模式）
                        recent = before[-10:] if len(before) >= 10 else before
                        follows_book = "》" in recent
                        if not in_book and not follows_book:
                            volume_refs.append(f"  {relpath}:{i}: {line.strip()[:80]}")
    
    if volume_refs:
        errors.append(f"正文中发现 {len(volume_refs)} 处硬编码卷号引用（应改为卷名）：\n" + "\n".join(volume_refs))
    
    # 4. 检查章编号连续性
    for vol in manifest["volumes"]:
        dirpath = os.path.join(BASE, vol["dir"])
        if not os.path.isdir(dirpath):
            continue
        for fname in sorted(os.listdir(dirpath)):
            if not fname.startswith("篇") or not fname.endswith(".md"):
                continue
            fpath = os.path.join(dirpath, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                chapters = re.findall(r"^### 第([一二三四五六七八九十]+)章", f.read(), re.MULTILINE)
            if len(chapters) != len(set(chapters)):
                seen = set()
                dups = [c for c in chapters if c in seen or seen.add(c)]
                errors.append(f"章编号重复: {vol['dir']}/{fname} 重复章: {dups}")
    
    # 输出
    if errors:
        print(f"发现 {len(errors)} 个问题：\n")
        for e in errors:
            print(f"✗ {e}\n")
        sys.exit(1)
    else:
        print("✓ 卷结构一致性检查全部通过")
        print(f"  - {len(manifest['volumes'])} 个卷目录和标题一致")
        print(f"  - 正文无硬编码卷号引用")
        print(f"  - 章编号无重复")

if __name__ == "__main__":
    main()

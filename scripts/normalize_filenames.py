#!/usr/bin/env python3
"""
文件名吸附器 v1.0 — 自动检测并修复不规范的篇文件名
用法：
  python3 scripts/normalize_filenames.py          # 预览模式（只报告不执行）
  python3 scripts/normalize_filenames.py --apply   # 实际执行git mv + 标题修复
"""
import re, sys, subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BOOK = REPO / "生命论_模块化"
CN = {"零":0,"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10,"十一":11,"十二":12}
APPLY = "--apply" in sys.argv

def compute_new_name(stem):
    """计算规范文件名，返回(new_stem, label)或None"""
    # 已经规范
    if re.match(r'^\d{2}(-\d)?[_]', stem) or stem.startswith("00_"):
        return None
    # 篇X之Y
    m = re.match(r"篇([零一二三四五六七八九十]+)(?:之([零一二三四五六七八九十]+))?_(.+)", stem)
    if m:
        main = CN.get(m.group(1), 99)
        sub = CN.get(m.group(2)) if m.group(2) else None
        rest = m.group(3)
        if sub is not None:
            ns = f"{main:02d}-{sub}_篇{m.group(1)}之{m.group(2)}_{rest}"
            label = (f"第{m.group(1)}篇之{m.group(2)}" if m.group(1) != "零" else f"篇零之{m.group(2)}")
        else:
            ns = f"{main:02d}_篇{m.group(1)}_{rest}"
            label = (f"第{m.group(1)}篇" if m.group(1) != "零" else "篇零")
        return ns, label
    # 附录X
    m = re.match(r"附录([一二三四五六七八九十]+)_(.+)", stem)
    if m:
        num = CN.get(m.group(1), 99)
        ns = f"{num:02d}_附录{m.group(1)}_{m.group(2)}"
        return ns, f"附录{m.group(1)}"
    return None

def fix_heading(content, label):
    """统一文件第一个标题的篇号"""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            title = re.sub(r'^第[零一二三四五六七八九十]+篇(?:之[零一二三四五六七八九十]+)?\s*', '', title)
            title = re.sub(r'^篇[零一二三四五六七八九十]+(?:之[零一二三四五六七八九十]+)?\s*', '', title)
            title = re.sub(r'^附录[一二三四五六七八九十]+\s*', '', title)
            lines[i] = f"{'#' * level} {label} {title}"
            break
    return "\n".join(lines)

def main():
    changes = []
    for vol in sorted(BOOK.iterdir()):
        if not vol.is_dir() or vol.name == "项目文档": continue
        for f in sorted(vol.glob("*.md")):
            result = compute_new_name(f.stem)
            if not result: continue
            new_stem, label = result
            new_name = new_stem + f.suffix
            if new_name == f.name: continue
            changes.append((f, vol / new_name, label))

    if not changes:
        print("✅ 所有文件名已规范，无需吸附")
        return

    print(f"发现 {len(changes)} 个不规范文件：\n")
    for old, new, label in changes:
        print(f"  {old.parent.name}/")
        print(f"    {old.name}")
        print(f"    → {new.name}")

    if not APPLY:
        print(f"\n预览模式，加 --apply 执行")
        return

    print(f"\n执行吸附...")
    renamed = 0; headings = 0
    for old, new, label in changes:
        content = old.read_text(encoding="utf-8")
        fixed = fix_heading(content, label)
        if fixed != content:
            old.write_text(fixed, encoding="utf-8")
            headings += 1
        r = subprocess.run(["git", "mv", str(old), str(new)],
                         capture_output=True, text=True, cwd=str(REPO))
        if r.returncode == 0: renamed += 1
        else: print(f"  ❌ {old.name}: {r.stderr.strip()}")

    print(f"\n✅ 改名 {renamed} 个，标题修复 {headings} 个")

if __name__ == "__main__":
    main()

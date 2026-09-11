#!/usr/bin/env python3
"""
生命论合订本生成器 v2.1 — 标题精确修复
修复：子篇标题加篇号、附录排序、去掉篇目目录页、卷标题只留H1
"""
import os, re, sys
from pathlib import Path
from datetime import datetime

REPO = Path("/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun")
BOOK_DIR = REPO / "生命论_模块化"
OUT = REPO / "build_output"
OUT.mkdir(exist_ok=True)

VOLUMES = [
    "00_卷首_命经", "01_卷一_存在论", "02_卷二_操作论", "03_卷三_认识论",
    "04_卷四_实践论", "05_卷五_群己论", "06_卷六_异化论", "07_卷七_解放论",
    "08_卷八_格物论", "09_卷九_人文论", "10_卷十_传统论", "11_卷十一_践演论", "12_附录",
]
FRONT_MATTER = ["00_全书导言.md", "00_体系总纲.md", "00_推导链总览.md"]
TAIL_MATTER = ["00_尾声.md"]
CN = {"零":0,"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10,"十一":11,"十二":12}

def chapter_sort_key(f):
    """排序键：优先按数字前缀（新命名），兼容旧中文篇号（吸附功能）"""
    name = f.stem
    # 新命名：00_卷标题 / 01_篇一 / 01a_篇一之二（a=子篇1, b=子篇2...）
    m = re.match(r"(\d{2})([a-z])?[_]", name)
    if m:
        main = int(m.group(1))
        sub = ord(m.group(2)) - ord('a') + 1 if m.group(2) else 0
        return (0, main, sub, name)
    # 旧命名兼容：00_开头
    if name.startswith("00_"): return (0, 0, 0, name)
    # 旧命名：篇X之Y
    m = re.match(r"篇([零一二三四五六七八九十]+)(?:之([零一二三四五六七八九十]+))?", name)
    if m:
        main = CN.get(m.group(1), 99)
        sub = CN.get(m.group(2), 0) if m.group(2) else 0
        return (1, main, sub, name)
    # 旧命名：附录X
    m = re.match(r"附录([一二三四五六七八九十]+)", name)
    if m: return (1, CN.get(m.group(1),99), 0, name)
    return (2, 0, 0, name)

def extract_chapter_label(filename):
    """从文件名提取篇号标签，兼容新(01_篇一)旧(篇一)命名"""
    # 新命名：01_篇一 / 01-2_篇一之二
    m = re.search(r"(篇[零一二三四五六七八九十]+(?:之[零一二三四五六七八九十]+)?)", filename)
    return m.group(1) if m else None

def extract_appendix_label(filename):
    m = re.search(r"(附录[一二三四五六七八九十]+)", filename)
    return m.group(1) if m else None

def strip_meta_notes(content):
    lines = content.split("\n")
    result = []
    for line in lines:
        s = line.strip()
        if re.match(r'^[-*]\s+\*\*状态\*\*', s) and ("待入全本" in s or "待核实" in s): continue
        if re.match(r'^>\s*\*\*状态\*\*', s) and ("待入全本" in s or "待核实" in s): continue
        result.append(line)
    return "\n".join(result)

def process_vol_title(content):
    """卷标题文件：只保留H1和引言，去掉'## 篇目'及后面的目录列表"""
    lines = content.split("\n")
    result = []
    in_toc = False
    for line in lines:
        if re.match(r'^##\s*篇目', line.strip()):
            in_toc = True
            continue
        if in_toc:
            # 跳过目录列表，直到下一个标题或空行后有内容
            if line.strip() and not line.strip().startswith("-") and not line.strip().startswith("*"):
                in_toc = False
            else:
                continue
        result.append(line)
    return "\n".join(result)

def fix_chapter_heading(content, filename):
    """修复篇标题：用文件名的篇号为准，统一格式为'第一篇'/'第一篇之二'/'附录四'"""
    # 从文件名提取篇号
    label = extract_chapter_label(filename)
    is_appendix = False
    if not label:
        label = extract_appendix_label(filename)
        is_appendix = True
    if not label:
        return content

    # 转换为标准格式：篇一 → 第一篇，篇一之二 → 第一篇之二
    if not is_appendix:
        m = re.match(r"篇([零一二三四五六七八九十]+)(?:之([零一二三四五六七八九十]+))?", label)
        if m:
            main = m.group(1)
            sub = m.group(2)
            if main == "零":
                label = f"篇零" if not sub else f"篇零之{sub}"
            else:
                label = f"第{main}篇" if not sub else f"第{main}篇之{sub}"

    lines = content.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            # 去掉标题中已有的篇号（第一篇/篇一/附录X等）
            title = re.sub(r'^第[零一二三四五六七八九十]+篇(?:之[零一二三四五六七八九十]+)?\s*', '', title)
            title = re.sub(r'^篇[零一二三四五六七八九十]+(?:之[零一二三四五六七八九十]+)?\s*', '', title)
            title = re.sub(r'^附录[一二三四五六七八九十]+\s*', '', title)
            # 新标题：标准篇号 + 文章名
            new_title = f"{'#' * level} {label} {title}"
            lines[i] = new_title
            break
    return "\n".join(lines)

def normalize_headings(content, target_level=2):
    lines = content.split("\n")
    first_level = None
    for line in lines:
        m = re.match(r"^(#{1,6})\s", line.strip())
        if m: first_level = len(m.group(1)); break
    if first_level is None: return content
    diff = target_level - first_level
    if diff == 0: return content
    result = []
    for line in lines:
        m = re.match(r"^(#{1,6})(\s)", line)
        if m:
            new_level = max(1, len(m.group(1)) + diff)
            line = "#" * new_level + m.group(2) + line[len(m.group(1))+1:]
        result.append(line)
    return "\n".join(result)

def clean_control_chars(text):
    return ''.join(c for c in text if ord(c) >= 32 or c in '\n\r\t')

def build():
    parts = []
    stats = {"volumes": [], "total_files": 0, "total_chars": 0}
    date_str = datetime.now().strftime("%Y-%m-%d")

    parts.append(f"""# 生命论（明本论）· 合订本

生成时间：{date_str}
作者：北原慢热
来源：https://github.com/192781-li/mingbenlun
12卷+卷首+尾声，按卷→篇→子篇顺序合并。
已过滤研究笔记状态标注，输出干净全本。
标题层级：卷=H1，篇=H2，章=H3。

---

""")

    for fm in FRONT_MATTER:
        fp = BOOK_DIR / fm
        if fp.exists():
            content = clean_control_chars(fp.read_text(encoding="utf-8"))
            content = strip_meta_notes(content)
            content = normalize_headings(content, target_level=2)
            parts.append(content); parts.append("\n\n---\n\n")
            stats["total_files"] += 1; stats["total_chars"] += len(content)

    for vol_name in VOLUMES:
        vol_dir = BOOK_DIR / vol_name
        if not vol_dir.exists():
            print(f"  ⚠️  卷目录不存在: {vol_name}"); continue
        files = sorted([f for f in vol_dir.glob("*.md") if f.is_file()], key=chapter_sort_key)
        vol_chars = 0; vol_files = 0
        for f in files:
            content = clean_control_chars(f.read_text(encoding="utf-8"))
            content = strip_meta_notes(content)
            is_vol_title = f.name in ("00_卷标题.md", "00_附录标题.md")
            if is_vol_title:
                content = process_vol_title(content)
                content = normalize_headings(content, target_level=1)
            else:
                content = fix_chapter_heading(content, f.name)
                content = normalize_headings(content, target_level=2)
            parts.append(content); parts.append("\n\n")
            vol_chars += len(content); vol_files += 1
            stats["total_files"] += 1; stats["total_chars"] += len(content)
        stats["volumes"].append((vol_name, vol_files, vol_chars))
        print(f"  {vol_name}: {vol_files}篇, {vol_chars:,}字")

    for tm in TAIL_MATTER:
        fp = BOOK_DIR / tm
        if fp.exists():
            content = clean_control_chars(fp.read_text(encoding="utf-8"))
            content = strip_meta_notes(content)
            content = normalize_headings(content, target_level=2)
            parts.append(content)
            stats["total_files"] += 1; stats["total_chars"] += len(content)

    combined = "".join(parts)

    # ═══ 验证 ═══
    print(f"\n=== 构建后验证 ===")
    errors = []
    ctrl = [c for c in combined if ord(c) < 32 and c not in '\n\r\t']
    if ctrl: errors.append(f"存在{len(ctrl)}个控制字符")
    else: print("  ✅ 无控制字符")

    expected_vols = ["卷首 命经","第一卷","第二卷","第三卷","第四卷","第五卷",
                     "第六卷","第七卷","第八卷","第九卷","第十卷","第十一卷","附录"]
    missing = [v for v in expected_vols if f"# {v}" not in combined]
    if missing: errors.append(f"缺少卷: {missing}")
    else: print("  ✅ 13卷齐全")

    if "待入全本" in combined: errors.append(f"存在{combined.count('待入全本')}处'待入全本'")
    else: print("  ✅ 无'待入全本'标注")

    h1_count = len(re.findall(r'^# ', combined, re.MULTILINE))
    if h1_count != 14: errors.append(f"H1数量={h1_count}, expected 14")
    else: print("  ✅ H1数量=14")

    # 检查"篇目"是否还存在
    if re.search(r'^## 篇目', combined, re.MULTILINE):
        errors.append("仍存在'## 篇目'目录页")
    else: print("  ✅ 无'篇目'目录页")

    # 检查卷六子篇标题是否有篇号
    vol6_start = combined.find("# 第六卷")
    vol7_start = combined.find("# 第七卷")
    if vol6_start > 0 and vol7_start > 0:
        vol6 = combined[vol6_start:vol7_start]
        # 子篇应该有"篇零"、"篇一之二"等前缀
        if "篇零" not in vol6:
            errors.append("卷六缺少'篇零'标题")
        if "篇一之二" not in vol6:
            errors.append("卷六缺少'篇一之二'标题")
        if "篇二之二" not in vol6:
            errors.append("卷六缺少'篇二之二'标题")
        if not any(e.startswith("卷六") for e in errors):
            print("  ✅ 卷六子篇标题正确")

    # 检查附录顺序
    app_start = combined.find("# 附录")
    if app_start > 0:
        app = combined[app_start:]
        app_h2s = re.findall(r'^## (附录[一二三四五六七八九十]+)', app, re.MULTILINE)
        expected_app = ["附录一","附录二","附录三","附录四","附录五","附录六","附录七"]
        if app_h2s != expected_app[:len(app_h2s)]:
            errors.append(f"附录顺序错误: {app_h2s}")
        else:
            print(f"  ✅ 附录顺序正确: {app_h2s}")

    if errors:
        print(f"\n❌ 验证失败:")
        for e in errors: print(f"  - {e}")
        sys.exit(1)

    md_path = OUT / "生命论_合订本.md"
    md_path.write_text(combined, encoding="utf-8")
    txt_path = OUT / "生命论_合订本.txt"
    txt = re.sub(r'[#*>`\[\]()]', '', combined)
    txt_path.write_text(txt, encoding="utf-8")

    print(f"\n✅ 合订本生成完成")
    print(f"  文件数: {stats['total_files']}")
    print(f"  总字符: {stats['total_chars']:,}")
    return stats

if __name__ == "__main__":
    build()

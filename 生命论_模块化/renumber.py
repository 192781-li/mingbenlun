#!/usr/bin/env python3
"""重新编号全本章节。读取manifest.txt中所有文件，按顺序找到### 第X章，重新编号。"""
import re
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(SCRIPT_DIR, "manifest.txt")

# 中文数字
CN = "零一二三四五六七八九"

def int2cn(n):
    if n <= 10:
        return CN[n] if n < 10 else "十"
    if n < 20:
        return "十" + CN[n - 10]
    if n < 100:
        tens = n // 10
        ones = n % 10
        return CN[tens] + "十" + (CN[ones] if ones else "")
    if n < 1000:
        hundreds = n // 100
        rest = n % 100
        result = CN[hundreds] + "百"
        if rest == 0:
            return result
        if rest < 10:
            return result + "零" + CN[rest]
        if rest == 10:
            return result + "一十"
        if rest < 20:
            return result + "一十" + CN[rest - 10]
        tens = rest // 10
        ones = rest % 10
        return result + CN[tens] + "十" + (CN[ones] if ones else "")
    return str(n)

def cn2int(s):
    """简单中文数字转int，支持到999"""
    if not s:
        return 0
    # 纯数字
    if s.isdigit():
        return int(s)
    result = 0
    if "百" in s:
        parts = s.split("百")
        result += CN.index(parts[0]) * 100
        s = parts[1] if len(parts) > 1 else ""
        if s.startswith("零"):
            s = s[1:]
    if "十" in s:
        parts = s.split("十")
        if parts[0]:
            result += CN.index(parts[0]) * 10
        else:
            result += 10
        s = parts[1] if len(parts) > 1 else ""
    if s and s in CN:
        result += CN.index(s)
    return result

def main():
    with open(MANIFEST, 'r', encoding='utf-8') as f:
        files = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    chapter_re = re.compile(r'^### 第([一二三四五六七八九十百零\d]+)章\s*(.*)$')

    total = 0
    changes = []

    for relpath in files:
        filepath = os.path.join(SCRIPT_DIR, relpath)
        if not os.path.exists(filepath):
            print(f"警告：文件不存在 {relpath}")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        modified = False
        for i, line in enumerate(lines):
            m = chapter_re.match(line)
            if m:
                total += 1
                old_num = cn2int(m.group(1))
                new_num = total
                old_cn = m.group(1)
                new_cn = int2cn(new_num)
                title = m.group(2)

                if old_cn != new_cn:
                    lines[i] = f"### 第{new_cn}章 {title}\n"
                    modified = True
                    changes.append(f"{relpath}: 第{old_cn}章→第{new_cn}章 {title[:20]}")

        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)

    print(f"共 {total} 章")
    for c in changes:
        print(c)
    if not changes:
        print("编号无需调整")

if __name__ == "__main__":
    main()

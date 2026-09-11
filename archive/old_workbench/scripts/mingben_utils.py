#!/usr/bin/env python3
"""
明本共享工具库
统一所有脚本中重复的工具函数，消除代码重复。
用法：from mingben_utils import cn2int, int2cn, read_text, ...
"""
import re
import os
import sys
from pathlib import Path
from collections import Counter

# ========== 路径锚定 ==========
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
WORKSPACE = SKILL_DIR.parent
MODDIR = WORKSPACE / "生命论_模块化"
FULL_MD = WORKSPACE / "生命论合订本_最新.md"

# ========== 中文数字转换 ==========
CN_DIGITS = {'零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4,
             '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
CN_UNITS = {'十': 10, '百': 100, '千': 1000}


def cn2int(s):
    """中文数字转int，支持到九千九百九十九。无法解析返回None。"""
    if not s:
        return 0
    if s.isdigit():
        return int(s)
    result = 0
    current = 0
    for ch in s:
        if ch in CN_DIGITS:
            current = CN_DIGITS[ch]
        elif ch in CN_UNITS:
            if current == 0:
                current = 1
            result += current * CN_UNITS[ch]
            current = 0
        else:
            return None
    result += current
    return result


def int2cn(n):
    """int转中文数字，支持到9999。"""
    if n < 0:
        return '负' + int2cn(-n)
    if n < 10:
        return '零一二三四五六七八九'[n]
    if n < 20:
        return '十' + ('零一二三四五六七八九'[n - 10] if n > 10 else '')
    if n < 100:
        tens, ones = divmod(n, 10)
        return '零一二三四五六七八九'[tens] + '十' + (
            '零一二三四五六七八九'[ones] if ones else '')
    if n < 1000:
        hundreds, rest = divmod(n, 100)
        s = '零一二三四五六七八九'[hundreds] + '百'
        if rest == 0:
            return s
        if rest < 10:
            return s + '零' + '零一二三四五六七八九'[rest]
        return s + int2cn(rest)
    if n < 10000:
        thousands, rest = divmod(n, 1000)
        s = '零一二三四五六七八九'[thousands] + '千'
        if rest == 0:
            return s
        if rest < 100:
            return s + '零' + int2cn(rest)
        return s + int2cn(rest)
    return str(n)


# ========== 文件读写 ==========
def read_text(path):
    """安全读取文本文件，自动处理编码。"""
    p = Path(path)
    if not p.exists():
        return None
    return p.read_text(encoding='utf-8', errors='replace')


def write_text(path, content):
    """写入文本文件，自动创建目录。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')


# ========== 章节解析 ==========
CHAPTER_RE = re.compile(r'^###\s*(第([一二三四五六七八九十百零两\d]+)章)\s*(.*?)$', re.MULTILINE)


def parse_chapters(text):
    """解析文本中的所有章节，返回 [{num, title, start, end}]。"""
    chapters = []
    matches = list(CHAPTER_RE.finditer(text))
    for i, m in enumerate(matches):
        num = cn2int(m.group(2))
        title = m.group(3).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapters.append({'num': num, 'title': title, 'start': start, 'end': end})
    return chapters


def get_chapter_count(text=None):
    """获取合订本实际章数。"""
    if text is None:
        text = read_text(FULL_MD)
    if text is None:
        return None
    return len(re.findall(r'^### 第[零一二三四五六七八九十百千两]+章', text, re.MULTILINE))


# ========== manifest操作 ==========
def load_manifest():
    """加载manifest，返回文件路径列表。"""
    manifest = MODDIR / "manifest.txt"
    if not manifest.exists():
        return []
    return [l.strip() for l in manifest.read_text(encoding='utf-8').splitlines()
            if l.strip() and not l.startswith('#')]


# ========== 文本质量检查 ==========
def check_garbled(text):
    """检查乱码字符，返回乱码数量。"""
    return len(re.findall(r'[\ufffd\u0000-\u0008\u000b\u000c\u000e-\u001f]', text))


def check_unclosed_bold(text):
    """检查未闭合的加粗标记，返回行号列表。"""
    bad = []
    for i, line in enumerate(text.split('\n'), 1):
        if line.count('**') % 2 != 0:
            bad.append((i, line.strip()[:60]))
    return bad


def find_duplicate_paragraphs(text, min_len=50):
    """查找重复段落，返回 {hash: count}。"""
    import hashlib
    counter = Counter()
    for para in re.split(r'\n\s*\n', text):
        p = para.strip()
        if len(p) > min_len:
            counter[hashlib.md5(p.encode()).hexdigest()] += 1
    return {h: c for h, c in counter.items() if c > 1}


# ========== 人类可读大小 ==========
def human_size(n):
    """字节数转人类可读格式。"""
    for unit in ['B', 'K', 'M', 'G', 'T', 'P', 'E']:
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.0f}Z"


# ========== 计时工具 ==========
import time


class Timer:
    """简易计时器，用于性能监控。"""

    def __init__(self, name=""):
        self.name = name
        self.start = None
        self.elapsed = 0

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.elapsed = time.time() - self.start
        if self.name:
            print(f"  ⏱ {self.name}: {self.elapsed:.3f}s")


# ========== 并行执行工具 ==========
from concurrent.futures import ThreadPoolExecutor, as_completed


def run_parallel(funcs, max_workers=8):
    """并行执行无参数函数列表，返回结果列表（按输入顺序）。"""
    results = [None] * len(funcs)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {executor.submit(fn): i for i, fn in enumerate(funcs)}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                results[idx] = e
    return results


# ========== 自检 ==========
if __name__ == '__main__':
    # 中文数字转换测试
    test_cases = [
        ('一', 1), ('十', 10), ('十一', 11), ('二十', 20),
        ('二十五', 25), ('一百', 100), ('一百零一', 101),
        ('一百一十', 110), ('二百三十四', 234), ('一千', 1000),
        ('一千零一', 1001), ('一千二百三十四', 1234), ('两', 2),
    ]
    passed = 0
    failed = 0
    for cn, expected in test_cases:
        result = cn2int(cn)
        back = int2cn(expected)
        ok = result == expected
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"  ❌ cn2int('{cn}')={result}, 期望{expected}")
    print(f"中文数字转换: {passed}通过, {failed}失败")
    print(f"工作区: {WORKSPACE}")
    print(f"模块目录: {MODDIR}")
    print(f"合订本: {'存在' if FULL_MD.exists() else '不存在'}")

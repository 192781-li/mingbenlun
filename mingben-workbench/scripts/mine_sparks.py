#!/usr/bin/env python3
"""
闪光点挖掘器。
扫描项目所有md/txt文件，用模式匹配找出潜在的洞见表述。
输出候选列表供人工筛选，不自动录入闪光点.md。
"""
import re
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent
SCAN_DIRS = [
    WORKSPACE / "生命论_模块化",
    WORKSPACE / ".sessions/38435926642711810/attachments",
]
SCAN_EXTS = {".md", ".txt"}
OUTPUT_FILE = Path(__file__).parent.parent / "references" / "spark_candidates.md"

# 已有闪光点的关键句（去重用）
EXISTING = Path(WORKSPACE / "闪光点.md")

# 洞见模式
PATTERNS = [
    (r"^[^#\n].*——[^—].*$", "破折号定义式"),  # X——Y 定义式
    (r"^[^#\n].*不是.{1,30}[，,].*是.{1,50}$", "不是…是…式"),
    (r"^[^#\n>].*在于.{1,60}$", "在于判断式"),
    (r"^> .{10,}$", "引用块"),
    (r"^[^#\n].*本质(上|是|就).{1,60}$", "本质判断"),
    (r"^[^#\n].*根本(上|是|就).{1,60}$", "根本判断"),
    (r"^[^#\n].*真正(的|地).{1,60}$", "真正判断"),
    (r"^[^#\n].*绝不[^。]{1,40}。$", "绝不式"),
    (r"^[^#\n].*即[^。]{1,40}。$", "即是式"),
    (r"^[^#\n].*无非[^。]{1,40}。$", "无非式"),
    (r"^[^#\n].*只不过[^。]{1,40}。$", "只不过式"),
]

def load_existing_phrases():
    """加载已有闪光点中的关键短语用于去重"""
    phrases = set()
    if EXISTING.exists():
        text = EXISTING.read_text(encoding="utf-8")
        # 提取加粗内容和引用内容
        for m in re.finditer(r'\*\*(.+?)\*\*', text):
            phrases.add(m.group(1)[:30])
        for m in re.finditer(r'^> ?(.+)$', text, re.M):
            phrases.add(m.group(1)[:30])
    return phrases

def scan_file(filepath, existing):
    candidates = []
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return candidates
    
    lines = text.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            continue
        if len(stripped) < 8 or len(stripped) > 200:
            continue
        
        for pattern, ptype in PATTERNS:
            if re.match(pattern, stripped):
                # 去重：检查是否已在闪光点中
                short = stripped[:30]
                dup = False
                for ep in existing:
                    if ep in stripped or short[:20] in ep:
                        dup = True
                        break
                if not dup:
                    # 过滤掉明显的目录、引用文献、代码
                    if any(skip in stripped for skip in ["http://", "https://", "```", "|", "---"]):
                        continue
                    rel = filepath.relative_to(WORKSPACE)
                    candidates.append((str(rel), i, ptype, stripped))
                break
    return candidates

def main():
    existing = load_existing_phrases()
    all_candidates = []
    
    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            continue
        for f in sorted(scan_dir.rglob("*")):
            if f.suffix in SCAN_EXTS and not f.name.startswith("."):
                all_candidates.extend(scan_file(f, existing))
    
    # 按文件分组输出
    by_file = {}
    for path, line, ptype, text in all_candidates:
        by_file.setdefault(path, []).append((line, ptype, text))
    
    out = ["# 闪光点候选\n", f"共扫描出 {len(all_candidates)} 条候选，需人工筛选。\n"]
    for path, items in sorted(by_file.items()):
        out.append(f"\n## {path}（{len(items)}条）\n")
        for line, ptype, text in items:
            out.append(f"- L{line} [{ptype}] {text}")
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(out), encoding="utf-8")
    print(f"扫描完成：{len(all_candidates)} 条候选 → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

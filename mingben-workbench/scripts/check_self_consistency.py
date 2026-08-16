#!/usr/bin/env python3
"""
践演自洽启发式检查（检查5）
扫描全本，寻找"用独断的方式反对独断论"的可疑段落：
- 批判教条/经文/独断的段落，本身是否在用教条语气？
- 批判经文化的段落，是否把自己的概念写成了不可质疑的？
- 论证阳主阴从时，是否用阴（形式结构）完全压过了阳（活操作）？

启发式：只标记同一段落内同时出现"批判词"和"独断词"的情况，需人工判断。
"""

import re
import sys
from pathlib import Path

MODULES_DIR = Path(__file__).parent.parent.parent / "生命论_模块化"

# 批判词：表示这段在批判独断/教条/经文化
CRITIQUE_WORDS = ["教条", "经文", "独断", "经文化", "教条主义", "本本主义", "造神", "新的神"]

# 独断词：表示这段在用独断语气（只保留最明确的）
DOGMATIC_WORDS = [
    "不容置疑", "不可动摇", "唯一正确", "永远正确",
    "无可辩驳", "毋庸置疑地", "必须无条件", "不容讨论", "不许质疑",
]

# 强规范词（需要更多上下文判断，只在和批判词同段时标记）
STRONG_NORMATIVE = ["绝不能", "绝不允许", "必须彻底", "必须坚决"]

# 表示"在描述别人立场"的标记（出现这些词时，独断词是被描述的对象）
DESCRIPTION_MARKERS = [
    "说成", "当成", "叫作", "称为", "宣称", "鼓吹", "扬言",
    "他们把", "把它", "被神话化", "认为", "以为", "声称",
    "教条主义", "绝对主义", "独断论", "经文化",
    "统治阶级", "资产阶级", "反动派", "敌人",
]

# 引号对
QUOTE_CHARS = [("\u201c", "\u201d"), ("\"", "\""), ("'", "'"), ("「", "」")]


def get_paragraphs(filepath):
    """按空行分段"""
    content = filepath.read_text(encoding="utf-8")
    paragraphs = re.split(r"\n\s*\n", content)
    return [(p.strip(), filepath.name) for p in paragraphs if p.strip()]


def check_paragraph(paragraph, filename):
    """检查一个段落是否有践演不自洽的可疑模式"""
    findings = []

    has_critique = any(w in paragraph for w in CRITIQUE_WORDS)
    if not has_critique:
        return findings

    # 否定前缀：如果独断词前面是否定词，说明是在否定它，不是在使用它
    negations = ["不", "没", "无", "非", "别", "莫", "勿"]
    # 引用/描述前缀：如果独断词出现在这些语境中，是在描述别人的立场
    quote_markers = ["说成", "当成", "叫作", "称为", "宣称", "鼓吹", "扬言", "认为", "他们把", "把它", "被神话化"]

    def is_negated_or_quoted(text, word, idx):
        """检查独断词是否处于否定、引用或描述他人立场的语境中"""
        before = text[max(0, idx - 15):idx]
        after = text[idx + len(word):idx + len(word) + 15]

        # 否定语境（向前看15个字符）
        for neg in ["不", "没", "无", "非", "别", "莫", "勿"]:
            if neg in before[-5:]:
                return True
        # "不是...而是..." 结构
        if "不是" in before or "并非" in before:
            return True

        # 引用语境：检查是否在引号内
        for lq, rq in QUOTE_CHARS:
            if lq == rq:
                # 同字符引号（如ASCII"）：前面出现奇数次=在引号内
                if text[:idx].count(lq) % 2 == 1:
                    return True
            else:
                # 异字符引号（如中文""）：左引号多于右引号=在引号内
                if text[:idx].count(lq) - text[:idx].count(rq) > 0:
                    return True
        # 紧邻引号（5字符内有引号）也算引用
        nearby = text[max(0, idx - 5):idx]
        if any(q in nearby for q in ['\u201c', '"', '\u300c', "'"]):
            return True

        # 描述他人立场的语境（向前看15个字符）
        for marker in DESCRIPTION_MARKERS:
            if marker in before:
                return True

        # 向后看：如果后面跟着"是错误的""是有害的"等否定评价
        for neg_eval in ["是错误", "是有害", "是荒谬", "是反动", "行不通", "要不得"]:
            if neg_eval in after:
                return True

        return False

    # 检查1：批判独断但自己用独断词
    for word in DOGMATIC_WORDS:
        start = 0
        while True:
            idx = paragraph.find(word, start)
            if idx == -1:
                break
            if not is_negated_or_quoted(paragraph, word, idx):
                context = paragraph[max(0, idx - 30):idx + len(word) + 30].replace("\n", " ")
                findings.append(
                    f"[以独断反独断?] {filename}: ...{context}..."
                )
            start = idx + len(word)

    # 检查2：批判经文化但把自己的概念说成不可质疑
    # 更紧的模式：概念+是+不可质疑/不容怀疑（概念是主语，不是句子中随便出现的）
    book_concepts = ["操作", "自指", "明性", "感", "生命论", "阳主阴从", "践演坐实"]
    for concept in book_concepts:
        pattern = rf"{concept}(是|就是|乃是|永远是|绝对是)[^。！？\n]*(不可质疑|不可怀疑|不能否定|不容反驳|不容置疑)"
        for m in re.finditer(pattern, paragraph):
            idx = m.start()
            if not is_negated_or_quoted(paragraph, concept, idx):
                context = paragraph[max(0, idx - 20):m.end() + 20].replace("\n", " ")
                findings.append(
                    f"[概念独断化?] {filename}: ...{context}..."
                )

    # 检查3：强规范词在批判段落中（低可疑度）
    for word in STRONG_NORMATIVE:
        start = 0
        while True:
            idx = paragraph.find(word, start)
            if idx == -1:
                break
            if not is_negated_or_quoted(paragraph, word, idx):
                context = paragraph[max(0, idx - 30):idx + len(word) + 30].replace("\n", " ")
                findings.append(
                    f"[强规范词(低可疑)] {filename}: ...{context}..."
                )
            start = idx + len(word)

    return findings


def main():
    if not MODULES_DIR.exists():
        print(f"模块目录不存在: {MODULES_DIR}")
        return 1

    all_findings = []
    files_checked = 0

    for md_file in sorted(MODULES_DIR.rglob("*.md")):
        files_checked += 1
        for para, filename in get_paragraphs(md_file):
            all_findings.extend(check_paragraph(para, filename))

    print(f"践演自洽检查：扫描了 {files_checked} 个文件")

    if all_findings:
        # 分离高可疑和低可疑
        high = [f for f in all_findings if "低可疑" not in f]
        low = [f for f in all_findings if "低可疑" in f]

        print(f"发现 {len(high)} 个高可疑项、{len(low)} 个低可疑项：")
        for f in all_findings:
            marker = "⚠" if "低可疑" in f else "✗"
            print(f"  {marker} {f}")
        return 1
    else:
        print("✓ 全部通过：未发现以独断反独断、概念独断化的可疑模式")
        return 0


if __name__ == "__main__":
    sys.exit(main())

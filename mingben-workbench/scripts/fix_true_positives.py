#!/usr/bin/env python3
"""处理人工复核确认的真问题"""
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "生命论_模块化" / "00_推导链总览.md"
text = path.read_text(encoding="utf-8")

# 1. 科学理论支撑小结正文补标注
old1 = "本套推演并非纯粹哲学思辨，建立在若干跨学科研究成果之上。"
new1 = "本套推演并非纯粹哲学思辨，建立在若干跨学科研究成果之上。【经验】"
if old1 in text and new1 not in text:
    text = text.replace(old1, new1, 1)
    print("行354已标注")

# 2. 行167真问题：继续革命段落加中介显式化
old2 = "**继续革命的存在论根据：** 因为反自指可以从任何操作关系中化生（资本是化生的），所以革命不是一次性事件，是持续的实践。"
new2 = ("**继续革命的存在论根据：** 因为反自指可以从任何操作关系中化生（资本是化生的），"
        "所以革命不是一次性事件，是持续的实践。【社\u00b7经验+\u22a9\u2098决断】"
        "（注：存在论提供\u201c根据\u201d而非\u201c命令\u201d\u2014\u2014"
        "\u201c反自指可化生\u201d是存在论命题，\u201c继续革命\u201d是阶级决断，"
        "二者之间的\u22a9\u2098中介需显式：因为选择站在劳动者一边【决断】，"
        "才必须持续对抗反自指的再生。）")
if old2 in text and new2 not in text:
    text = text.replace(old2, new2, 1)
    print("行167中介已显式化")
elif new2 in text:
    print("行167已处理")
else:
    print("行167未找到原文")

path.write_text(text, encoding="utf-8")
print("完成")

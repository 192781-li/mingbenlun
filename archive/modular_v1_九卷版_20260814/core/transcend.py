"""transcend.py — 超越实体本体论：以操作一元取代实体一元

本模块将"超越前人"落到可运行对照：
- 巴门尼德（实体/to eon）→ 操作 primordial：实体是稳定操作的抽象
- 康德（先验统觉"我思"）→ 缄默意识：前反思第一人称操作，范畴由操作沉淀
- 黑格尔（绝对精神）→ 一元无实体 S=f(S)：过程非实体、无目的论
- 马克思（劳动价值实体）→ 操作四规定性：价值根于自指操作而非劳动实体

超越不是喊口号，而是把实体/概念还原为操作的可溯源结构。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Ontology:
    name: str
    base: str  # 本体论基底
    needs_substance: bool
    teleology: bool  # 是否有目的论


ENTITY = Ontology("实体本体论(巴门尼德/黑格尔)", "不变实体/绝对精神", True, True)
OPERATION = Ontology("操作存在论(本书)", "操作 S=f(S) 自指闭环", False, False)


def transcend_report() -> List[str]:
    """逐位前人，给出"如何超越"的具体（小本质）论证。"""
    return [
        "超越巴门尼德：'实体'(to eon) 非基底，而是稳定循环操作的人为抽象；操作先于实体。",
        "超越康德：先验统觉'我思'是静态逻辑条件；缄默意识是前反思第一人称操作，"
        "范畴由操作沉淀而非先天。",
        "超越黑格尔：绝对精神是实体+目的论的最终形态；本书以'一元而无实体'的自指过程"
        "取代之，无精神上升螺旋、无历史目的论。",
        "超越马克思：劳动价值论仍以'劳动'为价值实体；本书以操作四规定性"
        "(分己/为己/自为/主动)为根，价值根于自指维持而非劳动实体。",
        "超越一切实体与概念：名(概念)是操作的沉淀，须受名实判据约束，"
        "不得凝成新实体（防止'操作'自身被神化）。",
    ]


def superiority(o: Ontology) -> str:
    if o.needs_substance:
        return "依赖不可证成的实体基底/目的论预设"
    return "仅以可观察的操作闭环为基底，无悬设"

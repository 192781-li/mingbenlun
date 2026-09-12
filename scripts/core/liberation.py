"""liberation.py — 解放三阶：解蔽 → 收权 → 集体实践

对应总纲：解放不是个体独享，而是火种共通——"应"使个体之火
汇聚为集体自觉之能，共同改造社会/符号层阴性约束。
"""
from __future__ import annotations

from typing import List


STAGES = ["解蔽", "收权", "集体实践"]


def liberation_three_stages() -> List[str]:
    return list(STAGES)


def collective_energy(agents: int) -> float:
    """个体之火互通交融，集体自觉之能随联合主体数非线性增长。"""
    if agents < 0:
        raise ValueError("主体数不能为负")
    return agents ** 1.5

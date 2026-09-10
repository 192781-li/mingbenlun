"""modality.py — 三模态：必 / 可 / 能

必：阴锁死唯一路径，无选择（无机物、f1 多数状态）
可：阴提供多条并行路径，浅层选择（动物、人日常浅层抉择）
能：主体自觉审视并改造创造（仅 f3 人类拥有自觉之能）
"""
from __future__ import annotations

from enum import Enum
from typing import List


class Modality(Enum):
    BI = "必"  # necessity
    KE = "可"  # possibility
    NENG = "能"  # creative capability


def classify(options: List[str]) -> Modality:
    """由可行路径数量判定模态。

    >>> classify(["唯一路径"])
    <Modality.BI: '必'>
    >>> classify(["A", "B", "C"])
    <Modality.KE: '可'>
    """
    if len(options) <= 1:
        return Modality.BI
    return Modality.KE


def can_transcend(agent_tier: int) -> bool:
    """只有 f3（三阶符号自指）拥有"能"（自觉改造创造）。"""
    return agent_tier >= 3

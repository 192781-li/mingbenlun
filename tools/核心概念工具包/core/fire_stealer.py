"""fire_stealer.py — 生命作为盗火者：创世之能的三重凝聚

第一层（f1）：盗取"区分觉知"——从混沌必然链中截取内在视角
第二层（f2）：盗取"可选可能性"——从单一"必"开辟"可"
第三层（f3）：盗取"重构规则/自我立法"的符号创世之火

全部生命即宇宙层面的盗火者：把原本只潜藏在宇宙底层规则里、
永远无法自行显现的"可能性、能动、觉知、重塑之力"通过自指闭环
截留、收拢、内化，凝聚为属于自身的内在权能。不脱离因果，却超越宿命。
"""
from __future__ import annotations

from typing import Dict, List


class Universe:
    """灰色宇宙：仅他指因果，只有"必"模态，无觉知、无多元可能。"""

    mode = "他指因果"

    def capacities(self) -> List[str]:
        return ["被动流转", "无觉知", "无选择"]


class Life:
    """生命自指闭环：盗火者。"""

    def __init__(self, tier: int):
        self.tier = tier

    def steal_fire(self) -> Dict[str, str]:
        fire: Dict[str, str] = {}
        if self.tier >= 1:
            fire["第一层"] = "盗取区分觉知（f1 完成基础盗取，单细胞已具）"
        if self.tier >= 2:
            fire["第二层"] = "盗取可选可能性（必→可，f2 浅层选择之火）"
        if self.tier >= 3:
            fire["第三层"] = "盗取符号创世之火（自我立法/改造阴/集体创世，f3 终极盗火）"
        return fire


def condensed_creation_energy(tier: int) -> int:
    """凝聚的创世之能随递归层级递增。"""
    return {1: 1, 2: 2, 3: 3}.get(tier, 0)

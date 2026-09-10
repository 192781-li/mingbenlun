"""alienation.py — 异化双维度 + 主动弃火

维度一：感被蔽（缄默觉知被外部概念压制）
维度二：不应（第二人称呼答结构中断，彼此降格为"它"）
唯有持火的 f3 能主动熄灭手中火种——反向佐证创世才能真实存在。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Alienation:
    sense_obscured: bool = False  # 感被蔽
    non_responsive: bool = False  # 不应

    @property
    def is_alienated(self) -> bool:
        return self.sense_obscured or self.non_responsive

    def extinguish_fire(self) -> None:
        """f3 主动交出符号审视权，退回 f2 式被本能/规训支配的状态。"""
        self.sense_obscured = True
        self.non_responsive = True


def can_voluntarily_extinguish(tier: int) -> bool:
    """只有持有完整符号火种的 f3 才有"主动弃火"的资格。"""
    return tier >= 3

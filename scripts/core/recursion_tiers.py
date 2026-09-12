"""recursion_tiers.py — f1/f2/f3 三层递归跃迁与"反思间隙"

- f1 一阶自指：刺激 → 行动（零间隙，无自觉）
- f2 二阶自指：刺激 → 欲望/记忆 → 行动（无审视间隙）
- f3 三阶符号自指：刺激 → 符号审视 → 行动（有反思间隙 = 自由意志根基）

对应总纲：自由是程度概念；f3 的反思间隙是唯物层面自由意志唯一实在根基，
不是脱离因果，而是因果主导权回流至主体自身（自因，非第一因）。
"""
from __future__ import annotations

from typing import Any, Callable


class Agent:
    tier: int = 0

    def __init__(self, name: str):
        self.name = name

    def act(self, stimulus: Any) -> Any:
        raise NotImplementedError

    def reflection_gap(self) -> float:
        """感知与行动之间的可延迟/重构空间，[0,1]。"""
        return 0.0


class F1(Agent):
    tier = 1

    def act(self, stimulus: Any) -> str:
        return f"[{self.name}] 刺激→直接行动"  # 零间隙


class F2(Agent):
    tier = 2

    def act(self, stimulus: Any) -> str:
        desire = f"欲望({stimulus})"
        return f"[{self.name}] {desire}→直接行动"  # 欲望直达行动，无审视间隙

    def reflection_gap(self) -> float:
        return 0.0  # 愿望与行动间无对象化批判


class F3(Agent):
    tier = 3

    def __init__(self, name: str, review: Callable[[Any], Any]):
        super().__init__(name)
        self.review = review

    def act(self, stimulus: Any) -> str:
        reviewed = self.review(stimulus)  # 符号中介审视：延迟、否定、重构
        return f"[{self.name}] 审视({reviewed})→自主抉择→行动"

    def reflection_gap(self) -> float:
        return 1.0  # 存在结构化反思间隙

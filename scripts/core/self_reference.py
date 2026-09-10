"""self_reference.py — 自创生闭环与"活"的判定

生命 = 自指闭环（代谢 + 自我修复的稳定循环操作）。
本模块用最小模型演示：当系统的输出回流为自身下一状态的前置条件，
且能自维持时，即出现"活"（自指）。这把"生命是活的"从格言落成可运行结构。
"""
from __future__ import annotations

from typing import Any, Callable, List


class AutopoieticLoop:
    """极简自创生模型：每步阳（自指修复）与阴（环境耗散）共同作用。

    >>> loop = AutopoieticLoop(repair_rate=0.6, drain=0.2)
    >>> for _ in range(20): loop.step()
    >>> loop.is_alive
    True
    >>> dead = AutopoieticLoop(repair_rate=0.1, drain=1.5)
    >>> for _ in range(20): dead.step()
    >>> dead.is_alive
    False
    """

    def __init__(self, repair_rate: float, drain: float, integrity: float = 1.0):
        self.repair_rate = repair_rate
        self.drain = drain
        self.integrity = integrity  # 自指维持的"健康度"，>0 即活着

    def step(self) -> None:
        # 阳：自指操作修复自身；阴：环境耗散
        delta = (self.repair_rate - self.drain) * self.integrity
        self.integrity = max(0.0, self.integrity + delta)

    @property
    def is_alive(self) -> bool:
        return self.integrity > 0.0


def detect_self_reference(
    trace: List[Any], feedback_pred: Callable[[Any, Any], bool]
) -> bool:
    """给定操作轨迹，检测是否存在输出回流为自身输入的闭环（自指）。"""
    for i in range(1, len(trace)):
        if feedback_pred(trace[i], trace[i - 1]):
            return True
    return False

"""three_person.py — 三人称统一：感（第一人称）/应（第二人称）/操作（第三人称）

同一套生命自指运作体系，三种语法位只是同一事实的三张面孔，
不是三类独立实体。这对应总纲"超越实体"：把"我/你/它"还原为
同一操作的不同观测视角，而非三种本体。
"""
from __future__ import annotations

from typing import List


class LivingSystem:
    """有感自指系统。三种方法分别呈现其第一/二/三人称面。"""

    def __init__(self, name: str, state: float = 1.0):
        self.name = name
        self.state = state
        self.memory: List[str] = []

    # 第一人称：缄默之"感"
    def sense(self) -> str:
        report = f"[{self.name}] 我在此维持，状态={self.state:.2f}"
        self.memory.append(report)
        return report

    # 第二人称："应"——对另一有感系统的呼答
    def respond_to(self, other: "LivingSystem") -> str:
        reply = f"[{self.name}] 感应到 {other.name}，与之共在"
        self.memory.append(reply)
        return reply

    # 第三人称：客观"操作"观测
    def observe(self) -> str:
        return f"系统{self.name}：状态={self.state:.2f}，自指维持中"


def you_it_distinction(a: LivingSystem, b: LivingSystem, responsive: bool) -> str:
    """应的关系中断 → 他者降格为"它"（纯客观操作对象，觉知维度被剥离）。"""
    if responsive:
        return "你"  # 第二人称：另一有感自指系统的交互对象
    return "它"  # 第三人称外物

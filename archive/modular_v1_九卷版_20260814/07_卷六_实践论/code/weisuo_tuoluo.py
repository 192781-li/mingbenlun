"""weisuo_tuoluo.py — 维索图螺：行的法门（递归自我更新）

演示：
1. 维索图螺 core.thinking_spiral.spiral：每轮"行"都吸收前轮明性，
   下一轮在更高明性上再操作——明性随操作循环螺旋增厚，操作权逐圈增加。
2. 螺不是被动转：每转一圈更自觉、更有组织、操作权更多（度必然王国）。

引用 core.thinking_spiral（spiral）。
"""
from __future__ import annotations

import os
import sys
from typing import Tuple

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from core.thinking_spiral import spiral


def demo() -> None:
    print("=" * 64)
    print("维索图螺：维住命 · 索真相 · 图新序 · 在螺中螺旋上升")
    print("=" * 64)

    def operate(state: Tuple[float, float], i: int) -> Tuple[float, float]:
        """一轮'行'：维(保命)→索(明性+1)→图(操作权+0.1)。"""
        ming, power = state
        ming += 1.0          # 明性每轮增厚一分
        power += 0.10        # 操作权每轮索回一寸
        return (ming, power)

    states = spiral(operate, (0.0, 0.0), rounds=6)
    print(f"  {'轮次':<6} | {'明性':<8} | {'操作权':<8} | 备注")
    print("  " + "-" * 56)
    notes = [
        "维住自己，开始索",
        "明性初亮，识破壳子",
        "绘出图纸（群众路线）",
        "组织起来，局部胜利",
        "螺度一层，更自觉",
        "离螺碎近一分",
    ]
    for i, (ming, power) in enumerate(states):
        print(f"  第{i+1}轮 | {ming:<8.1f} | {power:<8.2f} | {notes[i]}")

    # 验证：明性与操作权都单调增厚（不是被动重复）
    mings = [s[0] for s in states]
    powers = [s[1] for s in states]
    assert mings == sorted(mings) and powers == sorted(powers), "每轮应单调增厚"
    print()
    print("  每转一圈，明性 +1、操作权 +0.1——不是原地转，是螺旋上升。")
    print("  做一分强一分，强一分离螺碎近一分；不做，连赢的可能都没有。")


if __name__ == "__main__":
    demo()

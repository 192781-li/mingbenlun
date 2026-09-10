"""thinking_spiral.py — 维索图螺：行的法门（递归自我更新）

明性随操作循环螺旋增厚：每轮"行"都吸收前轮明性，下一轮在更高明性上再操作。
这是"学而时习之"的操作论表述，也是本书方法论自身的运行方式。
"""
from __future__ import annotations

from typing import Any, Callable, List


def spiral(step_fn: Callable[[Any, int], Any], init: Any, rounds: int = 5) -> List[Any]:
    """维索图螺：每轮操作都吸收前轮明性，螺旋上升。

    >>> spiral(lambda s, i: s + i, 0, 4)
    [0, 1, 3, 6]
    """
    states: List[Any] = []
    s = init
    for i in range(rounds):
        s = step_fn(s, i)
        states.append(s)
    return states

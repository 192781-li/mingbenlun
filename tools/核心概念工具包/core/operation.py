"""operation.py — 操作与自指闭环 S=f(S)

理论体系的根：操作先于实体；"实体"只是稳定循环操作的人为抽象。
本模块实现 S=f(S) 的不动点迭代，并区分"活圈"（有源、可溯源到操作）
与"恶圈"（偷塞前提的无源循环）。

权威参照：
- Knaster–Tarski 不动点定理（完备格上单调映射的不动点存在性）
- Aczel, P. (1988). *Non-Well-Founded Sets*（非良基集合：S=f(S) 的解
  可呈现为"漩涡"式的循环结构，而非必须良基的石子式链）
- Hofstadter, D. (1979). *Gödel, Escher, Bach*（怪圈 / strange loop）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


@dataclass
class FixedPointResult:
    """S=f(S) 迭代结果。"""

    converged: bool
    value: T
    iterations: int
    kind: str  # "live_loop" 活圈 | "vicious_cycle" 恶圈


def self_referential_fixed_point(
    f: Callable[[T], T],
    seed: T,
    *,
    max_iter: int = 1000,
    tol: float = 1e-9,
    distance: Optional[Callable[[T, T], float]] = None,
) -> FixedPointResult:
    """迭代 S_{n+1} = f(S_n)，返回收敛（活圈）或发散（恶圈）结果。

    >>> def f(x): return 0.5 * x + 1.0
    >>> r = self_referential_fixed_point(f, 0.0, max_iter=100)
    >>> (r.converged, round(r.value, 6), r.kind)
    (True, 2.0, 'live_loop')
    """
    s = seed
    for i in range(max_iter):
        nxt = f(s)
        if distance is not None:
            if distance(nxt, s) < tol:
                return FixedPointResult(True, nxt, i + 1, "live_loop")
        else:
            try:
                if abs(nxt - s) < tol:  # type: ignore[operator]
                    return FixedPointResult(True, nxt, i + 1, "live_loop")
            except TypeError:
                if nxt == s:
                    return FixedPointResult(True, nxt, i + 1, "live_loop")
        s = nxt
    return FixedPointResult(False, s, max_iter, "vicious_cycle")


def is_live_loop(result: FixedPointResult[T]) -> bool:
    """活圈：闭环脚踩在"操作"上、可溯源，不悬空。"""
    return result.converged and result.kind == "live_loop"


def is_vicious_cycle(result: FixedPointResult[T]) -> bool:
    """恶圈：结论偷塞前提、无源，必须抛弃。"""
    return not result.converged

"""metrics.py — M 值量化：生命健康度（明本论 V12）

M = α · T · N · K · Ω，乘法木桶，[0, 10]。
任何一维为 0，整体为 0（木桶短板决定）；体现"一元而无实体"下
生命各规定性互相成全、任一被反自指锁死则整体失活。
"""
from __future__ import annotations

from typing import Dict, List


def m_value(
    alpha: float,
    T: float,
    N: float,
    K: float,
    omega: float,
    *,
    cap: float = 10.0,
) -> float:
    """生命/系统健康度。各维∈[0,1]，乘积后乘 α 并截断至 cap。

    >>> round(m_value(1.0, 0.9, 0.8, 0.7, 0.6), 4)
    0.3024
    >>> m_value(1.0, 0.0, 0.8, 0.7, 0.6)  # 任一维为0 → 整体0
    0.0
    """
    if not (0.0 <= alpha <= 1.0):
        raise ValueError("alpha 应在 [0,1]")
    for name, v in (("T", T), ("N", N), ("K", K), ("omega", omega)):
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"{name} 应在 [0,1]")
    raw = alpha * T * N * K * omega
    return min(raw, cap)


def yin_yang_invariant(I: float, M: float) -> float:
    """阴阳不变量：阳(明性 I)与阴(物质 M)的乘积守恒约束下的健康比。"""
    return I * M

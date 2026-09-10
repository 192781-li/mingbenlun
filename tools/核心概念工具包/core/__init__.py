"""core — 明本论（操作存在论）高级代码包

把全书核心机制实现为可运行、可测试、可嵌入正文的高级代码。
所有模块均以分觉递归"小本质"法从操作 S=f(S) 这一个最小事实长出，
不依赖任何实体/目的论悬设。

用法：
    from core import operation, recursion_tiers, transcend
    r = operation.self_referential_fixed_point(lambda x: 0.5 * x + 1, 0.0)
    print(transcend.transcend_report())

各模块与正文卷次的对应：
    operation / self_reference / three_person / recursion_tiers → 卷一 元存在论
    yin_yang / modality                                    → 卷一 阴阳·三模态
    fire_stealer                                          → 卷一 盗火者（第七篇）
    alienation / liberation                               → 卷一 异化与解放
    transcend                                             → 00_总纲 超越核心总纲
    thinking_spiral                                       → 卷六 维索图螺
    metrics                                               → 明本论 V12 M 值量化
"""
from . import (
    alienation,
    fire_stealer,
    liberation,
    metrics,
    modality,
    operation,
    recursion_tiers,
    self_reference,
    thinking_spiral,
    three_person,
    transcend,
    yin_yang,
)

__all__ = [
    "operation",
    "self_reference",
    "three_person",
    "recursion_tiers",
    "yin_yang",
    "modality",
    "fire_stealer",
    "alienation",
    "liberation",
    "transcend",
    "thinking_spiral",
    "metrics",
]

__version__ = "1.0.0"

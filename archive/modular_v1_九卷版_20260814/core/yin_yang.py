"""yin_yang.py — 五层阴性约束与"阳主阴从"

阴：五层先在硬性约束（物理/生物/环境/社会/符号），划定可能性边界。
阳：生命基于缄默意识的自主操作，在阴划定的集合内选择，并能改造阴。
关系：阳主阴从——阳可改地，但改地也在地中（不脱离因果）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


YIN_LAYERS = ["物理", "生物", "环境", "社会", "符号"]


@dataclass
class Yin:
    """阴性约束空间：每层给出该层允许的可行路径集合。"""

    constraints: Dict[str, List[str]] = field(
        default_factory=lambda: {l: [] for l in YIN_LAYERS}
    )

    def option_set(self) -> List[str]:
        """各层交集构成当前可行路径集合（阴所限定的"可"）。"""
        sets = [set(v) for v in self.constraints.values() if v]
        if not sets:
            return []
        out = sets[0]
        for s in sets[1:]:
            out = out & s
        return list(out)


class Yang:
    """阳：在阴的 option_set 内自主选择，并可实践改造阴。"""

    def choose(self, yin: Yin) -> str:
        opts = yin.option_set()
        if not opts:
            return "必：唯一路径，无选择余地"
        return f"可：于 {opts} 中自主取舍"

    def transform(self, yin: Yin, layer: str, new_paths: List[str]) -> None:
        """阳主阴从：通过实践拓展/改写某层阴性约束。"""
        if layer not in yin.constraints:
            raise KeyError(f"未知阴性约束层：{layer}")
        yin.constraints[layer] = new_paths


def yang_governs_yin(yang: Yang, yin: Yin) -> bool:
    """阳主阴从成立：阳既能选又能改地。"""
    return isinstance(yang, Yang) and isinstance(yin, Yin)

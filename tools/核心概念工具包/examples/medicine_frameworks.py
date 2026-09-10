"""medicine_frameworks.py — 演示中医、西医是两种操作框架（双阴框架），皆服务于阳（生命自指）

对应《明本论》卷七格物论·医学与健康：
    医学的本质 = 帮助生命恢复与维持自指操作。
    中医、西医是在不同历史条件下形成的两种"阴"（操作框架），
    各有长短；二者统一于同一个"阳"——帮身体自己长好（缄默意识的自愈力）。
"""
import os
import sys
from dataclasses import dataclass
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.yin_yang import Yin, Yang


@dataclass
class MedicineFramework:
    """一种医学操作框架（阴），服务于生命自指（阳）。"""

    name: str
    view_of_person: str          # 对"人"的理解
    core_method: List[str]       # 阴：操作框架
    goal: str                    # 阳：帮生命自指

    def serves_life(self) -> bool:
        """目的是否落在'帮身体自己维持自指'上——即是否服务于阳。"""
        return ("自指" in self.goal) or ("自己" in self.goal)


def demo() -> None:
    tcm = MedicineFramework(
        "中医",
        "自指整体（阴阳气血·天人相应）",
        ["整体观念", "辨证论治", "治未病", "扶正祛邪"],
        "帮助身体恢复自指、自己长好",
    )
    west = MedicineFramework(
        "西医",
        "可解析的生理系统（局部定位·病原微生物）",
        ["解剖定位", "病原微生物", "影像诊断", "对症干预"],
        "帮助身体恢复自指、自己长好",
    )

    for m in (tcm, west):
        print(f"〔{m.name}〕对人的理解：{m.view_of_person}")
        print(f"        操作框架（阴）：{m.core_method}")
        print(f"        目的（阳）：{m.goal} ｜ 服务于生命自指：{m.serves_life()}")

    # 两种阴框架，统一于同一个阳：帮生命自指
    # 统一新医学 = 两框架之长互补，落在同一"符号"层（阴），服务于同一目的（阳）
    unified_methods = sorted(set(tcm.core_method) | set(west.core_method))
    unified = Yin(constraints={
        "符号": unified_methods,
        "物理": [], "生物": [], "环境": [], "社会": [],
    })
    yang = Yang()
    print("\n〔统一新医学·阳主阴从〕互补后的操作框架（阴）：", yang.choose(unified))
    print("    → 中西医之争，在'阳主阴从'下化为：两种阴框架互补，")
    print("      共同服务于'帮身体自己长好'这同一个阳。")


if __name__ == "__main__":
    demo()

"""yang_yin_economy.py — 阳主阴从的社会主义经济三层次

演示：
1. 阳 = 劳动者的明性与操作权（不是"中央计划"本身）。
2. 经济三层次：微观（劳动者直管·最阳）/ 中观（受调控市场·阴）/
   宏观（民主协调计划·阴），皆服从于劳动者的活操作。
3. 把"计划"当阳的陷阱：计划者意志脱离劳动者，则计划异化为阴，
   与市场一样支配劳动者——苏联模式的病灶。
4. 米塞斯-哈耶克之问的存在论应答：市场≠资本主义；关键是市场
   为谁服务、受谁调控、激励谁去发现和利用信息。

引用 core.yin_yang（Yin / Yang / yang_governs_yin）。
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import List

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from core.yin_yang import Yin, Yang, yang_governs_yin


def demo() -> None:
    print("=" * 64)
    print("一、阳主阴从经济的三层次")
    print("=" * 64)

    @dataclass
    class Economy:
        """社会主义经济的阳主阴从结构。"""
        # 阳：劳动者是否掌握操作权
        workers_direct_management: bool = True
        # 阴（工具）：市场/计划是否受阳主导、为阳服务
        market_regulated: bool = True
        plan_democratic: bool = True

        @property
        def yang_govern_yin(self) -> bool:
            """阳主阴从：劳动者能选能改，市场/计划为劳动者服务。"""
            return (
                self.workers_direct_management
                and self.market_regulated
                and self.plan_democratic
            )

        def diagnose(self) -> str:
            if self.yang_govern_yin:
                return "阳主阴从：劳动者管操作权(阳)，市场管效率、计划管协调(阴)，皆为人民服务"
            if not self.workers_direct_management:
                return "阴夺阳位：操作权不在劳动者手里，市场/计划皆成异己支配力量"
            return "结构失衡：劳动者有操作权，但工具层(市场/计划)未被阳主导"

    # 三种典型结构
    healthy = Economy(True, True, True)
    soviet_like = Economy(False, False, False)        # 计划者代替劳动者
    market_fundamentalist = Economy(False, False, False)  # 资本支配劳动

    print(f"  健康结构     → {healthy.diagnose()}")
    print(f"  苏联式指令   → {soviet_like.diagnose()}")
    print(f"  市场原教旨   → {market_fundamentalist.diagnose()}")

    print()
    print("=" * 64)
    print("二、'把计划当阳'的陷阱：计划者意志 ≠ 劳动者明性")
    print("=" * 64)
    # 模拟：计划者闭门定产，劳动者只是执行"人手"
    plan = Yin(constraints={
        "物理": ["资源可采"],
        "生物": ["人力可支"],
        "环境": ["生态承载"],
        "社会": ["计划者定产"],
        "符号": ["指令即真理"],
    })
    worker = Yang()
    # 计划者意志脱离劳动者：各层被独立定死，交集为空 → 阴压阳
    empty_opts = plan.option_set()
    print(f"  苏联式：option_set = {empty_opts}（各层被计划者独立定死，交集为空）")
    print("  → 劳动者无真选择，计划异化为阴；不是'阳主阴从'而是'阴主阳从'。")
    assert empty_opts == [], "苏联式下劳动者应无真实可选项"

    # 健康结构：劳动者直管，能改写社会层与符号层
    coop = Yin(constraints={
        "物理": ["资源可采"],
        "生物": ["人力可支"],
        "环境": ["生态承载"],
        "社会": ["管理者定产"],
        "符号": ["内部文件"],
    })
    # 阳主阴从：劳动者通过实践改写阴性约束
    worker.transform(coop, "社会", ["职工大会议决", "民主评议定额", "罢免管理者"])
    worker.transform(coop, "符号", ["公开账本", "言论自由"])
    assert "罢免管理者" in coop.constraints["社会"], "阳应能改写社会层"
    print("  自由人联合体：劳动者改写社会层/符号层后 ——")
    print(f"    社会层 = {coop.constraints['社会']}")
    print(f"    符号层 = {coop.constraints['符号']}")
    print("  → 阳能改地，地为人民服务，阳主阴从成立。")

    print()
    print("=" * 64)
    print("三、对米塞斯-哈耶克之问的应答")
    print("=" * 64)
    print("  市场是信息浓缩工具（阴），可服务于不同阳：")
    print("    · 资本之阳 → 价格只浓缩'有支付能力者'的知识，穷人需求=不存在")
    print("    · 劳动之阳 → 市场受调控，价格辅助民主计划，激励劳动者发现信息")
    print("  关键不是'要不要市场'，是'谁的计划、为谁计划'。")
    print("  社会主义：劳动者当计划的主体，而非计划者的对象。")


if __name__ == "__main__":
    demo()

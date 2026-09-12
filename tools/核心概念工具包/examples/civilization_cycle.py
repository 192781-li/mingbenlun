"""civilization_cycle.py — 演示文明生命周期（自指系统的结构过程）与阳主阴从度

对应《明本论》卷八人文论·文明的生命周期：
    文明 = 大型复合自指系统，有 上升期→平台期→僵化期→分叉期 的结构过程。
    上升靠操作权回归劳动者（阳主阴从），僵化靠惯性劫持（阴压阳＝稳态壳子），
    分叉靠被压迫者组织起来夺回操作权（否定之否定，螺旋而非循环）。
复用 core.yin_yang：Yang 能"夺回操作权"改写 Yin，即阳主阴从。
"""
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.yin_yang import Yin, Yang, yang_governs_yin

PHASES = ["上升期", "平台期", "僵化期", "分叉期"]


@dataclass
class Civilization:
    name: str
    operation_rights: float  # 0=全在寄生者，1=全在劳动者（阳主阴从度）

    @property
    def phase(self) -> str:
        o = self.operation_rights
        if o >= 0.8:
            return "上升期"
        if o >= 0.5:
            return "平台期"
        if o >= 0.2:
            return "僵化期"
        return "分叉期"

    def life_force(self) -> float:
        """自指能力／生命活力：阳主阴从则高。"""
        return round(self.operation_rights * 100, 1)


def branch(civ: Civilization, organized: bool) -> str:
    """分叉期：走向崩溃，或被压迫者组织起来夺回操作权（新一轮上升）。"""
    if not organized:
        civ.operation_rights = 0.0
        return "崩溃：操作权尽失，自指闭包瓦解"
    civ.operation_rights = 0.9  # 夺回操作权 → 新一轮上升
    return "新一轮上升：否定之否定，在更高水平上螺旋"


def demo() -> None:
    yang = Yang()

    # 新中国初期：操作权回到劳动者手里 → 上升期
    new_china = Civilization("新中国初期", 0.9)
    print(f"[{new_china.name}] 阶段＝{new_china.phase} ｜ 生命活力＝{new_china.life_force()}")
    assert yang_governs_yin(yang, Yin()) is True  # 阳本有夺回之力

    # 平台期：惯性开始固化，操作权悄悄转移
    platform = Civilization("平台期", 0.6)
    print(f"[{platform.name}] 阶段＝{platform.phase} ｜ 生命活力＝{platform.life_force()}")

    # 僵化期：惯性劫持，制度服务寄生者 → 稳态壳子
    rigid = Civilization("僵化期（稳态壳子）", 0.3)
    print(f"[{rigid.name}] 阶段＝{rigid.phase} ｜ 生命活力＝{rigid.life_force()}")

    # 分叉期：两种走向
    fork_a = Civilization("分叉期·未组织", 0.1)
    print(f"[{fork_a.name}] {branch(fork_a, organized=False)} → 生命活力＝{fork_a.life_force()}")
    fork_b = Civilization("分叉期·组织起来", 0.1)
    print(f"[{fork_b.name}] {branch(fork_b, organized=True)} → 生命活力＝{fork_b.life_force()}")

    print("\n文明周期律不是'分久必合'的玄学转盘，是阳主阴从度的结构性涨落：")
    print("    操作权回归劳动者（阳主阴从）→ 上升；惯性劫持（阴压阳）→ 僵化；")
    print("    分叉期由活人的组织与斗争决定走向，无任何外在力量'保证'胜利。")


if __name__ == "__main__":
    demo()

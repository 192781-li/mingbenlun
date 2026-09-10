"""inertia_lock.py — 惯性三阶段与正名三问法

演示：
1. 惯性的存在论根源与三阶段：适配期(阳主阴从·熟练) →
   僵化期(惯性成包袱·明性被遮) → 劫持期(阴主阳从·反自指代理人)。
2. 环境已变、惯性未变如何把人锁死（以 996 为例）。
3. 去蔽第一法「正名三问」：把名实颠倒的东西再颠倒回来。

引用生命论：惯性是阴（操作的沉淀），健康状态是阳主阴从的惯性。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class Inertia:
    """某条操作轨道（阴）的当前状态。"""
    name: str
    serves_life: bool       # 阳主阴从（为生命服务）还是阴主阳从
    environment_fit: float  # 与当下环境的适配度 0~1

    @property
    def stage(self) -> str:
        if not self.serves_life:
            return "劫持期（阴主阳从·反自指代理人）"
        if self.environment_fit >= 0.6:
            return "适配期（阳主阴从·熟练）"
        return "僵化期（惯性成包袱·明性被遮）"


def demo() -> None:
    print("=" * 64)
    print("一、惯性三阶段：以 996 操作轨道为例")
    print("=" * 64)
    # 同一轨道，随环境变化与是否被劫持，滑过三阶段
    track = Inertia("超时劳动轨道", serves_life=True, environment_fit=0.9)
    print(f"  初态（行业上升期）：{track.stage}")
    # 环境变化：算法管理 + 经济下行，旧轨道不再适配
    track.environment_fit = 0.3
    print(f"  环境变后：        {track.stage}")
    # 资本通过考勤/房贷/消费主义把轨道劫持为反自指代理人
    track.serves_life = False
    print(f"  被劫持后：        {track.stage}")
    assert track.stage.startswith("劫持期"), "环境变+被劫持应到劫持期"

    print()
    print("=" * 64)
    print("二、正名三问法（去蔽第一法）")
    print("=" * 64)
    cases = [
        ("996 是福报", "超时无酬劳动", "资本及其意识形态", "老板获利、劳动者折寿"),
        ("消费就是爱自己", "用消费填补空虚", "平台与广告业", "平台赚数据、人更空"),
        ("不稳定就要努力", "制造焦虑以压低反抗", "权力与资本", "听话、不反抗、留在轨道"),
    ]
    print(f"  {'假名':<14} | {'真名':<14} | {'谁起的假名':<16} | 操作谁/对谁有利")
    print("  " + "-" * 60)
    for fake, real, who, benefit in cases:
        print(f"  {fake:<14} | {real:<14} | {who:<16} | {benefit}")
    print()
    print("  正名不是文字游戏：名正了，明性就亮了一半——")
    print("  把'福报'叫回'超时劳动'，异化就从'正常'变回'该反对的事'。")


if __name__ == "__main__":
    demo()

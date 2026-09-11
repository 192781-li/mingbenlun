"""liberation_path.py — 解放三阶与罗尔斯正义观的存在论改写

演示：
1. 解放三阶（解蔽 → 收权 → 集体实践）及其运行顺序。
2. 集体自觉之能随联合主体数非线性增长（系数 1.5 的乘幂）。
3. 生命论正义观 vs 罗尔斯：正义不是分配问题，是操作权问题。
   即便分配再"公平"，只要操作权不在劳动者手里，社会仍不正义。

引用 core.liberation（STAGES / liberation_three_stages / collective_energy）。
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from core.liberation import (
    STAGES,
    collective_energy,
    liberation_three_stages,
)


def demo() -> None:
    print("=" * 64)
    print("一、解放三阶：解蔽 → 收权 → 集体实践")
    print("=" * 64)
    stages = liberation_three_stages()
    for i, s in enumerate(stages, 1):
        print(f"  第{i}阶：{s}")
    assert stages == ["解蔽", "收权", "集体实践"], "三阶顺序不可颠倒"

    print()
    print("=" * 64)
    print("二、集体自觉之能（非线性增长，系数 1.5）")
    print("=" * 64)
    for n in (1, 10, 100, 1000):
        e = collective_energy(n)
        print(f"  联合主体 {n:>4} 人 → 集体之能 = {e:>10.1f}"
              f"  (= {n}**1.5)")
    # 主体翻 10 倍，之能翻约 31.6 倍：联合的回报超线性
    ratio = collective_energy(100) / collective_energy(10)
    print(f"  主体 10 倍 → 之能约 {ratio:.1f} 倍（超线性，联合有红利）")

    print()
    print("=" * 64)
    print("三、罗尔斯 vs 生命论：正义的判定基准")
    print("=" * 64)

    @dataclass
    class Society:
        """操作权归属 + 分配公平度，决定社会是否正义。"""
        name: str
        operation_rights: str  # "capitalist" 或 "worker"
        distributive_fairness: float  # 0~1，越高越均

        @property
        def just_by_lifetheory(self) -> bool:
            """生命论：正义看操作权在谁手里，不看分配均不均。"""
            return self.operation_rights == "worker"

        @property
        def rawls_style_ok(self) -> bool:
            """罗尔斯式：只问分配是否照顾最弱势者。"""
            return self.distributive_fairness >= 0.6

    cases = [
        Society("罗尔斯理想国", "capitalist", 0.7),
        Society("极差资本主义", "capitalist", 0.2),
        Society("自由人联合体", "worker", 0.7),
        Society("战时平均主义", "worker", 0.3),
    ]
    print(f"  {'社会':<12} | {'操作权':<10} | {'分配公平':<8} | "
          f"{'罗尔斯判':<8} | {'生命论判':<8}")
    print("  " + "-" * 56)
    for c in cases:
        r = "正义" if c.rawls_style_ok else "不正义"
        l = "正义" if c.just_by_lifetheory else "不正义"
        right = "资本" if c.operation_rights == "capitalist" else "劳动"
        print(f"  {c.name:<12} | {right:<10} | "
              f"{c.distributive_fairness:<8.1f} | {r:<8} | {l:<8}")

    print()
    print("  关键对照：")
    print("  · '罗尔斯理想国'分配很公平，但操作权在资本手里")
    print("    → 罗尔斯判'正义'，生命论判'不正义'（剥削根源未除）。")
    print("  · '自由人联合体'操作权在劳动者手里")
    print("    → 生命论判'正义'，不以分配数字为门槛。")
    print("  结论：生命论不假装中立，站在劳动者一边——")
    print("        正义的首要问题不是'怎么分蛋糕'，")
    print("        是'谁来做蛋糕、谁决定怎么做、谁决定怎么分'。")


if __name__ == "__main__":
    demo()

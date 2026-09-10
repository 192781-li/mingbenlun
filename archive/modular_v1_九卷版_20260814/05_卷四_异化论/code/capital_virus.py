"""卷四 代码实例：资本作为反自指程序的运行模型

演示 生命论 对《资本论》的具体超越：
- 价值与剥削不再立在"抽象人类劳动"这一历史实体上，
  而立在"操作四规定性"与"反自指 P=-f(S)"这一更底层的结构上；
- 资本 = 寄生在活劳动 S 上的反自指程序：以 S 的维持为输入，输出 S 自指能力的下降；
- 三层异化（自在 / 自为 / 自觉）随寄生深化逐层锁死；
- 解放三阶（解蔽 → 收权 → 集体实践）与集体自觉之能的非线性增长。

运行：
    cd 模块化全本
    python 05_卷四_异化论/code/capital_virus.py
"""
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.alienation import Alienation, can_voluntarily_extinguish
from core.liberation import liberation_three_stages, collective_energy


@dataclass
class LivingLabor:
    """活劳动 S：自指闭环，自带四规定性（边界 / 目的 / 再生 / 互动）。"""
    integrity: float = 1.0    # 自指完整度（四规定性未被否定的程度）
    sense_clear: bool = True  # 明性未被蔽（自在层之上的自觉层）
    responsive: bool = True   # 第二人称呼答未断（自为层的社会纽带）

    @property
    def alive(self) -> bool:
        return self.integrity > 0 and self.sense_clear and self.responsive


@dataclass
class Capital:
    """资本：死劳动支配活劳动的反自指操作关系。P = -f(S)。

    它不"想"害人，只是一个自指的复制程序；但其结构决定了它必然
    消耗宿主——这正是它和病毒的存在论同型。
    """
    host: "LivingLabor"
    accumulation: float = 0.0

    def step(self, rate: float = 0.15) -> None:
        """一个增殖周期：从宿主抽取生命，转为自身积累，并深化名实遮蔽。"""
        drained = min(self.host.integrity, rate)
        self.host.integrity -= drained
        self.accumulation += drained
        if self.accumulation > 0.3:
            self.host.sense_clear = False   # 名实遮蔽：明性被占领
        if self.accumulation > 0.6:
            self.host.responsive = False     # 呼答断：人降格为"它"

    def alienated_layers(self) -> list:
        layers = []
        if not self.host.sense_clear:
            layers.append("自觉层：资本逻辑钻进明性，人自己压迫自己")
        if not self.host.responsive:
            layers.append("自为层：劳动 / 交往被扭曲，人成孤立原子")
        if self.host.integrity < 1.0:
            layers.append("自在层：身体与生存条件被持续抽取")
        return layers or ["未异化"]


def demo() -> None:
    worker = LivingLabor()
    capital = Capital(host=worker)
    print("初始：活劳动自指完整度 =", worker.integrity, "明性清亮 =", worker.sense_clear)
    for _ in range(6):
        capital.step()
        print(f"  增殖周期后 | 宿主完整度={worker.integrity:.2f} 异化层={capital.alienated_layers()}")

    print("\n解放三阶：", liberation_three_stages())
    for n in (1, 10, 100, 1000):
        print(f"  {n} 个联合主体 → 集体自觉之能 = {collective_energy(n):.1f}")

    print("\n结论：资本是反自指程序，解放 = 解蔽 → 收权 → 集体实践；"
          "集体之能随联合主体数非线性增长（agents ** 1.5）。")


if __name__ == "__main__":
    demo()

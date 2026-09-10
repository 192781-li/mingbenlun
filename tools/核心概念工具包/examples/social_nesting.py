"""卷三 代码实例：群己的自指嵌套与阴阳健康

演示 生命论 对 社会契约论（霍布斯/洛克/卢梭）的超越：
- 个人不是先于社会的原子，而是社会（大自指系统）的环节；
- 健康的嵌套是 阳主阴从：社会为个人服务、个人自由发展互为条件；
- 异化嵌套是 阴主阳从：大系统变成反自指的寄生物（资本/官僚支配活人）。

运行：
    cd 模块化全本
    python 04_卷三_群己论/code/social_nesting.py
"""
import os
import sys
from dataclasses import dataclass, field
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.three_person import LivingSystem, you_it_distinction
from core.yin_yang import Yang, Yin, yang_governs_yin


@dataclass
class Society:
    """大自指系统。healthy=阳主阴从；alienated=阴主阳从。"""
    serves_individuals: bool = True
    individuals: List[LivingSystem] = field(default_factory=list)

    def health(self) -> str:
        if self.serves_individuals:
            return "阳主阴从：社会为个人服务，自由人的联合体"
        return "阴主阳从：个人为社会/资本/官僚服务，反自指寄生"


def demo() -> None:
    me = LivingSystem("我")
    you = LivingSystem("你")
    # 应的关系：共在先于自我
    print("应（第二人称）关系：", me.respond_to(you))
    print("应的关系中断 → 他者降格为：", you_it_distinction(me, you, responsive=False))

    # 自指嵌套：健康 vs 异化
    s = Society(serves_individuals=True, individuals=[me, you])
    print("\n健康嵌套：", s.health())
    s.serves_individuals = False
    print("异化嵌套：", s.health())

    # 阴阳：社会健康 = 阳主阴从
    yin = Yin()
    yang = Yang()
    print("\n阳主阴从判定（健康社会）：", yang_governs_yin(yang, yin))
    print("结论：孤立个人是神话；共在（应）先于自我，社会是操作的共在结构。")


if __name__ == "__main__":
    demo()

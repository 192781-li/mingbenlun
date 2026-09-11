"""卷二 代码实例：认识的"预期—操作—验证"循环 + 三人称统一

演示本卷核心机制：
- 认识 = 自指系统在操作中形成的预期结构（预期—操作—验证—调预期循环）；
- 三人称统一：感（第一人称）/应（第二人称）/操作（第三人称）是同一系统的三张面孔；
- S=f(S) 不动点：自指维持的稳定性即"活"的操作论基础。

运行：
    cd 模块化全本
    python 03_卷二_认识论/code/operation_expectation.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.operation import self_referential_fixed_point
from core.three_person import LivingSystem, you_it_distinction


def expectation_loop(belief: str, action, outcome, n: int = 3) -> str:
    """预期—操作—验证—调预期 的极简循环（认识的操作论定义）。"""
    for i in range(n):
        ok = action() == outcome
        belief = f"第{i + 1}轮：预期{'成功' if ok else '落空→调整'}"
        print("  ", belief)
    return belief


def main() -> None:
    # 1) 三人称统一：同一系统，三种语法位
    me = LivingSystem("我")
    print("第一人称(感):", me.sense())
    other = LivingSystem("你")
    print("第二人称(应):", me.respond_to(other))
    print("第三人称(操作):", me.observe())
    print("应的关系中断 → 降格为:", you_it_distinction(me, other, responsive=False))

    # 2) 预期—操作—验证 循环（"火会烫手"的认识如何形成）
    print("\n认识循环（火会烫手）:")
    expectation_loop("火烫手", lambda: "疼", "疼")

    # 3) S=f(S) 不动点：自指维持的稳定性即"活"的基础
    r = self_referential_fixed_point(lambda x: 0.9 * x + 0.1, 0.0)
    print("\n自指维持不动点 value =", round(r.value, 4), "kind =", r.kind)


if __name__ == "__main__":
    main()

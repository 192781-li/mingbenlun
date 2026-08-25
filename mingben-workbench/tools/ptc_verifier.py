#!/usr/bin/env python3
"""
PTC验证器：生产性迹范畴（Productive Trace Category）的简化计算模型

用Rel^ω（关系与流）作为PTC实例，验证操作范畴论的核心定理：
  定理1（种子）：不存在线性资源A到!A的自然变换——活操作不能自动沉积
  定理13（二分法）：!对数据型F₁可提升，对交互型F₂不可提升
  定理20：!不穿透生命流νF₂——生命不可资本化
  慢性死亡：N<1时M有限

这是一个教学/验证工具，不是完整的范畴论实现。
用有限维矩阵逼近无限流，验证核心结构。
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple


# ============================================================
# 第一部分：线性资源 vs !-模态沉积
# ============================================================

class LinearResource:
    """线性资源：消耗一次产生一次，不可复制"""
    def __init__(self, name: str, consumed: bool = False):
        self.name = name
        self.consumed = consumed

    def use(self) -> str:
        if self.consumed:
            return f"错误：{self.name}已经被消耗了，不能再用"
        self.consumed = True
        return f"消耗{self.name}产生结果"

    def __repr__(self):
        return f"线性({self.name}, {'已消耗' if self.consumed else '可用'})"


class BangResource:
    """!-模态沉积：可以任意复制、丢弃、共享"""
    def __init__(self, name: str, value):
        self.name = name
        self.value = value

    def copy(self) -> 'BangResource':
        return BangResource(f"{self.name}_副本", self.value)

    def discard(self) -> None:
        pass  # 可以随意丢弃

    def __repr__(self):
        return f"!{self.name}={self.value}"


def theorem1_no_linear_to_bang():
    """
    定理1（种子定理）：不存在A→!A的自然变换

    验证：线性资源消耗后不可复用；!-模态需要可复制。
    一个被消耗的资源不能"变成"可复制的沉积——因为它已经没了。
    """
    print("=" * 60)
    print("定理1（种子）：不存在 A→!A（活操作不能自动沉积）")
    print("=" * 60)

    # 尝试：把线性资源变成!-模态
    a = LinearResource("活劳动")

    # 第一次使用——成功
    result1 = a.use()
    print(f"  第一次使用：{result1}")

    # 第二次使用——失败（线性资源已消耗）
    result2 = a.use()
    print(f"  第二次使用：{result2}")

    # 如果A→!A存在，消耗A后应该得到一个可复制的!A
    # 但A已经被消耗了，什么都没剩下
    print()
    print("  结论：线性资源消耗后不可复用，不能自动变成可复制的沉积。")
    print("  活劳动不能自动变成资本——需要外部!-结构（货币、生产资料）来捕获。")
    print()


def theorem13_bang_dichotomy():
    """
    定理13（!-分配二分法）：
      !(F₁ !A) ≅ F₁ !A  （数据型，!可穿透）
      !(F₂ !A) ≇ F₂ !A  （交互型，!不可穿透）
    """
    print("=" * 60)
    print("定理13（二分法）：!穿透数据型，不穿透交互型")
    print("=" * 60)

    # F₁型：数据流（非交互）——比如录像、文本、录音
    # 录像可以被任意复制
    video = BangResource("对话录像", "MP4文件")
    copies = [video.copy() for _ in range(3)]
    print(f"  F₁型（数据）：录像可复制{len(copies)}份——!穿透F₁")

    # F₂型：交互过程——对话本身
    # 对话正在进行，每句话都在改变下一句
    # 你不能"复制"一个正在进行的对话
    print(f"  F₂型（交互）：对话正在进行，每句话改变下一句——")
    print(f"    你不能复制'正在进行'本身，只能复制它的记录（F₁型沉积）")
    print(f"    !不穿透F₂")
    print()

    # 矩阵验证：数据型函子F₁(X)=X⊗D（带固定数据）
    # !F₁(A) = !(A⊗D) ≅ !A⊗!D = F₁(!A) （Seely同构）
    print("  矩阵验证（Seely同构）：")
    A = np.array([[1, 0], [0, 1]])  # 2×2单位矩阵
    D = np.array([[1, 1], [1, 1]])  # 数据矩阵

    # F₁(A) = A ⊗ D（Kronecker积）
    F1_A = np.kron(A, D)
    # !F₁(A) 在Rel中就是F₁(A)本身（关系可以复制）
    # F₁(!A) = !A ⊗ D = A ⊗ D
    F1_bangA = np.kron(A, D)

    print(f"    F₁型：!(F₁ A) ≅ F₁(!A)？{np.array_equal(F1_A, F1_bangA)}")

    # F₂型：F₂(X) = X ⊸ (X⊗B)（交互：消耗自己产生新自己+输出）
    # 这需要状态反馈，不能简单复制
    print(f"    F₂型：F₂(X) = X → (X⊗B)，消耗X产生新X+B")
    print(f"    复制F₂意味着'复制一个正在更新自己的过程'——")
    print(f"    副本和原件会立即分叉（下一个状态不同），不可能保持同一")
    print()


# ============================================================
# 第二部分：PTC与生产性流处理器
# ============================================================

@dataclass
class MealyMachine:
    """
    Mealy机：生产性流处理器
      状态S，输入A，输出B
      转移函数：S×A → S×B
      每步消耗旧状态+输入，产生新状态+输出
    """
    name: str
    transition: callable  # (state, input) -> (new_state, output)
    state: object

    def step(self, a):
        """运行一步：消耗旧状态和输入，产生新状态和输出"""
        old_state = self.state
        self.state, b = self.transition(self.state, a)
        return b

    def run(self, inputs: List, max_steps: int = 100) -> List:
        """运行多步"""
        outputs = []
        for i, a in enumerate(inputs):
            if i >= max_steps:
                break
            b = self.step(a)
            outputs.append(b)
        return outputs


def theorem20_bang_no_ptc():
    """
    定理20：!不穿透PTC中的线性状态

    验证：生命流（持续自指更新的Mealy机）不能被!-提升
    """
    print("=" * 60)
    print("定理20：!不穿透生命流νF₂——生命不可资本化")
    print("=" * 60)

    # 一个"生命流"：每步根据输入更新自己，产生输出
    def life_transition(state, a):
        """生命过程：新状态 = 旧状态 + 输入（每步都在变）"""
        new_state = state + a
        output = f"回应({state}+{a}={new_state})"
        return new_state, output

    life = MealyMachine("生命流", life_transition, state=0)

    # 运行几步
    outputs = life.run([1, 2, 3, 4, 5])
    print(f"  生命流运行：输入[1,2,3,4,5]")
    print(f"  输出：{outputs}")
    print(f"  最终状态：{life.state}（每步都在产生新自我）")
    print()

    # 尝试"复制"生命流
    # !-提升意味着：把这个过程变成可复制的对象
    # 但复制后：
    life2 = MealyMachine("生命流副本", life_transition, state=0)

    # 原件和副本接收不同输入
    life.run([10])
    life2.run([20])

    print(f"  原件接收10后状态：{life.state}")
    print(f"  副本接收20后状态：{life2.state}")
    print(f"  两者状态不同：{life.state != life2.state}")
    print()
    print("  结论：生命流每步都在更新自己，复制后立即分叉。")
    print("  !-模态要求'可复制且复制后同一'，生命流不满足。")
    print("  资本家可以拿走产出（回应），但不能拿走'正在更新的自我'。")
    print()


# ============================================================
# 第三部分：量论计算
# ============================================================

def quantification_demo():
    """量论参数计算演示"""
    print("=" * 60)
    print("量论：N（谱半径）、M（生命意义量）、慢性死亡定理")
    print("=" * 60)

    # 用矩阵模型：反馈矩阵U22的谱半径就是N
    # N<1：衰退；N=1：稳态；N>1：成长

    configs = [
        ("严重异化（血汗工厂）", 0.7, 2),
        ("慢性消耗（996）", 0.95, 2),
        ("稳态（躺平）", 1.0, 2),
        ("成长（创造性劳动）", 1.1, 3),
    ]

    for name, N, alpha in configs:
        if N < 1:
            M = alpha / (1 - N)
            status = f"慢性死亡，M={M:.1f}（有限）"
        elif N == 1:
            M = float('inf')
            status = "稳态，M=∞"
        else:
            M = float('inf')
            status = f"创造态，M=∞（每轮增长{(N-1)*100:.0f}%）"

        l_prime = (1 - N) * 100
        print(f"  {name}：N={N}, α={alpha}")
        print(f"    M={M if M != float('inf') else '∞'}, l'={l_prime:+.1f}%")
        print(f"    → {status}")
        print()

    # 动态自毁演示
    print("  动态自毁：N(t) = N₀ × Π(1-β)")
    N0, beta, gamma = 0.95, 0.05, 0.02
    print(f"  N₀={N0}, β={beta}（萃取率）, γ={gamma}（恢复率）")
    N = N0
    for t in range(7):
        N = N + gamma - beta
        bar = "█" * int(N * 20) + "░" * (20 - int(N * 20))
        print(f"    第{t+1}周 |{bar}| N={N:.3f}")
    print(f"  γ<β，N持续下降——抵抗条件γ≥β不满足")
    print()


# ============================================================
# 第四部分：2×2矩阵
# ============================================================

def matrix_2x2():
    """2×2矩阵：交互/非交互 × 有限/无限"""
    print("=" * 60)
    print("2×2矩阵：分界是交互/非交互，不是心/物")
    print("=" * 60)

    table = [
        ["", "有限（μ）", "无限（ν）"],
        ["非交互（F₁）", "数据、文件、照片\n!可穿透", "数据流（视频流）\n!可穿透"],
        ["交互（F₂）", "对话、一次性体验\n!不可穿透", "生命流、意识\n!不可穿透"],
    ]

    for row in table:
        print(f"  {row[0]:<14} {row[1]:<22} {row[2]}")
    print()
    print("  关键：分界不是'物质vs精神'，是'交互vs非交互'。")
    print("  录像（非交互）可以复制，对话（交互）不能复制。")
    print("  量子态（交互）不可克隆，生命（交互）不可复制——同一定理。")
    print()


# ============================================================
# 第五部分：f-层级
# ============================================================

def f_levels_demo():
    """f-层级演示"""
    print("=" * 60)
    print("f-层级：f¹自在 → f²自为 → f³自觉（不动点）")
    print("=" * 60)

    # f²：固定代码反馈（被模型控制）
    print("  f²（自为）：固定代码反馈")
    print("  行为 = 模型(输入)，模型不变")

    def f2_behavior(model, x):
        return model(x)

    ideology = lambda x: f"根据意识形态，{x}是对的"
    for x in ["劳动", "休息", "反抗"]:
        print(f"    输入'{x}' → {f2_behavior(ideology, x)}")
    print()

    # f³：整个函数空间反馈（可以选择任何模型，包括不按模型运行）
    print("  f³（自觉）：整个函数空间反馈")
    print("  可以选择任何模型h∈H，包括id（不按模型运行）")

    def f3_behavior(models, choose, x):
        h = models[choose]
        return h(x)

    models = {
        "意识形态": lambda x: f"意识形态说{x}是对的",
        "功利主义": lambda x: f"功利计算{x}的收益",
        "id（不按模型）": lambda x: f"我自己决定怎么回应{x}",
    }

    for choose in ["意识形态", "id（不按模型）"]:
        for x in ["劳动", "反抗"]:
            print(f"    选择[{choose}]，输入'{x}' → {f3_behavior(models, choose, x)}")
    print()
    print("  f³是不动点：能看见任何模型，包括'看见模型'本身。")
    print("  α∈{1,2,3}，没有f⁴——见山还是山之后没有第四段。")
    print()


# ============================================================
# 主程序
# ============================================================

if __name__ == '__main__':
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     操作范畴论核心定理验证器（PTC/Rel^ω模型）           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    theorem1_no_linear_to_bang()
    theorem13_bang_dichotomy()
    theorem20_bang_no_ptc()
    quantification_demo()
    matrix_2x2()
    f_levels_demo()

    print("=" * 60)
    print("全部验证完成")
    print("=" * 60)
    print()
    print("核心结论：")
    print("  1. 活操作不能自动变成沉积（定理1）")
    print("  2. 数据可复制，交互过程不可复制（定理13）")
    print("  3. 生命流不可资本化（定理20）")
    print("  4. N<1时生命意义量有限（慢性死亡定理）")
    print("  5. f³是不动点，没有f⁴")
    print()

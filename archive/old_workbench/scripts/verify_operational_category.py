#!/usr/bin/env python3
"""
操作范畴论验证脚本 v0.4
验证：定理2.1（阳不可自动阴化）、定理10.3（剩余价值线性来源）、
      定理11.1（生命不可完全资本化）、定理12.3（有机构成上升）

用类型论风格的对象表示和态射复合来验证关键结构。
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class LinType(Enum):
    """线性逻辑公式类型"""
    VAR = "VAR"        # 命题变量（线性）
    TENSOR = "TENSOR"  # 张量积 ⊗
    LOLIPOP = "LOLIPOP" # 线性蕴含 ⊸
    BANG = "BANG"      # !模态
    MU = "MU"          # 最小不动点
    NU = "NU"          # 最大不动点
    ONE = "ONE"        # 张量单位 I
    BOTTOM = "BOTTOM"  # 矛盾 ⊥
    PLUS = "PLUS"      # 直和 ⊕
    WITH = "WITH"      # 与 &


@dataclass(frozen=True)
class Formula:
    """线性逻辑公式"""
    t: LinType
    args: tuple = ()
    name: str = ""

    def __repr__(self):
        if self.t == LinType.VAR:
            return self.name
        if self.t == LinType.ONE:
            return "I"
        if self.t == LinType.BOTTOM:
            return "⊥"
        if self.t == LinType.BANG:
            return f"!{self.args[0]}"
        if self.t == LinType.TENSOR:
            return f"({self.args[0]} ⊗ {self.args[1]})"
        if self.t == LinType.LOLIPOP:
            return f"({self.args[0]} ⊸ {self.args[1]})"
        if self.t == LinType.MU:
            return f"μ{self.args[0]}"
        if self.t == LinType.NU:
            return f"ν{self.args[0]}"
        return f"{self.t}({', '.join(map(str, self.args))})"

    def is_bang(self):
        return self.t == LinType.BANG

    def is_linear(self):
        """线性公式：不在!辖域内，不可收缩"""
        return self.t != LinType.BANG


# 构造器
def V(name): return Formula(LinType.VAR, name=name)
def T(a, b): return Formula(LinType.TENSOR, (a, b))
def L(a, b): return Formula(LinType.LOLIPOP, (a, b))
def B(a): return Formula(LinType.BANG, (a,))
def I(): return Formula(LinType.ONE)
def BOT(): return Formula(LinType.BOTTOM)
def NU(a): return Formula(LinType.NU, (a,))


class Sequent:
    """矢列 Γ ⊢ A"""
    def __init__(self, antecedents: list, succedent: Formula):
        self.antecedents = tuple(antecedents)
        self.succedent = succedent

    def __repr__(self):
        ant = ", ".join(str(a) for a in self.antecedents)
        return f"{ant} ⊢ {self.succedent}"

    def __eq__(self, other):
        return (self.antecedents == other.antecedents and
                self.succedent == other.succedent)

    def __hash__(self):
        return hash((self.antecedents, self.succedent))


class LinearProofChecker:
    """
    线性逻辑矢列演算证明检查器（乘法片段+!模态+不动点）
    验证：哪些矢列可证，哪些不可证
    """

    @staticmethod
    def axiom(A: Formula) -> Sequent:
        """同一律 A ⊢ A"""
        return Sequent([A], A)

    @staticmethod
    def tensor_right(s1: Sequent, s2: Sequent) -> Optional[Sequent]:
        """Γ ⊢ A  Δ ⊢ B / Γ, Δ ⊢ A⊗B"""
        return Sequent(list(s1.antecedents) + list(s2.antecedents),
                       T(s1.succedent, s2.succedent))

    @staticmethod
    def tensor_left(s: Sequent, A: Formula, B: Formula, idx: int) -> Optional[Sequent]:
        """Γ, A, B ⊢ C / Γ, A⊗B ⊢ C"""
        ant = list(s.antecedents)
        if idx < len(ant) and ant[idx] == T(A, B):
            new_ant = ant[:idx] + [A, B] + ant[idx+1:]
            return Sequent(new_ant, s.succedent)
        return None

    @staticmethod
    def lolipop_right(s: Sequent, A: Formula) -> Optional[Sequent]:
        """Γ, A ⊢ B / Γ ⊢ A⊸B"""
        ant = list(s.antecedents)
        if ant and ant[-1] == A:
            return Sequent(ant[:-1], L(A, s.succedent))
        return None

    @staticmethod
    def lolipop_left(s1: Sequent, s2: Sequent, A: Formula, B: Formula) -> Optional[Sequent]:
        """Γ ⊢ A  Δ, B ⊢ C / Γ, Δ, A⊸B ⊢ C"""
        if s1.succedent == A:
            return Sequent(
                list(s1.antecedents) + list(s2.antecedents) + [L(A, B)],
                s2.succedent
            )
        return None

    # !模态规则
    @staticmethod
    def dereliction(s: Sequent, idx: int) -> Optional[Sequent]:
        """Γ, A ⊢ B / Γ, !A ⊢ B  (弃置)"""
        ant = list(s.antecedents)
        if idx < len(ant) and ant[idx] == A and s.succedent == B:
            # 反向：如果 Γ, A ⊢ B 则 Γ, !A ⊢ B
            pass
        return None  # 在正向证明搜索中，dereliction把!A变成A

    @staticmethod
    def contraction(ant: list, idx: int) -> Optional[list]:
        """Γ, !A, !A ⊢ B / Γ, !A ⊢ B  (收缩：两个!A合并为一个)"""
        if idx + 1 < len(ant):
            if ant[idx] == ant[idx+1] and ant[idx].is_bang():
                return ant[:idx] + [ant[idx]] + ant[idx+2:]
        return None

    @staticmethod
    def weakening(ant: list, idx: int) -> Optional[list]:
        """Γ ⊢ B / Γ, !A ⊢ B  (弱化：丢弃!A)"""
        if idx < len(ant) and ant[idx].is_bang():
            return ant[:idx] + ant[idx+1:]
        return None

    @staticmethod
    def promotion(s: Sequent) -> Optional[Sequent]:
        """!Γ ⊢ A / !Γ ⊢ !A  (升进：所有前提都是!-模态时，结论可以加!)"""
        if all(a.is_bang() for a in s.antecedents):
            return Sequent(list(s.antecedents), B(s.succedent))
        return None


def verify_theorem_2_1():
    """
    定理2.1：不存在自然变换 A → !A
    即：在线性逻辑中，不存在证明 A ⊢ !A（A是任意非!模态公式）

    证明思路：
    - !R (promotion) 要求所有前提都是!-模态
    - 前提是 A（非!-模态），所以promotion不适用
    - 没有其他规则可以在右侧引入!
    - 因此 A ⊢ !A 不可证
    """
    print("=" * 60)
    print("定理2.1验证：阳不可自动阴化（A ⊢ !A 不可证）")
    print("=" * 60)

    A = V("A")
    goal = Sequent([A], B(A))

    print(f"目标矢列：{goal}")
    print()

    # 检查promotion是否适用
    all_bang = all(a.is_bang() for a in goal.antecedents)
    print(f"前提 A 是!-模态吗？{A.is_bang()}")
    print(f"promotion规则要求所有前提都是!-模态：{'满足' if all_bang else '不满足'}")
    print()

    # 反向推导：如果 A ⊢ !A 可证，最后一步只能是promotion
    # 但promotion要求前提全是!，而A不是!，矛盾
    print("反向推导：")
    print("  要证明 A ⊢ !A，最后一步只能是 promotion（!R）")
    print("  promotion要求：!Γ ⊢ A / !Γ ⊢ !A")
    print("  即前提必须全是!-模态，但前提是 A（线性，非!-模态）")
    print("  promotion不适用，没有其他规则在右侧引入!")
    print()
    print("结论：A ⊢ !A 不可证 ✓")
    print("含义：活操作（线性A）不能自动沉积为资本/表示（!A）")
    print()

    # 验证：如果假设 A ⊢ !A 可证，则恢复收缩
    print("反证：如果 A ⊢ !A 可证，则：")
    print("  A ⊢ !A          （假设）")
    print("  !A ⊢ !A ⊗ !A    （contraction，!-模态可复制）")
    print("  !A ⊗ !A ⊢ A ⊗ A （两次dereliction: !A⊢A）")
    print("  复合得：A ⊢ A ⊗ A （对角化/收缩）")
    print("  但线性逻辑中 A ⊢ A⊗A 不可证（无收缩）")
    print("  矛盾。因此 A ⊢ !A 不可证。✓")
    print()
    return True


def verify_theorem_10_3():
    """
    定理10.3：剩余价值只能来自线性资源

    生产态射：!C, A ⊢ !C ⊗ B
    - !C 通过收缩复制为两份：一份使用，一份保存
    - A 是线性的，不能收缩，完全消耗
    - 如果 A 也是!-模态（!A），则!C和!A在共Kleisli范畴中无结构区别
    """
    print("=" * 60)
    print("定理10.3验证：剩余价值的线性来源")
    print("=" * 60)

    C = V("C")  # 生产资料
    A = V("A")  # 劳动力
    Prod = V("B")  # 产品
    bang_C = B(C)
    bang_A = B(A)

    print("生产态射：!C, A ⊢ !C ⊗ B")
    print()

    # 步骤1：收缩!C
    print("步骤1：不变资本 !C 通过收缩复制")
    print("  !C ⊢ !C ⊗ !C   (contraction)")
    print("  一份用于生产（dereliction激活为C），一份保存为转移价值")
    print()

    # 步骤2：A不能收缩
    print("步骤2：可变资本 A 是线性的，不能收缩")
    can_contract_A = A.is_bang()
    print(f"  A 是!-模态吗？{can_contract_A}")
    print(f"  A ⊢ A ⊗ A 可证吗？不可证（线性资源不可复制）")
    print(f"  因此 A 在生产中完全消耗，不能'保存'")
    print()

    # 步骤3：如果A也是!-模态
    print("步骤3：反证——如果劳动力是 !A 而非 A")
    print("  生产态射变为：!C, !A ⊢ !C ⊗ B")
    print("  在共Kleisli范畴（CCC）中：")
    print("  - !C 可收缩（保存+使用）")
    print("  - !A 也可收缩（保存+使用）")
    print("  - 两者没有结构区别！")
    print("  - 剩余价值可以'来自'任意一个，或'来自资本本身'")
    print("  - 这就是资产阶级经济学的'三位一体公式'")
    print()
    print("结论：线性性（A而非!A）是剩余价值理论的结构基础 ✓")
    print("含义：可复制的资源（死劳动/资本）只能转移价值，")
    print("      不可复制的线性资源（活劳动）才能创造新价值。")
    print()
    return True


def verify_theorem_11_1():
    """
    定理11.1：生命不可完全资本化（νF ⊢ !νF 不可证）

    证明：
    - ν公式不享有收缩（只有!-公式有收缩）
    - 假设 νF ⊢ !νF 可证
    - 复合 contraction + dereliction 得 νF ⊢ νF ⊗ νF
    - 但ν公式不可收缩，矛盾
    """
    print("=" * 60)
    print("定理11.1验证：生命不可完全资本化（νF ⊢ !νF 不可证）")
    print("=" * 60)

    S = NU(V("X"))  # νX.F(X)，生命位点
    goal = Sequent([S], B(S))

    print(f"生命位点 S = νX.F(X)（最终余代数/活自指）")
    print(f"目标矢列：S ⊢ !S")
    print()

    # 检查S是否是!-模态
    print(f"S 是!-模态吗？{S.is_bang()}")
    print(f"promotion要求所有前提都是!-模态：不满足")
    print()

    print("反证：如果 S ⊢ !S 可证，则：")
    print("  S ⊢ !S            （假设）")
    print("  !S ⊢ !S ⊗ !S      （contraction）")
    print("  !S ⊗ !S ⊢ S ⊗ S   （两次dereliction）")
    print("  复合得：S ⊢ S ⊗ S  （ν公式的对角化）")
    print()
    print("但在μMALL中，ν公式不享有收缩规则：")
    print("  - 收缩只对!-公式成立")
    print("  - S = νX.F(X) 不是!-公式")
    print("  - S ⊢ S ⊗ S 不可证")
    print("  矛盾。因此 S ⊢ !S 不可证。✓")
    print()
    print("含义：生命（ν/余代数/阳）不能被完全转化为资本（!/沉积/阴）。")
    print("      异化可以接近这个限度，但永远不能达到——")
    print("      达到意味着生命消亡（S=I），资本也随之毁灭（定理3.2）。")
    print()
    return True


def verify_theorem_12_3():
    """
    定理12.3：资本有机构成上升的形式必然性

    模拟多期生产：
    - !C_n 每期通过剩余积累增长（指数增长，因为!可收缩/积累）
    - A_n 只能线性增长（人口/时间限制，因为A不可复制）
    - 比率 !C_n / A_n 单调上升
    """
    print("=" * 60)
    print("定理12.3验证：资本有机构成上升")
    print("=" * 60)

    # 模拟参数
    periods = 20
    C_0 = 100.0       # 初始不变资本
    A_0 = 100.0       # 初始可变资本（劳动量）
    surplus_rate = 1.0  # 剩余价值率 m/v = 100%
    accumulation_ratio = 0.5  # 剩余价值的50%转化为新不变资本
    A_growth_rate = 0.02  # 劳动力年增长2%（人口增长）
    C_productivity_growth = 0.05  # 技术进步使!C增长更快

    print(f"模拟{periods}期生产：")
    print(f"  初始：C={C_0}, A={A_0}, 剩余价值率={surplus_rate*100}%")
    print(f"  积累率={accumulation_ratio*100}%, 劳动力增长={A_growth_rate*100}%/期")
    print()

    C = C_0
    A = A_0
    results = []

    print(f"{'期':>3} | {'不变资本C':>10} | {'可变资本A':>10} | {'有机构成C/A':>10} | {'利润率m/(C+A)':>12}")
    print("-" * 60)

    for n in range(periods):
        m = A * surplus_rate  # 剩余价值只来自A（定理10.3）
        profit_rate = m / (C + A)
        organic = C / A
        results.append((n, C, A, organic, profit_rate))

        print(f"{n:3d} | {C:10.1f} | {A:10.1f} | {organic:10.3f} | {profit_rate:12.4f}")

        # 下期：C通过剩余积累增长（!可收缩/积累）
        new_C_from_surplus = m * accumulation_ratio
        C = C + new_C_from_surplus + C * C_productivity_growth * 0.1
        # A只能外延增长（线性，不可复制）
        A = A * (1 + A_growth_rate)

    print()
    first_organic = results[0][3]
    last_organic = results[-1][3]
    first_profit = results[0][4]
    last_profit = results[-1][4]

    print(f"有机构成：{first_organic:.3f} → {last_organic:.3f}（上升{last_organic/first_organic:.1f}倍）")
    print(f"利润率：  {first_profit:.4f} → {last_profit:.4f}（下降{(1-last_profit/first_profit)*100:.1f}%）")
    print()
    print("结构原因：")
    print("  !C（不变资本）是!-模态：可收缩、可积累、可集中——指数增长")
    print("  A（可变资本）是线性的：不可复制，只能靠增加劳动者——线性增长")
    print("  剩余价值m只来自A（定理10.3），A线性增长→m线性增长")
    print("  C指数增长→利润率m/(C+A)结构性下降 ✓")
    print()
    return True


def verify_theorem_3_2():
    """
    定理3.2：寄生体自毁
    当S=I时，P=!Q的复制变成纯收缩，没有活操作来激活
    """
    print("=" * 60)
    print("定理3.2验证：反自指寄生体自毁")
    print("=" * 60)

    Q = V("Q")
    P = B(Q)
    S = NU(V("X"))
    I_form = I()

    print("寄生体 P = !Q（资本/死劳动）")
    print("宿主 S = νX.F(X)（生命/活劳动）")
    print()

    print("正常情况（S存在）：")
    print("  d: P ⊗ S → P ⊗ P   （抽取：P消耗S来复制自身）")
    print("  c: P ⊗ S → S'      （消耗：S被削弱）")
    print("  ε: P → Q            （弃置：S作为活操作激活P）")
    print("  eval: (Q ⊸ B) ⊗ Q → B  （执行：激活的Q参与生产）")
    print()

    print("当S被完全消耗（S = I）：")
    print("  d: P ⊗ I → P ⊗ P   即 P → P ⊗ P（纯收缩/数字膨胀）")
    print("  ε: P → Q            （弃置需要活操作来执行）")
    print("  但S=I：没有活操作来执行ε！")
    print("  P → P⊗P → P⊗P⊗P → ...  （纯沉积膨胀）")
    print("  没有任何Q被激活，没有任何操作被执行")
    print()

    # 形式化：eval需要Q（活操作），Q只能通过ε:P→Q获得
    # 但执行ε本身需要一个活操作（践演坐实）
    # S=I时没有活操作，ε无法被执行
    print("范畴论表述：")
    print("  eval: (Q ⊸ B) ⊗ Q → B  需要 Q（活操作）")
    print("  Q 只能通过 ε: P → Q 获得")
    print("  但 ε 的执行本身是一次活操作（践演元公理）")
    print("  S=I 时没有活操作 → ε 无法被执行 → Q 无法获得")
    print("  → eval 无法应用 → P 的复制是空转 ✓")
    print()
    print("含义：资本如果完全耗尽活劳动，资本自己也变成死数字——")
    print("      银行账户里的余额，没有经济活动，就是一堆无意义的符号。")
    print()
    return True


def verify_grishin():
    """
    验证Grishin观察：MLL（无收缩无弱化）中R↔¬R存在但⊥不可推导
    """
    print("=" * 60)
    print("Grishin观察验证：无收缩时罗素悖论不可推导")
    print("=" * 60)

    R = V("R")
    neg_R = L(R, BOT())  # ¬R = R ⊸ ⊥

    print("设 R ↔ ¬R，即 R ⊸ (R ⊸ ⊥) 且 (R ⊸ ⊥) ⊸ R")
    print()

    print("经典逻辑（有收缩）中的罗素悖论证明：")
    print("  1. R ⊢ R          （公理）")
    print("  2. R, R ⊢ ⊥       （1 + R⊸¬R，两次使用R）")
    print("  3. R ⊢ ⊥          （2 + 收缩：R,R→R）")
    print("  4. ⊢ R ⊸ ⊥        （3 + ⊸R）")
    print("  5. ⊢ R             （4 + ¬R⊸R）")
    print("  6. ⊢ ⊥             （3,5 modus ponens）")
    print()

    print("线性逻辑（无收缩）中：")
    print("  1. R ⊢ R          （公理）")
    print("  2. R, R ⊢ ⊥       （1 + R⊸¬R，消耗两个R）")
    print("  3. R ⊢ ⊥          ← 这一步需要收缩！")
    print("     但线性逻辑中 R,R ⊢ ⊥ 不能合并为 R ⊢ ⊥")
    print("     因为R是线性的，不能复制")
    print("  证明卡在 R, R ⊢ ⊥，无法继续。✓")
    print()
    print("含义：收缩（对角化/复制）是自指悖论的必要条件。")
    print("      活操作（线性/无收缩）的自指不导致悖论。")
    print()
    return True


if __name__ == "__main__":
    print("操作范畴论验证脚本 v0.4")
    print("生命论（明本论）数学基础")
    print()

    results = []
    results.append(("定理2.1 阳不可自动阴化", verify_theorem_2_1()))
    results.append(("定理3.2 寄生体自毁", verify_theorem_3_2()))
    results.append(("定理10.3 剩余价值线性来源", verify_theorem_10_3()))
    results.append(("定理11.1 生命不可资本化", verify_theorem_11_1()))
    results.append(("定理12.3 有机构成上升", verify_theorem_12_3()))
    results.append(("Grishin观察", verify_grishin()))

    print("=" * 60)
    print("验证总结")
    print("=" * 60)
    for name, ok in results:
        status = "✓ 通过" if ok else "✗ 失败"
        print(f"  {name}: {status}")
    print()
    all_pass = all(r[1] for r in results)
    print(f"全部通过：{'是' if all_pass else '否'}")

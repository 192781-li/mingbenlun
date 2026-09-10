"""yinyang_hexagram.py — 演示"阳主阴从"在卦位上的表达，及乾/复两卦的存在论读法

对应《明本论》卷九术数扬弃·河图六爻与量论：
    六爻自下而上六个位阶；阳爻居阳位（初/三/五）为正、阴爻居阴位（二/四/上）为正，
    这是"阳主阴从"在卦位上的表达。
    乾（纯阳）上九"亢龙有悔"＝阳极生阴，纯阳无阴则阳无所附；
    复（一阳生于五阴之下）＝旧的阴压到极致，新的阳从底层升起（否定之否定）。
复用 core.yin_yang：Yang 主、Yin 从，阳主阴从＝健康，阴夺阳位＝异化。
"""
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.yin_yang import Yin, Yang, yang_governs_yin

YANG_LINES = {1, 3, 5}   # 阳位：初、三、五
YIN_LINES = {2, 4, 6}    # 阴位：二、四、上


@dataclass
class HexLine:
    pos: int          # 1..6 从下而上
    is_yang: bool     # True=阳爻，False=阴爻

    @property
    def proper(self) -> bool:
        """阳爻居阳位、阴爻居阴位为正——阳主阴从在卦位上的表达。"""
        return (self.is_yang and self.pos in YANG_LINES) or \
               (not self.is_yang and self.pos in YIN_LINES)


def demo() -> None:
    yang = Yang()

    # 阳主阴从卦位规则演示
    lines = [HexLine(p, is_yang=(p in YANG_LINES)) for p in range(1, 7)]
    proper = [ln.proper for ln in lines]
    print("六爻位阶(1=初..6=上) 阳主阴从正位判定：", proper)
    assert all(proper)  # 阳居阳位、阴居阴位，皆正

    # 乾卦 ☰：纯阳。上九"亢龙有悔"＝阳极生阴
    qian = [HexLine(p, True) for p in range(1, 7)]
    print("\n〔乾·纯阳〕三爻皆阳，发用极致；上九'亢龙有悔'＝阳极生阴，纯阳无阴则阳无所附。")
    assert all(ln.is_yang for ln in qian)
    print("    阳主阴从判据（阳能否主、阴能否从）：", yang_governs_yin(yang, Yin()))

    # 复卦：一阳生于五阴之下（初九为阳，余五阴）＝新的阳从底层升起
    fu = [HexLine(1, True)] + [HexLine(p, False) for p in range(2, 7)]
    print("\n〔复·一阳来复〕五阴压下，初九一阳升起——旧的阴（异化）压到极致，")
    print("    新的阳（解放）从最底层重新生长；革命的曙光期，需'闭关护阳'。")
    assert fu[0].is_yang and not any(ln.is_yang for ln in fu[1:])
    print("    这是否定之否定的直观表达：力量尚小，方向已明，维住它、索出路、图新序。")

    print("\n卦位之法不是宿命预测，而是'阳主阴从'的结构表达：")
    print("    阳居阳位则正（发用有凭依），阴夺阳位则病（异化）；")
    print("    乾示阳极必返阴，复示阴极必生阳——和'反自指必然崩溃／生命能胜'同构。")


if __name__ == "__main__":
    demo()

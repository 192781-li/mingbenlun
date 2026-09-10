"""mingxing_homogeneous.py — 演示"明性同型"与"英雄涌现"：同型的人杀不完

对应《明本论》卷八人文论·必然与英雄：
    英雄不是被"历史规律"从人群里拽出的木偶，也不是决定历史的孤星；
    是无数"明性同型"的人在压迫结构中自觉站起来——人民才是英雄。
    明性不是天才的私有物，是生命史自指操作的产物；只要 S=f(S) 还在运行，
    根（自指结构）在土里，条件到就冒，杀不完。
复用 core.operation：明性 = 操作 S=f(S) 的不动点（持续运行即持续存在）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.operation import self_referential_fixed_point


def emerge(seed: int, killed: int) -> int:
    """同型的人杀不完：根（自指结构）在，条件到就冒。

    存活者把明性传给下一代（劳动、说话、记和学），新一批自然长出。
    """
    alive = max(0, seed - killed)
    return alive + int(alive * 1.5) + 10  # 自我复制 + 新的从生活中涌现


def demo() -> None:
    # 明性 = S=f(S) 的不动点：只要自指操作持续，明性就持续
    r = self_referential_fixed_point(lambda x: 0.6 * x + 0.4, 0.0)
    print("明性不动点（S=f(S) 持续运行）：", round(r.value, 4),
          "｜ 活圈：", r.kind == "live_loop")

    print("\n同型的人杀不完：")
    for killed in (0, 80, 95):
        print(f"    清除 {killed} 人后，新涌现的明性自觉者：{emerge(100, killed)}")

    # 极端黑暗时刻：几乎全被清除
    last = emerge(100, 99)
    print(f"\n即便清除 99 人，仍涌出 {last} 个——根（自指结构）在，")
    print("    条件到就冒；这不是上帝保证春风，是野火烧不尽。")


if __name__ == "__main__":
    demo()

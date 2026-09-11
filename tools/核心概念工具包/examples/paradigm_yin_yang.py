"""paradigm_yin_yang.py — 演示"科学范式作为阴（操作框架）"与阳主阴从的科学观

对应《明本论》卷七格物论·科学哲学：
    科学 = 阳（活的研究）与阴（沉淀的理论框架／范式）的统一。
    范式（阴）为研究（阳）服务；当范式不再能指导研究时，阳更新阴（科学革命）。
    把范式当不可挑战的教条 = 阴压阳，科学僵化（即库恩批评之超越）。

复用 core.yin_yang：Yin 承载"符号"层的理论操作集合（阴），
Yang 既能 option_set 内选择、又能 transform 重写该集合（阳主阴从）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.yin_yang import Yin, Yang, yang_governs_yin


def demo() -> None:
    yang = Yang()

    # 牛顿范式（阴）："符号"层承载当时允许的理论操作
    newton = Yin(constraints={
        "符号": ["轨道计算", "摄动修正", "观测拟合"],
        "物理": [], "生物": [], "环境": [], "社会": [],
    })
    print("〔常规科学〕牛顿范式下的可行路径（阴限定）：", newton.option_set())

    # 常规科学是阴的正常运作：在框架内积累、解谜
    # ——但此时阳只能"选"，尚未"改"，阴压阳的苗头已现
    print("    研究者只能在框内取舍：", yang.choose(newton))

    # 科学革命：阳更新阴——反常积累后，框架本身被替换
    yang.transform(newton, "符号", ["时空几何", "光线偏折预测", "质能关系"])
    print("〔科学革命〕阳更新阴后可行路径：", newton.option_set())

    # 健康科学 = 阳主阴从：阳既能选、又能改写阴
    print("    阳主阴从成立：", yang_governs_yin(yang, newton))

    # 教条化 = 阴压阳：框架被当绝对真理，阳被剥夺"改地"之力
    # （此处以"从不允许调用 transform"表示框架锁死）
    dogmatic = Yin(constraints={
        "符号": ["轨道计算", "摄动修正"],
        "物理": [], "生物": [], "环境": [], "社会": [],
    })
    frozen = dogmatic.option_set()
    print("\n〔教条化·阴压阳〕若阳永不更新，框架锁死于：", frozen)
    assert set(frozen) == {"轨道计算", "摄动修正"}
    # 科学之所以为科学，不在范式永恒，而在阳能更新阴
    assert yang_governs_yin(yang, dogmatic) is True  # 阳本有改地之力

    print("\n生命论科学观：范式（阴）是沉淀的操作框架；")
    print("    阳主阴从则活（框架为研究服务、可被实践更新），")
    print("    阴压阳则僵（框架被当绝对真理、反成认识枷锁）。")


if __name__ == "__main__":
    demo()

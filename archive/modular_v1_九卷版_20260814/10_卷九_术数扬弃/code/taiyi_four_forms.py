"""taiyi_four_forms.py — 演示太乙四凶格（掩迫击格）作为反自指四种形态的直观模型

对应《明本论》卷九术数扬弃·术数的去神秘化：
    去掉神秘外衣，太乙四凶格描述了反自指统治的四种形态——
      掩＝名实遮蔽（意识形态一手）／迫＝身体压迫（暴力一手）／
      击＝阶级斗争爆发／格＝系统僵死（稳态壳子）。
    术数模型是对统治结构的"直观把握"，可作分析辅助，但不能代替对具体社会的经验研究。
"""
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.yin_yang import Yin, Yang  # 仅借"阴压阳"判据符号


@dataclass
class TaiyiForm:
    name: str            # 四凶格之一
    antiphase: str       # 对应反自指形态
    life_meaning: str    # 对生命论的含义


def demo() -> None:
    forms = [
        TaiyiForm("掩", "名实遮蔽（商品拜物教／历史修正主义）", "文的一手：意识形态遮蔽，让被压迫者连'该怀疑'都想不到"),
        TaiyiForm("迫", "身体压迫（996／算法管控／暴力机器）", "武的一手：直接的身体异化、相对过剩人口、警察国家"),
        TaiyiForm("击", "阶级斗争（排异反应／革命）", "矛盾的爆发：被压迫者反抗、压迫者镇压"),
        TaiyiForm("格", "系统僵死（官僚主义／稳态壳子）", "阴阳格拒：信息堵塞、形式主义、壳子阶段"),
    ]

    print("太乙四凶格 → 反自指四种形态（去神秘化读法）：")
    for f in forms:
        print(f"  〔{f.name}〕{f.antiphase}")
        print(f"        ＝ {f.life_meaning}")

    chain = "→".join(f.name for f in forms)
    print(f"\n链条：{chain} ＝ 反自指从思想遮蔽→身体压迫→矛盾爆发→系统僵死。")
    print("说明：这是术数模型对统治结构的直观把握，")
    print("      可作分析辅助，但不代替对具体社会的经验研究（不声称能'预测'定数）。")
    # 仅以 core 符号印证"阴压阳"判据的存在（不引入新实体）
    _ = (Yin(), Yang())


if __name__ == "__main__":
    demo()

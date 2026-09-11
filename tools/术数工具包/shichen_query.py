#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时辰属性查询工具
功能：
1. 单时辰查询：输入公历年月日时，输出该时辰完整属性
2. 一日十二时辰查询：输入年月日，输出当天12个时辰对比表
3. 流时T值影响：输入某人八字和当前时间，计算流时对该人T值的影响

用法：
  python3 shichen_query.py 单时辰 2026 9 11 17
  python3 shichen_query.py 一日 2026 9 11
  python3 shichen_query.py 流时 2008 9 25 7 2026 9 11 17
  （流时：前四个是出生时间，后四个是当前查询时间）
"""

from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bazi_paipan import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES,
    STEM_ELEMENT, STEM_YIN_YANG,
    BRANCH_ELEMENT, BRANCH_YIN_YANG,
    BRANCH_HIDDEN_STEMS, NAYIN,
    GENERATES, OVERCOMES,
    get_shishen, get_kongwang, paipan
)

try:
    from t_value_calculator import calc_T as calc_T_v33
    T_CALC_AVAILABLE = True
except ImportError:
    T_CALC_AVAILABLE = False


# ==================== 时辰基础数据 ====================

# 十二时辰对应时间（北京时间）
SHICHEN_TIME = {
    "子": "23:00-01:00",
    "丑": "01:00-03:00",
    "寅": "03:00-05:00",
    "卯": "05:00-07:00",
    "辰": "07:00-09:00",
    "巳": "09:00-11:00",
    "午": "11:00-13:00",
    "未": "13:00-15:00",
    "申": "15:00-17:00",
    "酉": "17:00-19:00",
    "戌": "19:00-21:00",
    "亥": "21:00-23:00",
}

# 时辰别称
SHICHEN_ALIAS = {
    "子": "夜半、子夜",
    "丑": "鸡鸣",
    "寅": "平旦、黎明",
    "卯": "日出",
    "辰": "食时",
    "巳": "隅中",
    "午": "日中",
    "未": "日昳",
    "申": "晡时",
    "酉": "日入",
    "戌": "黄昏",
    "亥": "人定",
}

# 驿马（日支查）
MA_XING = {
    "申": "寅", "子": "寅", "辰": "寅",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥",
    "亥": "巳", "卯": "巳", "未": "巳",
}


def get_ma_xing(day_zhi):
    """根据日支查驿马"""
    return MA_XING.get(day_zhi, "")


# 五行旺相休囚死
def get_wuxing_wangshuai(month_branch):
    """根据月支判断五行旺相休囚死"""
    month_elem = BRANCH_ELEMENT[month_branch]
    result = {}
    for elem in ["木", "火", "土", "金", "水"]:
        if elem == month_elem:
            result[elem] = "旺"
        elif GENERATES[month_elem] == elem:
            result[elem] = "相"
        elif GENERATES[elem] == month_elem:
            result[elem] = "休"
        elif OVERCOMES[elem] == month_elem:
            result[elem] = "囚"
        elif OVERCOMES[month_elem] == elem:
            result[elem] = "死"
    return result


# ==================== 时辰排盘 ====================

def get_shichen_properties(year, month, day, hour, day_master=None):
    """获取单个时辰的完整属性"""
    # 用bazi_paipan排盘
    result = paipan(year, month, day, hour, gender="男")
    pillars = result["四柱"]
    day_gan = pillars["日柱"]["天干"]

    if day_master is None:
        day_master = day_gan

    hour_zhi = pillars["时柱"]["地支"]

    result_out = {
        "公历": f"{year}年{month}月{day}日 {hour:02d}时",
        "时辰": hour_zhi,
        "时辰时间": SHICHEN_TIME[hour_zhi],
        "时辰别称": SHICHEN_ALIAS[hour_zhi],
        "四柱": {},
        "空亡": get_kongwang(pillars["日柱"]["天干"] + pillars["日柱"]["地支"]),
        "马星": get_ma_xing(pillars["日柱"]["地支"]),
        "五行旺衰": get_wuxing_wangshuai(pillars["月柱"]["地支"]),
    }

    # 各柱详细属性
    for pillar_name in ["年柱", "月柱", "日柱", "时柱"]:
        p = pillars[pillar_name]
        gan = p["天干"]
        zhi = p["地支"]
        pillar_info = {
            "天干": gan,
            "地支": zhi,
            "干支": gan + zhi,
            "天干五行": STEM_ELEMENT[gan],
            "天干阴阳": STEM_YIN_YANG[gan],
            "地支五行": BRANCH_ELEMENT[zhi],
            "地支阴阳": BRANCH_YIN_YANG[zhi],
            "纳音": p.get("纳音", NAYIN.get(gan + zhi, "")),
            "藏干": BRANCH_HIDDEN_STEMS[zhi],
            "十神": get_shishen(day_master, gan),
        }
        result_out["四柱"][pillar_name] = pillar_info

    # 时柱对日主的影响
    hour_gan = pillars["时柱"]["天干"]
    hour_gan_elem = STEM_ELEMENT[hour_gan]
    hour_zhi_elem = BRANCH_ELEMENT[hour_zhi]
    day_elem = STEM_ELEMENT[day_master]
    print_elem = [e for e in ['木','火','土','金','水'] if GENERATES[e] == day_elem][0]

    if hour_gan_elem == day_elem or hour_gan_elem == print_elem:
        gan_effect = "帮身（生扶）"
    else:
        gan_effect = "克泄耗（消耗）"

    if hour_zhi_elem == day_elem or hour_zhi_elem == print_elem:
        zhi_effect = "帮身（生扶）"
    else:
        zhi_effect = "克泄耗（消耗）"

    result_out["时柱对日主影响"] = {
        "时干十神": get_shishen(day_master, hour_gan),
        "时干影响": gan_effect,
        "时支影响": zhi_effect,
    }

    return result_out


def print_shichen(props):
    """打印单个时辰属性"""
    print("=" * 60)
    print(f"  时辰属性查询：{props['公历']}")
    print("=" * 60)

    print(f"\n【基本信息】")
    print(f"  时辰：{props['时辰']}时（{props['时辰时间']}）")
    print(f"  别称：{props['时辰别称']}")
    print(f"  空亡：{props['空亡']}")
    print(f"  驿马：{props['马星']}")

    print(f"\n【五行旺衰（月令）】")
    for elem, state in props["五行旺衰"].items():
        print(f"  {elem}: {state}")

    print(f"\n【四柱详细】")
    print(f"  {'':<6}{'年柱':<12}{'月柱':<12}{'日柱':<12}{'时柱':<12}")

    # 干支
    print(f"  {'干支':<6}", end="")
    for p in ["年柱", "月柱", "日柱", "时柱"]:
        print(f"{props['四柱'][p]['干支']:<12}", end="")
    print()

    # 十神
    print(f"  {'十神':<6}", end="")
    for p in ["年柱", "月柱", "日柱", "时柱"]:
        print(f"{props['四柱'][p]['十神']:<12}", end="")
    print()

    # 天干五行
    print(f"  {'天干':<6}", end="")
    for p in ["年柱", "月柱", "日柱", "时柱"]:
        info = props['四柱'][p]
        print(f"{info['天干']}({info['天干五行']}{info['天干阴阳']}){'':<4}", end="")
    print()

    # 地支五行
    print(f"  {'地支':<6}", end="")
    for p in ["年柱", "月柱", "日柱", "时柱"]:
        info = props['四柱'][p]
        print(f"{info['地支']}({info['地支五行']}{info['地支阴阳']}){'':<4}", end="")
    print()

    # 藏干
    print(f"  {'藏干':<6}", end="")
    for p in ["年柱", "月柱", "日柱", "时柱"]:
        hidden = "".join(props['四柱'][p]['藏干'])
        print(f"{hidden:<12}", end="")
    print()

    # 纳音
    print(f"  {'纳音':<6}", end="")
    for p in ["年柱", "月柱", "日柱", "时柱"]:
        print(f"{props['四柱'][p]['纳音']:<12}", end="")
    print()

    # 时柱对日主影响
    effect = props["时柱对日主影响"]
    print(f"\n【时柱对日主影响】")
    print(f"  时干十神：{effect['时干十神']}")
    print(f"  时干影响：{effect['时干影响']}")
    print(f"  时支影响：{effect['时支影响']}")

    print("\n" + "=" * 60)


def print_day_shichen(year, month, day, day_master=None):
    """打印一天12个时辰的对比表"""
    print("=" * 80)
    print(f"  一日十二时辰属性对比：{year}年{month}月{day}日")
    print("=" * 80)

    if day_master:
        print(f"\n  日主：{day_master}（{STEM_ELEMENT[day_master]}）")

    print(f"\n  {'时辰':<6}{'时间':<14}{'时柱':<8}{'时干十神':<10}{'时干五行':<10}{'时支五行':<10}{'对日主':<12}")
    print("  " + "-" * 74)

    for hour in [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]:
        props = get_shichen_properties(year, month, day, hour, day_master)
        p = props["四柱"]["时柱"]
        effect = props["时柱对日主影响"]

        if day_master:
            effect_str = effect["时干影响"]
        else:
            effect_str = "-"

        print(f"  {props['时辰']:<6}{props['时辰时间']:<14}{p['干支']:<8}{p['十神']:<10}{p['天干五行']:<10}{p['地支五行']:<10}{effect_str:<12}")

    print("\n" + "=" * 80)
    print("  注：子时跨日（23:00-01:00），上表以0点为子时代表")
    print("=" * 80)


def print_liushi_T(birth_year, birth_month, birth_day, birth_hour,
                    query_year, query_month, query_day, query_hour):
    """计算流时对某人T值的影响"""
    # 出生八字
    birth_result = paipan(birth_year, birth_month, birth_day, birth_hour, gender="男")
    birth_pillars = birth_result["四柱"]
    day_master = birth_pillars["日柱"]["天干"]
    birth_four = [
        birth_pillars["年柱"]["天干"] + birth_pillars["年柱"]["地支"],
        birth_pillars["月柱"]["天干"] + birth_pillars["月柱"]["地支"],
        birth_pillars["日柱"]["天干"] + birth_pillars["日柱"]["地支"],
        birth_pillars["时柱"]["天干"] + birth_pillars["时柱"]["地支"],
    ]

    # 当前流时
    current_props = get_shichen_properties(query_year, query_month, query_day, query_hour, day_master)
    current_pillars = current_props["四柱"]

    print("=" * 70)
    print(f"  流时T值影响分析")
    print("=" * 70)

    print(f"\n【出生八字】")
    print(f"  日主：{day_master}（{STEM_ELEMENT[day_master]}）")
    print(f"  四柱：{' '.join(birth_four)}")

    print(f"\n【当前流时】")
    print(f"  时间：{current_props['公历']}")
    print(f"  时辰：{current_props['时辰']}时（{current_props['时辰时间']}）")
    print(f"  流年：{current_pillars['年柱']['干支']}（{current_pillars['年柱']['十神']}）")
    print(f"  流月：{current_pillars['月柱']['干支']}（{current_pillars['月柱']['十神']}）")
    print(f"  流日：{current_pillars['日柱']['干支']}（{current_pillars['日柱']['十神']}）")
    print(f"  流时：{current_pillars['时柱']['干支']}（{current_pillars['时柱']['十神']}）")

    # 计算原局T值
    if T_CALC_AVAILABLE:
        try:
            four_pillars_list = [
                (birth_pillars["年柱"]["天干"], birth_pillars["年柱"]["地支"]),
                (birth_pillars["月柱"]["天干"], birth_pillars["月柱"]["地支"]),
                (birth_pillars["日柱"]["天干"], birth_pillars["日柱"]["地支"]),
                (birth_pillars["时柱"]["天干"], birth_pillars["时柱"]["地支"]),
            ]
            t_result = calc_T_v33(day_master, birth_pillars["月柱"]["地支"], four_pillars_list, method='v33')
            # calc_T返回元组：(T值, 总评, 五行力量, 帮身, 总力量, 组合效应)
            base_T = t_result[0]
            base_rating = t_result[1]
            print(f"\n【原局T值】")
            print(f"  T值：{base_T}（{base_rating}）")
        except Exception as e:
            print(f"\n【原局T值】计算失败：{e}")
            base_T = None
    else:
        base_T = None

    # 流时干支对日主的影响
    print(f"\n【流时干支对日主影响】")
    day_elem = STEM_ELEMENT[day_master]
    print_elem = [e for e in ['木','火','土','金','水'] if GENERATES[e] == day_elem][0]

    total_bangshen = 0
    total_kexiehao = 0
    for pillar_name in ["年柱", "月柱", "日柱", "时柱"]:
        p = current_pillars[pillar_name]
        gan_elem = STEM_ELEMENT[p["天干"]]
        zhi_elem = BRANCH_ELEMENT[p["地支"]]

        bangshen = 0
        kexiehao = 0
        for elem in [gan_elem, zhi_elem]:
            if elem == day_elem or elem == print_elem:
                bangshen += 1
            else:
                kexiehao += 1

        total_bangshen += bangshen
        total_kexiehao += kexiehao

        if bangshen > kexiehao:
            effect = "T↑帮身"
        elif kexiehao > bangshen:
            effect = "T↓克泄耗"
        else:
            effect = "T→平衡"

        print(f"  {pillar_name} {p['干支']}（{p['十神']}）：{effect}（帮{bangshen}/耗{kexiehao}）")

    print(f"\n  总计：帮身{total_bangshen}，克泄耗{total_kexiehao}")
    if total_bangshen > total_kexiehao:
        print(f"  当前流时整体：T↑（帮身运，适合学习、创作、输出）")
    elif total_kexiehao > total_bangshen:
        print(f"  当前流时整体：T↓（克泄耗运，适合休息、吸收、蓄能）")
    else:
        print(f"  当前流时整体：T→（平衡运，皆宜）")

    # 具体建议
    print(f"\n【操作建议】")
    if total_bangshen > total_kexiehao:
        print("  当前能量偏旺，适合：")
        print("    - 做需要创造力、表达力的事（伤官食神发力）")
        print("    - 学习新东西、思考深度问题（印星生身）")
        print("    - 社交、沟通、表达（比劫帮身）")
        print("    - 不适合：过度休息、拖延、内耗")
    elif total_kexiehao > total_bangshen:
        print("  当前能量偏弱，适合：")
        print("    - 休息、睡眠、恢复能量")
        print("    - 做简单、机械、不需要太多创造力的事")
        print("    - 吸收知识、阅读、听课（印星补身）")
        print("    - 不适合：重大决策、激烈争论、高强度输出")
    else:
        print("  当前能量平衡，皆宜。注意劳逸结合。")

    print("\n" + "=" * 70)


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：")
        print("  python3 shichen_query.py 单时辰 年 月 日 时 [日主]")
        print("  python3 shichen_query.py 一日 年 月 日 [日主]")
        print("  python3 shichen_query.py 流时 出生年 月 日 时 查询年 月 日 时")
        print("\n示例：")
        print("  python3 shichen_query.py 单时辰 2026 9 11 17")
        print("  python3 shichen_query.py 一日 2026 9 11 戊")
        print("  python3 shichen_query.py 流时 2008 9 25 7 2026 9 11 17")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "单时辰":
        year = int(sys.argv[2])
        month = int(sys.argv[3])
        day = int(sys.argv[4])
        hour = int(sys.argv[5])
        day_master = sys.argv[6] if len(sys.argv) > 6 else None
        props = get_shichen_properties(year, month, day, hour, day_master)
        print_shichen(props)

    elif mode == "一日":
        year = int(sys.argv[2])
        month = int(sys.argv[3])
        day = int(sys.argv[4])
        day_master = sys.argv[5] if len(sys.argv) > 5 else None
        print_day_shichen(year, month, day, day_master)

    elif mode == "流时":
        birth_year = int(sys.argv[2])
        birth_month = int(sys.argv[3])
        birth_day = int(sys.argv[4])
        birth_hour = int(sys.argv[5])
        query_year = int(sys.argv[6])
        query_month = int(sys.argv[7])
        query_day = int(sys.argv[8])
        query_hour = int(sys.argv[9])
        print_liushi_T(birth_year, birth_month, birth_day, birth_hour,
                        query_year, query_month, query_day, query_hour)

    else:
        print(f"未知模式：{mode}")
        print("可用模式：单时辰、一日、流时")
        sys.exit(1)

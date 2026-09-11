#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T值硬判断计算器 v1.0
公式：T = Σ(帮身力量) - Σ(克泄耗力量)
权重：月令 > 天干 > 地支本气 > 地支藏干
用法：python3 t_value_calculator.py <年柱> <月柱> <日柱> <时柱>
示例：python3 t_value_calculator.py 戊子 辛酉 戊辰 丙辰
"""

import sys

# 五行对应
STEM_ELEMENT = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
BRANCH_ELEMENT = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
GENERATES = {'木':'火','火':'土','土':'金','金':'水','水':'木'}  # 我生
OVERCOMES = {'木':'土','土':'水','水':'火','火':'金','金':'木'}  # 我克

# 地支藏干（本气、中气、余气，带比例）
BRANCH_HIDDEN = {
    '子':[('癸',1.0)],
    '丑':[('己',0.6),('癸',0.3),('辛',0.1)],
    '寅':[('甲',0.6),('丙',0.3),('戊',0.1)],
    '卯':[('乙',1.0)],
    '辰':[('戊',0.6),('乙',0.3),('癸',0.1)],
    '巳':[('丙',0.6),('庚',0.3),('戊',0.1)],
    '午':[('丁',0.7),('己',0.3)],
    '未':[('己',0.6),('丁',0.3),('乙',0.1)],
    '申':[('庚',0.6),('壬',0.3),('戊',0.1)],
    '酉':[('辛',1.0)],
    '戌':[('戊',0.6),('辛',0.3),('丁',0.1)],
    '亥':[('壬',0.7),('甲',0.3)]
}

def get_shishen(day_stem, other_stem):
    """计算十神"""
    day_elem = STEM_ELEMENT[day_stem]
    other_elem = STEM_ELEMENT[other_stem]
    day_yy = '阳' if day_stem in '甲丙戊庚壬' else '阴'
    other_yy = '阳' if other_stem in '甲丙戊庚壬' else '阴'
    if day_elem == other_elem:
        return '比肩' if day_yy == other_yy else '劫财'
    elif GENERATES[day_elem] == other_elem:
        return '食神' if day_yy == other_yy else '伤官'
    elif GENERATES[other_elem] == day_elem:
        return '偏印' if day_yy == other_yy else '正印'
    elif OVERCOMES[other_elem] == day_elem:
        return '七杀' if day_yy == other_yy else '正官'
    elif OVERCOMES[day_elem] == other_elem:
        return '偏财' if day_yy == other_yy else '正财'
    return '未知'

def calc_T(day_stem, month_branch, four_pillars):
    """
    T值硬判断
    T = Σ(帮身力量) - Σ(克泄耗力量)
    返回：(T值, 总评, 明细字典)
    """
    day_elem = STEM_ELEMENT[day_stem]
    month_elem = BRANCH_ELEMENT[month_branch]
    T = 0
    detail = {'月令':0, '天干帮扶':0, '天干克泄耗':0, '地支帮扶':0, '地支克泄耗':0, '藏干帮扶':0, '藏干克泄耗':0}

    # 1. 月令（权重最高）
    if month_elem == day_elem:
        T += 30; detail['月令'] = 30  # 旺
    elif GENERATES[month_elem] == day_elem:
        T += 20; detail['月令'] = 20  # 休（月令生我）
    elif GENERATES[day_elem] == month_elem:
        T -= 15; detail['月令'] = -15  # 相（我生月令=泄身）
    elif OVERCOMES[month_elem] == day_elem:
        T -= 25; detail['月令'] = -25  # 囚（月令克我）
    elif OVERCOMES[day_elem] == month_elem:
        T -= 10; detail['月令'] = -10  # 死（我克月令=耗身）

    # 2. 天干（除日主）
    for stem, branch in four_pillars:
        if stem == day_stem:
            continue
        ss = get_shishen(day_stem, stem)
        if ss in ['比肩','劫财']:
            T += 10; detail['天干帮扶'] += 10
        elif ss in ['正印','偏印']:
            T += 8; detail['天干帮扶'] += 8
        elif ss in ['七杀','正官']:
            T -= 10; detail['天干克泄耗'] -= 10
        elif ss in ['食神','伤官']:
            T -= 8; detail['天干克泄耗'] -= 8
        elif ss in ['正财','偏财']:
            T -= 8; detail['天干克泄耗'] -= 8

    # 3. 地支本气
    for stem, branch in four_pillars:
        main_hidden = BRANCH_HIDDEN[branch][0][0]
        ss = get_shishen(day_stem, main_hidden)
        if ss in ['比肩','劫财']:
            T += 12; detail['地支帮扶'] += 12
        elif ss in ['正印','偏印']:
            T += 10; detail['地支帮扶'] += 10
        elif ss in ['七杀','正官']:
            T -= 12; detail['地支克泄耗'] -= 12
        elif ss in ['食神','伤官']:
            T -= 10; detail['地支克泄耗'] -= 10
        elif ss in ['正财','偏财']:
            T -= 10; detail['地支克泄耗'] -= 10

    # 4. 地支藏干（除本气）
    for stem, branch in four_pillars:
        hidden_list = BRANCH_HIDDEN[branch]
        for i, (h, ratio) in enumerate(hidden_list):
            if i == 0:  # 本气已算
                continue
            ss = get_shishen(day_stem, h)
            if ss in ['比肩','劫财']:
                w = int(4 * ratio); T += w; detail['藏干帮扶'] += w
            elif ss in ['正印','偏印']:
                w = int(3 * ratio); T += w; detail['藏干帮扶'] += w
            elif ss in ['七杀','正官']:
                w = int(4 * ratio); T -= w; detail['藏干克泄耗'] -= w
            elif ss in ['食神','伤官']:
                w = int(3 * ratio); T -= w; detail['藏干克泄耗'] -= w
            elif ss in ['正财','偏财']:
                w = int(3 * ratio); T -= w; detail['藏干克泄耗'] -= w

    # 总评
    if T >= 40: rating = "身强"
    elif T >= 15: rating = "偏强"
    elif T >= -15: rating = "中和"
    elif T >= -40: rating = "偏弱"
    else: rating = "身弱"

    return T, rating, detail

def main():
    if len(sys.argv) != 5:
        print("用法：python3 t_value_calculator.py <年柱> <月柱> <日柱> <时柱>")
        print("示例：python3 t_value_calculator.py 戊子 辛酉 戊辰 丙辰")
        sys.exit(1)

    pillars = [(sys.argv[1][0], sys.argv[1][1]),
                (sys.argv[2][0], sys.argv[2][1]),
                (sys.argv[3][0], sys.argv[3][1]),
                (sys.argv[4][0], sys.argv[4][1])]
    day_stem = sys.argv[3][0]
    month_branch = sys.argv[2][1]

    T, rating, detail = calc_T(day_stem, month_branch, pillars)

    print("=" * 60)
    print(f"  T值硬判断 v1.0")
    print("=" * 60)
    print(f"  八字：{sys.argv[1]} {sys.argv[2]} {sys.argv[3]} {sys.argv[4]}")
    print(f"  日主：{day_stem}（{STEM_ELEMENT[day_stem]}）")
    print(f"  月令：{month_branch}（{BRANCH_ELEMENT[month_branch]}）")
    print("-" * 60)
    print(f"  月令贡献：{detail['月令']:+d}")
    print(f"  天干帮扶：{detail['天干帮扶']:+d}")
    print(f"  天干克泄耗：{detail['天干克泄耗']:+d}")
    print(f"  地支帮扶：{detail['地支帮扶']:+d}")
    print(f"  地支克泄耗：{detail['地支克泄耗']:+d}")
    print(f"  藏干帮扶：{detail['藏干帮扶']:+d}")
    print(f"  藏干克泄耗：{detail['藏干克泄耗']:+d}")
    print("-" * 60)
    print(f"  T值 = {T}")
    print(f"  总评 = {rating}")
    print("=" * 60)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T值硬判断计算器 v2.0
v2.0（默认）：五行力量占比法 T=(帮身/总力量)×100-50
v1.0（对比）：绝对值累加法 T=Σ(帮身)-Σ(克泄耗)
用法：python3 t_value_calculator.py <年柱> <月柱> <日柱> <时柱> [--method v1|v2]
示例：python3 t_value_calculator.py 戊子 辛酉 戊辰 丙辰
"""

import sys
import argparse

STEM_ELEMENT = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
BRANCH_ELEMENT = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
GENERATES = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
OVERCOMES = {'木':'土','土':'水','水':'火','火':'金','金':'木'}
BRANCH_HIDDEN = {
    '子':[('癸',1.0)], '丑':[('己',0.6),('癸',0.3),('辛',0.1)],
    '寅':[('甲',0.6),('丙',0.3),('戊',0.1)], '卯':[('乙',1.0)],
    '辰':[('戊',0.6),('乙',0.3),('癸',0.1)], '巳':[('丙',0.6),('庚',0.3),('戊',0.1)],
    '午':[('丁',0.7),('己',0.3)], '未':[('己',0.6),('丁',0.3),('乙',0.1)],
    '申':[('庚',0.6),('壬',0.3),('戊',0.1)], '酉':[('辛',1.0)],
    '戌':[('戊',0.6),('辛',0.3),('丁',0.1)], '亥':[('壬',0.7),('甲',0.3)]
}

def get_shishen(day_stem, other_stem):
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

def get_print_element(day_elem):
    """获取印星五行（生我者）"""
    for e in ['木','火','土','金','水']:
        if GENERATES[e] == day_elem:
            return e
    return None

def calc_wuxing_power(four_pillars, month_branch):
    """计算五行力量分布"""
    power = {'木':0,'火':0,'土':0,'金':0,'水':0}
    for stem, branch in four_pillars:
        power[STEM_ELEMENT[stem]] += 10  # 天干10分
        for j, (h, ratio) in enumerate(BRANCH_HIDDEN[branch]):
            if j == 0:
                base = 12
                if branch == month_branch:
                    base += 15  # 月令本气额外+15
            elif j == 1:
                base = 4
            else:
                base = 2
            power[STEM_ELEMENT[h]] += base
    return power

def calc_T_v2(day_stem, month_branch, four_pillars):
    """v2.0：五行力量占比法"""
    day_elem = STEM_ELEMENT[day_stem]
    print_elem = get_print_element(day_elem)
    power = calc_wuxing_power(four_pillars, month_branch)
    total = sum(power.values())
    support = power[day_elem] + power[print_elem]
    T = round(support / total * 100 - 50, 1)
    if T >= 15: rating = "身强"
    elif T >= 5: rating = "偏强"
    elif T >= -5: rating = "中和"
    elif T >= -15: rating = "偏弱"
    else: rating = "身弱"
    return T, rating, power, support, total

def calc_T_v1(day_stem, month_branch, four_pillars):
    """v1.0：绝对值累加法（保留用于对比）"""
    day_elem = STEM_ELEMENT[day_stem]
    month_elem = BRANCH_ELEMENT[month_branch]
    T = 0
    # 月令
    if month_elem == day_elem: T += 30
    elif GENERATES[month_elem] == day_elem: T += 20
    elif GENERATES[day_elem] == month_elem: T -= 15
    elif OVERCOMES[month_elem] == day_elem: T -= 25
    elif OVERCOMES[day_elem] == month_elem: T -= 10
    # 天干
    for stem, branch in four_pillars:
        if stem == day_stem: continue
        ss = get_shishen(day_stem, stem)
        if ss in ['比肩','劫财']: T += 10
        elif ss in ['正印','偏印']: T += 8
        elif ss in ['七杀','正官']: T -= 10
        elif ss in ['食神','伤官']: T -= 8
        elif ss in ['正财','偏财']: T -= 8
    # 地支本气
    for stem, branch in four_pillars:
        main_hidden = BRANCH_HIDDEN[branch][0][0]
        ss = get_shishen(day_stem, main_hidden)
        if ss in ['比肩','劫财']: T += 12
        elif ss in ['正印','偏印']: T += 10
        elif ss in ['七杀','正官']: T -= 12
        elif ss in ['食神','伤官']: T -= 10
        elif ss in ['正财','偏财']: T -= 10
    # 藏干
    for stem, branch in four_pillars:
        for i, (h, ratio) in enumerate(BRANCH_HIDDEN[branch]):
            if i == 0: continue
            ss = get_shishen(day_stem, h)
            if ss in ['比肩','劫财']: T += int(4*ratio)
            elif ss in ['正印','偏印']: T += int(3*ratio)
            elif ss in ['七杀','正官']: T -= int(4*ratio)
            elif ss in ['食神','伤官']: T -= int(3*ratio)
            elif ss in ['正财','偏财']: T -= int(3*ratio)
    if T >= 40: rating = "身强"
    elif T >= 15: rating = "偏强"
    elif T >= -15: rating = "中和"
    elif T >= -40: rating = "偏弱"
    else: rating = "身弱"
    return T, rating

def main():
    parser = argparse.ArgumentParser(description='T值硬判断计算器')
    parser.add_argument('pillars', nargs=4, help='年柱 月柱 日柱 时柱')
    parser.add_argument('--method', choices=['v1','v2'], default='v2', help='计算方法（默认v2）')
    args = parser.parse_args()

    pillars = [(p[0], p[1]) for p in args.pillars]
    day_stem = args.pillars[2][0]
    month_branch = args.pillars[1][1]
    day_elem = STEM_ELEMENT[day_stem]
    print_elem = get_print_element(day_elem)

    print("=" * 60)
    print(f"  T值硬判断 {args.method.upper()}")
    print("=" * 60)
    print(f"  八字：{' '.join(args.pillars)}")
    print(f"  日主：{day_stem}（{day_elem}）  印星：{print_elem}")
    print("-" * 60)

    if args.method == 'v2':
        T, rating, power, support, total = calc_T_v2(day_stem, month_branch, pillars)
        print(f"  五行力量：木{power['木']} 火{power['火']} 土{power['土']} 金{power['金']} 水{power['水']}")
        print(f"  总力量：{total}")
        print(f"  帮身（{day_elem}+{print_elem}）：{support}（{round(support/total*100,1)}%）")
        print(f"  克泄耗：{total-support}（{round((total-support)/total*100,1)}%）")
        print("-" * 60)
        print(f"  T值 = {T}")
        print(f"  总评 = {rating}")
    else:
        T, rating = calc_T_v1(day_stem, month_branch, pillars)
        print(f"  T值 = {T}")
        print(f"  总评 = {rating}")
    print("=" * 60)

if __name__ == '__main__':
    main()

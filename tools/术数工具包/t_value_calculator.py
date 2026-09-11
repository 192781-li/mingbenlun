#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T值硬判断计算器 v2.1
v2.1（默认）：五行力量占比 + 刑冲合害修正层（不连乘，取最大修正）
v2.0：五行力量占比（无修正）
v1.0：绝对值累加法（对比用）
用法：python3 t_value_calculator.py <年柱> <月柱> <日柱> <时柱> [--method v1|v2|v21]
"""

import sys
import argparse
from collections import Counter

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

LIU_CHONG = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅','卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}
LIU_HE = {'子':'丑','丑':'子','寅':'亥','亥':'寅','卯':'戌','戌':'卯','辰':'酉','酉':'辰','巳':'申','申':'巳','午':'未','未':'午'}
LIU_HAI = {'子':'未','未':'子','丑':'午','午':'丑','寅':'巳','巳':'寅','卯':'辰','辰':'卯','申':'亥','亥':'申','酉':'戌','戌':'酉'}
SAN_XING = {'寅':{'巳','申'},'巳':{'寅','申'},'申':{'寅','巳'},'丑':{'戌','未'},'戌':{'丑','未'},'未':{'丑','戌'},'子':{'卯'},'卯':{'子'}}
ZI_XING = {'辰','酉','午','亥'}

def get_shishen(day_stem, other_stem):
    day_elem = STEM_ELEMENT[day_stem]
    other_elem = STEM_ELEMENT[other_stem]
    day_yy = '阳' if day_stem in '甲丙戊庚壬' else '阴'
    other_yy = '阳' if other_stem in '甲丙戊庚壬' else '阴'
    if day_elem == other_elem: return '比肩' if day_yy == other_yy else '劫财'
    elif GENERATES[day_elem] == other_elem: return '食神' if day_yy == other_yy else '伤官'
    elif GENERATES[other_elem] == day_elem: return '偏印' if day_yy == other_yy else '正印'
    elif OVERCOMES[other_elem] == day_elem: return '七杀' if day_yy == other_yy else '正官'
    elif OVERCOMES[day_elem] == other_elem: return '偏财' if day_yy == other_yy else '正财'
    return '未知'

def get_print_element(day_elem):
    for e in ['木','火','土','金','水']:
        if GENERATES[e] == day_elem: return e
    return None

def get_branch_modifier(branches):
    """刑冲合害修正系数（取最严重的，不连乘）"""
    modifiers = {b: 1.0 for b in branches}
    effects = []
    blist = list(branches)
    for i, b1 in enumerate(blist):
        for b2 in blist[i+1:]:
            if LIU_CHONG.get(b1) == b2:
                modifiers[b1] = min(modifiers[b1], 0.7)
                modifiers[b2] = min(modifiers[b2], 0.7)
                effects.append(f"{b1}{b2}冲")
            elif b2 in SAN_XING.get(b1, set()):
                modifiers[b1] = min(modifiers[b1], 0.8)
                modifiers[b2] = min(modifiers[b2], 0.8)
                effects.append(f"{b1}{b2}刑")
            elif LIU_HE.get(b1) == b2:
                modifiers[b1] = min(modifiers[b1], 0.9)
                modifiers[b2] = min(modifiers[b2], 0.9)
                effects.append(f"{b1}{b2}合")
            elif LIU_HAI.get(b1) == b2:
                modifiers[b1] = min(modifiers[b1], 0.95)
                modifiers[b2] = min(modifiers[b2], 0.95)
                effects.append(f"{b1}{b2}害")
    counts = Counter(branches)
    for b, cnt in counts.items():
        if b in ZI_XING and cnt >= 2:
            modifiers[b] = min(modifiers[b], 0.9)
            effects.append(f"{b}{b}自刑")
    return modifiers, effects

def calc_wuxing_power(four_pillars, month_branch, use_correction=True):
    """计算五行力量（可选刑冲合害修正）"""
    branches = [p[1] for p in four_pillars]
    modifiers, effects = (get_branch_modifier(branches) if use_correction else ({b:1.0 for b in branches}, []))
    power = {'木':0,'火':0,'土':0,'金':0,'水':0}
    for stem, branch in four_pillars:
        power[STEM_ELEMENT[stem]] += 10  # 天干不受修正
        mod = modifiers[branch]
        for j, (h, ratio) in enumerate(BRANCH_HIDDEN[branch]):
            if j == 0: base = 12 + (15 if branch == month_branch else 0)
            elif j == 1: base = 4
            else: base = 2
            power[STEM_ELEMENT[h]] += int(base * mod)
    return power, effects, modifiers

def calc_T(day_stem, month_branch, four_pillars, method='v21'):
    """统一T值计算入口"""
    day_elem = STEM_ELEMENT[day_stem]
    print_elem = get_print_element(day_elem)
    
    if method == 'v1':
        return calc_T_v1(day_stem, month_branch, four_pillars)
    
    use_corr = (method == 'v21')
    power, effects, _ = calc_wuxing_power(four_pillars, month_branch, use_corr)
    total = sum(power.values())
    support = power[day_elem] + power[print_elem]
    T = round(support / total * 100 - 50, 1)
    if T >= 15: rating = "身强"
    elif T >= 5: rating = "偏强"
    elif T >= -5: rating = "中和"
    elif T >= -15: rating = "偏弱"
    else: rating = "身弱"
    return T, rating, power, support, total, effects

def calc_T_v1(day_stem, month_branch, four_pillars):
    """v1.0：绝对值累加法"""
    day_elem = STEM_ELEMENT[day_stem]
    month_elem = BRANCH_ELEMENT[month_branch]
    T = 0
    if month_elem == day_elem: T += 30
    elif GENERATES[month_elem] == day_elem: T += 20
    elif GENERATES[day_elem] == month_elem: T -= 15
    elif OVERCOMES[month_elem] == day_elem: T -= 25
    elif OVERCOMES[day_elem] == month_elem: T -= 10
    for stem, branch in four_pillars:
        if stem == day_stem: continue
        ss = get_shishen(day_stem, stem)
        if ss in ['比肩','劫财']: T += 10
        elif ss in ['正印','偏印']: T += 8
        elif ss in ['七杀','正官']: T -= 10
        elif ss in ['食神','伤官']: T -= 8
        elif ss in ['正财','偏财']: T -= 8
    for stem, branch in four_pillars:
        main_hidden = BRANCH_HIDDEN[branch][0][0]
        ss = get_shishen(day_stem, main_hidden)
        if ss in ['比肩','劫财']: T += 12
        elif ss in ['正印','偏印']: T += 10
        elif ss in ['七杀','正官']: T -= 12
        elif ss in ['食神','伤官']: T -= 10
        elif ss in ['正财','偏财']: T -= 10
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
    return T, rating, None, None, None, []

def main():
    parser = argparse.ArgumentParser(description='T值硬判断计算器 v2.1')
    parser.add_argument('pillars', nargs=4, help='年柱 月柱 日柱 时柱')
    parser.add_argument('--method', choices=['v1','v2','v21'], default='v21', help='计算方法（默认v21）')
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

    result = calc_T(day_stem, month_branch, pillars, args.method)
    T, rating = result[0], result[1]
    
    if args.method == 'v1':
        print(f"  T值 = {T}")
        print(f"  总评 = {rating}")
    else:
        power, support, total, effects = result[2], result[3], result[4], result[5]
        print(f"  五行力量：木{power['木']} 火{power['火']} 土{power['土']} 金{power['金']} 水{power['水']}")
        print(f"  总力量：{total}")
        print(f"  帮身（{day_elem}+{print_elem}）：{support}（{round(support/total*100,1)}%）")
        print(f"  克泄耗：{total-support}（{round((total-support)/total*100,1)}%）")
        if effects:
            print(f"  刑冲合害：{', '.join(effects)}")
        print("-" * 60)
        print(f"  T值 = {T}")
        print(f"  总评 = {rating}")
    print("=" * 60)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T值硬判断计算器 v3.2
v3.2（默认）：五行力量占比 + 六冲力量对比 + 五种十神组合（含互斥逻辑+比劫帮身）
v3.1：五行力量占比 + 六冲力量对比 + 四种十神组合
v3.0：五行力量占比 + 六冲力量对比 + 两种十神组合
v2.2：五行力量占比 + 六冲力量对比
v2.1：五行力量占比 + 刑冲合害修正
v2.0：五行力量占比（无修正）
v1.0：绝对值累加法（对比用）
用法：python3 t_value_calculator.py <年柱> <月柱> <日柱> <时柱> [--method v1|v2|v21|v22|v30|v31|v32]
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

def get_branch_raw_power(branch, month_branch):
    """地支原始力量（用于六冲力量对比）"""
    total = 0
    for j, (h, ratio) in enumerate(BRANCH_HIDDEN[branch]):
        if j == 0: base = 12 + (15 if branch == month_branch else 0)
        elif j == 1: base = 4
        else: base = 2
        total += base
    return total

def get_branch_modifier(branches, month_branch, method='v22'):
    """刑冲合害修正系数（不连乘，取最大修正）"""
    modifiers = {b: 1.0 for b in branches}
    effects = []
    blist = list(branches)
    raw_powers = {b: get_branch_raw_power(b, month_branch) for b in set(branches)}

    for i, b1 in enumerate(blist):
        for b2 in blist[i+1:]:
            if LIU_CHONG.get(b1) == b2:
                if method == 'v22':
                    p1, p2 = raw_powers[b1], raw_powers[b2]
                    if p1 > p2 * 1.3:
                        modifiers[b1] = min(modifiers[b1], 0.8)
                        modifiers[b2] = min(modifiers[b2], 0.5)
                        effects.append(f"{b1}强冲{b2}弱(×0.8/×0.5)")
                    elif p2 > p1 * 1.3:
                        modifiers[b1] = min(modifiers[b1], 0.5)
                        modifiers[b2] = min(modifiers[b2], 0.8)
                        effects.append(f"{b2}强冲{b1}弱(×0.8/×0.5)")
                    else:
                        modifiers[b1] = min(modifiers[b1], 0.7)
                        modifiers[b2] = min(modifiers[b2], 0.7)
                        effects.append(f"{b1}{b2}冲(均×0.7)")
                else:
                    modifiers[b1] = min(modifiers[b1], 0.7)
                    modifiers[b2] = min(modifiers[b2], 0.7)
                    effects.append(f"{b1}{b2}冲")
            elif b2 in SAN_XING.get(b1, set()):
                modifiers[b1] = min(modifiers[b1], 0.8)
                modifiers[b2] = min(modifiers[b2], 0.8)
                effects.append(f"{b1}{b2}刑")
            elif LIU_HE.get(b1) == b2:
                if method == 'v22':
                    effects.append(f"{b1}{b2}合(仅记录)")
                else:
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

def calc_wuxing_power(four_pillars, month_branch, method='v22'):
    branches = [p[1] for p in four_pillars]
    use_corr = method in ('v21', 'v22')
    modifiers, effects = (get_branch_modifier(branches, month_branch, method) if use_corr else ({b:1.0 for b in branches}, []))
    power = {'木':0,'火':0,'土':0,'金':0,'水':0}
    for stem, branch in four_pillars:
        power[STEM_ELEMENT[stem]] += 10
        mod = modifiers[branch]
        for j, (h, ratio) in enumerate(BRANCH_HIDDEN[branch]):
            if j == 0: base = 12 + (15 if branch == month_branch else 0)
            elif j == 1: base = 4
            else: base = 2
            power[STEM_ELEMENT[h]] += int(base * mod)
    return power, effects

def apply_shishen_combo(day_stem, month_branch, four_pillars, power):
    """v3.2十神组合效应：杀印相生/食神制杀（互斥）/比劫帮身/伤官佩印/财滋弱杀"""
    day_elem = STEM_ELEMENT[day_stem]
    print_elem = get_print_element(day_elem)
    stems = [p[0] for p in four_pillars]
    month_elem = BRANCH_ELEMENT[month_branch]
    effects = []
    shishen_power = {'比劫':0,'印星':0,'食伤':0,'官杀':0,'财星':0}
    for e in ['木','火','土','金','水']:
        if e == day_elem: ss = '比劫'
        elif GENERATES[e] == day_elem: ss = '印星'
        elif GENERATES[day_elem] == e: ss = '食伤'
        elif OVERCOMES[e] == day_elem: ss = '官杀'
        else: ss = '财星'
        shishen_power[ss] += power[e]
    guansha_elem = next(e for e in ['木','火','土','金','水'] if OVERCOMES[e] == day_elem)
    yin_elem = print_elem
    shishang_elem = next(e for e in ['木','火','土','金','水'] if GENERATES[day_elem] == e)
    cai_elem = next(e for e in ['木','火','土','金','水'] if OVERCOMES[day_elem] == e)
    bijie_elem = day_elem
    guansha_dangling = (month_elem == guansha_elem)
    yin_tougan = any(STEM_ELEMENT[s] == yin_elem for s in stems)
    yin_root = any(STEM_ELEMENT[h] == yin_elem and r >= 0.3 for _, b in four_pillars for h, r in BRANCH_HIDDEN[b])
    shishang_tougan = any(STEM_ELEMENT[s] == shishang_elem for s in stems)
    shishang_dangling = (month_elem == shishang_elem)
    bijie_tougan = any(STEM_ELEMENT[s] == bijie_elem for s in stems)
    bijie_root = any(STEM_ELEMENT[h] == bijie_elem and r >= 0.3 for _, b in four_pillars for h, r in BRANCH_HIDDEN[b])
    shayin_triggered = False
    # 1. 杀印相生（最高优先级）
    if (guansha_dangling or shishen_power['官杀'] > 20) and yin_tougan and yin_root:
        convert_ratio = min(shishen_power['印星'] / max(shishen_power['官杀'],1), 0.4)
        converted = int(shishen_power['官杀'] * convert_ratio)
        power[guansha_elem] -= converted; power[yin_elem] += converted
        effects.append(f"杀印相生：官杀-{converted}，印+{converted}")
        shishen_power['官杀'] -= converted; shishen_power['印星'] += converted
        shayin_triggered = True
    # 2. 食神制杀（杀印未触发时才考虑，互斥）
    if not shayin_triggered and (guansha_dangling or shishen_power['官杀'] > 20) and shishen_power['食伤'] > 10 and shishang_tougan:
        zhu_ratio = min(shishen_power['食伤'] / max(shishen_power['官杀'],1), 0.4)
        zhu_amount = int(shishen_power['官杀'] * zhu_ratio)
        power[guansha_elem] -= zhu_amount
        effects.append(f"食神制杀：官杀-{zhu_amount}")
        shishen_power['官杀'] -= zhu_amount
    # 3. 比劫帮身：比劫>15 + 官杀>15 + 比劫透干或有根，分担上限30%
    if shishen_power['比劫'] > 15 and shishen_power['官杀'] > 15 and (bijie_tougan or bijie_root):
        fendan_ratio = min(shishen_power['比劫'] / max(shishen_power['官杀'],1), 0.3)
        fendan_amount = int(shishen_power['官杀'] * fendan_ratio)
        power[guansha_elem] -= fendan_amount
        effects.append(f"比劫帮身：官杀-{fendan_amount}")
    # 4. 伤官佩印
    if (shishang_dangling or shishen_power['食伤'] > 30) and shishen_power['食伤'] > shishen_power['印星'] and yin_tougan and yin_root:
        zhu_ratio = min(shishen_power['印星'] / max(shishen_power['食伤'],1), 0.4)
        zhu_amount = int(shishen_power['食伤'] * zhu_ratio)
        power[shishang_elem] -= zhu_amount
        effects.append(f"伤官佩印：食伤-{zhu_amount}")
    # 5. 财滋弱杀
    cai_dangling = (month_elem == cai_elem)
    guansha_root = any(STEM_ELEMENT[h] == guansha_elem and r >= 0.3 for _, b in four_pillars for h, r in BRANCH_HIDDEN[b])
    if (cai_dangling or shishen_power['财星'] > 20) and 0 < shishen_power['官杀'] < 15 and guansha_root:
        sheng_ratio = min(shishen_power['财星'] / max(shishen_power['官杀'],1), 0.4)
        sheng_amount = int(shishen_power['官杀'] * sheng_ratio)
        power[guansha_elem] += sheng_amount
        effects.append(f"财滋弱杀：官杀+{sheng_amount}")
    return power, effects

def calc_T(day_stem, month_branch, four_pillars, method='v32'):
    day_elem = STEM_ELEMENT[day_stem]
    print_elem = get_print_element(day_elem)
    if method == 'v1':
        return calc_T_v1(day_stem, month_branch, four_pillars)
    # v30/v31/v32用v22的修正，再加十神组合
    calc_method = 'v22' if method in ('v30','v31','v32') else method
    power, effects = calc_wuxing_power(four_pillars, month_branch, calc_method)
    if method in ('v30','v31','v32'):
        power, combo_effects = apply_shishen_combo(day_stem, month_branch, four_pillars, power)
        effects = effects + combo_effects
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
    parser = argparse.ArgumentParser(description='T值硬判断计算器 v2.2')
    parser.add_argument('pillars', nargs=4, help='年柱 月柱 日柱 时柱')
    parser.add_argument('--method', choices=['v1','v2','v21','v22','v30','v31','v32'], default='v32', help='计算方法（默认v32）')
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
        support_pct = round(support/total*100,1)
        print(f"  帮身（{day_elem}+{print_elem}）：{support}（{support_pct}%）")
        print(f"  克泄耗：{total-support}（{round((total-support)/total*100,1)}%）")
        if effects:
            print(f"  冲刑合害：{', '.join(effects)}")
        # 从格判断
        day_root = any(STEM_ELEMENT[h] == day_elem and r >= 0.3 for _, b in pillars for h, r in BRANCH_HIDDEN[b])
        print_root = any(STEM_ELEMENT[h] == print_elem and r >= 0.3 for _, b in pillars for h, r in BRANCH_HIDDEN[b])
        is_cong = (support_pct < 25) and (not day_root) and (not print_root)
        if is_cong:
            consume = {}
            for e in ['木','火','土','金','水']:
                if e == day_elem or e == print_elem: continue
                if OVERCOMES[day_elem] == e: t = '财星'
                elif OVERCOMES[e] == day_elem: t = '官杀'
                else: t = '食伤'
                consume[t] = consume.get(t, 0) + power[e]
            cong_type = max(consume, key=consume.get) if consume else '从势'
            print("-" * 60)
            print(f"  ⚠ 从格判断：帮身{support_pct}%<25% + 日主无根 + 印星无根")
            print(f"  从格类型：从{cong_type}格（忌帮身，顺势而为）")
        print("-" * 60)
        print(f"  T值 = {T}")
        print(f"  总评 = {rating}" + ("（非从格，按T值判断）" if not is_cong else ""))
    print("=" * 60)

if __name__ == '__main__':
    main()

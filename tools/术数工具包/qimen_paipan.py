#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奇门遁甲排盘工具
阴遁/阳遁，拆补法定局
输出：地盘、天盘、九星、八门、八神、空亡、马星
"""

from datetime import datetime
import math

# ==================== 基础数据 ====================

# 九宫对应
PALACES = {
    1: {"name": "坎", "element": "水", "star": "天蓬", "door": "休门"},
    2: {"name": "坤", "element": "土", "star": "天芮", "door": "死门"},
    3: {"name": "震", "element": "木", "star": "天冲", "door": "伤门"},
    4: {"name": "巽", "element": "木", "star": "天辅", "door": "杜门"},
    5: {"name": "中", "element": "土", "star": "天禽", "door": "寄坤"},
    6: {"name": "乾", "element": "金", "star": "天心", "door": "开门"},
    7: {"name": "兑", "element": "金", "star": "天柱", "door": "惊门"},
    8: {"name": "艮", "element": "土", "star": "天任", "door": "生门"},
    9: {"name": "离", "element": "火", "star": "天英", "door": "景门"},
}

# 三奇六仪顺序（阳遁顺排用）
YI_QI = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]

# 九星顺序（顺排）
STARS = ["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"]
# 九星对应宫
STAR_PALACE = {"天蓬":1, "天芮":2, "天冲":3, "天辅":4, "天禽":5, "天心":6, "天柱":7, "天任":8, "天英":9}

# 八门运行顺序（阳遁顺行用）
DOORS = ["休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"]
# 八门对应宫
DOOR_PALACE = {"休门":1, "死门":2, "伤门":3, "杜门":4, "开门":6, "惊门":7, "生门":8, "景门":9}
# 宫位对应门
PALACE_DOOR = {1:"休门", 2:"死门", 3:"伤门", 4:"杜门", 5:"寄坤", 6:"开门", 7:"惊门", 8:"生门", 9:"景门"}

# 八神
SPIRITS = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]

# 天干
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
# 地支
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 五行
ELEMENTS = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"
}

# 二十四节气（月, 日, 名称, 阴阳遁, 上元局, 中元局, 下元局）
SOLAR_TERMS = [
    (1, 6, "小寒", "阳", 2, 8, 5),
    (1, 20, "大寒", "阳", 3, 9, 6),
    (2, 4, "立春", "阳", 8, 5, 2),
    (2, 19, "雨水", "阳", 9, 6, 3),
    (3, 6, "惊蛰", "阳", 1, 7, 4),
    (3, 21, "春分", "阳", 3, 9, 6),
    (4, 5, "清明", "阳", 8, 5, 2),
    (4, 20, "谷雨", "阳", 9, 6, 3),
    (5, 6, "立夏", "阳", 4, 1, 7),
    (5, 21, "小满", "阳", 5, 2, 8),
    (6, 6, "芒种", "阳", 4, 1, 7),
    (6, 21, "夏至", "阴", 9, 3, 6),
    (7, 7, "小暑", "阴", 8, 2, 5),
    (7, 23, "大暑", "阴", 7, 1, 4),
    (8, 8, "立秋", "阴", 2, 5, 8),
    (8, 23, "处暑", "阴", 1, 4, 7),
    (9, 8, "白露", "阴", 9, 3, 6),
    (9, 23, "秋分", "阴", 7, 1, 4),
    (10, 8, "寒露", "阴", 2, 5, 8),
    (10, 23, "霜降", "阴", 1, 4, 7),
    (11, 7, "立冬", "阴", 6, 9, 3),
    (11, 22, "小雪", "阴", 5, 8, 2),
    (12, 7, "大雪", "阴", 6, 9, 3),
    (12, 22, "冬至", "阳", 1, 7, 4),
]

# 十二地支对应宫（时支定宫用）
BRANCH_PALACE = {
    "子": 1, "丑": 8, "寅": 8, "卯": 3, "辰": 4, "巳": 4,
    "午": 9, "未": 2, "申": 2, "酉": 7, "戌": 6, "亥": 6
}

# 马星
HORSE_STAR = {
    "申": "寅", "子": "寅", "辰": "寅",
    "亥": "巳", "卯": "巳", "未": "巳",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥"
}

# ==================== 工具函数 ====================

def get_ganzhi_index(ganzhi):
    """获取干支在六十甲子中的索引 (0-59)"""
    gan = ganzhi[0]
    zhi = ganzhi[1]
    gi = HEAVENLY_STEMS.index(gan)
    zi = EARTHLY_BRANCHES.index(zhi)
    # 六十甲子：天干地支组合，索引满足 gi % 2 == zi % 2
    # 找到第一个匹配的
    for i in range(60):
        if i % 10 == gi and i % 12 == zi:
            return i
    return -1

def get_day_ganzhi(year, month, day):
    """计算日干支（基于已知基准日）"""
    # 基准：2000年1月1日是甲子日？不对，让我用公式
    # 用蔡勒公式的变体计算儒略日
    if month <= 2:
        year -= 1
        month += 12
    A = year // 100
    B = 2 - A + A // 4
    JD = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
    JD = int(JD + 0.5)
    # 1900年1月1日是甲戌日（索引10）
    # 儒略日 2415021 = 1900-01-01
    base_jd = 2415021
    base_idx = 10  # 甲戌
    diff = JD - base_jd
    idx = (base_idx + diff) % 60
    return HEAVENLY_STEMS[idx % 10] + EARTHLY_BRANCHES[idx % 12]

def get_hour_ganzhi(day_ganzhi, hour_branch):
    """根据日干支和时支计算时干支"""
    day_gan = day_ganzhi[0]
    # 五鼠遁：甲己还加甲，乙庚丙作初，丙辛从戊起，丁壬庚子居，戊癸何方发，壬子是真途
    start_map = {
        "甲": 0, "己": 0,  # 甲子
        "乙": 2, "庚": 2,  # 丙子
        "丙": 4, "辛": 4,  # 戊子
        "丁": 6, "壬": 6,  # 庚子
        "戊": 8, "癸": 8,  # 壬子
    }
    start = start_map[day_gan]
    zhi_idx = EARTHLY_BRANCHES.index(hour_branch)
    gan_idx = (start + zhi_idx) % 10
    return HEAVENLY_STEMS[gan_idx] + hour_branch

def get_solar_term(month, day):
    """获取当前节气"""
    for i, (m, d, name, yin_yang, shang, zhong, xia) in enumerate(SOLAR_TERMS):
        if (month == m and day >= d) or (month > m):
            # 检查是否已经过了下一个节气
            if i < len(SOLAR_TERMS) - 1:
                next_m, next_d = SOLAR_TERMS[i+1][0], SOLAR_TERMS[i+1][1]
                if month > next_m or (month == next_m and day >= next_d):
                    continue
            return SOLAR_TERMS[i]
    return SOLAR_TERMS[-1]

def get_jushu(day_ganzhi, solar_term, year, month, day):
    """确定局数（拆补法：节气后第一个甲己日为上元开始）"""
    name, yin_yang, shang, zhong, xia = solar_term[2], solar_term[3], solar_term[4], solar_term[5], solar_term[6]
    
    # 找到节气日期
    term_month, term_day = solar_term[0], solar_term[1]
    
    # 从节气日开始，找到第一个甲己日
    day_idx = get_ganzhi_index(day_ganzhi)
    
    # 计算节气日的日干支
    term_ganzhi = get_day_ganzhi(year, term_month, term_day)
    term_idx = get_ganzhi_index(term_ganzhi)
    
    # 从节气日开始，找到第一个甲己日（天干甲或己）
    first_jiari_idx = None
    for i in range(15):  # 节气后15天内一定有甲己日
        check_idx = (term_idx + i) % 60
        check_gan = HEAVENLY_STEMS[check_idx % 10]
        if check_gan in ["甲", "己"]:
            first_jiari_idx = check_idx
            days_after_jiari = i
            break
    
    # 计算当前日距离第一个甲己日的天数
    days_from_jiari = (day_idx - first_jiari_idx) % 60
    
    # 每5天为一元
    yuan_num = days_from_jiari // 5
    if yuan_num == 0:
        return shang, yin_yang, "上元"
    elif yuan_num == 1:
        return zhong, yin_yang, "中元"
    else:
        return xia, yin_yang, "下元"

def get_kongwang(day_ganzhi):
    """空亡"""
    idx = get_ganzhi_index(day_ganzhi)
    # 旬首：idx - idx % 10
    xunshou_idx = idx - idx % 10
    xunshou_zhi = EARTHLY_BRANCHES[xunshou_idx % 12]
    # 空亡是旬首地支的前两个
    zhi_idx = EARTHLY_BRANCHES.index(xunshou_zhi)
    kw1 = EARTHLY_BRANCHES[(zhi_idx - 2) % 12]
    kw2 = EARTHLY_BRANCHES[(zhi_idx - 1) % 12]
    return kw1, kw2

# ==================== 排盘核心 ====================

def arrange_dipan(jushu, yin_yang):
    """排地盘三奇六仪"""
    dipan = {}
    if yin_yang == "阳":
        # 阳遁顺排：戊从局数宫开始，顺排
        start = jushu
        for i, yi in enumerate(YI_QI):
            palace = ((start - 1 + i) % 9) + 1
            dipan[palace] = yi
    else:
        # 阴遁逆排：戊从局数宫开始，逆排
        start = jushu
        for i, yi in enumerate(YI_QI):
            palace = ((start - 1 - i) % 9) + 1
            if palace < 1:
                palace += 9
            dipan[palace] = yi
    return dipan

def get_xunshou(hour_ganzhi):
    """确定时干支的旬首，返回旬首六仪（戊己庚辛壬癸）"""
    # 六十甲子索引
    gan = hour_ganzhi[0]
    zhi = hour_ganzhi[1]
    gi = HEAVENLY_STEMS.index(gan)
    zi = EARTHLY_BRANCHES.index(zhi)
    # 找到六十甲子索引
    idx = -1
    for i in range(60):
        if i % 10 == gi and i % 12 == zi:
            idx = i
            break
    # 旬首：每10个一旬
    xun_idx = (idx // 10) * 10
    xun_gan = HEAVENLY_STEMS[xun_idx % 10]
    xun_zhi = EARTHLY_BRANCHES[xun_idx % 12]
    # 旬首隐六仪：甲子→戊、甲戌→己、甲申→庚、甲午→辛、甲辰→壬、甲寅→癸
    xunshou_yi_map = {"甲": "戊", "乙": "己", "丙": "庚", "丁": "辛", "戊": "壬", "己": "癸"}
    # 旬首天干都是甲（甲子、甲戌、甲申、甲午、甲辰、甲寅）
    xunshou_yi = {"子": "戊", "戌": "己", "申": "庚", "午": "辛", "辰": "壬", "寅": "癸"}[xun_zhi]
    return xunshou_yi, xun_gan + xun_zhi


def arrange_tianpan_stars(dipan, shigan, hour_ganzhi, yin_yang):
    """排天盘九星和天盘三奇六仪"""
    # 1. 时干所在宫
    shigan_palace = None
    for p, yi in dipan.items():
        if yi == shigan:
            shigan_palace = p
            break

    # 2. 确定旬首六仪，找到值符宫（旬首六仪所在宫）
    xunshou_yi, xunshou_ganzhi = get_xunshou(hour_ganzhi)
    zhifu_palace = None
    for p, yi in dipan.items():
        if yi == xunshou_yi:
            zhifu_palace = p
            break

    # 3. 值符星 = 值符宫的地盘九星
    zhifu_star = PALACES[zhifu_palace]["star"]

    # 4. 天盘九星：值符星移到时干宫，其他星按阳顺阴逆排列
    tianpan_stars = {}
    star_idx = STARS.index(zhifu_star)
    palace_order = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    start_pos = palace_order.index(shigan_palace)
    for i in range(9):
        if yin_yang == "阳":
            palace = palace_order[(start_pos + i) % 9]
        else:
            palace = palace_order[(start_pos - i) % 9]
        star = STARS[(star_idx + i) % 9]
        tianpan_stars[palace] = star

    # 5. 天盘三奇六仪：跟着九星走，每个星带着它原来宫位的地盘三奇六仪
    tianpan_yi = {}
    for palace, star in tianpan_stars.items():
        original_palace = STAR_PALACE[star]
        tianpan_yi[palace] = dipan[original_palace]

    return tianpan_stars, tianpan_yi, zhifu_star, shigan_palace, zhifu_palace

def arrange_tianpan_doors(shizhi):
    """排天盘八门"""
    # 值使 = 时干宫的地盘八门（这个需要时干宫，在外面传进来）
    # 这里先不排，在主函数里排
    pass

def arrange_spirits(zhifu_palace, yin_yang):
    """排八神"""
    spirits = {}
    # 八神排8宫（不含中5）
    palace_order = [1, 2, 3, 4, 6, 7, 8, 9]
    if yin_yang == "阳":
        # 阳遁顺排
        start_pos = palace_order.index(zhifu_palace if zhifu_palace != 5 else 2)
        for i in range(8):
            palace = palace_order[(start_pos + i) % 8]
            spirits[palace] = SPIRITS[i]
    else:
        # 阴遁逆排
        start_pos = palace_order.index(zhifu_palace if zhifu_palace != 5 else 2)
        for i in range(8):
            palace = palace_order[(start_pos - i) % 8]
            spirits[palace] = SPIRITS[i]
    return spirits

# ==================== 主排盘函数 ====================

def qimen_pan(year, month, day, hour_branch):
    """排奇门遁甲盘"""
    # 1. 日干支
    day_ganzhi = get_day_ganzhi(year, month, day)
    
    # 2. 时干支
    hour_ganzhi = get_hour_ganzhi(day_ganzhi, hour_branch)
    shigan = hour_ganzhi[0]
    shizhi = hour_ganzhi[1]
    
    # 3. 节气和局数
    solar_term = get_solar_term(month, day)
    jushu, yin_yang, yuan = get_jushu(day_ganzhi, solar_term, year, month, day)
    
    # 4. 空亡
    kw1, kw2 = get_kongwang(day_ganzhi)
    
    # 5. 马星
    horse = HORSE_STAR[shizhi]
    
    # 6. 地盘
    dipan = arrange_dipan(jushu, yin_yang)
    
    # 7. 天盘九星和三奇六仪
    tianpan_stars, tianpan_yi, zhifu_star, shigan_palace, zhifu_palace = arrange_tianpan_stars(dipan, shigan, hour_ganzhi, yin_yang)
    
    # 8. 值使门 = 值符宫的地盘门（不是时干宫）
    zhishi_door = PALACES[zhifu_palace]["door"]
    if zhishi_door == "寄坤":
        zhishi_door = "死门"  # 中5寄坤2，死门
    
    # 9. 天盘八门：值使门从本宫（值符宫）数到时支（阳顺阴逆），其他门按序排列
    zhishi_palace = zhifu_palace
    # 九宫顺序（含中5）
    palace_order_9 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    # 八宫顺序（不含中5，中5寄坤2）
    palace_order_8 = [1, 2, 3, 4, 6, 7, 8, 9]
    # 从子时开始数，数到时支
    hour_branches_list = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    hour_idx = hour_branches_list.index(shizhi)
    # 从值使门本宫开始，阳顺阴逆数hour_idx步
    start_idx_9 = palace_order_9.index(zhishi_palace)
    if yin_yang == "阳":
        zhishi_idx_9 = (start_idx_9 + hour_idx) % 9
    else:
        zhishi_idx_9 = (start_idx_9 - hour_idx) % 9
    zhishi_actual_palace = palace_order_9[zhishi_idx_9]
    if zhishi_actual_palace == 5:
        zhishi_actual_palace = 2  # 中5寄坤2
    # 值使门落在实际宫位，其他门按阳顺阴逆排列
    door_idx = DOORS.index(zhishi_door)
    start_pos_8 = palace_order_8.index(zhishi_actual_palace)
    tianpan_doors = {}
    for i in range(8):
        if yin_yang == "阳":
            palace = palace_order_8[(start_pos_8 + i) % 8]
        else:
            palace = palace_order_8[(start_pos_8 - i) % 8]
        door = DOORS[(door_idx + i) % 8]
        tianpan_doors[palace] = door
    # 中5寄坤2
    tianpan_doors[5] = tianpan_doors[2]
    
    # 10. 八神（从值符宫开始排，阳顺阴逆）
    spirits = arrange_spirits(zhifu_palace, yin_yang)
    
    # 11. 判断是否伏吟/反吟
    fuyin = True
    for p in range(1, 10):
        if tianpan_stars[p] != PALACES[p]["star"]:
            fuyin = False
            break
    
    return {
        "day_ganzhi": day_ganzhi,
        "hour_ganzhi": hour_ganzhi,
        "solar_term": solar_term[2],
        "jushu": jushu,
        "yin_yang": yin_yang,
        "yuan": yuan,
        "kongwang": (kw1, kw2),
        "horse": horse,
        "zhifu_star": zhifu_star,
        "zhishi_door": zhishi_door,
        "shigan_palace": shigan_palace,
        "zhifu_palace": zhifu_palace,
        "shizhi_palace": zhishi_palace,
        "fuyin": fuyin,
        "dipan": dipan,
        "tianpan_stars": tianpan_stars,
        "tianpan_yi": tianpan_yi,
        "tianpan_doors": tianpan_doors,
        "spirits": spirits,
    }

def print_pan(pan):
    """打印排盘结果"""
    print("=" * 60)
    print(f"奇门遁甲排盘")
    print(f"日干支：{pan['day_ganzhi']}  时干支：{pan['hour_ganzhi']}")
    print(f"节气：{pan['solar_term']}  {pan['yin_yang']}遁{pan['jushu']}局  {pan['yuan']}")
    print(f"空亡：{pan['kongwang'][0]}{pan['kongwang'][1]}  马星：{pan['horse']}")
    print(f"值符：{pan['zhifu_star']}  值使：{pan['zhishi_door']}")
    print(f"{'伏吟局' if pan['fuyin'] else ''}")
    print("=" * 60)
    
    # 按九宫格打印
    print(f"\n{'宫':<4} {'地盘仪':<6} {'天盘仪':<6} {'地盘星':<6} {'天盘星':<6} {'地盘门':<6} {'天盘门':<6} {'八神':<6}")
    print("-" * 60)
    # 空亡地支对应宫
    kw_palaces = set()
    for zhi in pan['kongwang']:
        if zhi in ["子"]: kw_palaces.add(1)
        elif zhi in ["丑", "寅"]: kw_palaces.add(8)
        elif zhi in ["卯"]: kw_palaces.add(3)
        elif zhi in ["辰", "巳"]: kw_palaces.add(4)
        elif zhi in ["午"]: kw_palaces.add(9)
        elif zhi in ["未", "申"]: kw_palaces.add(2)
        elif zhi in ["酉"]: kw_palaces.add(7)
        elif zhi in ["戌", "亥"]: kw_palaces.add(6)
    
    for p in [4, 9, 2, 3, 5, 7, 8, 1, 6]:
        dp = pan['dipan'].get(p, "-")
        tp = pan['tianpan_yi'].get(p, "-")
        ds = PALACES[p]["star"]
        ts = pan['tianpan_stars'].get(p, "-")
        dd = PALACES[p]["door"]
        td = pan['tianpan_doors'].get(p, "-")
        sp = pan['spirits'].get(p, "-")
        kw_mark = " ★" if p in kw_palaces else ""
        print(f"{PALACES[p]['name']}{p:<3} {dp:<6} {tp:<6} {ds:<6} {ts:<6} {dd:<6} {td:<6} {sp:<6}{kw_mark}")
    
    print("\n注：★为空亡宫")

# ==================== 测试 ====================

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 5:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
        day = int(sys.argv[3])
        hour = int(sys.argv[4])
        # 时辰转换（23-1点子时，1-3点丑时...）
        if hour == 23 or hour == 0:
            hour_branch = "子"
        else:
            hour_branches = ["丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
            hour_branch = hour_branches[(hour - 1) // 2]
        pan = qimen_pan(year, month, day, hour_branch)
        print_pan(pan)
    else:
        print("用法：python qimen_paipan.py 年 月 日 时(24小时制)")
        print("示例：python qimen_paipan.py 2026 9 5 10")
        print()
        # 默认测试
        pan = qimen_pan(2026, 8, 29, "亥")
        print_pan(pan)

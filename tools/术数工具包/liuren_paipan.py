#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大六壬排盘工具
术数之王，三式之首
功能：月将加时、四课三传、九宗门、天将排布、空亡马星、课体判断
生命论视角：大六壬是特定时空点的能量态势分析，不是宿命预言
"""

from datetime import datetime
import json
import sys

# ==================== 基础数据 ====================

# 十二地支
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 天干
STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 月将（太阳过宫，以节气为界）
# 月将名：登明(亥)、河魁(戌)、从魁(酉)、传送(申)、小吉(未)、胜光(午)、太乙(巳)、天罡(辰)、太冲(卯)、功曹(寅)、大吉(丑)、神后(子)
MONTH_GENERALS = {
    "亥": "登明", "戌": "河魁", "酉": "从魁", "申": "传送",
    "未": "小吉", "午": "胜光", "巳": "太乙", "辰": "天罡",
    "卯": "太冲", "寅": "功曹", "丑": "大吉", "子": "神后"
}

# 月将与节气对应（太阳过宫）
# 注意：月将以中气为界（不是节气）
SOLAR_TERMS_TO_MONTH_GENERAL = [
    ("雨水", "亥"),   # 雨水后太阳过亥宫
    ("春分", "戌"),   # 春分后太阳过戌宫
    ("谷雨", "酉"),   # 谷雨后太阳过酉宫
    ("小满", "申"),   # 小满后太阳过申宫
    ("夏至", "未"),   # 夏至后太阳过未宫
    ("大暑", "午"),   # 大暑后太阳过午宫
    ("处暑", "巳"),   # 处暑后太阳过巳宫
    ("秋分", "辰"),   # 秋分后太阳过辰宫
    ("霜降", "卯"),   # 霜降后太阳过卯宫
    ("小雪", "寅"),   # 小雪后太阳过寅宫
    ("冬至", "丑"),   # 冬至后太阳过丑宫
    ("大寒", "子"),   # 大寒后太阳过子宫
]

# 二十四节气日期（近似，每年有1-2天波动）
SOLAR_TERMS_DATES = {
    "小寒": (1, 6), "大寒": (1, 20),
    "立春": (2, 4), "雨水": (2, 19),
    "惊蛰": (3, 6), "春分": (3, 21),
    "清明": (4, 5), "谷雨": (4, 20),
    "立夏": (5, 6), "小满": (5, 21),
    "芒种": (6, 6), "夏至": (6, 21),
    "小暑": (7, 7), "大暑": (7, 23),
    "立秋": (8, 8), "处暑": (8, 23),
    "白露": (9, 8), "秋分": (9, 23),
    "寒露": (10, 8), "霜降": (10, 23),
    "立冬": (11, 7), "小雪": (11, 22),
    "大雪": (12, 7), "冬至": (12, 22),
}

# 日干寄宫（天干在地支中的寄位）
STEM_TO_BRANCH = {
    "甲": "寅", "乙": "辰", "丙": "巳", "丁": "未",
    "戊": "巳", "己": "未", "庚": "申", "辛": "戌",
    "壬": "亥", "癸": "丑"
}

# 十二天将
TWELVE_GENERALS = [
    "贵人", "螣蛇", "朱雀", "六合", "勾陈", "青龙",
    "天空", "白虎", "太常", "玄武", "太阴", "天后"
]

# 贵人起法（日干→贵人地支）
# 甲戊庚牛羊（丑未），乙己鼠猴乡（子申），丙丁猪鸡位（亥酉），壬癸蛇兔藏（巳卯），六辛逢马虎（午寅）
NOBLEMAN_DAY = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("巳", "卯"), "癸": ("巳", "卯"),
    "辛": ("午", "寅")
}

# 地支五行
BRANCH_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水"
}

# 天干五行
STEM_ELEMENT = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火",
    "戊": "土", "己": "土", "庚": "金", "辛": "金",
    "壬": "水", "癸": "水"
}

# 地支相冲
BRANCH_CLASH = {
    "子": "午", "丑": "未", "寅": "申", "卯": "酉",
    "辰": "戌", "巳": "亥", "午": "子", "未": "丑",
    "申": "寅", "酉": "卯", "戌": "辰", "亥": "巳"
}

# 地支六合
BRANCH_COMBINE = {
    "子": "丑", "丑": "子", "寅": "亥", "亥": "寅",
    "卯": "戌", "戌": "卯", "辰": "酉", "酉": "辰",
    "巳": "申", "申": "巳", "午": "未", "未": "午"
}

# 驿马（日支→马星）
# 申子辰马在寅，亥卯未马在巳，寅午戌马在申，巳酉丑马在亥
HORSE_STAR = {
    "申": "寅", "子": "寅", "辰": "寅",
    "亥": "巳", "卯": "巳", "未": "巳",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥"
}

# 日旬空亡
def get_kongwang(day_ganzhi):
    """计算日柱旬空"""
    stem_idx = STEMS.index(day_ganzhi[0])
    branch_idx = BRANCHES.index(day_ganzhi[1])
    # 旬首地支 = branch_idx - stem_idx (mod 12)
    xunshou_branch_idx = (branch_idx - stem_idx) % 12
    # 空亡 = 旬首地支 + 10, +11 (mod 12)
    kw1_idx = (xunshou_branch_idx + 10) % 12
    kw2_idx = (xunshou_branch_idx + 11) % 12
    return BRANCHES[kw1_idx] + BRANCHES[kw2_idx]


# ==================== 核心排盘函数 ====================

def get_month_general(month, day):
    """根据日期确定月将（太阳过宫，以中气为界）
    月将顺序：大寒后子、雨水后亥、春分后戌、谷雨后酉、小满后申、
    夏至后未、大暑后午、处暑后巳、秋分后辰、霜降后卯、小雪后寅、冬至后丑
    """
    # 按时间顺序排列中气（从1月大寒开始）
    terms_in_order = [
        ("大寒", "子", 1, 20),
        ("雨水", "亥", 2, 19),
        ("春分", "戌", 3, 21),
        ("谷雨", "酉", 4, 20),
        ("小满", "申", 5, 21),
        ("夏至", "未", 6, 21),
        ("大暑", "午", 7, 23),
        ("处暑", "巳", 8, 23),
        ("秋分", "辰", 9, 23),
        ("霜降", "卯", 10, 23),
        ("小雪", "寅", 11, 22),
        ("冬至", "丑", 12, 22),
    ]
    # 找到最后一个满足条件的中气（日期>=该中气日期）
    result = "子"  # 默认：大寒前属于上一年的子月将
    for term_name, mg, t_month, t_day in terms_in_order:
        if (month > t_month) or (month == t_month and day >= t_day):
            result = mg
        else:
            break
    return result


def get_hour_branch(hour):
    """根据小时确定时支"""
    if hour == 23:
        return "子"
    return BRANCHES[(hour + 1) // 2 % 12]


def get_day_pillar(year, month, day):
    """计算日柱（以1900年1月1日甲戌日为基准）"""
    base = datetime(1900, 1, 1)
    target = datetime(year, month, day)
    delta = (target - base).days
    idx = (10 + delta) % 60  # 甲戌idx=10
    stem_idx = idx % 10
    branch_idx = idx % 12
    return STEMS[stem_idx] + BRANCHES[branch_idx]


def setup_heaven_plate(month_general, hour_branch):
    """月将加时，排布天盘
    返回：dict {地盘支: 天盘支}
    """
    mg_idx = BRANCHES.index(month_general)
    hour_idx = BRANCHES.index(hour_branch)
    # 月将加在占时上：天盘的hour_idx位置是month_general
    # 天盘顺排
    heaven_plate = {}
    for i in range(12):
        earth_branch = BRANCHES[(hour_idx + i) % 12]
        heaven_branch = BRANCHES[(mg_idx + i) % 12]
        heaven_plate[earth_branch] = heaven_branch
    return heaven_plate


def get_four_lessons(day_stem, day_branch, heaven_plate):
    """起四课
    返回：list of (地盘, 天盘)，共4课
    第一课：干上（日干寄宫的天盘）
    第二课：干阴（第一课天盘的地盘位置上的天盘）
    第三课：支上（日支的天盘）
    第四课：支阴（第三课天盘的地盘位置上的天盘）
    """
    # 日干寄宫
    stem_branch = STEM_TO_BRANCH[day_stem]

    # 第一课：干上
    lesson1_earth = stem_branch
    lesson1_heaven = heaven_plate[stem_branch]

    # 第二课：干阴
    lesson2_earth = lesson1_heaven
    lesson2_heaven = heaven_plate[lesson1_heaven]

    # 第三课：支上
    lesson3_earth = day_branch
    lesson3_heaven = heaven_plate[day_branch]

    # 第四课：支阴
    lesson4_earth = lesson3_heaven
    lesson4_heaven = heaven_plate[lesson3_heaven]

    return [
        ("干上", lesson1_earth, lesson1_heaven),
        ("干阴", lesson2_earth, lesson2_heaven),
        ("支上", lesson3_earth, lesson3_heaven),
        ("支阴", lesson4_earth, lesson4_heaven)
    ]


def is_ke(upper, lower):
    """判断下克上（lower克upper）
    五行相克：木克土，土克水，水克火，火克金，金克木
    """
    overcomes = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    return overcomes.get(BRANCH_ELEMENT[lower]) == BRANCH_ELEMENT[upper]


def is_ke_upper(upper, lower):
    """判断上克下（upper克lower）"""
    overcomes = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    return overcomes.get(BRANCH_ELEMENT[upper]) == BRANCH_ELEMENT[lower]


def get_three_transmissions(four_lessons, day_stem, day_branch, heaven_plate, month_general, hour_branch):
    """起三传（九宗门）
    返回：(初传, 中传, 末传, 起法名称)
    """
    # 检查是否伏吟（天盘=地盘，即月将=占时）
    if month_general == hour_branch:
        # 伏吟法：初传取日干寄宫上神（即寄宫本身），中传取初传的天盘（即本身），末传取中传的天盘
        # 伏吟课：有克取克，无克取马星
        # 简化：初传取日干寄宫
        stem_branch = STEM_TO_BRANCH[day_stem]
        first = stem_branch
        second = heaven_plate[first]
        third = heaven_plate[second]
        return (first, second, third, "伏吟法")

    # 检查是否反吟（月将与占时相冲，天盘与地盘相冲）
    if BRANCH_CLASH.get(month_general) == hour_branch:
        # 反吟法：有克取克，无克取马星
        # 先检查四课有无克
        ke_list = []
        for name, earth, heaven in four_lessons:
            if is_ke(heaven, earth):  # 下克上
                ke_list.append((name, earth, heaven, "下克上"))
        if ke_list:
            # 取第一个下克上的天盘为初传
            first = ke_list[0][2]
            second = heaven_plate[first]
            third = heaven_plate[second]
            return (first, second, third, "反吟法(有克)")
        else:
            # 无克取马星
            horse = HORSE_STAR.get(day_branch, "寅")
            first = horse
            second = heaven_plate[first]
            third = heaven_plate[second]
            return (first, second, third, "反吟法(无克取马)")

    # 检查四课是否全（八专/别责）
    unique_lessons = set()
    for name, earth, heaven in four_lessons:
        unique_lessons.add((earth, heaven))
    if len(unique_lessons) < 4:
        # 四课不全，可能是八专或别责
        # 八专：日支与日干寄宫相同（如甲寅、庚申、丁未、己丑）
        stem_branch = STEM_TO_BRANCH[day_stem]
        if stem_branch == day_branch:
            # 八专法：无克，取日干寄宫上神为初传，顺数三位为中传，再顺数三位为末传
            first = heaven_plate[stem_branch]
            first_idx = BRANCHES.index(first)
            second = BRANCHES[(first_idx + 3) % 12]
            third = BRANCHES[(first_idx + 6) % 12]
            return (first, second, third, "八专法")
        else:
            # 别责法：四课不全，取日干合神为初传
            # 天干五合：甲己合、乙庚合、丙辛合、丁壬合、戊癸合
            stem_combine = {"甲": "己", "己": "甲", "乙": "庚", "庚": "乙",
                           "丙": "辛", "辛": "丙", "丁": "壬", "壬": "丁", "戊": "癸", "癸": "戊"}
            combined_stem = stem_combine.get(day_stem, day_stem)
            first = STEM_TO_BRANCH.get(combined_stem, "寅")
            second = heaven_plate[first]
            third = heaven_plate[second]
            return (first, second, third, "别责法")

    # 正常九宗门
    # 1. 贼克法：四课中有下克上
    xia_ke_shang = []
    shang_ke_xia = []
    for name, earth, heaven in four_lessons:
        if is_ke(heaven, earth):  # 下克上（地盘克天盘）
            xia_ke_shang.append((name, earth, heaven))
        if is_ke_upper(heaven, earth):  # 上克下（天盘克地盘）
            shang_ke_xia.append((name, earth, heaven))

    if len(xia_ke_shang) == 1:
        # 贼克法：只有一个下克上，取其天盘为初传
        first = xia_ke_shang[0][2]
        second = heaven_plate[first]
        third = heaven_plate[second]
        return (first, second, third, "贼克法")

    elif len(xia_ke_shang) > 1:
        # 比用法：多个下克上，取与日干比和者为初传
        day_element = STEM_ELEMENT[day_stem]
        bihe_list = []
        for name, earth, heaven in xia_ke_shang:
            if BRANCH_ELEMENT[heaven] == day_element:
                bihe_list.append((name, earth, heaven))
        if len(bihe_list) == 1:
            first = bihe_list[0][2]
            second = heaven_plate[first]
            third = heaven_plate[second]
            return (first, second, third, "比用法")
        elif len(bihe_list) > 1:
            # 涉害法：多个比和，取涉害深者为初传
            # 涉害：从日干寄宫数到该天盘地盘位置，经过的克数
            # 简化：取第一个
            first = bihe_list[0][2]
            second = heaven_plate[first]
            third = heaven_plate[second]
            return (first, second, third, "涉害法(简化)")
        else:
            # 涉害法：无比和，取涉害深者
            # 简化：取第一个下克上
            first = xia_ke_shang[0][2]
            second = heaven_plate[first]
            third = heaven_plate[second]
            return (first, second, third, "涉害法")

    elif len(xia_ke_shang) == 0 and len(shang_ke_xia) > 0:
        # 遥克法：无下克上，有上克下
        # 蒿矢法：神克日（天盘克日干）
        # 弹射法：日克神（日干克天盘）
        # 简化：取第一个上克下的天盘为初传
        first = shang_ke_xia[0][2]
        second = heaven_plate[first]
        third = heaven_plate[second]
        return (first, second, third, "遥克法(蒿矢/弹射)")

    else:
        # 昴星法：四课无克
        # 阳日取酉上神为初传，阴日取酉下神为初传
        day_stem_idx = STEMS.index(day_stem)
        is_yang_day = (day_stem_idx % 2 == 0)  # 甲丙戊庚壬为阳
        if is_yang_day:
            first = heaven_plate["酉"]  # 酉上神（天盘酉位）
        else:
            # 酉下神：地盘酉的天盘是heaven_plate["酉"]，酉下神是地盘上对应天盘酉的位置
            # 即找天盘为酉的地盘
            for earth, heaven in heaven_plate.items():
                if heaven == "酉":
                    first = earth
                    break
            else:
                first = "酉"
        second = heaven_plate[first]
        third = heaven_plate[second]
        return (first, second, third, "昴星法")


def setup_twelve_generals(day_stem, hour, heaven_plate, first_transmission):
    """排布十二天将
    返回：dict {地盘支: 天将}
    """
    # 确定贵人（阳贵人/阴贵人）
    # 白天用阳贵人，晚上用阴贵人
    # 简化：卯时到酉时（5-19点）用阳贵人，其他用阴贵人
    yang_noble, yin_noble = NOBLEMAN_DAY[day_stem]
    if 5 <= hour <= 19:
        noble_branch = yang_noble  # 阳贵人
    else:
        noble_branch = yin_noble  # 阴贵人

    # 贵人顺行/逆行
    # 贵人在亥子丑寅卯辰为顺行，在巳午未申酉戌为逆行
    noble_idx = BRANCHES.index(noble_branch)
    if noble_idx in [11, 0, 1, 2, 3, 4]:  # 亥子丑寅卯辰
        is_shun = True
    else:
        is_shun = False

    # 排布十二天将
    generals = {}
    for i in range(12):
        if is_shun:
            branch = BRANCHES[(noble_idx + i) % 12]
        else:
            branch = BRANCHES[(noble_idx - i) % 12]
        generals[branch] = TWELVE_GENERALS[i]

    return generals, noble_branch, ("阳贵" if 5 <= hour <= 19 else "阴贵"), ("顺行" if is_shun else "逆行")


def judge_keti(four_lessons, three_transmissions, method, month_general, hour_branch):
    """判断课体"""
    keti = []

    # 课体名称
    if method == "伏吟法":
        keti.append("伏吟课")
    elif method == "反吟法(有克)" or method == "反吟法(无克取马)":
        keti.append("反吟课")
    elif method == "八专法":
        keti.append("八专课")
    elif method == "别责法":
        keti.append("别责课")
    elif method == "昴星法":
        keti.append("昴星课")
    elif method == "遥克法(蒿矢/弹射)":
        keti.append("遥克课")
    elif method == "涉害法" or method == "涉害法(简化)":
        keti.append("涉害课")
    elif method == "比用法":
        keti.append("比用课")
    elif method == "贼克法":
        keti.append("贼克课")

    # 重审课：初传下克上
    first, second, third = three_transmissions
    # 知一课：多个下克上取比用
    if method == "比用法":
        keti.append("知一课")

    return keti


# ==================== 主排盘函数 ====================

def paipan(year, month, day, hour, question=""):
    """大六壬完整排盘"""
    result = {
        "基本信息": {
            "公历": f"{year}年{month}月{day}日{hour}时",
            "占时": get_hour_branch(hour) + "时",
            "月将": "",
            "月将名": "",
            "日干": "",
            "日支": "",
            "日柱": "",
            "旬空": "",
            "驿马": "",
            "占问": question
        },
        "天盘": {},
        "四课": [],
        "三传": {},
        "十二天将": {},
        "课体": [],
        "生命论解读": []
    }

    # 1. 确定月将
    mg = get_month_general(month, day)
    result["基本信息"]["月将"] = mg
    result["基本信息"]["月将名"] = MONTH_GENERALS[mg]

    # 2. 确定占时
    hour_branch = get_hour_branch(hour)

    # 3. 确定日柱
    day_pillar = get_day_pillar(year, month, day)
    day_stem = day_pillar[0]
    day_branch = day_pillar[1]
    result["基本信息"]["日干"] = day_stem
    result["基本信息"]["日支"] = day_branch
    result["基本信息"]["日柱"] = day_pillar

    # 4. 旬空
    kongwang = get_kongwang(day_pillar)
    result["基本信息"]["旬空"] = kongwang

    # 5. 驿马
    horse = HORSE_STAR.get(day_branch, "寅")
    result["基本信息"]["驿马"] = horse

    # 6. 月将加时，排布天盘
    heaven_plate = setup_heaven_plate(mg, hour_branch)
    result["天盘"] = heaven_plate

    # 7. 起四课
    four_lessons = get_four_lessons(day_stem, day_branch, heaven_plate)
    result["四课"] = four_lessons

    # 8. 起三传
    first, second, third, method = get_three_transmissions(
        four_lessons, day_stem, day_branch, heaven_plate, mg, hour_branch
    )
    result["三传"] = {
        "初传": first,
        "中传": second,
        "末传": third,
        "起法": method,
        "初传天将": "",
        "中传天将": "",
        "末传天将": ""
    }

    # 9. 排布十二天将
    generals, noble_branch, noble_type, direction = setup_twelve_generals(
        day_stem, hour, heaven_plate, first
    )
    result["十二天将"] = {
        "排布": generals,
        "贵人": noble_branch,
        "贵人类型": noble_type,
        "贵人行向": direction
    }
    result["三传"]["初传天将"] = generals.get(first, "")
    result["三传"]["中传天将"] = generals.get(second, "")
    result["三传"]["末传天将"] = generals.get(third, "")

    # 10. 课体判断
    keti = judge_keti(four_lessons, (first, second, third), method, mg, hour_branch)
    result["课体"] = keti

    # 11. 空亡判断（三传、四课是否逢空）
    kw1, kw2 = kongwang[0], kongwang[1]
    result["空亡分析"] = {
        "初传空亡": first in kongwang,
        "中传空亡": second in kongwang,
        "末传空亡": third in kongwang,
        "说明": "空亡=名实不符，看起来有实际没有，需要操作还原去验证"
    }

    # 12. 生命论解读
    result["生命论解读"] = [
        "大六壬是特定时空点的能量态势分析（感的层面），不是宿命预言",
        "三传=感→应→操作的三个阶段：初传是当前爆发点（感），中传是过程中的变化（应），末传是操作后的收敛方向",
        "空亡=名实不符的位置，需要操作还原去验证，不是没有，是还没填实",
        "课体是结构倾向，不是结果判决书——结构硬，操作软，阳主阴从",
        f"本课{method}，{keti[0] if keti else ''}，核心操作方向需结合具体占问判断"
    ]

    return result


def print_paipan(result):
    """格式化打印大六壬排盘"""
    info = result["基本信息"]
    print("=" * 60)
    print("  大六壬排盘（生命论视角）")
    print("=" * 60)

    print(f"\n【基本信息】")
    print(f"  公历：{info['公历']}")
    print(f"  占时：{info['占时']}")
    print(f"  月将：{info['月将']}（{info['月将名']}）")
    print(f"  日柱：{info['日柱']}（日干{info['日干']}，日支{info['日支']}）")
    print(f"  旬空：{info['旬空']}")
    print(f"  驿马：{info['驿马']}")
    if info['占问']:
        print(f"  占问：{info['占问']}")

    # 天盘地盘对照
    print(f"\n【天盘地盘对照】")
    print(f"  {'地盘':<6}{'子':<4}{'丑':<4}{'寅':<4}{'卯':<4}{'辰':<4}{'巳':<4}{'午':<4}{'未':<4}{'申':<4}{'酉':<4}{'戌':<4}{'亥':<4}")
    heaven = result["天盘"]
    print(f"  {'天盘':<6}", end="")
    for b in BRANCHES:
        print(f"{heaven[b]:<4}", end="")
    print()

    # 四课
    print(f"\n【四课】")
    print(f"  {'':<8}{'干上':<10}{'干阴':<10}{'支上':<10}{'支阴':<10}")
    lessons = result["四课"]
    print(f"  {'天盘':<8}", end="")
    for name, earth, heaven_b in lessons:
        print(f"{heaven_b:<10}", end="")
    print()
    print(f"  {'地盘':<8}", end="")
    for name, earth, heaven_b in lessons:
        print(f"{earth:<10}", end="")
    print()

    # 三传
    san = result["三传"]
    print(f"\n【三传】（起法：{san['起法']}）")
    print(f"  {'':<8}{'初传':<10}{'中传':<10}{'末传':<10}")
    print(f"  {'地支':<8}{san['初传']:<10}{san['中传']:<10}{san['末传']:<10}")
    print(f"  {'天将':<8}{san['初传天将']:<10}{san['中传天将']:<10}{san['末传天将']:<10}")

    # 十二天将
    tj = result["十二天将"]
    print(f"\n【十二天将】（贵人{tj['贵人']}，{tj['贵人类型']}，{tj['贵人行向']}）")
    print(f"  {'地盘':<6}", end="")
    for b in BRANCHES:
        print(f"{b:<4}", end="")
    print()
    print(f"  {'天将':<6}", end="")
    for b in BRANCHES:
        print(f"{tj['排布'][b]:<4}", end="")
    print()

    # 课体
    print(f"\n【课体】")
    for k in result["课体"]:
        print(f"  - {k}")

    # 空亡分析
    kw = result["空亡分析"]
    print(f"\n【空亡分析】")
    print(f"  初传空亡：{'是' if kw['初传空亡'] else '否'}")
    print(f"  中传空亡：{'是' if kw['中传空亡'] else '否'}")
    print(f"  末传空亡：{'是' if kw['末传空亡'] else '否'}")
    print(f"  说明：{kw['说明']}")

    # 生命论解读
    print(f"\n【生命论解读】")
    for line in result["生命论解读"]:
        print(f"  {line}")

    print("\n" + "=" * 60)
    print("  注：大六壬是特定时空点的能量态势分析，不是宿命预言。")
    print("  三传=感→应→操作，空亡=名实不符需操作验证，课体=结构倾向。")
    print("  结构硬，操作软，阳主阴从。")
    print("=" * 60)


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    if len(sys.argv) >= 5:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
        day = int(sys.argv[3])
        hour = int(sys.argv[4])
        question = sys.argv[5] if len(sys.argv) > 5 else ""

        result = paipan(year, month, day, hour, question)
        print_paipan(result)

        if "--json" in sys.argv:
            print("\n\n=== JSON 输出 ===")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法：python liuren_paipan.py 年 月 日 时 [占问内容] [--json]")
        print("示例：python liuren_paipan.py 2026 9 2 16 感情")
        print("示例：python liuren_paipan.py 2026 8 18 2 事业 --json")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字排盘工具
输入：公历年月日时（或农历）
输出：四柱八字、十神、藏干、五行统计、日主旺衰、大运流年
生命论视角：八字是初始能量结构S₀，不是命运判决书
"""

from datetime import datetime, timedelta
import math
import json
import sys

# ==================== 基础数据 ====================

# 天干
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
# 地支
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 天干五行
STEM_ELEMENT = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水"
}

# 天干阴阳（阳干=同性，阴干=异性）
STEM_YIN_YANG = {
    "甲": "阳", "乙": "阴",
    "丙": "阳", "丁": "阴",
    "戊": "阳", "己": "阴",
    "庚": "阳", "辛": "阴",
    "壬": "阳", "癸": "阴"
}

# 地支五行
BRANCH_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水"
}

# 地支阴阳
BRANCH_YIN_YANG = {
    "子": "阳", "丑": "阴", "寅": "阳", "卯": "阴",
    "辰": "阳", "巳": "阴", "午": "阳", "未": "阴",
    "申": "阳", "酉": "阴", "戌": "阳", "亥": "阴"
}

# 地支藏干（本气、中气、余气）
BRANCH_HIDDEN_STEMS = {
    "子": ["癸"],
    "丑": ["己", "辛", "癸"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"]
}

# 五行生克
# 生：木生火，火生土，土生金，金生水，水生木
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 克：木克土，土克水，水克火，火克金，金克木
OVERCOMES = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 五虎遁：年干推正月（寅月）月干
# 甲己之年丙作首，乙庚之岁戊为头，丙辛必定寻庚起，丁壬壬位顺行流，戊癸何方发，甲寅之上好追求
FIVE_TIGER_ESCAPE = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲"
}

# 五鼠遁：日干推子时干
# 甲己还加甲，乙庚丙作初，丙辛从戊起，丁壬庚子居，戊癸何方发，壬子是真途
FIVE_RAT_ESCAPE = {
    "甲": "甲", "己": "甲",
    "乙": "丙", "庚": "丙",
    "丙": "戊", "辛": "戊",
    "丁": "庚", "壬": "庚",
    "戊": "壬", "癸": "壬"
}

# 二十四节气（每月一个节一个气，月柱以"节"为界）
# 节：立春、惊蛰、清明、立夏、芒种、小暑、立秋、白露、寒露、立冬、大雪、小寒
# 气：雨水、春分、谷雨、小满、夏至、大暑、处暑、秋分、霜降、小雪、冬至、大寒
SOLAR_TERMS = {
    "立春": (2, 4),    "雨水": (2, 19),
    "惊蛰": (3, 6),    "春分": (3, 21),
    "清明": (4, 5),    "谷雨": (4, 20),
    "立夏": (5, 6),    "小满": (5, 21),
    "芒种": (6, 6),    "夏至": (6, 21),
    "小暑": (7, 7),    "大暑": (7, 23),
    "立秋": (8, 8),    "处暑": (8, 23),
    "白露": (9, 8),    "秋分": (9, 23),
    "寒露": (10, 8),   "霜降": (10, 23),
    "立冬": (11, 7),   "小雪": (11, 22),
    "大雪": (12, 7),   "冬至": (12, 22),
    "小寒": (1, 6),    "大寒": (1, 20)
}

# 月支对应（寅月=立春后，卯月=惊蛰后...）
MONTH_BRANCH = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
# 每个月支对应的"节"
MONTH_JIE = ["立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "小寒"]

# 纳音五行（六十甲子纳音）
NAYIN = {
    "甲子": "海中金", "乙丑": "海中金",
    "丙寅": "炉中火", "丁卯": "炉中火",
    "戊辰": "大林木", "己巳": "大林木",
    "庚午": "路旁土", "辛未": "路旁土",
    "壬申": "剑锋金", "癸酉": "剑锋金",
    "甲戌": "山头火", "乙亥": "山头火",
    "丙子": "涧下水", "丁丑": "涧下水",
    "戊寅": "城头土", "己卯": "城头土",
    "庚辰": "白蜡金", "辛巳": "白蜡金",
    "壬午": "杨柳木", "癸未": "杨柳木",
    "甲申": "泉中水", "乙酉": "泉中水",
    "丙戌": "屋上土", "丁亥": "屋上土",
    "戊子": "霹雳火", "己丑": "霹雳火",
    "庚寅": "松柏木", "辛卯": "松柏木",
    "壬辰": "长流水", "癸巳": "长流水",
    "甲午": "沙中金", "乙未": "沙中金",
    "丙申": "山下火", "丁酉": "山下火",
    "戊戌": "平地木", "己亥": "平地木",
    "庚子": "壁上土", "辛丑": "壁上土",
    "壬寅": "金箔金", "癸卯": "金箔金",
    "甲辰": "覆灯火", "乙巳": "覆灯火",
    "丙午": "天河水", "丁未": "天河水",
    "戊申": "大驿土", "己酉": "大驿土",
    "庚戌": "钗钏金", "辛亥": "钗钏金",
    "壬子": "桑柘木", "癸丑": "桑柘木",
    "甲寅": "大溪水", "乙卯": "大溪水",
    "丙辰": "沙中土", "丁巳": "沙中土",
    "戊午": "天上火", "己未": "天上火",
    "庚申": "石榴木", "辛酉": "石榴木",
    "壬戌": "大海水", "癸亥": "大海水"
}

# 十干禄（地支中天干的禄位）
STEM_LU = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳", "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
# 十干羊刃
STEM_YANGREN = {"甲": "卯", "乙": "寅", "丙": "午", "丁": "巳", "戊": "午", "己": "巳", "庚": "酉", "辛": "申", "壬": "子", "癸": "亥"}
# 十干墓库
STEM_MU = {"甲": "未", "乙": "戌", "丙": "戌", "丁": "丑", "戊": "戌", "己": "丑", "庚": "丑", "辛": "辰", "壬": "辰", "癸": "未"}


# ==================== 核心计算函数 ====================

def get_year_pillar(year, month, day):
    """计算年柱（以立春为界）"""
    # 立春一般在2月4日左右
    lichun_month, lichun_day = SOLAR_TERMS["立春"]
    if (month < lichun_month) or (month == lichun_month and day < lichun_day):
        year -= 1
    # 年干：(year - 4) % 10
    stem_idx = (year - 4) % 10
    # 年支：(year - 4) % 12
    branch_idx = (year - 4) % 12
    return HEAVENLY_STEMS[stem_idx] + EARTHLY_BRANCHES[branch_idx]


def get_month_pillar(year_stem, month, day):
    """计算月柱（以节为界）"""
    # 确定当前月支索引
    month_branch_idx = None
    for i, jie_name in enumerate(MONTH_JIE):
        jie_month, jie_day = SOLAR_TERMS[jie_name]
        # 检查是否过了这个节
        if (month > jie_month) or (month == jie_month and day >= jie_day):
            month_branch_idx = i
        else:
            break
    if month_branch_idx is None:
        # 还在小寒之前，属于上一年的丑月
        month_branch_idx = 11  # 丑

    month_branch = MONTH_BRANCH[month_branch_idx]
    # 月干：五虎遁，从寅月（index 0）开始
    first_month_stem = FIVE_TIGER_ESCAPE[year_stem]
    first_stem_idx = HEAVENLY_STEMS.index(first_month_stem)
    month_stem_idx = (first_stem_idx + month_branch_idx) % 10
    month_stem = HEAVENLY_STEMS[month_stem_idx]
    return month_stem + month_branch


def get_day_pillar(year, month, day):
    """计算日柱（核心算法：以1900年1月1日为甲戌日基准）"""
    # 1900年1月1日是甲戌日（甲戌在六十甲子中索引为10）
    base_date = datetime(1900, 1, 1)
    target_date = datetime(year, month, day)
    delta_days = (target_date - base_date).days
    # 甲戌日索引=10（甲=0, 戌=10, 60甲子中甲戌的索引）
    # 六十甲子索引计算：stem_idx = idx % 10, branch_idx = idx % 12
    # 甲戌：stem=0, branch=10，需要满足 idx%10=0 且 idx%12=10
    # 解：idx=10 (10%10=0, 10%12=10) ✓
    ganzhi_idx = (10 + delta_days) % 60
    stem_idx = ganzhi_idx % 10
    branch_idx = ganzhi_idx % 12
    return HEAVENLY_STEMS[stem_idx] + EARTHLY_BRANCHES[branch_idx]


def get_hour_pillar(day_stem, hour):
    """计算时柱"""
    # 时支：23-1点=子, 1-3点=丑, 3-5点=寅...
    if hour == 23:
        hour_branch_idx = 0  # 子
    else:
        hour_branch_idx = (hour + 1) // 2 % 12
    hour_branch = EARTHLY_BRANCHES[hour_branch_idx]
    # 时干：五鼠遁
    first_hour_stem = FIVE_RAT_ESCAPE[day_stem]
    first_stem_idx = HEAVENLY_STEMS.index(first_hour_stem)
    hour_stem_idx = (first_stem_idx + hour_branch_idx) % 10
    hour_stem = HEAVENLY_STEMS[hour_stem_idx]
    return hour_stem + hour_branch


def get_shishen(day_stem, other_stem):
    """计算十神（以日干为我）"""
    day_elem = STEM_ELEMENT[day_stem]
    day_yy = STEM_YIN_YANG[day_stem]
    other_elem = STEM_ELEMENT[other_stem]
    other_yy = STEM_YIN_YANG[other_stem]
    same_yy = (day_yy == other_yy)  # 同性

    if other_elem == day_elem:
        return "比肩" if same_yy else "劫财"
    elif GENERATES[other_elem] == day_elem:  # 生我者
        return "偏印" if same_yy else "正印"
    elif GENERATES[day_elem] == other_elem:  # 我生者
        return "食神" if same_yy else "伤官"
    elif OVERCOMES[other_elem] == day_elem:  # 克我者
        return "七杀" if same_yy else "正官"
    elif OVERCOMES[day_elem] == other_elem:  # 我克者
        return "偏财" if same_yy else "正财"
    else:
        return "未知"


def get_branch_shishen(day_stem, branch):
    """计算地支藏干的十神"""
    hidden = BRANCH_HIDDEN_STEMS[branch]
    result = []
    for stem in hidden:
        result.append((stem, get_shishen(day_stem, stem)))
    return result


def count_wuxing(four_pillars):
    """统计五行数量（天干+地支藏干）"""
    count = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for pillar in four_pillars:
        stem = pillar[0]
        branch = pillar[1]
        # 天干五行（权重1.0）
        count[STEM_ELEMENT[stem]] += 1.0
        # 地支藏干（本气0.6，中气0.3，余气0.1）
        hidden = BRANCH_HIDDEN_STEMS[branch]
        weights = [0.6, 0.3, 0.1]
        for i, h_stem in enumerate(hidden):
            w = weights[i] if i < len(weights) else 0.1
            count[STEM_ELEMENT[h_stem]] += w
    return count


def analyze_wangshuai(day_stem, month_branch, four_pillars, wuxing_count):
    """分析日主旺衰（得令、得地、得势）"""
    day_elem = STEM_ELEMENT[day_stem]
    result = {"得令": False, "得地": 0, "得势": 0, "总评": "", "分数": 0}

    # 1. 得令：日主五行在月令是否旺相
    # 月令五行
    month_elem = BRANCH_ELEMENT[month_branch]
    # 旺相休囚死：同我者旺，我生者相，生我者休，克我者囚，我克者死
    if month_elem == day_elem:
        result["得令"] = True
        result["分数"] += 30
    elif GENERATES[day_elem] == month_elem:  # 我生月令（月令是我生的）=相
        result["分数"] += 15
    elif GENERATES[month_elem] == day_elem:  # 月令生我=休
        result["分数"] += 10
    elif OVERCOMES[month_elem] == day_elem:  # 月令克我=囚
        result["分数"] -= 10
    elif OVERCOMES[day_elem] == month_elem:  # 我克月令=死
        result["分数"] -= 5

    # 2. 得地：日主在其他地支中是否有根（禄、刃、库、余气）
    lu_branch = STEM_LU[day_stem]
    yr_branch = STEM_YANGREN[day_stem]
    mu_branch = STEM_MU[day_stem]
    for pillar in four_pillars:
        branch = pillar[1]
        if branch == lu_branch:
            result["得地"] += 2
            result["分数"] += 15
        elif branch == yr_branch:
            result["得地"] += 1.5
            result["分数"] += 12
        elif branch == mu_branch:
            result["得地"] += 1
            result["分数"] += 8
        else:
            # 检查地支藏干中是否有同五行
            hidden = BRANCH_HIDDEN_STEMS[branch]
            for h in hidden:
                if STEM_ELEMENT[h] == day_elem:
                    result["得地"] += 0.5
                    result["分数"] += 3
                    break

    # 3. 得势：天干中是否有比劫帮身、印星生身
    for pillar in four_pillars:
        stem = pillar[0]
        if stem == day_stem:
            continue
        shishen = get_shishen(day_stem, stem)
        if shishen in ["比肩", "劫财"]:
            result["得势"] += 1
            result["分数"] += 10
        elif shishen in ["正印", "偏印"]:
            result["得势"] += 0.5
            result["分数"] += 5

    # 总评
    score = result["分数"]
    if score >= 50:
        result["总评"] = "身强"
    elif score >= 20:
        result["总评"] = "偏强"
    elif score >= -10:
        result["总评"] = "中和"
    elif score >= -30:
        result["总评"] = "偏弱"
    else:
        result["总评"] = "身弱"

    return result


def get_dayun(day_stem, year_stem, birth_datetime, gender="男"):
    """计算大运（阳男阴女顺排，阴男阳女逆排）"""
    day_yy = STEM_YIN_YANG[day_stem]
    year_yy = STEM_YIN_YANG[year_stem]
    # 阳男阴女顺排，阴男阳女逆排
    # 注意：大运顺逆看的是年干阴阳和性别，不是日干
    is_yang_year = (year_yy == "阳")
    is_male = (gender == "男")
    shun_pai = (is_yang_year and is_male) or (not is_yang_year and not is_male)

    # 起运年龄：从出生到最近节气的天数 / 3 = 起运岁数
    # 顺排：从出生到下一个节
    # 逆排：从上一个节到出生
    birth_month = birth_datetime.month
    birth_day = birth_datetime.day
    birth_hour = birth_datetime.hour

    # 找最近的节
    jie_list = [(name, SOLAR_TERMS[name]) for name in MONTH_JIE]
    jie_list.sort(key=lambda x: (x[1][0], x[1][1]))

    target_jie = None
    days_diff = 0
    if shun_pai:
        # 找下一个节
        for name, (m, d) in jie_list:
            if (m > birth_month) or (m == birth_month and d >= birth_day):
                target_jie = name
                jie_date = datetime(birth_datetime.year, m, d, 0, 0, 0)
                delta = jie_date - birth_datetime
                days_diff = delta.total_seconds() / 86400
                break
        if target_jie is None:
            # 下一年的小寒
            target_jie = "小寒"
            jie_date = datetime(birth_datetime.year + 1, 1, 6, 0, 0, 0)
            delta = jie_date - birth_datetime
            days_diff = delta.total_seconds() / 86400
    else:
        # 找上一个节
        for name, (m, d) in reversed(jie_list):
            if (m < birth_month) or (m == birth_month and d <= birth_day):
                target_jie = name
                jie_date = datetime(birth_datetime.year, m, d, 0, 0, 0)
                delta = birth_datetime - jie_date
                days_diff = delta.total_seconds() / 86400
                break
        if target_jie is None:
            # 上一年的大雪
            target_jie = "大雪"
            jie_date = datetime(birth_datetime.year - 1, 12, 7, 0, 0, 0)
            delta = birth_datetime - jie_date
            days_diff = delta.total_seconds() / 86400

    # 起运年龄：3天=1岁，1天=4个月，1小时=5天
    qiyun_years = days_diff / 3
    qiyun_sui = int(qiyun_years)  # 虚岁
    qiyun_months = int((qiyun_years - qiyun_sui) * 12)

    # 大运干支：从月柱开始顺排或逆排
    month_pillar = get_month_pillar(year_stem, birth_month, birth_day)
    month_stem_idx = HEAVENLY_STEMS.index(month_pillar[0])
    month_branch_idx = EARTHLY_BRANCHES.index(month_pillar[1])

    dayun_list = []
    for i in range(8):  # 排8步大运
        if shun_pai:
            stem_idx = (month_stem_idx + i + 1) % 10
            branch_idx = (month_branch_idx + i + 1) % 12
        else:
            stem_idx = (month_stem_idx - i - 1) % 10
            branch_idx = (month_branch_idx - i - 1) % 12
        dayun_stem = HEAVENLY_STEMS[stem_idx]
        dayun_branch = EARTHLY_BRANCHES[branch_idx]
        start_age = qiyun_sui + i * 10
        start_year = birth_datetime.year + start_age
        dayun_list.append({
            "大运": dayun_stem + dayun_branch,
            "起运年龄": f"{start_age}岁",
            "起运年份": f"{start_year}年",
            "十神": get_shishen(day_stem, dayun_stem),
            "纳音": NAYIN.get(dayun_stem + dayun_branch, "")
        })

    return {
        "顺逆": "顺排" if shun_pai else "逆排",
        "起运年龄": f"{qiyun_sui}岁{qiyun_months}个月",
        "起运天数": f"{days_diff:.1f}天",
        "最近节气": target_jie,
        "大运列表": dayun_list
    }


def get_liunian(day_stem, birth_year, start_year, count=10):
    """计算流年"""
    result = []
    for i in range(count):
        year = start_year + i
        stem_idx = (year - 4) % 10
        branch_idx = (year - 4) % 12
        liunian_stem = HEAVENLY_STEMS[stem_idx]
        liunian_branch = EARTHLY_BRANCHES[branch_idx]
        result.append({
            "年份": f"{year}年",
            "干支": liunian_stem + liunian_branch,
            "十神": get_shishen(day_stem, liunian_stem),
            "纳音": NAYIN.get(liunian_stem + liunian_branch, "")
        })
    return result


# ==================== 主排盘函数 ====================

def paipan(year, month, day, hour, gender="男", name=""):
    """完整八字排盘"""
    result = {
        "基本信息": {
            "姓名": name,
            "性别": gender,
            "公历": f"{year}年{month}月{day}日{hour}时",
            "排盘时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    # 四柱
    year_pillar = get_year_pillar(year, month, day)
    month_pillar = get_month_pillar(year_pillar[0], month, day)
    day_pillar = get_day_pillar(year, month, day)
    hour_pillar = get_hour_pillar(day_pillar[0], hour)
    four_pillars = [year_pillar, month_pillar, day_pillar, hour_pillar]
    pillar_names = ["年柱", "月柱", "日柱", "时柱"]

    result["四柱"] = {}
    for i, name_p in enumerate(pillar_names):
        pillar = four_pillars[i]
        stem = pillar[0]
        branch = pillar[1]
        result["四柱"][name_p] = {
            "天干": stem,
            "地支": branch,
            "干支": pillar,
            "天干十神": get_shishen(day_pillar[0], stem) if name_p != "日柱" else "日主",
            "地支藏干": get_branch_shishen(day_pillar[0], branch),
            "纳音": NAYIN.get(pillar, ""),
            "空亡": get_kongwang(day_pillar) if name_p != "日柱" else ""
        }

    # 日主
    day_stem = day_pillar[0]
    result["日主"] = {
        "天干": day_stem,
        "五行": STEM_ELEMENT[day_stem],
        "阴阳": STEM_YIN_YANG[day_stem],
        "描述": get_day_stem_description(day_stem)
    }

    # 五行统计
    wuxing = count_wuxing(four_pillars)
    result["五行统计"] = {k: round(v, 1) for k, v in wuxing.items()}
    result["五行旺衰"] = get_wuxing_wangshuai(wuxing)

    # 日主旺衰
    wangshuai = analyze_wangshuai(day_stem, month_pillar[1], four_pillars, wuxing)
    result["日主旺衰"] = wangshuai

    # 用神建议
    result["用神建议"] = get_yong_shen(day_stem, wangshuai, wuxing, month_pillar[1])

    # 十神统计
    result["十神统计"] = count_shishen(day_stem, four_pillars)

    # 大运
    birth_dt = datetime(year, month, day, hour)
    dayun = get_dayun(day_stem, year_pillar[0], birth_dt, gender)
    result["大运"] = dayun

    # 流年（从今年开始10年）
    current_year = datetime.now().year
    result["流年"] = get_liunian(day_stem, year, current_year, 10)

    # 特殊格局
    result["特殊格局"] = check_special_patterns(day_stem, four_pillars, wuxing)

    # 生命论解读
    result["生命论解读"] = get_mingbenlun_interpretation(day_stem, wangshuai, four_pillars)

    return result


def get_kongwang(day_pillar):
    """计算空亡（日柱旬空）"""
    stem_idx = HEAVENLY_STEMS.index(day_pillar[0])
    branch_idx = EARTHLY_BRANCHES.index(day_pillar[1])
    # 旬首：stem_idx - (stem_idx % 10) 不对，应该是六甲旬首
    # 六甲：甲子、甲戌、甲申、甲午、甲辰、甲寅
    # 旬首地支 = branch_idx - stem_idx (mod 12)
    xunshou_branch_idx = (branch_idx - stem_idx) % 12
    # 空亡 = 旬首地支 + 10, +11 (mod 12)
    kw1_idx = (xunshou_branch_idx + 10) % 12
    kw2_idx = (xunshou_branch_idx + 11) % 12
    return EARTHLY_BRANCHES[kw1_idx] + EARTHLY_BRANCHES[kw2_idx]


def get_day_stem_description(stem):
    """日主天干描述"""
    descriptions = {
        "甲": "参天大树，栋梁之木，正直向上，有担当，但易折",
        "乙": "花草藤蔓，柔韧曲折，善于适应，重感情，但易纠结",
        "丙": "太阳之火，光明热烈，外向积极，有感染力，但易急躁",
        "丁": "灯烛之火，温暖细腻，内秀持久，重精神，但易忧郁",
        "戊": "高山厚土，稳重包容，诚信务实，有承载力，但易固执",
        "己": "田园之土，温润滋养，细心周到，善积累，但易多疑",
        "庚": "刀剑之金，刚硬锋利，果断勇敢，有魄力，但易伤人",
        "辛": "珠宝之金，精致锐利，审美出众，重品质，但易挑剔",
        "壬": "江河之水，奔流不息，智慧灵活，有魄力，但易泛滥",
        "癸": "雨露之水，润物无声，敏感细腻，重直觉，但易沉溺"
    }
    return descriptions.get(stem, "")


def get_wuxing_wangshuai(wuxing):
    """五行旺衰排序"""
    sorted_items = sorted(wuxing.items(), key=lambda x: x[1], reverse=True)
    return " > ".join([f"{k}({v})" for k, v in sorted_items])


def get_yong_shen(day_stem, wangshuai, wuxing, month_branch):
    """用神建议（简化版）"""
    day_elem = STEM_ELEMENT[day_stem]
    result = {"喜用": [], "忌神": [], "说明": ""}

    if wangshuai["总评"] in ["身强", "偏强"]:
        # 身强喜克泄耗：官杀（克我）、食伤（我生）、财星（我克）
        result["喜用"].append(f"{OVERCOMES[day_elem]}（官杀，克身）")
        result["喜用"].append(f"{GENERATES[day_elem]}（食伤，泄身）")
        result["喜用"].append(f"{[e for e in OVERCOMES if OVERCOMES[e]==day_elem][0]}（财星，耗身）")
        result["忌神"].append(f"{day_elem}（比劫，帮身）")
        result["忌神"].append(f"{[e for e in GENERATES if GENERATES[e]==day_elem][0]}（印星，生身）")
        result["说明"] = "身强喜克泄耗，忌生扶。用神在官杀、食伤、财星。"
    elif wangshuai["总评"] in ["身弱", "偏弱"]:
        # 身弱喜生扶：印星（生我）、比劫（同我）
        result["喜用"].append(f"{[e for e in GENERATES if GENERATES[e]==day_elem][0]}（印星，生身）")
        result["喜用"].append(f"{day_elem}（比劫，帮身）")
        result["忌神"].append(f"{OVERCOMES[day_elem]}（官杀，克身）")
        result["忌神"].append(f"{GENERATES[day_elem]}（食伤，泄身）")
        result["忌神"].append(f"{[e for e in OVERCOMES if OVERCOMES[e]==day_elem][0]}（财星，耗身）")
        result["说明"] = "身弱喜生扶，忌克泄耗。用神在印星、比劫。但身弱不等于命不好，是能量承载力需要后天加厚（T值提升）。"
    else:
        result["喜用"].append("需结合具体格局判断")
        result["说明"] = "中和之命，用神需结合具体格局和大运流年动态调整。"

    return result


def count_shishen(day_stem, four_pillars):
    """统计十神数量"""
    count = {}
    for pillar in four_pillars:
        stem = pillar[0]
        if stem == day_stem:
            ss = "日主"
        else:
            ss = get_shishen(day_stem, stem)
        count[ss] = count.get(ss, 0) + 1
        # 地支藏干
        hidden = BRANCH_HIDDEN_STEMS[pillar[1]]
        for h in hidden:
            h_ss = get_shishen(day_stem, h)
            count[h_ss] = count.get(h_ss, 0) + 0.3
    return {k: round(v, 1) for k, v in sorted(count.items(), key=lambda x: x[1], reverse=True)}


def check_special_patterns(day_stem, four_pillars, wuxing):
    """检查特殊格局"""
    patterns = []
    day_elem = STEM_ELEMENT[day_stem]

    # 从格（某五行极旺，日主弱极，从其旺势）
    max_elem = max(wuxing, key=wuxing.get)
    max_value = wuxing[max_elem]
    total = sum(wuxing.values())
    if max_value / total > 0.5 and day_elem != max_elem:
        patterns.append(f"疑似从格（{max_elem}极旺，占{max_value/total*100:.0f}%），需结合具体判断")

    # 五行缺某行
    for elem, val in wuxing.items():
        if val < 0.5:
            patterns.append(f"五行缺{elem}（{val}）")

    # 天干一字格
    stems = [p[0] for p in four_pillars]
    if len(set(stems)) == 1:
        patterns.append("天干一字格（四干相同）")

    # 地支一字格
    branches = [p[1] for p in four_pillars]
    if len(set(branches)) == 1:
        patterns.append("地支一字格（四支相同）")

    if not patterns:
        patterns.append("无明显特殊格局，按正格分析")

    return patterns


def get_mingbenlun_interpretation(day_stem, wangshuai, four_pillars):
    """生命论视角解读"""
    day_elem = STEM_ELEMENT[day_stem]
    interpretation = []

    # α（生命层级/格局）
    interpretation.append("【α·格局】八字是初始能量结构S₀，决定你的基本操作倾向，不是命运判决书。格局高低看五行流通和用神有力程度。")

    # T（稳态基准/身强身弱）
    if wangshuai["总评"] in ["身强", "偏强"]:
        interpretation.append("【T·稳态】身强=能量承载力较强，油箱厚，能担财官。但身强也容易刚愎自用，需要食伤泄秀或官杀约束。")
    elif wangshuai["总评"] in ["身弱", "偏弱"]:
        interpretation.append("【T·稳态】身弱=能量承载力偏弱，油箱薄，担不动太多东西。不是命不好，是需要后天加厚T值——睡眠、运动、规律作息、印星（学习、吸收）补身。身弱的人往往感知力强、敏感度高，α值可能不低。")
    else:
        interpretation.append("【T·稳态】中和=能量平衡，承载力适中，适应性强。")

    # N（负熵比率/大运流年）
    interpretation.append("【N·操作】大运流年是时间维度的能量场，决定你在什么环境里操作。N无天花板——好的大运能让M翻倍，差的大运也能通过操作（N>1）逆转。阳主阴从：你的操作（N）主导，结构（α+T）从属。")

    # M（生命意义总量）
    interpretation.append("【M·成果】M=α×T×N。八字给的是α+T的初始值，N是你每一步的操作，M是操作的总和。命好不如运好，运好不如操作好——这就是生命论的术数观。")

    return interpretation


# ==================== 格式化输出 ====================

def print_paipan(result):
    """格式化打印排盘结果"""
    print("=" * 60)
    print("  八字排盘（生命论视角）")
    print("=" * 60)

    # 基本信息
    info = result["基本信息"]
    print(f"\n【基本信息】")
    print(f"  姓名：{info['姓名'] or '未知'}")
    print(f"  性别：{info['性别']}")
    print(f"  公历：{info['公历']}")
    print(f"  排盘时间：{info['排盘时间']}")

    # 四柱
    print(f"\n【四柱八字】")
    print(f"  {'':<6}{'年柱':<10}{'月柱':<10}{'日柱':<10}{'时柱':<10}")
    pillars = result["四柱"]
    # 天干十神
    print(f"  {'十神':<6}", end="")
    for name in ["年柱", "月柱", "日柱", "时柱"]:
        print(f"{pillars[name]['天干十神']:<10}", end="")
    print()
    # 天干
    print(f"  {'天干':<6}", end="")
    for name in ["年柱", "月柱", "日柱", "时柱"]:
        print(f"{pillars[name]['天干']:<10}", end="")
    print()
    # 地支
    print(f"  {'地支':<6}", end="")
    for name in ["年柱", "月柱", "日柱", "时柱"]:
        print(f"{pillars[name]['地支']:<10}", end="")
    print()
    # 藏干
    print(f"  {'藏干':<6}", end="")
    for name in ["年柱", "月柱", "日柱", "时柱"]:
        hidden = pillars[name]["地支藏干"]
        hidden_str = "".join([h[0] for h in hidden])
        print(f"{hidden_str:<10}", end="")
    print()
    # 纳音
    print(f"  {'纳音':<6}", end="")
    for name in ["年柱", "月柱", "日柱", "时柱"]:
        print(f"{pillars[name]['纳音']:<10}", end="")
    print()

    # 日主
    day_master = result["日主"]
    print(f"\n【日主】{day_master['天干']}（{day_master['五行']}·{day_master['阴阳']}）")
    print(f"  {day_master['描述']}")

    # 五行统计
    print(f"\n【五行统计】")
    wuxing = result["五行统计"]
    for elem in ["木", "火", "土", "金", "水"]:
        bar = "█" * int(wuxing[elem] * 2)
        print(f"  {elem}: {wuxing[elem]:<5} {bar}")
    print(f"  旺衰排序：{result['五行旺衰']}")

    # 日主旺衰
    ws = result["日主旺衰"]
    print(f"\n【日主旺衰分析】")
    print(f"  得令：{'是' if ws['得令'] else '否'}")
    print(f"  得地（根气）：{ws['得地']}")
    print(f"  得势（帮扶）：{ws['得势']}")
    print(f"  综合评分：{ws['分数']}")
    print(f"  总评：{ws['总评']}")

    # 用神建议
    ys = result["用神建议"]
    print(f"\n【用神建议】")
    print(f"  喜用：{'、'.join(ys['喜用'])}")
    print(f"  忌神：{'、'.join(ys['忌神'])}")
    print(f"  说明：{ys['说明']}")

    # 十神统计
    print(f"\n【十神统计】")
    for ss, count in result["十神统计"].items():
        print(f"  {ss}: {count}")

    # 特殊格局
    print(f"\n【特殊格局】")
    for p in result["特殊格局"]:
        print(f"  - {p}")

    # 大运
    print(f"\n【大运】（{result['大运']['顺逆']}，起运{result['大运']['起运年龄']}，距{result['大运']['最近节气']}{result['大运']['起运天数']}）")
    print(f"  {'序号':<6}{'大运':<10}{'十神':<8}{'起运年龄':<10}{'起运年份':<10}{'纳音':<10}")
    for i, dy in enumerate(result["大运"]["大运列表"]):
        print(f"  {i+1:<6}{dy['大运']:<10}{dy['十神']:<8}{dy['起运年龄']:<10}{dy['起运年份']:<10}{dy['纳音']:<10}")

    # 流年
    print(f"\n【近10年流年】")
    print(f"  {'年份':<10}{'干支':<10}{'十神':<8}{'纳音':<10}")
    for ln in result["流年"]:
        print(f"  {ln['年份']:<10}{ln['干支']:<10}{ln['十神']:<8}{ln['纳音']:<10}")

    # 生命论解读
    print(f"\n【生命论解读】")
    for line in result["生命论解读"]:
        print(f"  {line}")

    print("\n" + "=" * 60)
    print("  注：八字是初始能量结构S₀，不是命运判决书。")
    print("  M=α×T×N，操作（N）主导，结构（α+T）从属。")
    print("=" * 60)


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    if len(sys.argv) >= 5:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
        day = int(sys.argv[3])
        hour = int(sys.argv[4])
        gender = sys.argv[5] if len(sys.argv) > 5 else "男"
        name = sys.argv[6] if len(sys.argv) > 6 else ""

        result = paipan(year, month, day, hour, gender, name)
        print_paipan(result)

        # 同时输出JSON
        if "--json" in sys.argv:
            print("\n\n=== JSON 输出 ===")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法：python bazi_paipan.py 年 月 日 时 [性别] [姓名] [--json]")
        print("示例：python bazi_paipan.py 2008 9 1 10 男 北原慢热")
        print("示例：python bazi_paipan.py 1818 5 5 2 男 马克思 --json")

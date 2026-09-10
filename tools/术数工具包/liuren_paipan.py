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

# ==================== 类神系统 ====================
# 类神 = 占问的那件事在符号系统中的操作闭包
# 占不同事取不同类神，类神不是盘给的，是问题决定的

# 五行生克（生=赋能，克=制约）
ELEMENT_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
ELEMENT_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 十神定义（以日干为我）
def get_shishen(day_stem, other_stem):
    """计算十神"""
    my_elem = STEM_ELEMENT[day_stem]
    other_elem = STEM_ELEMENT[other_stem]
    my_yin = day_stem in ["乙", "丁", "己", "辛", "癸"]
    other_yin = other_stem in ["乙", "丁", "己", "辛", "癸"]
    same_yin = my_yin == other_yin
    if my_elem == other_elem:
        return "比肩" if same_yin else "劫财"
    elif ELEMENT_SHENG[my_elem] == other_elem:
        return "食神" if same_yin else "伤官"
    elif ELEMENT_KE[my_elem] == other_elem:
        return "正财" if same_yin else "偏财"
    elif ELEMENT_KE[other_elem] == my_elem:
        return "正官" if same_yin else "七杀"
    elif ELEMENT_SHENG[other_elem] == my_elem:
        return "正印" if same_yin else "偏印"
    return "未知"

# 类神分类表（占问类型 → 主要类神列表）
LEISHEN_TABLE = {
    "感情": {"主要": [
        {"名称": "正财", "类型": "十神", "说明": "正缘/稳定关系（男占）"},
        {"名称": "偏财", "类型": "十神", "说明": "偏缘/短暂关系（男占）"},
        {"名称": "天后", "类型": "天将", "说明": "女方/女性"},
        {"名称": "青龙", "类型": "天将", "说明": "男方/男性"}],
     "辅助": [
        {"名称": "六合", "类型": "天将", "说明": "结合/合作通道"},
        {"名称": "太阴", "类型": "天将", "说明": "暗恋/隐藏感情"},
        {"名称": "朱雀", "类型": "天将", "说明": "沟通/表达"}]},
    "婚姻": {"主要": [
        {"名称": "正财", "类型": "十神", "说明": "妻子（男占）"},
        {"名称": "正官", "类型": "十神", "说明": "丈夫（女占）"},
        {"名称": "六合", "类型": "天将", "说明": "婚姻/结合"}],
     "辅助": [
        {"名称": "太常", "类型": "天将", "说明": "聘礼/宴席"},
        {"名称": "天后", "类型": "天将", "说明": "女方"},
        {"名称": "青龙", "类型": "天将", "说明": "男方"}]},
    "事业": {"主要": [
        {"名称": "正官", "类型": "十神", "说明": "稳定工作/体制内"},
        {"名称": "七杀", "类型": "十神", "说明": "创业/挑战/突破"},
        {"名称": "青龙", "类型": "天将", "说明": "贵人/机遇"}],
     "辅助": [
        {"名称": "正印", "类型": "十神", "说明": "靠山/资质/学历"},
        {"名称": "六合", "类型": "天将", "说明": "合作/团队"},
        {"名称": "驿马", "类型": "神煞", "说明": "变动/出差"}]},
    "工作": {"主要": [
        {"名称": "正官", "类型": "十神", "说明": "工作/职位"},
        {"名称": "七杀", "类型": "十神", "说明": "压力/挑战"},
        {"名称": "青龙", "类型": "天将", "说明": "贵人/机遇"}],
     "辅助": [
        {"名称": "正印", "类型": "十神", "说明": "靠山/资质"},
        {"名称": "六合", "类型": "天将", "说明": "合作"}]},
    "考试": {"主要": [
        {"名称": "正印", "类型": "十神", "说明": "文书/学历/知识"},
        {"名称": "朱雀", "类型": "天将", "说明": "文笔/表达/考试"},
        {"名称": "青龙", "类型": "天将", "说明": "贵人/顺利"}],
     "辅助": [
        {"名称": "食神", "类型": "十神", "说明": "才华/输出"},
        {"名称": "伤官", "类型": "十神", "说明": "创造力/思维"}]},
    "升学": {"主要": [
        {"名称": "正印", "类型": "十神", "说明": "学历/学校"},
        {"名称": "朱雀", "类型": "天将", "说明": "考试/文书"},
        {"名称": "青龙", "类型": "天将", "说明": "贵人/机遇"}],
     "辅助": [
        {"名称": "驿马", "类型": "神煞", "说明": "远行/异地求学"},
        {"名称": "六合", "类型": "天将", "说明": "合作/录取"}]},
    "财运": {"主要": [
        {"名称": "正财", "类型": "十神", "说明": "稳定收入/工资"},
        {"名称": "偏财", "类型": "十神", "说明": "意外收入/投资"},
        {"名称": "青龙", "类型": "天将", "说明": "财源/贵人"}],
     "辅助": [
        {"名称": "玄武", "类型": "天将", "说明": "暗财/风险"},
        {"名称": "白虎", "类型": "天将", "说明": "破财/风险"},
        {"名称": "六合", "类型": "天将", "说明": "合作求财"}]},
    "投资": {"主要": [
        {"名称": "偏财", "类型": "十神", "说明": "投资/投机"},
        {"名称": "玄武", "类型": "天将", "说明": "暗昧/风险"},
        {"名称": "白虎", "类型": "天将", "说明": "波动/风险"}],
     "辅助": [
        {"名称": "青龙", "类型": "天将", "说明": "贵人/机遇"},
        {"名称": "六合", "类型": "天将", "说明": "合作投资"}]},
    "失物": {"主要": [
        {"名称": "玄武", "类型": "天将", "说明": "丢失/暗昧"},
        {"名称": "太阴", "类型": "天将", "说明": "隐藏/找不到"}],
     "辅助": [
        {"名称": "白虎", "类型": "天将", "说明": "损坏/破坏"},
        {"名称": "六合", "类型": "天将", "说明": "找回/复合"}]},
    "健康": {"主要": [
        {"名称": "白虎", "类型": "天将", "说明": "病症/伤痛"},
        {"名称": "青龙", "类型": "天将", "说明": "康复/生机"}],
     "辅助": [
        {"名称": "正印", "类型": "十神", "说明": "休养/调理"},
        {"名称": "螣蛇", "类型": "天将", "说明": "虚惊/慢性病"}]},
    "疾病": {"主要": [
        {"名称": "白虎", "类型": "天将", "说明": "病症/伤痛"},
        {"名称": "螣蛇", "类型": "天将", "说明": "虚惊/缠绕"}],
     "辅助": [
        {"名称": "青龙", "类型": "天将", "说明": "康复"},
        {"名称": "正印", "类型": "十神", "说明": "休养"}]},
    "出行": {"主要": [
        {"名称": "驿马", "类型": "神煞", "说明": "出行/变动"},
        {"名称": "青龙", "类型": "天将", "说明": "顺利/贵人"}],
     "辅助": [
        {"名称": "六合", "类型": "天将", "说明": "顺利/合作"},
        {"名称": "白虎", "类型": "天将", "说明": "风险/意外"},
        {"名称": "玄武", "类型": "天将", "说明": "迷失/暗昧"}]},
    "搬家": {"主要": [
        {"名称": "驿马", "类型": "神煞", "说明": "变动/迁移"},
        {"名称": "正印", "类型": "十神", "说明": "居所/房子"},
        {"名称": "六合", "类型": "天将", "说明": "顺利/安稳"}],
     "辅助": [
        {"名称": "青龙", "类型": "天将", "说明": "贵人/顺利"},
        {"名称": "白虎", "类型": "天将", "说明": "变动/冲煞"}]},
    "官司": {"主要": [
        {"名称": "朱雀", "类型": "天将", "说明": "口舌/文书/诉讼"},
        {"名称": "正官", "类型": "十神", "说明": "官方/制裁"},
        {"名称": "勾陈", "类型": "天将", "说明": "纠缠/拖延"}],
     "辅助": [
        {"名称": "青龙", "类型": "天将", "说明": "贵人/胜诉"},
        {"名称": "六合", "类型": "天将", "说明": "和解/调解"},
        {"名称": "白虎", "类型": "天将", "说明": "刑伤/风险"}]},
    "口舌": {"主要": [
        {"名称": "朱雀", "类型": "天将", "说明": "口舌/是非"},
        {"名称": "螣蛇", "类型": "天将", "说明": "虚惊/缠绕"}],
     "辅助": [
        {"名称": "太阴", "类型": "天将", "说明": "暗中/隐藏"},
        {"名称": "玄武", "类型": "天将", "说明": "暗昧/小人"}]},
    "合作": {"主要": [
        {"名称": "六合", "类型": "天将", "说明": "合作/结合"},
        {"名称": "朱雀", "类型": "天将", "说明": "合同/文书"},
        {"名称": "青龙", "类型": "天将", "说明": "贵人/顺利"}],
     "辅助": [
        {"名称": "勾陈", "类型": "天将", "说明": "拖延/纠缠"},
        {"名称": "正财", "类型": "十神", "说明": "利益/分配"}]},
    "父母": {"主要": [
        {"名称": "正印", "类型": "十神", "说明": "母亲/长辈"},
        {"名称": "偏印", "类型": "十神", "说明": "父亲/继母"},
        {"名称": "太阴", "类型": "天将", "说明": "母亲/女性长辈"}],
     "辅助": [
        {"名称": "青龙", "类型": "天将", "说明": "健康/顺利"}]},
    "兄弟": {"主要": [
        {"名称": "比肩", "类型": "十神", "说明": "同性朋友/兄弟"},
        {"名称": "劫财", "类型": "十神", "说明": "异性朋友/竞争者"},
        {"名称": "六合", "类型": "天将", "说明": "好友/合作"}],
     "辅助": [
        {"名称": "朱雀", "类型": "天将", "说明": "沟通/争吵"},
        {"名称": "青龙", "类型": "天将", "说明": "贵人/帮助"}]},
    "子女": {"主要": [
        {"名称": "食神", "类型": "十神", "说明": "女儿/才华"},
        {"名称": "伤官", "类型": "十神", "说明": "儿子/创造力"},
        {"名称": "青龙", "类型": "天将", "说明": "喜悦/顺利"}],
     "辅助": [
        {"名称": "六合", "类型": "天将", "说明": "和谐/团圆"},
        {"名称": "天后", "类型": "天将", "说明": "女性/母亲"}]},
    "贵人": {"主要": [
        {"名称": "青龙", "类型": "天将", "说明": "贵人/机遇"},
        {"名称": "六合", "类型": "天将", "说明": "合作/帮助"}],
     "辅助": [
        {"名称": "正印", "类型": "十神", "说明": "靠山/长辈"}]},
    "桃花": {"主要": [
        {"名称": "天后", "类型": "天将", "说明": "女性/感情"},
        {"名称": "玄武", "类型": "天将", "说明": "暗昧/私情"}],
     "辅助": [
        {"名称": "太阴", "类型": "天将", "说明": "暗恋/隐藏"},
        {"名称": "六合", "类型": "天将", "说明": "结合/缘分"}]},
}

# 占问类型关键词映射
QUESTION_KEYWORDS = {
    "感情": ["感情", "爱情", "恋爱", "喜欢", "女友", "男友", "对象", "表白", "暗恋", "心动", "女生", "男生"],
    "婚姻": ["婚姻", "结婚", "离婚", "复婚", "妻子", "丈夫", "老婆", "老公", "嫁娶"],
    "事业": ["事业", "职业", "发展", "前途", "创业", "升职", "加薪"],
    "工作": ["工作", "上班", "辞职", "跳槽", "面试", "offer", "职场"],
    "考试": ["考试", "高考", "考研", "考公", "笔试", "答题", "成绩", "分数", "考"],
    "升学": ["升学", "上学", "学校", "大学", "录取", "志愿", "留学"],
    "财运": ["财运", "发财", "赚钱", "钱", "收入", "工资", "财富"],
    "投资": ["投资", "炒股", "股票", "基金", "理财", "投机"],
    "失物": ["失物", "丢", "找不到", "丢失", "遗失"],
    "健康": ["健康", "身体", "养生", "锻炼", "休息", "睡眠"],
    "疾病": ["疾病", "病", "医院", "治疗", "吃药", "手术", "症状"],
    "出行": ["出行", "旅行", "旅游", "出门", "去"],
    "搬家": ["搬家", "搬迁", "租房", "买房", "装修"],
    "官司": ["官司", "诉讼", "起诉", "法院", "律师", "法律"],
    "口舌": ["口舌", "是非", "吵架", "争吵", "骂", "矛盾"],
    "合作": ["合作", "合伙", "团队", "合同", "协议", "签约"],
    "父母": ["父母", "爸爸", "妈妈", "父亲", "母亲", "爹", "娘", "长辈"],
    "兄弟": ["兄弟", "朋友", "哥们", "闺蜜", "同学", "同事", "友谊"],
    "子女": ["子女", "孩子", "儿子", "女儿", "怀孕", "生育"],
    "贵人": ["贵人", "帮助", "扶持", "机遇", "机会"],
    "桃花": ["桃花", "缘分", "艳遇", "异性"],
}


def detect_question_type(question):
    """识别占问类型"""
    if not question:
        return "通用"
    for qtype, keywords in QUESTION_KEYWORDS.items():
        for kw in keywords:
            if kw in question:
                return qtype
    return "通用"


def get_leishen(question_type):
    """根据占问类型返回类神列表"""
    if question_type == "通用":
        return {
            "主要": [
                {"名称": "日干", "类型": "天干", "说明": "自己/操作主体"},
                {"名称": "日支", "类型": "地支", "说明": "对方/环境"}],
            "辅助": [
                {"名称": "初传", "类型": "三传", "说明": "当前爆发点/感"},
                {"名称": "末传", "类型": "三传", "说明": "收敛方向/操作结果"}]}
    return LEISHEN_TABLE.get(question_type, LEISHEN_TABLE.get("通用"))


def get_element_wangshuai(element, month_branch):
    """判断五行在当月的旺相休囚死"""
    month_elem = BRANCH_ELEMENT[month_branch]
    if element == month_elem:
        return "旺"
    elif ELEMENT_SHENG[month_elem] == element:
        return "相"
    elif ELEMENT_SHENG[element] == month_elem:
        return "休"
    elif ELEMENT_KE[element] == month_elem:
        return "囚"
    elif ELEMENT_KE[month_elem] == element:
        return "死"
    return "平"


def analyze_leishen(result, question_type):
    """分析类神在盘上的状态"""
    leishen_list = get_leishen(question_type)
    day_stem = result["基本信息"]["日干"]
    month_general = result["基本信息"]["月将"]
    generals = result["十二天将"]["排布"]
    kongwang = result["基本信息"]["旬空"]
    san = result["三传"]

    analysis = {"占问类型": question_type, "主要类神": [], "辅助类神": [], "综合判断": ""}

    for role in ["主要", "辅助"]:
        for ls in leishen_list[role]:
            name = ls["名称"]
            ltype = ls["类型"]
            info = {"名称": name, "类型": ltype, "说明": ls["说明"]}
            location = None
            element = None

            if ltype == "天将":
                for branch, general in generals.items():
                    if general == name:
                        location = branch
                        element = BRANCH_ELEMENT[branch]
                        break
            elif ltype == "十神":
                target_elements = []
                my_elem = STEM_ELEMENT[day_stem]
                if name in ["正财", "偏财"]:
                    target_elements = [ELEMENT_KE[my_elem]]
                elif name in ["正官", "七杀"]:
                    for e in ["木", "火", "土", "金", "水"]:
                        if ELEMENT_KE[e] == my_elem:
                            target_elements = [e]
                            break
                elif name in ["正印", "偏印"]:
                    for e in ["木", "火", "土", "金", "水"]:
                        if ELEMENT_SHENG[e] == my_elem:
                            target_elements = [e]
                            break
                elif name in ["食神", "伤官"]:
                    target_elements = [ELEMENT_SHENG[my_elem]]
                elif name in ["比肩", "劫财"]:
                    target_elements = [my_elem]
                for branch in BRANCHES:
                    if BRANCH_ELEMENT[branch] in target_elements:
                        location = branch
                        element = BRANCH_ELEMENT[branch]
                        break
            elif ltype == "神煞":
                if name == "驿马":
                    location = result["基本信息"]["驿马"]
                    element = BRANCH_ELEMENT[location]
                else:
                    location = "需手动定位"
            elif ltype == "天干":
                location = day_stem
                element = STEM_ELEMENT[day_stem]
            elif ltype == "地支":
                location = result["基本信息"]["日支"]
                element = BRANCH_ELEMENT[location]
            elif ltype == "三传":
                if name == "初传":
                    location = san["初传"]
                elif name == "末传":
                    location = san["末传"]
                element = BRANCH_ELEMENT[location] if location else None

            info["落宫"] = location
            info["五行"] = element
            if element and location and location != "需手动定位":
                info["旺衰"] = get_element_wangshuai(element, month_general)
            else:
                info["旺衰"] = "未知"
            info["空亡"] = location in kongwang if location and location != "需手动定位" else False

            status_parts = []
            if info.get("旺衰") in ["旺", "相"]:
                status_parts.append("能量充足")
            elif info.get("旺衰") in ["休", "囚", "死"]:
                status_parts.append("能量不足")
            if info.get("空亡"):
                status_parts.append("名实不符（需填实）")
            if location and location != "需手动定位":
                status_parts.append(f"在{location}宫")
            info["状态"] = "，".join(status_parts) if status_parts else "需手动分析"

            if role == "主要":
                analysis["主要类神"].append(info)
            else:
                analysis["辅助类神"].append(info)

    main_statuses = [ls["状态"] for ls in analysis["主要类神"]]
    if all("能量充足" in s and "名实不符" not in s for s in main_statuses):
        analysis["综合判断"] = f"占{question_type}，主要类神旺相不空，能量充足，操作空间大。但类神旺不等于一定成，操作权在人。"
    elif any("名实不符" in s for s in main_statuses):
        analysis["综合判断"] = f"占{question_type}，主要类神有空亡，名实不符，看起来有实际没有，需要填实（等时间或主动操作验证）。"
    elif any("能量不足" in s for s in main_statuses):
        analysis["综合判断"] = f"占{question_type}，主要类神能量不足，适合积累不宜冒进，等旺相窗口再操作。"
    else:
        analysis["综合判断"] = f"占{question_type}，类神状态混合，需结合具体操作判断。结构硬，操作软，阳主阴从。"
    return analysis


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


def calc_shehai_depth(day_stem, heaven_branch, earth_branch):
    """计算涉害深度（标准算法）
    从日干寄宫开始，顺时针数到天盘神的地盘位置，
    经过的地支中五行克日干的数量，即为涉害深度。
    克日干的五行=官杀（如日干木，金克木，申酉为官杀）
    """
    overcomes = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    stem_palace = STEM_TO_BRANCH[day_stem]
    day_element = STEM_ELEMENT[day_stem]
    # 找克日干的五行（官杀）：如日干木，金克木，ke_element=金
    ke_element = None
    for k, v in overcomes.items():
        if v == day_element:
            ke_element = k
            break

    start_idx = BRANCHES.index(stem_palace)
    end_idx = BRANCHES.index(earth_branch)

    depth = 0
    count = (end_idx - start_idx) % 12
    for i in range(1, count + 1):
        b = BRANCHES[(start_idx + i) % 12]
        if BRANCH_ELEMENT[b] == ke_element:
            depth += 1
    return depth


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
            # 标准算法：从日干寄宫数到天盘地盘位置，经过的克日干地支数
            best = None
            best_depth = -1
            for name, earth, heaven in bihe_list:
                depth = calc_shehai_depth(day_stem, heaven, earth)
                if depth > best_depth:
                    best_depth = depth
                    best = (name, earth, heaven)
            first = best[2]
            second = heaven_plate[first]
            third = heaven_plate[second]
            return (first, second, third, f"涉害法(深度{best_depth})")
        else:
            # 涉害法：无比和，取涉害深者
            best = None
            best_depth = -1
            for name, earth, heaven in xia_ke_shang:
                depth = calc_shehai_depth(day_stem, heaven, earth)
                if depth > best_depth:
                    best_depth = depth
                    best = (name, earth, heaven)
            first = best[2]
            second = heaven_plate[first]
            third = heaven_plate[second]
            return (first, second, third, f"涉害法(深度{best_depth})")

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
    elif method.startswith("涉害法"):
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


# ==================== 年命行年 ====================

def get_nianming(birth_year):
    """计算年命（出生年份地支）"""
    # 天干地支纪年：公元4年为甲子年
    stem_idx = (birth_year - 4) % 10
    branch_idx = (birth_year - 4) % 12
    return STEMS[stem_idx] + BRANCHES[branch_idx], BRANCHES[branch_idx]


def get_xingnian(birth_year, current_year, gender="男"):
    """计算行年
    男命：从寅起，一岁在寅，顺行
    女命：从申起，一岁在申，逆行
    """
    age = current_year - birth_year
    if gender == "男":
        # 男命顺行，一岁在寅（index=2）
        start_idx = 2
        xingnian_idx = (start_idx + age - 1) % 12
    else:
        # 女命逆行，一岁在申（index=8）
        start_idx = 8
        xingnian_idx = (start_idx - (age - 1)) % 12
    return BRANCHES[xingnian_idx], age


# ==================== 主排盘函数 ====================

def paipan(year, month, day, hour, question="", birth_year=None, gender="男"):
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

    # 6. 年命行年（如果提供了出生年份）
    if birth_year:
        nianming_ganzhi, nianming_branch = get_nianming(birth_year)
        xingnian_branch, age = get_xingnian(birth_year, year, gender)
        result["基本信息"]["年命"] = f"{nianming_ganzhi}（{nianming_branch}）"
        result["基本信息"]["行年"] = f"{xingnian_branch}（{age}岁）"
        result["基本信息"]["性别"] = gender

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

    # 12. 类神分析（根据占问类型自动识别）
    question_type = detect_question_type(question)
    result["类神分析"] = analyze_leishen(result, question_type)

    # 13. 生命论解读
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
    if '年命' in info:
        print(f"  年命：{info['年命']}")
        print(f"  行年：{info['行年']}")
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

    # 类神分析
    if "类神分析" in result:
        ls = result["类神分析"]
        print(f"\n【类神分析】（占问类型：{ls['占问类型']}）")
        print(f"  主要类神：")
        for item in ls["主要类神"]:
            loc = item.get("落宫", "?")
            ws = item.get("旺衰", "?")
            kw_flag = "空亡" if item.get("空亡") else "不空"
            print(f"    - {item['名称']}（{item['说明']}）：{loc}宫，{ws}，{kw_flag}，{item['状态']}")
        if ls["辅助类神"]:
            print(f"  辅助类神：")
            for item in ls["辅助类神"]:
                loc = item.get("落宫", "?")
                ws = item.get("旺衰", "?")
                kw_flag = "空亡" if item.get("空亡") else "不空"
                print(f"    - {item['名称']}（{item['说明']}）：{loc}宫，{ws}，{kw_flag}")
        print(f"  综合判断：{ls['综合判断']}")

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
        question = sys.argv[5] if len(sys.argv) > 5 and not sys.argv[5].startswith("--") else ""

        # 解析可选参数
        birth_year = None
        gender = "男"
        for i, arg in enumerate(sys.argv):
            if arg.startswith("--birth="):
                birth_year = int(arg.split("=")[1])
            elif arg.startswith("--gender="):
                gender = arg.split("=")[1]

        result = paipan(year, month, day, hour, question, birth_year, gender)
        print_paipan(result)

        if "--json" in sys.argv:
            print("\n\n=== JSON 输出 ===")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法：python liuren_paipan.py 年 月 日 时 [占问内容] [--birth=出生年] [--gender=男/女] [--json]")
        print("示例：python liuren_paipan.py 2026 9 2 16 感情")
        print("示例：python liuren_paipan.py 2026 8 18 2 事业 --birth=2008 --gender=男 --json")

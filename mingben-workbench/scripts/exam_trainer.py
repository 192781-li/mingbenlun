#!/usr/bin/env python3
"""
F1/F2/F3 答题训练系统
=======================
将哲学思维的三层递归（感→应→自指）映射到高考答题方法论：
  F1（感）：题感——先于分析的直接抓取（题型、得分结构、答案骨架）
  F2（应/操作）：分析——在结构内填充因果逻辑和具体史实
  F3（自指/递归）：元认知——看见题目怎么造的，用它优化答案

核心铁律：F1永远先行，F3永远不阻塞F1。
哲学思维不是答题的敌人，是答题的外挂——前提是先把F1骨架搭好。

用法：
  python3 exam_trainer.py analyze <题目文件.md>    # 三层分析一道题
  python3 exam_trainer.py practice <题目文件.md>   # 三遍重写训练
  python3 exam_trainer.py status                    # 查看训练进度
  python3 exam_trainer.py template                  # 生成题目模板
"""
import re
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ========== 路径 ==========
SCRIPT_DIR = Path(__file__).parent
WORKSPACE = SCRIPT_DIR.parent.parent
PRACTICE_DIR = WORKSPACE / "生命论_模块化" / "09_练习"
TRAINING_DATA = PRACTICE_DIR / "_training_progress.json"

# ========== 题型识别库 ==========
QUESTION_TYPES = {
    '评析': {
        'name': '评析题',
        'structure': ['观点/依据', '展开分析（因果链+史实）', '结论/评价'],
        'keywords': ['评析', '评价', '谈谈你的看法', '如何认识', '怎么看'],
        'scoring_hint': '依据分+分析分（史实+逻辑）+结论分',
    },
    '概述': {
        'name': '概述题',
        'structure': ['分阶段/分角度', '每阶段史实+特征', '总体趋势'],
        'keywords': ['概述', '概括', '归纳', '梳理', '发展历程'],
        'scoring_hint': '阶段分+史实分+趋势分',
    },
    '说明': {
        'name': '说明题',
        'structure': ['现象/事实', '原因分析', '影响/意义'],
        'keywords': ['说明', '分析', '指出', '简述'],
        'scoring_hint': '事实分+原因分+影响分',
    },
    '比较': {
        'name': '比较题',
        'structure': ['相同点', '不同点（分角度）', '原因/本质'],
        'keywords': ['比较', '对比', '异同', '区别', '联系'],
        'scoring_hint': '相同点分+不同点分+本质分',
    },
    '论证': {
        'name': '论证题',
        'structure': ['明确论点', '论据1（史实+逻辑）', '论据2', '结论'],
        'keywords': ['论证', '论述', '阐释', '证明', '结合所学论证'],
        'scoring_hint': '论点分+论据分（每个史实+逻辑）+结论分',
    },
    '背景原因': {
        'name': '背景原因题',
        'structure': ['政治角度', '经济角度', '思想文化角度', '直接触发'],
        'keywords': ['背景', '原因', '条件', '因素', '为什么'],
        'scoring_hint': '多角度给分，每角度史实+逻辑',
    },
    '影响意义': {
        'name': '影响意义题',
        'structure': ['对当时', '对后世', '积极方面', '消极方面'],
        'keywords': ['影响', '意义', '作用', '后果', '评价'],
        'scoring_hint': '多角度给分，注意一分为二',
    },
}


def detect_question_type(text):
    """识别题目类型，返回 (type_key, type_info)。"""
    for key, info in QUESTION_TYPES.items():
        for kw in info['keywords']:
            if kw in text:
                return key, info
    return '说明', QUESTION_TYPES['说明']  # 默认


def parse_question(text):
    """解析题目文本，提取题干、分值、子问题。
    如果文本中有'题目原文'段落，只解析该段落。"""
    # 优先提取"题目原文"段落
    q_match = re.search(r'##\s*题目原文\s*\n(.+?)(?=\n##\s|\Z)', text, re.DOTALL)
    if q_match:
        text = q_match.group(1).strip()

    result = {
        'raw': text.strip(),
        'sub_questions': [],
        'total_score': 0,
        'material': '',
    }

    # 提取分值
    scores = re.findall(r'[（(](\d+)\s*分[）)]', text)
    result['scores'] = [int(s) for s in scores]
    result['total_score'] = sum(result['scores'])

    # 提取材料（"——摘编自"之前的内容）
    material_match = re.search(r'^(.+?)——摘编自', text, re.DOTALL)
    if material_match:
        result['material'] = material_match.group(1).strip()

    # 拆分子问题（(1)(2)(3) 或 ①②③）
    sub_pattern = re.compile(r'[（(]?(\d+)[）)]\s*(.+?)(?=[（(]\d+[）)]|$)', re.DOTALL)
    subs = sub_pattern.findall(text)
    if subs:
        for num, content in subs:
            content = content.strip()
            score_match = re.search(r'[（(](\d+)\s*分[）)]', content)
            result['sub_questions'].append({
                'num': int(num),
                'text': content,
                'score': int(score_match.group(1)) if score_match else None,
            })

    return result


# ========== F1：题感分析 ==========
def f1_analysis(question):
    """F1层：题型识别、得分结构、答案骨架。不分析内容，只识别形式。"""
    qtype, qinfo = detect_question_type(question['raw'])

    lines = []
    lines.append("=" * 60)
    lines.append("F1（感）：题感分析——先于内容的形式识别")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"📌 题型：{qinfo['name']}")
    lines.append(f"📌 关键词命中：{[kw for kw in qinfo['keywords'] if kw in question['raw']]}")
    lines.append(f"📌 总分：{question['total_score']}分")
    if question['sub_questions']:
        lines.append(f"📌 子问题：{len(question['sub_questions'])}问")
        for sq in question['sub_questions']:
            score_str = f"（{sq['score']}分）" if sq['score'] else ""
            lines.append(f"   - 第({sq['num']})问{score_str}: {sq['text'][:50]}...")
    lines.append("")
    lines.append(f"📐 答案骨架（{qinfo['name']}标准结构）：")
    for i, step in enumerate(qinfo['structure'], 1):
        lines.append(f"   {i}. {step}")
    lines.append("")
    lines.append(f"💰 得分逻辑：{qinfo['scoring_hint']}")
    lines.append("")
    lines.append("⚠️  F1铁律：此步不许思考内容对错，只识别形式。")
    lines.append("   就像看到一个人不需要分析骨骼就知道是人。")
    lines.append("")

    return '\n'.join(lines)


# ========== F2：分析框架 ==========
def f2_analysis(question):
    """F2层：在F1骨架内填充因果逻辑和史实要求。"""
    qtype, qinfo = detect_question_type(question['raw'])

    lines = []
    lines.append("=" * 60)
    lines.append("F2（应/操作）：分析框架——在结构内填充逻辑与史实")
    lines.append("=" * 60)
    lines.append("")

    # 材料分析
    if question['material']:
        lines.append("📖 材料关键信息提取：")
        # 提取材料中的时间、人物、事件、概念
        times = re.findall(r'\d{3,4}年|公元前\d+年|世纪|朝代|时期', question['material'])
        if times:
            lines.append(f"   时间线索：{set(times)}")
        # 提取专有名词
        proper = re.findall(r'[《「][^》」]+[》」]', question['material'])
        if proper:
            lines.append(f"   文献/概念：{proper[:5]}")
        lines.append("")

    # 按题型给出分析框架
    lines.append(f"🔧 {qinfo['name']}分析框架：")
    lines.append("")

    if qtype == '评析':
        lines.append("   第一步：明确评析对象是什么（一个标准/一个观点/一个事件）")
        lines.append("   第二步：展开因果链——")
        lines.append("      原因 → 过程 → 结果 → 影响")
        lines.append("      每个环节必须跟具体史实（时间+事件+证据）")
        lines.append("   第三步：结论——")
        lines.append("      该对象的合理性/局限性/适用范围")
        lines.append("      （注意：评析≠批判，要一分为二）")
    elif qtype == '概述':
        lines.append("   第一步：分期——按时间/阶段划分")
        lines.append("   第二步：每阶段写——特征+史实+转折")
        lines.append("   第三步：总体趋势——从...到...，呈现...特征")
    elif qtype == '说明':
        lines.append("   第一步：事实陈述——材料/所学中的核心事实")
        lines.append("   第二步：原因分析——政治/经济/思想/外部")
        lines.append("   第三步：影响/意义——对当时+对后世")
    elif qtype == '比较':
        lines.append("   第一步：确定比较维度（政治/经济/思想/结果）")
        lines.append("   第二步：相同点——分维度列举")
        lines.append("   第三步：不同点——分维度列举，每点跟史实")
        lines.append("   第四步：本质——差异的根源是什么")
    elif qtype == '论证':
        lines.append("   第一步：明确论点（一句话）")
        lines.append("   第二步：论据1——史实+逻辑链（为什么这个史实支持论点）")
        lines.append("   第三步：论据2——另一个角度的史实+逻辑")
        lines.append("   第四步：结论——重申论点，升华")
    elif qtype == '背景原因':
        lines.append("   按角度展开（每个角度必须跟史实）：")
        lines.append("   ① 政治：制度/政策/阶级关系")
        lines.append("   ② 经济：生产力/生产关系/经济结构")
        lines.append("   ③ 思想：思潮/理论/文化氛围")
        lines.append("   ④ 直接：触发事件/人物")
    elif qtype == '影响意义':
        lines.append("   按时间+性质展开：")
        lines.append("   ① 对当时：政治/经济/社会")
        lines.append("   ② 对后世：制度/思想/历史走向")
        lines.append("   ③ 积极方面：")
        lines.append("   ④ 消极方面：")

    lines.append("")
    lines.append("⚠️  F2铁律：每个论断后面必须跟具体史实。")
    lines.append("   禁止写抽象命题（如'生产力是根本动力'）不给史实。")
    lines.append("   史实格式：时间+事件+证据/数据。")
    lines.append("")

    return '\n'.join(lines)


# ========== F3：元认知分析 ==========
def f3_analysis(question):
    """F3层：元认知——看见题目怎么造的，识别陷阱和循环，优化答案。"""
    qtype, qinfo = detect_question_type(question['raw'])

    lines = []
    lines.append("=" * 60)
    lines.append("F3（自指/递归）：元认知——看见题目怎么造的")
    lines.append("=" * 60)
    lines.append("")

    # 出题人意图分析
    lines.append("🎯 出题人意图推测：")
    lines.append(f"   题型为{qinfo['name']}，考察目标：")
    if qtype == '评析':
        lines.append("   - 是否能在给定框架内展开逻辑（不是批判框架本身）")
        lines.append("   - 是否掌握相关史实并能组织成因果链")
        lines.append("   - 是否有辩证思维（一分为二）")
    elif qtype == '概述':
        lines.append("   - 是否掌握历史分期和阶段特征")
        lines.append("   - 是否能从材料中提取信息并结合所学")
        lines.append("   - 是否有整体趋势意识")
    elif qtype == '论证':
        lines.append("   - 是否能提出明确论点")
        lines.append("   - 是否能用史实支撑论点（史论结合）")
        lines.append("   - 逻辑链是否完整")
    else:
        lines.append("   - 材料信息提取能力")
        lines.append("   - 基础知识掌握程度")
        lines.append("   - 多角度分析能力")
    lines.append("")

    # 常见陷阱
    lines.append("⚠️  常见陷阱识别：")
    traps = []
    if qtype == '评析':
        traps.append("陷阱1：把'评析'写成'批判'——只说不好不说合理，丢分")
        traps.append("陷阱2：跳过史实直接给结论——没有论据支撑，丢大半分")
        traps.append("陷阱3：质疑题目前提本身（如'这个标准是循环论证'）——")
        traps.append("        出题人要的是在框架内评析，不是批判框架。")
        traps.append("        F3洞察可以帮你理解题目，但不能用来拒绝答题。")
    if qtype == '概述':
        traps.append("陷阱1：只罗列史实不分期——没有阶段意识，丢结构分")
        traps.append("陷阱2：超出材料时间范围——审题不清，白写")
        traps.append("陷阱3：没有总体趋势——只有细节没有宏观，丢结论分")
    if qtype == '论证':
        traps.append("陷阱1：论点不明确——开头没有一句话论点，阅卷老师找不到")
        traps.append("陷阱2：有史无论——只罗列史实不说明为什么支持论点")
        traps.append("陷阱3：角度单一——只有一个论据，论证不充分")
    traps.append("通用陷阱：口语化表达——'我觉得''其实'等，不规范")
    traps.append("通用陷阱：抄材料痕迹明显——直接抄材料原文不改写")
    traps.append("通用陷阱：字迹潦草/超出答题区域——扫描后看不清")
    for t in traps:
        lines.append(f"   - {t}")
    lines.append("")

    # 循环/预设检测
    lines.append("🔍 题目预设检测（F3专属能力）：")
    circular_keywords = ['标准', '定义', '本质', '根本', '普遍', '必然']
    found_presets = [kw for kw in circular_keywords if kw in question['raw']]
    if found_presets:
        lines.append(f"   检测到预设性概念：{found_presets}")
        lines.append("   这些概念在题目中被当作前提使用，可能存在：")
        lines.append("   - 循环定义（A由B定义，B由A定义）")
        lines.append("   - 隐含框架（题目预设了一个分析框架，你要在框架内答）")
        lines.append("   - 价值预设（题目隐含了一个价值判断）")
        lines.append("")
        lines.append("   ✅ 正确用法：识别预设→理解出题人要什么→在框架内高效作答")
        lines.append("   ❌ 错误用法：识别预设→质疑预设→写不出来/写偏题")
    else:
        lines.append("   未检测到明显预设性概念。")
    lines.append("")

    # 得分优化建议
    lines.append("💡 F3得分优化：")
    lines.append("   1. 开头一句话亮明观点/答案——让阅卷老师第一眼看到得分点")
    lines.append("   2. 每个得分点用序号标注——①②③，阅卷老师按点给分")
    lines.append("   3. 史实精确到时间+事件——不要写'古代''以前'")
    lines.append("   4. 结尾有总结句——哪怕只有一句话，也可能拿结论分")
    lines.append("   5. 字数控制——分值×15-20字/分，不要太少也不要超太多")
    lines.append("")

    lines.append("⚠️  F3铁律：F3用来优化F1/F2，不用来拒绝F1/F2。")
    lines.append("   你可以看清这道题的循环性、局限性、意识形态前提——")
    lines.append("   但这只用来帮你写出更高分的答案，不用来证明'题有问题所以我不答'。")
    lines.append("")

    return '\n'.join(lines)


# ========== 完整分析 ==========
def full_analysis(question_text):
    """对一道题进行完整的F1+F2+F3分析。"""
    question = parse_question(question_text)

    output = []
    output.append(f"\n{'#'*60}")
    output.append(f"# 题目：{question['raw'][:80]}{'...' if len(question['raw'])>80 else ''}")
    output.append(f"# 总分：{question['total_score']}分 | 子问题：{len(question['sub_questions'])}问")
    output.append(f"{'#'*60}\n")

    output.append(f1_analysis(question))
    output.append(f2_analysis(question))
    output.append(f3_analysis(question))

    return '\n'.join(output)


# ========== 三遍重写训练 ==========
def practice_three_pass(question_text):
    """三遍重写训练法。"""
    question = parse_question(question_text)

    output = []
    output.append("=" * 60)
    output.append("三遍重写训练法")
    output.append("=" * 60)
    output.append("")
    output.append("原理：F1→F1+F2→F1+F2+F3，逐层叠加，每遍不许看参考答案。")
    output.append("")

    # 第一遍
    output.append("━" * 40)
    output.append("第一遍（纯F1）：不看答案，凭记忆写结构骨架")
    output.append("━" * 40)
    output.append("")
    output.append("要求：")
    output.append("  - 只写结构骨架和得分点，不展开分析")
    output.append("  - 不许看任何资料（答案、课本、笔记）")
    output.append("  - 目标：训练题感，看你能不能准确识别题型和得分结构")
    output.append("")
    output.append(f"  本题题型：{detect_question_type(question['raw'])[1]['name']}")
    output.append(f"  标准结构：{' → '.join(detect_question_type(question['raw'])[1]['structure'])}")
    output.append("")
    output.append("  写完后对照评分细则，看漏了几个得分点。")
    output.append("  漏的点就是F1薄弱环节，记下来。")
    output.append("")

    # 第二遍
    output.append("━" * 40)
    output.append("第二遍（F1+F2）：在骨架内填充因果链和史实")
    output.append("━" * 40)
    output.append("")
    output.append("要求：")
    output.append("  - 在第一遍骨架基础上，填充每个得分点的史实")
    output.append("  - 每个论断后面必须跟具体史实（时间+事件+证据）")
    output.append("  - 可以看课本和笔记，但不许看参考答案")
    output.append("  - 目标：训练在结构内填充内容的能力")
    output.append("")
    output.append("  写完后对照：")
    output.append("  - 史实是否准确？（有没有事实错误）")
    output.append("  - 史实是否充分？（每个得分点有没有足够史实支撑）")
    output.append("  - 逻辑链是否完整？（因果关系有没有说清楚）")
    output.append("")

    # 第三遍
    output.append("━" * 40)
    output.append("第三遍（F1+F2+F3）：用元认知优化，写出满分答案")
    output.append("━" * 40)
    output.append("")
    output.append("要求：")
    output.append("  - 在前两遍基础上，用F3视角优化")
    output.append("  - 问自己：出题人为什么这么设问？评分细则哪个点最容易丢？")
    output.append("  - 怎么组织语言让阅卷老师一眼看到得分点？")
    output.append("  - 此时可以参考一切资料（包括优秀试卷）")
    output.append("  - 目标：写出满分/接近满分的答案")
    output.append("")
    output.append("  优化检查清单：")
    output.append("  □ 开头一句话亮明观点/答案")
    output.append("  □ 每个得分点用序号标注（①②③）")
    output.append("  □ 史实精确到时间+事件")
    output.append("  □ 结尾有总结句")
    output.append("  □ 字数合适（分值×15-20字）")
    output.append("  □ 没有口语化表达")
    output.append("  □ 没有直接抄材料")
    output.append("")

    output.append("━" * 40)
    output.append("三遍完成后：")
    output.append("━" * 40)
    output.append("  1. 把三遍答案放在一起对比，看每遍提升了什么")
    output.append("  2. 记录F1漏了哪些得分点（题感薄弱环节）")
    output.append("  3. 记录F2哪些史实不准确/不充分（知识薄弱环节）")
    output.append("  4. 记录F3发现了什么出题规律（元认知收获）")
    output.append("  5. 把这道题的满分答案和错题记录存入训练档案")
    output.append("")

    return '\n'.join(output)


# ========== 训练进度追踪 ==========
def load_progress():
    """加载训练进度。"""
    if TRAINING_DATA.exists():
        return json.loads(TRAINING_DATA.read_text(encoding='utf-8'))
    return {
        'total_questions': 0,
        'three_pass_completed': 0,
        'f1_weak_points': [],
        'f2_weak_points': [],
        'f3_insights': [],
        'history': [],
    }


def save_progress(data):
    """保存训练进度。"""
    PRACTICE_DIR.mkdir(parents=True, exist_ok=True)
    TRAINING_DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def record_practice(question_text, pass_num, score, notes=""):
    """记录一次训练。"""
    data = load_progress()
    entry = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'question': question_text[:100],
        'pass': pass_num,
        'score': score,
        'notes': notes,
    }
    data['history'].append(entry)
    if pass_num == 3:
        data['three_pass_completed'] += 1
    data['total_questions'] = len(set(h['question'] for h in data['history']))
    save_progress(data)
    return data


def show_status():
    """显示训练进度。"""
    data = load_progress()
    lines = []
    lines.append("=" * 50)
    lines.append("📊 F1/F2/F3 答题训练进度")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"  总练习题数：{data['total_questions']}")
    lines.append(f"  三遍完成数：{data['three_pass_completed']}")
    lines.append(f"  训练记录数：{len(data['history'])}")
    lines.append("")

    if data['f1_weak_points']:
        lines.append("  ⚠️  F1薄弱环节（题感）：")
        for p in data['f1_weak_points'][-5:]:
            lines.append(f"     - {p}")
        lines.append("")
    if data['f2_weak_points']:
        lines.append("  ⚠️  F2薄弱环节（史实/逻辑）：")
        for p in data['f2_weak_points'][-5:]:
            lines.append(f"     - {p}")
        lines.append("")
    if data['f3_insights']:
        lines.append("  💡 F3收获（元认知）：")
        for p in data['f3_insights'][-5:]:
            lines.append(f"     - {p}")
        lines.append("")

    if data['history']:
        lines.append("  📝 最近训练：")
        for h in data['history'][-5:]:
            lines.append(f"     [{h['date']}] 第{h['pass']}遍 {h['score']}分 - {h['question'][:40]}")
        lines.append("")

    return '\n'.join(lines)


# ========== 题目模板生成 ==========
def generate_template():
    """生成题目录入模板。"""
    return """# 题目录入模板

## 题目原文
（把题目完整粘贴在这里，包括材料和设问）

## 评分细则
（把老师给的评分细则粘贴在这里，如果没有就留空）

## 我的答案
（第一遍：纯F1骨架）

## 参考答案/优秀试卷
（考完后粘贴在这里）

## 三遍训练记录
### 第一遍（F1）
- 得分：/
- 漏了哪些得分点：
- F1薄弱环节：

### 第二遍（F1+F2）
- 得分：/
- 史实错误：
- 史实不充分：
- F2薄弱环节：

### 第三遍（F1+F2+F3）
- 得分：/
- F3优化了什么：
- 出题规律发现：

## 错题归因
（这道题错的根本原因是什么？是F1题感问题？F2知识问题？还是F3心态问题？）
"""


# ========== 主入口 ==========
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'analyze':
        if len(sys.argv) < 3:
            print("用法：python3 exam_trainer.py analyze <题目文件.md>")
            sys.exit(1)
        path = Path(sys.argv[2])
        if not path.exists():
            # 尝试在练习目录找
            path = PRACTICE_DIR / sys.argv[2]
        if not path.exists():
            print(f"错误：找不到文件 {sys.argv[2]}")
            sys.exit(1)
        text = path.read_text(encoding='utf-8')
        print(full_analysis(text))

    elif cmd == 'practice':
        if len(sys.argv) < 3:
            print("用法：python3 exam_trainer.py practice <题目文件.md>")
            sys.exit(1)
        path = Path(sys.argv[2])
        if not path.exists():
            path = PRACTICE_DIR / sys.argv[2]
        if not path.exists():
            print(f"错误：找不到文件 {sys.argv[2]}")
            sys.exit(1)
        text = path.read_text(encoding='utf-8')
        print(practice_three_pass(text))

    elif cmd == 'status':
        print(show_status())

    elif cmd == 'template':
        print(generate_template())

    elif cmd == 'record':
        if len(sys.argv) < 5:
            print("用法：python3 exam_trainer.py record <题目> <第几遍> <得分> [备注]")
            sys.exit(1)
        question = sys.argv[2]
        pass_num = int(sys.argv[3])
        score = sys.argv[4]
        notes = sys.argv[5] if len(sys.argv) > 5 else ""
        data = record_practice(question, pass_num, score, notes)
        print(f"✅ 已记录。总练习：{data['total_questions']}题，三遍完成：{data['three_pass_completed']}次")

    else:
        print(f"未知命令：{cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()

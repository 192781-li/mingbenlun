#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金句提纯-归位-选择 正式管线（可重复运行）。
输入：docs/raw_materials/金句录_最终归位.json（已是纯用户块、带波次/时间/概念锚）
输出：
  - 金句_五波归位样稿.md     每波Top代表作（给人读的净稿）
  - 金句录_金句候选.json     全部通过提纯门、带金句力分的候选（供将来精修）
根本判据：用户的话是【说】出来的（语音转文字，一逗到底+卡顿重复+语气词），
         AI是【写】出来的（顿号并列、分号引号破折号、工整对仗）。
"""
import json
import re
from collections import defaultdict

SRC = 'docs/raw_materials/金句录_最终归位.json'
OUT_MD = 'docs/notes/时间线/金句_五波归位样稿.md'
OUT_JSON = 'docs/raw_materials/金句录_金句候选.json'

# —— 真人语音指纹（多字语气词/卡顿/粗口；刻意不含搞/弄/整等会误判的单字）——
REAL_ORAL = ['我操', '他妈', '傻逼', '牛逼', '狗屎', '啥', '咋', '呗', '嘛', '哎', '嗯', '呃',
             '呀', '哦', '我觉得', '我认为', '我感觉', '我突然', '我跟你', '你懂', '对吧',
             '是不是', '说白了', '反正', '就是说', '我靠', '卧槽', '鸡毛', '扯淡', '妈的',
             '咱们', '你别', '你就', '我就', '这这', '那个那个', '然后呢', '明摆', '鸡巴', '唐了',
             '的的', '我我', '就是就是', '然后然后', '其实', '真的', '我想', '咱']
# —— 事务性指令（不是金句）——
TASK = ['帮我', '给我生成', '你给我', '给我弄', '弄到桌面', '设置一个', '定时任务', '锁死',
        '别乱搞', '生成一', '改一下', '总结一下', '填一下', '你就先', '发给我', '头像', '打印',
        '下载', '上传', '截图', '你查', '搜一下', '等一下', '先别', '整理一下', '你看一下',
        'V12.', '230万字', '这一编', '包含三章', '无删减', '不做删减', '全部保留']
# —— 日常碎句（无概念含量时剔除）——
DAILY = ['分手', '那个孩子', '比赛', '上课', '作业', '考试', '座位', '吃饭', '睡觉', '洗澡',
         '头发', '衣服', '平板', '电脑坏', '快递', '外卖', '痒', '痘', '皮肤', '药']
CORE = ['生命', '操作', '自指', '反自指', '在感', '明性', '缄默', '异化', '资本', '寄生', '惯性',
        '阴阳', '践演', '迁演', '实体', '本质', '根本', '历史', '人民', '阶级', '革命', '解放',
        '自由', '真理', '主体', '唯物', '唯心', '辩证', '矛盾', '实践', '感性', '理性', '意识',
        '符号', '意识形态', '名实', '遮蔽', '规训', '闭环', '递归', '阳主阴从', '劳动', '生产力',
        '必然', '自由人', '联合体', '文明', '存在']
URL_RE = re.compile(r'(https?://|\[image\]|\[图片\]|byteimg|x-expires|tos-cn)')
PREFIX_RE = re.compile(r'^[\s◦•·\-\*>]+')


def real_oral(t):
    return [o for o in REAL_ORAL if o in t]


def idea(t):
    return sum(1 for c in CORE if c in t)


def is_noise(t):
    if URL_RE.search(t):
        return True
    if PREFIX_RE.match(t):
        return True
    if len(t) < 12:
        return True
    return False


def written_punct(t):
    return (t.count('、') + t.count('；') + t.count('"') + t.count('"') + t.count('“')
            + t.count('”') + t.count('——') * 2 + t.count('「') + t.count('」') + t.count('《'))


def is_pasted_ai(t):
    """无真人语音指纹、却呈书面写作特征 -> 判为用户粘贴的AI成稿。"""
    if real_oral(t):
        return False
    if t.count('、') >= 3:                 # 顿号并列≥3
        return True
    if written_punct(t) >= 4:             # 书面标点密集
        return True
    if len(t) >= 45 and t.count('，') <= 1:  # 超长却几乎不口语停顿
        return True
    return False


def is_task(t):
    return any(x in t for x in TASK)


def is_daily(t):
    return sum(1 for x in DAILY if x in t) >= 1 and idea(t) == 0


def power(t):
    s = idea(t) * 3
    for k in ['不是', '而是', '从来', '一切', '所有', '根本', '本质', '恰恰', '正是', '无非',
              '必然', '只能', '不可', '必须', '一旦', '永远', '说白了', '真相', '决定', '统一',
              '同一', '颠倒']:
        if k in t:
            s += 1
    if 28 <= len(t) <= 115:
        s += 4
    elif 18 <= len(t) < 140:
        s += 2
    if '不是' in t and '而是' in t:
        s += 3
    if real_oral(t):
        s += 1
    return s


def written_score(t):
    """书面成稿嫌疑度：越高越像粘贴的AI文本。"""
    s = 0
    s += min(t.count('、'), 4)
    s += written_punct(t)
    s += t.count('，') <= 1 and len(t) >= 40
    # AI惯用书面连接/结构词
    for w in ['本应', '旨在', '据此', '由此', '综上', '然而', '因此', '值得注意', '不难发现',
              '具体而言', '换言之', '与此同时', '不是靠', '理论悲剧', '分析框架', '本源答案',
              '可靠路径', '破局路径', '高阶', '涌现', '统摄', '范式', '协同', '耦合']:
        if w in t:
            s += 1
    return s


def tier(t):
    """A=确凿口述(带语音指纹) B=完整口述理论(无指纹但不成稿) C=疑似粘贴AI成稿"""
    if real_oral(t):
        return 'A'
    if written_score(t) >= 5:
        return 'C'
    return 'B'


def main():
    d = json.load(open(SRC))
    qs = d['quotes']
    buckets = defaultdict(list)
    reason = defaultdict(int)
    for q in qs:
        t = q['text']
        if is_noise(t):
            reason['噪声'] += 1; continue
        if q.get('AI腔分', 0) >= 2 or is_pasted_ai(t):
            reason['AI成稿'] += 1; continue
        if is_task(t):
            reason['事务'] += 1; continue
        if is_daily(t):
            reason['日常碎句'] += 1; continue
        if idea(t) == 0:
            reason['无概念'] += 1; continue
        q['金句力'] = power(t)
        q['档位'] = tier(t)
        buckets[q['波次']].append(q)

    order = ['零·奠基潜伏', '一波·现象(缄默意识)', '过渡一→二', '二波·体系整合', '三波·形式化',
             '过渡三→四', '四波·存在论奠基(日期待考)', '五波·文档固化', '待定·无时间戳']
    out = ['# 北原慢热金句·五波归位样稿（分档净稿）\n',
           '> A档=带语音指纹的确凿本人口述（样稿主体）；B档=成熟完整的口述理论；',
           '> C档=疑似粘贴AI成稿，不进样稿、只在JSON打标待辨。根本判据：话是"说"出来的，不是"写"出来的。\n']
    all_cand = []
    for w in order:
        items = sorted(buckets.get(w, []), key=lambda x: (-({'A': 2, 'B': 1, 'C': 0}[x['档位']]), -x['金句力']))
        total = sum(1 for q in qs if q['波次'] == w)
        all_cand.extend(items)
        na = sum(1 for q in items if q['档位'] == 'A')
        nb = sum(1 for q in items if q['档位'] == 'B')
        nc = sum(1 for q in items if q['档位'] == 'C')
        out.append(f'\n---\n\n## {w}（全{total}｜A确凿口述{na}·B完整理论{nb}·C疑粘贴{nc}）\n')
        seen = set(); n = 0
        for q in items:
            if q['档位'] == 'C':
                continue  # C档不进样稿
            if q['text'] in seen:
                continue
            seen.add(q['text'])
            c = '、'.join(q['概念锚'][:3])
            tag = '' if q['档位'] == 'A' else '〔B·完整口述〕'
            out.append(f'> {q["text"]}\n> \u3000\u3000——{q["time"][:16]}〔{q["对话"]}〕{tag}'
                       f'{("｜" + c) if c else ""}\n')
            n += 1
            if n >= 7:
                break
    open(OUT_MD, 'w').write('\n'.join(out))
    with open(OUT_JSON, 'w') as f:
        json.dump({'total': len(all_cand), 'quotes': all_cand}, f, ensure_ascii=False, indent=2)
    print('剔除统计：', dict(reason))
    print(f'金句候选总数：{len(all_cand)}  '
          f'A={sum(1 for q in all_cand if q["档位"]=="A")} '
          f'B={sum(1 for q in all_cand if q["档位"]=="B")} '
          f'C={sum(1 for q in all_cand if q["档位"]=="C")}')
    for w in order:
        print(f'  {w}: {len(buckets.get(w, []))}')
    print(f'\n-> {OUT_MD}\n-> {OUT_JSON}')


if __name__ == '__main__':
    main()

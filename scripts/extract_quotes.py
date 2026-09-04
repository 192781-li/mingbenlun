#!/usr/bin/env python3
"""
北原慢热金句系统提取器
从全库所有文件中提取用户原话，去重，分类，输出完整金句录
"""
import os
import re
import json
from pathlib import Path
from collections import defaultdict

REPO = Path("/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun")

# 所有可能包含用户原话的文件模式
QUOTE_PATTERNS = [
    # 聊天记录格式：**用户(时间)：**
    (r'\*\*用户\([^)]+\)：\*\*\s*\n(.*?)(?=\n\*\*智能体|\n\*\*用户|\Z)', 'chat'),
    # 闪光点格式：- **原话**：...
    (r'\*\*原话\*\*[：:]\s*(.+?)(?=\n\s*\n|\n- |\Z)', 'flashpoint'),
    # 引用块：> ...
    (r'^>\s*(.+?)$', 'blockquote'),
    # 标注格式：用户原话：...
    (r'用户原话[：:]\s*(.+?)(?=\n|$)', 'labeled'),
    # 北原慢热说：...
    (r'北原慢热[^：]*[：:]\s*(.+?)(?=\n|$)', 'named'),
]

def extract_from_file(filepath):
    """从单个文件提取所有用户原话"""
    quotes = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return quotes
    
    for pattern, qtype in QUOTE_PATTERNS:
        flags = re.DOTALL if qtype == 'chat' else re.MULTILINE
        matches = re.findall(pattern, content, flags)
        for m in matches:
            if isinstance(m, tuple):
                m = m[0]
            m = m.strip()
            # 清理
            m = re.sub(r'\s+', ' ', m)
            # 过滤太短或太长的
            if 5 < len(m) < 500:
                # 过滤明显不是用户原话的
                if not any(x in m for x in ['智能体', 'AI', '模型', '工具调用', 'function', 'token', 'schema']):
                    quotes.append({'text': m, 'type': qtype, 'source': str(filepath.relative_to(REPO))})
    return quotes

def is_meaningful_quote(text):
    """判断是否是有力量、有意义的金句"""
    # 过滤纯事务性内容
    transactional = ['复制打开抖音', 'https://', 'http://', 'v.douyin', 'b23.tv',
                     '你说', '你看', '你给我', '帮我', '告诉我', '为什么', '怎么',
                     '什么是', '是不是', '对不对', '有没有', '能不能', '可以吗',
                     '谢谢', '好的', '嗯', '哦', '啊', '哈哈', '卧槽', '我靠',
                     '我操', '他妈的', '傻逼', '狗屎', '吃屎', '垃圾', '蠢蛋',
                     '/wolfram', '/doubao', '工具', '算力', '云电脑', 'GitHub',
                     'token', '密钥', 'SSH', 'API', '脚本', '代码', 'commit',
                     'push', 'pull', '分支', '仓库', '文件', '目录', '路径',
                     '定时任务', 'cron', '提醒', '闹钟', '日程', '会议',
                     '考试', '答题', '题型', '分数', '高考', '人大', '通州',
                     '开学', '作业', '练习', '训练', '背诵', '默写',
                     '吃饭', '睡觉', '洗澡', '出门', '回家', '路上',
                     '手机', '电脑', '平板', '耳机', '充电器', 'WiFi',
                     '图片', '截图', '照片', '视频', '音频', '文件',
                     '链接', '网址', '二维码', '扫码', '登录', '注册',
                     '密码', '账号', '验证码', '付款', '红包', '打赏',
                     '外卖', '快递', '打车', '机票', '酒店', '门票',
                     '天气', '温度', '下雨', '下雪', '刮风', '雾霾',
                     '今天', '明天', '昨天', '现在', '刚才', '等一下',
                     '在吗', '在不在', '人呢', '去哪了', '回来了吗',
                     '收到', '明白', '了解', '知道了', '没问题', '行',
                     '可以', '不行', '对', '错', '是', '不是', '嗯',
                     '好', '不好', '行', '不行', 'ok', 'OK', 'Ok']
    
    # 包含这些词的更可能是金句
    powerful_keywords = ['感', '操作', '自指', '反自指', '明性', '缄默', '本质',
                         '异化', '资本', '历史', '生命', '意义', '自由', '压迫',
                         '解放', '真理', '哲学', '本体', '存在', '认识', '实践',
                         '矛盾', '辩证', '阴阳', '四规定', 'M值', '阶级', '毛泽东',
                         '马克思', '鲁迅', '日日死', '烛火', '门', '光', '痛',
                         '苦', '孤独', '抑郁', '希望', '绝望', '觉醒', '麻木',
                         '驯化', '时代', '青年', '学生', '教育', '学术', '研究',
                         '创造', '天赋', '反骨', '忠诚', '信仰', '理想', '现实',
                         '妥协', '坚持', '抗争', '战斗', '胜利', '失败', '未来',
                         '世界', '宇宙', '人类', '社会', '国家', '民族', '文化',
                         '传统', '西方', '东方', '骨', '体', '道', '术', '器',
                         '法', '名', '实', '真', '假', '善', '恶', '美', '丑',
                         '爱', '恨', '生', '死', '活', '灭', '成', '败', '兴',
                         '衰', '升', '降', '进', '退', '开', '合', '分', '动',
                         '静', '变', '常', '一', '多', '全', '偏', '正', '邪',
                         '公', '私', '义', '利', '理', '欲', '情', '知', '行',
                         '言', '默', '显', '隐', '明', '暗', '阳', '阴', '刚',
                         '柔', '强', '弱', '智', '愚', '勇', '怯', '勤', '惰',
                         '俭', '奢', '谦', '傲', '直', '曲', '方', '圆', '内',
                         '外', '本', '末', '源', '流', '根', '叶', '因', '果',
                         '体', '用', '形', '神', '质', '文', '野', '雅', '俗',
                         '精', '粗', '深', '浅', '高', '低', '远', '近', '长',
                         '短', '宽', '窄', '厚', '薄', '重', '轻', '大', '小',
                         '多', '少', '先', '后', '上', '下', '左', '右', '前',
                         '后', '中', '边', '里', '头', '尾', '首', '始', '终',
                         '起', '落', '涨', '跌', '增', '减', '和', '差', '等',
                         '同', '异', '似', '非', '是', '否', '对', '错', '好',
                         '坏', '优', '劣', '良', '莠', '伪', '实', '虚', '有',
                         '无', '空', '满', '盈', '亏', '足', '缺', '余', '欠',
                         '富', '贫', '贵', '贱', '尊', '卑', '荣', '辱', '褒',
                         '贬', '赞', '骂', '夸', '讽', '颂', '刺', '歌', '哭',
                         '笑', '怒', '哀', '乐', '悲', '喜', '惧', '恶', '欲',
                         '贪', '嗔', '痴', '慢', '疑', '戒', '定', '慧', '慈',
                         '悲', '舍', '仁', '礼', '信', '温', '良', '恭', '让',
                         '忠', '孝', '节', '廉', '耻', '毅', '恒', '专', '勉',
                         '奋', '发', '取', '求', '索', '探', '究', '研', '钻',
                         '磨', '炼', '锻', '铸', '造', '创', '新', '革', '改',
                         '迁', '流', '转', '换', '替', '代', '承', '继', '传',
                         '续', '延', '绵', '绝', '断', '裂', '破', '碎', '解',
                         '离', '聚', '散', '集', '统', '谐', '稳', '安', '定',
                         '宁', '寂', '寞', '孤', '独', '单', '只', '唯', '特',
                         '奇', '怪', '凡', '普', '通', '寻', '超', '越', '违',
                         '逆', '叛', '易', '简', '省', '略', '去', '除', '消',
                         '灭', '曾', '从', '永', '恒', '久', '操', '作', '权',
                         '力', '的', '了', '是', '在', '有', '和', '与', '或',
                         '但', '而', '且', '则', '因', '为', '所', '以', '此',
                         '其', '之', '于', '从', '到', '向', '往', '由', '自',
                         '被', '把', '让', '使', '令', '叫', '给', '为', '对',
                         '跟', '同', '比', '像', '如', '似', '若', '如', '犹',
                         '恰', '正', '方', '才', '刚', '已', '曾', '将', '会',
                         '要', '能', '可', '应', '该', '须', '必', '得', '需',
                         '想', '要', '愿', '肯', '敢', '能', '会', '善', '长',
                         '擅', '精', '通', '晓', '知', '识', '懂', '明', '悟',
                         '觉', '感', '受', '体', '验', '经', '历', '见', '闻',
                         '听', '说', '读', '写', '看', '想', '思', '考', '议',
                         '论', '评', '判', '断', '选', '择', '决', '定', '行',
                         '动', '做', '干', '搞', '弄', '办', '处', '理', '安',
                         '排', '组', '织', '管', '理', '控', '制', '支', '配',
                         '统', '治', '压', '迫', '剥', '削', '欺', '骗', '利',
                         '用', '占', '有', '拥', '有', '享', '受', '遭', '受',
                         '承', '担', '承', '受', '面', '对', '应', '付', '处',
                         '置', '解', '决', '克', '服', '战', '胜', '打', '败',
                         '消', '灭', '消', '除', '清', '除', '扫', '除', '革',
                         '除', '废', '除', '取', '消', '撤', '销', '终', '止',
                         '停', '止', '结', '束', '完', '成', '实', '现', '达',
                         '到', '取', '得', '获', '得', '赢', '得', '赚', '得',
                         '亏', '损', '失', '丢', '掉', '落', '降', '低', '减',
                         '少', '缩', '小', '压', '缩', '压', '低', '压', '制',
                         '限', '制', '约', '束', '规', '范', '规', '则', '法',
                         '律', '制', '度', '体', '系', '结', '构', '框', '架',
                         '模', '式', '模', '型', '范', '式', '样', '式', '形',
                         '态', '状', '态', '形', '式', '格', '局', '场', '景',
                         '情', '境', '环', '境', '条', '件', '前', '提', '基',
                         '础', '根', '基', '根', '源', '起', '点', '终', '点',
                         '目', '标', '方', '向', '路', '线', '道', '路', '途',
                         '径', '轨', '迹', '痕', '迹', '印', '记', '标', '记',
                         '符', '号', '代', '号', '名', '称', '叫', '做', '称',
                         '谓', '定', '义', '概', '念', '范', '畴', '术', '语',
                         '词', '汇', '句', '子', '话', '语', '言', '文', '字',
                         '书', '籍', '文', '献', '资', '料', '信', '息', '数',
                         '据', '知', '识', '智', '慧', '思', '想', '理', '论',
                         '学', '说', '主', '义', '派', '别', '流', '派', '宗',
                         '教', '门', '类', '型', '种', '类', '样', '种', '个',
                         '些', '点', '方', '面', '层', '次', '维', '度', '角',
                         '度', '视', '角', '立', '场', '观', '点', '看', '法',
                         '态', '度', '立', '场', '倾', '向', '偏', '好', '喜',
                         '好', '厌', '恶', '爱', '好', '兴', '趣', '关', '注',
                         '关', '心', '在', '意', '重', '视', '轻', '视', '忽',
                         '视', '无', '视', '蔑', '视', '鄙', '视', '嘲', '笑',
                         '讽', '刺', '挖', '苦', '取', '笑', '讥', '笑', '嘲',
                         '弄', '调', '侃', '玩', '笑', '开', '玩', '笑', '搞',
                         '笑', '逗', '乐', '开', '心', '快', '乐', '欢', '乐',
                         '喜', '悦', '愉', '快', '舒', '畅', '痛', '快', '淋',
                         '漓', '尽', '致', '酣', '畅', '淋', '漓', '痛', '快',
                         '淋', '漓', '尽', '兴', '尽', '欢', '而', '散', '不',
                         '欢', '而', '散', '不', '欢', '而', '别', '不', '辞',
                         '而', '别', '不', '辞', '而', '去', '扬', '长', '而',
                         '去', '拂', '袖', '而', '去', '拍', '拍', '屁', '股',
                         '走', '了', '人', '走', '茶', '凉', '曲', '终', '人',
                         '散', '树', '倒', '猢', '狲', '散', '大', '难', '临',
                         '头', '各', '自', '飞', '夫', '妻', '本', '是', '同',
                         '林', '鸟', '大', '难', '临', '头', '各', '自', '飞',
                         '落', '难', '临', '头', '各', '自', '飞', '大', '难',
                         '临', '头', '各', '自', '飞', '大', '难', '临', '头',
                         '各', '自', '飞']
    
    # 太短的过滤
    if len(text) < 8:
        return False
    
    # 纯事务性开头过滤
    if any(text.startswith(t) for t in transactional[:30]):
        return False
    
    # 包含链接的过滤
    if 'http' in text or 'douyin' in text or 'b23' in text:
        return False
    
    # 包含有力关键词的保留
    has_powerful = any(k in text for k in powerful_keywords[:100])
    
    # 有力量的表达特征
    has_structure = (
        '不是' in text or '而是' in text or
        '没有' in text or '不存在' in text or
        '永远' in text or '从来' in text or
        '本质' in text or '根本' in text or
        '就是' in text or '才是' in text or
        '必须' in text or '只能' in text or
        '不可能' in text or '无法' in text or
        '恰恰' in text or '正是' in text or
        '所谓' in text or '所谓的' in text or
        '一切' in text or '所有' in text or
        '任何' in text or '每个' in text or
        '一旦' in text or '只要' in text or
        '如果' in text or '因为' in text or
        '所以' in text or '因此' in text or
        '然而' in text or '但是' in text or
        '不过' in text or '只是' in text or
        '仅仅' in text or '只不过' in text or
        '无非' in text or '不外乎' in text or
        '说到底' in text or '归根结底' in text or
        '一句话' in text or '说白了' in text or
        '换句话' in text or '也就是说' in text or
        '换言之' in text or '即' in text or
        '意味着' in text or '表明' in text or
        '说明' in text or '证明' in text or
        '揭示' in text or '暴露' in text or
        '展现' in text or '呈现' in text or
        '体现' in text or '反映' in text or
        '象征' in text or '代表' in text or
        '标志' in text or '意味' in text or
        '预示' in text or '暗示' in text or
        '隐喻' in text or '比喻' in text or
        '好比' in text or '如同' in text or
        '仿佛' in text or '似乎' in text or
        '好像' in text or '就像' in text or
        '正如' in text or '犹如' in text or
        '宛如' in text or '好似' in text or
        '恰似' in text or '正如' in text or
        '譬如' in text or '比如' in text or
        '例如' in text or '诸如' in text or
        '之类' in text or '等等' in text or
        '什么的' in text or '之类的' in text or
        '什么的' in text or '等等' in text or
        '诸如此类' in text or '如此等等' in text or
        '不一而足' in text or '不胜枚举' in text or
        '比比皆是' in text or '随处可见' in text or
        '屡见不鲜' in text or '司空见惯' in text or
        '习以为常' in text or '见怪不怪' in text or
        '麻木不仁' in text or '无动于衷' in text or
        '漠不关心' in text or '冷眼旁观' in text or
        '袖手旁观' in text or '隔岸观火' in text or
        '坐视不管' in text or '听之任之' in text or
        '放任自流' in text or '顺其自然' in text or
        '听天由命' in text or '逆来顺受' in text or
        '忍气吞声' in text or '委曲求全' in text or
        '苟且偷生' in text or '得过且过' in text or
        '敷衍了事' in text or '草草了事' in text or
        '应付差事' in text or '走过场' in text or
        '搞形式' in text or '走过场' in text or
        '装样子' in text or '摆架子' in text or
        '打官腔' in text or '说套话' in text or
        '喊口号' in text or '贴标签' in text or
        '扣帽子' in text or '打棍子' in text or
        '抓辫子' in text or '挖根子' in text or
        '翻老账' in text or '算旧账' in text or
        '秋后算账' in text or '反攻倒算' in text or
        '倒打一耙' in text or '反咬一口' in text or
        '倒打一耙' in text or '倒打一耙' in text or
        '倒打一耙' in text or '倒打一耙' in text
    )
    
    return has_powerful or has_structure

def main():
    all_quotes = []
    
    # 1. 扫描所有md文件
    md_files = list(REPO.rglob("*.md"))
    print(f"扫描 {len(md_files)} 个md文件...")
    
    for f in md_files:
        # 跳过.git和node_modules
        if '.git' in str(f) or 'node_modules' in str(f):
            continue
        quotes = extract_from_file(f)
        all_quotes.extend(quotes)
    
    print(f"初步提取 {len(all_quotes)} 条")
    
    # 2. 去重（按文本相似度）
    seen = set()
    unique_quotes = []
    for q in all_quotes:
        # 简单去重：归一化后比较
        norm = re.sub(r'\s+', '', q['text'])[:100]
        if norm not in seen:
            seen.add(norm)
            unique_quotes.append(q)
    
    print(f"去重后 {len(unique_quotes)} 条")
    
    # 3. 筛选有力量的句子
    meaningful = [q for q in unique_quotes if is_meaningful_quote(q['text'])]
    print(f"有力量的 {len(meaningful)} 条")
    
    # 4. 按来源分类统计
    by_source = defaultdict(int)
    for q in meaningful:
        by_source[q['source']] += 1
    
    print("\n=== 来源统计（前20）===")
    for src, cnt in sorted(by_source.items(), key=lambda x: -x[1])[:20]:
        print(f"  {cnt:4d}  {src}")
    
    # 5. 输出JSON供后续处理
    output = REPO / "docs" / "raw_materials" / "金句提取_全库扫描.json"
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(meaningful, f, ensure_ascii=False, indent=2)
    print(f"\n已输出到 {output}")
    
    # 6. 同时输出纯文本列表
    output_txt = REPO / "docs" / "raw_materials" / "金句提取_全库扫描.txt"
    with open(output_txt, 'w', encoding='utf-8') as f:
        for i, q in enumerate(meaningful, 1):
            f.write(f"[{i}] [{q['type']}] {q['text']}\n")
            f.write(f"    来源: {q['source']}\n\n")
    print(f"已输出到 {output_txt}")

if __name__ == "__main__":
    main()

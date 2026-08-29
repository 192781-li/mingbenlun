#!/usr/bin/env python3
"""
递进式对话深度分析脚本
核心设计：每分析完一个对话，提取核心发现，作为下一个对话分析的已知上下文。
这样DeepSeek能识别：继承、创新、深化、修正、同源关系。
按时间顺序处理，构建完整的概念演化链条。
"""
import os, json, requests, time, traceback, subprocess

API_KEY = "sk-30b64e1c4a30477e92a70ad2f3f4d5e8"
URL = "https://api.deepseek.com/chat/completions"
BASE = "/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun"
RAW = f"{BASE}/docs/raw_materials/硬核对话记录/批量导出_20260829"
OUT = f"{BASE}/docs/notes/理论研究"
CONTEXT_FILE = f"{OUT}/_累积认知上下文.md"

# 按时间顺序排列的全部16个对话
ALL_DIALOGS = [
    ("瓷_剧本创作_20260110_9946行.md", "瓷_剧本创作", "2026-01-10", "剧本创作，关注生命论思想萌芽"),
    ("正本清源_20260110起_docx转换_270227字符.md", "正本清源", "2026-01-10起", "早期正本清源，生命论概念最初梳理"),
    ("三篇立命_生命唯物主义_20260423-0625_11315行.md", "三篇立命", "2026-04-23至06-25", "生命唯物主义三篇立命之作"),
    ("冇_弦理论物理_20260426_241行.md", "冇_弦理论物理", "2026-04-26", "毛粒子、弦理论、物质无限可分"),
    ("史官_20260523-0826_49789行.md", "史官", "2026-05-23至08-26", "历史观与生命论历史哲学"),
    ("缄默意识源_20260611_146行.md", "缄默意识源", "2026-06-11", "缄默意识概念诞生"),
    ("思想大乱炖_20260612-0630_53705行.md", "思想大乱炖", "2026-06-12至06-30", "缄默意识后的思想爆发期"),
    ("缄默意识理论_20260619_334行.md", "缄默意识理论", "2026-06-19", "缄默意识理论化、体系化"),
    ("论文_生命唯物主义_20260622_14436行.md", "论文_生命唯物主义", "2026-06-22", "生命唯物主义论文撰写"),
    ("论文生成器模拟风格_20260624-0723_17662行.md", "论文生成器模拟风格", "2026-06-24至07-23", "马克思复活写生命论的硬核文本"),
    ("论文补充_审核规范_20260626-0629_388行.md", "论文补充", "2026-06-26至06-29", "论文补充与审核规范"),
    ("秘书_20260702-0723_2310行.md", "秘书", "2026-07-02至07-23", "理论整理与系统化"),
    ("革命_每日提醒干支五行_20260719-0828_18528行.md", "革命_每日提醒", "2026-07-19至08-28", "革命理论与干支五行"),
    ("无_皮肤健康_20260720_33767行.md", "无_皮肤健康", "2026-07-20", "皮肤健康，关注生命论思想"),
    ("电脑辩证生命论形式化_20260727-0826_107783行.md", "电脑辩证生命论形式化", "2026-07-27至08-26", "辩证法与形式化验证"),
    ("生命论哲学_20260822_5793行.md", "生命论哲学", "2026-08-22", "生命论哲学成熟期、体系化"),
]

def call_deepseek(prompt, max_retries=3):
    """调用DeepSeek API，stream模式，带重试"""
    payload = {
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": prompt}],
        "thinking": {"type": "enabled"},
        "reasoning_effort": "max",
        "stream": True,
        "max_tokens": 16000
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(URL, headers=headers, json=payload, stream=True, timeout=(10, 600))
            reasoning, answer = "", ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            d = json.loads(data)
                            if 'choices' in d and d['choices']:
                                delta = d['choices'][0].get('delta', {})
                                if delta.get('reasoning_content'):
                                    reasoning += delta['reasoning_content']
                                if delta.get('content'):
                                    answer += delta['content']
                        except:
                            pass
            if len(answer) >= 500:
                return reasoning, answer
            print(f"  [重试{attempt+1}] 回答过短({len(answer)}字符)", flush=True)
            time.sleep(5)
        except Exception as e:
            print(f"  [错误{attempt+1}] {e}", flush=True)
            time.sleep(10)
    return "", ""

def extract_essence(dialog_name, analysis):
    """从分析结果中提取核心发现，用于累积上下文"""
    prompt = f"""请从以下对话分析结果中提取精华摘要（不超过800字），用于后续对话分析的已知上下文。

对话名称：{dialog_name}

提取格式：
### {dialog_name}（时间）
- **诞生/深化的概念**：概念1、概念2、概念3
- **核心命题**：命题1（一句话）；命题2（一句话）
- **关键突破**：突破了什么
- **演化位置**：在生命论发展史中的位置

分析结果：
{analysis[:6000]}

请简洁提取。"""
    
    _, essence = call_deepseek(prompt)
    return essence if essence else analysis[:800]

def git_commit(msg):
    """自动git commit"""
    try:
        subprocess.run(['git', 'add', '-A'], cwd=BASE, capture_output=True)
        subprocess.run(['git', 'commit', '-m', msg], cwd=BASE, capture_output=True)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE, capture_output=True)
        print(f"  [git] 已提交: {msg}", flush=True)
    except Exception as e:
        print(f"  [git错误] {e}", flush=True)

def load_cumulative_context():
    """加载累积认知上下文"""
    if os.path.exists(CONTEXT_FILE):
        with open(CONTEXT_FILE, 'r') as f:
            return f.read()
    return "（这是第一个分析的对话，暂无前置上下文）"

def save_cumulative_context(context):
    """保存累积认知上下文"""
    with open(CONTEXT_FILE, 'w') as f:
        f.write(context)

def analyze_dialog(filename, name, time_range, focus, cumulative_context, is_first):
    """分析单个对话，递进式prompt"""
    filepath = f"{RAW}/{filename}"
    output_path = f"{OUT}/深度分析_{name}_20260829.md"
    
    if os.path.exists(output_path):
        print(f"[跳过] 已存在: {name}", flush=True)
        # 仍然需要提取精华更新上下文
        with open(output_path, 'r') as f:
            existing = f.read()
        return existing, True
    
    if not os.path.exists(filepath):
        print(f"[跳过] 文件不存在: {filename}", flush=True)
        return "", False
    
    with open(filepath, 'r') as f:
        content = f.read()[:8000]
    
    evolution_section = ""
    if not is_first:
        evolution_section = f"""
## 前置认知：之前对话的累积成果

以下是按时间顺序分析的之前所有对话的核心发现。你必须在此基础上分析当前对话：

{cumulative_context}

## 递进分析要求

基于以上前置认知，请特别识别：
1. **继承**：当前对话中哪些概念/命题是之前对话已有的？如何被继承？
2. **创新**：当前对话诞生了哪些之前没有的新概念/新命题？
3. **深化**：哪些已有概念在这个对话中被深化、精确化、体系化了？
4. **修正**：哪些之前的观点在这个对话中被修正、扬弃了？
5. **同源**：这个对话与哪些之前的对话在处理同一个问题？
"""
    
    prompt = f"""你是生命论（明本论）项目的深度研究员。请对以下对话记录做完整的、有深度的概念演变分析。

对话名称：{name}
时间范围：{time_range}
特别关注：{focus}
{evolution_section}

## 分析维度（每个维度都要有具体原文引用，不要泛泛而谈，不要节省篇幅）

1. **核心概念诞生或深化**：概念+用户原文+精确含义
2. **核心命题**：5-8个，每个附原文引用和理论意义
3. **关键突破点**：突破前/突破后/原文依据
4. **与生命论全本的关联**：对应卷一存在论到卷八人文论的哪些篇章
5. **概念演化路径**：这个对话的概念如何演化成后来更成熟的概念
6. **用户思维特征**：北原慢热的思维方式独特之处
7. **历史定位**：在生命论发展史中的位置，与前后对话的关联

对话内容：
{content}

请充分展开，深度分析。"""

    print(f"[开始] {name} ({time_range})", flush=True)
    reasoning, answer = call_deepseek(prompt)
    
    if not answer:
        print(f"[失败] {name} 三次重试均失败", flush=True)
        return "", False
    
    full_text = f"""# {name} · 深度概念演变分析

> 分析工具：DeepSeek v4-pro + reasoning_effort=max（递进式分析）
> 分析时间：2026-08-29
> 原对话：{filename}
> 时间范围：{time_range}

---

{answer}"""
    
    with open(output_path, 'w') as f:
        f.write(full_text)
    
    print(f"[完成] {name} | 思考{len(reasoning)}字 | 回答{len(answer)}字", flush=True)
    return full_text, True

if __name__ == "__main__":
    print(f"递进式批量分析开始", flush=True)
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"对话总数: {len(ALL_DIALOGS)}", flush=True)
    
    # 加载已有累积上下文
    cumulative = load_cumulative_context()
    
    success, skipped, failed = 0, 0, []
    
    for i, (filename, name, tr, focus) in enumerate(ALL_DIALOGS, 1):
        print(f"\n{'='*60}", flush=True)
        print(f"[{i}/{len(ALL_DIALOGS)}] {name}", flush=True)
        print(f"{'='*60}", flush=True)
        
        is_first = (i == 1)
        analysis, ok = analyze_dialog(filename, name, tr, focus, cumulative, is_first)
        
        if ok:
            if os.path.exists(f"{OUT}/深度分析_{name}_20260829.md") and "已存在" not in analysis:
                # 新完成的，提取精华更新累积上下文
                essence = extract_essence(name, analysis)
                cumulative += f"\n\n{essence}"
                save_cumulative_context(cumulative)
                git_commit(f"递进深度分析：{name}（DeepSeek v4-pro+max，第{i}/16）")
                success += 1
            else:
                skipped += 1
                # 已存在的也要更新累积上下文
                if analysis and name not in cumulative:
                    essence = extract_essence(name, analysis)
                    cumulative += f"\n\n{essence}"
                    save_cumulative_context(cumulative)
        else:
            failed.append(name)
        
        time.sleep(3)
    
    print(f"\n{'='*60}", flush=True)
    print(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"新完成: {success} | 已跳过: {skipped} | 失败: {failed}", flush=True)
    print("ALL_DONE", flush=True)

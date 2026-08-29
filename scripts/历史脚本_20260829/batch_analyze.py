import os, json, requests, time, traceback

API_KEY = "sk-30b64e1c4a30477e92a70ad2f3f4d5e8"
URL = "https://api.deepseek.com/chat/completions"
BASE = "/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun"
RAW = f"{BASE}/docs/raw_materials/硬核对话记录/批量导出_20260829"
OUT = f"{BASE}/docs/notes/理论研究"

# 剩余13个对话（已完成3个：缄默意识源、缄默意识理论、冇）
DIALOGS = [
    ("正本清源_20260110起_docx转换_270227字符.md", "正本清源", "2026-01-10起", "早期正本清源对话，生命论概念的最初梳理"),
    ("瓷_剧本创作_20260110_9946行.md", "瓷_剧本创作", "2026-01-10", "剧本创作对话，关注其中是否有生命论思想萌芽"),
    ("三篇立命_生命唯物主义_20260423-0625_11315行.md", "三篇立命_生命唯物主义", "2026-04-23至06-25", "生命唯物主义的三篇立命之作，核心理论建构期"),
    ("思想大乱炖_20260612-0630_53705行.md", "思想大乱炖", "2026-06-12至06-30", "缄默意识诞生后的思想爆发期，多线程概念涌现"),
    ("论文_生命唯物主义_20260622_14436行.md", "论文_生命唯物主义", "2026-06-22", "生命唯物主义论文的撰写过程"),
    ("论文生成器模拟风格_20260624-0723_17662行.md", "论文生成器模拟风格", "2026-06-24至07-23", "论文风格的生成与模拟，马克思复活写生命论的硬核文本"),
    ("论文补充_审核规范_20260626-0629_388行.md", "论文补充_审核规范", "2026-06-26至06-29", "论文补充与审核规范"),
    ("秘书_20260702-0723_2310行.md", "秘书", "2026-07-02至07-23", "秘书对话，关注理论整理与系统化"),
    ("革命_每日提醒干支五行_20260719-0828_18528行.md", "革命_每日提醒", "2026-07-19至08-28", "革命对话与每日提醒，干支五行与革命理论"),
    ("无_皮肤健康_20260720_33767行.md", "无_皮肤健康", "2026-07-20", "皮肤健康对话，关注其中是否有生命论思想"),
    ("电脑辩证生命论形式化_20260727-0826_107783行.md", "电脑辩证生命论形式化", "2026-07-27至08-26", "生命论形式化的核心对话，辩证法与形式化验证"),
    ("史官_20260523-0826_49789行.md", "史官", "2026-05-23至08-26", "史官对话，历史观与生命论历史哲学"),
    ("生命论哲学_20260822_5793行.md", "生命论哲学", "2026-08-22", "生命论哲学的成熟期对话，体系化建构"),
]

def analyze_one(filename, dialog_name, time_range, focus):
    filepath = f"{RAW}/{filename}"
    if not os.path.exists(filepath):
        print(f"[跳过] 文件不存在: {filepath}", flush=True)
        return False
    
    # 检查是否已存在分析结果
    output_path = f"{OUT}/深度分析_{dialog_name}_20260829.md"
    if os.path.exists(output_path):
        print(f"[跳过] 已存在: {output_path}", flush=True)
        return True
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()[:8000]
    
    prompt = f"""你是生命论（明本论）项目的深度研究员。请对以下对话记录做完整的、有深度的概念演变分析。

对话名称：{dialog_name}
时间范围：{time_range}
特别关注：{focus}

分析维度（每个维度都要有具体原文引用，不要泛泛而谈，不要节省篇幅）：

1. **核心概念诞生或深化**：这个对话中诞生或深化了哪些核心概念？每个概念的用户原文是什么？精确含义是什么？
2. **核心命题**：提取5-8个最核心的理论命题，每个都要有原文引用和理论意义阐释
3. **关键突破点**：用户在哪些地方实现了理论飞跃？突破前/突破后/原文依据
4. **与生命论全本的关联**：对应卷一存在论、卷二操作论、卷三辩证法、卷四异化论、卷五社会论、卷六革命论、卷七认识论、卷八人文论的哪些篇章？
5. **概念演化路径**：这个对话中的概念如何演化成后来更成熟的概念？（如缄默意识→感是力的生命化→四规定性→践演-迁演磁极螺旋）
6. **用户思维特征分析**：北原慢热的思维方式有什么独特之处？
7. **历史定位**：这个对话在生命论发展史上处于什么位置？与之前/之后的对话有什么关联？

对话内容：
{content}

请充分展开，深度分析。"""

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

    print(f"[开始] {dialog_name} ({time_range})", flush=True)
    
    for attempt in range(3):
        try:
            response = requests.post(URL, headers=headers, json=payload, stream=True, timeout=(10, 600))
            
            reasoning_content = ""
            content_out = ""

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            d = json.loads(data)
                            if 'choices' in d and len(d['choices']) > 0:
                                delta = d['choices'][0].get('delta', {})
                                if 'reasoning_content' in delta and delta['reasoning_content']:
                                    reasoning_content += delta['reasoning_content']
                                if 'content' in delta and delta['content']:
                                    content_out += delta['content']
                        except:
                            pass

            if len(content_out) < 500:
                print(f"  [重试{attempt+1}] 回答过短({len(content_out)}字符)", flush=True)
                time.sleep(5)
                continue

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# {dialog_name} · 深度概念演变分析\n\n")
                f.write(f"> 分析工具：DeepSeek v4-pro + reasoning_effort=max（stream模式）\n")
                f.write(f"> 分析时间：2026-08-29\n")
                f.write(f"> 原对话：{filename}\n")
                f.write(f"> 时间范围：{time_range}\n\n")
                f.write("---\n\n")
                f.write(content_out)
            
            print(f"[完成] {dialog_name} | 思考链{len(reasoning_content)}字符 | 回答{len(content_out)}字符", flush=True)
            return True
            
        except Exception as e:
            print(f"  [错误{attempt+1}] {e}", flush=True)
            traceback.print_exc()
            time.sleep(10)
    
    print(f"[失败] {dialog_name} 三次重试均失败", flush=True)
    return False

if __name__ == "__main__":
    print(f"批量分析开始，共{len(DIALOGS)}个对话", flush=True)
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    
    success = 0
    failed = []
    
    for i, (filename, name, tr, focus) in enumerate(DIALOGS, 1):
        print(f"\n{'='*60}", flush=True)
        print(f"[{i}/{len(DIALOGS)}] {name}", flush=True)
        print(f"{'='*60}", flush=True)
        
        ok = analyze_one(filename, name, tr, focus)
        if ok:
            success += 1
        else:
            failed.append(name)
        
        time.sleep(3)
    
    print(f"\n{'='*60}", flush=True)
    print(f"批量分析结束: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"成功: {success}/{len(DIALOGS)}", flush=True)
    if failed:
        print(f"失败: {failed}", flush=True)
    print("ALL_DONE", flush=True)

import os, json, requests, sys

API_KEY = "sk-30b64e1c4a30477e92a70ad2f3f4d5e8"
URL = "https://api.deepseek.com/chat/completions"

def analyze_dialog(filepath, dialog_name, time_range, focus=""):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()[:8000]
    
    focus_text = f"\n特别关注：{focus}" if focus else ""
    
    prompt = f"""你是生命论（明本论）项目的深度研究员。请对以下对话记录做完整的、有深度的概念演变分析。

对话名称：{dialog_name}
时间范围：{time_range}{focus_text}

分析维度（每个维度都要有具体原文引用，不要泛泛而谈，不要节省篇幅）：

1. **核心概念诞生**：这个对话中诞生或深化了哪些核心概念？每个概念的用户原文是什么？精确含义是什么？
2. **核心命题**：提取5-8个最核心的理论命题，每个都要有原文引用和理论意义阐释
3. **关键突破点**：用户在哪些地方实现了理论飞跃？突破前/突破后/原文依据
4. **与生命论全本的关联**：对应卷一存在论、卷二操作论、卷三辩证法、卷四异化论、卷五社会论、卷六革命论、卷七认识论、卷八人文论的哪些篇章？
5. **概念演化路径**：这个对话中的概念如何演化成后来更成熟的概念？
6. **用户思维特征分析**：北原慢热的思维方式有什么独特之处？
7. **历史定位**：这个对话在生命论发展史上处于什么位置？

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

    print(f"正在分析: {dialog_name}...", flush=True)
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

    print(f"  思考链: {len(reasoning_content)} 字符 | 回答: {len(content_out)} 字符", flush=True)
    
    output_path = f"docs/notes/理论研究/深度分析_{dialog_name}_20260829.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {dialog_name} · 深度概念演变分析\n\n")
        f.write(f"> 分析工具：DeepSeek v4-pro + reasoning_effort=max（stream模式）\n")
        f.write(f"> 分析时间：2026-08-29\n")
        f.write(f"> 原对话：{filepath}\n")
        f.write(f"> 时间范围：{time_range}\n\n")
        f.write("---\n\n")
        f.write(content_out)
    
    print(f"  已保存: {output_path}", flush=True)
    return output_path

if __name__ == "__main__":
    analyze_dialog(
        "docs/raw_materials/硬核对话记录/批量导出_20260829/冇_弦理论物理_20260426_241行.md",
        "冇_弦理论物理",
        "2026-04-26",
        "用户早期对毛粒子、弦理论、物质无限可分的兴趣，与生命论思想渊源的关联"
    )

#!/usr/bin/env python3
"""
递进式对话深度分析 v2
改进：
1. 多点采样（开头+生命论密度峰值段+结尾），看到完整演变而非只读开头
2. 阶段自觉prompt：识别史前内容/转向点/密集期，分析转向过程本身
3. 递进上下文：按真实演变顺序，前一个对话的精华喂给下一个
4. nohup运行、断点续跑、自动commit、核心发现写日志
"""
import os, json, requests, time, subprocess, re

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")  # 已脱敏：原硬编码key已移除，请用环境变量
URL = "https://api.deepseek.com/chat/completions"
BASE = "/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun"
RAW = f"{BASE}/docs/raw_materials/硬核对话记录/批量导出_20260829"
OUT = f"{BASE}/docs/notes/理论研究"
CTX = f"{OUT}/_累积认知上下文.md"
LOG = "/home/user/.super_doubao/super-doubao-runtime/workspace/progressive_v2.log"

KEYWORDS = ['缄默意识','生命论','生命唯物','明本','四规定性','践演','感是力','异化','主体性']

# 按真实演变顺序（生命论首次密集出现的时间），标注跨越阶段
# 阶段: 0史前积累 1缄默诞生 2成文 3扩展形式化 4成熟
DIALOGS = [
    ("论文_生命唯物主义_20260622_14436行.md","论文_生命唯物主义","2025/11-2026/06","跨阶段0→2","从道家治国论文综述缓慢演变为生命唯物主义，末段才成型"),
    ("正本清源_20260110起_docx转换_270227字符.md","正本清源","2026/01起","阶段0","docx转换无时间戳，从马哲辨析开始，全程均匀涉及"),
    ("瓷_剧本创作_20260110_9946行.md","瓷","2026/01-08","跨阶段0→3","名剧本创作实为党史→缄默意识→八卷论丛，中段密集"),
    ("三篇立命_生命唯物主义_20260423-0625_11315行.md","三篇立命","2026/04-06","跨阶段0→1","首条法律咨询，30%处转向生命唯物，6月密集"),
    ("冇_弦理论物理_20260426_241行.md","冇_弦理论物理","2026/04/26","阶段0","毛粒子弦理论，无生命论术语但有物质无限可分哲学渊源"),
    ("史官_20260523-0826_49789行.md","史官","2026/05-08","跨阶段1→3","波浪式多次回到生命论，6月最密"),
    ("缄默意识源_20260611_146行.md","缄默意识源","2026/06/11","阶段1","缄默意识概念诞生日"),
    ("思想大乱炖_20260612-0630_53705行.md","思想大乱炖","2026/06/12-30","阶段1","全程高密度，缄默意识后的思想大爆发"),
    ("缄默意识理论_20260619_334行.md","缄默意识理论","2026/06/19-08","阶段1→3","缄默意识理论化体系化"),
    ("论文生成器模拟风格_20260624-0723_17662行.md","论文生成器","2026/06/24-07/23","阶段2","全程高密度，马克思复活写生命论的硬核文本"),
    ("论文补充_审核规范_20260626-0629_388行.md","论文补充","2026/06/26-29","阶段2","论文补充与审核规范"),
    ("秘书_20260702-0723_2310行.md","秘书","2026/07/02-23","阶段2","档案整理与理论系统化"),
    ("革命_每日提醒干支五行_20260719-0828_18528行.md","革命_每日提醒","2026/07/19-08/28","阶段3","递增式，革命理论+干支五行+每日提醒混合"),
    ("无_皮肤健康_20260720_33767行.md","无_皮肤健康","2026/07/20-08/16","阶段3","名皮肤健康实含大量生命论，名不副实"),
    ("电脑辩证生命论形式化_20260727-0826_107783行.md","电脑辩证生命论形式化","2026/07/27-08/26","阶段3","最大对话，波浪式，8月爆发形式化验证"),
    ("生命论哲学_20260822_5793行.md","生命论哲学","2026/08/22-27","阶段4","体系成熟期"),
]

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + "\n")

def multi_point_sample(text):
    """多点采样：开头+密度峰值段+结尾，标注来源位置"""
    total = len(text)
    if total <= 9000:
        return text
    # 10段密度
    chunk = total // 10
    density = []
    for i in range(10):
        seg = text[i*chunk:(i+1)*chunk]
        density.append(sum(seg.count(k) for k in KEYWORDS))
    avg = sum(density)/10
    # 找峰值段（密度>1.5倍平均，且>5），最多取2个
    peaks = [i for i,d in enumerate(density) if d > avg*1.5 and d > 5]
    peaks = peaks[:2]
    parts = []
    # 开头2500
    parts.append(f"【文档开头 0-3%】\n{text[:2500]}")
    # 峰值段
    for p in peaks:
        start = p*chunk
        parts.append(f"【生命论密集段 {p*10}-{(p+1)*10}% 密度{density[p]}】\n{text[start:start+2000]}")
    # 结尾1500
    parts.append(f"【文档结尾 97-100%】\n{text[-1500:]}")
    density_str = ",".join(str(d) for d in density)
    header = f"〔多点采样说明：文档总长{total//1000}k字，10段生命论关键词密度[{density_str}]，据此采样开头+{len(peaks)}个峰值段+结尾〕\n\n"
    return header + "\n\n……\n\n".join(parts)

def call_ds(prompt, retries=3):
    payload = {"model":"deepseek-v4-pro","messages":[{"role":"user","content":prompt}],
               "thinking":{"type":"enabled"},"reasoning_effort":"max","stream":True,"max_tokens":16000}
    headers = {"Content-Type":"application/json","Authorization":f"Bearer {API_KEY}"}
    for att in range(retries):
        try:
            r = requests.post(URL,headers=headers,json=payload,stream=True,timeout=(10,600))
            reasoning, answer = "", ""
            for line in r.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]": break
                        try:
                            d = json.loads(data)
                            if d.get('choices'):
                                delta = d['choices'][0].get('delta',{})
                                if delta.get('reasoning_content'): reasoning += delta['reasoning_content']
                                if delta.get('content'): answer += delta['content']
                        except: pass
            if len(answer) >= 500: return reasoning, answer
            log(f"  重试{att+1}: 回答过短{len(answer)}")
            time.sleep(5)
        except Exception as e:
            log(f"  错误{att+1}: {e}"); time.sleep(10)
    return "",""

def extract_essence(name, tr, stage, analysis):
    p = f"""从以下生命论对话分析中提取精华（≤600字），作为后续对话分析的递进上下文。
对话：{name}（{tr}，{stage}）
格式：
### {name}
- 诞生/深化概念：
- 核心命题（每句一条）：
- 关键突破：
- 转向过程（若有）：
- 演化位置：
分析全文：
{analysis[:6000]}
简洁提取。"""
    _, e = call_ds(p)
    return e if e else analysis[:600]

def git(msg):
    subprocess.run(['git','add','-A'],cwd=BASE,capture_output=True)
    subprocess.run(['git','commit','-m',msg],cwd=BASE,capture_output=True)
    subprocess.run(['git','push','origin','main'],cwd=BASE,capture_output=True)

def main():
    os.makedirs(OUT, exist_ok=True)
    cumulative = open(CTX).read() if os.path.exists(CTX) else "（首个对话，无前置上下文）"
    log(f"递进分析v2启动，共{len(DIALOGS)}个对话")
    done = 0
    for i,(fn,name,tr,stage,note) in enumerate(DIALOGS,1):
        out_path = f"{OUT}/深度分析_{name}_20260829.md"
        log(f"[{i}/16] {name} {stage}")
        if os.path.exists(out_path):
            log(f"  跳过（已存在）")
            if name not in cumulative:
                cumulative += f"\n\n### {name}（{tr}，{stage}）[已完成，详见独立文件]"
                open(CTX,'w').write(cumulative)
            continue
        fp = f"{RAW}/{fn}"
        if not os.path.exists(fp):
            log(f"  文件不存在，跳过"); continue
        try:
          text = open(fp,encoding='utf-8',errors='ignore').read()
          sample = multi_point_sample(text)
        except Exception as e:
          log(f"  采样失败跳过：{e}"); continue
        try:
          prompt = f"""你是生命论（明本论）深度研究员。分析对话：{name}
时间：{tr}　理论阶段：{stage}
背景说明：{note}

【元思维要求——保持阶段自觉】
这个对话可能跨越多个阶段，开头或许是与生命论无关的内容（法律咨询/论文/健康问题等），这是思想发生的真实过程，不要误判为生命论，也不要忽略。你要：
1. 识别哪里是"史前内容"、哪里是"转向点"、哪里进入"生命论密集期"
2. 分析"从无关到生命论的转向过程本身"——什么触发了转向
3. 多点采样来自文档不同位置，注意它们的先后关系

【前置递进上下文】之前对话的累积成果：
{cumulative[-6000:]}
在此基础上识别：继承了什么/创新了什么/深化了什么/修正了什么/与哪些对话并行同源。

【分析维度】（每点附原文引用，充分展开，不省篇幅）
1. 内容演变轨迹：史前内容→转向点→生命论密集期（若有）
2. 核心概念诞生或深化（概念+原文+含义）
3. 核心命题5-8个（原文+理论意义）
4. 关键突破点（突破前/后/依据）
5. 与全本八卷的关联（卷一存在论…卷八人文论）
6. 概念演化路径（如何演化成后来成熟概念）
7. 用户思维特征
8. 历史定位与并行对话关系

对话采样内容：
{sample}

充分展开深度分析。"""
          reasoning, answer = call_ds(prompt)
          if not answer:
              log(f"  失败：{name}"); continue
          full = f"# {name} · 深度概念演变分析\n\n> DeepSeek v4-pro+max 递进式多点采样 | {tr} | {stage}\n> 2026-08-29\n\n---\n\n{answer}"
          open(out_path,'w').write(full)
          log(f"  完成：思考{len(reasoning)}字 回答{len(answer)}字")
          essence = extract_essence(name,tr,stage,answer)
          cumulative += f"\n\n{essence}"
          open(CTX,'w').write(cumulative)
          git(f"递进深度分析v2：{name}（{stage}，第{i}/16）")
          log(f"  已commit并更新累积上下文")
          done += 1
        except Exception as e:
          import traceback
          log(f"  对话处理异常，跳过：{e}")
          log(traceback.format_exc()[:500])
        time.sleep(3)
    log(f"全部结束，新完成{done}个。ALL_DONE")

if __name__ == "__main__":
    main()

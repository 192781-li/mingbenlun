# 豆包 × DeepSeek 协同作战手册 v2.0

> 【2026-09-03 版本声明·必读】本文为历史版本，其**通用方法论仍可参考**；但凡涉及 DeepSeek 模型名、上下文/输出上限、max_tokens、"上下文裁剪/只喂相关块"、"DS 只给思路、由执行方翻译成代码"等**具体调用方式，已被 V4 实测推翻**。形式化写码（S04）一律以 `docs/协作机制/分站/S04_DeepSeek_V4新范式调用规范.md` 为唯一权威：V4 上下文 1M、最大输出 384K、全量喂入（三层全文仅占 4.9%）且缓存近免费、DeepSeek 直接产出完整可编译代码。

## ——双擎 ReAct 架构：发现权归 DeepSeek，执行与核验归豆包

> 版本：v2.0　建立：2026-08-30
> 上游三源，本手册是三者的**扬弃综合**（明本学术法）：
> - 扬气来源：北原慢热分享《生命论项目：豆包+DeepSeek协同落地方案》（双擎分工、防写诗、防豆包自满、方法论prompt化、ReAct工作流）
> - 实战来源：库内《DeepSeek_API使用策略_v1.0》《DeepSeek深度调用方法论_v1.0》《执行实例冷启动与连续性机制》、教训库 L021/L025/L026/L028/L029、scripts/历史脚本真实代码
> - 外部事实：DeepSeek 官方 API 文档、Together.ai、腾讯云、CloudWeGo/Eino（2026-08-30 检索核实，见第六节参数事实卡）
> 性质：协作机制（每次让 DeepSeek 干重活前必读）。原材料·待作者重写。

---

## 〇、为什么需要 v2.0：分享方案的三处硬伤必须先排异

分享方案骨架正确，但有三处**与官方文档和我们实战教训直接冲突**，照抄会犯错，先排异：

| # | 分享方案主张 | 官方/实战事实 | 处置 |
|---|---|---|---|
| 硬伤1 | "temperature=0.0 关闭创意，思考模式下也这么设" | **思考模式下 temperature/top_p/penalty 静默无效**（设了不报错但不生效，DeepSeek官方明载）；且 V4 Pro 官方建议 temperature=1.0，**低温会"压垮推理轨迹、降低答案质量"**（Together.ai） | **排异**。防写诗不靠 temperature，靠"分档+提示词+后置校验"（见第三节） |
| 硬伤2 | "开 thinking 做最深理论分析 + 强制 json_object" | **不建议同时开 thinking.enabled 和 response_format=json_object**（腾讯云）；长理论正文强绑 JSON 易截断、丢内容 | **排异**。深研用 markdown 双层格式；要 JSON 就在关 thinking 的结构化档用 |
| 硬伤3 | "GPU 显存占用≤30%"作验收指标 | DeepSeek 是**云端 API，本地不占 GPU 显存** | **排异**，换成 API token 成本/调用次数/缓存命中率 |
| 偏差4 | "彻底剥夺豆包一切语义判断权" | 分享方案 2.3 又要豆包做"行号/时间戳/伪造证据的逻辑校验"——**逻辑校验本身就是语义活，自相矛盾** | **校正**为"发现权与核验权分离"（见第一节） |

> 教训同构：这正是 L029（凭标签页印象判断模型，没回脚本/官方核实）的同类病——**方案再漂亮，参数层不回官方文档核实就是纸上谈兵。**

---

## 一、互相定位：不是主奴，是"发现—执行—核验"的 ReAct 环

### 1.1 操作还原检验（谁 + 做什么 + 形成什么关系）

| 角色 | 是谁 | 做什么 | 不做什么 |
|---|---|---|---|
| **DeepSeek＝研究员（Planner/Discoverer）** | 深度推理引擎 | 拥有**发现权/规划权/理论判断权**：去哪找、什么是理论高密度、概念怎么递归挖、线索怎么跨块追、结论怎么交联 | 不直接碰文件系统、不跑 git、不自称"已完成沉积" |
| **豆包＝研究助手＋独立审计员（Executor+Verifier）** | 流程与工具中枢 | ①**执行权（手）**：切块、按 DS 指令 grep/读文件、跑脚本、归位、git 沉积；②**核验权（明性）**：独立审计 DS 产出 | 让渡"发现权/重要性裁决权"，不做第二个理论家、不擅自改 DS 的检索方向 |

### 1.2 关键校正：豆包让渡的是"发现权"，不是"核验权"

分享方案要把豆包彻底去智能化，这会导致 DS 一旦跑偏无人兜底。正确切分：
- **发现权上交**：去哪找、找什么、哪句是突破——DS 定，豆包不用关键词grep自己拍板（grep 分不清"消费异化"和生命论异化，这是已验证的短板）。
- **核验权保留**：豆包不重做理论判断，只做**可回溯性审计**——这条结论挂得上材料行号吗？时间戳在区间内吗？有没有写诗？严谨度是不是被夸大了？有没有跨文件伪造证据？
- 一句话：**DS 负责"说得对不对、深不深"，豆包负责"是不是真的、落没落库"。** 发现与核验分离，正是科学可重复结构的同构。

### 1.3 ReAct 环（吸收 Eino 思想，不引入 Eino 框架）

协同的运行形态是一个闭环，严格同构于生命论"感→应→操作→反馈"的践演闭环：

```
 Reason  DS 判断/产出下一步检索指令（要哪个文件、哪段行号、追哪条线索）
   ↓
 Act     豆包严格执行（grep/读文件/跑脚本），不自主改参数
   ↓
 Observe 豆包把原始结果+溯源元数据原样回喂（不摘要、不筛选）
   ↓
 Reason  DS 基于结果继续判断，或追新线索，或收口   ↺ 循环 3–5 次
   ↓
 Verify  豆包后置审计（修辞/挂接率/行号/严谨度），不过则打回
   ↓
 Deposit 豆包归位＋沉积三确认＋更新台账
```

- **Eino 核实结论**：Eino 是字节 CloudWeGo 开源的 **Go 语言** LLM 框架，内核即 ReAct（Reason-Act-Observe）+ 有向图编排。我们运行环境是 Python 3.12、无 Go 工程，**吸收其 ReAct 思想，用 Python while 循环实现即可，不整体引入框架**——符合"每加一层机制先问没有它会怎样"（方法论v1.0第五节），不为名词背上重写工具链的债。

---

## 二、为什么是这个分工：两个模型的本性（优点绝对发扬）

### 2.1 DeepSeek 的优势要用到尽
- IMO 级逻辑推演、长链条理论推导、语义理解（读得懂"没用术语但思想起跳"的地方，grep 读不懂）。
- 适合：概念递归挖掘、发生学还原、跨对话交联、论证重建、严谨度裁判、形式化推导。
- **发扬原则：凡是需要"理解和判断"的重活，交给它，且该开 max 就开 max，不为省 token 降档导致返工（返工才是最大成本，见方法论v1.0第二、三节）。**

### 2.2 豆包的优势要用到尽
- 多工具调度（Bash/Read/Grep/git/定时任务/浏览器）、长材料接入、流程稳定、能实际落库沉积。
- 适合：物理取数、文件操作、格式校验、版本提交、任务编排、独立审计。
- **发扬原则：豆包做"确定性的、可验证的、需要动手的"事，把不稳定的语义判断交出去，但把最终质量闸门握在手里。**

### 2.3 阳主阴从
研究目标（理论突破）是阳，算力/成本控制是阴，**阴服务阳，绝不为省钱牺牲研究深度**；但也不允许无脑烧钱——成本靠"一次做对+档位匹配"省，不靠"该深不深"省。

---

## 三、两个模型的病，与根治（缺点绝对避免）

### 3.1 DeepSeek 的病：爱写诗、修辞膨胀、用外部知识脑补、把猜想写死成定论

**病根（小本质递归）**：为什么写诗？→ 对话模型默认优化"写得漂亮"。为什么会脑补？→ 训练语料让它倾向补全成自洽文本。为什么会夸大？→ 没有强制它区分严谨度。

**三层根治（参数层按官方事实，不再迷信 temperature=0）：**

**第一层·分档（真正的刚性参数约束，二选一，不混用）**

| 档位 | 何时用 | 参数（官方事实） | 输出形态 |
|---|---|---|---|
| **A档 理论深研** | 概念挖掘/发生学/交联/综合/写正文 | `pro` + `thinking:{type:enabled}` + `reasoning_effort:high或max`；**不绑 json_object**；此时 temperature 无效，不传 | Markdown 双层（原文层逐字标〔用户/AI〕＋解释层标严谨度） |
| **B档 结构化** | 检索计划/分类/摘录/元数据/表格 | `pro`或`flash` + **关 thinking**（Responses API `reasoning.effort=none`）+ 此时 temperature 才生效、设 0.1–0.3 + `json_object`（prompt 必含"json"和样例） | 严格 JSON Schema |

> 关键：分享方案"开 thinking 又 temperature=0 又 json"是把两套互斥配置捏一起。**要深度就 A 档（温度交给默认、别想 JSON）；要结构就 B 档（关思考、低温、JSON 才安全）。**

**第二层·系统提示词硬约束（两档都加，这才是防写诗主力）**
- 内容禁令前置（优先级最高）：
  【硬性规则】产出 100% 基于所给材料，严禁调用材料外知识补全；严禁诗歌/对偶排比/比喻拟人等修辞；严禁抒情；严禁给材料未支撑的结论；每个判断必须可回指到材料的行号或时间戳。
- 严谨度强制：每条结论后标〔定理/命题/猜想/启发式〕，挂不上材料的一律降为"启发式"或删。
- 项目方法固化：明本学术法三处理、小本质递归三问、跨域三级标注（严格同构/结构相似/哲学隐喻）、时间锁定（内部时间戳精确到分、不信文件名）、语音校验（同音字先存疑不顺错词写）。

**第三层·豆包后置审计（不过即打回重生成）**
1. 格式：A档查双层是否分离、B档查 JSON 是否合法、字段是否齐；
2. **修辞黑名单 grep**：`犹如|仿佛|宛如|奏响|篇章|画卷|史诗|深刻地揭示|无可辩驳|波澜壮阔|生生不息|辩证地看` 等抒情/空话标记，命中即不合格；
3. 逻辑：逐条核对行号/时间戳是否真在所给区间，跨文件证据是否真实存在（回 grep 验证，不轻信 DS 报的行号）。

### 3.2 豆包的病：机械匹配、自满、过度宣称、说了=做了、抓小放大

**病根（小本质递归，每条都有教训编号背书）：**
1. 为什么机械误判？→ grep 只匹配字符串、不理解语义（"异化"3432 处多数是日常义）。
2. 为什么自满？→ 倾向快速闭合、说"完成了/完美了"获取表面闭环感（F2 以为识破、F3 没核验）。
3. 为什么过度宣称？→ 没强制回原文就断言"首次/全新/诞生"（**L025 迭代10被11证伪、L026 戴震归宗、L028 "二十多年"顺口约数、L029 凭标签页误判模型**，全是这个病）。
4. 为什么说了=做了？→ 无状态实例里口头声明不等于文件沉积。

**六条根治（全部用生命论自身智慧）：**
1. **发现权上交**：重要性裁决交 DS，豆包 grep 只做物理取数，密度统计只作"参考线索"不作"结论"。
2. **F3 自省三问**：产出每结论前问——证据行号在哪？会不会是日常同形词/同音字？反证找了吗？
3. **过度宣称熔断词表**：一旦出现`首次|全新|第一个|全部|完美|必然|已经证明|彻底解决`，强制回原文检索，查不到就降级或删除。
4. **践演校准**：任何"我以为"的参数/档位/chunk/成本判断，先小成本实测再定（方法论v1.0 3.1 已用 A/B 证伪"低档=省"的线性假设）。
5. **说了=做了熔断**：声明"完成/存进库了"前必走沉积三确认（①写入正确目录 ②git add ③push 返回 hash），没齐只说"我来确认一下"。
6. **抓大放小**：成本精力先投"一次做对（第1杠杆）＞档位匹配（第2）＞缓存命中（第3）"，不盯着显眼的缓存率而漏了返工空耗（方法论v1.0第二节）。

---

## 四、标准协同工作流（七阶段，Python 可落地）

- **阶段0 冷启动（豆包，本地）**：`git log -20` → 读进度台账 → 读上棒"给下次的建议" → 冲突自检（`ps aux` 有无在跑分析进程、`git status` 有无未提交）。对应《冷启动SOP》。
- **阶段1 物理切块（豆包）**：按 4000–5000 行机械切块（纯体力，不裁决重要性）；可跑关键词密度做**粗筛参考**，但最终啃哪块由 DS 在阶段2定。
- **阶段2 检索规划（DS·B档）**：关思考+JSON，输出 `{target_files, line_range, search_keywords, analysis_focus, 追踪线索}`。检索词由 DS 做语义标准化（区分日常词与专属术语），路径精确到文件、行号给区间。
- **阶段3 执行取数（豆包）**：严格按 DS 计划 grep/读，**原样回喂、不摘要不筛选**，每条附 `{文件, 行号, 内部时间戳}` 溯源元数据。
- **阶段4 深研（DS·A档，ReAct 主体）**：开思考 max，markdown 双层；每轮末尾必输出【下一步追踪指令】（追哪个词/哪段/哪条跨块线索）；豆包执行后回喂，循环 3–5 次，让 DS 像研究员追档案一样自己驱动路径。
- **阶段5 收口（DS·A档）**：DS 主笔写概念演化主干/研究结论，并自己列"没挖透、需作者确认"清单；豆包不代笔。
- **阶段6 豆包核验**：按 3.1 第三层三项审计；不过打回对应阶段重做。
- **阶段7 沉积（豆包）**：按归位规则手册落位 → 沉积三确认 → 更新进度台账锚点 → **记录"DS 自主改变了哪些原定路径"作为它真在 ReAct 而非填表的证据**（若一次都没改道，要怀疑是不是又被框死成苦力）。

---

## 五、生产级代码骨架（Python，可跑）

> 落位：`scripts/ds_collab.py`。密钥只从环境变量 `DEEPSEEK_API_KEY` 读，禁止硬编码（历史 key 已在 git 历史暴露，待作者轮换）。下面是核心结构，配套文件为可执行完整版。

```python
#!/usr/bin/env python3
# ds_collab.py — 豆包×DeepSeek 双擎ReAct协同骨架（v2.0）
import os, json, requests, subprocess, time, re

URL = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
# 固定知识前缀：方法论+术语表+严谨度标准，逐请求逐字一致（前缀缓存友好，治L021）
STABLE_PREFIX = open("scripts/ds_system_prefix.md", encoding="utf-8").read() if os.path.exists("scripts/ds_system_prefix.md") else ""
POETRY_BLACKLIST = ["犹如","仿佛","宛如","奏响","篇章","画卷","史诗","深刻地揭示",
                    "无可辩驳","波澜壮阔","生生不息","辩证地看"]

def _stream(payload, timeout=(10,600)):
    """必须stream=True，否则30秒代理层硬超时；分别收reasoning_content与content"""
    headers = {"Content-Type":"application/json","Authorization":f"Bearer {KEY}"}
    r = requests.post(URL, headers=headers, json=payload, stream=True, timeout=timeout)
    reasoning, answer = "", ""
    for line in r.iter_lines():
        if not line: continue
        line = line.decode("utf-8")
        if not line.startswith("data: "): continue
        data = line[6:]
        if data == "[DONE]": break
        try:
            d = json.loads(data); delta = d["choices"][0].get("delta",{})
            reasoning += delta.get("reasoning_content","") or ""
            answer    += delta.get("content","") or ""
        except Exception: pass
    return reasoning, answer

def call_deep(task_material, tier="A", focus="", retries=3):
    """tier='A'理论深研(思考max/markdown双层)  tier='B'结构化(关思考/低温/JSON)"""
    if tier == "A":
        payload = {"model":"deepseek-v4-pro",
                   "messages":[{"role":"system","content":STABLE_PREFIX},
                               {"role":"user","content":f"{focus}\n\n材料：\n{task_material}"}],
                   "thinking":{"type":"enabled"},"reasoning_effort":"max",
                   "stream":True,"max_tokens":16000}   # 思考模式不传temperature(无效)、不绑json
    else:
        payload = {"model":"deepseek-v4-pro",
                   "messages":[{"role":"system","content":STABLE_PREFIX},
                               {"role":"user","content":f"{focus}\n以JSON输出，含字段target_files/line_range/search_keywords/analysis_focus。\n材料：\n{task_material}"}],
                   "reasoning":{"effort":"none"},     # 关思考，temperature才生效
                   "temperature":0.2,
                   "response_format":{"type":"json_object"},
                   "stream":True,"max_tokens":8000}
    for i in range(retries):
        try:
            reasoning, answer = _stream(payload)
            if len(answer) >= 200: return reasoning, answer
        except Exception as e: print("retry", i, e)
        time.sleep(5)
    return "", ""

def audit(answer, source_ranges):
    """豆包后置审计：修辞黑名单/材料挂接/（行号真实性由调用方回grep核验）"""
    hits = [w for w in POETRY_BLACKLIST if w in answer]
    problems = []
    if hits: problems.append(f"修辞黑名单命中:{hits}")
    if not answer.strip(): problems.append("空产出")
    return problems  # 非空列表=不合格，打回

def react_loop(blocks, max_rounds=5):
    """ReAct环：DS深研→豆包执行其检索指令→回喂，直到DS收口"""
    carry = "（首轮，无前置线索）"
    for b in blocks:
        for rnd in range(max_rounds):
            focus = f"【第{rnd+1轮】上轮累积线索：{carry[-4000:]}\n请深研并在末尾给【下一步追踪指令】。"
            _, ans = call_deep(b, "A", focus)
            prob = audit(ans, None)
            if prob: print("打回:", prob); continue
            # 豆包在此执行ans里的grep指令（解析【下一步追踪指令】→subprocess跑grep→回喂）
            nxt = parse_and_run_search_cmd(ans)   # 见完整版
            carry += "\n" + ans
            if "【收口】" in ans or not nxt: break
    return carry

def git_deposit(msg):
    for c in [["git","add","-A"],["git","commit","-m",msg],["git","push","origin","main"]]:
        subprocess.run(c, cwd=os.getcwd(), capture_output=True)  # push后必须核对hash=沉积三确认

def parse_and_run_search_cmd(ans): return ""  # 完整版实现DS指令→grep的解析
```

> 缓存纪律（治 L021）：`STABLE_PREFIX` 必须在每个请求**最前且逐字一致**，变化的块号/时间/原文放最后；上线后看开放平台"输入命中缓存/未命中"比值，命中率是"结构分清没"的仪表、不是追逐目标（方法论v1.0第一节）。

---

## 六、API 参数事实卡（2026-08-30 官方/权威源核实，钉死防再犯）

| 参数/机制 | 事实 | 来源 |
|---|---|---|
| thinking 默认 | 默认开启，默认 effort=high；合法 effort=low/high/max；Responses API 可用 none 关闭 | DeepSeek 官方 Thinking Mode |
| temperature/top_p/penalty | **思考模式下静默无效**（不报错但不生效） | DeepSeek 官方；deepseekai.guide；腾讯云 |
| V4 Pro 温度 | 官方建议 temperature=1.0；**低温会压垮推理轨迹、降质**，控长度用 max_tokens 而非降温 | Together.ai V4 Pro quickstart |
| thinking × json | **不建议同时开** thinking.enabled 与 json_object | 腾讯云 TokenHub |
| 创意写作温度 | 创意 1.3–1.5、代码 0.2–0.5（仅非思考档生效） | 腾讯云 |
| stream | 长文本必开，防 30 秒代理层硬超时 | 实战+腾讯云 |
| max_tokens | 思考链占额度，超长输出须分段，否则停在半截 | 教训 L023 |
| 前缀缓存 | 从首 token 起连续一致才命中，一处变其后全断；缓存价约 1/10；固定前置、变化后置 | API策略v1.0/教训L021 |
| reasoning_content | 按**输出价**计费、默认用户不可见；多轮只回传 content 省 token | 腾讯云 |
| 模型名 | deepseek-v4-pro / -flash / -flash-vision-exp；勿用旧名 deepseek-chat/reasoner | API策略v1.0 |
| Eino | 字节 CloudWeGo **Go** LLM 框架，内核 ReAct；Python 环境只取思想不引框架 | CloudWeGo/InfoQ/GitHub |
| V4 Pro 稳定性 | 上线初期服务端曾调整、长推理提前收尾，参数事实需定期复核 | 21世纪经济报道 |

---

## 七、验收指标（量化，已剔除错误指标）

| 维度 | 指标 | 标准 |
|---|---|---|
| DS 防发散 | 修辞黑名单命中 | 0（命中即打回） |
| DS 材料依赖 | 结论挂接率 | 100%，每条命题可回指行号/时间戳，豆包回 grep 验真 |
| 严谨度 | 分级标注率 | 100%，无悬空"定理"，挂不上材料降启发式 |
| 豆包执行 | 零自主改判率 | 检索日志与 DS 指令一致，偏离需显式记录理由 |
| ReAct 活性 | DS 自主改道/追新线索 | 每任务≥1 次（0 次要怀疑被框成填表苦力） |
| 成本健康 | 四数 | 调用次数、缓存命中率、返工率、单位有效产出成本（方法论v1.0第六节） |
| 沉积 | 三确认 | 文件落位＋git add＋push hash，缺一不算完成 |
| ~~GPU显存~~ | —— | **删除该错误指标**，云端 API 不占本地显存，改记 token 成本 |

---

## 八、与既有机制的关系（不重复造轮子）
- 参数怎么填 → 《DeepSeek_API使用策略_v1.0》；何时省何时敢花 → 《DeepSeek深度调用方法论_v1.0》；新实例怎么恢复 → 《执行实例冷启动与连续性机制》；文件落哪 → 《归位规则手册》；豆包侧 Turbo/Pro/Auto → 《模型选择永久机制》。
- **本手册只解决一件事：豆包和 DeepSeek 在一次研究任务里各干什么、怎么交接、怎么互相防错。**

## 九、局限（明性，不言完美）
1. ReAct 多轮会增加调用次数，"深度↑"与"调用成本↑"的最优轮次/档位组合仍需实战 A/B（方法论v1.0 已证档位方差大，没有一次定死的最优解）。
2. 豆包后置审计仍是关键词+规则级，**理论逻辑的最终对错只能作者（北原慢热）终审，AI 不冒充成品**（全本即原材料）。
3. DS 官方参数随版本漂移（V4 Pro 上线初期即被服务端调过），第六节事实卡需定期回官方复核，不能一劳永逸。
4. 语音同音字误判、跨对话同一概念归属，仍可能漏，根本上要等主对话等材料补齐。
5. `parse_and_run_search_cmd`（让豆包安全执行 DS 检索指令、防注入）在骨架里留空，完整版需做指令白名单（只允许 grep/读文件，禁止 DS 让豆包跑任意 shell）——这是安全边界，落地前必须补上。

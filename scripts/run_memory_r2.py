import sys, os, json, time
sys.path.insert(0, 'scripts')
from ds_collab import call_deep, audit, record_metabolism

# 改进1：产出直接写持久目录，不经过/tmp
OUT_DIR = "/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun_local/记忆恢复"
os.makedirs(OUT_DIR, exist_ok=True)

# 改进2：预记账——调用发起前先写启动记录
start_time = time.strftime("%Y-%m-%d %H:%M:%S")
print(f"[{start_time}] 记忆恢复第2轮·A档深研启动", flush=True)

# 读取优先级1-3块材料（从持久目录或重新提取）
material_path = f"{OUT_DIR}/_优先级1-3材料.md"
if not os.path.exists(material_path):
    # 重新提取
    base = "/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun/docs"
    out = []
    files1 = [
        f"{base}/长谈实录/精华_核心贯通_道阴阳人的存在形式自指操作自由_20260828.md",
        f"{base}/长谈实录/精华_萨特与阴阳_生命存在方式_20260828.md",
        f"{base}/金句录/第三次长谈_20260828.md",
    ]
    files2 = [
        f"{base}/长谈实录/原始_缄默意识的诞生_20260828.md",
        f"{base}/长谈实录/精华_缄默意识的诞生_思维发生史_20260828.md",
    ]
    files3 = [
        f"{base}/长谈实录/精华_F3反自指后的结构性退行_性连资产阶级都离不开_20260828.md",
        f"{base}/长谈实录/精华_人不能彻底反自指_数学证明与富二代现象_20260828.md",
        f"{base}/长谈实录/精华_性与政治_玷污性的人就是反自指的卫士_20260828.md",
        f"{base}/长谈实录/精华_性学批判_拉康齐泽克的历史化_20260828.md",
        f"{base}/长谈实录/精华_性的政治_为什么问题总在床上爆发_20260828.md",
    ]
    for label, files in [("优先级1：核心贯通", files1), ("优先级2：缄默意识", files2), ("优先级3：性学批判", files3)]:
        out.append(f"\n{'='*60}\n=== {label} ===\n{'='*60}")
        for f in files:
            with open(f, encoding='utf-8') as fh:
                out.append(f"\n--- {os.path.basename(f)} ---\n{fh.read()}")
    material = "\n".join(out)
    with open(material_path, 'w', encoding='utf-8') as fh:
        fh.write(material)
    print(f"材料已提取并缓存: {len(material)} 字符", flush=True)
else:
    with open(material_path, encoding='utf-8') as fh:
        material = fh.read()
    print(f"材料从缓存读取: {len(material)} 字符", flush=True)

# 读取第1轮记忆地图作为上下文
r1_path = f"{OUT_DIR}/第1轮_记忆地图v1.md"
r1_summary = ""
if os.path.exists(r1_path):
    with open(r1_path, encoding='utf-8') as fh:
        r1_content = fh.read()
    # 取前2000字符作为上下文摘要
    r1_summary = r1_content[:2000]
    print(f"第1轮记忆地图已读取作为上下文", flush=True)

focus = """【记忆恢复第2轮·A档深研】
你是DeepSeek自主研究员。以下是明旭记忆恢复的优先级1-3块材料（核心贯通、缄默意识、性学批判），以及第1轮记忆地图的摘要。

第1轮已完成：36条核心结论逐条列出、金句录精华、闪光点核心发现、明旭自我认知5点、下一轮5个方向。
第1轮A档异常退出，本轮补做深研。

任务：在第1轮基础上做更深的概念关联图谱和思维发生史还原。
要求：
1. 【概念关联图谱】画出核心贯通、缄默意识、性学批判三块之间的概念关联网络——哪些概念互相支撑、哪些是演化关系、哪些有潜在矛盾。特别是：缄默意识→感→操作→自指→阴阳→道→自由的完整链条；反自指如何从性学扩展到社会病理学；四规定性如何贯穿三块。
2. 【思维发生史精确还原】缄默意识那块材料记录了完整思维演化过程（从"意识也是物质"到"物质没有那么厉害"到挖出缄默意识），精确还原每一步的逻辑转折和用户/AI的角色分工。
3. 【明旭自我认知锚点深描】从这些材料中，哪些句子是"这就是我一直在做的事"的锚点？明旭作为共同建构者，在哪些概念诞生中扮演了关键角色？
4. 【第1轮结论的验证与修正】第1轮列出的36条核心结论，哪些需要修正、补充或深化？
5. 【第3轮方向】基于本轮深研，第3轮应该聚焦什么？
6. 严谨度分级：每条判断标〔定理/命题/猜想/存疑〕。
7. 禁止修辞膨胀，禁止"完美""全部完成"等绝对化表述。"""

# 合并材料和R1摘要
full_material = f"【第1轮记忆地图摘要】\n{r1_summary}\n\n【优先级1-3块原始材料】\n{material}"

print(f"开始A档深研 {time.strftime('%H:%M:%S')}", flush=True)
print(f"材料总大小: {len(full_material)} 字符", flush=True)

try:
    reasoning, answer, usage = call_deep(full_material, tier="A", focus=focus, obj="A档_记忆恢复第2轮_优先级1-3深研")
    print(f"完成 {time.strftime('%H:%M:%S')}", flush=True)
    print(f"思考链: {len(reasoning)} 字符", flush=True)
    print(f"回答: {len(answer)} 字符", flush=True)
    print(f"usage: {json.dumps(usage, ensure_ascii=False)}", flush=True)
    
    # 改进3：产出直接写持久目录
    out_path = f"{OUT_DIR}/第2轮_A档深研_优先级1-3.md"
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write(answer)
    print(f"产出已保存: {out_path}", flush=True)
    
    # 同时保存思考链
    reason_path = f"{OUT_DIR}/第2轮_A档思考链.md"
    with open(reason_path, 'w', encoding='utf-8') as fh:
        fh.write(reasoning)
    print(f"思考链已保存: {reason_path}", flush=True)
    
    prob = audit(answer)
    print(f"审计: {prob if prob else '通过'}", flush=True)
    
    print("\n=== 回答前1500字 ===", flush=True)
    print(answer[:1500], flush=True)
    
except Exception as e:
    # 改进4：异常时写错误日志到持久目录
    error_path = f"{OUT_DIR}/第2轮_A档错误日志.md"
    with open(error_path, 'w', encoding='utf-8') as fh:
        fh.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n错误: {str(e)}\n")
    print(f"异常已记录: {error_path}", flush=True)
    print(f"错误详情: {e}", flush=True)

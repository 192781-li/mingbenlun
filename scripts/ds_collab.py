#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ds_collab.py — 豆包×DeepSeek 双擎 ReAct 协同（配套《豆包×DeepSeek协同作战手册_v2.0》）

分工铁律：
  DeepSeek=研究员（发现权/规划权/理论判断权）；豆包=执行手+独立审计员。
  A档=理论深研(pro+thinking max+markdown双层，不传temperature、不绑json)
  B档=结构化  (关thinking+低温0.2+json_object，仅检索计划/分类/摘录)

安全边界：DeepSeek 给的"下一步检索指令"只允许走白名单（按行读文件/grep固定词），
         禁止任意 shell，防提示注入。

用法：
  export DEEPSEEK_API_KEY=sk-xxxx
  python3 ds_collab.py plan   <file> [line_a line_b]   # B档：让DS出检索计划(JSON)
  python3 ds_collab.py deep   <file> <line_a> <line_b> # A档：深研一块
  python3 ds_collab.py react  <manifest.json>         # ReAct多轮（manifest列块）
密钥只从环境变量读，禁止硬编码。
"""
import os, sys, json, time, subprocess, re
import requests

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
BASE = "/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun"
PREFIX_PATH = os.path.join(BASE, "scripts", "ds_system_prefix.md")
STABLE_PREFIX = open(PREFIX_PATH, encoding="utf-8").read() if os.path.exists(PREFIX_PATH) else ""

# 修辞/空话黑名单（豆包后置审计，命中即打回）
POETRY_BLACKLIST = ["犹如", "仿佛", "宛如", "奏响", "篇章", "画卷", "史诗",
                    "深刻地揭示", "无可辩驳", "波澜壮阔", "生生不息", "辩证地看",
                    "浓墨重彩", "熠熠生辉", "波澜起伏"]
# 过度宣称熔断词
OVERCLAIM = ["首次", "全新", "第一个", "全部解决", "完美", "必然证明", "彻底解决", "已经证明"]


# ---------- 底层：stream 分别收 reasoning_content / content ----------
def _stream(payload, timeout=(10, 600), retries=3):
    if not KEY:
        raise RuntimeError("未设置环境变量 DEEPSEEK_API_KEY")
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {KEY}"}
    last = ""
    for att in range(retries):
        try:
            r = requests.post(API, headers=headers, json=payload,
                              stream=True, timeout=timeout)
            reasoning, answer = "", ""
            for line in r.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8")
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                d = json.loads(data)
                delta = d["choices"][0].get("delta", {})
                reasoning += delta.get("reasoning_content", "") or ""
                answer += delta.get("content", "") or ""
            if answer.strip():
                return reasoning, answer
            last = f"空回答(att{att+1})"
        except Exception as e:
            last = str(e)
        time.sleep(5)
    return "", f"[调用失败:{last}]"


def call_deep(material, tier="A", focus=""):
    """tier A=深研  B=结构化。参数严格按2026-08-30官方事实卡。"""
    common_sys = STABLE_PREFIX
    if tier == "A":
        payload = {
            "model": "deepseek-v4-pro",
            "messages": [
                {"role": "system", "content": common_sys},
                {"role": "user", "content":
                    f"{focus}\n\n【本块原始材料】\n{material}"}],
            "thinking": {"type": "enabled"},
            "reasoning_effort": "max",
            "stream": True, "max_tokens": 16000,
            # 思考模式：不传 temperature/top_p（静默无效），不绑 json_object
        }
    else:
        payload = {
            "model": "deepseek-v4-pro",
            "messages": [
                {"role": "system", "content": common_sys},
                {"role": "user", "content":
                    f"{focus}\n只输出JSON。\n\n【材料】\n{material}"}],
            "reasoning": {"effort": "none"},      # 关思考，温度才生效
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "stream": True, "max_tokens": 8000,
        }
    return _stream(payload)


# ---------- 豆包侧：安全取数（白名单，不执行任意shell） ----------
def read_lines(path, a, b):
    if not os.path.isfile(path):
        return f"[文件不存在:{path}]"
    with open(path, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    a, b = max(1, a), min(len(lines), b)
    return "".join(lines[a-1:b])

def safe_grep(path, keyword, ctx=0):
    """只允许在指定文件内grep固定字符串，禁止正则注入到shell。"""
    if not os.path.isfile(path):
        return f"[文件不存在:{path}]"
    out = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        ls = f.readlines()
    for i, l in enumerate(ls):
        if keyword in l:
            s, e = max(0, i-ctx), min(len(ls), i+ctx+1)
            out.append(f"L{i+1}: " + "".join(ls[s:e]).strip())
    return "\n".join(out[:60]) if out else f"[未命中:{keyword}]"

# DS检索指令格式：SEARCH file=... kw=...  或  READ file=... a=... b=...
_CMD = re.compile(r"(SEARCH|READ)\s+file=(\S+)(?:\s+kw=(.+?))?(?:\s+a=(\d+)\s+b=(\d+))?$", re.M)
def parse_and_run_search_cmd(ds_text):
    """解析DS的【下一步追踪指令】，白名单执行，返回回喂文本；不跑任意shell。"""
    block = ""
    m = re.search(r"【下一步追踪指令】(.*?)(?:【|$)", ds_text, re.S)
    if not m:
        return "", False
    cmd_text = m.group(1)
    fed, any_cmd = [], False
    for c in re.finditer(r"(SEARCH|READ)\s+file=(\S+)(?:\s+kw=(\S+))?(?:\s+a=(\d+)\s+b=(\d+))?", cmd_text):
        any_cmd = True
        op, rel, kw, a, b = c.groups()
        path = rel if os.path.isabs(rel) else os.path.join(BASE, rel)
        # 路径必须在库内，防越界
        if not os.path.abspath(path).startswith(BASE):
            fed.append(f"[拒绝越界路径:{rel}]"); continue
        if op == "SEARCH" and kw:
            fed.append(f"### 检索 {rel} 关键词「{kw}」\n" + safe_grep(path, kw))
        elif op == "READ" and a and b:
            fed.append(f"### 取段 {rel} L{a}-{b}\n" + read_lines(path, int(a), int(b)))
    return "\n\n".join(fed), any_cmd


# ---------- 豆包后置审计 ----------
def audit(answer):
    problems = []
    hits = [w for w in POETRY_BLACKLIST if w in answer]
    if hits:
        problems.append(f"修辞/空话黑名单命中:{hits}")
    oc = [w for w in OVERCLAIM if w in answer]
    if oc:
        problems.append(f"过度宣称词需回原文核实:{oc}")
    # 严谨度标注粗检：出现结论性段落却没有任何严谨度标记
    if len(answer) > 800 and not re.search(r"(定理|命题|猜想|启发式)", answer):
        problems.append("未见严谨度分级标注")
    return problems


# ---------- ReAct 主循环 ----------
def react(manifest_path, max_rounds=5):
    mani = json.load(open(manifest_path, encoding="utf-8"))
    carry = "（首轮，无前置线索）"
    log = []
    for blk in mani["blocks"]:
        path = os.path.join(BASE, blk["file"])
        material = read_lines(path, blk["a"], blk["b"])
        detour = 0
        for rnd in range(max_rounds):
            focus = (f"【第{rnd+1}轮】累积线索：{carry[-4000:]}\n"
                     "深研本块；若需豆包取数，末尾按格式给【下一步追踪指令】"
                     "（SEARCH file=相对路径 kw=词  /  READ file=相对路径 a=行 b=行）；"
                     "无需再取数、结论已完整时，末尾写【收口】。")
            reasoning, ans = call_deep(material, "A", focus)
            if ans.startswith("[调用失败"):
                log.append(f"{blk} r{rnd} 调用失败:{ans}"); break
            prob = audit(ans)
            if prob:
                log.append(f"{blk} r{rnd} 审计打回:{prob}（重试）")
                focus += "\n上轮不合格（%s），请去除修辞、补严谨度分级后重做。" % prob
                continue
            fed, any_cmd = parse_and_run_search_cmd(ans)
            if any_cmd:
                detour += 1
                material = material + "\n\n【按你的指令取回的材料】\n" + fed
                carry += "\n" + ans
                continue  # 带着新材料再进一轮=ReAct
            carry += "\n" + ans
            break
        log.append(f"{blk['file']} L{blk['a']}-{blk['b']} 完成，DS自主追取{detour}次")
    out = manifest_path.replace(".json", "_result.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# ReAct协同产出\n\n" + carry +
                "\n\n---\n## 执行日志\n" + "\n".join(log))
    print("产出:", out); print("\n".join(log))
    return out


def git_deposit(msg):
    for c in [["git", "add", "-A"], ["git", "commit", "-m", msg]]:
        subprocess.run(c, cwd=BASE, capture_output=True)
    p = subprocess.run(["git", "push", "origin", "main"], cwd=BASE,
                       capture_output=True, text=True)
    print(p.stdout[-300:], p.stderr[-300:])  # push后核对hash=沉积三确认之③


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    mode = sys.argv[2] if sys.argv[1] in ("plan", "deep") and len(sys.argv) > 2 else None
    if sys.argv[1] == "react":
        react(sys.argv[2])
    elif sys.argv[1] in ("plan", "deep"):
        f = sys.argv[2]
        a = int(sys.argv[3]); b = int(sys.argv[4])
        tier = "B" if sys.argv[1] == "plan" else "A"
        material = read_lines(os.path.join(BASE, f), a, b)
        focus = "输出结构化检索计划JSON" if tier == "B" else "做生命论深度理论分析，markdown双层（原文层标〔用户/AI〕＋解释层标严谨度）"
        r, ans = call_deep(material, tier, focus)
        print("=== reasoning %d字 ===" % len(r))
        print(ans)
        print("=== 审计 ===", audit(ans))

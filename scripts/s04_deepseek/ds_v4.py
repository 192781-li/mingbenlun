#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek V4 客户端（S04 形式化专用）—— 2026-09-03 三轮原地打磨产物，工程化入库。
基于实测（非记忆）：
  - deepseek-chat/reasoner 旧名已路由到 deepseek-v4-flash；可直接点名 v4-flash/v4-pro
  - V4: 上下文 1M, 最大输出 384K；thinking 显式开关；reasoning_content 单独返回且占 completion 额度
  - 历史"空输出"真相：思考模式 max_tokens 给小，reasoning 吃光额度 -> content 空 / finish=length
机制：thinking 开关 / 人民币定价 / reasoning 单独存档 / length 自动续跑去接缝 / JSON+CSV 留痕
路径与 key 全部走 _paths.py（环境变量可覆盖），不写死机器目录。
"""
import json, time, os, csv, urllib.request
from datetime import datetime
from _paths import read_api_key, TRACE_DIR, METABOLISM_CSV

URL = "https://api.deepseek.com/chat/completions"

# V4 人民币定价（元/百万 token），官方 pricing 2026-09-03；若官方调价，改这里并注明日期
PRICING = {
    "deepseek-v4-flash": {"hit": 0.02, "miss": 1.0, "out": 2.0},
    "deepseek-v4-pro":   {"hit": 0.025,"miss": 3.0, "out": 6.0},
    "deepseek-chat":     {"hit": 0.02, "miss": 1.0, "out": 2.0},   # 旧别名→flash
    "deepseek-reasoner": {"hit": 0.02, "miss": 1.0, "out": 2.0},
}

def _join_overlap(a, b, max_ol=24):
    """拼接续写段：消除 a 尾部与 b 头部的最长重叠（治 '15,,16' 类接缝）。"""
    if not a: return b
    if not b: return a
    cap = min(max_ol, len(a), len(b))
    for k in range(cap, 0, -1):
        if a[-k:] == b[:k]:
            return a + b[k:]
    return a + b

def _one_request(model, messages, max_tokens, temperature, thinking, timeout):
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens,
               "temperature": temperature, "thinking": {"type": thinking}}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {read_api_key()}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def chat(messages, model="deepseek-v4-flash", thinking="enabled",
         max_tokens=32000, temperature=0.1, task_name="task",
         auto_continue=True, max_continues=6, timeout=600, save=True):
    """返回 dict: content, reasoning, usage(累加), cost_yuan, status, rounds, finish, trace_file"""
    t0 = time.time(); convo = list(messages)
    content, reasoning, segs = "", "", []
    tot = {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0,
           "prompt_cache_hit_tokens":0,"prompt_cache_miss_tokens":0,"reasoning_tokens":0}
    rounds = 0; final_fin = None
    while True:
        rounds += 1
        res = _one_request(model, convo, max_tokens, temperature, thinking, timeout)
        ch = res["choices"][0]; msg = ch.get("message",{}); fin = ch.get("finish_reason")
        ct = msg.get("content") or ""; rs = msg.get("reasoning_content") or ""
        content = _join_overlap(content, ct)
        reasoning = (reasoning + ("\n" if reasoning and rs else "") + rs)
        segs.append({"finish":fin,"content":ct,"reasoning":rs})
        u = res.get("usage",{})
        for k in ("prompt_tokens","completion_tokens","total_tokens",
                  "prompt_cache_hit_tokens","prompt_cache_miss_tokens"):
            tot[k] += u.get(k,0)
        tot["reasoning_tokens"] += u.get("completion_tokens_details",{}).get("reasoning_tokens",0)
        final_fin = fin
        if not (auto_continue and fin == "length" and rounds <= max_continues):
            break
        convo = convo + [
            {"role":"assistant","content":ct},
            {"role":"user","content":"你上一段在 max_tokens 处被截断。请从断点直接继续输出，不要重复已有内容，不要寒暄，直接续写。"}]
    price = PRICING.get(model, PRICING["deepseek-v4-flash"])
    cost = (tot["prompt_cache_hit_tokens"]/1e6*price["hit"]
            + tot["prompt_cache_miss_tokens"]/1e6*price["miss"]
            + tot["completion_tokens"]/1e6*price["out"])
    status = "success" if content.strip() else ("empty_output" if final_fin!="length" else "still_truncated")
    out = {"timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"task_name":task_name,
           "model":model,"thinking":thinking,"rounds":rounds,"finish":final_fin,"status":status,
           "elapsed_s":round(time.time()-t0,2),"usage":tot,"cost_yuan":round(cost,5),
           "content":content,"reasoning":reasoning,"segments":len(segs)}
    if save: _save(out, messages, segs)
    return out

def _save(out, messages, segs):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fp = TRACE_DIR / f"{ts}_{out['status']}_{out['task_name'][:30].replace(' ','_')}.json"
    with open(fp,"w",encoding="utf-8") as f:
        json.dump({"info":{k:v for k,v in out.items() if k not in ('content','reasoning')},
                   "messages":messages,"full_content":out["content"],
                   "full_reasoning":out["reasoning"],"segments":segs}, f, ensure_ascii=False, indent=2)
    fe = METABOLISM_CSV.exists()
    METABOLISM_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(METABOLISM_CSV,"a",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f)
        if not fe or METABOLISM_CSV.stat().st_size==0:
            w.writerow(["时间","实例","模型","档位","对象","缓存命中输入","未命中输入","输出",
                        "重试次数","状态","耗时秒","总费用","缓存命中率","finish_reason","任务名"])
        u=out["usage"]; ti=u["prompt_cache_hit_tokens"]+u["prompt_cache_miss_tokens"]
        w.writerow([out["timestamp"],"S04",out["model"],
                    "A" if out["thinking"]=="enabled" else "B",out["task_name"],
                    u["prompt_cache_hit_tokens"],u["prompt_cache_miss_tokens"],u["completion_tokens"],
                    out["rounds"]-1,out["status"],out["elapsed_s"],out["cost_yuan"],
                    round(u["prompt_cache_hit_tokens"]/ti,4) if ti else 0,out["finish"],out["task_name"]])
    out["trace_file"]=str(fp)

if __name__ == "__main__":
    import sys
    if "--live" not in sys.argv:
        print("离线模式：不发起付费调用。加 --live 做一次真实自测（flash非思考 + pro思考）。")
        sys.exit(0)
    r=chat([{"role":"user","content":"只回答两个字：正常"}],model="deepseek-v4-flash",
           thinking="disabled",max_tokens=200,task_name="selftest_flash")
    print("flash:",r["status"],repr(r["content"][:40]),"cost",r["cost_yuan"])
    r=chat([{"role":"user","content":"用一句话说明 Coq 里 revert 再 induction 的作用。"}],
           model="deepseek-v4-pro",thinking="enabled",max_tokens=2000,task_name="selftest_pro")
    print("pro:",r["status"],"reason?",bool(r["reasoning"]),repr(r["content"][:60]),"cost",r["cost_yuan"])

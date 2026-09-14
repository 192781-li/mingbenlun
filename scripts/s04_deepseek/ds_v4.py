#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek V4 瀹㈡埛绔紙S04 褰㈠紡鍖栦笓鐢級鈥斺€?2026-09-03 涓夎疆鍘熷湴鎵撶（浜х墿锛屽伐绋嬪寲鍏ュ簱銆?鍩轰簬瀹炴祴锛堥潪璁板繂锛夛細
  - deepseek-chat/reasoner 鏃у悕宸茶矾鐢卞埌 deepseek-v4-flash锛涘彲鐩存帴鐐瑰悕 v4-flash/v4-pro
  - V4: 涓婁笅鏂?1M, 鏈€澶ц緭鍑?384K锛泃hinking 鏄惧紡寮€鍏筹紱reasoning_content 鍗曠嫭杩斿洖涓斿崰 completion 棰濆害
  - 鍘嗗彶"绌鸿緭鍑?鐪熺浉锛氭€濊€冩ā寮?max_tokens 缁欏皬锛宺easoning 鍚冨厜棰濆害 -> content 绌?/ finish=length
鏈哄埗锛歵hinking 寮€鍏?/ 浜烘皯甯佸畾浠?/ reasoning 鍗曠嫭瀛樻。 / length 鑷姩缁窇鍘绘帴缂?/ JSON+CSV 鐣欑棔
璺緞涓?key 鍏ㄩ儴璧?_paths.py锛堢幆澧冨彉閲忓彲瑕嗙洊锛夛紝涓嶅啓姝绘満鍣ㄧ洰褰曘€?"""
import json, time, os, csv, socket, ssl, urllib.request
from urllib.error import URLError, HTTPError
from http.client import IncompleteRead, RemoteDisconnected
from datetime import datetime
from _paths import read_api_key, TRACE_DIR, METABOLISM_CSV

URL = "https://api.deepseek.com/chat/completions"

# 鍙畨鍏ㄩ噸璇曠殑缃戠粶/鏈嶅姟绔灛鏃跺紓甯革紙chat completion 鏃犵姸鎬侊紝鍚岃姹傞噸鍙戝箓绛夛級
_NET_ERR = (ConnectionResetError, ConnectionAbortedError, BrokenPipeError,
            TimeoutError, socket.timeout, URLError, IncompleteRead,
            RemoteDisconnected, ssl.SSLError, OSError)
_RETRY_HTTP = (429, 500, 502, 503, 504)
_MAX_NET_RETRY = 5

# V4 浜烘皯甯佸畾浠凤紙鍏?鐧句竾 token锛夛紝瀹樻柟 pricing 2026-09-03锛涜嫢瀹樻柟璋冧环锛屾敼杩欓噷骞舵敞鏄庢棩鏈?PRICING = {
    "deepseek-v4-flash": {"hit": 0.02, "miss": 1.0, "out": 2.0},
    "deepseek-v4-pro":   {"hit": 0.025,"miss": 3.0, "out": 6.0},
    "deepseek-chat":     {"hit": 0.02, "miss": 1.0, "out": 2.0},   # 鏃у埆鍚嶁啋flash
    "deepseek-reasoner": {"hit": 0.02, "miss": 1.0, "out": 2.0},
}

def _join_overlap(a, b, max_ol=24):
    """鎷兼帴缁啓娈碉細娑堥櫎 a 灏鹃儴涓?b 澶撮儴鐨勬渶闀块噸鍙狅紙娌?'15,,16' 绫绘帴缂濓級銆?""
    if not a: return b
    if not b: return a
    cap = min(max_ol, len(a), len(b))
    for k in range(cap, 0, -1):
        if a[-k:] == b[:k]:
            return a + b[k:]
    return a + b

def _one_request(model, messages, max_tokens, temperature, thinking, timeout, _attempt=0):
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens,
               "temperature": temperature, "thinking": {"type": thinking}}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {read_api_key()}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except HTTPError as e:
        retryable = e.code in _RETRY_HTTP
        if retryable and _attempt < _MAX_NET_RETRY:
            wait = min(2 ** (_attempt + 1), 30)
            print(f"[net] HTTP {e.code}锛寋wait}s 鍚庣 {_attempt+2} 娆￠噸璇?, flush=True)
            time.sleep(wait)
            return _one_request(model, messages, max_tokens, temperature, thinking, timeout, _attempt+1)
        raise
    except _NET_ERR as e:
        if _attempt < _MAX_NET_RETRY:
            wait = min(2 ** (_attempt + 1), 30)
            print(f"[net] 杩炴帴寮傚父 {type(e).__name__}锛寋wait}s 鍚庣 {_attempt+2} 娆￠噸璇?, flush=True)
            time.sleep(wait)
            return _one_request(model, messages, max_tokens, temperature, thinking, timeout, _attempt+1)
        raise

def chat(messages, model="deepseek-v4-flash", thinking="enabled",
         max_tokens=32000, temperature=0.1, task_name="task",
         auto_continue=True, max_continues=6, timeout=1800, save=True):
    """杩斿洖 dict: content, reasoning, usage(绱姞), cost_yuan, status, rounds, finish, trace_file"""
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
            {"role":"user","content":"浣犱笂涓€娈靛湪 max_tokens 澶勮鎴柇銆傝浠庢柇鐐圭洿鎺ョ户缁緭鍑猴紝涓嶈閲嶅宸叉湁鍐呭锛屼笉瑕佸瘨鏆勶紝鐩存帴缁啓銆?}]
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
            w.writerow(["鏃堕棿","瀹炰緥","妯″瀷","妗ｄ綅","瀵硅薄","缂撳瓨鍛戒腑杈撳叆","鏈懡涓緭鍏?,"杈撳嚭",
                        "閲嶈瘯娆℃暟","鐘舵€?,"鑰楁椂绉?,"鎬昏垂鐢?,"缂撳瓨鍛戒腑鐜?,"finish_reason","浠诲姟鍚?])
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
        print("绂荤嚎妯″紡锛氫笉鍙戣捣浠樿垂璋冪敤銆傚姞 --live 鍋氫竴娆＄湡瀹炶嚜娴嬶紙flash闈炴€濊€?+ pro鎬濊€冿級銆?)
        sys.exit(0)
    r=chat([{"role":"user","content":"鍙洖绛斾袱涓瓧锛氭甯?}],model="deepseek-v4-flash",
           thinking="disabled",max_tokens=200,task_name="selftest_flash")
    print("flash:",r["status"],repr(r["content"][:40]),"cost",r["cost_yuan"])
    r=chat([{"role":"user","content":"鐢ㄤ竴鍙ヨ瘽璇存槑 Coq 閲?revert 鍐?induction 鐨勪綔鐢ㄣ€?}],
           model="deepseek-v4-pro",thinking="enabled",max_tokens=2000,task_name="selftest_pro")
    print("pro:",r["status"],"reason?",bool(r["reasoning"]),repr(r["content"][:60]),"cost",r["cost_yuan"])

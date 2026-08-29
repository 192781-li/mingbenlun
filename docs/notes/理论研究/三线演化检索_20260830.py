#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""任务2第一步：跨对话检索轻生/希望/自学/历史唯物四条线在用户消息中的言说节点。
只匹配用户消息，AI消息作为上下文。输出到 三线演化检索结果_20260830.md"""
import re, os, json

BASE = "/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun/docs/raw_materials/硬核对话记录/批量导出_20260829"
FILES = {
    "史官": "史官_20260523-0826_49789行.md",
    "思想大乱炖": "思想大乱炖_20260612-0630_53705行.md",
    "缄默意识理论": "缄默意识理论_20260619_334行.md",
    "三篇立命": "三篇立命_生命唯物主义_20260423-0625_11315行.md",
}
# 四条线关键词（用户消息匹配）
PATTERNS = {
    "轻生/存在": re.compile(r"轻生|想死|不想活|活不下去|自杀|为什么活|新生的希望|新生|活下去|不想活了|活着有什么|活着的意义|为什么还要活|拯救|救赎|一束光"),
    "自学/学校": re.compile(r"自学|不上学|请假|逃学|在家学|学校.*浪费|课堂.*浪费|学习方法|不想上学"),
    "历史唯物": re.compile(r"历史唯物|物质基础|上层建筑|经济基础|革命史|1840|1949|生产力决定|生产关系|唯物主义"),
}

def parse_messages(path):
    """解析导出文件为消息列表 [(time, role, content), ...]"""
    msgs = []
    cur_time = cur_role = None
    cur_buf = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = re.match(r"\*\*(用户|智能体)\((\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\)：\*\*\s*$", line.strip())
            if m:
                if cur_time is not None:
                    msgs.append((cur_time, cur_role, "\n".join(cur_buf).strip()))
                cur_role, cur_time = m.group(1), m.group(2)
                cur_buf = []
            else:
                if cur_time is not None:
                    cur_buf.append(line.rstrip("\n"))
    if cur_time is not None:
        msgs.append((cur_time, cur_role, "\n".join(cur_buf).strip()))
    return msgs

def main():
    out = ["# 三线演化检索结果（任务2第一步）\n",
           "> 检索范围：史官、思想大乱炖、缄默意识理论、三篇立命 四个对话的**用户消息**。",
           "> 匹配关键词：轻生/存在、自学/学校、历史唯物 三组。AI消息仅作上下文。",
           "> 目的：定位6.2之后四条线的言说节点，为DeepSeek综合演化分析提供锚点。\n"]
    total_hits = 0
    for dlg, fname in FILES.items():
        path = os.path.join(BASE, fname)
        if not os.path.exists(path):
            out.append(f"\n## {dlg}：文件不存在\n"); continue
        msgs = parse_messages(path)
        out.append(f"\n## {dlg}（共{len(msgs)}条消息）\n")
        hits = []
        for i, (t, role, content) in enumerate(msgs):
            if role != "用户": continue
            for line_name, pat in PATTERNS.items():
                if pat.search(content):
                    hits.append((i, t, line_name, content))
                    break
        # 按时间排序（已经是顺序）
        for i, t, line_name, content in hits:
            total_hits += 1
            ctx_prev = msgs[i-1] if i > 0 else None
            ctx_next = msgs[i+1] if i+1 < len(msgs) else None
            out.append(f"\n### [{dlg}] {t} · 匹配线：{line_name}")
            if ctx_prev:
                out.append(f"- 上文（{ctx_prev[1]} {ctx_prev[0]}）：{ctx_prev[2][:200]}")
            out.append(f"- **用户原话**：{content[:600]}")
            if ctx_next:
                out.append(f"- 下文（{ctx_next[1]} {ctx_next[0]}）：{ctx_next[2][:200]}")
        out.append(f"\n> {dlg} 命中 {len(hits)} 条用户消息。")
    out.append(f"\n---\n**总计命中 {total_hits} 条用户消息。**")
    out_path = "/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun/docs/notes/理论研究/三线演化检索结果_20260830.md"
    with open(out_path, "w", encoding='utf-8') as f:
        f.write("\n".join(out))
    print(f"完成，命中{total_hits}条，输出到{out_path}")

if __name__ == "__main__":
    main()

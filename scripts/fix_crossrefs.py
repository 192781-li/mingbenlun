#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交叉引用同步：标题改数字编号后，正文内部引用同步更新。只改内部引用，外部著作引证不动。"""
import glob,re,os
ROOT="生命论_模块化"
CN={'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
def cn2int(s):
    if s=='十':return 10
    if s.startswith('十'):return 10+CN.get(s[1:],0)
    if '十' in s:
        a,b=s.split('十');return CN.get(a,1)*10+(CN.get(b,0) if b else 0)
    return CN.get(s)

log=[]
SKIP_NAMES={'AGENTS.md','语义论纲要.md'}
def _exempt(p):
    fn=os.path.basename(p)
    return fn in SKIP_NAMES or '命经' in fn
# ---- 第一层：带篇/卷前缀 (卷X)?篇Y(之Z)?第N章 -> 前缀+ 1.N ----
pat=re.compile(r'(卷[一二三四五六七八九十]+)?(篇[零一二三四五六七八九十]+(?:之[一二三四五六])?)第([一二三四五六七八九十]+)章')
def repl(m):
    juan,pian,ch=m.group(1),m.group(2),cn2int(m.group(3))
    return f"{juan or ''}{pian} 1.{ch}"
for p in glob.glob(f"{ROOT}/**/*.md",recursive=True):
    if '项目文档' in p or _exempt(p):continue
    t=open(p,encoding='utf-8').read();orig=t
    # 跳过标题行内的替换：逐行处理
    out=[]
    for line in t.split('\n'):
        if re.match(r'^#{1,6} ',line): out.append(line);continue
        newline=pat.sub(repl,line)
        if newline!=line: log.append(f"{os.path.basename(p)[:24]}: 篇前缀引用")
        out.append(newline)
    t='\n'.join(out)
    if t!=orig: open(p,'w',encoding='utf-8').write(t)

# ---- 第二层+第三层：本篇/裸引用 白名单精确替换 ----
# (文件名匹配片段, [(旧,新),...])
whitelist=[
 ("篇二_自指操作",[("第四章讲了阴阳","1.4讲了阴阳")]),
 ("篇一之二_劳动价值论",[("（第七章）","（1.7）"),("第四章的排除法","1.4的排除法")]),
 ("篇二_剩余价值与剥削",[("（第六章）","（1.6）"),("本篇第八章","本篇 1.8"),("保留于第六章","保留于1.6")]),
 ("篇二之三_平均利润",[("本篇第三章","本篇 1.3"),("本篇第四章利息","本篇 1.4利息"),("本篇第四章企业主","本篇 1.4企业主")]),
 ("篇二之二_社会总资本",[("本篇第六章","本篇 1.6")]),
 ("篇五_收编",[("本篇第四章","本篇 1.4")]),
 ("篇八_帝国主义",[("本篇第五章","本篇 1.5")]),
 ("篇五之三_社会主义经济运行论下",[("本篇第十一章","本篇 1.6")]),
 ("篇五之二_社会主义经济运行论上",[("详见第四章","详见1.4")]),
 ("00_推导链总览",[("，第四章又承认","，1.4又承认")]),
]
for key,pairs in whitelist:
    for p in glob.glob(f"{ROOT}/**/*.md",recursive=True):
        if key not in os.path.basename(p):continue
        t=open(p,encoding='utf-8').read();o=t
        for a,b in pairs:
            if a in t: t=t.replace(a,b);log.append(f"{os.path.basename(p)[:24]}: {a}→{b}")
        if t!=o:open(p,'w',encoding='utf-8').write(t)

print(f"共处理 {len(log)} 处内部引用")
for x in log:print(" ",x)

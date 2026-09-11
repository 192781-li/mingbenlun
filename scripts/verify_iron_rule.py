#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
术语铁律校验器 —— 《生命论·明本论》专用

铁律：绝不说「物质自己会活」「物质是活的」。
正确根：「生命是活的，故生命物质才是活的」（活，只属于生命）。

本脚本扫描文本，区分三类命中：
  [VIOLATION] 裸用断言——把"物质"当活的主体（必须改）
  [OK-QUOTE]  引用铁律本身（"绝不说物质自己会活"）——允许
  [OK-ROOT]   正确根表述 / "物质不活"反向断言——允许
  [OK-PHYS]   物理对象陈述（"胶球有自指结构而不活"）——允许

用法：
  python verify_iron_rule.py <文件或目录> [--json]
例：
  python verify_iron_rule.py 明本论研究/_text/vols_final
  python verify_iron_rule.py 进化版·卷一（感应力深化稿）.md
"""
import os, re, sys, json

# 裸用违例：物质 + (自己会活|是活的|本身会活|自己活|也会活|能活|活了)
VIOLATION = re.compile(r'物质.{0,6}(自己会活|是活的|本身会活|自己活|也会活|能活|活了)')
# 引用铁律（"绝不说…"）或反向断言（"物质不活"）或正确根（"生命是活的，故生命物质才是活的"）
# 或批驳/封堵误读语境（堵"物质自己会活"误读 / "物质自己会活"被引号包裹作引述）
SAFE = re.compile(r'(绝不说.{0,10}物质.{0,8}会活|物质不活|生命是活的，?故生命物质才是活的|生命是活的。?故|生命物质才是活的|活的⾃指维持|有感即活|物质（胶球）|堵.{0,4}物质自己会活|破.{0,4}物质自己会活|物质自己会活.{0,4}误读|["\u201c\u201d].{0,6}物质自己会活.{0,6}["\u201c\u201d])')

def scan_text(text):
    res = {'violation': [], 'ok': []}
    for i, line in enumerate(text.split('\n'), 1):
        if VIOLATION.search(line):
            if SAFE.search(line):
                res['ok'].append((i, line.strip()))
            else:
                res['violation'].append((i, line.strip()))
        elif SAFE.search(line) and '绝不说' in line:
            res['ok'].append((i, line.strip()))
    return res

def scan_path(path):
    viol=[]; ok=[]
    # 历史存档/旧版本/原始对话保留原貌，不按现行铁律追溯（CI 只扫 生命论_模块化/，此处让全库扫描与 CI 结论一致）
    IGNORE_DIRS = {'.git','backup','__pycache__','raw_materials','archive','历史脚本_20260829','.ipynb_checkpoints'}
    if os.path.isdir(path):
        for root,dirs,fs in os.walk(path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for fn in fs:
                if fn.lower().endswith(('.md','.txt')):
                    p=os.path.join(root,fn)
                    t=open(p,encoding='utf-8',errors='ignore').read()
                    r=scan_text(t)
                    for ln,l in r['violation']: viol.append((os.path.relpath(p),ln,l))
                    for ln,l in r['ok']: ok.append((os.path.relpath(p),ln,l))
    else:
        t=open(path,encoding='utf-8',errors='ignore').read()
        r=scan_text(t)
        for ln,l in r['violation']: viol.append((path,ln,l))
        for ln,l in r['ok']: ok.append((path,ln,l))
    return viol, ok

if __name__=='__main__':
    target = sys.argv[1] if len(sys.argv)>1 else '.'
    as_json = '--json' in sys.argv
    viol, ok = scan_path(target)
    if as_json:
        print(json.dumps({'violations':viol,'safe_hits':ok}, ensure_ascii=False, indent=2))
    else:
        print(f'=== 术语铁律校验：{target} ===')
        print(f'裸用违例（必须改）：{len(viol)}')
        for f,ln,l in viol: print(f'  [VIOLATION] {f}:{ln}  {l[:80]}')
        print(f'合规命中（允许）：{len(ok)}')
        for f,ln,l in ok[:12]: print(f'  [OK] {f}:{ln}  {l[:60]}')
        if len(ok)>12: print(f'  ... 其余 {len(ok)-12} 条略')
        if not viol:
            print('✅ 零违例：全稿符合术语铁律。')
        else:
            print('❌ 存在违例，请修正后再交付。')
            sys.exit(1)

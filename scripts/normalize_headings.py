#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生命论_模块化 标题层级统一脚本（只改标题行，不碰正文）
目标层级：H2=篇(每文件1个) H3=章(X.Y) H4=节(X.Y.Z 或文字标签)
- Convention A: 无H1、单H2、H3=第X章 → H3中文转数字
- Convention B: 有H1、多H2(章)、H3=X.Y(节) → H1降H2、H2降H3、H3降H4并重编号
"""
import glob, re, os, sys

ROOT = "生命论_模块化"
CN = {'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}

def cn2int(s):
    s = s.strip()
    if s == '十': return 10
    if s.startswith('十'): return 10 + CN.get(s[1:],0)
    if '十' in s:
        a,b = s.split('十')
        return CN.get(a,1)*10 + (CN.get(b,0) if b else 0)
    if len(s)==1: return CN.get(s,None)
    return None

# 从文件名提取篇号中文（兼容 NN_篇一 / 篇一 / 篇零 / 篇三之二 / NN_附录五）
def pian_from_filename(fn):
    m = re.search(r'(篇[零一二三四五六七八九十]+(?:之[二三四五六])?)', fn)
    if m:
        token = m.group(1)
        num = token[1:].split('之')[0]
        if num == '零': label = '篇零'
        else: label = f'第{num}篇'
        if '之' in token:
            label += '之' + token.split('之')[1]
        return label
    m = re.search(r'(附录[一二三四五六七八九十]+)', fn)
    if m: return m.group(1)
    return None

# 不编号的特殊章关键词（前言/引言/小结等）
INTRO_KW = ('引言','前言','导言','序','绪论')
OUTRO_KW = ('小结','总结','余论','结语','尾声','本篇','全库','联动','附记','补记')

def is_heading(line): return bool(re.match(r'^#{1,6} ', line))
def level(line):
    m = re.match(r'^(#+) ', line); return len(m.group(1)) if m else 0
def text_of(line):
    return re.sub(r'^#+ ', '', line).rstrip('\n')

changelog = []

def process(path):
    fn = os.path.basename(path)
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()

    h_idx = [i for i,l in enumerate(lines) if is_heading(l)]
    h1 = [i for i in h_idx if level(lines[i])==1]
    h2 = [i for i in h_idx if level(lines[i])==2]

    # 跳过：卷标题/根文件(00_)、命经、工程指南、语义论纲要、项目文档
    SKIP_NAMES = {'AGENTS.md','语义论纲要.md'}
    if fn.startswith('00_') or '命经' in fn or fn in SKIP_NAMES: return None
    convB = len(h1)>=1 and len(h2)>=2

    pian = pian_from_filename(fn)
    out = list(lines)
    changes = []

    if convB:
        # ---- Convention B: 整体下移一级 ----
        # 1) H1(篇标题) -> 单个H2
        hi = h1[0]
        h1text = text_of(lines[hi])
        # 若H1正文已自带篇号前缀(如"第二篇…"/"篇零之二…")则不重复添加
        if pian and h1text.startswith(pian):
            new_h2 = f"## {h1text}\n"
        else:
            new_h2 = f"## {pian} {h1text}\n" if pian else f"## {h1text}\n"
        out[hi] = new_h2
        changes.append(f"H1→H2: {h1text[:30]} => {new_h2.strip()[:40]}")
        # 若还有多余H1（异常），也降为H2
        for extra in h1[1:]:
            out[extra] = '#'+lines[extra]  # # -> ##
        # 2) 其余 H2->H3, H3->H4, H4->H5（顺序：先深后浅避免连环）
        for i in reversed(h_idx):
            lv = level(out[i])
            if i==hi: continue
            if lv==2: out[i] = '#'+out[i]
            elif lv==3: out[i] = '#'+out[i]
            elif lv==4: out[i] = '#'+out[i]

    # ---- 统一重编号 H3（章） ----
    # 重新扫描（convB后层级已变）
    chap = 0
    seen_first_chap = False
    for i,l in enumerate(out):
        if not re.match(r'^### ', l): continue
        body = text_of(l)
        m_cn = re.match(r'^第([一二三四五六七八九十]+)章\s*(.*)$', body)
        m_int = re.match(r'^(\d+)[\.、]\s*(.*)$', body)  # 附录一 "1. xxx"
        m_xy = re.match(r'^\d+\.\d+\s*(.*)$', body)      # 已经 X.Y
        if m_cn:
            n = cn2int(m_cn.group(1))
            chap += 1; seen_first_chap=True
            title = m_cn.group(2).strip()
            out[i] = f"### 1.{chap} {title}\n".replace('  ',' ')
            changes.append(f"章: 第{m_cn.group(1)}章→1.{chap} {title[:20]}")
        elif m_int and not m_xy:
            chap += 1; seen_first_chap=True
            title = m_int.group(2).strip()
            out[i] = f"### 1.{chap} {title}\n"
            changes.append(f"章: {m_int.group(1)}.→1.{chap} {title[:20]}")
        elif m_xy:
            # convB 后原 X.Y 节应已降为 H4；若仍在 H3 说明是A风格已编号，统计不重排
            pass
        else:
            # 无编号H3
            is_intro = any(body.startswith(k) for k in INTRO_KW)
            is_outro = any(body.startswith(k) for k in OUTRO_KW)
            if is_intro and not seen_first_chap:
                # 归一为"引言/前言"保留无编号
                changes.append(f"引言保留: {body[:24]}")
            elif is_outro:
                changes.append(f"小结保留: {body[:24]}")
            else:
                # 夹在章节间的实质无编号H3 → 降为H4
                if seen_first_chap:
                    out[i] = '#'+l
                    changes.append(f"浮动H3→H4: {body[:24]}")
                else:
                    changes.append(f"前置无编号保留: {body[:24]}")

    # ---- Convention B: 重编号 H4（原 X.Y 节 → 1.X.Y） ----
    if convB:
        for i,l in enumerate(out):
            if not re.match(r'^#### ', l): continue
            body = text_of(l)
            m = re.match(r'^(\d+)\.(\d+)\s*(.*)$', body)
            if m:
                x,y = int(m.group(1)),int(m.group(2)); title=m.group(3)
                out[i] = f"#### 1.{x}.{y} {title}\n"
        # convB 里原 H4(####) 已升 H5(#####)，保持

    if out != lines:
        with open(path,'w',encoding='utf-8') as f: f.writelines(out)
        return changes
    return []

def fix_appendix_h2():
    """修正附录H2编号与文件名对齐（兼容 NN_ 数字前缀，按文件名关键子串匹配）"""
    fixes = [
        ('附录四_', '## 附录四 对手诘难与逐条回应'),
        ('附录五_', '## 附录五 参考文献'),
        ('附录六_', '## 附录六 反自指案例实录——时代峰峻长江国际事件'),
    ]
    import glob as _g
    done=[]
    for p in sorted(_g.glob(f"{ROOT}/12_附录/*.md")):
        fn=os.path.basename(p)
        for key,new in fixes:
            if key in fn:
                with open(p,encoding='utf-8') as f: ls=f.readlines()
                for i,l in enumerate(ls):
                    if re.match(r'^## ',l):
                        if l.strip()!=new:
                            done.append(f"{fn}: {l.strip()[:20]}→{new[:20]}")
                            ls[i]=new+'\n'
                        break
                with open(p,'w',encoding='utf-8') as f: f.writelines(ls)
                break
    return done

if __name__=='__main__':
    total=0
    for p in sorted(glob.glob(f"{ROOT}/**/*.md",recursive=True)):
        if '项目文档' in p: continue
        r = process(p)
        if r:
            total+=1
            print(f"\n### {p.replace(ROOT+'/','')}  ({len(r)}处)")
            for c in r[:50]: print("  ",c)
    print("\n\n=== 附录H2修正 ===")
    for x in fix_appendix_h2(): print("  ",x)
    print(f"\n共修改 {total} 个文件")

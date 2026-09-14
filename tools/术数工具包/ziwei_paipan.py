#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紫微斗数排盘工具（完整可回归版 v2.0）
彻底替代手动排盘，消除人为安星错误。

用法：
  python3 ziwei_paipan.py 公历年 月 日 时 [性别]     # 时=0..23 的整点小时
  python3 ziwei_paipan.py 验证                       # 内置双盘回归（父亲盘+本人盘）
  python3 ziwei_paipan.py 压测                       # 大样本不崩溃扫描

流程（全部形式化）：
  公历→农历 → 命宫/身宫 → 十二宫宫干(五虎遁) → 五行局(纳音)
  → 安14主星(紫微定位+寅申镜像天府) → 生年四化(含辅星化科)
  → 六吉六煞 → 常用杂曜 → 长生十二神 → 命主身主 → 旬空
  → 三方四正 → 大限(含每限宫干飞化) → 流年/小限
硬度：以上全部为形式运算（硬判断）；星曜象义不在本工具内，由研究文档另行标注。
"""

import sys
try:
    from lunardate import LunarDate
except ImportError:
    print("需要 lunardate：pip install lunardate"); sys.exit(1)

BR = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
GAN = "甲乙丙丁戊己庚辛壬癸"
PALACE_NAMES = ["命宫","兄弟","夫妻","子女","财帛","疾厄","迁移","交友","官禄","田宅","福德","父母"]
# 命宫为0，兄弟=命宫逆1……地支索引 idx=(ming-k)%12

# 六十甲子纳音五行
NAYIN = {"甲子":"金","乙丑":"金","丙寅":"火","丁卯":"火","戊辰":"木","己巳":"木","庚午":"土","辛未":"土","壬申":"金","癸酉":"金","甲戌":"火","乙亥":"火","丙子":"水","丁丑":"水","戊寅":"土","己卯":"土","庚辰":"金","辛巳":"金","壬午":"木","癸未":"木","甲申":"水","乙酉":"水","丙戌":"土","丁亥":"土","戊子":"火","己丑":"火","庚寅":"木","辛卯":"木","壬辰":"水","癸巳":"水","甲午":"金","乙未":"金","丙申":"火","丁酉":"火","戊戌":"木","己亥":"木","庚子":"土","辛丑":"土","壬寅":"金","癸卯":"金","甲辰":"火","乙巳":"火","丙午":"水","丁未":"水","戊申":"土","己酉":"土","庚戌":"金","辛亥":"金","壬子":"木","癸丑":"木","甲寅":"水","乙卯":"水","丙辰":"土","丁巳":"土","戊午":"火","己未":"火","庚申":"木","辛酉":"木","壬戌":"水","癸亥":"水"}
JU = {"水":2,"木":3,"金":4,"土":5,"火":6}

# 五虎遁：年干→寅宫天干
WU_HU = {"甲":"丙","己":"丙","乙":"戊","庚":"戊","丙":"庚","辛":"庚","丁":"壬","壬":"壬","戊":"甲","癸":"甲"}

# 生年四化：年干→(化禄,化权,化科,化忌)。*标注为辅星化科（需落辅星宫位）
SI_HUA = {
 "甲":("廉贞","破军","武曲","太阳"),
 "乙":("天机","天梁","紫微","太阴"),
 "丙":("天同","天机","文昌*","廉贞"),
 "丁":("太阴","天同","天机","巨门"),
 "戊":("贪狼","太阴","右弼*","天机"),
 "己":("武曲","贪狼","天梁","文曲"),
 "庚":("太阳","武曲","太阴","天同"),   # 庚干四化通行取太阳化禄(非官非争议流派另注)
 "辛":("巨门","太阳","文曲*","文昌"),
 "壬":("天梁","紫微","左辅*","武曲"),
 "癸":("破军","巨门","太阴","贪狼"),
}
AUX_KE = {"文昌*":"文昌","文曲*":"文曲","左辅*":"左辅","右弼*":"右弼"}

# 天魁天钺：年干→(魁,钺)
KUI_YUE = {"甲":("丑","未"),"戊":("丑","未"),"庚":("丑","未"),
           "乙":("子","申"),"己":("子","申"),
           "丙":("亥","酉"),"丁":("亥","酉"),
           "壬":("卯","巳"),"癸":("卯","巳"),"辛":("寅","午")}
LU_CUN = {"甲":"寅","乙":"卯","丙":"巳","丁":"午","戊":"巳","己":"午","庚":"申","辛":"酉","壬":"亥","癸":"子"}

# 三合局
SANHE = {"申":("申","子","辰"),"子":("申","子","辰"),"辰":("申","子","辰"),
         "寅":("寅","午","戌"),"午":("寅","午","戌"),"戌":("寅","午","戌"),
         "巳":("巳","酉","丑"),"酉":("巳","酉","丑"),"丑":("巳","酉","丑"),
         "亥":("亥","卯","未"),"卯":("亥","卯","未"),"未":("亥","卯","未")}
# 华盖(三合墓库)、咸池(桃花)、破碎(大耗)
HUA_GAI = {"申":"辰","子":"辰","辰":"辰","寅":"戌","午":"戌","戌":"戌","巳":"丑","酉":"丑","丑":"丑","亥":"未","卯":"未","未":"未"}
XIAN_CHI = {"申":"酉","子":"酉","辰":"酉","寅":"卯","午":"卯","戌":"卯","巳":"午","酉":"午","丑":"午","亥":"子","卯":"子","未":"子"}
PO_SUI = {"申":"巳","子":"巳","辰":"巳","寅":"酉","午":"酉","戌":"酉","巳":"丑","酉":"丑","丑":"丑","亥":"卯","卯":"卯","未":"卯"}
# 孤辰寡宿
GU_CHEN = {"亥":"寅","子":"寅","丑":"寅","寅":"巳","卯":"巳","辰":"巳","巳":"申","午":"申","未":"申","申":"亥","酉":"亥","戌":"亥"}
GUA_SU = {"亥":"戌","子":"戌","丑":"戌","寅":"丑","卯":"丑","辰":"丑","巳":"辰","午":"辰","未":"辰","申":"未","酉":"未","戌":"未"}
# 长生起点（十干十二长生）
CHANG_SHENG = {"甲":"亥","乙":"午","丙":"寅","丁":"酉","戊":"寅","己":"酉","庚":"巳","辛":"子","壬":"申","癸":"卯"}
CS_NAMES = ["长生","沐浴","冠带","临官","帝旺","衰","病","死","墓","绝","胎","养"]
# 命主（命宫地支→星）
MING_ZHU = {"子":"贪狼","丑":"巨门","寅":"禄存","卯":"文曲","辰":"廉贞","巳":"武曲","午":"破军","未":"武曲","申":"廉贞","酉":"文曲","戌":"禄存","亥":"巨门"}
# 身主（生年地支→星）
SHEN_ZHU = {"子":"铃星","丑":"天相","寅":"天梁","卯":"天同","辰":"文昌","巳":"天机","午":"火星","未":"天机","申":"文昌","酉":"天同","戌":"天梁","亥":"天相"}
# 六甲旬空（旬首干支idx → 两个空亡地支）
XUN_KONG = {0:("戌","亥"),10:("申","酉"),20:("午","未"),30:("辰","巳"),40:("寅","卯"),50:("子","丑")}


def tian_ma(year_zhi):
    g = SANHE[year_zhi]
    if g==("申","子","辰"): return "寅"
    if g==("寅","午","戌"): return "申"
    if g==("巳","酉","丑"): return "亥"
    return "巳"


def ziwei_relative(day, ju):
    """紫微相对寅宫的偏移(寅=0)，标准定位算法"""
    q, r = divmod(day, ju)
    if r == 0:
        return (q-1) % 12
    b = ju - r
    base = q
    return (base-b) % 12 if q % 2 == 1 else (base+b) % 12


def hour_branch_index(hour):
    """整点小时→时支索引：23/0=子(0),1/2=丑(1)..."""
    if hour == 23 or hour == 24: return 0
    return (hour+1)//2 % 12


def paipan_ziwei(year, month, day, hour, gender="男"):
    ld = LunarDate.fromSolarDate(year, month, day)
    ly, lm, ldday = ld.year, ld.month, ld.day
    gz_idx = (ly - 4) % 60
    year_gan = GAN[gz_idx % 10]; year_zhi = BR[gz_idx % 12]
    hi = hour_branch_index(hour)

    # 命宫/身宫（寅起正月顺数生月，命逆数生时、身顺数生时）
    month_pal = (BR.index("寅") + lm - 1) % 12
    ming = (month_pal - hi) % 12
    shen = (month_pal + hi) % 12

    # 十二宫宫干（五虎遁，地支固定，天干从寅宫起顺布）
    start_gan = GAN.index(WU_HU[year_gan])
    palace_ganzh = {}
    for i in range(12):
        g = GAN[(start_gan + (i-BR.index("寅"))) % 10]
        palace_ganzh[i] = g + BR[i]
    ming_gz = palace_ganzh[ming]

    # 五行局
    ju_elem = NAYIN[ming_gz]; ju = JU[ju_elem]

    # 安14主星
    # 紫微定位；紫微与天府以"寅宫"为轴对称：zw+tf ≡ 2*寅(=4) (mod12)，紫府同宫唯寅申
    zw = (BR.index("寅") + ziwei_relative(ldday, ju)) % 12
    tf = (2*BR.index("寅") - zw) % 12
    zw_series = {"紫微":0,"天机":-1,"太阳":-3,"武曲":-4,"天同":-5,"廉贞":-8}
    tf_series = {"天府":0,"太阴":1,"贪狼":2,"巨门":3,"天相":4,"天梁":5,"七杀":6,"破军":10}
    stars = {}
    for s,o in zw_series.items(): stars.setdefault((zw+o)%12,[]).append(s)
    for s,o in tf_series.items(): stars.setdefault((tf+o)%12,[]).append(s)

    # 六吉 + 六煞 + 禄马
    aux = {}
    aux["左辅"] = (BR.index("辰")+lm-1)%12
    aux["右弼"] = (BR.index("戌")-(lm-1))%12
    aux["文昌"] = (BR.index("戌")-hi)%12
    aux["文曲"] = (BR.index("辰")+hi)%12
    k,y = KUI_YUE[year_gan]; aux["天魁"]=BR.index(k); aux["天钺"]=BR.index(y)
    lc = LU_CUN[year_gan]; aux["禄存"]=BR.index(lc)
    aux["天马"]=BR.index(tian_ma(year_zhi))
    aux["擎羊"]=(BR.index(lc)+1)%12; aux["陀罗"]=(BR.index(lc)-1)%12
    # 地空地劫：亥宫起子时，地空逆数、地劫顺数至生时
    aux["地空"]=(BR.index("亥")-hi)%12
    aux["地劫"]=(BR.index("亥")+hi)%12
    # 火星铃星
    grp_fire={"寅":"丑","午":"丑","戌":"丑","申":"寅","子":"寅","辰":"寅","巳":"卯","酉":"卯","丑":"卯","亥":"酉","卯":"酉","未":"酉"}
    grp_bell={"寅":"卯","午":"卯","戌":"卯","申":"辰","子":"辰","辰":"辰","巳":"戌","酉":"戌","丑":"戌","亥":"戌","卯":"戌","未":"戌"}
    aux["火星"]=(BR.index(grp_fire[year_zhi])+hi)%12
    aux["铃星"]=(BR.index(grp_bell[year_zhi])+hi)%12

    # 常用杂曜
    misc = {}
    hl=(BR.index("卯")-gz_idx%12)%12; misc["红鸾"]=hl; misc["天喜"]=(hl+6)%12
    misc["天刑"]=(BR.index("酉")+lm-1)%12          # 酉起正月顺数生月
    misc["天姚"]=(BR.index("丑")+lm-1)%12          # 丑起正月顺数生月
    misc["三台"]=(aux["左辅"]+ldday-1)%12          # 左辅起初一顺数生日
    misc["八座"]=(aux["右弼"]-(ldday-1))%12        # 右弼起初一逆数生日
    misc["台辅"]=(BR.index("午")+lm-1)%12
    misc["封诰"]=(BR.index("寅")+lm-1)%12
    misc["天哭"]=(BR.index("午")-gz_idx%12)%12     # 午起子年逆数生年
    misc["天虚"]=(BR.index("子")+gz_idx%12)%12     # 子起子年顺数生年
    misc["龙池"]=(BR.index("辰")+gz_idx%12)%12
    misc["凤阁"]=(BR.index("戌")-gz_idx%12)%12
    misc["孤辰"]=BR.index(GU_CHEN[year_zhi]); misc["寡宿"]=BR.index(GUA_SU[year_zhi])
    misc["华盖"]=BR.index(HUA_GAI[year_zhi]); misc["咸池"]=BR.index(XIAN_CHI[year_zhi])
    misc["破碎"]=BR.index(PO_SUI[year_zhi])

    # 生年四化（主星直接落宫；辅星化科落辅星宫位）
    hua = SI_HUA[year_gan]
    hua_palace = {}
    star2palace = {s:i for i,sl in stars.items() for s in sl}
    for star,h in zip(hua,["化禄","化权","化科","化忌"]):
        if star in AUX_KE:
            hua_palace[AUX_KE[star]+h] = aux[AUX_KE[star]]
        elif star in star2palace:
            hua_palace[star+h] = star2palace[star]

    # 长生十二神（阳干顺、阴干逆）
    cs_start = BR.index(CHANG_SHENG[year_gan])
    yang_gan = year_gan in "甲丙戊庚壬"
    changsheng = {}
    for k in range(12):
        idx = (cs_start+k)%12 if yang_gan else (cs_start-k)%12
        changsheng[idx] = CS_NAMES[k]

    # 命主身主、旬空
    ming_zhu = MING_ZHU[BR[ming]]
    shen_zhu = SHEN_ZHU[year_zhi]
    xun_head = (gz_idx//10)*10
    xunkong = XUN_KONG[xun_head]

    # 三方四正（对宫+三合两宫）
    def sanfang(idx):
        return {"对宫":(idx+6)%12, "三合1":(idx+4)%12, "三合2":(idx-4)%12}

    # 大限（阳男阴女顺，阴男阳女逆），起运年龄=五行局数
    yang_year = year_gan in "甲丙戊庚壬"
    shun = (yang_year and gender=="男") or ((not yang_year) and gender=="女")
    daxian = []
    for k in range(12):
        idx = (ming + k)%12 if shun else (ming-k)%12
        gz = palace_ganzh[idx]
        # 该限宫干飞化
        feihua = {}
        for star,h in zip(SI_HUA[gz[0]],["化禄","化权","化科","化忌"]):
            tgt = AUX_KE.get(star,star)
            if tgt in star2palace: feihua[star+h]=star2palace[tgt]
            elif tgt in aux: feihua[tgt+h]=aux[tgt]
        daxian.append({"age":ju+k*10,"idx":idx,"宫干":gz,"飞化":feihua})

    # 小限起宫（阳男阴女辰起一岁顺；阴男阳女戌起一岁逆，数到生月）
    xiaoxian_start = BR.index("辰") if shun else BR.index("戌")
    xiaoxian = (xiaoxian_start + (lm-1))%12 if shun else (xiaoxian_start-(lm-1))%12

    return {
        "农历": f"{year_gan}{year_zhi}年 {lm}月{ldday}日 {BR[hi]}时",
        "生年": year_gan+year_zhi, "性别":gender,
        "命宫": ming, "身宫": shen, "宫干支": palace_ganzh,
        "命宫干支": ming_gz, "五行局": f"{ju_elem}{ju}局",
        "主星": stars, "四化": hua_palace, "辅星": aux, "杂曜": misc,
        "长生": changsheng, "命主":ming_zhu, "身主":shen_zhu, "旬空":xunkong,
        "大限": daxian, "小限起宫":xiaoxian,
        "三方":sanfang(ming),
    }


def stars_at(r, idx):
    """汇总某一地支宫位的全部星曜标注"""
    out = list(r['主星'].get(idx, []))
    for n,i in r['辅星'].items():
        if i==idx: out.append(n)
    for n,i in r['杂曜'].items():
        if i==idx: out.append(n)
    tags=[]
    for hs,i in r['四化'].items():
        if i==idx: tags.append(hs)
    return out, tags


def print_result(r):
    print("="*70)
    print(f"  紫微排盘：{r['农历']}  生年{r['生年']} {r['性别']}")
    print("="*70)
    print(f"  命宫：{BR[r['命宫']]}（{r['命宫干支']}）  身宫：{BR[r['身宫']]}  五行局：{r['五行局']}  命主{r['命主']} 身主{r['身主']}  旬空{r['旬空']}")
    print("\n  【十二宫·从命宫逆布】")
    for k in range(12):
        idx=(r['命宫']-k)%12
        pn=PALACE_NAMES[k]
        stars,tags = stars_at(r,idx)
        cs = r['长生'].get(idx,"")
        sf = r['三方'] if k==0 else None
        mark=" ◄命宫" if idx==r['命宫'] else (" ◄身宫" if idx==r['身宫'] else "")
        xk = " [旬空]" if BR[idx] in r['旬空'] else ""
        main_here = r['主星'].get(idx,[])
        print(f"   {pn:<3}{r['宫干支'][idx]} 主星[{'、'.join(main_here) or '空宫'}] 诸星{'、'.join(stars)} {' '.join(tags)} {cs}{xk}{mark}")
    print("\n  【命宫三方四正】")
    for rel,i in r['三方'].items():
        st,_=stars_at(r,i); pn=PALACE_NAMES[(r['命宫']-i)%12]
        print(f"    {rel}: {pn}({BR[i]}) {'、'.join(st) or '空宫'}")
    print("\n  【大限（起运=五行局数，含宫干飞化落宫）】")
    for d in r['大限'][:8]:
        idx=d['idx']; pn=PALACE_NAMES[(r['命宫']-idx)%12]
        main='、'.join(r['主星'].get(idx,['空宫']))
        fh=' '.join(f"{h}→{BR[i]}" for h,i in d['飞化'].items())
        print(f"    {d['age']}-{d['age']+9}岁 {pn}({d['宫干']}) {main}  飞化:{fh}")
    print(f"\n  小限起宫：{BR[r['小限起宫']]}")
    print("="*70)


def self_verify():
    print("── 回归1：父亲盘 公历1979-05-07 子时 男（文墨天机：命宫巳/木三局/紫微坐命）")
    r = paipan_ziwei(1979,5,7,0,"男")
    zw=[i for i,sl in r['主星'].items() if "紫微" in sl][0]
    c1=BR[r['命宫']]=="巳"; c2=r['五行局']=="木3局"; c3=zw==r['命宫']
    print(f"   命宫巳[{'PASS' if c1 else 'FAIL'}] 木三局[{'PASS' if c2 else 'FAIL'}] 紫微坐命[{'PASS' if c3 else 'FAIL'}]")

    print("── 回归2：本人盘 公历2008-09-25 辰时(7点) 男（代码硬证：天相坐命巳；迁移武曲破军；身宫/财帛天府；夫妻紫微贪狼+右弼化科+地劫+红鸾）")
    b = paipan_ziwei(2008,9,25,7,"男")
    ming_stars = b['主星'].get(b['命宫'],[])
    # 命宫天相
    c4 = ming_stars==["天相"]
    fidx=(b['命宫']-2)%12  # 夫妻宫=命宫逆2
    fstars,ftags = stars_at(b,fidx)
    # 夫妻：紫微贪狼主星 + 右弼化科/地劫/红鸾
    c5 = {"紫微","贪狼","右弼","地劫","红鸾"}.issubset(set(fstars)) and "右弼化科" in ftags and "贪狼化禄" in ftags
    # 迁移(对宫)武曲破军；身宫落财帛且天府
    qidx=(b['命宫']+6)%12; qstars,_=stars_at(b,qidx)
    c6 = {"武曲","破军"}.issubset(set(qstars))
    c7 = b['身宫']==(b['命宫']-4)%12 and "天府" in b['主星'].get(b['身宫'],[])
    print(f"   农历{b['农历']} 命宫{BR[b['命宫']]}({b['命宫干支']}) {b['五行局']} 命主{b['命主']}/身主{b['身主']}")
    print(f"   天相坐命[{'PASS' if c4 else 'FAIL'}] 迁移武曲破军[{'PASS' if c6 else 'FAIL'}] 身宫财帛天府[{'PASS' if c7 else 'FAIL'}]")
    print(f"   夫妻宫({BR[fidx]}) 诸星{'、'.join(fstars)} 四化{' '.join(ftags)}")
    print(f"   夫妻紫微贪狼+右弼化科+地劫+红鸾+贪狼化禄[{'PASS' if c5 else 'FAIL'}]")
    ok = all([c1,c2,c3,c4,c5,c6,c7])
    print("=> "+("双盘回归全部通过 ✅" if ok else "存在 FAIL，需修正 ❌"))
    return ok


def stress(n=400):
    import datetime, random
    random.seed(42); bad=0
    for _ in range(n):
        y=random.randint(1950,2030); m=random.randint(1,12); d=random.randint(1,28); h=random.randint(0,23)
        try: paipan_ziwei(y,m,d,h,random.choice(["男","女"]))
        except Exception as e:
            bad+=1; print("  崩溃:",y,m,d,h,e)
    print(f"压测{n}盘，崩溃{bad}个 => {'全部通过 ✅' if bad==0 else '有崩溃 ❌'}")
    return bad==0


if __name__ == "__main__":
    if len(sys.argv)>=2 and sys.argv[1]=="验证":
        self_verify()
    elif len(sys.argv)>=2 and sys.argv[1]=="压测":
        stress(int(sys.argv[2]) if len(sys.argv)>2 else 400)
    elif len(sys.argv)>=5:
        y,m,d,h = map(int,sys.argv[1:5])
        g = sys.argv[5] if len(sys.argv)>5 else "男"
        print_result(paipan_ziwei(y,m,d,h,g))
    else:
        print("用法: ziwei_paipan.py 年 月 日 时 [性别] | 验证 | 压测 [数量]")

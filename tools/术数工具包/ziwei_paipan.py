#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紫微斗数排盘工具（代码可复现版）
彻底替代手动排盘，消除人为安星错误。

用法：
  python3 ziwei_paipan.py 公历年 月 日 时 [性别]
  python3 ziwei_paipan.py 验证        # 内置交叉验证（父亲盘）

流程（全部形式化）：
  公历→农历(lunardate) → 命宫/身宫 → 命宫天干 → 五行局 → 安14主星
  → 生年四化 → 辅星(左右昌曲魁钺禄存天马羊陀红鸾) → 大限
"""

import sys
try:
    from lunardate import LunarDate
except ImportError:
    print("需要 lunardate：pip install lunardate"); sys.exit(1)

BR = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
GAN = "甲乙丙丁戊己庚辛壬癸"
PALACE_NAMES = ["命宫","兄弟","夫妻","子女","财帛","疾厄","迁移","交友","官禄","田宅","福德","父母"]

# 六十甲子纳音五行
NAYIN = {"甲子":"金","乙丑":"金","丙寅":"火","丁卯":"火","戊辰":"木","己巳":"木","庚午":"土","辛未":"土","壬申":"金","癸酉":"金","甲戌":"火","乙亥":"火","丙子":"水","丁丑":"水","戊寅":"土","己卯":"土","庚辰":"金","辛巳":"金","壬午":"木","癸未":"木","甲申":"水","乙酉":"水","丙戌":"土","丁亥":"土","戊子":"火","己丑":"火","庚寅":"木","辛卯":"木","壬辰":"水","癸巳":"水","甲午":"金","乙未":"金","丙申":"火","丁酉":"火","戊戌":"木","己亥":"木","庚子":"土","辛丑":"土","壬寅":"金","癸卯":"金","甲辰":"火","乙巳":"火","丙午":"水","丁未":"水","戊申":"土","己酉":"土","庚戌":"金","辛亥":"金","壬子":"木","癸丑":"木","甲寅":"水","乙卯":"水","丙辰":"土","丁巳":"土","戊午":"火","己未":"火","庚申":"木","辛酉":"木","壬戌":"水","癸亥":"水"}
JU = {"水":2,"木":3,"金":4,"土":5,"火":6}

# 五虎遁：年干→寅宫天干
WU_HU = {"甲":"丙","己":"丙","乙":"戊","庚":"戊","丙":"庚","辛":"庚","丁":"壬","壬":"壬","戊":"甲","癸":"甲"}

# 生年四化：年干→(化禄,化权,化科,化忌)
SI_HUA = {
 "甲":("廉贞","破军","武曲","太阳"),
 "乙":("天机","天梁","紫微","太阴"),
 "丙":("天同","天机","文昌","廉贞"),
 "丁":("太阴","天同","天机","巨门"),
 "戊":("贪狼","太阴","右弼","天机"),
 "己":("武曲","贪狼","天梁","文曲"),
 "庚":("太阳","武曲","太阴","天同"),
 "辛":("巨门","太阳","文曲","文昌"),
 "壬":("天梁","紫微","左辅","武曲"),
 "癸":("破军","巨门","太阴","贪狼"),
}

# 天魁天钺：年干→(魁,钺)
KUI_YUE = {"甲":("丑","未"),"戊":("丑","未"),"庚":("丑","未"),
           "乙":("子","申"),"己":("子","申"),
           "丙":("亥","酉"),"丁":("亥","酉"),
           "壬":("卯","巳"),"癸":("卯","巳"),"辛":("寅","午")}

# 禄存：年干→地支
LU_CUN = {"甲":"寅","乙":"卯","丙":"巳","丁":"午","戊":"巳","己":"午","庚":"申","辛":"酉","壬":"亥","癸":"子"}

# 天马：年支三合
def tian_ma(year_zhi):
    if year_zhi in ("申","子","辰"): return "寅"
    if year_zhi in ("寅","午","戌"): return "申"
    if year_zhi in ("巳","酉","丑"): return "亥"
    return "巳"


def ziwei_relative(day, ju):
    """紫微相对寅宫的偏移(寅=0)，标准定位算法"""
    q, r = divmod(day, ju)
    if r == 0:
        return (q-1) % 12
    b = ju - r
    base = q
    return (base-b) % 12 if q % 2 == 1 else (base+b) % 12


def paipan_ziwei(year, month, day, hour, gender="男"):
    # 1.农历
    ld = LunarDate.fromSolarDate(year, month, day)
    ly, lm, ldday = ld.year, ld.month, ld.day
    # 年干支
    gz_idx = (ly - 4) % 60
    year_gan = GAN[gz_idx % 10]; year_zhi = BR[gz_idx % 12]

    # 2.命宫/身宫
    month_pal = (BR.index("寅") + lm - 1) % 12
    hour_idx = (hour+1)//2 % 12 if hour != 23 else 0
    ming = (month_pal - hour_idx) % 12
    shen = (month_pal + hour_idx) % 12

    # 3.命宫天干
    start = GAN.index(WU_HU[year_gan])
    ming_gan = GAN[(start + (ming-BR.index("寅"))) % 10]
    ming_gz = ming_gan + BR[ming]

    # 4.五行局
    ju_elem = NAYIN[ming_gz]; ju = JU[ju_elem]

    # 5.安14主星
    zw = (BR.index("寅") + ziwei_relative(ldday, ju)) % 12
    tf = (BR.index("寅")+BR.index("申") - zw) % 12
    zw_series = {"紫微":0,"天机":-1,"太阳":-3,"武曲":-4,"天同":-5,"廉贞":-8}
    tf_series = {"天府":0,"太阴":1,"贪狼":2,"巨门":3,"天相":4,"天梁":5,"七杀":6,"破军":10}
    stars = {}
    for s,o in zw_series.items(): stars.setdefault((zw+o)%12,[]).append(s)
    for s,o in tf_series.items(): stars.setdefault((tf+o)%12,[]).append(s)

    # 6.四化落宫
    hua = SI_HUA[year_gan]
    hua_palace = {}
    for star,h in zip(hua,["化禄","化权","化科","化忌"]):
        if star in ("左弼","右弼","文昌","文曲","左辅"):
            hua_palace[star+h] = None; continue
        for idx,sl in stars.items():
            if star in sl: hua_palace[star+h] = idx

    # 7.辅星
    aux = {}
    # 左辅：辰起正月顺数生月；右弼：戌起正月逆数生月
    aux["左辅"] = (BR.index("辰")+lm-1)%12
    aux["右弼"] = (BR.index("戌")-(lm-1))%12
    # 文昌：戌起子时逆数生时；文曲：辰起子时顺数生时
    aux["文昌"] = (BR.index("戌")-hour_idx)%12
    aux["文曲"] = (BR.index("辰")+hour_idx)%12
    # 魁钺
    k,y = KUI_YUE[year_gan]; aux["天魁"]=BR.index(k); aux["天钺"]=BR.index(y)
    # 禄存、天马
    lc = LU_CUN[year_gan]; aux["禄存"]=BR.index(lc)
    aux["天马"]=BR.index(tian_ma(year_zhi))
    # 擎羊(禄存前)陀罗(禄存后)
    aux["擎羊"]=(BR.index(lc)+1)%12; aux["陀罗"]=(BR.index(lc)-1)%12
    # 红鸾：卯起子年逆数；天喜对宫
    hl=(BR.index("卯")-gz_idx%12)%12; aux["红鸾"]=hl; aux["天喜"]=(hl+6)%12
    # 火星铃星：按年支三合组定起始，从该宫起子时顺数生时
    grp_fire={"寅":"丑","午":"丑","戌":"丑","申":"寅","子":"寅","辰":"寅",
              "巳":"卯","酉":"卯","丑":"卯","亥":"酉","卯":"酉","未":"酉"}
    grp_bell={"寅":"卯","午":"卯","戌":"卯","申":"辰","子":"辰","辰":"辰",
              "巳":"戌","酉":"戌","丑":"戌","亥":"戌","卯":"戌","未":"戌"}
    aux["火星"]=(BR.index(grp_fire[year_zhi])+hour_idx)%12
    aux["铃星"]=(BR.index(grp_bell[year_zhi])+hour_idx)%12

    # 8.大限（阳男阴女顺，阴男阳女逆）
    yang_year = year_gan in "甲丙戊庚壬"
    shun = (yang_year and gender=="男") or ((not yang_year) and gender=="女")
    start_age = ju
    daxian = []
    for k in range(12):
        idx = (ming + k)%12 if shun else (ming-k)%12
        daxian.append((start_age+k*10, idx))

    return {
        "农历": f"{year_gan}{year_zhi}年 {lm}月{ldday}日",
        "生年": year_gan+year_zhi, "命宫": ming, "身宫": shen,
        "命宫干支": ming_gz, "五行局": f"{ju_elem}{ju}局",
        "主星": stars, "四化": hua_palace, "辅星": aux, "大限": daxian,
    }


def print_result(r):
    print("="*64)
    print(f"  紫微排盘：{r['农历']}  生年{r['生年']}")
    print("="*64)
    print(f"  命宫：{BR[r['命宫']]}（{r['命宫干支']}）  身宫：{BR[r['身宫']]}  五行局：{r['五行局']}")

    print("\n  【十二宫】")
    for k in range(12):
        idx=(r['命宫']-k)%12
        pn=PALACE_NAMES[k]
        main=' '.join(r['主星'].get(idx,['(空宫)']))
        # 该宫四化
        hua_str=""
        for hs,p_idx in r['四化'].items():
            if p_idx==idx: hua_str+=" "+hs
        # 辅星
        aux_str=""
        for name,a_idx in r['辅星'].items():
            if a_idx==idx: aux_str+=" "+name
        mark=" ◄命宫" if idx==r['命宫'] else ""
        print(f"    {pn:<4}({BR[idx]}) {main:<10}{hua_str:<8}{aux_str}{mark}")

    print("\n  【大限】")
    for age,idx in r['大限'][:8]:
        pn=PALACE_NAMES[(r['命宫']-idx)%12]
        main=' '.join(r['主星'].get(idx,['(空宫)']))
        print(f"    {age}-{age+9}岁 {pn}({BR[idx]}) {main}")
    print("="*64)


def self_verify():
    """交叉验证：父亲 己未年农历四月十二子时，应得 命宫巳/木三局/紫微在巳"""
    # 直接用农历构造：己未年=1979
    # 农历四月十二对应公历1979年5月7日
    r = paipan_ziwei(1979,5,7,0,"男")
    ok1 = BR[r['命宫']]=="巳"
    ok2 = r['五行局']=="木3局"
    zw_idx = [i for i,sl in r['主星'].items() if "紫微" in sl][0]
    ok3 = zw_idx == r['命宫']
    print(f"  父亲盘验证：命宫巳[{ 'PASS' if ok1 else 'FAIL'}] 木三局[{ 'PASS' if ok2 else 'FAIL'}] 紫微在命宫[{ 'PASS' if ok3 else 'FAIL'}]")
    print("  => 算法" + "通过独立案例验证" if (ok1 and ok2 and ok3) else "仍有问题")
    return ok1 and ok2 and ok3


if __name__ == "__main__":
    if len(sys.argv)>=2 and sys.argv[1]=="验证":
        self_verify()
    elif len(sys.argv)>=5:
        y,m,d,h = map(int,sys.argv[1:5])
        g = sys.argv[5] if len(sys.argv)>5 else "男"
        print_result(paipan_ziwei(y,m,d,h,g))
    else:
        print("用法: python3 ziwei_paipan.py 年 月 日 时 [性别] | python3 ziwei_paipan.py 验证")

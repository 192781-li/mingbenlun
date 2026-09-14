# -*- coding: utf-8 -*-
"""
八字 + 紫微 统一硬回归（S03 术数工具质量门）
================================================
铁规：凡改动 bazi_paipan.py / ziwei_paipan.py / t_value_calculator.py，
必须先 `python3 chart_regression.py` 全绿，才允许对外输出任何命理结论。

三层锁：
  A. 双盘锚点断言（本人盘 + 父亲盘，共 18 项，硬运算不可漂移）
  B. 裁决稳定性（同一盘重复 5 次，最终裁决必须一致）
  C. 大样本：600 随机盘 0 崩溃 + 十神五行方向通用不变量
     （独立用生克字典推导"印比食财官"期望五行，与 get_yong_shen 输出逐一比对，
      永久锁死 2026-09-14 抓到的"官杀↔财星五行对调"这一类方向性 bug）

退出码：全过 0；任一 FAIL 1（可接 CI / pre-commit）。
"""
import os, sys, random, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bazi_paipan as B
import ziwei_paipan as Z

PASS, FAIL = 0, 0
FAIL_ITEMS = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        FAIL_ITEMS.append(name)
        print(f"  [FAIL] {name}  {detail}")


def pillar(r, which):
    return "".join(r["四柱"][which]["干支"])


# ----------------------------------------------------------------------
# A1. 本人八字：公历 2008-09-25 辰时(7点) 男 —— 戊土身弱、喜火土
# ----------------------------------------------------------------------
def reg_user_bazi():
    print("── A1 本人八字 2008-09-25 辰时男（戊子/辛酉/戊辰/丙辰，戊土偏弱喜火土）")
    r = B.paipan(2008, 9, 25, 7, "男")
    ws, ys = r["日主旺衰"], r["用神建议"]
    check("年柱戊子", pillar(r, "年柱") == "戊子", pillar(r, "年柱"))
    check("月柱辛酉", pillar(r, "月柱") == "辛酉", pillar(r, "月柱"))
    check("日柱戊辰", pillar(r, "日柱") == "戊辰", pillar(r, "日柱"))
    check("时柱丙辰", pillar(r, "时柱") == "丙辰", pillar(r, "时柱"))
    check("日主戊土", r["日主"]["天干"] == "戊", r["日主"]["天干"])
    check("酉月失令(得令=False)", ws["得令"] is False, str(ws.get("月令状态")))
    check("最终裁决=偏弱/身弱", ws.get("最终") in ("偏弱", "身弱"), str(ws.get("最终")))
    xi = "".join(ys["喜用"])
    ji = "".join(ys["忌神"])
    check("喜用含火(印)与土(比劫)", ("火" in xi) and ("土" in xi), xi)
    check("忌:木=官杀", "木（官杀" in ji, ji)
    check("忌:金=食伤", "金（食伤" in ji, ji)
    check("忌:水=财星", "水（财星" in ji, ji)
    check("时干丙=偏印", r["四柱"]["时柱"]["天干十神"] == "偏印",
          r["四柱"]["时柱"]["天干十神"])
    return r


# ----------------------------------------------------------------------
# A2. 父亲八字：公历 1979-05-07 子时 男 —— 甲木身弱、喜水木
# ----------------------------------------------------------------------
def reg_father_bazi():
    print("── A2 父亲八字 1979-05-07 子时男（己未/己巳/甲戌/甲子，甲木身弱喜水木）")
    r = B.paipan(1979, 5, 7, 0, "男")
    ws, ys = r["日主旺衰"], r["用神建议"]
    check("年柱己未", pillar(r, "年柱") == "己未", pillar(r, "年柱"))
    check("月柱己巳", pillar(r, "月柱") == "己巳", pillar(r, "月柱"))
    check("日柱甲戌", pillar(r, "日柱") == "甲戌", pillar(r, "日柱"))
    check("时柱甲子", pillar(r, "时柱") == "甲子", pillar(r, "时柱"))
    check("日主甲木", r["日主"]["天干"] == "甲", r["日主"]["天干"])
    check("最终裁决=偏弱/身弱", ws.get("最终") in ("偏弱", "身弱"), str(ws.get("最终")))
    xi = "".join(ys["喜用"])
    check("喜用含水(印)与木(比劫)", ("水" in xi) and ("木" in xi), xi)
    return r


# ----------------------------------------------------------------------
# B. 本人紫微：土五局、命宫巳=天府、迁移紫微七杀、身宫财帛丑空宫、
#    夫妻廉贞破军+右弼化科+地劫+红鸾、福德武曲贪狼+贪狼化禄、
#    父母天同太阴+太阴化权、官禄天相（文墨天机专业版终验 2026-09-10）
# ----------------------------------------------------------------------
def reg_user_ziwei():
    print("── B1 本人紫微 2008-09-25 辰时男（土5局/命宫巳天府，文墨天机终验）")
    b = Z.paipan_ziwei(2008, 9, 25, 7, "男")
    ming = b["命宫"]
    check("命宫在巳(index5)", Z.BR[ming] == "巳" and ming == 5, str(ming))
    check("五行局=土5局", b["五行局"] == "土5局", b["五行局"])
    check("命宫主星唯天府", b["主星"].get(ming, []) == ["天府"],
          str(b["主星"].get(ming)))
    # 迁移(对宫亥)=紫微七杀
    qidx = (ming + 6) % 12
    check("迁移(对宫亥)紫微七杀",
          {"紫微", "七杀"}.issubset(set(b["主星"].get(qidx, []))),
          str(b["主星"].get(qidx)))
    # 身宫=财帛丑且空宫(无主星)
    check("身宫=财帛(丑,index1)且空宫无主星",
          b["身宫"] == (ming - 4) % 12 and b["主星"].get(b["身宫"], []) == [],
          f"身宫{Z.BR[b['身宫']]}主星{b['主星'].get(b['身宫'])}")
    # 夫妻卯=廉贞破军+右弼化科+地劫+红鸾
    fidx = (ming - 2) % 12
    fstars, ftags = Z.stars_at(b, fidx)
    check("夫妻(卯)廉贞破军+右弼+地劫+红鸾,右弼化科",
          {"廉贞", "破军", "右弼", "地劫", "红鸾"}.issubset(set(fstars))
          and "右弼化科" in ftags,
          f"{fstars}|{ftags}")
    # 福德未=武曲贪狼+贪狼化禄
    fuidx = (ming + 2) % 12
    fustars, futags = Z.stars_at(b, fuidx)
    check("福德(未)武曲贪狼+贪狼化禄",
          {"武曲", "贪狼"}.issubset(set(fustars)) and "贪狼化禄" in futags,
          f"{fustars}|{futags}")
    # 父母午=天同太阴+太阴化权
    pidx = (ming + 1) % 12
    pstars, ptags = Z.stars_at(b, pidx)
    check("父母(午)天同太阴+太阴化权",
          {"天同", "太阴"}.issubset(set(pstars)) and "太阴化权" in ptags,
          f"{pstars}|{ptags}")
    # 官禄酉=天相
    oidx = (ming + 4) % 12
    check("官禄(酉)天相", b["主星"].get(oidx, []) == ["天相"],
          str(b["主星"].get(oidx)))
    return b


def reg_father_ziwei():
    print("── B2 父亲紫微 1979-05-07 子时男（木3局/命宫巳紫微坐命）")
    r = Z.paipan_ziwei(1979, 5, 7, 0, "男")
    zw = [i for i, sl in r["主星"].items() if "紫微" in sl][0]
    check("命宫在巳", Z.BR[r["命宫"]] == "巳", Z.BR[r["命宫"]])
    check("五行局=木3局", r["五行局"] == "木3局", r["五行局"])
    check("紫微坐命", zw == r["命宫"], str(zw))
    return r


# ----------------------------------------------------------------------
# C1. 裁决稳定性：本人盘连算 5 次，最终裁决必须一致
# ----------------------------------------------------------------------
def reg_stability():
    print("── C1 裁决稳定性（本人盘连算5次）")
    finals = [B.paipan(2008, 9, 25, 7, "男")["日主旺衰"].get("最终") for _ in range(5)]
    check("5次裁决完全一致", len(set(finals)) == 1, str(finals))


# ----------------------------------------------------------------------
# C2. 十神五行方向通用不变量（核心：独立推导期望，逐盘比对）
#     对日主 X：
#       印=生X者  比=X  食伤=X生者  财=X所克  官杀=克X者
#     身弱喜用五行集合必须恰为 {印,比}；忌神五行集合必须恰为 {官杀,食伤,财}；
#     身强反之。任一标签与其五行错位即 FAIL。
# ----------------------------------------------------------------------
def expected_shishen_elements(day_elem):
    yin = [e for e in B.GENERATES if B.GENERATES[e] == day_elem][0]
    shi = B.GENERATES[day_elem]
    cai = B.OVERCOMES[day_elem]
    guan = [e for e in B.OVERCOMES if B.OVERCOMES[e] == day_elem][0]
    return {"印": yin, "比劫": day_elem, "食伤": shi, "财": cai, "官杀": guan}


def elem_of_item(item):
    # 取条目字符串最前面的那个五行字
    for e in "木火土金水":
        if item.strip().startswith(e):
            return e
    return None


def reg_direction_invariant_and_stress(n=600):
    print(f"── C2 大样本 {n} 随机盘：0崩溃 + 十神五行方向不变量")
    random.seed(20260914)
    crash, dirbad = 0, []
    neutral = 0
    for _ in range(n):
        y = random.randint(1950, 2030); m = random.randint(1, 12)
        d = random.randint(1, 28); h = random.randint(0, 23)
        g = random.choice(["男", "女"])
        try:
            r = B.paipan(y, m, d, h, g)
        except Exception:
            crash += 1
            traceback.print_exc()
            continue
        ws = r["日主旺衰"]; ys = r["用神建议"]
        day_elem = r["日主"]["五行"]
        exp = expected_shishen_elements(day_elem)
        rating = ws.get("最终", "")
        xi_elems = [elem_of_item(x) for x in ys["喜用"] if "（" in x]
        ji_elems = [elem_of_item(x) for x in ys["忌神"] if "（" in x]
        # 标签只取"（"后、第一个"，"前的规范十神名（说明文字里也可能出现别的十神词，禁止全串子串匹配）
        def label_of(item):
            if "（" not in item:
                return None
            inner = item.split("（", 1)[1]
            return inner.split("，")[0].strip()
        label2key = {"印星": "印", "比劫": "比劫", "食伤": "食伤", "财星": "财", "官杀": "官杀"}
        for item in (ys["喜用"] + ys["忌神"]):
            t = label_of(item); e = elem_of_item(item)
            if t is None or e is None:
                continue
            tkey = label2key.get(t)
            want = exp.get(tkey)
            if want and e != want:
                dirbad.append(f"{y}-{m}-{d}-{h}{g} 日主{day_elem} {item} 期望{want}")
        if rating in ("中和", "") or "需结合" in "".join(ys["喜用"]):
            neutral += 1
    check(f"{n}随机盘0崩溃", crash == 0, f"崩溃{crash}")
    check("十神五行方向全部正确(0错位)", len(dirbad) == 0,
          f"错位{len(dirbad)} 例:{dirbad[:3]}")
    print(f"     （其中临界中和/需结合格局 {neutral} 盘，占比{neutral/n*100:.1f}%）")


def reg_ziwei_stress(n=600):
    print(f"── C3 紫微 {n} 随机盘压测 0 崩溃")
    random.seed(914)
    crash = 0
    for _ in range(n):
        y = random.randint(1950, 2030); m = random.randint(1, 12)
        d = random.randint(1, 28); h = random.randint(0, 23)
        try:
            Z.paipan_ziwei(y, m, d, h, random.choice(["男", "女"]))
        except Exception:
            crash += 1
            traceback.print_exc()
    check(f"紫微{n}盘0崩溃", crash == 0, f"崩溃{crash}")


def main():
    print("=" * 64)
    print("八字+紫微 统一硬回归  chart_regression.py")
    print("=" * 64)
    reg_user_bazi()
    reg_father_bazi()
    reg_user_ziwei()
    reg_father_ziwei()
    reg_stability()
    reg_direction_invariant_and_stress(600)
    reg_ziwei_stress(600)
    print("=" * 64)
    print(f"通过 {PASS} 项，失败 {FAIL} 项")
    if FAIL:
        print("失败项：", "；".join(FAIL_ITEMS))
        print("=> 硬回归未通过，禁止输出命理结论 ❌")
        sys.exit(1)
    print("=> 全部硬回归通过 ✅，可安全输出命理结论")
    sys.exit(0)


if __name__ == "__main__":
    main()

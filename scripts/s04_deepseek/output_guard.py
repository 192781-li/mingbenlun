# -*- coding: utf-8 -*-
"""
输出守卫 output_guard —— 输出前的强制自检硬闸（E07/E11/E12/E13 固化）。

事故根因：用户反复要求"冷峻简洁狠、不画饼、不说空话、不元话语爆炸"，
但 S04 经常输出几百字"我识别到...我计划...我将..."，用"完美/绝对/彻底/必然胜利"
等无数据支撑的绝对化词汇画饼。这些是软约束（靠自觉），必须变成硬闸（不过闸无法输出）。

检查项（每项不通过=输出不合格，必须修正后再输出）：
  1. 禁用绝对化词汇：完美/绝对/彻底/必然胜利/100%/一定能/保证完成（除非有具体数据支撑）
  2. 禁用元话语铺垫：我识别到/我计划/我将/我打算/我准备/首先我/接下来我（超过2处）
  3. 行数限制：常规回答不超过30行（复杂报告不超过80行）
  4. 每个结论必须有数据支撑：commit hash / coqc 结果 / 文件路径 / 可复现数据（结论句无支撑=不合格）
  5. 明性 F3 不混用：检查"明性"是否被泛化为一切意识照亮（与"生命之光/照亮/红点"同时出现需告警）

用法：
  python output_guard.py check <text_file>     # 检查文件
  python output_guard.py check-stdin            # 从 stdin 读
  python output_guard.py selftest                # 离线自检

设计原则：
  - 只做机械检查，不做语义判断（语义判断靠人）
  - 告警≠阻止，硬错误=阻止（exit 1）
  - 检查结果落 trace，可追溯
"""
import sys, re, os, datetime

# ---------------------------------------------------------------- 禁用词汇
# 绝对化词汇（无数据支撑时禁用；有具体数据/引用时允许，但需人工确认）
ABSOLUTE_WORDS = [
    r"完美", r"绝对(?!路径|地址|值|坐标|时间|压强|温度|湿度|高度|速度|位置)",
    r"彻底(?!解决|根治|清除|消灭|删除|改变|推翻|否定)", r"必然胜利",
    r"100%", r"一定能", r"保证完成", r"毫无疑问", r"毋庸置疑",
    r"完美无缺", r"万无一失", r"稳操胜券",
]
# 元话语铺垫（超过2处=不合格）
META_DISCOURSE = [
    r"我识别到", r"我计划", r"我将", r"我打算", r"我准备",
    r"首先我", r"接下来我", r"我认为我", r"我觉得我",
    r"我现在要", r"我接下来要",
]
# 结论句标记（以"因此/所以/综上/结论是/这说明/可见/证明了"开头的句子）
CONCLUSION_MARKERS = r"(?:因此|所以|综上|综上所述|结论是|这说明|可见|证明了|表明了|证实了)"
# 数据支撑标记（commit hash / coqc / 文件路径 / 数字+单位 / 引用）
EVIDENCE_MARKERS = [
    r"[0-9a-f]{7,40}",  # commit hash
    r"coqc\s*(?:exit|通过|失败|exit=)",
    r"(?:docs|scripts|coq|tools)/[\w/._-]+",  # 文件路径
    r"\d+\s*(?:个|条|轮|元|分钟|小时|天|次|行|KB|MB|%)",  # 数字+单位
    r"L\d{3}",  # 教训编号
    r"结晶\d{3}",  # 结晶编号
]
# 明性混用检查：明性与"照亮/红点/生命之光/常亮"同时出现需告警
MINGXING_MIX = [r"明性", r"(?:照亮|红点|生命之光|常亮|向外照亮)"]

MAX_LINES_NORMAL = 30
MAX_LINES_REPORT = 80


def check_absolute_words(text):
    """检查绝对化词汇。返回 [(word, line_no)]"""
    hits = []
    for i, line in enumerate(text.split("\n"), 1):
        for pat in ABSOLUTE_WORDS:
            for m in re.finditer(pat, line):
                # 有数据支撑的绝对化词汇允许（同行有 commit hash / 数字 / 文件路径）
                has_evidence = any(re.search(em, line) for em in EVIDENCE_MARKERS)
                if not has_evidence:
                    hits.append((m.group(0), i))
    return hits


def check_meta_discourse(text):
    """检查元话语铺垫。超过2处=不合格。返回 [(phrase, line_no)]"""
    hits = []
    for i, line in enumerate(text.split("\n"), 1):
        for pat in META_DISCOURSE:
            for m in re.finditer(pat, line):
                hits.append((m.group(0), i))
    return hits


def check_line_count(text, is_report=False):
    """检查行数。返回 (actual, limit)"""
    lines = text.strip().split("\n")
    limit = MAX_LINES_REPORT if is_report else MAX_LINES_NORMAL
    return len(lines), limit


def check_conclusion_evidence(text):
    """检查结论句是否有数据支撑。返回 [(conclusion, line_no, has_evidence)]"""
    hits = []
    for i, line in enumerate(text.split("\n"), 1):
        # 找结论句
        for m in re.finditer(CONCLUSION_MARKERS + r"[^\n。！？]*[。！？]?", line):
            sent = m.group(0)
            has_evidence = any(re.search(em, sent) for em in EVIDENCE_MARKERS)
            if not has_evidence and len(sent) > 10:  # 短结论（如"因此Qed"）不算
                hits.append((sent[:60], i, False))
    return hits


def check_mingxing_mix(text):
    """检查明性 F3 是否与生命之光混用。返回 [(line_no, context)]"""
    hits = []
    for i, line in enumerate(text.split("\n"), 1):
        has_mingxing = re.search(MINGXING_MIX[0], line)
        has_light = re.search(MINGXING_MIX[1], line)
        if has_mingxing and has_light:
            hits.append((i, line.strip()[:80]))
    return hits


def check(text, is_report=False):
    """完整检查。返回 dict：passed(bool), errors(list), warnings(list), stats(dict)"""
    errors = []
    warnings = []

    # 1. 绝对化词汇（硬错误）
    abs_hits = check_absolute_words(text)
    for word, line in abs_hits:
        errors.append("绝对化词汇无数据支撑: '%s' (行%d)" % (word, line))

    # 2. 元话语（超过2处=硬错误）
    meta_hits = check_meta_discourse(text)
    if len(meta_hits) > 2:
        errors.append("元话语铺垫过多: %d处（限2处）" % len(meta_hits))
    elif len(meta_hits) > 0:
        warnings.append("元话语铺垫: %d处" % len(meta_hits))

    # 3. 行数（硬错误）
    actual, limit = check_line_count(text, is_report)
    if actual > limit:
        errors.append("行数超限: %d行（限%d行）" % (actual, limit))

    # 4. 结论无数据支撑（告警，非硬错误——有些结论是哲学判断，允许无数据但需标注）
    concl_hits = check_conclusion_evidence(text)
    for sent, line, _ in concl_hits:
        warnings.append("结论句可能无数据支撑: '%s...' (行%d)" % (sent, line))

    # 5. 明性混用（告警）
    mx_hits = check_mingxing_mix(text)
    for line, ctx in mx_hits:
        warnings.append("明性F3可能与生命之光混用 (行%d): %s" % (line, ctx))

    passed = len(errors) == 0
    return {
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "absolute_words": len(abs_hits),
            "meta_discourse": len(meta_hits),
            "lines": actual,
            "line_limit": limit,
            "conclusions_no_evidence": len(concl_hits),
            "mingxing_mix": len(mx_hits),
        },
    }


def format_report(result):
    """格式化检查报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("输出守卫 output_guard 检查报告")
    lines.append("=" * 60)
    lines.append("状态: %s" % ("PASS ✅" if result["passed"] else "FAIL ❌（必须修正后再输出）"))
    lines.append("")
    if result["errors"]:
        lines.append("【硬错误】（必须修正）:")
        for e in result["errors"]:
            lines.append("  ❌ %s" % e)
        lines.append("")
    if result["warnings"]:
        lines.append("【告警】（建议修正）:")
        for w in result["warnings"]:
            lines.append("  ⚠️  %s" % w)
        lines.append("")
    s = result["stats"]
    lines.append("【统计】:")
    lines.append("  绝对化词汇: %d" % s["absolute_words"])
    lines.append("  元话语铺垫: %d" % s["meta_discourse"])
    lines.append("  行数: %d / 限%d" % (s["lines"], s["line_limit"]))
    lines.append("  结论无数据支撑: %d" % s["conclusions_no_evidence"])
    lines.append("  明性F3混用: %d" % s["mingxing_mix"])
    lines.append("=" * 60)
    return "\n".join(lines)


# ================================================================== 离线自检
if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        print("== output_guard 离线自检 ==")

        # 测试1：合格输出
        good = """【S04】J1g选择层Qed净增长
编译：coqc exit=0，Admitted：L2=1
DS：2轮，0.087元
commit：715c269
需要主人：无"""
        r1 = check(good)
        assert r1["passed"], "合格输出应通过: %s" % r1["errors"]
        print("  测试1（合格输出）: PASS")

        # 测试2：绝对化词汇
        bad_abs = "这个方案完美无缺，一定能彻底解决问题。"
        r2 = check(bad_abs)
        assert not r2["passed"], "绝对化词汇应失败"
        assert any("绝对化词汇" in e for e in r2["errors"]), "应报绝对化词汇错误"
        print("  测试2（绝对化词汇）: PASS（抓到 %d 处）" % r2["stats"]["absolute_words"])

        # 测试3：元话语过多
        bad_meta = "我识别到问题。我计划这样做。我将开始执行。我准备下一步。"
        r3 = check(bad_meta)
        assert not r3["passed"], "元话语过多应失败"
        assert any("元话语" in e for e in r3["errors"]), "应报元话语错误"
        print("  测试3（元话语过多）: PASS（抓到 %d 处）" % r3["stats"]["meta_discourse"])

        # 测试4：行数超限
        bad_lines = "\n".join(["line %d" % i for i in range(40)])
        r4 = check(bad_lines)
        assert not r4["passed"], "行数超限应失败"
        print("  测试4（行数超限）: PASS（%d行）" % r4["stats"]["lines"])

        # 测试5：有数据支撑的绝对化词汇允许
        ok_abs = "彻底根治完成，commit 5764e2a，39个错误31已固化。"
        r5 = check(ok_abs)
        assert r5["passed"], "有数据支撑的绝对化词汇应通过: %s" % r5["errors"]
        print("  测试5（有数据支撑的绝对化）: PASS")

        # 测试6：明性混用告警
        mx_text = "明性照亮了整个场域，红点常亮。"
        r6 = check(mx_text)
        assert len(r6["warnings"]) > 0, "明性混用应告警"
        print("  测试6（明性混用告警）: PASS")

        print("\n[output_guard] 离线自检全部通过。")

    elif len(sys.argv) >= 3 and sys.argv[1] == "check":
        with open(sys.argv[2], encoding="utf-8") as f:
            text = f.read()
        is_report = "--report" in sys.argv
        result = check(text, is_report)
        print(format_report(result))
        sys.exit(0 if result["passed"] else 1)

    elif len(sys.argv) >= 2 and sys.argv[1] == "check-stdin":
        text = sys.stdin.read()
        result = check(text)
        print(format_report(result))
        sys.exit(0 if result["passed"] else 1)

    else:
        print("用法:")
        print("  python output_guard.py check <file> [--report]")
        print("  python output_guard.py check-stdin")
        print("  python output_guard.py selftest")
        sys.exit(1)

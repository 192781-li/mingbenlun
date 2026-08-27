#!/usr/bin/env python3
"""
社会N值蒙特卡洛模拟
把单点估算升级为区间估算+不确定性量化
"""
import random
import json
from statistics import mean, median, stdev

def estimate_N(fertility, trust, mental_health, le_trend, creativity, suicide_rate):
    """6指标加权估算N值（来自social_n_diagnosis.py）"""
    scores = {}
    # 1. 生育率
    if fertility >= 2.1:
        scores["fertility"] = 0.15
    elif fertility >= 1.5:
        scores["fertility"] = 0.0
    elif fertility >= 1.2:
        scores["fertility"] = -0.10
    else:
        scores["fertility"] = -0.20
    # 2. 社会信任
    scores["trust"] = (trust - 0.40) * 0.5
    # 3. 心理健康
    scores["mental_health"] = (mental_health - 0.50) * 0.3
    # 4. 预期寿命趋势
    scores["le_trend"] = le_trend * 0.08
    # 5. 创造性
    scores["creativity"] = (creativity - 0.50) * 0.15
    # 6. 自杀率
    if suicide_rate <= 8:
        scores["suicide"] = 0.02
    elif suicide_rate <= 12:
        scores["suicide"] = -0.02
    else:
        scores["suicide"] = -0.08
    N = 1.0 + sum(scores.values())
    return max(0.3, min(2.0, N)), scores

def monte_carlo(params, n=10000):
    """蒙特卡洛模拟：每个参数在[low, high]均匀采样"""
    results = []
    score_history = []
    for _ in range(n):
        fertility = random.uniform(*params["fertility"])
        trust = random.uniform(*params["trust"])
        mh = random.uniform(*params["mental_health"])
        le = random.uniform(*params["le_trend"])
        creat = random.uniform(*params["creativity"])
        sr = random.uniform(*params["suicide_rate"])
        N, scores = estimate_N(fertility, trust, mh, le, creat, sr)
        results.append(N)
        score_history.append(scores)
    return results, score_history

def percentile(data, p):
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_data) else f
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

def sensitivity_analysis(params, n=5000):
    """单因素敏感性分析：每次只变一个参数，其他取中心值"""
    base = {k: (v[0]+v[1])/2 for k, v in params.items()}
    base_N, _ = estimate_N(**base)
    results = {}
    for param in params:
        low = dict(base); low[param] = params[param][0]
        high = dict(base); high[param] = params[param][1]
        N_low, _ = estimate_N(**low)
        N_high, _ = estimate_N(**high)
        results[param] = {
            "base": base_N,
            "low": N_low,
            "high": N_high,
            "range": abs(N_high - N_low)
        }
    return results

def weight_robustness(params, n=5000):
    """权重稳健性检验：随机扰动权重，看N值分布变化"""
    base_weights = {"fertility": 0.15, "trust": 0.5, "mental_health": 0.3, "le_trend": 0.08, "creativity": 0.15, "suicide": 0.05}
    results = []
    for _ in range(n):
        # 每个权重在±30%范围内随机扰动
        w = {k: v * random.uniform(0.7, 1.3) for k, v in base_weights.items()}
        # 用扰动后的权重计算（简化版：只改连续变量的权重，分档变量保持不变）
        fertility = (params["fertility"][0]+params["fertility"][1])/2
        trust = (params["trust"][0]+params["trust"][1])/2
        mh = (params["mental_health"][0]+params["mental_health"][1])/2
        le = (params["le_trend"][0]+params["le_trend"][1])/2
        creat = (params["creativity"][0]+params["creativity"][1])/2
        sr = (params["suicide_rate"][0]+params["suicide_rate"][1])/2
        # 生育率和自杀率是分档的，权重影响有限
        if fertility >= 2.1: fert_score = 0.15 * random.uniform(0.7, 1.3)
        elif fertility >= 1.5: fert_score = 0.0
        elif fertility >= 1.2: fert_score = -0.10 * random.uniform(0.7, 1.3)
        else: fert_score = -0.20 * random.uniform(0.7, 1.3)
        if sr <= 8: suic_score = 0.02 * random.uniform(0.7, 1.3)
        elif sr <= 12: suic_score = -0.02 * random.uniform(0.7, 1.3)
        else: suic_score = -0.08 * random.uniform(0.7, 1.3)
        N = 1.0 + fert_score + (trust-0.4)*w["trust"] + (mh-0.5)*w["mental_health"] + le*w["le_trend"] + (creat-0.5)*w["creativity"] + suic_score
        results.append(max(0.3, min(2.0, N)))
    return results

# ============================================================
# 参数定义（取值范围，基于历史数据和估算）
# ============================================================

mao_era = {
    "fertility": (4.5, 5.5),        # 总和生育率，国家统计局数据
    "trust": (0.75, 0.90),           # 社会信任度，估算（革命后集体主义）
    "mental_health": (0.55, 0.75),   # 心理健康指数，估算（意义感强但政治压力大）
    "le_trend": (1.0, 2.0),          # 预期寿命年变化，60→65岁/10年
    "creativity": (0.35, 0.55),      # 创新指数，政治运动压制
    "suicide_rate": (10, 15),        # 每10万人自杀率，估算
}

dayue_tui = {
    "fertility": (1.0, 1.3),         # 总和生育率，国家统计局1.09
    "trust": (0.40, 0.55),           # 社会信任度，WVS约50%且下降
    "mental_health": (0.45, 0.65),   # 心理健康指数，抑郁焦虑上升
    "le_trend": (-0.5, 0.5),         # 预期寿命年变化，疫情后停滞
    "creativity": (0.55, 0.75),      # 创新指数，WIPO排名上升
    "suicide_rate": (6, 10),         # 每10万人自杀率，WHO数据
}

# ============================================================
# 运行模拟
# ============================================================
random.seed(42)

print("=" * 70)
print("社会N值蒙特卡洛模拟报告")
print("=" * 70)

for name, params in [("毛泽东时代(1965-1975)", mao_era), ("大跃退时代(2010-2024)", dayue_tui)]:
    print(f"\n{'='*70}")
    print(f"【{name}】")
    print(f"{'='*70}")

    # 参数范围
    print("\n参数取值范围：")
    for k, v in params.items():
        print(f"  {k:20s}: [{v[0]:.2f}, {v[1]:.2f}]  中心={ (v[0]+v[1])/2:.2f}")

    # 蒙特卡洛
    results, score_history = monte_carlo(params, n=10000)
    print(f"\nN值分布（10000次采样）：")
    print(f"  均值   = {mean(results):.4f}")
    print(f"  中位数 = {median(results):.4f}")
    print(f"  标准差 = {stdev(results):.4f}")
    print(f"  最小值 = {min(results):.4f}")
    print(f"  最大值 = {max(results):.4f}")
    print(f"  5%分位  = {percentile(results, 5):.4f}")
    print(f"  25%分位 = {percentile(results, 25):.4f}")
    print(f"  75%分位 = {percentile(results, 75):.4f}")
    print(f"  95%分位 = {percentile(results, 95):.4f}")
    print(f"  90%置信区间: [{percentile(results, 5):.4f}, {percentile(results, 95):.4f}]")

    # N>1的概率
    p_gt1 = sum(1 for r in results if r > 1.0) / len(results) * 100
    print(f"  N>1（成长态）的概率: {p_gt1:.1f}%")
    p_gt105 = sum(1 for r in results if r > 1.05) / len(results) * 100
    print(f"  N>1.05（明显成长）的概率: {p_gt105:.1f}%")
    p_lt1 = sum(1 for r in results if r < 1.0) / len(results) * 100
    print(f"  N<1（衰退态）的概率: {p_lt1:.1f}%")

    # 各指标平均贡献
    print(f"\n各指标平均贡献：")
    avg_scores = {}
    for key in score_history[0]:
        avg_scores[key] = mean(s[key] for s in score_history)
    for key, val in sorted(avg_scores.items(), key=lambda x: abs(x[1]), reverse=True):
        sign = "+" if val > 0 else ""
        print(f"  {key:20s}: {sign}{val:.4f}")

    # 敏感性分析
    print(f"\n敏感性分析（单因素变动，其他取中心值）：")
    sens = sensitivity_analysis(params)
    for param, res in sorted(sens.items(), key=lambda x: x[1]["range"], reverse=True):
        print(f"  {param:20s}: N范围[{res['low']:.4f}, {res['high']:.4f}]  变动幅度={res['range']:.4f}")

    # 权重稳健性
    wr = weight_robustness(params, n=5000)
    print(f"\n权重稳健性检验（权重±30%扰动，5000次）：")
    print(f"  均值   = {mean(wr):.4f}")
    print(f"  90%区间: [{percentile(wr, 5):.4f}, {percentile(wr, 95):.4f}]")
    p_gt1_wr = sum(1 for r in wr if r > 1.0) / len(wr) * 100
    print(f"  N>1的概率: {p_gt1_wr:.1f}%")

# ============================================================
# 两个时代的对比
# ============================================================
print(f"\n{'='*70}")
print("【两个时代对比】")
print(f"{'='*70}")

mao_results, _ = monte_carlo(mao_era, n=10000)
dyt_results, _ = monte_carlo(dayue_tui, n=10000)

# 毛泽东时代N > 大跃退时代N的概率
count = 0
for _ in range(10000):
    if random.choice(mao_results) > random.choice(dyt_results):
        count += 1
print(f"  毛泽东时代N > 大跃退时代N的概率: {count/100:.1f}%")
print(f"  毛泽东时代N均值: {mean(mao_results):.4f}  90%区间[{percentile(mao_results,5):.4f}, {percentile(mao_results,95):.4f}]")
print(f"  大跃退时代N均值: {mean(dyt_results):.4f}  90%区间[{percentile(dyt_results,5):.4f}, {percentile(dyt_results,95):.4f}]")

# 保存结果
output = {
    "mao_era": {
        "mean": mean(mao_results),
        "median": median(mao_results),
        "std": stdev(mao_results),
        "ci90": [percentile(mao_results, 5), percentile(mao_results, 95)],
        "p_gt_1": sum(1 for r in mao_results if r > 1) / len(mao_results),
    },
    "dayue_tui": {
        "mean": mean(dyt_results),
        "median": median(dyt_results),
        "std": stdev(dyt_results),
        "ci90": [percentile(dyt_results, 5), percentile(dyt_results, 95)],
        "p_gt_1": sum(1 for r in dyt_results if r > 1) / len(dyt_results),
    },
    "mao_gt_dyt_probability": count / 10000,
}
with open("/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun/mingben-workbench/results/n_value_monte_carlo.json", "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(f"\n结果已保存到 mingben-workbench/results/n_value_monte_carlo.json")

#!/usr/bin/env python3
"""
社会N值诊断工具
用真实社会指标估计N（生命力）、W（萃取率）、M（意义量）
数据来源：世界银行、WHO、各国统计局公开数据
"""
import json
from dataclasses import dataclass, field
from typing import Optional

# ============================================================
# 数据：各国社会指标（最近可用年份，约2020-2024）
# ============================================================

COUNTRY_DATA = {
    "中国": {
        "fertility_rate": 1.09,       # 总和生育率 2023（国家统计局）
        "fertility_replacement": 2.1,  # 更替水平
        "trust_level": 0.50,           # 社会信任度（"大多数人可信"比例，WVS约50%，近年下降）
        "mental_health_index": 0.55,   # 心理健康指数（抑郁/焦虑患病率反向，WHO估计）
        "life_expectancy": 78.2,       # 预期寿命
        "life_expectancy_trend": -0.3, # 疫情后趋势（年变化，负=下降）
        "gini": 0.47,                  # 基尼系数（官方0.47，民间估计更高）
        "labor_share": 0.52,           # 劳动报酬占GDP比重（约52%，发达国家约60%+）
        "housing_burden": 0.45,        # 住房支出占收入比（一线城市更高）
        "suicide_rate": 8.0,           # 每10万人自杀率（WHO，近年下降但青少年上升）
        "social_mobility": 0.40,       # 代际流动性（0-1，低=固化）
        "work_hours": 47.0,            # 平均周工时（国家统计局约47小时，996行业更高）
        "creativity_index": 0.65,      # 创新指数（WIPO全球创新指数排名折算）
        "education_burden": 0.35,      # 教育支出占家庭收入比
        "medical_burden": 0.20,        # 医疗支出占家庭收入比
        "youth_unemployment": 0.20,    # 青年失业率（官方约20%，2023年曾暂停发布）
    },
    "美国": {
        "fertility_rate": 1.66,
        "fertility_replacement": 2.1,
        "trust_level": 0.37,           # WVS: 约37%
        "mental_health_index": 0.45,
        "life_expectancy": 76.4,
        "life_expectancy_trend": -0.5,
        "gini": 0.41,
        "labor_share": 0.56,
        "housing_burden": 0.30,
        "suicide_rate": 14.5,
        "social_mobility": 0.45,
        "work_hours": 38.7,
        "creativity_index": 0.85,
        "education_burden": 0.25,
        "medical_burden": 0.30,
        "youth_unemployment": 0.08,
    },
    "日本": {
        "fertility_rate": 1.30,
        "fertility_replacement": 2.1,
        "trust_level": 0.39,
        "mental_health_index": 0.50,
        "life_expectancy": 84.3,
        "life_expectancy_trend": 0.0,
        "gini": 0.33,
        "labor_share": 0.56,
        "housing_burden": 0.25,
        "suicide_rate": 14.0,
        "social_mobility": 0.47,
        "work_hours": 36.6,
        "creativity_index": 0.75,
        "education_burden": 0.20,
        "medical_burden": 0.15,
        "youth_unemployment": 0.04,
    },
    "瑞典": {
        "fertility_rate": 1.70,
        "fertility_replacement": 2.1,
        "trust_level": 0.65,           # 北欧高信任
        "mental_health_index": 0.60,
        "life_expectancy": 83.3,
        "life_expectancy_trend": 0.1,
        "gini": 0.28,
        "labor_share": 0.62,
        "housing_burden": 0.22,
        "suicide_rate": 11.7,
        "social_mobility": 0.60,
        "work_hours": 36.0,
        "creativity_index": 0.80,
        "education_burden": 0.10,      # 免费教育
        "medical_burden": 0.10,        # 公费医疗
        "youth_unemployment": 0.08,
    },
    "毛泽东时代中国(1965-1975)": {
        "fertility_rate": 5.0,         # 高生育率
        "fertility_replacement": 2.1,
        "trust_level": 0.85,           # 估计：高社会信任（革命后集体主义）
        "mental_health_index": 0.65,   # 估计：意义感强但政治压力大
        "life_expectancy": 65.0,       # 从35岁增长到65岁
        "life_expectancy_trend": 1.5,  # 快速增长
        "gini": 0.20,                  # 低不平等
        "labor_share": 0.70,           # 高劳动份额（资本收益低）
        "housing_burden": 0.05,        # 福利分房
        "suicide_rate": 12.0,          # 政治运动期间估计较高
        "social_mobility": 0.70,       # 高流动性（出身不好受歧视但普通群众上升通道）
        "work_hours": 48.0,
        "creativity_index": 0.45,      # 政治运动压制部分创造力
        "education_burden": 0.05,      # 免费/低成本教育
        "medical_burden": 0.05,        # 公费医疗
        "youth_unemployment": 0.05,    # 上山下乡但本质是就业
    },
}

# ============================================================
# N/W/M 估计模型
# ============================================================

@dataclass
class SocialDiagnosis:
    country: str
    N: float          # 生命力（<1衰退，=1稳态，>1成长）
    W: float          # 萃取率（0-1）
    M_relative: float # 相对意义量（以某基准为1）
    N_confidence: float  # 估计置信度（0-1）
    diagnosis: str
    indicators: dict = field(default_factory=dict)


def estimate_N(data: dict) -> tuple[float, float, dict]:
    """
    估计社会N值。
    N = 1 + Σ(贡献项)，每个贡献项反映"社会反馈是生产性的还是萃取性的"
    
    代理指标映射：
    - 生育率：N>1→对未来有信心→生育率≥更替；N<1→看不到未来→生育率暴跌
    - 社会信任：线性耦合的基础，高信任=高N
    - 心理健康：N<1→慢性死亡→抑郁/焦虑/自杀
    - 预期寿命趋势：N>1→T延长；N<1→T缩短
    - 创造性：N>1→ν*F扩展；N<1→文化停滞
    - 工作时长/强度：过长=被萃取，但不是直接的N指标
    """
    scores = {}
    
    # 1. 生育率贡献（权重0.25）
    fr = data["fertility_rate"]
    rep = data["fertility_replacement"]
    if fr >= rep:
        fert_score = 0.15  # 达到更替水平
    elif fr >= 1.5:
        fert_score = 0.0
    elif fr >= 1.2:
        fert_score = -0.10
    else:
        fert_score = -0.20  # 极低生育率=严重衰退信号
    scores["生育率"] = fert_score
    
    # 2. 社会信任贡献（权重0.20）
    trust = data["trust_level"]
    trust_score = (trust - 0.40) * 0.5  # 以40%为中性
    scores["社会信任"] = round(trust_score, 3)
    
    # 3. 心理健康贡献（权重0.20）
    mh = data["mental_health_index"]
    mh_score = (mh - 0.50) * 0.3
    scores["心理健康"] = round(mh_score, 3)
    
    # 4. 预期寿命趋势（权重0.15）
    le_trend = data["life_expectancy_trend"]
    le_score = le_trend * 0.08
    scores["预期寿命趋势"] = round(le_score, 3)
    
    # 5. 创造性贡献（权重0.10）
    creat = data["creativity_index"]
    creat_score = (creat - 0.50) * 0.15
    scores["创造性"] = round(creat_score, 3)
    
    # 6. 自杀率反向贡献（权重0.10）
    # 自杀率<10为正常，>15为严重
    sr = data["suicide_rate"]
    if sr <= 8:
        suicide_score = 0.02
    elif sr <= 12:
        suicide_score = -0.02
    else:
        suicide_score = -0.08
    scores["自杀率"] = suicide_score
    
    N = 1.0 + sum(scores.values())
    N = max(0.3, min(2.0, N))  # 限制在合理范围
    
    # 置信度：数据越完整、指标越一致，置信度越高
    confidence = 0.6  # 代理指标模型的基础置信度
    # 如果所有指标方向一致，提高置信度
    signs = [1 if v > 0 else (-1 if v < 0 else 0) for v in scores.values()]
    if abs(sum(signs)) >= 4:
        confidence += 0.15
    if abs(sum(signs)) >= 5:
        confidence += 0.10
    
    return round(N, 3), round(confidence, 2), scores


def estimate_W(data: dict) -> tuple[float, dict]:
    """
    估计萃取率W。
    W = 活劳动产出中被!-寄生体拿走的比例
    
    代理指标：
    - 劳动份额：W ≈ 1 - labor_share（资本拿走的部分）
    - 基尼系数：高基尼=高萃取
    - 住房/教育/医疗负担：三座大山=直接萃取
    - 代际流动性：低流动性=!-沉积自我复制（δ: !X→!!X）
    """
    scores = {}
    
    # 1. 资本萃取（权重0.35）
    capital_extraction = 1.0 - data["labor_share"]
    scores["资本萃取"] = round(capital_extraction, 3)
    
    # 2. 不平等附加（权重0.15）
    gini = data["gini"]
    gini_extraction = max(0, (gini - 0.30) * 0.5)
    scores["不平等附加"] = round(gini_extraction, 3)
    
    # 3. 三座大山超额负担（权重0.30）
    # 住房/教育/医疗的"基本保障线"以下不算萃取，以上才算
    # 社会主义底线：住房<15%、教育<5%、医疗<5%
    excess_housing = max(0, data["housing_burden"] - 0.15)
    excess_education = max(0, data["education_burden"] - 0.05)
    excess_medical = max(0, data["medical_burden"] - 0.05)
    burden_extraction = min(0.30, (excess_housing + excess_education + excess_medical) * 0.5)
    scores["三座大山超额"] = round(burden_extraction, 3)
    
    # 4. 流动性扣除（权重0.20）
    mobility = data["social_mobility"]
    mobility_extraction = (1 - mobility) * 0.15
    scores["流动性扣除"] = round(mobility_extraction, 3)
    
    W = sum(scores.values())
    W = max(0.0, min(0.95, W))
    
    return round(W, 3), scores


def estimate_M(N: float, T: int = 70, alpha: float = 1.0) -> float:
    """
    估计意义量M = α·T_cap·ΣNⁿ
    T_cap取预期寿命×365（天），这里用年为单位简化
    """
    if N == 1.0:
        M = alpha * T
    elif N < 1.0:
        M = alpha * (1 - N**T) / (1 - N) if N != 1.0 else alpha * T
    else:
        # N>1时M指数增长，但用有限T
        M = alpha * (N**T - 1) / (N - 1)
    return M


def diagnose(country: str, data: dict) -> SocialDiagnosis:
    """综合诊断"""
    N, confidence, n_scores = estimate_N(data)
    W, w_scores = estimate_W(data)
    
    T = int(data["life_expectancy"])
    M = estimate_M(N, T)
    
    # 诊断文本
    if N > 1.05:
        diagnosis = f"成长态（N={N}）：社会反馈生产性，意义量指数增长，人民对未来有信心"
    elif N > 0.95:
        diagnosis = f"稳态（N={N}）：社会反馈接近平衡，可持续但缺乏成长动力"
    elif N > 0.80:
        diagnosis = f"轻度衰退（N={N}）：意义量有限增长后趋于枯竭，慢性死亡早期"
    elif N > 0.65:
        diagnosis = f"中度衰退（N={N}）：意义量明显有限，社会在慢性死亡中"
    else:
        diagnosis = f"严重衰退（N={N}）：意义量极度有限，社会接近崩溃"
    
    if W > 0.5:
        diagnosis += f"；萃取率极高（W={W}），!-寄生体严重"
    elif W > 0.35:
        diagnosis += f"；萃取率较高（W={W}）"
    elif W < 0.20:
        diagnosis += f"；萃取率低（W={W}），分配较公平"
    
    indicators = {
        "N分项": n_scores,
        "W分项": w_scores,
        "预期寿命T": T,
        "相对M值": round(M, 1),
    }
    
    return SocialDiagnosis(
        country=country,
        N=N,
        W=W,
        M_relative=M,
        N_confidence=confidence,
        diagnosis=diagnosis,
        indicators=indicators,
    )


def main():
    print("=" * 70)
    print("社会N值诊断工具（操作度量学原型）")
    print("=" * 70)
    print()
    print("⚠ 注意：N/W值是基于代理指标的估计，不是精确测量。")
    print("  代理指标包括：生育率、信任度、心理健康、预期寿命趋势、")
    print("  创造性、自杀率、劳动份额、基尼系数、住房/教育/医疗负担。")
    print("  置信度反映指标方向一致性，不反映绝对准确性。")
    print()
    
    results = []
    for country, data in COUNTRY_DATA.items():
        d = diagnose(country, data)
        results.append(d)
    
    # 按N值排序
    results.sort(key=lambda x: x.N, reverse=True)
    
    # 打印表格
    print(f"{'国家/地区':<25} {'N值':>6} {'W值':>6} {'置信度':>6} {'诊断'}")
    print("-" * 90)
    for r in results:
        print(f"{r.country:<25} {r.N:>6.3f} {r.W:>6.3f} {r.N_confidence:>5.2f}  {r.diagnosis}")
    
    print()
    print("=" * 70)
    print("详细指标")
    print("=" * 70)
    
    for r in results:
        print(f"\n【{r.country}】N={r.N}, W={r.W}, T={r.indicators['预期寿命T']}年")
        print(f"  N分项：")
        for k, v in r.indicators["N分项"].items():
            sign = "+" if v > 0 else ""
            print(f"    {k:<12} {sign}{v:.3f}")
        print(f"  W分项：")
        for k, v in r.indicators["W分项"].items():
            print(f"    {k:<12} {v:.3f}")
    
    # 关键发现
    print()
    print("=" * 70)
    print("关键发现")
    print("=" * 70)
    
    china_modern = next(r for r in results if r.country == "中国")
    china_mao = next(r for r in results if "毛泽东时代" in r.country)
    
    print(f"""
1. 生育率是N值最强的单一信号：
   - 中国当前生育率1.09（全球最低之一）→ N={china_modern.N}
   - 毛泽东时代生育率5.0 → N={china_mao.N}
   - 生育率不是"养不起"那么简单——它是社会生命力的综合温度计

2. 毛泽东时代N={china_mao.N}但W={china_mao.W}：
   - N高（成长态）：信任高、流动性高、寿命快速增长、三座大山基本消除
   - W低（萃取少）：劳动份额高、福利分房、免费教育医疗
   - 但创造力分项为负（政治运动压制），自杀率分项为负
   - 这说明：N>1不代表一切都好——成长可以伴随痛苦

3. 瑞典N={next(r.N for r in results if r.country=='瑞典')}：
   - 资本主义框架内N值最高——高信任、高福利、低萃取
   - 但生育率仍低于更替水平（1.70），说明资本主义框架内N>1.05很难

4. 美国N={next(r.N for r in results if r.country=='美国')}：
   - 创造性高（0.85）拉动N，但信任低（0.37）、心理健康差（0.45）拖累
   - W={next(r.W for r in results if r.country=='美国')}：医疗负担30%是主要萃取

5. 模型局限：
   - 代理指标不是N值本身，是N值的可观测影子
   - 毛泽东时代数据部分是估计值，置信度应更低
   - 没有包含政治自由度、环境质量等维度
   - N值是社会整体平均值，掩盖了阶级/地区/年龄差异
""")


if __name__ == "__main__":
    main()

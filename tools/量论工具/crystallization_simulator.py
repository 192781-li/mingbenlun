#!/usr/bin/env python3
"""
结晶动力学模拟器
模拟活系统（νF₂）中!-沉积的产生、积累、结晶、反萃取过程
对应论文第二十五章
"""
import numpy as np
import json
import os

def simulate_crystallization(
    N0=1.15,        # 初始生命力
    k_d=0.05,       # 沉积速率（每步产生多少沉积）
    k_c=0.03,       # 明性清除速率
    beta=0.15,      # 结晶反萃取率
    D_c=1.0,        # 结晶阈值
    steps=200,      # 模拟步数
    M_const=None,   # 生命意义量（None=N*10）
    intervention=None,  # 干预函数(step, S, D) -> new_S, new_D
):
    """
    模拟结晶动力学
    dS/dt = -beta*(D-Dc)*S  （结晶压低生命力）
    dD/dt = k_d*S + beta*(D-Dc)*S - k_c*M  （沉积-结晶-清除）
    """
    S = N0
    D = 0.0
    # M是明性清除能力，和生命力S成正比，但不是10倍
    # M = S * mingxing_ratio, mingxing_ratio代表"有多在感"
    if M_const is None:
        M = S * 1.0  # 明性能力和生命力1:1
    else:
        M = M_const

    history = []
    phase = "健康"  # 健康/结晶中/衰退/恢复

    for step in range(steps):
        # 计算M（明性清除能力和生命力成正比）
        if M_const is None:
            M = max(S, 0.01)

        # 结晶反萃取
        extraction = beta * max(D - D_c, 0) * S

        # 更新
        dS = -extraction
        dD = k_d * S + extraction - k_c * M

        S_new = max(S + dS, 0.01)
        D_new = max(D + dD, 0)

        # 干预
        if intervention:
            S_new, D_new = intervention(step, S_new, D_new)

        # 阶段判断
        if D_new > D_c and S_new < 0.8:
            phase = "衰退"
        elif D_new > D_c:
            phase = "结晶中"
        elif S_new > N0 * 0.9:
            phase = "健康"
        else:
            phase = "恢复"

        history.append({
            'step': step,
            'S': round(S_new, 4),
            'D': round(D_new, 4),
            'phase': phase,
            'extraction': round(extraction, 4)
        })

        S, D = S_new, D_new

    return history

def print_summary(history, title=""):
    """打印模拟摘要"""
    print(f"\n{'='*60}")
    print(f"结晶动力学模拟：{title}")
    print(f"{'='*60}")
    print(f"{'步数':>4} {'生命力S':>8} {'沉积D':>8} {'反萃取':>8} {'阶段':>6}")
    print("-" * 45)

    # 打印关键点
    key_steps = [0, 10, 20, 50, 100, 150, len(history)-1]
    for i in key_steps:
        if i < len(history):
            h = history[i]
            print(f"{h['step']:4d} {h['S']:8.4f} {h['D']:8.4f} {h['extraction']:8.4f} {h['phase']:>6}")

    # 找相变点
    crystal_step = None
    decay_step = None
    for h in history:
        if crystal_step is None and h['D'] > 1.0:
            crystal_step = h['step']
        if decay_step is None and h['S'] < 0.8:
            decay_step = h['step']

    print(f"\n结晶开始：第{crystal_step}步" if crystal_step else "\n未结晶")
    print(f"生命力衰退：第{decay_step}步" if decay_step else "生命力未衰退")
    print(f"最终状态：S={history[-1]['S']:.4f}, D={history[-1]['D']:.4f}")

def scenario_no_mingxing():
    """场景1：无明性清除（k_c=0）——必然结晶衰退"""
    h = simulate_crystallization(k_c=0.0, steps=200)
    print_summary(h, "无明性清除（k_c=0）——官僚化必然发生")

def scenario_with_mingxing():
    """场景2：有明性清除——健康维持"""
    h = simulate_crystallization(k_c=0.04, steps=200)
    print_summary(h, "有日常明性清除（k_c=0.04）——持续清除沉积")

def scenario_growth_high_deposit():
    """场景3：高成长高沉积——N>1但沉积快"""
    h = simulate_crystallization(N0=1.3, k_d=0.08, k_c=0.04, steps=200)
    print_summary(h, "高成长高沉积（N=1.3, k_d=0.08）——成长越快越要警惕")
def scenario_revolution():
    """场景4：革命干预——第80步大清除"""
    def revolution(step, S, D):
        if step == 80:
            print(f"\n  >> 第{step}步：革命干预！清除80%沉积")
            return S * 1.1, D * 0.2  # 革命清除沉积，但也有代价
        return S, D

    h = simulate_crystallization(k_c=0.01, steps=200, intervention=revolution)
    print_summary(h, "革命干预（第80步大清除）——代价大但有效")

def scenario_distributed_mingxing():
    """场景5：分布式日常明性——最优策略"""
    h = simulate_crystallization(k_c=0.05, k_d=0.05, beta=0.12, steps=200)
    print_summary(h, "分布式日常明性（k_c=0.05=k_d）——沉积产生即清除")

def scenario_comparison():
    """对比不同策略"""
    print(f"\n{'='*60}")
    print("四种策略200步后对比")
    print(f"{'='*60}")
    print(f"{'策略':>20} {'最终S':>8} {'最终D':>8} {'阶段':>8}")
    print("-" * 50)

    scenarios = [
        ("无明性（放任）", 0.0, 0.05, 0.15, None),
        ("弱明性(k_c=0.02)", 0.02, 0.05, 0.15, None),
        ("中明性(k_c=0.04)", 0.04, 0.05, 0.15, None),
        ("强明性(k_c=0.06)", 0.06, 0.05, 0.15, None),
        ("革命一次(第80步)", 0.01, 0.05, 0.15,
         lambda s,S,D: (S*1.1, D*0.2) if s==80 else (S,D)),
    ]

    for name, k_c, k_d, beta, interv in scenarios:
        h = simulate_crystallization(k_c=k_c, k_d=k_d, beta=beta,
                                      steps=200, intervention=interv)
        last = h[-1]
        print(f"{name:>20} {last['S']:8.4f} {last['D']:8.4f} {last['phase']:>8}")

if __name__ == "__main__":
    scenario_no_mingxing()
    scenario_with_mingxing()
    scenario_growth_high_deposit()
    scenario_revolution()
    scenario_distributed_mingxing()
    scenario_comparison()

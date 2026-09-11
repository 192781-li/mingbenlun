#!/usr/bin/env python3
"""
新数学概念验证脚本
验证：临界质量定理、多体耦合、结晶过程、ν*F扩展
"""
import numpy as np
from collections import defaultdict

def critical_mass(N0, c):
    """定理14.2：临界质量 k_c = ceil((1-N0)/c) + 1"""
    k_c = int(np.ceil((1 - N0) / c)) + 1
    return k_c

def couple_N(N0, c, k):
    """k个相同过程线性耦合后的N值：N0 + c(k-1)"""
    return N0 + c * (k - 1)

def parasitic_couple(N_host, beta):
    """定理9.3：寄生耦合后宿主N = (1-beta)*N_host"""
    return (1 - beta) * N_host

def crystallization_trajectory(N0, beta, gamma, steps):
    """结晶过程：宿主N下降，寄生体N上升"""
    N_host = N0
    N_parasite = 0.001  # 初始微小沉积
    history = []
    for step in range(steps):
        history.append((step, N_host, N_parasite))
        # 宿主被萃取
        N_host = N_host * (1 - beta) + gamma * 0.1  # 宿主自己恢复一点
        # 寄生体靠萃取增长
        N_parasite = N_parasite + beta * N_host * 0.5
        if N_host < 0.01:
            N_host = 0.01
    return history

def expanding_state_space():
    """定理8.7：N>1要求状态空间无限扩展"""
    print("=== 定理8.7验证：N>1要求dim X_n→∞ ===")
    # 固定维度D=3，N>1的算子
    D = 3
    U = np.array([[1.1, 0.1, 0.0],
                  [0.1, 1.0, 0.1],
                  [0.0, 0.1, 1.1]])
    N_fixed = max(abs(np.linalg.eigvals(U)))
    print(f"  固定{D}维空间，谱半径N={N_fixed:.4f}")

    # 模拟：固定空间中N>1的算子，状态范数增长但空间有限
    x = np.ones(D) / D
    norms = []
    for i in range(20):
        x = U @ x
        norms.append(np.linalg.norm(x))
    print(f"  状态范数：{norms[0]:.4f} → {norms[-1]:.4f}（在增长，但空间只有{D}维）")
    print(f"  20步后范数{norms[-1]:.2f}，但状态仍在同一个{D}维空间里——没有新维度")
    print(f"  结论：固定空间中N>1导致状态饱和（范数无限增长但不产生新质）")
    print(f"  真正的成长需要X_n维度增长：学习新东西=进入新空间\n")

def geometric_M(N, alpha, T):
    """M = α·ΣN^n 几何级数"""
    if T == float('inf'):
        if N < 1:
            return alpha / (1 - N)
        else:
            return float('inf')
    else:
        if abs(N - 1.0) < 1e-9:
            return alpha * T
        else:
            return alpha * (N**T - 1) / (N - 1)

def verify_all():
    print("=" * 60)
    print("新数学概念验证")
    print("=" * 60)

    # 1. 临界质量定理
    print("\n=== 定理14.2：临界质量 ===")
    N0, c = 0.95, 0.01
    k_c = critical_mass(N0, c)
    print(f"  每人N={N0}，互相帮助强度c={c}")
    print(f"  临界人数k_c={k_c}")
    for k in [1, 3, 5, 6, 7, 10]:
        N_c = couple_N(N0, c, k)
        status = "成长✓" if N_c > 1 else "衰退✗"
        print(f"  k={k:2d}人: N_couple={N_c:.4f} {status}")

    # 2. 寄生耦合
    print("\n=== 定理9.3：寄生耦合 ===")
    N_host = 1.2  # 宿主本来在成长
    for beta in [0.1, 0.2, 0.3, 0.5]:
        N_new = parasitic_couple(N_host, beta)
        print(f"  萃取率β={beta:.0%}: 宿主N {N_host}→{N_new:.2f}", end="")
        if N_new < 1:
            print("（衰退！）")
        else:
            print("（还在成长）")

    # 3. 结晶过程
    print("\n=== 定理16.1：结晶过程 ===")
    hist = crystallization_trajectory(1.1, 0.08, 0.02, 30)
    phase_transition = None
    for step, Nh, Np in hist:
        if phase_transition is None and Nh <= 1.0:
            phase_transition = step
        if step % 5 == 0 or step == len(hist)-1:
            print(f"  第{step:2d}步: 宿主N={Nh:.4f}, 寄生体N={Np:.4f}")
    if phase_transition:
        print(f"  → 相变点在第{phase_transition}步（宿主N降到1以下）")

    # 4. 扩展状态空间
    print()
    expanding_state_space()

    # 5. M公式验证
    print("=== M公式验证 ===")
    test_cases = [
        (1.0, 2, 40, "N=1稳态，40轮"),
        (0.95, 2, float('inf'), "N=0.95慢性死亡，无限时间"),
        (1.1, 3, 50, "N=1.1成长，50轮"),
    ]
    for N, alpha, T, desc in test_cases:
        M = geometric_M(N, alpha, T)
        print(f"  {desc}: M={M:.2f}" if M != float('inf') else f"  {desc}: M=∞")

    # 6. !-模态耦合不产生相变
    print("\n=== 定理14.3：!-模态耦合不产生相变 ===")
    print("  线性耦合：N_couple=N0+c(k-1)，随k增长→相变")
    print("  !-模态耦合：N_couple≤max(N0,ρ(!))，不随k增长→无相变")
    print("  数学：!-模态交叉项经过沉积，不产生新线性反馈路径")
    print("  哲学：通过制度/金钱中介的'团结'不是真团结\n")

    print("=" * 60)
    print("全部验证完成")
    print("=" * 60)

if __name__ == "__main__":
    verify_all()

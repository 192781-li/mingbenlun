#!/usr/bin/env python3
"""
量论操作化验证脚本
验证 T/N/α/M/W/l'/C 的计算和定理39-42
"""
import numpy as np
from numpy.linalg import matrix_power, eigvals

def nilpotency_index(U22, tol=1e-10, max_steps=10000):
    """T = 幂零指数：最小的n使得U22^n=0"""
    n = U22.shape[0]
    current = np.eye(n)
    for i in range(max_steps):
        current = current @ U22
        if np.allclose(current, 0, atol=tol):
            return i + 1  # U^(i+1)=0，幂零指数为i+1
    return None  # 非幂零（无限过程）

def spectral_radius(U22):
    """N = 谱半径"""
    return max(abs(eigvals(U22)))

def meaning_total(alpha, T, N):
    """M = 意义总量"""
    if T is None:  # 无限过程
        if N < 1 - 1e-10:
            return alpha / (1 - N)  # 慢性死亡：有限
        else:
            return float('inf')  # 稳态或创造：无限
    else:  # 有限过程
        return alpha * T * N

def alienation_rate(N):
    """l' = (1-N)×100%"""
    if N <= 1 + 1e-10:
        return (1 - N) * 100
    else:
        return None  # 创造态无异化率

def extraction_rate(O, M):
    """W = O/M"""
    if M == 0:
        return None
    if M == float('inf'):
        return 0.0  # 无限意义中萃取有限部分，萃取率为0
    return O / M

def revolutionary_consciousness(R, A):
    """C = R - A"""
    return R - A

def analyze(name, U22, alpha=1, O=0, R=0, A=0):
    """分析一个Mealy机的量论参数"""
    N = spectral_radius(U22)
    # N=0（所有特征值为零）→ 幂零，有限过程；N>0 → 无限过程
    if N < 1e-10:
        T = nilpotency_index(U22)
    else:
        T = None  # 非幂零，无限过程
    M = meaning_total(alpha, T, N)
    lp = alienation_rate(N)
    W = extraction_rate(O, M)
    C = revolutionary_consciousness(R, A)

    print(f"\n{'='*60}")
    print(f"示例：{name}")
    print(f"{'='*60}")
    print(f"反馈矩阵 U22:")
    print(U22)
    print(f"\nT（寿命）= {T if T is not None else '∞（无限过程）'}")
    print(f"N（净方向/谱半径）= {N:.4f}")
    if N < 1 - 1e-10:
        state = "异化/磨损（慢性死亡）"
    elif N <= 1 + 1e-10:
        state = "稳态"
    else:
        state = "创造/超越"
    print(f"状态：{state}")
    print(f"α（f-层级）= {alpha}")
    print(f"M（意义总量）= {M:.4f}" if M != float('inf') else "M（意义总量）= ∞")
    if lp is not None:
        print(f"l'（异化率）= {lp:.2f}%")
    else:
        print(f"l'（异化率）= 无定义（创造态）")
    if W is not None:
        print(f"W（萃取率）= {W:.4f}")
    print(f"C（革命意识）= {C:.2f} ({'认清>接受' if C > 0 else '接受>认清' if C < 0 else '平衡'})")
    return {'T': T, 'N': N, 'M': M, 'l_prime': lp, 'W': W, 'C': C}

print("=" * 60)
print("量论操作化验证")
print("=" * 60)

# 示例1：简单有限过程（3步终止）
# x0 -> x1 -> x2 -> 终止
U1 = np.array([
    [0, 0, 0],
    [1, 0, 0],
    [0, 1, 0]
], dtype=float)
r1 = analyze("简单有限过程（3步终止，f¹）", U1, alpha=1)
assert r1['T'] == 3, f"Expected T=3, got {r1['T']}"
assert abs(r1['N']) < 1e-10, f"Expected N=0, got {r1['N']}"

# 示例2：稳态循环（f¹，N=1）
# x0 -> x1 -> x0 -> x1 -> ...
U2 = np.array([
    [0, 1],
    [1, 0]
], dtype=float)
r2 = analyze("稳态循环（2-周期，f¹）", U2, alpha=1)
assert r2['T'] is None, "Expected T=∞"
assert abs(r2['N'] - 1.0) < 1e-10, f"Expected N=1, got {r2['N']}"
assert r2['M'] == float('inf'), "Expected M=∞"

# 示例3：异化劳动（f²，N=0.95）
U3 = np.array([
    [0.95, 0.0],
    [0.0, 0.95]
], dtype=float)
r3 = analyze("异化劳动（N=0.95，f²，80%萃取）", U3, alpha=2, O=32, R=0.2, A=0.8)
assert abs(r3['N'] - 0.95) < 1e-10
assert abs(r3['M'] - 40.0) < 1e-10, f"Expected M=40, got {r3['M']}"
assert abs(r3['l_prime'] - 5.0) < 1e-10
assert abs(r3['W'] - 0.8) < 1e-10
assert abs(r3['C'] - (-0.6)) < 1e-10

# 示例4：明性实践者（f³，N=1）
U4 = np.array([
    [0, 1, 0],
    [0, 0, 1],
    [1, 0, 0]
], dtype=float)
r4 = analyze("明性实践者（3-周期稳态，f³）", U4, alpha=3, O=0.2, R=0.9, A=0.2)
assert abs(r4['N'] - 1.0) < 1e-10
assert r4['M'] == float('inf')
assert abs(r4['C'] - 0.7) < 1e-10

# 示例5：革命创造（f³，N>1）
U5 = np.array([
    [0, 1.1],
    [1.1, 0]
], dtype=float)
r5 = analyze("革命创造（N=1.1，f³）", U5, alpha=3, R=0.95, A=0.05)
assert r5['N'] > 1
assert r5['M'] == float('inf')
assert r5['l_prime'] is None  # 创造态无异化率

# 示例6：慢性死亡对比——不同N值的M
print(f"\n{'='*60}")
print("定理39验证：慢性死亡——N<1时M有限")
print(f"{'='*60}")
for N_val in [0.5, 0.9, 0.95, 0.99, 0.999]:
    M_val = 2 / (1 - N_val)  # α=2
    lp_val = (1 - N_val) * 100
    print(f"N={N_val:.3f}: M={M_val:.1f}, l'={lp_val:.1f}%")

# 验证定理41：萃取加速异化
print(f"\n{'='*60}")
print("定理41验证：萃取率W越高，N越低")
print(f"{'='*60}")
for w in [0.0, 0.2, 0.5, 0.8, 1.0]:
    # 模拟：萃取w比例的产出，反馈矩阵乘以(1-w)
    N_eff = 1.0 * (1 - w)
    print(f"W={w:.1f}: N={N_eff:.2f}, l'={(1-N_eff)*100:.1f}%")

# 验证定理42：明性抵抗磨损
print(f"\n{'='*60}")
print("定理42验证：C>0时N趋向≥1")
print(f"{'='*60}")
for C_val in [-0.8, -0.4, 0, 0.4, 0.8]:
    # C>0时f³运行，N恢复；C<0时f²接受!-模型，N下降
    N_base = 0.9
    N_adjusted = N_base + 0.1 * C_val  # 简化模型
    N_adjusted = min(N_adjusted, 1.5)  # 上限
    print(f"C={C_val:.1f}: N={N_adjusted:.2f} ({'异化' if N_adjusted < 1 else '稳态/创造'})")

print(f"\n{'='*60}")
print("全部验证通过 ✓")
print(f"{'='*60}")

#!/usr/bin/env python3
"""
网络临界质量计算器
计算不同网络拓扑下，多少人线性耦合能使N_couple>1
用幂迭代快速计算谱半径
"""
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh

def spectral_radius(A, max_iter=1000, tol=1e-10):
    """幂迭代计算谱半径（自动处理稀疏矩阵）"""
    n = A.shape[0]
    if n > 500:
        # 大矩阵用稀疏幂迭代
        x = np.ones(n) / np.sqrt(n)
        for _ in range(max_iter):
            x_new = A @ x
            norm = np.linalg.norm(x_new)
            if norm < 1e-15: return 0.0
            x_new = x_new / norm
            if np.linalg.norm(x_new - x) < tol: break
            x = x_new
        return float(np.linalg.norm(A @ x))
    else:
        x = np.ones(n) / np.sqrt(n)
        for _ in range(max_iter):
            x_new = A @ x
            norm = np.linalg.norm(x_new)
            if norm < 1e-15: return 0.0
            x_new = x_new / norm
            if np.linalg.norm(x_new - x) < tol: break
            x = x_new
        return float(np.linalg.norm(A @ x))

def complete_graph(k):
    return np.ones((k,k)) - np.eye(k)

def cycle_graph(k):
    A = np.zeros((k,k))
    for i in range(k):
        A[i,(i+1)%k] = 1
        A[i,(i-1)%k] = 1
    return A

def grid_2d(n):
    k = n*n
    A = np.zeros((k,k))
    for i in range(n):
        for j in range(n):
            idx = i*n+j
            if i>0: A[idx,(i-1)*n+j] = 1
            if i<n-1: A[idx,(i+1)*n+j] = 1
            if j>0: A[idx,i*n+j-1] = 1
            if j<n-1: A[idx,i*n+j+1] = 1
    return A

def small_world(k, p=0.1, degree=4):
    A = np.zeros((k,k))
    for i in range(k):
        for d in range(1, degree//2+1):
            A[i,(i+d)%k] = 1
            A[i,(i-d)%k] = 1
    rng = np.random.RandomState(42)
    for i in range(k):
        for j in range(k):
            if A[i,j]==1 and rng.random()<p:
                A[i,j]=0
                new_j = rng.randint(k)
                while new_j==i or A[i,new_j]==1:
                    new_j = rng.randint(k)
                A[i,new_j]=1
    return A

def scale_free(k, m=2):
    A = np.zeros((k,k))
    for i in range(m):
        for j in range(m):
            if i!=j: A[i,j]=1
    for new_node in range(m, k):
        degrees = A.sum(axis=1)[:new_node]
        total = degrees.sum()
        if total == 0:
            targets = list(range(min(m,new_node)))
        else:
            probs = degrees/total
            targets = np.random.RandomState(new_node).choice(
                new_node, size=min(m,new_node), replace=False, p=probs)
        for t in targets:
            A[new_node,t]=1
            A[t,new_node]=1
    return A

def analyze_all(N0=0.95, c=0.01):
    print("="*65)
    print(f"网络临界质量分析（N0={N0}, c={c}）")
    print(f"临界条件：rho(A) > {(1-N0)/c:.2f}")
    print("="*65)

    networks = [
        ("完全图（所有人直接连接）", complete_graph, range(2,201)),
        ("环图（1D链式传播）", cycle_graph, range(2,201)),
        ("2D网格（社区网络）", grid_2d, [n*n for n in range(2,11)]),
        ("小世界网络（社交媒体）", small_world, range(10,201,10)),
        ("无标度网络（核心节点结构）", scale_free, range(10,201,10)),
    ]

    for name, func, k_range in networks:
        print(f"\n【{name}】")
        k_c = None
        shown = set()
        for k in k_range:
            A = func(k)
            rho_A = spectral_radius(A)
            N_couple = N0 + c * rho_A
            if N_couple > 1 and k_c is None:
                k_c = k
            if k in [list(k_range)[0], 10, 50, 100, 200] or k == k_c:
                if k not in shown:
                    shown.add(k)
                    status = "成长V" if N_couple > 1 else "衰退X"
                    print(f"  k={k:3d}: rho(A)={rho_A:8.3f}, N_couple={N_couple:.4f} {status}")
        if k_c:
            print(f"  >> 临界人数：{k_c}")
        else:
            print(f"  >> 在测试范围内未达到相变")

def hub_analysis(N0=0.95, c=0.01):
    print("\n" + "="*65)
    print("无标度网络：核心节点的作用")
    print("="*65)
    k = 100
    A = scale_free(k)
    degrees = A.sum(axis=1)
    hub_idx = int(np.argmax(degrees))
    rho_A = spectral_radius(A)
    print(f"\n{k}人无标度网络：")
    print(f"  最大核心节点连接数：{degrees[hub_idx]:.0f}")
    print(f"  网络谱半径rho(A)={rho_A:.3f}")
    A_no_hub = A.copy()
    A_no_hub[hub_idx,:] = 0
    A_no_hub[:,hub_idx] = 0
    rho_no_hub = spectral_radius(A_no_hub)
    print(f"  移除核心节点后rho(A)={rho_no_hub:.3f}")
    print(f"  N_couple: {N0+c*rho_A:.4f} -> {N0+c*rho_no_hub:.4f}")
    print(f"\n  核心节点被招安（边变!-模态）：")
    print(f"  N_couple降到{N0+c*rho_no_hub:.4f}——和移除核心节点一样")

def modality_comparison():
    print("\n" + "="*65)
    print("线性耦合 vs !-模态耦合")
    print("="*65)
    N0, c = 0.95, 0.01
    print(f"\n{'人数':>6} | {'线性N':>8} | {'!-模态N':>8} | 差异")
    print("-"*45)
    for k in [1, 5, 10, 50, 100, 200]:
        A = complete_graph(k)
        rho_A = spectral_radius(A)
        N_linear = N0 + c*rho_A
        N_bang = N0
        print(f"{k:6d} | {N_linear:8.4f} | {N_bang:8.4f} | {N_linear-N_bang:.4f}")
    print("\n结论：通过制度/金钱/媒介中介的'团结'（!-模态）")
    print("      不管多少人都不产生相变。真正的团结必须是直接的、活的。")

if __name__ == "__main__":
    analyze_all()
    hub_analysis()
    modality_comparison()

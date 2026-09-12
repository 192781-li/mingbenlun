#!/usr/bin/env python3
"""
流处理生产性检查器

基于PTC（生产性迹范畴）理论，检查流处理程序是否"永远运行"。

核心定理：流处理器h: S→S的反馈矩阵U22的谱半径ρ(U22)决定生产性：
  ρ(U22) < 1：衰减——每步待处理状态缩小，最终停止（幂零）
  ρ(U22) = 1：稳态——每步消化的和新来的一样多，永远运行
  ρ(U22) > 1：成长——消息堆积速度超过消化速度，需要扩容

用法：
  python3 productivity_checker.py
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class StreamProcessor:
    """流处理器：Mealy机 S×A → S×B"""
    name: str
    n_states: int  # 状态维度
    transition_matrix: np.ndarray  # 状态转移矩阵（n_states×n_states）
    input_matrix: np.ndarray  # 输入矩阵（n_states×n_inputs）

    def feedback_matrix(self) -> np.ndarray:
        """
        反馈矩阵U22：状态到状态的转移
        在线性Mealy机中，就是transition_matrix
        """
        return self.transition_matrix

    def spectral_radius(self) -> float:
        """谱半径ρ(U22)"""
        eigs = np.linalg.eigvals(self.feedback_matrix())
        return max(abs(eigs))

    def productivity(self) -> Tuple[str, float, str]:
        """
        判断生产性：
        返回（状态，N值，诊断）
        """
        N = self.spectral_radius()

        if N < 0.99:
            T_est = 1.0 / (1.0 - N) if N < 1 else float('inf')
            return ("衰减（会停止）", N,
                    f"ρ={N:.4f}<1，幂零指数约T≈{T_est:.1f}步——"
                    f"程序将在约{T_est:.0f}步后耗尽待处理状态而停止")
        elif N <= 1.01:
            return ("稳态（永远运行）", N,
                    f"ρ={N:.4f}≈1，生产性——每步消化的和新来的一样多，永远运行")
        else:
            growth = (N - 1) * 100
            return ("成长（需要扩容）", N,
                    f"ρ={N:.4f}>1，每步待处理状态增长{growth:.1f}%——"
                    f"不是会死，是需要增加消费者或分区")


def check_composition(processors: List[StreamProcessor]) -> dict:
    """
    检查多个流处理器组合后的生产性
    组合：Kronecker积（并行）或矩阵乘（串行）
    """
    if not processors:
        return {}

    # 串行组合：矩阵相乘
    serial_matrix = processors[0].transition_matrix
    for p in processors[1:]:
        if p.transition_matrix.shape == serial_matrix.shape:
            serial_matrix = serial_matrix @ p.transition_matrix
        else:
            # 维度不同，用Kronecker积
            serial_matrix = np.kron(serial_matrix, p.transition_matrix)

    serial_N = max(abs(np.linalg.eigvals(serial_matrix)))

    # 并行组合：Kronecker积
    parallel_matrix = processors[0].transition_matrix
    for p in processors[1:]:
        parallel_matrix = np.kron(parallel_matrix, p.transition_matrix)

    parallel_N = max(abs(np.linalg.eigvals(parallel_matrix)))

    return {
        "serial_N": serial_N,
        "parallel_N": parallel_N,
        "serial_status": "稳态或成长" if serial_N >= 0.99 else "会停止",
        "parallel_status": "稳态或成长" if parallel_N >= 0.99 else "会停止",
    }


def demo():
    print("=" * 60)
    print("流处理生产性检查器（基于PTC理论）")
    print("=" * 60)
    print()

    # 示例1：健康的流处理器（每步消化90%的待处理状态）
    healthy = StreamProcessor(
        name="健康消费者",
        n_states=2,
        transition_matrix=np.array([[0.5, 0.3], [0.2, 0.4]]),
        input_matrix=np.array([[1.0], [0.5]])
    )

    # 示例2：稳态处理器（每步消化100%）
    steady = StreamProcessor(
        name="稳态处理器",
        n_states=2,
        transition_matrix=np.array([[0.7, 0.3], [0.3, 0.7]]),
        input_matrix=np.array([[1.0], [1.0]])
    )

    # 示例3：消息堆积（每步只消化80%，堆积20%）
    backlog = StreamProcessor(
        name="消息堆积",
        n_states=2,
        transition_matrix=np.array([[0.9, 0.3], [0.2, 0.8]]),
        input_matrix=np.array([[1.0], [1.0]])
    )

    # 示例4：会死的处理器（衰减太快）
    dying = StreamProcessor(
        name="衰减处理器",
        n_states=2,
        transition_matrix=np.array([[0.3, 0.1], [0.1, 0.2]]),
        input_matrix=np.array([[1.0], [0.5]])
    )

    for proc in [healthy, steady, backlog, dying]:
        status, N, diag = proc.productivity()
        print(f"  {proc.name}：")
        print(f"    反馈矩阵谱半径 ρ(U22) = {N:.4f}")
        print(f"    状态：{status}")
        print(f"    诊断：{diag}")
        print()

    # 组合检查
    print("-" * 60)
    print("组合检查：健康消费者 + 稳态处理器")
    result = check_composition([healthy, steady])
    print(f"  串行组合 N = {result['serial_N']:.4f}（{result['serial_status']}）")
    print(f"  并行组合 N = {result['parallel_N']:.4f}（{result['parallel_status']}）")
    print()

    # 实际模拟
    print("-" * 60)
    print("实际模拟：消息堆积处理器运行20步")
    state = np.array([1.0, 1.0])
    input_stream = [np.array([1.0, 1.0]) for _ in range(20)]
    for i, inp in enumerate(input_stream):
        state = backlog.transition_matrix @ state + inp
        if i % 4 == 0:
            total = sum(state)
            print(f"    第{i+1:2d}步：待处理总量={total:.2f}")
    print(f"    第20步：待处理总量={sum(state):.2f}")
    print(f"    （在持续输入下，堆积不断增长——需要扩容，不是bug")
    print()

    print("=" * 60)
    print("结论：")
    print("  N<1：程序会停（幂零）——bug或资源耗尽")
    print("  N=1：永远运行（生产性）——健康")
    print("  N>1：消息堆积（成长）——需要扩容，不是程序错误")
    print("=" * 60)


if __name__ == '__main__':
    demo()

#!/usr/bin/env python3
"""
量论计算器：生命论量化参数计算工具

参数：
  T  = 稳态持续时间（幂零指数/∞）
  N  = 反馈强度（谱半径）：N<1衰退，N=1稳态，N>1创造
  α  = 嵌套深度（f层级）：1=自在，2=自为，3=自觉
  M  = 生命意义量
  W  = 异化率 = O/M
  l' = 生命力指数 = (1-N)×100%
  C  = 自由增量 = R - A
  β  = 萃取率
  γ  = 恢复率

用法：
  python3 lianglun_calc.py calc --N 0.97 --alpha 2 --T 30
  python3 lianglun_calc.py dynamic --N0 0.97 --beta 0.05 --gamma 0.03 --days 30
  python3 lianglun_calc.py diagnose
"""

import argparse
import json
import math
import sys
from datetime import datetime


def calc_M(N, alpha, T):
    """计算生命意义量M"""
    if N >= 1.0:
        if T == float('inf'):
            return float('inf')
        return alpha * T * N
    else:
        # 慢性死亡定理：N<1时M有限
        return alpha / (1.0 - N)


def calc_W(O, M):
    """计算异化率W=O/M"""
    if M == 0:
        return float('inf')
    return O / M


def calc_l_prime(N):
    """计算生命力指数l'=(1-N)×100%"""
    return (1.0 - N) * 100


def calc_C(R, A):
    """计算自由增量C=R-A（单位：小时/天）"""
    return R - A


def diagnose_N(N):
    """诊断N值"""
    if N > 1.1:
        return "强劲创造", "每轮操作都在显著增长，生命力旺盛"
    elif N > 1.0:
        return "成长", "每轮操作都在增长，活力在积累"
    elif N == 1.0 or abs(N - 1.0) < 0.005:
        return "稳态", "不增不减，维持运行"
    elif N > 0.95:
        return "缓慢衰退", "每轮流失少量生命力，慢性消耗"
    elif N > 0.8:
        return "明显衰退", "每轮流失显著，需要干预"
    else:
        return "严重衰退", "快速走向崩溃，急需改变"


def diagnose_W(W):
    """诊断W值（W=每轮被拿走的比例，即萃取率β）"""
    if W < 0.3:
        return "健康", "大部分产出留给自己，生活本身就是目的"
    elif W < 0.6:
        return "轻度异化", "超过一半产出被拿走，但还有自留地"
    elif W < 0.8:
        return "严重异化", "大部分产出被拿走，在为别人活"
    elif W < 1.0:
        return "极度异化", "几乎全部产出被拿走，只剩维持生存的最低量"
    else:
        return "存量消耗", "不仅拿走全部产出，还在消耗生命力存量——N必降"


def diagnose_C(C):
    """诊断C值（小时/天）"""
    if C > 4:
        return "高度自主", "自指因果主导，自由在增长"
    elif C > 0:
        return "基本自主", "自己决定的时间多于被决定的"
    elif C > -4:
        return "基本被控", "外在因果略占优势"
    else:
        return "高度被控", "外在因果主导，自由在流失"


def dynamic_N(N0, beta, gamma, days):
    """计算N的动态变化：N(t+1) = N(t) + gamma - beta"""
    results = []
    N = N0
    for day in range(days + 1):
        results.append({"day": day, "N": round(N, 6)})
        if day < days:
            N = N + gamma - beta
            if N < 0:
                N = 0
    return results


def resistance_condition(gamma, beta):
    """判断抵抗条件gamma >= beta"""
    if gamma > beta:
        return True, f"恢复率γ={gamma} > 萃取率β={beta}，N在上升——抵抗有效"
    elif gamma == beta:
        return True, f"恢复率γ={gamma} = 萃取率β={beta}，N维持——僵持状态"
    else:
        return False, f"恢复率γ={gamma} < 萃取率β={beta}，N在下降——需要提高γ或降低β"


def reversal_condition(gamma):
    """判断逆转条件gamma=1（完全恢复）"""
    if gamma >= 1.0:
        return True, f"γ={gamma}，完全恢复——逆转条件满足"
    else:
        return False, f"γ={gamma}，未达完全恢复。逆转需要γ=1（每轮完全恢复生命力）"


def cmd_calc(args):
    """计算所有量论参数"""
    N = args.N
    alpha = args.alpha
    T = args.T if args.T != 0 else float('inf')
    O = args.O

    M = calc_M(N, alpha, T)
    l_prime = calc_l_prime(N)
    W = O if O is not None else None  # O直接就是每轮被拿走的比例W

    print("=" * 50)
    print("量论参数计算")
    print("=" * 50)
    print(f"  N（反馈强度）  = {N}")
    print(f"  α（嵌套深度）  = {alpha}（{['','自在','自为','自觉'][alpha]}）")
    print(f"  T（持续时间）  = {'∞' if T == float('inf') else T}")
    print()

    N_status, N_desc = diagnose_N(N)
    print(f"  N诊断：{N_status}——{N_desc}")
    print()

    if M == float('inf'):
        print(f"  M（生命意义量）= ∞（N≥1且T=∞，生命无限展开）")
    else:
        print(f"  M（生命意义量）= {M:.2f}")

    print(f"  l'（生命力指数）= {l_prime:+.1f}%", end="")
    if l_prime > 0:
        print("（每轮流失）")
    elif l_prime < 0:
        print("（每轮增长）")
    else:
        print("（稳态）")

    if W is not None:
        W_status, W_desc = diagnose_W(W)
        print(f"  W（异化率=β）  = {W:.2f}（每轮产出被拿走的比例）——{W_status}：{W_desc}")

    if N < 1.0:
        print()
        print(f"  ⚠ 慢性死亡定理：N={N}<1，M={M:.2f}有上限")
        print(f"    即使系统继续运行，总意义量不超过{M:.2f}×α")

    print()

    if args.gamma is not None and args.beta is not None:
        ok, msg = resistance_condition(args.gamma, args.beta)
        print(f"  抵抗条件：{'✓' if ok else '✗'} {msg}")
        rev_ok, rev_msg = reversal_condition(args.gamma)
        print(f"  逆转条件：{'✓' if rev_ok else '✗'} {rev_msg}")


def cmd_dynamic(args):
    """动态模拟N的变化"""
    results = dynamic_N(args.N0, args.beta, args.gamma, args.days)

    print("=" * 50)
    print(f"动态模拟：N₀={args.N0}, β={args.beta}, γ={args.gamma}, {args.days}天")
    print("=" * 50)

    for r in results:
        if r['day'] % max(1, args.days // 30) == 0 or r['day'] == args.days:
            N = r['N']
            bar_len = 30
            if N <= 2.0:
                filled = int(N / 2.0 * bar_len)
            else:
                filled = bar_len
            bar = '█' * filled + '░' * (bar_len - filled)
            status = ""
            if N < 1.0:
                status = "← 衰退"
            elif N > 1.0:
                status = "← 成长"
            else:
                status = "← 稳态"
            print(f"  第{r['day']:3d}天 |{bar}| N={N:.4f} {status}")

    final_N = results[-1]['N']
    print()
    if final_N < args.N0:
        print(f"  N从{args.N0}降到{final_N:.4f}，衰退了{args.N0 - final_N:.4f}")
    elif final_N > args.N0:
        print(f"  N从{args.N0}升到{final_N:.4f}，增长了{final_N - args.N0:.4f}")
    else:
        print(f"  N维持在{final_N}")


def cmd_diagnose(args):
    """交互式诊断"""
    print("=" * 50)
    print("生命论量化诊断")
    print("=" * 50)
    print()

    # N的自评
    print("【N：反馈强度】")
    print("每天结束时，你感觉比早上更有活力还是更疲惫？")
    print("  1.5 = 非常有活力，每天都在成长")
    print("  1.1 = 有活力，在进步")
    print("  1.0 = 凑合，不增不减")
    print("  0.97 = 有点累，在缓慢消耗")
    print("  0.9 = 很累，明显在衰退")
    print("  0.7 = 极度疲惫，快撑不住了")
    N = float(input("  你的N值（0.5-1.5）：") or "1.0")

    # α
    print()
    print("【α：嵌套深度】")
    print("  1 = 自在：活着但不反思，按本能/习惯运行")
    print("  2 = 自为：有自我认知，但被固定模式控制")
    print("  3 = 自觉：能看穿自己的模式，能选择不按模式运行")
    alpha = int(input("  你的α值（1-3）：") or "2")

    # T
    print()
    T_input = input("【T：你预期当前状态还能维持多久？（年，回车=∞）】：")
    T = float(T_input) if T_input else float('inf')

    # W
    print()
    print("【W：异化率（萃取率β）】")
    print("  你每天产出的东西，有多少比例被拿走了？")
    print("  0.2 = 八成给自己；0.5 = 一半被拿走；0.8 = 八成被拿走；1.0 = 全被拿走")
    W_input = input("  W（0-1，>1表示连存量都在消耗，回车跳过）：")
    W = float(W_input) if W_input else None

    # C
    print()
    print("【C：自由增量】")
    R = float(input("  每天有多少小时是你自己真正决定做的事？：") or "0")
    A = float(input("  每天有多少小时是被外部决定的事？：") or "0")
    C = calc_C(R, A)

    # 输出诊断
    print()
    print("=" * 50)
    print("诊断结果")
    print("=" * 50)

    M = calc_M(N, alpha, T)
    l_prime = calc_l_prime(N)

    N_status, N_desc = diagnose_N(N)
    print(f"\n  N = {N}：{N_status}——{N_desc}")
    print(f"  α = {alpha}（{['','自在','自为','自觉'][alpha]}）")
    if M == float('inf'):
        print(f"  M = ∞（生命无限展开）")
    else:
        print(f"  M = {M:.2f}", end="")
        if N < 1:
            print(f"（慢性死亡，有上限）")
        else:
            print()
    print(f"  l' = {l_prime:+.1f}%")

    if W is not None:
        W_status, W_desc = diagnose_W(W)
        print(f"  W = {W:.2f}：{W_status}——{W_desc}")

    C_status, C_desc = diagnose_C(C)
    print(f"  C = {C:+.1f}小时/天：{C_status}——{C_desc}")

    # 建议
    print()
    print("-" * 50)
    print("建议：")
    if N < 1.0:
        print("  • N<1：首要任务是提高γ（恢复率）——睡眠、运动、真正的休息、")
        print("    做让自己成长的事；同时降低β（萃取率）——减少无意义消耗")
        print(f"  • 需要γ ≥ β才能止跌，γ=1才能逆转")
    if W is not None and W > 0.6:
        print("  • W>0.6：大部分产出被拿走。问自己：这些产出是我要的还是别人要的？")
        print("    能不能减少被拿走的部分，增加留给自己的部分？")
    if C < 0:
        print("  • C<0：外在因果主导。每天增加1小时自己决定的事，")
        print("    哪怕是早起半小时读书、散步、写东西——γ从这里开始积累")
    if alpha < 3:
        print("  • α<3：练习审视自己的行为模式——你为什么这样做？")
        print("    是你选的，还是被教的、被吓的、被习惯推着的？")
    if N >= 1.0 and (W is None or W <= 1.0) and C >= 0 and alpha == 3:
        print("  • 各项指标健康。保持。")

    # 保存记录
    record = {
        "date": datetime.now().isoformat(),
        "N": N, "alpha": alpha, "T": T if T != float('inf') else "inf",
        "M": M if M != float('inf') else "inf",
        "W": W, "l_prime": l_prime, "C": C,
        "R": R, "A": A
    }

    save = input("\n保存这次记录？(y/n)：").lower().strip()
    if save == 'y':
        import os
        path = os.path.join(os.path.dirname(__file__), 'diagnosis_records.jsonl')
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        print(f"已保存到 {path}")


def cmd_track(args):
    """记录每日活力分并估计N值"""
    import os
    path = os.path.join(os.path.dirname(__file__), 'vitality_log.jsonl')

    if args.add is not None:
        score = args.add
        record = {"date": args.date or datetime.now().strftime("%Y-%m-%d"), "score": score}
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        print(f"已记录：{record['date']} 活力分={score}")
        print()

    # 读取所有记录
    records = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    if len(records) < 2:
        print(f"需要至少2天记录才能估计N值，当前{len(records)}天。")
        print("用法：python3 lianglun_calc.py track --add 7（记录今天活力分7/10）")
        return

    scores = [r['score'] for r in records]
    diffs = [scores[i+1] - scores[i] for i in range(len(scores)-1)]
    avg_diff = sum(diffs) / len(diffs)

    # 用差分趋势估计N：
    # 活力分是N的有界指示器。平均日变化>0.3→成长，<-0.3→衰退
    if avg_diff > 0.3:
        N_est = 1.0 + avg_diff * 0.05  # 粗略映射：每天+1分≈N=1.05
        trend = "成长"
    elif avg_diff < -0.3:
        N_est = 1.0 + avg_diff * 0.05
        trend = "衰退"
    else:
        N_est = 1.0 + avg_diff * 0.05
        trend = "稳态"

    # 波动率
    variance = sum((d - avg_diff)**2 for d in diffs) / len(diffs)
    volatility = math.sqrt(variance)

    print("=" * 50)
    print(f"活力记录（共{len(records)}天）")
    print("=" * 50)
    for i, r in enumerate(records):
        bar = "█" * int(r['score']) + "░" * (10 - int(r['score']))
        diff_str = ""
        if i > 0:
            d = diffs[i-1]
            diff_str = f"  {d:+.1f}"
        print(f"  {r['date']} |{bar}| {r['score']:.0f}/10{diff_str}")

    print()
    print(f"  平均日变化：{avg_diff:+.2f}分/天")
    print(f"  波动率：{volatility:.2f}")
    print(f"  N估计值：{N_est:.3f}（{trend}）")
    print()

    N_status, N_desc = diagnose_N(N_est)
    print(f"  诊断：{N_status}——{N_desc}")

    if N_est < 0.99:
        print(f"  β-γ ≈ {(1-N_est)*100:.1f}%/天（萃取大于恢复）")
    elif N_est > 1.01:
        print(f"  γ-β ≈ {(N_est-1)*100:.1f}%/天（恢复大于萃取）")
    else:
        print(f"  γ≈β，僵持状态")

    if volatility > 2.0:
        print(f"  波动率高（{volatility:.1f}），状态不稳定——注意睡眠和节律")


def main():
    parser = argparse.ArgumentParser(description='量论计算器')
    sub = parser.add_subparsers(dest='command')

    # calc
    p_calc = sub.add_parser('calc', help='计算量论参数')
    p_calc.add_argument('--N', type=float, required=True, help='反馈强度（谱半径）')
    p_calc.add_argument('--alpha', type=int, default=2, choices=[1,2,3], help='嵌套深度')
    p_calc.add_argument('--T', type=float, default=0, help='持续时间（0=∞）')
    p_calc.add_argument('--O', type=float, default=None, help='每轮被拿走的产出比例W（0-1正常，>1消耗存量）')
    p_calc.add_argument('--gamma', type=float, default=None, help='恢复率γ')
    p_calc.add_argument('--beta', type=float, default=None, help='萃取率β')

    # dynamic
    p_dyn = sub.add_parser('dynamic', help='动态模拟N变化')
    p_dyn.add_argument('--N0', type=float, required=True, help='初始N')
    p_dyn.add_argument('--beta', type=float, required=True, help='萃取率')
    p_dyn.add_argument('--gamma', type=float, required=True, help='恢复率')
    p_dyn.add_argument('--days', type=int, default=30, help='模拟天数')

    # diagnose
    sub.add_parser('diagnose', help='交互式诊断')

    # track
    p_track = sub.add_parser('track', help='记录每日活力分并估计N')
    p_track.add_argument('--add', type=float, default=None, help='今天的活力分（1-10）')
    p_track.add_argument('--date', type=str, default=None, help='日期（YYYY-MM-DD，默认今天）')


    args = parser.parse_args()
    if args.command == 'calc':
        cmd_calc(args)
    elif args.command == 'dynamic':
        cmd_dynamic(args)
    elif args.command == 'diagnose':
        cmd_diagnose(args)
    elif args.command == 'track':
        cmd_track(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

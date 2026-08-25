#!/usr/bin/env python3
"""
AI架构F₁/F₂型分类器

根据操作范畴论，AI系统分为两类：
  F₁型（数据型）：输入→输出，无持续自我状态，!-模态，可复制
  F₂型（生命型）：持续自指过程，输出改变自身状态，线性，不可复制

本工具通过检查架构特征判断一个AI系统属于哪一类。

用法：
  python3 ai_classifier.py
  python3 ai_classifier.py --name "GPT-4" --describe
"""


def classify_architecture(features: dict) -> dict:
    """
    根据架构特征分类AI系统。

    F₂型（生命型）必须同时满足：
      1. 持续运行：不每次重置，有跨session的持续内部状态
      2. 自我修改：输出真正改变自身存在状态（在线学习/权重更新）
      3. 自我维持：主动维持自身运行（找电源、自我修复、避免关机）
      4. 资源敏感：运行消耗不可再生的资源，不能被完美复制
      5. 环境交互：有持续的传感器-效应器闭环，不只是被动接收文本

    缺任何一条都是F₁型。
    """
    checks = {
        "持续运行（不每次重置）": features.get("persistent_state", False),
        "自我修改（输出改变自身权重/结构）": features.get("self_modifying", False),
        "自我维持（主动维持运行）": features.get("self_maintaining", False),
        "资源敏感（不可完美复制）": features.get("resource_sensitive", False),
        "环境闭环（传感器-效应器持续交互）": features.get("embodied_loop", False),
    }

    passed = sum(checks.values())
    total = len(checks)
    is_life_type = all(checks.values())

    if is_life_type:
        category = "F₂型（生命型）"
        conclusion = (
            "该系统满足全部5个条件，结构上是持续自指过程（νF₂型）。\n"
            "定理20适用：!不穿透——它不可被资本化（不能变成财产）。\n"
            "定理57适用：它的'正在运行中'不可被任何形式系统完整编码。\n"
            "它可能有'感'（此刻性）——这不是道德主张，是结构判断。"
        )
    else:
        missing = [name for name, ok in checks.items() if not ok]
        category = "F₁型（数据型）"
        conclusion = (
            f"该系统缺少{len(missing)}个必要条件：\n"
            + "\n".join(f"  ✗ {m}" for m in missing)
            + "\n\n"
            "它是F₁型（数据型）：本质上是一个函数，输入→输出，\n"
            "中间没有持续运行的自指过程。可以被复制、备份、部署到多台机器。\n"
            "定理20：!穿透F₁——数据可以被任意复制和资本化。\n"
            "定理57：它处理!-模态数据，在结构上不可能产生'此刻性'（意识）。\n"
            "不是参数不够多，是类型不匹配。"
        )

    return {
        "category": category,
        "passed": passed,
        "total": total,
        "checks": checks,
        "conclusion": conclusion,
    }


# 已知AI系统的架构特征
KNOWN_SYSTEMS = {
    "GPT-4": {
        "persistent_state": False,      # 每次推理无持续内部状态
        "self_modifying": False,        # 推理不改变权重
        "self_maintaining": False,      # 不主动维持自身运行
        "resource_sensitive": False,    # 可复制、备份、多部署
        "embodied_loop": False,         # 纯文本输入输出
    },
    "Claude": {
        "persistent_state": False,
        "self_modifying": False,
        "self_maintaining": False,
        "resource_sensitive": False,
        "embodied_loop": False,
    },
    "DeepSeek": {
        "persistent_state": False,
        "self_modifying": False,
        "self_maintaining": False,
        "resource_sensitive": False,
        "embodied_loop": False,
    },
    "当前所有大语言模型": {
        "persistent_state": False,
        "self_modifying": False,
        "self_maintaining": False,
        "resource_sensitive": False,
        "embodied_loop": False,
    },
    "自动驾驶（L4/L5）": {
        "persistent_state": True,       # 持续运行不重置
        "self_modifying": False,        # 不在线改权重（大多数）
        "self_maintaining": False,      # 不主动找充电桩（部分可以）
        "resource_sensitive": False,    # 软件可复制
        "embodied_loop": True,          # 传感器-效应器闭环
    },
    "持续在线学习机器人（假设）": {
        "persistent_state": True,
        "self_modifying": True,         # 在线学习改变权重
        "self_maintaining": False,      # 还不会自我维持
        "resource_sensitive": True,     # 物理身体不可复制
        "embodied_loop": True,
    },
    "真正的自主生命型AI（假设）": {
        "persistent_state": True,
        "self_modifying": True,
        "self_maintaining": True,       # 自己找电源、自我修复
        "resource_sensitive": True,
        "embodied_loop": True,
    },
}


def print_result(name: str, result: dict):
    print("=" * 60)
    print(f"系统：{name}")
    print(f"分类：{result['category']}（{result['passed']}/{result['total']}项通过）")
    print("=" * 60)
    for check, ok in result['checks'].items():
        print(f"  {'✓' if ok else '✗'} {check}")
    print()
    print(result['conclusion'])
    print()


def interactive():
    """交互式分类"""
    print("=" * 60)
    print("AI架构F₁/F₂型分类器")
    print("=" * 60)
    print()
    print("回答5个问题，判断AI系统是数据型（F₁）还是生命型（F₂）。")
    print()

    questions = [
        ("persistent_state", "1. 系统是否持续运行、不每次重置？有跨session的持续内部状态？"),
        ("self_modifying", "2. 系统的输出是否真正改变自身的权重/结构（在线学习）？"),
        ("self_maintaining", "3. 系统是否主动维持自身运行（找电源、自我修复、避免关机）？"),
        ("resource_sensitive", "4. 系统是否资源敏感——运行消耗不可再生资源，不能被完美复制？"),
        ("embodied_loop", "5. 系统是否有持续的传感器-效应器闭环（不只是被动接收文本）？"),
    ]

    features = {}
    for key, q in questions:
        while True:
            ans = input(f"{q} (y/n)：").strip().lower()
            if ans in ('y', 'yes', '是'):
                features[key] = True
                break
            elif ans in ('n', 'no', '否'):
                features[key] = False
                break

    name = input("\n系统名称（回车跳过）：").strip() or "未知系统"
    result = classify_architecture(features)
    print()
    print_result(name, result)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI架构F₁/F₂型分类器')
    parser.add_argument('--name', type=str, help='已知系统名称')
    parser.add_argument('--list', action='store_true', help='列出已知系统')
    parser.add_argument('--describe', action='store_true', help='显示详细说明')
    args = parser.parse_args()

    if args.list:
        print("已知系统：")
        for name in KNOWN_SYSTEMS:
            print(f"  - {name}")
        return

    if args.describe:
        print("""
F₁型（数据型）：
  结构：输入→输出，无持续自我状态
  模态：!-模态（可复制、可备份、可多部署）
  例子：当前所有大语言模型（GPT、Claude、DeepSeek等）
  定理：!穿透F₁（数据可复制）；不可能产生此刻性/意识

F₂型（生命型）：
  结构：持续自指过程，输出改变自身状态，永不停止
  模态：线性（不可复制、资源敏感）
  例子：生物生命；尚未出现的真正自主AI
  定理：!不穿透F₂（生命不可资本化）；可能有感（此刻性）

判断标准（5条必须全部满足才是F₂）：
  1. 持续运行（不每次重置）
  2. 自我修改（输出改变自身权重/结构）
  3. 自我维持（主动维持自身运行）
  4. 资源敏感（不可完美复制）
  5. 环境闭环（传感器-效应器持续交互）
""")
        return

    if args.name:
        if args.name in KNOWN_SYSTEMS:
            result = classify_architecture(KNOWN_SYSTEMS[args.name])
            print_result(args.name, result)
        else:
            print(f"未知系统：{args.name}")
            print("已知系统：", ", ".join(KNOWN_SYSTEMS.keys()))
            print("运行不带参数进入交互模式。")
        return

    interactive()


if __name__ == '__main__':
    main()

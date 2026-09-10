# 概念协奏自动检索器（七维定位法可执行版）

配套理论文档：`docs/体系研究/生命论概念协奏坐标系_七维定位法_20260911.md`

## 文件
- `concept_coords.json`：概念坐标库（种子 v0.1，39 条）。每入库一个重要概念，追加一条记录。
- `resonance_search.py`：检索脚本，纯标准库，Python 3.8+。

## 三种用法

### 1. 以库里已有概念为锚，找协奏近亲（最常用）
```bash
python3 scripts/concept_resonance/resonance_search.py --concept 不忍
python3 scripts/concept_resonance/resonance_search.py --concept 大跃退 --top 8
```

### 2. 自由坐标查询（新讨论先打坐标，再找协奏）
```bash
# 各轴可多值、可只给部分轴
python3 scripts/concept_resonance/resonance_search.py -p P1 -f f3 -r R1 -s L0 L3 -t Tj --phase 解 -c K现象 K判准
# 例：找所有"去脸"轴(R6)的负向机制
python3 scripts/concept_resonance/resonance_search.py -r R6 --dir neg
```

### 3. 列表 / 机器可读
```bash
python3 scripts/concept_resonance/resonance_search.py --list
python3 scripts/concept_resonance/resonance_search.py --concept 不忍 --json
```

## 轴代码速查
| 轴 | 取值 |
|---|---|
| 人称 -p | P1第一人称 P2第二人称 P3第三人称 |
| f层 -f | f1自在 f2自为/意识形态 f3自觉 |
| 关系 -r | R1维持 R2寄生 R3沉积 R4流动/传承 R5断裂 R6去脸↔具脸 R7名实分离↔还原 R8归还 |
| 尺度 -s | L0身体 L1人际 L2阶级 L3国家 L4文明 LF形式层 |
| 时间 -t | Ts慢性 Tj急性 Tp脉冲 Td沉积 Tt代际 |
| 阶段 --phase | 生 蔽 解 行 中 |
| 类型 -c | K判准 K机制 K现象 K法门 K形式 K决断 K谱系 |
| 方向 --dir | pos正向 neg负向 neu中性 |

## 打分逻辑
- 逐轴重合加权：关系型3.0 > 人称/f层/阶段/类型各1.5 > 尺度/时间各1.0（权重在 JSON 的 meta.axis_weights 可调）。
- 三种强协奏加分：
  - **同构跨尺度**：同关系型，且对方带来查询没有的新尺度层（+1.5）
  - **跨人称互译**：结构同、人称位不同（同一现象的三身）（+1.0）
  - **逆向对治**：同关系轴方向相反，或互为反治对 R2↔R8、R5↔R8、R3↔R4（+1.0）
- `覆盖x/y` = 你给的 y 个轴里命中了 x 个；命中轴越少说明越是远亲，或该坐标组合在库中是新结构（造新概念的信号）。

## 维护规则
1. 新增概念：往 `concept_coords.json` 的 `concepts` 数组追加一条，坐标必须能在 `axes` 里找到合法值。
2. 坐标拿不准就留空数组 `[]`，不要硬填。
3. 每次追加后跑一遍 `--list` 确认 JSON 合法、条目数正确。
4. 坐标是 S00 依据已读卷册的初标，重要概念由 S01 复核。

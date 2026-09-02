# 项目工作状态 STATUS

> 最后更新：2026-09-02
> 所有AI开始干活前先看这个文件，干完活更新这个文件。
> **项目总纲（必读）**：docs/协作机制/项目总纲_生命论形式化_20260902.md

---

## 当前谁在干什么

| 分站 | 分支 | 状态 | 当前任务 |
|---|---|---|---|
| S01哲学 | s01-philosophy | 活跃 | 哲学研判、贯穿证明策略、PPar深入研究、项目总纲整理 |
| S04 Coq | s04-coq | 活跃（定时任务每15分钟） | substitution_general证明（5/8完成，PIn/POut/PPar待证） |
| S00大总站 | main | 待激活 | PR合并、全局协调 |
| S02高考文科 | s02-gaokao-arts | 独立 | 高考文科备考（不处理项目任务） |
| S03术数 | s03-divination | 独立 | 术数复盘 |
| S05信息 | s05-info | 待激活 | 库巡检、地图维护、报告萃取 |

---

## 技术路线

- **A线（当前）**：自定义insert_at/set_none/操作权流动方法，先走完L2
- **B线（待启动）**：标准de Bruijn + Autosubst + 操作权语义解释，A线完成后启动
- **不并行**：集中精力先把A线走完

详细路线见项目总纲。

---

## Coq形式化进度（L1-L5）

| 层 | 状态 | Admitted |
|---|---|---|
| L1 操作结构 | ✅ 完成 | 0 |
| L2 类型系统 | 🔧 进行中 | 2（substitution_general内部5个admit + congruence） |
| L3 存在论状态 | ✅ 完成 | 0 |
| L4 自指循环 | 📋 哲学基础完成，Coq未启动 | - |
| L5 资本化高级形态 | 📋 未启动 | - |

### substitution_general 8case进度

PZero✅ PTau✅ PVar✅ PRes✅ PRep✅ PIn🔑 POut🔑 PPar🔬

---

## 项目结构

```
mingbenlun/
├── 生命论_模块化/     # 正文（12卷，00-12）
├── docs/
│   ├── 协作机制/       # 项目总纲、分站运行指令、智慧河流、自运行机制
│   ├── notes/         # 研究笔记（哲学研究、证明策略、反身思考）
│   ├── assets/html/   # 可视化文件
│   ├── flashpoints/   # 闪光点原材料
│   └── ...
├── coq/               # Coq形式化（L1-L5，theories/ALL/Layer1-3.v）
├── scripts/           # 构建/备份/同步/河流汇合器脚本
├── archive/           # 归档（旧版、备份、个人材料）
└── NEW_AGENT_ONBOARDING.md # 新对话启动包
```

---

## 待办事项

### 进行中
- substitution_general剩余3case（PIn/POut/PPar）
- congruence_preserves_typing证明
- PPar case深入研究（需要5个辅助引理）
- 阶级形成三条线联动理论的全本渗透
- 鞍钢宪法相关内容的全本渗透

### 待深入（A线完成后）
- B线标准方法验证
- L4 νF₂余归纳形式化
- 形式化与《资本论》的连接（剥削/异化/积累的形式化）
- F1→F2→F3具体机制
- 真理标准问题（M值作为真理检验标准）

---

## 核心文件速查

| 用途 | 文件 |
|---|---|
| **项目总纲** | docs/协作机制/项目总纲_生命论形式化_20260902.md |
| 新AI入门 | NEW_AGENT_ONBOARDING.md |
| S01运行指令 | docs/协作机制/分站/S01_运行指令.md |
| S04运行指令 | docs/协作机制/分站/S04_运行指令.md |
| 智慧河流状态 | docs/协作机制/智慧河流/河流状态.md |
| 智慧结晶库 | docs/协作机制/智慧河流/智慧结晶库.md |
| S04启动必读 | docs/协作机制/智慧河流/S04启动必读_一页纸摘要.md |
| 自运行机制 | docs/协作机制/明旭分站自运行机制_彻底不用主人操心.md |
| 教训库 | docs/协作机制/教训库.md |
| 方法论 | docs/collaboration/METHODOLOGY.md |

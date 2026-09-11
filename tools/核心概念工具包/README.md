# 核心概念工具包

> 来源：mingbenlun-modular 九卷版（2026-08-14）
> 迁移：S05 信息分站 · 2026-09-10
> 定位：生命论核心概念的 Python 快速验证层

---

## 这是什么

生命论核心概念的**可运行 Python 实现**——把哲学概念变成能跑的代码，用机器验证概念的自洽性。

不是生产代码，是**思想实验工具**：写一个概念，跑一下，看它能不能work。

---

## 目录结构

```
核心概念工具包/
├── core/                    14个核心概念模块
│   ├── operation.py         操作 S=f(S) 自指闭环
│   ├── self_reference.py    自指（死自指/活自指/践演坐实）
│   ├── metrics.py           度量学（量论公式 M=α·T·N）
│   ├── transcend.py         超越（如何超越前人）
│   ├── yin_yang.py          阴阳
│   ├── alienation.py        异化（资本病毒）
│   ├── liberation.py        解放（操作权复归）
│   ├── modality.py          模态（能/必/可）
│   ├── recursion_tiers.py   递归层级
│   ├── three_person.py      三人称
│   ├── thinking_spiral.py   思维螺旋
│   ├── fire_stealer.py      盗火者
│   ├── run_all.py           全量测试入口
│   └── __init__.py
└── examples/                各卷级示例（11个）
    ├── operation_expectation.py    卷二·认识论
    ├── social_nesting.py           卷三·群己论
    ├── capital_virus.py            卷四·异化论（资本病毒）
    ├── liberation_path.py          卷五·解放论
    ├── yang_yin_economy.py         卷五·解放论（阴阳经济）
    ├── inertia_lock.py             卷六·实践论（惯性锁）
    ├── weisuo_tuoluo.py            卷六·实践论
    ├── medicine_frameworks.py      卷七·格物论（医学框架）
    ├── paradigm_yin_yang.py        卷七·格物论
    ├── civilization_cycle.py       卷八·人文论（文明循环）
    ├── mingxing_homogeneous.py     卷八·人文论（明性齐物）
    ├── taiyi_four_forms.py         卷九·术数扬弃（太易四态）
    └── yinyang_hexagram.py         卷九·术数扬弃（阴阳卦象）
```

---

## 快速使用

```bash
# 跑全部模块的doctest，验证代码健康
python3 core/run_all.py

# 单独运行某个模块
python3 core/operation.py
python3 core/self_reference.py
python3 core/metrics.py

# 运行卷级示例
python3 examples/capital_virus.py
python3 examples/yinyang_hexagram.py
```

---

## 模块说明

| 模块 | 对应生命论概念 | 状态 |
|---|---|---|
| operation.py | 操作 S=f(S) 自指闭环 | ✅ 3 doctest |
| self_reference.py | 自指（死/活/践演） | ✅ 6 doctest |
| metrics.py | 量论 M=α·T·N | ✅ 2 doctest |
| modality.py | 模态（能/必/可） | ✅ 2 doctest |
| thinking_spiral.py | 思维螺旋 | ✅ 1 doctest |
| yin_yang.py | 阴阳 | ⬜ 待补doctest |
| alienation.py | 异化/资本病毒 | ⬜ 待补doctest |
| liberation.py | 解放 | ⬜ 待补doctest |
| transcend.py | 超越 | ⬜ 待补doctest |
| recursion_tiers.py | 递归层级 | ⬜ 待补doctest |
| three_person.py | 三人称 | ⬜ 待补doctest |
| fire_stealer.py | 盗火者 | ⬜ 待补doctest |

---

## 与 Coq 形式化的关系

- **Coq（coq/）**：严格的定理证明，数学终裁
- **core包（这里）**：快速验证、思想实验、Python原型
- 两者互补：core包快速试错 → 确认方向 → Coq严格证明

---

## 相关文件

- 术语铁律校验器：`scripts/verify_iron_rule.py`
- 超越对照表：`docs/体系研究/超越对照表.md`
- 三条铁律：`docs/协作机制/三条铁律.md`
- 可检索知识库：`docs/reference_materials/知识库/知识库.html`

---

*S05 信息分站迁移整理 · 从 archive/modular_v1_九卷版_20260814/ 恢复*

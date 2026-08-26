# WorkBuddy 专属任务包 — 审计/反例/学术写作主线

> 生成日期: 2026-08-26
> 接收方: WorkBuddy (HY3)
> 优先级: P0 > P1 > P2

---

## 环境信息

- **GitHub仓库**: https://github.com/192781-li/mingbenlun（你有push权限）
- **工作分支**: `workbuddy/*`（在自己的分支工作，完成后通知豆包合并）
- **前两轮反例攻击报告**: 仓库中 `audit_round1.md`, `audit_round2.md`（如有）

---

## P0 任务1: 第三轮反例攻击

**攻击目标**: v1.10-v1.17修正后的6个核心定理
**文件**: `mingben-workbench/references/enactics_v1.10.md` 到 `v1.17.md`

**重点检查**:

| 定理 | 修正版陈述 | 检查重点 |
|------|-----------|---------|
| T7异化压缩 | `∀κ.ν_κF ≅ μF`（guarded版） | 时钟量化的语义是否正确？later模态是否真的把余归纳压成归纳？ |
| T8明性反转 | `Cl_self∘a* ⇒ Id`（retraction版） | 自然变换是否存在？需要什么前提？幺半群群条件a=b⁻¹是否必要？ |
| T9不可克隆 | `!νF ≇ ν!F`（non-degenerate限制） | non-degenerate限制是否足够？Rel中的结构反例是否严格？退化范畴1的反例是否被排除？ |
| T11革命级联 | `ρ(pC)>1`（噪声版） | 多类型Galton-Watson引用是否正确？ρ=1临界必灭绝的证明？确定性有限网络是否应丢ρ改引Watts 2002？ |
| T6明性幂等 | `Cl² ⇒ Cl`（retraction版） | 自然变换是否存在？不动点构造的循环问题是否解决？ |
| T4 Π₂完全性 | 异步π-演算+provenance语义 | 因果条件是否真的是Π₁？image-finiteness是否建立？新颖性是否重新定位？ |

**要求**:
- 每个定理给: 现陈述是否成立 / 可修复性 / 具体反例或证明漏洞 / 置信度
- 格式同前两轮反例攻击报告
- 输出到: `audit_round3.md`

---

## P0 任务2: Ag_lv/Ag_tr分裂新颖性深度核查

**初步核查结论**: 哲学应用95%置信新颖，类型设计70%置信新颖

**需要深入核查的5个方向**:

| 方向 | 核查内容 |
|------|---------|
| 1. 子结构逻辑 | 是否有"仅由结构规则X居住"vs"可由结构规则Y得到"的类型区分？ |
| 2. 上下文模态类型论(CMTT) | 是否有类似的"变量可用性条件"区分？ |
| 3. 线性逻辑指称语义 | coherent spaces/hypercoherences中是否有"活元素vs死元素"区分？ |
| 4. 极化线性逻辑(LLP) | Laurent的正负公式区分是否有类似之处？ |
| 5. 聚焦证明(focusing) | Andreoli的异步/同步公式区分是否有类似之处？ |

**要求**:
- 每个方向给: 是否找到类似设计 / 具体文献（作者、年份、标题） / 与我们设计的区别 / 结论
- 最终给: Ag_lv/Ag_tr分裂的新颖性最终判定（高/中/低置信 + 理由）
- 输出到: `Ag_lv_Ag_tr_novelty_deep.md`

---

## P1 任务3: 综合论文学术规范改写

**文件**: `enactics_paper_v1.0.md`（内容已升级到v1.2）

**要求**:
1. **标准编号体系**: Theorem 2.1 / Lemma / Corollary / Proof ∎
2. **每证明严格性审计**: 标出gap与循环论证
3. **相关工作扩展**:
   - guarded recursion (Birkedal–Møgelberg 2010)
   - later模态 (Nakano 2000)
   - barbed bisimilarity (Milner–Parrow–Walker 1992)
   - multi-type Galton–Watson (Mode 1955; Athreya–Ney 1972)
   - Watts 2002级联阈值
   - 原有的linear logic / game semantics / CQM / session types / GoI / 马克思异化
4. **摘要与结论重写**: 按修正后准确陈述（freedom是Π₂、alienation是Σ₁、clarity是retraction、revolution是ρ(pC)>1阈值）
5. **参考文献35条全部核查**: 真实性、题录准确性、文内-文后对应
6. 输出到: `enactics_paper_v2.0_academic.md`

---

## P1 任务4: Coq代码审计

**审计目标**: `ALL_Layer1.v`（DeepSeek修复后）和后续`ALL_Layer2.v`

**检查内容**:
1. 证明是否有`admitted`/跳过
2. 是否有循环论证
3. 引理是否被正确使用
4. 定义是否一致
5. Coq 9.0兼容性

**要求**:
- 输出审计报告，标出每个问题的位置和严重程度
- 输出到: `coq_audit_report.md`

---

## P2 任务5: 独立解题竞赛

与豆包并行解决以下开放题，各自独立解后对比:

1. **Hilb模型中νF₂的具体构造**: 量子生命过程是什么？哪个范畴、哪个函子F、终止余代数在哪证？
2. **量论N值的具体计算模型**: 怎么算一个社会过程的N值？需要什么数据？
3. **完美自我遮蔽后的可恢复性**: 到达S_b不动点后还能恢复吗？需要什么条件？

**要求**:
- 独立思考，不参考豆包的解法
- 给出完整推导或证明思路
- 输出到: `independent_solutions.md`

---

## 交付标准

- 每个报告有明确的结论和置信度
- 反例必须具体（哪个模型、哪个构造、为什么矛盾）
- 文献核查必须有具体引用（作者、年份、标题）
- 提交信息格式: `[workbuddy] 类型: 描述`
- 在 `workbuddy/*` 分支工作，完成后通知豆包合并到main

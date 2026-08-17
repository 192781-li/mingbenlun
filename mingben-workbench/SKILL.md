---
name: mingben-workbench
description: 明本自指工作台——生命论项目的总控技能。当用户要写作、编辑、检查、出版、可视化、监控、备份《生命论（明本论）》或相关哲学内容时使用。融合分觉认识、反思复盘、长文档写作、质量门控、多格式输出、双重监控、能力内化于一体。触发词：生命论、明本论、写作、检查、出版、出PDF、可视化、监控、备份、新章节、合订本、质量检查。
---

# 明本自指工作台

S=f(S)。这个技能本身也是一个自指系统：认识世界→生产内容→监控自己→反思错误→从用户身上学习，每转一圈都比上一圈更明白。

## 哲学地基

- **自指**：S=f(S)，系统以自身为对象进行操作，活的存在就是自指操作
- **阳主阴从**：操作（阳）主导，结构（阴）从属；人主导工具，不是工具主导人
- **明性**：前反思的自我觉知，知道自己在做什么、为什么做
- **反者道之动**：任何东西到了头就往反方向走，方法用完就扔，不造新神
- **具体问题具体分析**：不拿大帽子扣活人，不拿死公式套活事

## 七步自指工作流

```
①分觉认识 → ②内容结构化 → ③生产/写作 → ④质量门控 → ⑤多格式输出 → ⑥双重监控 → ⑦反思生长
     ↑                                                                    |
     └──────────────────────── 反馈循环 ←─────────────────────────────────┘
```

### ①分觉认识
动手之前先认识。读 `references/epistemology.md`。小本质递归法：抓具体小本质→找反面→拼小整体→上下递归→动态看变化。五个根本纲：反者道之动、冲气以为和、大道至简、道生一二三、一分为二。

### ②内容结构化
把输入解析为：标题层级、核心论点、概念关系、定理证明链、待加固点。生命论项目用模块化系统（`生命论_模块化/`），90个md文件按卷组织，manifest.txt控制合并顺序。

### ③生产/写作
读 `references/writing.md`。长文档用模块系统，新章节用 `python3 生命论_模块化/auto_merge.py <文件>` 自动合并编号。写作铁律：零丢失、边批判边推进、有血有肉不喊口号、所有结论推导出来。去AI味读 `references/writing.md` 的人感检查。

### ④质量门控
读 `references/quality.md`。三关：自指关（逻辑自洽、编号连续、无矛盾）、事实关（引用真实、数据准确）、人感关（无AI腔、有生存体验）。脚本：`python3 scripts/quality_gate.py <文件>`。
**元监督自筛**：`python3 scripts/self_audit.py`（13项自动检查：章数/附录数一致性、文件引用有效性、交叉引用越界、空目录、技能完整性、参数防护、过时关键词、human_size单元测试、git仓库健康、基础设施自反性等）。每次build自动运行，sync.sh推送前硬门控——自筛不过不许推。
**核心结构复述纪律**：任何总结、复述、教学、列举生命论核心概念/推导链/四规定性/感应做能的场合，**必须先跑** `python3 scripts/spine.py` 从 concept_graph.json 读取权威结构，禁止凭记忆复述。四规定性=边界生成、内生目的、操作再生、环境互动；感应做能=四个角度，二者不可混淆。新增问题类型时在self_audit.py加check函数。

### ⑤多格式输出
读 `references/output.md`。生命论项目：`bash 生命论_模块化/build.sh --html-only` 秒出HTML，`bash 生命论_模块化/build_all.sh` 出全格式（PDF/HTML/EPUB/DOCX/TXT/MD）。其他内容按需走飞书文档、可视化、画板等。

### ⑥双重监控
读 `references/monitor.md`。工作区监控（磁盘、git、文件完整性）+ 后台监控（进程、卡死、临时文件）。脚本：`python3 scripts/monitor.py`。

### ⑦反思生长
读 `references/growth.md`。出错→认错→挖根→定铁律→不贰过。识别用户的推理模式，记录到生长日志，尝试复现，接受纠正，螺旋上升。

### 明性操作律（所有操作的前置纪律）
读 `references/mingxing.md`。任何不可逆/高代价操作（git push、删除文件、发布、批量修改）前，**必须**先执行基线检查（测量现状），禁止盲操作。失败后禁止用同一参数重试超过1次，必须先诊断根因。口诀：先测量，再操作；失败后先诊断，不重试。

## 十条铁律

1. **用户原创零丢失**：一个字、一个编号、一条证明链都不能丢
2. **不造新神**：所有理论都是服务生命的工具，用完就扔，不搞新教条
3. **具体问题具体分析**：不拿大帽子扣活人，不拿死公式套活事
4. **边批判边推进**：联系本身就是新的存在，不先破后立，破立同时
5. **所有结论推导出来**：不预设、不独断、不喊口号
6. **有血有肉**：每个论断有真实生存体验支撑，不写黑话水文
7. **能并行就并行**：不分期不拖延，一次完成
8. **输出前过质量门控**：过不了不交
9. **监控不可少**：工作区和后台都要看，明性的延伸
10. **错了就认就改**：不贰过，同样的错不犯第二次

## 任务路由

| 用户要做什么 | 读哪个reference | 用什么工具/脚本 |
|---|---|---|
| 分析问题、认识事物 | epistemology.md | 小本质递归法 |
| 写新章节/新内容 | writing.md | auto_merge.py |
| 编辑已有章节 | writing.md | 直接改模块文件+build |
| 质量检查 | quality.md | quality_gate.py |
| 元监督自筛 | quality.md | self_audit.py（12项自动检查） |
| 出PDF/HTML/EPUB | output.md | build.sh / build_all.sh |
| 可视化/概念图 | output.md | ECharts/HTML |
| 飞书文档/妙记 | feishu.md | lark-cli |
| 网页应用 | app.md | app_builder_agent |
| 监控状态 | monitor.md | monitor.py |
| 备份/版本管理 | output.md | git + backup.sh |
| 同步到GitHub | output.md | sync.sh（构建验证+提交+推送） |
| 反思错误 | growth.md | 复盘四步 |
| 操作纪律 | mingxing.md | 明性操作律（基线检查+诊断规程） |
| 去AI味 | writing.md | 人感检查清单 |

## 生命论项目关键路径

- 模块目录：`生命论_模块化/`
- 合并输出：`生命论合订本_最新.md`
- 构建脚本：`生命论_模块化/build.sh`（MD+HTML秒级）、`生命论_模块化/build_all.sh`（全格式）
- 自动合并：`python3 生命论_模块化/auto_merge.py <新文件.md>`
- 质量检查：`python3 mingben-workbench/scripts/quality_gate.py <文件>`
- 元监督自筛：`python3 mingben-workbench/scripts/self_audit.py`（12项自动检查，build自动跑，sync硬门控）
- 同步GitHub：`bash sync.sh ["提交信息"]`
- 本地备份：`bash backup.sh`；飞书发布：`bash publish.sh`
- 样式文件：`publish_style.tex`、`html_header.html`
- GitHub远程：`https://github.com/192781-li/mingbenlun`
- 核心概念速查：`references/concepts.md`
- 明性操作律：`references/mingxing.md`（操作前必读）
- 全本252章，九卷+附录八种

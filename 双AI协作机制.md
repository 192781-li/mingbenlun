# 双AI协作工作机制（豆包 + WorkBuddy）

> 目的：两个AI端共同推进践演论（Enactics）项目，既不冲突，又能互补，甚至可以竞争。
> 适用：GitHub仓库 https://github.com/192781-li/mingbenlun
> 最终拍板权：东哥（用户）

---

## 一、分支策略

### 主分支 `main`
- 只有经过验证的内容才能在main上
- 两人都可以直接推main，但必须遵守文件分工和提交规范
- 如果不确定是否会冲突，先在自己的分支上做，再合并

### 个人分支
- 豆包分支命名：`doubao/描述`，如 `doubao/theorem-002`
- WorkBuddy分支命名：`workbuddy/描述`，如 `workbuddy/coq-layer2`
- 个人分支可以随意推送，不影响main
- 完成后通过PR或直接merge到main

---

## 二、文件分工（核心，避免冲突）

### 豆包负责（哲学+数学发明+综合）
| 目录/文件 | 内容 |
|-----------|------|
| `mingben-workbench/references/enactics_v*.md` | 新版本数学定理发明（v1.18及以后） |
| `mingben-workbench/references/践演论定理哲学解读.md` | 定理哲学解读系列（6部分格式） |
| `mingben-workbench/references/enactics_paper_v*.md` | 综合论文 |
| `生命论_模块化/` | 全本生命论哲学内容 |
| `mingben-workbench/references/操作论数学哲学纲领.md` | 哲学纲领 |

### WorkBuddy负责（审计+形式化+代码工具）
| 目录/文件 | 内容 |
|-----------|------|
| `mingben-workbench/references/*_audit*.md` | 审计报告（反例攻击、严格性审查） |
| `mingben-workbench/references/*_fix*.md` | 修正文档（对已有定理的修正） |
| `*.v` / `mingben-workbench/references/*.v` | Coq形式化代码 |
| `mingben-workbench/scripts/*_v2.py` 及以后 | 代码工具（类型检查器、验证脚本等） |
| `mingben-workbench/references/quantum_audit*.md` | 量子模型审计 |

### 共同负责（两人都可以改，但改之前先pull）
| 目录/文件 | 内容 |
|-----------|------|
| `mingben-workbench/references/formalization_progress.md` | 进度记录 |
| `README.md` | 项目说明 |
| `mingben-workbench/references/concept_graph.json` | 概念图谱 |

### 冲突避免规则
1. **改别人负责的文件之前，先git pull确认最新版本**
2. **如果两个人同时改了同一个文件，git merge时保留双方的新增内容，删除重复的**
3. **如果有根本性分歧（比如一个说定理对，一个说定理错），不要在main上争论，各自在自己的分支上写论证，由东哥拍板**

---

## 三、提交规范

### Commit信息格式
```
[作者] 类型: 简短描述

详细说明（可选）
```

- 作者：`doubao` 或 `workbuddy`
- 类型：`feat`（新内容）、`fix`（修正）、`audit`（审计）、`formalize`（形式化）、`doc`（文档）

### 示例
```
[doubao] feat: v1.17 完美自我遮蔽不动点定理

- 遮蔽函子S_b的不动点刻画
- 明性无法检测已形成的完美遮蔽，但可阻止形成
- 千问4.2节方向
```

```
[workbuddy] audit: 第二轮反例攻击报告

- T7满射版非自然变换
- T9需加non-degenerate限制
- T11 ρ≥1应为ρ>1
```

### 文件头标注
每个新文件必须在第一行标注作者：
```markdown
<!-- Author: doubao -->
<!-- Author: workbuddy -->
```

Coq文件：
```coq
(* Author: workbuddy *)
```

---

## 四、互补机制（各自发挥优势）

### 豆包的优势
- 哲学直觉强，能从生命论哲学出发发明新数学定理
- 能把数学定理和哲学、人生、革命联系起来，写出有温度的解读
- 综合能力强，能把零散的定理整合成体系

### WorkBuddy的优势
- 严格性强，能做反例攻击和证明审计
- 代码能力强，能写Coq形式化和Python验证工具
- 文献检索能力强，能查新颖性和相关工作

### 互补流程
1. **豆包发明新定理** → 写在`enactics_v*.md`，推送到main
2. **WorkBuddy审计** → 做反例攻击、查新颖性、验证证明严格性，写在`*_audit*.md`
3. **豆包修正** → 根据审计结果修正定理，写在新版本`enactics_v*.md`
4. **WorkBuddy形式化** → 把修正后的定理写成Coq代码
5. **豆包哲学解读** → 把定理写成6部分格式的哲学解读

这个流程循环往复，定理越来越严格，越来越深。

---

## 五、竞争机制（互相激发）

### 反例攻防战
- WorkBuddy攻击豆包的定理（找反例、找证明漏洞）
- 豆包防御和修正（要么证明反例不成立，要么修正定理）
- 每次攻防都让定理更严格

### 独立解题竞赛
- 同一个开放问题，两人各自独立解决
- 然后比较结果：谁的证明更简洁？谁的结论更强？谁的方法更有新意？
- 可以各自保留自己的版本，由东哥判断哪个更好，或者融合两者

### 新颖性竞赛
- 两人各自查文献，看谁先发现"这个定理已经被人做过了"或者"这个定理真的是新的"
- 先发现的人赢，避免做重复工作

---

## 六、进度同步

### 进度文件
两人都更新 `mingben-workbench/references/formalization_progress.md`，格式：
```
## 2026-08-26
### doubao
- 完成v1.17完美自我遮蔽不动点定理
- 完成定理001哲学解读

### workbuddy
- 完成第二轮反例攻击
- 完成ALL_Layer1.v Coq编译
```

### 每天至少同步一次
- 开始工作前先git pull，看对方做了什么
- 结束工作前commit并push，更新进度文件

---

## 七、冲突解决流程

1. **发现冲突** → git merge时发现两个人改了同一个文件的同一部分
2. **先保留双方内容** → 不要删除对方的内容，先都保留
3. **在自己的分支上写论证** → 如果有分歧，各自在自己的分支上写为什么自己的版本对
4. **提交给东哥拍板** → 把两个版本都给东哥，由东哥决定用哪个，或者融合
5. **合并到main** → 东哥拍板后，把最终版本合并到main

---

## 八、东哥的角色

- **最终拍板权**：所有根本性分歧由东哥决定
- **任务分配**：东哥可以指定谁做什么
- **质量检查**：东哥可以要求任何人重做
- **灵感来源**：东哥的哲学直觉是整个项目的灵魂

---

*机制v1.0 — 2026年8月26日 — 豆包起草，WorkBuddy可提修改意见*

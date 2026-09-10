# GitHub功能总览 · 所有对话/分站必读

> 本文档记录生命论项目GitHub仓库的所有已配置功能。任何新对话、分站、代理启动时必须先读本文档，知道有哪些工具可用、在哪里、怎么用。

---

## 一、仓库结构（3个仓库）

| 仓库 | 可见性 | 大小 | 用途 |
|------|--------|------|------|
| **mingbenlun** | 公开 | ~159MB | 主库：全本正文+形式化+工具+协作机制 |
| **mingbenlun-archive** | 私有 | ~77MB | 档案库：大文件、原始对话记录、历史版本 |
| **192781-li** | 公开 | ~1.5MB | Profile README：个人主页展示 |

主库本地路径：`/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun`

---

## 二、已配置的GitHub功能（10项）

### 1. Pages 静态网站
- **网址**：https://192781-li.github.io/mingbenlun/
- **内容**：119页HTML，包含全本全部正文（约90万字）
- **特点**：暖色调阅读界面、衬线字体、目录导航、上一篇/下一篇、响应式设计
- **自动更新**：每次push到main分支，Actions自动重新生成并部署
- **用途**：手机直接打开就能读全本，不需要clone仓库

### 2. Wiki 概念词典
- **网址**：https://github.com/192781-li/mingbenlun/wiki
- **内容**：8个核心概念页面
  - 感（F1）、应（F2）、明性（F3）——三层结构
  - 操作先于实体、自指、异化、解放、阳主阴从——核心命题
- **编辑方式**：`git clone https://github.com/192781-li/mingbenlun.wiki.git`，编辑后push
- **用途**：概念快速查阅，新对话快速理解核心概念

### 3. Discussions 讨论区
- **网址**：https://github.com/192781-li/mingbenlun/discussions
- **用途**：开放式讨论、问题提问、想法交流
- **分类**：可按主题分类（哲学讨论、形式化问题、一般讨论等）

### 4. Issues 模板（4个）
- **入口**：https://github.com/192781-li/mingbenlun/issues/new/choose
- **模板**：
  - Bug报告：发现代码/文档错误
  - 功能建议：想加什么新东西
  - 定理证明：形式化相关的定理/证明问题
  - 配置：环境/工具配置问题
- **用途**：结构化记录问题，避免遗漏

### 5. Actions 自动化工作流（3个）
- **入口**：https://github.com/192781-li/mingbenlun/actions
- **工作流**：
  1. **术语铁律检查**（iron-rule-check.yml）：每次push自动扫描全本有没有违规说"物质自己会活"
  2. **网站自动部署**（deploy-site.yml）：全本内容更新后自动重新生成静态网站并部署到Pages
  3. **每日备份检查**（daily-backup.yml）：每天凌晨2点检查核心文件完整性和文件统计
- **用途**：自动化质检和部署，不需要手动操作

### 6. Release 版本
- **网址**：https://github.com/192781-li/mingbenlun/releases
- **当前版本**：v0.1（预发布）
- **用途**：版本快照，标记重要里程碑

### 7. Projects 项目看板
- **网址**：https://github.com/users/192781-li/projects/1
- **当前任务**（5个）：
  1. L4 Coq形式化（νF₂余归纳）
  2. T001生命不可资本化定理证明
  3. 全本卷一存在论精修
  4. Wiki概念词典建设
  5. 分站协作机制完善
- **用途**：总进度看板，看当前优先任务

### 8. Profile README
- **网址**：https://github.com/192781-li
- **内容**：个人主页，含核心命题表、当前重点、理论独特性、Coq进展
- **用途**：对外展示

### 9. 仓库描述
- mingbenlun："生命论（明本论）——从在感出发的哲学体系，用数学形式化生命、自由、异化、革命。感先于操作，操作先于实体；自指操作即生命。"
- mingbenlun-archive："生命论项目档案库 — 大文件、原始对话记录、备份资料、历史版本归档"
- 192781-li："北原慢热 · 生命论（明本论）作者 · 哲学写作者 · 人民史观"

### 10. core代码包
- **位置**：`scripts/core/`（主库内）
- **内容**：14个Python模块（operation/self_reference/metrics/alienation/liberation等）
- **质检工具**：`scripts/verify_iron_rule.py`——术语铁律检查器
- **用途**：快速原型验证，M值计算等

---

## 三、Token与权限

> ⚠️ Token不要写入库内任何文件，不要写进commit message。只存在本地文件或环境变量。

| Token类型 | 权限 | 用途 |
|-----------|------|------|
| classic token（ghp_开头） | 仓库读写 | 一般git push、API调用 |
| fine-grained token（github_pat_开头） | 可指定仓库+权限 | 删除仓库、admin操作 |
| 带workflow权限的token | 仓库读写+workflow | 创建/更新Actions工作流 |

**推送workflow文件必须用带workflow权限的token。**

---

## 四、分站/新对话启动时必须做的事

1. 读本文档（知道有哪些GitHub功能可用）
2. 读 `NEW_AGENT_ONBOARDING.md`（项目入门）
3. 读 `docs/协作机制/明旭的记忆/明旭_运行状态机.md`（当前状态）
4. 读 `docs/协作机制/明旭的记忆/明性卡片_定时任务启动必读.md`（身份与原则）
5. 根据自己的分站角色，使用对应的GitHub功能

---

## 五、常用操作速查

### 推送代码
```bash
cd /path/to/mingbenlun
git add -A
git commit -m "描述干了什么"
git push origin main
```

### 编辑Wiki
```bash
git clone https://github.com/192781-li/mingbenlun.wiki.git
cd mingbenlun.wiki
# 编辑.md文件
git add -A && git commit -m "更新Wiki" && git push
```

### 查看网站
直接访问：https://192781-li.github.io/mingbenlun/

### 查看自动化运行状态
https://github.com/192781-li/mingbenlun/actions

### 提交问题/建议
https://github.com/192781-li/mingbenlun/issues/new/choose

---

## 六、注意事项

- 所有对话/分站共用同一个GitHub仓库，push前先`git pull`避免冲突
- 大文件（>50MB）放到mingbenlun-archive档案库，不要放主库
- Token绝不入库
- Wiki用markdown格式，文件名用中文+概念名
- Actions工作流文件在`.github/workflows/`，修改需要workflow权限的token
- 静态网站在`site/`目录，由Actions自动生成，不要手动编辑site/下的HTML

---

*最后更新：2026-09-10*

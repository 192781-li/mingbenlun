# 明旭库工具挖掘与 GitHub 功能利用报告 v1.0

> 挖掘：S05 信息分站 · 2026-09-10
> 范围：仓库内隐藏工具 + GitHub 平台功能

---

## 一、已挖掘并迁移的工具（8个）

### 量论工具（3个）→ `tools/量论工具/`

| 工具 | 行数 | 功能 | 状态 |
|---|---|---|---|
| `lianglun_calc.py` | 459 | 量论计算器，完整CLI：calc/dynamic/diagnose/track | ✅ 可运行 |
| `n_value_monte_carlo.py` | 232 | N值蒙特卡洛模拟 | ✅ 已迁移 |
| `crystallization_simulator.py` | 166 | 结晶模拟器 | ✅ 已迁移 |

**使用示例**：
```bash
python3 tools/量论工具/lianglun_calc.py calc --alpha 0.8 --T 1.2 --N 3
python3 tools/量论工具/lianglun_calc.py diagnose
```

### 质量检查工具（4个）→ `scripts/质量检查/`

| 工具 | 行数 | 功能 |
|---|---|---|
| `quality_gate.py` | 274 | 践演论全本质量门禁（结构/引用/越级陈述检查） |
| `overclaim_checker.py` | 338 | 过度宣称检查器 |
| `circular_reasoning_detector.py` | 350 | 循环论证检测器 |
| `mingxing_guard.py` | 186 | 明性守卫（概念纪律检查） |

**使用示例**：
```bash
python3 scripts/质量检查/quality_gate.py 生命论_模块化/
python3 scripts/质量检查/overclaim_checker.py 目标文件.md
```

### 高考答题训练（1个）→ `tools/高考答题训练/`

| 工具 | 行数 | 功能 |
|---|---|---|
| `exam_trainer.py` | 604 | F1/F2/F3 三层递归答题训练系统（感→应→自指映射高考答题） |

**使用示例**：
```bash
python3 tools/高考答题训练/exam_trainer.py
```

---

## 二、仍在 archive/ 待评估的工具

### old_workbench/scripts/（剩余40个）

高潜力待评估：
- `self_audit.py` (563行) —— 自审工具，最大
- `check_self_consistency.py` (177行) —— 自洽性检查
- `ref_consistency_checker.py` (313行) —— 引用一致性检查
- `pre_commit_hook.py` (137行) —— git pre-commit钩子
- `build_combined_book.py` (107行) —— 构建合订本
- `mingcheck.py` (181行) —— 明本综合检查
- `spine.py` (69行) —— 骨架生成

低优先级/可能过时：
- `check_formal_*.py` (4个) —— 旧形式化检查，S04已有新工具链
- `verify_*.py` (5个) —— 旧定理验证，Coq已替代
- `migrate_old_refs.py`、`analyze_old_refs.py` —— 旧参考迁移，一次性脚本

### old_workbench/tools/（剩余8个）

- `new_math_verifier.py` (138行) —— 新数学验证器
- `ai_classifier.py` (224行) —— AI分类器
- `productivity_checker.py` (174行) —— 生产力检查
- `network_critical_mass.py` (168行) —— 网络临界质量
- `ptl_prototype.py` + `ptl/` —— PTL原型

---

## 三、GitHub 平台隐藏功能（当前未利用）

### 1. GitHub Actions（最有价值，当前完全没用）

**可以做的自动化**：
- 每次 push 自动运行 `quality_gate.py` + `verify_iron_rule.py`
- 每次 PR 自动运行质量检查
- 每日自动构建合订本
- 自动备份到 archive 库

**需要创建**：`.github/workflows/quality-check.yml`

### 2. GitHub Pages（可以托管静态内容）

**可以托管**：
- `docs/reference_materials/知识库/知识库.html` —— 可检索知识库
- 全库导航地图（转HTML）
- 生命论在线阅读版

**需要创建**：`.github/workflows/pages.yml` + 开启 Pages

### 3. GitHub Releases（版本发布）

**可以发布**：
- 生命论合订本 PDF/EPUB/TXT
- 工具包打包下载
- 里程碑版本标记

### 4. Issue 模板（当前只有 PR 模板）

**可以添加**：
- `.github/ISSUE_TEMPLATE/bug_report.md` —— 工具bug报告
- `.github/ISSUE_TEMPLATE/feature_request.md` —— 功能建议
- `.github/ISSUE_TEMPLATE/分站任务.md` —— 分站任务模板

### 5. 标签（Labels）规范化

当前可能没有系统标签。建议：
- `分站-S00/S01/S02/S03/S04/S05` —— 按分站分类
- `优先级-高/中/低`
- `类型-bug/feature/docs/refactor`
- `状态-待办/进行中/已完成/阻塞`

### 6. GitHub Projects（项目看板）

可以用 Projects 做分站任务看板，替代当前的 JSON 配置文件。

### 7. 仓库安全功能

- **Dependabot** —— 自动检查依赖更新
- **Code scanning** —— 代码安全扫描
- **Secret scanning** —— 检测token泄露（重要！防止token被提交）

---

## 四、当前 .github/ 状态

```
.github/
└── PULL_REQUEST_TEMPLATE.md  (已存在，1923字节)
```

**缺失**：
- ❌ workflows/（GitHub Actions）
- ❌ ISSUE_TEMPLATE/
- ❌ dependabot.yml
- ❌ CODEOWNERS

---

## 五、建议的下一步（按优先级）

### 高优先级
1. **创建 GitHub Actions 质量检查** —— 每次push自动跑 quality_gate + verify_iron_rule
2. **开启 Secret scanning** —— 防止token泄露（已有6个分站token，风险高）
3. **更新 README** —— 移除已归档的 mingben-workbench/ 引用，更新工具列表

### 中优先级
4. **评估并迁移 self_audit.py** —— 563行的自审工具
5. **创建 Issue 模板** —— 规范分站任务提交
6. **GitHub Pages 托管知识库** —— 让知识库.html 可在线访问

### 低优先级
7. **GitHub Releases 发布合订本**
8. **Projects 看板**
9. **Dependabot 依赖更新**

---

## 六、工具总索引（整理后）

```
tools/
├── 核心概念工具包/    14核心模块+11示例+README（刚迁移）
├── 量论工具/          lianglun_calc + n_value_monte_carlo + crystallization（刚迁移）
├── 高考答题训练/      exam_trainer F1/F2/F3系统（刚迁移）
├── 术数工具包/        奇门/八字/六壬排盘
├── video_tools/       视频转写v2.0
└── 实时留痕工具包/    auto_commit + 模板

scripts/
├── 质量检查/          quality_gate + overclaim + circular + mingxing_guard（刚迁移）
├── s04_deepseek/      S04证明循环（22脚本）
├── token_management/  token配置+修复
├── verify_iron_rule.py  术语铁律校验（刚迁移）
├── mingben_cli.py     统一CLI入口（刚迁移）
└── 其他脚本            金句提取/备份/同步等
```

---

*S05 信息分站出品 · 工具挖掘与GitHub功能利用*

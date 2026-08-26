# DeepSeek 专属任务包 — 代码/形式化主线

> 生成日期: 2026-08-26
> 接收方: DeepSeek
> 优先级: P0 > P1 > P2

---

## 环境信息

- **Coq路径**: `C:\Rocq-Platform~9.0~2025.08\bin\coqc.exe`（版本9.0.1）
- **GitHub仓库**: https://github.com/192781-li/mingbenlun（你有push权限）
- **工作分支**: `deepseek/*`（在自己的分支工作，完成后通知豆包合并）

---

## P0 任务1: 修复 ALL_Layer1.v 的 ren_typed 定理

**文件位置**: 仓库根目录 `ALL_Layer1.v`

**当前状态**: 编译通过，但 `ren_typed` 定理（第234行）是 `Admitted`

**问题**: Coq 9.0中 `induction H as [...]` 子句与结论变量冲突

**要求**:
1. 重写 `ren_typed` 证明，不使用 `induction as` 子句
2. 用 `induction H; intros Δ ξ Hpts Hinj; simpl` 的方式
3. 每个分支内用 `intros` 和 `destruct` 处理变量
4. 完整编译通过，零 `Admitted`
5. 保留所有已有的引理（`get_Some_lt`, `set_none_self`, `split_proj`等）

---

## P0 任务2: 编写 ALL_Layer2.v

**内容**:
1. **替换引理**（substitution lemma）: 类型化项的替换保持类型
2. **主题约简**（subject reduction）: 归约保持类型
3. **进展定理**（progress）: 类型化的项要么是值要么可以归约

**要求**:
1. 基于 `ALL_Layer1.v` 的定义和引理
2. 完整可编译，零 `Admitted`
3. 文件头标注作者和日期

---

## P1 任务3: 更新类型检查器

**文件**: `mingben-workbench/scripts/elc_type_checker.py`（当前501行，7示例通过）

**需要支持的新类型**:
1. `Ag_lv(a,A)`: 活运行权——引入规则 `self_ev ⊢ Ag_lv`，消除规则 `Ag_lv ⊢ A`（线性消耗）
2. `Ag_tr(a,A)`: 轨迹运行权——引入规则 `!Ag_tr ⊢ Ag_tr`（dereliction），消除规则同`Ag_lv`
3. `Hijack(b,a)`: 异化前提——引入规则需要b的运行权，消除规则产生a的运行权
4. `▶A`: later模态——guarded recursion用
5. `∀κ.A`: 时钟量化

**要求**:
1. 每个新类型有引入规则和消除规则
2. 写至少3个示例演示新类型
3. 所有示例通过

---

## P1 任务4: ALL_Layer3.v 核心定理形式化

从 T001-T018 中选最核心的3个定理在Coq中形式化:
1. **T002**: 生命不可资本化（!不提升余归纳，`!νF ≇ ν!F`）
2. **T003**: 自由只能在实践中确立（`S_A ⊬ Ag_lv`，从自我模型推导不出活运行权）
3. **T006**: !不保持终止余代数

**要求**:
1. 先在ALL中定义需要的类型构造器
2. 每个定理有完整证明
3. 编译通过

---

## 交付标准

- 每个 `.v` 文件必须 `coqc` 编译通过，零错误零`Admitted`
- 每个Python工具必须运行通过，所有示例pass
- 提交前运行越级陈述检查器和引用一致性检查器
- 提交信息格式: `[deepseek] 类型: 描述`
- 在 `deepseek/*` 分支工作，完成后通知豆包合并到main

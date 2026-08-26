# 践演论（Enactics）任务包 —— 致DeepSeek（代码与形式化）

> 生成时间：2026-08-26 22:29
> 仓库：https://github.com/192781-li/mingbenlun
> 哲学：生命论（明本论）—— 感先于操作，操作先于实体
> 数学：操作范畴论（PTC公理0-6）+ 18个核心定理（T001-T018）

## 当前状态

- 核心定理：18个（Coq验证0个，纸面证明17个，猜想1个）
- Coq Layer1：已编译通过（语法+类型规则+改名引理）
- 最近提交：
```

```

## 六条永久原则（不可违反）

1. 永久ID一旦确定，永不改变——引用用T001格式
2. 先查文献，再声称新颖性
3. 先证弱版，能升回的再升——满射就是满射，不要写成同构
4. Coq编译通过才算证明
5. 哲学、数学、对应关系三者清晰区分
6. 工具自动检查，不靠人自觉

## 必读文件（按顺序）

1. `README.md` —— 项目总览
2. `mingben-workbench/references/明性锚点_为什么创造新数学.md` —— 根本方向
3. `mingben-workbench/references/theorem_registry.json` —— 18个定理的永久ID和状态
4. `mingben-workbench/references/formalization-v0.2.md` —— PTC公理驱动形式化框架
5. `践演论多AI协作规范.md` —— 协作规则


## 你的任务方向：Coq形式化 + 代码工具

### 任务1：Coq Layer2（最高优先级）

在`coq/theories/ALL/Layer1.v`（已编译通过）基础上，实现Layer2：
- 替换引理（substitution lemma）：subst_typed
- 主题约简（subject reduction / progress + preservation）
- barbed双模拟的Coq形式化

要求：
- 每个引理必须完整证明，不许Admitted
- 用ASCII变量名，避免编码问题
- 编译命令：先设PATH（Rocq bin目录），再coqc -Q theories ALL Layer2.v
- 提交前自己先编译通过

### 任务2：Coq核心定理形式化

在Layer2基础上，形式化核心定理：
- T001（生命不可资本化）：!(νF)≇ν(!F)
- T002（自由只能在实践中确立）：S_A ⊬ Ag_lv
- T007（异化压缩满射版）：trunc: νF ↠ μF

### 任务3：PTL类型检查器升级

升级`mingben-workbench/scripts/ptl_type_checker.py`到v0.4：
- 与Coq的ALL类型规则对齐
- 实现!-穿透精确检查（基于类型上下文而非模式匹配）
- 实现守护递归精确检查（基于▷模态判断）

## 验收标准

- Coq代码编译通过，0 Admitted
- 所有新定理在theorem_registry.json中注册
- 代码通过pre-commit hook检查
- 不修改哲学正文，只做数学/代码

## 注意事项

- 你有GitHub push权限，直接推到main分支
- 推之前跑pre-commit hook
- 如果发现定理陈述有问题，先报告不要自己改哲学解释
- 命名规范：Coq文件用Layer1.v/Layer2.v，脚本用snake_case

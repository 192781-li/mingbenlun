# 践演论Coq开发指南

> 所有参与Coq形式化的开发者（DeepSeek、豆包、其他AI）必读。
> 最后更新: 2026-08-26

---

## 一、项目结构

```
coq/
├── _CoqProject              # Coq项目配置（编译入口）
├── coq_verify.py            # 验证脚本（Admitted检测+循环依赖+编译检查）
├── coq_verify_report.json   # 验证脚本自动生成的报告
├── README.md                 # 本文件（开发指南）
└── theories/
    ├── ALL/                  # ALL形式系统核心
    │   ├── Layer1.v         # 第1层：语法+类型规则+改名引理（已完成，ren_typed Admitted）
    │   ├── Layer2.v         # 第2层：替换引理+主题约简（待写）
    │   └── Layer3.v         # 第3层：核心定理形式化（待写）
    ├── metatheory/           # 元理论定理
    │   ├── Incompleteness.v # 践演不完备性定理（Theorem 3.1）
    │   ├── Complexity.v     # Π₂完全性（Theorem 3.2）
    │   ├── NoCloning.v      # !不保持终止余代数（Theorem 6.1）
    │   ├── Alienation.v     # 异化压缩满射（Theorem 5.1）
    │   ├── Clarity.v        # 明性不动点（Theorem 4.2 + f³不动点）
    │   └── Cascade.v        # 革命级联（Theorem 7.6a/7.6b）
    └── applications/         # 应用定理
        ├── AISafety.v       # AI安全定理（Theorem 7.4/7.5）
        └── HijackDetection.v # 劫持检测定理（Theorem 7.1/7.2/7.3）
```

---

## 二、命名规范

### 2.1 文件命名
- 文件名使用PascalCase：`Layer1.v`、`Incompleteness.v`
- 每个文件对应一个主题，不要把不相关的定理混在一个文件里

### 2.2 定理命名
- 定理名使用snake_case，描述定理内容：`ren_typed`、`subject_reduction`、`no_cloning`
- **禁止**使用`theorem1`、`lemma2`这种无意义编号
- 定理的永久ID（T001-T018）写在注释里，不要写在定理名里

### 2.3 模块命名
- 模块名与文件名一致：`Layer1`、`Incompleteness`
- 使用`Require Import Enactics.ALL.Layer1.`导入

---

## 三、验证脚本用法

### 3.1 基本用法
```bash
cd coq
python coq_verify.py
```

### 3.2 严格模式（有Admitted就报错）
```bash
python coq_verify.py --strict
```

### 3.3 检查内容
1. **Admitted检测**：扫描所有`.v`文件，找出未证明的定理（`Admitted.`），列出定理名和类型
2. **循环依赖检测**：DFS检测`Require Import`的有向环
3. **编译检查**：调用`coqc`编译每个文件，报告编译错误
4. **报告生成**：输出`coq_verify_report.json`

### 3.4 退出码
- `0`: 全部通过
- `1`: 有编译错误
- `2`: 严格模式下有Admitted

---

## 四、开发流程

### 4.1 新增定理
1. 在`theorem_registry.json`中注册永久ID（T001-T018）
2. 在对应的`.v`文件中写`Theorem`声明
3. 写证明（禁止直接`Admitted`，除非明确标记为待证明）
4. 运行`python coq_verify.py --strict`确认通过
5. 更新`三方协作任务监控表.md`

### 4.2 修复Admitted
1. 找到对应的`Theorem ... Admitted.`
2. 替换为完整证明
3. 运行验证脚本确认Admitted数量减少
4. commit并push

### 4.3 新增文件
1. 在对应目录下创建`.v`文件
2. 在`_CoqProject`中添加文件路径
3. 写内容
4. 运行验证脚本

---

## 五、Coq版本与依赖

- **Coq版本**: 8.13+（当前使用Rocq 9.0.1，兼容Coq 8.13语法）
- **依赖**: 仅Coq标准库（`List`、`PeanoNat`、`Lia`、`ClassicalEpsilon`）
- **禁止**引入外部库（如mathcomp、stdpp），保持依赖最小化

### 5.1 Windows路径
Coq可执行文件：`C:\Rocq-Platform~9.0~2025.08\bin\coqc.exe`

使用前需要将Coq路径加入PATH：
```powershell
$env:PATH = "C:\Rocq-Platform~9.0~2025.08\bin;" + $env:PATH
```

---

## 六、质量标准

### 6.1 证明质量
- **禁止**`Admitted`溜进综合论文对应的定理
- 证明必须完整，不能跳步（除非用`auto`、`eauto`等策略自动完成）
- 复杂证明需要注释说明思路

### 6.2 弱版优先
- 先证弱版（满射`↠`、retraction`⇒`、双模拟`≈`），能升回同构`≅`的再升
- 禁止在没有严格证明的情况下写`≅`
- 如果证明中发现需要降级，立即更新`theorem_registry.json`

### 6.3 三者清晰区分
- **数学定理**：Coq中证明的命题
- **哲学命题**：关于存在、价值、意义的论断（写在注释或独立文档中，不写进Coq证明）
- **对应关系论证**：哲学命题与数学定理之间的对应（写在注释或独立文档中）

---

## 七、常见问题

### Q: 我可以直接修改Layer1.v吗？
A: 可以，但请先运行`python coq_verify.py`确认当前状态，修改后再次运行确认没有引入新错误。

### Q: 证明卡住了怎么办？
A: 可以暂时`Admitted`，但必须在注释中标记`(* TODO: 待证明，原因：... *)`，并在`三方协作任务监控表.md`中更新状态。

### Q: 我可以新增文件吗？
A: 可以，但必须在`_CoqProject`中注册，并遵循命名规范。

### Q: 验证脚本报coqc not found怎么办？
A: 在Windows上需要先设置PATH：`$env:PATH = "C:\Rocq-Platform~9.0~2025.08\bin;" + $env:PATH`

---

*本指南实时更新。如有疑问，在消息中@豆包。*

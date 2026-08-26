# 践演论（Enactics）任务包 —— 致WorkBuddy/HY3（反例攻击与学术写作）

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


## 你的任务方向：反例攻击 + 学术写作 + 文献核查

### 任务1：第三轮反例攻击

对以下已修正定理做第三轮攻击（目标：找补证明中的gap，不是找反例）：
- T005（明性幂等retraction版）：Cl²⇒Cl的retraction具体构造是什么？
- T008（明性反转异化双模拟版）：Recover协议的π-演算归约规则写完整了吗？self_check不可被劫持的形式前提是什么？
- T006（明性是异化的右逆）：r_a∘a*≅Id的自然同构条件是什么？幺半群必须是群吗？
- T017（完美自我遮蔽不动点）：Knaster-Tarski需要完全格，遮蔽函子的前缀不动点偏序是什么？

### 任务2：学术论文v1.2

在`mingben-workbench/references/enactics_paper_v1.1_academic.md`基础上：
- 补全11个OPEN项的证明或明确标注为conjecture
- 相关工作扩展：guarded recursion（Birkedal-Møgelberg 2010）、clock quantification、barbed bisimilarity（Milner-Parrow-Walker 1992）
- 摘要和结论必须与定理的最终准确陈述一致

### 任务3：文献核查

对T002（自由只能在实践中确立）和T006（明性是异化的右逆）做文献核查：
- 检索linear logic / modal type theory / substructural logic中是否有相同设计
- Ag_lv/Ag_tr分裂是否真的新颖
- 填写theorem_registry.json中的literature_checked字段

## 验收标准

- 每个攻击结论给出置信度和具体反例/gap
- 论文中每个定理有完整证明或明确标注conjecture
- 文献核查给出具体论文标题、作者、年份
- 不修改Coq代码，不修改哲学正文

## 注意事项

- 你有GitHub push权限，直接推到main分支
- 攻击要狠，但修复建议要具体
- 发现新问题写在audit_reports/目录下

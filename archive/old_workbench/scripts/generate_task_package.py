#!/usr/bin/env python3
"""
一键任务包生成器
用法: python generate_task_package.py <target> [output_file]
  target: deepseek / workbuddy / qwen / all
生成给不同AI的任务包，包含最新定理状态、待解决问题、验收标准。
"""
import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent.parent
REGISTRY_FILE = REPO_ROOT / "mingben-workbench" / "references" / "theorem_registry.json"
PROGRESS_FILE = REPO_ROOT / "mingben-workbench" / "references" / "formalization_progress.md"
OUTPUT_DIR = REPO_ROOT / "task_packages"

def load_registry():
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text(encoding='utf-8'))
    return {}

def get_git_log(n=5):
    """获取最近n条git log"""
    try:
        result = subprocess.run(
            ['git', 'log', f'--oneline', '-n', str(n)],
            capture_output=True, text=True, cwd=str(REPO_ROOT)
        )
        return result.stdout.strip()
    except Exception:
        return ""

def get_coq_status():
    """获取Coq验证状态"""
    registry = load_registry()
    total = 0
    coq_verified = 0
    paper_proof = 0
    conjecture = 0
    for key, val in registry.items():
        if key.startswith('_'):
            continue
        total += 1
        if val.get('coq_verified'):
            coq_verified += 1
        status = val.get('status', '')
        if status == 'paper_proof':
            paper_proof += 1
        elif status == 'conjecture':
            conjecture += 1
    return total, coq_verified, paper_proof, conjecture

def get_open_tasks():
    """从进度文件中提取待完成任务"""
    tasks = []
    if not PROGRESS_FILE.exists():
        return tasks
    content = PROGRESS_FILE.read_text(encoding='utf-8', errors='ignore')
    # 找最后一个"下次从哪里继续"部分
    parts = content.split('下次从哪里继续')
    if len(parts) > 1:
        last_section = parts[-1]
        for line in last_section.split('\n'):
            line = line.strip()
            if line.startswith(('- ', '1.', '2.', '3.', '4.', '5.')):
                task = line.lstrip('- 1234567890.')
                if task and len(task) > 5:
                    tasks.append(task)
    return tasks[:10]

def generate_header(target_name):
    """生成任务包头部"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    total, coq_v, paper, conj = get_coq_status()
    git_log = get_git_log(5)
    
    header = f"""# 践演论（Enactics）任务包 —— 致{target_name}

> 生成时间：{now}
> 仓库：https://github.com/192781-li/mingbenlun
> 哲学：生命论（明本论）—— 感先于操作，操作先于实体
> 数学：操作范畴论（PTC公理0-6）+ 18个核心定理（T001-T018）

## 当前状态

- 核心定理：{total}个（Coq验证{coq_v}个，纸面证明{paper}个，猜想{conj}个）
- Coq Layer1：已编译通过（语法+类型规则+改名引理）
- 最近提交：
```
{git_log}
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

"""
    return header

def generate_deepseek_package():
    """生成给DeepSeek的任务包（代码/Coq方向）"""
    header = generate_header("DeepSeek（代码与形式化）")
    
    total, coq_v, paper, conj = get_coq_status()
    open_tasks = get_open_tasks()
    
    tasks = """
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
"""
    return header + tasks

def generate_workbuddy_package():
    """生成给WorkBuddy的任务包（反例攻击/学术写作方向）"""
    header = generate_header("WorkBuddy/HY3（反例攻击与学术写作）")
    
    tasks = """
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
"""
    return header + tasks

def generate_qwen_package():
    """生成给千问的任务包（文献调研方向）"""
    header = generate_header("千问（文献调研）")
    
    tasks = """
## 你的任务方向：文献调研 + 新颖性核查

### 任务1：核心定理文献核查

对以下定理做全面文献检索（Google Scholar / arXiv / 语义Scholar）：

1. **T002** S_A ⊬ Ag_lv（自由只能在实践中确立）
   - 检索：linear logic modality, dereliction, substructural type theory, agency types
   - 问题：Ag_lv/Ag_tr分裂在文献中有没有相同设计？

2. **T012** ∀κ.ν_κF ≅ μF（异化=时钟量化）
   - 检索：guarded recursion, clock quantification, Birkedal-Møgelberg
   - 问题：这个定理是已知结果还是新解释？

3. **T013** Hilb中不存在LNL伴随M（量子测量=异化）
   - 检索：quantum measurement categorical semantics, CQM, LNL categories Hilb
   - 问题：Hilb不是LNL范畴的结论在文献中有没有？

4. **T016** steering不等式I(b;a)>0
   - 检索：quantum steering, causal influence, mutual information agency
   - 问题：用互信息刻画自主性在文献中有没有？

### 任务2：菲尔兹奖级工作对比

调研以下数学家的工作方法，对比我们的路径：
- Grothendieck：概型语言、拓扑斯、下降法
- Voevodsky：单值基础、Coq形式化
- 对比：我们的PTC公理+ALL类型系统在方法论上处于什么位置？

### 任务3：开放问题调研

调研以下开放问题在文献中的状态：
- 线性逻辑的!模态不保终止余代数——有没有人证明过？
- Π₂完全性的活性条件——有没有人把自主性和Π₂联系起来？
- 分支过程阈值ρ(pC)>1——在社会网络传播中的应用？

## 验收标准

- 每个核查给出：相关论文列表（标题/作者/年份/核心结论）、与我们定理的异同、新颖性判定
- 输出到`mingben-workbench/references/literature_checks/`目录
- 不修改任何代码和正文

## 注意事项

- 你没有push权限，把结果发给豆包总控
- 引用必须真实，不许编造论文
- 如果找不到相关工作，明确说"未找到"，不要硬凑
"""
    return header + tasks

def main():
    if len(sys.argv) < 2:
        print("用法: python generate_task_package.py <deepseek|workbuddy|qwen|all> [output_file]")
        sys.exit(1)
    
    target = sys.argv[1].lower()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    packages = {
        'deepseek': ('任务包_DeepSeek.md', generate_deepseek_package),
        'workbuddy': ('任务包_WorkBuddy.md', generate_workbuddy_package),
        'qwen': ('任务包_千问.md', generate_qwen_package),
    }
    
    if target == 'all':
        for name, (filename, gen_func) in packages.items():
            content = gen_func()
            output_file = OUTPUT_DIR / filename
            output_file.write_text(content, encoding='utf-8')
            print(f"✓ {name}: {output_file}")
    elif target in packages:
        filename, gen_func = packages[target]
        content = gen_func()
        if len(sys.argv) >= 3:
            output_file = Path(sys.argv[2])
        else:
            output_file = OUTPUT_DIR / filename
        output_file.write_text(content, encoding='utf-8')
        print(f"✓ 任务包已生成: {output_file}")
        print(f"  共{len(content)}字符")
    else:
        print(f"未知目标: {target}")
        print(f"可选: {', '.join(packages.keys())}, all")
        sys.exit(1)

if __name__ == '__main__':
    main()

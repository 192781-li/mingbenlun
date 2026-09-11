#!/usr/bin/env python3
"""
PTL（践演迹语言）类型检查器 v0.3
基于形式化v0.3框架的PTL类型规则

核心检查：
1. 线性性检查：变量是否被用了多次（对应公理2——操作不可复制）
2. !-穿透检查：!是否被非法应用于νF₂（对应定理20——生命不可资本化）
3. 生产性检查：递归是否是守护的（对应公理5——守护递归）
4. 公理依赖检查：每一步推导用了哪些类型规则/公理
5. 类型推断：基于模式匹配推断每一步的类型

与旧启发式脚本的区别：
- 旧脚本用关键词匹配（"由此可见""因此"）抓可疑推导
- PTL检查器用类型规则做精确检查

注意：本检查器是初版，用模式匹配+启发式实现，不是完整的类型推断器。
完整的PTL类型检查器需要Coq形式化（见coq/theories/ALL/）。
"""

import re
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

# ============================================================
# PTL类型系统（7类类型）
# ============================================================

class PTLType(Enum):
    """PTL的7类类型"""
    LINEAR = "A"           # 线性类型：操作（不可复制）
    BANG = "!A"            # !-模态：轨迹/沉积（可复制）
    TENSOR = "A⊗B"        # 张量积：并行操作
    LIN_ARROW = "A⊸B"     # 线性蕴涵：操作干预
    MU = "μF"              # 归纳类型：有限操作
    NU = "νF"              # 余归纳类型：无限操作/生命流
    LATER = "▷A"           # later模态：守护递归

# ============================================================
# 公理系统（公理0-6）
# ============================================================

AXIOMS = {
    "公理0": {"name": "感（践演事实）", "type": "践演坐实", "description": "在感是原初的第一人称事实，不是类型规则"},
    "公理1": {"name": "操作先于实体", "type": "存在论", "description": "操作是原初的，实体是操作的沉积"},
    "公理2": {"name": "操作不可复制", "type": "线性性", "description": "线性变量只能用一次，操作不可复制"},
    "公理3": {"name": "!-模态分离", "type": "模态", "description": "!-模态（轨迹/沉积）与线性操作分离，!不穿透νF₂"},
    "公理4": {"name": "自指操作", "type": "自指", "description": "操作可以指向自身，S=f(S)，自指是生命的结构"},
    "公理5": {"name": "守护递归", "type": "递归", "description": "递归必须是守护的（guarded），生产性过程每步都有产出"},
    "公理6": {"name": "决断", "type": "规范", "description": "决断不是推导，是活操作的选择，站在公理6的输入位置"},
}

# ============================================================
# 检查结果数据结构
# ============================================================

@dataclass
class Violation:
    """违规记录"""
    check_type: str           # 检查类型：linearity / bang_penetration / productivity / axiom_dependency
    severity: str             # 严重程度：error / warning / info
    file: str                 # 文件路径
    line: int                 # 行号
    context: str              # 上下文（该行内容）
    message: str              # 违规说明
    suggestion: str           # 修复建议

@dataclass
class DerivationStep:
    """推导步骤"""
    file: str
    line: int
    content: str
    inferred_type: Optional[str] = None      # 推断的类型
    axioms_used: List[str] = field(default_factory=list)  # 使用的公理
    is_guarded: Optional[bool] = None         # 是否守护递归

@dataclass
class CheckReport:
    """检查报告"""
    files_scanned: int = 0
    lines_scanned: int = 0
    derivation_steps: int = 0
    violations: List[Violation] = field(default_factory=list)
    steps: List[DerivationStep] = field(default_factory=list)

# ============================================================
# 模式定义
# ============================================================

# !-穿透模式：!被非法应用于νF₂或生命相关概念
BANG_PENETRATION_PATTERNS = [
    (r'!νF[₂2]', '!νF₂', '!-模态非法穿透νF₂（生命流）', '定理20：νF₂→!νF₂不存在，生命不可资本化'),
    (r'!生命', '!生命', '!-模态非法应用于生命', '生命是νF₂型生产性过程，不可被!-模态捕获'),
    (r'!活劳动', '!活劳动', '!-模态非法应用于活劳动', '活劳动是线性的，不可被资本化为!-模态'),
    (r'!感', '!感', '!-模态非法应用于感', '感是原初的第一人称事实，不可被!-模态固定'),
    (r'!明性', '!明性', '!-模态非法应用于明性', '明性是f³的操作，不可被!-模态固化'),
]

# 线性性违规模式：操作/生命/活劳动等被复制或重复使用
LINEARITY_VIOLATION_PATTERNS = [
    (r'复制(操作|生命|活劳动|感|明性)', '复制线性资源', '线性资源被复制', '公理2：操作不可复制，线性变量只能用一次'),
    (r'(操作|生命|活劳动|感|明性).*?同时.*?(操作|生命|活劳动|感|明性)', '线性资源同时使用', '同一线性资源可能被同时使用', '检查是否为同一资源的多次使用'),
]

# 生产性/守护递归模式
PRODUCTIVITY_PATTERNS = [
    (r'递归.*?(不终止|无限循环|永远运行)', '非守护递归', '递归可能不是守护的', '公理5：递归必须是守护的，生产性过程每步都有产出'),
    (r'无限递归', '无限递归', '无限递归需要检查生产性', '守护递归（▷模态）保证生产性'),
]

# 推导步骤模式：包含推导连接词的行
DERIVATION_PATTERNS = [
    r'因此', r'所以', r'由此', r'故', r'于是', r'从而', r'可见',
    r'因为.*?所以', r'既然.*?就', r'如果.*?那么',
]

# 公理触发词模式
AXIOM_TRIGGERS = {
    "公理0": [r'在感', r'在活着', r'感是', r'活着是'],
    "公理1": [r'操作先于', r'操作是原初', r'实体是.*?沉积'],
    "公理2": [r'不可复制', r'线性', r'只能用一次', r'用一次'],
    "公理3": [r'!-模态', r'轨迹', r'沉积', r'不穿透'],
    "公理4": [r'自指', r'S=f\(S\)', r'指向自身', r'自我递归'],
    "公理5": [r'守护', r'生产性', r'每步都有', r'▷'],
    "公理6": [r'决断', r'选择', r'站在', r'革命'],
}

# 类型推断模式
TYPE_INFERENCE_PATTERNS = [
    (r'νF[₂2]|生命流|生产性过程|永远运行', PTLType.NU.value),
    (r'μF|有限操作|终止|完成态', PTLType.MU.value),
    (r'!-?模态|轨迹|沉积|可复制', PTLType.BANG.value),
    (r'线性|不可复制|用一次', PTLType.LINEAR.value),
    (r'并行|同时|张量', PTLType.TENSOR.value),
    (r'蕴涵|干预|导致', PTLType.LIN_ARROW.value),
    (r'守护|稍后|▷|later', PTLType.LATER.value),
]

# 否定陈述白名单：包含这些词的行跳过!-穿透和线性性检查
# 因为"不存在!νF₂""复制生命不可能"是否定陈述，不是违规
NEGATION_WHITELIST = [
    r'不存在', r'不可能', r'无法', r'不能', r'没有', r'不可', r'不会',
    r'不允许', r'不成立', r'不穿透', r'不可复制', r'不可资本化',
    r'被否定', r'被拒绝', r'被排除', r'被禁止',
]

# 元讨论白名单：包含这些词的行跳过检查
# 因为"检查器发现bug""这是误报"是关于检查器本身的讨论
META_DISCUSSION_WHITELIST = [
    r'检查器', r'误报', r'bug', r'Bug', r'BUG',
    r'扫描结果', r'检查报告', r'检查结果', r'违规标记',
    r'白名单', r'黑名单', r'模式匹配', r'正则',
]

# 报告文件排除模式：这些文件是检查器自身产生的报告，不需要被扫描
REPORT_FILE_PATTERNS = [
    r'_report\.md$', r'_report\.json$',
    r'overclaim_report', r'check.*report', r'ptl_type_checker_report',
    r'formalization_report', r'check456_fullscan_report',
    r'check6_report', r'formalization_check_report',
    r'项目状态报告', r'项目基础设施检查清单',
]

# ============================================================
# 检查器实现
# ============================================================

class PTLTypeChecker:
    """PTL类型检查器"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.report = CheckReport()
        self.exclude_dirs = {'.git', 'backup', '__pycache__', 'node_modules', '.venv', 'coq'}
        self.exclude_files = {'ptl_type_checker.py', 'elc_type_checker.py', 'elc_type_checker_v2.py'}
        self.negation_whitelist = NEGATION_WHITELIST
        self.meta_whitelist = META_DISCUSSION_WHITELIST
        self.report_patterns = REPORT_FILE_PATTERNS

    def is_negation(self, line: str) -> bool:
        """判断是否为否定陈述"""
        for pattern in self.negation_whitelist:
            if re.search(pattern, line):
                return True
        return False

    def is_meta_discussion(self, line: str) -> bool:
        """判断是否为元讨论"""
        for pattern in self.meta_whitelist:
            if re.search(pattern, line):
                return True
        return False

    def is_report_file(self, file_path: Path) -> bool:
        """判断是否为报告文件（检查器自身产生的）"""
        filename = file_path.name
        for pattern in self.report_patterns:
            if re.search(pattern, filename):
                return True
        return False

    def find_md_files(self) -> List[Path]:
        """查找所有Markdown文件（排除报告文件自身）"""
        md_files = []
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            for f in files:
                if f.endswith('.md') and f not in self.exclude_files:
                    fpath = Path(root) / f
                    if not self.is_report_file(fpath):
                        md_files.append(fpath)
        return sorted(md_files)

    def check_bang_penetration(self, file_path: Path, line_num: int, line: str):
        """检查!-穿透违规（跳过否定陈述和元讨论）"""
        # 白名单：否定陈述和元讨论跳过
        if self.is_negation(line) or self.is_meta_discussion(line):
            return
        for pattern, matched, message, suggestion in BANG_PENETRATION_PATTERNS:
            if re.search(pattern, line):
                self.report.violations.append(Violation(
                    check_type="bang_penetration",
                    severity="error",
                    file=str(file_path.relative_to(self.repo_root)),
                    line=line_num,
                    context=line.strip()[:200],
                    message=f"{matched}: {message}",
                    suggestion=suggestion
                ))

    def check_linearity(self, file_path: Path, line_num: int, line: str):
        """检查线性性违规（跳过否定陈述和元讨论）"""
        # 白名单：否定陈述和元讨论跳过
        if self.is_negation(line) or self.is_meta_discussion(line):
            return
        for pattern, matched, message, suggestion in LINEARITY_VIOLATION_PATTERNS:
            if re.search(pattern, line):
                self.report.violations.append(Violation(
                    check_type="linearity",
                    severity="warning",
                    file=str(file_path.relative_to(self.repo_root)),
                    line=line_num,
                    context=line.strip()[:200],
                    message=f"{matched}: {message}",
                    suggestion=suggestion
                ))

    def check_productivity(self, file_path: Path, line_num: int, line: str):
        """检查生产性/守护递归"""
        for pattern, matched, message, suggestion in PRODUCTIVITY_PATTERNS:
            if re.search(pattern, line):
                self.report.violations.append(Violation(
                    check_type="productivity",
                    severity="info",
                    file=str(file_path.relative_to(self.repo_root)),
                    line=line_num,
                    context=line.strip()[:200],
                    message=f"{matched}: {message}",
                    suggestion=suggestion
                ))

    def infer_type(self, line: str) -> Optional[str]:
        """推断行的类型"""
        for pattern, ptype in TYPE_INFERENCE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                return ptype
        return None

    def infer_axioms(self, line: str) -> List[str]:
        """推断行使用的公理"""
        axioms = []
        for axiom, patterns in AXIOM_TRIGGERS.items():
            for pattern in patterns:
                if re.search(pattern, line):
                    axioms.append(axiom)
                    break
        return axioms

    def is_derivation_step(self, line: str) -> bool:
        """判断是否为推导步骤"""
        for pattern in DERIVATION_PATTERNS:
            if re.search(pattern, line):
                return True
        return False

    def check_file(self, file_path: Path):
        """检查单个文件"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return

        lines = content.split('\n')
        self.report.lines_scanned += len(lines)

        # 收集推导步骤用于多行链分析
        derivation_steps_in_file = []

        for i, line in enumerate(lines, 1):
            # 跳过空行和标题
            if not line.strip() or line.strip().startswith('#'):
                continue

            # 检查!-穿透
            self.check_bang_penetration(file_path, i, line)

            # 检查线性性
            self.check_linearity(file_path, i, line)

            # 检查生产性
            self.check_productivity(file_path, i, line)

            # v0.3: 检查哲学压制数学
            self.check_philosophy_overreach(file_path, i, line)

            # 如果是推导步骤，记录并推断类型和公理
            if self.is_derivation_step(line):
                step = DerivationStep(
                    file=str(file_path.relative_to(self.repo_root)),
                    line=i,
                    content=line.strip()[:200],
                    inferred_type=self.infer_type(line),
                    axioms_used=self.infer_axioms(line),
                )
                self.report.steps.append(step)
                self.report.derivation_steps += 1
                derivation_steps_in_file.append(step)

        # v0.3: 多行推导链分析
        self.check_derivation_chains(file_path, derivation_steps_in_file, lines)

    def check_philosophy_overreach(self, file_path: Path, line_num: int, line: str):
        """v0.3: 检查哲学压制数学——在数学证明语境中用哲学论断代替数学证明"""
        if self.is_negation(line) or self.is_meta_discussion(line):
            return

        # 数学证明语境触发词
        math_context = bool(re.search(r'证明|定理|引理|推论|Coq|形式化|类型检查|推导', line))
        # 哲学压制模式
        philosophy_overreach_patterns = [
            (r'哲学上必然', '哲学上必然', '在数学证明中用"哲学上必然"代替形式证明'),
            (r'本质上决定', '本质上决定', '用"本质上决定"跳过数学推导'),
            (r'辩证法告诉我们', '辩证法告诉我们', '用辩证法结论代替数学证明'),
            (r'显然.*?成立', '显然成立', '"显然"跳过证明步骤'),
            (r'不难看出', '不难看出', '"不难看出"跳过证明步骤'),
            (r'显而易见', '显而易见', '"显而易见"跳过证明步骤'),
        ]

        if math_context:
            for pattern, matched, message in philosophy_overreach_patterns:
                if re.search(pattern, line):
                    self.report.violations.append(Violation(
                        check_type="philosophy_overreach",
                        severity="warning",
                        file=str(file_path.relative_to(self.repo_root)),
                        line=line_num,
                        context=line.strip()[:200],
                        message=f"{matched}: {message}",
                        suggestion="哲学给方向，数学给硬约束。数学证明中每一步都要有形式依据，不能用哲学论断跳过。"
                    ))

    def check_derivation_chains(self, file_path: Path, steps: List[DerivationStep], all_lines: List[str]):
        """v0.3: 多行推导链分析——检查公理依赖链的连贯性"""
        if len(steps) < 2:
            return

        # 将连续的推导步骤（间隔不超过3行）组成链
        chains = []
        current_chain = [steps[0]]
        for i in range(1, len(steps)):
            if steps[i].line - current_chain[-1].line <= 3:
                current_chain.append(steps[i])
            else:
                if len(current_chain) >= 2:
                    chains.append(current_chain)
                current_chain = [steps[i]]
        if len(current_chain) >= 2:
            chains.append(current_chain)

        # 检查每条链
        for chain in chains:
            all_axioms = set()
            for step in chain:
                all_axioms.update(step.axioms_used)

            # 检查1：从公理0（感）直接跳到经验事实，没有中间公理
            has_axiom0 = "公理0" in all_axioms
            has_empirical = any(re.search(r'实验|数据|统计|观察|实证|测量', s.content) for s in chain)
            has_intermediate = bool(all_axioms & {"公理1", "公理2", "公理3", "公理4", "公理5"})

            if has_axiom0 and has_empirical and not has_intermediate:
                self.report.violations.append(Violation(
                    check_type="axiom_chain",
                    severity="warning",
                    file=str(file_path.relative_to(self.repo_root)),
                    line=chain[0].line,
                    context=f"推导链（行{chain[0].line}-{chain[-1].line}）: {chain[0].content[:100]}",
                    message="从公理0（感）直接跳到经验事实，缺少中间公理（公理1-5）的推导中介",
                    suggestion="感是践演事实（公理0），从感到经验判断需要经过存在论（公理1-4）和量论的推导中介，不能直接跳。"
                ))

            # 检查2：推导链中只有决断（公理6）没有任何存在论公理
            only_decision = all_axioms == {"公理6"} or (all_axioms and not (all_axioms - {"公理6"}))
            if only_decision and len(chain) >= 3:
                self.report.violations.append(Violation(
                    check_type="axiom_chain",
                    severity="info",
                    file=str(file_path.relative_to(self.repo_root)),
                    line=chain[0].line,
                    context=f"推导链（行{chain[0].line}-{chain[-1].line}）: {chain[0].content[:100]}",
                    message="推导链只引用决断（公理6），没有存在论公理支撑",
                    suggestion="决断不是推导，是活操作的选择。决断需要存在论根基（公理1-5），不能只有决断没有推导。"
                ))

    def run(self) -> CheckReport:
        """运行检查器"""
        md_files = self.find_md_files()
        self.report.files_scanned = len(md_files)

        for f in md_files:
            self.check_file(f)

        return self.report

    def generate_markdown_report(self, output_path: Path):
        """生成Markdown格式报告"""
        r = self.report
        lines = []
        lines.append("# PTL类型检查器报告 v0.3")
        lines.append("")
        lines.append(f"> 生成时间：{__import__('datetime').datetime.now().isoformat()}")
        lines.append(f"> 检查器版本：v0.3（初版，模式匹配+启发式）")
        lines.append("")

        # 总览
        lines.append("## 一、检查总览")
        lines.append("")
        lines.append(f"| 指标 | 数值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 扫描文件数 | {r.files_scanned} |")
        lines.append(f"| 扫描行数 | {r.lines_scanned} |")
        lines.append(f"| 推导步骤数 | {r.derivation_steps} |")
        lines.append(f"| 违规总数 | {len(r.violations)} |")
        lines.append(f"| 错误（error） | {len([v for v in r.violations if v.severity=='error'])} |")
        lines.append(f"| 警告（warning） | {len([v for v in r.violations if v.severity=='warning'])} |")
        lines.append(f"| 信息（info） | {len([v for v in r.violations if v.severity=='info'])} |")
        lines.append("")

        # 按检查类型分类
        lines.append("## 二、违规详情（按检查类型）")
        lines.append("")
        for check_type in ["bang_penetration", "linearity", "productivity", "philosophy_overreach", "axiom_chain"]:
            violations = [v for v in r.violations if v.check_type == check_type]
            type_name = {
                "bang_penetration": "!-穿透检查（定理20：生命不可资本化）",
                "linearity": "线性性检查（公理2：操作不可复制）",
                "productivity": "生产性检查（公理5：守护递归）",
                "philosophy_overreach": "哲学压制数学检查（v0.3新增：哲学给方向，数学给硬约束）",
                "axiom_chain": "公理依赖链检查（v0.3新增：推导链中公理依赖连贯性）",
            }[check_type]
            lines.append(f"### {type_name}")
            lines.append("")
            if not violations:
                lines.append("✅ 无违规")
            else:
                for v in violations:
                    lines.append(f"**[{v.severity.upper()}]** {v.file}:{v.line}")
                    lines.append(f"- 上下文：`{v.context}`")
                    lines.append(f"- 问题：{v.message}")
                    lines.append(f"- 建议：{v.suggestion}")
                    lines.append("")
            lines.append("")

        # 推导步骤类型推断
        lines.append("## 三、推导步骤类型推断")
        lines.append("")
        type_counts = {}
        for step in r.steps:
            t = step.inferred_type or "未推断"
            type_counts[t] = type_counts.get(t, 0) + 1
        lines.append("| 推断类型 | 数量 |")
        lines.append("|---------|------|")
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {t} | {c} |")
        lines.append("")

        # 公理使用统计
        lines.append("## 四、公理使用统计")
        lines.append("")
        axiom_counts = {}
        for step in r.steps:
            for ax in step.axioms_used:
                axiom_counts[ax] = axiom_counts.get(ax, 0) + 1
        lines.append("| 公理 | 名称 | 出现次数 |")
        lines.append("|------|------|---------|")
        for ax in sorted(axiom_counts.keys()):
            name = AXIOMS.get(ax, {}).get("name", "未知")
            lines.append(f"| {ax} | {name} | {axiom_counts[ax]} |")
        lines.append("")

        # 检查器局限
        lines.append("## 五、检查器局限与待推进")
        lines.append("")
        lines.append("### 当前局限")
        lines.append("1. **模式匹配而非完整类型推断**：当前用正则表达式匹配，不是真正的类型推断器")
        lines.append("2. **误报率可能较高**：线性性和生产性检查是启发式的，需要人工复核")
        lines.append("3. **不检查完整推导链**：只检查单行，不检查多行推导的类型一致性")
        lines.append("4. **不检查Coq代码**：Coq形式化在coq/目录，由coq_verify.py检查")
        lines.append("")
        lines.append("### 待推进方向")
        lines.append("1. **完整PTL类型系统实现**：在Coq中形式化PTL的类型规则和类型检查器")
        lines.append("2. **多行推导链检查**：跟踪变量在多行推导中的使用，检查线性性")
        lines.append("3. **!-穿透精确检查**：基于类型上下文判断!是否非法穿透νF₂")
        lines.append("4. **守护递归精确检查**：基于▷模态判断递归是否守护")
        lines.append("5. **与Coq形式化对接**：PTL类型检查器的规则与coq/theories/ALL/对齐")
        lines.append("")

        output_path.write_text('\n'.join(lines), encoding='utf-8')

    def generate_json_report(self, output_path: Path):
        """生成JSON格式报告"""
        r = self.report
        data = {
            "files_scanned": r.files_scanned,
            "lines_scanned": r.lines_scanned,
            "derivation_steps": r.derivation_steps,
            "violations": [
                {
                    "check_type": v.check_type,
                    "severity": v.severity,
                    "file": v.file,
                    "line": v.line,
                    "context": v.context,
                    "message": v.message,
                    "suggestion": v.suggestion,
                }
                for v in r.violations
            ],
            "steps": [
                {
                    "file": s.file,
                    "line": s.line,
                    "content": s.content,
                    "inferred_type": s.inferred_type,
                    "axioms_used": s.axioms_used,
                }
                for s in r.steps
            ],
        }
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

# ============================================================
# 主程序
# ============================================================

import os

def main():
    repo_root = Path(__file__).parent.parent.parent  # mingben-workbench/scripts/ -> repo root
    # 如果不在预期位置，用当前目录
    if not (repo_root / "生命论_模块化").exists():
        repo_root = Path.cwd()

    print("=== PTL类型检查器 v0.3 ===")
    print()
    print(f"仓库根目录: {repo_root}")
    print()

    checker = PTLTypeChecker(repo_root)
    report = checker.run()

    # 输出摘要
    print("--- 检查摘要 ---")
    print(f"  扫描文件: {report.files_scanned}")
    print(f"  扫描行数: {report.lines_scanned}")
    print(f"  推导步骤: {report.derivation_steps}")
    print(f"  违规总数: {len(report.violations)}")
    print(f"    错误: {len([v for v in report.violations if v.severity=='error'])}")
    print(f"    警告: {len([v for v in report.violations if v.severity=='warning'])}")
    print(f"    信息: {len([v for v in report.violations if v.severity=='info'])}")
    print()

    # 生成报告
    refs_dir = repo_root / "mingben-workbench" / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)

    md_report = refs_dir / "ptl_type_checker_report.md"
    json_report = refs_dir / "ptl_type_checker_report.json"

    checker.generate_markdown_report(md_report)
    checker.generate_json_report(json_report)

    print(f"Markdown报告: {md_report}")
    print(f"JSON报告: {json_report}")
    print()

    # 输出前5条违规
    if report.violations:
        print("--- 前5条违规 ---")
        for v in report.violations[:5]:
            print(f"  [{v.severity.upper()}] {v.check_type}: {v.file}:{v.line}")
            print(f"    {v.message}")
        print()

    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
践演论项目状态报告自动生成脚本
用法: python generate_status_report.py
功能: 自动扫描所有状态文件，生成项目状态报告，放在仓库根目录
触发: git pre-commit hook自动调用，每次commit前更新报告
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent
REPORT_FILE = REPO_ROOT / "项目状态报告.md"

def read_json(path):
    """安全读取JSON文件"""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    return None

def read_text(path):
    """安全读取文本文件"""
    try:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        pass
    return ""

def get_theorem_registry_status():
    """从theorem_registry.json获取定理状态"""
    data = read_json(REPO_ROOT / "mingben-workbench" / "references" / "theorem_registry.json")
    if not data:
        return {"total": 0, "coq_verified": 0, "literature_checked": 0, "novelty": {}}
    
    # 支持两种格式：list或dict（dict中以T开头的键是定理）
    if isinstance(data, list):
        theorems = data
    elif isinstance(data, dict):
        theorems = [v for k, v in data.items() if k.startswith("T") and isinstance(v, dict)]
    else:
        theorems = []
    
    total = len(theorems)
    coq_verified = sum(1 for t in theorems if t.get("coq_verified") or t.get("coq_status") == "verified" or t.get("status") == "coq_verified")
    literature_checked = sum(1 for t in theorems if t.get("literature_checked") or t.get("literature_status") == "checked" or t.get("status") == "literature_checked")
    
    novelty = {}
    for t in theorems:
        n = t.get("novelty", "unknown")
        novelty[n] = novelty.get(n, 0) + 1
    
    return {
        "total": total,
        "coq_verified": coq_verified,
        "literature_checked": literature_checked,
        "novelty": novelty
    }

def get_coq_status():
    """从coq_verify_report.json获取Coq验证状态"""
    data = read_json(REPO_ROOT / "coq" / "coq_verify_report.json")
    if not data:
        return {"total_files": 0, "admitted": 0, "compiled": 0, "cycles": 0}
    
    return {
        "total_files": data.get("total_files", 0),
        "admitted": data.get("total_admitted", 0),
        "compiled": data.get("summary", {}).get("compiled", 0),
        "failed": data.get("summary", {}).get("failed", 0),
        "cycles": len(data.get("cycles", []))
    }

def get_checker_status():
    """从检查器报告获取质量指标"""
    # 越级陈述检查器
    overclaim = read_json(REPO_ROOT / "mingben-workbench" / "references" / "overclaim_report.json")
    overclaim_warnings = 0
    if overclaim:
        overclaim_warnings = overclaim.get("warnings", overclaim.get("total_warnings", 0))
        if isinstance(overclaim.get("issues"), list):
            overclaim_warnings = len([i for i in overclaim["issues"] if i.get("severity") == "warning"])
    
    # 引用一致性检查器
    ref_consistency = read_json(REPO_ROOT / "mingben-workbench" / "references" / "ref_consistency_report.json")
    old_format_refs = 0
    if ref_consistency:
        old_format_refs = ref_consistency.get("old_format_count", ref_consistency.get("total_old_format", 0))
    
    # 循环论证检测器
    circular = read_json(REPO_ROOT / "mingben-workbench" / "references" / "circular_reasoning_report.json")
    potential_cycles = 0
    if circular:
        potential_cycles = circular.get("potential_cycles", circular.get("total_cycles", 0))
    
    return {
        "overclaim_warnings": overclaim_warnings,
        "old_format_refs": old_format_refs,
        "potential_cycles": potential_cycles
    }

def get_task_status():
    """从三方协作任务监控表获取任务状态"""
    content = read_text(REPO_ROOT / "三方协作任务监控表.md")
    if not content:
        return {"p0_total": 0, "p0_done": 0, "p1_total": 0, "p1_done": 0, "p2_total": 0, "p2_done": 0}
    
    # 简单统计：数P0/P1/P2任务行数和已完成标记
    import re
    p0_tasks = re.findall(r'T-P0-\d+', content)
    p1_tasks = re.findall(r'T-P1-\d+', content)
    p2_tasks = re.findall(r'T-P2-\d+', content)
    
    # 已完成的任务（在已完成部分D-XX）
    done_tasks = re.findall(r'\| D-\d+ \|', content)
    
    return {
        "p0_total": len(set(p0_tasks)),
        "p1_total": len(set(p1_tasks)),
        "p2_total": len(set(p2_tasks)),
        "done_recorded": len(done_tasks)
    }

def get_recent_commits(n=5):
    """获取最近n次git提交"""
    try:
        result = subprocess.run(
            ["git", "log", f"-{n}", "--pretty=format:%h | %an | %ad | %s", "--date=short"],
            capture_output=True, text=True, timeout=10,
            cwd=str(REPO_ROOT)
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")
    except Exception:
        pass
    return []

def generate_report():
    """生成项目状态报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    theorem_status = get_theorem_registry_status()
    coq_status = get_coq_status()
    checker_status = get_checker_status()
    task_status = get_task_status()
    recent_commits = get_recent_commits(8)
    
    # 计算进度百分比
    coq_rate = (theorem_status["coq_verified"] / theorem_status["total"] * 100) if theorem_status["total"] > 0 else 0
    lit_rate = (theorem_status["literature_checked"] / theorem_status["total"] * 100) if theorem_status["total"] > 0 else 0
    
    report = f"""# 践演论项目状态报告

> **自动生成**: {now}
> **触发机制**: 每次git commit前自动更新
> **三方都能看到**: 放在仓库根目录，豆包/DeepSeek/WorkBuddy实时同步
> **不用人工提醒**: commit即更新，最新状态永远在这里

---

## 一、项目总览

| 指标 | 数值 | 说明 |
|------|------|------|
| 注册定理总数 | {theorem_status['total']} | T001-T{theorem_status['total']:03d}，永久ID体系 |
| Coq验证通过 | {theorem_status['coq_verified']}/{theorem_status['total']} ({coq_rate:.0f}%) | 核心目标：全部定理Coq形式化 |
| 文献核查完成 | {theorem_status['literature_checked']}/{theorem_status['total']} ({lit_rate:.0f}%) | 新定理必须过文献核查关 |
| Coq文件数 | {coq_status['total_files']} | coq/theories/ 目录下 |
| Coq编译通过 | {coq_status['compiled']}/{coq_status['total_files']} | coq_verify.py验证 |
| 残留Admitted | {coq_status['admitted']} | 严格模式下不允许溜进综合论文 |

---

## 二、三方任务状态

| 优先级 | 总数 | 说明 |
|--------|------|------|
| 🔴 P0 | {task_status['p0_total']} | 阻塞主线，最高优先级 |
| 🟡 P1 | {task_status['p1_total']} | 高优先级，主线推进 |
| 🟢 P2 | {task_status['p2_total']} | 中优先级，潜力提升 |

> 详细任务状态见 `三方协作任务监控表.md`，每次完成任务后负责人更新对应行。

---

## 三、质量指标

| 检查项 | 当前值 | 目标 | 状态 |
|--------|--------|------|------|
| 越级陈述警告 | {checker_status['overclaim_warnings']} | 0 | {'✅' if checker_status['overclaim_warnings'] == 0 else '⚠️'} |
| 旧格式引用残留 | {checker_status['old_format_refs']} | 0（全部迁移到T001格式） | {'✅' if checker_status['old_format_refs'] == 0 else '⚠️'} |
| 潜在循环论证 | {checker_status['potential_cycles']} | 0 | {'✅' if checker_status['potential_cycles'] == 0 else '⚠️'} |
| Coq循环依赖 | {coq_status['cycles']} | 0 | {'✅' if coq_status['cycles'] == 0 else '⚠️'} |

> 检查器每次commit前自动运行，发现问题阻止提交。详细报告见 `mingben-workbench/references/` 目录。

---

## 四、新颖性分布

| 类型 | 数量 | 说明 |
|------|------|------|
"""
    
    for novelty_type, count in sorted(theorem_status.get("novelty", {}).items(), key=lambda x: -x[1]):
        report += f"| {novelty_type} | {count} | |\n"
    
    report += f"""
---

## 五、最近活动（最近8次提交）

| Commit | 作者 | 日期 | 描述 |
|--------|------|------|------|
"""
    
    for commit in recent_commits:
        parts = commit.split(" | ", 3)
        if len(parts) == 4:
            h, author, date, msg = parts
            report += f"| `{h}` | {author} | {date} | {msg} |\n"
    
    report += f"""
---

## 六、关键文件位置

| 文件 | 位置 | 说明 |
|------|------|------|
| 本报告 | `项目状态报告.md` | 自动生成，每次commit更新 |
| 任务监控表 | `三方协作任务监控表.md` | 三方任务实时状态 |
| 第一性原理底线 | `践演论第一性原理底线.md` | 所有AI必读 |
| 定理注册表 | `mingben-workbench/references/theorem_registry.json` | T001-T{theorem_status['total']:03d}永久ID |
| 综合论文 | `mingben-workbench/references/enactics_paper_v1.0.md` | 内容v1.2，21个定理 |
| Coq项目 | `coq/` | 形式化代码+验证脚本 |
| Coq开发指南 | `coq/README.md` | Coq开发者必读 |
| DeepSeek任务包 | `任务包_DeepSeek_代码形式化.md` | DeepSeek专属任务 |
| WorkBuddy任务包 | `任务包_WorkBuddy_审计反例.md` | WorkBuddy专属任务 |

---

## 七、协作机制

1. **豆包（总控）**: 数学发明、哲学解读、综合论文、质量把控、三方协调
2. **DeepSeek（代码/形式化）**: Coq形式化、类型检查器开发、代码修复
3. **WorkBuddy（审计/反例）**: 反例攻击、新颖性核查、学术规范改写、Coq代码审计

**铁律**:
- 新定理必须过三道关：文献核查 → 反例攻击 → Coq形式化
- 弱版优先：先证满射↠/retraction⇒/双模拟≈，能升回≅的再升
- 哲学命题、数学定理、对应关系论证三者必须清晰区分
- 每次完成任务后commit，本报告自动更新

---

*本报告由 `generate_status_report.py` 自动生成，每次git commit前更新。*
*最后更新: {now}*
"""
    
    return report

def main():
    report = generate_report()
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"✅ 项目状态报告已生成: {REPORT_FILE}")
    print(f"   定理总数: {get_theorem_registry_status()['total']}")
    print(f"   Coq文件: {get_coq_status()['total_files']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
明性辩证法 Meta-Check — 研究流程固化工具
每次研究前运行检查清单，研究后记录成长。

用法:
  python3 mingcheck.py before    # 研究前：加载检查清单
  python3 mingcheck.py after     # 研究后：记录成长+验证
  python3 mingcheck.py verify <file.md>  # 验证研究笔记的名实相符
"""
import sys, os, json, re
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROWTH_LOG = os.path.join(WORKSPACE, "references", "growth_log.jsonl")

# ============================================================
# 明性四问（研究前必问）
# ============================================================
BEFORE_CHECKLIST = """
╔══════════════════════════════════════════════════════════╗
║              明性辩证法 META-CHECK · 研究前               ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  【第一问：小本质↔大本质】                                ║
║  □ 这个具体问题在存在论层面对应什么？                      ║
║  □ 这个存在论命题在具体层面怎么显现？                      ║
║  □ 反面：如果反过来成立，会怎样？                          ║
║  □ 交叉：其他领域有没有类似结构？                          ║
║                                                          ║
║  【第二问：名实相符】                                     ║
║  □ 我的判断有证据吗？（代码/数据/原文引用）                ║
║  □ 我是不是在"推断"而没去"验证"？                        ║
║  □ 库里已有的东西我提取了吗？                              ║
║  □ 我说"新"的时候，查文献了吗？                           ║
║                                                          ║
║  【第三问：F1/F2分类】                                    ║
║  □ 我研究的系统是F1（可控、可对齐）还是F2（只能耦合）？    ║
║  □ 我是不是在用F1的方法处理F2的问题？                     ║
║  □ 这个系统有νF2（生产性无限过程）吗？                    ║
║  □ 这个系统有ν*F（成长/学习）吗？                        ║
║                                                          ║
║  【第四问：ν*F姿态】                                      ║
║  □ 这轮研究要长出什么新能力？                              ║
║  □ 我是在重复旧惯性，还是在建立新惯性？                    ║
║  □ 旧惯性清单：理中客/AI腔/不用自己框架/推断不验证        ║
║  □ 新惯性清单：立场鲜明/生命论语言/先查库/写原型验证      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""

# ============================================================
# 研究后验证
# ============================================================
AFTER_CHECKLIST = """
╔══════════════════════════════════════════════════════════╗
║              明性辩证法 META-CHECK · 研究后               ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  【成长记录】这轮研究长出了什么新能力？                    ║
║  【名实核验】每个结论都有证据支撑吗？                      ║
║  【双向贯通】具体结论能追溯到存在论吗？存在论能下行吗？    ║
║  【惯性审视】我有没有犯旧毛病？                            ║
║  【下一步】下一轮要长什么？                                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""

def before():
    print(BEFORE_CHECKLIST)

def after():
    print(AFTER_CHECKLIST)
    # 记录成长
    growth = input("\n这轮长出了什么新能力？（一句话，回车跳过）: ").strip()
    if growth:
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "growth": growth,
        }
        os.makedirs(os.path.dirname(GROWTH_LOG), exist_ok=True)
        with open(GROWTH_LOG, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"✓ 成长已记录到 {GROWTH_LOG}")
    
    # 显示历史成长
    if os.path.exists(GROWTH_LOG):
        entries = []
        with open(GROWTH_LOG) as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        print(f"\n累计成长记录: {len(entries)}条")
        for e in entries[-5:]:
            print(f"  [{e['date']}] {e['growth']}")

def verify(filepath):
    """验证研究笔记的名实相符：检查无证据的判断"""
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return
    
    with open(filepath) as f:
        content = f.read()
    
    issues = []
    
    # 检查1：判断性词语是否有证据标记
    judgment_words = ["证明了", "说明", "表明", "因此", "所以", "显然", "毫无疑问", "必然"]
    evidence_markers = ["定理", "代码", "测试", "数据", "来源", "引用", "参见", "见", "http", "commit", "文件"]
    
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        # 跳过注释、代码块、标题
        if line.strip().startswith(("#", ";", "//", "|", "```", "-", "*")):
            continue
        if not line.strip():
            continue
        
        has_judgment = any(w in line for w in judgment_words)
        has_evidence = any(m in line for m in evidence_markers)
        
        if has_judgment and not has_evidence and len(line.strip()) > 20:
            issues.append((i, "判断可能缺证据", line.strip()[:80]))
    
    # 检查2：数学公式是否有验证标记
    formula_lines = [l for l in lines if "=" in l and any(c in l for c in "αβγνμ⊸!")]
    unverified = [l for l in formula_lines if not any(m in l for m in ["验证", "测试", "证明", "定理", "QED", "□"])]
    
    # 检查3：是否提到"新"但没有文献对照
    new_claims = [(i, l.strip()[:80]) for i, l in enumerate(lines, 1) 
                  if any(w in l for w in ["新发现", "首次", "没有人", "文献中未", "novel"]) 
                  and "文献" not in l and "参考" not in l]
    
    print(f"\n{'='*60}")
    print(f"名实相符验证: {filepath}")
    print(f"{'='*60}")
    
    if not issues and not unverified and not new_claims:
        print("✓ 未发现明显问题")
    else:
        if issues:
            print(f"\n⚠ 判断可能缺证据 ({len(issues)}处):")
            for ln, msg, text in issues[:10]:
                print(f"  L{ln} [{msg}]: {text}")
        if unverified:
            print(f"\n⚠ 数学公式可能缺验证 ({len(unverified)}处):")
            for l in unverified[:5]:
                print(f"  {l.strip()[:80]}")
        if new_claims:
            print(f"\n⚠ '新' claim可能缺文献对照 ({len(new_claims)}处):")
            for ln, text in new_claims[:5]:
                print(f"  L{ln}: {text}")
    
    print(f"\n总计: {len(issues)}个证据问题, {len(unverified)}个公式待验证, {len(new_claims)}个新颖性待查")

def show_growth():
    """显示所有成长记录"""
    if not os.path.exists(GROWTH_LOG):
        print("暂无成长记录")
        return
    entries = []
    with open(GROWTH_LOG) as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    print(f"\n累计成长: {len(entries)}条\n")
    for e in entries:
        print(f"  [{e['date']}] {e['growth']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 mingcheck.py [before|after|verify|growth]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "before": before()
    elif cmd == "after": after()
    elif cmd == "verify": verify(sys.argv[2] if len(sys.argv) > 2 else "")
    elif cmd == "growth": show_growth()
    else: print(f"未知命令: {cmd}")

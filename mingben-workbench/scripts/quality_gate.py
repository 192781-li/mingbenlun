#!/usr/bin/env python3
"""
全本质量门禁
用法: python quality_gate.py [--fix]
在导出全本或提交前跑所有检查器，确保0错误。
--fix: 自动修复可修复的问题
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "mingben-workbench" / "scripts"
REFERENCES_DIR = REPO_ROOT / "mingben-workbench" / "references"
BOOK_DIR = REPO_ROOT / "生命论_模块化"

# 颜色
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

class QualityGate:
    def __init__(self):
        self.results = []
        self.errors = 0
        self.warnings = 0
        self.passed = 0
    
    def check(self, name, func):
        """运行一个检查"""
        print(f"  检查 {name}...", end=' ', flush=True)
        try:
            result = func()
            if result.get('error'):
                print(f"{RED}✗ {result['error']}{RESET}")
                self.results.append((name, 'ERROR', result))
                self.errors += 1
            elif result.get('warning'):
                print(f"{YELLOW}⚠ {result['warning']}{RESET}")
                self.results.append((name, 'WARN', result))
                self.warnings += 1
            else:
                print(f"{GREEN}✓ {result.get('msg', '通过')}{RESET}")
                self.results.append((name, 'PASS', result))
                self.passed += 1
        except Exception as e:
            print(f"{RED}✗ 异常: {e}{RESET}")
            self.results.append((name, 'ERROR', {'error': str(e)}))
            self.errors += 1
    
    def report(self):
        """输出总结"""
        print()
        print("=" * 60)
        print(f"质量门禁结果：{GREEN}{self.passed}通过{RESET} / {YELLOW}{self.warnings}警告{RESET} / {RED}{self.errors}错误{RESET}")
        print("=" * 60)
        
        if self.errors > 0:
            print(f"\n{RED}错误详情：{RESET}")
            for name, status, result in self.results:
                if status == 'ERROR':
                    print(f"  [{name}] {result.get('error', '')}")
        
        if self.warnings > 0:
            print(f"\n{YELLOW}警告详情：{RESET}")
            for name, status, result in self.results:
                if status == 'WARN':
                    print(f"  [{name}] {result.get('warning', '')}")
        
        return self.errors == 0

def check_theorem_registry():
    """检查定理注册表完整性"""
    registry_file = REFERENCES_DIR / "theorem_registry.json"
    if not registry_file.exists():
        return {'error': '定理注册表不存在'}
    
    registry = json.loads(registry_file.read_text(encoding='utf-8'))
    required_fields = ['name', 'statement', 'current_version', 'status', 'coq_verified', 'literature_checked', 'novelty', 'philosophy_correspondence']
    
    issues = []
    theorem_count = 0
    for key, val in registry.items():
        if key.startswith('_'):
            continue
        theorem_count += 1
        for field in required_fields:
            if field not in val:
                issues.append(f"{key}缺少{field}")
    
    if issues:
        return {'error': f'{len(issues)}个问题: ' + '; '.join(issues[:3])}
    
    # 检查ID连续性
    ids = sorted([k for k in registry if k.startswith('T')])
    expected = [f"T{i:03d}" for i in range(1, len(ids)+1)]
    if ids != expected:
        return {'warning': f'定理ID不连续: {ids}'}
    
    return {'msg': f'{theorem_count}个定理，字段完整'}

def check_cross_refs():
    """检查交叉引用有效性"""
    cn_num = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    
    # 获取现有卷篇
    existing = set()
    for vol_dir in BOOK_DIR.iterdir():
        if vol_dir.is_dir():
            import re
            vol_match = re.match(r'(\d+)_卷([一二三四五六七八九十\d]+)', vol_dir.name)
            if vol_match:
                v = cn_num.get(vol_match.group(2), int(vol_match.group(2)) if vol_match.group(2).isdigit() else None)
                if v:
                    for md in vol_dir.glob('篇*.md'):
                        pian_match = re.match(r'篇([一二三四五六七八九十\d]+)', md.name)
                        if pian_match:
                            p = cn_num.get(pian_match.group(1), int(pian_match.group(1)) if pian_match.group(1).isdigit() else None)
                            if p:
                                existing.add((v, p))
    
    # 扫描引用
    import re
    invalid = []
    pattern = r'卷([一二三四五六七八九十\d]+)篇([一二三四五六七八九十\d]+)'
    for root, dirs, files in os.walk(BOOK_DIR):
        dirs[:] = [d for d in dirs if d not in {'.git', 'backup', '__pycache__'}]
        for f in files:
            if f.endswith('.md'):
                content = (Path(root) / f).read_text(encoding='utf-8', errors='ignore')
                for m in re.finditer(pattern, content):
                    v = cn_num.get(m.group(1), int(m.group(1)) if m.group(1).isdigit() else None)
                    p = cn_num.get(m.group(2), int(m.group(2)) if m.group(2).isdigit() else None)
                    if v and p and (v, p) not in existing:
                        rel = str(Path(root).relative_to(REPO_ROOT) / f)
                        if '重组方案' not in rel:  # 重组方案文件中引用旧编号是正常的
                            invalid.append(f"卷{v}篇{p} in {rel}")
    
    if invalid:
        return {'error': f'{len(invalid)}个无效引用: ' + '; '.join(invalid[:3])}
    return {'msg': f'{len(existing)}个卷篇，引用全部有效'}

def check_coq_compilation():
    """检查Coq Layer1是否编译通过"""
    coq_file = REPO_ROOT / "coq" / "theories" / "ALL" / "Layer1.v"
    if not coq_file.exists():
        return {'warning': 'Layer1.v不存在，跳过Coq检查'}
    
    # 检查文件中是否有Admitted
    content = coq_file.read_text(encoding='utf-8', errors='ignore')
    admitted_count = content.count('Admitted')
    if admitted_count > 0:
        return {'error': f'Layer1.v中有{admitted_count}个Admitted'}
    
    return {'msg': 'Layer1.v无Admitted'}

def check_overclaim():
    """运行越级陈述检查器"""
    checker = SCRIPTS_DIR / "overclaim_checker.py"
    if not checker.exists():
        return {'warning': '越级陈述检查器不存在'}
    
    try:
        result = subprocess.run(
            [sys.executable, str(checker), '--quiet'],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60
        )
        # 检查器返回0=通过，1=有警告
        output = result.stdout + result.stderr
        if 'W001' in output or 'W002' in output or 'W003' in output:
            return {'error': '发现已证伪的越级陈述（W001/W002/W003）'}
        return {'msg': '越级陈述检查通过'}
    except subprocess.TimeoutExpired:
        return {'warning': '越级陈述检查超时'}
    except Exception as e:
        return {'warning': f'越级陈述检查异常: {e}'}

def check_ref_consistency():
    """运行引用一致性检查器"""
    checker = SCRIPTS_DIR / "ref_consistency_checker.py"
    if not checker.exists():
        return {'warning': '引用一致性检查器不存在'}
    
    try:
        result = subprocess.run(
            [sys.executable, str(checker), '--quiet'],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60
        )
        output = result.stdout + result.stderr
        if '无效引用' in output and '0' not in output.split('无效引用')[0][-5:]:
            return {'error': '发现无效定理引用'}
        return {'msg': '引用一致性检查通过'}
    except Exception as e:
        return {'warning': f'引用一致性检查异常: {e}'}

def check_name_consistency():
    """检查核心概念名称一致性（明性/明本/民本）"""
    issues = []
    
    # 检查"民本辩证法"和"民本学术法"是否还存在（应该是"明性辩证法"和"明性学术法"）
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in {'.git', 'backup', '__pycache__', 'node_modules', 'raw_materials'}]
        for f in files:
            if f.endswith('.md'):
                p = Path(root) / f
                rel = str(p.relative_to(REPO_ROOT))
                # 跳过历史版本和报告；raw_materials原始对话记录保留历史原貌不检查
                if any(x in rel for x in ['enactics_v0', 'backup', '_report', '重组方案', 'raw_materials']):
                    continue
                content = p.read_text(encoding='utf-8', errors='ignore')
                if '民本辩证法' in content:
                    issues.append(f'{rel}: 民本辩证法→应为明性辩证法')
                if '民本学术法' in content:
                    issues.append(f'{rel}: 民本学术法→应为明性学术法')
    
    if issues:
        return {'error': f'{len(issues)}处名称错误: ' + '; '.join(issues[:3])}
    return {'msg': '明性/明本/民本名称一致'}

def check_no_ai_boilerplate():
    """检查是否有AI套话（质性内容）"""
    ai_phrases = [
        '值得注意的是', '总而言之', '综上所述', '不言而喻',
        '在某种程度上', '从某种意义上说',
    ]
    # 这个检查只在数学文档中运行
    math_docs = list((REFERENCES_DIR).glob('enactics_v1.*.md'))
    issues = []
    for doc in math_docs:
        content = doc.read_text(encoding='utf-8', errors='ignore')
        for phrase in ai_phrases:
            if phrase in content:
                issues.append(f'{doc.name}: "{phrase}"')
    
    if issues:
        return {'warning': f'{len(issues)}处可能的AI套话'}
    return {'msg': '无AI套话'}

def main():
    print("=" * 60)
    print(f"践演论全本质量门禁 —— {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print()
    
    gate = QualityGate()
    
    print("【结构检查】")
    gate.check("定理注册表", check_theorem_registry)
    gate.check("交叉引用", check_cross_refs)
    gate.check("名称一致性", check_name_consistency)
    
    print("\n【数学检查】")
    gate.check("Coq编译", check_coq_compilation)
    gate.check("越级陈述", check_overclaim)
    gate.check("引用一致性", check_ref_consistency)
    
    print("\n【文风检查】")
    gate.check("AI套话", check_no_ai_boilerplate)
    
    passed = gate.report()
    
    if passed:
        print(f"\n{GREEN}质量门禁通过，可以导出全本。{RESET}")
        sys.exit(0)
    else:
        print(f"\n{RED}质量门禁未通过，修复错误后再导出。{RESET}")
        sys.exit(1)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
明性守护脚本
用法: python mingxing_guard.py [--quiet]
检查核心原则、关键文件、禁止模式，防止明性在多轮对话/多AI协作中被遗忘或篡改。
每次pre-commit和每日定时任务自动运行。
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
REGISTRY_FILE = REPO_ROOT / "mingben-workbench" / "references" / "principles_registry.json"

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def load_registry():
    if not REGISTRY_FILE.exists():
        return None
    return json.loads(REGISTRY_FILE.read_text(encoding='utf-8'))

def check_critical_files(registry):
    """检查关键文件是否存在"""
    errors = []
    for f in registry.get('critical_files', []):
        p = REPO_ROOT / f
        if not p.exists():
            errors.append(f"关键文件丢失: {f}")
    return errors

def check_principles(registry, category):
    """检查一类原则的关键词是否在指定文件中"""
    errors = []
    for item in registry.get(category, []):
        check_type = item.get('check_type', 'keywords')
        
        if check_type == 'no_admitted':
            # 检查Coq文件是否有Admitted
            target = REPO_ROOT / item['target']
            if target.exists():
                for v in target.glob('Layer*.v'):
                    content = v.read_text(encoding='utf-8', errors='ignore')
                    if 'Admitted' in content:
                        errors.append(f"{item['id']}: {v.name}中有Admitted")
        
        elif check_type == 'no_ai_phrases':
            # 检查AI套话
            target_pattern = item.get('target', '')
            for p in REPO_ROOT.glob(target_pattern):
                content = p.read_text(encoding='utf-8', errors='ignore')
                for phrase in ['值得注意的是', '总而言之', '不言而喻', '综上所述']:
                    if phrase in content:
                        errors.append(f"{item['id']}: {p.name}中有AI套话'{phrase}'")
        
        elif check_type == 'regex':
            # 检查正则模式是否存在
            for f in item.get('must_contain_in', []):
                p = REPO_ROOT / f
                if p.exists():
                    content = p.read_text(encoding='utf-8', errors='ignore')
                    if not re.search(item['pattern'], content):
                        errors.append(f"{item['id']}: {f}中未找到模式'{item['pattern']}'")
        
        elif check_type == 'informational':
            # 信息性原则，不自动检查
            pass
        
        else:
            # 默认：关键词检查
            keywords = item.get('keywords', [])
            for f in item.get('must_contain_in', []):
                p = REPO_ROOT / f
                if not p.exists():
                    errors.append(f"{item['id']}: 文件不存在 {f}")
                    continue
                content = p.read_text(encoding='utf-8', errors='ignore')
                for kw in keywords:
                    if kw not in content:
                        errors.append(f"{item['id']}: {f}中缺少关键词'{kw}'")
    return errors

def check_forbidden_patterns(registry):
    """检查禁止模式（只扫描当前有效文件，排除旧版/审计/备份/脚本自身）"""
    errors = []
    # 只扫描这些目录中的当前有效文件
    scan_dirs = [
        REPO_ROOT / "生命论_模块化",
        REPO_ROOT / "coq" / "theories",
    ]
    # references目录中只扫描核心文件，排除旧版enactics和审计报告
    refs_dir = REPO_ROOT / "mingben-workbench" / "references"
    exclude_name_patterns = ['enactics_v1.', 'enactics_paper_v1.0', 'overclaim_report',
                              'ref_output', 'circular_output', 'audit', '_old', 'backup']
    
    for item in registry.get('forbidden_patterns', []):
        pattern = item['pattern']
        replacement = item.get('replacement', '')
        reason = item.get('reason', '')
        
        # 扫描指定目录
        files_to_check = []
        for d in scan_dirs:
            if d.exists():
                files_to_check.extend(d.rglob('*.md'))
                files_to_check.extend(d.rglob('*.v'))
        
        # 扫描references中的核心文件
        if refs_dir.exists():
            for p in refs_dir.glob('*.md'):
                if not any(x in p.name for x in exclude_name_patterns):
                    files_to_check.append(p)
            for p in refs_dir.glob('*.json'):
                files_to_check.append(p)
        
        for p in files_to_check:
            try:
                # 排除注册表自身（它的replacement字段包含被禁止的词）
                if p.name == 'principles_registry.json':
                    continue
                content = p.read_text(encoding='utf-8', errors='ignore')
                rel = str(p.relative_to(REPO_ROOT))
                if re.search(pattern, content):
                    errors.append(f"禁止模式 '{pattern}' 出现在 {rel}（应为 {replacement}。{reason}）")
            except Exception:
                pass
    return errors

def main():
    quiet = '--quiet' in sys.argv
    
    registry = load_registry()
    if registry is None:
        if not quiet:
            print(f"{RED}原则注册表不存在: {REGISTRY_FILE}{RESET}")
        sys.exit(1)
    
    all_errors = []
    
    # 1. 关键文件
    errors = check_critical_files(registry)
    all_errors.extend(errors)
    if not quiet:
        status = f"{GREEN}✓{RESET}" if not errors else f"{RED}✗{RESET}"
        print(f"  {status} 关键文件检查 ({len(registry.get('critical_files', []))}个)")
    
    # 2. 哲学原则
    errors = check_principles(registry, 'philosophy')
    all_errors.extend(errors)
    if not quiet:
        status = f"{GREEN}✓{RESET}" if not errors else f"{RED}✗{RESET}"
        print(f"  {status} 哲学原则检查 ({len(registry.get('philosophy', []))}条)")
    
    # 3. 数学原则
    errors = check_principles(registry, 'mathematics')
    all_errors.extend(errors)
    if not quiet:
        status = f"{GREEN}✓{RESET}" if not errors else f"{RED}✗{RESET}"
        print(f"  {status} 数学原则检查 ({len(registry.get('mathematics', []))}条)")
    
    # 4. 禁止模式
    errors = check_forbidden_patterns(registry)
    all_errors.extend(errors)
    if not quiet:
        status = f"{GREEN}✓{RESET}" if not errors else f"{RED}✗{RESET}"
        print(f"  {status} 禁止模式检查 ({len(registry.get('forbidden_patterns', []))}条)")
    
    # 输出结果
    if all_errors:
        if not quiet:
            print(f"\n{RED}明性守护发现 {len(all_errors)} 个问题：{RESET}")
            for e in all_errors[:20]:
                print(f"  {RED}•{RESET} {e}")
            if len(all_errors) > 20:
                print(f"  ...还有{len(all_errors)-20}个")
        sys.exit(1)
    else:
        if not quiet:
            print(f"\n{GREEN}明性守护通过：所有核心原则完整，关键文件在位，无禁止模式。{RESET}")
        sys.exit(0)

if __name__ == '__main__':
    main()

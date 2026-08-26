#!/usr/bin/env python3
"""
项目状态秒查
用法: python project_status.py [--json]
快速输出项目当前状态，供对话开始时加载。
"""
import json
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent.parent
REFERENCES_DIR = REPO_ROOT / "mingben-workbench" / "references"
BOOK_DIR = REPO_ROOT / "生命论_模块化"

# Git路径（Windows PortableGit）
GIT_EXE = r"C:\Users\lison\Desktop\PortableGit\bin\git.exe"

def run_git(args):
    try:
        git_cmd = [GIT_EXE] if Path(GIT_EXE).exists() else ['git']
        r = subprocess.run(git_cmd + args, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10)
        return r.stdout.strip()
    except Exception:
        return ""

def get_theorem_status():
    reg_file = REFERENCES_DIR / "theorem_registry.json"
    if not reg_file.exists():
        return {}
    reg = json.loads(reg_file.read_text(encoding='utf-8'))
    theorems = {k: v for k, v in reg.items() if not k.startswith('_')}
    stats = {
        'total': len(theorems),
        'coq_verified': sum(1 for t in theorems.values() if t.get('coq_verified')),
        'literature_checked': sum(1 for t in theorems.values() if t.get('literature_checked')),
        'paper_proof': sum(1 for t in theorems.values() if t.get('status') == 'paper_proof'),
        'conjecture': sum(1 for t in theorems.values() if t.get('status') == 'conjecture'),
    }
    return stats

def get_book_structure():
    structure = {}
    if not BOOK_DIR.exists():
        return structure
    for vol_dir in sorted(BOOK_DIR.iterdir()):
        if vol_dir.is_dir() and '卷' in vol_dir.name:
            pian_count = len(list(vol_dir.glob('篇*.md')))
            structure[vol_dir.name] = pian_count
    return structure

def get_coq_status():
    coq_dir = REPO_ROOT / "coq" / "theories" / "ALL"
    if not coq_dir.exists():
        return {'layers': 0, 'admitted': 0}
    layers = list(coq_dir.glob('Layer*.v'))
    admitted = 0
    for layer in layers:
        content = layer.read_text(encoding='utf-8', errors='ignore')
        admitted += content.count('Admitted')
    return {'layers': len(layers), 'admitted': admitted}

def get_open_issues():
    """从进度文件提取最近的待办"""
    prog_file = REFERENCES_DIR / "formalization_progress.md"
    if not prog_file.exists():
        return []
    content = prog_file.read_text(encoding='utf-8', errors='ignore')
    # 找最后一个"下次从哪里继续"
    parts = content.split('下次从哪里继续')
    if len(parts) < 2:
        return []
    last = parts[-1]
    tasks = []
    for line in last.split('\n'):
        line = line.strip()
        if line.startswith(('- ', '1.', '2.', '3.', '4.', '5.')) and len(line) > 8:
            task = line.lstrip('- 1234567890.').strip()
            # 过滤掉产出文件行（以`开头）
            if not task.startswith('`'):
                tasks.append(task)
    return tasks[:8]

def get_checker_scripts():
    scripts_dir = REPO_ROOT / "mingben-workbench" / "scripts"
    if not scripts_dir.exists():
        return []
    checkers = []
    for f in scripts_dir.glob('*.py'):
        if any(x in f.name for x in ['check', 'verify', 'gate', 'detector']):
            checkers.append(f.name)
    return sorted(checkers)

def main():
    as_json = '--json' in sys.argv
    
    stats = get_theorem_status()
    book = get_book_structure()
    coq = get_coq_status()
    git_hash = run_git(['rev-parse', '--short', 'HEAD'])
    git_log = run_git(['log', '--oneline', '-3'])
    open_tasks = get_open_issues()
    checkers = get_checker_scripts()
    
    total_pian = sum(book.values())
    
    if as_json:
        result = {
            'timestamp': datetime.now().isoformat(),
            'git': {'hash': git_hash, 'recent': git_log},
            'theorems': stats,
            'book': {'volumes': len(book), 'pian': total_pian, 'detail': book},
            'coq': coq,
            'checkers': checkers,
            'open_tasks': open_tasks,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    
    print("=" * 55)
    print(f"践演论项目状态 —— {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 55)
    
    print(f"\n【Git】{git_hash}")
    for line in git_log.split('\n')[:3]:
        if line.strip():
            print(f"  {line.strip()}")
    
    print(f"\n【定理】{stats.get('total', 0)}个核心定理")
    print(f"  Coq验证: {stats.get('coq_verified', 0)}/{stats.get('total', 0)}")
    print(f"  文献核查: {stats.get('literature_checked', 0)}/{stats.get('total', 0)}")
    print(f"  纸面证明: {stats.get('paper_proof', 0)}  猜想: {stats.get('conjecture', 0)}")
    
    print(f"\n【全书】{len(book)}卷 {total_pian}篇")
    for vol, pian in book.items():
        print(f"  {vol}: {pian}篇")
    
    print(f"\n【Coq】{coq['layers']}层, {coq['admitted']}个Admitted")
    
    print(f"\n【检查器】{len(checkers)}个")
    for c in checkers:
        print(f"  {c}")
    
    if open_tasks:
        print(f"\n【待办】")
        for i, task in enumerate(open_tasks, 1):
            print(f"  {i}. {task}")
    
    print("\n" + "=" * 55)

if __name__ == '__main__':
    main()

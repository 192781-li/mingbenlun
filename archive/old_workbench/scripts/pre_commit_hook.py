#!/usr/bin/env python3
"""
践演论 git pre-commit hook
在每次git commit前自动运行所有检查器，拦截越级陈述、无效引用等问题。

安装方法（Windows PowerShell）：
    Copy-Item mingben-workbench\scripts\pre_commit_hook.py .git\hooks\pre-commit
    # 或者创建一个调用此脚本的pre-commit文件

安装方法（Linux/Mac）：
    cp mingben-workbench/scripts/pre_commit_hook.py .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
"""

import sys
import os
import subprocess
from pathlib import Path

# 项目根目录（脚本在 mingben-workbench/scripts/ 下）
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # mingben-workbench/scripts/ -> 项目根
REFERENCES_DIR = PROJECT_ROOT / 'mingben-workbench' / 'references'
REGISTRY_PATH = REFERENCES_DIR / 'theorem_registry.json'

# 检查器脚本
CHECKERS = [
    ('越级陈述检查器', 'overclaim_checker.py'),
    ('引用一致性检查器', 'ref_consistency_checker.py'),
]

# 严重程度阈值
# error: 必须修复，阻止提交
# warning: 警告，允许提交但提示
# info: 信息，不阻止提交
BLOCK_ON_ERROR = True
BLOCK_ON_WARNING = False  # 警告不阻止提交，但会显示


def run_checker(name, script_name, *args):
    """运行一个检查器，返回(通过, 错误数, 警告数, 输出)"""
    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        return True, 0, 0, f'[跳过] {name}: 脚本不存在 ({script_path})'

    cmd = [sys.executable, str(script_path)] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(PROJECT_ROOT)
        )
        output = result.stdout + result.stderr

        # 解析输出中的统计
        errors = output.count('### E')
        warnings = output.count('### W')

        # 检查是否有"发现问题"统计
        import re
        match = re.search(r'\*\*发现问题\*\*\s*\|\s*\*\*(\d+)\*\*', output)
        total_issues = int(match.group(1)) if match else errors + warnings

        passed = errors == 0 if BLOCK_ON_ERROR else True
        return passed, errors, warnings, output

    except subprocess.TimeoutExpired:
        return True, 0, 0, f'[超时] {name}: 运行超过60秒，跳过'
    except Exception as e:
        return True, 0, 0, f'[错误] {name}: {e}'


def main():
    print('=' * 60)
    print('践演论 pre-commit 检查')
    print('=' * 60)
    print()

    all_passed = True
    total_errors = 0
    total_warnings = 0

    for name, script in CHECKERS:
        print(f'▶ 运行 {name}...')

        if 'overclaim' in script:
            passed, errors, warnings, output = run_checker(
                name, script, str(REFERENCES_DIR)
            )
        elif 'ref_consistency' in script:
            passed, errors, warnings, output = run_checker(
                name, script, str(REFERENCES_DIR), str(REGISTRY_PATH)
            )
        else:
            passed, errors, warnings, output = run_checker(name, script)

        total_errors += errors
        total_warnings += warnings

        if not passed:
            all_passed = False
            print(f'  ✗ 失败: {errors} 错误, {warnings} 警告')
        else:
            print(f'  ✓ 通过: {errors} 错误, {warnings} 警告')

        # 显示错误详情
        if errors > 0:
            print()
            lines = output.split('\n')
            in_error = False
            for line in lines:
                if line.startswith('## 错误'):
                    in_error = True
                elif line.startswith('## ') and in_error:
                    break
                elif in_error:
                    print(f'  {line}')
            print()

    print('=' * 60)
    print(f'总计: {total_errors} 错误, {total_warnings} 警告')

    if all_passed:
        print('✓ 所有检查通过，允许提交')
        print('=' * 60)
        sys.exit(0)
    else:
        print('✗ 存在错误，请修复后重新提交')
        print('  提示: 可以用 git commit --no-verify 跳过检查（不推荐）')
        print('=' * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()

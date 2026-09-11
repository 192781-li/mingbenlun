#!/usr/bin/env python3
"""
明本统一CLI入口
================
整合生命论项目所有工具：构建、质检、自审、监控、答题训练、合并。

用法：
  python3 mingben.py build [--html-only|--pdf-only|--check]   构建
  python3 mingben.py audit [--quiet]                            自审
  python3 mingben.py quality <文件.md>                           质量门控
  python3 mingben.py monitor [--background] [--watch N]         监控
  python3 mingben.py merge <新文件.md> [--dry-run]              自动合并
  python3 mingben.py exam analyze <题目.md>                      答题三层分析
  python3 mingben.py exam practice <题目.md>                     三遍重写训练
  python3 mingben.py exam status                                  训练进度
  python3 mingben.py exam template                                生成题目模板
  python3 mingben.py sync ["提交信息"]                           构建+提交+推送
  python3 mingben.py status                                       项目总览
"""
import sys
import os
import subprocess
from pathlib import Path

# 路径锚定
SCRIPT_DIR = Path(__file__).parent
WORKSPACE = SCRIPT_DIR.parent
MODDIR = WORKSPACE / "生命论_模块化"
SCRIPTS = SCRIPT_DIR / "scripts"


def run_cmd(cmd, cwd=None):
    """运行命令并实时输出。"""
    return subprocess.run(cmd, cwd=cwd or str(WORKSPACE))


def cmd_build(args):
    """构建生命论。"""
    build_sh = MODDIR / "build.sh"
    cmd = ['bash', str(build_sh)] + args
    return run_cmd(cmd).returncode


def cmd_audit(args):
    """自审。"""
    script = SCRIPTS / "self_audit.py"
    cmd = [sys.executable, str(script)] + args
    return run_cmd(cmd).returncode


def cmd_quality(args):
    """质量门控。"""
    if not args:
        print("用法：mingben.py quality <文件.md>")
        return 1
    script = SCRIPTS / "quality_gate.py"
    return run_cmd([sys.executable, str(script)] + args).returncode


def cmd_monitor(args):
    """监控。"""
    script = SCRIPTS / "monitor.py"
    cmd = [sys.executable, str(script), '--workspace', str(WORKSPACE)] + args
    return run_cmd(cmd).returncode


def cmd_merge(args):
    """自动合并。"""
    if not args:
        print("用法：mingben.py merge <新文件.md> [--dry-run]")
        return 1
    script = MODDIR / "auto_merge.py"
    return run_cmd([sys.executable, str(script)] + args).returncode


def cmd_exam(args):
    """答题训练。"""
    if not args:
        print("用法：mingben.py exam <analyze|practice|status|template|record> [参数]")
        return 1
    script = SCRIPTS / "exam_trainer.py"
    return run_cmd([sys.executable, str(script)] + args).returncode


def cmd_sync(args):
    """构建验证+提交+推送。"""
    sync_sh = WORKSPACE / "sync.sh"
    msg = args[0] if args else "更新"
    return run_cmd(['bash', str(sync_sh), msg]).returncode


def cmd_status(args):
    """项目总览。"""
    from datetime import datetime
    print("=" * 55)
    print("📚 明本项目总览")
    print("=" * 55)
    print(f"  时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 章数
    full_md = WORKSPACE / "生命论合订本_最新.md"
    if full_md.exists():
        import re
        text = full_md.read_text(encoding='utf-8', errors='replace')
        chapters = len(re.findall(r'^### 第[零一二三四五六七八九十百千两]+章', text, re.MULTILINE))
        size = full_md.stat().st_size
        print(f"  📖 合订本：{chapters}章，{size/1024:.0f}KB")
    else:
        print("  ⚠️  合订本不存在（先构建）")

    # manifest
    manifest = MODDIR / "manifest.txt"
    if manifest.exists():
        modules = [l for l in manifest.read_text(encoding='utf-8').splitlines()
                   if l.strip() and not l.startswith('#')]
        print(f"  📂 模块文件：{len(modules)}个")

    # git状态
    try:
        r = subprocess.run(['git', 'status', '--porcelain'], cwd=str(WORKSPACE),
                          capture_output=True, text=True, timeout=10)
        changes = len([l for l in r.stdout.strip().split('\n') if l])
        flag = "✅" if changes == 0 else "⚠️"
        print(f"  {flag} Git：{changes}个未提交变更")
    except:
        pass

    # 答题训练
    training_data = MODDIR / "09_练习" / "_training_progress.json"
    if training_data.exists():
        import json
        data = json.loads(training_data.read_text(encoding='utf-8'))
        print(f"  ✏️  答题训练：{data.get('total_questions', 0)}题，三遍完成{data.get('three_pass_completed', 0)}次")

    print()
    print("  快捷命令：")
    print("    mingben.py build --html-only    秒级构建HTML")
    print("    mingben.py audit                自审检查")
    print("    mingben.py exam analyze <题>    答题三层分析")
    print("    mingben.py sync \"信息\"          构建+提交+推送")
    print()
    return 0


# 命令路由
COMMANDS = {
    'build': cmd_build,
    'audit': cmd_audit,
    'quality': cmd_quality,
    'monitor': cmd_monitor,
    'merge': cmd_merge,
    'exam': cmd_exam,
    'sync': cmd_sync,
    'status': cmd_status,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help', 'help'):
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"未知命令：{cmd}")
        print(f"可用命令：{', '.join(COMMANDS.keys())}")
        sys.exit(1)

    sys.exit(COMMANDS[cmd](sys.argv[2:]))


if __name__ == '__main__':
    main()

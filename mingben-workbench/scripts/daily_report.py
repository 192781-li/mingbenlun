#!/usr/bin/env python3
"""
明本项目状态日报生成器
每天定时运行，生成轻量项目状态摘要，供对话开始时快速加载。
输出：项目状态日报.md（控制在500字以内）
"""
import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent.parent
MODDIR = WORKSPACE / "生命论_模块化"
OUTPUT = WORKSPACE / "项目状态日报.md"


def get_chapter_count():
    """获取合订本章数。"""
    full_md = WORKSPACE / "生命论合订本_最新.md"
    if not full_md.exists():
        return "未知（未构建）"
    text = full_md.read_text(encoding='utf-8', errors='replace')
    return len(re.findall(r'^### 第[零一二三四五六七八九十百千两]+章', text, re.MULTILINE))


def get_module_count():
    """获取manifest模块数。"""
    manifest = MODDIR / "manifest.txt"
    if not manifest.exists():
        return 0
    return len([l for l in manifest.read_text(encoding='utf-8').splitlines()
                if l.strip() and not l.startswith('#')])


def get_recent_files(hours=24):
    """获取最近N小时修改的文件。"""
    import time
    now = time.time()
    recent = []
    for root, dirs, files in os.walk(WORKSPACE):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules' and d != '备份']
        for f in files:
            if f.startswith('.'):
                continue
            fp = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(fp)
                if now - mtime < hours * 3600:
                    size = os.path.getsize(fp)
                    rel = os.path.relpath(fp, WORKSPACE)
                    recent.append((mtime, size, rel))
            except:
                pass
    recent.sort(reverse=True)
    return recent[:8]


def get_training_progress():
    """获取答题训练进度。"""
    data_file = MODDIR / "09_练习" / "_training_progress.json"
    if not data_file.exists():
        return None
    try:
        return json.loads(data_file.read_text(encoding='utf-8'))
    except:
        return None


def get_git_status():
    """获取git状态。"""
    try:
        r = subprocess.run(['git', 'status', '--porcelain'], cwd=str(WORKSPACE),
                          capture_output=True, text=True, timeout=10)
        changes = [l for l in r.stdout.strip().split('\n') if l]
        return len(changes)
    except:
        return -1


def get_pending_sparks():
    """检查闪光点中是否有待入全本条目。"""
    spark = WORKSPACE / "闪光点.md"
    if not spark.exists():
        return 0
    text = spark.read_text(encoding='utf-8', errors='replace')
    return text.count('待入全本')


def main():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    chapters = get_chapter_count()
    modules = get_module_count()
    git_changes = get_git_status()
    pending = get_pending_sparks()
    training = get_training_progress()
    recent = get_recent_files(24)

    lines = []
    lines.append(f"# 明本项目状态日报")
    lines.append(f"> 生成时间：{now}")
    lines.append(f"> 本文件由定时任务自动生成，供对话开始时快速加载。")
    lines.append("")
    lines.append("## 项目状态")
    lines.append(f"- 合订本：{chapters}章")
    lines.append(f"- 模块文件：{modules}个")
    git_flag = "✅" if git_changes == 0 else "⚠️" if git_changes > 0 else "❓"
    lines.append(f"- Git：{git_flag} {git_changes}个未提交变更" if git_changes >= 0 else "- Git：状态未知")
    if pending > 0:
        lines.append(f"- ⚠️ 闪光点：{pending}条待入全本")
    lines.append("")

    if training:
        lines.append("## 答题训练")
        lines.append(f"- 总练习题数：{training.get('total_questions', 0)}")
        lines.append(f"- 三遍完成数：{training.get('three_pass_completed', 0)}")
        f1_weak = training.get('f1_weak_points', [])
        if f1_weak:
            lines.append(f"- F1薄弱环节：{', '.join(f1_weak[-3:])}")
        lines.append("")

    if recent:
        lines.append("## 最近24小时修改")
        import time
        now_t = time.time()
        for mtime, size, rel in recent:
            mins = int((now_t - mtime) / 60)
            time_str = f"{mins}分钟前" if mins < 60 else f"{mins//60}小时前"
            lines.append(f"- [{time_str}] {rel}")
        lines.append("")

    lines.append("## 快捷命令")
    lines.append("```bash")
    lines.append("./mingben status           # 项目总览")
    lines.append("./mingben exam analyze <题> # 答题三层分析")
    lines.append("./mingben audit --parallel  # 并行自审")
    lines.append("./mingben build --html-only # 秒级构建")
    lines.append("```")

    content = '\n'.join(lines)
    OUTPUT.write_text(content, encoding='utf-8')
    print(f"✅ 日报已生成：{OUTPUT}（{len(content)}字）")


if __name__ == '__main__':
    main()

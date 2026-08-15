#!/usr/bin/env python3
"""双重监控：工作区状态 + 后台进程。"""
import os, sys, time, subprocess, argparse
from datetime import datetime, timedelta
from pathlib import Path

def human_size(n):
    for unit in ['K','M','G','T']:
        if n < 1024: return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.0f}P"

def monitor_workspace(ws):
    print(f"=== 工作区监控: {ws} ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 磁盘
    try:
        u = os.statvfs(ws)
        free = u.f_bavail * u.f_frsize
        total = u.f_blocks * u.f_frsize
        pct = (1 - u.f_bavail/u.f_blocks) * 100
        flag = "✅" if pct < 85 else "⚠️" if pct < 95 else "❌"
        print(f"{flag} 磁盘: {human_size(free)}B / {human_size(total)}B 可用 ({pct:.0f}%已用)")
    except: pass

    # git状态（git仓库在workspace根目录）
    try:
        r = subprocess.run(['git','status','--porcelain'], cwd=ws, capture_output=True, text=True, timeout=10)
        n = len([l for l in r.stdout.strip().split('\n') if l])
        flag = "✅" if n == 0 else "⚠️"
        print(f"{flag} Git: {n}个未提交变更")
    except: pass

    # 最近修改
    print()
    print("📝 最近1小时修改的文件:")
    now = time.time()
    recent = []
    for root, dirs, files in os.walk(ws):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
        for f in files:
            fp = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(fp)
                if now - mtime < 3600:
                    size = os.path.getsize(fp)
                    recent.append((mtime, size, os.path.relpath(fp, ws)))
            except: pass
    recent.sort(reverse=True)
    for mtime, size, rel in recent[:15]:
        mins = int((now - mtime) / 60)
        print(f"  {mins}分钟前 [{human_size(size)}] {rel}")

    # 生命论项目专项
    print()
    print("📚 生命论项目:")
    mod_dir = Path(ws) / "生命论_模块化"
    manifest = mod_dir / "manifest.txt"
    if manifest.exists():
        with open(manifest) as f:
            modules = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        missing = [m for m in modules if not (mod_dir / m).exists()]
        if missing:
            print(f"  ❌ manifest中{len(missing)}个模块缺失: {missing[:5]}")
        else:
            print(f"  ✅ manifest完整 ({len(modules)}个模块)")

    merged = Path(ws) / "生命论合订本_最新.md"
    if merged.exists():
        size = merged.stat().st_size
        if size < 100000:
            print(f"  ❌ 合并文件异常 ({human_size(size)}B)")
        else:
            print(f"  ✅ 合并文件正常 ({human_size(size)}B)")

    out_dir = Path(ws) / "生命论_输出"
    if out_dir.exists():
        files = list(out_dir.glob('*'))
        print(f"  ✅ 输出目录: {len(files)}个文件")

def monitor_background():
    print()
    print("=== 后台任务监控 ===")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    keywords = ['xelatex', 'pandoc', 'build.sh', 'build_all.sh', 'auto_merge', 'quality_gate']
    try:
        r = subprocess.run(['ps','aux'], capture_output=True, text=True, timeout=10)
        procs = []
        for line in r.stdout.split('\n')[1:]:
            for kw in keywords:
                if kw in line and 'monitor.py' not in line:
                    parts = line.split()
                    if len(parts) > 10:
                        pid = parts[1]; etime = parts[9] if len(parts) > 9 else '?'
                        cmd = ' '.join(parts[10:])[:80]
                        procs.append((pid, etime, cmd, kw))
                    break
        if procs:
            print(f"🔄 运行中的相关进程 ({len(procs)}):")
            for pid, etime, cmd, kw in procs:
                print(f"  [{kw}] PID={pid} 运行={etime}")
                print(f"    {cmd}")
        else:
            print("✅ 无运行中的构建进程")
    except Exception as e:
        print(f"⚠️ 进程检查失败: {e}")

    # 临时文件
    tmp_dir = Path('/tmp')
    if tmp_dir.exists():
        tmps = list(tmp_dir.glob('pdf_*')) + list(tmp_dir.glob('*.aux')) + list(tmp_dir.glob('*.log'))
        if len(tmps) > 20:
            print(f"⚠️ 临时文件堆积: {len(tmps)}个")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', default='.')
    parser.add_argument('--background', action='store_true')
    parser.add_argument('--watch', type=int, default=0)
    args = parser.parse_args()

    while True:
        monitor_workspace(args.workspace)
        if args.background:
            monitor_background()
        if args.watch > 0:
            print(f"\n--- {args.watch}秒后刷新 ---")
            time.sleep(args.watch)
        else:
            break

#!/usr/bin/env python3
"""
践演论项目自动备份脚本
用法: python backup_project.py [--full]
功能:
  1. 备份关键文件到 backup/ 目录
  2. 生成备份清单
  3. 清理过期备份（保留最近30天）
  4. 可选：全量备份（包含所有文件）
触发: 可手动运行，也可加入定时任务
"""
import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta

REPO_ROOT = Path(__file__).parent
BACKUP_DIR = REPO_ROOT / "backup"
KEEP_DAYS = 30

# 关键文件列表（必须备份的）
CRITICAL_FILES = [
    # 核心文档
    "项目状态报告.md",
    "三方协作任务监控表.md",
    "践演论第一性原理底线.md",
    "项目基础设施检查清单.md",
    # 任务包
    "任务包_DeepSeek_代码形式化.md",
    "任务包_WorkBuddy_审计反例.md",
    # 综合论文
    "mingben-workbench/references/enactics_paper_v1.0.md",
    # 定理注册表
    "mingben-workbench/references/theorem_registry.json",
    # 研究笔记
    "mingben-workbench/references/f层级形式化_研究笔记_v0.1.md",
    "mingben-workbench/references/参考文献审计报告_v1.2.md",
    "mingben-workbench/references/Ag_lv_Ag_tr分裂新颖性核查报告.md",
    # 规范文档
    "mingben-workbench/references/版本号规范化体系.md",
    "mingben-workbench/references/文献核查清单模板.md",
    # Coq项目
    "coq/_CoqProject",
    "coq/README.md",
    "coq/coq_verify.py",
    "coq/theories/ALL/Layer1.v",
    # 检查器
    "mingben-workbench/scripts/overclaim_checker.py",
    "mingben-workbench/scripts/ref_consistency_checker.py",
    "mingben-workbench/scripts/circular_reasoning_detector.py",
    "mingben-workbench/scripts/pre_commit_hook.py",
    "mingben-workbench/scripts/elc_type_checker.py",
    # 自动化
    "generate_status_report.py",
    "backup_project.py",
]

def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def backup_critical_files(backup_subdir):
    """备份关键文件"""
    backed_up = []
    failed = []
    
    for rel_path in CRITICAL_FILES:
        src = REPO_ROOT / rel_path
        if src.exists():
            dst = backup_subdir / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, dst)
                backed_up.append(rel_path)
            except Exception as e:
                failed.append({"file": rel_path, "error": str(e)})
        else:
            failed.append({"file": rel_path, "error": "文件不存在"})
    
    return backed_up, failed

def backup_full(backup_subdir):
    """全量备份（排除.git、backup、__pycache__等）"""
    exclude_dirs = {".git", "backup", "__pycache__", "node_modules", ".venv"}
    exclude_ext = {".pyc", ".pyo", ".log"}
    
    backed_up = []
    failed = []
    
    for root, dirs, files in os.walk(REPO_ROOT):
        # 排除目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if Path(file).suffix in exclude_ext:
                continue
            src = Path(root) / file
            rel_path = src.relative_to(REPO_ROOT)
            dst = backup_subdir / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, dst)
                backed_up.append(str(rel_path))
            except Exception as e:
                failed.append({"file": str(rel_path), "error": str(e)})
    
    return backed_up, failed

def cleanup_old_backups():
    """清理过期备份"""
    if not BACKUP_DIR.exists():
        return []
    
    cutoff = datetime.now() - timedelta(days=KEEP_DAYS)
    deleted = []
    
    for backup_dir in BACKUP_DIR.iterdir():
        if backup_dir.is_dir() and backup_dir.name.startswith("backup_"):
            try:
                # 从目录名解析时间
                time_str = backup_dir.name.replace("backup_", "")
                backup_time = datetime.strptime(time_str, "%Y%m%d_%H%M%S")
                if backup_time < cutoff:
                    shutil.rmtree(backup_dir)
                    deleted.append(backup_dir.name)
            except (ValueError, Exception):
                # 无法解析时间的目录不删除
                pass
    
    return deleted

def generate_manifest(backup_subdir, backed_up, failed, backup_type):
    """生成备份清单"""
    manifest = {
        "backup_time": datetime.now().isoformat(),
        "backup_type": backup_type,
        "total_files": len(backed_up),
        "failed_count": len(failed),
        "backed_up_files": backed_up,
        "failed_files": failed,
        "backup_location": str(backup_subdir.relative_to(REPO_ROOT))
    }
    
    manifest_path = backup_subdir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest

def main():
    full_backup = "--full" in sys.argv
    backup_type = "full" if full_backup else "critical"
    
    print(f"=== 践演论项目备份 ===")
    print(f"备份类型: {backup_type}")
    print(f"备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建备份目录
    timestamp = get_timestamp()
    backup_subdir = BACKUP_DIR / f"backup_{timestamp}"
    backup_subdir.mkdir(parents=True, exist_ok=True)
    
    # 执行备份
    print("--- 执行备份 ---")
    if full_backup:
        backed_up, failed = backup_full(backup_subdir)
    else:
        backed_up, failed = backup_critical_files(backup_subdir)
    
    print(f"  成功备份: {len(backed_up)} 个文件")
    if failed:
        print(f"  失败: {len(failed)} 个文件")
        for f in failed[:5]:
            print(f"    - {f['file']}: {f['error']}")
        if len(failed) > 5:
            print(f"    ... 还有 {len(failed)-5} 个")
    print()
    
    # 生成清单
    manifest = generate_manifest(backup_subdir, backed_up, failed, backup_type)
    print(f"--- 备份清单 ---")
    print(f"  位置: {manifest['backup_location']}")
    print(f"  文件: manifest.json")
    print()
    
    # 清理过期备份
    print("--- 清理过期备份 ---")
    deleted = cleanup_old_backups()
    if deleted:
        print(f"  已删除 {len(deleted)} 个过期备份（保留最近{KEEP_DAYS}天）")
        for d in deleted[:3]:
            print(f"    - {d}")
    else:
        print(f"  无过期备份（保留最近{KEEP_DAYS}天）")
    print()
    
    # 总结
    print("=== 备份完成 ===")
    print(f"  备份位置: {backup_subdir}")
    print(f"  备份文件: {len(backed_up)} 个")
    print(f"  失败文件: {len(failed)} 个")
    
    return 0 if len(failed) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

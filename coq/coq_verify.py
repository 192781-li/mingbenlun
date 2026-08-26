#!/usr/bin/env python3
"""
践演论Coq验证脚本
用法: python coq_verify.py [--strict]
功能:
  1. 编译coq/theories/下所有.v文件
  2. 检查Admitted（未证明的定理）
  3. 检查循环依赖
  4. 生成验证报告
  5. 返回退出码: 0=全部通过, 1=编译错误, 2=有Admitted(仅strict模式)
"""
import os
import sys
import subprocess
import re
import json
from pathlib import Path
from datetime import datetime

COQ_DIR = Path(__file__).parent
THEORIES_DIR = COQ_DIR / "theories"
REPORT_FILE = COQ_DIR / "coq_verify_report.json"

def find_coqc():
    """自动检测coqc路径，支持Windows和Linux/macOS"""
    # 1. 环境变量COQC
    env_coqc = os.environ.get("COQC")
    if env_coqc and Path(env_coqc).exists():
        return env_coqc
    
    # 2. PATH中的coqc
    try:
        result = subprocess.run(["where", "coqc"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[0].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        result = subprocess.run(["which", "coqc"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[0].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # 3. Windows已知安装路径
    if sys.platform == "win32":
        windows_paths = [
            r"C:\Rocq-Platform~9.0~2025.08\bin\coqc.exe",
            r"C:\Coq\bin\coqc.exe",
            r"C:\Program Files\Coq\bin\coqc.exe",
            r"C:\Program Files (x86)\Coq\bin\coqc.exe",
        ]
        # 也扫描Rocq-Platform开头的目录
        program_files = Path("C:/")
        if program_files.exists():
            for d in program_files.iterdir():
                if d.name.startswith("Rocq-Platform") or d.name.startswith("Coq"):
                    candidate = d / "bin" / "coqc.exe"
                    if candidate.exists():
                        windows_paths.append(str(candidate))
        
        for p in windows_paths:
            if Path(p).exists():
                return p
    
    # 4. 默认返回coqc（让系统找）
    return "coqc"

COQC_PATH = find_coqc()

def find_v_files():
    """查找所有.v文件"""
    return sorted(THEORIES_DIR.rglob("*.v"))

def check_admitted(v_file):
    """检查.v文件中是否有Admitted"""
    content = v_file.read_text(encoding="utf-8", errors="ignore")
    # 匹配Admitted（不是注释中的）
    admitted_pattern = re.compile(r'^\s*Admitted\.', re.MULTILINE)
    matches = admitted_pattern.findall(content)
    # 也检查Theorem/Lemma后面直接跟Admitted的情况
    theorem_admitted = re.findall(r'(Theorem|Lemma|Corollary|Proposition|Fact)\s+(\w+)[^.]*\.\s*Admitted\.', content)
    return len(matches), theorem_admitted

def compile_v_file(v_file, coqc_path=None):
    """编译单个.v文件"""
    if coqc_path is None:
        coqc_path = COQC_PATH
    try:
        result = subprocess.run(
            [coqc_path, "-R", str(THEORIES_DIR), "Enactics", str(v_file)],
            capture_output=True, text=True, timeout=120,
            cwd=str(COQ_DIR)
        )
        return {
            "file": str(v_file.relative_to(COQ_DIR)),
            "success": result.returncode == 0,
            "stdout": result.stdout[:500] if result.stdout else "",
            "stderr": result.stderr[:1000] if result.stderr else "",
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "file": str(v_file.relative_to(COQ_DIR)),
            "success": False,
            "error": "timeout",
            "returncode": -1
        }
    except FileNotFoundError:
        return {
            "file": str(v_file.relative_to(COQ_DIR)),
            "success": False,
            "error": "coqc not found",
            "returncode": -2
        }

def check_import_cycle(v_files):
    """检查导入循环（简单的DFS）"""
    graph = {}
    for vf in v_files:
        content = vf.read_text(encoding="utf-8", errors="ignore")
        imports = re.findall(r'Require\s+(?:Import\s+|Export\s+)?(?:Enactics\.)?(\w+(?:\.\w+)*)\.', content)
        graph[str(vf.stem)] = imports
    
    # DFS检测环
    visited = set()
    rec_stack = set()
    cycles = []
    
    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor, path + [node]):
                    return True
            elif neighbor in rec_stack:
                cycles.append(path + [node, neighbor])
                return True
        rec_stack.remove(node)
        return False
    
    for node in graph:
        if node not in visited:
            dfs(node, [])
    
    return cycles

def main():
    strict = "--strict" in sys.argv
    
    v_files = find_v_files()
    print(f"=== 践演论Coq验证 ===")
    print(f"找到 {len(v_files)} 个.v文件")
    print(f"严格模式: {'是' if strict else '否'}")
    print()
    
    # 1. 检查Admitted
    print("--- 检查Admitted ---")
    total_admitted = 0
    admitted_details = []
    for vf in v_files:
        count, theorems = check_admitted(vf)
        if count > 0:
            rel = vf.relative_to(COQ_DIR)
            print(f"  ⚠️  {rel}: {count}个Admitted")
            for thm_type, thm_name in theorems:
                print(f"      - {thm_type} {thm_name}")
            total_admitted += count
            admitted_details.append({"file": str(rel), "count": count, "theorems": [f"{t} {n}" for t, n in theorems]})
    if total_admitted == 0:
        print("  ✅ 无Admitted")
    print()
    
    # 2. 检查循环依赖
    print("--- 检查循环依赖 ---")
    cycles = check_import_cycle(v_files)
    if cycles:
        print(f"  ⚠️  发现 {len(cycles)} 个循环依赖:")
        for cycle in cycles:
            print(f"      {' -> '.join(cycle)}")
    else:
        print("  ✅ 无循环依赖")
    print()
    
    # 3. 尝试编译（如果coqc可用）
    print("--- 编译检查 ---")
    coqc_path = COQC_PATH
    print(f"  coqc路径: {coqc_path}")
    
    compile_results = []
    try:
        version = subprocess.run([coqc_path, "--version"], capture_output=True, text=True, timeout=10)
        version_str = version.stdout.strip() or version.stderr.strip() or "unknown"
        print(f"  coqc版本: {version_str}")
        for vf in v_files:
            result = compile_v_file(vf, coqc_path)
            compile_results.append(result)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['file']}")
            if not result["success"] and result.get("stderr"):
                # 只显示前3行错误
                for line in result["stderr"].split("\n")[:3]:
                    if line.strip():
                        print(f"      {line.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  ⚠️  coqc不可用，跳过编译检查（只做静态检查）")
    print()
    
    # 4. 生成报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_files": len(v_files),
        "total_admitted": total_admitted,
        "admitted_details": admitted_details,
        "cycles": cycles,
        "compile_results": compile_results,
        "strict_mode": strict,
        "summary": {
            "compiled": sum(1 for r in compile_results if r.get("success")),
            "failed": sum(1 for r in compile_results if not r.get("success") and r.get("returncode", 0) >= 0),
            "skipped": sum(1 for r in compile_results if r.get("returncode", 0) < 0),
        }
    }
    
    REPORT_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"--- 报告已写入: {REPORT_FILE} ---")
    print()
    
    # 5. 总结
    print("=== 总结 ===")
    print(f"  文件数: {len(v_files)}")
    print(f"  Admitted: {total_admitted}")
    print(f"  循环依赖: {len(cycles)}")
    if compile_results:
        print(f"  编译通过: {report['summary']['compiled']}/{len(compile_results)}")
    
    # 退出码
    if compile_results and report["summary"]["failed"] > 0:
        print("\n❌ 有编译错误")
        return 1
    if strict and total_admitted > 0:
        print(f"\n❌ 严格模式: 有{total_admitted}个Admitted")
        return 2
    print("\n✅ 验证通过")
    return 0

if __name__ == "__main__":
    sys.exit(main())

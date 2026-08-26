#!/usr/bin/env python3
"""扫描核心定理的名称引用，迁移到T00X"""
import os
import re
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent
REGISTRY_FILE = REPO_ROOT / "mingben-workbench" / "references" / "theorem_registry.json"

EXCLUDE_DIRS = {'.git', 'backup', '__pycache__', 'node_modules', '.venv'}
# 不迁移的文件类别
EXCLUDE_FILE_PATTERNS = [
    r'enactics_v\d+\.\d+\.md$',  # 历史版本
    r'_report\.md$', r'_report\.json$',  # 报告
    r'overclaim', r'audit', r'attack', r'round\d',  # 审计/攻击
    r'old_refs_migration', r'cross_refs',  # 迁移报告自身
]

# 核心定理的名称模式（用于匹配名称引用）
# 从注册表中提取每个定理的关键词
THEOREM_NAME_PATTERNS = {
    "T001": [  # 生命不可资本化
        r'生命不可资本化', r'生命不可复制', r'!不保持?余归纳', r'!不保余归纳',
        r'!νF₂?≇ν!F', r'!(νF)≇ν(!F)', r'!不穿透νF',
    ],
    "T002": [  # 自由只能在实践中确立
        r'自由只能在实践中确立', r'S_A\s*⊬\s*Ag_lv',
    ],
    "T003": [  # Π₂完全性
        r'Π₂-?完全性', r'系统自主性的不可判定性', r'AGENCY.*Π₂',
    ],
    "T004": [  # AGENCY与PRODUCTIVE递归同构
        r'AGENCY.*PRODUCTIVE.*递归同构', r'自主性.*生产性.*同构',
    ],
    "T005": [  # 明性幂等
        r'明性幂等',
    ],
    "T006": [  # 明性是异化的右逆
        r'明性.*异化.*右逆', r'明性余单',
    ],
    "T007": [  # 异化压缩
        r'异化压缩',
    ],
    "T008": [  # 明性反转异化
        r'明性反转异化',
    ],
    "T009": [  # !不保余归纳/不可克隆
        r'一般不可克隆', r'不可克隆定理',
    ],
    "T010": [  # self_check检测异化
        r'self_check检测异化', r'self_check.*检测.*异化',
    ],
    "T011": [  # 革命级联
        r'革命级联', r'星星之火.*燎原.*数学',
    ],
    "T012": [  # 异化=时钟量化
        r'异化.*时钟量化', r'clock quantification',
    ],
    "T013": [  # 量子测量=异化
        r'量子测量.*异化', r'Hilb外部基定理',
    ],
    "T014": [  # 异化链定理
        r'异化链定理',
    ],
    "T015": [  # Workbody第二轮修正汇总
        r'Workbody第二轮修正',
    ],
    "T016": [  # 运行权steering不等式
        r'steering不等式', r'运行权.*steering',
    ],
    "T017": [  # 完美自我遮蔽不动点
        r'完美自我遮蔽不动点', r'完美遮蔽.*不动点',
    ],
    "T018": [  # 持续感染源推论
        r'持续感染源', r'永生感染源',
    ],
}

def should_exclude(rel_path):
    """判断文件是否应该排除"""
    name = Path(rel_path).name
    for pattern in EXCLUDE_FILE_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return True
    return False

def find_md_files():
    md_files = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith('.md'):
                md_files.append(Path(root) / f)
    return sorted(md_files)

def main():
    print("=== 核心定理名称引用扫描 ===")
    print()
    
    total_matches = 0
    file_matches = {}
    
    for md_file in find_md_files():
        rel_path = str(md_file.relative_to(REPO_ROOT))
        if should_exclude(rel_path):
            continue
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        
        matches_in_file = []
        for tid, patterns in THEOREM_NAME_PATTERNS.items():
            for pattern in patterns:
                found = re.findall(pattern, content)
                if found:
                    # 检查是否已经有T00X引用在附近
                    for m in re.finditer(pattern, content):
                        # 检查前后50个字符内是否已有T00X
                        start = max(0, m.start() - 50)
                        end = min(len(content), m.end() + 50)
                        context = content[start:end]
                        if tid not in context:
                            matches_in_file.append((tid, m.group(), m.start()))
        
        if matches_in_file:
            file_matches[rel_path] = matches_in_file
            total_matches += len(matches_in_file)
    
    print(f"找到 {total_matches} 处核心定理名称引用（附近无T00X）")
    print(f"分布在 {len(file_matches)} 个文件中")
    print()
    
    # 按定理统计
    tid_counts = {}
    for matches in file_matches.values():
        for tid, name, pos in matches:
            tid_counts[tid] = tid_counts.get(tid, 0) + 1
    
    print("=== 按定理统计 ===")
    for tid in sorted(tid_counts.keys()):
        print(f"  {tid}: {tid_counts[tid]}处")
    print()
    
    # 显示前20个文件的详情
    print("=== 详情（前20个文件）===")
    for rel_path, matches in sorted(file_matches.items(), key=lambda x: -len(x[1]))[:20]:
        print(f"  {rel_path}: {len(matches)}处")
        for tid, name, pos in matches[:5]:
            print(f"    {tid}: \"{name}\"")
    
    # 保存结果
    result = {
        "total_matches": total_matches,
        "files": {
            rel_path: [{"tid": tid, "matched_text": name} for tid, name, pos in matches]
            for rel_path, matches in file_matches.items()
        }
    }
    result_file = REPO_ROOT / "mingben-workbench" / "references" / "name_refs_scan.json"
    result_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n结果已保存: {result_file}")

if __name__ == '__main__':
    main()

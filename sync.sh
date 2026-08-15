#!/bin/bash
# 明本同步脚本：构建验证 → 元监督自筛 → 本地提交 → 推送到GitHub
# 用法：bash sync.sh ["提交信息"]
# 不带提交信息则用时间戳
set -e
cd "$(dirname "$0")"
echo "=== 明本同步 $(date '+%Y-%m-%d %H:%M:%S') ==="

# 1. 先构建验证
echo "[1/4] 构建验证..."
bash 生命论_模块化/build.sh --html-only > /dev/null 2>&1 && echo "  ✓ 构建通过" || { echo "  ✗ 构建失败，终止同步"; exit 1; }

# 2. 元监督自筛（硬门控：有问题不许推）
echo "[2/4] 元监督自筛..."
if python3 mingben-workbench/scripts/self_audit.py --quiet; then
    echo "  ✓ 自筛全部通过"
else
    echo "  ✗ 自筛未通过，终止同步。用 'python3 mingben-workbench/scripts/self_audit.py' 查看详情"
    exit 1
fi

# 3. 提交
echo "[3/4] 提交..."
git add -A
if git diff --cached --quiet; then
    echo "  无变更需要提交"
else
    msg="${1:-同步 $(date '+%Y-%m-%d %H:%M')}"
    git commit -m "$msg"
    echo "  已提交: $msg"
fi

# 4. 推送
echo "[4/4] 推送到GitHub..."
git push origin main 2>&1
echo ""
echo "✓ 同步完成: https://github.com/192781-li/mingbenlun"

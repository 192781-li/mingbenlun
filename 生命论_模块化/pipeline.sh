#!/bin/bash
# 生命论全自动管道
# 用法：
#   bash pipeline.sh <新文件>     # 合并新文件→检查→构建→提交
#   bash pipeline.sh --check      # 只检查
#   bash pipeline.sh --build      # 只构建多格式
#   bash pipeline.sh --commit     # 只提交git
#   bash pipeline.sh --all        # 检查+构建+提交（不合并新文件）

set -e
cd "$(dirname "$0")"
MODDIR=$(pwd)
WORKSPACE=$(dirname "$MODDIR")
cd "$WORKSPACE"

ACTION="${1:---all}"

echo "╔══════════════════════════════════════╗"
echo "║     生命论（明本论）自动构建管道      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 1. 合并新文件
if [[ "$ACTION" != "--check" && "$ACTION" != "--build" && "$ACTION" != "--commit" && "$ACTION" != "--all" ]]; then
    echo "═══ 步骤1：合并新内容 ═══"
    python3 "$MODDIR/smart_merge.py" "$ACTION" --no-build
    echo ""
fi

# 2. 质量检查
if [[ "$ACTION" != "--build" && "$ACTION" != "--commit" ]]; then
    echo "═══ 步骤2：质量检查 ═══"
    python3 "$MODDIR/quality_check.py" || {
        echo "质量检查发现错误，是否继续？(y/N)"
        read -r ans
        [[ "$ans" != "y" ]] && exit 1
    }
    echo ""
fi

# 3. 多格式构建
if [[ "$ACTION" != "--check" && "$ACTION" != "--commit" ]]; then
    echo "═══ 步骤3：多格式构建 ═══"
    bash "$MODDIR/build_all.sh" html epub docx txt md  # 先构建快的
    echo ""
    echo "PDF在后台构建中（5-10分钟）..."
    bash "$MODDIR/build_all.sh" pdf &
    PDF_PID=$!
    echo "  PID: $PDF_PID（完成后在 生命论_输出/ 目录）"
    echo ""
fi

# 4. Git提交
if [[ "$ACTION" != "--check" && "$ACTION" != "--build" ]]; then
    echo "═══ 步骤4：版本提交 ═══"
    cd "$MODDIR"
    git add -A
    if git diff --cached --quiet; then
        echo "无变更，跳过提交"
    else
        COMMIT_MSG="更新：$(date '+%Y-%m-%d %H:%M')"
        # 统计变更
        CHANGED=$(git diff --cached --stat | tail -1)
        git commit -m "$COMMIT_MSG" -m "$CHANGED" 2>&1 | tail -3
        echo "已提交：$COMMIT_MSG"
    fi
    cd "$WORKSPACE"
    echo ""
fi

echo "╔══════════════════════════════════════╗"
echo "║  管道完成。输出目录：生命论_输出/     ║"
echo "╚══════════════════════════════════════╝"

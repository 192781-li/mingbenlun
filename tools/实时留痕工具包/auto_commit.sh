#!/bin/bash
# =====================================================================
# 实时留痕自动提交脚本 v1.0
# 功能：检测文件变化 → 自动git add/commit/push → 精确到秒的时间戳
# 用法：
#   bash auto_commit.sh "提交说明"          # 单次提交
#   bash auto_commit.sh --watch              # 监控模式，每30秒自动提交一次
#   bash auto_commit.sh --watch 60           # 监控模式，每60秒自动提交一次
#   bash auto_commit.sh --status             # 查看当前状态和最近5条提交
# 设计原则：
#   1. 不管干什么都留痕，精确到秒
#   2. commit message自动带时间戳和操作人
#   3. 失败不破坏库，错误记入日志
#   4. 可配合cron定时任务或手动调用
# =====================================================================
set -e

# 配置
REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"  # 仓库根目录（工具包在tools/下）
LOG_FILE="$REPO_DIR/tools/实时留痕工具包/commit_log.csv"
BRANCH="main"
OPERATOR="${OPERATOR:-明旭}"  # 操作人，可通过环境变量覆盖

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 确保在仓库目录
cd "$REPO_DIR"

# 初始化日志文件
init_log() {
    if [ ! -f "$LOG_FILE" ]; then
        mkdir -p "$(dirname "$LOG_FILE")"
        echo "时间,操作人,操作类型,文件数,commit_hash,状态,备注" > "$LOG_FILE"
    fi
}

# 获取精确时间戳
timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# 记录日志
log_commit() {
    local op_type="$1"
    local file_count="$2"
    local commit_hash="$3"
    local status="$4"
    local note="$5"
    echo "$(timestamp),$OPERATOR,$op_type,$file_count,$commit_hash,$status,$note" >> "$LOG_FILE"
}

# 单次提交
do_commit() {
    local message="$1"
    local ts
    ts=$(timestamp)

    # 检查是否有变化
    if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
        echo -e "${YELLOW}[$ts] 无文件变化，跳过提交${NC}"
        return 0
    fi

    # 统计变化文件数
    local file_count
    file_count=$(git status --porcelain | wc -l)

    # 构造commit message：时间戳 + 操作人 + 说明
    local commit_msg
    if [ -z "$message" ]; then
        commit_msg="实时留痕 [$ts] $OPERATOR"
    else
        commit_msg="[$ts] $OPERATOR：$message"
    fi

    # 执行提交
    echo -e "${GREEN}[$ts] 检测到 $file_count 个文件变化，正在提交...${NC}"

    git add -A 2>/dev/null || {
        echo -e "${RED}[$ts] git add 失败${NC}"
        log_commit "commit" "$file_count" "N/A" "失败" "git add失败"
        return 1
    }

    local commit_hash
    commit_hash=$(git commit -m "$commit_msg" 2>/dev/null | grep -oP '(?<=\[).*(?=\])' | head -1 || echo "N/A")

    if [ "$commit_hash" = "N/A" ]; then
        # 可能是nothing to commit
        commit_hash=$(git rev-parse --short HEAD 2>/dev/null || echo "N/A")
        echo -e "${YELLOW}[$ts] 无新提交（可能已提交）${NC}"
        log_commit "commit" "$file_count" "$commit_hash" "无变化" "nothing to commit"
        return 0
    fi

    # push
    local push_status="成功"
    git push origin "$BRANCH" 2>/dev/null || {
        push_status="push失败"
        echo -e "${RED}[$ts] push失败（本地已提交，稍后重试）${NC}"
    }

    echo -e "${GREEN}[$ts] 提交成功：$commit_hash（$file_count个文件，push：$push_status）${NC}"
    log_commit "commit" "$file_count" "$commit_hash" "$push_status" "$message"
    return 0
}

# 监控模式
watch_mode() {
    local interval="${1:-30}"
    echo -e "${GREEN}启动监控模式：每 ${interval} 秒自动检测并提交一次${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止${NC}"

    while true; do
        do_commit "自动监控提交"
        sleep "$interval"
    done
}

# 查看状态
show_status() {
    echo "=== 仓库状态 ==="
    git status --short
    echo ""
    echo "=== 最近5条提交 ==="
    git log --oneline -5
    echo ""
    echo "=== 提交日志（最近10条）==="
    if [ -f "$LOG_FILE" ]; then
        tail -10 "$LOG_FILE"
    else
        echo "日志文件不存在"
    fi
}

# 主入口
init_log

case "${1:-}" in
    --watch)
        watch_mode "${2:-30}"
        ;;
    --status)
        show_status
        ;;
    --help|-h)
        echo "用法："
        echo "  bash auto_commit.sh \"提交说明\"    单次提交"
        echo "  bash auto_commit.sh --watch [秒数]  监控模式（默认30秒）"
        echo "  bash auto_commit.sh --status         查看状态"
        echo ""
        echo "环境变量："
        echo "  OPERATOR=名字    设置操作人（默认：明旭）"
        ;;
    *)
        do_commit "$*"
        ;;
esac

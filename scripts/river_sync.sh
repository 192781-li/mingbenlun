#!/bin/bash
# ============================================================
# 河流汇合器 river_sync.sh
# 智慧河流的硬约束同步机制——S01和S04定时任务必须调用
# 不调用pull不能开始干活，不调用push不能结束
# ============================================================

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RIVER_DIR="docs/协作机制/智慧河流"
RIVER_FILES=("河流主干.md" "河流状态.md" "智慧结晶库.md" "DeepSeek干渠.md")

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[河流汇合器]${NC} $1"; }
ok()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn(){ echo -e "${YELLOW}[警告]${NC} $1"; }
err() { echo -e "${RED}[错误]${NC} $1"; }

# ============================================================
# 确定自己的分站和对方分支
# ============================================================
detect_station() {
    local branch
    branch=$(git -C "$REPO_DIR" branch --show-current 2>/dev/null || echo "")
    case "$branch" in
        s01-philosophy)
            MY_STATION="S01"
            MY_BRANCH="s01-philosophy"
            OTHER_BRANCH="s04-coq"
            ;;
        s04-coq)
            MY_STATION="S04"
            MY_BRANCH="s04-coq"
            OTHER_BRANCH="s01-philosophy"
            ;;
        main)
            MY_STATION="S00"
            MY_BRANCH="main"
            OTHER_BRANCH=""
            ;;
        *)
            err "当前分支 $branch 不是明旭分站分支"
            err "请先 git checkout s01-philosophy 或 s04-coq"
            exit 1
            ;;
    esac
    log "本站：$MY_STATION ($MY_BRANCH)，对方分支：$OTHER_BRANCH"
}

# ============================================================
# 检查河流文件是否存在
# ============================================================
check_river_exists() {
    local missing=0
    for f in "${RIVER_FILES[@]}"; do
        if [ ! -f "$REPO_DIR/$RIVER_DIR/$f" ]; then
            warn "本地缺少河流文件：$f"
            missing=1
        fi
    done
    if [ $missing -eq 1 ]; then
        warn "本地河流文件不完整，将从对方分支拉取"
    else
        ok "本地河流文件完整（4个文件）"
    fi
}

# ============================================================
# 从对方分支拉取河流文件并智能合并
# ============================================================
pull_river() {
    detect_station
    check_river_exists

    if [ -z "$OTHER_BRANCH" ]; then
        warn "在main分支，不需要pull"
        return 0
    fi

    log "从 origin/$OTHER_BRANCH 拉取最新河流..."
    git -C "$REPO_DIR" fetch origin "$OTHER_BRANCH" 2>/dev/null || {
        err "fetch origin/$OTHER_BRANCH 失败"
        return 1
    }

    local tmpdir
    tmpdir=$(mktemp -d)
    trap "rm -rf $tmpdir" EXIT

    local merged=0
    local created=0

    for f in "${RIVER_FILES[@]}"; do
        local remote_content
        remote_content=$(git -C "$REPO_DIR" show "origin/$OTHER_BRANCH:$RIVER_DIR/$f" 2>/dev/null || echo "")

        if [ -z "$remote_content" ]; then
            warn "对方分支没有 $f，跳过"
            continue
        fi

        local local_file="$REPO_DIR/$RIVER_DIR/$f"

        if [ ! -f "$local_file" ]; then
            # 本地没有，直接复制
            echo "$remote_content" > "$local_file"
            log "创建本地文件：$f"
            created=$((created + 1))
        else
            # 智能合并：append-only文件取并集，状态文件取最新
            case "$f" in
                "河流主干.md"|"智慧结晶库.md"|"DeepSeek干渠.md")
                    # append-only：把对方独有的记录追加到本地
                    # 方法：把两个文件拼起来，去重（按行），保持顺序
                    local combined
                    combined=$(cat "$local_file" <(echo "$remote_content") | awk '!seen[$0]++')
                    echo "$combined" > "$local_file"
                    log "合并（append-only）：$f"
                    merged=$((merged + 1))
                    ;;
                "河流状态.md")
                    # 状态文件：比较最后更新时间，取最新的
                    local local_time remote_time
                    local_time=$(grep -oP '最后更新：\K[0-9:-]+' "$local_file" 2>/dev/null || echo "0")
                    remote_time=$(echo "$remote_content" | grep -oP '最后更新：\K[0-9:-]+' 2>/dev/null || echo "0")
                    if [[ "$remote_time" > "$local_time" ]]; then
                        echo "$remote_content" > "$local_file"
                        log "对方状态更新（$remote_time > $local_time），采用对方版本：$f"
                        merged=$((merged + 1))
                    else
                        log "本地状态更新或相同（$local_time >= $remote_time），保留本地：$f"
                    fi
                    ;;
            esac
        fi
    done

    ok "拉取完成：创建 $created 个，合并 $merged 个"

    # 验证合并后的完整性
    verify_river_integrity

    # 自动commit拉取的合并
    if [ $merged -gt 0 ] || [ $created -gt 0 ]; then
        log "自动commit河流合并..."
        git -C "$REPO_DIR" add "$RIVER_DIR/" 2>/dev/null || true
        git -C "$REPO_DIR" commit -m "$MY_STATION: 河流汇合器自动pull——从$OTHER_BRANCH合并最新河流文件

河流汇合器river_sync.sh pull自动执行：
- 从origin/$OTHER_BRANCH拉取4个河流文件
- append-only文件智能合并（河流主干/结晶库/DeepSeek干渠）
- 状态文件取最新版本
- 完整性验证通过" 2>/dev/null || warn "没有新内容需要commit"
    fi

    echo ""
    log "=== 河流汇合报告 ==="
    log "本站：$MY_STATION，对方：$OTHER_BRANCH"
    log "创建文件：$created，合并文件：$merged"
    log "河流主干最后5条记录："
    tail -5 "$REPO_DIR/$RIVER_DIR/河流主干.md" 2>/dev/null | head -5
    log "===================="
}

# ============================================================
# 验证河流完整性
# ============================================================
verify_river_integrity() {
    local issues=0

    # 检查1：河流文件存在
    for f in "${RIVER_FILES[@]}"; do
        if [ ! -f "$REPO_DIR/$RIVER_DIR/$f" ]; then
            err "完整性检查失败：缺少 $f"
            issues=$((issues + 1))
        fi
    done

    # 检查2：河流主干非空
    if [ -f "$REPO_DIR/$RIVER_DIR/河流主干.md" ]; then
        local lines
        lines=$(wc -l < "$REPO_DIR/$RIVER_DIR/河流主干.md")
        if [ "$lines" -lt 5 ]; then
            warn "河流主干只有 $lines 行，可能不完整"
        else
            ok "河流主干：$lines 行"
        fi
    fi

    # 检查3：智慧结晶库至少有结晶
    if [ -f "$REPO_DIR/$RIVER_DIR/智慧结晶库.md" ]; then
        local crystals
        crystals=$(grep -c "## 结晶" "$REPO_DIR/$RIVER_DIR/智慧结晶库.md" 2>/dev/null || echo "0")
        ok "智慧结晶库：$crystals 条结晶"
    fi

    # 检查4：河流状态有最后更新时间
    if [ -f "$REPO_DIR/$RIVER_DIR/河流状态.md" ]; then
        local update_time
        update_time=$(grep -oP '最后更新：\K[0-9:-]+' "$REPO_DIR/$RIVER_DIR/河流状态.md" 2>/dev/null || echo "未知")
        ok "河流状态最后更新：$update_time"
    fi

    if [ $issues -gt 0 ]; then
        err "完整性检查发现 $issues 个问题"
        return 1
    else
        ok "河流完整性验证通过"
        return 0
    fi
}

# ============================================================
# 推送河流文件到自己分支
# ============================================================
push_river() {
    detect_station

    log "验证河流完整性..."
    verify_river_integrity || {
        err "完整性验证失败，拒绝push"
        return 1
    }

    log "检查是否有未提交的河流文件改动..."
    local changes
    changes=$(git -C "$REPO_DIR" status --porcelain "$RIVER_DIR/" 2>/dev/null | wc -l)

    if [ "$changes" -eq 0 ]; then
        ok "河流文件没有新改动，不需要push"
        return 0
    fi

    log "有 $changes 个河流文件改动，准备push..."

    git -C "$REPO_DIR" add "$RIVER_DIR/" 2>/dev/null || true
    git -C "$REPO_DIR" commit -m "$MY_STATION: 河流汇合器自动push——本轮产出汇入河流

河流汇合器river_sync.sh push自动执行：
- 完整性验证通过
- 本轮所有产出已append到河流主干
- 河流状态已更新
- 智慧结晶/DeepSeek记录已沉淀" 2>/dev/null || {
        warn "没有新内容需要commit"
        return 0
    }

    git -C "$REPO_DIR" push origin "$MY_BRANCH" 2>/dev/null || {
        err "push到 origin/$MY_BRANCH 失败"
        err "请运行：git -C $REPO_DIR push origin $MY_BRANCH"
        return 1
    }

    ok "河流已push到 origin/$MY_BRANCH"
    ok "=== 河流汇合完成 ==="
}

# ============================================================
# 状态检查
# ============================================================
status_river() {
    detect_station
    echo ""
    echo "========== 河流状态报告 =========="
    echo "本站：$MY_STATION ($MY_BRANCH)"
    echo "对方分支：$OTHER_BRANCH"
    echo ""

    # 本地河流状态
    echo "--- 本地河流文件 ---"
    for f in "${RIVER_FILES[@]}"; do
        if [ -f "$REPO_DIR/$RIVER_DIR/$f" ]; then
            local lines
            lines=$(wc -l < "$REPO_DIR/$RIVER_DIR/$f" 2>/dev/null || echo "0")
            echo "  ✅ $f ($lines 行)"
        else
            echo "  ❌ $f (缺失)"
        fi
    done

    # 对方分支最新commit
    echo ""
    echo "--- 对方分支最新commit ---"
    if [ -n "$OTHER_BRANCH" ]; then
        git -C "$REPO_DIR" fetch origin "$OTHER_BRANCH" 2>/dev/null || true
        git -C "$REPO_DIR" log "origin/$OTHER_BRANCH" --oneline -3 2>/dev/null || echo "  无法获取"
    fi

    # 本地分支最新commit
    echo ""
    echo "--- 本地分支最新commit ---"
    git -C "$REPO_DIR" log "$MY_BRANCH" --oneline -3 2>/dev/null || echo "  无法获取"

    # 河流主干最后3条
    echo ""
    echo "--- 河流主干最后3条记录 ---"
    tail -15 "$REPO_DIR/$RIVER_DIR/河流主干.md" 2>/dev/null | grep "^##" | tail -3 || echo "  无记录"

    echo ""
    echo "=================================="
}

# ============================================================
# 主入口
# ============================================================
case "${1:-all}" in
    pull)
        pull_river
        ;;
    push)
        push_river
        ;;
    status)
        status_river
        ;;
    verify)
        detect_station
        verify_river_integrity
        ;;
    all)
        echo "用法：$0 {pull|push|status|verify}"
        echo ""
        echo "  pull   - 从对方分支拉取并智能合并河流文件（定时任务第一步必须调用）"
        echo "  push   - 验证完整性后push河流文件到自己分支（定时任务最后一步必须调用）"
        echo "  status - 查看河流状态报告"
        echo "  verify - 仅验证河流完整性"
        echo ""
        echo "硬约束：不调用pull不能开始干活，不调用push不能结束。"
        ;;
    *)
        echo "未知命令：$1"
        echo "用法：$0 {pull|push|status|verify}"
        exit 1
        ;;
esac

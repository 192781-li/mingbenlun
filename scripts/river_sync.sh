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
# 全部分站分支：main(S00) 是集成主干，pull 时要从所有分站汇合，
# 不能再把 main 排除在同步环外（否则结晶/河流会长期压在分支、main 停更）。
# 【提交纪律·L040/2026-09-12】本脚本在 main 上 pull 会产生一次"自动commit河流合并"，
# 该 commit 只是本地落盘，绝不能据此直推 main：S00 须先把它转入 s00-主题-日期 临时分支
# 走 PR 合入，再让本地 main 对齐 origin/main；分站在各自长期分支同理，main 永远只走 PR。
ALL_STATION_BRANCHES=()

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
            ALL_STATION_BRANCHES=()
            ;;
        s04-coq)
            MY_STATION="S04"
            MY_BRANCH="s04-coq"
            OTHER_BRANCH="s01-philosophy"
            ALL_STATION_BRANCHES=()
            ;;
        main)
            MY_STATION="S00"
            MY_BRANCH="main"
            OTHER_BRANCH=""
            # S00 在 main 上从所有分站分支汇合河流（多分支集成）
            ALL_STATION_BRANCHES=(s01-philosophy s02-gaokao-arts s03-divination s04-coq s05-info s06-math)
            ;;
        *)
            err "当前分支 $branch 不是明旭分站分支"
            err "请先 git checkout s01-philosophy / s04-coq / main"
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
# 结晶库同号异义检测：输出冲突编号串（空=无冲突）
# 根治旧版"整行去重"会把两个 ## 结晶NNN 都保留、造成重复编号却不报警的缺口
# ============================================================
crystal_clash() {
    python3 - "$1" "$2" <<'PY' 2>/dev/null
import sys,re
def load(p):
    d={}
    try:
        for line in open(p,encoding='utf-8'):
            x=re.match(r'^## 结晶(\d{3})[：:](.+)$',line)
            if x: d[x.group(1)]=x.group(2).strip()
    except FileNotFoundError:
        pass
    return d
a,b=load(sys.argv[1]),load(sys.argv[2])
print(' '.join(n for n in sorted(b) if n in a and a[n][:12]!=b[n][:12]))
PY
}

# ============================================================
# 从单个对方分支拉取河流文件并智能合并（结果累加到 TOTAL_*）
# ============================================================
merge_from_branch() {
    local other="$1"
    log "从 origin/$other 拉取最新河流..."
    git -C "$REPO_DIR" fetch origin "$other" 2>/dev/null || {
        warn "fetch origin/$other 失败，跳过该分支"
        return 0
    }

    local tmpdir
    tmpdir=$(mktemp -d)

    for f in "${RIVER_FILES[@]}"; do
        local remote_content
        remote_content=$(git -C "$REPO_DIR" show "origin/$other:$RIVER_DIR/$f" 2>/dev/null || echo "")
        if [ -z "$remote_content" ]; then
            continue
        fi

        local local_file="$REPO_DIR/$RIVER_DIR/$f"
        local remote_tmp="$tmpdir/$f"
        mkdir -p "$(dirname "$remote_tmp")"
        echo "$remote_content" > "$remote_tmp"

        if [ ! -f "$local_file" ]; then
            echo "$remote_content" > "$local_file"
            log "[$other] 创建本地文件：$f"
            TOTAL_CREATED=$((TOTAL_CREATED + 1))
        else
            case "$f" in
                "智慧结晶库.md")
                    # 先做编号冲突检测：同号异义绝不自动合并，交 S00 裁决
                    local clash
                    clash=$(crystal_clash "$local_file" "$remote_tmp")
                    if [ -n "$clash" ]; then
                        err "[$other] 结晶库同号异义冲突，编号：$clash"
                        err "  已跳过自动合并（避免重复编号污染）。分支应改用临时号，合 main 时由 S00 分配正式号。"
                        CRYSTAL_CLASH=1
                        continue
                    fi
                    local combined
                    combined=$(cat "$local_file" "$remote_tmp" | awk '!seen[$0]++')
                    echo "$combined" > "$local_file"
                    log "[$other] 合并（append-only，已过编号冲突检测）：$f"
                    TOTAL_MERGED=$((TOTAL_MERGED + 1))
                    ;;
                "河流主干.md"|"DeepSeek干渠.md")
                    local combined
                    combined=$(cat "$local_file" "$remote_tmp" | awk '!seen[$0]++')
                    echo "$combined" > "$local_file"
                    log "[$other] 合并（append-only）：$f"
                    TOTAL_MERGED=$((TOTAL_MERGED + 1))
                    ;;
                "河流状态.md")
                    local local_time remote_time
                    local_time=$(grep -oP '最后更新：\K[0-9:-]+' "$local_file" 2>/dev/null || echo "0")
                    remote_time=$(grep -oP '最后更新：\K[0-9:-]+' "$remote_tmp" 2>/dev/null || echo "0")
                    if [[ "$remote_time" > "$local_time" ]]; then
                        echo "$remote_content" > "$local_file"
                        log "[$other] 对方状态更新（$remote_time > $local_time），采用：$f"
                        TOTAL_MERGED=$((TOTAL_MERGED + 1))
                    fi
                    ;;
            esac
        fi
    done

    rm -rf "$tmpdir"
}

# ============================================================
# 拉取河流：分站只对对方分支；main(S00) 从所有分站分支汇合
# ============================================================
pull_river() {
    detect_station
    check_river_exists

    TOTAL_MERGED=0
    TOTAL_CREATED=0
    CRYSTAL_CLASH=0

    local targets=()
    if [ -n "$OTHER_BRANCH" ]; then
        targets=("$OTHER_BRANCH")
    fi
    if [ "$MY_STATION" = "S00" ]; then
        targets=("${ALL_STATION_BRANCHES[@]}")
    fi
    if [ ${#targets[@]} -eq 0 ]; then
        warn "当前没有可汇合的对方分支"
        return 0
    fi
    log "本轮汇合目标分支：${targets[*]}"

    local br
    for br in "${targets[@]}"; do
        merge_from_branch "$br"
    done

    ok "拉取完成：创建 $TOTAL_CREATED 个，合并 $TOTAL_MERGED 个"

    verify_river_integrity

    if [ $TOTAL_MERGED -gt 0 ] || [ $TOTAL_CREATED -gt 0 ]; then
        # 此自动commit仅本地落盘，禁止据此直推main（main只走PR）；S00转临时分支走PR，见文件头纪律。
        log "自动commit河流合并..."
        git -C "$REPO_DIR" add "$RIVER_DIR/" 2>/dev/null || true
        git -C "$REPO_DIR" commit -m "$MY_STATION: 河流汇合器自动pull——从${targets[*]}合并河流文件

河流汇合器river_sync.sh pull自动执行：
- 汇合分支：${targets[*]}（main=S00从所有分站多分支汇合）
- append-only文件智能合并（河流主干/结晶库/DeepSeek干渠）
- 结晶库合并前做同号异义冲突检测，冲突不自动合并、交S00裁决
- 状态文件取最新版本" 2>/dev/null || warn "没有新内容需要commit"
    fi

    if [ $CRYSTAL_CLASH -eq 1 ]; then
        err "存在结晶编号同号异义冲突未自动合并，须 S00 大总站裁决后再汇合"
        return 2
    fi

    echo ""
    log "=== 河流汇合报告 ==="
    log "本站：$MY_STATION，汇合：${targets[*]}"
    log "创建文件：$TOTAL_CREATED，合并文件：$TOTAL_MERGED"
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

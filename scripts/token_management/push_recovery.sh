#!/bin/bash
# ============================================================
# 明旭分站Push失败自动恢复脚本 v1.0
# 
# 功能：
#   当git push失败时，自动诊断原因并恢复
#   支持的错误类型：
#     1. 认证失败（token无效/过期）
#     2. 远程有新提交（fetch first）
#     3. 有未暂存的改动（unstaged changes）
#     4. 冲突（CONFLICT）
#     5. 分支不存在
#     6. 网络问题
#
# 使用方法：
#   bash scripts/token_management/push_recovery.sh <分站ID>
#
# 作者：明旭
# 日期：2026-09-01
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

declare -A STATION_BRANCH
STATION_BRANCH["S00"]="main"
STATION_BRANCH["S01"]="s01-philosophy"
STATION_BRANCH["S02"]="s02-gaokao-arts"
STATION_BRANCH["S03"]="s03-divination"
STATION_BRANCH["S04"]="s04-coq"
STATION_BRANCH["S05"]="s05-info"

REPO_OWNER="192781-li"
REPO_NAME="mingbenlun"

print_info() { echo -e "${BLUE}[信息]${NC} $1"; }
print_success() { echo -e "${GREEN}[成功]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[警告]${NC} $1"; }
print_error() { echo -e "${RED}[错误]${NC} $1"; }
print_separator() { echo "============================================================"; }

# ============================================================
# 诊断函数
# ============================================================

diagnose_and_recover() {
    local STATION_ID="$1"
    local BRANCH="${STATION_BRANCH[$STATION_ID]}"
    
    print_separator
    echo -e "${BLUE}明旭分站Push失败自动恢复脚本 v1.0${NC}"
    print_separator
    echo ""
    print_info "分站: $STATION_ID"
    print_info "分支: $BRANCH"
    echo ""
    
    # ============================================================
    # 第1步：检查token是否配置
    # ============================================================
    print_info "第1步：检查Token配置..."
    
    local TOKEN=""
    local TOKEN_VAR="GITHUB_TOKEN_${STATION_ID}"
    
    if [ -n "${!TOKEN_VAR}" ]; then
        TOKEN="${!TOKEN_VAR}"
        print_success "找到分站专属token: $TOKEN_VAR"
    elif [ -n "$GITHUB_SUB_TOKEN" ]; then
        TOKEN="$GITHUB_SUB_TOKEN"
        print_warning "使用通用token: GITHUB_SUB_TOKEN"
    elif [ -f "$HOME/.mingxu/tokens/${STATION_ID}.token" ]; then
        TOKEN=$(cat "$HOME/.mingxu/tokens/${STATION_ID}.token" | tr -d '[:space:]')
        print_warning "从本地文件读取token"
    else
        print_error "未找到任何token！"
        echo ""
        echo "请配置token："
        echo "  export ${TOKEN_VAR}=\"你的GitHub Personal Access Token\""
        echo ""
        echo "或运行配置脚本："
        echo "  bash scripts/token_management/station_token_setup.sh $STATION_ID"
        return 1
    fi
    
    # 重新配置remote
    local AUTH_URL="https://${TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"
    git remote set-url origin "$AUTH_URL"
    print_success "Git remote已重新配置"
    
    # ============================================================
    # 第2步：验证token有效性
    # ============================================================
    print_info "第2步：验证Token有效性..."
    
    if git ls-remote --heads origin "$BRANCH" >/dev/null 2>&1; then
        print_success "Token有效，能访问仓库"
    else
        print_error "Token无效或权限不足！"
        echo ""
        echo "请检查："
        echo "  1. token是否正确（不要有多余空格）"
        echo "  2. token是否过期（GitHub Settings → Tokens）"
        echo "  3. token是否勾选了repo权限"
        echo ""
        echo "重新生成token：https://github.com/settings/tokens"
        return 1
    fi
    
    # ============================================================
    # 第3步：检查当前分支
    # ============================================================
    print_info "第3步：检查当前分支..."
    
    local CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
        print_warning "当前分支是 $CURRENT_BRANCH，应该是 $BRANCH"
        print_info "正在切换到 $BRANCH..."
        
        if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
            git checkout "$BRANCH"
        else
            git checkout -b "$BRANCH"
        fi
        print_success "已切换到 $BRANCH"
    else
        print_success "当前分支正确: $BRANCH"
    fi
    
    # ============================================================
    # 第4步：检查未暂存的改动
    # ============================================================
    print_info "第4步：检查未暂存的改动..."
    
    if ! git diff --quiet || ! git diff --cached --quiet; then
        print_warning "有未提交的改动，正在提交..."
        git add -A
        git commit -m "[$(date '+%Y-%m-%d %H:%M:%S')] 明旭-${STATION_ID}: 自动提交未保存的改动"
        print_success "未提交的改动已自动提交"
    else
        print_success "没有未提交的改动"
    fi
    
    # ============================================================
    # 第5步：拉取远程最新代码
    # ============================================================
    print_info "第5步：拉取远程最新代码..."
    
    # 检查远程分支是否存在
    if git ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH"; then
        # 远程分支存在，尝试pull
        if git pull --rebase origin "$BRANCH" 2>&1; then
            print_success "远程代码已同步"
        else
            # pull失败，可能有冲突
            print_warning "Pull失败，可能有冲突，正在处理..."
            
            # 检查是否有冲突
            if git status | grep -q "Unmerged paths"; then
                print_error "存在合并冲突！"
                echo ""
                echo "冲突文件："
                git diff --name-only --diff-filter=U
                echo ""
                echo "请手动解决冲突后："
                echo "  git add 冲突文件"
                echo "  git rebase --continue"
                echo "  git push origin $BRANCH"
                return 1
            else
                # 其他pull失败，尝试stash
                print_warning "尝试stash方式..."
                git stash
                git pull --rebase origin "$BRANCH"
                git stash pop
                git add -A
                git commit -m "[$(date '+%Y-%m-%d %H:%M:%S')] 明旭-${STATION_ID}: 合并远程更新"
                print_success "远程代码已同步（stash方式）"
            fi
        fi
    else
        print_warning "远程分支 $BRANCH 不存在，将在首次push时创建"
    fi
    
    # ============================================================
    # 第6步：推送
    # ============================================================
    print_info "第6步：推送到远程..."
    
    if git push origin "$BRANCH" 2>&1; then
        print_success "推送成功！"
        echo ""
        echo "远程分支：https://github.com/${REPO_OWNER}/${REPO_NAME}/tree/${BRANCH}"
        return 0
    else
        print_error "推送仍然失败！"
        echo ""
        echo "请检查："
        echo "  1. 网络连接是否正常"
        echo "  2. token是否有push权限（勾选repo）"
        echo "  3. 分支是否受保护（GitHub Settings → Branches）"
        echo ""
        echo "手动推送命令："
        echo "  git push origin $BRANCH"
        return 1
    fi
}

# ============================================================
# 主流程
# ============================================================

main() {
    local STATION_ID="$1"
    
    if [ -z "$STATION_ID" ]; then
        echo "用法：bash push_recovery.sh <分站ID>"
        echo ""
        echo "可用分站："
        for id in S00 S01 S02 S03 S04 S05; do
            echo "  $id - ${STATION_BRANCH[$id]}"
        done
        exit 1
    fi
    
    diagnose_and_recover "$STATION_ID"
}

main "$@"

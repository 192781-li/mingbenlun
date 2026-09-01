#!/bin/bash
# ============================================================
# 明旭分站网络问题一键诊断与修复脚本 v1.0
# 
# 功能：自动诊断并修复分站常见的网络/git/token问题
# 适用：所有分站（S00-S05），在分站运行的电脑上执行
#
# 使用方法：
#   bash scripts/token_management/station_network_fix.sh <分站ID>
#   例如：bash scripts/token_management/station_network_fix.sh S04
#
# 自动修复的问题：
#   1. token配置错误或丢失
#   2. git remote URL错误
#   3. git网络配置未优化（导致超时）
#   4. push冲突（远程有新提交）
#   5. 未提交的改动阻塞切换分支
#   6. git锁文件
#   7. 分支不存在
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

# 分站信息
declare -A STATION_BRANCH
declare -A STATION_TOKEN

STATION_BRANCH["S00"]="main"
STATION_BRANCH["S01"]="s01-philosophy"
STATION_BRANCH["S02"]="s02-gaokao-arts"
STATION_BRANCH["S03"]="s03-divination"
STATION_BRANCH["S04"]="s04-coq"
STATION_BRANCH["S05"]="s05-info"

# Token列表（从环境变量或参数获取，不硬编码）
# 使用时通过环境变量传入：
#   export TOKEN_S04="你的token"
#   bash station_network_fix.sh S04

REPO_URL="https://github.com/192781-li/mingbenlun.git"
REPO_DIR=""

print_info() { echo -e "${BLUE}[诊断]${NC} $1"; }
print_fix() { echo -e "${YELLOW}[修复]${NC} $1"; }
print_ok() { echo -e "${GREEN}[正常]${NC} $1"; }
print_error() { echo -e "${RED}[错误]${NC} $1"; }
print_separator() { echo "============================================================"; }

# ============================================================
# 主流程
# ============================================================

main() {
    local STATION_ID="$1"
    local TOKEN_VAR="TOKEN_${STATION_ID}"
    local TOKEN="${!TOKEN_VAR}"
    
    print_separator
    echo -e "${BLUE}明旭分站网络问题一键诊断与修复脚本 v1.0${NC}"
    print_separator
    echo ""
    
    if [ -z "$STATION_ID" ]; then
        print_error "请指定分站ID：bash station_network_fix.sh S04"
        exit 1
    fi
    
    if [ -z "${STATION_BRANCH[$STATION_ID]}" ]; then
        print_error "未知分站ID: $STATION_ID"
        exit 1
    fi
    
    local BRANCH="${STATION_BRANCH[$STATION_ID]}"
    
    echo "分站: $STATION_ID"
    echo "分支: $BRANCH"
    echo "Token环境变量: $TOKEN_VAR"
    echo ""
    
    # 如果没有通过环境变量传token，尝试从本地文件读取
    if [ -z "$TOKEN" ]; then
        if [ -f ~/.mingxu/tokens/$STATION_ID.token ]; then
            TOKEN=$(cat ~/.mingxu/tokens/$STATION_ID.token | tr -d '[:space:]')
            print_info "从本地文件读取token: ~/.mingxu/tokens/$STATION_ID.token"
        else
            print_error "未找到token！请先设置环境变量："
            echo "  export $TOKEN_VAR=\"你的GitHub token\""
            echo "  然后重新运行此脚本"
            exit 1
        fi
    fi
    
    # ============================================================
    # 第1步：定位仓库目录
    # ============================================================
    print_separator
    echo -e "${BLUE}第1步：定位仓库目录${NC}"
    print_separator
    
    # 尝试常见位置
    for dir in ~/Desktop/mingbenlun ~/mingbenlun ./mingbenlun /home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun; do
        if [ -d "$dir/.git" ]; then
            REPO_DIR="$dir"
            break
        fi
    done
    
    if [ -z "$REPO_DIR" ]; then
        print_error "未找到仓库！请先克隆仓库："
        echo "  cd ~/Desktop"
        echo "  git clone https://github.com/192781-li/mingbenlun.git"
        exit 1
    fi
    
    print_ok "仓库目录: $REPO_DIR"
    cd "$REPO_DIR"
    
    # ============================================================
    # 第2步：清理git锁文件
    # ============================================================
    print_separator
    echo -e "${BLUE}第2步：清理git锁文件${NC}"
    print_separator
    
    if [ -f .git/index.lock ]; then
        print_fix "发现git锁文件，正在删除..."
        rm -f .git/index.lock
        print_ok "锁文件已删除"
    else
        print_ok "没有锁文件"
    fi
    
    # ============================================================
    # 第3步：验证token有效性
    # ============================================================
    print_separator
    echo -e "${BLUE}第3步：验证Token有效性${NC}"
    print_separator
    
    local HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $TOKEN" https://api.github.com/user)
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_ok "Token有效（HTTP 200）"
    else
        print_error "Token无效（HTTP $HTTP_CODE）！"
        echo "请检查token是否正确，是否过期，是否有repo权限"
        exit 1
    fi
    
    # 保存token到本地文件
    mkdir -p ~/.mingxu/tokens
    echo "$TOKEN" > ~/.mingxu/tokens/$STATION_ID.token
    chmod 600 ~/.mingxu/tokens/$STATION_ID.token
    print_ok "Token已保存到本地文件"
    
    # ============================================================
    # 第4步：配置git remote
    # ============================================================
    print_separator
    echo -e "${BLUE}第4步：配置Git Remote${NC}"
    print_separator
    
    local AUTH_URL="https://${TOKEN}@github.com/192781-li/mingbenlun.git"
    
    # 检查当前remote
    local CURRENT_URL=$(git remote get-url origin 2>/dev/null || echo "")
    
    if [ "$CURRENT_URL" != "$AUTH_URL" ]; then
        print_fix "Git remote URL不正确，正在更新..."
        git remote set-url origin "$AUTH_URL"
        print_ok "Git remote已更新"
    else
        print_ok "Git remote正确"
    fi
    
    # 配置git user
    git config user.name "mingxu-$STATION_ID"
    git config user.email "mingxu-$STATION_ID@localhost"
    print_ok "Git用户已配置: mingxu-$STATION_ID"
    
    # ============================================================
    # 第5步：优化git网络配置
    # ============================================================
    print_separator
    echo -e "${BLUE}第5步：优化Git网络配置${NC}"
    print_separator
    
    git config --global http.postBuffer 524288000
    git config --global http.lowSpeedLimit 0
    git config --global http.lowSpeedTime 999999
    git config --global http.version HTTP/1.1
    git config --global https.postBuffer 524288000
    git config --global core.compression 0
    print_ok "网络配置已优化（大buffer、长超时、HTTP/1.1）"
    
    # ============================================================
    # 第6步：处理未提交的改动
    # ============================================================
    print_separator
    echo -e "${BLUE}第6步：处理未提交的改动${NC}"
    print_separator
    
    if ! git diff --quiet || ! git diff --cached --quiet; then
        print_fix "发现未提交的改动，正在stash..."
        git stash
        print_ok "未提交的改动已保存到stash"
    else
        print_ok "没有未提交的改动"
    fi
    
    # ============================================================
    # 第7步：切换到专属分支
    # ============================================================
    print_separator
    echo -e "${BLUE}第7步：切换到专属分支${NC}"
    print_separator
    
    # 检查本地分支是否存在
    if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
        git checkout "$BRANCH"
        print_ok "已切换到本地分支: $BRANCH"
    else
        # 检查远程分支是否存在
        if git ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH"; then
            git fetch origin "$BRANCH"
            git checkout -b "$BRANCH" "origin/$BRANCH"
            print_ok "已从远程创建并切换到分支: $BRANCH"
        else
            # 从main创建新分支
            git checkout main
            git pull origin main
            git checkout -b "$BRANCH"
            print_ok "已从main创建新分支: $BRANCH"
        fi
    fi
    
    # ============================================================
    # 第8步：拉取最新代码（解决冲突）
    # ============================================================
    print_separator
    echo -e "${BLUE}第8步：拉取最新代码（解决冲突）${NC}"
    print_separator
    
    # 先拉main的最新代码
    print_info "正在拉取main最新代码..."
    git fetch origin main
    
    # 把main合并到当前分支
    if git merge origin/main --no-edit 2>&1; then
        print_ok "main最新代码已合并到$BRANCH"
    else
        print_fix "合并冲突，正在尝试自动解决..."
        # 检查是否有冲突
        if git status | grep -q "Unmerged paths"; then
            print_error "存在合并冲突，需要手动解决："
            git diff --name-only --diff-filter=U
            echo ""
            echo "解决冲突后执行："
            echo "  git add 冲突文件"
            echo "  git commit -m '合并冲突'"
            exit 1
        else
            # 其他错误，尝试abort后重新merge
            git merge --abort 2>/dev/null || true
            print_fix "合并失败，尝试rebase方式..."
            git rebase origin/main 2>&1 || {
                print_error "Rebase也失败，请手动检查"
                exit 1
            }
            print_ok "Rebase成功"
        fi
    fi
    
    # 恢复stash
    if git stash list | grep -q "stash@{0}"; then
        print_info "正在恢复stash的改动..."
        if git stash pop 2>&1; then
            print_ok "stash改动已恢复"
        else
            print_fix "stash恢复有冲突，请手动解决后commit"
            git status
        fi
    fi
    
    # ============================================================
    # 第9步：测试push
    # ============================================================
    print_separator
    echo -e "${BLUE}第9步：测试Push${NC}"
    print_separator
    
    # 创建空提交测试
    git commit --allow-empty -m "网络修复验证测试 [skip ci]" 2>/dev/null || true
    
    if git push origin "$BRANCH" 2>&1; then
        print_ok "Push成功！网络连接正常"
        # 回滚测试提交
        git reset --soft HEAD~1 2>/dev/null || true
    else
        print_error "Push失败！"
        echo "可能原因："
        echo "  1. 网络不稳定 - 重试几次"
        echo "  2. 分支受保护 - 检查GitHub分支保护规则"
        echo "  3. Token权限不足 - 确认token勾选了repo权限"
        exit 1
    fi
    
    # ============================================================
    # 完成
    # ============================================================
    print_separator
    echo -e "${GREEN}诊断与修复完成！${NC}"
    print_separator
    echo ""
    echo "分站: $STATION_ID"
    echo "分支: $BRANCH"
    echo "仓库: $REPO_DIR"
    echo ""
    echo "已修复/验证："
    echo "  ✅ Token有效性"
    echo "  ✅ Git remote配置"
    echo "  ✅ Git网络优化"
    echo "  ✅ 未提交改动处理"
    echo "  ✅ 分支切换"
    echo "  ✅ 远程代码合并"
    echo "  ✅ Push测试"
    echo ""
    echo -e "${GREEN}现在可以正常干活了！${NC}"
    echo ""
    echo "常用命令："
    echo "  git add -A"
    echo "  git commit -m \"你的提交信息\""
    echo "  git push origin $BRANCH"
    echo ""
    echo "如果以后再遇到网络问题，重新运行此脚本即可。"
}

main "$@"

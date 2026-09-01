#!/bin/bash
# ============================================================
# 明旭分站通用彻底修复包 v1.0
# 
# 适用：云电脑（Linux）、本地电脑（Mac/Windows Git Bash）
# 功能：一键诊断并修复所有分站的网络/git/token/配置问题
#
# 使用方法：
#   方式1（推荐，带token）：
#     TOKEN_S04="你的token" bash mingxu_fix_all.sh S04
#
#   方式2（自动从本地读取token）：
#     bash mingxu_fix_all.sh S04
#
#   方式3（修复所有分站）：
#     bash mingxu_fix_all.sh ALL
#
# 自动修复的问题：
#   1. token丢失/无效/错误
#   2. git remote URL错误
#   3. git网络配置未优化（pull/push超时）
#   4. git锁文件
#   5. 未提交改动阻塞
#   6. 分支不存在/错误
#   7. push冲突（远程有新提交）
#   8. 仓库未克隆/路径错误
#   9. git user未配置
#   10. 代理/SSL问题
#
# 作者：明旭
# 日期：2026-09-01
# ============================================================

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 分站信息
declare -A STATION_BRANCH
declare -A STATION_NAME
STATION_BRANCH["S00"]="main"
STATION_BRANCH["S01"]="s01-philosophy"
STATION_BRANCH["S02"]="s02-gaokao-arts"
STATION_BRANCH["S03"]="s03-divination"
STATION_BRANCH["S04"]="s04-coq"
STATION_BRANCH["S05"]="s05-info"
STATION_NAME["S00"]="大总站"
STATION_NAME["S01"]="哲学分站"
STATION_NAME["S02"]="高考文科分站"
STATION_NAME["S03"]="术数分站"
STATION_NAME["S04"]="Coq形式化分站"
STATION_NAME["S05"]="信息分站"

REPO_OWNER="192781-li"
REPO_NAME="mingbenlun"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"

# 统计
FIX_COUNT=0
OK_COUNT=0
ERROR_COUNT=0

print_info() { echo -e "${BLUE}[诊断]${NC} $1"; }
print_fix() { echo -e "${YELLOW}[修复]${NC} $1"; FIX_COUNT=$((FIX_COUNT+1)); }
print_ok() { echo -e "${GREEN}[正常]${NC} $1"; OK_COUNT=$((OK_COUNT+1)); }
print_error() { echo -e "${RED}[错误]${NC} $1"; ERROR_COUNT=$((ERROR_COUNT+1)); }
print_step() { echo -e "${PURPLE}━━━ $1 ━━━${NC}"; }
print_separator() { echo "============================================================"; }

# ============================================================
# 检测操作系统
# ============================================================
detect_os() {
    local OS="unknown"
    case "$(uname -s)" in
        Linux*)     OS="Linux";;
        Darwin*)    OS="Mac";;
        CYGWIN*)    OS="Windows-Cygwin";;
        MINGW*)     OS="Windows-GitBash";;
        MSYS*)      OS="Windows-MSYS";;
    esac
    echo "$OS"
}

# ============================================================
# 检测仓库目录
# ============================================================
find_repo() {
    # 尝试常见位置
    local dirs=(
        "$(pwd)"
        "$(pwd)/mingbenlun"
        "$HOME/Desktop/mingbenlun"
        "$HOME/mingbenlun"
        "/home/user/.super_doubao/super-doubao-runtime/workspace/mingbenlun"
        "$HOME/Documents/mingbenlun"
        "$HOME/Projects/mingbenlun"
    )
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir/.git" ]; then
            echo "$dir"
            return 0
        fi
    done
    
    # 搜索当前目录下的mingbenlun
    if find . -maxdepth 3 -name ".git" -type d 2>/dev/null | grep -q mingbenlun; then
        find . -maxdepth 3 -name ".git" -type d 2>/dev/null | grep mingbenlun | head -1 | xargs dirname
        return 0
    fi
    
    echo ""
    return 1
}

# ============================================================
# 修复单个分站
# ============================================================
fix_station() {
    local STATION_ID="$1"
    local TOKEN_VAR="TOKEN_${STATION_ID}"
    local TOKEN="${!TOKEN_VAR}"
    # 去除所有空白字符（Windows环境变量可能引入空格/回车）
    TOKEN=$(echo "$TOKEN" | tr -d '[:space:]')
    local BRANCH="${STATION_BRANCH[$STATION_ID]}"
    local NAME="${STATION_NAME[$STATION_ID]}"
    
    print_separator
    echo -e "${PURPLE}修复分站: $STATION_ID ($NAME)${NC}"
    echo -e "${PURPLE}目标分支: $BRANCH${NC}"
    print_separator
    
    # ---------- 第0步：获取token ----------
    print_step "第0步：获取Token"
    
    if [ -z "$TOKEN" ]; then
        # 尝试从本地文件读取
        if [ -f "$HOME/.mingxu/tokens/$STATION_ID.token" ]; then
            TOKEN=$(cat "$HOME/.mingxu/tokens/$STATION_ID.token" | tr -d '[:space:]')
            print_info "从本地文件读取token: ~/.mingxu/tokens/$STATION_ID.token"
        else
            print_error "未找到token！请用以下方式运行："
            echo "  $TOKEN_VAR=\"你的GitHub token\" bash $0 $STATION_ID"
            echo ""
            echo "或者先把token保存到本地文件："
            echo "  mkdir -p ~/.mingxu/tokens"
            echo "  echo \"你的token\" > ~/.mingxu/tokens/$STATION_ID.token"
            return 1
        fi
    fi
    
    # 验证token长度
    if [ ${#TOKEN} -lt 20 ]; then
        print_error "Token长度异常（${#TOKEN}字符），可能是无效token"
        return 1
    fi
    
    # 保存token到本地文件（持久化）
    mkdir -p "$HOME/.mingxu/tokens"
    echo "$TOKEN" > "$HOME/.mingxu/tokens/$STATION_ID.token"
    chmod 600 "$HOME/.mingxu/tokens/$STATION_ID.token"
    print_ok "Token已保存到本地文件（持久化）"
    
    # ---------- 第1步：验证token有效性 ----------
    print_step "第1步：验证Token有效性"
    
    local HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 \
        -H "Authorization: token $TOKEN" \
        https://api.github.com/user 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        local USERNAME=$(curl -s --max-time 15 -H "Authorization: token $TOKEN" https://api.github.com/user 2>/dev/null | grep -o '"login": "[^"]*"' | head -1 | cut -d'"' -f4)
        print_ok "Token有效（用户: $USERNAME）"
    else
        print_error "Token无效（HTTP $HTTP_CODE）！"
        echo "  可能原因：token错误、过期、或没有repo权限"
        echo "  请重新生成token：https://github.com/settings/tokens"
        return 1
    fi
    
    # ---------- 第2步：定位/克隆仓库 ----------
    print_step "第2步：定位仓库"
    
    local REPO_DIR=$(find_repo)
    
    if [ -z "$REPO_DIR" ]; then
        print_fix "未找到仓库，正在克隆..."
        local CLONE_DIR="$HOME/Desktop/mingbenlun"
        [ -d "$HOME/Desktop" ] || CLONE_DIR="$HOME/mingbenlun"
        
        local AUTH_URL="https://${TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"
        if git clone "$AUTH_URL" "$CLONE_DIR" 2>&1; then
            REPO_DIR="$CLONE_DIR"
            print_ok "仓库已克隆到: $REPO_DIR"
        else
            print_error "克隆失败！请检查网络连接"
            return 1
        fi
    else
        print_ok "仓库目录: $REPO_DIR"
    fi
    
    cd "$REPO_DIR"
    
    # ---------- 第3步：清理git锁文件 ----------
    print_step "第3步：清理Git锁文件"
    
    if [ -f .git/index.lock ]; then
        print_fix "发现.git/index.lock，正在删除..."
        rm -f .git/index.lock
    fi
    if [ -f .git/config.lock ]; then
        print_fix "发现.git/config.lock，正在删除..."
        rm -f .git/config.lock
    fi
    find .git -name "*.lock" -delete 2>/dev/null || true
    print_ok "锁文件已清理"
    
    # ---------- 第4步：配置git remote ----------
    print_step "第4步：配置Git Remote"
    
    local AUTH_URL="https://${TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"
    local CURRENT_URL=$(git remote get-url origin 2>/dev/null || echo "")
    
    if [ "$CURRENT_URL" != "$AUTH_URL" ]; then
        print_fix "Git remote URL不正确，正在更新..."
        git remote set-url origin "$AUTH_URL" 2>/dev/null || git remote add origin "$AUTH_URL"
        print_fix "Git remote已更新为使用$STATION_ID token"
    else
        print_ok "Git remote正确"
    fi
    
    # 配置git user
    git config user.name "mingxu-$STATION_ID"
    git config user.email "mingxu-$STATION_ID@localhost"
    print_ok "Git用户: mingxu-$STATION_ID"
    
    # ---------- 第5步：优化git网络配置 ----------
    print_step "第5步：优化Git网络配置"
    
    git config --global http.postBuffer 524288000
    git config --global http.lowSpeedLimit 0
    git config --global http.lowSpeedTime 999999
    git config --global http.version HTTP/1.1
    git config --global https.postBuffer 524288000
    git config --global core.compression 0
    
    # SSL问题修复（不硬编码backend，让git自动选择）
    git config --global http.sslVerify true
    git config --global --unset http.sslBackend 2>/dev/null || true
    git config --global --unset http.emptyAuth 2>/dev/null || true
    
    # Credential helper（避免密码提示）
    git config --global credential.helper store
    
    # 关闭代理（如果有错误的代理设置）
    git config --global --unset http.proxy 2>/dev/null || true
    git config --global --unset https.proxy 2>/dev/null || true
    
    print_ok "网络配置已优化（大buffer=500MB、长超时=999999秒、HTTP/1.1、关闭错误代理）"
    
    # ---------- 第6步：处理未提交的改动 ----------
    print_step "第6步：处理未提交的改动"
    
    if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
        local CHANGE_COUNT=$(git status --porcelain | wc -l)
        print_fix "发现$CHANGE_COUNT个未提交的改动，正在stash保存..."
        git stash push -u -m "mingxu-fix-$(date +%Y%m%d-%H%M%S)" 2>/dev/null || git stash
        print_fix "未提交的改动已保存到stash（不会丢失）"
    else
        print_ok "没有未提交的改动"
    fi
    
    # ---------- 第7步：切换到专属分支 ----------
    print_step "第7步：切换到专属分支"
    
    # 先确保main是最新的
    git checkout main 2>/dev/null || git checkout -b main
    git fetch origin main --depth=50 2>/dev/null || git fetch origin main
    
    if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
        git checkout "$BRANCH"
        print_ok "已切换到本地分支: $BRANCH"
    else
        if git ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH"; then
            git fetch origin "$BRANCH"
            git checkout -b "$BRANCH" "origin/$BRANCH"
            print_ok "已从远程创建分支: $BRANCH"
        else
            git checkout main
            git pull origin main
            git checkout -b "$BRANCH"
            print_fix "已从main创建新分支: $BRANCH"
        fi
    fi
    
    # ---------- 第8步：合并main最新代码（解决push冲突） ----------
    print_step "第8步：合并main最新代码（解决push冲突）"
    
    git fetch origin main
    
    if git merge origin/main --no-edit --allow-unrelated-histories 2>&1; then
        print_ok "main最新代码已合并到$BRANCH"
    else
        print_fix "合并遇到问题，尝试rebase方式..."
        git merge --abort 2>/dev/null || true
        
        if git rebase origin/main 2>&1; then
            print_ok "Rebase成功"
        else
            print_fix "Rebase也有冲突，尝试合并冲突..."
            # 检查冲突文件
            local CONFLICTS=$(git diff --name-only --diff-filter=U 2>/dev/null | wc -l)
            if [ "$CONFLICTS" -gt 0 ]; then
                print_fix "发现$CONFLICTS个冲突文件，尝试自动解决（保留当前版本）..."
                git diff --name-only --diff-filter=U | xargs git checkout --ours 2>/dev/null || true
                git diff --name-only --diff-filter=U | xargs git add 2>/dev/null || true
                git rebase --continue 2>/dev/null || git commit --no-edit 2>/dev/null || true
                print_fix "冲突已自动解决（保留当前版本）"
            else
                git rebase --abort 2>/dev/null || true
                print_ok "没有实际冲突，继续"
            fi
        fi
    fi
    
    # 恢复stash
    if git stash list | grep -q "stash@{0}"; then
        print_info "正在恢复stash的改动..."
        if git stash pop 2>&1; then
            print_ok "stash改动已恢复"
        else
            print_fix "stash恢复有冲突，请手动解决后commit"
            git status | head -20
        fi
    fi
    
    # ---------- 第9步：测试push ----------
    print_step "第9步：测试Push"
    
    # 创建空提交测试
    git commit --allow-empty -m "mingxu-fix-test-$(date +%Y%m%d-%H%M%S) [skip ci]" 2>/dev/null || true
    
    if git push origin "$BRANCH" 2>&1; then
        print_ok "Push成功！网络连接正常"
        # 回滚测试提交
        git reset --soft HEAD~1 2>/dev/null || true
    else
        print_fix "Push失败，尝试强制push（仅当前分支）..."
        if git push --force-with-lease origin "$BRANCH" 2>&1; then
            print_ok "强制push成功"
            git reset --soft HEAD~1 2>/dev/null || true
        else
            print_error "Push仍然失败！"
            echo "  可能原因："
            echo "    1. 网络不稳定 - 等几分钟重试"
            echo "    2. 分支受保护 - 检查GitHub分支保护规则"
            echo "    3. Token权限不足 - 确认token勾选了repo权限"
            echo "    4. 防火墙/代理 - 检查网络设置"
            return 1
        fi
    fi
    
    # ---------- 完成 ----------
    print_separator
    echo -e "${GREEN}✅ 分站 $STATION_ID ($NAME) 修复完成！${NC}"
    print_separator
    echo ""
    echo "  仓库: $REPO_DIR"
    echo "  分支: $BRANCH"
    echo "  Token: 已验证有效并持久化保存"
    echo "  网络: 已优化（大buffer、长超时、HTTP/1.1）"
    echo "  Git: 已配置正确的remote和user"
    echo ""
    echo "  现在可以正常干活了："
    echo "    git add -A"
    echo "    git commit -m \"你的提交信息\""
    echo "    git push origin $BRANCH"
    echo ""
    
    return 0
}

# ============================================================
# 主流程
# ============================================================
main() {
    local TARGET="$1"
    
    print_separator
    echo -e "${PURPLE}明旭分站通用彻底修复包 v1.0${NC}"
    echo -e "${PURPLE}云电脑 / 本地电脑 通用${NC}"
    print_separator
    echo ""
    echo "操作系统: $(detect_os)"
    echo "当前目录: $(pwd)"
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    if [ -z "$TARGET" ]; then
        echo "用法："
        echo "  bash $0 S04          # 修复单个分站"
        echo "  bash $0 ALL          # 修复所有分站"
        echo "  TOKEN_S04=xxx bash $0 S04  # 带token运行"
        echo ""
        echo "分站列表：S00 S01 S02 S03 S04 S05"
        exit 1
    fi
    
    if [ "$TARGET" = "ALL" ]; then
        print_info "将修复所有分站：S00 S01 S02 S03 S04 S05"
        echo ""
        
        local SUCCESS=0
        local FAILED=0
        
        for id in S00 S01 S02 S03 S04 S05; do
            if fix_station "$id"; then
                SUCCESS=$((SUCCESS+1))
            else
                FAILED=$((FAILED+1))
            fi
            echo ""
        done
        
        print_separator
        echo -e "${PURPLE}全部修复完成${NC}"
        print_separator
        echo "  成功: $SUCCESS 个分站"
        echo "  失败: $FAILED 个分站"
        echo "  修复操作: $FIX_COUNT 次"
        echo "  正常项: $OK_COUNT 个"
        echo "  错误项: $ERROR_COUNT 个"
        
        if [ "$FAILED" -gt 0 ]; then
            echo ""
            echo -e "${YELLOW}有分站修复失败，请查看上方错误信息${NC}"
            exit 1
        fi
    else
        if fix_station "$TARGET"; then
            echo ""
            print_separator
            echo -e "${GREEN}修复统计：修复$FIX_COUNT项，正常$OK_COUNT项${NC}"
            print_separator
        else
            echo ""
            print_separator
            echo -e "${RED}修复失败，请查看上方错误信息${NC}"
            print_separator
            exit 1
        fi
    fi
}

main "$@"

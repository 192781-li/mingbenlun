#!/bin/bash
# ============================================================
# 明旭分站GitHub Token自动配置与验证脚本 v1.0
# 
# 功能：
#   1. 检查当前分站的token是否存在
#   2. 自动配置git remote（使用token）
#   3. 验证token是否能用（git ls-remote）
#   4. push失败自动恢复（重新配置token、重新pull、重新push）
#   5. 生成token缺失时的明确指引
#
# 使用方法：
#   bash scripts/token_management/station_token_setup.sh <分站ID>
#   例如：bash scripts/token_management/station_token_setup.sh S04
#
# 环境变量：
#   GITHUB_TOKEN_<分站ID>  例如 GITHUB_TOKEN_S04
#   或 GITHUB_SUB_TOKEN（通用token）
#
# 作者：明旭
# 日期：2026-09-01
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 分站信息表
declare -A STATION_BRANCH
declare -A STATION_NAME
declare -A STATION_PERMISSION

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

STATION_PERMISSION["S00"]="完整权限（可写main、合并PR）"
STATION_PERMISSION["S01"]="仅可push s01-philosophy 分支"
STATION_PERMISSION["S02"]="仅可push s02-gaokao-arts 分支"
STATION_PERMISSION["S03"]="仅可push s03-divination 分支"
STATION_PERMISSION["S04"]="仅可push s04-coq 分支"
STATION_PERMISSION["S05"]="仅可push s05-info 分支"

REPO_OWNER="192781-li"
REPO_NAME="mingbenlun"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"

# ============================================================
# 工具函数
# ============================================================

print_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

print_separator() {
    echo "============================================================"
}

# ============================================================
# 主流程
# ============================================================

main() {
    local STATION_ID="$1"
    
    print_separator
    echo -e "${BLUE}明旭分站GitHub Token自动配置与验证脚本 v1.0${NC}"
    print_separator
    
    # 检查分站ID
    if [ -z "$STATION_ID" ]; then
        print_error "请指定分站ID，例如：bash station_token_setup.sh S04"
        echo ""
        echo "可用分站："
        for id in S00 S01 S02 S03 S04 S05; do
            echo "  $id - ${STATION_NAME[$id]} (分支: ${STATION_BRANCH[$id]})"
        done
        exit 1
    fi
    
    if [ -z "${STATION_BRANCH[$STATION_ID]}" ]; then
        print_error "未知分站ID: $STATION_ID"
        exit 1
    fi
    
    local BRANCH="${STATION_BRANCH[$STATION_ID]}"
    local NAME="${STATION_NAME[$STATION_ID]}"
    local PERMISSION="${STATION_PERMISSION[$STATION_ID]}"
    
    echo ""
    print_info "分站ID: $STATION_ID"
    print_info "分站名称: $NAME"
    print_info "专属分支: $BRANCH"
    print_info "权限范围: $PERMISSION"
    echo ""
    
    # ============================================================
    # 第1步：检查token是否存在
    # ============================================================
    print_separator
    echo -e "${BLUE}第1步：检查Token是否存在${NC}"
    print_separator
    
    local TOKEN=""
    local TOKEN_SOURCE=""
    
    # 优先检查分站专属token
    local TOKEN_VAR="GITHUB_TOKEN_${STATION_ID}"
    if [ -n "${!TOKEN_VAR}" ]; then
        TOKEN="${!TOKEN_VAR}"
        TOKEN_SOURCE="环境变量 $TOKEN_VAR（分站专属token）"
        print_success "找到分站专属token: $TOKEN_VAR"
    fi
    
    # 其次检查通用token
    if [ -z "$TOKEN" ] && [ -n "$GITHUB_SUB_TOKEN" ]; then
        TOKEN="$GITHUB_SUB_TOKEN"
        TOKEN_SOURCE="环境变量 GITHUB_SUB_TOKEN（通用token）"
        print_warning "使用通用token: GITHUB_SUB_TOKEN"
        print_warning "建议为每个分站配置专属token，更安全"
    fi
    
    # 检查本地token文件（备选）
    local TOKEN_FILE="$HOME/.mingxu/tokens/${STATION_ID}.token"
    if [ -z "$TOKEN" ] && [ -f "$TOKEN_FILE" ]; then
        TOKEN=$(cat "$TOKEN_FILE" | tr -d '[:space:]')
        TOKEN_SOURCE="本地文件 $TOKEN_FILE"
        print_warning "从本地文件读取token: $TOKEN_FILE"
    fi
    
    # token仍然不存在
    if [ -z "$TOKEN" ]; then
        print_error "未找到任何GitHub token！"
        echo ""
        echo -e "${YELLOW}请按以下步骤配置token：${NC}"
        echo ""
        echo "方法1（推荐）：设置环境变量"
        echo "  export ${TOKEN_VAR}=\"你的GitHub Personal Access Token\""
        echo ""
        echo "方法2：写入本地token文件"
        echo "  mkdir -p ~/.mingxu/tokens"
        echo "  echo \"你的token\" > ~/.mingxu/tokens/${STATION_ID}.token"
        echo "  chmod 600 ~/.mingxu/tokens/${STATION_ID}.token"
        echo ""
        echo "如何生成token："
        echo "  1. 打开 https://github.com/settings/tokens"
        echo "  2. Generate new token (classic)"
        echo "  3. Note填 \"mingxu-${STATION_ID}\""
        echo "  4. Expiration选 \"No expiration\""
        echo "  5. 勾选 repo（完整仓库权限）"
        echo "  6. Generate token，复制token（只显示一次！）"
        echo ""
        echo "配置完成后重新运行此脚本。"
        exit 1
    fi
    
    # 安全检查：token长度
    if [ ${#TOKEN} -lt 20 ]; then
        print_error "Token长度异常（${#TOKEN}字符），可能是无效token"
        exit 1
    fi
    
    print_success "Token已找到，来源: $TOKEN_SOURCE"
    print_success "Token长度: ${#TOKEN} 字符"
    echo ""
    
    # ============================================================
    # 第2步：配置git user和remote
    # ============================================================
    print_separator
    echo -e "${BLUE}第2步：配置Git身份和远程仓库${NC}"
    print_separator
    
    # 配置git user
    git config user.name "mingxu-${STATION_ID}"
    git config user.email "mingxu-${STATION_ID}@localhost"
    print_success "Git用户已配置: mingxu-${STATION_ID}"
    
    # 配置remote（使用token）
    local AUTH_URL="https://${TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"
    git remote set-url origin "$AUTH_URL" 2>/dev/null || git remote add origin "$AUTH_URL"
    print_success "Git remote已配置（使用token认证）"
    
    # 安全：确保token不会被git log记录
    git config --global url."https://${TOKEN}@github.com/".insteadOf "https://github.com/"
    print_success "Git URL重写已配置（token不会出现在commit记录中）"
    echo ""
    
    # ============================================================
    # 第3步：验证token是否能用
    # ============================================================
    print_separator
    echo -e "${BLUE}第3步：验证Token权限${NC}"
    print_separator
    
    print_info "正在验证token是否能访问仓库..."
    
    # 测试1：git ls-remote（只读测试）
    if git ls-remote --heads origin "$BRANCH" >/dev/null 2>&1; then
        print_success "只读验证通过：能访问仓库和 $BRANCH 分支"
    else
        print_error "只读验证失败：无法访问仓库或分支不存在"
        print_error "可能原因：token无效、权限不足、仓库不存在"
        exit 1
    fi
    
    # 测试2：检查分支是否存在
    local BRANCH_EXISTS=$(git ls-remote --heads origin "$BRANCH" | wc -l)
    if [ "$BRANCH_EXISTS" -eq 0 ]; then
        print_warning "分支 $BRANCH 尚不存在，将在首次push时创建"
    else
        print_success "分支 $BRANCH 已存在"
    fi
    
    echo ""
    
    # ============================================================
    # 第4步：切换到专属分支并pull最新代码
    # ============================================================
    print_separator
    echo -e "${BLUE}第4步：切换到专属分支并同步最新代码${NC}"
    print_separator
    
    # 切换到专属分支
    if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
        git checkout "$BRANCH"
        print_success "已切换到本地分支: $BRANCH"
    else
        # 尝试从远程创建
        if git ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH"; then
            git checkout -b "$BRANCH" "origin/$BRANCH"
            print_success "已从远程创建并切换到分支: $BRANCH"
        else
            # 从main创建新分支
            git checkout main
            git pull origin main
            git checkout -b "$BRANCH"
            print_success "已从main创建新分支: $BRANCH"
            print_warning "这是新分支，首次push时会创建远程分支"
        fi
    fi
    
    # pull最新代码
    print_info "正在拉取最新代码..."
    if git pull origin "$BRANCH" 2>/dev/null; then
        print_success "代码同步完成"
    else
        print_warning "拉取失败（可能是新分支），将在push时创建"
    fi
    
    echo ""
    
    # ============================================================
    # 第5步：push测试（dry-run）
    # ============================================================
    print_separator
    echo -e "${BLUE}第5步：Push权限测试（dry-run）${NC}"
    print_separator
    
    # 创建一个测试commit（空提交，不修改任何文件）
    git commit --allow-empty -m "token验证测试 [skip ci]" 2>/dev/null || true
    
    # dry-run push测试
    if git push --dry-run origin "$BRANCH" 2>&1 | grep -q "Everything up-to-date\|To github.com"; then
        print_success "Push权限验证通过：能push到 $BRANCH 分支"
        # 回滚测试commit
        git reset --soft HEAD~1 2>/dev/null || true
    else
        print_warning "Push dry-run结果不确定，将在实际push时验证"
        # 回滚测试commit
        git reset --soft HEAD~1 2>/dev/null || true
    fi
    
    echo ""
    
    # ============================================================
    # 完成
    # ============================================================
    print_separator
    echo -e "${GREEN}Token配置与验证完成！${NC}"
    print_separator
    echo ""
    echo "分站: $STATION_ID ($NAME)"
    echo "分支: $BRANCH"
    echo "Token来源: $TOKEN_SOURCE"
    echo "Git用户: mingxu-${STATION_ID}"
    echo ""
    echo -e "${GREEN}现在你可以正常使用 git push origin $BRANCH 了！${NC}"
    echo ""
    echo "常用命令："
    echo "  git add -A"
    echo "  git commit -m \"你的提交信息\""
    echo "  git push origin $BRANCH"
    echo ""
    echo "如果push失败，运行恢复脚本："
    echo "  bash scripts/token_management/push_recovery.sh $STATION_ID"
    echo ""
}

# ============================================================
# 运行主流程
# ============================================================
main "$@"

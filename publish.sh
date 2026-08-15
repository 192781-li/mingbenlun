#!/bin/bash
# 明本快速发布：构建 + 上传飞书云空间
# 用法：bash publish.sh          # 构建HTML+MD并上传
#       bash publish.sh --build-only  # 只构建不上传
set -e
cd "$(dirname "$0")"

MD_TOKEN="YTpgbYHlnoPLD9xjp8McxI7xnYg"
HTML_TOKEN="Cvsib1KDhoasfBxJEe1cc1xen3O"

echo "=== 明本发布 $(date '+%Y-%m-%d %H:%M:%S') ==="

# 1. 构建
echo "[1/3] 构建合订本..."
bash 生命论_模块化/build.sh --html-only

# 2. 检查
if [ ! -f "生命论合订本_最新.md" ]; then
    echo "✗ MD文件不存在，终止"
    exit 1
fi

if [ "$1" = "--build-only" ]; then
    echo "✓ 构建完成（跳过上传）"
    exit 0
fi

# 3. 上传飞书
echo "[2/3] 上传MD到飞书..."
lark-cli markdown +overwrite --file-token "$MD_TOKEN" --file "生命论合订本_最新.md" --as user --format json 2>&1 | grep -o '"ok":[a-z]*'

echo "[3/3] 上传HTML到飞书..."
lark-cli drive +upload --file "生命论（明本论）合订本.html" --file-token "$HTML_TOKEN" --as user --format json 2>&1 | grep -o '"ok":[a-z]*'

echo ""
echo "✓ 发布完成"
echo "  MD:   https://my.feishu.cn/file/$MD_TOKEN"
echo "  HTML: https://my.feishu.cn/file/$HTML_TOKEN"

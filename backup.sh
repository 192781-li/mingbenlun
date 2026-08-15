#!/bin/bash
# 明本备份脚本：技能恢复 + 本地提交 + 全量打包
# 用法：bash backup.sh [--full]
set -e
cd "$(dirname "$0")"
echo "=== 明本备份 $(date '+%Y-%m-%d %H:%M:%S') ==="

# 0. 技能文件自愈：环境重置会清空 .user_skills，从 workspace 源恢复
#    技能发现机制扫描的是 workspace/.user_skills/，不是 runtime/user_skills/
SKILL_ROOT=".user_skills"
mkdir -p "$SKILL_ROOT"

for skill in mingben-workbench mingben-output; do
    if [ -d "$skill" ]; then
        # workspace 根目录有源（mingben-workbench 在根目录，mingben-output 只在 .user_skills）
        SRC="$skill"
    elif [ -d "$SKILL_ROOT/$skill" ]; then
        continue  # 只在 .user_skills 里有，不需要恢复
    else
        echo "⚠ 找不到技能源: $skill，跳过"
        continue
    fi

    DST="$SKILL_ROOT/$skill"
    if [ ! -d "$DST" ] || [ ! -f "$DST/SKILL.md" ]; then
        echo "⚠ 技能 $skill 丢失，正在恢复..."
        mkdir -p "$DST"
        cp -r "$SRC"/* "$DST"/
        echo "✓ $skill 已恢复"
    else
        diff -rq "$SRC" "$DST" >/dev/null 2>&1 || {
            echo "⚠ 技能 $skill 不一致，正在同步..."
            cp -r "$SRC"/* "$DST"/
            echo "✓ $skill 已同步"
        }
    fi
done

# 1. 本地提交
git add -A
if git diff --cached --quiet; then
    echo "✓ 无变更需要提交"
else
    msg="自动备份 $(date '+%Y-%m-%d %H:%M')"
    git commit -m "$msg"
    echo "✓ 已提交: $msg"
fi

# 2. 全量打包
mkdir -p 备份
DATE=$(date '+%Y%m%d')

# git bundle（完整版本历史）
git bundle create "备份/生命论_源码_${DATE}.bundle" --all 2>/dev/null

# 全量tar.gz
tar czf "备份/生命论_全量_${DATE}.tar.gz" \
    --exclude='.git' \
    --exclude='shengminglun_full_*' \
    --exclude='shengminglun_all_docs' \
    --exclude='生命论_输出' \
    --exclude='电子书' \
    --exclude='备份' \
    --exclude='*.zip' \
    生命论_模块化/ \
    mingben-workbench/ \
    mingben-output/ \
    .user_skills/ \
    publish_style.tex html_header.html \
    backup.sh sync.sh \
    生命论合订本_最新.md \
    2>/dev/null || true

# 最新构建产物
[ -f "生命论（明本论）合订本_出版级排版.pdf" ] && cp "生命论（明本论）合订本_出版级排版.pdf" 备份/
[ -f "生命论（明本论）合订本.html" ] && cp "生命论（明本论）合订本.html" 备份/

# 清理7天前的备份
find 备份/ -name "*.bundle" -mtime +7 -delete 2>/dev/null
find 备份/ -name "*.tar.gz" -mtime +7 -delete 2>/dev/null

echo "✓ 备份目录: $(du -sh 备份/ | cut -f1)"
echo "=== 备份完成 ==="

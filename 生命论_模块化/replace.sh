#!/bin/bash
# 快速替换模块并重新构建
# 用法：
#   bash replace.sh <模块关键词> <新文件>   # 替换指定模块
#   bash replace.sh --list                   # 列出所有模块
#   bash replace.sh --add <卷目录> <新文件>  # 在指定卷末尾新增一篇
#
# 示例：
#   bash replace.sh 胶球 新章节.md
#   bash replace.sh "篇三_阶级" 新的第三篇.md
#   bash replace.sh --list
#   bash replace.sh --add 05_卷五_解放论 新增一篇.md

set -e
cd "$(dirname "$0")/.."
MODDIR="生命论_模块化"

if [ "$1" = "--list" ]; then
    echo "=== 模块清单 ==="
    echo "00_总序与导论.md"
    while IFS= read -r f; do
        [ -n "$f" ] && echo "$f"
    done < "$MODDIR/manifest.txt"
    exit 0
fi

if [ "$1" = "--add" ]; then
    TARGET_DIR="$MODDIR/$2"
    NEWFILE="$3"
    if [ ! -d "$TARGET_DIR" ]; then
        echo "错误：卷目录 $TARGET_DIR 不存在"
        echo "可用目录："
        ls -d "$MODDIR"/*/
        exit 1
    fi
    if [ ! -f "$NEWFILE" ]; then
        echo "错误：新文件 $NEWFILE 不存在"
        exit 1
    fi
    # 复制新文件到目标目录
    BASENAME=$(basename "$NEWFILE")
    cp "$NEWFILE" "$TARGET_DIR/$BASENAME"
    # 添加到manifest（在该卷最后一个文件后插入，而非追加到文件末尾）
    ENTRY="$2/$BASENAME"
    MANIFEST="$MODDIR/manifest.txt"
    if grep -qF "$ENTRY" "$MANIFEST"; then
        echo "已存在于manifest: $ENTRY"
    else
        # 找到该卷最后一行的行号，在其后插入
        LAST_LINE=$(grep -n "^$2/" "$MANIFEST" | tail -1 | cut -d: -f1)
        if [ -n "$LAST_LINE" ]; then
            sed -i "${LAST_LINE}a\\${ENTRY}" "$MANIFEST"
        else
            echo "$ENTRY" >> "$MANIFEST"
        fi
        echo "已添加：$ENTRY（插入到$2末尾）"
    fi
    echo "重新构建..."
    bash "$MODDIR/build.sh" --html-only
    exit 0
fi

# 替换模式
KEYWORD="$1"
NEWFILE="$2"
if [ -z "$KEYWORD" ] || [ -z "$NEWFILE" ]; then
    echo "用法：bash replace.sh <模块关键词> <新文件>"
    echo "      bash replace.sh --list"
    exit 1
fi
if [ ! -f "$NEWFILE" ]; then
    echo "错误：新文件 $NEWFILE 不存在"
    exit 1
fi

# 在manifest和00文件中查找匹配模块
FOUND=""
for f in "00_总序与导论.md" $(cat "$MODDIR/manifest.txt"); do
    if echo "$f" | grep -q "$KEYWORD"; then
        FOUND="$f"
        break
    fi
done

if [ -z "$FOUND" ]; then
    echo "错误：找不到包含 '$KEYWORD' 的模块"
    echo "用 --list 查看所有模块"
    exit 1
fi

echo "替换模块：$FOUND"
cp "$NEWFILE" "$MODDIR/$FOUND"
echo "已替换。重新构建HTML..."
bash "$MODDIR/build.sh" --html-only
echo ""
echo "HTML已更新。如需PDF：bash $MODDIR/build.sh --pdf-only"

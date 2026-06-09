#!/usr/bin/env bash
#
# 代码格式自动 Hook
# 写入/编辑代码后自动格式化
#

FILE="$1"
[ -z "$FILE" ] && exit 0

# 获取文件扩展名
EXT="${FILE##*.}"

case "$EXT" in
    py)
        # Python: 使用 black 格式化
        if command -v black &> /dev/null; then
            black "$FILE" 2>/dev/null || true
        fi
        ;;
    ts|tsx|js|jsx)
        # JavaScript/TypeScript: 使用 prettier
        if command -v prettier &> /dev/null; then
            prettier --write "$FILE" 2>/dev/null || true
        fi
        ;;
    go)
        # Go: 使用 gofmt
        if command -v gofmt &> /dev/null; then
            gofmt -w "$FILE" 2>/dev/null || true
        fi
        ;;
esac

echo "{}"
exit 0

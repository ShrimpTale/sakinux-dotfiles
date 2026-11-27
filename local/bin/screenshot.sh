#!/bin/bash
# 区域截图：框选 → 保存到 ~/Pictures/screenshots/ + 复制到剪贴板
set -u
DIR="$HOME/Pictures/screenshots"
mkdir -p "$DIR"
FILE="$DIR/screenshot-$(date +%Y%m%d-%H%M%S).png"

# 框选区域（ESC 取消则退出）
GEOM=$(slurp 2>/dev/null) || exit 0

grim -g "$GEOM" "$FILE" || exit 1
wl-copy < "$FILE"
notify-send -a "截图" "已保存到剪贴板" "$FILE"

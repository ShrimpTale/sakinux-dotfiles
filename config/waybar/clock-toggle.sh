#!/bin/bash
# 点击时钟：时间 <-> 日期 视图切换，并通知 waybar 立即刷新
STATE="${XDG_CACHE_HOME:-$HOME/.cache}/waybar-clock-mode"

if [ -f "$STATE" ] && [ "$(cat "$STATE")" = "date" ]; then
    echo "time" > "$STATE"
else
    echo "date" > "$STATE"
fi

pkill -RTMIN+1 waybar

#!/usr/bin/env bash
# 重启 Wi-Fi 菜单（供 hyprctl exec / 调试用）；按锁文件里的 pid 杀，避免误伤
LOCK="${XDG_RUNTIME_DIR:-/run/user/1000}/wifi-menu.pid"
pid=$(cat "$LOCK" 2>/dev/null)
if [ -n "$pid" ] && [ "$pid" -gt 1 ] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null
    sleep 0.6
fi
rm -f "$LOCK" 2>/dev/null
setsid $HOME/.local/bin/wifi-menu >/dev/null 2>&1 &

#!/usr/bin/env bash
# mpris-watch.sh — 让 waybar 的音乐模块在 MPRIS 状态一变就立刻重跑（不必等 1s 轮询）
#
# 原理：监听会话总线上所有 MPRIS 播放器的 PropertiesChanged（Metadata / PlaybackStatus）
# 与 Seeked，收到就给 waybar 发 SIGRTMIN+8；waybar config 里音乐模块的 "signal": 8
# 会让它立刻重跑 exec。
#
# 安全阀：老配置/老 waybar（不认识 "signal": 8）里没有这一项时**不发** RT 信号 ——
# 未注册处理函数的实时信号会直接杀掉 waybar，所以发信号前必须确认 config 里有 signal 8。
#
# 兜底：waybar 各模块仍保留 "interval": 1，本脚本挂了也只是回到旧的 1s 轮询。

set -u

CONFIG="${WAYBAR_CONFIG:-$HOME/.config/waybar/config}"

# 单实例：重复启动（重启 waybar / 重新登录）时直接退出
exec 9>"${XDG_RUNTIME_DIR:-/tmp}/mpris-watch.lock"
flock -n 9 || exit 0

notify_waybar() {
  pgrep -x waybar >/dev/null 2>&1 || return 0
  grep -q '"signal"[[:space:]]*:[[:space:]]*8' "$CONFIG" 2>/dev/null || return 0
  pkill -RTMIN+8 -x waybar 2>/dev/null || true
}

while :; do
  dbus-monitor --session "type='signal',path='/org/mpris/MediaPlayer2'" 2>/dev/null |
    while IFS= read -r line; do
      case "$line" in
        *member=PropertiesChanged* | *member=Seeked*)
          sleep 0.05          # 合并同一轮里的多条信号（Metadata + PlaybackStatus 常常一起到）
          notify_waybar
          ;;
      esac
    done
  sleep 1                      # dbus-monitor 退出（会话总线重启等）→ 稍后重连
done

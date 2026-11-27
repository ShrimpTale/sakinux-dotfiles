#!/usr/bin/env bash
# hypridle 熄屏/亮屏调用脚本（Hyprland 0.56 新 dispatch 语法）
# 用法: hypr-dpms.sh off | on
export HYPRLAND_INSTANCE_SIGNATURE="${HYPRLAND_INSTANCE_SIGNATURE:-$(ls /run/user/1000/hypr/ 2>/dev/null | head -1)}"
case "$1" in
    off) state="false" ;;
    on)  state="true"  ;;
    *)   echo "用法: $0 off|on"; exit 1 ;;
esac
hyprctl dispatch "hl.dsp.dpms($state)"

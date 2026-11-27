#!/bin/sh
# waybar 温度显示 — 滤除 x86_pkg_temp 瞬时伪影（单次执行模式）
# waybar 每 interval 秒重新执行本脚本；脚本输出一行 JSON 后退出。
#   - 双读滤波：间隔 1s 读两次；两次一致 → 真实值直接接受
#   - 两次不一致 → 伪影，只接受与上次显示值接近（≤12°C）的那个
#   - 上次值存于缓存文件（单次执行跨调用记忆）
zone=/sys/class/thermal/thermal_zone9/temp
state="${XDG_CACHE_HOME:-$HOME/.cache}/waybar-temp-prev"
prev=$(cat "$state" 2>/dev/null) || prev=""
v1=$(cat "$zone" 2>/dev/null) || v1=0
sleep 1
v2=$(cat "$zone" 2>/dev/null) || v2=0
d=$((v1 > v2 ? v1 - v2 : v2 - v1))
if [ -n "$prev" ]; then
    if [ "$d" -le 3000 ]; then
        prev=$v2
    else
        for v in "$v1" "$v2"; do
            dp=$((v > prev ? v - prev : prev - v))
            [ "$dp" -le 12000 ] && prev=$v
        done
    fi
else
    [ "$d" -le 3000 ] || exit 0   # 首轮两次不一致：不输出，下轮再试
    prev=$v2
fi
t=$((prev / 1000))
cls=normal
[ "$t" -ge 80 ] && cls=critical
printf '{"text":"%d°C","class":"%s"}\n' "$t" "$cls"
echo "$prev" > "$state" 2>/dev/null || true

#!/usr/bin/env bash
# waybar 电池模块（custom/battery）
# 为什么不用内置 battery 模块：
#   waybar 在 AC 在线时会把 sysfs 的 "Not charging"/"Discharging" 改写成 "Plugged"，
#   format-not-charging / format-full 都不会命中，只能回落到 format。
#   Redmi Book 16 2024 的 EC 会在 ~98% 停止充电（无软件限充，纯粹是电量计漂移），
#   所以这里自己判定"充满"，并给出真实电量 + 健康度。
BAT=BAT0
D=/sys/class/power_supply/$BAT
FULL_AT=96   # 插电、已停充、且电量 >= 此值 => 视为充满

cap=$(cat "$D/capacity" 2>/dev/null)
st=$(cat "$D/status" 2>/dev/null)
ef=$(cat "$D/energy_full" 2>/dev/null)
en=$(cat "$D/energy_now" 2>/dev/null)
ed=$(cat "$D/energy_full_design" 2>/dev/null)
: "${cap:=0}" "${st:=Unknown}" "${ef:=0}" "${en:=0}" "${ed:=0}"

ac=0
for a in /sys/class/power_supply/ADP*; do
  [ -f "$a/online" ] && [ "$(cat "$a/online")" = "1" ] && ac=1
done

# 健康度 = 满电容量 / 设计容量；同时给出 Wh 形式（m/n Wh）
read -r health wh_f wh_d <<<"$(awk -v ef="$ef" -v ed="$ed" 'BEGIN{
  h = (ed > 0) ? ef*100/ed : 0;
  printf "%.1f %.1f %.0f", h, ef/1000000, ed/1000000 }')"

icons=("󰂎" "󰁺" "󰁻" "󰁼" "󰁽" "󰁾" "󰁿" "󰂀" "󰂁" "󰂂" "󰁹")
idx=$(( cap * 10 / 100 )); [ "$idx" -gt 10 ] && idx=10; [ "$idx" -lt 0 ] && idx=0
ico=${icons[$idx]}

if [ "$st" = "Charging" ]; then
  text="󰂄充电中喵${cap}%"; cls="charging"
elif [ "$ac" = "1" ] && [ "$st" != "Discharging" ] && [ "$cap" -ge "$FULL_AT" ]; then
  text="󰁹充满了喵"; cls="full"
elif [ "$ac" = "1" ] && [ "$st" != "Discharging" ]; then
  text="󰚥插电待机${cap}%"; cls="plugged"
elif [ "$ac" = "1" ]; then
  text="${ico}${cap}%（插电放电中）"; cls="discharging"
else
  text="${ico}${cap}%↓"; cls="discharging"
fi
[ "$cap" -le 15 ] && cls="critical"
[ "$cap" -le 30 ] && [ "$cls" != "critical" ] && cls="warning"

tooltip="电量 ${cap}%\n健康度 ${health}%（${wh_f}/${wh_d} Wh）"

printf '{"text":"%s","tooltip":"%s","class":"%s"}\n' "$text" "$tooltip" "$cls"

#!/usr/bin/env bash
# media-player.sh — waybar 的媒体小控件（显示 + 控制）
#
# 数据来源：MPRIS（playerctl）
#   1) Apple Music —— Sidra 自带 MPRIS（org.mpris.MediaPlayer2.sidra）
#   2) 网页播放   —— 浏览器自带 MPRIS（Firefox 实测能读出哔哩哔哩的标题/进度/封面/URL）
# 优先级（主人指定 2026-09-23）：**两者同时在播时显示 Apple Music**；
#   Apple Music 没在播才轮到网页；两个都没在播、Apple Music 只是暂停 → 仍显示 Apple Music
#   （方便直接点开继续放）；Sidra 关掉且浏览器有媒体 → 显示网页。
#
# 显示（waybar exec 调用，输出 JSON）：
#   show-prev / show-toggle / show-next / show-title
# 控制（on-click、滚轮）：
#   act-prev / act-toggle / act-next / act-raise / act-seek-fwd / act-seek-back
#
# 两个来源都没有 → 显示模式输出空，配合 waybar 的 hide-empty-text 整组隐藏。
# 注意：控制动作只作用于「当前显示的那个播放器」。

set -u

APPLE="sidra"                                                            # 第一优先
BROWSER_RE='^(firefox|librewolf|chromium|chrome|brave|vivaldi|zen|edge|opera)[.]'  # 第二优先（浏览器 MPRIS）
SEP='§'

command -v playerctl >/dev/null 2>&1 || exit 0

# 所有 playerctl 调用都加超时：某个播放器不回应时 D-Bus 默认要等 ~25 秒，
# 那会把 waybar 这条音乐模块一起冻在旧歌上（2026-11-27 实测：切歌后栏最多落后 ~2.3s）。
PW_T=1.5
PW_LOG="${XDG_RUNTIME_DIR:-/tmp}/waybar-media.log"
pctl() {
  timeout -k 0.5 "$PW_T" playerctl "$@" 2>/dev/null
  local rc=$?
  if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
    if [ "$(stat -c %s "$PW_LOG" 2>/dev/null || echo 0)" -gt 65536 ]; then
      tail -n 50 "$PW_LOG" > "$PW_LOG.new" 2>/dev/null && mv "$PW_LOG.new" "$PW_LOG"
    fi
    printf '%s timeout: playerctl %s\n' "$(date '+%F %T')" "$*" >> "$PW_LOG" 2>/dev/null || true
  fi
  return 0
}

list_players() { pctl -l; }

# ── 选当前要显示的播放器 ─────────────────────────────────────────
# 每个播放器只查一次 status（旧版同一秒里查了两遍，播放器卡顿时白等一倍超时）
players="$(list_players)"
apple="$(printf '%s\n' "$players" | grep -x -m1 "$APPLE" || true)"
browser="$(printf '%s\n' "$players" | grep -m1 -E "$BROWSER_RE" || true)"

apple_status=""; browser_status=""
[ -n "$apple" ]   && apple_status="$(pctl -p "$apple" status)"
[ -n "$browser" ] && browser_status="$(pctl -p "$browser" status)"

active=""; kind="apple"; status=""
if [ -n "$apple" ] && [ "$apple_status" = "Playing" ]; then
  active="$apple"; status="$apple_status"                      # 同时在播 → Apple Music 优先
elif [ -n "$browser" ] && [ "$browser_status" = "Playing" ]; then
  active="$browser"; kind="web"; status="$browser_status"
elif [ -n "$apple" ]; then
  active="$apple"; status="$apple_status"
elif [ -n "$browser" ]; then
  active="$browser"; kind="web"; status="$browser_status"
fi
[ -n "$active" ] || exit 0

# ── 动作模式：执行就退出 ─────────────────────────────────────────
sel=""; [ "$kind" = "web" ] && sel="web"
case "${1:-}" in
  act-toggle)    pctl -p "$active" play-pause  >/dev/null 2>&1; exit 0 ;;
  act-next)      pctl -p "$active" next        >/dev/null 2>&1; exit 0 ;;
  act-prev)      pctl -p "$active" previous    >/dev/null 2>&1; exit 0 ;;
  act-seek-fwd)  pctl -p "$active" position 10+ >/dev/null 2>&1; exit 0 ;;
  act-seek-back) pctl -p "$active" position 10- >/dev/null 2>&1; exit 0 ;;
  act-raise)
    if [ "$kind" = "apple" ]; then
      gdbus call --session --dest "org.mpris.MediaPlayer2.$active" \
        --object-path /org/mpris/MediaPlayer2 \
        --method org.mpris.MediaPlayer2.Raise >/dev/null 2>&1
    else
      # 浏览器：按窗口类名找窗口拉前台（Firefox 的 MPRIS Raise 不保证真的抬窗）
      base="$(printf '%s' "$active" | cut -d. -f1)"
      addr="$(hyprctl clients -j 2>/dev/null \
              | jq -r --arg b "$base" '.[] | select((.class // "" | ascii_downcase) | test($b)) | .address' 2>/dev/null \
              | head -1)"
      if [ -n "$addr" ] && [ "$addr" != "null" ]; then
        hyprctl dispatch focuswindow "address:$addr" >/dev/null 2>&1
      else
        gdbus call --session --dest "org.mpris.MediaPlayer2.$active" \
          --object-path /org/mpris/MediaPlayer2 \
          --method org.mpris.MediaPlayer2.Raise >/dev/null 2>&1
      fi
    fi
    exit 0 ;;
esac

# ── 显示模式（status 已在上面查过一次，不再重复）─────────────────
meta="$(pctl -p "$active" metadata --format \
  "{{title}}${SEP}{{artist}}${SEP}{{album}}${SEP}{{xesam:url}}${SEP}{{duration(position)}}${SEP}{{duration(mpris:length)}}")"

# 交给 jq 组装：转义安全、按字符（不是字节）截断，中日文标题不会被切坏
jq -nc --arg mode "${1:-}" --arg st "$status" --arg kind "$kind" --arg meta "$meta" '
  def clip($s; $n): if ($s | length) > $n then ($s[0:($n - 1)] + "…") else $s end;

  ($meta | split("§")) as $f |
  ($f[0] // "") as $title  | ($f[1] // "") as $artist | ($f[2] // "") as $album |
  ($f[3] // "") as $url    | ($f[4] // "") as $pos    | ($f[5] // "") as $len |

  # 来源细分：Apple Music / 哔哩哔哩 / 其它网页
  (if $kind == "apple" then "apple"
   elif ($url | test("bilibili\\.com")) then "bili"
   else "web" end) as $src |
  (if $src == "apple" then "Apple Music"
   elif $src == "bili" then "哔哩哔哩"
   else "网页播放" end) as $srcName |
  (if $src == "apple" then " ｜ 右键 回到 Sidra 窗口" else "" end) as $raiseHint |

  (if $st == "Playing" then "playing" else "paused" end) as $state |

  (clip($title; 26)) as $t | (clip($artist; 14)) as $a |
  (if $src == "apple" then
     (if $t == "" then "" elif $a == "" then $t else "\($t) — \($a)" end)
   elif $src == "bili" then
     (if $t == "" then "" else "B站 · " + clip($title; 30) end)
   else clip($title; 30) end) as $text |

  (if $mode == "show-prev" then {text: "\uf048", tooltip: "上一首 · \($srcName)"}
   elif $mode == "show-next" then {text: "\uf051", tooltip: "下一首 · \($srcName)"}
   elif $mode == "show-toggle" then
     {text: (if $st == "Playing" then "\uf04c" else "\uf04b" end),
      tooltip: ("\($srcName) · " + (if $st == "Playing" then "正在播放 · 左键 暂停" else "已暂停 · 左键 播放" end) + $raiseHint)}
   else
     {text: $text,
      tooltip: ("\($srcName) · " + (if $st == "Playing" then "正在播放" else "已暂停" end) + "\n"
                + "\($title)\n"
                + (if $artist == "" then "" else "\($artist)\(if $album == "" then "" else " · " + clip($album; 28) end)\n" end)
                + "\($pos) / \($len)\n"
                + (if $src == "apple" then "左键 回到 Sidra 窗口" else "左键 回到浏览器窗口" end)
                + " ｜ 滚轮上/下 快进 / 快退 10 秒")}
   end) as $out |
  $out + {class: [$state, $src]}
'

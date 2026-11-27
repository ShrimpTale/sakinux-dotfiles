#!/usr/bin/env bash
# install.sh —— 把本仓库的配置安装到当前用户（Arch / Hyprland）
#
#   ./install.sh                 # 安装配置 + GTK 主题
#   ./install.sh --dry-run       # 只打印将要做什么
#   ./install.sh --no-gtk-themes # 跳过 ~/.themes（10MB，5 套 GTK 主题）
#   ./install.sh --with-theme-studio  # 额外把 theme-studio 装到 ~/.local/share 并链 zhuti
#
# 原则：
#   1. 已存在的同名文件先整体备份到 ~/.dotfiles-backup-<时间戳>/，不覆盖不丢东西
#   2. 仓库里家目录写成 @@HOME@@ 的文件（GTK CSS / jsonc / .desktop 不展开变量）在这里展开
#   3. 只拷贝，不删任何你没被覆盖的东西
set -uo pipefail

REPO="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
DRY=0; WITH_GTK=1; WITH_TS=0
for a in "$@"; do
    case "$a" in
        --dry-run) DRY=1 ;;
        --no-gtk-themes) WITH_GTK=0 ;;
        --with-theme-studio) WITH_TS=1 ;;
        -h|--help) sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "未知参数: $a" >&2; exit 2 ;;
    esac
done

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$HOME/.dotfiles-backup-$STAMP"
say() { printf '%s\n' "$*"; }
run() { if [ "$DRY" = 1 ]; then printf '  [dry] %s\n' "$*"; else "$@"; fi; }

# 装一个文件：必要时先备份
put() {
    local src="$1" dst="$2"
    if [ -e "$dst" ] && ! cmp -s "$src" "$dst"; then
        run mkdir -p "$(dirname "$BACKUP/${dst#$HOME/}")"
        run cp -p "$dst" "$BACKUP/${dst#$HOME/}"
    fi
    run mkdir -p "$(dirname "$dst")"
    run cp -p "$src" "$dst"
}

# 展开 @@HOME@@（只改这几个宿主不展开变量的文件）
expand_home() {
    for f in "$@"; do
        [ -f "$f" ] || continue
        grep -q '@@HOME@@' "$f" || continue
        if [ "$DRY" = 1 ]; then
            printf '  [dry] sed @@HOME@@ → %s  %s\n' "$HOME" "$f"
        else
            sed -i "s|@@HOME@@|$HOME|g" "$f"
        fi
    done
}

say "== 仓库: $REPO"
say "== 模式: $([ "$DRY" = 1 ] && echo 演练 || echo 实际安装)，备份目录: $BACKUP"

# ── 1. ~/.config ────────────────────────────────────────────
say ""
say "== [1/5] ~/.config"
while IFS= read -r -d '' f; do
    rel="${f#"$REPO/config/"}"
    put "$f" "$HOME/.config/$rel"
done < <(find "$REPO/config" -type f -print0)

# ── 2. ~/.local/bin & ~/.local/share ───────────────────────
say ""
say "== [2/5] ~/.local"
while IFS= read -r -d '' f; do
    rel="${f#"$REPO/local/bin/"}"
    put "$f" "$HOME/.local/bin/$rel"
    run chmod +x "$HOME/.local/bin/$rel"
done < <(find "$REPO/local/bin" -type f -print0)
while IFS= read -r -d '' f; do
    rel="${f#"$REPO/local/share/"}"
    put "$f" "$HOME/.local/share/$rel"
done < <(find "$REPO/local/share" -type f -print0)

# ── 3. 点文件 ───────────────────────────────────────────────
say ""
say "== [3/5] ~/.bashrc ~/.bash_profile ~/.config/starship.toml"
for f in .bashrc .bash_profile; do put "$REPO/$f" "$HOME/$f"; done
put "$REPO/starship.toml" "$HOME/.config/starship.toml"

# ── 4. GTK 主题 ────────────────────────────────────────────
if [ "$WITH_GTK" = 1 ]; then
    say ""
    say "== [4/5] ~/.themes（5 套 GTK 主题）"
    for d in "$REPO/gtk-themes"/*/; do
        [ -d "$d" ] || continue
        name="$(basename "$d")"
        run mkdir -p "$HOME/.themes/$name"
        run cp -a "$d." "$HOME/.themes/$name/"
    done
else
    say ""; say "== [4/5] 跳过 GTK 主题（--no-gtk-themes）"
fi

# ── 5. theme-studio（可选）────────────────────────────────
if [ "$WITH_TS" = 1 ]; then
    say ""
    say "== [5/5] theme-studio → ~/.local/share/theme-studio"
    run mkdir -p "$HOME/.local/share/theme-studio"
    run cp -a "$REPO/theme-studio/." "$HOME/.local/share/theme-studio/"
    run ln -sf "$HOME/.local/share/theme-studio/zhuti" "$HOME/.local/bin/zhuti"
else
    say ""; say "== [5/5] 跳过 theme-studio（加 --with-theme-studio 安装，或用目录里的 zhuti）"
fi

# ── 展开占位符 ─────────────────────────────────────────────
say ""
say "== 展开 @@HOME@@"
expand_home \
    "$HOME/.config/wlogout/style.css" \
    "$HOME/.config/fastfetch/config.jsonc" \
    "$HOME/.config/autostart/bongocat.desktop"

# ── 依赖体检 ───────────────────────────────────────────────
say ""
say "== 依赖体检（✗ 的需要自己装）"
miss=0
for b in hyprctl waybar wlogout rofi swaync ghostty starship fastfetch \
         cliphist wl-paste wl-copy grim slurp playerctl brightnessctl pavucontrol \
         blueman-applet fcitx5 uwsm eza bat zoxide nmcli python3; do
    if command -v "$b" >/dev/null 2>&1; then printf '  ✓ %s\n' "$b"
    else printf '  ✗ %s\n' "$b"; miss=$((miss+1)); fi
done
[ -e /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 ] \
    && printf '  ✓ polkit-gnome（认证弹窗）\n' || { printf '  ✗ polkit-gnome\n'; miss=$((miss+1)); }

say ""
say "== 还需要手动做的一次性步骤"
say "  1) 剪贴板历史：systemctl --user enable --now cliphist"
say "  2) 字体：pacman -S ttf-jetbrains-mono-nerd（waybar / 终端 / swaync 都用它）"
say "  3) 图标：装 Papirus 后跑  python3 theme-studio/icon-variants.py install（第一次），之后切主题会自动换"
say "  4) 壁纸：本仓库不含壁纸，请自行放 ~/Pictures 并在 hyprland.lua 里替换"
say "  5) 注销重登（或 hyprctl reload）让 hyprland.lua / 图标 / GTK 主题生效"
say ""
[ "$miss" -eq 0 ] && say "✓ 依赖齐全" || say "缺 $miss 项，见上"
[ "$DRY" = 1 ] && say "（演练结束，未写入任何文件）"
exit 0

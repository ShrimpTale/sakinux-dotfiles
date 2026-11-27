#!/usr/bin/env python3
"""从主题包的 26 槽生成 GTK 用户样式覆盖块（@define-color）。

原理：GTK 加载顺序是「主题 CSS → 用户 CSS（~/.config/gtk-3.0/gtk.css）」，
后加载的 @define-color 会覆盖先加载的，所以不必改任何已安装的主题包，
也不必新建主题目录 —— 只重define 颜色变量即可让 GTK 应用（Nemo 等）跟着换色。

变量名对齐的是系统里实际存在的 catppuccin GTK 主题所定义的那一套
（theme_*/insensitive_*/unfocused_*/borders/warning/error/success + GTK4 的
 headerbar_*/card_*/dialog_*/popover_*/view_*/window_*/accent_*），
未覆盖的变量会退回基础主题的定义，不会变黑块。

用法：gtk-block.py <主题包名>   → 输出覆盖块
"""

import pathlib
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent
THEMES = ROOT / "themes"
BEGIN = "/* ===== theme-studio BEGIN（由 zhuti 主题引擎生成，请勿手改）===== */"
END = "/* ===== theme-studio END ===== */"


def load(name: str) -> dict[str, str]:
    pal = {}
    for line in (THEMES / name / "palette.env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            pal[k.strip()] = v.strip().strip('"').lstrip("#")
    return pal


def rgba(hex6: str, alpha: float) -> str:
    r, g, b = (int(hex6[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def block(name: str) -> str:
    p = load(name)
    S = lambda k: "#" + p[k]            # noqa: E731
    sel_fg = S("crust")
    lines = [
        BEGIN,
        "/* 由主题包 %s 生成；相关色值随 zhuti 切换自动更新 */" % name,
        f"@define-color theme_bg_color {S('base')};",
        f"@define-color theme_base_color {S('base')};",
        f"@define-color theme_fg_color {S('text')};",
        f"@define-color theme_text_color {S('text')};",
        f"@define-color theme_selected_bg_color {S('mauve')};",
        f"@define-color theme_selected_fg_color {sel_fg};",
        f"@define-color insensitive_bg_color {S('base')};",
        f"@define-color insensitive_base_color {S('mantle')};",
        f"@define-color insensitive_fg_color {rgba(p['subtext0'], 0.5)};",
        f"@define-color theme_unfocused_bg_color {S('base')};",
        f"@define-color theme_unfocused_base_color {S('base')};",
        f"@define-color theme_unfocused_fg_color {S('text')};",
        f"@define-color theme_unfocused_text_color {S('text')};",
        f"@define-color theme_unfocused_selected_bg_color {S('mauve')};",
        f"@define-color theme_unfocused_selected_fg_color {sel_fg};",
        f"@define-color unfocused_insensitive_color {rgba(p['subtext0'], 0.5)};",
        f"@define-color borders {rgba(p['text'], 0.12)};",
        f"@define-color unfocused_borders {rgba(p['text'], 0.12)};",
        f"@define-color warning_color {S('yellow')};",
        f"@define-color error_color {S('red')};",
        f"@define-color success_color {S('green')};",
        f"@define-color destructive_color {S('red')};",
        f"@define-color destructive_bg_color {S('red')};",
        f"@define-color error_bg_color {S('red')};",
        f"@define-color warning_bg_color {S('yellow')};",
        f"@define-color success_bg_color {S('green')};",
        f"@define-color placeholder_text_color {rgba(p['subtext0'], 0.7)};",
        f"@define-color content_view_bg {S('base')};",
        f"@define-color text_view_bg {S('base')};",
        f"@define-color view_bg_color {S('base')};",
        f"@define-color view_fg_color {S('text')};",
        f"@define-color window_bg_color {S('base')};",
        f"@define-color window_fg_color {S('text')};",
        f"@define-color dialog_bg_color {S('surface0')};",
        f"@define-color dialog_fg_color {S('text')};",
        f"@define-color card_bg_color {S('surface0')};",
        f"@define-color card_fg_color {S('text')};",
        f"@define-color popover_bg_color {S('surface0')};",
        f"@define-color popover_fg_color {S('text')};",
        f"@define-color headerbar_bg_color {S('surface0')};",
        f"@define-color headerbar_fg_color {S('text')};",
        f"@define-color headerbar_border_color {rgba(p['text'], 0.12)};",
        f"@define-color headerbar_backdrop_color {S('surface0')};",
        f"@define-color headerbar_shade_color {rgba(p['crust'], 0.36)};",
        f"@define-color card_shade_color {rgba(p['crust'], 0.36)};",
        f"@define-color shade_color {rgba(p['crust'], 0.36)};",
        f"@define-color scrollbar_outline_color {rgba(p['text'], 0.1)};",
        f"@define-color accent_color {S('mauve')};",
        f"@define-color accent_bg_color {S('mauve')};",
        f"@define-color accent_fg_color {sel_fg};",
        f"@define-color wm_bg {S('surface0')};",
        f"@define-color wm_border {rgba(p['text'], 0.12)};",
        f"@define-color wm_title {S('text')};",
        f"@define-color wm_unfocused_bg {S('mantle')};",
        f"@define-color wm_unfocused_title {S('overlay1')};",
        f"@define-color wm_highlight {S('surface1')};",
        f"@define-color wm_button_icon {S('text')};",
        f"@define-color wm_button_close_active_bg {S('red')};",
        f"@define-color wm_button_close_hover_bg {S('maroon')};",
        f"@define-color wm_button_max_active_bg {S('green')};",
        f"@define-color wm_button_max_hover_bg {S('green')};",
        f"@define-color wm_button_min_active_bg {S('yellow')};",
        f"@define-color wm_button_min_hover_bg {S('yellow')};",
        END,
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("用法：gtk-block.py <主题包名>")
    sys.stdout.write(block(sys.argv[1]))

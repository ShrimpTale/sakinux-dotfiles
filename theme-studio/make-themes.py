#!/usr/bin/env python3
"""从 palette.env 生成各风味主题包的 theme.toml。

规则（来自 Mocha 现状快照的反推）：
  * accent_soft = mauve × 0.85                → 派生自原先锁屏用的手调紫 #ad8dd2
  * hover_bg    = surface0 + (-1, 0, -2)      → 派生自 wlogout hover 底 #303242
  * placeholder = #ffffff99                   → 暗色主题通用的"白 60%"占位文字
  * shadow      = rgba(0, 0, 0, 0.8)          → swaync 卡片阴影
  * panel_bg    = rgba(base, 0.90)            → wlogout 半透明底板
  * bar_bg      = shade(@mauve, 0.4)          → waybar 栏底
亮色（Latte）单独手工取值，见 LATTE_OVERRIDE。
"""

import colorsys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
THEMES = ROOT / "themes"


def folder_shade(hex6: str) -> str:
    """文件夹图标内层阴影：实测变换 = HLS 空间里 S×0.708、L−7.9
    （基准：mocha mauve #cba6f7 → 图标里真实的 #b792e3）"""
    hex6 = hex6.lstrip("#")
    r, g, b = (int(hex6[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r2, g2, b2 = colorsys.hls_to_rgb(h, max(0.0, l - 0.079), s * 0.708)
    return "#%02x%02x%02x" % (round(r2 * 255), round(g2 * 255), round(b2 * 255))

DISPLAY = {
    "catppuccin-mocha": ("Catppuccin Mocha", "dark"),
    "catppuccin-frappe": ("Catppuccin Frappé", "dark"),
    "catppuccin-macchiato": ("Catppuccin Macchiato", "dark"),
    "catppuccin-latte": ("Catppuccin Latte", "light"),
}

LATTE_OVERRIDE = {
    "accent_soft": "#7430cb",           # latte mauve × 0.85
    "hover_bg": "#bcc0cc",              # latte surface1（亮底上要"压暗"才看得出 hover）
    "placeholder": "#4c4f6999",         # latte text 60%
    "shadow": "rgba(0, 0, 0, 0.15)",    # 亮底上重阴影会脏
    "panel_bg": "rgba(239, 241, 245, 0.90)",
    "bar_bg": "#e7d7fc",                # latte mauve 与白 2:8 混合的淡紫栏底
}

# ghostty 内置主题名 = 系统主题文件名（ASCII，不带重音！）
# “Catppuccin Frappé”是给人看的显示名，“Catppuccin Frappe”才是 ghostty 找得到的名字
GHOSTTY_NAME = {
    "catppuccin-mocha": "Catppuccin Mocha",
    "catppuccin-frappe": "Catppuccin Frappe",
    "catppuccin-macchiato": "Catppuccin Macchiato",
    "catppuccin-latte": "Catppuccin Latte",
}

TEMPLATE = '''# ============================================================
# {display} —— 主题包（同格式 26 槽 + 语义附加槽）
# {note}
# ============================================================
name = "{name}"
display = "{display}"
family = "Catppuccin"
variant = "{variant}"
appearance = "{appearance}"
accent = "mauve"
source = "{source}"

# 只写"主题名"而不是色值的配置（这里的名字必须是目标程序真实存在的主题名）
[names]
ghostty = "{ghostty_theme}"
fcitx5 = "catppuccin-{flavor}-mauve"
gtk = "catppuccin-{flavor}-mauve-standard+default"
starship = "catppuccin_{flavor}"
hypr = "catppuccin-{flavor}"            # 同上

# 非 26 槽位的语义色（各主题可"脱钩"，不必照抄暗色值）
[extras]
accent_soft = "{accent_soft}"           # 预留槽（原先锁屏的大时钟/头像环用）
hover_bg = "{hover_bg}"                 # wlogout 按钮 hover 底
placeholder = "{placeholder}"           # 预留槽（原先锁屏输入框占位文字）
shadow = "{shadow}"                     # swaync 卡片阴影
panel_bg = "{panel_bg}"                 # wlogout 半透明底板
nemo_view_bg = "{nemo_view_bg}"         # 主人 gtk.css 里 Nemo 文件视图底（base 微提亮 + 0.78 透明）
folder_shade = "{folder_shade}"         # Papirus 文件夹图标内层阴影（mauve × 0.90）

[waybar]
bar_bg = "{bar_bg}"                     # 栏底
'''


def load_palette(name: str) -> dict[str, str]:
    d = {}
    for line in (THEMES / name / "palette.env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip().strip('"').lstrip("#").lower()
    return d


def triple(h: str) -> list[int]:
    return [int(h[i : i + 2], 16) for i in (0, 2, 4)]


def hx(v: list[int]) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in v)


for name, (display, appearance) in DISPLAY.items():
    p = load_palette(name)
    flavor = name.split("-", 1)[1]
    extras = {
        "accent_soft": hx([c * 0.85 for c in triple(p["mauve"])]),
        "hover_bg": hx([c + d for c, d in zip(triple(p["surface0"]), (-1, 0, -2))]),
        "placeholder": "#ffffff99",
        "shadow": "rgba(0, 0, 0, 0.8)",
        "panel_bg": "rgba(%d, %d, %d, 0.90)" % tuple(triple(p["base"])),
        "bar_bg": "shade(@mauve, 0.4)",
        "nemo_view_bg": "rgba(%d, %d, %d, 0.78)" % tuple(
            c + d for c, d in zip(triple(p["base"]), (2, 4, 7))
        ),
        "folder_shade": folder_shade(p["mauve"]),
    }
    if appearance == "light":
        extras.update(LATTE_OVERRIDE)
    note = (
        "现有桌面配色快照（20 文件 / 300 处命中，全部落在这 26 槽）"
        if name == "catppuccin-mocha"
        else f"以 Mocha 主题包为标准创作的 {display} 版本（槽位 1:1 角色对齐，附加槽按亮/暗语义重取）"
    )
    body = TEMPLATE.format(name=name, display=display, appearance=appearance,
                           flavor=flavor, flavor_title=display.split(" ", 1)[1],
                           variant=display.split(" ", 1)[1],
                           ghostty_theme=GHOSTTY_NAME[name],
                           note=note, source=note, **extras)
    (THEMES / name / "theme.toml").write_text(body)
    print(f"写入 themes/{name}/theme.toml")
    for k, v in extras.items():
        print(f"    {k:<12} {v}")

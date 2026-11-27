#!/usr/bin/env python3
"""生成原创主题包 Nordic Fjord（北欧·峡湾）——冷灰蓝、低饱和、克制的强调色。

设计规则（可复现，不是随手填色）：
  1. 中性色阶：统一色相 214°（冷蓝灰），饱和度 ≤ 18%，明度 7%→85% 分 12 级；
     底色越深饱和度略高一点点，接近纯黑但不发死。
  2. 强调色：色相沿冷暖两端拉开（冰川蓝 212°为签名色），饱和度上限 42%，
     明度 62%→86% —— 低饱和 + 中高明度 = 「冷淡」而非灰暗。
  3. 语义色保留可辨识度：红 6°、陶土 24°、砂金 44°、苔绿 140°，饱和度压到 24%–38%，
     既不像霓虹，也不至于出错时看不出是红的。
  4. 输出沿用 Catppuccin 26 槽「格式标准」，可被 theme-switch.py 直接识别与切换。
"""

import colorsys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "themes" / "nordic-fjord"
OUT.mkdir(parents=True, exist_ok=True)


def hsl(h: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


# (色相, 饱和度, 明度) —— 中性色阶：冷蓝灰 214°
NEUTRAL = {
    "crust": (214, 18, 7),
    "mantle": (214, 16, 9.5),
    "base": (214, 15, 12),
    "surface0": (214, 14, 16),
    "surface1": (214, 13, 20),
    "surface2": (214, 12, 25),
    "overlay0": (214, 10, 34),
    "overlay1": (214, 10, 42),
    "overlay2": (214, 9, 50),
    "subtext0": (214, 10, 62),
    "subtext1": (214, 12, 72),
    "text": (214, 14, 85),
}

# 强调色：低饱和 + 中高明度
ACCENT = {
    "rosewater": (210, 22, 86),   # 极地晨曦白
    "flamingo": (206, 26, 80),
    "pink": (268, 22, 78),        # 石楠紫
    "mauve": (212, 36, 68),       # ★ 签名色：冰川蓝
    "red": (6, 38, 63),           # 哑光胭脂
    "maroon": (8, 28, 62),
    "peach": (24, 38, 68),        # 陶土
    "yellow": (44, 36, 72),       # 沙金
    "green": (140, 24, 64),       # 苔绿
    "teal": (188, 28, 62),        # 霜青
    "sky": (196, 36, 70),
    "sapphire": (206, 38, 64),
    "blue": (218, 42, 70),
    "lavender": (232, 34, 74),
}

ORDER = ["rosewater", "flamingo", "pink", "mauve", "red", "maroon", "peach", "yellow",
         "green", "teal", "sky", "sapphire", "blue", "lavender",
         "text", "subtext1", "subtext0", "overlay2", "overlay1", "overlay0",
         "surface2", "surface1", "surface0", "base", "mantle", "crust"]

P = {**{k: hsl(*v) for k, v in ACCENT.items()}, **{k: hsl(*v) for k, v in NEUTRAL.items()}}


def folder_shade(hex6: str) -> str:
    """文件夹图标内层阴影：实测变换 = HLS 里 S×0.708、L−7.9（mocha mauve #cba6f7 → #b792e3）"""
    hex6 = hex6.lstrip("#")
    r, g, b = (int(hex6[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r2, g2, b2 = colorsys.hls_to_rgb(h, max(0.0, l - 0.079), s * 0.708)
    return "#%02x%02x%02x" % (round(r2 * 255), round(g2 * 255), round(b2 * 255))

OUT.joinpath("palette.env").write_text(
    "# Nordic Fjord —— 北欧·峡湾（冷灰蓝 / 低饱和 / 克制强调）\n"
    "# 规则见 make-nordic.py：中性 214°≤18% 饱和，强调色 ≤42% 饱和、62-86% 明度\n"
    + "".join(f"{k} = {P[k]}\n" for k in ORDER)
)


def trip(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def hx(v):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in v)


mauve = trip(P["mauve"])
surface0 = trip(P["surface0"])
text = trip(P["text"])
base = trip(P["base"])

extras = {
    "accent_soft": hx([c * 0.85 for c in mauve]),
    "hover_bg": hx([c + d for c, d in zip(surface0, (-1, 0, -2))]),
    "placeholder": hx(text) + "99",
    "shadow": "rgba(0, 0, 0, 0.6)",
    "panel_bg": "rgba(%d, %d, %d, 0.90)" % tuple(base),
    "bar_bg": "shade(@mauve, 0.38)",
    "nemo_view_bg": "rgba(%d, %d, %d, 0.78)" % tuple(c + d for c, d in zip(base, (2, 4, 7))),
    "folder_shade": folder_shade(P["mauve"]),
}

OUT.joinpath("theme.toml").write_text(f'''# ============================================================
# Nordic Fjord —— 原创主题包（沿用 Catppuccin 26 槽「格式标准」）
# 关键词：北欧风 / 冷淡 / 高级感
# 设计规则见同目录生成脚本 make-nordic.py（HSL 可复现，不是凭感觉填的）
# ============================================================
name = "nordic-fjord"
display = "Nordic Fjord 北欧·峡湾"
family = "Nordic"
variant = "Fjord 北欧·峡湾"
appearance = "dark"
accent = "mauve"          # 签名色 = 冰川蓝 {P['mauve']}
source = "原创：HSL 规则生成（中性 214° 色相、饱和≤18%；强调色饱和≤42%、明度 62-86%）"

# 只写"主题名"而不是色值的配置
[names]
ghostty = "nordic-fjord"            # 自定义主题文件，随主题包一起安装
fcitx5 = "nordic-fjord"
gtk = "nordic-fjord"
starship = "nordic_fjord"           # 需在 starship.toml 里有同名的色板段
hypr = "nordic-fjord"

# 非 26 槽位的语义色
[extras]
accent_soft = "{extras['accent_soft']}"           # 预留槽（原先锁屏的大时钟/头像环用）
hover_bg = "{extras['hover_bg']}"                 # wlogout 按钮 hover 底
placeholder = "{extras['placeholder']}"           # 预留槽（原先锁屏输入框占位文字）（正文色 60%）
shadow = "{extras['shadow']}"                     # swaync 卡片阴影（比猫猫那套更轻，收"高级感"）
panel_bg = "{extras['panel_bg']}"                 # wlogout 半透明底板
nemo_view_bg = "{extras['nemo_view_bg']}"         # Nemo 文件视图底（跟随主题）
folder_shade = "{extras['folder_shade']}"         # Papirus 文件夹图标内层阴影

[waybar]
bar_bg = "{extras['bar_bg']}"                     # 栏底：比默认再压深一点
''')

# 终端主题文件（ghostty 用户主题目录格式）
ANSI = {
    0: "surface1", 1: "red", 2: "green", 3: "yellow", 4: "blue", 5: "lavender",
    6: "teal", 7: "subtext1", 8: "surface2", 9: "maroon", 10: "green", 11: "peach",
    12: "sky", 13: "pink", 14: "sapphire", 15: "text",
}
OUT.joinpath("ghostty.theme").write_text(
    "# Nordic Fjord —— ghostty 终端配色（由主题包自动安装到 ~/.config/ghostty/themes/）\n"
    + "".join(f"palette = {i}=#{P[name][1:]}\n" for i, name in ANSI.items())
    + f"background = {P['base']}\n"
    + f"foreground = {P['text']}\n"
    + f"cursor-color = {P['mauve']}\n"
    + f"cursor-text = {P['base']}\n"
    + f"selection-background = {P['surface2']}\n"
    + f"selection-foreground = {P['text']}\n"
)

print("26 槽：")
for k in ORDER:
    print(f"  {k:<10} {P[k]}")
print("\n附加槽：")
for k, v in extras.items():
    print(f"  {k:<12} {v}")

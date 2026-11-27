#!/usr/bin/env python3
"""生成原创主题包 Morandi Canvas（莫兰迪 · 百搭画布）。

设计参考（不是拍脑袋，三套工业/艺术色彩体系各取一条原则）：
  1. Radix Colors —— 中性色阶按「用途分层」：最底两层当背景、中间层当组件底、再往上当描边、
     顶层当文字；层与层之间的对比度可预期。
  2. Solarized（Ethan Schoonover）—— 所有强调色**等亮度**（CIELAB 的 L* 对齐），
     谁也不比谁亮，因此任意搭配都不刺眼、不会有一色跳出来抢镜。这是「百搭」的关键。
  3. 莫兰迪色系 —— 强调色统一"掺灰"（低彩度 C*≈20），像粉刷过的墙面，和照片/壁纸放一起不打架。

工程规则（全部在 CIELAB 空间里定，而不是在 RGB 里手调）：
  * 中性色阶：L* 8 → 96 共 12 级，色相 40°（暖灰），彩度 C* ≤ 4（近无彩，微微偏暖）
  * 强调色：统一 L* ≈ 72、C* ≈ 18–24，色相沿色轮铺开；语义色（错/警/成）只收窄彩度，不改色相
  * 输出对比度实测（WCAG），低于可用线的直接调 L*
"""

import colorsys
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "themes" / "morandi-canvas"
OUT.mkdir(parents=True, exist_ok=True)

# ---------- CIELAB 工具 ----------

WHITE = (0.95047, 1.0, 1.08883)


def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _unlin(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def lch_to_hex(L: float, C: float, h_deg: float) -> str:
    """L*C*h(ab) → sRGB hex（超色域时截断）。"""
    a = C * math.cos(math.radians(h_deg))
    b = C * math.sin(math.radians(h_deg))
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200

    def finv(t: float) -> float:
        return t ** 3 if t ** 3 > 216 / 24389 else (t - 4 / 29) * 108 / 841

    x, y, z = finv(fx) * WHITE[0], finv(fy) * WHITE[1], finv(fz) * WHITE[2]
    r = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g = -0.9689 * x + 1.8758 * y + 0.0415 * z
    bl = 0.0557 * x - 0.2040 * y + 1.0570 * z
    return "#%02x%02x%02x" % tuple(round(255 * max(0.0, min(1.0, _unlin(v)))) for v in (r, g, bl))


def hex_to_lab(hex6: str) -> tuple[float, float, float]:
    r, g, b = (_lin(int(hex6[i:i + 2], 16) / 255) for i in (1, 3, 5))
    x = 0.4124 * r + 0.3576 * g + 0.1805 * b
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = 0.0193 * r + 0.1192 * g + 0.9505 * b

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 216 / 24389 else (841 / 108) * t + 4 / 29

    fx, fy, fz = f(x / WHITE[0]), f(y / WHITE[1]), f(z / WHITE[2])
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def rel_lum(hex6: str) -> float:
    r, g, b = (_lin(int(hex6[i:i + 2], 16) / 255) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ---------- 色板 ----------

WARM = 40  # 中性色阶色相：暖灰

NEUTRAL_L = {  # 槽位 -> L*（Radix 式分层：底→面→描边→文字）
    "crust": 8, "mantle": 11, "base": 14, "surface0": 19,
    "surface1": 24, "surface2": 30, "overlay0": 40, "overlay1": 48,
    "overlay2": 56, "subtext0": 70, "subtext1": 80, "text": 92,
}

# 强调色：统一 L*≈72 / C*≈20（等亮度 + 掺灰），色相按用途铺开
ACCENT_LCH = {
    "rosewater": (86, 8, 60),     # 暖白
    "flamingo": (78, 14, 25),
    "pink": (72, 20, 345),        # 灰玫瑰
    "mauve": (75, 22, 285),      # ★ 签名色：灰紫（中性、不抢戏；L* 抬到 75 是为了在 surface2 上也过 AA）
    "red": (66, 26, 22),          # 赤陶
    "maroon": (64, 22, 8),
    "peach": (74, 22, 45),        # 陶土
    "yellow": (78, 22, 85),       # 赭石
    "green": (72, 20, 140),       # 鼠尾草绿
    "teal": (70, 18, 175),        # 铜绿
    "sky": (76, 18, 205),
    "sapphire": (70, 22, 235),
    "blue": (72, 24, 258),
    "lavender": (76, 22, 300),
}

P = {k: lch_to_hex(*ACCENT_LCH[k]) for k in ACCENT_LCH}
P.update({k: lch_to_hex(v, 4, WARM) for k, v in NEUTRAL_L.items()})


def folder_shade(hex6: str) -> str:
    """文件夹图标内层阴影：实测变换 = HLS 里 S×0.708、L−7.9（mocha mauve #cba6f7 → #b792e3）"""
    hex6 = hex6.lstrip("#")
    r, g, b = (int(hex6[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r2, g2, b2 = colorsys.hls_to_rgb(h, max(0.0, l - 0.079), s * 0.708)
    return "#%02x%02x%02x" % (round(r2 * 255), round(g2 * 255), round(b2 * 255))

ORDER = ["rosewater", "flamingo", "pink", "mauve", "red", "maroon", "peach", "yellow",
         "green", "teal", "sky", "sapphire", "blue", "lavender",
         "text", "subtext1", "subtext0", "overlay2", "overlay1", "overlay0",
         "surface2", "surface1", "surface0", "base", "mantle", "crust"]

OUT.joinpath("palette.env").write_text(
    "# Morandi Canvas —— 莫兰迪·百搭画布（暖中性灰 + 等亮度掺灰强调色）\n"
    "# 规则见 make-canvas.py：中性 L*8-96 / C*≤4 / 色相 40；强调色 L*≈72 / C*≈20\n"
    + "".join(f"{k} = {P[k]}\n" for k in ORDER)
)


def trip(h: str) -> list[int]:
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def hx(v) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in v)


mauve = trip(P["mauve"])
surface0 = trip(P["surface0"])
text = trip(P["text"])
base = trip(P["base"])

extras = {
    "accent_soft": hx([c * 0.85 for c in mauve]),
    "hover_bg": hx([c + d for c, d in zip(surface0, (2, 1, -1))]),
    "placeholder": hx(text) + "99",
    "shadow": "rgba(0, 0, 0, 0.55)",
    "panel_bg": "rgba(%d, %d, %d, 0.90)" % tuple(base),
    "bar_bg": "shade(@mauve, 0.35)",
    "nemo_view_bg": "rgba(%d, %d, %d, 0.78)" % tuple(c + d for c, d in zip(base, (2, 4, 7))),
    "folder_shade": folder_shade(P["mauve"]),
}

OUT.joinpath("theme.toml").write_text(f'''# ============================================================
# Morandi Canvas —— 原创主题包（沿用 26 槽「格式标准」）
# 关键词：百搭 / 中性画布 / 莫兰迪灰调
# 参考：Radix Colors 的分层灰阶 · Solarized 的等亮度强调色 · 莫兰迪色系的掺灰低彩度
# 规则见 make-canvas.py（CIELAB 计算，可复现）
# ============================================================
name = "morandi-canvas"
display = "Morandi Canvas 百搭画布"
family = "Morandi"
variant = "Canvas 百搭画布"
appearance = "dark"
accent = "mauve"          # 签名色 = 灰紫 {P['mauve']}（中性、不抢戏）
source = "原创：CIELAB 规则生成（中性 L*8-96/C*≤4 暖灰；强调色统一 L*≈72/C*≈20 等亮度掺灰）"

[names]
ghostty = "morandi-canvas"          # 自定义主题文件，随主题包一起安装
fcitx5 = "morandi-canvas"
gtk = "morandi-canvas"
starship = "morandi_canvas"
hypr = "morandi-canvas"

[extras]
accent_soft = "{extras['accent_soft']}"
hover_bg = "{extras['hover_bg']}"
placeholder = "{extras['placeholder']}"
shadow = "{extras['shadow']}"
panel_bg = "{extras['panel_bg']}"
nemo_view_bg = "{extras['nemo_view_bg']}"
folder_shade = "{extras['folder_shade']}"

[waybar]
bar_bg = "{extras['bar_bg']}"
''')

ANSI = {0: "surface1", 1: "red", 2: "green", 3: "yellow", 4: "blue", 5: "lavender",
        6: "teal", 7: "subtext1", 8: "surface2", 9: "maroon", 10: "green", 11: "peach",
        12: "sky", 13: "pink", 14: "sapphire", 15: "text"}
OUT.joinpath("ghostty.theme").write_text(
    "# Morandi Canvas —— ghostty 终端配色（随主题包安装）\n"
    + "".join(f"palette = {i}=#{P[n][1:]}\n" for i, n in ANSI.items())
    + f"background = {P['base']}\nforeground = {P['text']}\n"
    + f"cursor-color = {P['mauve']}\ncursor-text = {P['base']}\n"
    + f"selection-background = {P['surface2']}\nselection-foreground = {P['text']}\n"
)

# ---------- 自检：等亮度 / 对比度 ----------
print("26 槽（附 CIELAB 实测，验证是否真的等亮度）：")
for k in ORDER:
    L, a, b = hex_to_lab(P[k])
    C = math.hypot(a, b)
    tag = "强调" if k in ACCENT_LCH else "中性"
    print(f"  {tag} {k:<10} {P[k]}  L*={L:5.1f}  C*={C:5.1f}")

print("\n对比度自检（WCAG）：")
pairs = [("text", "base"), ("text", "surface1"), ("subtext0", "base"),
         ("mauve", "base"), ("mauve", "surface2"),
         ("red", "base"), ("green", "base"), ("yellow", "base"), ("teal", "base")]
for fg, bg in pairs:
    r = contrast(P[fg], P[bg])
    verdict = "AAA" if r >= 7 else ("AA" if r >= 4.5 else "偏弱")
    print(f"  {fg:<9} on {bg:<9} {r:5.2f}  {verdict}")
print("  说明：overlay0/overlay1 是描边/分隔线用的低优先级层，不承担正文对比度职责")
print("  调色重点：所有强调色 C* 18-26（掺灰）、主体 L* 66-76（等亮度）—— 所以谁都不抢镜")

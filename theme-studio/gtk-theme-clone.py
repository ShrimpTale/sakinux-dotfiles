#!/usr/bin/env python3
"""克隆系统里已安装的 GTK 主题并按主题包换色，生成用户级 GTK 主题。

思路：GTK 主题 = 一套 CSS + 一堆 SVG 控件资源。既然系统里已经有一套完整的
Catppuccin Mocha 主题，就把它整个复制到 ~/.themes/<主题名>，再把里面的 Mocha
色值整体替换成目标配色的 26 槽色值 —— 滑块/勾选/开关等控件随之换色，不需要
重新画图，也不需要额外安装任何包。

被 theme-switch.py 作为一步调用（build()），也可单独跑：
    gtk-theme-clone.py <主题包名>          # 生成/更新 ~/.themes/<gtk 主题名>
    gtk-theme-clone.py <主题包名> --check  # 只报告会替换多少处
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent
THEMES = ROOT / "themes"
BASE_THEME = pathlib.Path("/usr/share/themes/catppuccin-mocha-mauve-standard+default")
SRC_PALETTE = "catppuccin-mocha"
TEXT_EXT = {".css", ".svg", ".theme", ".xml", ".themerc"}

HEX_RE = re.compile(r"(?<![0-9a-zA-Z#])(#?)([0-9a-fA-F]{8}|[0-9a-fA-F]{6})(?![0-9a-zA-Z])")
DEC_RE = re.compile(r"(rgba?\()\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})")


def load_palette(name: str) -> dict[str, str]:
    pal: dict[str, str] = {}
    for line in (THEMES / name / "palette.env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            pal[k.strip()] = v.strip().strip('"').lstrip("#").lower()
    return pal


def triple(h: str) -> tuple[int, int, int]:
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def recolor(text: str, hexmap: dict[str, str], decmap: dict[tuple, str]) -> tuple[str, int]:
    n = 0

    def hex_rep(m: re.Match) -> str:
        nonlocal n
        hash_, h = m.group(1), m.group(2)
        key = h[:6].lower()
        if key not in hexmap:
            return m.group(0)
        n += 1
        return hash_ + hexmap[key] + (h[6:].lower() if len(h) == 8 else "")

    text = HEX_RE.sub(hex_rep, text)

    def dec_rep(m: re.Match) -> str:
        nonlocal n
        t = tuple(int(m.group(i)) for i in (2, 3, 4))
        new = decmap.get(t)  # type: ignore[arg-type]
        if not new:
            return m.group(0)
        n += 1
        r, g, b = triple(new)
        return f"{m.group(1)}{r}, {g}, {b}"

    return DEC_RE.sub(dec_rep, text), n


def gtk_theme_name(theme: str) -> str:
    meta = tomllib.loads((THEMES / theme / "theme.toml").read_text())
    return meta.get("names", {}).get("gtk", theme)


def plan(theme: str, base: pathlib.Path = BASE_THEME):
    src, dst = load_palette(SRC_PALETTE), load_palette(theme)
    hexmap = {src[k]: dst[k] for k in src if k in dst and src[k] != dst[k]}
    decmap = {triple(k): v for k, v in hexmap.items()}
    files = [f for f in base.rglob("*") if f.is_file() and f.suffix.lower() in TEXT_EXT]
    results = []
    total = 0
    for f in files:
        try:
            text = f.read_text()
        except UnicodeDecodeError:
            continue
        new, n = recolor(text, hexmap, decmap)
        if n:
            total += n
            results.append((f.relative_to(base), new, n))
    return files, results, total


def build(theme: str, out_dir: pathlib.Path, base: pathlib.Path = BASE_THEME) -> tuple[int, int]:
    """把 base 主题复制到 out_dir 并换色。返回 (文件数, 换色处数)。"""
    _files, results, total = plan(theme, base)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(base, out_dir)
    for rel, new, _n in results:
        (out_dir / rel).write_text(new)
    idx = out_dir / "index.theme"
    if idx.exists():
        t = idx.read_text()
        t = re.sub(r"(?m)^Name=.*$", f"Name={out_dir.name}", t)
        t = re.sub(r"(?m)^GtkTheme=.*$", f"GtkTheme={out_dir.name}", t)
        idx.write_text(t)
    return sum(1 for _ in out_dir.rglob("*") if _.is_file()), total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("theme")
    ap.add_argument("--out", default=str(pathlib.Path.home() / ".themes"))
    ap.add_argument("--base", default=str(BASE_THEME))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if not (THEMES / args.theme / "palette.env").exists():
        sys.exit(f"没有这个主题包：{args.theme}")
    base = pathlib.Path(args.base).expanduser()
    if not base.is_dir():
        sys.exit(f"基础主题不存在：{base}")

    name = gtk_theme_name(args.theme)
    target = pathlib.Path(args.out).expanduser() / name
    _files, results, total = plan(args.theme, base)
    print(f"主题包：{args.theme}  →  GTK 主题名：{name}")
    print(f"基础主题：{base}")
    print(f"命中 {len(results)} 个文件，共 {total} 处换色")
    print(f"输出：{target}")
    if args.check:
        for rel, _new, n in sorted(results, key=lambda r: -r[2])[:8]:
            print(f"  {rel}  {n} 处")
        return 0
    nfiles, total = build(args.theme, target, base)
    print(f"完成：{nfiles} 个文件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

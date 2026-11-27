#!/usr/bin/env python3
"""配色对比预览：preview.py <主题A> <主题B> [输出.png]
生成左右对照的 26 槽 + 附加槽色卡（SVG → PNG，需要 rsvg-convert）。"""

import html
import pathlib
import subprocess
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent
THEMES = ROOT / "themes"


def load(name: str) -> tuple[dict, dict, dict]:
    d = THEMES / name
    pal = {}
    for line in (d / "palette.env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            pal[k.strip()] = v.strip().strip('"').lstrip("#")
    meta = tomllib.loads((d / "theme.toml").read_text())
    extras = {**meta.get("extras", {}), **meta.get("waybar", {})}
    return pal, meta, extras


def chip(x, y, fill, label, value, label_color="#d3d8de", sub="#7f849c"):
    if fill is None:
        fill = "#313244"
    return (f'<rect x="{x}" y="{y}" width="58" height="24" rx="5" fill="{fill}" '
            f'stroke="#585b70" stroke-width="1"/>'
            f'<text x="{x+70}" y="{y+17}" fill="{label_color}" font-family="monospace" font-size="14">{html.escape(label)}</text>'
            f'<text x="{x+190}" y="{y+17}" fill="{sub}" font-family="monospace" font-size="12">{html.escape(value)[:36]}</text>')


def main() -> int:
    a, b = sys.argv[1], sys.argv[2]
    out = pathlib.Path(sys.argv[3] if len(sys.argv) > 3 else ROOT / f"preview-{a}-vs-{b}.png")
    pa, ma, ea = load(a)
    pb, mb, eb = load(b)
    rows = list(pa.keys()) + ["—"] + list(ea.keys())
    rowh, top = 34, 118
    H = top + rowh * len(rows) + 50
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="920" height="{H}" viewBox="0 0 920 {H}">',
         '<rect width="100%" height="100%" fill="#11111b"/>',
         f'<text x="40" y="50" fill="#cdd6f4" font-family="JetBrainsMono Nerd Font,monospace" font-size="25">'
         f'{html.escape(ma.get("display", a))}   →   {html.escape(mb.get("display", b))}</text>',
         f'<text x="40" y="80" fill="#7f849c" font-family="JetBrainsMono Nerd Font,monospace" font-size="14">'
         f'左：{html.escape(ma.get("appearance",""))}   右：{html.escape(mb.get("appearance",""))}   '
         f'26 槽 1:1 角色对齐，附加槽各自独立</text>',
         f'<text x="60" y="{top-8}" fill="#9399b2" font-family="monospace" font-size="13">{html.escape(ma.get("display",""))}</text>',
         f'<text x="500" y="{top-8}" fill="#9399b2" font-family="monospace" font-size="13">{html.escape(mb.get("display",""))}</text>']
    y = top
    for k in pa:
        s.append(chip(60, y, f'#{pa[k]}', k, f'#{pa[k]}'))
        s.append(chip(500, y, f'#{pb[k]}', k, f'#{pb[k]}'))
        y += rowh
    s.append(f'<text x="60" y="{y+14}" fill="#f9e2af" font-family="monospace" font-size="13">— 附加语义槽 —</text>')
    y += rowh
    for k in ea:
        for x, ex in ((60, ea), (500, eb)):
            v = str(ex.get(k, "—"))
            fill = "#" + v.lstrip("#")[:6] if v.startswith("#") and len(v.lstrip("#")) >= 6 else None
            s.append(chip(x, y, fill, k, v))
        y += rowh
    s.append("</svg>")
    svg = out.with_suffix(".svg")
    svg.write_text("\n".join(s))
    subprocess.run(["rsvg-convert", "-w", "920", str(svg), "-o", str(out)], check=True)
    print(f"{out}  ({out.stat().st_size//1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""统一配色主题切换器（主题包版）

主题包 = themes/<名字>/ 目录，内含：
    palette.env   26 个标准槽位（Catppuccin 同格式）—— 主题的"骨架"
    theme.toml    元数据：外观、名称映射、非槽位语义色 [extras]、派生值 [waybar]

用法：
    ./theme-switch.py list                     列出主题包
    ./theme-switch.py show <名字>               打印主题包内容
    ./theme-switch.py current                   当前主题
    ./theme-switch.py switch <名字> [--apply] [--reload] [--gtk] [--root DIR] [--from NAME]

设计要点：
  * 槽位替换 1:1（mauve→mauve、base→base…），Catppuccin 各风味官方就是按角色对齐的，
    所以亮色/暗色互换无需额外映射。
  * 三种记法都覆盖：6 位 hex、带 alpha 的 8 位 hex（保留后两位）、十进制 rgba(r, g, b, a)。
  * 非槽位的手调色走 [extras] 字面替换（如原先锁屏的手调紫、wlogout hover 底）——
    亮色主题可以在这几个点上"脱钩"，不必照抄暗色值。
  * 默认 dry-run；--apply 才写，写前逐文件备份到 backups/<时间戳>/，可 rollback。
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parent
THEMES = ROOT / "themes"
BACKUPS = ROOT / "backups"
STATE = ROOT / "state"

# 需要做色值替换的文件（相对 ~/.config）
HEX_TARGETS = [
    "waybar/mocha.css",
    "waybar/style.css",
    "fuzzel/fuzzel.ini",
    "wlogout/style.css",
    "wlogout/icons/*.svg",
    "fastfetch/config.jsonc",
    "hypr/themes/catppuccin-*.lua",
    "ghostty/config",          # 除主题名外还硬写了 background 色值
    "gtk-3.0/gtk.css",        # 主人手写的 Nemo 规则（含硬编码色值）
]

# 用户级资源（相对 $HOME）：Papirus 图标随主题换色
# 范围是全部 SVG（不只 folder*）—— 实测 places/user-*、actions/* 等也带主题色
HOME_TARGETS = [
    ".local/share/icons/Papirus/**/*.svg",
]

# 图标变体模式（T3，2026-10-09 上线）：Papirus 改成目录软链时，6 套预生成的变色树随主题换链，
# 切换瞬时完成；绝不再往活动树里逐文件重写（变体间共享 inode，原地写会穿透污染所有变体）。
ICONS_DIR = HOME / ".local/share/icons"
PAPIRUS_LIVE = ICONS_DIR / "Papirus"
VARIANT_PREFIX = "Papirus-"

# 写"主题名"而非色值的配置：路径 -> (toml 里的键, 正则, 模板)
NAME_TARGETS = {
    "ghostty/config": ("ghostty", r"(?m)^\s*theme\s*=.*$", "theme = {value}"),
    "starship.toml": ("starship", r"(?m)^\s*palette\s*=.*$", "palette = '{value}'"),
    "fcitx5/conf/classicui.conf": ("fcitx5", r"(?m)^\s*Theme\s*=.*$", "Theme={value}"),
}

# 需要"主题包已安装"才敢切的配置（否则保留原样）
CONDITIONAL = {
    "fcitx5/conf/classicui.conf": "fcitx5",
    "gtk4": "gtk",
}

RELOAD = [
    ("waybar", ["pkill", "-SIGUSR2", "-x", "waybar"]),
    ("hyprland", ["hyprctl", "reload"]),
    ("swaync", ["swaync-client", "-rs"]),
    ("ghostty", ["pkill", "-SIGUSR2", "-x", "ghostty"]),
]

HEX_RE = re.compile(r"(?<![0-9a-zA-Z#])(#?)([0-9a-fA-F]{8}|[0-9a-fA-F]{6})(?![0-9a-zA-Z])")
DEC_RE = re.compile(r"(rgba?\()\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})")


# ---------- 主题包 ----------


def load_theme(name: str) -> dict:
    d = THEMES / name
    if not (d / "palette.env").exists():
        sys.exit(f"没有这个主题包：{name}（可用：{', '.join(list_themes())}）")
    palette: dict[str, str] = {}
    for line in (d / "palette.env").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        hex6 = v.strip().strip('"').lstrip("#").lower()
        if not re.fullmatch(r"[0-9a-f]{6}", hex6):
            sys.exit(f"{name}/palette.env 槽位 {k} 色值不合法：{v}")
        palette[k.strip()] = hex6
    if len(palette) < 26:
        sys.exit(f"{name}/palette.env 槽位不足（{len(palette)}/26）")
    meta = tomllib.loads((d / "theme.toml").read_text()) if (d / "theme.toml").exists() else {}
    return {
        "name": name,
        "dir": d,
        "palette": palette,
        "meta": meta,
        "display": meta.get("display", name),
        "appearance": meta.get("appearance", "dark"),
        "names": meta.get("names", {}),
        "extras": meta.get("extras", {}),
        "derived": meta.get("waybar", {}),
        "ghostty_theme": (d / "ghostty.theme") if (d / "ghostty.theme").exists() else None,
    }


def list_themes() -> list[str]:
    return sorted(p.parent.name for p in THEMES.glob("*/palette.env"))


def rgb_triple(hex6: str) -> tuple[int, int, int]:
    return tuple(int(hex6[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


# ---------- 替换 ----------


def build_sub(src: dict, dst: dict):
    hexmap = {src["palette"][k]: dst["palette"][k] for k in src["palette"] if k in dst["palette"]}
    decmap = {
        rgb_triple(src["palette"][k]): dst["palette"][k]
        for k in src["palette"]
        if k in dst["palette"] and src["palette"][k] != dst["palette"][k]
    }
    literals: list[tuple[str, str]] = []
    for group in ("extras", "derived"):
        for k, v in src[group].items():
            nv = dst[group].get(k)
            if not nv or nv == v:
                continue
            literals.append((v, nv))
            # 附加槽写的是 hex，但文件里可能用十进制 rgb 或大写 hex 记法：
            # 十进制走 decmap，大写 hex 赊入大小写不敏感的 hexmap（否则 #B792E3 这种会漏）
            for old, new in ((v, nv),):
                hex_re = r"#?[0-9a-fA-F]{6}"
                if re.fullmatch(hex_re, old) and re.fullmatch(hex_re, new):
                    decmap[rgb_triple(old.lstrip('#'))] = new.lstrip("#")
                    hexmap[old.lstrip("#").lower()] = new.lstrip("#").lower()
    literals.sort(key=lambda p: len(p[0]), reverse=True)  # 长串优先，避免被短串截断
    return hexmap, decmap, literals


def apply_sub(text: str, sub) -> tuple[str, int, dict[str, int]]:
    hexmap, decmap, literals = sub
    counts: dict[str, int] = {}
    hits = 0

    for old, new in literals:
        if old in text:
            n = text.count(old)
            text = text.replace(old, new)
            counts["extras:" + old] = n
            hits += n

    def hex_rep(m: re.Match) -> str:
        nonlocal hits
        hash_, hexs = m.group(1), m.group(2)
        key = hexs[:6].lower()
        if key not in hexmap:
            return m.group(0)
        new = hexmap[key] + (hexs[6:].lower() if len(hexs) == 8 else "")
        if hexs.isupper():
            new = new.upper()
        hits += 1
        counts["slot:" + key] = counts.get("slot:" + key, 0) + 1
        return hash_ + new

    text = HEX_RE.sub(hex_rep, text)

    def dec_rep(m: re.Match) -> str:
        nonlocal hits
        triple = tuple(int(m.group(i)) for i in (2, 3, 4))
        new = decmap.get(triple)  # type: ignore[arg-type]
        if not new:
            return m.group(0)
        hits += 1
        counts["rgb:" + ",".join(map(str, triple))] = counts.get(
            "rgb:" + ",".join(map(str, triple)), 0
        ) + 1
        r, g, b = rgb_triple(new)
        return f"{m.group(1)}{r}, {g}, {b}"

    text = DEC_RE.sub(dec_rep, text)
    return text, hits, counts


def ensure_starship_palette(path: Path, name: str, palette: dict[str, str], text: str) -> tuple[str, bool]:
    """自定义主题在 starship.toml 里没有同名色板段时自动补上（已有就不动）。"""
    if not name or re.search(rf"(?m)^\[palettes\.{re.escape(name)}\]", text):
        return text, False
    block = [f"[palettes.{name}]"] + [f'{k} = "#{v}"' for k, v in palette.items()]
    return text.rstrip("\n") + "\n\n" + "\n".join(block) + "\n", True


def icons_variant_mode() -> bool:
    """Papirus 是否已改成「变体模式」（目录软链）——是则图标切换只换链，不重写文件。"""
    return PAPIRUS_LIVE.is_symlink()


def variant_path(name: str) -> Path:
    return ICONS_DIR / f"{VARIANT_PREFIX}{name}"


def swap_icon_link(name: str) -> None:
    """原子换软链：先建临时链再 os.replace，避免出现「Papirus 不存在」的瞬间。"""
    tmp = ICONS_DIR / f".Papirus.new.{os.getpid()}"
    if tmp.is_symlink() or tmp.exists():
        tmp.unlink()
    os.symlink(f"{VARIANT_PREFIX}{name}", tmp)
    os.replace(tmp, PAPIRUS_LIVE)


def ensure_icon_variant(name: str, log: list[str], apply: bool) -> bool:
    """变体缺失（如以后新增主题）时按需生成：从当前变体 cp -al + 换色 + 刷缓存。"""
    if variant_path(name).is_dir():
        return True
    if not apply:
        log.append(f"图标：变体 {VARIANT_PREFIX}{name} 不存在，将按需生成后换链")
        return True
    link = os.readlink(PAPIRUS_LIVE) if PAPIRUS_LIVE.is_symlink() else ""
    src = link[len(VARIANT_PREFIX):] if link.startswith(VARIANT_PREFIX) else ""
    if not src or not variant_path(src).is_dir():
        log.append("图标：找不到可用的源变体，本次保持原样")
        return False
    r = subprocess.run(
        [sys.executable, str(ROOT / "icon-variants.py"), "build",
         "--themes", name, "--from", src, "--tree", str(variant_path(src))],
        capture_output=True, text=True, env=session_env(),
    )
    built = ICONS_DIR / ".theme-studio-stage" / f"{VARIANT_PREFIX}{name}"
    if r.returncode != 0 or not built.is_dir():
        tail = ((r.stderr or r.stdout).strip().splitlines() or [""])[-1][:70]
        log.append(f"图标：变体生成失败 {tail}")
        return False
    os.rename(built, variant_path(name))
    log.append(f"图标：已按需生成 {VARIANT_PREFIX}{name}")
    return True


def expand(conf: Path) -> list[Path]:
    files: list[Path] = []
    for pat in HEX_TARGETS:
        files.extend(sorted(conf.glob(pat)))
    if not icons_variant_mode():  # 变体模式：图标不逐文件重写，只换软链
        for pat in HOME_TARGETS:
            files.extend(sorted(p for p in Path.home().glob(pat) if not p.is_symlink()))
    return [f for f in files if f.is_file()]


def backup_rel(path: Path, conf: Path) -> Path:
    """备份目录内的相对路径：配置目录内保持原结构，$HOME 下的前缀 home/。"""
    for base, prefix in ((conf, ""), (Path.home(), "home"), (Path("/"), "abs")):
        try:
            return Path(prefix) / path.relative_to(base) if prefix else path.relative_to(base)
        except ValueError:
            continue
    return Path("abs") / path.name


def current_palette() -> str | None:
    return STATE.read_text().strip() if STATE.exists() else None


def installed_fcitx5(name: str) -> bool:
    return (HOME / ".local/share/fcitx5/themes" / name).is_dir() or (
        Path("/usr/share/fcitx5/themes") / name
    ).is_dir()


def installed_gtk(name: str) -> bool:
    return (Path("/usr/share/themes") / name).is_dir()


def user_gtk_theme(theme: dict, log: list[str], apply: bool = True) -> str | None:
    """返回该主题应激活的 GTK 主题名；系统里没有就克隆生成用户级主题。"""
    name = theme["names"].get("gtk", "")
    if not name:
        return None
    if installed_gtk(name):
        log.append(f"GTK: 使用系统主题 {name}")
        return name
    out = Path.home() / ".themes" / name
    marker = out / ".theme-studio"
    if marker.exists() and marker.read_text().strip() == theme["name"]:
        log.append(f"GTK: 复用已生成的 ~/.themes/{name}")
        return name
    import importlib.util

    spec = importlib.util.spec_from_file_location("gtkclone", ROOT / "gtk-theme-clone.py")
    if spec is None or spec.loader is None:
        log.append("GTK: 找不到 gtk-theme-clone.py，跳过")
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not apply:  # 干跑不得产生副作用
        _files, results, total = mod.plan(theme["name"])
        log.append(f"GTK: 将生成用户主题 ~/.themes/{name}（{len(results)} 个文件 / {total} 处换色）")
        return name
    files, hits = mod.build(theme["name"], out)
    marker.write_text(theme["name"] + "\n")
    log.append(f"GTK: 生成用户主题 ~/.themes/{name}（{files} 个文件 / {hits} 处换色）")
    return name


def ghostty_theme_exists(name: str) -> bool:
    """ghostty 主题名 = 主题文件名，得在用户目录或系统目录里真存在。"""
    return (HOME / ".config/ghostty/themes" / name).exists() or (
        Path("/usr/share/ghostty/themes") / name
    ).exists()


def proc_environ(field: str, *names: str) -> str | None:
    """从运行中的进程里取环境变量（如 swaync 的 DBUS 地址）。"""
    for p in Path("/proc").glob("[0-9]*/comm"):
        try:
            if p.read_text().strip() not in names:
                continue
            raw = (p.parent / "environ").read_bytes()
        except OSError:
            continue
        for item in raw.split(b"\0"):
            if item.startswith((field + "=").encode()):
                return item.split(b"=", 1)[1].decode(errors="replace")
    return None


def session_env() -> dict[str, str]:
    """在非交互环境（cron/exec）里补齐 Wayland/Hyprland/DBus 会话变量。"""
    env = dict(os.environ)
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    rt = Path(env["XDG_RUNTIME_DIR"])
    if not env.get("WAYLAND_DISPLAY"):
        cands = sorted(p.name for p in rt.glob("wayland-*"))
        if cands:
            env["WAYLAND_DISPLAY"] = cands[0]
    if not env.get("HYPRLAND_INSTANCE_SIGNATURE"):
        live = [d for d in (rt / "hypr").glob("*") if (d / ".socket.sock").exists()]
        if live:
            env["HYPRLAND_INSTANCE_SIGNATURE"] = max(live, key=lambda d: d.stat().st_mtime).name
    if not env.get("DBUS_SESSION_BUS_ADDRESS"):
        bus = proc_environ("DBUS_SESSION_BUS_ADDRESS", "swaync", "waybar", "Hyprland")
        if bus:
            env["DBUS_SESSION_BUS_ADDRESS"] = bus
    return env


# ---------- 主流程 ----------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "show", "current", "switch", "rollback"])
    ap.add_argument("target", nargs="?")
    ap.add_argument("--apply", action="store_true", help="真正写入（默认 dry-run）")
    ap.add_argument("--reload", action="store_true", help="写入后热重载运行中的程序")
    ap.add_argument("--no-gtk", action="store_true", help="不改 GTK 主题（默认会生成/切换 GTK 主题）")
    ap.add_argument("--root", help="配置根目录（默认 ~/.config，用于沙箱验证）")
    ap.add_argument("--force", action="store_true", help="目标=当前主题时也重新套用（用于补齐/修复）")
    ap.add_argument("--from", dest="src", help="指定源主题（默认读 state，再退回 mocha）")
    args = ap.parse_args()

    conf = Path(args.root).expanduser().resolve() if args.root else HOME / ".config"

    if args.cmd == "list":
        cur = current_palette()
        for n in list_themes():
            t = load_theme(n)
            mark = "*" if n == cur else " "
            print(f"{mark} {n:<22} {t['appearance']:<6} {t['display']}")
        return 0
    if args.cmd == "show":
        t = load_theme(args.target or "")
        print(t["dir"] / "theme.toml")
        print((t["dir"] / "theme.toml").read_text())
        return 0
    if args.cmd == "current":
        print(current_palette() or "(未记录，按 catppuccin-mocha 处理)")
        return 0
    if args.cmd == "rollback":
        if not args.target:
            dirs = sorted(d.name for d in BACKUPS.iterdir() if d.is_dir())
            print("可用备份（新->旧）：")
            for d in reversed(dirs[-15:]):
                print(f"  {d}  ({len(list((BACKUPS / d).rglob('*')))} 项)")
            print("\n用法：theme-switch.py rollback <时间戳>")
            return 0
        src_dir = BACKUPS / args.target
        if not src_dir.is_dir():
            sys.exit(f"没有这个备份：{src_dir}")
        for f in sorted(src_dir.rglob("*")):
            if f.is_file():
                rel = f.relative_to(src_dir)
                parts = rel.parts
                if parts and parts[0] == "home":
                    dest = Path.home() / Path(*parts[1:])
                elif parts and parts[0] == "abs":
                    dest = Path("/") / Path(*parts[1:])
                else:
                    dest = conf / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
                print(f"恢复 {dest}")
        print("注意：state 未回写，如需一致请再执行一次 switch")
        return 0

    to_name = args.target
    assert to_name
    from_name = args.src or current_palette() or "catppuccin-mocha"
    if from_name == to_name and not args.force:
        print(f"已经是 {to_name}，无需切换（加 --force 可重新套用/补齐缺失部分）")
        return 0
    src, dst = load_theme(from_name), load_theme(to_name)
    sub = build_sub(src, dst)
    print(f"切换：{src['display']} -> {dst['display']}（{dst['appearance']}）"
          f"   模式：{'APPLY' if args.apply else 'dry-run'}   根目录：{conf}")

    texts: dict[Path, str] = {}
    hits_by: dict[Path, int] = {}
    counts_by: dict[Path, dict] = {}

    def stage(p: Path, new_text: str, hits: int, counts: dict) -> None:
        texts[p] = new_text
        hits_by[p] = hits_by.get(p, 0) + hits
        acc = counts_by.setdefault(p, {})
        for k, v in counts.items():
            acc[k] = acc.get(k, 0) + v

    for path in expand(conf):
        old = path.read_text()
        new, hits, counts = apply_sub(old, sub)
        if hits:
            stage(path, new, hits, counts)

    skipped: list[str] = []
    custom_ghostty = dst["ghostty_theme"]
    for rel, (key, pattern, template) in NAME_TARGETS.items():
        p = conf / rel
        if not p.exists():
            continue
        value = dst["names"].get(key)
        if key == "ghostty" and custom_ghostty:
            value = dst["name"]  # 自定义主题：用主题包名指向随包安装的主题文件
        if not value:
            continue
        if key == "fcitx5" and not installed_fcitx5(value):
            skipped.append(f"{rel}: 主题 {value} 未安装 -> 保留原样")
            continue
        if key == "ghostty" and not custom_ghostty and not ghostty_theme_exists(value):
            skipped.append(f"{rel}: ghostty 主题 {value} 不存在 -> 保留原样（避免终端报错）")
            continue
        old = texts.get(p) or p.read_text()  # 接着色值替换后的文本改，避免覆盖
        new = re.sub(pattern, lambda _m: template.format(value=value), old)
        if new != old:
            stage(p, new, 1, {"name:" + key: 1})

    # 随包安装 ghostty 终端主题文件
    if custom_ghostty:
        target = conf / "ghostty/themes" / dst["name"]
        content = custom_ghostty.read_text()
        if (target.read_text() if target.exists() else None) != content:
            stage(target, content, 1, {"ghostty-theme": 1})

    # 自定义主题：必要时补 starship 色板段
    sp = conf / "starship.toml"
    if sp.exists():
        merged, added = ensure_starship_palette(
            sp, dst["names"].get("starship", ""), dst["palette"], texts.get(sp) or sp.read_text()
        )
        if added:
            stage(sp, merged, 1, {"starship-palette": 1})

    # GTK 主题：系统有就用系统的，没有就克隆基础主题换色生成用户级主题
    gtk_name = None
    gtk_log: list[str] = []
    if not args.no_gtk:
        gtk_name = user_gtk_theme(dst, gtk_log, apply=args.apply)
    if gtk_name:
        for rel in ("gtk-3.0/settings.ini", "gtk-4.0/settings.ini"):
            p = conf / rel
            old = texts.get(p)
            if old is None:
                old = p.read_text() if p.exists() else "[Settings]\ngtk-icon-theme-name=Papirus\n"
            new = re.sub(r"(?m)^\s*gtk-theme-name\s*=.*$", f"gtk-theme-name={gtk_name}", old)
            if "gtk-theme-name" not in new:
                new = new.rstrip("\n") + f"\ngtk-theme-name={gtk_name}\n"
            if new != old or not p.exists():
                stage(p, new, 1, {"gtk-theme-name": 1})

    icon_note: list[str] = []
    icon_ready = False
    if not args.root and icons_variant_mode():
        icon_ready = ensure_icon_variant(to_name, icon_note, apply=args.apply)
        if icon_ready and args.apply:
            # 变体就位后必须把 Papirus 软链指过去 —— 只 build 不换链的话，
            # 切完主题其它地方都变了，唯独文件夹图标还是旧颜色（2026-11-27 修）。
            swap_icon_link(to_name)
            icon_note.append(f"图标：已换链 -> {VARIANT_PREFIX}{to_name}（瞬时）")
        elif icon_ready:
            icon_note.append(f"图标：将换链 {PAPIRUS_LIVE} -> {VARIANT_PREFIX}{to_name}（瞬时）")

    for path, hits in hits_by.items():
        counts = counts_by.get(path, {})
        top = ", ".join(f"{k.split(':')[-1]}×{v}" for k, v in
                        sorted(counts.items(), key=lambda kv: -kv[1])[:4]
                        if k.startswith("slot:"))
        extra = f"  [{top}]" if top else ""
        print(f"  {backup_rel(path, conf)}  {hits} 处{extra}")
    for s in skipped:
        print(f"  [跳过] {s}")
    for line in gtk_log:
        print(f"  {line}")
    for line in icon_note:
        print(f"  {line}")
    if not texts:
        print("  没有任何文件需要改动")

    if not args.apply:
        print(f"\n共 {len(texts)} 个文件待改，合计 {sum(hits_by.values())} 处。"
              f"（dry-run 未写入；加 --apply 落地）")
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = BACKUPS / stamp
    n = 2
    while backup_dir.exists():  # 同一秒内连续切换不能互相覆盖备份
        backup_dir = BACKUPS / f"{stamp}-{n}"
        n += 1
    backup_dir.mkdir(parents=True)
    icon_dirs: set[Path] = set()
    for path, new in texts.items():
        if path.exists():  # 新建文件（如随包安装的 ghostty 主题）没有旧版本可备
            bak = backup_dir / backup_rel(path, conf)
            bak.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, bak)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".theme-studio.tmp")  # 变体树共享 inode：必须换 inode 写
        tmp.write_text(new)
        os.replace(tmp, path)
        if ".local/share/icons" in str(path):  # 图标改了要刷缓存，否则应用还看旧的
            parts = path.parts
            i = parts.index("icons")
            icon_dirs.add(Path(*parts[: i + 2]))
    if not args.root:
        STATE.write_text(to_name + "\n")
        if icon_ready:  # 图标：原子换链（瞬时）
            swap_icon_link(to_name)
            print(f"  图标变体已换链: {VARIANT_PREFIX}{to_name}")
    print(f"\n已写入 {len(texts)} 个文件；备份：{backup_dir}")
    for d in sorted(icon_dirs):
        if shutil.which("gtk-update-icon-cache"):
            r = subprocess.run(["gtk-update-icon-cache", "-f", "-t", str(d)],
                               capture_output=True, text=True)
            print(f"  图标缓存已刷新: {d}" if r.returncode == 0 else f"  图标缓存刷新失败: {r.stderr.strip()[:60]}")

    if args.apply and gtk_name and not args.root:
        env = session_env()
        r = subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", gtk_name],
            capture_output=True, text=True, env=env,
        )
        if r.returncode == 0:
            print(f"  GTK 主题已激活: {gtk_name}")
        else:
            print(f"  GTK 主题激活失败: {(r.stderr or '').strip()[:70]}")
    if args.reload and not args.root:
        env = session_env()
        if not env.get("HYPRLAND_INSTANCE_SIGNATURE"):
            print("  [提示] 没找到 Hyprland IPC socket，跳过 hyprctl reload")
        for label, cmd in RELOAD:
            if not shutil.which(cmd[0]):
                print(f"  reload {label}: 未安装，跳过")
                continue
            if cmd[0] == "hyprctl" and not env.get("HYPRLAND_INSTANCE_SIGNATURE"):
                continue
            r = subprocess.run(cmd, capture_output=True, text=True, env=env)
            if r.returncode == 0:
                print(f"  reload {label}: ✓")
            elif cmd[0] == "pkill" and r.returncode == 1:
                print(f"  reload {label}: 未在运行，跳过")
            else:
                msg = (r.stdout or r.stderr or "").strip().splitlines()
                print(f"  reload {label}: ✗ rc={r.returncode} {msg[0][:70] if msg else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

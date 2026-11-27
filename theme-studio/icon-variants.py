#!/usr/bin/env python3
"""Papirus 图标主题变体（T3）：预生成每套主题的变色树，切换 = 换目录软链（瞬时）

设计（2026-10-09 实测数据）：
  * 活动树 304MB / 65,283 个真 SVG / 42,979 个软链；其中只有 16,458 个文件带主题色。
  * 每套变体 = cp -al 全树硬链接克隆（1.1s）+ 只重写带色文件（temp+rename，1.8s）+ 刷缓存（1.4s）。
    硬链接克隆每套实际只多吃 ~23MB（其余与其它变体共享 inode）。
  * 铁律：带色文件一律 temp+rename 写；绝不在活动树/其它变体里原地写（会穿透共享 inode）。
  * 切换 = os.replace 原子换 Papirus 软链，≈0.05s。

用法：
  icon-variants.py build [--themes A,B] [--from NAME] [--out DIR]   建变体（默认全部主题）
  icon-variants.py list                      查看变体状态
  icon-variants.py install [--from NAME]     一次性上线：活动树改名为变体 + Papirus 软链 + 搬入暂存变体
  icon-variants.py switch <主题名>            把 Papirus 软链指向对应变体（瞬时）
  icon-variants.py status
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parent
ICONS = HOME / ".local/share/icons"
LIVE = ICONS / "Papirus"
STAGE = ICONS / ".theme-studio-stage"
PREFIX = "Papirus-"


def engine():
    spec = importlib.util.spec_from_file_location("tswitch", ROOT / "theme-switch.py")
    if spec is None or spec.loader is None:
        sys.exit("找不到 theme-switch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def variant_path(name: str) -> Path:
    return ICONS / f"{PREFIX}{name}"


def live_is_variant_mode() -> bool:
    return LIVE.is_symlink()


def swap_link(name: str) -> None:
    """原子换软链：临时链 + os.replace。"""
    tmp = ICONS / f".Papirus.new.{os.getpid()}"
    if tmp.is_symlink() or tmp.exists():
        tmp.unlink()
    os.symlink(f"{PREFIX}{name}", tmp)
    os.replace(tmp, LIVE)


def recolor_tree(src_text: str, sub, out: Path, cache: bool) -> tuple[int, int]:
    """把 src_text 按 sub 换色写到 out（temp+rename）。返回 (是否写入, 命中数)。"""
    new, hits, _ = engine().apply_sub(src_text, sub)
    if not hits:
        return 0, 0
    tmp = out.with_name(out.name + ".zt.tmp")
    tmp.write_text(new)
    os.replace(tmp, out)
    return 1, hits


def build(themes: list[str], src_name: str, out_root: Path, tree: Path | None = None) -> None:
    E = engine()
    src = E.load_theme(src_name)
    hex_id = {v: v for v in src["palette"].values()}
    dec_id = {E.rgb_triple(v): v for v in src["palette"].values()}
    lits = [(v, v) for v in list(src["extras"].values()) + list(src["derived"].values())
            if isinstance(v, str)]
    detect = (hex_id, dec_id, lits)
    subs = {t: E.build_sub(src, E.load_theme(t)) for t in themes if t != src_name}

    src_tree = tree or LIVE
    if not src_tree.is_dir() or src_tree.is_symlink():
        sys.exit(f"构建源不是普通目录：{src_tree}")

    t0 = time.time()
    files = [p for p in src_tree.rglob("*") if p.is_file() and not p.is_symlink()]
    print(f"源树 {src_tree}：{len(files)} 个真文件；源主题 {src_name}；目标变体 {len(subs)} 套")

    # 1) 硬链接克隆
    out_root.mkdir(parents=True, exist_ok=True)
    for t in subs:
        d = out_root / f"{PREFIX}{t}"
        if d.exists():
            shutil.rmtree(d)
        subprocess.run(["cp", "-al", str(src_tree), str(d)], check=True)
    t_clone = time.time() - t0
    print(f"[1/3] cp -al 克隆 {len(subs)} 套：{t_clone:.1f}s")

    # 2) 单遍扫描 + 只重写带色文件
    t0 = time.time()
    changed = 0
    per_theme = {t: 0 for t in subs}
    for p in files:
        rel = p.relative_to(src_tree)
        try:
            text = p.read_text(errors="surrogateescape")
        except OSError:
            continue
        _t, hits, _c = E.apply_sub(text, detect)
        if not hits:
            continue
        changed += 1
        for t, sub in subs.items():
            wrote, _h = recolor_tree(text, sub, out_root / f"{PREFIX}{t}" / rel, cache=True)
            per_theme[t] += wrote
    t_recolor = time.time() - t0
    print(f"[2/3] 扫描 {len(files)} 文件、{changed} 个带主题色；重写：{t_recolor:.1f}s")
    for t, n in sorted(per_theme.items()):
        print(f"      {PREFIX}{t}: 重写 {n} 个文件")

    # 3) 每套刷图标缓存（先 unlink 掉克隆来的共享 inode）
    t0 = time.time()
    for t in subs:
        d = out_root / f"{PREFIX}{t}"
        c = d / "icon-theme.cache"
        if c.exists() or c.is_symlink():
            c.unlink()
        r = subprocess.run(["gtk-update-icon-cache", "-f", "-t", str(d)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"      ⚠ {PREFIX}{t} 刷缓存失败：{(r.stderr or '').strip()[:80]}")
    print(f"[3/3] 刷 {len(subs)} 套图标缓存：{time.time()-t0:.1f}s")
    print(f"完成，共 {time.time()-t0+t_clone+t_recolor:.0f}s")


def cmd_list() -> None:
    E = engine()
    cur = E.current_palette()
    print(f"活动树：{LIVE}  {'（软链 -> %s）' % os.readlink(LIVE) if LIVE.is_symlink() else '（普通目录）'}")
    for n in E.list_themes():
        d = variant_path(n)
        mark = "*" if n == cur else " "
        state = "缺失"
        if d.is_dir():
            state = f"已建 ({len(list(d.rglob('*.svg')))} svg)"
        print(f"{mark} {n:<22} {PREFIX}{n:<32} {state}")
    if STAGE.is_dir():
        print(f"暂存区 {STAGE}：" + ", ".join(sorted(p.name for p in STAGE.iterdir())))


def cmd_install(src_name: str | None, stage: Path) -> None:
    E = engine()
    src_name = src_name or E.current_palette() or "catppuccin-mocha"
    if live_is_variant_mode():
        sys.exit("已经是变体模式（Papirus 已是软链），无需再 install")
    if not LIVE.is_dir():
        sys.exit(f"活动图标树不存在或不是目录：{LIVE}")
    # 1) 活动树改名当「当前主题」的变体（同盘 rename，瞬时、不复制）
    dst = variant_path(src_name)
    if dst.exists():
        sys.exit(f"目标变体已存在，请先手工处理：{dst}")
    os.rename(LIVE, dst)
    print(f"活动树改名 -> {dst}")
    # 2) 建软链
    swap_link(src_name)
    print(f"建立软链 {LIVE} -> {PREFIX}{src_name}")
    # 3) 搬入暂存变体（同盘 rename）
    moved = 0
    if stage.is_dir():
        for d in sorted(stage.iterdir()):
            target = ICONS / d.name
            if d.name == dst.name:
                shutil.rmtree(d)      # 多余的一份（与活动树共享 inode），删安全
                continue
            if target.exists():
                print(f"  跳过（已存在）：{target}")
                continue
            os.rename(d, target)
            moved += 1
        try:
            stage.rmdir()
        except OSError:
            pass
    print(f"搬入暂存变体 {moved} 套；暂存区已清")
    cmd_list()


def cmd_switch(name: str) -> None:
    E = engine()
    if not variant_path(name).is_dir():
        sys.exit(f"没有这个变体：{variant_path(name)}（先 build）")
    swap_link(name)
    print(f"已切换：{LIVE} -> {PREFIX}{name}")


def cmd_status() -> None:
    if live_is_variant_mode():
        target = os.readlink(LIVE)
        print(f"模式：变体（LIVE -> {target}）")
        probe = LIVE / "24x24/places/folder.svg"
        if probe.exists():
            import re
            cols = re.findall(r"#[0-9A-Fa-f]{6}", probe.read_text(errors="replace"))
            from collections import Counter
            print("folder.svg 颜色：", Counter(c.upper() for c in cols).most_common(4))
    else:
        print("模式：传统（LIVE 是普通目录，切换会逐文件重写）")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "list", "install", "switch", "status"])
    ap.add_argument("target", nargs="?")
    ap.add_argument("--themes", help="逗号分隔的主题包名，默认全部")
    ap.add_argument("--from", dest="src", help="源主题（默认读 state）")
    ap.add_argument("--out", help=f"变体输出目录（默认 {STAGE}）")
    ap.add_argument("--tree", help="构建源树目录（默认活动树；按需生成时指向源变体）")
    args = ap.parse_args()
    E = engine()
    cur = args.src or E.current_palette() or "catppuccin-mocha"
    if args.cmd == "build":
        themes = args.themes.split(",") if args.themes else E.list_themes()
        out = Path(args.out).expanduser() if args.out else STAGE
        build(themes, cur, out, Path(args.tree).expanduser() if args.tree else None)
    elif args.cmd == "list":
        cmd_list()
    elif args.cmd == "install":
        cmd_install(args.src, Path(args.out).expanduser() if args.out else STAGE)
    elif args.cmd == "switch":
        cmd_switch(args.target or "")
    else:
        cmd_status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

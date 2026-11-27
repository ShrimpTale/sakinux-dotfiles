# 主题系统

> 一处改色，全场跟随。

`theme-studio/` 把整个桌面的配色收敛到 **26 个色槽**，切换主题 = 改一处调色板。

```bash
zhuti                      # 交互选择（fzf，带真彩色带预览）
zhuti list                 # 列出 6 个主题包
zhuti preview Nordic       # 只看色带
zhuti dry Catppuccin Latte # 干跑
zhuti rollback <时间戳>    # 整体回滚
```

引擎默认 **dry-run**，写入前逐文件备份。替换目标 9 个：`waybar/{mocha.css,style.css}`、`wlogout/{style.css,icons/*.svg}`、`fastfetch/config.jsonc`、`ghostty/config`、`gtk-3.0/gtk.css`、`fuzzel/fuzzel.ini`、`hypr/themes/*.lua`。

| 生成器 | 作用 |
|---|---|
| `make-themes.py` | 26 个色值 → 反推整套 `theme.toml`（`accent_soft`/`hover_bg`/`folder_shade`… 的派生规则来自对现有桌面的反推） |
| `make-canvas.py` | **自制主题 Morandi Canvas**：CIELAB 空间定规则（中性色 L\*8→96、强调色等亮度 L\*≈72、掺灰 C\*≤24），输出时实测 WCAG 对比度并回调 |
| `make-nordic.py` | **自制主题 Nordic Fjord**：色相锁 214° 冷蓝灰、S≤18%，强调色 212° |
| `gtk-theme-clone.py` | 把系统 GTK 主题整树复制到 `~/.themes/<名>` 再整体换色 |
| `icon-variants.py` | Papirus 6 套变色变体（硬链接克隆 + 只重写 16,458 个带色 SVG + 原子换链，切换 0.05s） |
| `gtk-block.py` | 生成 `@define-color` 覆盖块（当前未启用，留作备选） |

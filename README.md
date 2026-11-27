# sakinux

> 自用手搓的键盘流 Hyprland 桌面美化

![Hyprland](https://img.shields.io/badge/Hyprland-0.57-58E1FF?style=for-the-badge&labelColor=%23424242)
![Arch](https://img.shields.io/badge/Arch_Linux-rolling-1793D1?style=for-the-badge&labelColor=%23424242)
![Catppuccin](https://img.shields.io/badge/Catppuccin-Mocha-CBA6F7?style=for-the-badge&labelColor=%23424242)
![Themes](https://img.shields.io/badge/themes-6-A6E3A1?style=for-the-badge&labelColor=%23424242)
![License](https://img.shields.io/badge/license-MIT-B2FF59?style=for-the-badge&labelColor=%23424242)

[![桌面](screenshots/desktop.png)](screenshots/desktop.png)

没有 dock，没有桌面图标，就一条 30px 的浮岛顶栏挂在上面，别的基本都靠键盘。

- **全键盘**：开程序、切窗口、平铺、截图、关机，全有键。鼠标基本只拿来点网页链接
- **一条栏**：waybar 拆成左中右三块浮岛，缝里透出壁纸。毛玻璃只给 waybar、rofi、wlogout 这三个浮层，普通窗口老老实实不透明
- **一个调色板**：26 个色槽，改一处，顶栏、关机菜单、终端、GTK、图标、光标、输入法全跟着换
- **两套自己调的主题**：Morandi Canvas 是用 CIELAB 算出来的，出图前还跑一遍 WCAG 对比度；Nordic Fjord 锁 214° 冷蓝灰
- **顺手写的小东西**：GTK4 的 Wi-Fi 菜单（763 行，密码走 DBus 不进命令行）、6 个 waybar 模块、Papirus 换色生成器

## Preview

| fastfetch + Nemo | wlogout（`Super+Delete`） |
|:---:|:---:|
| [![fastfetch 与 Nemo](screenshots/fastfetch.png)](screenshots/fastfetch.png) | [![wlogout](screenshots/wlogout.png)](screenshots/wlogout.png) |

> [!NOTE]
> 这套是照着 1920×1200、Intel 核显、`BAT0` 电池调的。换机器要改哪几处，我记在 [已知问题](docs/install.md#已知问题) 里了。

## 安装

<details>
    <summary>自动</summary>

```bash
git clone <this-repo> ~/dotfiles && cd ~/dotfiles
./install.sh --dry-run     # 先看它要动哪些文件
./install.sh               # 你原来有的会先备份到 ~/.dotfiles-backup-<时间戳>/
systemctl --user enable --now cliphist
```

装完注销重登一次。缺哪些依赖、还有哪几步得手动做，都在 [docs/install.md](docs/install.md)。

</details>

<details>
    <summary>手动</summary>

- 基础依赖：`hyprland waybar wlogout rofi swaync ghostty starship fastfetch cliphist`，别忘了 `ttf-jetbrains-mono-nerd`
- 外观：`catppuccin-gtk-theme-mocha`、`catppuccin-cursors-mocha`、`papirus-icon-theme`
- 搬文件：`config/` → `~/.config/`，`local/` → `~/.local/`，`gtk-themes/` → `~/.themes/`
- `config/wlogout/style.css`、`config/fastfetch/config.jsonc`、`config/autostart/bongocat.desktop` 里的 `@@HOME@@` 换成你自己的家目录
- 图标想跟着主题变色就跑 `python3 theme-studio/icon-variants.py build`

</details>

## 键位

| 键 | 动作 |
|---|---|
| `Super+Q` / `Super+C` | 终端 / 关窗 |
| `Super+R` | 启动器 |
| `Super+E` | 文件管理器 |
| `Super+方向键` | 移焦点 |
| `Super+1..0` | 切工作区 |
| `Super+Shift+1..0` | 把窗口丢到那个工作区 |
| `Super+V` / `Super+P` / `Super+J` | 浮动切换 / 伪平铺 / 切分屏方向 |
| `Super+S` | 特殊工作区（暂存器） |
| `Super+Alt+X` | 区域截图，存盘 + 进剪贴板 |
| `Super+Alt+V` | 剪贴板历史 |
| `Super+Delete` | wlogout 关机菜单 |

剩下的快捷键、鼠标操作在 [docs/keybinds.md](docs/keybinds.md)。

## 还想看细节

- [装的时候有哪些坑、哪些值是绑机器的](docs/install.md)
- [完整键位](docs/keybinds.md)
- [26 槽怎么换色、6 个生成器各干什么](docs/theme-studio.md)
- [为什么是这么设计的，代价是什么](docs/design.md)
- [没传的那些（壁纸/锁屏/rofi 主题/图标/光标…）是谁的、你自己怎么搞](docs/not-included.md)

## Thanks to

- [HyDE](https://github.com/HyDE-Project/HyDE)：wlogout 的观感是照它的 `style_1` 扒的
- [Catppuccin](https://github.com/catppuccin)：色值、GTK 主题基座、光标、fcitx5 皮肤、ghostty 配色
- [Papirus](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme) + papirus-folders：图标底子
- [BongoCat](https://github.com/ayangweb/BongoCat)：右下角那只猫
- [waywallen](https://github.com/waywallen/waywallen)：动态壁纸客户端
- [Hyprland](https://github.com/hyprwm/Hyprland)：配置骨架来自它自带的 Lua 模板
- wlogout 的图标出自 onlinewebfonts.com 的 Svg Vector Icons

## License

MIT，只覆盖我自己写的部分。上游那些授权情况 [这里](docs/not-included.md) 各节都写了。随便抄，抄坏了别怪我。

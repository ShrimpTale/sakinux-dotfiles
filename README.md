# sakinux

> 自用手搓的键盘流 Hyprland 桌面美化

![Hyprland](https://img.shields.io/badge/Hyprland-0.57-58E1FF?style=for-the-badge&labelColor=%23424242)
![Arch](https://img.shields.io/badge/Arch_Linux-rolling-1793D1?style=for-the-badge&labelColor=%23424242)
![Catppuccin](https://img.shields.io/badge/Catppuccin-Mocha-CBA6F7?style=for-the-badge&labelColor=%23424242)
![Themes](https://img.shields.io/badge/themes-6-A6E3A1?style=for-the-badge&labelColor=%23424242)
![License](https://img.shields.io/badge/license-MIT-B2FF59?style=for-the-badge&labelColor=%23424242)

[![桌面](screenshots/desktop.png)](screenshots/desktop.png)

根据自己使用习惯慢慢手搓的键盘流美化，除了waybar与hyprland别无他物

大部分功能通过绑定快捷键进行，力图做到简约现代

## Preview

| fastfetch + Nemo | wlogout（`Super+Delete`） |
|:---:|:---:|
| [![fastfetch 与 Nemo](screenshots/fastfetch.png)](screenshots/fastfetch.png) | [![wlogout](screenshots/wlogout.png)](screenshots/wlogout.png) |

> [!NOTE]
> 基于1920×1200、与`BAT0` 电池，可能需根据设备调整

## 安装

<details>
    <summary>自动</summary>

```bash
git clone <this-repo> ~/dotfiles && cd ~/dotfiles
./install.sh --dry-run     
./install.sh               
systemctl --user enable --now cliphist
```

装完需重启桌面

</details>

<details>
    <summary>手动</summary>

- 基础依赖：`hyprland waybar wlogout rofi swaync ghostty starship fastfetch cliphist ttf-jetbrains-mono-nerd`
- 外观：`catppuccin-gtk-theme-mocha`、`catppuccin-cursors-mocha`、`papirus-icon-theme`
- 搬文件：`config/` → `~/.config/`，`local/` → `~/.local/`，`gtk-themes/` → `~/.themes/`
- `config/wlogout/style.css`、`config/fastfetch/config.jsonc`、`config/autostart/bongocat.desktop` 里的 `@@HOME@@` 换成本地～目录
- zhuti命令切换主题需要 `python3 theme-studio/icon-variants.py build`

</details>

## 键位，可于hyprland.lua更改

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


## Thanks to

- [HyDE](https://github.com/HyDE-Project/HyDE)：wlogout视觉效果
- [Catppuccin](https://github.com/catppuccin)：色值、GTK 主题基座、光标、fcitx5 皮肤、ghostty 配色
- [Papirus](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme) + papirus-folders：图标
- [BongoCat](https://github.com/ayangweb/BongoCat)：桌宠
- [waywallen](https://github.com/waywallen/waywallen)：动态壁纸客户端
- [Hyprland](https://github.com/hyprwm/Hyprland)

## License

MIT， [详见此文件](docs/not-included.md)

# 安装与依赖

> 回到 [主页](../README.md)

## 快速开始

```bash
git clone <this-repo> ~/dotfiles && cd ~/dotfiles
./install.sh --dry-run     # 先看会做什么
./install.sh               # 安装（已存在的文件先备份到 ~/.dotfiles-backup-<时间戳>/）
```

装完还有几条一次性步骤：

```bash
systemctl --user enable --now cliphist        # 剪贴板历史，否则 Super+Alt+V 是空的
pacman -S ttf-jetbrains-mono-nerd             # 全局唯一字体
python3 theme-studio/icon-variants.py build   # 生成 Papirus 变色图标（需要先有 Papirus）
# 注销重登，让 hyprland.lua / GTK 主题 / 图标全部生效
```

没有显示管理器的方案（tty1 登录后直接进桌面）在 `local/bin/start-desktop` + `.bash_profile` 里，`install.sh` 会一起装上。

## 依赖

```
hyprland (≥0.57, 要 lua 配置支持)   waybar (0.16.x)   wlogout   rofi (2.0)   swaync
ghostty   starship   fastfetch   cliphist   wl-clipboard
grim   slurp   playerctl   brightnessctl   pavucontrol   blueman   polkit-gnome
uwsm   fcitx5   eza   bat   zoxide   python (3.11+)
```

外观：

```
ttf-jetbrains-mono-nerd                          字体
catppuccin-gtk-theme-mocha                       GTK 主题基座
catppuccin-cursors-mocha                         光标
papirus-icon-theme + papirus-folders             图标基座
python-gobject + gtk4 + libnm                    Wi-Fi 菜单
```

## 仓库结构

```
config/         → ~/.config/
  hypr/         hyprland.lua(主体,lua) hyprland-gui.lua(空占位) hypridle.conf
                themes/catppuccin-mocha.lua(26 槽) scripts/hypr-dpms.sh
  waybar/       config style.css mocha.css + clock/temp/battery/media/mpris 等模块
  wlogout/      layout style.css icons/*.svg
  ghostty/ fastfetch/ fcitx5/ fuzzel/ gtk-3.0/ gtk-4.0/ autostart/
local/          → ~/.local/
  bin/          wifi-menu bongocat screenshot.sh cliphist-select.sh start-desktop …
  share/        wifi-menu/wifi-menu.py(GTK4 Wi-Fi 菜单) fcitx5/themes/…
gtk-themes/     → ~/.themes/ 5 套（Catppuccin 三风味 + 2 套自制）
theme-studio/   26 槽换色引擎 + zhuti CLI + 6 个生成器 + 6 个主题包
README.md  CHANGES-vs-live.md  install.sh  LICENSE
starship.toml  .bashrc  .bash_profile
```

`CHANGES-vs-live.md` 记录了「仓库版」和「这台机器上跑的版本」的每一处差异（剔除了哪些、改了什么），想核对改动就看它。

## 已知问题

1. **`config/waybar/config` 不是严格 JSON**（有尾逗号）。waybar 的 jsoncpp 认，`jq` 不认 —— 校验前先 `sed 's/,\(\s*[}\]])/\1/g'`。
2. **`wifi-menu` 的 `APP_ID = "dev.xxhjppx.wifimenu"`** 同时也是 `hyprland.lua` 里窗口规则的匹配串，改一处必须改另一处。
3. **`hyprland.lua` 里的 `hl.exec_cmd("cliphist daemon")` 是无效命令**（cliphist 没有 `daemon` 子命令）。真正生效的是包自带的 `cliphist.service`，记得 `systemctl --user enable cliphist`。
4. **`hyprland-gui.lua` 是 0 字节**，由 HypMod 生成，但末尾 `require("hyprland-gui")` 依赖它存在，别删。
5. **机器专属值**：`battery.sh` 的 `BAT0` / `FULL_AT=96`、`temp.sh` 的 `thermal_zone9`、`waybar` 的 `intel_backlight`、桌宠坐标 1580,842 —— 不匹配就改名字或直接删模块。
6. **`Super+Alt+{A,P}`** 原本指向私有程序，已注释，装了再把注释解开。
7. **`wlogout` 的「休眠」是真按钮**（`systemctl hibernate`），要求 swap ≥ 内存 + `resume=` + initramfs 有 `resume` hook，否则点了没反应。

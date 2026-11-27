# 没收录的部分：归属与 DIY

> 这些我用了但没打包（体积 / 版权 / 绑这台机器）。每项都写了：用的是谁的东西、为什么没传、你自己怎么弄。

这些我用了、但**不打包**（体积、版权、或者绑这台机器）。下面每一项都写了：用的是谁的东西、为什么没传、你自己怎么弄出来。

### 壁纸

**归属**：Wallpaper Engine（Steam 付费订阅）+ Linux 客户端 [waywallen](https://github.com/waywallen/waywallen) 或 Steam 版客户端。素材是买来的，不能分发。

**为什么没传**：素材版权 + 体积（我这套库 344MB）。

**自己实现**（三选一）：

```bash
# ① 静态图，最省事
pacman -S hyprpaper
# ~/.config/hypr/hyprpaper.conf:
#   preload = ~/Pictures/wall.png
#   wallpaper = eDP-1, ~/Pictures/wall.png

# ② 动态壁纸（本地视频）
paru -S mpvpaper && mpvpaper -o "no-audio --loop" '*' ~/Videos/wall.mp4

# ③ 用 Wallpaper Engine 素材：装 waywallen（或 Steam 上的 Wallpaper Engine）
```

然后把 `config/hypr/hyprland.lua` 里被注释掉的那行换成你的壁纸程序：

```lua
-- hl.exec_cmd("/opt/waywallen-bin/usr/bin/waywallen --no-ui")
```

### 锁屏

**归属**：[hyprlock](https://github.com/hyprwm/hyprlock)（Hyprland 官方）。

**为什么没传**：本机根本没做锁屏美化 —— `hypridle.conf` 的 `lock_cmd` 一直是注释状态。`wlogout` 的「锁定」格调的是系统默认 hyprlock。

**自己实现**：写 `~/.config/hypr/hyprlock.conf`，最小可用：

```ini
background { monitor = ; path = ~/Pictures/wall.png ; blur_passes = 2 }
input-field {
    monitor = ; size = 250, 60 ; outline_thickness = 2
    inner_color = rgba(108,112,134,0.5) ; font_color = rgb(cdd6f4)
    font_family = JetBrainsMono Nerd Font ; placeholder_text = 输入密码
}
label { monitor = ; text = cmd[update:1000] echo "$(date +%H:%M)" ; font_size = 120 ; color = rgb(cba6f7) }
```

再在 `hypridle.conf` 里加 `general { lock_cmd = hyprlock }` + 一个 300 秒的 listener 即可。参考 [hyprlock 文档](https://wiki.hypr.land/Hypr-Ecosystem/hyprlock/)。

### rofi 主题（启动器 / 剪贴板菜单）

**归属**：我这套是 [HyDE](https://github.com/HyDE-Project/HyDE) 的 `quickapps` 风格改的；另一个常见来源是 [catppuccin/rofi](https://github.com/catppuccin/rofi)。

**为什么没传**：只收录了程序，样式没进仓库 —— 现在 `Super+R` 用的是 rofi 默认外观。

**自己实现**：

```bash
# ① 拿现成的
git clone https://github.com/catppuccin/rofi && cp rofi/basic/.config/rofi/*.rasi ~/.config/rofi/
# ② 或者从默认主题导出一份自己改
rofi -dump-theme > ~/.config/rofi/my.rasi
```

然后让 `hyprland.lua` 的启动器指过去（注意本仓库那行故意没带 `-theme`）：

```lua
local menu = "pkill -x rofi || rofi -normal-window -no-lazy-grab -click-to-exit -show drun -show-icons -theme " .. HOME .. "/.config/rofi/my.rasi"
```

⚠️ `-normal-window` 是安全模式：rofi 2.0 的 layer 模式在部分机器上会吃键盘 grab（卡死要重启会话）。换成 `rofi-wayland` 后可以去掉，并让 `hyprland.lua` 里那条 `rofi-blur` layer_rule 生效。

### 通知中心

**归属**：[swaync](https://github.com/ErikReider/SwayNotificationCenter) + [catppuccin/swaync](https://github.com/catppuccin/swaync) 配色。

**为什么没传**：样式没进仓库，通知仍由 swaync 守护进程提供（默认外观），`screenshot.sh` 的 `notify-send` 也靠它。

**自己实现**：

```bash
mkdir -p ~/.config/swaync
git clone https://github.com/catppuccin/swaync /tmp/swaync-catppuccin
cp /tmp/swaync-catppuccin/themes/mocha/style.css ~/.config/swaync/style.css
# config.json 里调位置/宽度，参考上游 README
```

### btop / yazi / cava

**归属**：都是 [Catppuccin](https://github.com/catppuccin) 的官方移植：`catppuccin/btop`、`catppuccin/yazi`。

**为什么没传**：只留程序不留样式。

**自己实现**：

```bash
# btop：主题文件丢进 ~/.config/btop/themes/，在 btop.conf 里 color_theme = "catppuccin_mocha"
curl -LO https://raw.githubusercontent.com/catppuccin/btop/main/themes/catppuccin-mocha.theme

# yazi：flavor 或直接拷 theme.toml
ya pkg add yazi-rs/flavors:catppuccin-mocha      # 新版 yazi 用 ya pkg
# 在 ~/.config/yazi/yazi.toml 里 [manager] flavor = "catppuccin-mocha"

# cava：不用主题文件，直接写 4 个渐变色（取 26 槽里的值）
# [color] gradient_color_1 = '#cba6f7' … _4 = '#89dceb'
```

### 图标（随主题变色）

**归属**：[Papirus](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme) + [papirus-folders](https://github.com/PapirusDevelopmentTeam/papirus-folders)，文件夹配色方案来自 Papirus 自带的 `cat-mocha-mauve` 等预设。

**为什么没传**：一份 Papirus 就有 6.5 万个 SVG（304MB），6 套变体没法进 git —— 但**生成器在仓库里**（`theme-studio/icon-variants.py`），4 秒重建。

**自己实现**：

```bash
paru -S papirus-icon-theme papirus-folders
papirus-folders -l                       # 看可选配色
papirus-folders -C cat-mocha-mauve       # 换成 Catppuccin Mocha 紫
python3 theme-studio/icon-variants.py build          # 生成 6 套变体
python3 theme-studio/icon-variants.py switch nordic-fjord   # 瞬时切换
```

### 光标

**归属**：[catppuccin/cursors](https://github.com/catppuccin/cursors)（AUR 包 `catppuccin-cursors-mocha`，装完 `/usr/share/icons/` 下有 16 套）。

**为什么没传**：素材不进仓库，只写「怎么启用」。**光标不是装了就生效**，三处都要设：

```lua
-- config/hypr/hyprland.lua，放在 hl.on("hyprland.start") 里
hl.env("XCURSOR_THEME", "catppuccin-mocha-mauve-cursors")     -- 管新启动的程序
hl.env("HYPRCURSOR_THEME", "catppuccin-mocha-mauve-cursors")  -- 管 hyprcursor 原生
hl.exec_cmd("hyprctl setcursor catppuccin-mocha-mauve-cursors 24")  -- 管 Hyprland 已画的
```

漏掉 `setcursor` 就会出现「一半界面新箭头、一半旧箭头」。

### GTK 主题

**归属**：[catppuccin/gtk](https://github.com/catppuccin/gtk)（AUR 包 `catppuccin-gtk-theme-mocha`，按强调色和尺寸生 40 多套）。

**为什么传了**：仓库里那 5 套是**成品**（9.7MB），`~/.themes/` 直接可用；其中 `morandi-canvas`、`nordic-fjord` 是用 `gtk-theme-clone.py` 从 Catppuccin 基座换色生成的**自制版**。

**自己重新生成**：

```bash
python3 theme-studio/gtk-theme-clone.py nordic-fjord      # 输出到 ~/.themes/nordic-fjord
python3 theme-studio/gtk-theme-clone.py morandi-canvas --check   # 只报会替换多少处
```

### 输入法皮肤

**归属**：[catppuccin/fcitx5](https://github.com/catppuccin/fcitx5)（本仓库已收录，`local/share/fcitx5/themes/`）。

启用：`~/.config/fcitx5/conf/classicui.conf` 里 `Theme=catppuccin-mocha-mauve`。

### 终端里的彩色 logo（fastfetch）

**归属**：自己把图转成 ANSI 色块，不是别人的作品。

**自己换图**：

```bash
pacman -S chafa
chafa -f symbols -s 90x45 你的图.png > ~/.config/fastfetch/logo.txt
```

`config/fastfetch/config.jsonc` 里 `"logo": { "type": "raw", "source": "…/logo.txt" }`。

### 企业微信 / 容器 / 自建播放器

这些是**纯私有工具链**，没有任何参考价值，全部剔除：企业微信（社区 Wine 版 + 两扇幽灵窗的窗口规则）、ros1/ros2 容器与 redroid 安卓容器（对应 4 个 waybar 模块和 `Super+U`）、自建弹幕播放器、Apple Music 客户端。

如果你只需要「容器状态显示在顶栏」，思路是：waybar 的 `custom` 模块 + 一个输出 JSON 的脚本，`docker inspect` 拿状态即可。

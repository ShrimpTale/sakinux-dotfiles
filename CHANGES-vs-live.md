# 仓库 vs 真机：逐项差异

本文件记录「上传版」与这台机器上实际运行的配置之间**所有**差异，便于审计和日后同步。
生成时间：2026-11-27 14:5x（本地时区 Asia/Shanghai）

## 一、整块剔除（真机有，仓库没有）

| 内容 | 真机位置 | 原因 |
|---|---|---|
| 锁屏配置 | `~/.config/hypr/hyprlock.conf`（97 行） | 主人明确不上传任何 hyprlock |
| 锁屏头像 | `~/.config/hypr/avatar.png`（653K） | 只被上面那个文件引用 |
| 锁屏颜色 | `~/.config/hypr/mocha.conf`（1.2K） | `grep` 结果：仅被 `hyprlock.conf:2` 的 `source =` 引用 |
| 锁屏播放信息脚本 | `~/.config/hypr/scripts/songdetail.sh` | 仅被 hyprlock 调用（且该脚本写死 `playerctl -p spotify`） |
| 企业微信（3 处 + 1 个工具） | `hyprland.lua` 的 `Super+Alt+Q` 绑定、主窗/幽灵窗规则块、`hl.on("window.open")` 事件；`~/.local/bin/wecom-ring-shadow`(178 行) + `wecom-ring-shadow.service` | 私有工具链 |
| 容器工具 | `hyprland.lua` 的 `xhost-allow-container.sh` 自启、`Super+U`→`ros-open.sh`；`waybar/{ros,android}-*.sh`、`ros1.sh`、`ros2.sh`、`ros-active`、`xhost-allow-container.sh`；`waybar/config` 的 `custom/ros`、`custom/android` 两个模块 | 私有环境 |
| 壁纸引擎 | `~/.config/waywallen/`；`hyprland.lua` 的 waywallen 启动行 | 不含壁纸 |
| rofi 主题 | `~/.config/rofi/*.rasi`（4 个） | 按要求不收录；`Super+R` 改用 rofi 默认外观 |
| swaync 样式 | `~/.config/swaync/{config.json,style.css}` | 同上；通知仍由 swaync 守护进程提供（默认外观） |
| btop / yazi / cava 配置 | `~/.config/{btop,yazi,cava}/` | 同上 |
| wlogout 的「休眠禁用」改造 | `wlogout/{layout,style.css,icons/hibernate-disabled.svg}` + `restore-hibernate/`(5 文件) | **设备特有**（本机 `CanHibernate=na`）。已用备份原件还原成标准按钮 `systemctl hibernate` |
| 全部备份 | `hyprland.lua.bak-*`×13、`waybar/config.bak-*`×3、`waybar/style.css.bak-*`、`wlogout/*.bak*`、`cava/备份`、`fastfetch/config (复制 1).jsonc`、`swaync/style.css.catppuccin-backup` | 历史快照 |
| 杂物 | `swaync/教材.c`、`cava/shaders/`、`cava/themes/`（config 里 0 引用） | 无引用 |
| theme-studio 运行时 | `backups/`（46 个快照 294MB）、`state`、`__pycache__` | 运行时产物 |

## 二、逐文件修改

| 文件 | 改动 | 行数 |
|---|---|---|
| `config/hypr/hyprland.lua` | ① 删企业微信绑定 + 注释（2 行）<br>② 删企业微信规则块（含 `hl.on("window.open")` 幽灵窗事件 + 2 条 tag 规则）<br>③ 删 `xhost-allow-container.sh` 自启（注释+调用）<br>④ 删 `Super+U` → `ros-open.sh`（注释+绑定）<br>⑤ waywallen 启动行 → 注释 + 说明（+2）<br>⑥ `Super+Alt+A`(Sidra)、`Super+Alt+P`(Marchen) → 注释 + 说明（+2）<br>⑦ `/home/<user>` → `HOME .. "`，顶部加 `local HOME = os.getenv("HOME")` | 727 → 665 |
| `config/hypr/hyprland.lua`（第 2 轮） | 启动器 `menu` 去掉 `-theme …/rofi/launcher.rasi`，注释改为「本仓库不含 rofi 主题」 | — |
| `local/bin/cliphist-select.sh` | 去掉 `-theme …/rofi/dmenu.rasi` | — |
| `config/wlogout/{layout,style.css}` | 用备份原件还原：`action` → `systemctl hibernate`、图标 → `hibernate.svg`、删掉「休眠禁用开始/结束」整块 | 81 → 61 |
| `theme-studio/theme-switch.py` | `HEX_TARGETS` 删 `swaync/style.css`、`cava/config`、`yazi/catppuccin-*.toml` | — |
| `theme-studio/make-*.py` + 6 个 `theme.toml` | 删 `yazi = …` 的 name 映射 | — |
| `install.sh` | 依赖体检去掉 `yazi/cava/btop` | — |
| `config/waybar/config` | 删 `custom/android`、`custom/ros`（modules-center 2 项 + 2 个模块定义）；路径 → `$HOME` | 200 → 177 |
| `config/hypr/hypridle.conf` | 2 处路径 → `$HOME`；删掉锁屏相关的注释块（`lock_cmd`/`unlock_cmd`/5 分钟锁屏 listener），只留"10 分钟熄屏" | 20 → 14 |
| `config/wlogout/style.css` | 6 处图标路径 → `@@HOME@@`（GTK CSS 不展开变量） | 不变（81） |
| `config/wlogout/restore-hibernate/style.css.orig` | 6 处 → `@@HOME@@`；`restore.sh` 增加一步展开 | +5 |
| `config/fastfetch/config.jsonc` | 删 `"format": "12th Gen Intel(R) Core(TM) i5-12450H"`；logo 路径 → `@@HOME@@` | 104 → 103 |
| `config/autostart/bongocat.desktop` | Exec 路径 → `@@HOME@@`（XDG Exec 不展开 `$HOME`） | 不变 |
| `.bashrc` | `xhost +` 整段注释掉并说明（安全放宽，默认关） | 19 → 20 |
| `theme-studio/zhuti` | `ROOT` 从 `$HOME/.openclaw/workspace/theme-studio` 改为**脚本自身所在目录** | 不变 |
| `local/bin/{wifi-menu,launch-nyan.sh}`、`local/share/wifi-menu/restart.sh` | 路径 → `$HOME` | 不变 |

## 三、新增（真机没有）

| 文件 | 说明 |
|---|---|
| `README.md` | 95 行：标题 + 一句注 + 5 徽章 + **主图** + 6 条口语化功能 + 2 图 Preview + 2 个安装折叠块 + 键位表 + 文档索引 + thanks |
| `docs/design.md` | 设计取舍（6 条）与代价（4 条） |
| `docs/install.md` | 快速开始 / 依赖 / 仓库结构 / 已知问题 |
| `docs/keybinds.md` | 完整键位表 |
| `docs/theme-studio.md` | 26 槽引擎、`zhuti` 用法、6 个生成器 |
| `docs/not-included.md` | 12 项未收录内容的归属 + DIY 步骤 |
| `install.sh` | 安装器：先备份、按映射拷贝、展开 `@@HOME@@`、依赖体检。支持 `--dry-run` |
| `LICENSE` | MIT（含上游 attribution 声明） |
| `.gitignore` | 排除`.bak*`/`__pycache__`/theme-studio 运行时产物 |
| `CHANGES-vs-live.md` | 本文件 |
| `screenshots/{desktop,fastfetch,wlogout}.png` | 3 张 1920×1200 实拍（主人上传的附件，已落进仓库，不再依赖 GitHub 附件链接） |

## 四、保留的「本机专属」，故意不改

| 位置 | 值 | 为什么留着 |
|---|---|---|
| `waybar/config` | `"device": "intel_backlight"` | 绝大多数 Intel 笔记本通用；不匹配就换名字 |
| `waybar/battery.sh` | `BAT0`、`FULL_AT=96` | 同上 |
| `waybar/temp.sh` | `thermal_zone9` | 温度传感器编号因机型而异，脚本不匹配就静默不显示 |
| `hyprland.lua` | `layout-*` 规则里的 937×560 / 1580,842 等坐标 | 对应 1920×1200 屏；已注释掉启动命令，规则留着当示例 |
| `hyprland.lua` | `BongoCat` 窗口 312×287 @ 1580,842 | 桌宠定位 |
| `wifi-menu.py` + `hyprland.lua` | `APP_ID = dev.xxhjppx.wifimenu` | 作者命名空间；**两处必须一起改** |

## 五、未经运行验证的部分

| 项 | 风险 |
|---|---|
| `install.sh` 全流程 | 只跑过 `--dry-run`；真实安装会覆盖 `~/.config`，未在本机执行（会破坏正在用的桌面） |
| `theme-studio` 换主题 | 引擎与原机一致，只改了 `zhuti` 的 `ROOT` 解析；未在临时目录跑过完整 `switch` |
| `gtk-block.py` | 生成了但本机从未启用（`gtk.css` 里 0 处 `@define-color`），未验证效果 |
| `icon-variants.py` | 需要先有 Papirus 基座；本机已有，未在干净环境验证 |
| 光标 | 真机已用 `hyprctl setcursor` 生效（返回 `ok`）+ 配置持久化；但 16 套里的其它颜色未测 |

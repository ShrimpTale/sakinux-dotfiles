# 截图清单

主页 README 引用了下面 4 张必需图 + 2 张可选图。文件放本目录，**文件名必须一致**，否则 README 里不显示。

| 文件名 | 拍什么 | 必需 |
|---|---|---|
| `desktop.png` | 桌面全景：壁纸 + 顶栏 + 一个终端窗口 | ✅ |
| `fastfetch.png` | 终端：`fastfetch` 的彩色 logo + starship 提示符 | ✅ |
| `wlogout.png` | `Super+Delete` 的关机菜单（3×2 六格全露） | ✅ |
| `waybar.png` | 顶栏特写：三块浮岛 + 工作区罗马数字 + 音乐控件 + 系统区 | ✅ |
| `launcher.png` | `Super+R` 启动器 | ⬜ 可选 |
| `gtk.png` | Nemo：半透明底 + 马卡龙紫选中高亮 | ⬜ 可选 |

## 拍之前

- 分辨率建议 **1920×1200**（和配置假定的屏幕一致），`grim` 默认截当前输出全屏
- **把私密东西关掉**：聊天窗口、带书名/文件名的 Nemo、浏览器标签、终端里 `pwd` 显示的路径
- 顶栏的托盘区不要有乱七八糟的临时图标
- 想截到鼠标指针：`grim` 默认不画光标，需要 `grim -p`（`-p` 是画光标）

## 命令

```bash
mkdir -p ~/dotfiles/screenshots && cd ~/dotfiles/screenshots

# 1) 桌面全景 —— 先把终端放好（建议右半屏，露出壁纸左侧）
grim desktop.png

# 2) fastfetch —— 在 ghostty 里跑 fastfetch，让提示符那行也在画面里
grim fastfetch.png

# 3) 顶栏特写 —— 截全屏再裁上半部分（或用 slurp 框选）
grim -g "$(slurp)" waybar.png
#   全屏后在图片里裁也行：顶栏高 30px + 浮岛圆角，建议裁 y=0..90 的一条

# 4) wlogout —— 先按 Super+Delete 让菜单出来，再截
#    ⚠️ 用 hyprctl 挪光标不会触发 GTK 的 hover 效果，所以别指望截出"悬停高亮"，
#       就截常态即可（真要悬停效果得手动把鼠标移上去再截）
grim wlogout.png

# 5) 可选：启动器
#    Super+R 弹出后：
grim launcher.png

# 6) 可选：Nemo
#    打开 Nemo，选几个文件（出现紫色高亮）后：
grim gtk.png
```

## 拍完检查

```bash
cd ~/dotfiles/screenshots && ls -la *.png
# 每张图都该在 1-3MB 之间；如果只有几十 KB，多半截到了空白区
```

再顺手压一下体积（可选，`oxipng`/`zopflipng` 任选）：

```bash
paru -S oxipng && oxipng -o 4 --strip safe *.png
```

README 里的表格写的是相对路径，图放进来就自动显示，不需要改 README。

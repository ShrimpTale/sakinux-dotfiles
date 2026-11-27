export PATH="$HOME/.npm-global/bin:$PATH"
export PATH="/usr/bin:$PATH"
# ===== PATH =====
# 把 ~/.local/bin 加入 PATH，放最前面优先查找
export PATH="$HOME/.local/bin:$PATH"

# ===== 常用 alias =====
alias ls='eza'
alias la='eza -la'
alias lt='eza --tree'
alias cat='bat'
alias v='vim'
# ===== zoxide 智能跳转（Bash 版本初始化） =====
eval "$(zoxide init bash)"
eval "$(starship init bash)"
# 原句：允许 Docker 容器访问 X11 显示。公开版默认注释掉 ——
# `xhost +` 等于对所有本机/容器进程开放 X 服务器，是主动放宽安全边界，按需自己打开。
# if [[ $DISPLAY ]]; then
#     xhost + > /dev/null 2>&1
# fi

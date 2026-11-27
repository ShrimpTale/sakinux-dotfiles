#
# ~/.bash_profile
#

[[ -f ~/.bashrc ]] && . ~/.bashrc

# ===== 免 SDDM：tty1 登录后自动进 Hyprland（2026-09-27 主人批准方案 C） =====
if [ -z "$WAYLAND_DISPLAY" ] && [ -z "$DISPLAY" ] && [ "$(tty 2>/dev/null)" = "/dev/tty1" ]; then
  [ -x "$HOME/.local/bin/start-desktop" ] && "$HOME/.local/bin/start-desktop"
fi

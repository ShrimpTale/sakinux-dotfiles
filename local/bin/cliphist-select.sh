#!/bin/bash
# 剪贴板历史选择器：cliphist + rofi（2026-10-13 由 fuzzel 迁移到 rofi）
cliphist list | rofi -dmenu -i -p "󰅎 剪贴板" | cliphist decode | wl-copy

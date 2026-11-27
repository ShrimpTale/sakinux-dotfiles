#!/bin/bash
echo "$(date): 尝试启动 Timeshift" >> /tmp/timeshift-debug.log
echo "DISPLAY=$DISPLAY" >> /tmp/timeshift-debug.log
echo "WAYLAND_DISPLAY=$WAYLAND_DISPLAY" >> /tmp/timeshift-debug.log
echo "XAUTHORITY=$XAUTHORITY" >> /tmp/timeshift-debug.log
/usr/bin/pkexec /usr/bin/timeshift-gtk 2>> /tmp/timeshift-debug.log
echo "退出码: $?" >> /tmp/timeshift-debug.log
echo "---" >> /tmp/timeshift-debug.log

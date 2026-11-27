#!/bin/bash
sleep 2
ghostty --title="clock-terminal" -e /usr/bin/bash -c "/usr/bin/tty-clock -c -C 7 -s" &

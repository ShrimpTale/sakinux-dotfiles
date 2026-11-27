#!/bin/bash
session="nyan"
/usr/bin/tmux kill-session -t "$session" 2>/dev/null
/usr/bin/tmux new-session -d -s "$session" "/usr/bin/nyancat"
/usr/bin/tmux split-window -h -t "$session" "/usr/bin/cava; exec /usr/bin/bash"
/usr/bin/tmux set-option -t "$session" status off
/usr/bin/tmux attach-session -t "$session"

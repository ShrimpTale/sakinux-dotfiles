#!/bin/bash
sleep 1
ghostty --title="info-terminal" -e /usr/bin/bash -c "/usr/bin/fastfetch; exec /usr/bin/bash" &

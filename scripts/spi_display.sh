#!/usr/bin/env bash
# Desktop login starts the supervised kiosk; repeated calls create no extra windows.
set -euo pipefail
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
systemctl --user import-environment DISPLAY XAUTHORITY
systemctl --user start rdk-x5-kiosk.service

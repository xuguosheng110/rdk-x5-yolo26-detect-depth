#!/usr/bin/env bash
# systemd owns the browser and restarts it if it exits. No external network needed.
set -euo pipefail
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
until xset q >/dev/null 2>&1; do sleep 2; done
xset s off
xset s noblank
xset -dpms || true

# Prevent desktop power management from blanking the exhibition display later.
if command -v xfconf-query >/dev/null; then
  set_pref() {
    local channel=$1 property=$2 type=$3 value=$4
    if xfconf-query -c "$channel" -p "$property" >/dev/null 2>&1; then
      xfconf-query -c "$channel" -p "$property" -s "$value"
    else
      xfconf-query -c "$channel" -p "$property" -n -t "$type" -s "$value"
    fi
  }
  set_pref xfce4-power-manager /xfce4-power-manager/dpms-enabled bool false
  set_pref xfce4-power-manager /xfce4-power-manager/blank-on-ac int 0
  set_pref xfce4-power-manager /xfce4-power-manager/inactivity-on-ac uint 0
  set_pref xfce4-session /general/SaveOnExit bool false
fi

# The camera may enumerate late; wait without a fixed startup deadline.
until curl -fsS --max-time 2 http://127.0.0.1:8080/stats.json >/dev/null; do sleep 2; done
profile="$HOME/.local/share/rdk-x5-vision/firefox"
mkdir -p "$profile"
cat > "$profile/user.js" <<'PREFS'
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("browser.startup.page", 0);
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("browser.sessionstore.max_resumed_crashes", 0);
user_pref("browser.tabs.warnOnClose", false);
user_pref("browser.fullscreen.autohide", true);
PREFS
exec firefox --new-instance --profile "$profile" --kiosk 'http://127.0.0.1:8080/?spi'

#!/usr/bin/env bash
# Install exhibition startup without downloading models or recompiling.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $(id -u) == 0 && $(pwd) == /app/rdk-x5-vision ]] || {
  echo 'Run as root from /app/rdk-x5-vision on the X5' >&2; exit 1;
}
for program in firefox xset curl xfconf-query; do command -v "$program" >/dev/null; done
test -x cpp/build/yolo26_dual
backup="output/exhibition-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup"
for file in /etc/systemd/system/rdk-x5-vision.service \
    /etc/lightdm/lightdm.conf.d/90-rdk-x5-exhibition.conf \
    /home/sunrise/.config/autostart/rdk-x5-vision.desktop \
    /home/sunrise/.config/autostart/xscreensaver.desktop \
    /home/sunrise/.config/systemd/user/rdk-x5-kiosk.service; do
  if [[ -f "$file" ]]; then cp --parents "$file" "$backup/"; fi
done
chmod 755 scripts/spi_display.sh scripts/kiosk_session.sh
install -m644 config/rdk-x5-vision.service /etc/systemd/system/rdk-x5-vision.service
install -d -o sunrise -g sunrise /home/sunrise/.config/autostart /home/sunrise/.config/systemd/user
install -o sunrise -g sunrise -m644 config/rdk-x5-vision.desktop /home/sunrise/.config/autostart/
install -o sunrise -g sunrise -m644 config/rdk-x5-kiosk.service /home/sunrise/.config/systemd/user/
cat > /home/sunrise/.config/autostart/xscreensaver.desktop <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Screensaver disabled for RDK X5 exhibition
Hidden=true
DESKTOP
chown sunrise:sunrise /home/sunrise/.config/autostart/xscreensaver.desktop
mkdir -p /etc/lightdm/lightdm.conf.d
cat > /etc/lightdm/lightdm.conf.d/90-rdk-x5-exhibition.conf <<'LIGHTDM'
[Seat:*]
autologin-user=sunrise
autologin-user-timeout=0
user-session=xfce
LIGHTDM
systemctl set-default graphical.target
systemctl daemon-reload
systemctl enable --now rdk-x5-vision.service
if [[ -S /tmp/.X11-unix/X0 && -S /run/user/1000/bus ]]; then
  runuser -u sunrise -- env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus systemctl --user daemon-reload
  runuser -u sunrise -- /app/rdk-x5-vision/scripts/spi_display.sh
fi
echo "Exhibition startup installed. Previous files saved in $backup"

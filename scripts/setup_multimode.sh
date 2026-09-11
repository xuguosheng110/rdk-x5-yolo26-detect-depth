#!/usr/bin/env bash
# Install after scripts/install.sh; preserves the original USB demo and kiosk.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $(id -u) == 0 && $(pwd) == /app/rdk-x5-vision ]] || { echo 'Run as root in /app/rdk-x5-vision'; exit 1; }
for pkg in mipi_cam hobot_stereonet mono2d_body_detection face_age_detection; do
  test -d "/opt/tros/humble/share/$pkg" || { echo "Missing TROS package: $pkg"; exit 1; }
done
python3 -c 'import cv2,numpy'
bash scripts/build.sh
backup="output/multimode-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup" output/body /run/rdk-vision
for f in /etc/systemd/system/rdk-x5-{vision,camera,bridge,mode,portal}.service; do
  [[ ! -f "$f" ]] || cp "$f" "$backup/"
done
cp -a /opt/tros/humble/lib/mono2d_body_detection/config output/body/
[[ -f config/selected-mode.env ]] || printf 'RDK_MODE=yolo\n' > config/selected-mode.env
for service in camera bridge mode portal; do
  install -m644 "config/rdk-x5-$service.service" /etc/systemd/system/
done
systemctl disable --now rdk-x5-vision.service
systemctl daemon-reload
systemctl enable rdk-x5-camera rdk-x5-bridge rdk-x5-mode rdk-x5-portal
systemctl start rdk-x5-portal
# Do not start a second camera over a manually running MIPI process.
echo 'Installed. Reboot once to activate camera, selected mode and SPI kiosk.'
echo 'LAN: http://<BOARD_IP>:8080/   SPI: http://127.0.0.1:8080/?spi'

#!/usr/bin/env bash
# Run on the X5 after deploying this project to /app/rdk-x5-vision.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $(id -u) == 0 ]] || { echo 'Run as root on the X5' >&2; exit 1; }
[[ "$(pwd)" == /app/rdk-x5-vision ]] || { echo 'Deploy to /app/rdk-x5-vision first' >&2; exit 1; }
grep -aq 'RDK X5' /sys/firmware/devicetree/base/model || { echo 'X5 required' >&2; exit 1; }
apt-get install -y --no-install-recommends build-essential cmake libopencv-dev libdrm-dev libyuv-dev v4l-utils curl xdotool x11-utils x11-xserver-utils
bash scripts/download_models.sh
bash scripts/build.sh
mkdir -p output
# This named drop-in belongs to this demo and selects the repository preset.
mkdir -p /etc/systemd/system/rdk-x5-vision.service.d
printf '[Service]\nExecStart=\nExecStart=/usr/bin/python3 -u /app/rdk-x5-vision/scripts/run.py\n' > /etc/systemd/system/rdk-x5-vision.service.d/models.conf
bash scripts/setup_exhibition.sh

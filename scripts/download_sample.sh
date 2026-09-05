#!/usr/bin/env bash
# Optional upstream test image; excluded from Git and governed by its upstream terms.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p assets
expected=c02019c4979c191eb739ddd944445ef408dad5679acab6fd520ef9d434bfbc63
if [[ -f assets/bus.jpg ]] && [[ $(sha256sum assets/bus.jpg | cut -d ' ' -f1) == "$expected" ]]; then
  echo 'Sample already verified'; exit 0
fi
curl -fL --retry 3 --connect-timeout 15 https://ultralytics.com/images/bus.jpg -o assets/bus.jpg.part
printf '%s  assets/bus.jpg.part\n' "$expected" | sha256sum -c -
mv assets/bus.jpg.part assets/bus.jpg

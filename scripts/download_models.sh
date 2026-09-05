#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p models
fetch() {
  local name="$1" expected="$2" url="$3"
  if [[ -f "models/$name" ]] && [[ "$(sha256sum "models/$name" | cut -d ' ' -f1)" == "$expected" ]]; then
    echo "Verified $name"; return
  fi
  curl -fL --retry 3 --connect-timeout 15 "$url" -o "models/$name.part"
  echo "$expected  models/$name.part" | sha256sum -c -
  mv "models/$name.part" "models/$name"
}
fetch yolo26n_detect_bayese_640x640_nv12.bin e889ad1feb76ab319f59cd72bf12418f18043e851e5fcab0818917c37e5edba4 https://archive.d-robotics.cc/downloads/rdk_model_zoo/rdk_x5/Ultralytics_YOLO_OE_1.2.8/yolo26n_detect_bayese_640x640_nv12.bin
fetch yolo26n_depth_bayese_768x768_nv12.bin e55091eb594e20e37e6c36a36cce42a94ad80ec651ae893a2143cd2273ed9b0b https://archive.d-robotics.cc/downloads/rdk_model_zoo/rdk_x5/yolo26_depth/yolo26n_depth_bayese_768x768_nv12.bin
fetch yolo26s_detect_bayese_640x640_nv12.bin fb31906ed8968d6fc84c79d7b9951b5d83521022cb0853b78a3923f8ab29de02 https://archive.d-robotics.cc/downloads/rdk_model_zoo/rdk_x5/Ultralytics_YOLO_OE_1.2.8/yolo26s_detect_bayese_640x640_nv12.bin
fetch yolo26s_depth_bayese_768x768_nv12.bin 0e43958195f504d7a8ac48b1c99f4802cd9a4c3580321bfb251d0e0f892ccf4c https://archive.d-robotics.cc/downloads/rdk_model_zoo/rdk_x5/yolo26_depth/yolo26s_depth_bayese_768x768_nv12.bin

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build cpp/build -j4
ctest --test-dir cpp/build --output-on-failure

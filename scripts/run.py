#!/usr/bin/env python3
"""Start the X5 demo with a reversible 30fps camera profile."""
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTROLS = ['auto_exposure', 'exposure_time_absolute', 'exposure_dynamic_framerate', 'power_line_frequency']


def main():
    args = sys.argv[1:]
    if '--help' in args:
        print('''RDK X5 detection + relative depth, browser http://BOARD:8080
Usage: scripts/run.sh [options]
  --source 0             V4L2 index, /dev/videoN, or video file
  --cam-w 640 --cam-h 480 --cam-fps 30
  --keep-camera-settings Skip the temporary manual 10ms / anti-flicker off profile
  --preset quality       quality=S/S, balanced=S/N, nano=N/N
  --track                Enable C++ person ByteTrack (off by default)
  --hdmi                 Enable HDMI on /dev/dri/card1; requires a connected monitor
  --max-seconds 60        Bounded test; default continuous
  --score 0.25 --nms 0.45 --grid-cols 4 --grid-rows 3 --no-grid
  --image assets/bus.jpg --save output/bus_dual.jpg
  --det-model PATH --dep-model PATH  Official X5 float32-output NV12 BIN models
Camera settings are restored on normal exit, SIGINT and SIGTERM.
Depth numbers are relative, not meters; 30fps refers to unique displayed camera frames.''')
        return 0
    config=json.loads((ROOT/'config/runtime.json').read_text())
    preset=config['default_preset']
    if '--preset' in args:
        index=args.index('--preset');preset=args[index+1];del args[index:index+2]
    if preset not in config['presets']:
        raise RuntimeError('Unknown preset; expected nano, balanced, quality')
    for flag,key in [('--det-model','detect'),('--dep-model','depth')]:
        if flag not in args: args.extend([flag,str(ROOT/'models'/config['presets'][preset][key])])
    keep = '--keep-camera-settings' in args
    if keep:
        args.remove('--keep-camera-settings')
    source = args[args.index('--source') + 1] if '--source' in args else '0'
    device = '/dev/video' + source if source.isdigit() else source
    binary = ROOT / 'cpp/build/yolo26_dual'
    if not binary.is_file():
        raise RuntimeError('Build first: bash scripts/build.sh')
    lock = open(ROOT / 'output/run.lock', 'a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError('An instance is already running in this project')
    previous = {}
    child = None
    stopping = False

    def ctl(*options, check=True):
        return subprocess.run(['v4l2-ctl', '-d', device, *options],
                              check=check, text=True, capture_output=True)

    def on_signal(sig, _frame):
        nonlocal stopping
        stopping = True
        if child is not None and child.poll() is None:
            child.send_signal(sig)

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)
    try:
        if device.startswith('/dev/video') and '--image' not in args and not keep:
            raw = ctl('--get-ctrl=' + ','.join(CONTROLS)).stdout
            for name in CONTROLS:
                match = re.search(rf'^{name}:\s*(-?\d+)', raw, re.M)
                if not match:
                    raise RuntimeError(f'Camera lacks {name}; use --keep-camera-settings')
                previous[name] = int(match[1])
            ctl('--set-ctrl=auto_exposure=1,exposure_dynamic_framerate=0,power_line_frequency=0')
            ctl('--set-ctrl=exposure_time_absolute=100')
            print('[camera] temporary manual 10ms profile; original settings saved', flush=True)
        if stopping:
            return 130
        child = subprocess.Popen([str(binary), *args], cwd=ROOT,
                                 env=dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1'))
        return child.wait()
    finally:
        if previous:
            # Exposure can only be restored while the camera is in manual mode.
            failures = []
            for settings in ['auto_exposure=1', f'exposure_time_absolute={previous["exposure_time_absolute"]}',
                             ','.join(f'{k}={v}' for k, v in previous.items() if k != 'exposure_time_absolute')]:
                result = ctl('--set-ctrl=' + settings, check=False)
                if result.returncode:
                    failures.append(result.stderr)
            if failures:
                print('[camera] RESTORE FAILED: ' + '; '.join(failures), file=sys.stderr)
            else:
                print('[camera] original settings restored', flush=True)
        lock.close()


if __name__ == '__main__':
    (ROOT / 'output').mkdir(exist_ok=True)
    try:
        sys.exit(main())
    except (RuntimeError, subprocess.CalledProcessError, IndexError) as error:
        print(f'[error] {error}', file=sys.stderr)
        sys.exit(1)

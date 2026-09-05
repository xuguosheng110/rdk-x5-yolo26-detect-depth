# Sources and licenses

- Reference application: https://github.com/maxma615/yolo26-detect-depth-demo , commit `915b37a2991da043c8c715e285fbc3d596235bdb`, MIT. Original license retained in LICENSE. The cpp, tracking, overlay, metrics and web files are modified derivatives.
- Reference article: https://forum.d-robotics.cc/t/topic/35680 . Target was S100P, not X5; its throughput figures do not apply to this board.
- Official X5 model and inference reference: https://github.com/D-Robotics/rdk_model_zoo/tree/rdk_x5 , commit `3dce01e784b0ac1f5bd1486525fa9df28b79c953`, Apache-2.0 sample code. Pinned Python wrappers and license retained under vendor/rdk_model_zoo. Ultralytics models retain their upstream model licensing.
- X5 depth decoding: samples/vision/yolo26_depth/runtime/{cpp,python}, exp(calibrated log depth), relative depth only.
- X5 detection decoding: samples/vision/ultralytics_yolo26/runtime/python/yolo26_det.py, 3 pairs of class logits / LTRB outputs, classwise NMS.

Port changes: X5 hbPackedDNNHandle_t, hbDNNInfer/hbDNNWaitTaskDone/hbDNNReleaseTask, hbSys allocations and cache operations, sysMem[0], one packed NV12 input. S100 UCP calls and scheduler backend masks are not used. All outputs are validated as contiguous float32 before decoding. X5 telemetry uses /sys/class/devfreq/3a000000.bpu and /sys/devices/system/bpu/ratio. SPI is card0, HDMI is card1. Unsupported metric-depth conversion is rejected instead of labelling normalized values as meters.

The complete unmodified S100P Git archive snapshot is retained in references/s100p; its SHA256 manifest is references/s100p-manifest.json. X5-specific changes are in the repository root.

Optional bus.jpg test image: https://ultralytics.com/images/bus.jpg , SHA256 c02019c4979c191eb739ddd944445ef408dad5679acab6fd520ef9d434bfbc63. Downloaded separately with scripts/download_sample.sh, not redistributed in this repository.

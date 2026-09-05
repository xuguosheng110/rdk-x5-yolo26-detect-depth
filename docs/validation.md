# 验证与复测

## 已完成的板端验证

测试平台：RDK X5 V1.0，RDK OS 3.5.0，内核 6.1.83，DNN 1.24.5 / HBRT 3.15.55，BPU 约 996MHz。USB 摄像头 640×480 MJPEG，临时手动 10ms 曝光。ByteTrack 关闭，SPI Firefox 全屏运行。

- CTest 3/3：ByteTrack、browser overlay、system metrics。公开版又在板端独立目录完成 Release 构建和 3/3 测试；[发布检查摘要](../reports/publication_checks.json)。
- 双 S 稳态 64.2 秒：视频编码 29.58fps，检测 18.30fps，深度 14.55fps；BPU 平均 83.55%、P95 91%、瞬时最大 100%。[原测量摘要](../reports/quality_final_60s_summary.json)。
- S/N 对照：[测量摘要](../reports/s_detect_n_depth_summary.json)。
- N/N 对照：[由原采样计算的摘要](../reports/nano_spi_30s_summary.json)。
- 官方 bus.jpg 单图对照：高置信检测匹配 IoU 均大于 0.99999；深度 log 输出余弦相似度 0.999875，相对误差 P95 约 4.39%。[结果](../reports/verification_summary.json)。这是同一模型实现的数值一致性检查，不是数据集 mAP 或深度精度评估。
- 完成实际重启、全屏、屏幕常亮、浏览器与推理退出恢复检查。[展会摘要](../reports/exhibition_summary.json)。

公开仓库保留统计结果，不包含原始室内相机抓屏、完整检测样本、设备启动 ID 或局域网地址。X5 应用核心源码与实机版本一致；发布整理只调整文档、辅助脚本的本机默认地址、二维码与无效的上游打包规则。

## 复测

```bash
cd /app/rdk-x5-vision
bash scripts/build.sh
python3 scripts/measure_live.py --help
# 默认测量本机服务；实际参数见 --help
python3 scripts/measure_live.py --seconds 65 --output output/live_benchmark.json
```

单图数值对照需要板端官方 Python 运行时及其依赖（与主 C++ 服务的依赖不同）：

```bash
bash scripts/download_sample.sh
systemctl stop rdk-x5-vision
mkdir -p reports/verify_quality output
bash scripts/run.sh --preset quality --image assets/bus.jpg --verify-dir reports/verify_quality --save output/bus_dual.jpg
python3 scripts/verify_models.py
systemctl start rdk-x5-vision
```

单图脚本保留固定版本官方解码，检测阈值 IoU > 0.95；深度中位相对误差 < 3%、P95 < 10%。它依赖系统 `hbm_runtime`、OpenCV、NumPy 及官方 Python 示例所需库，不能在普通 x86 环境冒充 BPU 测试。

帧率定义见 [architecture.md](architecture.md)。SPI 全帧物理上限见 [spi-display.md](spi-display.md)。

# 参考方案与来源

## S100P 原始案例

- 作者项目：[maxma615/yolo26-detect-depth-demo](https://github.com/maxma615/yolo26-detect-depth-demo)
- 社区文章：[RDK S100P · YOLO26 检测 + 单目深度双模型 BPU 并发实时演示](https://forum.d-robotics.cc/t/topic/35680)
- 固定提交：[`915b37a2991da043c8c715e285fbc3d596235bdb`](https://github.com/maxma615/yolo26-detect-depth-demo/tree/915b37a2991da043c8c715e285fbc3d596235bdb)
- 本仓库快照：[s100p/](s100p/)，由该提交 `git archive` 导出，保留全部已跟踪源码、文档和许可证。不是子模块，普通 clone 即可获得。
- 原许可证：[MIT](s100p/LICENSE)。原作者代码和文档保持不变，文件哈希清单见 [s100p-manifest.json](s100p-manifest.json)。

该案例提供双线程 BPU 推理、MJPEG 面板、深度网格、原生 C++ ByteTrack、HDMI/KMS 等结构。本项目在此基础上适配 X5 的模型格式、DNN API、NV12 内存、模型输出、BPU 指标节点和 SPI 浏览器展示。

**S100P 目录仅供阅读和对照。其脚本、模型路径和性能数据属于原设备，不可直接用于 X5；请在仓库根目录执行 X5 安装脚本。** S100P 在本项目中未重新实机验证。上游文档中的“米”换算和高帧率描述不能作为 X5 的精度或显示能力承诺。

## 官方 X5 模型和推理示例

- [D-Robotics/rdk_model_zoo · rdk_x5](https://github.com/D-Robotics/rdk_model_zoo/tree/rdk_x5)
- 对照代码固定提交：[`3dce01e784b0ac1f5bd1486525fa9df28b79c953`](https://github.com/D-Robotics/rdk_model_zoo/tree/3dce01e784b0ac1f5bd1486525fa9df28b79c953)
- [YOLO26 检测](https://github.com/D-Robotics/rdk_model_zoo/tree/3dce01e784b0ac1f5bd1486525fa9df28b79c953/samples/vision/ultralytics_yolo26)
- [YOLO26 深度](https://github.com/D-Robotics/rdk_model_zoo/tree/3dce01e784b0ac1f5bd1486525fa9df28b79c953/samples/vision/yolo26_depth)
- [本仓库保留的官方对照代码](../vendor/rdk_model_zoo/)及其 [Apache-2.0 许可证](../vendor/rdk_model_zoo/LICENSE)

模型下载地址和 SHA256 在 [download_models.sh](../scripts/download_models.sh) 中。采用 X5 Bayes-e NV12 BIN，不能替换成 S100P Nash HBM。模型许可由原模型提供方规定，应用代码的 MIT 许可证不改变模型许可。

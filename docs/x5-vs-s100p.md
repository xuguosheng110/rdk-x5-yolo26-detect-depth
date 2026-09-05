# X5 与 S100P：移植边界

| 项目 | S100P 参考案例 | 本项目 X5 |
|---|---|---|
| BPU 模型平台 | Nash | Bayes-e |
| 部署模型 | HBM | 官方 X5 BIN |
| 推理/调度 API | hbDNNInferV2 / hbUCP | hbDNNInfer / hbDNNWaitTaskDone / hbDNNReleaseTask |
| 内存与缓存 | hbUCP 分配及缓存接口 | hbSysAllocCachedMem / hbSysFlushMem / hbSysFreeMem |
| NV12 输入 | 参考路径使用分离 Y / UV | 一个连续 Y+UV 缓冲区，sysMem[0] |
| 输出 | 取决于原案例模型 | 校验连续 float32 输出，拒绝未适配的量化或 padding 布局 |
| 检测 | 原案例模型选型 | N 或 S，640×640 NV12，三组分类/LTRB 输出 |
| 深度 | 原案例模型选型 | N 或 S，768×768 NV12，exp 解码已校准 log-depth |
| BPU 频率节点 | 28108000.bpu | 3a000000.bpu |
| BPU 使用率 | sysfs 硬件计数 | /sys/devices/system/bpu/ratio，缺失时不伪造数值 |
| 显示 | MJPEG + HDMI/KMS | MJPEG + SPI Firefox kiosk；HDMI 尚未接屏验证 |
| DRM 设备 | 原设备配置 | 当前 SPI card0、HDMI card1；换硬件需重新检查 |
| 跟踪 | 原生 C++ person ByteTrack | 保留，可选开启，默认关闭 |
| 深度单位 | 上游提供尺度系数 | 只显示相对近远，拒绝把归一化值标成米 |

X5 的检测保留官方 OpenCV letterbox（灰色 127）和分类 NMS；深度使用灰色 114 填充、exp 解码、还原 letterbox，再生成伪彩。libyuv 用于深度和显示缩放，检测预处理保持官方实现，避免缩放细节造成检测框差异。

两个模型的 CPU 前后处理可以与 BPU 执行交叠，但共用 X5 BPU 资源。不要把两个任务耗时相加后当作 BPU 使用率，也不要把 S100P 的吞吐直接套到 X5。升级到双 S 后算法更新约为检测 18fps、深度 15fps，摄像头画面仍可独立合成和编码到约 29.6fps。

出处：[原始案例](../references/README.md)。X5 数值来自 [实机验证摘要](validation.md)。

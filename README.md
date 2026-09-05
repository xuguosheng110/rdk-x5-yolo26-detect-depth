# RDK X5 · YOLO26 检测 + 单目深度 + SPI 展会演示

在 **RDK X5** 上并行运行 YOLO26 目标检测和单目深度估计，输出实时 Web 面板，并在 **480×320 SPI 屏**上全屏展示。支持开机自动登录、自动运行、屏幕常亮和进程异常恢复。

本项目移植自 [Max.Ma 的 RDK S100P 双模型演示](https://github.com/maxma615/yolo26-detect-depth-demo)，参考[地瓜机器人论坛案例](https://forum.d-robotics.cc/t/topic/35680)，模型与解码采用 [D-Robotics 官方 X5 Model Zoo](https://github.com/D-Robotics/rdk_model_zoo/tree/rdk_x5)。**仓库根目录是 X5 实现；[references/s100p](references/s100p) 是带原许可证的 S100P 原始源码快照。**

## 功能与验证结果

- YOLO26s 检测 + YOLO26s 深度为默认组合；可切换 nano（N/N）、balanced（S/N）。
- C++ `hbDNNInfer` / `libdnn`，X5 Bayes-e `.bin` 模型；不依赖 S100P 的 UCP 调度接口。
- USB 摄像头、两个推理工作线程、合成和编码分别执行；保留最新帧以减少排队。
- 检测框、深度伪彩、相对深度网格和 BPU/CPU 指标；ByteTrack 默认关闭，可选启用。
- Web 面板与 SPI kiosk 页面；已完成实机重启和两项进程退出恢复验证。

| X5 模型组合 | BPU 平均 | 检测更新 | 深度更新 | 视频编码 |
|---|---:|---:|---:|---:|
| N / N | 约 70% | 约 29.5fps | 约 19.5fps | 约 29.6fps |
| S / N | 约 82% | 约 22.3fps | 约 18.7fps | 约 29.6fps |
| S / S（默认） | 83.5% | 18.30fps | 14.55fps | 29.58fps |

S/S 测量窗口 64.2 秒，BPU P95 为 91%，偶有 100% 峰值。结果为该板卡、摄像头、散热和场景下的观测值。[指标摘要与测量方法](docs/validation.md)。

**视频编码/浏览器绘制帧率不等于 SPI 屏物理刷新率。** 当前 480×320 RGB565、40MHz SPI 的全帧传输理论上限为 **16.3fps**，实际含开销后更低。当前硬件不能达到物理全画面 30fps。深度网格显示相对近远，**不是米**；HDMI 路径可编译，但尚未接屏验收。

## 快速部署

已验证环境：RDK X5 V1.0、RDK OS 3.5.0 / Ubuntu 22.04、内核 6.1.83、DNN 1.24.5 / HBRT 3.15.55、Xfce + LightDM + Firefox。SPI 驱动和桌面须先配置好，详见 [SPI 前置条件](docs/spi-display.md)。默认桌面账户为 RDK 镜像的 `sunrise`，默认 USB 摄像头为 `/dev/video0`，支持 640×480 MJPEG。

在 X5 上执行（需要 root）：

```bash
sudo -i
apt-get update
apt-get install -y git
mkdir -p /app
git clone https://github.com/xuguosheng110/rdk-x5-yolo26-detect-depth.git /app/rdk-x5-vision
cd /app/rdk-x5-vision
bash scripts/install.sh
```

安装脚本安装构建依赖、下载并校验四个官方模型、编译、运行 3 项测试，然后配置推理服务与展会自启动。它会设置 `sunrise` 桌面自动登录和屏幕常亮；[安装内容、备份与维护方法](docs/exhibition.md)。安装脚本不安装 SPI 内核驱动，也不替换设备树。

- SPI 本机页面：`http://127.0.0.1:8080/?spi`
- 局域网面板：`http://<X5_IP>:8080/`
- 指标接口：`http://<X5_IP>:8080/stats.json`

展会展示使用本机页面，模型下载完成后无需外网。HTTP 接口是局域网演示服务，没有用户认证，不应直接暴露到公网。

## 运行与模型切换

```bash
cd /app/rdk-x5-vision
systemctl stop rdk-x5-vision
bash scripts/run.sh --preset quality        # S 检测 + S 深度
# Ctrl+C 后可尝试：
bash scripts/run.sh --preset balanced       # S 检测 + N 深度
bash scripts/run.sh --preset nano --track   # N/N + person ByteTrack
# 结束前台演示后恢复常驻服务：
systemctl start rdk-x5-vision
```

修改 [config/runtime.json](config/runtime.json) 的 `default_preset` 后，执行 `systemctl restart rdk-x5-vision` 即可改变服务默认组合。`scripts/install.sh` 安装的服务采用该预设。`--help` 可查看摄像头和显示参数。

摄像头默认暂时切换为手动 10ms 曝光，关闭动态降帧和防闪烁，以获得约 29.6 个独立相机帧/秒；正常退出、SIGINT 或 SIGTERM 时恢复原设置。该配置要求摄像头支持对应 V4L2 控件；其他摄像头可用 `--keep-camera-settings`，并自行验证曝光和帧率。冷启动、不同灯光条件可能影响检测效果。

## 结构与参考资料

```text
cpp/                  X5 C++ 推理、跟踪、绘制、指标和测试
scripts/              模型下载、构建、启动、展会自启动、测量与数值对照
config/               模型预设、systemd 服务和桌面启动项
web/                  Web 面板与 SPI kiosk 视图
vendor/rdk_model_zoo/  固定版本的官方 Python 对照实现
references/s100p/     S100P 原始案例源码快照（含原文档和 MIT 许可证）
docs/                 架构、平台差异、SPI、展会与验证说明
reports/              去除设备标识与原始场景信息后的验证摘要
```

- [参考方案索引与固定版本](references/README.md)
- [X5 / S100P 移植差异](docs/x5-vs-s100p.md)
- [数据流与帧率定义](docs/architecture.md)
- [SPI 屏前置条件](docs/spi-display.md)
- [展会部署、维护与恢复](docs/exhibition.md)
- [验证与复测](docs/validation.md)

## 来源与许可证

X5 应用派生自上游 MIT 项目，保留原作者声明；官方 Python 示例按 Apache-2.0 保留许可证。模型权重与可选测试图片由下载脚本从上游取得，不打包进 Git；其许可随各自上游。详见 [UPSTREAM.md](UPSTREAM.md)、[LICENSE](LICENSE) 和 [references/README.md](references/README.md)。

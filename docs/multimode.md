# GS130WI 三模式触屏与局域网演示

在同一块 RDK X5 上使用 GS130WI 双目模组，SPI 浏览器和局域网浏览器共享当前算法。点击底部按钮切换，自动清空旧画面并加载新结果；所有已打开的页面都会同步。不需要手动刷新页面。

| 按钮 | 输入与算法 | 数值含义 |
|---|---|---|
| 检测 + 单目深度 | 双目左路 → 原 C++ YOLO26s 检测、YOLO26s 深度 | 深度仅为相对近远，不能当作米 |
| 双目深度 | 校正后的左右目 → 官方 DStereo V2.4 int16 640×480 | 使用模组标定输出深度估计；需用已知距离验证 |
| 人体 + 年龄 | 左路 → 官方人体/人脸/头部/手部/关键点模型 → face_age_detection | 年龄是人脸外观估计，并非真实年龄核验 |

相机和图像桥接常驻，切换时只停止并启动选定的算法进程组，避免反复初始化 MIPI，也避免三套算法同时抢占 BPU。原 USB 演示仍可单独运行。

## 安装

前置条件：RDK OS 3.5.0、TROS Humble；已经配置好的 480×320 SPI 屏、Goodix 触摸、LightDM/Xfce、Firefox、sunrise 用户。SPI 驱动和设备树不是本脚本的安装范围，参见 [SPI 前置条件](spi-display.md)。

断电连接两条 FFC 排线。GS130WI 与 GS130W 的模组端触点方向不同，按 [官方 GS130WI 安装说明](https://developer.d-robotics.cc/accessories_stereo_camera_doc/stereo_camera_gs130wi/installation) 检查，不能只确认锁扣已扣紧。

在 X5 上以 root 执行：

```bash
apt-get update
apt-get install -y git python3-opencv python3-numpy \
  tros-humble-mipi-cam tros-humble-hobot-stereonet \
  tros-humble-mono2d-body-detection tros-humble-face-age-detection
# 首次安装；已有目录不要重复 clone，也不要覆盖自己的改动。
git clone https://github.com/xuguosheng110/rdk-x5-yolo26-detect-depth.git /app/rdk-x5-vision
cd /app/rdk-x5-vision
bash scripts/install.sh
bash scripts/setup_multimode.sh
reboot
```

已有 Git checkout 的用户，先保存自己的修改，再 `git pull --ff-only`、执行 `bash scripts/setup_multimode.sh` 并重启。若旧目录由压缩包部署、没有 `.git`，先备份旧目录和配置再部署新 checkout，模型目录可复用。不要对含有用户改动的目录强行 reset。

首次启动默认为 YOLO；后续记住上次选择的模式。模组初始化可能需要数十秒，页面会先出现等待提示。

- SPI：自动全屏打开 `http://127.0.0.1:8080/?spi`。
- 局域网电脑或手机：`http://<X5_IP>:8080/`。
- 状态：`/api/status`（`/stats.json` 为同一入口的兼容别名）。
- 当前画面：`/frame.jpg`。

这是无登录的局域网演示：同网段能够访问的人可以切换模式，不要端口转发到公网。控制接口只接受固定模式名的 JSON，拒绝跨站 Origin 请求；它不提供任意命令执行功能。

本机按实际接线显式配置左右通道：`mipi_channel:=0 mipi_channel2:=2`，即 CSI0 为左目、CSI2 为右目。其他设备应按自己的接线核对，不应把通道顺序当作模组通用默认值；交换通道也不能替代标定验收。

双目伪彩使用与官方 outdoor 同思路的自适应逆深度分位数映射，近红远蓝，避免默认 0–192 视差范围让室内画面几乎全蓝。色阶随场景变化，颜色不对应固定米数；深度数值与推理结果不因调色而更改。页面检测到 UI 版本变化会自动重载；本次已刷新此前一直打开旧脚本的电脑浏览器。

高清显示将原始左目 1280×1088 JPEG、640×480 深度伪彩和该深度帧的采样数值打包到 `/stereo.frame`，一次传输保持图文一致。浏览器在原图与深度图上独立绘制对应的距离框，电脑端保留 4×3 采样网格；SPI 减少数字数量。右侧深度图已按用户要求恢复此前的平滑缩放显示。左右配图按时间戳选择最近图像，差值超过 500ms 则不发布。兼容 `/frame.jpg` 仍提供双幅 JPEG，但电脑交互页面使用高清帧包。

`stereo.frame` 格式：前 8 字节为两个 little-endian uint32（JSON 字节数、原图 JPEG 字节数），之后依次为 UTF-8 JSON、原图 JPEG、深度 JPEG。元数据中的 `depth_width/height` 表示模型原生深度尺寸，不能将浏览器放大后的尺寸当作模型分辨率。

## 配置与维护

| 文件 / 服务 | 作用 |
|---|---|
| `config/rdk-x5-camera.service` | 常驻双目采集，15fps 请求，主路 1280×1088、子路 640×480、GDC 校正、LPWM 同步、实时戳 |
| `config/rdk-x5-bridge.service` | 常驻左目订阅与结果叠加，切换不重建采集订阅 |
| `config/rdk-x5-mode.service` | 选定的 ROS / C++ 算法进程组；退出后自动重启 |
| `config/rdk-x5-portal.service` | 8080 网页与切换控制；不随算法切换退出 |
| `config/selected-mode.env` | 安装后生成，保存上次模式，不提交到 Git |
| `scripts/mode_pipeline.launch.py` | 三个模式的模型与 ROS 参数 |
| `scripts/ros_bridge.py` | NV12 → 左目 JPEG、人体模型输入、结果叠加、显示帧 |
| `scripts/mode_server.py` / `web/modes.html` | 串行切换、就绪状态、自动重连、触屏布局 |

```bash
systemctl status rdk-x5-camera rdk-x5-bridge rdk-x5-mode rdk-x5-portal
journalctl -u rdk-x5-camera -u rdk-x5-mode -n 80 --no-pager
curl http://127.0.0.1:8080/api/status
curl -H 'Content-Type: application/json' \
  -d '{"mode":"stereo"}' http://127.0.0.1:8080/api/mode
# 维护：停止算法，不反复关闭相机
systemctl stop rdk-x5-mode
systemctl start rdk-x5-mode
```

模式值为 `yolo`、`stereo`、`body`。并发切换返回 HTTP 409，页面切换期间禁用按钮。先终止旧进程组，再更换模式、清除临时帧并启动新进程组。图像只在 `/run/rdk-vision` 保留最新帧；不保存持续录像。

原 USB 演示恢复方式（需要 USB 摄像头）：

```bash
systemctl disable --now rdk-x5-mode rdk-x5-bridge rdk-x5-portal rdk-x5-camera
systemctl enable --now rdk-x5-vision
```

## 关键适配点与故障排查

1. **传感器未识别**：先看相机日志中的 CSI 与芯片 ID。本机验证到 CSI0/I²C6/0x30 和 CSI2/I²C4/0x32，SC132GS ID 为 0x0132。两个地址都无响应时优先断电核对排线方向、插入深度与供电；不要先更换算法。地址是本次模组实测，不是所有模组的固定地址。
2. **标定与旋转**：本次 UNION EEPROM 模组使用 `mipi_rotation:=0.0` 的校正图；盲目设为 90° 会让投影矩阵的 fx/fy 为零，StereoNet 无法正确计算水平视差深度。不同模组应检查自己的 CameraInfo，不能套用另一模组的标定。`calib_params.yaml` 不存在不必然意味着无标定，模组 EEPROM 可提供标定。
3. **相机退出占用 MIPI**：本次调试中遇到采集进程退出时卡在内核 I²C 调用，重新启动会提示无可用 host。清理后重启设备恢复；本方案让相机和图像桥接常驻，正常算法切换不触碰相机进程。
4. **人体 NV12 缩放崩溃**：直接发布 960×544 NV12，绕过此版本官方人体节点的缩放路径。左右补边保持左目画面比例，结果与年龄模型使用同一时间戳。显示时去除补边。
5. **systemd 与 ROS 日志目录**：服务显式设置 `ROS_LOG_DIR`，避免非交互环境下 `rcutils_expand_user failed`。
6. **年龄不显示**：正脸太小、遮挡、倾斜或没有检测到人脸时可能没有年龄结果。空年龄列表不是固定年龄。UI 仅渲染模型实际返回的 `age` 属性。

7. **人体结果完整性**：以 `/hobot_mono2d_body_detection` 为主保留人体、人脸、头部、手部框和关键点；按照 `track_id` 合并官方年龄节点结果。年龄节点单独输出只包含人脸，不能用它代替完整人体消息。当前安装的官方人体和年龄模型未输出性别，页面不会生成虚构性别标签。
8. **CPU 和磁盘开销**：图像消息使用 `array.array('B')`，避免 Python 逐字节检查 NV12；关闭 StereoNet 的 `save_result_flag`，避免默认逐帧写入结果。OpenCV 使用一个线程。网页双目和 YOLO 使用左右排布，随窗口等比例放大；人体画面保持完整视野，不拉伸人物。
9. **切换后相机不出图**：此前随算法退出图像订阅时复现停帧，相机服务重启可恢复。当前图像桥接改为独立常驻服务，维持左目订阅；若遇到新的硬件采集异常，检查 `camera.json` 时间戳及相机日志，必要时 `systemctl restart rdk-x5-camera`，而不是刷新网页。

10. **StereoNet 内参重复缩放**：当前包接收大图的 CameraInfo 后先按模型尺寸缩放内参，图像 resize 路径又缩放一次。启用 640×480 子码流并同时指定对应左右 CameraInfo，绕开这条路径。不要只改变图像话题而沿用主码流内参。
11. **距离精度待验收**：本次场景的左右目特征匹配仍有明显垂直偏差；修正重复缩放不等于完成模组标定。页面明确标注距离暂不作测量依据。需固定相机、检查左右路与标定对应关系，并用标定板和已知距离重新验收，不能凭深度伪彩出图判定测距准确。

## 验收与边界

板端 C++ 构建和 CTest 3/3 通过。三模式真实相机出图、人脸年龄标签、浏览器按钮切换与 SPI 480×320 页面已验证。复测脚本检查六次切换、新帧增长、人体结果消息、YOLO 两项模型计数、无效模式和跨站请求：

```bash
python3 tests/verify_modes.py --url http://127.0.0.1:8080
```

脚本会实际切换正在展示的算法，最终停在 YOLO 模式。自动化结果见 [三模式验收记录](../reports/multimode-validation.md)。

原 USB 方案的约 30fps 测量不能用于本次 MIPI → ROS → JPEG 桥接方案，也不是 SPI 物理刷新率。当前优先实现可靠切换和复现；桥接与浏览器轮询存在额外开销。深度绝对精度、年龄准确率和不同模组兼容性没有完成标定测量或数据集评估。

官方参考：[双目采集](https://developer.d-robotics.cc/accessories_stereo_camera_doc/stereo_camera_gs130wi/quick_start)、[StereoNet](https://developer.d-robotics.cc/tros_doc/boxs/spatial/hobot_stereonet?v=3.5.0&p=RDK+X5)、[人体检测](https://github.com/D-Robotics/mono2d_body_detection)、[年龄模型](https://github.com/D-Robotics/face_age_detection)。模型由官方 TROS 包提供，不打包到本仓库。

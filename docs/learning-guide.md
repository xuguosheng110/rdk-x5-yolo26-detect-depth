# 学习与使用路线

建议按“先运行 → 看启动入口 → 跟一帧图像 → 看展示 → 修改一个小功能”的顺序学习。先打开 [整体代码架构图](architecture.md)，把本页与源码放在两个浏览器标签页中对照。

## 1. 先分清三个目录

| 目录 | 应如何使用 |
|---|---|
| 仓库根目录 | X5 应用，部署和运行都从这里开始 |
| `references/s100p/` | S100P 原始案例，适合比较设计和平台 API |
| `vendor/rdk_model_zoo/` | 官方 Python 推理对照实现，供验证前后处理 |

本项目的实时服务是 **C++ 推理**；Python 只做启动管理，浏览器只做展示。不要从 `vendor/` 的 Python 模型类开始寻找当前实时服务入口。

## 2. 建议阅读顺序

| 顺序 | 文件或符号 | 读完应能回答 |
|---|---|---|
| 1 | [README](../README.md)、[runtime.json](../config/runtime.json) | 用什么板子、模型、输入和显示方式？ |
| 2 | [run.sh](../scripts/run.sh)、[run.py](../scripts/run.py) | 预设怎样变成 C++ 参数？为什么要保存摄像头控件和加进程锁？ |
| 3 | [main()](../cpp/src/main.cpp#L1538)、[Args](../cpp/src/main.cpp#L1448) | 模型怎样加载？视频模式和单图模式在哪里分开？ |
| 4 | [FrameHub](../cpp/src/main.cpp#L618)、[工作线程](../cpp/src/main.cpp#L1762) | 一帧图像怎样交给两个模型？慢线程怎样跳过旧帧？ |
| 5 | [DnnModel](../cpp/src/main.cpp#L112) | CPU 与 BPU 共享内存怎样分配和刷新缓存？ |
| 6 | [DetectModel](../cpp/src/main.cpp#L315)、[DepthModel](../cpp/src/main.cpp#L408) | 输入怎么缩放补边？输出怎么还原成框或颜色？ |
| 7 | [合成与编码](../cpp/src/main.cpp#L1859)、[HttpServer](../cpp/src/main.cpp#L1255) | 带标注的图片怎样变成浏览器视频？ |
| 8 | [web/index.html](../web/index.html) | SPI 如何变成左右双画面？指标怎样更新？ |
| 9 | [展会配置](exhibition.md)、[跟踪实现](../cpp/src/tracking/byte_tracker.cpp) | 如何自动启动？需要轨迹 ID 时怎样扩展？ |

读 `main.cpp` 时优先用编辑器“跳转符号”或搜索类名。命令行也可以：

```bash
rg -n 'class DnnModel|class DetectModel|class DepthModel|class FrameHub|int main' cpp/src/main.cpp
rg -n 'det_worker|dep_worker|composer|encoder|build_stats' cpp/src/main.cpp
```

## 3. 先做一次只读检查

下面命令在 X5 上执行。项目运行目录是 `/app/rdk-x5-vision`，它和 GitHub 仓库名不同。

```bash
cd /app/rdk-x5-vision
systemctl status rdk-x5-vision --no-pager
curl -fsS http://127.0.0.1:8080/stats.json | python3 -m json.tool
# 输出最新合成图到本地文件
mkdir -p output
curl -fsS http://127.0.0.1:8080/snapshot.jpg -o output/snapshot.jpg
```

先在 JSON 中找 `models`、`capture.frames`、`detect.frames`、`depth.frames`、`encoded_frames` 和 `bpu.util_pct`。这些字段能确认实际加载的模型和每个阶段是否在前进。

浏览器打开 `http://<X5_IP>:8080/` 看完整面板；SPI 本机显示使用 `http://127.0.0.1:8080/?spi`。

## 4. 用前台运行理解参数

下面操作会暂时中断展会画面。先停止系统服务，避免同时占用摄像头和输出锁；浏览器可以保持打开，服务恢复后会自动重连。

```bash
cd /app/rdk-x5-vision
systemctl stop rdk-x5-vision
bash scripts/run.sh --help
# 限时 20 秒，便于观察日志和退出流程
bash scripts/run.sh --preset nano --max-seconds 20
# 对比默认双 S
bash scripts/run.sh --preset quality --max-seconds 20
# 学习完成后恢复展会服务
systemctl start rdk-x5-vision
```

应能看到：模型加载与张量形状、摄像头配置、detect/depth ready、HTTP 地址和结束时的统计。20 秒用于了解流程，严谨性能对比应使用稳定窗口，并保持场景、散热和客户端数量尽量一致。

`--preset` 由 Python 启动器处理并展开成两个模型路径；它不是 C++ `ParseArgs()` 的参数。`--max-seconds`、`--score` 等参数则会继续传给 C++。

## 5. 常用参数与修改位置

| 想实现的变化 | 优先修改/使用 | 需要理解的影响 |
|---|---|---|
| 在 N/N、S/N、S/S 间切换 | `--preset` 或 `config/runtime.json` | 模型越大不一定还能保持算法逐帧更新 |
| 换摄像头 | `--source /dev/video2` 等 | 先用 V4L2 枚举实际采集节点，不能仅凭编号猜设备 |
| 设相机尺寸与标称帧率 | `--cam-w`、`--cam-h`、`--cam-fps` | 相机必须支持对应模式；标称帧率不等于实际出帧 |
| 保留摄像头曝光策略 | `--keep-camera-settings` | 默认手动控件不兼容时可用；帧率和亮度需要复测 |
| 减少低置信框 | `--score 0.4` | 提高显示阈值可能减少误检，也可能漏掉目标 |
| 调整同类重叠框抑制 | `--nms 0.45` | 改的是 IoU 抑制阈值，不是置信度 |
| 显示 person 轨迹 ID | `--track` | 当前跟踪输入只筛选 person，不是所有类别 |
| 调整深度网格 | `--grid-cols 4 --grid-rows 3`，或 `--no-grid` | 网格交点数量为 `(cols+1)×(rows+1)` |
| 改 SPI 标题、字体、左右布局 | `web/index.html` 的 `spiMode` / canvas 分支 | 改 `.spi-mode` CSS 不能替代对 canvas 内文字与坐标的修改 |
| 改检测框与 HUD | C++ `DrawYoloBox()`、`DrawHud()` 或 `browser_overlay.cpp` | 这些文字和框已经画进 JPEG，需要重新编译 |
| 改完整面板卡片 | `web/index.html` 的 HTML/CSS、`renderStats()` | HTML 每次页面请求重新读取，刷新浏览器即可加载 |
| 新增一项统计数据 | C++ `build_stats()` + 前端 `renderStats()` | 后端提供数据，前端决定如何展示 |
| 换另一种模型 | `DnnModel`、`DetectModel` / `DepthModel` | 必须重新核对平台、shape、量化和前后处理；改标签文件不能改变模型类别数 |
| 改启动账号或屏幕环境 | systemd unit、`setup_exhibition.sh`、`kiosk_session.sh` | 当前绑定 sunrise / UID 1000 / DISPLAY :0 |

**学习练习建议：**先临时改置信度阈值，再改 SPI 标题，最后尝试新增指标。这样能依次理解“命令行 → 模型结果”“前端绘制”“前后端数据接口”，无需一开始修改 BPU 内存代码。

## 6. 让参数在服务中长期生效

标准安装方式采用 `config/runtime.json` 的默认组合。修改该文件后重启推理服务即可。若板子上曾装过显式指定模型的 systemd 覆盖配置，应先查看最终生效的启动命令：

```bash
systemctl cat rdk-x5-vision
```

例如，要把常驻服务改成 balanced 并显示置信度大于 0.35 的框，可执行 `systemctl edit rdk-x5-vision`，填写：

```ini
[Service]
ExecStart=
ExecStart=/usr/bin/python3 -u /app/rdk-x5-vision/scripts/run.py --preset balanced --score 0.35
```

然后：

```bash
systemctl daemon-reload
systemctl restart rdk-x5-vision
curl -fsS http://127.0.0.1:8080/stats.json | python3 -m json.tool
```

空的 `ExecStart=` 用来清除旧命令，下一行指定新命令。仍应查看 `systemctl cat` 确认不存在排序更晚的覆盖文件替换你的设置。覆盖命令中若显式写了 `--preset` 或模型路径，后续仅修改 JSON 默认预设不会覆盖它。

## 7. 编译、验证和恢复展示

修改 C++ 后在板端编译：

```bash
cd /app/rdk-x5-vision
systemctl stop rdk-x5-vision
bash scripts/build.sh
# 构建及测试通过后再启动
systemctl start rdk-x5-vision
```

`build.sh` 会执行 CMake Release 构建和 CTest。ByteTrack、绘制、系统指标的 3 项测试不能替代模型数值对照与实际摄像头验证；修改预处理、解码或模型时，继续按 [验证说明](validation.md) 做单图官方实现对照和实时测试。

只改 Web 文件时，部署文件后刷新浏览器，无需重新编译 C++。展会 kiosk 可通过重启用户服务重新加载页面：

```bash
runuser -u sunrise -- env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus systemctl --user restart rdk-x5-kiosk
```

## 8. 如何读性能数字

| 指标 | 实际含义 | 不应混同的指标 |
|---|---|---|
| `capture.frames` | 已发布的相机帧数 | 摄像头宣称支持的 fps |
| `detect.frames` / `depth.frames` | 对应模型完成的处理次数 | 视频编码帧数 |
| `composed_frames` | 合成完成数 | 两个模型同步完成的次数 |
| `encoded_frames` | JPEG 编码完成数 | 客户端实际画出的帧数 |
| 浏览器 FPS | 解码、绘制的不同源帧速度 | SPI 面板物理刷新率 |
| `bpu.util_pct` | sysfs 的硬件使用率 | 两模型 `bpu_ms` 相加后的估计值 |
| `detect/depth.age_ms` | 结果源帧发布到读取指标时的年龄 | 纯推理耗时、严格端到端显示延迟 |

后端 `capture.fps`、`detect.fps`、`depth.fps` 由累计帧数和运行时长计算，刚启动时受预热影响；要看近期稳定速度，应比较两个时间点的帧计数差，或运行测量脚本。`display_fps` 则由合成线程约每秒更新，仍不是物理屏幕刷新率。

已有 S/S 实测约为视频 29.6fps、检测 18.3fps、深度 14.5fps、BPU 平均 84%。这意味着视频可以连续展示，但并非每一视频帧都跑完两项推理。40MHz SPI 的物理全帧传输理论上限约 16.3fps，不能用软件计数消除该带宽限制。

## 9. 常见问题怎么定位

| 现象 | 先看哪里 | 下一步 |
|---|---|---|
| 推理服务反复重启 | `journalctl -u rdk-x5-vision -n 60` | 核对模型是否下载、V4L2 控件是否支持、摄像头是否被占用 |
| 网页面板能打开但画面不动 | 连续读取 `/stats.json` 比较帧计数 | 相机计数不动查采集；相机前进而编码不动查合成/编码日志 |
| 算法框滞后，视频仍流畅 | `detect/depth.age_ms`、两项推理次数 | 对比 nano/balanced，检查 CPU 前后处理、BPU 占用和散热 |
| 局域网面板正常，SPI 没显示 | 用户服务 `rdk-x5-kiosk`、X11、桌面登录 | 检查 DISPLAY、XAUTHORITY、屏幕驱动；推理与显示分开定位 |
| 修改 JSON 后模型没变化 | `systemctl cat rdk-x5-vision` 和 `/stats.json` 的 `models` | 排查命令行模型路径或预设覆盖 |
| 关掉窗口后又出现 | kiosk 的 `Restart=always` | 维护时用用户服务的 `stop`，不要只关闭窗口 |
| 大量 Unknown arg 错误 | `run.py --help`、C++ `ParseArgs()` | 区分 Python 预设参数和 C++ 参数，检查拼写 |

完整展会操作见 [exhibition.md](exhibition.md)，更底层的平台差异见 [x5-vs-s100p.md](x5-vs-s100p.md)。

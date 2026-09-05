# SPI 屏前置条件

本项目在已完成驱动适配的 Waveshare 3.5 英寸 ST7796S SPI 屏上验证，480×320、RGB565、40MHz。它不包含可通用于任意 X5 内核和屏幕的驱动安装包。

准备好 SPI 驱动、设备树、面板固件、背光和 X11 桌面后，再运行应用安装脚本。当前测试配置为 `panel-mipi-dbi` 驱动，SPI 位于 DRM card0，HDMI 位于 card1。应根据实际硬件检查，不要盲目覆盖系统配置。

```bash
cat /sys/class/graphics/fb0/name
cat /sys/class/drm/card0-SPI-1/status
ls /dev/dri/
DISPLAY=:0 XAUTHORITY=/home/sunrise/.Xauthority xrandr
```

已验证 X11 使用 `modesetting` 指向 `/dev/dri/card0`；桌面为 480×320，Firefox 以 kiosk 模式全屏。安装脚本依赖现有 Firefox、LightDM、Xfce 和 sunrise 用户，当前目标为 RDK OS 3.5.0。

带宽上限：`40,000,000 / (480 × 320 × 16) = 16.28 fps`。命令传输、DMA 和驱动开销会继续降低物理全帧刷新率。X11 截图与浏览器 canvas 指标不能证明面板达到 30fps。

更高分辨率或更高刷新展示可另行验证 HDMI；当前仓库仅记录 SPI 已验证路径。主项目的 HDMI 代码可编译，尚无接屏验收结果。

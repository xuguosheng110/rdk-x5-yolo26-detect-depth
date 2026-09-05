# 展会自启动与维护

完成 `scripts/install.sh` 后，接好摄像头与 SPI 屏，通电即可自动登录桌面并打开双模型全屏展示。应用资源和页面位于板内，正常展示无需外网。模型首次下载、软件安装需要网络。

## 启动顺序

1. 系统启动 `rdk-x5-vision.service`，加载当前模型预设。摄像头尚未就绪或进程退出时，systemd 持续重试，间隔 3 秒。
2. LightDM 自动登录 sunrise / Xfce。
3. 桌面启动项执行 `spi_display.sh`，启动用户级 `rdk-x5-kiosk.service`。
4. 浏览器启动脚本等待 X11 和本机 `/stats.json`，设置屏幕常亮，再使用独立 Firefox 配置以 `--kiosk` 打开 `http://127.0.0.1:8080/?spi`。
5. 浏览器退出后自动重启；页面断流则自动重新连接 MJPEG。

已有推理环境只需安装自启动：

```bash
bash /app/rdk-x5-vision/scripts/setup_exhibition.sh
```

脚本要求工程路径 `/app/rdk-x5-vision`，用户名 `sunrise`，UID 1000，X11 DISPLAY `:0`。其他系统需要先适配脚本和 unit 中对应值。

## 配置文件

| 路径 | 用途 |
|---|---|
| /etc/lightdm/lightdm.conf.d/90-rdk-x5-exhibition.conf | 自动登录 sunrise |
| /etc/systemd/system/rdk-x5-vision.service | 推理开机启动与重启 |
| /home/sunrise/.config/autostart/rdk-x5-vision.desktop | 登录后启动浏览器服务 |
| /home/sunrise/.config/systemd/user/rdk-x5-kiosk.service | 全屏浏览器进程托管 |
| /home/sunrise/.config/autostart/xscreensaver.desktop | 禁用屏保启动项 |
| /home/sunrise/.local/share/rdk-x5-vision/firefox | 展会专用 Firefox 配置 |

同名配置安装前备份到 `output/exhibition-backup-*`；屏幕常亮还会设置 Xfce 电源管理属性和 X11 DPMS。初次安装后的真实重启验收须在所部署设备上自行进行。

## 维护命令（SSH / root）

```bash
systemctl status rdk-x5-vision
journalctl -b -u rdk-x5-vision -n 50
systemctl restart rdk-x5-vision

# 暂时退出全屏；只关闭窗口会被自动拉起
runuser -u sunrise -- env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus systemctl --user stop rdk-x5-kiosk
# 再次打开
runuser -u sunrise -- /app/rdk-x5-vision/scripts/spi_display.sh
```

## 关闭与恢复开机展示（SSH / root）

关闭后立即停止展示，后续重启也不会自动运行推理或打开全屏浏览器：

```bash
# 取消登录后启动浏览器；.disabled 后缀不会被桌面作为启动项加载
mv /home/sunrise/.config/autostart/rdk-x5-vision.desktop \
   /home/sunrise/.config/autostart/rdk-x5-vision.desktop.disabled
runuser -u sunrise -- env XDG_RUNTIME_DIR=/run/user/1000 \
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
  systemctl --user stop rdk-x5-kiosk.service
systemctl disable --now rdk-x5-vision.service
```

恢复开机展示并立即打开：

```bash
mv /home/sunrise/.config/autostart/rdk-x5-vision.desktop.disabled \
   /home/sunrise/.config/autostart/rdk-x5-vision.desktop
systemctl enable --now rdk-x5-vision.service
runuser -u sunrise -- /app/rdk-x5-vision/scripts/spi_display.sh
```

用户级 kiosk 服务由桌面启动项直接启动，因此仅执行 `systemctl --user disable` 不会关闭登录后全屏。只关闭 Firefox 窗口也会被服务自动拉起。

以上操作保留桌面自动登录和屏幕常亮设置。如果还要恢复普通桌面策略，可从 `output/exhibition-backup-*` 恢复原配置（有备份时），移除本项目新增的 `/etc/lightdm/lightdm.conf.d/90-rdk-x5-exhibition.conf` 覆盖项，并在 Xfce 电源设置中重新开启需要的节能选项。

## 温度监控

网页 CPU/BPU 资源区与 SPI 屏底部显示 CPU、DDR 温度（°C）。后端按 `/sys/class/thermal/thermal_zone*/type` 识别 `thermal-cpu` 和 `thermal-ddr`，将 `temp` 的毫摄氏度换算为摄氏度，不依赖 zone 编号。当前板子没有独立 BPU 温度接口，不能把 DDR 温度标成 BPU 温度。

`/stats.json` 提供 `thermal.cpu_c`、`thermal.ddr_c`、`thermal.bpu_c`；不可用时为 `null`，界面显示 `—`。网页连续三次获取状态失败也会清除温度显示。

本次实机已验证：重启自动全屏；浏览器 SIGKILL 后约 16.2 秒恢复全屏；推理主进程 SIGTERM 后约 10.4 秒恢复并已采集超过 60 帧。恢复时间包括进程启动与模型/浏览器初始化，不只是配置中的 3 秒重试间隔。[验收摘要](../reports/exhibition_summary.json)。

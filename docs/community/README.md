# 社区文章与架构配图

已发布到地瓜机器人论坛：[YOLO26 检测 + 单目深度：代码架构、SPI 全屏与展会自启动](https://forum.d-robotics.cc/t/topic/35691)。作者 `guosheng_xu`，分类“应用开发”，标签“RDK X5 / 分享帖”。

- [文章 Markdown](forum-post.md)：保留本地图片引用，方便在 GitHub 阅读和维护。
- [整体架构 PNG](images/x5-architecture.png)
- [单帧处理 PNG](images/x5-frame-pipeline.png)
- [展会启动 PNG](images/x5-exhibition-boot.png)
- [发布记录](publication.json)

论坛使用独立上传的图片，正文内容与这里的文章一致（省略重复标题并替换图片地址）。配图由 [render_community_diagrams.py](../../scripts/render_community_diagrams.py) 生成，需要 Pillow 和 Noto Sans CJK 字体。运行方式：

```bash
python3 scripts/render_community_diagrams.py
```

图中描述的是当前 X5 方案；S100P 原始源码和许可位于 `references/s100p/`。图片可点击放大查看。

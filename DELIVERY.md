# 四季像素短片 V2 · 成片交付
成片母版已完成并通过独立复验。以下为两处发布应使用的**同一份完整 MP4**；仓库不存放成片二进制。

| 项目 | 参数 |
| --- | --- |
| 文件名 | `Rainroji_Lofi_V2_1080p.mp4` |
| 文件大小 | 151,159,718 字节 |
| SHA‑256 | `0213513d08d439c965ef7320b2d896814733fac404d2dc6ddfeac4c122da60ba` |
| 视频 | 1920×1080 · 30 fps · 5,917 帧 · H.264 High / CRF 14 / yuv420p / BT.709 / faststart |
| 时长与码率 | 197.233333 秒 · 容器约 6.131 Mb/s · 视频约 5.865 Mb/s |
| 音频 | AAC-LC · 48 kHz 立体声 · 256 kb/s（目标） |
| 实测音频 | −16.04 LUFS-I · −4.74 dBTP · LRA 8.1 LU |

## 发布渠道
- **GitHub Release**：待上传同一原片并完成核验。
- **Google Drive**：待上传同一原片并完成核验。

## 从仓库重建完整原件

在 [锁定的工具链](tools/gate3/README.md)上运行 `python tools/gate3/reproduce.py`，不配置任何项目路径。产物 `dist/Rainroji_Lofi_V2_1080p.mp4` 已从干净快照独立跑通，SHA-256 与上表逐字节一致；[实跑报告](previews/gate_3/reproduction_qa.json)中记录了每一步校验。双渠道的当前报错详见 [制作进度](DEV_STATUS.md)。

## 审看
[三处转场实解码抽帧](previews/gate_3/encoded_transition_storyboard.jpg) · [独立复验报告](previews/gate_3/QA.md) · [完整署名](CREDITS.md)

原生 320×180 帧做叠化再 6× 最近邻放大，视频仅编码一次。三处叠化以 48 / 96 / 144 秒为中心，各持续 2 秒。配乐《Green Tea》完整保留；春风、夏雨、秋叶、冬窗声底约低 15.02 LU。最终 MP4 与两条母轨的压缩数据逐包相同。

发布后以下载所得文件或服务端的 SHA‑256 校验字段对照上表，并实测链接可访问。

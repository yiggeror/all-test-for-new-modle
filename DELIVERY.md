# 四季像素短片 V2.1 · 成片交付（最新终审签收）

**v2.1 动效升级版成片**已完成全流程审片、云端确定性重建、1× 实片抽段实看实听终审，并以**逐字节完全一致的同一份单个 1080p MP4 文件**完成 **GitHub Release** 与 **Google Drive** 双渠道发布（仓库不存放超限二进制文件）。

---

## 最新推荐版本：v2.1（动效可见度升级 + 丰富小动物 + 夏夜“网吧”闪烁回归）

### 双渠道正式链接（两处逐字节完全一致）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.1-rainroji-lofi-1080p>
- **GitHub Release 单文件直链**：<https://github.com/yiggeror/all-test-for-new-modle/releases/download/v2.1-rainroji-lofi-1080p/Rainroji_Lofi_V2.1_1080p.mp4>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1DIg66GW6FHtitbUyHgslwJta29awbtD-/view?usp=drivesdk>（File ID：`1DIg66GW6FHtitbUyHgslwJta29awbtD-`）

### v2.1 已发布成品实测参数

| 项目 | 参数 |
| --- | --- |
| 文件名 | `Rainroji_Lofi_V2.1_1080p.mp4` |
| 文件大小 | `153,200,285` 字节（146.10 MB，GitHub Release 与 Google Drive 完全一致） |
| SHA-256 | `62ceff09d8cd365f80f74686ae385f7aec6a138da27e2a428402483a23cc098b` |
| MD5 | `7715a8d21383bd1f2b4538eafca37c23` |
| 视频 | `1920×1080`（由 `320×180` 原生像素画经 `6×` 最近邻无损整数放大）· 30 fps · 5,917 帧 · H.264 High / CRF 14 / yuv420p / BT.709 / faststart |
| 时长与码率 | 197.233333 秒（3 分 17.23 秒）· 容器约 6.21 Mb/s · 视频约 5.95 Mb/s |
| 音频 | 无损流拷贝沿用 v2.0 全部 9,247 个 AAC-LC 包（48 kHz 立体声 · 256 kb/s） |
| 实测响度 | −16.04 LUFS-I · −4.77 dBTP · LRA 8.1 LU（零削波） |
| 发布构建流水线 | GitHub Actions `Publish Rainroji Lo-Fi V2.1 1080p Release`（Run `#45326160983`，Ubuntu 24.04 + FFmpeg 6.1.1 + Python 3.12） |

### v2.1 相对 v2.0 核心升级一览
- **春**：门楼睡猫明显抬头环顾并两次扫尾再伏下；自行车车把新增蹦跳轻啄的暖棕小麻雀；主路灯四只暖金小蛾绕飞更清晰。
- **夏**：恢复原版 Rainroji 经典 **“网吧”红霓虹电流闪烁**（6.40–7.80 秒四次骤暗至 21%～24%），灯字、邻侧砖墙红光溢出与右下湿地红色碎光 100% 同帧联动；棚内暖光货架前避雨花猫新增清晰抬爪洗脸与摆尾，檐滴涟漪与理发转灯同步加强。
- **秋**：左侧落叶道新增 **3 只错拍蹦跳、低头啄食、扑翅回位的觅食小鸟/鸽子**；报刊亭暗底暖白热汽加高至约 22 px 清晰袅袅上卷；上方粉紫暮空 4 只归鸟扇翅滑翔清晰优雅，另有金叶贴地滑过斑马线。
- **冬**：右下前景新增 **暖胸小肥鸟从雪人帽顶歪头抖雪 → 短飞落到石凳 → 蹦跳飞回雪人帽顶**；值班室暖窗原时码翻页书页反光更清楚，屋顶小烟囱淡烟连贯，远楼四层声控灯温柔错拍。

---

## 历史归档版本：v2.0（初版终审签收）

- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.0-rainroji-lofi-1080p>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1pQLUQez4nAWbnoMQ7wYO3ojIl7b1zhEO/view?usp=drivesdk>
- **文件名 / 大小 / SHA-256**：`Rainroji_Lofi_V2_1080p.mp4` / `151,157,219` 字节 / `2987f1b6b85cc9fe2ecc165315b3cc8fef6dc3c9eae4b3efdd2101f67569fe5b`

---

## 从仓库一键重建与核查文档

- v2.1 重建：`python tools/gate3_v21/reproduce.py`（说明见 [tools/gate3_v21/README.md](tools/gate3_v21/README.md)）
- v2.1 实解码抽帧与独立复验：[三处转场抽帧](previews/gate_3_1/encoded_transition_storyboard.jpg) · [独立复验报告](previews/gate_3_1/QA.md) · [完整音乐署名（CC BY 4.0）](CREDITS.md) · [全流程审片记录](REVIEW_LOG.md)

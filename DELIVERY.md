# 四季像素短片 · 成片交付（v2.4 精细打磨进行中）

> **当前状态（2026-11-24 Round 15）**：在 v2.3 干净基线之上已启动 **v2.4（Gate 2.4）精准微调**（锁定夏景不动；春/秋/冬恢复 ±1px 干脆像素级叶颤与细枝轻摇；补足春树左右两侧落花与秋树落叶；春季院落新增严格 1:1 比例循环生物动态，详见 [`REVIEW_LOG.md`](REVIEW_LOG.md) Round 15）。以下 v2.3 链接为当前最新已发布成片，待 v2.4 终审通过后将以 `v2.4-rainroji-lofi-1080p` 正式更新。

---

## 当前已发布最新版本：v2.3（v2.4 制作中）

### 双渠道正式链接（两处逐字节完全一致）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.3-rainroji-lofi-1080p>
- **GitHub Release 单文件直链**：<https://github.com/yiggeror/all-test-for-new-modle/releases/download/v2.3-rainroji-lofi-1080p/Rainroji_Lofi_V2.3_1080p.mp4>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1OHGVCFF3U3X4Y-5tgJif8t7-Fo4H99rr/view?usp=drivesdk>（File ID：`1OHGVCFF3U3X4Y-5tgJif8t7-Fo4H99rr`）

### v2.3 已发布成品实测参数

| 项目 | 参数 |
| --- | --- |
| 文件名 | `Rainroji_Lofi_V2.3_1080p.mp4` |
| 文件大小 | `124,559,510` 字节（118.79 MiB，GitHub Release 与 Google Drive 完全一致） |
| SHA-256 | `e33bc5e738ed472fabdcb8ba1837779087c7c8f3e3c2a28882b8d4604453dee8` |
| MD5 | `b2bb6620cc77b9e7f29aa5b7dd6fee65` |
| 视频 | `1920×1080`（由 `320×180` 原生像素画经 `6×` 最近邻无损整数放大）· 30 fps · `5,917` 帧 · H.264 High / CRF 14 / yuv420p / BT.709 / faststart |
| 时长与码率 | 197.233333 秒（3 分 17.23 秒）· 容器约 5.05 Mb/s · 视频约 4.79 Mb/s |
| 音频 | 无损流拷贝沿用 v2.0 全部 9,247 个 AAC-LC 包（48 kHz 立体声 · 257.5 kb/s） |
| 实测响度 | −16.0 LUFS-I · −4.7 dBFS True Peak · LRA 8.3 LU（零削波） |
| 发布构建流水线 | GitHub Actions `Publish Rainroji Lo-Fi V2.3 1080p Release`（Run `#45403465994`，Ubuntu 24.04 + FFmpeg 6.1.1 + Python 3.12） |

### v2.3 相对 v2.2 核心修复与质变
- **春 · 老巷暮色**：彻底清除整树/树干正弦波浪形变，树干与樱花主冠全 330 帧 100% 像素锁定稳固（零果冻感）；右下院内米白/浅灰蓝素布与暖砖墙清晰分离，采用 5 帧一换（6 fps）离散像素步进摆动；暖路灯光锥内落花呈现平静 → 阵风斜穿 → 平静的呼吸节奏。
- **夏 · 雨夜街角**：取消 31 帧抽帧插值，升级为 330 帧逐帧真实双车灯传输（零重影）；暖琥珀光斑柔和轻掠湿路（51.133s）与红车车身（52.100s），不再把右下有机红水洼冲糊发白；“网吧”红霓虹 4 次硬切瞬暗（53.4–54.8s）+ 邻墙红光 + 湿沥青碎红倒影 100% 同帧联动；左灯雨丝与檐滴更锐利克制。
- **秋 · 梧桐黄昏**：彻底删除 `map_coordinates` 2D 液化扭曲，双侧梧桐树冠与树干 100% 像素锁定锐利；清除报刊亭脏暗糊块与雾中红渍；聚焦稳固树影下的分层落叶、5 帧姿态保持的贴地翻滚金叶、暗底柔和茶汽与紫暮空隙 3 只可读剪影归鸟。
- **冬 · 雪夜家属院**：彻底拆除空白墙面凭空浮现的 5 盏机械渐变假楼道灯与前景枯树 2D 扭曲；远楼仅留有实体窗框的固定暖窗；完整保留值班室干净翻页（148.500s 峰值书页与台灯分离 >4 原生像素，零亮桥粘连）、屋顶斜飘淡烟、路灯光锥风雪与枝梢抖雪。

---

## 历史归档版本

### v2.2（已被 v2.3 全面取代 — 仅作迭代归档）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.2-rainroji-lofi-1080p>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1y9qdcQPk3geWR6BVjEySXCH69rjytw_3/view?usp=drivesdk>
- **文件名 / 大小 / SHA-256**：`Rainroji_Lofi_V2.2_1080p.mp4` / `196,231,965` 字节 / `334ef2fde251af347048bc608d202d9a44700a8810e886dd2e4c4a7ec39b66d4`

### v2.1（已被后续版本取代 — 仅作迭代归档）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.1-rainroji-lofi-1080p>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1DIg66GW6FHtitbUyHgslwJta29awbtD-/view?usp=drivesdk>
- **文件名 / 大小 / SHA-256**：`Rainroji_Lofi_V2.1_1080p.mp4` / `153,200,285` 字节 / `62ceff09d8cd365f80f74686ae385f7aec6a138da27e2a428402483a23cc098b`

### v2.0（初版终审签收归档）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.0-rainroji-lofi-1080p>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1pQLUQez4nAWbnoMQ7wYO3ojIl7b1zhEO/view?usp=drivesdk>
- **文件名 / 大小 / SHA-256**：`Rainroji_Lofi_V2_1080p.mp4` / `151,157,219` 字节 / `2987f1b6b85cc9fe2ecc165315b3cc8fef6dc3c9eae4b3efdd2101f67569fe5b`

---

## 从仓库一键重建与核查文档

- v2.3 重建：`python tools/gate3_v23/reproduce.py`（说明见 [tools/gate3_v23/README.md](tools/gate3_v23/README.md)）
- v2.3 实解码抽帧与独立复验：[春→夏转场](previews/gate_3_3/decoded_transition_spring_summer.jpg) · [夏→秋转场](previews/gate_3_3/decoded_transition_summer_autumn.jpg) · [秋→冬转场](previews/gate_3_3/decoded_transition_autumn_winter.jpg) · [夏冬关键动作](previews/gate_3_3/decoded_cue_check.jpg) · [春布持帧与秋叶](previews/gate_3_3/decoded_held_spring_and_autumn_leaf.jpg) · [独立复验报告](previews/gate_3_3/QA.md) · [完整音乐署名（CC BY 4.0）](CREDITS.md) · [全流程审片记录](REVIEW_LOG.md)

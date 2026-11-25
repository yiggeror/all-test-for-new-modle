# 四季像素短片 · 成片交付（v2.9 精修中 / 当前已发布基线 v2.8）

> **当前状态（2026-11-25 Round 32 · v2.9 精修中）**：用户实看指出春、夏、冬四处显眼主光源缺少可见物理支撑（尤其冬景主路灯呈浮空状），已下达 [`REVIEW_LOG.md`](REVIEW_LOG.md) Round 32 精修令，正在为四处光源补全在 `320×180` 像素画下清晰连续的老式金属挑臂、斜撑与灯罩（秋景 v2.7、冬夜暖窗翻书 v2.8 及所有已签收动态与 9,247 包音轨 100% 锁定不动）。以下为上一已发布版本 v2.8 留档，待 v2.9 严审通过后发布替换。

---

## 上一已发布版本：v2.8（待 v2.9 替换）

### 双渠道正式链接（两处逐字节 100% 一致）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.8-rainroji-lofi-1080p>
- **GitHub Release 单文件直链**：<https://github.com/yiggeror/all-test-for-new-modle/releases/download/v2.8-rainroji-lofi-1080p/Rainroji_Lofi_V2.8_1080p.mp4>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1UVVet6giggXUzx_LOafk83aiTNf_mS3Y/view?usp=drivesdk>（File ID：`1UVVet6giggXUzx_LOafk83aiTNf_mS3Y`）

### v2.8 已发布成品实测参数

| 项目 | 参数 |
| --- | --- |
| 文件名 | `Rainroji_Lofi_V2.8_1080p.mp4` |
| 文件大小 | `141,459,565` 字节（134.91 MiB，GitHub Release 与 Google Drive 逐字节一致） |
| SHA-256 | `515b5185225f2c8c27ec7906dc5d77de112f9f943d76d9a6a7017abb59502cc9` |
| MD5 | `41e37a5f8862d30edbb178d89c6514ca` |
| 视频 | `1920×1080`（由 `320×180` 原生像素画经 `6×` 最近邻无损整数放大）· 30 fps · `5,917` 帧 · H.264 High / CRF 14 / yuv420p / BT.709 / `faststart` |
| 时长与码率 | `197.233333` 秒（3 分 17.23 秒，严格不加时）· 容器约 5.74 Mb/s · 视频约 5.47 Mb/s |
| 音频 | 无损流拷贝沿用已签收 v2.4–v2.7 全部 9,247 个 48 kHz 立体声 AAC-LC 包（257.8 kb/s · 完整 Purrple Cat《Green Tea》+ 四季确定性环境音 + 冬窗翻页拟音 + 尾声冬夜雪风 +8.0 dB 渐强收尾） |
| 实测响度 | −16.0 LUFS-I · −4.7 dBFS True Peak · LRA 13.4 LU（零削波） |
| 发布构建流水线 | GitHub Actions `Publish Rainroji Lo-Fi V2.8 1080p Release`（Run `#45587982643`，Ubuntu 24.04 + FFmpeg + Python 3.12） |

### v2.8 相对 v2.7 核心升级与实片终审亮点
- **冬 · 雪夜家属院（值班室暖窗伏案翻书彻底重塑）**：
  - **贴桌低弧度自然翻书**：彻底消除旧版“水平直臂空悬 0.8 秒 + 半空悬空发光小白旗/斧头”的违和感；翻起的暖纸单页底部始终稳扎桌面书脊，手腕贴桌顺滑轻捻并沿低矮柔和弧线（最高约 1.5 px）将书页从右向左翻过压平，精准对齐既有冬窗纸页轻拂拟音；
  - **头肩柔和协同微动**：将暖窗伏案人影头肩纳入动态合成，翻页时自然配合极克制的微低头跟视与回正，零边缘渗漏与闪烁；
  - **冬景窗外全层 100% 零回归**：完整保留“欢度春节”红横幅微褶、细枝风颤、路灯压降、电视微光、烟囱轻烟、全层落雪/窗雪/雪粉与空白墙面零假灯（暖窗 ROI 之外全屏 `0` 像素变动）。
- **春、夏、秋**：**100% 逐字节锁定沿用 v2.7**（春整冠风波 + 暖地常驻单猫 + 双侧落花 + 6 只归燕；夏逐帧暖琥珀车灯 + “网吧”4 次硬切同帧联动红水洼；秋 v2.7 修长优雅倚树看书少女 + 三段迎风长发 + 身前清晰翻书 + 有机多尺度 FBM 树冠风 + 静态路面独立地面积叶 + 88 条双侧飘叶）。
- **尾声冬夜环境音渐强收尾（不加时，精确 `3:17.23`）**：无损保留全部 9,247 个 AAC-LC 音包——在《Green Tea》自然静默的过程中，温润低通冬夜雪风平滑抬升 **+8.0 dB** 步入前景，最后 **2.70 秒**随尾帧淡黑同步淡出至干净静音。

---

## 历史归档版本

### v2.7（已被 v2.8 升级取代 — 归档）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.7-rainroji-lofi-1080p>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1f9WOEhDfcBVXH3xt1DtUFh8N8RVGPqBu/view?usp=drivesdk>
- **文件名 / 大小 / SHA-256**：`Rainroji_Lofi_V2.7_1080p.mp4` / `141,465,116` 字节 / `20a0082f699a8c01255dc0ea85607447c9c89ca115f82dca81d5da96ea724518`

### v2.6（已被后续版本取代 — 归档）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.6-rainroji-lofi-1080p>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1D-cOfHm4f93lEVud4uJ2auEOhPaiqJA3/view?usp=drivesdk>
- **文件名 / 大小 / SHA-256**：`Rainroji_Lofi_V2.6_1080p.mp4` / `141,458,386` 字节 / `22e4039aff0e886323632568efe34a4d91c308f7f9ca45bd8ba904713d58e565`

### v2.5（已被后续版本取代 — 归档）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.5-rainroji-lofi-1080p>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1WIaoLMtNmBffElUx1ahcf0nYBwzyyDn6/view?usp=drivesdk>
- **文件名 / 大小 / SHA-256**：`Rainroji_Lofi_V2.5_1080p.mp4` / `141,154,392` 字节 / `90b96d6e02b63b7a3054d262a2101b32c2a75735f52bc85de1151775452407fd`

### v2.4（已被后续版本取代 — 归档）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.4-rainroji-lofi-1080p>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1b5rSQKERX4LZ1RH_VFj7ELRzqb5C5lCW/view?usp=drivesdk>
- **文件名 / 大小 / SHA-256**：`Rainroji_Lofi_V2.4_1080p.mp4` / `132,852,726` 字节 / `a9870ce471487b76b68c93eb779a075182e5d1b28b3e18d145aae99f480d0687`

### v2.3（已被后续版本取代 — 干净基线归档）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.3-rainroji-lofi-1080p>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1OHGVCFF3U3X4Y-5tgJif8t7-Fo4H99rr/view?usp=drivesdk>
- **文件名 / 大小 / SHA-256**：`Rainroji_Lofi_V2.3_1080p.mp4` / `124,559,510` 字节 / `e33bc5e738ed472fabdcb8ba1837779087c7c8f3e3c2a28882b8d4604453dee8`

### v2.2（已被后续版本取代 — 仅作迭代归档）
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

- **v2.8 一键重建**：`python tools/gate3_v28/reproduce.py`（说明见 [tools/gate3_v28/README.md](tools/gate3_v28/README.md)）
- **v2.8 实解码对比与独立复验**：[v2.7 vs v2.8 冬夜暖窗实解逐帧对比](previews/gate_3_8/reader_v27_v28_decoded_compare.png) · [冬夜暖窗 5× 实解带音原速片段](previews/gate_3_8/review_winter_reader_5x_1x.mp4) · [独立成片复验数据](previews/gate_3_8/INDEPENDENT_QA.json) · [完整音乐署名（CC BY 4.0）](CREDITS.md) · [全流程审片记录](REVIEW_LOG.md)




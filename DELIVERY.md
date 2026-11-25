# 四季像素短片 · 成片交付（v2.5 已正式发布 · v2.6 秋景靠树少女精修进行中）

> **当前状态（2026-11-24 Round 22）**：在 v2.5 已发布成片基础上已启动 **`v2.6 / Gate 2.6` 专项精修**（春、夏、冬及秋景风波/落叶/地面积叶与 v2.4 尾声冬夜雪风音轨 100% 锁定不动；仅将秋景报刊亭前的人物重塑为**倚靠梧桐树干惬意看书、发丝随风轻摇的少女**，详见 [`REVIEW_LOG.md`](REVIEW_LOG.md) Round 22）。以下 **v2.5** 链接为当前最新已发布正式成品。


---

## 当前最新正式版：v2.5（终审定版 · 推荐）

### 双渠道正式链接（两处逐字节 100% 一致）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.5-rainroji-lofi-1080p>
- **GitHub Release 单文件直链**：<https://github.com/yiggeror/all-test-for-new-modle/releases/download/v2.5-rainroji-lofi-1080p/Rainroji_Lofi_V2.5_1080p.mp4>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1WIaoLMtNmBffElUx1ahcf0nYBwzyyDn6/view?usp=drivesdk>（File ID：`1WIaoLMtNmBffElUx1ahcf0nYBwzyyDn6`）

### v2.5 已发布成品实测参数

| 项目 | 参数 |
| --- | --- |
| 文件名 | `Rainroji_Lofi_V2.5_1080p.mp4` |
| 文件大小 | `141,154,392` 字节（134.62 MiB，GitHub Release 与 Google Drive 逐字节一致） |
| SHA-256 | `90b96d6e02b63b7a3054d262a2101b32c2a75735f52bc85de1151775452407fd` |
| MD5 | `4b25fc693fcd2d76323ca0f5b9dd78b8` |
| 视频 | `1920×1080`（由 `320×180` 原生像素画经 `6×` 最近邻无损整数放大）· 30 fps · `5,917` 帧 · H.264 High / CRF 14 / yuv420p / BT.709 / `faststart` |
| 时长与码率 | `197.233333` 秒（3 分 17.23 秒，严格不加时）· 容器约 5.73 Mb/s · 视频约 5.46 Mb/s |
| 音频 | 无损流拷贝沿用已签收 v2.4 全部 9,247 个 48 kHz 立体声 AAC-LC 包（257.8 kb/s · 完整 Purrple Cat《Green Tea》+ 四季确定性环境音 + 冬窗翻页拟音 + 尾声冬夜雪风 +8.0 dB 渐强收尾） |
| 实测响度 | −16.0 LUFS-I · −4.7 dBFS True Peak · LRA 13.4 LU（零削波） |
| 发布构建流水线 | GitHub Actions `Publish Rainroji Lo-Fi V2.5 1080p Release`（Run `#45534392699`，Ubuntu 24.04 + FFmpeg + Python 3.12） |

### v2.5 相对 v2.4 核心升级与实片终审亮点
- **春 · 老巷暮色**：树冠升级为**整冠连续 FBM 风场相位波 ±1px 整数像素叶颤**（覆盖 71.1% 物理叶片、单帧活跃 12.6%，彻底告别局部 5×5 抽搐与果冻感，粗树干 0 位移）；院落小猫升级为**全程 330 帧留在暖橘受光地面带内的单只自然往返闭环**（绝不离场刷怪、绝不钻左墙冷暗影、去回路径错开、始终清晰可读侧身/3/4 猫咪剪影与接地影）；保留左右双侧丰盈落花、暮空 6 只灰紫归燕、老路灯短促压降与 5 帧步进晾衣布。
- **夏 · 雨夜街角**：**100% 逐字节锁定沿用 v2.4 / v2.3**（逐帧双车灯扫路与红车、有机暗红碎波水洼、“网吧”4 次硬切同帧联动）。
- **秋 · 梧桐黄昏**：左侧报刊亭前新增 **1:1 真实 3D 站立低头看报路人**（胸前双肘自然托举暖光报纸、真实接地投影、每周期一次清晰可读的胸前翻报动作，与冬景值班室读书人形成跨季呼应）；双侧梧桐冠升级为**整冠连续 FBM 风场相位波 ±1px 整数像素叶颤**（覆盖 74.0% 物理叶片、单帧活跃 11.4%，彻底取代 16 个孤立椭圆斑点）；空中落叶加密至 **88 条左右均衡树冠飘落轨迹**，并新增**左右路牙与人行道地面积叶随阵风沙沙微颤与贴地短滑**；保留热茶汽、斑马线卷叶、3 只暮空归鸟与钠灯短促压降。
- **冬 · 雪夜家属院**：**100% 逐字节锁定沿用 v2.4**（中景“欢度春节”红横幅迎风微褶、上部细枝轻颤、左路灯短促压降、空白右墙零假楼道灯、值班室干净翻页与屋顶斜烟）。
- **尾声冬夜环境音渐强收尾（不加时，精确 `3:17.23`）**：无损保留 v2.4 全部 9,247 个 AAC-LC 音包——在《Green Tea》自然静默的过程中，温润低通冬夜雪风平滑抬升 **+8.0 dB** 步入前景，最后 **2.70 秒**随尾帧淡黑同步淡出至干净静音。

---

## 历史归档版本

### v2.4（已被 v2.5 升级取代 — 归档）
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

- **v2.5 一键重建**：`python tools/gate3_v25/reproduce.py`（说明见 [tools/gate3_v25/README.md](tools/gate3_v25/README.md)）
- **v2.5 实解码抽帧与独立复验**：[三季转场实解总览](previews/gate_3_5/encoded_transition_storyboard.jpg) · [秋报刊亭看报人实解](previews/gate_3_5/independent_actual_autumn_reader.png) · [春猫暖地往返实解](previews/gate_3_5/independent_actual_spring_cat.png) · [冬值班室实解](previews/gate_3_5/independent_actual_winter_reader.png) · [独立成片复验报告](previews/gate_3_5/GATE35_INDEPENDENT_QA.md) · [完整音乐署名（CC BY 4.0）](CREDITS.md) · [全流程审片记录](REVIEW_LOG.md)



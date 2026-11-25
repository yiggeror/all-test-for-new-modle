# 四季像素短片 · 成片交付（v2.7 返工中 / 当前已发布基线 v2.6）

> **当前状态（2026-11-24 Round 26 · v2.7 返工中）**：用户与验收官实片复查指出 v2.6 秋景人物比例臃肿、驼背且屈膝呈“靠墙静蹲”怪姿，已下达 [`REVIEW_LOG.md`](REVIEW_LOG.md) Round 26 返工令，正在彻底重建修长优雅的秋景靠树看书少女（春、夏、冬、秋景有机树风/独立地面积叶与 v2.4 音轨 100% 锁定不动）。以下为上一已发布版本 v2.6 留档，待 v2.7 严审通过后发布替换。

---

## 上一已发布版本：v2.6（待 v2.7 替换）

### 双渠道正式链接（两处逐字节 100% 一致）
- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.6-rainroji-lofi-1080p>
- **GitHub Release 单文件直链**：<https://github.com/yiggeror/all-test-for-new-modle/releases/download/v2.6-rainroji-lofi-1080p/Rainroji_Lofi_V2.6_1080p.mp4>
- **Google Drive 单文件**：<https://drive.google.com/file/d/1D-cOfHm4f93lEVud4uJ2auEOhPaiqJA3/view?usp=drivesdk>（File ID：`1D-cOfHm4f93lEVud4uJ2auEOhPaiqJA3`）

### v2.6 已发布成品实测参数

| 项目 | 参数 |
| --- | --- |
| 文件名 | `Rainroji_Lofi_V2.6_1080p.mp4` |
| 文件大小 | `141,458,386` 字节（134.91 MiB，GitHub Release 与 Google Drive 逐字节一致） |
| SHA-256 | `22e4039aff0e886323632568efe34a4d91c308f7f9ca45bd8ba904713d58e565` |
| MD5 | `8dd72765dd22def28adf25b4f941a84b` |
| 视频 | `1920×1080`（由 `320×180` 原生像素画经 `6×` 最近邻无损整数放大）· 30 fps · `5,917` 帧 · H.264 High / CRF 14 / yuv420p / BT.709 / `faststart` |
| 时长与码率 | `197.233333` 秒（3 分 17.23 秒，严格不加时）· 容器约 5.74 Mb/s · 视频约 5.47 Mb/s |
| 音频 | 无损流拷贝沿用已签收 v2.4 / v2.5 全部 9,247 个 48 kHz 立体声 AAC-LC 包（257.8 kb/s · 完整 Purrple Cat《Green Tea》+ 四季确定性环境音 + 冬窗翻页拟音 + 尾声冬夜雪风 +8.0 dB 渐强收尾） |
| 实测响度 | −16.0 LUFS-I · −4.7 dBFS True Peak · LRA 13.4 LU（零削波） |
| 发布构建流水线 | GitHub Actions `Publish Rainroji Lo-Fi V2.6 1080p Release`（Run `#45552625070`，Ubuntu 24.04 + FFmpeg + Python 3.12） |

### v2.6 相对 v2.5 核心升级与实片终审亮点
- **秋 · 梧桐黄昏（重点重塑）**：
  - **倚树看书少女**：替换 v2.5 僵硬岔腿站姿人物，重塑为**背部自然倚靠在报刊亭旁梧桐树干左侧暖光面、双腿并拢微曲放松站立的文艺少女**（浅燕麦针织开衫 + 深色微伞摆过膝半裙 + 短靴，不强雕五官、纯粹氛围剪影）；**深黑栗色中长发随秋风阵风清晰轻摇**，每 11 秒循环内**单手自然轻抬划过小巧暖光书影惬意翻页**，与冬景值班室暖窗读书人形成跨季呼应；
  - **地面积叶彻底去假**：删除 v2.5 整块人行道贴图平移的 `GroundWind` 假抖动，保证路面底板 100% 稳固静态，改为**左右广域人行道与路牙独立贴地落叶错拍轻掀与短滑**；
  - **树冠风场柔化升级**：采用**多尺度有机 FBM 湍流微风 ±1px 整数叶颤**（打散平行斜纹扫描感，保持整冠高覆盖、粗树干 0 位移、零果冻）；完整保留 88 条双侧飘叶、斑马线卷叶、热茶汽、3 只暮空归鸟与钠灯微压降。
- **春、夏、冬**：**100% 逐字节锁定沿用 v2.5**（春整冠风波 + 暖地常驻单猫 + 双侧落花 + 6 只归燕；夏逐帧暖琥珀车灯 + “网吧”4 次硬切同帧联动红水洼；冬“欢度春节”红横幅微褶 + 细枝风颤 + 值班室干净翻页 + 零假灯）。
- **尾声冬夜环境音渐强收尾（不加时，精确 `3:17.23`）**：无损保留全部 9,247 个 AAC-LC 音包——在《Green Tea》自然静默的过程中，温润低通冬夜雪风平滑抬升 **+8.0 dB** 步入前景，最后 **2.70 秒**随尾帧淡黑同步淡出至干净静音。

---

## 历史归档版本

### v2.5（已被 v2.6 升级取代 — 归档）
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

- **v2.6 一键重建**：`python tools/gate3_v26/reproduce.py`（说明见 [tools/gate3_v26/README.md](tools/gate3_v26/README.md)）
- **v2.6 实解码抽帧与独立复验**：[三季转场实解总览](previews/gate_3_6/encoded_transition_storyboard.jpg) · [秋靠树少女翻页与飘发 4× 实解](previews/gate_3_6/independent_v26_autumn_reader_4x.png) · [秋 F3005 原尺寸实解](previews/gate_3_6/independent_v26_f3005_actual_1080p.png) · [独立成片复验报告](previews/gate_3_6/INDEPENDENT_GATE36_QA.md) · [完整音乐署名（CC BY 4.0）](CREDITS.md) · [全流程审片记录](REVIEW_LOG.md)




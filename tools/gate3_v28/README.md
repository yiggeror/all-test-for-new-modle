# Rainroji v2.8 · 四季成片

冬夜值班室暖窗改为贴桌捻页、轻压与回手，头肩随之微动。春、夏、秋、冬窗外与原音轨均沿用 v2.7。

## 重建

检出含 [Round 30 签收记录](https://github.com/yiggeror/all-test-for-new-modle/blob/ba035943bd6057ad107b8decf6eb1c416a81b624/REVIEW_LOG.md) 与 `previews/gate_2_8/lossless_parts/` 的分支。需要 Python 3.12、带 libx264 的 FFmpeg / ffprobe，及约 850 MB 工作空间。默认从 GitHub 下载上一版的正式 MP4 作为音频来源。

```sh
python -m pip install -r tools/gate3_v28/requirements.txt
python -m unittest discover -s tools/gate3_v28 -v
python tools/gate3_v28/reproduce.py
```

成片写入 `dist/Rainroji_Lofi_V2.8_1080p.mp4`。原速审片、解码抽帧与核验记录写入 `dist/gate3_v28_qa/`。添加 `--keep-picture` 可同时保留未加音轨的中间文件。离线可先下载 v2.7 GitHub 正式发布件并设 `RAINROJI_V27_RELEASE_CACHE=/path/to/Rainroji_Lofi_V2.7_1080p.mp4`，或传 `--v27-release-cache`。两种路径都校验完整文件 **141,465,116 字节**、SHA-256 `20a0082f699a8c01255dc0ea85607447c9c89ca115f82dca81d5da96ea724518`，然后核验同一音轨。

## 装配和校验

- 仅使用 [3826618 的 16 份无损分卷](https://github.com/yiggeror/all-test-for-new-modle/tree/382661831203769681ebcd369603f5512629f74f/previews/gate_2_8/lossless_parts) 作为画面输入。春 1、夏 8、秋 1、冬 6。逐卷检验长度和 SHA-256、按序重组，核验每段 660 个 PTS、双循环的完整 YUV 字节、用原有限色表精确恢复 330 帧原生 RGB。一键重建过程中不读取审片代理或旧成品的视频作为画面来源。
- **0:48、1:36、2:24** 各进行 2 秒线性光 smoothstep 叠化；开头 1.5 秒淡入，193.4–197.2 秒淡出。逐帧对照确认旧版 **F0–4290** 的预编码画面逐字节相同；冬景参与叠化后的变化也仅在暖窗人物与图书的原生范围。先叠化再做 6× 最近邻放大，1920×1080、30 fps、5917 帧、精确 5917/30 秒，H.264 High、CRF 14、BT.709、faststart。
- 正式音轨直接流拷贝。9,247 个 AAC-LC 包的载荷与 PTS/DTS、首包 priming、末包有效长度及完整解码 PCM 都须和基线上相同。音乐为 Purrple Cat《Green Tea》，署名与许可见仓库 `CREDITS.md`。
- 审片视频取自上述已经封装的成片。窗框局部放大与全景取同一段 11 秒、保留原速和同步音频。暖窗 QP0 审片对比原片裁切的 330 帧 YUV 字节；两段审片的 AAC 只用于观看，和正式成片的 9,247 个原 AAC 包分开核验。
- 不同 FFmpeg/libx264 版本可产生不同的压缩字节；需要在同一锁定软件环境内复验文件哈希。各帧时间、画面输入原生哈希、音轨哈希均有独立锁。

# 四季像素短片 V2 · 成片交付（已终审签收）

成片母版已完成复现、逐段实看实听终审，并已以**逐字节完全一致的同一份完整 1080p MP4** 完成 **GitHub Release** 与 **Google Drive** 双渠道发布（仓库不存放超限二进制文件）。

## 正式发布渠道（双渠道逐字节一致）

- **GitHub Release 页面**：<https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.0-rainroji-lofi-1080p>
- **GitHub Release 完整单文件直链**：<https://github.com/yiggeror/all-test-for-new-modle/releases/download/v2.0-rainroji-lofi-1080p/Rainroji_Lofi_V2_1080p.mp4>
- **Google Drive 完整单文件**：<https://drive.google.com/file/d/1pQLUQez4nAWbnoMQ7wYO3ojIl7b1zhEO/view?usp=drivesdk>（File ID：`1pQLUQez4nAWbnoMQ7wYO3ojIl7b1zhEO`）

## 已发布成品实测参数

| 项目 | 参数 |
| --- | --- |
| 文件名 | `Rainroji_Lofi_V2_1080p.mp4` |
| 文件大小 | `151,157,219` 字节（144.15 MB，GitHub Release 与 Google Drive 完全一致） |
| SHA-256 | `2987f1b6b85cc9fe2ecc165315b3cc8fef6dc3c9eae4b3efdd2101f67569fe5b` |
| MD5 | `12dde1ef080376a50e56f0d6054b2c87` |
| 视频 | `1920×1080`（由 `320×180` 原生像素画经 `6×` 最近邻整数放大）· 30 fps · 5,917 帧 · H.264 High / CRF 14 / yuv420p / BT.709 / faststart |
| 时长与码率 | 197.233333 秒（3 分 17.23 秒）· 容器约 6.13 Mb/s · 视频约 5.87 Mb/s |
| 音频 | AAC-LC · 48 kHz 立体声 · 256 kb/s |
| 实测响度 | −16.04 LUFS-I · −4.77 dBTP · LRA 8.1 LU（零削波） |
| 发布构建流水线 | GitHub Actions `Publish Rainroji Lo-Fi V2 1080p Release`（Run `#45169522195`，Ubuntu 24.04 + FFmpeg 6.1.1 + Python 3.12） |

## 从仓库一键重建

在任意 Linux 环境中安装依赖 `pip install -r tools/gate3/requirements.txt` 与 `ffmpeg`，运行 `python tools/gate3/reproduce.py` 或查看 [tools/gate3/README.md](tools/gate3/README.md) 即可从 `previews/gate_2/lossless_parts/` 与 Purrple Cat 官方原曲完全复现。注：编码 AI 在 Debian 13 + FFmpeg 7.1.5 下的构建为 `151,159,718` 字节（SHA-256 `0213513d08d439c965ef7320b2d896814733fac404d2dc6ddfeac4c122da60ba`）；GitHub Actions（Ubuntu 24.04 + FFmpeg 6.1.1）基于完全相同的 4 份无损 320×180 RGB 原片与同一份作者原曲（SHA-256 `f6feac60...`）直出并同步至 Google Drive，两处云端成品逐字节一致。

## 核查与署名

[三处转场实解码抽帧](previews/gate_3/encoded_transition_storyboard.jpg) · [独立复验报告](previews/gate_3/QA.md) · [完整音乐署名（CC BY 4.0）](CREDITS.md) · [全流程审片记录](REVIEW_LOG.md)

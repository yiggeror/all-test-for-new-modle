# Gate 3 合片脚本
将本目录脚本分别放到配套的 `alltest_gate3_picture/` 与 `alltest_gate3_audio/tools/` 中使用。原生帧沿用已审 Gate 2 两组渲染器：见 `previews/gate_2/source/`。`assemble.py` 的源清单记录四季预期的原生 .npy 文件路径和哈希，禁止把兼容版 MP4 当作输入。作者原曲以 `CREDITS.md` 的录音地址取得；原文件 SHA-256 为 `f6feac60dc29b89ea1513e04d0b30addf86f9c8576827e7566e27b5abd522e71`。

最终封装只复制两条流，电影时基 48000 保留完整末尾采样：

```sh
ffmpeg -i picture_only.mp4 -i green_tea_gate3.m4a -map 0:v:0 -map 1:a:0 -c copy \
  -movie_timescale 48000 -movflags +faststart -metadata creation_time=2026-11-23T00:00:00Z Rainroji_Lofi_V2_1080p.mp4
```

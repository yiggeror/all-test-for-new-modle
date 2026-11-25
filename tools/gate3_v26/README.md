# Rainroji v2.6 · Gate 3.6 终版

只从 Gate 2.6 已审批的 16 份无损分卷还原画面，音频取已发布的 v2.5 正式件并原包复制。不要用压缩预览、旧整片画面或制作端 NPY 代替画源。

## 一键重建

检出包含 [Round 24 正式审批](https://github.com/yiggeror/all-test-for-new-modle/blob/2b1f97a62d61b2375029e8ed32419890f6ade03f/REVIEW_LOG.md) 与完整 `previews/gate_2_6/lossless_parts/` 的仓库。需要 Python 3.12+、FFmpeg / ffprobe（带 libx264），`dist/` 至少 850 MB 可用：

```sh
python -m pip install -r tools/gate3_v26/requirements.txt
python tools/gate3_v26/reproduce.py
```

生成 `dist/Rainroji_Lofi_V2.6_1080p.mp4` 和 `dist/gate3_v26_qa/`；拒绝覆盖现有正式输出。加 `--keep-picture` 可同时留只含画面的原编码轨。默认仅下载 [官方 v2.5 发布件](https://github.com/yiggeror/all-test-for-new-modle/releases/download/v2.5-rainroji-lofi-1080p/Rainroji_Lofi_V2.5_1080p.mp4) 取已验收的一条音轨，无需登录；已有同一发布件时可用 `--v25-release-cache /path/to/Rainroji_Lofi_V2.5_1080p.mp4` 或 `RAINROJI_V25_RELEASE_CACHE`。始终核对 **141,154,392 B / SHA-256 `90b96d6e02b63b7a3054d262a2101b32c2a75735f52bc85de1151775452407fd`**，旧本地候审或其他转码不替代。

## 锁定内容和证据

- 审批对象 `44964634a3fb72c168ae5304988e402b767708ac`，分卷清单 SHA-256 `7b37e9527d578797430c4b15f4a1a3d12830f10b3f62777c0fea37bab506baaf`，春 1 / 夏 8 / 秋 1 / 冬 6。逐卷与合并容器验字节和 SHA，再解码每季 660 帧、两周完全相同。有限色彩表把真实无损 YUV 整格恢复为原生 RGB；表内没有画面数据。
- 时间线与 v2.5 相同：48/96/144 s 中心各 2.0 s 线性光 smoothstep、1.5 s 开头淡入、193.4–197.2 s 尾淡。实际送编码器 320×180 RGB24 完整指纹 `a5b17e2c3a20ebf0e56245871346fc010c08154dc8beec42b49a6810f1f9ccc0`；硬验 F0–2850（含春夏叠化）及 F4350–5916（含尾淡）两段和 v2.5 同一，差异仅落在秋及其两侧叠化。
- 6× 整数最近邻输出 1920×1080、30fps、5,917 帧 / 197.233333 s、H.264 High / CRF14、BT.709 限幅矩阵、faststart。音轨 `-c:a copy`，校验所有 9,247 AAC-LC 包载荷、PTS/DTS/时长、配置、priming 和尾有效段，保持 9,467,200 个有效 48kHz 样点。不会重混或重新编码。
- 末段验证成片真正全解码与响度，并保存无叠字的全幅解码静帧。实测环境：Python 3.12.14 / NumPy 2.3.5 / Pillow 13.0.0 / FFmpeg 7.1.5-0+deb13u1。不依赖系统中文字体完成媒体；不同 FFmpeg/libx264 的最终容器字节可以不同，但原生画面输入、包内容、时钟与窗口不变。

```sh
python -m unittest discover -s tools/gate3_v26 -v
```

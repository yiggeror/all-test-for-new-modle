# Gate 3 一键重建

在拿到含 `previews/gate_2/lossless_parts/` 的本分支后，使用 **Python 3.12、`requirements.txt` 锁定的 NumPy/SciPy/Pillow、带 libx264 的 FFmpeg 和 ffprobe**。首次使用可把依赖装到 Python 虚拟环境：`python -m pip install -r tools/gate3/requirements.txt`。

从仓库根目录运行：

```sh
python tools/gate3/reproduce.py
```

不需要改脚本、下载预览代理、配置中间路径或访问团队工作区。正常运行只联网读取 [Purrple Cat 作者原始录音](https://html-classic.itch.zone/html/19949767/media/Green%20Tea.mp3)；其它输入来自本仓库。需要可用空间约 1 GB；原生 RGB、合片和 QC 在普通 Linux CPU 上用几分钟。输出：

- `dist/Rainroji_Lofi_V2_1080p.mp4`：151,159,718 B；SHA-256 `0213513d08d439c965ef7320b2d896814733fac404d2dc6ddfeac4c122da60ba`。
- `dist/reproduction_qa.json`：工具链、作者曲源、原生流及压缩中间文件指纹，整片解码、时长、声道、响度和真峰值实测。

脚本先分卷核验还原四条 Gate 2 无损两周期 MP4，再用已审色板恢复并逐文件验证原生 320×180 RGB 的同一周期（详见 [RECOVERY.md](RECOVERY.md)）。画面先在原生帧完成叠化，再 6× 最近邻放大和 CRF 14 编码；音频以完整原曲混成四季环境和 AAC-LC。最终 `-c copy -movie_timescale 48000`，不二次编码，也不截断尾音。哈希不同不会覆盖原件或生成同名候选成片。

原件的字节级校验环境为 Linux x86‑64、Python 3.12.14、FFmpeg `7.1.5-0+deb13u1`、x264 core 164 `r3108 31e19f9`；其它二进制构建可能改变编码字节。遇到摘要不符先看 `reproduction_qa.json`，再按本版本重试；不要把重编码代理当作验收原件。仓库不提交 `dist/` 成片或临时音视频。

轻量测试：`python -m unittest discover -s tools/gate3`。

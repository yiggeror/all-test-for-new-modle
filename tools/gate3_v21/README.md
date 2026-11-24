# Rainroji v2.1 · Gate 3.1 一键重建

在完整的 `feat/lofi-seasons-v2` 仓库根目录（含 `previews/gate_2_1/lossless_parts/`）运行：

```bash
python tools/gate3_v21/reproduce.py
```

一次性环境：Linux / Python 3.12，PATH 内含 FFmpeg + ffprobe 与 libx264，`python -m pip install -r tools/gate3_v21/requirements.txt`。如系统 Python 由系统包管理，请在 Python 虚拟环境中安装。运行需要约 1 GB 工作空间。无需设置项目路径；只有一次已签收 v2.0 官方 MP4 的 HTTPS 下载。已持有同一 MP4 时可用 `--v20-release-cache /path/to/official-v2.0.mp4`，仍验证其 151,157,219 bytes、整文件 SHA-256 `2987f1b6b85cc9fe2ecc165315b3cc8fef6dc3c9eae4b3efdd2101f67569fe5b` 与 AAC 包序列；M4A、旧本地构建和浏览器代理不会被当成这份锁定原件。

## 产物

- `dist/Rainroji_Lofi_V2.1_1080p.mp4`：最终完整 MP4，5917 帧，30 fps，1920×1080，197.233333 秒，High / CRF 14 / BT.709 / faststart。
- `dist/gate3_v21_qa/{reproduction_qa,picture_render,picture_plan}.json`：实际整片校验、构建信息、声画流和时码。`--keep-picture` 可另外保留画面母轨做独立审查。输出已存在时不自动覆盖。

## 锁定范围

1. 只用 `bc09740` Gate 2.1 合计 19 个无损分卷；每卷、拼接正本、四季实际原生 `330×180×320×3 uint8` 恢复结果分别验证。以每季固定的、无碰撞的 Y:Cb:Cr→RGB 表逆还原原生像素，不从 `previews/gate_2_1/*_loop.mp4` 浏览器预览转码。输入色表和三种 SHA 保存在 `native_fingerprints.json`。
2. 保留 v2.0 的线性光叠化：60 帧窗 `[1410,1470)` / `[2850,2910)` / `[4290,4350)`，中心 48 / 96 / 144 秒；时间权重沿已审 v2.0 `u²(3−2u)`，不是以时钟恒速变化，中点各 50%。45 帧淡入、114 帧尾淡，末帧 197.2 秒为黑。先在 320×180 合成，再 6× 最近邻放大并仅一次 H.264 编码。
3. 官方 v2.0 Release 的完整配乐、四季环境和纸页拟音保留原 AAC：`-c copy`、电影时基 48000，无截断/位移/再编码。逐包锁定 9247 个载荷，在输出中重验 PTS/DTS、有效时长、1024 样本 priming 与 ADTS SHA；保留作者完整曲目及 [CC BY 4.0 署名](../../CREDITS.md)。

已测工具链：Linux x86-64、Python 3.12.14、NumPy 2.3.5、Pillow 13.0.0、FFmpeg / ffprobe `7.1.5-0+deb13u1`、x264 core 164 `r3108 31e19f9`。不同 FFmpeg / x264 / 数值库构建的画面压缩字节或罕见的转场舍入可能不同；对每台构建机记录实际 SHA 并以同一个成片文件同步发布。输入原生帧身份与音轨包身份不是可放宽项。不要把另一工具链的整片哈希写成此报告的实测值。

单测：`python -m unittest discover -s tools/gate3_v21`。

# Rainroji v2.2 · Gate 3.2 一键重建

在完整的 feat/lofi-seasons-v2 仓库根目录（含 previews/gate_2_2/lossless_parts/）运行：

    python tools/gate3_v22/reproduce.py

一次性环境：Python 3.12，PATH 内含 FFmpeg / ffprobe 和 libx264，先在虚拟环境运行：

    python -m pip install -r tools/gate3_v22/requirements.txt

请预留 2 GB 工作空间。脚本没有手填路径；只进行一次官方 v2.0 MP4 的 HTTPS 下载。已有官方完整文件时，可加 --v20-release-cache /path/to/v2.0.mp4，仍验 151,157,219 字节、整片 SHA-256、AAC 编码和包时码。M4A、v2.1 文件、浏览器代理和旧本地成片都不能取代官方输入。

## 画面、音轨与输出

- [Round 10](https://github.com/yiggeror/all-test-for-new-modle/blob/a76a1b807b114c15036caebe58bffadeec3f53dd/REVIEW_LOG.md) 所批准的 [352fa0a](https://github.com/yiggeror/all-test-for-new-modle/commit/352fa0a2e7d86b7f5b5030eed7c99b22ed162d3b) 26 份分卷是唯一画面来源。先验清单、每卷与四条完整正本，再读原 Y:Cb:Cr。每季固定色板的反查键互不碰撞，58／59／60／60 色逐像素恢复；同时验证 660 帧、两周期恒等以及首周期 RGB 哈希。JSON 只存颜色和哈希，不装原生帧；运行不读取本地原始 NPY 或任何 MP4 代理。临时 NPY 由本次分卷生成。
- 画面从 320×180 原生做线性光混合；三段 60 帧窗为 [1410,1470)、[2850,2910)、[4290,4350)，中心 48／96／144 秒。时间权重沿已审 v2.0 的 smoothstep 曲线，四分点 15.625%／84.375%、中点 50%。片头 45 帧淡入，片尾从 F5802（193.4s）在 114 帧内淡黑。随后 6× 最近邻，只做一次 H.264 High / CRF14 / BT.709 限幅编码。
- 保留官方 v2.0 Release 的完整《Green Tea》、四季环境音和冬窗拟音，依次核验 9,247 AAC 包载荷、PTS/DTS、有效时长与 1024 采样 priming；-c copy 流复制，不混音或截断。同时复核最终 H.264 包经过封装保持一致。[音乐署名与 CC BY 4.0](../../CREDITS.md)。
- 正式候审输出 **dist/Rainroji_Lofi_V2.2_1080p.mp4**，1920×1080 / 30 fps / 5,917 帧 / 197.233333 秒，faststart。
- 复现证据写入 **dist/gate3_v22_qa/**：合成时间表、实编码和响度报告、三处原尺寸实解码转场图与首尾淡变图、出处和 SHA-256。可选 --keep-picture 额外保留封装前 H.264 轨供独立核查；默认不保留重复画面文件。已有输出不覆盖。

匹配的 Debian 参考工具链为 Python 3.12.14、NumPy 2.3.5、Pillow 13.0.0、FFmpeg 7.1.5-0+deb13u1、libx264 core 164 r3108 31e19f9；其他 x264 编译版本可能得到不同成片字节。不同数值库构建若发现原生混合舍入少量差异，脚本在报告中明确标记，正式发布时进行实解码复核。已获审批的四个输入和原 AAC 包身份保持硬校验。

单测：

    python -m unittest discover -s tools/gate3_v22

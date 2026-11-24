# Rainroji v2.3 · Gate 3.3 一键重建

在含有审批分卷的仓库根目录运行：

    python tools/gate3_v23/reproduce.py

需 Python 3.12、PATH 上的 FFmpeg / ffprobe（含 libx264），以及：

    python -m pip install -r tools/gate3_v23/requirements.txt

请预留 2 GB。默认只从 GitHub 下载已经签收的 v2.0 正式 MP4（不重新混音）；若本地已有该正式文件可传 --v20-release-cache 路径，仍按正式文件完整字节数和 SHA-256 验证。可另加 --keep-picture 留下封装前画面轨供复验。已存在的输出不覆盖。

- 唯一画面输入是 [Round 13](https://github.com/yiggeror/all-test-for-new-modle/blob/8fbb28eb7a61329ffa218c6e7f92b4f72d19c6ee/REVIEW_LOG.md) 审批的 [d491fe13](https://github.com/yiggeror/all-test-for-new-modle/commit/d491fe13aaa2ff4b5addd296d42f1a40b73c85fc) 下 16 个无损分卷。逐一核清单、每卷及重组后四条 H.264 正本。逐轨核实际 660 帧 PTS、两周期逐像素恒等。小色表存限定色板的 Y:Cb:Cr → RGB 反查键，不含画面；颜色键无碰撞。仅本次从分卷生成临时 NPY，不读代理、上版成片或任何外部原生帧。
- 春季相邻 132 个天然持帧是已批素材：只接受精确相等索引，从 0 到 329 每一相位仍占一个 1/30 秒帧位，绝不抽帧或去重。四季分别核每个原生帧的顺序指纹；整片则验证解码顺序的 PTS 与送编码器的 5917 帧 320×180 RGB24 字节指纹。
- 320×180 线性光混合后，以 6× 最近邻升至 1920×1080。60 帧窗口为 [1410,1470)、[2850,2910)、[4290,4350)，中心 48/96/144 秒；沿 v2.0 的 smoothstep 权重处理中间 50%、四分点 15.625% 与 84.375%。片头 45 帧淡入，片尾从 F5802（193.4 秒）以 114 帧步长淡至 F5916。一次 H.264 High / CRF14 / BT.709 限幅编码，30fps，faststart。
- v2.0 正式发布件为 151,157,219 字节。全部 9,247 AAC-LC 包原样流复制，核每包载荷、PTS/DTS、有效时长、首包 1024 采样 priming 和 ADTS 指纹；封装不改 H.264 包。音轨完全继承原《Green Tea》、四季环境音、冬窗翻页拟音。[音乐署名及 CC BY 4.0](../../CREDITS.md)。
- 输出 **dist/Rainroji_Lofi_V2.3_1080p.mp4**，共 5,917 帧 / 197.233333 秒。**dist/gate3_v23_qa/** 中有实际成片解码抽帧、关键动作对应帧、整片 QC、编码和证据指纹。不在源图加审片标注。

参考构建：Debian x86_64、Python 3.12.14、NumPy 2.3.5、Pillow 13.0.0、FFmpeg 7.1.5-0+deb13u1、libx264 core 164 r3108 31e19f9。不同 x264 构建的压缩字节可能不同；原始分卷、送编码器的完整 320×180/5917 RGB24 流及 AAC 包身份要求一致，有偏差立即停止，不自动换源。

单测：

    python -m unittest discover -s tools/gate3_v23

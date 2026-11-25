# Rainroji v2.9｜四季成片

春天街灯与院灯、夏天左上路灯、冬天雪院路灯补齐了挑臂、斜撑和灯罩。秋景、四季原有动作、完整音轨和总时长沿用 v2.8。

## 重建

从含 [Round 33 核验记录](https://github.com/yiggeror/all-test-for-new-modle/blob/a0d0e108f04f5f2d92455cb0eada3ee1c2f2adc1/REVIEW_LOG.md) 的项目根目录执行。需要 Python 3.12、FFmpeg（含 libx264）和 ffprobe。预留约 600 MB 工作空间。

~~~sh
python -m pip install -r tools/gate3_v29/requirements.txt
python -m unittest discover -s tools/gate3_v29 -v
python tools/gate3_v29/reproduce.py
~~~

- 成片：`dist/Rainroji_Lofi_V2.9_1080p.mp4`。
- 原速审片、实解码 1080p 静帧、灯具局部和核验报告：`dist/gate3_v29_qa/`。
- 音轨默认从 [v2.8 官方发布件](https://github.com/yiggeror/all-test-for-new-modle/releases/tag/v2.8-rainroji-lofi-1080p) 获取。离线时传 `--v28-release-cache /path/to/Rainroji_Lofi_V2.8_1080p.mp4`，或设置 `RAINROJI_V28_RELEASE_CACHE`。两条路径均校验 141,459,565 字节、SHA-256 `515b5185225f2c8c27ec7906dc5d77de112f9f943d76d9a6a7017abb59502cc9`，然后逐包核验。
- 加 `--keep-picture` 可保留封装前 H.264 画面轨。重建前将同名输出移动到另一位置。

## 固定时间线与复核

片源为 [03b5d2c 的 16 份无损分卷](https://github.com/yiggeror/all-test-for-new-modle/tree/03b5d2cef53f60a97b095e54323e35d22bd8e794/previews/gate_2_9/lossless_parts)，春 1、夏 8、秋 1、冬 6。校验每卷及合并后的 SHA-256，顺序解码每季 660 帧并验证 330 帧循环重复，再按已审定的色板还原 320×180 原生 RGB。v2.8 发布 MP4 只提供原声；审片代理不进入画面总装。

第 48、96、144 秒为 2.0 秒 smoothstep 线性光叠化的中心。开头 1.5 秒淡入，193.4–197.2 秒尾淡。先在 320×180 计算叠化，再进行 6× 最近邻放大。总帧数 **5,917**，帧率 **30 fps**，总时长精确 **5917/30 秒**（197.233333 秒），画面 **1920×1080**，H.264 High、CRF 14、yuv420p、BT.709、faststart。

`rgb_locks.json` 记录独立从 v2.8 与 v2.9 签收无损卷重算的七个原生时域、四处灯具范围和关键边界。两版原生画面的差异只出现在对应时刻的灯具像素及其叠化表现。**F2910–4290** 的 1,381 帧与 v2.8 原生 RGB 逐字节一致。F0000 和 F5916 均为黑场。不同 FFmpeg/libx264 构建环境可产生不同的 H.264 包；复核应依据原生 RGB、时间线、色域、逐包音轨和实解码报告。

封装时直接复制 v2.8 的 **9,247 个 AAC-LC 包**，逐包比对载荷、PTS/DTS、有效时长以及首包 priming，核对完整有效立体声 PCM。音乐为 Purrple Cat《Green Tea》；作品许可与致谢见仓库 `CREDITS.md`。

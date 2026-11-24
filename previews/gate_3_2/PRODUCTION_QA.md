# Gate 3.2 · v2.2 本地实片核验

[Round 10](https://github.com/yiggeror/all-test-for-new-modle/blob/a76a1b807b114c15036caebe58bffadeec3f53dd/REVIEW_LOG.md) 放行后，从批准的 [352fa0a](https://github.com/yiggeror/all-test-for-new-modle/commit/352fa0a2e7d86b7f5b5030eed7c99b22ed162d3b) 四季原件分卷重建。以下为本地候审成片的实测，不标记云端发布已经完成。

| 实测 | 结果 |
| :--- | :--- |
| 文件 | Rainroji_Lofi_V2.2_1080p.mp4 |
| 文件大小 | 196,231,459 字节 |
| SHA-256 | 9f2e8e207e126752d97994d32e9eeba961d1ba6a6e254013f5648cc61041907a |
| 画面 | 1920×1080 · 30 fps · 5,917 帧 · 197.233333 秒 |
| 编码 | H.264 High / CRF 14 / yuv420p / BT.709 矩阵、限幅 / faststart |
| 音轨 | 官方 v2.0 AAC-LC / 48 kHz / 双声道，9,247 个包与 PTS/DTS/时长/首包 priming 全部相同 |
| 统一仪表实测 | v2.0 官方件与 v2.2 均为 -16.04 LUFS-I、-4.74 dBTP、8.10 LU |

- 26 份审批分卷逐件验 SHA-256 与大小。仅用四条无损 MP4 的原 Y:Cb:Cr 反查精确原生 RGB；累计全解码 2,640 帧，各季 330 对完全相合。58／59／60／60 色均无碰撞。无画面代理或制作工作区原生帧输入。
- 实际编码管道的 5,917 张 320×180 RGB24 无文件头顺序字节流 SHA-256 是 9e412685c15d65b279d2d693a44cab4eefc94698d1df848bbfc4a09607aee6e8，等于独立参考。线性光混色的中心时码为 48／96／144 秒，窗长 2.0s，时间权重保持 v2.0 的 smoothstep。F0 与 F5916 实解码为黑，45 帧淡入与从 F5802 开始的 114 帧尾淡。
- 输出封装检查 5,917 个独立 PTS 连续无缺口，全视频＋音频实际 FFmpeg 解码成功，H.264 压缩包经过封装逐个保持。v2.0 完整原曲、环境和翻书拟音没有重混。Round 10 中的 −4.77 dBTP 仅是记录差异；同一工具链的统一仪表下，正式 v2.0 与本候审 v2.2 完全一致，音频包和时基是判断依据。[原仪表数据](official_reference_meter.json)
- [干净回建](one_click_verified.json) 不带路径参数、既有 NPY、预览代理或音频缓存。默认下载官方 v2.0，按输入锁从零取得成片与上述 SHA。16 项测试通过。不同 x264 构建的成片压缩字节可能不同；发布应把同一个实测文件用于两渠道。

## 真实解码证据

- [48 秒 春→夏](decoded_spring_summer_F1440.png) · [96 秒 夏→秋](decoded_summer_autumn_F2880.png) · [144 秒 秋→冬](decoded_autumn_winter_F4320.png)
- [片头 F022](decoded_head_fade_F022.png) · [片尾 F5870](decoded_tail_fade_F5870.png) · [总览抽帧](encoded_transition_storyboard.jpg)
- [实测读数](reproduction_qa.json) · [全部帧时间表](picture_plan.json) · [逐点解码误差/全片结构](picture_complete_qa.json) · [实编码日志](encode.log)

[独立一键工具](../../tools/gate3_v22/) · [音乐署名](../../CREDITS.md)

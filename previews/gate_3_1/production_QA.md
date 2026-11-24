# Gate 3.1 · v2.1 本地成片实测

使用 [Round 7](https://github.com/yiggeror/all-test-for-new-modle/blob/bc10313a30fab60fef6672b212b1bcc18893d5f3/REVIEW_LOG.md) 批准的 Gate 2.1 无损分卷。v2.0 的正式视频、配乐、标签及重建脚本均原样保留。本页是**本地候审**校验，正式 Release 与 Drive 核验由终审执行。

| 实测项 | 结果 |
| --- | --- |
| 本地成片 | `Rainroji_Lofi_V2.1_1080p.mp4` · 153,200,299 字节 |
| 最终 SHA-256 | `692bf5cab708192337c9537d8abf95ed07aeef54dc63dd9a230cb9661e06d367` |
| 画面 | 1920×1080 · 30 fps · 5,917 帧 · 197.233333 秒 |
| 压缩格式 | H.264 High，CRF 14，yuv420p，BT.709 矩阵、限幅 `tv`，faststart |
| 音频 | AAC-LC，48 kHz 立体声，全曲+原环境和拟音；9,247 包逐包载荷及采样时码与正式 v2.0 相同 |
| 成片响度实测 | −16.04 LUFS-I · −4.74 dBTP · LRA 8.10 LU，留足峰值余量 |

## 成片节奏与画质

- 四季原生合计 1,320 RGB 帧，在封装前分别通过来源分卷、整条无损片、逆查色板及 NPY 哈希；实际送编码管道的 5,917 帧 `320×180` packed RGB24 无头字节流 SHA-256 为 `e875a665d4333c0c3054bd848bf83a9dc6653afd2518d9094d84c4813cb27b9d`，同独立合成计算的该域哈希。
- 三次线性光叠化 `[47,49)`／`[95,97)`／`[143,145)`，中心 48／96／144 秒。在光强线性空间混合，保留 v2.0 的 `smoothstep` 时间权重，四分点为 15.625%／84.375%、中点 50%。45 帧淡入、114 帧尾淡；第 0 帧和最后一帧实解码为黑。
- [转场实解码图](encoded_transition_storyboard.jpg) 选自实际编码画面，图注没有烧进成片。检查全部 5,917 帧递增的播放时戳；72 个实解码帧抽查过转场、循环缝、红霓虹和首尾。对编码前 YUV 的实测平均亮度绝对差约 0.0913/255。视频压缩包在最终封装中不重编码；音画全解码无错。
- 官方 v2.0 原件 SHA-256 `2987f1b6b85cc9fe2ecc165315b3cc8fef6dc3c9eae4b3efdd2101f67569fe5b`；成片音轨的 ADTS SHA-256 `3eb43b1c07211e4ece9173fae7ff25e73e4195f50c430e2f388285971725693d`，首包 −1,024 PTS 和既有 priming 保留，末包 320 样本，完整有效播放 9,467,200 采样。没有重新混音、编码或补音效。[音乐署名](../../CREDITS.md) 沿用。

## 独立核验与重建

[独立核验摘要](independent_qa_summary.json) 以实际候审成片解码抽查 222 帧，另核对完整的 AAC 包、黑边和原生画面；全部通过。

[一键工具](../../tools/gate3_v21/) · [实测 JSON](reproduction_qa.json) · [时间表](picture_plan.json) · [编码画面逐项核验](picture_complete_qa.json)。

在第二个只含仓库无损分卷和工具的工作副本中，零参数 `python tools/gate3_v21/reproduce.py` 下载正式 v2.0 发布件并实际退出 0；输出与上表候审件用 `cmp` 逐字节一致。14 项自动测试通过。见 [干净重建证据](one_click_verified.json)。

本地构建工具链是 Linux x86-64、Python 3.12.14、NumPy 2.3.5、Pillow 13.0.0、FFmpeg / ffprobe 7.1.5 与 x264 core 164 `r3108 31e19f9`。不同编码器实现可能产生不同的成片 SHA；正式双渠道须为同一次发布构建的同一个完整文件。原生输入和 AAC 身份在所有工具链均要求匹配。

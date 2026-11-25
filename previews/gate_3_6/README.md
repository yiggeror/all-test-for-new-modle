# Rainroji v2.6 · Gate 3.6 候审记录

- 终版 `Rainroji_Lofi_V2.6_1080p.mp4`，141,456,016 B，实测 SHA-256 `c193872a27cc2d0384429f86e3153711ebf9d878f3b7c5188e782098923c8931`（当前工具链）；全解码 5,917 帧，30 fps，197.233333 s，实测 BT.709 限幅矩阵，High / CRF14，faststart。
- 唯一画源为 Round 24 审批的 16 份 Gate 2.6 QP0 分卷（1+8+1+6，不使用压缩预览）。实际编码输入 5917 张 RGB24 指纹 `a5b17e2c3a20ebf0e56245871346fc010c08154dc8beec42b49a6810f1f9ccc0`，与独立参考全同。
- F0–2850（含春夏叠化）、F4350–5916（含冬与尾淡）与 v2.5 编码前逐像素同一，只有含秋的 F2851–4349 改动。三个正片转场中心 48 / 96 / 144 s，保留各 2.0 s 线性光 smoothstep；原 1.5 s 入淡与 193.4–197.2 s 尾淡。
- 音频来自官方 v2.5 发布件。全部 9,247 个包、AAC 配置、时戳、1024 样点 priming 和尾有效段全等，保留 9,467,200 样点与冬尾雪风。候审文件实际解码测得 **-16.05 LUFS-I / -4.74 dBTP**。

[春→夏](transition_48_spring_summer.jpg) · [夏→秋](transition_96_summer_autumn.jpg) · [秋→冬](transition_144_autumn_winter.jpg) · [入淡](fade_head_decoded.jpg) · [尾淡](fade_tail_decoded.jpg)。合成证据为正式封装后真解码读回，不是源帧或早期代理。

[实际输出验证](reproduction_qa.json) · [全幅静帧时间码](decoded_frame_manifest.json) · [一键生成说明](../../tools/gate3_v26/README.md)。

[独立终审前复验](INDEPENDENT_GATE36_QA.md) · [无参数重建记录](zero_arg_replay_proof.json)。

# Rainroji v2.5 · Gate 3.5 候审记录

- 终版 `Rainroji_Lofi_V2.5_1080p.mp4`，141,154,406 B，实测 SHA-256 `26bfaf99c36da141858249c2f07b520f61fa2a3b11eb1281972a79bf426d0cef`（当前工具链）；全解码 5,917 帧，30 fps，197.233333 s，实测 BT.709 限幅矩阵，High / CRF14，faststart。
- 唯一画源为 Round 20 审批的实际 17 份 Gate 2.5 QP0 分卷（1+8+2+6，不使用压缩预览）。实际编码输入 5917 张 RGB24 指纹 `ec41d7f865316a6a205e4471749dc7ee35a43952f18d72ab7235a5465f02315e`，与独立参考全同。
- 夏 F1470–2850、冬 F4350–5916 仍与 v2.4 编码前逐像素同一。三个正片转场中心 48 / 96 / 144 s，保留各 2.0 s 线性光 smoothstep；原 1.5 s 入淡与 193.4–197.2 s 尾淡。
- 音频来自官方 v2.4 发布件。全部 9,247 个包、AAC 配置、时戳、1024 样点 priming 和尾有效段全等，保留 9,467,200 样点与冬尾雪风。候审文件实际解码测得 **-16.05 LUFS-I / -4.74 dBTP**。

[春→夏](transition_48_spring_summer.jpg) · [夏→秋](transition_96_summer_autumn.jpg) · [秋→冬](transition_144_autumn_winter.jpg) · [入淡](fade_head_decoded.jpg) · [尾淡](fade_tail_decoded.jpg)。合成证据为正式封装后真解码读回，不是源帧或早期代理。

[实际输出验证](reproduction_qa.json) · [全幅静帧时间码](decoded_frame_manifest.json) · [一键生成说明](../../tools/gate3_v25/README.md)。

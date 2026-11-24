# Gate 3.1｜v2.1 成片独立复核

**本地成片通过独立核查，可交最后实片验收。** Rainroji_Lofi_V2.1_1080p.mp4，153,200,299 字节，SHA-256：692bf5cab708192337c9537d8abf95ed07aeef54dc63dd9a230cb9661e06d367。

- **画面：**1920×1080 / 30 fps / 5,917 帧 / 197.233333 秒。H.264 High、CRF 14、BT.709、yuv420p、faststart；完整实际解码，零报错、零漏帧、零额外重复帧。
- **唯一画面输入：**[bc09740 的已审批分卷](https://github.com/yiggeror/all-test-for-new-modle/tree/bc09740/previews/gate_2_1/lossless_parts) 逐个验哈希后重组，四季首周期共 1,320 张重算原生彩色帧与参考逐像素一致。先在 320×180 合成，再做 6× 最近邻整数放大。独立比对 222 张成片实际解码帧，未见额外边栏或覆盖字样。
- **叠化：**三处各 2.0 秒（47–49、95–97、143–145），中心严格 48／96／144 秒。在线性光空间混色，透明度保留官方 v2.0 实片的 smoothstep 缓入缓出；不是将时间权重改成直线。两版三处实解帧与四种可能模型各自对照，均吻合这一模型。片头 0–1.5 秒淡亮，片尾 193.4–197.2 秒淡黑。
- **原音轨：**直接沿用正式发布的 v2.0 音轨，9,247 个 AAC 包的内容、时戳、长度、首包预跳和解码配置逐项相同。48 kHz AAC-LC 立体声；实际解码 -16.04 LUFS，真峰值 -4.74 dBTP。全曲《Green Tea》、四季环境音与冬窗翻页保留，无重新压制。
- **实帧证据：**[春→夏](decoded_transition_spring_summer.jpg) · [夏→秋](decoded_transition_summer_autumn.jpg) · [秋→冬](decoded_transition_autumn_winter.jpg) · [片头片尾](decoded_fades.jpg) · [机器读数](QA.json)。

本文件记录本地实际复验，不代表已发布 GitHub Release 或 Google Drive。

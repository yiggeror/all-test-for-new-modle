# Rainroji v2.4 · Gate 3.4 成片审阅

仓库根目录运行 **python tools/gate3_v24/reproduce.py**，无参数实跑生成 dist/Rainroji_Lofi_V2.4_1080p.mp4：**132,850,666 字节**，SHA-256 **81297609f124b90bcbc97533a0a9514179a7681fb66a0c05903b277a973229ae**。此处仅送审，最终发布由评审完成。

- [技术验片](reproduction_qa.json)：16 个审批无损分卷；夏八卷与 v2.3 全部相同。真解原生 5,917 帧序列与独审哈希一致，30fps PTS 全量无失。1920×1080、High CRF14、BT.709 限幅、faststart，197.233333 秒。中心 48 / 96 / 144 秒的线性光 smoothstep 与首尾淡入出保持锁定。
- [实解码三段转场](encoded_transition_storyboard.jpg) 与 [22 个原幅时间点](decoded_frame_manifest.json) 都来自实际候审视频。单看春猫和暮鸟、夏灯与红反光、秋细叶和暖树影、冬横幅和翻页的帧号见 [动作索引](art_cue_map.json)。
- [旧尾声试听](tail_before.flac) / [新尾声实解试听](tail_after_encoded.flac)：三个等长片段都从正片 3:00 起。建议同音量按顺序听。前者是旧配方的冻结 PCM，后者与实际成片 AAC 解码在 24-bit FLAC 量化精度内一致；另有 [编码前新混音](tail_after.flac)。[封装后试听读回证明](tail_final_mux_readback.json)。
- [分轨能量图](tail_energy.png) / [逐窗数据](tail_energy.csv) / [实际重新混音报告](audio_tail_report.json)：完整《Green Tea》实际从 191.268 秒进入数字静默，不另剪歌。旧配方前 185 秒 PCM 逐位一致；只对沿用的暖低通冬底做渐强，顶段对185秒前提升 **8.28 dB**，翻页声音和早段不搬时、不推强。194.5–197.2 秒的最后2.7秒收淡。
- 正片新混音 48kHz 双声道 AAC-LC / 256 kbps 编码目标。9247个包由真实新混音轨完整流复制入成片，实测 **-16.05 LUFS-I / -4.74 dBTP**，无削波；音画有效时长同为 5917/30 秒。

[配乐署名](../../CREDITS.md) ｜ [确定性一键工具](../../tools/gate3_v24/)

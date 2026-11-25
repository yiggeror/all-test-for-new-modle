# Gate 3.7 · Rainroji 四季短片审片

成片由 Round 27 签收的 16 份无损分卷重新装配。秋景只换读书人和接地影：她站立靠树，发梢随风起落，约 1:39.5–1:41.0 轻翻一页。春、夏、冬、秋景其余动态与 v2.6 一致。三处叠化点在 0:48、1:36、2:24，片长 3:17.233，音轨沿用 v2.6 的原 AAC-LC 包。

- `review_autumn_1080p_1x.mp4`、`review_autumn_reader_4x_1x.mp4`：同一段成片 1:37–1:48 的 11 秒原速审片。近景保留树干、双脚和地面。
- `reader_v26_v27_decoded_compare.png`：上排 v2.6、下排 v2.7，从两部实际封装的 1080p 视频中取同相位未加字证据。列为 F2940、F2985、F2995、F3000、F3005、F3010、F3030。
- `encoded_transition_storyboard.jpg`：三个转场的解码抽帧；`decoded_*.png` 为全部 34 张 1920×1080 无叠字画面，时间与文件 SHA-256 见 `decoded_frame_manifest.json`。
- `reproduction_qa.json`：记录逐卷恢复、预编码时域锁、输出参数、响度与音频包核验。原生 RGB 证据与实际编码后抽帧分开列出，另有独立原生比较与封装后有损对照报告。
- 原版构建见 [tools/gate3_v27](../../tools/gate3_v27/)。主输出 `dist/Rainroji_Lofi_V2.7_1080p.mp4`；上述短片只供审片。


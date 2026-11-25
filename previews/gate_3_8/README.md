# Gate 3.8 · Rainroji 四季短片终审材料

取自 Gate 3.8 完整成片。四季时长、转场与音轨沿用上一版；变化集中于冬夜值班室暖窗。

- `review_winter_1080p_1x.mp4`：1920×1080 原速全景，按成片 F4384–F4713 直接截取，含成片同步声音。
- `review_winter_reader_5x_1x.mp4`：同一段直接从成片取完整暖窗，含人物、书、桌与台灯；整数放大、原速原声。对应翻页拟音中心为成片 **F4446 / F4459**（148.200 / 148.633 秒）。
- `reader_v27_v28_decoded_compare.png`：上排 v2.7 正式成片，下排 v2.8 成片候选；同一机位与帧号，自冬景局部相位 f120 至 f212 每隔 4 帧取一格。
- `encoded_transition_storyboard.jpg`：三处转场的实际解码帧；各张 `decoded_*.png` 为成片直出的 1080p 无文字抽帧，含冬景捻角、翻至书脊、压平和收手。
- `independent_input_comparison.json`：锁定 16 个 Git 审批分卷，独立核对冬景外不变和整片预编码时间域。
- `reproduction_qa.json`、`build_checks.json`：一键构建、输出规格、完整 AAC-LC 包及 PCM 比对、复验散列。图/音时码见 `art_cue_map.json`、`review_clip_manifest.json`。

重建入口：[tools/gate3_v28](../../tools/gate3_v28/README.md)。完整候选为 `dist/Rainroji_Lofi_V2.8_1080p.mp4`；该目录不包含 Release 成品。

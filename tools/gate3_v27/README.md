# Rainroji v2.7 · 四季成片

本版以 Gate 2.7 通过复审的秋景读书人替换旧人物。春、夏、冬、秋景其余层和原音轨不变。时长为 3 分 17.23 秒。

## 重建

检出 [Round 27 复审记录](https://github.com/yiggeror/all-test-for-new-modle/blob/151ce2503554dd299837236b6b6dd188e2912527/REVIEW_LOG.md) 与 `previews/gate_2_7/lossless_parts/`。需要 Python 3.12+、带 libx264 的 FFmpeg 与 ffprobe、`dist/` 约 850 MB 可用空间。

```sh
python -m pip install -r tools/gate3_v27/requirements.txt
python tools/gate3_v27/reproduce.py
```

成片写入 `dist/Rainroji_Lofi_V2.7_1080p.mp4`，解码静帧、转场表和复验记录写入 `dist/gate3_v27_qa/`。加 `--keep-picture` 可同时保留视频轨。默认获取已发布的 v2.6 MP4，按原包复制音轨。有本地缓存可加 `--v26-release-cache <MP4路径>` 或设置 `RAINROJI_V26_RELEASE_CACHE`。流程校验来源文件为 141,458,386 字节，SHA-256 为 `22e4039aff0e886323632568efe34a4d91c308f7f9ca45bd8ba904713d58e565`。

## 画面和音轨

- 只从审批提交 `898b3d17cdb8f242f741dfeb63c8bfde0f5594d1` 的 16 份无损分卷恢复画面。春 1、夏 8、秋 1、冬 6。清单 SHA-256 为 `91452eabd3a46117defa2c6ff48c5535d9ecca3049ff30725184b38eb5662292`；每季还原双周期 660 帧，按已锁定的有限色表精确恢复单周期 320×180 RGB。
- 48 / 96 / 144 秒各进行 2 秒线性光 smoothstep 叠化；开头 1.5 秒淡入，末尾 193.4 到 197.2 秒淡出。实际进入编码器的 RGB 逐帧对照，F0–2850 与 F4350–5916 和 v2.6 完全一致。随后 6× 最近邻放大，输出 1920×1080 / 30 fps / 5917 帧，H.264 High、CRF 14、BT.709、faststart。不同的 FFmpeg / libx264 组合可能产生不同的 MP4 字节，帧内容输入与时间不变。
- 保留原音轨的 9,247 个 AAC-LC 包，核对载荷、PTS / DTS / 时长、解码配置、起始 priming 样点和末包有效区间；旧版和新版有效解码 PCM 的哈希相同。音轨含 Purrple Cat 的《Green Tea》、四季环境声、冬窗翻页及尾声雪风。音乐署名见 `CREDITS.md`。

```sh
python -m unittest discover -s tools/gate3_v27 -v
```

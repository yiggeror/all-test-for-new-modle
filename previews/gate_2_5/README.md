# 四季像素短片 · Gate 2.5 样片

四套预览均为 1920 × 1080、30 fps、22 秒，串接两个 11 秒循环。夏、冬预览和无损分卷直接复用 Gate 2.4 的相同 Git blob。春、秋保留原机位与像素网格。
春夜小猫一直留在院内，两条弧线往返；秋日看报人和地面卷叶融入原有街景。枝干、招牌与电线保持固定。




## 下载和审片

- 直接播放：[春](spring_loop.mp4) · [夏](summer_loop.mp4) · [秋](autumn_loop.mp4) · [冬](winter_loop.mp4)
- [春景核查说明](qa/SPRING_NOTES.md) · [原画关键帧](peaks/) · [全周期独立复核](qa/GATE25_INDEPENDENT_QA.md) · [源码](source/)
- 无损分卷：下载本目录及 `lossless_parts` 后执行 `python3 tools/restore_lossless.py --out-dir gate25_lossless`，按清单检验、合并四套 QP0。无需重编码。

这是动作样片审片阶段；本轮正式成片尚未合成。

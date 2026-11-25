# 四季像素短片 · Gate 2.5 · Round 19 返工样片

四季均为 1920 × 1080、30 fps、22 秒，包含两个 11 秒循环。[第 19 轮审片反馈](https://github.com/yiggeror/all-test-for-new-modle/blob/d4cde25ec35477c8585cd0d6b17d4c742c17c982/REVIEW_LOG.md#L762-L807) 只要求返工春猫和秋景看报人。夏冬、春秋整冠风、秋景落叶和原有场景层原样保留。

## 先看 1080p 原速全景

- [春景](spring_loop.mp4) · [夏景](summer_loop.mp4) · [秋景](autumn_loop.mp4) · [冬景](winter_loop.mp4)
- 春景右下小猫沿暖地做错开的横弧往返，停一下抬头再折返。看 [4× 原速双周期](qa/spring_cat_two_cycles_4x.mp4) 或 [配套核查](qa/SPRING_NOTES.md)。
- 秋景左下报刊亭前，人物低头在胸前托报，约 0:05 一角掀起、跨过中缝后落下。看 [4× 原速翻页](qa/autumn_reader_normal_speed_detail.mp4)。
- [Round 19 独立核查](qa/GATE25_ROUND19_INDEPENDENT_QA.md) · [Round 18 已锁定的风和落叶原始证据](https://github.com/yiggeror/all-test-for-new-modle/blob/3826dec8fdcbc07b0ad22ea96747b0444ed5e811/previews/gate_2_5/qa/GATE25_INDEPENDENT_QA.md) · [关键帧](peaks/) · [源码归档](source/)。

下载本目录及 `lossless_parts` 后执行 `python3 tools/restore_lossless.py --out-dir gate25_lossless`，可按清单校验并合并四套 QP0，无需重编码。

本次仅重交动作样片；待评审放行后合成 Gate 3.5。

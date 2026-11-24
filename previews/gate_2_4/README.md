# Gate 2.4 · 四季循环样片

按 [Round 15 / 补充要求](../../REVIEW_LOG.md) 在 v2.3 原片上打磨。每个场景是 11 秒循环的连续两轮（22 秒、1920×1080、30 fps）。本轮先核画面，不含音乐；尾声混音待 Gate 3.4。

- [春](spring_loop.mp4)：整冠双侧落花、局部整数像素叶颤、院内小猫、暮空归鸟和旧灯短促降亮；晾衣沿用 v2.3。
- [夏](summer_loop.mp4)：代理及八个无损分卷逐字节沿用 Gate 2.3，正片 SHA-256 为 `a26523e1ec77ccc303769997d4b965de0fdfc08fe300efe2e60550f86d12916c`。
- [秋](autumn_loop.mp4)：双冠叶簇微动、左右各 22 片空中落叶、与叶颤同步的局部暖光；卷叶、茶汽和归鸟延续 v2.3。
- [冬](winter_loop.mp4)：只动细枝和横幅中下部，粗干和布旗两端不动；老灯压降联动灯晕与雪，旧楼空墙不再出现假灯。

`peaks/` 为原幅关键帧，`qa/` 为运动热图、逐相位核查和放大条带，`source/` 为本轮源包。上面的 MP4 为兼容预览。QP0 正片可使用 `python previews/gate_2_4/tools/restore_lossless.py --out-dir gate24_lossless` 复原，脚本核验分卷与合并后的完整哈希。

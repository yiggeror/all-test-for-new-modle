# Rainroji · v2.3 / Gate 2.3 像素动态返工送审

本批对应 [Round 12](https://github.com/yiggeror/all-test-for-new-modle/blob/16951626d5db44eacf6ac0f9b52caf80cafd2a5b/REVIEW_LOG.md)。只交四幕审片；未做 Gate 3.3 合片，不修改已发行的旧版。

## 先按原速看双周期

[春](spring_loop.mp4) · [夏](summer_loop.mp4) · [秋](autumn_loop.mp4) · [冬](winter_loop.mp4)

页面上方为兼容审阅副本：1920×1080、30 fps、22 秒，11 秒处是第一周期的接缝。看细节请取下方无损正本，附图与技术证据用实际冻结原生或解码帧生成。

| 场景 | 原尺寸 1080p 实解码峰值 | 全 330 帧热图及局部连续证据 |
| --- | --- | --- |
| 春：整树静止，只动落瓣与 6 fps 挂布 | [静止 F015](peaks/spring_peak_015_calm_no_cat.png) · [落瓣 F180](peaks/spring_peak_180_blossom_shower.png) · [晾布 F195](peaks/spring_peak_195_washing_billow.png) | [热图](qa/spring_motion_heatmap.png) · [树](qa/spring_adjacent_fixed_tree.jpg) · [布](qa/spring_adjacent_cloth.jpg) · [瓣](qa/spring_adjacent_petals.jpg) |
| 夏：真实逐帧车灯、纤细雨滴、四次霓虹硬闪 | [湿路 F124](peaks/summer_headlight_road_F124.png) · [车侧 F153](peaks/summer_headlight_car_face_F153.png) · [檐滴 F071](peaks/summer_rain_eave_drop_F071.png) · [亮 F190](peaks/summer_neon_wet_road_F190.png) / [暗 F194](peaks/summer_neon_dark_comparison_F194.png) | [热图](qa/summer_motion_heatmap.png) · [湿路](qa/summer_adjacent_wet_115_132.jpg) · [车](qa/summer_adjacent_car_143_158.jpg) · [檐滴](qa/summer_adjacent_eave_065_078.jpg) · [前后对比](qa/summer_v22_v23_effect_comparison.jpg) |
| 秋：树和钠灯固定，空中与地面叶、暖汽和小归鸟分层 | [空中叶 F123](peaks/autumn_aloft_f123_1080p.png) · [归鸟 F152](peaks/autumn_bird_wings_f152_1080p.png) · [贴地叶与暖汽 F178](peaks/autumn_roll_and_vapor_f178_1080p.png) | [热图](qa/autumn_motion.png) · [贴地叶](qa/autumn_rolling_strip.png) · [暖汽](qa/autumn_steam_strip.png) · [暮鸟](qa/autumn_birds_strip.png) |
| 冬：整树与居民窗固定，保留翻页、雪和暖烟 | [暖窗 F153](peaks/winter_warm_window_f153_1080p.png) · [翻页 F165](peaks/winter_page_f165_1080p.png) · [雪 F220](peaks/winter_snow_gust_f220_1080p.png) | [热图](qa/winter_motion.png) · [固定远楼窗](qa/winter_facade_strip.png) · [翻页](qa/winter_page_strip.png) · [枝梢雪粉](qa/winter_powder_strip.png) |

## 无损正本、出处及核查

在仓库根目录运行，拼接正本不转码、逐卷验 SHA-256：

    python previews/gate_2_3/tools/restore_lossless.py --out-dir gate23_lossless

[分卷清单](lossless_parts/MANIFEST.json) · [实际恢复比对](qa/lossless_restore.json) · [制作核查](qa/PRODUCTION_QA.md)
 
[春源](source/spring_v23_source.zip) · [夏源](source/summer_v23_source.zip) · [秋冬源](source/autumn_winter_v23.zip)。原件为两次 330 帧周期，320×180 原生以 6× 最近邻整数放大，H.264 QP0 / yuv420p / BT.709 限幅。各源包以 README 说明依赖、参数和复现命令。

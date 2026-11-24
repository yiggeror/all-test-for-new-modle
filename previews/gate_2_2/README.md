# Rainroji · v2.2 / Gate 2.2 四季返工审片

本提交对应 [Round 9](https://github.com/yiggeror/all-test-for-new-modle/blob/4c06e29619b2efa6ed8c4f9b75888417d91a4bb7/REVIEW_LOG.md)。沿用原世界比例、机位和景物，舍弃退回版 v2.1 的违和角色和机械特效。仅交四季制作样片，不合整片，不改动旧版或正式发行。

## 以 1× 看完整 22 秒

[春](spring_loop.mp4) · [夏](summer_loop.mp4) · [秋](autumn_loop.mp4) · [冬](winter_loop.mp4)

页面上方是 1920×1080、30 fps 的手机兼容审片，各自 22 秒。看完两个完整 11 秒周期，确认动作、轮廓与 11.00 秒接缝。精确像素与无损证据用以下原件。

| 场景 | 应看的动作 | 1920×1080 全画幅峰值，取自实际候审正本 |
|:--|:--|:--|
| 春 · 老巷暮色落花 | 挂布承重处和固定，衣角随风；花冠和灯下斜落花瓣各自有深度 | [挂布 F203](peaks/spring_peak_203_washing_billow.png) · [花瓣峰 F186](peaks/spring_peak_186_blossom_shower.png) · [屋脊和车把静证 F105](peaks/spring_peak_105_roof_no_cat_neutral.png) |
| 夏 · 雨夜街角小店 | 画外双灯扫右侧湿路、低墙及红车侧；红霓虹雨滴碎斑、四次三处同闪 | [湿路扫光 F124](peaks/summer_headlight_road_F124.png) · [真实车侧受光 F153](peaks/summer_headlight_car_face_F153.png) · [霓虹高 F190](peaks/summer_neon_wet_road_F190.png) · [霓虹低 F194](peaks/summer_neon_dark_comparison_F194.png) |
| 秋 · 梧桐黄昏大道 | 梧桐冠阵风、枝间钠灯、秋叶卷过斑马线；报亭暖汽透亮 | [冠/灯 F122](peaks/autumn_canopy_f122_1080p.png) · [阵风 F178](peaks/autumn_gust_f178_1080p.png) · [斑马线落叶 F201](peaks/autumn_leaves_f201_1080p.png) |
| 冬 · 雪夜家属院 | 改后暖窗翻页与灯距；暖灯雪涡、细枝落粉，雪人与石凳间清静 | [楼道灯 F095](peaks/winter_stairs_f095_1080p.png) · [暖窗 F164](peaks/winter_page_f164_1080p.png) · [雪风 F214](peaks/winter_snow_gust_f214_1080p.png) |

## 一键取回无损原件

在仓库根目录运行，离线。逐片验字节数和 SHA-256，再验完整正本；不转码。四个正本是 330 张 320×180 RGB 原生帧各循环两次，严格 6× 最近邻整数放大。H.264 lossless QP0 / yuv420p / BT.709 limited。

```bash
python previews/gate_2_2/tools/restore_lossless.py --out-dir gate22_lossless
```

[分卷与 SHA-256](lossless_parts/MANIFEST.json) · [恢复比对报告](qa/lossless_restore.json) · [制作复现核验](qa/PRODUCTION_QA.md)

## 有据的制作源

[春](source/spring_v22_source.zip) · [夏](source/summer_v22_source.zip) · [秋冬](source/autumn_winter_v22.zip)。均有根位 README、原场景来源和命令。不是把 v2.1 成片裁成动画：春从分层光追几何再算动态三角网与真实暖光，夏把运动算在有真实反射及阴影的世界面上，秋冬沿已锁渐层光与深度构建各自新动作。

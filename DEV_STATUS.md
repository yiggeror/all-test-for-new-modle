# 四季像素短片 v2 · 制作进度

**Gate 1：静帧候选已渲染，待评审。** 尚未选定 A/B；未开展 Gate 2 动态样片、音画混合或完整影片。对应需求版 `473786ad`，原型渲染源码来自 `yiggeror/Rainroji@d3fff8c`。

## 先看整体，再看像素

- [A 四季总览：320×180 → 1080p（6×）](previews/gate_1/overview_A_320x180.png)
- [B 四季总览：384×216 → 1080p（5×）](previews/gate_1/overview_B_384x216.png)
- [同机位 1:1 A/B：春](previews/gate_1/spring_comparison.png) · [夏](previews/gate_1/summer_comparison.png) · [秋](previews/gate_1/autumn_comparison.png) · [冬](previews/gate_1/winter_comparison.png)

| 季节 | A 1080p 净图 | B 1080p 净图 | 后续动作落点 |
|---|---|---|---|
| 春 · 老巷 | [A](previews/gate_1/spring_320x180_1080p.png) | [B](previews/gate_1/spring_384x216_1080p.png) | [门楼瓦脊睡猫、暖灯区小蛾](previews/gate_1/spring_motion_note.png) |
| 夏 · 雨夜 | [A](previews/gate_1/summer_320x180_1080p.png) | [B](previews/gate_1/summer_384x216_1080p.png) | [雨棚边缘滴水、内侧避雨剪影](previews/gate_1/summer_motion_note.png) |
| 秋 · 梧桐 | [A](previews/gate_1/autumn_320x180_1080p.png) | [B](previews/gate_1/autumn_384x216_1080p.png) | [左侧热茶水汽、天空缝里的远鸟](previews/gate_1/autumn_motion_note.png) |
| 冬 · 家属院 | [A](previews/gate_1/winter_320x180_1080p.png) | [B](previews/gate_1/winter_384x216_1080p.png) | [右上暖窗翻页、院中小棚白汽](previews/gate_1/winter_motion_note.png) |

## 构图调整

- 春：粉花树与门楼压近成一组，左侧砖墙和旧自行车作另一层，暖灯不被花冠吃掉。
- 夏：把取景从远广角收回小卖部、理发柱和红车；下移并减弱左侧路灯，保住右侧巷口，网吧红灯与路面倒光同组。
- 秋：双侧树冠作夹景，斑马线从下沿把视线送向粉紫夕雾。左边只留近处报刊亭的暖光作层次。
- 冬：枯树移到左侧约 22%，左暖右冷；右侧雪人挪近镜头，石凳与暖窗一前一后，不靠加大雪雾制造氛围。

每场 A/B 独立从 3D 世界重渲，同一视口与时相，共用 60 色色板；导出通过逐像素整数复制，原生图、净图、色卡、标注图分别保存。制作测试结果与复现见 [REPRO.md](REPRO.md)。色板条也在 1:1 A/B 对照内，净图上无说明字。

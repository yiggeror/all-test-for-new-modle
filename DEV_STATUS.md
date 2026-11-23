# 四季像素短片 v2 · 制作进度

## 当前：Gate 2 四季循环与配乐送审

已根据 [Round 2](https://github.com/yiggeror/all-test-for-new-modle/blob/9e49b969e8b549c39f947c1fd8e3783d170bfc40/REVIEW_LOG.md) 进入动态阶段。锁定 320×180 原生作画，6× 最近邻、1920×1080 @30 fps。每季单循环 11 秒、330 帧，样片两周期，共 660 帧 / 22 秒。此次提交供动态与配乐评审，总装尚未开始。

[四季动态样片](previews/gate_2/) · [配乐候选和音画试配](previews/gate_2/MUSIC_SHORTLIST.md)

- 春：轻摆尾尖、暖光勾耳背；保留落花、树冠微风、电视光，加入小蛾暖点。
- 夏：横向雨波拆散红灯箱倒影，红灯箱与倒影相位同步；保留坐猫尖耳、檐滴、湿地涟漪与理发柱。
- 秋：暖汽避开亮货架，从左侧暗暖背景前升起；远鸟一次掠过，隐入右侧树冠；叶团静区与柔和电视光按周期衔接。
- 冬：暖窗中人物大部分时间伏案，每周期只做一次翻页；烟、逐层灯和穿光落雪持续但不抢画面。

完整无损原件可从仓库分片按 [清单及校验命令](previews/gate_2/README.md#无损原件) 恢复。仓库中直接打开的 MP4 是从同一原件转出的 H.264 High 兼容审看版。原件与代理的检查结果均附在 [复验记录](previews/gate_2/qa/)。

## 历史：Gate 1.5 精修静帧

依据 [Round 1 评审 `0afc93d`](https://github.com/yiggeror/all-test-for-new-modle/blob/0afc93d133023b3952d826f100e82397c6ec6c29/REVIEW_LOG.md)，本轮只交 **320×180 原生 / 6× 整数放大 / 1920×1080 静帧**。本轮静帧已获 Round 2 评审通过；首轮 A/B 也保留作对照。

- [本轮四季总览](previews/gate_1_5/overview_gate_1_5.png)
- 春：[1080p](previews/gate_1_5/spring_320x180_1080p.png) · [动作位置](previews/gate_1_5/spring_motion_note.png)
- 夏：[1080p](previews/gate_1_5/summer_320x180_1080p.png) · [动作位置](previews/gate_1_5/summer_motion_note.png)
- 秋：[1080p](previews/gate_1_5/autumn_320x180_1080p.png) · [动作位置](previews/gate_1_5/autumn_motion_note.png)
- 冬：[1080p](previews/gate_1_5/winter_320x180_1080p.png) · [动作位置](previews/gate_1_5/winter_motion_note.png)

**本轮制作记录：**

- 春：给砖楼和花树上方腾出暮空；把路灯暖金光带推到粉花、旧砖和地面；瓦脊上加入实体静态卧猫供位置、体量和轮廓复核。
- 夏：去掉水面死白镜面亮斑，分别处理米黄店光与右下拆成条段的红霓虹水面反光；店招回调为暖米黄底和深色笔划；把堵路棚后移回巷内；猫移入灯下货架的前缘，采用静态轮廓。
- 秋：收拢两侧树冠的叶团，扩大粉紫暮空空间；移开斜切报刊亭的枝条；标清左下热汽、上方归鸟的位置。
- 冬：分开前景树和道旁灯杆，移除室外方块人；移树、后撤旧棚并将新值班室暖窗放在右中景，窗口原生投影约 23×17 像素。窗内已有低头伏案、书和台灯的静态轮廓，在静帧阶段仅确认位置；动态翻页与白汽见 Gate 2。

配乐预研已整理候选，正式配画与试听对比见 Gate 2。复现方法见 [REPRO.md](REPRO.md)。

## 历史：Gate 1 A/B 对照

**Gate 1：已评审并选定 A。** 保留原始候选作前后比较。对应需求版 `473786ad`，原型渲染源码来自 `yiggeror/Rainroji@d3fff8c`。

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


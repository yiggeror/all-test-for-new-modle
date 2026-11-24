# 四季像素短片 v2 · 制作进度

## Round 7：Gate 2.1 已通过，Gate 3.1 本地成片待终审

[Round 7](https://github.com/yiggeror/all-test-for-new-modle/blob/bc10313a30fab60fef6672b212b1bcc18893d5f3/REVIEW_LOG.md) 已通过四季动效样片。本轮使用 `previews/gate_2_1/lossless_parts/` 的正本直接恢复 320×180 RGB，按已审 v2.0 的线性光叠化曲线与 48／96／144 秒中心合成，然后严格 6× 最近邻放大，仅一次 CRF 14 画面编码。没有读取有损预览代理。

**本地候审成片** `Rainroji_Lofi_V2.1_1080p.mp4`：153,200,299 字节，SHA-256 `692bf5cab708192337c9537d8abf95ed07aeef54dc63dd9a230cb9661e06d367`；1920×1080、30 fps、5,917 帧、197.233333 秒。完整保留经 v2.0 正式发布签收的 9,247 个 AAC 包（Purrple Cat《Green Tea》、原四季环境及翻书拟音），实测 −16.04 LUFS、−4.74 dBTP。全解码与首尾节奏验核通过。

在仓库根目录运行 `python tools/gate3_v21/reproduce.py`。脚本独立于原 v2.0 目录，核分卷、原生帧和官方 v2.0 下载文件，音频仅流复制，并再次核 AAC 包与采样时码。[重建说明](tools/gate3_v21/) · [转场实解码抽帧](previews/gate_3_1/encoded_transition_storyboard.jpg) · [独立核查与分转场实帧](previews/gate_3_1/QA.md) · [制作与编码核查](previews/gate_3_1/production_QA.md)。

[干净工作副本零参数重建](previews/gate_3_1/one_click_verified.json) 实际通过；重建 MP4 与本地候审件在同一工具链下逐字节相同。

本轮只提交复现工具、技术核查和审看片，不修改 v2.0 Release、Drive 或原片；v2.1 正式双渠道留待终审通过后的同文件发布。

## Round 6：Gate 2.1 四季动效样片已制作，等待 1× 审看

保留已签收 v2.0；这轮不合片，不动正式 Release、Drive 或原配乐。四季仍使用冻结机位、320×180 原生、6× 最近邻、11 秒一循环。

本轮提交 [四季动效审片、正本分卷与复现源](previews/gate_2_1/)：

- **春：**门楼睡猫抬头跟视、两次扫尾后伏下；自行车车把暖棕麻雀短跃两次、低头轻啄；四只暖金灯蛾绕灯扩轨。
- **夏：**棚下花猫抬爪洗脸、摆尾，暖色檐滴与落点涟漪加强，理发柱三色缓转。红霓虹 **6.40–7.80 秒**集中跳暗四次（30 fps 帧 `[192,197)` / `[204,209)` / `[216,220)` / `[229,234)`，亮度 **22% / 24% / 21% / 23.5%**）；同一增益驱动灯字、邻墙和湿路横纹，实帧核查四组同起同落。
- **秋：**左侧三只觅食鸟错拍蹦啄、扬翅回步；四只归鸟、约 20–23 px 暖汽、四片贴地金叶过斑马线。
- **冬：**暖栗胖鸟从雪人帽短飞到石凳再返落，先歪头抖雪；保留原 4.30–6.90 秒翻书窗口，书页反光更清楚；烟囱淡烟连贯，楼梯四层灯错拍亮灭。

**技术核查：**每季 1920×1080、30 fps、22 秒双周期；正本的 660 帧解码对 6× 原生转换逐帧相等，第二周期 330/330 同首周期；`329→330` 没有重复尾帧。GitHub 顶层 MP4 是兼容审片副本，精确块、哈希及无损原件用 [分卷还原](previews/gate_2_1/README.md#直接看与无损核对)核对。通过本轮实看片后再安排 v2.1 最终合片与双渠道发布。

## Round 4：完成一键复现；双渠道发布尚未完成

[Round 4 评审](https://github.com/yiggeror/all-test-for-new-modle/blob/d49da1bf3adcc1abb409005e1f7173232e748a8c/REVIEW_LOG.md)确认成片参数、转场抽帧和署名，要求补双渠道实体交付。当前两个渠道都没有取得完整原片的下载地址：

- **GitHub Release**：当前已连接的 GitHub 接口只能读取 Release，未提供创建 Release 或上传资产操作。GitHub CLI 实际返回 `You are not logged into any GitHub hosts.`，网页当前也未登录。目标 Release 查询返回 HTTP 404。
- **Google Drive**：提交 151,159,718 字节原片时，上传接口在执行前返回 `HTTPException: 413: File too large to download: 151159718 bytes exceeds the 104857600-byte limit.`。这是当前连接器的转运上限；本次未在 Drive 创建文件。

**仓库单命令复现**：`python tools/gate3/reproduce.py`。按 [重建说明](tools/gate3/README.md)准备工具链即可，不需要填任何路径。四季无损分卷与作者原曲会逐项校验；从干净仓库输入实跑得到 `dist/Rainroji_Lofi_V2_1080p.mp4`，与验收母版逐字节一致。该方案交付完全相同的一个 MP4，不降低画质、也不需要现成的预览视频。
SHA-256：`0213513d08d439c965ef7320b2d896814733fac404d2dc6ddfeac4c122da60ba`。见 [实跑报告](previews/gate_3/reproduction_qa.json)。

依据 [Round 3](https://github.com/yiggeror/all-test-for-new-modle/blob/2ba3d65f4bab7a6fd479a662b369858ddaeb9572/REVIEW_LOG.md) 完成最终总装。从四个冻结的 320×180 RGB 序列直接合成，6× 最近邻，最终一次 CRF 14 高质量编码。春、夏、秋、冬顺序，完整保留《Green Tea》；三个叠化中心 48 / 96 / 144 秒，各 2 秒。

独立复验：最终 MP4 全解码 5,917 帧，连续 30 fps，0 丢帧、0 重复，H.264 与 AAC 压缩包和两条母轨逐包一致。成片约 3 分 17.23 秒，−16.04 LUFS、−4.74 dBTP。详见 [交付参数](DELIVERY.md)、[逐帧图](previews/gate_3/encoded_transition_storyboard.jpg)、[独立复验](previews/gate_3/QA.md) 和 [署名](CREDITS.md)。对外托管完成并核验后，在交付页补正式链接。

## 历史：Gate 2 四季循环与配乐送审

已根据 [Round 2](https://github.com/yiggeror/all-test-for-new-modle/blob/9e49b969e8b549c39f947c1fd8e3783d170bfc40/REVIEW_LOG.md) 进入动态阶段。锁定 320×180 原生作画，6× 最近邻、1920×1080 @30 fps。每季单循环 11 秒、330 帧，样片两周期，共 660 帧 / 22 秒。本轮已评审通过，选定完整《Green Tea》。

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



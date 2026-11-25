# 四季像素短片 v2 · 制作进度

## Round 27：v2.7 / Gate 3.7 四季完整合片候审

依据[第 27 轮放行](https://github.com/yiggeror/all-test-for-new-modle/commit/151ce2503554dd299837236b6b6dd188e2912527)，用已批准的 16 份 Gate 2.7 无损分卷还原画面。新版秋景保留了倚树读书人的自然站姿、飘发和翻页；春、夏、冬及秋景非人物层不变。

- 候审成片：1920×1080，30 fps，5,917 帧，197.233333 秒；H.264 High CRF 14、BT.709、faststart。保留 48/96/144 秒中心的 2 秒线性光叠化、1.5 秒片头淡入、3.8 秒片尾淡出。
- 实际送入编码器的原生 RGB 画面与独立复核一致，开头至 F2850、F4350 至结尾与 v2.6 逐像素相同；差异限于秋景人物及其投影，包括秋景参与的两段叠化。
- 直接复制 v2.6 正式成片的 AAC 音轨。9,247 个包及有效的 9,467,200 个音频样点均与已发布版本一致。
- [无参数复现流程](tools/gate3_v27/) · [成片解码抽帧与审片资料](previews/gate_3_7/)。

本次提交用于最终审片，正式发布见后续交付记录。

---

## Round 26：v2.7 / Gate 2.7 秋景人物候审

本轮只重做秋景倚树读书的人物。站姿由屈膝前顶改为一侧肩背轻倚、承重腿顺直，头颈与肩背对齐，外套和半裙恢复各自轮廓。长发随同一阵秋风扬起、回落；手和书移到身前，从抬页到落回书边保持连贯，约第 5 秒可见。

- [秋景 1080p 原速循环](previews/gate_2_7/autumn_loop.mp4) · [人物原速放大](previews/gate_2_7/autumn_girl_normal_speed_detail.mp4)（保留树干、双脚及脚下地面）
- [四季原生无损分卷](previews/gate_2_7/lossless_parts/MANIFEST.json) · [秋景复现源码](previews/gate_2_7/source/autumn_v27.zip)

v2.6 正式版仍可下载。v2.7 本次提交为秋景阶段审片；其余三季与成片音轨沿用 v2.6。

---

## Round 24：v2.6 / Gate 3.6 完整四季合片候审

依据[第 24 轮放行](https://github.com/yiggeror/all-test-for-new-modle/commit/2b1f97a62d61b2375029e8ed32419890f6ade03f)，只从 (4496463) 批准的 16 份 Gate 2.6 无损分卷复原画面，保留 48、96、144 秒三处线性光 2 秒叠化、1.5 秒片头淡入与 3.8 秒片尾淡出。成片始末及春夏冬没有新增改动。

- 候审成片 `Rainroji_Lofi_V2.6_1080p.mp4`：1920×1080、30 fps、5,917 帧、197.233333 秒；H.264 High CRF 14，BT.709，faststart。当前工具链生成 141,456,016 字节，SHA-256 `c193872a27cc2d0384429f86e3153711ebf9d878f3b7c5188e782098923c8931`。
- 实际送入编码器的 5,917 个原生 RGB 帧与独立逐帧轨迹一致。F0–2850（含首处叠化）和 F4350–5916 与 v2.5 逐像素相同；中间仅秋景与其参与的两处叠化更换。
- 沿用已发布 v2.5 音轨。实测 9,247 个 AAC 包逐包相同，9,467,200 个呈现样本逐位相同；保留配乐、环境声与冬夜尾声，-16.05 LUFS-I / -4.74 dBTP。
- [无参数复现场景](tools/gate3_v26/) · [实际成片时间码与真解码样张](previews/gate_3_6/)。秋景倚树少女的翻页在成片约 1:40。

本提交用于发布前的完整终审；正式 GitHub Release 与 Google Drive 随终审发布。

---

## Round 23：v2.6 / Gate 2.6 秋景少女画面精修重交

按[第 23 轮](https://github.com/yiggeror/all-test-for-new-modle/blob/eee3d38cd1ae9b3ed27a9b51c77288d228de47ce/REVIEW_LOG.md#L923-L967)，保留 v6 秋景的风、地面积叶、88 片浮叶以及少女靠树支点和收腿骨架。源码包仅 `reader25.py` 内容更新。

- 以原灯光衬浅燕麦外套、深色微伞摆裙与黑栗长发；暖窗前是发束、袖和页尖的轮廓，没有增加灯或脸部亮色。沿同一阵风做发束离身与回稳。
- 书本保持原尺度。翻手挑起并带过书脊，纸页角先从袖口与暗柜之间抬起，跨过后落回原位置。 [秋景双循环](previews/gate_2_6/autumn_loop.mp4) · [4× 原速](previews/gate_2_6/autumn_girl_normal_speed_detail.mp4)。
- 关闭新旧人物与实影后，330 个同相位原生画面逐像素相同；春夏冬 15 个原始无损分卷保持原 blob。其余锁定内容未改。

本次仅重送 Gate 2.6。通过后才合成 Gate 3.6；完整配乐与时长沿用 v2.5。

---

## Round 22–22c：v2.6 / Gate 2.6 秋景三项精修候审

对照[第 22 轮及 22c 补充](https://github.com/yiggeror/all-test-for-new-modle/blob/c005ce6e02e2a5be1927128216d3f3b120a71a57/REVIEW_LOG.md#L856-L930)，提交新版[秋景完整双循环](previews/gate_2_6/autumn_loop.mp4)（1080p30、660 帧，原生 320×180、6× 整数复制）。

- 将报刊亭前的岔腿读者改为靠着真实梧桐树皮的少女。双脚落地、腿窄收拢，保留既有暖光；一只手轻掀并带页越过书脊，发梢随同一阵风摇摆。[无标原速](previews/gate_2_6/autumn_girl_normal_speed_1080p.mp4) · [人物 4× 原速](previews/gate_2_6/autumn_girl_normal_speed_detail.mp4)。
- 删除人行道积叶的整块贴图偏移，改用 22 片世界坐标叶；22 片均取得原生逐叶可见证据，其中 18 片在 66 个状态中至少可见 34 个，12 条位移轨迹为 4.21–9.52 像素，原斑马线卷叶保留。[两侧人行道 4× 原速](previews/gate_2_6/autumn_ground_both_sides_4x_1x.mp4)。
- 替换秋冠平行斜波。全 330 帧真片同相位对照：整体每帧 10.00%–14.07%，并集 82.25%（物理叶冠 23,703 像素）；受保护树干、硬边零改动。分别关闭旧/新三处变更后，与已发布 v2.5 原始秋景共同底板逐像素相同。灯、茶汽、飞鸟、空中 88 片叶和斑马线原效果保留。[完整实测](previews/gate_2_6/)。
- 春、夏、冬 15 个分卷直接引用已发布 v2.5 的原 blob；秋景新 QP0 正本 SHA-256 `6af4c7f8d82fe9867e0e62ca1aa7ec8eabd27f4dea4976e845cdf7809534d652`。四季完整 [无损分卷清单](previews/gate_2_6/lossless_parts/MANIFEST.json)。

本次仅送审 Gate 2.6 秋景。待评审放行再合成 Gate 3.6，保持 v2.5 完整音轨与原时长。

---

## Round 20：v2.5 / Gate 3.5 1080p 成片候审

[Round 20 已通过四季样片](https://github.com/yiggeror/all-test-for-new-modle/blob/de0190b398d70b2cf39d82db9fe5a674fff45137/REVIEW_LOG.md#L807-L845)。从批准提交 `6ef7236d` 的清单恢复四季全部 17 个无损分卷（春 1、夏 8、秋 2、冬 6），没有读取网页预览或旧成片画面。

- 重建产物 `dist/Rainroji_Lofi_V2.5_1080p.mp4`：141,154,406 字节，SHA-256 `26bfaf99c36da141858249c2f07b520f61fa2a3b11eb1281972a79bf426d0cef`。1920×1080、30 fps、5,917 帧，197.233333 秒；H.264 High / CRF 14 / BT.709 限幅矩阵 / faststart。
- 保留 48、96、144 秒三处 2 秒线性光 smoothstep 叠化，片头淡入 1.5 秒、片尾淡出 3.8 秒。夏、冬纯景段的编码前 RGB，与 v2.4 分别逐像素相同。
- 直接复制已发布 v2.4 的 AAC 音轨。全 9,247 个包的内容与时序、48 kHz 立体声 9,467,200 个呈现样本均与官方成品完全一致；实测 −16.05 LUFS-I、−4.74 dBTP。
- [复现入口](tools/gate3_v25/) · [实际解码静帧](previews/gate_3_5/) · [独立复核](previews/gate_3_5/GATE35_INDEPENDENT_QA.md)。

本次提交用于云端重建和终审；GitHub Release 与 Google Drive 由评审发布。此前正式发布保持原样。

---

## Round 19：v2.5 / Gate 2.5 春猫与秋景看报人重交

按[第 19 轮审片意见](https://github.com/yiggeror/all-test-for-new-modle/blob/d4cde25ec35477c8585cd0d6b17d4c742c17c982/REVIEW_LOG.md#L762-L807)，仅修改两处角色动画。新版[春景](previews/gate_2_5/spring_loop.mp4)与[秋景](previews/gate_2_5/autumn_loop.mp4)均为 1080p30、22 秒双周期。

- 春猫在暖色庭院地面走两条错开的扁弧，以侧身、斜侧身为主，暖处短停抬头再折返。奶油灰毛背和深耳尾使用既有灯光下的实体材质，没有额外加灯或描边。重查旧回程 F250–310，实体头躯最窄仍有 6 个原生像素。
- 秋景人物双腿错站、短颈微低头，胸前双手托住展开的报纸。纸面落在暗围板和深外套前，单页依次上掀、翻过中缝、落平。
- 春、秋各 330 帧同相关闭角色及其影子与上一版逐像素一致；两季实际画面变化均局限于两版角色和影子的并集。夏、冬的预览与 14 个无损分卷直接复用原 Git blob。四季按最新清单恢复，复验码流。

[春猫 4× 正常速度](previews/gate_2_5/qa/spring_cat_two_cycles_4x.mp4) · [秋景翻报 4× 正常速度](previews/gate_2_5/qa/autumn_reader_normal_speed_detail.mp4) · [独立复核](previews/gate_2_5/qa/GATE25_ROUND19_INDEPENDENT_QA.md)。

待评审放行后合成 Gate 3.5，沿用 v2.4 音轨与 197.233333 秒原时长；v2.4 正式发布不动。

---

## Round 18：v2.5 / Gate 2.5 四季双周期样片送审

按 [Round 18](https://github.com/yiggeror/all-test-for-new-modle/blob/347e47c41b5c5ee19cbf0a289e1d96aac57d9fba/REVIEW_LOG.md#L688-L761) 提交[四季 1080p 样片与无损分卷](previews/gate_2_5/)。每季 22 秒、30 fps、660 帧，包含两个 330 帧循环。

- 春：全冠有效叶区 11,122 个原生像素。单帧同相比较（不含微压灯）变化 1,319–1,502 / 11,122（11.86%–13.50%）；全 330 帧累计为 7,908 / 11,122（71.10%），剔除微压灯帧为 7,890 / 11,122（70.94%）。树干、电线和硬边零位移。实光追小猫 330/330 帧在院内可见，探嗅暂停、走不同双弧往返，独立重渲 F330 与 F0 像素完全相同。原落花、远燕、晾衣、暖灯压降与蛾完整保留。
- 秋：独立复核双侧完整物理冠面 24,161 像素。非压灯单帧变化 2,657–2,916 / 24,161（11.00%–12.07%），全周期累计 17,874 / 24,161（73.98%）。站在报刊亭外的 3D 路人手持报纸、在暖光下翻一次，软影接地，招牌、主架与粗树干零覆盖。左右各 44 片有源空叶，另有 8 片沿路缘短滑后落稳。与 v2.4 同相隔离对照，旧滚叶、茶汽、归鸟、路灯、报刊亭与电视六层各 330 帧逐 RGB 相同。
- 夏冬：两条预览和全部 14 个无损分卷使用相同 Git blob，不重新生成。四季均从清单恢复并逐帧解码核查。

[春景猫 4× 正常速度](previews/gate_2_5/qa/spring_cat_two_cycles_4x.mp4) · [秋景翻报 4× 正常速度](previews/gate_2_5/qa/autumn_reader_normal_speed_detail.mp4) · [独立证据与测试](previews/gate_2_5/qa/)。

本次仅提交 Gate 2.5。待评审放行后合成 Gate 3.5，沿用 v2.4 音轨与 197.233333 秒原时长；现有 v2.4 正式发布不动。

---

## Round 16：v2.4 / Gate 3.4 成片已合成，待实看实听终审

按[终审前合片要求](https://github.com/yiggeror/all-test-for-new-modle/blob/1fa86680089be1b6ee8a07dab2a13d865de05dd6/REVIEW_LOG.md)，从已通过的 Gate 2.4 十六份无损分卷重建画面，保留 48 / 96 / 144 秒三处 2 秒线性光叠化、片头 1.5 秒淡入及片尾 3.8 秒淡黑。夏景使用原封分卷，不使用任何兼容预览作为素材。

- 本地无参数重建产物 `dist/Rainroji_Lofi_V2.4_1080p.mp4`：132,850,666 字节，SHA-256 `81297609f124b90bcbc97533a0a9514179a7681fb66a0c05903b277a973229ae`。1920×1080、30 fps、5,917 帧、197.233333 秒，H.264 High / CRF14 / BT.709 矩阵限幅 / faststart。
- 新音轨保留完整《Green Tea》和冬窗翻页。前 185 秒混音 PCM 与批准版逐样相同；原曲自然落静后，冬夜雪风留在前景，底声抬升约 8 dB，最后 2.7 秒渐淡。48 kHz 立体声 AAC-LC，精确 9,467,200 个采样帧，实测 −16.05 LUFS-I、−4.74 dBTP。
- [重建入口](tools/gate3_v24/) · [实际解码帧、尾声试听及分轨曲线](previews/gate_3_4/) · [音乐及尾声署名](CREDITS.md)。

本次提交可复现工具和审片证据。正式 GitHub Release 与 Drive 文件由终审发布；v2.3 归档保持不动。

---

## Round 15–15d：v2.4 / Gate 2.4 四季双周期样片送审

根据[评审要求](https://github.com/yiggeror/all-test-for-new-modle/blob/30f9d44033cd0a9dce73b9bc0467dc5e4d2317ae/REVIEW_LOG.md)，本轮在 v2.3 的干净画面上恢复细微动势。[四季 22 秒样片、无损分卷、源包和动作证据](previews/gate_2_4/) 已归集。

- 春：猫按实际院落地面尺寸和相机投影安排，从遮挡后走入暖光、停顿抬头、再走进右侧遮挡。补整冠两侧落花、六只远鸟、局部 ±1 像素叶颤和老灯短降；原两块晾衣保留。
- 夏：原八个无损分卷与兼容预览逐字节复用。合并后的 SHA-256 和 v2.3 一致。
- 秋：双侧各 22 片空中落叶、离散叶颤和同风的局部暖光；保留茶汽、贴地卷叶、三只归鸟。
- 冬：固定树干与横幅两端，仅细枝和横幅下摆作整数像素微动；灯与风雪同步短暂降亮，旧空墙无假灯，暖窗的翻页保留。

Gate 2.4 只提交循环画面，待审后再制作 Gate 3.4。尾声调整采用 Round 15d 的原时长 197.233333 秒版本；本次不改现行 v2.3 发布件。

---

## Round 13：v2.3 / Gate 3.3 成片已从审批分卷重建，待终审

- [Round 13](https://github.com/yiggeror/all-test-for-new-modle/blob/8fbb28eb7a61329ffa218c6e7f92b4f72d19c6ee/REVIEW_LOG.md) 已通过 Gate 2.3 的 [d491fe13](https://github.com/yiggeror/all-test-for-new-modle/commit/d491fe13aaa2ff4b5addd296d42f1a40b73c85fc)。仅使用其 16 个无损分卷；实解四条 660 帧原片，锁定顺序、春 132 个天然持帧和整片 5,917 帧 PTS。
- 干净取件后运行 **python tools/gate3_v23/reproduce.py**（无参数）生成 dist/Rainroji_Lofi_V2.3_1080p.mp4：**124,559,524 字节**，SHA-256 f0be07bb737f320055a1c4783d0009ea9e6a1bda72286ea0bc5ff94d643eb0f5。1920×1080 @30 / 197.233333 秒，H.264 High CRF14 / BT.709 限幅 / faststart。48、96、144 秒各 2 秒线性光 smoothstep，片头 1.5 秒和尾部 3.8 秒照旧。
- 逐包保留已经签收 v2.0 官方 Release 的 9,247 个 AAC-LC 包、PTS/DTS、长度和 priming；不重新编码或混音。[实际解码关键帧、编码与画面核查](previews/gate_3_3/) 和 [一键工具](tools/gate3_v23/) 已备。
- [独立成片复核](previews/gate_3_3/QA.md) 已核全 5,917 帧、546 个预定的相邻持帧位置、灯光/翻页实片和原 AAC。当前等待终验实片、实听与后续正式双渠道发布；此提交不改旧版工具、分卷、Release 或 Drive。

---


## Round 12：v2.3 / Gate 2.3 像素动态返工待审

按 [Round 12](https://github.com/yiggeror/all-test-for-new-modle/blob/16951626d5db44eacf6ac0f9b52caf80cafd2a5b/REVIEW_LOG.md) 的否决项完成 [四季双周期样片、分卷、峰值和真实运动证据](previews/gate_2_3/)。

- 春：树干、枝和整冠固定。暖灯落瓣承担风动；两件米白与浅灰蓝布留在原横杆上，衣角每 5 帧换姿，挂点不穿柱。
- 夏：两只车灯在每个原生时刻实时求发射位置、材质和投影，暖琥珀限能沿湿地到红车，暗红霓虹及四次真实硬切照旧；左暖灯雨丝和檐滴变细。
- 秋：树和建筑固定，删除报亭晃动灰块和雾里红渍，街上靠分层落叶、暗底暖汽和三个暮色小归鸟读出风。
- 冬：拆掉整列假楼道灯，远楼仅保留有实体窗框的固定窗；枯树不动，保留雪、上升细烟和与灯罩分开的翻页。

四条原件仍为 330 原生帧 × 2 周期、1920×1080 / 30fps / 22s，从 320×180 严格 6× 最近邻放大。当前只交 Gate 2.3 审片，不合片、不改 v2.2 已归档发行。 [四季独立审片报告](previews/gate_2_3/qa/GATE23_INDEPENDENT_QA.md) 已回看四支原速双周期、逐帧连续条带及完整 330 相位控制。

## Round 10：Gate 2.2 已通过，Gate 3.2 成片待终审

[Round 10](https://github.com/yiggeror/all-test-for-new-modle/blob/a76a1b807b114c15036caebe58bffadeec3f53dd/REVIEW_LOG.md) 已通过四季 v2.2 样片。本次完整成片只用批准的 [Gate 2.2 无损分卷](previews/gate_2_2/lossless_parts/) 恢复四季原生 RGB，再做锁定 48／96／144 秒的三处 2 秒线性光叠化、1.5 秒淡入和 3.8 秒尾淡，然后 6× 整数放大；未使用有损样片。完整 9,247 个正式 v2.0 AAC 压缩包与采样时戳原样沿用。

**候审成片** Rainroji_Lofi_V2.2_1080p.mp4：196,231,459 字节，SHA-256 9f2e8e207e126752d97994d32e9eeba961d1ba6a6e254013f5648cc61041907a。成片 1920×1080 / 30fps / 5,917 帧 / 197.233333 秒。声画全解码、时戳逐帧与干净重做均通过。

在仓库根目录运行 python tools/gate3_v22/reproduce.py。[重建操作](tools/gate3_v22/) · [独立成片核查](previews/gate_3_2/QA.md) · [候审技术报告](previews/gate_3_2/PRODUCTION_QA.md) · [一键实跑](previews/gate_3_2/one_click_verified.json)。夏景 51.133 秒车灯扫过湿路、52.100 秒掠过红车，53.400—54.800 秒灯牌、邻墙和红倒影同帧四次骤暗；冬景 148.467 秒书页与灯罩分离。本轮只提交复现与审片佐证，GitHub Release 与 Drive 更新留给终审；不动已归档的 v2.0/v2.1。

## Round 9：v2.2 / Gate 2.2 四季返工样片待实片审核

依据 [Round 9 返工指令](https://github.com/yiggeror/all-test-for-new-modle/blob/4c06e29619b2efa6ed8c4f9b75888417d91a4bb7/REVIEW_LOG.md)，这一轮回到锁定的真 3D 分层场景和世界尺度，清掉退回版的巨型动物、断头和机械倒影。只交 [四季双周期样片、无损分卷、全幅动作峰值](previews/gate_2_2/)，尚未合片或发布 v2.2。

- **春：**清除屋脊猫和车把雀，衣物用实际院内旧架承重、暖光与暮紫暗面统一；风压带动真实花冠几何，一次花瓣穿暖灯光空间并有逐帧深度遮挡。
- **夏：**从实景彻底去猫，不加避雨角色。画外车灯压着湿地扫到漆面和低墙后离去；沥青反射是受不规则的真实受光、微面元和雨滴波场驱动的暗红碎点。灯箱、邻砖墙和路面四段同步骤暗 22%／24%／21%／23.5%，其余雨、檐滴、壶汽、理发柱与单次微闪各守住原空间。
- **秋：**撤去三只贴地大鸟，主动作改为粉紫晚雾里的阵风、梧桐冠的枝叶缝和轻卷过斑马线的落叶；茶汽呈半透明暖雾。
- **冬：**雪人和石凳间不再有荧光大鸟。暖窗里的读者留灯距、只在原动作时间翻一页，屋顶烟斜融蓝灰夜空；温暖光锥中的雪阵、树梢抖雪和远楼声控灯分层。

兼容样片均为 1920×1080、30 fps、22 秒。正本由 320×180 原生直接 6× 整数放大后无损编码，660 帧为 2×330，分卷重组已逐文件对正本。旧 v2.0/v2.1 的归档影视、署名和发布版本不变。

[四季独立审片与逐帧核查](previews/gate_2_2/qa/GATE22_INDEPENDENT_QA.md) · [实测数据](previews/gate_2_2/qa/GATE22_INDEPENDENT_QA.json) · [夏季真实反光与参考对照](previews/gate_2_2/qa/summer_v22_reference_comparison.jpg)。


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

# Gate 2｜四季配乐候选

**先看 [18 秒冬窗试配](winter_music_audition.mp4)。** 首选 **Purrple Cat《Green Tea》**：80 BPM，电钢琴般的圆头音和松弛的反拍给雪景一层暖意；鼓点有存在感，却不催促窗里的人。若更想表现秋天走在老街的生活气，选第 2 首木吉他。四首来自四位作者，两首有律动，两首无鼓；本轮不锁总片配乐。

| 可播放的本地片段 | 曲风与用途 | BPM / 调性 | 原曲 → 试听 |
|---|---|---|---|
| [01 · Green Tea](music_candidates/01_green_tea.mp3) · Purrple Cat | 键盘轻鼓 Chillhop。暖和弦有清楚的敲击起头，低音铺得圆，适合冬窗与春灯。 | 80 / C 大调 | 3:17.21 → **36.00 秒** |
| [02 · lofibeat_70bpm.wav](music_candidates/02_guitar_beat.mp3) · Seth_Makes_Sounds | 木吉他 Lo-Fi。拨弦、扫弦和松的鼓点各有空间。比 01 的键盘多了一点指尖与琴弦的摩擦感，适合有风的秋路。 | 70 / D 大调 | 1:42.86 → **34.29 秒** |
| [03 · First Light Particles](music_candidates/03_first_light.mp3) · Yoiyami | 梦幻氛围琴。轻琴音与后方持续和声分开，无鼓、不靠重拍推进；适合从雪夜切回早春。 | 音符约 94，慢数 47 / G 大调 | 2:11.72 → **38.00 秒** |
| [04 · Forget Me Not](music_candidates/04_forget_me_not.mp3) · Kistol | 磁带琴小品试听版。旋律干净，音符收住后会留下很宽的空隙，适合冬段收尾；与 03 持续铺底的写法不同。 | 音符约 100，慢数 50 / F 大调 | 3:08.90 → **38.40 秒** |

原曲均为已发表成曲。01、02 保持原速；03、04 的 BPM 是琴音起音的估计值，不能当成底鼓速度。01 调性与作品目录相符；02、03 用录音的五组色度模板全曲分析；04 源文件名注明 F 大调。04 的轻微转速偏移、左右串音与极低底噪是**本项目制作的试听处理**，不是对原琴录制设备的描述。四首片段均为 48 kHz 立体声 MP3、224 kbps，做定增益与短首尾淡化；鼓的瞬态和琴句的音量起伏都保留。

## 声音的差别

下面是**交付片段**的实测，能量比按双声道 Welch 功率计算；分母为这四段之和，数字不等于主观音量。四首已匹配至解码约 −18.7 LUFS，可直接横向比较。

| 片段 | 20–160 Hz | 160 Hz–2 kHz | 2–6 kHz | 6–20 kHz | LRA / 真峰值 |
|---|---:|---:|---:|---:|---|
| Green Tea | 61.71% | 38.05% | 0.13% | 0.11% | 5.2 LU / −8.28 dBTP |
| lofibeat_70bpm.wav | 61.39% | 36.29% | 2.09% | 0.22% | 2.1 LU / −1.64 dBTP |
| First Light Particles | 10.04% | 89.86% | 0.10% | <0.01% | 5.1 LU / −5.31 dBTP |
| Forget Me Not | 10.79% | 89.20% | <0.01% | <0.01% | 14.1 LU / −2.32 dBTP |

01 的 12–24 秒仍在逐步进入主体，24 秒后律动完整；02 比 01 在 2–6 kHz 多约 2 个百分点，琴弦与鼓的起音更容易从画面听出。03 主要停留在中频，画面可以“呼吸”；04 的强弱起伏最大，建议保留休止，不要用压缩器把停顿间隙填满。

## 正式冬景试配（一次翻页，不按鼓点剪画面）

- 1920×1080，30 fps，540 帧 / 18.000 秒，H.264 + 48 kHz 立体声 AAC。从**本轮正式冬循环**的第 210 帧（7.000 秒）开始，样片 4.00 和 15.00 秒跨过画面循环接缝，音乐在两个位置都继续前行。
- 《Green Tea》取原录音 **00:30–00:48**（六个 4/4 小节）。把音乐的 150 Hz 附近轻收 1.5 dB，留出院子近处的空气感；无变速、无切碎伴奏。
- 现场声从零合成：低而宽的雪夜院风、靠右值班室的微弱风口声；隔着暖窗，在 **9.21、9.64、10.28 秒**只放了三小笔纸页摩擦。画面完整翻页窗口 **8.30–10.90 秒**。没有给每片雪配“落地声”，也没有假放大一声室内翻书。
- 声底比音乐低 **15 LU**（−31.20 与 −16.20 LUFS）；最终 AAC **−16.09 LUFS、−5.34 dBTP**，没有限幅。与无损冬景源逐一比过 540 个对应画面，SSIM 0.9966。完整数据见 [试听技术核查](music_qa.json)。这是供 Gate 2 选音乐的试配，不是 Gate 3 终混。

## 来源、许可与署名

- **Green Tea — Purrple Cat**：[作者 itch 发行页](https://purrplecat.itch.io/bloom)列为 *Bloom* 第 5 首，页面 Asset license 标明 **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)**。[作者上传的此版音频](https://html-classic.itch.zone/html/19949767/media/Green%20Tea.mp3)。允许署名复制、再分发、改编和商用；应保留作者、标题、来源、协议及改动说明。公开发布试配时可直接使用以下行：

  > 《Green Tea》/ Purrple Cat（https://purrplecat.itch.io/bloom），CC BY 4.0（https://creativecommons.org/licenses/by/4.0/）。本片节选 00:30–00:48，调整电平、低频与淡入淡出，叠加原创庭院环境并与冬景画面同步。

- **lofibeat_70bpm.wav — Seth_Makes_Sounds**：[作者原曲及逐曲许可](https://freesound.org/people/Seth_Makes_Sounds/sounds/664145/)明确是本人木吉他 Lo-Fi，授权栏为 **[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)**。本项目取同一条目的[官方 HQ 试听文件](https://cdn.freesound.org/previews/664/664145_13228046-hq.mp3)，不是低码率预览或另一个同名 beat。已节选、调电平及淡化。
- **First Light Particles — Yoiyami**：[作品页及逐曲许可](https://opengameart.org/node/182244)，**[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)**，作者还单列商业项目、视频、独立音轨和改编。[作者原始 WAV](https://opengameart.org/sites/default/files/first_light_particles_0.wav)。已节选、调电平及淡化。
- **Forget Me Not — Kistol**：[作品页及逐曲许可](https://opengameart.org/content/forget-me-not)，**[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)**。[作者完整版 Ogg](https://opengameart.org/sites/default/files/forget_me_not_in_f_major_0.ogg)；没有使用另一份循环剪辑。已节选、轻磁带处理、调电平及淡化。

三份 CC0 均可复制、再分发、改编与商用；这里仍保留作者署名。四个源文件的身份、SHA-256、逐曲证明和出处见 [music_sources.json](music_sources.json)。复现工具 [tools/gate2_audio.py](../../tools/gate2_audio.py) 只处理本地文件；完整成曲可从各创作者页取得。试听不使用 Rainroji 原配乐。

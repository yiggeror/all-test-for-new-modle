# Gate 3.3 / Rainroji v2.3 实解码候审

仓库根目录运行 **python tools/gate3_v23/reproduce.py**，生成 dist/Rainroji_Lofi_V2.3_1080p.mp4。实测 **124,559,524 字节**，SHA-256 **f0be07bb737f320055a1c4783d0009ea9e6a1bda72286ea0bc5ff94d643eb0f5**。这是待终审文件，非已发布链接。

- [reproduction_qa.json](reproduction_qa.json) 含全 5,917 画面时间戳、媒体规格、完整解码和 9,247 个 AAC 包逐包验证；原官方 v2.0 不重混，FFmpeg 7.1.5 对同包实测 **-16.04 LUFS-I / -4.74 dBTP**。
- [picture_plan.json](picture_plan.json) 为实际合片时间轴，[picture_render.json](picture_render.json) 为实际送入编码器的 RGB 帧指纹（5,917 帧、320×180 RGB24 原始字节，无文件头）。所有帧位保留，春季 330 相位中的 132 处相邻持帧不是重复时间戳。
- [encoded_transition_storyboard.jpg](encoded_transition_storyboard.jpg) 是实际 H.264 解码的三组转场；三个中心另有原尺寸图（F1440、F2880、F4320）。首尾渐变和关键动作共 17 张原尺寸无标记 PNG，索引见 [decoded_frame_manifest.json](decoded_frame_manifest.json) 和 [art_cue_map.json](art_cue_map.json)。
- 春 F180/F195 检查光锥落花、稳树与晾衣；夏 F1534/F1563 是湿地及车身暖车灯，F1601/F1604 是霓虹亮暗对应邻墙和红水洼；秋 F2972/F3002/F3028 是贴地叶、鸟及柔汽；冬 F4385/F4455/F4504 是固定远窗、分离的书页与台灯、光锥落雪。
- [picture_complete_qa.json](picture_complete_qa.json) 含生产端实片对照、循环边和缓变区；[palette_lock_probe.json](palette_lock_probe.json) 记录审批正本整解 2,640 帧，用同版颜色表全量精确恢复 320×180 像素，零碰撞。色卡不含画面。

[clean_command.json](clean_command.json) 与 [unit_test.log](unit_test.log) 记录默认命令和回归。[音乐署名](../../CREDITS.md) 保持原版。本地对 v2.0 正式文件同工具复测一致，保留包不改。仅提交候审证据和一键工具；GitHub Release / Drive 由评审方终验发布。

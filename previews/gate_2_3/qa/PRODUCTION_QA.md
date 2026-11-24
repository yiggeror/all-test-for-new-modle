# Gate 2.3 · 制作核查

这是制作方对冻结候审媒体的实测，不替代独立审片或终审。

- **春：**[静态世界和 66 个布姿](spring_physical_trace.json) · [固定花冠蒙版](spring_static_foliage_mask.png) · [接触检查](spring_rack_contact.json) · [完整逐帧报告](spring_decoded_qa.json)。树冠核心与树干 ROI 在全周期各 0 改变像素；布只在每第 5 帧换姿；衣料 3D 网点距柱边最窄 0.468 m，仍扶在原横杆上。
- **夏：**[真实逐相光位和遮挡射线](summer_headlight_actual_phases.json) · [同相物理 A/B 与霓虹各处边](summer_evidence.json) · [完整逐帧报告](summer_verified.json)。330 相按当时灯位即时求解，154 相两灯有光，F124 实打 130,898 条遮挡线，湿面暗红线索仍见；F153 车侧 696 个原生像素实际亮度上升至少 7 级。牌、砖墙和地面四次切暗及恢复同帧。
- **秋冬：**[秋导演/动作参数](autumn_scene.json) · [冬导演/动作参数](winter_scene.json) · [局部实测](scene_art_checks.json) · [秋逐帧](autumn_verified.json) · [冬逐帧](winter_verified.json)。秋双树、钠灯与冬树/居民楼的无动态控制均独立输出 330 帧，记录每个时刻固定像素，便于与全片的独立叶、雪层区分。冬台灯在翻页控制 A/B 下 44 相零污染差异。冬无居民窗开关变化，不保留假楼道渐亮。
- 四条正本的双周期分别逐帧核 660 张，分卷仅用于传输：最终数量以 [恢复比对](lossless_restore.json) 为准。

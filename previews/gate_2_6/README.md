# Gate 2.6 · 秋景三项精修

- [完整秋景](autumn_loop.mp4)：1080p、30 fps、22 秒两周期，无损 QP0。[未标原速短预览](autumn_girl_normal_speed_1080p.mp4) · [人物原速 4×](autumn_girl_normal_speed_detail.mp4) · [两侧人行道原速 4×](autumn_ground_both_sides_4x_1x.mp4)。
- 秋景左侧少女靠在实测梧桐树皮上，鞋底落在人行道，窄站、低头，一次抬手翻页；共用已改树冠的风压和阵风时钟带动真实发梢。优先以轮廓和现有暖光表现，没有另补脸部亮色。
- 取消人行道整块图层位移，改用 22 片独立贴地叶，22 片均在逐叶同相位原生对照中实际可见，其中 18 片在 66 个状态中至少可见 34 个。12 片各沿实际路面几何短移约 4.21–9.52 原生像素，其他错拍翻面或伏地；保留斑马线原滚叶。
- 秋冠 23,703 像素的物理分母，全 330 帧真合片 A/B 的单帧活跃 10.00%–14.07%，并集 82.25%。左右各自最高低均在 8%–16% 范围，受保护硬边零改动。斜纹前沿改用不规则多尺度风；原地面斑驳暖光仍用同一已验收时钟。
- [全 330 帧底板对照](qa/autumn_scope_wind_ground_330.json) 中，旧版和新版都关闭各自的人物及阴影、树冠和人行道落叶后，实际渲染原生 RGB 完全相同。春、夏、冬沿用 v2.5 的原始 15 个二进制分卷，见[清单](lossless_parts/MANIFEST.json)。
- [旧风斜纹同相位](qa/v25_crown_parallel_fronts.png) · [新风不规则前沿](qa/v26_crown_organic_fronts.png) · [真合片冠热力图](qa/autumn_crown_330_heatmap.png) · [落叶轨迹及实际点亮像素](qa/ground_individual_native_raster.json)。
- [完整可复算源码](source/autumn_v26.zip) · [逐帧翻页条带](qa/autumn_girl_turn_every_frame_4x.png) · [随风发梢真实开关对照](qa/autumn_girl_hair_A_B_4x.png) · [原幅盲看记录](qa/INDEPENDENT_FIRST_PASS.md)。

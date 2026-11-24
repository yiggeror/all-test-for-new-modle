# 春景 · Gate 2.4 送审证据

原片双周期 22 秒。GitHub 预览根的 spring_loop.mp4 是 1080p30 High 兼容件；验证及后续制作只用 lossless_parts/spring 下的 QP0 正本。分别核满 660 PTS，无漏帧或重复时戳，底片的离散持帧保留。源 ZIP 在 source/，10 幅未标记实际解码原尺寸关键图在 peaks/；本页的附图之外，所有实际无损条带在 QA 目录。

## 路线、比例和连续镜头

原有相机完全不动。按原建议 z=16.5–20、y=0 实投脚点 y=192–230，超出 180 原生画幅；实际选同院落、真正可见的 z≈9.55–12.43 地面。身体 0.466m、肩高 0.261m、头顶不超过 0.34m；停驻体宽约7px、高约5–6px，全步态最高7px，而院外自行车轮实投约12.56px。不增大体型。其余世界静物不改。

- [从原左门墙缝露出](spring_cat_4x_sunken_entry.png)：F40 首露，F45 头身已读；F0 335 个真实体射线全部被砖与金属遮挡。无透明度时间淡出。
- [暖地短停并抬头卷尾](spring_cat_4x_warm_pause.png)：F120–179 实体根保持同点；头、颈、肩连成同一个实际网格，脚掌接地、阴影分别由直接光与接触半球投射。尾尖上移一个原生像素后回。身体与固定静物边缘 66 姿态零相交。
- [进入右檐暗处](spring_cat_4x_right_occlusion.png)：F325 起整猫被原砖面和玻璃几何藏住，F329 327 个候选真实射线全被挡。F0 和 F329 的无猫同相 RGB 对照零像素差。整个镜头 329→0 的 RGB 平均差 .1642，低于同类 5 帧换姿边界中位 .1872。

## 其余细节

- [纯叶 ±1 实际开／关](spring_leaf_a_b4x.png)：9 射线确认为前景真叶，深度相近才整数邻取样，粗主枝／线／树干零位移。全帧变化图见 [spring_motion_heatmap.png](spring_motion_heatmap.png)。
- 195 片实际主樱花三角面三侧出生的 3D 落花（左／中／右各65），风向一致向画面左，有自然前后深度遮挡；源轨迹附 spring_petal_origins.json。两件衣料未改，和签收旧版同相纯布像素 122,180 个逐字节全相同。
- [老灯自然压降](spring_lamp_a_b4x.png)：F138–143 的分层灯强相对常态为82%，0.20s；F144即回稳，辉光和原受照域同源；F141 暖区实际画面亮度仍有静曲对照的约95.35%，不是闪黑。已有左楼 TV 小窗是独立低幅淡变。
- [暮燕入天空](spring_birds_4x_entry_sky.png) / [实际冠后](spring_birds_4x_tree_occlusion.png) / [再出冠](spring_birds_4x_reappearance_sky.png)：实际 5 帧一换的 3D 翼形，翼展2.35–3.88px，画面上在原色板仍有清楚但低调的灰紫差异，不锐化为黑点。

数值与同相控件：spring_gate24_art_proof.json、spring_layer_proof.npz、spring_cloth_pose_proof.npz、spring_physical.json、spring_verified_base_bindings.json。QA 数组只供取证，不作为下游 picture input。

# V2 · Phase C · 制服与动作，提请正式验收

- [全身八视角 NPR 与 1.60 m 标尺](previews/v2_phaseC/turnaround_8view_npr.png) · [四视角灰模和真实网格线](previews/v2_phaseC/turnaround_4view_clay_and_wire.png)
- [五方向打光测试](previews/v2_phaseC/lighting_stress_test.png) · [领结、星象仪、双层裙、袜环和圆头鞋特写](previews/v2_phaseC/details_npr.png)
- [1080p 转盘：8 秒全身与 4 秒上半身](previews/v2_phaseC/turntable_npr_1080p.mp4) · [1080p 连续动作与原生表情](previews/v2_phaseC/motion_expression_showcase.mp4)
- [可编辑 Blender 资产和动作](assets/suzu_v2_phaseC.blend) · [带统一动画片段的 GLB](assets/suzu_v2_phaseC.glb)

按 Round 5.5 完成袖管松量、立体翻领和上下衣分层、修净裙腰、加深展宽刀褶与加厚衬裙、统一午夜绀蓝和柔冷描边。保留已签收的头身、面部表情和三件发饰，刘海仅微压根部。圆头玛丽珍鞋由真实鞋楦和独立外底、低跟、窄搭扣构成。

保留原 154 根骨骼与 57 个表情目标；加入 16 根头发随动骨与 13 根裙摆骨。GLB 内使用同一连续动作片段同步身体和表情。复现入口 `bash tools/v2_phaseC/reproduce_phaseC.sh assets/suzu_v2_phaseB.blend <输出目录>`（Blender 4.3、C++17、FFmpeg、Pillow、NumPy）。

Phase C 待总监独立验收，未进入 Phase D。

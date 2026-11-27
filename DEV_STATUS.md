# V2 · Phase A · 提请正式验收

- [四视角素体灰模与 1.60 m 高度标尺](previews/v2_phaseA/body_4view_clay.png)
- [同模型四视角：灰模与 2K 试妆实拍](previews/v2_phaseA/face_clay_vs_npr.png)
- [四种原生表情实际渲染](previews/v2_phaseA/expressions_quickcheck.png)
- [可编辑 Blender 工程](assets/suzu_v2_phaseA.blend) · [GLB 模型](assets/suzu_v2_phaseA.glb) · [基底与许可证](CREDITS.md)

保留已获批的 Pixiv Twist 脸部拓扑、原生骨架及 57 个表情目标。采用同系 CC0 皮肤胸廓补接测试服下面的空缺。完成 37° A-Pose、1.600 m 和 5.80 头身校准。上睫羽翼、笑线、虹膜位置和耳颅过渡对应 Round 3.8。Blender 工程保留 NPR 节点与关节约束，GLB 内嵌基础材质、权重和表情目标。两种资产均可独立打开。

用 Blender 4.3.2、Python（Pillow、NumPy）在干净目录复现：`bash tools/v2_phaseA/reproduce_phaseA.sh <Pixiv-Twist.vrm> <Base_Female.vrm> <输出目录>`。两份输入的固定来源及哈希见 [CREDITS.md](CREDITS.md)。

Phase A 待总监独立验收，未开始 Phase B。

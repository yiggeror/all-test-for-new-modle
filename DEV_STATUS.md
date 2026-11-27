# V2 · Phase B · 发型与发饰，提请正式验收

- [同模型五视角：灰模与银紫冰蓝 NPR](previews/v2_phaseB/head_5view_npr_and_clay.png)
- [俯仰死角、后发纵深及三件发饰微距](previews/v2_phaseB/hair_deadangles_and_props.png)
- [戴上发型后的原生四表情](previews/v2_phaseB/expressions_with_hair.png)
- [Blender 模型](assets/suzu_v2_phaseB.blend) · [GLB 模型](assets/suzu_v2_phaseB.glb)

Round 4.5 的长碎刘海、压平额顶、消除后冠短瓣、加厚左马尾、长鬓发与冷灰紫细描边均纳入本轮。月牙、四角蓝星双杠与深绀双尾结已装到实物发面。锁定的 Phase A 脸、妆、57 个原生表情目标、素体及 154 骨架未变。本轮未合装衣物。

GLB 文件内已核查只有角色和实际发饰网格，无 Icosphere。Blender 默认导入可另生成一个球形骨骼显示件；测包围盒可打开 **Disable Bone Shape**，也可用仓内检视脚本验证原始包再重开。精修胸廓灰模细纹留在 Phase C，不动本轮锁定素体。

复现：`bash tools/v2_phaseB/reproduce_phaseB.sh assets/suzu_v2_phaseA.blend <输出目录>`（Blender 4.3、Pillow、NumPy）。等待总监独立验收，未进入 Phase C。

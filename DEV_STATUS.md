# 星野铃 · Phase D 终版送审

- [英雄海报](previews/final/suzu_hero_render.png) · [浏览器实机检视](previews/final/viewer_web_live.png) · [360° 转盘](previews/final/turntable_final_1080p.mp4) · [连续表演](previews/final/motion_final_1080p.mp4)
- [Blender 工程](assets/suzu_final.blend) · [GLB 模型](assets/suzu_final.glb) · [Web 检视器](viewer/) · [来源与许可](CREDITS.md)

终版模型与已签收的 Round 6 资产逐字节相同。浏览器用 Three.js r180 加载原 GLB 的网格、骨骼、贴图和动画，实时渲染调整不会写入资产。线框叠加随骨骼与表情，动作进度条播放原内嵌片段。

## 本地打开

在仓库根目录执行 `python3 viewer/start.py`，浏览器会打开 `http://127.0.0.1:8765/viewer/`。Windows 可双击 `start-viewer.cmd`。脚本与资源均随项目提供，运行时不需要联网。

## 从 A 到 D 复现

使用 Blender 4.3、Python 3（Pillow / NumPy）、FFmpeg 和 C++17 工具链。A 的两个固定输入及 SHA-256 见 [来源与许可](CREDITS.md)。在仓库根目录执行：

```bash
bash tools/v2_phaseA/reproduce_phaseA.sh /path/to/VRM1_Constraint_Twist_Sample.vrm /path/to/Base_Female.vrm build/A
bash tools/v2_phaseB/reproduce_phaseB.sh build/A/assets/suzu_v2_phaseA.blend build/B
bash tools/v2_phaseC/reproduce_phaseC.sh build/B/assets/suzu_v2_phaseB.blend build/C
bash tools/v2_phaseD/reproduce_phaseD.sh build/C build/D
python3 build/D/viewer/start.py
```

已有签收资产和片源时，可直接执行 `bash tools/v2_phaseD/reproduce_phaseD.sh . build/D`；加 `--viewer-only` 只组装离线检视器、模型和 ZIP。

## 浏览器复核

另开一个终端运行 `python3 viewer/start.py --no-browser`。在有 Node.js 和 Chromium 的环境：

```bash
npm ci --prefix tools/v2_phaseD
SUZU_CHROMIUM=/path/to/chromium npm run check --prefix tools/v2_phaseD
```

复核脚本禁止外网请求，并检查旋转、缩放、平移、三种显示、四种灯光、四个真实表情、动画播放/暂停/拖动和移动端布局。已在 Chromium 143 的实际 WebGL 页面和干净解压的离线包验证，完整交互测试中控制台、WebGL 和网络请求均无错误。

等待总监终审。

# *Un Jour à Giverny*（吉维尼的一天）— 纯 C++17 离线莫奈印象派一镜到底动画短片

> **100% 纯 C++17 CPU 离线油画笔触引擎（[`engine/`](engine/)）逐帧手算绘制**，零外部图像贴图、零 3D 模型/WebGL、零 AI 生图、零传统剪辑硬切。  
> 全片 **92.0 秒**（`2760` 帧，`30 fps`），以单条连续 $C^2$ Catmull-Rom 摄影机轨迹横跨 **5 个莫奈主题动态画境 + 4 道前景自然过渡门户**（世界坐标 `camX = 0 → 14120`），并配以德彪西《月光》（*Clair de Lune*）及 6 轨分景同步自然音效。

---

## 交付成片与无损分卷位置（分支：`monet-short-film`）

由于两支高码率离线成品均超过 GitHub 单文件 `100 MB` 限制，已采用二进制**绝对无缝分卷**（每卷 `<= 40,000,000` bytes / `38.15 MiB`），克隆仓库后运行 [`output/reassemble.sh`](output/reassemble.sh) 即可 100% 比特级无损还原并自动校验 SHA-256：

- **1080p 全高清母版（`1920×1080`，H.264 High CRF 16 slow / BT.709，`30 fps`，`2760` 帧，`92.0s`，AAC `48kHz` 立体声 `256kbps`，总码率 ~`41.9 Mbps`，`481,874,271` bytes / `460 MiB`）**
  - 分卷文件：`output/monet_un_jour_a_giverny_1080p.mp4.part.00` ～ `.part.12`（共 13 卷）
  - 完整 SHA-256：`3aa53824aac32e28fad3bc1e34a896fdf8fd6d351176278dbddb9e7ac211bbba`

- **720p 高清成片（由无损母版 Lanczos 锐化下采样，`1280×720`，H.264 High CRF 16 slow / BT.709，`30 fps`，`2760` 帧，`92.0s`，AAC `48kHz` 立体声 `256kbps`，总码率 ~`17.1 Mbps`，`196,830,744` bytes / `188 MiB`）**
  - 分卷文件：`output/monet_un_jour_a_giverny_720p.mp4.part.00` ～ `.part.04`（共 5 卷）
  - 完整 SHA-256：`f4163eac1450745a2bb7d53d9ad35404240ea2ae6918b74de118676ee88a86ee`

### 一键无损还原两支成片

- **Windows 电脑（零命令，鼠标双击即可）**：解压仓库后打开 `output` 文件夹，**直接双击 [`output/reassemble_windows.bat`](output/reassemble_windows.bat)**，等待数秒黑框提示完成后，同目录下即生成两支完整 `.mp4`。
- **macOS / Linux / Git Bash**：
  ```bash
  chmod +x output/reassemble.sh
  ./output/reassemble.sh
  ```

手动合并（Linux / macOS / Git Bash）：
```bash
cat output/monet_un_jour_a_giverny_1080p.mp4.part.* > output/monet_un_jour_a_giverny_1080p.mp4
cat output/monet_un_jour_a_giverny_720p.mp4.part.*  > output/monet_un_jour_a_giverny_720p.mp4
```

Windows CMD：
```bat
copy /b output\monet_un_jour_a_giverny_1080p.mp4.part.* output\monet_un_jour_a_giverny_1080p.mp4
copy /b output\monet_un_jour_a_giverny_720p.mp4.part.*  output\monet_un_jour_a_giverny_720p.mp4
```

---

## 一镜到底视觉旅程（`0.0s – 92.0s`）

全片摄影机由 [`engine/camera.hpp`](engine/camera.hpp) 的 Catmull-Rom 样条驱动，跨越 5 层视差油画长卷：

1. **Scene 1（`0s – 18s`）：《日出·印象》塞纳河晨雾**
   - 橙红朝阳与光晕、分层晨雾树影、手划木舟与船夫、掠空飞翔的白色白鹭群、碎色波光水面倒影。
   - **空间过渡 Portal 1（`~17.5s – 22.0s`）**：前景垂柳帘幕与树干自然分帘擦过镜头，水岸无缝延展至吉维尼莲池。
2. **Scene 2（`20s – 38s`）：《吉维尼睡莲池与日本桥》**
   - 绿漆拱桥与垂坠紫藤花串、桥上赏景人影、42 簇错落粉白睡莲、8 尾游动锦鲤、6 只轻盈蓝蜻蜓与碎光倒影。
   - **空间过渡 Portal 2（`~37.5s – 42.0s`）**：繁盛攀援的粉红重瓣玫瑰花门框住视野，沙砾小径连入诺曼底花坡。
3. **Scene 3（`40s – 57s`）：《撑阳伞的女人》诺曼底虞美人坡**
   - 迎风飘动丝巾与白裙的撑伞女子、花坡旁的小让·莫奈、远景红顶石砌农舍、随风摇曳的朱红虞美人花海。
   - **空间过渡 Portal 3（`~57.0s – 61.5s`）**：穿过无缝弯曲的吉维尼果园树干连廊，草色渐变为暖金秋收田野。
4. **Scene 4（`60s – 76s`）：《干草垛》黄金暮色田野**
   - 两座高耸穹顶麦秸垛（受光面金橙玫瑰金，背光面与长投影呈莫奈标志性紫罗兰互补色）、低头吃草的羊群与飞鸟。
   - **空间过渡 Portal 4（`~76.0s – 80.5s`）**：金紫暮色中穿过湖畔芦苇与鸢尾，地平线延续为静谧暮色泻湖。
5. **Scene 5（`79s – 92s`）：《月夜·吉维尼泻湖》终章**
   - 透出暖黄灯光与水中灯影的石砌船屋、伴游湖面的优雅双白天鹅、夜空弯月与微闪星辰、冉冉升起的萤火虫。

---

## 纯 C++17 引擎架构

- [`engine/paint_core.hpp`](engine/paint_core.hpp)：浮点 `OilCanvas`（RGBA + 厚涂颜料高度场 `height`）、多毛刷分叉二次贝塞尔笔触（`paintStroke` / `paintDab`）、斜光浮雕高光与亚麻画布织纹结算（`resolveCanvasToRGB24`）、多线程图层合成（`compositeLayerMT`）、树冠与无缝单段弯曲树干（`paintFoliageCanopy` / `paintContinuousTrunk`）。
- [`engine/world_layers.hpp`](engine/world_layers.hpp)：5 个大尺度连续全景静态油画长卷绘制（Layer 0 天空、Layer 1 远山、Layer 2 中景树林与农舍、Layer 3 主景地标、Layer 5 四重羽化门帘）。
- [`engine/camera.hpp`](engine/camera.hpp)：92 秒 $C^2$ Catmull-Rom 摄影机轨迹定义。
- [`engine/animator.hpp`](engine/animator.hpp)：逐帧视差合成、破碎水面反光波形、以及所有动态生物/人物/波光/星月/萤火虫笔触重绘。
- [`engine/render_film.cpp`](engine/render_film.cpp)：离线渲染主程序，支持关键帧审核（`--audit`）与原始 `RGB24` 视频流管道输出（`--video [--start N] [--end M]`）。
- [`scripts/prepare_audio.py`](scripts/prepare_audio.py)：FFmpeg 8 轨混音脚本，将德彪西《月光》与 6 轨公共领域自然音效按 C++ 分镜时间轴精确对齐混制为 `assets/audio/master_92s.wav`（详见 [`CREDITS.md`](CREDITS.md)）。

---

## 编译与本地复现

```bash
# 1. 编译纯 C++17 离线渲染器
mkdir -p build
g++ -O3 -march=native -std=c++17 -pthread engine/render_film.cpp -o build/render_film

# 2. 重新混音（可选，已内置 assets/audio/master_92s.wav）
python3 scripts/prepare_audio.py

# 3. 审核 19 个关键帧 + 5 张 1:1 局部放大图
mkdir -p output/audit
./build/render_film --audit

# 4. 流式离线渲染并压制 1080p 成片
./build/render_film --video | ffmpeg -y \
  -f rawvideo -pixel_format rgb24 -video_size 1920x1080 -framerate 30 -i - \
  -i assets/audio/master_92s.wav \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 256k -shortest -movflags +faststart \
  output/monet_un_jour_a_giverny_1080p.mp4
```

# *Un Jour à Giverny*（吉维尼的一天）— 纯代码莫奈印象派一镜到底动画短片

> **100% 纯代码（JavaScript + HTML5 Canvas 程序化油画笔触引擎）绘制**，零外部图像素材、零传统剪辑切换。  
> 全片 **92.0 秒**（`2760` 帧，`30 fps`），以单条 $C^2$ 连续一镜到底空间摄影机曲线横跨 **5 个动态莫奈主题画境 + 4 重前景自然过渡门户**，配以德彪西《月光》（*Clair de Lune*）与 6 轨分景自然环境音效混音。

---

## 交付成片位置（分支：`monet-short-film`）

- **720p 成片（完整单文件，40.1 MiB / `42,082,979` bytes）**：
  - [`output/monet_un_jour_a_giverny_720p.mp4`](output/monet_un_jour_a_giverny_720p.mp4)
  - 规格：`1280×720`，H.264 High (`yuv420p`)，`30 fps`，`92.0s`，AAC `48kHz` 立体声
  - SHA-256：`1df549743d3fe33985c6cec2907f8bd8277994cd214215a51307416c73a46b6b`

- **1080p 成片（总大小 79.2 MiB / `83,086,434` bytes，已按 GitHub 大文件最佳实践做二进制绝对无缝分卷，单卷 <= 40.1 MiB）**：
  - 分卷 0：[`output/monet_un_jour_a_giverny_1080p.mp4.part.00`](output/monet_un_jour_a_giverny_1080p.mp4.part.00)（`42,000,000` bytes）
  - 分卷 1：[`output/monet_un_jour_a_giverny_1080p.mp4.part.01`](output/monet_un_jour_a_giverny_1080p.mp4.part.01)（`41,086,434` bytes）
  - 无损合并脚本：[`output/reassemble_1080p.sh`](output/reassemble_1080p.sh)
  - 合并命令（比特级 100% 绝对无缝还原）：
    ```bash
    ./output/reassemble_1080p.sh
    # 或 Windows / 任意 POSIX Shell:
    # cat output/monet_un_jour_a_giverny_1080p.mp4.part.* > output/monet_un_jour_a_giverny_1080p.mp4
    ```
  - 完整 1080p 规格：`1920×1080`，H.264 High (`yuv420p`)，`30 fps`，`92.0s`，AAC `48kHz` 立体声
  - 合并后 SHA-256：`ca6f094658f4a07b0c2a76f9ce805d610d58ca39608f25d090b6a3589a5cf1da`

---

## 一镜到底分镜与空间过渡结构（`0.0s – 92.0s`）

全片摄影机由 [`src/core/camera.js`](src/core/camera.js) 的 Catmull-Rom 连续样条驱动，在 `worldX = 680 → 12120` 的统一多景深世界坐标中持续平移与微幅仰俯呼吸：

1. **Scene 1（`0s – 20s`）：《日出·印象》塞纳河晨雾** — [`src/scenes/scene1_dawn.js`](src/scenes/scene1_dawn.js)
   - 琥珀红晨日、多层色彩透视远山与港湾桅杆剪影、船夫划桨、波光碎金倒影、掠空飞翔的白色白鹭群。
   - **空间过渡 Portal 1（`~18.5s`）**：前景垂柳帘幕自然擦过镜头，从晨雾河湾步入吉维尼水园。
2. **Scene 2（`17s – 39s`）：《吉维尼睡莲池与日本桥》** — [`src/scenes/scene2_giverny.js`](src/scenes/scene2_giverny.js)
   - 拱形绿漆日本桥、摇曳的紫藤花串、桥上凭栏赏池的仕女、池中浮动的粉白睡莲与圆叶、游弋的锦鲤以及掠过水面的蓝蜻蜓。
   - **空间过渡 Portal 2（`~37.5s`）**：繁茂攀援的粉色玫瑰花门框住镜头右侧，引出阳光明媚的诺曼底高坡。
3. **Scene 3（`36s – 58s`）：《撑阳伞的女人》诺曼底罂粟花坡** — [`src/scenes/scene3_poppies.js`](src/scenes/scene3_poppies.js)
   - 漫山随风起伏的朱红罂粟花海、远景红顶白墙农舍、执白阳伞与飘舞纱巾的女子、花间嬉戏的孩童与粉白蝴蝶。
   - **空间过渡 Portal 3（`~56.5s`）**：镜头穿过金绿渐变果园树冠拱廊，日光转为暖金暮色。
4. **Scene 4（`55s – 76s`）：《干草垛》黄金暮色田野** — [`src/scenes/scene4_haystacks.js`](src/scenes/scene4_haystacks.js)
   - 两座高耸的麦秸垛（受光面呈金橙赭石、背光面与斜投影呈印象派紫罗兰互补色）、吃草游走的羊群与牧羊犬、低飞燕群、金粉光尘。
   - **空间过渡 Portal 4（`~74.5s`）**：暮色芦苇岸坡随摄影机下探至水面，衔接夜幕泻湖。
5. **Scene 5（`73s – 92s`）：《月夜·吉维尼泻湖》终章** — [`src/scenes/scene5_twilight.js`](src/scenes/scene5_twilight.js)
   - 远岸透出暖琥珀灯光的石拱船屋、相伴游过水面碎金月影的双天鹅、飘浮夜空的弯月与星辰、逐帧升起的萤火虫，最终镜头轻柔上仰定格于月夜星空。

---

## 核心代码与渲染架构

- [`src/core/brushes.js`](src/core/brushes.js)：预渲染多方向/多厚度程序化油画笔触图章（`broad`、`impasto`、`dab`、`wisp`、`ripple`），模拟猪鬃刷毛质感与湿画法色彩混合。
- [`src/core/palette.js`](src/core/palette.js)：按世界横坐标连续插值的时间-色彩大气系统（破晓粉橙 → 晨翠青 → 正午钴蓝 → 日暮紫金 → 静夜群青），内置印象派补色抖动（`jitterMonetColor`）。
- [`src/core/painter.js`](src/core/painter.js)：复用型程序化场景绘件（分形山脊杨树林带、积雨云/暮云笔触团、动态水面波纹反射等）。
- [`src/core/canvas_fx.js`](src/core/canvas_fx.js)：法式亚麻画布细微织纹（Linen Weave）与光学柔光晕映（Optical Bloom）。
- [`src/world.js`](src/world.js)：世界总控器，融合 5 块预绘印象派天空板并按世界深度依次调度 5 个动态场景。
- [`scripts/prepare_audio.py`](scripts/prepare_audio.py)：FFmpeg 8 轨混音管线，将德彪西《月光》自然终曲段落与 6 轨分景自然环境音效混制为 `assets/audio/master_92s.wav`。
- [`scripts/render_video.mjs`](scripts/render_video.mjs)：无头 Chromium + 流式 RGBA 管道直推 FFmpeg 编码 1080p 与 720p 成片。

> 音乐与音效署名及公共领域/CC 许可详情见 [`CREDITS.md`](CREDITS.md)。

---

## 本地预览与复现

1. **浏览器实时交互预览**：
   ```bash
   python3 -m http.server 8000 --directory src
   # 访问 http://localhost:8000 （支持时间轴拖动与实时画帧）
   ```
2. **重混音轨与全片渲染**：
   ```bash
   python3 scripts/prepare_audio.py
   node scripts/render_video.mjs
   ```

# *Les Heures de Lumière · 光阴画境*

A 100% procedurally generated **Claude Monet Impressionist** one-take animated short film (`96.0s`, `2880 frames @ 30 fps`, `1920×1080`) on a continuous multiplane oil-brush canvas.

---

## Five Hours of Light · 五段连续光影诗篇

The camera glides along a single uninterrupted horizontal & perspective spline (`camX: 0 → 20790`) through five overlapping Impressionist landscapes from dawn to dusk:

| Time | Scene | French Title | Lighting & Living Details |
| :--- | :--- | :--- | :--- |
| `0s – 19s` | **1. Étretat Dawn** | *Falaise d'Étretat, Marée du Matin* | Emerging from raw flax canvas into morning mist; sculpted *Porte d'Aval* chalk arch & *L'Aiguille* stack, breaking surf foam, rocking Normandy fishing luggers, wheeling gulls, shimmering dawn sun reflection. |
| `18s – 39s` | **2. Argenteuil Regatta** | *Les Régates à Argenteuil* | Curved Seine shoreline transition; tall swaying poplars & red-roofed villas, sailboats heeling in travelling wind gusts with fluttering pennants & broken water reflections, swaying foreground reeds. |
| `38s – 58s` | **3. Giverny Flower Path** | *Le Jardin de l'Artiste à Giverny* | World-anchored gravel *Grande Allée* flanked by swaying irises, nasturtiums, and four rose-draped wooden trellis arches leading toward Monet's pink-stucco & slate-roofed house; fluttering butterflies & drifting petals. |
| `57s – 78s` | **4. Rouen Cathedral Sunset** | *La Cathédrale de Rouen au Soleil Couchant* | Stone cobblestone plaza bathed in warm sunset light; densely layered golden-ochre & cobalt-violet impasto Gothic facade, twin towers, rose window & triple portals, gabled square townhouses, and circling doves. |
| `76s – 96s` | **5. Venice Dusk** | *San Giorgio Maggiore au Crépuscule* | Venetian lagoon bathed in crimson-magenta twilight; Palladian basilica, dome & campanile silhouette with warm lantern windows, three gliding gondolas with lanterns & ripples, blinking fireflies, stars, and painterly fade back to linen canvas title card. |

---

## Architecture · 技术实现

- **Procedural Oil-Brush Engine** ([`src/engine.py`](src/engine.py) & [`src/brush_native.cpp`](src/brush_native.cpp)):
  - 24 procedural 4-level mip-mapped oil brushstroke & paint-thickness sprites (`DASH`, `DAB`, `SCUM`, `GLOW`) generated in pure NumPy.
  - High-speed multi-threaded C++17 tile-binned rasterizer (`build/libbrush.so`, compiled automatically on first import) blending ~25k–42k depth-sorted world-space brushstrokes per frame.
  - Post-rasterization physical oil-on-linen shading: flax canvas weave in thin paint areas, directional Sobel impasto relief, canvas grain, quarter-resolution multi-scale highlight bloom, and vignette.
- **Continuous World & Camera Spline** ([`src/world.py`](src/world.py)):
  - PCHIP monotone cubic Hermite camera trajectory across `96.0s`, multiplane perspective projection, and coherent 2D Perlin-style travelling wind gusts (`Env.wind`).
- **Synchronized Soundtrack** ([`src/audio_mix.py`](src/audio_mix.py)):
  - Combines Claude Debussy's *Première Arabesque* (performed by Patrizia Prati) with scene-matched ocean surf, garden birdsong, cathedral bells, and evening pond ambience plus procedural stereo wind modulated by `Env.wind()`. See [`CREDITS.md`](CREDITS.md) for full open-license attributions.

---

## Reproducing Locally · 本地复现构建

### Requirements
- Python 3.10+, `numpy`, `pillow`
- `g++` (C++17 with `-pthread`)
- `ffmpeg` / `ffprobe`

### 1. Build the Synchronized 96s Audio Track
```bash
python3 src/audio_mix.py assets/audio/master_96s.wav
```

### 2. Audit Keyframes (`1080p` stills)
```bash
python3 src/render.py audit output/audit 1080
```

### 3. Render Full 1080p @ 30fps MP4 Master
```bash
python3 src/render.py pipe 0 2880 1080 \
  | ffmpeg -y -f rawvideo -pixel_format rgb24 -video_size 1920x1080 -framerate 30 -i - \
    -i assets/audio/master_96s.wav \
    -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
    -c:a aac -b:a 256k -movflags +faststart \
    output/les_heures_de_lumiere_1080p.mp4
```

---

## High-Bitrate Video Downloads · 高清成片下载

Large high-bitrate video masters (both this new v2 edition and the original v1 1080p high-bitrate edition) are hosted directly in **GitHub Releases** on this repository for one-click download without split-part reassembly.

# *Un Dimanche sur la Seine · 塞纳河畔的星期日* (v3)

A 100% procedurally painted **3D Claude Monet Impressionist** one-take animated short film (`120.0s`, `3600 frames @ 30 fps`, `1920×1080`) built directly on [**CodePaint-Engine**](https://github.com/yiggeror/CodePaint-Engine).

---

## Four Continuous 3D Acts · 四幕真三维连续长镜头

1. **`0s – 28s` · Morning Poppy Hill & Kite Boy** (*Les Coquelicots du Matin*)
   - Swoops from misty sunlit hillside down beside an articulated boy running with his terrier dog & soaring diamond kite (`rig3.py`), framed by dry-stone paddock walls, grazing Normandy cows, apple orchard, and a hillside farmhouse.
2. **`28s – 54s` · Stone Railway Viaduct & Steam Train** (*Le Train sur le Viaduc*)
   - Glides across the shimmering Seine as a vintage emerald-and-brass steam locomotive crosses the 5-arch ashlar stone viaduct puffing wind-drifted steam reflected in the water, then **swoops underneath the central vaulted stone arch**.
3. **`54s – 84s` · Noon Regatta & Willow Cove** (*Les Régates de Midi*)
   - Tracks & overtakes a heeling racing sloop with articulated crew, bow foam V-wakes (`RIPPLE`), wheeling Barn Swallows, and riverside village houses, before brushing past hanging weeping willow tendrils (`OVER`) and gliding white swans.
4. **`84s – 120s` · Sunset Guinguette & Twilight Village** (*Crépuscule à la Guinguette*)
   - Bathed in crimson-gold sunset & cobalt-indigo twilight: riverside Guinguette café with striped awnings and festoon lanterns, moored skiffs, 10-cottage riverside town with lit stone church spire, blinking fireflies, stars, and painterly linen dissolve.

---

## Technical Stack · 技术实现

- **Core Engine**: `CodePaint-Engine` (`anim.core.Engine`, `anim.time.TimeWarp`, `anim.paint.engine` Numba/OpenCV bristle rasterizer, `anim.paint.world3` 3D perspective camera, LOD & deterministic spatial hash `Field`s, `anim.paint.light` color keyframes, `anim.audio`, `anim.output`).
- **3D Soundtrack** ([`src/audio_mix3.py`](src/audio_mix3.py)): 100% genuine classical piano recordings (Debussy *Première Arabesque* → Ravel *Pavane pour une infante défunte*) + 13 spatialized real field recordings positioned in 3D world coordinates with stereo panning, distance falloff, valley convolution reverb, and under-arch low-pass filtering. See [`CREDITS.md`](CREDITS.md).

---

## Local Commands · 本地复现

```bash
pip install -e .
PYTHONPATH=src python3 src/audio_mix3.py assets/audio/master_v3_120s.wav
PYTHONPATH=src python3 src/render3.py audit output/audit_v3 1080
PYTHONPATH=src python3 src/render3.py preview output/preview_v3_15s.mp4 540
```

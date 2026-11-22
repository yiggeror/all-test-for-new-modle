# *Rêveries de Monet · 莫奈光影梦境* (v4)

A 100% procedurally painted **6-scene 3D Claude Monet Impressionist** animated short film (`120.0s`, `3600 frames @ 30 fps`, `1920×1080` + `720p`) built on [**CodePaint-Engine**](https://github.com/yiggeror/CodePaint-Engine).

---

## Six Living Impressionist Worlds · 六大三维莫奈光影梦境

1. **`0s – 20s` · 阿让特伊红罂粟与矢车菊花山 (*Les Coquelicots à Argenteuil*)**
   - Monotonic sunlit poppy & cornflower hillside with strict per-layer `depth_order`, cherry blossom orchard, stone farmhouse, grazing cows, strolling couples with parasols, morning sunbeams, drifting petals, and running kite boy + bounding terrier.
2. **`20s – 40s` · 吉维尼紫藤睡莲池 (*Le Bassin aux Nymphéas à Giverny*)**
   - Enchanted emerald Japanese footbridge draped in cascading violet wisteria racemes, 320+ floating pink/coral/ivory waterlilies, animated golden & crimson Koi swimming below ripples, sweeping weeping willows, pink villa, and calm mirror reflections.
3. **`40s – 60s` · 阿让特伊五孔石拱桥与帆船竞渡 (*Le Viaduc d'Argenteuil*)**
   - 5-arch ashlar stone railway viaduct with emerald-brass vintage steam locomotive trailing sunlit pearl-lavender steam clouds, plus 5 racing sailboats constrained strictly to arch centerlines (zero pier collision).
4. **`60s – 80s` · 鲁昂大教堂鎏金紫雾黄昏 (*La Cathédrale de Rouen*)**
   - Towering Gothic limestone facade bathed in molten sunset gold & cobalt-violet shadow, glowing stained-glass Rose Window, twin asymmetric spires (*Tour Saint-Romain* & *Tour de Beurre*), flower market stalls, warm café lanterns, and 32 spiraling white doves.
5. **`80s – 100s` · 普罗旺斯薰衣草海与风车晚霞 (*Champs de Lavande en Provence*)**
   - Undulating royal-violet and magenta-coral lavender furrows under blazing sunset clouds, turning hilltop limestone windmill, Provençal stone Mas farmhouse, Mediterranean cypresses, foreground sunflowers, and twilight fireflies.
6. **`100s – 120s` · 威尼斯圣乔治马焦雷月夜泻湖 (*Saint-Georges Majeur au Crépuscule*)**
   - Luminous turquoise Palladian dome, crimson brick Campanile, glowing palazzi along twilight ripples, 3 articulated rowing gondolas with bow lanterns, 140 twinkling stars, soft crescent moon, and painterly linen canvas dissolve.

---

## Soundtrack & SFX · 古典交响配乐与真实空间实录

100% genuine classical recordings and natural field recordings from Wikimedia Commons ([`src/audio_mix4.py`](src/audio_mix4.py)), zero synthesized SFX:
- **Music**: Claude Debussy *Arabesque No. 1* (`0–42s`) → Claude Debussy *La cathédrale engloutie* (`38.5–82s`) → Maurice Ravel *Pavane pour une infante défunte* (`78.5–120s`).
- **Field SFX**: Eurasian Skylark, Barn Swallow, Terrier barking, Babbling brook & Dordogne pond, Cogwheel steam locomotive & steam whistle, Seine waves & café chatter, Evening French church bells, Flapping doves, Provence twilight *Cicada orni*, Evening breeze.

---

## Local Commands · 本地验证与渲染

```bash
pip install -e .
PYTHONPATH=src python3 src/render4.py test
PYTHONPATH=src python3 src/render4.py audit output/audit_v4
PYTHONPATH=src python3 src/audio_mix4.py output/master_v4_120s.wav
```

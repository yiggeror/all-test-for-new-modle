#include "paint_core.hpp"
#include <chrono>
#include <iostream>

using namespace monet;

// Paint a dense, authentic Monet foliage mass with depth-layered leaf clusters
void paintFoliageCanopy(OilCanvas &cv, float cx, float cy, float rx, float ry,
                        RGB shadowCol, RGB midCol, RGB lightCol, RGB sunTipCol,
                        int count, uint32_t seed, float minSize = 7.0f, float maxSize = 20.0f) {
  RNG rng(seed);
  // Layer 1: Cool deep interior shadow dabs
  for (int i = 0; i < count * 0.35; ++i) {
    float ang = rng.range(0.0f, 6.28318f);
    float rad = std::sqrt(rng.next());
    float x = cx + std::cos(ang) * rx * rad;
    float y = cy + std::sin(ang) * ry * rad + ry * 0.08f;
    float n = fbm2D(x * 0.012f, y * 0.012f, 3, seed);
    if (n < 0.30f) continue;
    RGB col = jitterColor(mixRGB(shadowCol, midCol, n * 0.45f), rng, 0.05f, 0.08f, 0.04f);
    paintDab(cv, x, y, rng.range(minSize * 1.1f, maxSize * 1.2f), rng.range(minSize * 0.45f, maxSize * 0.55f),
             rng.range(-1.4f, 1.4f), col, rng.range(0.55f, 0.85f), 0.35f, seed + i * 17, 7);
  }
  // Layer 2: Rich midtone botanical leaf touches
  for (int i = 0; i < count * 0.42; ++i) {
    float ang = rng.range(0.0f, 6.28318f);
    float rad = std::sqrt(rng.next());
    float x = cx + std::cos(ang) * rx * rad;
    float y = cy + std::sin(ang) * ry * rad;
    float upper = clampf(0.55f - (y - cy) / (ry * 2.0f) + (cx - x) / (rx * 4.5f), 0.0f, 1.0f);
    RGB col = jitterColor(mixRGB(midCol, lightCol, upper * 0.8f), rng, 0.07f, 0.09f, 0.05f);
    paintDab(cv, x, y, rng.range(minSize, maxSize), rng.range(minSize * 0.38f, maxSize * 0.48f),
             rng.range(-1.6f, 1.6f), col, rng.range(0.65f, 0.90f), 0.55f, seed + 5000 + i * 23, 6);
  }
  // Layer 3: Crisp sunlit crown flecks catching upper-left daylight
  for (int i = 0; i < count * 0.23; ++i) {
    float ang = rng.range(0.0f, 6.28318f);
    float rad = std::sqrt(rng.next()) * 0.95f;
    float x = cx + std::cos(ang) * rx * rad - rx * 0.06f;
    float y = cy + std::sin(ang) * ry * rad - ry * 0.14f;
    float upper = clampf(0.75f - (y - cy) / (ry * 1.6f), 0.0f, 1.0f);
    if (rng.next() > upper + 0.25f) continue;
    RGB col = jitterColor(mixRGB(lightCol, sunTipCol, upper), rng, 0.08f, 0.10f, 0.06f);
    paintDab(cv, x, y, rng.range(minSize * 0.65f, maxSize * 0.72f), rng.range(minSize * 0.30f, maxSize * 0.36f),
             rng.range(-1.8f, 1.8f), col, rng.range(0.75f, 0.94f), 0.85f, seed + 9000 + i * 31, 5);
  }
}

int main() {
  auto t0 = std::chrono::steady_clock::now();
  const int W = 1920, H = 1080;
  // Warm cream Belgian linen ground
  OilCanvas cv(W, H, true, hexRGB(0xEAE2CE));
  RNG rng(20261114ULL);

  // 1. Sky & Upper Giverny Garden Light (criss-crossed Impressionist brushwork, ~18,000 strokes)
  RGB skyTop = hexRGB(0x7DA7CE);
  RGB skyMid = hexRGB(0xA9C6DE);
  RGB skyGlow = hexRGB(0xE8DEC2);
  for (int y = 0; y < 440; y += 7) {
    float v = clampf(y / 440.0f, 0.0f, 1.0f);
    RGB base = v < 0.55f ? mixRGB(skyTop, skyMid, v / 0.55f) : mixRGB(skyMid, skyGlow, (v - 0.55f) / 0.45f);
    for (int x = 0; x < W; x += 14) {
      float n = fbm2D(x * 0.005f, y * 0.008f, 3, 77);
      RGB col = jitterColor(base, rng, 0.055f, 0.06f, 0.045f);
      float ang = (n - 0.5f) * 0.85f + rng.range(-0.32f, 0.32f);
      paintDab(cv, x + rng.range(-6.0f, 6.0f), y + rng.range(-4.0f, 4.0f),
               rng.range(24.0f, 42.0f), rng.range(8.0f, 14.0f), ang,
               col, rng.range(0.45f, 0.72f), 0.24f, 1000 + x * 3 + y * 13, 8);
    }
  }
  // Fine luminous sky over-strokes
  for (int i = 0; i < 6000; ++i) {
    float x = rng.range(0, W), y = rng.range(0, 410);
    float v = y / 410.0f;
    RGB base = mixRGB(skyMid, skyGlow, v);
    if (rng.next() < 0.35f) base = shiftWarm(base, 0.35f, hexRGB(0xFFF3D4));
    paintDab(cv, x, y, rng.range(10.0f, 22.0f), rng.range(4.0f, 7.5f),
             rng.range(-0.45f, 0.45f), jitterColor(base, rng, 0.05f, 0.05f, 0.04f),
             rng.range(0.38f, 0.65f), 0.38f, 20000 + i, 6);
  }

  // 2. Distant Sunlit Bamboo & Giverny Garden Grove behind the pond (~35,000 strokes)
  paintFoliageCanopy(cv, 260, 290, 320, 175, hexRGB(0x2E5146), hexRGB(0x4E7C57), hexRGB(0x88AD64), hexRGB(0xD3DF8B), 4500, 301, 6, 17);
  paintFoliageCanopy(cv, 620, 265, 290, 165, hexRGB(0x2B4C48), hexRGB(0x4A785A), hexRGB(0x81A969), hexRGB(0xCBD789), 4200, 302, 6, 16);
  paintFoliageCanopy(cv, 980, 250, 310, 160, hexRGB(0x2F534C), hexRGB(0x52805F), hexRGB(0x8FB46D), hexRGB(0xDCE394), 4500, 303, 6, 16);
  paintFoliageCanopy(cv, 1340, 265, 300, 165, hexRGB(0x2C4D46), hexRGB(0x4D7B57), hexRGB(0x89AE63), hexRGB(0xD6DF8A), 4200, 304, 6, 17);
  paintFoliageCanopy(cv, 1710, 280, 320, 180, hexRGB(0x2A4B44), hexRGB(0x487654), hexRGB(0x84AA62), hexRGB(0xCDD986), 4500, 305, 6, 17);

  // Delicate background bamboo/reed stalks near the far pond bank
  for (int i = 0; i < 420; ++i) {
    float x = rng.range(10, W - 10);
    float hTop = rng.range(240, 340);
    float hBot = 455 + rng.range(-12, 16);
    float lean = rng.range(-14, 14);
    RGB stalkCol = jitterColor(mixRGB(hexRGB(0x557B52), hexRGB(0x96B56A), rng.next()), rng, 0.05f, 0.07f, 0.05f);
    paintStroke(cv, {x, hBot, x + lean, hTop, rng.range(-6, 6), rng.range(2.2f, 4.2f), 0.72f, 0.35f, 0.25f, 4, 0.04f, stalkCol, {}, false, static_cast<uint32_t>(4100 + i)});
  }

  // 3. Water Lily Pond Surface (inverted foliage reflection + 32,000 crisp shimmering water oil strokes)
  // First lay deep pond tonal base + reflected greenery/sky shimmer
  for (int y = 445; y < H; y += 5) {
    float v = (y - 445.0f) / (H - 445.0f);
    for (int x = 0; x < W; x += 12) {
      float wave = std::sin(x * 0.015f + y * 0.06f) * 0.5f + 0.5f;
      float skyMirror = std::exp(-std::pow((x - 960.0f) / 480.0f, 2.0f)) * (1.0f - v * 0.45f);
      RGB deepPond = mixRGB(hexRGB(0x274B58), hexRGB(0x325E66), wave);
      RGB greenRefl = mixRGB(hexRGB(0x3B6653), hexRGB(0x5C8559), fbm2D(x * 0.008f, y * 0.012f, 3, 55));
      RGB skyRefl = mixRGB(hexRGB(0x7DA7C4), hexRGB(0xD8D7BF), wave * 0.65f);
      RGB base = mixRGB(deepPond, greenRefl, 0.55f * (1.0f - skyMirror * 0.55f));
      base = mixRGB(base, skyRefl, skyMirror * 0.65f);
      if (v > 0.6f) base = shiftCool(base, (v - 0.6f) * 0.4f, hexRGB(0x21355C));
      RGB col = jitterColor(base, rng, 0.065f, 0.08f, 0.05f);
      paintDab(cv, x + rng.range(-5, 5), y + rng.range(-2, 2),
               rng.range(18.0f, 38.0f), rng.range(4.0f, 8.5f), rng.range(-0.08f, 0.08f),
               col, rng.range(0.55f, 0.82f), 0.32f, 50000 + x * 7 + y * 19, 7);
    }
  }
  // Fine horizontal broken-color shimmering touches across water
  for (int i = 0; i < 14000; ++i) {
    float x = rng.range(0, W);
    float y = rng.range(448, H - 2);
    float v = (y - 448.0f) / (H - 448.0f);
    float skyMirror = std::exp(-std::pow((x - 960.0f) / 440.0f, 2.0f));
    float pick = rng.next();
    RGB col;
    if (pick < 0.26f * skyMirror + 0.06f) {
      col = mixRGB(hexRGB(0xB8CFE0), hexRGB(0xF2E9CF), rng.next());
    } else if (pick < 0.55f) {
      col = mixRGB(hexRGB(0x457463), hexRGB(0x7FA66D), rng.next());
    } else {
      col = mixRGB(hexRGB(0x284D63), hexRGB(0x3E7684), rng.next());
    }
    col = jitterColor(col, rng, 0.06f, 0.08f, 0.05f);
    paintDab(cv, x, y, lerpf(10.0f, 26.0f, v), lerpf(1.8f, 4.4f, v), rng.range(-0.06f, 0.06f),
             col, rng.range(0.55f, 0.85f), 0.48f, 70000 + i, 5);
  }

  // 4. Sculpted Giverny Japanese Arched Footbridge (100% painterly wooden strokes — zero rigid vectors)
  auto bridgeArchY = [](float x) {
    float u = (x - 960.0f) / 620.0f; // -1..+1 across bridge span
    return 378.0f + u * u * 112.0f;
  };
  // Bridge reflection in water (rippling soft green/violet vertical-broken strokes)
  for (int x = 350; x <= 1570; x += 6) {
    float by = bridgeArchY(x);
    float waterLine = 465.0f;
    float reflY = waterLine + (waterLine - by) * 0.92f + std::sin(x * 0.04f) * 5.0f;
    if (reflY > 455 && reflY < H - 20) {
      RGB reflC = jitterColor(mixRGB(hexRGB(0x446858), hexRGB(0x3D516A), rng.next()), rng, 0.05f, 0.06f, 0.04f);
      paintDab(cv, x + rng.range(-4, 4), reflY, rng.range(12, 22), rng.range(3.0f, 5.5f),
               rng.range(-0.1f, 0.1f), reflC, 0.42f, 0.25f, 88000 + x, 5);
    }
  }

  // Timber piers descending cleanly into water with mossy waterlines
  float pierXs[] = {460, 690, 960, 1230, 1460};
  for (int pi = 0; pi < 5; ++pi) {
    float px = pierXs[pi];
    float topY = bridgeArchY(px) + 12.0f;
    float botY = 535.0f + (pi == 2 ? 12.0f : 0.0f);
    for (int k = 0; k < 22; ++k) {
      float t = k / 21.0f;
      float y = lerpf(topY, botY, t);
      RGB col = t > 0.72f ? hexRGB(0x395B48) : mixRGB(hexRGB(0x51785B), hexRGB(0x384B59), 0.45f);
      paintStroke(cv, {px + rng.range(-3, 3), y, px + rng.range(-3, 3), y + 18.0f, rng.range(-1.5f, 1.5f),
                       rng.range(7.0f, 11.0f), 0.85f, 0.65f, 0.20f, 6, 0.04f, jitterColor(col, rng, 0.04f, 0.06f, 0.04f), {}, false, static_cast<uint32_t>(91000 + pi * 50 + k)});
    }
    // Water ripple around pier base
    for (int r = 0; r < 6; ++r) {
      paintDab(cv, px + rng.range(-16, 16), botY + rng.range(-3, 4), rng.range(18, 34), 2.5f, 0.0f,
               jitterColor(hexRGB(0x9BC4C7), rng, 0.04f, 0.05f, 0.04f), 0.65f, 0.45f, 92000 + pi * 20 + r, 4);
    }
  }

  // Bridge deck beams & vertical balusters built strictly out of small overlapping oil strokes
  for (int x = 340; x <= 1580; x += 6) {
    float yDeck = bridgeArchY(x);
    float yDeckNext = bridgeArchY(x + 8);
    // Underside shadow beam
    paintStroke(cv, {static_cast<float>(x), yDeck + 13.0f, static_cast<float>(x + 9), yDeckNext + 13.0f, 0.0f,
                     9.0f, 0.88f, 0.55f, 0.18f, 6, 0.04f, jitterColor(hexRGB(0x39585A), rng, 0.05f, 0.06f, 0.04f), {}, false, static_cast<uint32_t>(93000 + x)});
    // Deck sunlit moss-green plank edge
    paintStroke(cv, {static_cast<float>(x), yDeck + 4.0f, static_cast<float>(x + 9), yDeckNext + 4.0f, 0.0f,
                     8.0f, 0.90f, 0.72f, 0.20f, 6, 0.05f, jitterColor(hexRGB(0x7DA86B), rng, 0.06f, 0.08f, 0.05f), {}, false, static_cast<uint32_t>(95000 + x)});
  }
  // Vertical railing posts & diagonal lattice slats
  for (int x = 355; x <= 1565; x += 26) {
    float yDeck = bridgeArchY(x);
    float yRail = yDeck - 52.0f;
    RGB postCol = jitterColor(hexRGB(0x5E8C68), rng, 0.06f, 0.07f, 0.05f);
    paintStroke(cv, {static_cast<float>(x), yDeck + 3.0f, static_cast<float>(x + rng.range(-1.5f, 1.5f)), yRail, 0.0f,
                     5.5f, 0.88f, 0.70f, 0.22f, 5, 0.04f, postCol, {}, false, static_cast<uint32_t>(97000 + x)});
    // Lattice crossbars between posts
    if (x + 26 <= 1565) {
      float yNextDeck = bridgeArchY(x + 26);
      float yNextRail = yNextDeck - 52.0f;
      RGB latCol = jitterColor(hexRGB(0x6D9C6D), rng, 0.06f, 0.07f, 0.05f);
      paintStroke(cv, {static_cast<float>(x), yRail + 8.0f, static_cast<float>(x + 26), yNextDeck - 6.0f, 0.0f,
                       3.2f, 0.75f, 0.50f, 0.25f, 4, 0.04f, latCol, {}, false, static_cast<uint32_t>(99000 + x)});
      paintStroke(cv, {static_cast<float>(x), yDeck - 6.0f, static_cast<float>(x + 26), yNextRail + 8.0f, 0.0f,
                       3.2f, 0.75f, 0.50f, 0.25f, 4, 0.04f, latCol, {}, false, static_cast<uint32_t>(101000 + x)});
    }
  }
  // Top arched handrail with warm sunlit top edge
  for (int x = 340; x <= 1580; x += 7) {
    float y0 = bridgeArchY(x) - 52.0f;
    float y1 = bridgeArchY(x + 8) - 52.0f;
    paintStroke(cv, {static_cast<float>(x), y0 + 2.0f, static_cast<float>(x + 8), y1 + 2.0f, 0.0f,
                     7.0f, 0.90f, 0.72f, 0.15f, 6, 0.04f, jitterColor(hexRGB(0x558163), rng, 0.05f, 0.06f, 0.04f), {}, false, static_cast<uint32_t>(103000 + x)});
    paintStroke(cv, {static_cast<float>(x), y0 - 2.0f, static_cast<float>(x + 8), y1 - 2.0f, 0.0f,
                     3.6f, 0.92f, 0.85f, 0.18f, 4, 0.05f, jitterColor(hexRGB(0xB4D186), rng, 0.06f, 0.08f, 0.05f), {}, false, static_cast<uint32_t>(105000 + x)});
  }

  // Overhanging Wisteria Racemes draping across the bridge arch (thousands of tiny lavender/violet/cream blossom dabs)
  for (int rx = 380; rx <= 1540; rx += 16) {
    float baseY = bridgeArchY(rx) - 56.0f + rng.range(-14.0f, 12.0f);
    float dropLen = rng.range(38.0f, 108.0f) * (0.65f + 0.55f * std::sin((rx - 380.0f) * 0.012f));
    int buds = static_cast<int>(dropLen * 0.85f);
    for (int bi = 0; bi < buds; ++bi) {
      float u = bi / static_cast<float>(buds);
      float bx = rx + rng.range(-8.0f, 8.0f) * (1.0f - u * 0.55f);
      float by = baseY + u * dropLen;
      RGB wBase = u < 0.35f ? hexRGB(0x74589F) : (u < 0.72f ? hexRGB(0x9E84C9) : hexRGB(0xD3BFE8));
      if (rng.next() < 0.22f) wBase = hexRGB(0xEFE3F4);
      RGB col = jitterColor(wBase, rng, 0.06f, 0.09f, 0.05f);
      paintDab(cv, bx, by, rng.range(4.5f, 8.5f), rng.range(3.0f, 5.0f), rng.range(0.6f, 2.5f),
               col, rng.range(0.75f, 0.95f), 0.78f, 110000 + rx * 29 + bi, 4);
    }
    // Wisteria green leaf tufts above each cluster
    for (int li = 0; li < 8; ++li) {
      paintDab(cv, rx + rng.range(-12, 12), baseY - rng.range(4, 18), rng.range(7, 13), rng.range(3.5f, 5.5f),
               rng.range(-1.4f, 1.4f), jitterColor(hexRGB(0x5E8E5A), rng, 0.06f, 0.08f, 0.05f),
               0.85f, 0.60f, 120000 + rx * 13 + li, 5);
    }
  }

  // 5. Lush Foreground Water Lily Pads & Multi-Petaled Blossoms (perspective scaled, ~8,000 fine strokes)
  for (int cluster = 0; cluster < 46; ++cluster) {
    float depth = std::pow(rng.next(), 0.72f); // 0 = near bridge, 1 = foreground bottom
    float cy = lerpf(545.0f, 1025.0f, depth);
    float cx = rng.range(50.0f, W - 50.0f);
    int padsInCluster = rng.range(3, 8);
    for (int pi = 0; pi < padsInCluster; ++pi) {
      float px = cx + rng.range(-95.0f, 95.0f) * (0.45f + 0.65f * depth);
      float py = cy + rng.range(-26.0f, 26.0f) * (0.45f + 0.65f * depth);
      float radX = lerpf(16.0f, 52.0f, depth) * rng.range(0.78f, 1.22f);
      float radY = radX * 0.34f;

      // Cool dark water shadow rim under pad
      for (int s = 0; s < 10; ++s) {
        float ang = rng.range(0.0f, 6.283f);
        paintDab(cv, px + std::cos(ang) * radX * 0.55f, py + std::sin(ang) * radY * 0.55f + 3.0f,
                 radX * 0.55f, radY * 0.45f, 0.05f, hexRGB(0x1D3944), 0.48f, 0.15f, 130000 + cluster * 100 + pi * 10 + s, 4);
      }

      // Sculpted pad leaf out of radial curved oil strokes (leaving V-notch!)
      float notchAng = rng.range(-0.6f, 0.6f) + (pi % 2 ? 2.6f : -0.4f);
      int leafStrokes = static_cast<int>(lerpf(14, 34, depth));
      for (int ls = 0; ls < leafStrokes; ++ls) {
        float a = rng.range(0.0f, 6.28318f);
        float diff = std::fmod(std::fabs(a - notchAng) + 6.28318f, 6.28318f);
        if (diff < 0.32f || diff > 6.28318f - 0.32f) continue;
        float r0 = rng.range(0.12f, 0.35f);
        float r1 = rng.range(0.75f, 1.02f);
        RGB leafBase = mixRGB(hexRGB(0x3D6E48), hexRGB(0x7DA85E), rng.next());
        if (std::sin(a) < -0.15f) leafBase = shiftWarm(leafBase, 0.32f, hexRGB(0xB8CE72));
        RGB col = jitterColor(leafBase, rng, 0.06f, 0.08f, 0.05f);
        paintStroke(cv, {
          px + std::cos(a) * radX * r0, py + std::sin(a) * radY * r0,
          px + std::cos(a) * radX * r1, py + std::sin(a) * radY * r1,
          rng.range(-2.0f, 2.0f), lerpf(2.8f, 6.5f, depth), 0.88f, 0.68f, 0.18f, 4, 0.04f,
          col, {}, false, static_cast<uint32_t>(140000 + cluster * 300 + pi * 40 + ls)
        });
      }

      // Occasional rose-pink or ivory multi-petaled water lily flower resting on pad
      if (rng.next() < 0.36f) {
        float fx = px + rng.range(-radX * 0.25f, radX * 0.25f);
        float fy = py - 3.0f;
        float fSize = lerpf(8.0f, 22.0f, depth);
        bool roseTint = rng.next() < 0.62f;
        RGB outerPetal = roseTint ? hexRGB(0xDE889E) : hexRGB(0xECE6DB);
        RGB innerPetal = roseTint ? hexRGB(0xFAD6DF) : hexRGB(0xFFFDF5);
        for (int pt = 0; pt < 14; ++pt) {
          float pa = -3.0f + (pt / 13.0f) * 3.1f + rng.range(-0.18f, 0.18f);
          float pl = fSize * rng.range(0.55f, 0.95f);
          RGB pCol = jitterColor(pt < 7 ? outerPetal : innerPetal, rng, 0.04f, 0.06f, 0.04f);
          paintStroke(cv, {
            fx, fy + 2.0f,
            fx + std::cos(pa) * pl * 1.15f, fy + std::sin(pa) * pl * 0.55f - 2.0f,
            rng.range(-1.5f, 1.5f), lerpf(2.2f, 4.6f, depth), 0.92f, 0.85f, 0.12f, 3, 0.03f,
            pCol, {}, false, static_cast<uint32_t>(180000 + cluster * 100 + pi * 20 + pt)
          });
        }
        // Golden stamen center
        for (int st = 0; st < 4; ++st) {
          paintDab(cv, fx + rng.range(-2.5f, 2.5f), fy - 1.5f, fSize * 0.28f, fSize * 0.20f,
                   rng.range(-1.0f, 1.0f), hexRGB(0xF5BE42), 0.95f, 0.95f, 190000 + cluster * 20 + st, 3);
        }
      }
    }
  }

  // 6. Framing Weeping Willow Curtains on left & right foreground margins (~14,000 delicate drooping frond touches)
  auto paintWillowSide = [&](float xStart, float xEnd, uint32_t sideSeed) {
    RNG wrng(sideSeed);
    int strands = 95;
    for (int s = 0; s < strands; ++s) {
      float bx = wrng.range(xStart, xEnd);
      float topY = wrng.range(-30.0f, 90.0f);
      float len = wrng.range(420.0f, 840.0f);
      float sway = wrng.range(-24.0f, 24.0f);
      // Thin trailing twig spine
      int segs = static_cast<int>(len / 14.0f);
      for (int k = 0; k < segs; ++k) {
        float u = k / static_cast<float>(segs);
        float px = bx + sway * u * u + std::sin(u * 4.5f + s) * 8.0f;
        float py = topY + u * len;
        RGB leafC = mixRGB(hexRGB(0x3B6644), hexRGB(0x9BC163), clampf(u * 0.7f + wrng.next() * 0.45f, 0.0f, 1.0f));
        if (u > 0.55f && wrng.next() < 0.35f) leafC = shiftWarm(leafC, 0.38f, hexRGB(0xDDE57E));
        paintDab(cv, px + wrng.range(-4, 4), py, wrng.range(10.0f, 18.0f), wrng.range(2.6f, 4.6f),
                 1.57f + wrng.range(-0.22f, 0.22f), jitterColor(leafC, wrng, 0.06f, 0.08f, 0.05f),
                 wrng.range(0.70f, 0.92f), 0.65f, sideSeed + s * 100 + k, 4);
      }
    }
  };
  paintWillowSide(-10.0f, 310.0f, 210000);
  paintWillowSide(1610.0f, 1930.0f, 220000);

  // Resolve with raking impasto lighting & Belgian linen weave
  std::vector<uint8_t> rgb;
  resolveCanvasToRGB24(cv, rgb, 0.10f, 0.18f);
  writePPM("output/audit/study_giverny.ppm", W, H, rgb);

  // Also save two 1:1 500x500 detail crops (Bridge wisteria center + foreground lilies)
  auto saveCrop = [&](const std::string &path, int cx0, int cy0, int cw, int ch) {
    std::vector<uint8_t> crop(static_cast<size_t>(cw) * ch * 3);
    for (int y = 0; y < ch; ++y) {
      for (int x = 0; x < cw; ++x) {
        size_t si = (static_cast<size_t>(cy0 + y) * W + (cx0 + x)) * 3;
        size_t di = (static_cast<size_t>(y) * cw + x) * 3;
        crop[di] = rgb[si]; crop[di + 1] = rgb[si + 1]; crop[di + 2] = rgb[si + 2];
      }
    }
    writePPM(path, cw, ch, crop);
  };
  saveCrop("output/audit/study_crop_bridge.ppm", 710, 180, 500, 500);
  saveCrop("output/audit/study_crop_lilies.ppm", 560, 560, 500, 500);

  auto t1 = std::chrono::steady_clock::now();
  double sec = std::chrono::duration<double>(t1 - t0).count();
  std::cout << "Study painted in " << sec << "s\n";
  return 0;
}

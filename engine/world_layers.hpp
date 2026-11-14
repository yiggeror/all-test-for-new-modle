#pragma once
#include "paint_core.hpp"
#include "camera.hpp"
#include <iostream>

namespace monet {

constexpr float LAYER_Y_PAD = 180.0f;
constexpr int LAYER_H = 1440; // 1080 + 2 * 180 vertical padding

struct PortalSprite {
  float anchorWorldX; // World X at depth 1.18 where sprite x=0 sits
  float depth = 1.18f;
  OilCanvas canvas;
};

struct WorldSceneData {
  OilCanvas skyLayer;       // d = 0.16, 4400 x 1440
  OilCanvas horizonLayer;   // d = 0.34, 7000 x 1440
  OilCanvas midgroundLayer; // d = 0.62, 11000 x 1440
  OilCanvas worldLayer;     // d = 1.00, 16600 x 1440 (grounded landmarks + terrain)
  PortalSprite portals[4];  // d = 1.18, 2500 x 1440 each
};

// Continuous shoreline/ground top Y in world coordinates (relative to Y_PAD=180)
inline float getTerrainTopY(float wx) {
  if (wx < 2700.0f) return 745.0f;
  if (wx < 3500.0f) return lerpf(745.0f, 645.0f, smoothstepf(2700.0f, 3500.0f, wx));
  if (wx < 5900.0f) return 645.0f;
  if (wx < 7200.0f) return lerpf(645.0f, 470.0f, smoothstepf(5900.0f, 7200.0f, wx));
  if (wx < 9200.0f) {
    float wave = std::sin((wx - 7200.0f) * 0.0022f) * 24.0f;
    return 470.0f + wave;
  }
  if (wx < 10200.0f) return lerpf(465.0f, 625.0f, smoothstepf(9200.0f, 10200.0f, wx));
  if (wx < 12300.0f) return 625.0f + std::sin((wx - 10200.0f) * 0.0018f) * 14.0f;
  if (wx < 13200.0f) return lerpf(628.0f, 732.0f, smoothstepf(12300.0f, 13200.0f, wx));
  return 732.0f;
}

// Feather left/right outer edges of a portal canvas smoothly to transparent (eliminates rectangular clip boxes!)
inline void featherPortalEdges(OilCanvas &cv, float fadeWidth = 220.0f) {
  for (int y = 0; y < cv.h; ++y) {
    for (int x = 0; x < cv.w; ++x) {
      float mL = smoothstepf(0.0f, fadeWidth, static_cast<float>(x));
      float mR = smoothstepf(0.0f, fadeWidth, static_cast<float>(cv.w - 1 - x));
      float m = std::min(mL, mR);
      if (m < 0.999f) {
        size_t idx = static_cast<size_t>(y) * cv.w + x;
        cv.a[idx] *= m;
        cv.height[idx] *= m;
      }
    }
  }
}

// Paint a billowing Monet cloud purely from layered curved oil brushstrokes
inline void paintPainterlyCloud(OilCanvas &cv, float cx, float cy, float rx, float ry,
                                RGB litCol, RGB midCol, RGB shadowCol, uint32_t seed, int strokes = 520) {
  RNG rng(seed);
  for (int i = 0; i < strokes * 0.35; ++i) {
    float ang = rng.range(0.0f, 6.283f);
    float r = std::pow(rng.next(), 0.6f);
    float x = cx + std::cos(ang) * rx * r;
    float y = cy + std::sin(ang) * ry * r * 0.72f + ry * 0.20f;
    float n = fbm2D(x * 0.009f, y * 0.014f, 3, seed);
    if (n < 0.25f) continue;
    RGB col = jitterColor(mixRGB(shadowCol, midCol, n * 0.55f), rng, 0.04f, 0.05f, 0.03f);
    paintDab(cv, x, y, rng.range(18.0f, 34.0f), rng.range(8.0f, 15.0f), rng.range(-0.35f, 0.35f),
             col, rng.range(0.35f, 0.62f), 0.18f, seed + i * 13, 8);
  }
  for (int i = 0; i < strokes * 0.42; ++i) {
    float u = rng.range(-0.92f, 0.92f);
    float arch = std::sqrt(std::max(0.0f, 1.0f - u * u));
    float x = cx + u * rx;
    float y = cy + rng.range(-arch * ry * 0.88f, ry * 0.25f);
    float heightFactor = clampf(0.65f - (y - cy) / (ry * 1.6f), 0.0f, 1.0f);
    RGB col = jitterColor(mixRGB(midCol, litCol, heightFactor), rng, 0.045f, 0.05f, 0.035f);
    paintDab(cv, x, y, rng.range(13.0f, 26.0f), rng.range(6.0f, 11.5f), rng.range(-0.42f, 0.42f),
             col, rng.range(0.48f, 0.78f), 0.42f, seed + 4000 + i * 17, 7);
  }
  for (int i = 0; i < strokes * 0.23; ++i) {
    float u = rng.range(-0.82f, 0.82f);
    float arch = std::sqrt(std::max(0.0f, 1.0f - u * u));
    float x = cx + u * rx + rng.range(-10.0f, 10.0f);
    float y = cy - arch * ry * rng.range(0.35f, 0.92f);
    RGB col = jitterColor(litCol, rng, 0.04f, 0.04f, 0.03f);
    paintDab(cv, x, y, rng.range(9.0f, 18.0f), rng.range(4.0f, 7.2f), rng.range(-0.55f, 0.55f),
             col, rng.range(0.60f, 0.88f), 0.75f, seed + 9000 + i * 23, 5);
  }
}

// Paint a small Normandy red-roofed stone cottage grounded firmly into garden hedges
inline void paintNormandyCottage(OilCanvas &cv, float cx, float baseY, float w, float h, uint32_t seed) {
  RNG rng(seed);
  // Warm limestone & plaster walls
  for (int y = static_cast<int>(baseY - h * 0.56f); y <= static_cast<int>(baseY + 8); y += 4) {
    for (int x = static_cast<int>(cx - w * 0.48f); x <= static_cast<int>(cx + w * 0.48f); x += 7) {
      bool shadedSide = x < cx - w * 0.10f;
      RGB wall = shadedSide ? hexRGB(0xA4A8BA) : hexRGB(0xE8DFC9);
      paintDab(cv, x + rng.range(-1.5f, 1.5f), y + rng.range(-1.5f, 1.5f), rng.range(8, 14), rng.range(4.5f, 7.0f),
               rng.range(-0.20f, 0.20f), jitterColor(wall, rng, 0.04f, 0.05f, 0.035f),
               0.94f, 0.55f, seed + x * 7 + y * 13, 5);
    }
  }
  // Pitched terracotta-crimson Normandy tile roof
  float roofTopY = baseY - h;
  float eaveY = baseY - h * 0.52f;
  for (int y = static_cast<int>(roofTopY); y <= static_cast<int>(eaveY); y += 4) {
    float t = (y - roofTopY) / std::max(1.0f, eaveY - roofTopY);
    float halfSpan = lerpf(w * 0.26f, w * 0.56f, t);
    for (int x = static_cast<int>(cx - halfSpan); x <= static_cast<int>(cx + halfSpan); x += 6) {
      bool litRoof = x > cx - halfSpan * 0.2f;
      RGB tile = litRoof ? mixRGB(hexRGB(0xC6553E), hexRGB(0xDF784C), rng.next())
                         : mixRGB(hexRGB(0x7E4253), hexRGB(0x9E504B), rng.next());
      paintDab(cv, x + rng.range(-1.5f, 1.5f), y + rng.range(-1.5f, 1.5f), rng.range(7, 12), rng.range(3.5f, 5.5f),
               rng.range(-0.30f, 0.30f), jitterColor(tile, rng, 0.05f, 0.07f, 0.04f),
               0.94f, 0.72f, seed + 5000 + x * 11 + y * 17, 5);
    }
  }
  // Chimney + windows + grounding lush hedge base so cottage sits firmly on hillside
  for (int k = 0; k < 6; ++k) {
    paintDab(cv, cx + w * 0.22f, roofTopY - k * 3.0f, 8.5f, 5.2f, 1.57f,
             jitterColor(hexRGB(0x8D635B), rng, 0.03f, 0.04f, 0.04f), 0.92f, 0.60f, seed + 9100 + k, 4);
  }
  paintDab(cv, cx + w * 0.14f, baseY - h * 0.28f, 9.0f, 5.5f, 1.57f, hexRGB(0x3B4460), 0.92f, 0.45f, seed + 9201, 4);
  paintDab(cv, cx - w * 0.28f, baseY - h * 0.26f, 8.0f, 5.0f, 1.57f, hexRGB(0x363D57), 0.90f, 0.45f, seed + 9202, 4);
  paintFoliageCanopy(cv, cx, baseY + 8.0f, w * 0.62f, 22.0f,
                     hexRGB(0x2D533C), hexRGB(0x4F834E), hexRGB(0x82B25D), hexRGB(0xB8D676),
                     220, seed + 9500, 4, 10);
}

// Build Layer 0: Seamless Continuous Diurnal Sky Panorama (4400 x 1440)
inline void buildSkyLayer(OilCanvas &sky) {
  const int W = 4400, H = LAYER_H;
  sky.resize(W, H, true, hexRGB(0x8BA5C4));
  RNG rng(1001ULL);

  struct SkyStop { float x; RGB top, mid, hor; };
  const SkyStop stops[] = {
    {0.0f,    hexRGB(0x6D7BA6), hexRGB(0xB8A6B8), hexRGB(0xF0C79C)}, // Dawn Seine mist
    {950.0f,  hexRGB(0x6A96C4), hexRGB(0xA4C2DC), hexRGB(0xEBDEC0)}, // Morning Giverny
    {1850.0f, hexRGB(0x4E89C9), hexRGB(0x8CBDE4), hexRGB(0xDFECED)}, // Sunlit Noon Poppies
    {2950.0f, hexRGB(0x706DA4), hexRGB(0xC98D93), hexRGB(0xF6BA76)}, // Golden Harvest Sunset
    {3800.0f, hexRGB(0x232E5C), hexRGB(0x43427A), hexRGB(0x88678D)}, // Twilight Lagoon
    {4400.0f, hexRGB(0x1B2349), hexRGB(0x313468), hexRGB(0x6B547D)}, // Deep Starlit Finale
  };

  auto sampleSkyAt = [&](float x, float y) -> RGB {
    int idx = 0;
    while (idx + 2 < 6 && x > stops[idx + 1].x) idx++;
    float u = smoothstepf(stops[idx].x, stops[idx + 1].x, x);
    RGB t = mixRGB(stops[idx].top, stops[idx + 1].top, u);
    RGB m = mixRGB(stops[idx].mid, stops[idx + 1].mid, u);
    RGB h = mixRGB(stops[idx].hor, stops[idx + 1].hor, u);
    float v = clampf((y - 60.0f) / 860.0f, 0.0f, 1.0f);
    return v < 0.52f ? mixRGB(t, m, v / 0.52f) : mixRGB(m, h, (v - 0.52f) / 0.48f);
  };

  // Pass 0: 100% opaque smooth atmospheric underpainting so zero bright canvas specks leak into twilight sky
  for (int y = 0; y < H; ++y) {
    for (int x = 0; x < W; ++x) {
      RGB base = sampleSkyAt(static_cast<float>(x), static_cast<float>(y));
      size_t idx = static_cast<size_t>(y) * W + x;
      sky.r[idx] = base.r;
      sky.g[idx] = base.g;
      sky.b[idx] = base.b;
      sky.a[idx] = 1.0f;
      sky.height[idx] = 0.08f;
    }
  }

  // Pass 1: Dense criss-crossed atmospheric sky brushstrokes (~85,000 strokes)
  for (int y = 6; y < H - 120; y += 8) {
    for (int x = 6; x < W - 6; x += 15) {
      RGB base = sampleSkyAt(static_cast<float>(x), static_cast<float>(y));
      float n = fbm2D(x * 0.0038f, y * 0.007f, 3, 41);
      RGB col = jitterColor(base, rng, 0.052f, 0.06f, 0.038f);
      float ang = (n - 0.5f) * 0.85f + rng.range(-0.30f, 0.30f);
      paintDab(sky, x + rng.range(-6, 6), y + rng.range(-4, 4),
               rng.range(24.0f, 42.0f), rng.range(8.5f, 14.5f), ang,
               col, rng.range(0.55f, 0.82f), 0.24f, 10000 + x * 3 + y * 11, 8);
    }
  }
  // Pass 2: Fine shimmering air touches
  for (int i = 0; i < 18000; ++i) {
    float x = rng.range(0, W), y = rng.range(20, H - 180);
    RGB col = jitterColor(sampleSkyAt(x, y), rng, 0.055f, 0.055f, 0.04f);
    paintDab(sky, x, y, rng.range(10.0f, 20.0f), rng.range(4.0f, 7.2f),
             rng.range(-0.42f, 0.42f), col, rng.range(0.42f, 0.70f), 0.36f, 90000 + i, 6);
  }

  // Rising Mist Dawn Sun (Impression, Sunrise focal point — elevated clearly above Seine horizon at ly = 415!)
  float sunX = 1120.0f, sunY = 415.0f;
  for (int ring = 0; ring < 340; ++ring) {
    float ang = rng.range(0.0f, 6.283f);
    float rad = std::pow(rng.next(), 0.70f) * 185.0f;
    float px = sunX + std::cos(ang) * rad;
    float py = sunY + std::sin(ang) * rad;
    float u = clampf(1.0f - rad / 185.0f, 0.0f, 1.0f);
    RGB halo = mixRGB(hexRGB(0xF3B68B), hexRGB(0xFF9348), u);
    paintDab(sky, px, py, rng.range(14, 26), rng.range(5, 10), ang + 1.57f,
             jitterColor(halo, rng, 0.03f, 0.04f, 0.03f), 0.16f + u * 0.34f, 0.24f, 120000 + ring, 5);
  }
  for (int disc = 0; disc < 160; ++disc) {
    float ang = rng.range(0.0f, 6.283f);
    float rad = std::sqrt(rng.next()) * 44.0f;
    RGB core = mixRGB(hexRGB(0xF27D3B), hexRGB(0xFFD69A), 1.0f - rad / 44.0f);
    paintDab(sky, sunX + std::cos(ang) * rad, sunY + std::sin(ang) * rad,
             rng.range(7, 14), rng.range(3.5f, 6.0f), ang + 1.2f,
             jitterColor(core, rng, 0.03f, 0.04f, 0.02f), 0.85f, 0.70f, 125000 + disc, 5);
  }

  // Painterly Clouds spanning the 5 time-of-day zones
  paintPainterlyCloud(sky, 740, 355, 220, 62, hexRGB(0xFCE4CA), hexRGB(0xDFB7AE), hexRGB(0x9D94AE), 1301, 440);
  paintPainterlyCloud(sky, 1680, 345, 260, 74, hexRGB(0xFFF6E3), hexRGB(0xDCE2E8), hexRGB(0x9FB1CA), 1302, 520);
  paintPainterlyCloud(sky, 2210, 290, 320, 92, hexRGB(0xFFFDF6), hexRGB(0xE1EAF3), hexRGB(0x9EB3CF), 1303, 660);
  paintPainterlyCloud(sky, 2760, 360, 240, 72, hexRGB(0xFFE7B8), hexRGB(0xE8B4A0), hexRGB(0x9E84A2), 1304, 520);
  paintPainterlyCloud(sky, 3360, 405, 280, 76, hexRGB(0xFFD2A4), hexRGB(0xCF8B98), hexRGB(0x7C6796), 1305, 560);
  paintPainterlyCloud(sky, 3980, 380, 290, 66, hexRGB(0xCFA3BE), hexRGB(0x886C9D), hexRGB(0x464675), 1306, 540);
}

// Build Layer 1: Continuous Far Normandy Horizon & Mist Spires (7000 x 1440, d = 0.34)
inline void buildHorizonLayer(OilCanvas &hor) {
  const int W = 7000, H = LAYER_H;
  hor.resize(W, H, false);
  RNG rng(2002ULL);

  auto hillTopY = [](float x) {
    float n = fbm2D(x * 0.0014f, 3.1f, 4, 211) * 95.0f;
    float valley = std::sin(x * 0.00095f) * 24.0f;
    // Low misty Seine shoreline in Scene 1 so Dawn Sun shines openly above it!
    float scene1Dip = std::exp(-std::pow((x - 580.0f) / 720.0f, 2.0f)) * 90.0f;
    float scene3Lift = std::exp(-std::pow((x - 3550.0f) / 900.0f, 2.0f)) * -58.0f;
    return 565.0f + n + valley + scene1Dip + scene3Lift;
  };

  auto horizonColor = [](float x) -> RGB {
    if (x < 1150.0f) return mixRGB(hexRGB(0x8F8DB2), hexRGB(0x7B8AA8), x / 1150.0f);
    if (x < 2350.0f) return mixRGB(hexRGB(0x7B8AA8), hexRGB(0x73988E), (x - 1150.0f) / 1200.0f);
    if (x < 3950.0f) return mixRGB(hexRGB(0x73988E), hexRGB(0x7A9C7A), (x - 2350.0f) / 1600.0f);
    if (x < 5300.0f) return mixRGB(hexRGB(0x8D7E8F), hexRGB(0x866886), (x - 3950.0f) / 1350.0f);
    return mixRGB(hexRGB(0x6D5A82), hexRGB(0x323968), clampf((x - 5300.0f) / 1300.0f, 0.0f, 1.0f));
  };

  for (int x = 0; x < W; x += 9) {
    float topY = hillTopY(static_cast<float>(x));
    RGB base = horizonColor(static_cast<float>(x));
    for (int y = static_cast<int>(topY); y < 860; y += 7) {
      float depth = clampf((y - topY) / 220.0f, 0.0f, 1.0f);
      RGB col = jitterColor(mixRGB(shiftWarm(base, 0.16f), shiftCool(base, 0.25f), depth), rng, 0.04f, 0.05f, 0.03f);
      paintDab(hor, x + rng.range(-3, 3), y + rng.range(-3, 3),
               rng.range(18, 28), rng.range(7, 12), rng.range(-0.42f, 0.42f),
               col, rng.range(0.62f, 0.88f), 0.24f, 200000 + x * 5 + y * 13, 6);
    }
    if (x > 1300 && hash2D(x / 9, 77, 505) > 0.65f) {
      float th = rng.range(22.0f, 64.0f);
      RGB treeCol = jitterColor(shiftCool(base, 0.22f), rng, 0.04f, 0.05f, 0.03f);
      for (int k = 0; k < 9; ++k) {
        float py = topY - (k / 8.0f) * th;
        float wid = lerpf(10.0f, 4.0f, k / 8.0f);
        paintDab(hor, x + rng.range(-2, 2), py, rng.range(9, 15), wid, 1.57f + rng.range(-0.18f, 0.18f),
                 treeCol, rng.range(0.55f, 0.82f), 0.30f, 250000 + x * 19 + k, 5);
      }
    }
  }

  // Scene 1 misty harbor sailboat masts rising softly above low river mist
  for (int m = 0; m < 14; ++m) {
    float mx = 280.0f + m * 58.0f + rng.range(-12, 12);
    float my = hillTopY(mx) + 12.0f;
    float mh = rng.range(52.0f, 94.0f);
    RGB mastC = jitterColor(hexRGB(0x6D6B8E), rng, 0.03f, 0.03f, 0.03f);
    paintStroke(hor, {mx, my, mx + rng.range(-2, 2), my - mh, 0.0f, 2.4f, 0.62f, 0.25f, 0.2f, 3, 0.03f, mastC, {}, false, static_cast<uint32_t>(260000 + m)});
    paintStroke(hor, {mx + 2.0f, my - mh * 0.18f, mx + 14.0f, my - mh * 0.72f, 4.0f, 8.0f, 0.38f, 0.18f, 0.35f, 4, 0.03f, hexRGB(0xC2ADB9), {}, false, static_cast<uint32_t>(261000 + m)});
  }
}

// Build Layer 2: Mid-far Wooded Groves, Grounded Cottages & Smooth Seasonal Transitions (11000 x 1440, d = 0.62)
inline void buildMidgroundLayer(OilCanvas &mid) {
  const int W = 11000, H = LAYER_H;
  mid.resize(W, H, false);
  RNG rng(3003ULL);

  // Scene 1 Seine misty far bank (x = 0..1950): grounded solidly into y = 755 waterline (NO floating shelf!)
  for (int cx = 40; cx < 1950; cx += 115) {
    float u = smoothstepf(1250.0f, 1950.0f, static_cast<float>(cx));
    // Keep left-center open and low so dawn sun & harbor mist breathe; build lush willow bank near right (Portal 1)
    float r = lerpf(58.0f, 108.0f, u) * rng.range(0.85f, 1.15f);
    float cy = lerpf(705.0f, 675.0f, u) + rng.range(-12, 12);
    RGB dC = mixRGB(hexRGB(0x475A72), hexRGB(0x22463A), u);
    RGB mC = mixRGB(hexRGB(0x637A89), hexRGB(0x41704E), u);
    RGB lC = mixRGB(hexRGB(0x8CA19D), hexRGB(0x7AA35E), u);
    RGB sC = mixRGB(hexRGB(0xD4B9A2), hexRGB(0xC9D67F), u);
    paintFoliageCanopy(mid, static_cast<float>(cx), cy, r * 1.25f, r * 0.95f, dC, mC, lC, sC, 950, 300000 + cx, 6, 15);
  }

  // Scene 2 Giverny lush pond-backing garden groves (x = 1850..4650, grounded solidly down to y = 760)
  for (int cx = 1900; cx < 4650; cx += 95) {
    float r = rng.range(85.0f, 152.0f);
    float cy = 545.0f + rng.range(-50.0f, 30.0f);
    paintFoliageCanopy(mid, static_cast<float>(cx), cy, r * 1.08f, r * 0.92f,
                       hexRGB(0x21443A), hexRGB(0x3F6D4D), hexRGB(0x78A15E), hexRGB(0xC9D67F),
                       1350, 320000 + cx, 6, 15);
    paintFoliageCanopy(mid, cx + rng.range(-25, 25), 655.0f, r * 0.92f, 68.0f,
                       hexRGB(0x1D3B35), hexRGB(0x325A44), hexRGB(0x5E8752), hexRGB(0x9BBA66),
                       550, 330000 + cx, 5, 12);
  }

  // Scene 3 -> Scene 5 Continuous Hillside Treeline (x = 4450..11000):
  // Smooth continuous elevation following terrain horizon + full undergrowth base down to y = 760 (ZERO floating bushes!)
  for (int cx = 4450; cx < 10960; cx += 108) {
    float fcx = static_cast<float>(cx);
    // Smoothly transition canopy baseline from Scene 3 hillside (515) -> Scene 4 harvest treeline (595) -> Scene 5 lagoon bank (645)
    float s4Mix = smoothstepf(5750.0f, 6750.0f, fcx);
    float s5Mix = smoothstepf(8550.0f, 9450.0f, fcx);
    float baseHillY = lerpf(518.0f, 598.0f, s4Mix);
    baseHillY = lerpf(baseHillY, 648.0f, s5Mix) + std::sin(fcx * 0.0021f) * 18.0f;

    // Gentle dip behind Woman with Parasol (world 8580 -> d=0.62 -> ~5520..5760) so parasol stands against sky & clouds
    float heroGap = std::exp(-std::pow((fcx - 5630.0f) / 310.0f, 2.0f));
    float cy = lerpf(baseHillY - 12.0f, baseHillY + 38.0f, heroGap);
    float r = rng.range(64.0f, 118.0f) * (1.0f - heroGap * 0.30f);

    float autumnMix = smoothstepf(5850.0f, 7050.0f, fcx);
    RGB dC = mixRGB(hexRGB(0x335B44), hexRGB(0x4C3D5C), autumnMix);
    RGB mC = mixRGB(hexRGB(0x568854), hexRGB(0x7C5B5A), autumnMix);
    RGB lC = mixRGB(hexRGB(0x8EB961), hexRGB(0xBA8651), autumnMix);
    RGB sC = mixRGB(hexRGB(0xCFE285), hexRGB(0xEBB864), autumnMix);

    dC = mixRGB(dC, hexRGB(0x1B2544), s5Mix);
    mC = mixRGB(mC, hexRGB(0x2B3B5C), s5Mix);
    lC = mixRGB(lC, hexRGB(0x465678), s5Mix);
    sC = mixRGB(sC, hexRGB(0x77769B), s5Mix);

    paintFoliageCanopy(mid, fcx, cy, r * 1.18f, r * 0.92f, dC, mC, lC, sC, 980, 340000 + cx, 5, 14);
    // Grounding dark wooded undergrowth & distant trunks down to y = 755 (zero floating air gap!)
    paintFoliageCanopy(mid, fcx + rng.range(-18, 18), cy + 68.0f, r * 1.10f, 76.0f,
                       shiftCool(dC, 0.25f), dC, mC, mC, 420, 345000 + cx, 5, 12);
  }
  // Two Normandy cottages firmly seated into the hillside trees
  paintNormandyCottage(mid, 5200.0f, 528.0f, 124.0f, 88.0f, 350001);
  paintNormandyCottage(mid, 6080.0f, 524.0f, 108.0f, 78.0f, 350002);
}

// Re-sculpted Woman with a Parasol: graceful flowing bell silhouette, soft natural edge brushwork, fluttering scarf
inline void paintWomanWithParasol(OilCanvas &cv, float footX, float footY, uint32_t seed) {
  RNG rng(seed);
  // 1. Soft cobalt-violet diagonal cast shadow over sunlit meadow grass
  for (int i = 0; i < 105; ++i) {
    float t = rng.next();
    float sx = footX - t * 128.0f + rng.range(-26, 24) * (1.0f - t * 0.35f);
    float sy = footY + t * 22.0f + rng.range(-7, 9);
    RGB sh = jitterColor(mixRGB(hexRGB(0x465874), hexRGB(0x617D56), t * 0.52f), rng, 0.04f, 0.06f, 0.03f);
    paintDab(cv, sx, sy, rng.range(13, 24), rng.range(4.5f, 7.5f), rng.range(-0.25f, 0.15f), sh, 0.45f, 0.20f, seed + i, 5);
  }

  // 2. Graceful curved bell skirt with organic sunlit folds & natural soft cloth edges (NO sawtooth triangle edge!)
  for (int i = 0; i < 720; ++i) {
    float u = std::pow(rng.next(), 0.78f); // 0 waist -> 1 hem
    float y = footY - 122.0f + u * 124.0f;
    float bell = std::sin(u * 1.35f);
    float windSweep = -std::pow(u, 1.30f) * 32.0f;
    float leftEdge = footX - lerpf(11.0f, 50.0f, bell) + windSweep * 0.42f;
    float rightEdge = footX + lerpf(12.0f, 32.0f, std::pow(u, 0.88f)) + rng.range(-2.5f, 2.5f);
    float side = rng.range(0.0f, 1.0f);
    float x = lerpf(leftEdge, rightEdge, side);

    float fold = std::sin(side * 11.0f - u * 4.2f) * 0.5f + 0.5f;
    RGB shadowF = mixRGB(hexRGB(0x7B89BA), hexRGB(0xAFBBE0), fold * 0.65f);
    RGB sunlitF = mixRGB(hexRGB(0xDFE4F4), hexRGB(0xFFF7E8), fold);
    RGB col = jitterColor(mixRGB(shadowF, sunlitF, smoothstepf(0.18f, 0.85f, side)), rng, 0.04f, 0.045f, 0.028f);
    float dx = lerpf(-10.0f, 4.0f, side) * (0.35f + u * 0.65f);
    paintStroke(cv, {x, y - 4.0f, x + dx, y + 10.0f, -2.0f, rng.range(3.8f, 6.2f),
                     0.88f, 0.72f, 0.15f, 4, 0.03f, col, {}, false, static_cast<uint32_t>(seed + 500 + i)});
  }

  // 3. Natural sculpted bodice & soft tucked waist
  for (int y = static_cast<int>(footY - 172); y <= static_cast<int>(footY - 118); y += 2) {
    float u = (y - (footY - 172.0f)) / 54.0f;
    float hw = lerpf(15.0f, 11.5f, std::sin(u * 3.14f) * 0.45f);
    for (float x = footX - hw; x <= footX + hw; x += 3.0f) {
      float side = (x - (footX - hw)) / (2.0f * hw);
      RGB base = mixRGB(hexRGB(0x7E8DC0), hexRGB(0xF8F2E5), smoothstepf(0.20f, 0.85f, side));
      if (u > 0.84f) base = mixRGB(base, hexRGB(0xB8737A), 0.55f);
      paintDab(cv, x, static_cast<float>(y), rng.range(6.5f, 10.5f), rng.range(3.2f, 4.8f), 0.85f + side * 0.4f,
               jitterColor(base, rng, 0.035f, 0.04f, 0.03f), 0.92f, 0.75f, seed + 2500 + y * 19 + static_cast<int>(x), 4);
    }
  }

  // 4. Head, chestnut hair, shaded profile & wide sunlit straw hat cleanly visible above treeline
  float headX = footX + 1.0f, headY = footY - 187.0f;
  for (int i = 0; i < 32; ++i) {
    float a = rng.range(0.0f, 6.283f), r = std::sqrt(rng.next()) * 10.5f;
    RGB face = (a > -1.0f && a < 1.2f) ? hexRGB(0xEAC0A4) : hexRGB(0x7E6068);
    paintDab(cv, headX + std::cos(a) * r, headY + std::sin(a) * r, 5.5f, 3.5f, rng.range(-0.8f, 0.8f),
             jitterColor(face, rng, 0.03f, 0.04f, 0.03f), 0.94f, 0.68f, seed + 3500 + i, 3);
  }
  // Soft rounded straw hat crown & gentle sunlit brim
  paintDab(cv, headX, headY - 13.0f, 12.0f, 5.5f, 0.0f, hexRGB(0xDFC178), 0.94f, 0.78f, seed + 3680, 4);
  for (int i = 0; i < 42; ++i) {
    float t = i / 41.0f;
    float hx = headX + lerpf(-22.0f, 20.0f, t);
    float hy = headY - 9.0f + std::sin(t * 3.14f) * -4.0f + rng.range(-1.5f, 1.5f);
    RGB hat = t > 0.45f ? hexRGB(0xF5DD92) : hexRGB(0xC29A5C);
    paintDab(cv, hx, hy, 8.5f, 4.0f, -0.15f + (t - 0.5f) * 0.25f, jitterColor(hat, rng, 0.04f, 0.05f, 0.03f), 0.94f, 0.80f, seed + 3700 + i, 4);
  }
  // Fluttering sheer white-lavender veil & scarf sweeping gracefully into breeze
  for (int i = 0; i < 55; ++i) {
    float u = i / 54.0f;
    float sx = headX - 6.0f - u * 72.0f;
    float sy = headY + 4.0f + std::sin(u * 4.8f) * 10.0f + u * 10.0f;
    RGB sc = mixRGB(hexRGB(0xD8E2F2), hexRGB(0xFFFDF8), rng.next());
    paintDab(cv, sx, sy, rng.range(10, 19), rng.range(2.8f, 5.0f), 0.15f + std::cos(u * 4.8f) * 0.28f,
             jitterColor(sc, rng, 0.03f, 0.04f, 0.03f), lerpf(0.78f, 0.26f, u), 0.45f, seed + 3900 + i, 4);
  }

  // 5. Raised arm & tilted jade-lined sunlit parasol dome
  float handX = footX + 18.0f, handY = footY - 156.0f;
  paintStroke(cv, {footX + 8.0f, footY - 158.0f, handX, handY, 2.0f, 4.5f, 0.92f, 0.62f, 0.14f, 4, 0.03f, hexRGB(0xC9B4BA), {}, false, seed + 4100});
  float paraX = footX + 7.0f, paraY = footY - 228.0f;
  paintStroke(cv, {handX, handY + 12.0f, paraX, paraY, 0.0f, 2.6f, 0.94f, 0.55f, 0.08f, 3, 0.02f, hexRGB(0x4E3734), {}, false, seed + 4101});

  for (int layer = 0; layer < 280; ++layer) {
    float u = rng.range(-1.0f, 1.0f);
    float v = rng.range(0.0f, 1.0f);
    float px = paraX + u * 58.0f;
    float arch = -std::sqrt(std::max(0.0f, 1.0f - u * u)) * 26.0f;
    float py = paraY + arch * (1.0f - v * 0.45f) + v * 13.0f;
    RGB domeCol = v < 0.36f ? mixRGB(hexRGB(0xFAF6E4), hexRGB(0xD3DFCF), v * 2.4f)
                           : mixRGB(hexRGB(0x9BC0A4), hexRGB(0x648E78), (v - 0.36f) / 0.64f);
    float slopeAng = -0.26f + u * 0.44f;
    paintDab(cv, px, py, rng.range(9.0f, 16.0f), rng.range(3.5f, 5.5f), slopeAng,
             jitterColor(domeCol, rng, 0.04f, 0.05f, 0.03f), 0.92f, 0.78f, seed + 4500 + layer, 4);
  }
}

// Re-sculpted Monet Beehive Haystack: true volumetric wrap driven strictly by actual spatial relX = (x - cx)/hw!
inline void paintMonetHaystack(OilCanvas &cv, float cx, float baseY, float w, float h, uint32_t seed) {
  RNG rng(seed);
  // 1. Soft cobalt-violet cast shadow stretching left across stubble field
  for (int i = 0; i < 680; ++i) {
    float u = rng.next();
    float spread = lerpf(0.75f, 1.15f, u);
    float sx = cx - u * w * 1.15f + rng.range(-w * 0.34f, w * 0.30f) * spread;
    float sy = baseY + u * 24.0f + rng.range(-13.0f, 15.0f);
    RGB sh = mixRGB(hexRGB(0x474576), hexRGB(0x7C6A88), u * 0.72f);
    paintDab(cv, sx, sy, rng.range(14, 28), rng.range(4.5f, 8.5f), rng.range(-0.18f, 0.14f),
             jitterColor(sh, rng, 0.05f, 0.06f, 0.04f), lerpf(0.72f, 0.34f, u), 0.35f, seed + i * 7, 6);
  }

  // Smooth rounded Monet beehive silhouette
  auto stackHalfW = [&](float v) -> float {
    if (v < 0.58f) {
      float u = v / 0.58f;
      return w * 0.50f * std::sqrt(std::sin(u * 1.5708f));
    } else {
      float u = (v - 0.58f) / 0.42f;
      return w * (0.50f - 0.05f * u * u);
    }
  };

  // 2. Opaque warm-violet / ochre underpainting core
  for (float v = 0.02f; v <= 1.0f; v += 0.015f) {
    float y = baseY - h * (1.0f - v);
    float hw = stackHalfW(v);
    for (float x = cx - hw; x <= cx + hw; x += 8.5f) {
      float relX = (x - cx) / std::max(1.0f, hw);
      RGB uCol = mixRGB(hexRGB(0x644E78), hexRGB(0xD88D48), smoothstepf(-0.62f, 0.68f, relX));
      paintDab(cv, x + rng.range(-2, 2), y + rng.range(-2, 2), rng.range(15, 22), rng.range(7, 11),
               relX * 0.42f + 1.57f, jitterColor(uCol, rng, 0.04f, 0.05f, 0.04f), 0.94f, 0.30f, seed + 2000 + static_cast<int>(v * 1000) * 13 + static_cast<int>(x), 6);
    }
  }

  // 3. 6,400 layered straw strokes driven strictly by spatial relX (ZERO center knife-edge!)
  for (int i = 0; i < 6400; ++i) {
    float v = std::pow(rng.next(), 0.85f);
    float y = baseY - h * (1.0f - v);
    float hw = stackHalfW(v);
    float x = cx + rng.range(-1.0f, 1.0f) * hw * (0.85f + 0.16f * rng.next());
    float relX = clampf((x - cx) / std::max(1.0f, hw), -1.0f, 1.0f);

    float lightNoise = (fbm2D(x * 0.022f, y * 0.022f, 2, seed) - 0.5f) * 0.24f;
    float light = clampf(smoothstepf(-0.68f, 0.68f, relX + lightNoise) * 0.84f + (1.0f - v) * 0.16f, 0.0f, 1.0f);

    RGB shadowStraw = mixRGB(hexRGB(0x524675), hexRGB(0x8D5F70), rng.next());
    RGB bridgeStraw = mixRGB(hexRGB(0xB86E58), hexRGB(0xDA8E48), rng.next());
    RGB sunlitStraw = mixRGB(hexRGB(0xF4BE54), hexRGB(0xFFE686), rng.next());

    RGB col = light < 0.46f ? mixRGB(shadowStraw, bridgeStraw, light / 0.46f)
                            : mixRGB(bridgeStraw, sunlitStraw, (light - 0.46f) / 0.54f);
    if (relX > 0.68f && rng.next() < 0.48f) col = shiftWarm(col, 0.45f, hexRGB(0xFFF3B2));
    col = jitterColor(col, rng, 0.06f, 0.08f, 0.05f);

    float angle = 1.57f - relX * lerpf(0.65f, 0.15f, v) + rng.range(-0.26f, 0.26f);
    paintDab(cv, x, y, rng.range(10.0f, 20.0f), rng.range(2.6f, 5.0f), angle,
             col, rng.range(0.78f, 0.94f), 0.78f, seed + 10000 + i, 5);
  }

  for (int i = 0; i < 240; ++i) {
    float x = cx + rng.range(-w * 0.52f, w * 0.52f);
    float y = baseY + rng.range(-5.0f, 8.0f);
    float relX = clampf((x - cx) / std::max(1.0f, w * 0.5f), -1.0f, 1.0f);
    RGB tCol = mixRGB(hexRGB(0x6D5A76), hexRGB(0xCF914C), smoothstepf(-0.55f, 0.55f, relX));
    paintDab(cv, x, y, rng.range(8, 16), rng.range(2.8f, 4.5f), rng.range(0.8f, 2.3f),
             jitterColor(tCol, rng, 0.05f, 0.07f, 0.04f), 0.92f, 0.72f, seed + 25000 + i, 4);
  }
}

// Build Layer 3: Grounded World Base, Japanese Bridge, Woman with Parasol, Haystacks & Twilight Boathouse
inline void buildWorldLayer(OilCanvas &wl) {
  const int W = 16600, H = LAYER_H;
  wl.resize(W, H, false);
  RNG rng(4004ULL);

  // A. Scene 1 Seine foreground bank tufts & grounded reeds (x = 0..2700, shoreY ~ 745)
  for (int x = 20; x < 2750; x += 26) {
    if (fbm2D(x * 0.005f, 1.7f, 3, 41) < 0.42f) continue;
    float baseY = 748.0f + rng.range(-5.0f, 7.0f);
    for (int k = 0; k < 14; ++k) {
      float rx = x + rng.range(-18, 18);
      float rh = rng.range(28.0f, 74.0f);
      RGB rc = mixRGB(hexRGB(0x3F5D50), hexRGB(0x7B8D68), rng.next());
      paintStroke(wl, {rx, baseY, rx + rng.range(-8, 8), baseY - rh, rng.range(-3, 3),
                       rng.range(2.2f, 3.8f), 0.86f, 0.45f, 0.22f, 4, 0.04f, jitterColor(rc, rng, 0.05f, 0.06f, 0.04f), {}, false, static_cast<uint32_t>(400000 + x * 17 + k)});
    }
  }

  // B. Scene 2 Giverny Pond Edge Irises & Sculpted Japanese Bridge (Hero center x = 5340, waterline y = 650)
  for (int x = 3100; x < 6350; x += 22) {
    float baseY = getTerrainTopY(static_cast<float>(x)) + rng.range(-8.0f, 10.0f);
    for (int k = 0; k < 9; ++k) {
      float ix = x + rng.range(-14, 14);
      float ih = rng.range(24.0f, 68.0f);
      RGB leafC = mixRGB(hexRGB(0x2D5B3E), hexRGB(0x6B9A53), rng.next());
      paintStroke(wl, {ix, baseY + 6.0f, ix + rng.range(-10, 10), baseY - ih, rng.range(-4, 4),
                       rng.range(2.6f, 4.4f), 0.88f, 0.55f, 0.18f, 4, 0.04f, jitterColor(leafC, rng, 0.05f, 0.06f, 0.04f), {}, false, static_cast<uint32_t>(420000 + x * 13 + k)});
    }
    if (rng.next() < 0.28f) {
      paintDab(wl, x + rng.range(-8, 8), baseY - rng.range(28, 52), 9.0f, 5.0f, rng.range(-0.6f, 0.6f),
               jitterColor(hexRGB(0x7463B5), rng, 0.06f, 0.08f, 0.04f), 0.90f, 0.80f, 430000 + x, 4);
    }
  }

  auto bridgeY = [](float x) {
    float u = (x - 5340.0f) / 640.0f;
    return 518.0f + u * u * 124.0f;
  };
  float piers[] = {4810.0f, 5075.0f, 5340.0f, 5605.0f, 5870.0f};
  for (int pi = 0; pi < 5; ++pi) {
    float px = piers[pi];
    float y0 = bridgeY(px) + 10.0f, y1 = 690.0f;
    for (int s = 0; s < 18; ++s) {
      float ty = lerpf(y0, y1, s / 17.0f);
      RGB pCol = ty > 640.0f ? hexRGB(0x2F4F3E) : mixRGB(hexRGB(0x476F55), hexRGB(0x364958), 0.42f);
      paintStroke(wl, {px + rng.range(-3, 3), ty, px + rng.range(-3, 3), ty + 16.0f, 0.0f,
                       8.5f, 0.92f, 0.65f, 0.15f, 6, 0.04f, jitterColor(pCol, rng, 0.04f, 0.05f, 0.04f), {}, false, static_cast<uint32_t>(440000 + pi * 50 + s)});
    }
  }
  for (int x = 4700; x <= 5980; x += 6) {
    float yd = bridgeY(static_cast<float>(x));
    float ydn = bridgeY(static_cast<float>(x + 8));
    paintStroke(wl, {static_cast<float>(x), yd + 12.0f, static_cast<float>(x + 8), ydn + 12.0f, 0.0f, 8.5f, 0.92f, 0.55f, 0.14f, 5, 0.04f, jitterColor(hexRGB(0x355354), rng, 0.04f, 0.05f, 0.04f), {}, false, static_cast<uint32_t>(450000 + x)});
    paintStroke(wl, {static_cast<float>(x), yd + 3.0f, static_cast<float>(x + 8), ydn + 3.0f, 0.0f, 7.5f, 0.94f, 0.75f, 0.14f, 5, 0.04f, jitterColor(hexRGB(0x7DA76B), rng, 0.05f, 0.07f, 0.05f), {}, false, static_cast<uint32_t>(455000 + x)});
  }

  float figX = 5375.0f, figY = bridgeY(figX) + 2.0f;
  for (int y = static_cast<int>(figY - 68); y <= static_cast<int>(figY - 6); y += 3) {
    float u = (y - (figY - 68.0f)) / 62.0f;
    float hw = lerpf(8.0f, 15.0f, u);
    for (float x = figX - hw; x <= figX + hw; x += 3.2f) {
      RGB dress = x < figX ? hexRGB(0x9BA6CF) : hexRGB(0xF5EFE1);
      if (u < 0.25f) dress = mixRGB(dress, hexRGB(0xD8A79E), 0.35f);
      paintDab(wl, x, static_cast<float>(y), 5.5f, 3.0f, 1.5f, jitterColor(dress, rng, 0.03f, 0.04f, 0.03f), 0.92f, 0.72f, 459000 + y * 19 + static_cast<int>(x), 4);
    }
  }
  paintDab(wl, figX, figY - 76.0f, 8.0f, 5.5f, 0.0f, hexRGB(0xE8BD9D), 0.92f, 0.70f, 459901, 4);
  paintDab(wl, figX, figY - 82.0f, 19.0f, 5.5f, -0.08f, hexRGB(0xEDD17E), 0.94f, 0.80f, 459902, 5);

  for (int x = 4715; x <= 5965; x += 26) {
    float yd = bridgeY(static_cast<float>(x));
    float yr = yd - 52.0f;
    paintStroke(wl, {static_cast<float>(x), yd + 3.0f, static_cast<float>(x), yr, 0.0f, 5.2f, 0.92f, 0.72f, 0.16f, 4, 0.04f, jitterColor(hexRGB(0x578762), rng, 0.05f, 0.06f, 0.04f), {}, false, static_cast<uint32_t>(460000 + x)});
    if (x + 26 <= 5965) {
      float ydn = bridgeY(static_cast<float>(x + 26));
      float yrn = ydn - 52.0f;
      RGB lCol = jitterColor(hexRGB(0x6D9C6D), rng, 0.05f, 0.06f, 0.04f);
      paintStroke(wl, {static_cast<float>(x), yr + 8.0f, static_cast<float>(x + 26), ydn - 6.0f, 0.0f, 3.0f, 0.80f, 0.50f, 0.20f, 3, 0.04f, lCol, {}, false, static_cast<uint32_t>(463000 + x)});
      paintStroke(wl, {static_cast<float>(x), yd - 6.0f, static_cast<float>(x + 26), yrn + 8.0f, 0.0f, 3.0f, 0.80f, 0.50f, 0.20f, 3, 0.04f, lCol, {}, false, static_cast<uint32_t>(466000 + x)});
    }
  }
  for (int x = 4700; x <= 5980; x += 7) {
    float y0 = bridgeY(static_cast<float>(x)) - 52.0f;
    float y1 = bridgeY(static_cast<float>(x + 8)) - 52.0f;
    paintStroke(wl, {static_cast<float>(x), y0 + 2.0f, static_cast<float>(x + 8), y1 + 2.0f, 0.0f, 6.8f, 0.94f, 0.72f, 0.12f, 5, 0.04f, jitterColor(hexRGB(0x548263), rng, 0.04f, 0.05f, 0.04f), {}, false, static_cast<uint32_t>(470000 + x)});
    paintStroke(wl, {static_cast<float>(x), y0 - 2.0f, static_cast<float>(x + 8), y1 - 2.0f, 0.0f, 3.4f, 0.94f, 0.88f, 0.14f, 4, 0.04f, jitterColor(hexRGB(0xB5D285), rng, 0.05f, 0.07f, 0.04f), {}, false, static_cast<uint32_t>(473000 + x)});
  }

  for (int rx = 4740; rx <= 5940; rx += 15) {
    float baseY = bridgeY(static_cast<float>(rx)) - 56.0f + rng.range(-12, 10);
    float drop = rng.range(34.0f, 96.0f) * (0.65f + 0.45f * std::sin((rx - 4740.0f) * 0.011f));
    int buds = static_cast<int>(drop * 0.85f);
    for (int bi = 0; bi < buds; ++bi) {
      float u = bi / static_cast<float>(buds);
      RGB wc = u < 0.35f ? hexRGB(0x70549C) : (u < 0.72f ? hexRGB(0x9D82C9) : hexRGB(0xD8C3EC));
      if (rng.next() < 0.20f) wc = hexRGB(0xF1E5F6);
      paintDab(wl, rx + rng.range(-7.5f, 7.5f) * (1.0f - u * 0.5f), baseY + u * drop,
               rng.range(4.2f, 8.0f), rng.range(2.8f, 4.8f), rng.range(0.6f, 2.4f),
               jitterColor(wc, rng, 0.05f, 0.08f, 0.04f), 0.90f, 0.78f, 480000 + rx * 23 + bi, 4);
    }
    for (int li = 0; li < 7; ++li) {
      paintDab(wl, rx + rng.range(-11, 11), baseY - rng.range(3, 15), rng.range(7, 13), rng.range(3.5f, 5.2f),
               rng.range(-1.3f, 1.3f), jitterColor(hexRGB(0x5E8E58), rng, 0.05f, 0.07f, 0.04f), 0.90f, 0.62f, 490000 + rx * 11 + li, 4);
    }
  }

  // C. Grounded Meadow Terrain for Scene 3 & Scene 4 (x = 6150..13100)
  // Pass 0: 100% OPAQUE soft ground underpainting wash so ZERO cream gaps EVER appear between strokes!
  auto sampleTerrainBase = [](float fx, float fy, float topY) -> RGB {
    float depth = clampf((fy - topY) / 760.0f, 0.0f, 1.0f);
    float n = fbm2D(fx * 0.006f, fy * 0.010f, 3, 606);
    float harvestMix = smoothstepf(8900.0f, 10200.0f, fx);
    float duskMix = smoothstepf(11800.0f, 13000.0f, fx);

    RGB summerGrass = mixRGB(hexRGB(0x5B9248), hexRGB(0x88BA57), n);
    if (depth > 0.45f) summerGrass = mixRGB(summerGrass, hexRGB(0x3D6E41), (depth - 0.45f) * 0.55f);

    float pathCenterY = 740.0f - (fx - 7300.0f) * 0.14f + std::sin(fx * 0.003f) * 26.0f;
    float pathFade = smoothstepf(6720.0f, 7420.0f, fx) * (1.0f - smoothstepf(8840.0f, 9220.0f, fx));
    float pathHalfW = lerpf(46.0f, 20.0f, 1.0f - depth);
    if (pathFade > 0.01f && std::fabs(fy - pathCenterY) < pathHalfW) {
      float pf = (1.0f - std::fabs(fy - pathCenterY) / pathHalfW) * pathFade;
      summerGrass = mixRGB(summerGrass, hexRGB(0xDFCAA2), pf * 0.72f);
    }

    RGB harvestGrass = mixRGB(hexRGB(0xB87F46), hexRGB(0xDFAA59), n);
    harvestGrass = mixRGB(harvestGrass, hexRGB(0x7B5E6F), (1.0f - n) * 0.22f);

    RGB base = mixRGB(summerGrass, harvestGrass, harvestMix);
    if (duskMix > 0.01f) base = mixRGB(base, hexRGB(0x2D3A54), duskMix * 0.85f);
    return base;
  };

  for (int x = 6150; x < 13100; ++x) {
    float fx = static_cast<float>(x);
    float topY = getTerrainTopY(fx);
    float entryAlpha = smoothstepf(6150.0f, 6420.0f, fx);
    int yTop = static_cast<int>(topY);
    for (int y = yTop; y < H; ++y) {
      RGB base = sampleTerrainBase(fx, static_cast<float>(y), topY);
      // Soft feather top 6px edge of hill contour
      float topFeather = smoothstepf(topY, topY + 5.0f, static_cast<float>(y));
      float a = entryAlpha * topFeather;
      size_t idx = static_cast<size_t>(y) * W + x;
      wl.r[idx] = base.r;
      wl.g[idx] = base.g;
      wl.b[idx] = base.b;
      wl.a[idx] = std::max(wl.a[idx], a);
      wl.height[idx] = 0.12f * a;
    }
  }

  // Pass 1: Rich multi-scale oil meadow & harvest stubble brushwork over opaque ground
  for (int x = 6180; x < 13080; x += 13) {
    float topY = getTerrainTopY(static_cast<float>(x));
    for (int y = static_cast<int>(topY) + 3; y < H - 4; y += 9) {
      RGB base = sampleTerrainBase(static_cast<float>(x), static_cast<float>(y), topY);
      RGB col = jitterColor(base, rng, 0.06f, 0.08f, 0.045f);
      paintDab(wl, x + rng.range(-5, 5), y + rng.range(-4, 4),
               rng.range(16.0f, 28.0f), rng.range(6.5f, 11.0f),
               rng.range(-0.26f, 0.26f), col, 0.92f, 0.44f, 520000 + x * 5 + y * 13, 6);
    }
  }

  // Scene 3: Woman with a Parasol (footX=8580, footY=542) & Young Boy (footX=8810, footY=622)
  paintWomanWithParasol(wl, 8580.0f, 542.0f, 610000);
  // Sculpted young child (Jean Monet) in cream smock, straw hat & cobalt shorts nestled softly in meadow grass
  float cX = 8810.0f, cY = 622.0f;
  for (int i = 0; i < 45; ++i) {
    paintDab(wl, cX - i * 1.2f, cY + i * 0.22f, 10.0f, 4.0f, -0.1f, hexRGB(0x475A6E), 0.36f, 0.15f, 619000 + i, 4);
  }
  for (int i = 0; i < 160; ++i) {
    float u = rng.next();
    float y = cY - 58.0f + u * 58.0f;
    float hw = lerpf(8.5f, 15.5f, std::pow(u, 0.75f)) + rng.range(-1.5f, 1.5f);
    float x = cX + rng.range(-hw, hw);
    float side = (x - (cX - hw)) / std::max(1.0f, 2.0f * hw);
    RGB smock = u > 0.64f ? mixRGB(hexRGB(0x3B5382), hexRGB(0x5C78AD), side)
                          : mixRGB(hexRGB(0xA6B2D4), hexRGB(0xF8F3E4), smoothstepf(0.18f, 0.85f, side));
    paintDab(wl, x, y, 6.2f, 3.4f, 1.25f + rng.range(-0.2f, 0.2f), jitterColor(smock, rng, 0.03f, 0.04f, 0.03f), 0.92f, 0.72f, 620000 + i, 4);
  }
  paintDab(wl, cX, cY - 65.0f, 8.5f, 6.0f, 0.0f, hexRGB(0xEAC0A0), 0.94f, 0.68f, 621001, 4);
  paintDab(wl, cX, cY - 74.0f, 8.5f, 4.2f, 0.0f, hexRGB(0xD8B468), 0.94f, 0.76f, 621010, 4);
  for (int i = 0; i < 20; ++i) {
    paintDab(wl, cX + lerpf(-13, 13, i / 19.0f), cY - 71.0f, 7.0f, 3.2f, -0.05f, hexRGB(0xF0D27D), 0.94f, 0.80f, 621050 + i, 4);
  }
  // Grass tufts overlapping child's boots for firm terrain grounding
  for (int i = 0; i < 18; ++i) {
    float gx = cX + rng.range(-20, 20);
    paintStroke(wl, {gx, cY + 4.0f, gx + rng.range(-5, 5), cY - rng.range(10, 18), 0.0f, 2.2f, 0.88f, 0.55f, 0.15f, 3, 0.03f, hexRGB(0x5D8C46), {}, false, static_cast<uint32_t>(621500 + i)});
  }

  // D. Scene 4 Monumental Monet Beehive Haystacks (grounded solidly in harvest stubble)
  paintMonetHaystack(wl, 11340.0f, 768.0f, 325.0f, 250.0f, 710000);
  paintMonetHaystack(wl, 11920.0f, 845.0f, 435.0f, 340.0f, 750000);

  // E. Scene 5 Stone Arched Boathouse / Twilight River Pavilion (x = 14740, baseY = 742)
  float bhX = 14740.0f, bhBaseY = 742.0f, bhW = 340.0f, bhH = 190.0f;
  for (int y = static_cast<int>(bhBaseY - 24); y <= static_cast<int>(bhBaseY + 14); y += 4) {
    for (int x = static_cast<int>(bhX - bhW * 0.58f); x <= static_cast<int>(bhX + bhW * 0.58f); x += 7) {
      RGB stone = y > bhBaseY ? hexRGB(0x232E47) : mixRGB(hexRGB(0x414866), hexRGB(0x615E7B), rng.next());
      paintDab(wl, x + rng.range(-2, 2), y + rng.range(-2, 2), rng.range(10, 17), rng.range(5, 7.5f),
               rng.range(-0.15f, 0.15f), jitterColor(stone, rng, 0.04f, 0.05f, 0.03f), 0.94f, 0.60f, 800000 + x * 5 + y * 11, 5);
    }
  }
  for (int y = static_cast<int>(bhBaseY - bhH * 0.72f); y <= static_cast<int>(bhBaseY - 8); y += 4) {
    for (int x = static_cast<int>(bhX - bhW * 0.46f); x <= static_cast<int>(bhX + bhW * 0.46f); x += 7) {
      RGB wall = mixRGB(hexRGB(0x3B4163), hexRGB(0x5E5B7D), fbm2D(x * 0.02f, y * 0.02f, 2, 81));
      paintDab(wl, x + rng.range(-1.5f, 1.5f), y + rng.range(-1.5f, 1.5f), rng.range(9, 15), rng.range(4.5f, 7.5f),
               rng.range(-0.12f, 0.12f), jitterColor(wall, rng, 0.04f, 0.05f, 0.03f), 0.95f, 0.65f, 810000 + x * 7 + y * 13, 5);
    }
  }
  for (int y = static_cast<int>(bhBaseY - bhH); y <= static_cast<int>(bhBaseY - bhH * 0.68f); y += 4) {
    float t = (y - (bhBaseY - bhH)) / (bhH * 0.32f);
    float hw = lerpf(bhW * 0.30f, bhW * 0.54f, t);
    for (int x = static_cast<int>(bhX - hw); x <= static_cast<int>(bhX + hw); x += 6) {
      RGB roof = mixRGB(hexRGB(0x282E4C), hexRGB(0x4E476E), (1.0f - t) * 0.7f);
      paintDab(wl, x + rng.range(-1.5f, 1.5f), y, rng.range(9, 14), rng.range(4, 6), rng.range(-0.22f, 0.22f),
               jitterColor(roof, rng, 0.04f, 0.05f, 0.03f), 0.95f, 0.72f, 820000 + x * 11 + y * 17, 5);
    }
  }
  // Clean boat-slip arches framed by stone voussoirs
  for (int ai = 0; ai < 2; ++ai) {
    float ax = bhX + (ai == 0 ? 36.0f : 98.0f);
    for (int ay = 0; ay < 38; ay += 3) {
      float u = ay / 38.0f;
      float hw = u < 0.4f ? 15.0f * std::sqrt(std::max(0.0f, 1.0f - std::pow(1.0f - u / 0.4f, 2.0f))) : 15.0f;
      for (float x = ax - hw; x <= ax + hw; x += 3.5f) {
        paintDab(wl, x, bhBaseY - 38.0f + ay, 6.0f, 3.8f, 1.57f, hexRGB(0x161D35), 0.95f, 0.35f, 825000 + ai * 200 + ay * 11 + static_cast<int>(x), 3);
      }
    }
  }
  // Three glowing warm amber arched lantern windows
  float winXs[] = {bhX - 92.0f, bhX - 38.0f, bhX + 68.0f};
  for (int wi = 0; wi < 3; ++wi) {
    float wx = winXs[wi], wy = bhBaseY - 96.0f;
    for (int g = 0; g < 65; ++g) {
      float a = rng.range(0.0f, 6.283f), r = std::sqrt(rng.next()) * 36.0f;
      RGB glow = mixRGB(hexRGB(0x8D5A52), hexRGB(0xF6AE4A), 1.0f - r / 36.0f);
      paintDab(wl, wx + std::cos(a) * r, wy + std::sin(a) * r, 9.0f, 5.0f, rng.range(-1.5f, 1.5f), glow, 0.42f, 0.55f, 830000 + wi * 100 + g, 4);
    }
    for (int c = 0; c < 30; ++c) {
      paintDab(wl, wx + rng.range(-8, 8), wy + rng.range(-12, 12), 7.5f, 4.5f, 1.57f,
               mixRGB(hexRGB(0xFFBE55), hexRGB(0xFFF3BA), rng.next()), 0.96f, 0.90f, 835000 + wi * 50 + c, 4);
    }
  }
  // Trailing twilight ivy & shoreline shrubs softening the boathouse corners & eaves
  paintFoliageCanopy(wl, bhX - bhW * 0.48f, bhBaseY - 46.0f, 48.0f, 56.0f,
                     hexRGB(0x18213B), hexRGB(0x273556), hexRGB(0x3D4C70), hexRGB(0x5A678A), 340, 840001, 5, 11);
  paintFoliageCanopy(wl, bhX + bhW * 0.48f, bhBaseY - 52.0f, 52.0f, 64.0f,
                     hexRGB(0x18213B), hexRGB(0x273556), hexRGB(0x3D4C70), hexRGB(0x5A678A), 360, 840002, 5, 11);
}

// Build Layer 5: 4 Lush Feathered Foreground Spatial Transition Portals (2500 x 1440 each, d = 1.18)
inline void buildPortals(PortalSprite portals[4]) {
  // Portal 1: Parted Weeping Willow Curtain (t ~ 19.5s — trunks anchored cleanly to bottom y=1440!)
  {
    portals[0].anchorWorldX = 4335.0f - 1250.0f;
    OilCanvas &cv = portals[0].canvas;
    cv.resize(2500, LAYER_H, false);
    RNG rng(910001ULL);

    paintContinuousTrunk(cv, 290, 1440, 560, 260, 58, 22, hexRGB(0x2A3531), hexRGB(0x55644C), 910100);
    paintContinuousTrunk(cv, 550, 290, 1120, 145, 22, 10, hexRGB(0x2A3531), hexRGB(0x55644C), 910200);
    paintContinuousTrunk(cv, 2210, 1440, 1920, 240, 60, 22, hexRGB(0x2A3531), hexRGB(0x55644C), 910300);
    paintContinuousTrunk(cv, 1930, 280, 1380, 150, 22, 10, hexRGB(0x2A3531), hexRGB(0x55644C), 910400);

    for (int cx = 240; cx <= 2260; cx += 180) {
      paintFoliageCanopy(cv, static_cast<float>(cx), 185.0f + rng.range(-45, 45), 205.0f, 148.0f,
                         hexRGB(0x1E3D31), hexRGB(0x416C45), hexRGB(0x7DA856), hexRGB(0xC8DC77),
                         1350, 911000 + cx, 6, 16);
    }
    for (int s = 0; s < 480; ++s) {
      float fx = rng.range(160, 2340);
      float centerDist = std::fabs(fx - 1250.0f) / 1100.0f;
      // Part center strands slightly so Dawn Sun & Giverny pond shimmer invite the viewer through!
      if (centerDist < 0.24f && rng.next() < 0.45f) continue;
      float topY = rng.range(100.0f, 340.0f);
      float drop = lerpf(620.0f, 1120.0f, clampf(0.32f + centerDist * 0.68f, 0.0f, 1.0f)) * rng.range(0.75f, 1.05f);
      int segs = static_cast<int>(drop / 13.0f);
      float curve = rng.range(-42.0f, 42.0f);
      for (int k = 0; k < segs; ++k) {
        float u = k / static_cast<float>(segs);
        float px = fx + curve * u * u + std::sin(u * 4.5f + s) * 9.0f;
        float py = topY + u * drop;
        RGB lCol = mixRGB(hexRGB(0x2D573B), hexRGB(0x9CC462), clampf(u * 0.65f + rng.next() * 0.45f, 0.0f, 1.0f));
        if (u > 0.5f && rng.next() < 0.30f) lCol = shiftWarm(lCol, 0.35f, hexRGB(0xDEE67B));
        paintDab(cv, px + rng.range(-4, 4), py, rng.range(11, 19), rng.range(3.0f, 5.2f), 1.57f + rng.range(-0.2f, 0.2f),
                 jitterColor(lCol, rng, 0.06f, 0.08f, 0.05f), rng.range(0.80f, 0.96f), 0.65f, 915000 + s * 110 + k, 4);
      }
    }
    featherPortalEdges(cv, 260.0f);
  }

  // Portal 2: Climbing Rose Pergola Arbor (t ~ 39.5s — organic curved arch, full cabbage roses, zero straight bars!)
  {
    portals[1].anchorWorldX = 8087.0f - 1250.0f;
    OilCanvas &cv = portals[1].canvas;
    cv.resize(2500, LAYER_H, false);
    RNG rng(920001ULL);

    auto archBotY = [](float x) -> float {
      float dx = (x - 1250.0f) / 680.0f;
      if (std::fabs(dx) < 0.72f) {
        float organicRuffle = std::sin(x * 0.025f) * 24.0f + std::cos(x * 0.06f) * 12.0f;
        return 415.0f - (0.52f - dx * dx) * 165.0f + organicRuffle;
      }
      return 1430.0f;
    };

    // Weathered organic curved garden trellis posts & arch boughs tucked inside rose canopy
    paintContinuousTrunk(cv, 620, 1440, 650, 390, 24, 16, hexRGB(0x2C4537), hexRGB(0x4E7358), 920100, -14.0f);
    paintContinuousTrunk(cv, 1880, 1440, 1850, 390, 24, 16, hexRGB(0x2C4537), hexRGB(0x4E7358), 920200, 14.0f);
    paintContinuousTrunk(cv, 650, 390, 1250, 225, 16, 12, hexRGB(0x2C4537), hexRGB(0x4E7358), 920300, 26.0f);
    paintContinuousTrunk(cv, 1850, 390, 1250, 225, 16, 12, hexRGB(0x2C4537), hexRGB(0x4E7358), 920350, -26.0f);

    // Dense climbing rose foliage forming irregular organic arched bower
    for (int cx = 260; cx <= 2240; cx += 150) {
      float maxY = archBotY(static_cast<float>(cx));
      for (float cy = 200.0f; cy <= maxY; cy += 190.0f) {
        paintFoliageCanopy(cv, static_cast<float>(cx) + rng.range(-25, 25), cy + rng.range(-18, 18), 185.0f, 165.0f,
                           hexRGB(0x1E4234), hexRGB(0x3D6F47), hexRGB(0x6EA058), hexRGB(0xB4CF73),
                           1150, 921000 + cx * 7 + static_cast<int>(cy), 6, 15);
      }
    }

    // 280 FULL OUTSIDE-IN Cabbage Roses strictly inside leafy arch (zero hollow bullseye rings!)
    for (int ri = 0; ri < 280; ++ri) {
      float rx = rng.range(260.0f, 2240.0f);
      float maxY = archBotY(rx) - 32.0f;
      float ry = rng.range(165.0f, std::max(195.0f, maxY));
      float rad = rng.range(11.0f, 22.0f);
      RGB rimPetal = hexRGB(0xFCE4EA);
      RGB midPetal = rng.next() < 0.55f ? hexRGB(0xF29EB2) : hexRGB(0xF5AE9D);
      RGB deepHeart = rng.next() < 0.6f ? hexRGB(0xC94468) : hexRGB(0xDF6A87);

      // Step 1: Broad outer petal ring (fills whole bloom footprint softly)
      for (int pt = 0; pt < 8; ++pt) {
        float pa = pt * 0.785f + rng.range(-0.25f, 0.25f);
        paintDab(cv, rx + std::cos(pa) * rad * 0.44f, ry + std::sin(pa) * rad * 0.44f,
                 rad * 0.68f, rad * 0.50f, pa + 1.57f,
                 jitterColor(pt % 2 ? rimPetal : midPetal, rng, 0.04f, 0.05f, 0.03f), 0.94f, 0.80f, 926000 + ri * 20 + pt, 4);
      }
      // Step 2: Overlapping warm pink mid-petals
      for (int pt = 0; pt < 6; ++pt) {
        float pa = pt * 1.047f + 0.4f + rng.range(-0.25f, 0.25f);
        paintDab(cv, rx + std::cos(pa) * rad * 0.22f, ry + std::sin(pa) * rad * 0.22f,
                 rad * 0.54f, rad * 0.40f, pa + 1.4f,
                 jitterColor(midPetal, rng, 0.04f, 0.05f, 0.03f), 0.95f, 0.85f, 927000 + ri * 20 + pt, 4);
      }
      // Step 3: Warm crimson spiral heart + golden-ivory catchlight touch
      paintDab(cv, rx, ry, rad * 0.38f, rad * 0.30f, rng.range(0, 3.14f), deepHeart, 0.96f, 0.90f, 928000 + ri * 2, 3);
      paintDab(cv, rx + rad * 0.14f, ry - rad * 0.14f, rad * 0.24f, rad * 0.16f, -0.4f, hexRGB(0xFFF3EC), 0.85f, 0.92f, 928001 + ri * 2, 2);
    }
    featherPortalEdges(cv, 280.0f);
  }

  // Portal 3: Sun-Dappled Normandy Apple Orchard Canopy (t ~ 59.0s — single seamless curved trunks!)
  {
    portals[2].anchorWorldX = 11981.0f - 1250.0f;
    OilCanvas &cv = portals[2].canvas;
    cv.resize(2500, LAYER_H, false);
    RNG rng(930001ULL);

    struct TreeSpec { float botX, topX, topY, w, bend; };
    const TreeSpec trees[] = {
      {450, 495, 390, 40, -34.0f},
      {790, 745, 445, 32,  28.0f},
      {1720, 1775, 415, 36, -30.0f},
      {2080, 2015, 435, 40,  34.0f}
    };
    for (int ti = 0; ti < 4; ++ti) {
      const auto &tr = trees[ti];
      paintContinuousTrunk(cv, tr.botX, 1440.0f, tr.topX, tr.topY, tr.w * 1.15f, tr.w * 0.45f,
                           hexRGB(0x3B333E), hexRGB(0x6C5C59), 931000 + ti * 100, tr.bend);
      // Asymmetric forked boughs tucked inside orchard canopy leaves
      paintContinuousTrunk(cv, tr.topX, tr.topY + 45.0f, tr.topX - 105.0f, tr.topY - 70.0f, tr.w * 0.42f, 9.0f,
                           hexRGB(0x3B333E), hexRGB(0x6C5C59), 931050 + ti * 100, 10.0f);
      paintContinuousTrunk(cv, tr.topX, tr.topY + 35.0f, tr.topX + 115.0f, tr.topY - 65.0f, tr.w * 0.42f, 9.0f,
                           hexRGB(0x3B333E), hexRGB(0x6C5C59), 931080 + ti * 100, -10.0f);
    }

    // Varied overarching amber-green orchard canopies
    for (int cx = 310; cx <= 2190; cx += 170) {
      float centerDist = std::fabs(cx - 1250.0f);
      float cy = centerDist > 420.0f ? rng.range(210.0f, 540.0f) : rng.range(160.0f, 340.0f);
      paintFoliageCanopy(cv, static_cast<float>(cx) + rng.range(-20, 20), cy, rng.range(175.0f, 225.0f), rng.range(145.0f, 195.0f),
                         hexRGB(0x374B36), hexRGB(0x6D8646), hexRGB(0xB8AC4F), hexRGB(0xF1CE6A),
                         1600, 932000 + cx, 6, 17);
    }
    featherPortalEdges(cv, 280.0f);
  }

  // Portal 4: Gracefully Curved Twilight Marsh Reeds & Cattail Clumps (t ~ 78.0s)
  {
    portals[3].anchorWorldX = 15639.0f - 1250.0f;
    OilCanvas &cv = portals[3].canvas;
    cv.resize(2500, LAYER_H, false);
    RNG rng(940001ULL);

    for (int cx = 280; cx <= 2120; cx += 210) {
      if (std::fabs(cx - 1250.0f) > 360.0f) {
        paintFoliageCanopy(cv, static_cast<float>(cx), 1160.0f, 200.0f, 240.0f,
                           hexRGB(0x19243B), hexRGB(0x2D3C55), hexRGB(0x4C5570), hexRGB(0x786A84),
                           950, 941000 + cx, 6, 15);
      }
    }
    for (int i = 0; i < 420; ++i) {
      float rx = rng.range(220.0f, 2080.0f);
      float rightFade = 1.0f - smoothstepf(1550.0f, 2080.0f, rx);
      if (rng.next() > 0.35f + 0.65f * rightFade) continue;
      float centerDist = std::fabs(rx - 1250.0f) / 1000.0f;
      float botY = 1440.0f;
      float h = lerpf(360.0f, 840.0f, clampf(0.35f + centerDist * 0.65f, 0.0f, 1.0f)) * rng.range(0.55f, 1.05f);
      float lean = rng.range(-135.0f, 135.0f);
      float bend = lean * 0.55f;
      RGB blade = mixRGB(hexRGB(0x1D283E), hexRGB(0x4E576D), rng.next());
      if (rng.next() < 0.28f) blade = mixRGB(blade, hexRGB(0x8E737D), 0.45f);
      paintStroke(cv, {rx, botY, rx + lean, botY - h, bend, rng.range(2.8f, 5.2f),
                       0.88f, 0.55f, 0.22f, 4, 0.04f, jitterColor(blade, rng, 0.04f, 0.05f, 0.03f), {}, false, static_cast<uint32_t>(945000 + i)});
      if (i % 3 == 0) {
        for (int p = 0; p < 7; ++p) {
          paintDab(cv, rx + lean + rng.range(-7, 7), botY - h + rng.range(-12, 16), rng.range(8, 15), rng.range(3, 5.2f),
                   1.4f + rng.range(-0.3f, 0.3f), jitterColor(hexRGB(0xA4818B), rng, 0.04f, 0.05f, 0.04f),
                   0.84f, 0.60f, 948000 + i * 10 + p, 4);
        }
      }
    }
    featherPortalEdges(cv, 280.0f);
  }
}

inline void buildAllWorldLayers(WorldSceneData &data) {
  std::cerr << "Painting Layer 0 (Continuous Sky Panorama)...\n";
  buildSkyLayer(data.skyLayer);
  std::cerr << "Painting Layer 1 (Far Normandy Horizon)...\n";
  buildHorizonLayer(data.horizonLayer);
  std::cerr << "Painting Layer 2 (Midground Groves & Cottages)...\n";
  buildMidgroundLayer(data.midgroundLayer);
  std::cerr << "Painting Layer 3 (Hero Landmarks, Bridge, Parasol, Haystacks & Boathouse)...\n";
  buildWorldLayer(data.worldLayer);
  std::cerr << "Painting Layer 5 (4 Lush Feathered Portal Curtains)...\n";
  buildPortals(data.portals);
  std::cerr << "All static museum oil layers complete!\n";
}

} // namespace monet

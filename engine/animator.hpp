#pragma once
#include "paint_core.hpp"
#include "camera.hpp"
#include "world_layers.hpp"
#include <cmath>

namespace monet {

// Paint live undulating Impressionist water reflections + broken-color shimmer strokes
inline void renderAnimatedWater(OilCanvas &cv, const CameraState &cam, double t) {
  float x0 = cam.x;
  float x1 = cam.x + cv.w;
  bool hasS1 = (x0 < 3600.0f);
  bool hasS2 = (x1 > 2600.0f && x0 < 6600.0f);
  bool hasS5 = (x1 > 12100.0f);
  if (!hasS1 && !hasS2 && !hasS5) return;

  float timeF = static_cast<float>(t);

  // Copy upper scene snapshot for clean vertical mirror reflection sampling
  std::vector<float> snapR = cv.r;
  std::vector<float> snapG = cv.g;
  std::vector<float> snapB = cv.b;
  std::vector<float> snapH = cv.height;

  for (int x = 0; x < cv.w; ++x) {
    float wx = cam.x + x;

    // Determine water presence & smooth edge blend across portals
    float waterMask = 0.0f;
    float waterWorldY = 745.0f;
    RGB tint = hexRGB(0x527488);
    float tintStrength = 0.42f;

    if (wx < 3500.0f) {
      // Scene 1 Seine -> transitions smoothly behind Portal 1 to Scene 2 pond
      float u12 = smoothstepf(2700.0f, 3500.0f, wx);
      waterWorldY = lerpf(745.0f, 645.0f, u12);
      tint = mixRGB(hexRGB(0x6D8298), hexRGB(0x2B575E), u12);
      tintStrength = lerpf(0.38f, 0.50f, u12);
      waterMask = 1.0f;
    } else if (wx < 6550.0f) {
      // Scene 2 Giverny Pond -> tucked cleanly behind Portal 2 hillside rise
      waterWorldY = 645.0f;
      tint = hexRGB(0x2A555C);
      tintStrength = 0.50f;
      waterMask = 1.0f - smoothstepf(5850.0f, 6450.0f, wx);
    } else if (wx > 12250.0f) {
      // Scene 5 Twilight Lagoon -> enters smoothly behind Portal 4 reeds
      waterWorldY = 732.0f;
      tint = hexRGB(0x1E2F54);
      tintStrength = 0.52f;
      waterMask = smoothstepf(12250.0f, 12950.0f, wx);
    }

    if (waterMask <= 0.01f) continue;

    int waterScreenY = static_cast<int>(std::lround(waterWorldY - LAYER_Y_PAD - cam.y));
    if (waterScreenY >= cv.h - 2) continue;

    // Soft shoreline water-edge ripple blend (no hard razor horizontal line)
    int yStart = std::max(0, waterScreenY - 3);
    for (int y = yStart; y < cv.h; ++y) {
      float dy = static_cast<float>(y - waterScreenY);
      float edgeFade = smoothstepf(-3.0f, 6.0f, dy) * waterMask;
      if (edgeFade <= 0.01f) continue;

      float depth = clampf(dy / std::max(80.0f, static_cast<float>(cv.h - waterScreenY)), 0.0f, 1.0f);
      float phaseNoise = std::sin(wx * 0.029f) * 1.85f + std::cos(wx * 0.067f) * 0.95f;
      float rippleX = std::sin(dy * 0.24f - timeF * 2.1f + wx * 0.019f + phaseNoise) * (2.2f + depth * 5.2f)
                    + std::sin(dy * 0.52f + timeF * 2.8f + wx * 0.047f) * (1.1f + depth * 2.1f)
                    + std::cos(dy * 0.88f - timeF * 1.6f + wx * 0.091f) * 0.85f;
      float rippleY = std::sin(wx * 0.034f + dy * 0.14f + timeF * 1.7f + phaseNoise * 0.6f) * (1.8f + depth * 4.4f)
                    + std::cos(wx * 0.073f - dy * 0.31f + timeF * 2.3f) * 1.05f;

      int sx = std::clamp(static_cast<int>(std::lround(x + rippleX)), 0, cv.w - 1);
      int sy = std::clamp(static_cast<int>(std::lround(waterScreenY - std::fabs(dy) * 0.88f + rippleY)), 0, cv.h - 1);

      size_t si = static_cast<size_t>(sy) * cv.w + sx;
      size_t di = static_cast<size_t>(y) * cv.w + x;

      RGB refl = {snapR[si], snapG[si], snapB[si]};
      // Darken & cool deeper foreground water slightly for natural aerial depth
      RGB deepTone = shiftCool(tint, depth * 0.35f, hexRGB(0x162442));
      RGB wCol = mixRGB(refl, deepTone, clampf(tintStrength + depth * 0.22f, 0.0f, 0.85f));

      // Preserve bright sun / lantern reflections cleanly as broken warm highlights
      float lum = 0.299f * refl.r + 0.587f * refl.g + 0.114f * refl.b;
      if (lum > 0.68f) {
        float sparkle = std::sin(dy * 0.42f - timeF * 2.6f + wx * 0.043f + phaseNoise) * 0.5f + 0.5f;
        wCol = mixRGB(wCol, refl, 0.45f * sparkle + 0.25f);
      }

      cv.r[di] = lerpf(cv.r[di], wCol.r, edgeFade);
      cv.g[di] = lerpf(cv.g[di], wCol.g, edgeFade);
      cv.b[di] = lerpf(cv.b[di], wCol.b, edgeFade);
      cv.height[di] = lerpf(cv.height[di], snapH[si] * 0.4f + 0.20f, edgeFade);
    }
  }

  // World-locked broken-color horizontal Impressionist water strokes
  int cellW = 24, cellH = 11;
  int wxStart = static_cast<int>(std::floor(cam.x / cellW)) * cellW;
  int wxEnd = static_cast<int>(std::ceil((cam.x + cv.w) / cellW)) * cellW;
  for (int gx = wxStart; gx <= wxEnd; gx += cellW) {
    float fwx = static_cast<float>(gx);
    if (fwx >= 6350.0f && fwx <= 12350.0f) continue;

    float waterWorldY = fwx < 3500.0f ? lerpf(745.0f, 645.0f, smoothstepf(2700.0f, 3500.0f, fwx))
                                      : (fwx < 6500.0f ? 645.0f : 732.0f);
    float waterMask = fwx < 5850.0f ? 1.0f
                    : (fwx < 6450.0f ? 1.0f - smoothstepf(5850.0f, 6450.0f, fwx)
                    : smoothstepf(12250.0f, 12950.0f, fwx));
    if (waterMask <= 0.05f) continue;

    for (int gy = static_cast<int>(waterWorldY) + 6; gy < 1265; gy += cellH) {
      float jx = (hash2D(gx, gy, 881u) - 0.5f) * cellW * 0.85f;
      float jy = (hash2D(gx, gy, 882u) - 0.5f) * cellH * 0.75f;
      float sx = (fwx + jx) - cam.x + std::sin(timeF * 1.4f + gy * 0.08f + gx * 0.02f) * 3.2f;
      float sy = (gy + jy) - LAYER_Y_PAD - cam.y;
      if (sx < -30 || sx > cv.w + 30 || sy < 0 || sy >= cv.h) continue;

      int ix = std::clamp(static_cast<int>(sx), 0, cv.w - 1);
      int iy = std::clamp(static_cast<int>(sy), 0, cv.h - 1);
      size_t idx = static_cast<size_t>(iy) * cv.w + ix;
      RGB sampleC = {cv.r[idx], cv.g[idx], cv.b[idx]};

      float depth = clampf((gy - waterWorldY) / 480.0f, 0.0f, 1.0f);
      float h = hash2D(gx / cellW, gy / cellH, 991u);
      RGB strokeCol = sampleC;
      if (fwx < 3300.0f) {
        // Seine dawn: warm peach-gold & lavender-cyan complementary dabs
        if (h < 0.22f) strokeCol = mixRGB(sampleC, hexRGB(0xF6C48A), 0.35f);
        else if (h > 0.78f) strokeCol = mixRGB(sampleC, hexRGB(0x526E8C), 0.35f);
      } else if (fwx < 6500.0f) {
        // Giverny pond: turquoise, emerald & soft sky lavender-cream
        if (h < 0.25f) strokeCol = mixRGB(sampleC, hexRGB(0x7DA874), 0.35f);
        else if (h > 0.76f) strokeCol = mixRGB(sampleC, hexRGB(0x3B7082), 0.38f);
      } else {
        // Twilight lagoon: ultramarine & warm amber shimmer
        if (h < 0.22f) strokeCol = mixRGB(sampleC, hexRGB(0x364D80), 0.35f);
        else if (h > 0.85f) strokeCol = mixRGB(sampleC, hexRGB(0x786A99), 0.28f);
      }

      float len = lerpf(11.0f, 25.0f, depth) * (0.75f + h * 0.5f);
      float wid = lerpf(1.8f, 3.8f, depth);
      paintDab(cv, sx, sy, len, wid, (h - 0.5f) * 0.08f, strokeCol,
               0.55f * waterMask, 0.42f, static_cast<uint32_t>(gx * 13 + gy * 29), 4);
    }
  }
}

// Scene 1: Dawn Sun Seine Reflection, Rowing Skiff, Dipping Oar Ripples & Banking White Egrets
inline void renderScene1Living(OilCanvas &cv, const CameraState &cam, double t) {
  if (cam.x > 3300.0f) return;
  float timeF = static_cast<float>(t);

  // Shimmering broken-color coral-gold Dawn Sun reflection column on Seine water
  float sunSX = 1120.0f - cam.x * 0.16f;
  float waterSY = 745.0f - LAYER_Y_PAD - cam.y;
  float sunVis = 1.0f - smoothstepf(2100.0f, 3150.0f, cam.x);
  if (sunVis > 0.02f && sunSX > -180.0f && sunSX < cv.w + 180.0f) {
    for (int r = 0; r < 68; ++r) {
      float u = r / 67.0f;
      float sy = lerpf(waterSY + 12.0f, static_cast<float>(cv.h - 24), u);
      float wave = std::sin(timeF * 2.1f - u * 16.0f + r * 0.7f) * lerpf(6.0f, 28.0f, u);
      float spread = (hash2D(r, 17, 1051u) - 0.5f) * lerpf(32.0f, 92.0f, u);
      float sx = sunSX + spread + wave;
      RGB sunRefl = mixRGB(hexRGB(0xF27D3B), hexRGB(0xFFD58C), 0.35f + 0.65f * (1.0f - std::fabs(spread) / 55.0f));
      paintDab(cv, sx, sy, lerpf(18.0f, 54.0f, u), lerpf(3.2f, 6.2f, u),
               (hash2D(r, 29, 1052u) - 0.5f) * 0.06f, sunRefl,
               (0.68f - u * 0.25f) * sunVis, 0.72f, 10500 + r, 4);
    }
  }

  // Wooden skiff gliding across dawn river reflection (scaled cleanly at 1.32x for 1:1 silhouette detail)
  float boatWX = 1390.0f + timeF * 32.0f;
  float boatWY = 835.0f + std::sin(timeF * 1.4f) * 2.5f;
  float bx = boatWX - cam.x;
  float by = boatWY - LAYER_Y_PAD - cam.y;
  float bs = 1.32f;

  if (bx > -220.0f && bx < cv.w + 220.0f) {
    // Inverted soft boat reflection in water
    for (int i = -24; i <= 24; ++i) {
      float rx = bx + i * 2.4f * bs + std::sin(timeF * 2.5f + i) * 3.0f;
      paintDab(cv, rx, by + (15.0f + std::fabs(i) * 0.32f) * bs, 9.5f * bs, 3.4f * bs, 0.05f,
               hexRGB(0x313850), 0.44f, 0.20f, 11000 + i, 4);
    }
    // Expanding water ripples around hull & oar dip
    float oarPhase = timeF * 1.65f;
    float oarTipX = bx - 8.0f * bs + std::cos(oarPhase) * 20.0f * bs;
    float oarTipY = by + 10.0f * bs + std::max(0.0f, std::sin(oarPhase)) * 5.0f * bs;
    for (int r = 0; r < 3; ++r) {
      float age = std::fmod(timeF * 0.7f + r * 0.33f, 1.0f);
      float radX = (12.0f + age * 48.0f) * bs;
      for (int a = 0; a < 10; ++a) {
        float ang = (a / 10.0f) * 6.283f;
        paintDab(cv, oarTipX + std::cos(ang) * radX, by + 12.0f * bs + std::sin(ang) * radX * 0.22f,
                 9.5f * bs, 2.2f * bs, 0.0f, hexRGB(0xEEC99D), (1.0f - age) * 0.65f, 0.45f, 12000 + r * 20 + a, 3);
      }
    }
    // Boatman (sculpted seated torso & leaning shoulders) + companion in cream shawl
    for (int k = 0; k < 24; ++k) {
      float u = k / 23.0f;
      float lean = std::sin(oarPhase) * 3.8f * bs;
      paintDab(cv, bx + 6.0f * bs + lean * (1.0f - u), by - (26.0f - u * 22.0f) * bs,
               10.5f * bs, 4.8f * bs, 1.4f,
               u < 0.35f ? hexRGB(0x475068) : hexRGB(0x353A52), 0.92f, 0.65f, 13000 + k, 4);
    }
    paintDab(cv, bx + 7.0f * bs + std::sin(oarPhase) * 4.2f * bs, by - 31.0f * bs, 8.0f * bs, 5.2f * bs, 0.1f, hexRGB(0xD8A88D), 0.92f, 0.65f, 13101, 3);
    paintDab(cv, bx + 7.0f * bs + std::sin(oarPhase) * 4.2f * bs, by - 36.0f * bs, 16.5f * bs, 4.4f * bs, -0.05f, hexRGB(0xC69A64), 0.92f, 0.70f, 13102, 4);
    // Companion passenger silhouette near stern
    for (int k = 0; k < 15; ++k) {
      paintDab(cv, bx - (22.0f - (k % 3 - 1) * 3.0f) * bs, by - (22.0f - k * 1.35f) * bs,
               9.5f * bs, 4.6f * bs, 1.5f,
               k < 6 ? hexRGB(0xE8D4C2) : hexRGB(0x6D6A8A), 0.90f, 0.62f, 13200 + k, 4);
    }
    paintDab(cv, bx - 22.0f * bs, by - 27.0f * bs, 7.2f * bs, 4.6f * bs, 0.0f, hexRGB(0xDFB59D), 0.90f, 0.65f, 13250, 3);
    // Mahogany hull sculpted from curved horizontal strokes + warm dawn rim highlight
    for (int row = 0; row < 5; ++row) {
      float hw = lerpf(58.0f, 38.0f, row / 4.0f) * bs;
      float ry = by - 2.0f * bs + row * 2.8f * bs;
      RGB hCol = row == 0 ? hexRGB(0xBA7E5C) : hexRGB(0x423344);
      paintStroke(cv, {bx - hw, ry - (row == 0 ? 3.5f * bs : 0.0f), bx + hw, ry - (row == 0 ? 3.5f * bs : 0.0f),
                       3.0f * bs, 5.2f * bs, 0.94f, 0.72f, 0.12f, 5, 0.03f, hCol, {}, false, static_cast<uint32_t>(13300 + row)});
    }
    // Long oar shaft dipping into water
    paintStroke(cv, {bx + 8.0f * bs, by - 14.0f * bs, oarTipX, oarTipY, 0.0f, 2.8f * bs, 0.92f, 0.60f, 0.10f, 3, 0.02f, hexRGB(0x8C6245), {}, false, 13400});
  }

  // Flock of 7 White Egrets banking across the misty dawn sky
  for (int e = 0; e < 7; ++e) {
    float ex = 1040.0f + e * 64.0f + timeF * (76.0f + (e % 3) * 4.5f) - cam.x;
    float ey = 468.0f - e * 14.0f - timeF * 5.2f + std::sin(timeF * 2.2f + e) * 7.5f - LAYER_Y_PAD - cam.y;
    if (ex < -80 || ex > cv.w + 80) continue;
    float flap = std::sin(timeF * 5.6f + e * 1.15f);
    float wingSpan = 18.0f + (e % 2) * 3.5f;
    RGB birdCol = mixRGB(hexRGB(0xF6EAE0), hexRGB(0xFFF9EE), 0.65f);
    // Graceful S-curved neck & plump ivory body
    paintDab(cv, ex, ey, 11.0f, 4.2f, -0.10f, birdCol, 0.94f, 0.75f, 14050 + e, 3);
    paintStroke(cv, {ex - 9.0f, ey + 2.0f, ex + 12.0f, ey - 1.8f, -2.0f, 3.6f, 0.94f, 0.75f, 0.12f, 3, 0.02f, birdCol, {}, false, static_cast<uint32_t>(14000 + e * 10)});
    // Flapping wing arcs
    paintStroke(cv, {ex, ey, ex - wingSpan * 0.78f, ey - flap * 13.0f - 4.5f, -3.5f, 3.6f, 0.92f, 0.75f, 0.15f, 3, 0.02f, birdCol, {}, false, static_cast<uint32_t>(14001 + e * 10)});
    paintStroke(cv, {ex + 2.0f, ey, ex + wingSpan * 0.68f, ey - flap * 11.5f - 5.2f, 3.0f, 3.4f, 0.90f, 0.72f, 0.15f, 3, 0.02f, hexRGB(0xE0C8C2), {}, false, static_cast<uint32_t>(14002 + e * 10)});
  }
}

// Scene 2: Animated Water Lilies, Swimming Koi & Azure Dragonflies
inline void renderScene2Living(OilCanvas &cv, const CameraState &cam, double t) {
  if (cam.x + cv.w < 3100.0f || cam.x > 6600.0f) return;
  float timeF = static_cast<float>(t);

  // 1. Swimming Golden-Orange Koi beneath translucent pond ripples
  for (int k = 0; k < 8; ++k) {
    float cx = 4250.0f + k * 280.0f;
    float cy = 760.0f + (k % 3) * 85.0f;
    float ang = timeF * (0.48f + (k % 3) * 0.12f) + k * 1.4f;
    float wx = cx + std::cos(ang) * 145.0f;
    float wy = cy + std::sin(ang * 2.0f) * 32.0f;
    float sx = wx - cam.x;
    float sy = wy - LAYER_Y_PAD - cam.y;
    if (sx < -60 || sx > cv.w + 60 || sy < 0 || sy > cv.h) continue;

    float vx = -std::sin(ang) * 145.0f;
    float vy = std::cos(ang * 2.0f) * 64.0f;
    float dir = std::atan2(vy, vx);
    float tailWag = std::sin(timeF * 7.5f + k * 2.0f) * 0.35f;

    RGB bodyCol = (k % 2 == 0) ? hexRGB(0xF07834) : hexRGB(0xF6B04C);
    paintDab(cv, sx, sy, 19.0f, 6.2f, dir, bodyCol, 0.66f, 0.35f, 21000 + k, 4);
    paintDab(cv, sx + std::cos(dir) * 6.0f, sy + std::sin(dir) * 6.0f, 8.0f, 4.5f, dir, hexRGB(0xFFF2DE), 0.58f, 0.35f, 21100 + k, 3);
    paintDab(cv, sx - std::cos(dir) * 11.0f, sy - std::sin(dir) * 11.0f, 9.0f, 3.5f, dir + tailWag, hexRGB(0xF29354), 0.54f, 0.28f, 21200 + k, 3);
  }

  // 2. 42 Rich Multi-Pad Water Lily Clusters (bobbing softly in pond ripples)
  RNG crng(25000ULL);
  for (int c = 0; c < 42; ++c) {
    float depth = std::pow(crng.next(), 0.72f);
    float cwx = crng.range(3550.0f, 6100.0f);
    float cwy = lerpf(690.0f, 1185.0f, depth);
    int padCount = static_cast<int>(crng.range(3.0f, 7.0f));

    for (int p = 0; p < padCount; ++p) {
      float pwx = cwx + crng.range(-90.0f, 90.0f) * (0.45f + 0.65f * depth);
      float pwy = cwy + crng.range(-24.0f, 24.0f) * (0.45f + 0.65f * depth);
      float radX = lerpf(14.0f, 44.0f, depth) * crng.range(0.8f, 1.2f);
      float radY = radX * 0.34f;
      bool hasFlower = crng.next() < 0.38f;
      bool roseTint = crng.next() < 0.62f;
      float notchAng = crng.range(-0.6f, 0.6f) + (p % 2 ? 2.5f : -0.3f);

      float sx = pwx - cam.x;
      float sy = pwy - LAYER_Y_PAD - cam.y + std::sin(timeF * 1.3f + c * 0.9f + p) * 1.4f;
      if (sx < -120 || sx > cv.w + 120 || sy < -60 || sy > cv.h + 60) continue;

      // Soft dark pond shadow rim
      paintDab(cv, sx + 2.0f, sy + 3.5f, radX * 1.65f, radY * 1.4f, 0.04f, hexRGB(0x1B3641), 0.46f, 0.15f, 26000 + c * 20 + p, 5);

      // Sculpted radial leaf strokes leaving V-notch
      int lsCount = static_cast<int>(lerpf(10, 22, depth));
      for (int ls = 0; ls < lsCount; ++ls) {
        float a = (ls / static_cast<float>(lsCount)) * 6.28318f + notchAng + 0.36f;
        float diff = std::fmod(std::fabs(a - notchAng) + 6.28318f, 6.28318f);
        if (diff < 0.34f || diff > 6.28318f - 0.34f) continue;
        RGB lc = mixRGB(hexRGB(0x3D6E48), hexRGB(0x82AD5F), (ls % 3) * 0.45f);
        if (std::sin(a) < -0.1f) lc = shiftWarm(lc, 0.30f, hexRGB(0xBDCE72));
        paintStroke(cv, {
          sx + std::cos(a) * radX * 0.18f, sy + std::sin(a) * radY * 0.18f,
          sx + std::cos(a) * radX * 0.98f, sy + std::sin(a) * radY * 0.98f,
          0.0f, lerpf(2.8f, 6.0f, depth), 0.88f, 0.65f, 0.16f, 4, 0.04f, lc, {}, false, static_cast<uint32_t>(27000 + c * 100 + p * 30 + ls)
        });
      }

      if (hasFlower) {
        float fSize = lerpf(7.5f, 19.0f, depth);
        RGB pOut = roseTint ? hexRGB(0xDE829B) : hexRGB(0xEAE4D9);
        RGB pIn = roseTint ? hexRGB(0xFAD6DF) : hexRGB(0xFFFDF5);
        for (int pt = 0; pt < 10; ++pt) {
          float pa = -2.95f + (pt / 9.0f) * 2.9f;
          float pl = fSize * (0.65f + (pt % 2) * 0.3f);
          paintStroke(cv, {
            sx, sy + 1.5f, sx + std::cos(pa) * pl * 1.15f, sy + std::sin(pa) * pl * 0.55f - 2.0f,
            0.0f, lerpf(2.2f, 4.2f, depth), 0.92f, 0.85f, 0.12f, 3, 0.03f, pt < 5 ? pOut : pIn, {}, false, static_cast<uint32_t>(29000 + c * 50 + p * 12 + pt)
          });
        }
        paintDab(cv, sx, sy - 1.5f, fSize * 0.34f, fSize * 0.24f, 0.0f, hexRGB(0xF6BE3D), 0.95f, 0.95f, 29900 + c * 20 + p, 3);
      }
    }
  }

  // 3. Iridescent Azure Dragonflies hovering & darting across the pond
  for (int d = 0; d < 6; ++d) {
    float wx = 4450.0f + d * 240.0f + std::sin(timeF * 1.4f + d * 1.8f) * 165.0f;
    float wy = 780.0f + (d % 3) * 75.0f + std::cos(timeF * 2.2f + d * 1.3f) * 38.0f;
    float sx = wx - cam.x;
    float sy = wy - LAYER_Y_PAD - cam.y;
    if (sx < -40 || sx > cv.w + 40) continue;
    float wing = std::sin(timeF * 28.0f + d) * 6.0f;
    paintStroke(cv, {sx - 9.0f, sy, sx + 9.0f, sy - 1.0f, 0.0f, 2.5f, 0.92f, 0.70f, 0.10f, 3, 0.02f, hexRGB(0x52B5D9), {}, false, static_cast<uint32_t>(29950 + d)});
    paintDab(cv, sx + 2.0f, sy - 4.0f + wing * 0.3f, 11.0f, 3.0f, -0.7f, hexRGB(0xD8F2FA), 0.62f, 0.40f, 29970 + d, 3);
    paintDab(cv, sx - 2.0f, sy - 4.0f - wing * 0.3f, 11.0f, 3.0f, 0.7f, hexRGB(0xD8F2FA), 0.62f, 0.40f, 29980 + d, 3);
  }
}

// Scene 3: Wind-Rippling Normandy Grass Blades, Scarlet Poppies & Fluttering Butterflies
inline void renderScene3Living(OilCanvas &cv, const CameraState &cam, double t) {
  if (cam.x + cv.w < 6100.0f || cam.x > 9600.0f) return;
  float timeF = static_cast<float>(t);

  // Wind-swept meadow grass blades & swaying poppy blooms visible inside viewport
  int wx0 = std::max(6350, static_cast<int>(cam.x) - 40);
  int wx1 = std::min(9250, static_cast<int>(cam.x + cv.w) + 40);
  int stepX = 24;
  int startGridX = (wx0 / stepX) * stepX;

  for (int gx = startGridX; gx <= wx1; gx += stepX) {
    float topY = getTerrainTopY(static_cast<float>(gx)) + 16.0f;
    for (int gy = static_cast<int>(topY); gy < 1260; gy += 30) {
      float depth = clampf((gy - topY) / 740.0f, 0.0f, 1.0f);
      float jx = (hash2D(gx, gy, 301u) - 0.5f) * 20.0f;
      float jy = (hash2D(gx, gy, 302u) - 0.5f) * 22.0f;
      float wx = gx + jx;
      float wy = gy + jy;
      float sx = wx - cam.x;
      float sy = wy - LAYER_Y_PAD - cam.y;
      if (sx < -30 || sx > cv.w + 30 || sy < -30 || sy > cv.h + 40) continue;

      // Skip sandy path center for dense poppies
      float pathY = 740.0f - (wx - 7300.0f) * 0.14f + std::sin(wx * 0.003f) * 26.0f;
      bool onPath = std::fabs(wy - pathY) < lerpf(16.0f, 34.0f, depth);

      // Continuous wind gust wave
      float wind = std::sin(timeF * 2.2f - wx * 0.0045f + wy * 0.003f) * 0.7f
                 + std::sin(timeF * 3.7f - wx * 0.009f) * 0.3f;
      float sway = (3.5f + depth * 8.5f) * (0.45f + wind);

      if (!onPath) {
        // Lush animated grass & golden clover blade
        float bh = lerpf(11.0f, 28.0f, depth);
        float hCol = hash2D(gx, gy, 303u);
        RGB gCol = hCol < 0.4f ? hexRGB(0x639848) : (hCol < 0.85f ? hexRGB(0x8EBF55) : hexRGB(0xCBD762));
        paintStroke(cv, {sx, sy, sx + sway, sy - bh, sway * 0.3f, lerpf(1.8f, 3.6f, depth),
                         0.82f, 0.55f, 0.22f, 3, 0.04f, gCol, {}, false, static_cast<uint32_t>(310000 + gx * 7 + gy)});
      }

      // Rich layered scarlet & coral poppies (sparse on path, dense across sunlit slope)
      float pChance = hash2D(gx, gy, 309u);
      float threshold = onPath ? 0.94f : (depth > 0.3f ? 0.56f : 0.72f);
      if (pChance > threshold) {
        float stemH = lerpf(12.0f, 32.0f, depth);
        float px = sx + sway * 1.15f;
        float py = sy - stemH;
        paintStroke(cv, {sx, sy, px, py, sway * 0.25f, lerpf(1.4f, 2.4f, depth),
                         0.85f, 0.45f, 0.15f, 3, 0.02f, hexRGB(0x46763E), {}, false, static_cast<uint32_t>(330000 + gx + gy)});

        float pRad = lerpf(4.0f, 10.5f, depth);
        RGB pA = hexRGB(0xD8352B);
        RGB pB = hexRGB(0xF35938);
        paintDab(cv, px - pRad * 0.32f, py, pRad * 1.05f, pRad * 0.70f, -0.35f, pA, 0.94f, 0.86f, 340000 + gx * 3 + gy, 4);
        paintDab(cv, px + pRad * 0.32f, py + 0.5f, pRad * 1.05f, pRad * 0.70f, 0.35f, pB, 0.94f, 0.86f, 341000 + gx * 3 + gy, 4);
        paintDab(cv, px, py - pRad * 0.25f, pRad * 0.90f, pRad * 0.55f, 0.0f, hexRGB(0xFF834F), 0.88f, 0.92f, 342000 + gx * 3 + gy, 3);
        paintDab(cv, px, py + 0.5f, pRad * 0.38f, pRad * 0.32f, 0.0f, hexRGB(0x361C2E), 0.92f, 0.90f, 343000 + gx * 3 + gy, 2);
      }
    }
  }

  // Delicate fluttering Pieris white & sulfur-yellow butterflies dancing over the poppies
  for (int b = 0; b < 14; ++b) {
    float wx = 7200.0f + b * 145.0f + std::sin(timeF * 0.85f + b * 2.1f) * 110.0f;
    float wy = 660.0f + (b % 4) * 95.0f + std::cos(timeF * 1.6f + b * 1.4f) * 48.0f;
    float sx = wx - cam.x;
    float sy = wy - LAYER_Y_PAD - cam.y;
    if (sx < -30 || sx > cv.w + 30) continue;
    float wingOpen = 0.35f + 0.65f * std::fabs(std::sin(timeF * 10.5f + b * 1.7f));
    RGB bfCol = (b % 3 == 0) ? hexRGB(0xFAF18A) : hexRGB(0xFFFDF5);
    paintDab(cv, sx - 3.5f * wingOpen, sy - 2.5f, 7.5f * wingOpen + 2.0f, 4.5f, -0.5f, bfCol, 0.90f, 0.70f, 350000 + b * 2, 3);
    paintDab(cv, sx + 3.5f * wingOpen, sy - 2.0f, 7.5f * wingOpen + 2.0f, 4.5f, 0.5f, bfCol, 0.90f, 0.70f, 350001 + b * 2, 3);
  }
}

// Scene 4: Grazing Woolly Sheep Flock, Shepherd, Swooping Swallows & Golden Harvest Dust
inline void renderScene4Living(OilCanvas &cv, const CameraState &cam, double t) {
  if (cam.x + cv.w < 9600.0f || cam.x > 12800.0f) return;
  float timeF = static_cast<float>(t);

  // 9 Sculpted Woolly Sheep grazing across the warm golden-violet sunset field (ZERO stick legs!)
  struct SheepDef { float wx, wy, scale, phase; int dir; };
  static const SheepDef flock[] = {
    {11120, 870, 0.85f, 0.2f, 1}, {11215, 895, 0.92f, 1.4f, 1},
    {11310, 860, 0.82f, 2.3f, -1}, {11440, 915, 0.96f, 0.7f, 1},
    {11535, 890, 0.88f, 3.1f, 1}, {11635, 935, 1.02f, 1.9f, -1},
    {11740, 910, 0.94f, 4.0f, 1}, {11830, 955, 1.05f, 2.7f, 1},
    {11040, 915, 0.90f, 5.1f, 1}
  };

  for (int i = 0; i < 9; ++i) {
    const auto &sh = flock[i];
    float walkX = std::sin(timeF * 0.22f + sh.phase) * 14.0f;
    float sx = sh.wx + walkX - cam.x;
    float sy = sh.wy - LAYER_Y_PAD - cam.y;
    if (sx < -80 || sx > cv.w + 80) continue;

    float s = sh.scale;
    float grazeDip = std::max(0.0f, std::sin(timeF * 1.15f + sh.phase)) * 4.5f * s;

    // Grounded violet shadow stretching left
    for (int k = 0; k < 8; ++k) {
      paintDab(cv, sx - 12.0f * s - k * 3.5f * s, sy + 14.0f * s + (k % 2) * 2.0f,
               14.0f * s, 5.0f * s, -0.1f, hexRGB(0x5B5074), 0.45f, 0.18f, 410000 + i * 20 + k, 4);
    }
    // Soft shadowed legs tucked naturally under fleece curls
    for (int lg : {-11, -5, 6, 12}) {
      paintStroke(cv, {sx + lg * s, sy + 4.0f * s, sx + lg * s, sy + 15.0f * s, 0.0f, 3.2f * s,
                       0.88f, 0.45f, 0.12f, 3, 0.02f, hexRGB(0x463D55), {}, false, static_cast<uint32_t>(411000 + i * 10 + lg)});
    }
    // Overlapping warm-cream & cool-lavender woolly curls
    for (int c = 0; c < 14; ++c) {
      float cx = sx + ((c % 5) - 2) * 7.2f * s;
      float cy = sy + ((c / 5) - 1) * 5.2f * s;
      bool topLit = cy < sy + 1.0f * s && cx > sx - 8.0f * s;
      RGB wool = topLit ? mixRGB(hexRGB(0xF6DEC2), hexRGB(0xFFF3D4), (c % 2) * 0.5f)
                        : mixRGB(hexRGB(0x8D7D98), hexRGB(0xC9B2B0), 0.45f);
      paintDab(cv, cx, cy, 13.0f * s, 9.5f * s, (c % 3 - 1) * 0.4f, wool, 0.94f, 0.80f, 412000 + i * 30 + c, 4);
    }
    // Sculpted dark-umber head dipping softly to graze
    float hx = sx + sh.dir * 20.0f * s;
    float hy = sy - 2.0f * s + grazeDip;
    paintDab(cv, hx, hy, 10.5f * s, 7.2f * s, sh.dir * 0.35f, hexRGB(0x3D3548), 0.95f, 0.70f, 413000 + i, 3);
    paintDab(cv, hx - sh.dir * 3.0f * s, hy - 3.5f * s, 5.5f * s, 2.8f * s, -sh.dir * 0.6f, hexRGB(0x4E4259), 0.92f, 0.65f, 413100 + i, 3);
  }

  // Swooping Barn Swallows arcing through warm sunset sky
  for (int sw = 0; sw < 8; ++sw) {
    float wx = 10400.0f + sw * 210.0f + std::fmod(timeF * (95.0f + sw * 6.0f), 1900.0f) - 400.0f;
    float wy = 390.0f + std::sin(timeF * 1.4f + sw * 1.3f) * 55.0f + (sw % 3) * 32.0f;
    float sx = wx - cam.x;
    float sy = wy - LAYER_Y_PAD - cam.y;
    if (sx < -40 || sx > cv.w + 40) continue;
    float flap = std::sin(timeF * 8.5f + sw * 1.4f);
    RGB bCol = hexRGB(0x2F2F4C);
    paintStroke(cv, {sx - 10.0f, sy - flap * 6.0f, sx, sy + 1.5f, -2.0f, 2.6f, 0.92f, 0.60f, 0.10f, 3, 0.02f, bCol, {}, false, static_cast<uint32_t>(420000 + sw)});
    paintStroke(cv, {sx, sy + 1.5f, sx + 10.0f, sy - flap * 6.0f, 2.0f, 2.6f, 0.92f, 0.60f, 0.10f, 3, 0.02f, bCol, {}, false, static_cast<uint32_t>(421000 + sw)});
  }

  // Sunlit golden harvest pollen motes drifting slowly upward
  for (int m = 0; m < 45; ++m) {
    float wx = 10600.0f + (m * 37) % 1600 + std::sin(timeF * 0.7f + m) * 28.0f;
    float wy = 620.0f + (m * 59) % 420 - std::fmod(timeF * 14.0f + m * 17.0f, 180.0f);
    float sx = wx - cam.x;
    float sy = wy - LAYER_Y_PAD - cam.y;
    if (sx < -20 || sx > cv.w + 20) continue;
    float glow = 0.45f + 0.55f * std::sin(timeF * 2.4f + m);
    paintDab(cv, sx, sy, 4.5f, 3.8f, 0.3f, hexRGB(0xFFE78E), glow * 0.72f, 0.85f, 430000 + m, 3);
  }
}

// Scene 5: Painterly Crescent Moon, Stars, Gliding Swans & Rising Fireflies
inline void renderScene5Living(OilCanvas &cv, const CameraState &cam, double t) {
  if (cam.x + cv.w < 12600.0f) return;
  float timeF = static_cast<float>(t);

  // 1. Sculpted Painterly Open Crescent Moon & Twinkling Stars (mapped cleanly at Sky Layer depth 0.16!)
  float moonSX = 3760.0f - cam.x * 0.16f;
  float moonSY = 335.0f - LAYER_Y_PAD - cam.y * 0.16f;
  if (moonSX > -160 && moonSX < cv.w + 160 && moonSY > -160 && moonSY < cv.h) {
    float theta0 = 2.28f; // Lit lower-left crescent rim facing sunset horizon
    // Soft violet-ivory glow centered gently around the lit crescent limb (never a closed ring!)
    for (int i = 0; i < 48; ++i) {
      float u = (i / 47.0f) * 2.0f - 1.0f;
      float ang = theta0 + u * 1.45f;
      float r = 24.0f + (i % 5) * 12.0f;
      RGB aura = mixRGB(hexRGB(0x5E5B92), hexRGB(0xF6E6BD), 1.0f - r / 84.0f);
      paintDab(cv, moonSX + std::cos(ang) * r, moonSY + std::sin(ang) * r, 15.0f, 7.0f, ang + 1.57f,
               aura, 0.12f + (1.0f - r / 84.0f) * 0.18f, 0.22f, 510000 + i, 4);
    }
    // Crisp open crescent built from tapered pearl-gold strokes (leaving concave dark side 100% open!)
    float R = 31.0f;
    for (int k = 0; k < 56; ++k) {
      float s = (k / 55.0f) * 2.0f - 1.0f; // -1..+1
      float ang = theta0 + s * 1.24f;     // ~142 deg open arc
      float bell = std::pow(std::max(0.0f, std::cos(s * 1.5708f)), 0.85f);
      float thick = 1.4f + bell * 9.5f;
      float rMid = R - thick * 0.36f;
      float mx = moonSX + std::cos(ang) * rMid;
      float my = moonSY + std::sin(ang) * rMid;
      RGB mCol = mixRGB(hexRGB(0xFCECB8), hexRGB(0xFFFDF2), bell);
      paintDab(cv, mx, my, std::max(2.2f, thick * 1.05f), std::max(1.5f, thick * 0.56f), ang + 1.57f,
               mCol, 0.78f + bell * 0.20f, 0.88f, 511000 + k, 4);
    }
    // Bright crisp outer rim line tying the crescent horns smoothly
    for (int k = 0; k < 32; ++k) {
      float s0 = (k / 32.0f) * 2.0f - 1.0f;
      float s1 = ((k + 1) / 32.0f) * 2.0f - 1.0f;
      float a0 = theta0 + s0 * 1.24f;
      float a1 = theta0 + s1 * 1.24f;
      float bell = std::pow(std::max(0.0f, std::cos(((s0 + s1) * 0.5f) * 1.5708f)), 0.9f);
      paintStroke(cv, {
        moonSX + std::cos(a0) * R, moonSY + std::sin(a0) * R,
        moonSX + std::cos(a1) * R, moonSY + std::sin(a1) * R,
        0.0f, 1.3f + bell * 2.2f, 0.95f, 0.92f, 0.08f, 3, 0.02f, hexRGB(0xFFFDF0), {}, false, static_cast<uint32_t>(512000 + k)
      });
    }
  }

  // Twinkling Painterly Night Stars across upper sky
  RNG srng(515000ULL);
  for (int s = 0; s < 95; ++s) {
    float wx0 = srng.range(3150.0f, 4350.0f);
    float wy0 = srng.range(185.0f, 540.0f);
    float sx = wx0 - cam.x * 0.16f;
    float sy = wy0 - LAYER_Y_PAD - cam.y * 0.16f;
    if (sx < -10 || sx > cv.w + 10 || sy < 0 || sy > 560) continue;
    float tw = 0.35f + 0.65f * (0.5f + 0.5f * std::sin(timeF * (1.8f + (s % 5) * 0.4f) + s * 1.7f));
    RGB stC = (s % 3 == 0) ? hexRGB(0xFFF6D2) : hexRGB(0xD8E2FF);
    paintDab(cv, sx, sy, 3.8f + (s % 3) * 1.1f, 2.4f, 0.0f, stC, tw * 0.82f, 0.80f, 516000 + s, 3);
  }

  // 2. Two Graceful White Swans gliding slowly across the twilight lantern reflection
  float swanProg = clampf((timeF - 78.0f) / 14.0f, 0.0f, 1.0f);
  struct SwanDef { float dx, dy, scale, phase; };
  static const SwanDef swans[] = {
    {0.0f, 0.0f, 1.0f, 0.0f},
    {-98.0f, 24.0f, 0.88f, 1.3f}
  };
  for (int i = 0; i < 2; ++i) {
    float wx = 14920.0f - swanProg * 280.0f + swans[i].dx;
    float wy = 895.0f + swans[i].dy + std::sin(timeF * 1.1f + swans[i].phase) * 2.0f;
    float sx = wx - cam.x;
    float sy = wy - LAYER_Y_PAD - cam.y;
    if (sx < -120 || sx > cv.w + 120) continue;
    float sc = swans[i].scale;

    // Gentle expanding V-wake behind gliding swan
    for (int w = 1; w <= 12; ++w) {
      float age = w / 12.0f;
      RGB wakeC = mixRGB(hexRGB(0x6D7AA8), hexRGB(0xDFBA7D), 0.28f * (1.0f - age));
      paintDab(cv, sx + w * 14.0f * sc, sy + 8.0f * sc + w * 2.2f * sc, 16.0f * sc, 2.4f, 0.08f,
               wakeC, (1.0f - age) * 0.55f, 0.40f, 520000 + i * 30 + w, 3);
      paintDab(cv, sx + w * 14.0f * sc, sy + 8.0f * sc - w * 1.6f * sc, 14.0f * sc, 2.2f, -0.06f,
               wakeC, (1.0f - age) * 0.48f, 0.40f, 521000 + i * 30 + w, 3);
    }

    // Soft inverted swan reflection in water
    for (int k = 0; k < 14; ++k) {
      paintDab(cv, sx - 14.0f * sc + k * 4.4f * sc + std::sin(timeF * 2.8f + k) * 2.5f, sy + 16.0f * sc + (k % 3) * 4.0f,
               14.0f * sc, 4.0f * sc, 0.05f, hexRGB(0x8893BD), 0.36f, 0.20f, 522000 + i * 20 + k, 4);
    }

    // Plump rounded breast & lifted arched wing feathers (classic sculptural swan form)
    for (int f = 0; f < 22; ++f) {
      float u = f / 21.0f;
      float fx = sx - 19.0f * sc + u * 44.0f * sc;
      float arch = std::sin(u * 3.14159f);
      float fy = sy - 2.0f * sc - arch * 12.5f * sc + (f % 3 - 1) * 2.2f * sc;
      RGB fCol = (u < 0.25f) ? hexRGB(0xFFF3DC) // warm amber lantern catchlight on breast
               : (u > 0.72f ? hexRGB(0xDCE2F4) : mixRGB(hexRGB(0xB8C2E2), hexRGB(0xFFFFFF), (f % 2) * 0.75f));
      paintDab(cv, fx, fy, 14.0f * sc, 7.2f * sc, -0.25f + u * 0.45f, fCol, 0.94f, 0.85f, 523000 + i * 30 + f, 4);
    }
    // High arched secondary wing plume
    for (int w = 0; w < 9; ++w) {
      float u = w / 8.0f;
      paintDab(cv, sx - 2.0f * sc + u * 26.0f * sc, sy - 13.0f * sc - std::sin(u * 3.14f) * 6.5f * sc,
               12.0f * sc, 5.5f * sc, -0.35f + u * 0.4f,
               w < 5 ? hexRGB(0xFFFDF5) : hexRGB(0xD8E0F4), 0.94f, 0.88f, 523500 + i * 20 + w, 4);
    }
    // Lower waterline shadow under belly for solid pond contact
    paintStroke(cv, {sx - 20.0f * sc, sy + 5.0f * sc, sx + 26.0f * sc, sy + 5.5f * sc, 1.5f * sc, 4.0f * sc,
                     0.70f, 0.30f, 0.10f, 4, 0.02f, hexRGB(0x4E5B88), {}, false, static_cast<uint32_t>(523900 + i)});

    // Sculpted graceful tapering S-curved neck (facing left toward lantern reflection)
    for (int n = 0; n < 15; ++n) {
      float u = n / 14.0f;
      float nx = sx - 16.0f * sc - std::sin(u * 2.75f) * 14.5f * sc - u * 4.5f * sc;
      float ny = sy - 5.0f * sc - u * 31.0f * sc;
      float nw = lerpf(8.5f, 4.4f, u) * sc;
      RGB nCol = mixRGB(hexRGB(0xFFEBD0), hexRGB(0xFFFBF2), u * 0.75f);
      paintDab(cv, nx, ny, nw, nw * 0.65f, 1.57f - std::cos(u * 2.75f) * 0.5f, nCol, 0.96f, 0.85f, 524000 + i * 20 + n, 3);
    }
    // Rounded crown, dark eye-lore & warm orange-coral beak
    float headX = sx - 25.5f * sc, headY = sy - 37.5f * sc;
    paintDab(cv, headX, headY, 8.6f * sc, 5.6f * sc, 0.08f, hexRGB(0xFFFDF4), 0.97f, 0.88f, 525000 + i, 3);
    paintDab(cv, headX - 4.2f * sc, headY + 0.5f * sc, 3.2f * sc, 2.0f * sc, -0.1f, hexRGB(0x2B2C3E), 0.94f, 0.75f, 525050 + i, 2);
    paintDab(cv, headX - 8.2f * sc, headY + 1.8f * sc, 6.2f * sc, 2.6f * sc, -0.22f, hexRGB(0xEC823A), 0.96f, 0.82f, 525100 + i, 2);
  }

  // 3. Rising Warm Golden Fireflies floating from shoreline reeds toward starry sky
  RNG frng(530000ULL);
  for (int f = 0; f < 80; ++f) {
    float baseWX = frng.range(13200.0f, 15900.0f);
    float baseWY = frng.range(380.0f, 1020.0f);
    float speed = frng.range(8.0f, 18.0f);
    float wx = baseWX + std::sin(timeF * 0.9f + f * 1.4f) * 32.0f;
    float wy = baseWY - std::fmod(timeF * speed + f * 23.0f, 260.0f);
    float sx = wx - cam.x;
    float sy = wy - LAYER_Y_PAD - cam.y;
    if (sx < -20 || sx > cv.w + 20 || sy < -20 || sy > cv.h + 20) continue;

    float pulse = std::pow(0.5f + 0.5f * std::sin(timeF * frng.range(1.8f, 3.6f) + f * 2.1f), 1.6f);
    if (pulse < 0.18f) continue;
    // Soft warm oil-dab glow + bright chartreuse-gold heart
    paintDab(cv, sx, sy, 13.0f, 9.0f, 0.3f, hexRGB(0xE8B94B), pulse * 0.30f, 0.35f, 531000 + f, 4);
    paintDab(cv, sx, sy, 5.0f, 3.8f, -0.2f, hexRGB(0xFFF6A8), pulse * 0.92f, 0.90f, 532000 + f, 3);
  }
}

// Render complete single frame at timeSec into outRGB (1920x1080 RGB24)
inline void renderWorldFrame(const WorldSceneData &data, double timeSec,
                             OilCanvas &frameCanvas, std::vector<uint8_t> &outRGB) {
  CameraState cam = getCamera(timeSec);
  float timeF = static_cast<float>(timeSec);

  if (frameCanvas.w != 1920 || frameCanvas.h != 1080) {
    frameCanvas.resize(1920, 1080, true, {0.9f, 0.9f, 0.85f});
  }

  // Layer 0 (d = 0.16): Sky panorama opaque blit
  blitSkyOpaque(frameCanvas, data.skyLayer, -cam.x * 0.16f, -LAYER_Y_PAD - cam.y * 0.16f);

  // Layer 1 (d = 0.34): Far Normandy Horizon
  compositeLayerMT(frameCanvas, data.horizonLayer, -cam.x * 0.34f, -LAYER_Y_PAD - cam.y * 0.34f);

  // Layer 2 (d = 0.62): Midground Groves & Cottages
  compositeLayerMT(frameCanvas, data.midgroundLayer, -cam.x * 0.62f, -LAYER_Y_PAD - cam.y * 0.62f);

  // Layer 3 (d = 1.00): Grounded Landmarks, Bridge, Woman with Parasol, Haystacks & Boathouse
  compositeLayerMT(frameCanvas, data.worldLayer, -cam.x, -LAYER_Y_PAD - cam.y);

  // Layer 4 (d = 1.00): Live Mirror Water Reflections & Broken-Color Water Brushwork
  renderAnimatedWater(frameCanvas, cam, timeSec);

  // Living Per-Frame Scenes (strictly ordered & grounded at d = 1.00)
  renderScene1Living(frameCanvas, cam, timeSec);
  renderScene2Living(frameCanvas, cam, timeSec);
  renderScene3Living(frameCanvas, cam, timeSec);
  renderScene4Living(frameCanvas, cam, timeSec);
  renderScene5Living(frameCanvas, cam, timeSec);

  // Layer 5 (d = 1.18): Foreground Spatial Portal Curtains with subtle wind breath
  for (int p = 0; p < 4; ++p) {
    const auto &portal = data.portals[p];
    float swayX = std::sin(timeF * 1.15f + p * 1.7f) * 4.5f;
    float swayY = std::cos(timeF * 0.85f + p * 2.1f) * 2.0f;
    float px = portal.anchorWorldX - cam.x * portal.depth + swayX;
    if (px + portal.canvas.w < -10 || px > frameCanvas.w + 10) continue;
    compositeLayerMT(frameCanvas, portal.canvas, px, -LAYER_Y_PAD - cam.y * portal.depth + swayY);
  }

  // Layer 6: Final Raking Impasto Relief & Belgian Linen Canvas Resolve
  resolveCanvasToRGB24(frameCanvas, outRGB, 0.10f, 0.16f);
}

} // namespace monet

#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <thread>
#include <vector>

namespace monet {

struct RGB {
  float r, g, b;
};

inline float clampf(float v, float lo, float hi) {
  return v < lo ? lo : (v > hi ? hi : v);
}

inline float lerpf(float a, float b, float t) {
  return a + (b - a) * t;
}

inline float smoothstepf(float e0, float e1, float x) {
  float t = clampf((x - e0) / (e1 - e0), 0.0f, 1.0f);
  return t * t * (3.0f - 2.0f * t);
}

inline RGB mixRGB(RGB a, RGB b, float t) {
  return {lerpf(a.r, b.r, t), lerpf(a.g, b.g, t), lerpf(a.b, b.b, t)};
}

inline RGB hexRGB(uint32_t hex) {
  return {
    ((hex >> 16) & 0xFF) / 255.0f,
    ((hex >> 8) & 0xFF) / 255.0f,
    (hex & 0xFF) / 255.0f
  };
}

// Fast deterministic SplitMix64 PRNG
struct RNG {
  uint64_t state;
  explicit RNG(uint64_t seed = 0x9E3779B97F4A7C15ULL) : state(seed) {}
  inline uint64_t nextU64() {
    uint64_t z = (state += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
  }
  inline float next() {
    return static_cast<float>((nextU64() >> 40) & 0xFFFFFF) / 16777216.0f;
  }
  inline float range(float lo, float hi) {
    return lo + (hi - lo) * next();
  }
};

// Smooth 2D value noise & FBM
inline float hash2D(int ix, int iy, uint32_t seed = 1337) {
  uint32_t h = static_cast<uint32_t>(ix) * 374761393u +
               static_cast<uint32_t>(iy) * 668265263u + seed * 1442695041u;
  h = (h ^ (h >> 13)) * 1274126177u;
  return static_cast<float>((h ^ (h >> 16)) & 0xFFFFFF) / 16777216.0f;
}

inline float noise2D(float x, float y, uint32_t seed = 101) {
  int ix = static_cast<int>(std::floor(x));
  int iy = static_cast<int>(std::floor(y));
  float fx = x - ix;
  float fy = y - iy;
  float ux = fx * fx * (3.0f - 2.0f * fx);
  float uy = fy * fy * (3.0f - 2.0f * fy);
  float a = hash2D(ix, iy, seed);
  float b = hash2D(ix + 1, iy, seed);
  float c = hash2D(ix, iy + 1, seed);
  float d = hash2D(ix + 1, iy + 1, seed);
  return lerpf(lerpf(a, b, ux), lerpf(c, d, ux), uy);
}

inline float fbm2D(float x, float y, int octaves = 4, uint32_t seed = 101) {
  float val = 0.0f, amp = 0.5f, freq = 1.0f, norm = 0.0f;
  for (int i = 0; i < octaves; ++i) {
    val += amp * noise2D(x * freq, y * freq, seed + static_cast<uint32_t>(i * 97));
    norm += amp;
    amp *= 0.5f;
    freq *= 2.03f;
  }
  return val / norm;
}

// Impressionist color helpers (HSL jitter + temperature shifting)
inline RGB jitterColor(RGB base, RNG &rng, float hueAmt, float satAmt, float valAmt) {
  // Subtle perceptual RGB + warm/cool complementary variation
  float dr = rng.range(-valAmt, valAmt);
  float dg = rng.range(-valAmt * 0.9f, valAmt * 0.9f);
  float db = rng.range(-valAmt, valAmt);
  float temp = rng.range(-hueAmt, hueAmt); // +warm (yellow-red), -cool (blue-violet)
  float sat = rng.range(-satAmt, satAmt);
  float lum = 0.299f * base.r + 0.587f * base.g + 0.114f * base.b;
  float r = lerpf(lum, base.r, 1.0f + sat) + dr + temp * 0.65f;
  float g = lerpf(lum, base.g, 1.0f + sat) + dg + temp * 0.22f;
  float b = lerpf(lum, base.b, 1.0f + sat) + db - temp * 0.72f;
  return {clampf(r, 0.0f, 1.0f), clampf(g, 0.0f, 1.0f), clampf(b, 0.0f, 1.0f)};
}

inline RGB shiftWarm(RGB c, float amount, RGB lightTint = {1.0f, 0.91f, 0.64f}) {
  return mixRGB(c, lightTint, clampf(amount, 0.0f, 1.0f));
}

inline RGB shiftCool(RGB c, float amount, RGB shadowTint = {0.26f, 0.30f, 0.58f}) {
  return mixRGB(c, shadowTint, clampf(amount, 0.0f, 1.0f));
}

struct OilCanvas {
  int w = 0;
  int h = 0;
  std::vector<float> r, g, b, a, height;

  OilCanvas() = default;
  OilCanvas(int width, int height, bool opaque = false, RGB bg = {0.95f, 0.92f, 0.86f}) {
    resize(width, height, opaque, bg);
  }

  void resize(int width, int height, bool opaque = false, RGB bg = {0.95f, 0.92f, 0.86f}) {
    w = width;
    h = height;
    size_t n = static_cast<size_t>(w) * h;
    this->r.assign(n, opaque ? bg.r : 0.0f);
    this->g.assign(n, opaque ? bg.g : 0.0f);
    this->b.assign(n, opaque ? bg.b : 0.0f);
    this->a.assign(n, opaque ? 1.0f : 0.0f);
    this->height.assign(n, 0.0f);
  }

  inline void blendPixel(int px, int py, RGB col, float alpha, float impH) {
    if (px < 0 || py < 0 || px >= w || py >= h || alpha <= 0.002f) return;
    size_t idx = static_cast<size_t>(py) * w + px;
    float dstA = a[idx];
    float outA = alpha + dstA * (1.0f - alpha);
    if (outA <= 1e-5f) return;

    // Premultiplied-style composition so transparent layer edges never darken/halo
    float srcW = alpha;
    float dstW = dstA * (1.0f - alpha);
    r[idx] = (col.r * srcW + r[idx] * dstW) / outA;
    g[idx] = (col.g * srcW + g[idx] * dstW) / outA;
    b[idx] = (col.b * srcW + b[idx] * dstW) / outA;
    a[idx] = outA;
    height[idx] = lerpf(height[idx], height[idx] * 0.45f + impH, clampf(alpha * 1.15f, 0.0f, 1.0f));
  }

  // Sample layer with bilinear filtering (for smooth sub-pixel parallax pan/zoom)
  inline void sampleBilinear(float fx, float fy, float &or_, float &og_, float &ob_, float &oa_, float &oh_) const {
    if (fx < -1.0f || fy < -1.0f || fx >= w || fy >= h) {
      or_ = og_ = ob_ = oa_ = oh_ = 0.0f;
      return;
    }
    int x0 = static_cast<int>(std::floor(fx));
    int y0 = static_cast<int>(std::floor(fy));
    float tx = fx - x0;
    float ty = fy - y0;
    int x1 = x0 + 1;
    int y1 = y0 + 1;
    x0 = std::max(0, std::min(w - 1, x0));
    x1 = std::max(0, std::min(w - 1, x1));
    y0 = std::max(0, std::min(h - 1, y0));
    y1 = std::max(0, std::min(h - 1, y1));

    size_t i00 = static_cast<size_t>(y0) * w + x0;
    size_t i10 = static_cast<size_t>(y0) * w + x1;
    size_t i01 = static_cast<size_t>(y1) * w + x0;
    size_t i11 = static_cast<size_t>(y1) * w + x1;

    float a00 = a[i00], a10 = a[i10], a01 = a[i01], a11 = a[i11];
    float w00 = (1 - tx) * (1 - ty), w10 = tx * (1 - ty), w01 = (1 - tx) * ty, w11 = tx * ty;
    oa_ = w00 * a00 + w10 * a10 + w01 * a01 + w11 * a11;
    if (oa_ < 1e-4f) {
      or_ = og_ = ob_ = oa_ = oh_ = 0.0f;
      return;
    }
    or_ = (w00 * a00 * r[i00] + w10 * a10 * r[i10] + w01 * a01 * r[i01] + w11 * a11 * r[i11]) / oa_;
    og_ = (w00 * a00 * g[i00] + w10 * a10 * g[i10] + w01 * a01 * g[i01] + w11 * a11 * g[i11]) / oa_;
    ob_ = (w00 * a00 * b[i00] + w10 * a10 * b[i10] + w01 * a01 * b[i01] + w11 * a11 * b[i11]) / oa_;
    oh_ = (w00 * height[i00] + w10 * height[i10] + w01 * height[i01] + w11 * height[i11]);
  }
};

// Multi-bristle curved oil brushstroke renderer
struct StrokeParams {
  float x0, y0;
  float x1, y1;
  float bend = 0.0f;         // Quadratic Bezier perpendicular curve amount (pixels)
  float width = 8.0f;        // Brush width (pixels)
  float opacity = 0.78f;     // Peak pigment opacity
  float impasto = 0.55f;     // Height deposit
  float dryness = 0.28f;     // Dry-brush break-up toward stroke tail
  int bristles = 9;          // Number of parallel bristles
  float colorMarble = 0.045f;// Per-bristle pigment variation
  RGB color = {0.5f, 0.5f, 0.5f};
  RGB accentColor = {0.5f, 0.5f, 0.5f};
  bool useAccent = false;
  uint32_t seed = 1;
};

inline void paintStroke(OilCanvas &cv, const StrokeParams &p) {
  float dx = p.x1 - p.x0;
  float dy = p.y1 - p.y0;
  float len = std::sqrt(dx * dx + dy * dy);
  if (len < 0.4f || p.width < 0.8f) return;

  // Quick bounding box cull
  float pad = p.width * 0.75f + std::fabs(p.bend) + 3.0f;
  float minX = std::min(p.x0, p.x1) - pad;
  float maxX = std::max(p.x0, p.x1) + pad;
  float minY = std::min(p.y0, p.y1) - pad;
  float maxY = std::max(p.y0, p.y1) + pad;
  if (maxX < 0 || minX >= cv.w || maxY < 0 || minY >= cv.h) return;

  float nx = -dy / len;
  float ny = dx / len;
  float cx = 0.5f * (p.x0 + p.x1) + nx * p.bend;
  float cy = 0.5f * (p.y0 + p.y1) + ny * p.bend;

  int steps = std::max(4, static_cast<int>(len * 1.45f));
  float invSteps = 1.0f / steps;
  float halfW = p.width * 0.5f;
  int wSteps = std::max(3, static_cast<int>(p.width * 1.6f));
  float invW = 1.0f / wSteps;

  // Precompute deterministic per-bristle phase & tint
  int B = std::clamp(p.bristles, 3, 18);
  float bristleTint[18];
  float bristleLoad[18];
  for (int bi = 0; bi < B; ++bi) {
    float h1 = hash2D(bi, static_cast<int>(p.seed & 0xFFFF), p.seed ^ 0x5A17u);
    float h2 = hash2D(bi + 31, static_cast<int>((p.seed >> 8) & 0xFFFF), p.seed ^ 0xA3C1u);
    bristleTint[bi] = (h1 - 0.5f) * 2.0f * p.colorMarble;
    bristleLoad[bi] = 0.65f + 0.55f * h2;
  }

  for (int si = 0; si <= steps; ++si) {
    float t = si * invSteps;
    float mt = 1.0f - t;
    float bx = mt * mt * p.x0 + 2.0f * mt * t * cx + t * t * p.x1;
    float by = mt * mt * p.y0 + 2.0f * mt * t * cy + t * t * p.y1;

    // Tangent direction for clean perpendicular normal along curve
    float tx = 2.0f * mt * (cx - p.x0) + 2.0f * t * (p.x1 - cx);
    float ty = 2.0f * mt * (cy - p.y0) + 2.0f * t * (p.y1 - cy);
    float tl = std::sqrt(tx * tx + ty * ty);
    if (tl < 1e-4f) continue;
    float pnx = -ty / tl;
    float pny = tx / tl;

    // Taper width subtly at start and end of brushstroke (filbert tip shape)
    float startEnv = smoothstepf(0.0f, 0.14f, t);
    float endEnv = 1.0f - smoothstepf(0.72f, 1.0f, t);
    float widthScale = 0.68f + 0.36f * std::sin(t * 3.1415926f);
    float curHalfW = halfW * widthScale;

    // Paint depletion & dry-brush break-up toward tail
    float longitudinalEnv = startEnv * (0.35f + 0.65f * endEnv);

    for (int wi = 0; wi <= wSteps; ++wi) {
      float u = wi * invW; // 0..1 across brush width
      float lat = (u * 2.0f - 1.0f); // -1..+1
      float pxF = bx + pnx * (lat * curHalfW);
      float pyF = by + pny * (lat * curHalfW);
      int px = static_cast<int>(std::lround(pxF));
      int py = static_cast<int>(std::lround(pyF));
      if (px < 0 || py < 0 || px >= cv.w || py >= cv.h) continue;

      // Bristle comb wave + organic bristle groove
      float bf = u * (B - 1);
      int bi = std::clamp(static_cast<int>(bf), 0, B - 1);
      float bFrac = bf - bi;
      float hairWave = 0.58f + 0.42f * std::sin(bf * 3.1415926f * 2.0f);

      // Dry-brush fragmentation at tail and outer edges
      float dryMask = 1.0f;
      if (p.dryness > 0.01f && t > 0.45f) {
        float nDry = hash2D(static_cast<int>(t * 28.0f), bi * 7, p.seed);
        float thresh = p.dryness * ((t - 0.45f) / 0.55f) * 0.85f;
        if (nDry < thresh) dryMask = 0.18f;
      }

      // Edge profile + slight paint ridge pushed to outer rim of stroke
      float edgeSoft = 1.0f - smoothstepf(0.72f, 1.0f, std::fabs(lat));
      float rimRidge = std::exp(-std::pow((std::fabs(lat) - 0.78f) / 0.16f, 2.0f)) * 0.42f;

      float alpha = p.opacity * longitudinalEnv * edgeSoft * hairWave * bristleLoad[bi] * dryMask;
      alpha = clampf(alpha, 0.0f, 0.96f);
      if (alpha < 0.015f) continue;

      // Slight marbled color across bristles + optional wet secondary accent
      float m = bristleTint[bi] + (bFrac - 0.5f) * p.colorMarble * 0.4f;
      RGB col = p.useAccent ? mixRGB(p.color, p.accentColor, clampf(0.15f + u * 0.6f + m, 0.0f, 1.0f)) : p.color;
      col.r = clampf(col.r + m * 0.85f, 0.0f, 1.0f);
      col.g = clampf(col.g + m * 0.95f, 0.0f, 1.0f);
      col.b = clampf(col.b - m * 0.55f, 0.0f, 1.0f);

      float imp = p.impasto * (0.45f + 0.55f * hairWave + rimRidge) * longitudinalEnv;
      cv.blendPixel(px, py, col, alpha, imp);
    }
  }
}

// High-density dabbed Impressionist touch (for blossoms, leaves, sunlit sparkles)
inline void paintDab(OilCanvas &cv, float x, float y, float len, float wid, float angle,
                     RGB col, float opacity, float impasto, uint32_t seed, int bristles = 6) {
  float c = std::cos(angle), s = std::sin(angle);
  float hl = len * 0.5f;
  StrokeParams sp;
  sp.x0 = x - c * hl;
  sp.y0 = y - s * hl;
  sp.x1 = x + c * hl;
  sp.y1 = y + s * hl;
  sp.bend = ((hash2D(static_cast<int>(x), static_cast<int>(y), seed) - 0.5f) * 0.35f) * len;
  sp.width = wid;
  sp.opacity = opacity;
  sp.impasto = impasto;
  sp.dryness = 0.22f;
  sp.bristles = bristles;
  sp.color = col;
  sp.seed = seed;
  paintStroke(cv, sp);
}

// Composite src OilCanvas over dst OilCanvas at pixel offset (dx, dy) with scale & optional globalAlpha
inline void compositeLayer(OilCanvas &dst, const OilCanvas &src, float offsetX, float offsetY,
                           float scale = 1.0f, float globalAlpha = 1.0f,
                           int yStart = 0, int yEnd = -1) {
  if (yEnd < 0 || yEnd > dst.h) yEnd = dst.h;
  float invScale = 1.0f / scale;
  for (int y = std::max(0, yStart); y < yEnd; ++y) {
    float sy = (y - offsetY) * invScale;
    if (sy < -1.0f || sy >= src.h) continue;
    for (int x = 0; x < dst.w; ++x) {
      float sx = (x - offsetX) * invScale;
      if (sx < -1.0f || sx >= src.w) continue;
      float sr, sg, sb, sa, sh;
      src.sampleBilinear(sx, sy, sr, sg, sb, sa, sh);
      sa *= globalAlpha;
      if (sa > 0.005f) {
        dst.blendPixel(x, y, {sr, sg, sb}, sa, sh * globalAlpha);
      }
    }
  }
}

inline void compositeLayerMT(OilCanvas &dst, const OilCanvas &src, float offsetX, float offsetY,
                             float scale = 1.0f, float globalAlpha = 1.0f) {
  int mid = dst.h / 2;
  std::thread t1([&]() { compositeLayer(dst, src, offsetX, offsetY, scale, globalAlpha, 0, mid); });
  compositeLayer(dst, src, offsetX, offsetY, scale, globalAlpha, mid, dst.h);
  t1.join();
}

// Fast opaque blit for full-screen Sky Plate (depth 0)
inline void blitSkyOpaque(OilCanvas &dst, const OilCanvas &sky, float offsetX, float offsetY) {
  for (int y = 0; y < dst.h; ++y) {
    float sy = y - offsetY;
    for (int x = 0; x < dst.w; ++x) {
      float sx = x - offsetX;
      float sr, sg, sb, sa, sh;
      sky.sampleBilinear(sx, sy, sr, sg, sb, sa, sh);
      size_t idx = static_cast<size_t>(y) * dst.w + x;
      dst.r[idx] = sr;
      dst.g[idx] = sg;
      dst.b[idx] = sb;
      dst.a[idx] = 1.0f;
      dst.height[idx] = sh;
    }
  }
}

// Final oil-on-linen lighting pass (impasto raking light + canvas weave + soft vignette)
inline void resolveStrip(const OilCanvas &cv, std::vector<uint8_t> &outRGB,
                         float vignetteAmt, float lightRelief, int y0, int y1) {
  int w = cv.w, h = cv.h;
  for (int y = y0; y < y1; ++y) {
    for (int x = 0; x < w; ++x) {
      size_t idx = static_cast<size_t>(y) * w + x;
      int xm1 = std::max(0, x - 1), xp1 = std::min(w - 1, x + 1);
      int ym1 = std::max(0, y - 1), yp1 = std::min(h - 1, y + 1);

      float hL = cv.height[static_cast<size_t>(y) * w + xm1];
      float hR = cv.height[static_cast<size_t>(y) * w + xp1];
      float hU = cv.height[static_cast<size_t>(ym1) * w + x];
      float hD = cv.height[static_cast<size_t>(yp1) * w + x];
      float dhx = (hR - hL) * 0.5f;
      float dhy = (hD - hU) * 0.5f;

      // Directional raking light from upper-left (-0.707, -0.707)
      float raking = (-dhx * 0.70f - dhy * 0.72f) * lightRelief;

      // Subtle organic Belgian linen grain: gentle flax modulation without uniform grid artifacts
      float flaxJitter = hash2D(x >> 2, y >> 2, 911u) * 0.35f;
      float wx = std::sin(x * 1.18f + flaxJitter);
      float wy2 = std::sin(y * 1.14f - flaxJitter);
      float weave = (wx * 0.52f + wy2 * 0.48f) * 0.0056f;
      float impCover = clampf(1.0f - cv.height[idx] * 0.72f, 0.18f, 1.0f);
      float grain = weave * impCover;

      // Subtle edge vignette
      float vx = (x / static_cast<float>(w) - 0.5f) * 2.0f;
      float vy = (y / static_cast<float>(h) - 0.5f) * 2.0f;
      float vig = 1.0f - vignetteAmt * clampf((vx * vx * 0.52f + vy * vy * 0.62f - 0.38f), 0.0f, 1.0f);

      float rr = (cv.r[idx] + raking * 1.06f + grain) * vig;
      float gg = (cv.g[idx] + raking * 0.98f + grain) * vig;
      float bb = (cv.b[idx] + raking * 0.80f + grain * 0.85f) * vig;

      outRGB[idx * 3 + 0] = static_cast<uint8_t>(clampf(rr, 0.0f, 1.0f) * 255.0f + 0.5f);
      outRGB[idx * 3 + 1] = static_cast<uint8_t>(clampf(gg, 0.0f, 1.0f) * 255.0f + 0.5f);
      outRGB[idx * 3 + 2] = static_cast<uint8_t>(clampf(bb, 0.0f, 1.0f) * 255.0f + 0.5f);
    }
  }
}

inline void resolveCanvasToRGB24(const OilCanvas &cv, std::vector<uint8_t> &outRGB,
                                 float vignetteAmt = 0.10f, float lightRelief = 0.16f) {
  outRGB.resize(static_cast<size_t>(cv.w) * cv.h * 3);
  int mid = cv.h / 2;
  std::thread t1([&]() { resolveStrip(cv, outRGB, vignetteAmt, lightRelief, 0, mid); });
  resolveStrip(cv, outRGB, vignetteAmt, lightRelief, mid, cv.h);
  t1.join();
}

// Solid-underpainted Impressionist foliage canopy (dense base + deep hollows + leaf dabs + sunlit crown)
inline void paintFoliageCanopy(OilCanvas &cv, float cx, float cy, float rx, float ry,
                               RGB deepCol, RGB midCol, RGB lightCol, RGB sunTipCol,
                               int leafCount, uint32_t seed, float minSize = 6.0f, float maxSize = 18.0f) {
  RNG rng(seed);
  // 0. Solid wet-on-wet oil underpainting mass so no bare canvas leaks through dense groves
  int baseCount = std::max(120, leafCount / 6);
  for (int i = 0; i < baseCount; ++i) {
    float ang = rng.range(0.0f, 6.28318f);
    float rad = std::pow(rng.next(), 0.55f) * 0.88f;
    float x = cx + std::cos(ang) * rx * rad;
    float y = cy + std::sin(ang) * ry * rad;
    float n = fbm2D(x * 0.008f, y * 0.008f, 3, seed);
    if (n < 0.22f) continue;
    RGB col = jitterColor(mixRGB(deepCol, midCol, n * 0.45f), rng, 0.04f, 0.06f, 0.03f);
    paintDab(cv, x, y, rng.range(maxSize * 1.4f, maxSize * 2.3f), rng.range(maxSize * 0.8f, maxSize * 1.3f),
             rng.range(-1.2f, 1.2f), col, rng.range(0.75f, 0.92f), 0.18f, seed + i * 11, 8);
  }
  // 1. Deep shadow pockets
  for (int i = 0; i < leafCount * 0.30; ++i) {
    float ang = rng.range(0.0f, 6.28318f);
    float rad = std::sqrt(rng.next()) * 0.96f;
    float x = cx + std::cos(ang) * rx * rad;
    float y = cy + std::sin(ang) * ry * rad + ry * 0.07f;
    float n = fbm2D(x * 0.012f, y * 0.012f, 3, seed + 19);
    if (n < 0.25f) continue;
    RGB col = jitterColor(mixRGB(deepCol, midCol, n * 0.5f), rng, 0.05f, 0.07f, 0.04f);
    paintDab(cv, x, y, rng.range(minSize * 1.1f, maxSize * 1.15f), rng.range(minSize * 0.45f, maxSize * 0.55f),
             rng.range(-1.5f, 1.5f), col, rng.range(0.68f, 0.88f), 0.35f, seed + 2000 + i * 17, 6);
  }
  // 2. Midtone botanical foliage touches
  for (int i = 0; i < leafCount * 0.44; ++i) {
    float ang = rng.range(0.0f, 6.28318f);
    float rad = std::sqrt(rng.next());
    float x = cx + std::cos(ang) * rx * rad;
    float y = cy + std::sin(ang) * ry * rad;
    float upper = clampf(0.55f - (y - cy) / (ry * 2.0f) + (cx - x) / (rx * 4.5f), 0.0f, 1.0f);
    RGB col = jitterColor(mixRGB(midCol, lightCol, upper * 0.85f), rng, 0.07f, 0.09f, 0.05f);
    paintDab(cv, x, y, rng.range(minSize, maxSize), rng.range(minSize * 0.36f, maxSize * 0.46f),
             rng.range(-1.7f, 1.7f), col, rng.range(0.72f, 0.92f), 0.58f, seed + 12000 + i * 23, 6);
  }
  // 3. Crisp sunlit crown flecks
  for (int i = 0; i < leafCount * 0.26; ++i) {
    float ang = rng.range(0.0f, 6.28318f);
    float rad = std::sqrt(rng.next()) * 0.95f;
    float x = cx + std::cos(ang) * rx * rad - rx * 0.05f;
    float y = cy + std::sin(ang) * ry * rad - ry * 0.14f;
    float upper = clampf(0.75f - (y - cy) / (ry * 1.6f), 0.0f, 1.0f);
    if (rng.next() > upper + 0.22f) continue;
    RGB col = jitterColor(mixRGB(lightCol, sunTipCol, upper), rng, 0.08f, 0.10f, 0.06f);
    paintDab(cv, x, y, rng.range(minSize * 0.65f, maxSize * 0.72f), rng.range(minSize * 0.28f, maxSize * 0.36f),
             rng.range(-1.8f, 1.8f), col, rng.range(0.78f, 0.95f), 0.85f, seed + 24000 + i * 31, 5);
  }
}

// Continuous organic tree trunk & forked limbs (smooth lengthwise bark, zero segmented beads or pinch seams)
inline void paintContinuousTrunk(OilCanvas &cv, float x0, float y0, float x1, float y1,
                                 float w0, float w1, RGB shadowBark, RGB litBark, uint32_t seed,
                                 float curveAmp = 0.0f) {
  RNG rng(seed);
  float dx = x1 - x0, dy = y1 - y0;
  float len = std::sqrt(dx * dx + dy * dy);
  if (len < 4.0f) return;
  float nx = -dy / len, ny = dx / len;
  int strips = std::max(5, static_cast<int>(w0 * 0.45f));
  for (int s = 0; s < strips; ++s) {
    float u = (s / static_cast<float>(std::max(1, strips - 1))) - 0.5f; // -0.5..+0.5 across width
    float bend = curveAmp + rng.range(-8.0f, 8.0f);
    // Paint in 4 overlapping long strokes so bark fibers flow continuously without rings
    for (int seg = 0; seg < 4; ++seg) {
      float t0 = std::max(0.0f, seg * 0.25f - 0.05f);
      float t1 = std::min(1.0f, (seg + 1) * 0.25f + 0.05f);
      float curW0 = lerpf(w0, w1, t0);
      float curW1 = lerpf(w0, w1, t1);
      float sx0 = lerpf(x0, x1, t0) + nx * (u * curW0 * 0.72f + std::sin(t0 * 3.14159f) * bend);
      float sy0 = lerpf(y0, y1, t0) + ny * (u * curW0 * 0.72f + std::sin(t0 * 3.14159f) * bend);
      float sx1 = lerpf(x0, x1, t1) + nx * (u * curW1 * 0.72f + std::sin(t1 * 3.14159f) * bend);
      float sy1 = lerpf(y0, y1, t1) + ny * (u * curW1 * 0.72f + std::sin(t1 * 3.14159f) * bend);
      RGB bCol = u > 0.15f ? litBark : mixRGB(shadowBark, litBark, clampf(u + 0.5f, 0.0f, 1.0f));
      paintStroke(cv, {sx0, sy0, sx1, sy1, rng.range(-3, 3), lerpf(curW0, curW1, 0.5f) * 0.48f,
                       0.94f, 0.65f, 0.14f, 5, 0.04f, jitterColor(bCol, rng, 0.04f, 0.05f, 0.03f), {}, false, seed + s * 29 + seg});
    }
  }
}

// Write PPM P6 (fast lossless image output convertible to PNG via ffmpeg/PIL)
inline bool writePPM(const std::string &path, int w, int h, const std::vector<uint8_t> &rgb) {
  std::ofstream out(path, std::ios::binary);
  if (!out) return false;
  out << "P6\n" << w << " " << h << "\n255\n";
  out.write(reinterpret_cast<const char *>(rgb.data()), static_cast<std::streamsize>(rgb.size()));
  return out.good();
}

} // namespace monet

#pragma once
#include "paint_core.hpp"
#include <vector>

namespace monet {

constexpr double FILM_DURATION_SEC = 92.0;
constexpr int FILM_FPS = 30;
constexpr int FILM_TOTAL_FRAMES = 2760;

struct CameraState {
  double t;
  float x; // World X of screen left edge at depth 1.0
  float y; // World Y vertical offset at depth 1.0
};

struct CamKeyframe {
  double t;
  float x;
  float y;
};

inline const std::vector<CamKeyframe> &getCameraKeyframes() {
  static const std::vector<CamKeyframe> kfs = {
    {0.0,   0.0f,     0.0f},     // Scene 1: Dawn mist on the Seine
    {8.5,   1180.0f,  -4.0f},    // Scene 1 Hero: Dawn sun, boatman & egrets
    {16.5,  2380.0f,  0.0f},     // Portal 1 Entry: Approaching weeping willows
    {19.5,  2860.0f,  -4.0f},    // Portal 1 Mid: Dense willow curtain
    {23.0,  3460.0f,  -8.0f},    // Scene 2 Enter: Giverny lily pond opens
    {29.5,  4380.0f,  -12.0f},   // Scene 2 Hero: Japanese Bridge, wisteria, koi & lilies
    {37.0,  5580.0f,  -16.0f},   // Portal 2 Entry: Climbing rose trellis
    {39.5,  6040.0f,  -58.0f},   // Portal 2 Mid: Ascending stone garden slope behind roses
    {42.5,  6600.0f,  -104.0f},  // Scene 3 Enter: Normandy poppy hill opens
    {49.0,  7680.0f,  -106.0f},  // Scene 3 Hero: Woman with a Parasol, child & poppies
    {56.5,  8880.0f,  -92.0f},   // Portal 3 Entry: Sun-dappled orchard canopy
    {59.0,  9340.0f,  -64.0f},   // Portal 3 Mid: Orchard foliage transition
    {62.0,  9880.0f,  -42.0f},   // Scene 4 Enter: Sunset harvest field opens
    {68.5,  10820.0f, -40.0f},   // Scene 4 Hero: Monumental haystacks, violet shadows & sheep
    {75.5,  11980.0f, -24.0f},   // Portal 4 Entry: Evening marsh reeds
    {78.0,  12440.0f, -4.0f},    // Portal 4 Mid: Descending bank behind reeds
    {81.0,  12980.0f, 4.0f},     // Scene 5 Enter: Twilight lagoon & stone boathouse
    {86.5,  13780.0f, 2.0f},     // Scene 5 Hero: Two white swans, amber lanterns & crescent moon
    {92.0,  14120.0f, -58.0f},   // Scene 5 Finale: Gentle skyward drift into stars & fireflies
  };
  return kfs;
}

inline float catmullRom(float p0, float p1, float p2, float p3, float t) {
  float t2 = t * t;
  float t3 = t2 * t;
  return 0.5f * ((2.0f * p1) +
                 (-p0 + p2) * t +
                 (2.0f * p0 - 5.0f * p1 + 4.0f * p2 - p3) * t2 +
                 (-p0 + 3.0f * p1 - 3.0f * p2 + p3) * t3);
}

inline CameraState getCamera(double timeSec) {
  double t = clampf(static_cast<float>(timeSec), 0.0f, static_cast<float>(FILM_DURATION_SEC));
  const auto &kf = getCameraKeyframes();
  size_t idx = 0;
  while (idx + 2 < kf.size() && t > kf[idx + 1].t) idx++;

  double t0 = kf[idx].t;
  double t1 = kf[idx + 1].t;
  float u = static_cast<float>(clampf(static_cast<float>((t - t0) / std::max(0.001, t1 - t0)), 0.0f, 1.0f));

  const auto &p0 = kf[idx > 0 ? idx - 1 : 0];
  const auto &p1 = kf[idx];
  const auto &p2 = kf[idx + 1];
  const auto &p3 = kf[idx + 2 < kf.size() ? idx + 2 : kf.size() - 1];

  float breathY = std::sin(static_cast<float>(t) * 0.42f) * 2.5f;
  return {
    t,
    catmullRom(p0.x, p1.x, p2.x, p3.x, u),
    catmullRom(p0.y, p1.y, p2.y, p3.y, u) + breathY
  };
}

} // namespace monet

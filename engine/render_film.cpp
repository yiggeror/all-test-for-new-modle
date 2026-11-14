#include "paint_core.hpp"
#include "camera.hpp"
#include "world_layers.hpp"
#include "animator.hpp"
#include <chrono>
#include <cstdio>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace monet;

static void saveCropPPM(const std::string &path, const std::vector<uint8_t> &rgb,
                        int W, int H, int cx0, int cy0, int cw, int ch) {
  cx0 = std::clamp(cx0, 0, W - cw);
  cy0 = std::clamp(cy0, 0, H - ch);
  std::vector<uint8_t> crop(static_cast<size_t>(cw) * ch * 3);
  for (int y = 0; y < ch; ++y) {
    for (int x = 0; x < cw; ++x) {
      size_t si = (static_cast<size_t>(cy0 + y) * W + (cx0 + x)) * 3;
      size_t di = (static_cast<size_t>(y) * cw + x) * 3;
      crop[di] = rgb[si]; crop[di + 1] = rgb[si + 1]; crop[di + 2] = rgb[si + 2];
    }
  }
  writePPM(path, cw, ch, crop);
}

int main(int argc, char **argv) {
  bool auditMode = false;
  bool videoMode = false;
  int startFrame = 0;
  int endFrame = FILM_TOTAL_FRAMES;
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--audit") auditMode = true;
    else if (arg == "--video") videoMode = true;
    else if (arg == "--start" && i + 1 < argc) startFrame = std::clamp(std::stoi(argv[++i]), 0, FILM_TOTAL_FRAMES);
    else if (arg == "--end" && i + 1 < argc) endFrame = std::clamp(std::stoi(argv[++i]), 0, FILM_TOTAL_FRAMES);
  }
  if (!auditMode && !videoMode) {
    std::cerr << "Usage: render_film [--audit | --video [--start N] [--end M]]\n";
    return 1;
  }

  auto tStart = std::chrono::steady_clock::now();
  WorldSceneData world;
  buildAllWorldLayers(world);
  auto tBuilt = std::chrono::steady_clock::now();
  std::cerr << "World layers built in "
            << std::chrono::duration<double>(tBuilt - tStart).count() << "s\n";

  OilCanvas frameCanvas;
  std::vector<uint8_t> outRGB;

  if (auditMode) {
    struct AuditShot { double t; std::string name; bool crop; int cx, cy; };
    const std::vector<AuditShot> shots = {
      {1.5,  "00_scene1_open_1.5s",       false, 0, 0},
      {8.5,  "01_scene1_dawn_8.5s",       true,  320, 460},
      {17.5, "02_portal1_entry_17.5s",    false, 0, 0},
      {19.5, "03_portal1_willow_19.5s",   false, 0, 0},
      {22.0, "03b_portal1_exit_22.0s",    false, 0, 0},
      {29.5, "04_scene2_giverny_29.5s",   true,  710, 260},
      {37.5, "05_portal2_entry_37.5s",    false, 0, 0},
      {39.5, "06_portal2_roses_39.5s",    false, 0, 0},
      {42.0, "06b_portal2_exit_42.0s",    false, 0, 0},
      {49.0, "07_scene3_parasol_49.0s",   true,  680, 140},
      {57.0, "08_portal3_entry_57.0s",    false, 0, 0},
      {59.0, "09_portal3_orchard_59.0s",  false, 0, 0},
      {61.5, "09b_portal3_exit_61.5s",  false, 0, 0},
      {68.5, "10_scene4_haystacks_68.5s", true,  780, 320},
      {76.0, "11_portal4_entry_76.0s",    false, 0, 0},
      {78.0, "12_portal4_reeds_78.0s",    false, 0, 0},
      {80.5, "12b_portal4_exit_80.5s",    false, 0, 0},
      {86.5, "13_scene5_twilight_86.5s",  true,  680, 420},
      {91.5, "14_scene5_finale_91.5s",    false, 0, 0}
    };

    for (const auto &s : shots) {
      auto f0 = std::chrono::steady_clock::now();
      renderWorldFrame(world, s.t, frameCanvas, outRGB);
      auto f1 = std::chrono::steady_clock::now();
      writePPM("output/audit/" + s.name + ".ppm", 1920, 1080, outRGB);
      if (s.crop) {
        saveCropPPM("output/audit/" + s.name + "_crop.ppm", outRGB, 1920, 1080, s.cx, s.cy, 520, 520);
      }
      std::cerr << "Rendered " << s.name << " ("
                << std::chrono::duration<double>(f1 - f0).count() << "s)\n";
    }
    return 0;
  }

  if (videoMode) {
    // Stream raw RGB24 frames cleanly to stdout
    std::ios_base::sync_with_stdio(false);
    int totalToRender = std::max(0, endFrame - startFrame);
    auto v0 = std::chrono::steady_clock::now();
    for (int f = startFrame; f < endFrame; ++f) {
      double t = static_cast<double>(f) / FILM_FPS;
      renderWorldFrame(world, t, frameCanvas, outRGB);
      std::fwrite(outRGB.data(), 1, outRGB.size(), stdout);
      int done = (f - startFrame) + 1;
      if (done % 60 == 0 || f + 1 == endFrame) {
        std::fflush(stdout);
        double elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - v0).count();
        double fps = done / std::max(0.01, elapsed);
        double eta = (totalToRender - done) / std::max(0.01, fps);
        std::cerr << "[Frame " << (f + 1) << "/" << FILM_TOTAL_FRAMES
                  << " | seg " << done << "/" << totalToRender << "] "
                  << std::fixed << std::setprecision(1) << (100.0 * done / std::max(1, totalToRender))
                  << "% | " << std::setprecision(2) << fps << " fps | elapsed "
                  << static_cast<int>(elapsed) << "s | ETA " << static_cast<int>(eta) << "s\n";
      }
    }
  }
  return 0;
}

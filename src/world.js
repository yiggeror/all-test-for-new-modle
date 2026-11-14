// Unified Continuous Monet World Orchestrator (5 Blended Sky Plates + 5 Scenes + 4 Portals + CanvasFX)
import { mulberry32, clamp, smoothstep, fbm2D } from "./core/noise.js";
import { getAtmosphere, mixRgb, jitterMonetColor } from "./core/palette.js";
import { BrushEngine } from "./core/brushes.js";
import { CanvasFX } from "./core/canvas_fx.js";
import { getCamera } from "./core/camera.js";
import { Scene1Dawn } from "./scenes/scene1_dawn.js";
import { Scene2Giverny } from "./scenes/scene2_giverny.js";
import { Scene3Poppies } from "./scenes/scene3_poppies.js";
import { Scene4Haystacks } from "./scenes/scene4_haystacks.js";
import { Scene5Twilight } from "./scenes/scene5_twilight.js";

const SKY_ANCHORS = [900, 3800, 6600, 9300, 11700];

export class MonetWorld {
  constructor(width = 1920, height = 1080) {
    this.width = width;
    this.height = height;
    this.brushes = new BrushEngine();
    this.fx = new CanvasFX(width, height);

    this.skyPlates = SKY_ANCHORS.map((wx, idx) => this._buildSkyPlate(wx, 700 + idx * 31));
    this.scene1 = new Scene1Dawn(this.brushes);
    this.scene2 = new Scene2Giverny(this.brushes);
    this.scene3 = new Scene3Poppies(this.brushes);
    this.scene4 = new Scene4Haystacks(this.brushes);
    this.scene5 = new Scene5Twilight(this.brushes);
  }

  _buildSkyPlate(anchorWorldX, seed) {
    const w = 2400;
    const h = 1100;
    const c = document.createElement("canvas");
    c.width = w;
    c.height = h;
    const ctx = c.getContext("2d");
    const rng = mulberry32(seed);
    const atmo = getAtmosphere(anchorWorldX);

    // Smooth vertical atmospheric underpainting wash
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, `rgb(${atmo.skyTop.map(Math.round).join(",")})`);
    grad.addColorStop(0.54, `rgb(${atmo.skyMid.map(Math.round).join(",")})`);
    grad.addColorStop(0.88, `rgb(${atmo.skyHorizon.map(Math.round).join(",")})`);
    grad.addColorStop(1, `rgb(${atmo.skyHorizon.map(Math.round).join(",")})`);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    // Criss-crossed Impressionist air brushstrokes across the sky plate
    const stepX = 42;
    const stepY = 28;
    for (let y = 12; y < h - 12; y += stepY) {
      const v = clamp(y / (h * 0.88), 0, 1);
      const base = v < 0.56
        ? mixRgb(atmo.skyTop, atmo.skyMid, v / 0.56)
        : mixRgb(atmo.skyMid, atmo.skyHorizon, (v - 0.56) / 0.44);
      for (let x = 12; x < w - 12; x += stepX) {
        const n = fbm2D(x * 0.004, y * 0.006, 3, seed + 17);
        const col = jitterMonetColor(base, rng, 10, 9, 7);
        const angle = n * 0.44 + (rng() - 0.5) * 0.30;
        this.brushes.stamp(
          ctx,
          "broad",
          (x + y) % 3,
          x + (rng() - 0.5) * 22,
          y + (rng() - 0.5) * 16,
          72 + rng() * 46,
          28 + rng() * 14,
          angle,
          col,
          0.46 + rng() * 0.22,
          0.22
        );
      }
    }
    this.brushes.resetCtx(ctx);
    return c;
  }

  _drawBlendedSky(ctx, cam) {
    const w = this.width;
    const h = this.height;
    const scale = (w / 1920) * cam.zoom;
    const plateW = 2400 * scale;
    const plateH = 1100 * scale;
    // Gentle sky parallax scroll wrapped smoothly across 2400px plate
    const shiftX = -((cam.x * 0.04) % (480 * scale));
    const shiftY = (-120 - cam.y * 0.08) * scale;

    // Determine active pair of sky plates for smooth time-of-day transition
    let idx = 0;
    while (idx < SKY_ANCHORS.length - 2 && cam.x > SKY_ANCHORS[idx + 1]) idx++;

    const a = SKY_ANCHORS[idx];
    const b = SKY_ANCHORS[Math.min(SKY_ANCHORS.length - 1, idx + 1)];
    const blend = cam.x <= a ? 0 : cam.x >= b ? 1 : smoothstep(a, b, cam.x);

    this.brushes.resetCtx(ctx);
    ctx.drawImage(this.skyPlates[idx], shiftX, shiftY, plateW, plateH);
    if (blend > 0.005 && idx + 1 < this.skyPlates.length) {
      ctx.globalAlpha = blend;
      ctx.drawImage(this.skyPlates[idx + 1], shiftX, shiftY, plateW, plateH);
      ctx.globalAlpha = 1;
    }
  }

  renderFrame(ctx, timeSec) {
    const cam = getCamera(timeSec);
    const atmo = getAtmosphere(cam.x);
    const w = this.width;
    const h = this.height;

    this.brushes.resetCtx(ctx);
    ctx.clearRect(0, 0, w, h);

    // 1. Seamless Time-of-Day Blended Impressionist Sky
    this._drawBlendedSky(ctx, cam);

    // 2. Render active scenes in world depth / progression order
    this.scene1.render(ctx, cam, timeSec, w, h, atmo);
    this.brushes.resetCtx(ctx);
    this.scene2.render(ctx, cam, timeSec, w, h, atmo);
    this.brushes.resetCtx(ctx);
    this.scene3.render(ctx, cam, timeSec, w, h, atmo);
    this.brushes.resetCtx(ctx);
    this.scene4.render(ctx, cam, timeSec, w, h, atmo);
    this.brushes.resetCtx(ctx);
    this.scene5.render(ctx, cam, timeSec, w, h, atmo);
    this.brushes.resetCtx(ctx);

    // 3. Final Optical Bloom, French Linen Canvas Weave & Vignette
    this.fx.apply(ctx, cam.x, cam.y, atmo, timeSec);
  }
}

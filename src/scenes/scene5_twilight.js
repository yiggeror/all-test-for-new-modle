// Scene 5 (73s - 92s): Twilight Lagoon, Stone Pavilion Lanterns, Gliding Swans, Crescent Moon & Fireflies
import { mulberry32, clamp, lerp, smoothstep } from "../core/noise.js";
import { mixRgb, jitterMonetColor } from "../core/palette.js";
import { worldToScreen, worldAnchor } from "../core/camera.js";
import {
  createPainterlyCloudSprite,
  createHillTreelineSprite,
  createLilyPadSprite,
  paintAnimatedWater,
  paintWaterRipple,
} from "../core/painter.js";

export class Scene5Twilight {
  constructor(brushes) {
    this.brushes = brushes;
    this._initSprites();
    this._initData();
  }

  _initSprites() {
    const b = this.brushes;
    // Soft twilight lavender-rose dusk clouds
    this.clouds = [
      createPainterlyCloudSprite(b, 520, 170, [176, 128, 166], [56, 62, 114], 501),
      createPainterlyCloudSprite(b, 440, 150, [188, 134, 162], [48, 56, 108], 502),
    ];

    // Deep indigo-teal distant treeline along lagoon shore
    this.farShore = createHillTreelineSprite(
      b, 2600, 300,
      [34, 48, 86],
      [78, 76, 126],
      [24, 32, 70],
      511,
      { treeDensity: 1.0, poplars: true, hazeAlpha: 0.25 }
    );

    // Romantic Stone Boathouse / Arched Pavilion with glowing warm amber lanterns
    this.pavilion = this._buildStonePavilionSprite();

    // Luminous painterly Crescent Moon sprite (transparent cutout via destination-out!)
    this.moonSprite = this._buildMoonSprite(140);

    // Dark twilight lily pads
    this.twilightPads = [
      createLilyPadSprite(b, 140, 521, true),
      createLilyPadSprite(b, 120, 522, true),
    ];
  }

  _buildMoonSprite(size) {
    const c = document.createElement("canvas");
    c.width = size; c.height = size;
    const ctx = c.getContext("2d");
    const cx = size * 0.5;
    const cy = size * 0.5;
    const r = size * 0.34;

    ctx.fillStyle = "rgba(255, 248, 218, 0.96)";
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fill();

    // Transparent crescent cutout
    ctx.globalCompositeOperation = "destination-out";
    ctx.fillStyle = "rgba(0, 0, 0, 1)";
    ctx.beginPath();
    ctx.arc(cx + r * 0.44, cy - r * 0.16, r * 0.88, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalCompositeOperation = "source-over";
    return c;
  }

  _buildStonePavilionSprite() {
    const w = 480, h = 300;
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    const ctx = c.getContext("2d");
    const b = this.brushes;
    const rng = mulberry32(540);

    // Deep dark boat arches backdrop first
    ctx.fillStyle = "rgb(16, 20, 48)";
    for (const ax of [265, 332]) {
      ctx.beginPath();
      ctx.ellipse(ax, 256, 24, 52, 0, Math.PI, 0);
      ctx.lineTo(ax + 24, 260);
      ctx.lineTo(ax - 24, 260);
      ctx.closePath();
      ctx.fill();
    }

    // Stone boathouse mass & arched portico (crisp twilight slate-indigo with warm rose rim)
    for (let y = 114; y < 254; y += 14) {
      for (let x = 86; x < 392; x += 18) {
        const inArch1 = Math.hypot((x - 265) / 23, (y - 256) / 50) < 1;
        const inArch2 = Math.hypot((x - 332) / 23, (y - 256) / 50) < 1;
        if (inArch1 || inArch2) continue;
        const base = x < 220 ? [38, 42, 86] : [52, 54, 102];
        const col = jitterMonetColor(base, rng, 7, 7, 6);
        b.stamp(ctx, "short", (x + y) % 4, x + (rng() - 0.5) * 6, y + (rng() - 0.5) * 5, 28, 17, (rng() - 0.5) * 0.14, col, 0.94, 0.35);
      }
    }

    // Pitched slate-indigo roof & eaves
    for (let i = 0; i < 48; i++) {
      const u = i / 47;
      const rx = lerp(70, 408, u);
      const ry = lerp(116, 78, Math.sin(u * Math.PI)) + (rng() - 0.5) * 8;
      const col = jitterMonetColor([30, 34, 76], rng, 7, 7, 6);
      b.stamp(ctx, "broad", i % 3, rx, ry, 34, 15, (u - 0.5) * 0.25, col, 0.95, 0.35);
    }
    // Delicate rose-lavender dusk rim along roof ridge
    b.stamp(ctx, "knife", 0, 238, 72, 210, 5.5, 0, [202, 136, 166], 0.72, 0.3);

    // 3 Glowing Warm Amber Lantern Windows (reset transform after roof ridge knife stamp!)
    b.resetCtx(ctx);
    const lanterns = [
      { x: 136, y: 164 },
      { x: 186, y: 164 },
      { x: 298, y: 152 },
    ];
    for (const ln of lanterns) {
      b.resetCtx(ctx);
      const g = ctx.createRadialGradient(ln.x, ln.y, 2, ln.x, ln.y, 44);
      g.addColorStop(0, "rgba(255, 224, 132, 0.92)");
      g.addColorStop(0.5, "rgba(255, 168, 78, 0.36)");
      g.addColorStop(1, "rgba(255, 168, 78, 0)");
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(ln.x, ln.y, 44, 0, Math.PI * 2);
      ctx.fill();
      b.stamp(ctx, "short", 0, ln.x, ln.y, 17, 24, Math.PI * 0.5, [255, 214, 114], 0.98, 0.5);
      b.stamp(ctx, "short", 1, ln.x, ln.y - 2, 11, 14, Math.PI * 0.5, [255, 248, 204], 0.98, 0.5);
    }

    b.resetCtx(ctx);
    return c;
  }

  _initData() {
    const rng = mulberry32(570);

    // Delicate twilight stars emerging across the entire upper indigo sky
    this.stars = [];
    for (let i = 0; i < 85; i++) {
      this.stars.push({
        targetX: 4800 + rng() * 14400,
        wy: -560 + rng() * 340,
        size: 3.5 + rng() * 4.5,
        phase: rng() * Math.PI * 2,
        speed: 1.4 + rng() * 2.0,
      });
    }

    // Foreground twilight water lily pads framing the lagoon corners
    this.pads = [];
    for (let i = 0; i < 24; i++) {
      const targetX = 11000 + rng() * 1450;
      const depth = 0.96 + rng() * 0.22;
      const wy = 240 + rng() * 220;
      this.pads.push({
        ...worldAnchor(targetX, 6, depth, 0, wy),
        depth,
        scale: lerp(0.65, 1.25, (wy - 240) / 220),
        idx: i % this.twilightPads.length,
        phase: rng() * Math.PI * 2,
      });
    }

    // Drifting golden-lime Fireflies rising gently into the twilight sky
    this.fireflies = [];
    for (let i = 0; i < 52; i++) {
      this.fireflies.push({
        baseTargetX: 10950 + rng() * 1650,
        baseWy: -280 + rng() * 540,
        depth: 0.88 + rng() * 0.42,
        phase: rng() * Math.PI * 2,
        speed: 0.6 + rng() * 0.9,
        riseSpeed: 6 + rng() * 10,
        warmth: rng(),
      });
    }
  }

  _drawSwan(ctx, b, sx, sy, sc, time, phase, flip = 1) {
    const s = sc * 1.38;
    const bob = Math.sin(time * 1.4 + phase) * 2.2 * s;
    const y = sy + bob;

    // Soft silver-lavender reflection beneath swan
    b.stamp(ctx, "broad", 0, sx, sy + 18 * s, 72 * s, 16 * s, 0, [118, 128, 178], 0.36, 0.15);

    // Body: cool moonlit periwinkle shadow base + luminous pearl-ivory back
    b.stamp(ctx, "curved", 0, sx, y - 8 * s, 64 * s, 26 * s, 0, [168, 184, 224], 0.95, 0.35);
    b.stamp(ctx, "curved", 1, sx - 4 * s * flip, y - 16 * s, 52 * s, 22 * s, -0.15 * flip, [242, 244, 252], 0.96, 0.45);
    b.stamp(ctx, "curved", 2, sx - 12 * s * flip, y - 24 * s, 38 * s, 18 * s, -0.35 * flip, [252, 248, 236], 0.92, 0.45);

    // Graceful S-curved neck & head
    const nx = sx + 26 * s * flip;
    const ny = y - 26 * s;
    b.stamp(ctx, "curved", 0, nx - 2 * s * flip, ny, 12 * s, 34 * s, 0.18 * flip, [238, 242, 250], 0.96, 0.4);
    b.stamp(ctx, "short", 0, nx + 6 * s * flip, ny - 18 * s, 15 * s, 11 * s, 0.1 * flip, [248, 248, 252], 0.96, 0.4);
    b.stamp(ctx, "knife", 0, nx + 14 * s * flip, ny - 16 * s, 11 * s, 4.5 * s, 0.15 * flip, [238, 154, 92], 0.95, 0.4);
  }

  render(ctx, cam, time, viewW, viewH, atmosphere) {
    if (cam.x < 9800) return;

    const b = this.brushes;
    b.resetCtx(ctx);
    const horizonY = worldToScreen(0, 62, 0.25, cam, viewW, viewH).y;
    const sceneAlpha = smoothstep(10150, 10900, cam.x);

    // 1. Shimmering Twilight Stars
    const starVis = atmosphere.starAlpha * smoothstep(10100, 11200, cam.x);
    if (starVis > 0.02) {
      for (let i = 0; i < this.stars.length; i++) {
        const st = this.stars[i];
        const anc = worldAnchor(st.targetX, -20, 0.12, 0, st.wy);
        const p = worldToScreen(anc.wx, anc.wy, 0.12, cam, viewW, viewH);
        if (p.x < -20 || p.x > viewW + 20 || p.y > horizonY - 40) continue;
        const twinkle = 0.45 + 0.55 * Math.sin(time * st.speed + st.phase);
        b.stamp(ctx, "scumble", 0, p.x, p.y, st.size * p.scale, st.size * p.scale, 0, [255, 246, 214], starVis * twinkle * 0.85, 0.1);
      }
    }

    // 2. Luminous Crescent Moon & Golden-Pearl Halo (reset transform after stars, elevated cleanly above farShore!)
    b.resetCtx(ctx);
    const moonAnc = worldAnchor(12040, -25, 0.14, 0, -395);
    const moonPos = worldToScreen(moonAnc.wx, moonAnc.wy, 0.14, cam, viewW, viewH);
    const moonVis = smoothstep(10400, 11400, cam.x);
    if (moonVis > 0.01) {
      ctx.save();
      ctx.globalAlpha = moonVis;
      const mg = ctx.createRadialGradient(moonPos.x, moonPos.y, 10, moonPos.x, moonPos.y, 240 * moonPos.scale);
      mg.addColorStop(0, "rgba(255, 246, 208, 0.78)");
      mg.addColorStop(0.35, "rgba(218, 220, 250, 0.26)");
      mg.addColorStop(1, "rgba(180, 190, 236, 0)");
      ctx.fillStyle = mg;
      ctx.beginPath();
      ctx.arc(moonPos.x, moonPos.y, 240 * moonPos.scale, 0, Math.PI * 2);
      ctx.fill();

      const mw = this.moonSprite.width * moonPos.scale;
      const mh = this.moonSprite.height * moonPos.scale;
      ctx.drawImage(this.moonSprite, moonPos.x - mw * 0.5, moonPos.y - mh * 0.5, mw, mh);
      ctx.restore();
    }

    // 3. Twilight Clouds framing the flanks of the Crescent Moon
    b.resetCtx(ctx);
    const c1Anc = worldAnchor(11180, -10, 0.18);
    const c1 = worldToScreen(c1Anc.wx + time * 4, -325, 0.18, cam, viewW, viewH);
    const c2Anc = worldAnchor(12340, -10, 0.20);
    const c2 = worldToScreen(c2Anc.wx + time * 5, -275, 0.20, cam, viewW, viewH);
    ctx.save();
    ctx.globalAlpha = 0.72 * moonVis;
    ctx.drawImage(this.clouds[0], c1.x - 260 * c1.scale, c1.y - 85 * c1.scale, 520 * c1.scale, 170 * c1.scale);
    ctx.drawImage(this.clouds[1], c2.x - 220 * c2.scale, c2.y - 75 * c2.scale, 440 * c2.scale, 150 * c2.scale);
    ctx.restore();

    // 4. Far Twilight Lagoon Treeline (depth 0.42, faded cleanly behind Portal 4)
    b.resetCtx(ctx);
    const pavAnc = worldAnchor(11620, 6, 0.56, 0, -170);
    const pavPos = worldToScreen(pavAnc.wx, pavAnc.wy, 0.56, cam, viewW, viewH);
    if (sceneAlpha > 0.01) {
      ctx.save();
      ctx.globalAlpha = sceneAlpha;
      const shoreAnc = worldAnchor(11650, 6, 0.42);
      const shorePos = worldToScreen(shoreAnc.wx - 1300, shoreAnc.wy - 175, 0.42, cam, viewW, viewH);
      ctx.drawImage(this.farShore, shorePos.x, shorePos.y, this.farShore.width * shorePos.scale, this.farShore.height * shorePos.scale);

      // 5. Stone Boathouse / Arched Pavilion with Glowing Amber Lanterns (depth 0.56)
      const pw = this.pavilion.width * pavPos.scale;
      const ph = this.pavilion.height * pavPos.scale;
      ctx.drawImage(this.pavilion, pavPos.x - pw * 0.5, pavPos.y, pw, ph);
      ctx.restore();
    }

    // 6. Tranquil Twilight Lagoon Water & Broken Lantern/Moon Reflections (feathered left!)
    const waterLeft = Math.max(-40, worldToScreen(worldAnchor(10350, 6, 1.0).wx, 0, 1.0, cam, viewW, viewH).x);
    const waterTop = Math.round(horizonY + 18 * cam.zoom);
    if (waterLeft < viewW + 40 && sceneAlpha > 0.02) {
      paintAnimatedWater(ctx, b, { x: waterLeft, y: waterTop, w: viewW - waterLeft + 60, h: viewH - waterTop + 40 }, time, {
        baseColor: [36, 62, 102],
        deepColor: [18, 34, 68],
        highlightColor: [176, 132, 168],
        sunColX: pavPos.x - 28 * pavPos.scale,
        sunColor: [255, 192, 92],
        reflectionBands: [
          { x: pavPos.x + 32 * pavPos.scale, yTop: waterTop + 12, width: 34 * pavPos.scale, height: 220, color: [255, 196, 98], waveAmp: 10, alpha: 0.75 },
          { x: moonPos.x, yTop: waterTop + 10, width: 36, height: 260, color: [236, 232, 206], waveAmp: 12, alpha: 0.45 },
          { x: pavPos.x, yTop: waterTop + 5, width: 230 * pavPos.scale, height: 110, color: [48, 52, 98], waveAmp: 7, alpha: 0.55 },
        ],
        seed: 588,
        fadeLeft: waterLeft > -20 ? 280 : 0,
      });
    }

    // 7. Pair of Graceful White Swans Gliding Serenely Across the Lagoon (depth 0.88)
    const swanDrift = clamp((time - 76) * 26, -120, 420);
    const swan1Anc = worldAnchor(11480 + swanDrift, 6, 0.88, 0, 185);
    const s1 = worldToScreen(swan1Anc.wx, swan1Anc.wy, 0.88, cam, viewW, viewH);
    const swan2Anc = worldAnchor(11395 + swanDrift, 6, 0.90, 0, 212);
    const s2 = worldToScreen(swan2Anc.wx, swan2Anc.wy, 0.90, cam, viewW, viewH);

    for (let w = 0; w < 3; w++) {
      const age = ((time * 0.45 + w * 0.33) % 1);
      if (s1.x > -100 && s1.x < viewW + 100) {
        paintWaterRipple(ctx, b, s1.x - age * 75 * s1.scale, s1.y + 8 * s1.scale, (28 + age * 82) * s1.scale, (7 + age * 18) * s1.scale, [218, 212, 232], (1 - age) * 0.45, 590 + w);
      }
      if (s2.x > -100 && s2.x < viewW + 100) {
        paintWaterRipple(ctx, b, s2.x - age * 70 * s2.scale, s2.y + 8 * s2.scale, (24 + age * 74) * s2.scale, (6 + age * 16) * s2.scale, [218, 212, 232], (1 - age) * 0.4, 595 + w);
      }
    }

    if (s1.x > -120 && s1.x < viewW + 120) this._drawSwan(ctx, b, s1.x, s1.y, s1.scale * 1.1, time, 0.2, 1);
    if (s2.x > -120 && s2.x < viewW + 120) this._drawSwan(ctx, b, s2.x, s2.y, s2.scale * 0.98, time, 1.9, 1);

    // 8. Dark Twilight Water Lily Pads
    b.resetCtx(ctx);
    for (let i = 0; i < this.pads.length; i++) {
      const pd = this.pads[i];
      const p = worldToScreen(pd.wx, pd.wy, pd.depth, cam, viewW, viewH);
      if (p.x < -140 || p.x > viewW + 140) continue;
      const bob = Math.sin(time * 1.1 + pd.phase) * 2.5 * p.scale;
      const spr = this.twilightPads[pd.idx];
      const sw = spr.width * p.scale * pd.scale;
      const sh = spr.height * p.scale * pd.scale;
      ctx.drawImage(spr, p.x - sw * 0.5, p.y - sh * 0.5 + bob, sw, sh);
    }

    // 9. Luminous Golden-Lime Fireflies rising gently into the Starlit Sky
    for (let i = 0; i < this.fireflies.length; i++) {
      const ff = this.fireflies[i];
      const anc = worldAnchor(ff.baseTargetX, 0, ff.depth, 0, ff.baseWy);
      const driftX = Math.sin(time * ff.speed + ff.phase) * 38;
      const driftY = -((time - 74) * ff.riseSpeed) + Math.cos(time * ff.speed * 1.3 + ff.phase) * 20;
      const p = worldToScreen(anc.wx + driftX, anc.wy + driftY, ff.depth, cam, viewW, viewH);
      if (p.x < -50 || p.x > viewW + 50 || p.y < -50 || p.y > viewH + 50) continue;

      const pulse = 0.35 + 0.65 * Math.pow(0.5 + 0.5 * Math.sin(time * 2.6 + ff.phase), 1.6);
      const colHalo = ff.warmth > 0.5 ? [255, 224, 118] : [214, 246, 134];
      const sc = p.scale;
      b.stamp(ctx, "scumble", 0, p.x, p.y, 26 * sc, 26 * sc, 0, colHalo, pulse * 0.36, 0.05);
      b.stamp(ctx, "short", 0, p.x, p.y, 8 * sc, 8 * sc, 0, [255, 250, 212], pulse * 0.92, 0.2);
    }

    b.resetCtx(ctx);
  }
}

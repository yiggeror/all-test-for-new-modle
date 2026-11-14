// Scene 4 (55s - 76s): Haystacks at Golden Hour, Violet Shadows, Sheep & Dog, Swallows & Reed Portal
import { mulberry32, clamp, lerp, smoothstep, fbm2D } from "../core/noise.js";
import { mixRgb, jitterMonetColor } from "../core/palette.js";
import { worldToScreen, worldAnchor } from "../core/camera.js";
import { createPainterlyCloudSprite, createHillTreelineSprite } from "../core/painter.js";

export class Scene4Haystacks {
  constructor(brushes) {
    this.brushes = brushes;
    this._initSprites();
    this._initData();
  }

  _initSprites() {
    const b = this.brushes;
    // Warm apricot-gold & violet-plum evening clouds
    this.clouds = [
      createPainterlyCloudSprite(b, 580, 200, [255, 212, 146], [148, 118, 168], 401),
      createPainterlyCloudSprite(b, 480, 175, [255, 198, 138], [136, 108, 162], 402),
    ];

    // Distant twilight-violet hill line with warm sunset rim
    this.farHills = createHillTreelineSprite(
      b, 2600, 320,
      [104, 86, 134],
      [216, 148, 114],
      [88, 68, 128],
      411,
      { treeDensity: 0.85, poplars: true, hazeAlpha: 0.34 }
    );

    // Pre-painted Golden Harvest Field base
    this.fieldBase = this._buildFieldBaseSprite();

    // Two monumental Monet Haystacks (Meules) with rich straw impasto & violet shadow!
    this.haystackBig = this._buildHaystackSprite(440, 360, 421);
    this.haystackSmall = this._buildHaystackSprite(350, 290, 422);
  }

  _buildFieldBaseSprite() {
    const w = 2900, h = 720;
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    const ctx = c.getContext("2d");
    const b = this.brushes;
    const rng = mulberry32(430);

    const topEdge = (x) => 125 + Math.sin(x * 0.002) * 32;

    // 1. Continuous feathered underpainting wash (zero grid/brick pattern, zero rectangular cutoffs!)
    const stripW = 24;
    for (let x = 0; x < w; x += stripW) {
      const edgeFade = smoothstep(0, 340, x) * smoothstep(w, w - 340, x);
      if (edgeFade < 0.01) continue;
      const topY = topEdge(x);
      ctx.save();
      ctx.globalAlpha = edgeFade;
      const g = ctx.createLinearGradient(0, topY - 10, 0, h);
      g.addColorStop(0, "rgba(176, 118, 86, 0)");
      g.addColorStop(0.08, "rgba(182, 122, 78, 0.96)");
      g.addColorStop(0.55, "rgba(212, 156, 82, 0.98)");
      g.addColorStop(1, "rgba(148, 102, 124, 1)");
      ctx.fillStyle = g;
      ctx.fillRect(x, topY - 10, stripW + 1, h - topY + 10);
      ctx.restore();
    }

    // 2. Non-grid, heavily jittered Impressionist harvest stubble strokes
    const count = 4200;
    for (let i = 0; i < count; i++) {
      const x = 40 + rng() * (w - 80);
      const y = 95 + rng() * (h - 105);
      const edgeFade = smoothstep(0, 340, x) * smoothstep(w, w - 340, x);
      if (edgeFade < 0.02) continue;
      const topY = topEdge(x);
      const topFade = smoothstep(topY - 6, topY + 28, y);
      if (topFade < 0.02) continue;

      const v = clamp((y - 95) / (h - 95), 0, 1);
      const n = fbm2D(x * 0.003, y * 0.004, 3, 431);
      const warmGold = [224, 168, 82];
      const burntSienna = [178, 112, 72];
      const violetEarth = [122, 92, 134];
      let base = mixRgb(burntSienna, warmGold, clamp(0.48 + n * 0.52, 0, 1));
      if (v > 0.62) base = mixRgb(base, violetEarth, (v - 0.62) * 0.68);
      const col = jitterMonetColor(base, rng, 11, 10, 8);
      b.stamp(ctx, "broad", i % 3, x, y, lerp(36, 74, v) * (0.8 + rng() * 0.4), lerp(14, 26, v), -0.06 + (rng() - 0.5) * 0.32, col, 0.82 * edgeFade * topFade, 0.3);
    }

    b.resetCtx(ctx);
    return c;
  }

  _buildHaystackSprite(w, h, seed) {
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    const ctx = c.getContext("2d");
    const b = this.brushes;
    const rng = mulberry32(seed);

    const cx = w * 0.52;
    const baseY = h * 0.82;
    const peakY = h * 0.14;
    const bodyW = w * 0.36;

    const halfWidthAt = (v) => {
      return v < 0.52
        ? lerp(6, bodyW, Math.pow(v / 0.52, 0.92))
        : bodyW * (1 - Math.pow((v - 0.52) / 0.48, 2) * 0.14);
    };

    // 1. Long diagonal Monet violet-cobalt cast shadow stretching left with feathered edges!
    for (let i = 0; i < 36; i++) {
      const u = i / 35;
      const sx = lerp(cx - bodyW * 0.12, w * 0.04, u);
      const sy = baseY - 2 + u * 20 + (rng() - 0.5) * 14;
      const col = jitterMonetColor(mixRgb([86, 66, 136], [148, 106, 152], u * 0.65), rng, 8, 8, 6);
      b.stamp(ctx, i % 2 === 0 ? "scumble" : "broad", i % 3, sx, sy, lerp(92, 46, u), lerp(28, 16, u), -0.10, col, (0.58 - u * 0.34), 0.2);
    }

    // 2. SOLID, 100% opaque painted conical silhouette underpainting (reset transform & alpha first!)
    b.resetCtx(ctx);
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(cx, peakY);
    for (let i = 1; i <= 20; i++) {
      const v = i / 20;
      ctx.lineTo(cx + halfWidthAt(v) * 0.96, lerp(peakY, baseY, v));
    }
    for (let i = 20; i >= 1; i--) {
      const v = i / 20;
      ctx.lineTo(cx - halfWidthAt(v) * 0.96, lerp(peakY, baseY, v));
    }
    ctx.closePath();
    const hg = ctx.createLinearGradient(cx - bodyW, peakY, cx + bodyW, baseY);
    hg.addColorStop(0, "rgb(88, 64, 124)");
    hg.addColorStop(0.38, "rgb(142, 92, 114)");
    hg.addColorStop(0.72, "rgb(212, 142, 74)");
    hg.addColorStop(1, "rgb(246, 198, 92)");
    ctx.fillStyle = hg;
    ctx.fill();
    ctx.restore();

    // 3. 290+ densely staggered overlapping straw thatch strokes (no vertical stripes!)
    for (let s = 0; s < 290; s++) {
      const v = Math.pow(rng(), 0.82); // slightly denser near lower fullness
      const py = lerp(peakY + 6, baseY - 2, v);
      const halfSpan = halfWidthAt(v);
      const u = rng(); // 0 = left shadow, 1 = right sunlit rim
      const px = cx + lerp(-halfSpan * 0.96, halfSpan * 0.96, u);

      let baseCol;
      if (u < 0.36) {
        baseCol = mixRgb([78, 58, 122], [134, 86, 120], u / 0.36);
      } else if (u < 0.76) {
        baseCol = mixRgb([164, 104, 74], [232, 160, 72], (u - 0.36) / 0.4);
      } else {
        baseCol = mixRgb([244, 186, 78], [255, 226, 128], (u - 0.76) / 0.24);
      }

      const col = jitterMonetColor(baseCol, rng, 10, 10, 8);
      const strawAngle = (u - 0.5) * 0.95 + Math.PI * 0.5 + (rng() - 0.5) * 0.28;
      b.stamp(ctx, "short", s % 4, px, py, 32 + rng() * 16, 15 + rng() * 7, strawAngle, col, 0.92, 0.45);
    }

    // 4. Stubble tufts blending haystack base organically into the harvest field
    for (let t = 0; t < 24; t++) {
      const u = t / 23;
      const halfSpan = halfWidthAt(1);
      const px = cx + lerp(-halfSpan * 0.95, halfSpan * 0.95, u);
      const col = u < 0.4 ? [112, 82, 128] : [206, 150, 78];
      b.stamp(ctx, "short", t % 4, px, baseY + 2 + (rng() - 0.5) * 6, 30, 14, (rng() - 0.5) * 0.25, col, 0.85, 0.35);
    }

    // 5. Shimmering golden-amber rim impasto dabs along sunlit right contour
    for (let r = 0; r < 18; r++) {
      const v = r / 17;
      const py = lerp(peakY + 6, baseY - 8, v);
      const halfSpan = halfWidthAt(v);
      const px = cx + halfSpan * 0.94;
      b.stamp(ctx, "knife", r % 3, px, py, 30, 8.5, 1.15 - v * 0.4, [255, 228, 136], 0.88, 0.5);
    }

    b.resetCtx(ctx);
    return c;
  }

  _initData() {
    const rng = mulberry32(470);

    // Flock of 8 woolly sheep walking gently homeward along the field edge
    this.sheep = [];
    for (let i = 0; i < 8; i++) {
      this.sheep.push({
        baseCamX: 9020 + i * 78 + (rng() - 0.5) * 24,
        wy: 138 + (rng() - 0.5) * 55,
        depth: 0.90 + (i % 3) * 0.03,
        scale: 0.9 + rng() * 0.22,
        phase: rng() * Math.PI * 2,
      });
    }
    this.sheep.sort((a, b) => a.depth - b.depth);

    // Graceful swallows wheeling in curving arcs across the evening sky
    this.swallows = [];
    for (let i = 0; i < 14; i++) {
      this.swallows.push({
        baseWx: 8550 + rng() * 1500,
        baseWy: -270 + rng() * 140,
        rx: 90 + rng() * 80,
        ry: 28 + rng() * 24,
        speed: 0.75 + rng() * 0.5,
        phase: rng() * Math.PI * 2,
      });
    }

    // Floating golden-hour pollen / dust motes
    this.motes = [];
    for (let i = 0; i < 45; i++) {
      this.motes.push({
        wx: 8250 + rng() * 2100,
        wy: -240 + rng() * 440,
        r: 7 + rng() * 10,
        phase: rng() * Math.PI * 2,
        speed: 0.8 + rng() * 1.1,
      });
    }

    // Portal 4: Dense Tall Twilight Reeds, Sedge Tufts & Cattails (bridges Haystacks -> Twilight Lagoon!)
    // Centered around camX = 10150..10980 at depth = 1.34..1.45
    this.reedPortal = [];
    for (let i = 0; i < 168; i++) {
      const targetX = 10140 + (i / 167) * 840 + (rng() - 0.5) * 32;
      const targetY = lerp(-64, 8, smoothstep(10140, 10980, targetX));
      const depth = 1.32 + (i % 4) * 0.04;
      this.reedPortal.push({
        ...worldAnchor(targetX, targetY, depth, 0, 395 + rng() * 200),
        depth,
        h: 440 + rng() * 380,
        lean: (rng() - 0.5) * 0.28,
        phase: rng() * Math.PI * 2,
        hasCattail: rng() < 0.26,
        duskT: smoothstep(10140, 10980, targetX),
      });
    }
  }

  _drawSheep(ctx, b, sx, sy, sc, time, phase) {
    const s = sc * 1.42;
    const step = Math.abs(Math.sin(time * 3.4 + phase)) * 3.5 * s;
    const y = sy - step;
    // Violet cast shadow
    b.stamp(ctx, "scumble", 0, sx - 18 * s, sy + 6 * s, 48 * s, 13 * s, 0, [86, 68, 136], 0.48, 0.15);
    // Tiny trotting legs
    const legSwing = Math.sin(time * 3.4 + phase) * 4 * s;
    b.stamp(ctx, "knife", 0, sx - 10 * s + legSwing, sy - 4 * s, 13 * s, 4 * s, Math.PI * 0.5, [76, 62, 108], 0.9, 0.2);
    b.stamp(ctx, "knife", 1, sx + 10 * s - legSwing, sy - 4 * s, 13 * s, 4 * s, Math.PI * 0.5, [76, 62, 108], 0.9, 0.2);
    // Woolly body: lavender shadow bottom + warm honey-cream fleece top
    b.stamp(ctx, "scumble", 0, sx - 2 * s, y - 14 * s, 44 * s, 27 * s, 0, [146, 130, 174], 0.94, 0.35);
    b.stamp(ctx, "short", 1, sx + 3 * s, y - 20 * s, 38 * s, 21 * s, 0, [246, 224, 184], 0.95, 0.45);
    b.stamp(ctx, "short", 2, sx + 9 * s, y - 23 * s, 22 * s, 14 * s, 0.1, [255, 240, 204], 0.92, 0.5);
    // Head facing right
    b.stamp(ctx, "short", 0, sx + 23 * s, y - 18 * s, 15 * s, 11.5 * s, 0.2, [74, 62, 106], 0.96, 0.3);
  }

  _drawShepherdDog(ctx, b, sx, sy, sc, time) {
    const s = sc * 1.42;
    const trot = Math.abs(Math.sin(time * 6.5)) * 5 * s;
    const y = sy - trot;
    b.stamp(ctx, "scumble", 0, sx - 12 * s, sy + 5 * s, 42 * s, 11 * s, 0, [84, 66, 132], 0.48, 0.15);
    b.stamp(ctx, "broad", 0, sx, y - 14 * s, 34 * s, 16 * s, -0.08, [138, 92, 74], 0.95, 0.35);
    b.stamp(ctx, "short", 1, sx + 6 * s, y - 18 * s, 22 * s, 10 * s, -0.05, [238, 194, 128], 0.88, 0.4);
    b.stamp(ctx, "curved", 0, sx - 19 * s, y - 20 * s, 16 * s, 6 * s, -0.7 + Math.sin(time * 9.0) * 0.35, [138, 92, 74], 0.92, 0.3);
    b.stamp(ctx, "short", 2, sx + 18 * s, y - 24 * s, 15 * s, 12 * s, -0.1, [118, 76, 68], 0.96, 0.35);
    const leg = Math.sin(time * 6.5) * 6 * s;
    b.stamp(ctx, "knife", 0, sx - 10 * s + leg, sy - 5 * s, 14 * s, 4 * s, Math.PI * 0.5, [96, 68, 78], 0.92, 0.2);
    b.stamp(ctx, "knife", 1, sx + 11 * s - leg, sy - 5 * s, 14 * s, 4 * s, Math.PI * 0.5, [96, 68, 78], 0.92, 0.2);
  }

  render(ctx, cam, time, viewW, viewH, atmosphere) {
    if (cam.x < 7100 || cam.x > 11600) return;

    const b = this.brushes;
    b.resetCtx(ctx);
    const sceneAlpha = smoothstep(7450, 8250, cam.x) * smoothstep(11100, 10250, cam.x);

    // 1. Low Golden Sun Glow on the Right Horizon
    const sunAnc = worldAnchor(9750, -78, 0.16);
    const sunPos = worldToScreen(sunAnc.wx, -88, 0.16, cam, viewW, viewH);
    const sunVis = smoothstep(7300, 8400, cam.x) * smoothstep(11500, 10100, cam.x);
    if (sunVis > 0.01) {
      ctx.save();
      ctx.globalAlpha = sunVis * 0.85;
      const g = ctx.createRadialGradient(sunPos.x, sunPos.y, 12, sunPos.x, sunPos.y, 380 * sunPos.scale);
      g.addColorStop(0, "rgba(255, 224, 136, 0.85)");
      g.addColorStop(0.42, "rgba(255, 178, 96, 0.32)");
      g.addColorStop(1, "rgba(255, 158, 96, 0)");
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(sunPos.x, sunPos.y, 380 * sunPos.scale, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // 2. Evening Apricot & Lavender Clouds
    const c1Anc = worldAnchor(8950, -78, 0.18);
    const c1 = worldToScreen(c1Anc.wx + time * 5, -310, 0.18, cam, viewW, viewH);
    const c2Anc = worldAnchor(9850, -78, 0.20);
    const c2 = worldToScreen(c2Anc.wx + time * 7, -270, 0.20, cam, viewW, viewH);
    ctx.save();
    ctx.globalAlpha = 0.88 * sceneAlpha;
    ctx.drawImage(this.clouds[0], c1.x - 290 * c1.scale, c1.y - 100 * c1.scale, 580 * c1.scale, 200 * c1.scale);
    ctx.drawImage(this.clouds[1], c2.x - 240 * c2.scale, c2.y - 87 * c2.scale, 480 * c2.scale, 175 * c2.scale);
    ctx.restore();

    // 3. Far Violet Hills & Harvest Field Base (faded cleanly behind Portals 3 & 4)
    b.resetCtx(ctx);
    if (sceneAlpha > 0.01) {
      ctx.save();
      ctx.globalAlpha = sceneAlpha;
      const hillAnc = worldAnchor(9350, -78, 0.42);
      const hillPos = worldToScreen(hillAnc.wx - 1300, hillAnc.wy - 170, 0.42, cam, viewW, viewH);
      ctx.drawImage(this.farHills, hillPos.x, hillPos.y, this.farHills.width * hillPos.scale, this.farHills.height * hillPos.scale);

      const fieldAnc = worldAnchor(9350, -78, 0.84);
      const fieldPos = worldToScreen(fieldAnc.wx - 1450, fieldAnc.wy - 140, 0.84, cam, viewW, viewH);
      ctx.drawImage(this.fieldBase, fieldPos.x, fieldPos.y, this.fieldBase.width * fieldPos.scale, this.fieldBase.height * fieldPos.scale);
      ctx.restore();
    }

    // 5. Wheeling Flock of Swallows in the Evening Sky
    for (let i = 0; i < this.swallows.length; i++) {
      const sw = this.swallows[i];
      const wx = sw.baseWx + Math.cos(time * sw.speed + sw.phase) * sw.rx + time * 16;
      const wy = sw.baseWy + Math.sin(time * sw.speed * 1.4 + sw.phase) * sw.ry;
      const p = worldToScreen(wx, wy, 0.56, cam, viewW, viewH);
      if (p.x < -50 || p.x > viewW + 50) continue;
      const flap = Math.sin(time * 9.5 + i * 1.8);
      const s = p.scale * 0.85;
      b.stamp(ctx, "curved", 0, p.x - 8 * s, p.y - flap * 5 * s, 18 * s, 4.5 * s, -0.35 + flap * 0.45, [76, 58, 108], 0.86 * sceneAlpha, 0.2);
      b.stamp(ctx, "curved", 1, p.x + 8 * s, p.y - flap * 5 * s, 18 * s, 4.5 * s, 0.35 - flap * 0.45, [76, 58, 108], 0.86 * sceneAlpha, 0.2);
    }

    // 6. Monumental Golden-Hour Haystacks (Meules)
    b.resetCtx(ctx);
    if (sceneAlpha > 0.01) {
      ctx.save();
      ctx.globalAlpha = sceneAlpha;
      const hs1Anc = worldAnchor(9040, -78, 0.88, 0, -48);
      const hs1Pos = worldToScreen(hs1Anc.wx, hs1Anc.wy, 0.88, cam, viewW, viewH);
      ctx.drawImage(this.haystackSmall, hs1Pos.x - 175 * hs1Pos.scale, hs1Pos.y - 230 * hs1Pos.scale, 350 * hs1Pos.scale, 290 * hs1Pos.scale);

      const hs2Anc = worldAnchor(9560, -78, 0.91, 0, -22);
      const hs2Pos = worldToScreen(hs2Anc.wx, hs2Anc.wy, 0.91, cam, viewW, viewH);
      ctx.drawImage(this.haystackBig, hs2Pos.x - 220 * hs2Pos.scale, hs2Pos.y - 290 * hs2Pos.scale, 440 * hs2Pos.scale, 360 * hs2Pos.scale);
      ctx.restore();
    }

    // 7. Walking Flock of Woolly Sheep & Trotting Shepherd Dog
    const flockDrift = (time - 64) * 20;
    for (let i = 0; i < this.sheep.length; i++) {
      const sh = this.sheep[i];
      const anc = worldAnchor(sh.baseCamX + flockDrift, -78, sh.depth, 0, sh.wy);
      const p = worldToScreen(anc.wx, anc.wy, sh.depth, cam, viewW, viewH);
      if (p.x < -80 || p.x > viewW + 80) continue;
      this._drawSheep(ctx, b, p.x, p.y, p.scale * sh.scale, time, sh.phase);
    }

    const dogAnc = worldAnchor(9660 + flockDrift + Math.sin(time * 1.1) * 32, -78, 0.94, 0, 175 + Math.cos(time * 1.1) * 18);
    const dogPos = worldToScreen(dogAnc.wx, dogAnc.wy, 0.94, cam, viewW, viewH);
    if (dogPos.x > -80 && dogPos.x < viewW + 80) {
      this._drawShepherdDog(ctx, b, dogPos.x, dogPos.y, dogPos.scale * 1.05, time);
    }

    // 8. Golden Pollen / Sunset Dust Motes
    for (let i = 0; i < this.motes.length; i++) {
      const m = this.motes[i];
      const mx = m.wx + Math.sin(time * m.speed + m.phase) * 24;
      const my = m.wy + Math.cos(time * m.speed * 0.7 + m.phase) * 18;
      const p = worldToScreen(mx, my, 1.08, cam, viewW, viewH);
      if (p.x < -40 || p.x > viewW + 40) continue;
      const pulse = 0.4 + 0.45 * Math.sin(time * 2.5 + m.phase);
      b.stamp(ctx, "scumble", 0, p.x, p.y, m.r * p.scale, m.r * p.scale, 0, [255, 224, 134], pulse * 0.65 * sceneAlpha, 0.1);
    }

    // 9. Portal 4: Dense Tall Twilight Reeds & Cattails (bridges Golden Haystacks -> Twilight Lagoon!)
    for (let i = 0; i < this.reedPortal.length; i++) {
      const rd = this.reedPortal[i];
      const p = worldToScreen(rd.wx, rd.wy, rd.depth, cam, viewW, viewH);
      if (p.x < -120 || p.x > viewW + 120) continue;
      const sway = Math.sin(time * 1.2 + rd.phase) * 18 * p.scale;
      const tipX = p.x + (rd.lean * rd.h + sway) * p.scale;
      const tipY = p.y - rd.h * p.scale;
      const midX = (p.x + tipX) * 0.5 + sway * 0.25;
      const midY = (p.y + tipY) * 0.5;
      const col = mixRgb([124, 92, 74], [32, 42, 82], rd.duskT);
      const ang = Math.atan2(tipY - p.y, tipX - p.x);
      b.stamp(ctx, "curved", i % 3, midX, midY, rd.h * p.scale, 15 * p.scale, ang, col, 0.92, 0.3);
      if (rd.hasCattail) {
        b.stamp(ctx, "short", 0, lerp(p.x, tipX, 0.78), lerp(p.y, tipY, 0.78), 36 * p.scale, 15 * p.scale, ang, mixRgb([96, 56, 52], [38, 32, 64], rd.duskT), 0.95, 0.4);
      }
    }

    b.resetCtx(ctx);
  }
}

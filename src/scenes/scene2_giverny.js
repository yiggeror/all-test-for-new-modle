// Scene 2 (17s - 39s): Giverny Water Lily Pond, Japanese Bridge, Wisteria, Koi, Dragonflies & Rose Arbor Portal
import { mulberry32, clamp, lerp, smoothstep } from "../core/noise.js";
import { mixRgb, jitterMonetColor } from "../core/palette.js";
import { worldToScreen, worldAnchor } from "../core/camera.js";
import {
  createPainterlyCloudSprite,
  createHillTreelineSprite,
  createLilyPadSprite,
  createLilyFlowerSprite,
  paintAnimatedWater,
  paintWaterRipple,
} from "../core/painter.js";

export class Scene2Giverny {
  constructor(brushes) {
    this.brushes = brushes;
    this._initSprites();
    this._initData();
  }

  _initSprites() {
    const b = this.brushes;
    // Luminous morning clouds
    this.clouds = [
      createPainterlyCloudSprite(b, 480, 175, [252, 248, 238], [164, 188, 218], 201),
      createPainterlyCloudSprite(b, 420, 160, [255, 250, 242], [170, 194, 222], 202),
    ];

    // Far Giverny garden bank (rich viridian, olive, sunlit chartreuse, violet-teal shadows)
    this.gardenBank = createHillTreelineSprite(
      b, 2600, 340,
      [52, 118, 86],
      [148, 192, 92],
      [64, 96, 134],
      211,
      { treeDensity: 1.35, poplars: false, hazeAlpha: 0.14 }
    );

    // Pre-painted Japanese Footbridge sprite (high detail, Monet sage-green & lavender shadow)
    this.bridgeSprite = this._buildJapaneseBridgeSprite();

    // Multiple unique lily pad & water lily flower sprites
    this.padSprites = [
      createLilyPadSprite(b, 140, 221, false),
      createLilyPadSprite(b, 120, 222, false),
      createLilyPadSprite(b, 155, 223, false),
    ];
    this.flowerSprites = [
      createLilyFlowerSprite(b, 68, "pink", 231),
      createLilyFlowerSprite(b, 64, "cream", 232),
      createLilyFlowerSprite(b, 72, "rose", 233),
    ];
  }

  _buildJapaneseBridgeSprite() {
    const w = 980, h = 410;
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    const ctx = c.getContext("2d");
    const b = this.brushes;
    const rng = mulberry32(250);

    const archY = (u) => {
      // u in [0, 1] -> graceful parabolic arch
      const t = (u - 0.5) * 2;
      return 275 - (1 - t * t) * 112;
    };

    // 1. Vertical support pilings submerged into water
    const posts = [0.08, 0.22, 0.36, 0.5, 0.64, 0.78, 0.92];
    for (const u of posts) {
      const px = lerp(55, w - 55, u);
      const topY = archY(u) - 72;
      const botY = 392;
      const col = jitterMonetColor([64, 98, 92], rng, 8, 8, 6);
      const steps = 10;
      for (let s = 0; s < steps; s++) {
        const py = lerp(topY, botY, s / (steps - 1));
        const shad = s > 6 ? [52, 74, 114] : col;
        b.stamp(ctx, "knife", s % 3, px + (rng() - 0.5) * 3, py, 28, 12, Math.PI * 0.5, shad, 0.88, 0.35);
      }
      // Sunlit post cap
      b.stamp(ctx, "short", 0, px, topY - 4, 22, 16, 0, [166, 202, 124], 0.9, 0.45);
    }

    // 2. Bridge deck underside (cool lavender-teal shadow) & sunlit deck edge
    for (let i = 0; i < 65; i++) {
      const u = i / 64;
      const px = lerp(45, w - 45, u);
      const py = archY(u);
      const slope = (archY(u + 0.01) - archY(u - 0.01)) / (0.02 * (w - 90));
      const ang = Math.atan(slope);
      b.stamp(ctx, "broad", i % 3, px, py + 14, 34, 18, ang, jitterMonetColor([66, 88, 124], rng, 8, 8, 6), 0.9, 0.3);
      b.stamp(ctx, "broad", (i + 1) % 3, px, py, 34, 15, ang, jitterMonetColor([124, 168, 116], rng, 10, 10, 7), 0.9, 0.35);
      b.stamp(ctx, "knife", i % 3, px, py - 8, 28, 7, ang, jitterMonetColor([198, 224, 146], rng, 8, 8, 6), 0.82, 0.45);
    }

    // 3. Curved Handrails & Lattice Balustrades
    for (let i = 0; i < 62; i++) {
      const u = i / 61;
      const px = lerp(52, w - 52, u);
      const py = archY(u) - 66;
      const slope = (archY(u + 0.01) - archY(u - 0.01)) / (0.02 * (w - 104));
      const ang = Math.atan(slope);
      // Mid rail
      b.stamp(ctx, "knife", i % 3, px, py + 32, 30, 7, ang, jitterMonetColor([88, 134, 104], rng, 8, 8, 6), 0.85, 0.3);
      // Top sunlit handrail
      b.stamp(ctx, "knife", (i + 1) % 3, px, py, 32, 10, ang, jitterMonetColor([138, 184, 116], rng, 9, 9, 7), 0.92, 0.4);
      b.stamp(ctx, "knife", (i + 2) % 3, px, py - 4, 24, 5, ang, [224, 236, 168], 0.72, 0.45);
      // Vertical pickets
      if (i % 2 === 0) {
        b.stamp(ctx, "knife", 0, px, py + 33, 56, 6, Math.PI * 0.5, jitterMonetColor([76, 116, 104], rng, 8, 8, 6), 0.82, 0.3);
      }
    }

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    return c;
  }

  _initData() {
    const rng = mulberry32(280);

    // Cascading wisteria racemes hanging gracefully along the bridge, parted gently around the girl
    this.wisteriaClusters = [];
    for (let i = 0; i < 48; i++) {
      const u = 0.07 + (i / 47) * 0.86 + (rng() - 0.5) * 0.015;
      const t = (u - 0.5) * 2;
      const archOffset = -(1 - t * t) * 112;
      const nearGirl = Math.abs(u - 0.45) < 0.09;
      this.wisteriaClusters.push({
        u,
        relX: (u - 0.5) * 860,
        relY: archOffset - (nearGirl ? 96 : 76) + rng() * 12,
        len: nearGirl ? 16 + rng() * 16 : 44 + rng() * 64,
        phase: rng() * Math.PI * 2,
        hue: rng(),
      });
    }

    // Lush Weeping Willow boughs anchored cleanly on the OUTER flanks, entering from above top frame
    this.pondWillows = [];
    const willowCenters = [3060, 3260, 4640, 4840];
    for (let w = 0; w < willowCenters.length; w++) {
      const cx = willowCenters[w];
      for (let s = 0; s < 20; s++) {
        const targetX = cx + (rng() - 0.5) * 260;
        const anc = worldAnchor(targetX, -20, 0.84, 0, -610 + (rng() - 0.5) * 90);
        this.pondWillows.push({
          wx: anc.wx,
          wy: anc.wy,
          len: 540 + rng() * 280,
          curve: (w < 2 ? 1 : -1) * (20 + rng() * 45),
          phase: rng() * Math.PI * 2,
          dabs: 18,
          warmth: 0.45 + rng() * 0.55,
        });
      }
    }

    // Water Lilies (Pads & Flowers) scattered artistically across the pond
    this.lilies = [];
    for (let i = 0; i < 48; i++) {
      const camAnchor = 2820 + rng() * 2220;
      const depth = 0.86 + rng() * 0.28;
      const wy = 190 + rng() * 270;
      const sc = lerp(0.58, 1.28, (wy - 190) / 270);
      this.lilies.push({
        ...worldAnchor(camAnchor, -15, depth, 0, wy),
        depth,
        scale: sc,
        padIdx: i % this.padSprites.length,
        hasFlower: i % 2 === 0 && rng() < 0.8,
        flowerIdx: i % this.flowerSprites.length,
        phase: rng() * Math.PI * 2,
      });
    }
    this.lilies.sort((a, b) => a.depth - b.depth);

    // Swimming Koi Fish beneath the translucent water surface
    this.kois = [
      { cx: 3420, cy: 310, rx: 140, ry: 48, speed: 0.52, phase: 0.2, col1: [238, 106, 48], col2: [252, 232, 210], scale: 1.05 },
      { cx: 3820, cy: 365, rx: 175, ry: 55, speed: -0.44, phase: 2.1, col1: [248, 154, 46], col2: [244, 92, 52], scale: 1.15 },
      { cx: 4160, cy: 295, rx: 130, ry: 42, speed: 0.58, phase: 4.0, col1: [248, 240, 224], col2: [228, 86, 48], scale: 0.95 },
      { cx: 4460, cy: 350, rx: 150, ry: 50, speed: -0.49, phase: 1.1, col1: [236, 118, 52], col2: [252, 216, 128], scale: 1.08 },
      { cx: 3620, cy: 255, rx: 115, ry: 34, speed: 0.46, phase: 3.3, col1: [244, 138, 58], col2: [255, 242, 226], scale: 0.85 },
    ];

    // Hovering Iridescent Blue Dragonflies
    this.dragonflies = [
      { wx: 3320, wy: 220, phase: 0.4, speed: 1.3 },
      { wx: 3780, wy: 260, phase: 2.1, speed: 1.6 },
      { wx: 4240, wy: 210, phase: 3.8, speed: 1.4 },
      { wx: 4580, wy: 245, phase: 5.0, speed: 1.5 },
    ];

    // Portal 2: Lush Climbing Rose Arbor Canopy & Flowering Garden Hedges (bridges Giverny -> Poppy Field!)
    this.roseClusters = [];
    for (let c = 0; c < 48; c++) {
      const targetX = 4880 + (c / 47) * 760 + (rng() - 0.5) * 40;
      const targetY = lerp(-30, -148, smoothstep(4880, 5640, targetX));
      const depth = 1.32 + (c % 4) * 0.04;
      // Arch framing: deep overhanging top canopy + cascading sides + lower rose hedge bank
      const mode = c % 3;
      const centerOffY = mode === 0 ? -520 + rng() * 240 : mode === 1 ? -220 + rng() * 380 : 280 + rng() * 240;
      const centerOffX = (rng() - 0.5) * 120;

      const dabs = [];
      for (let k = 0; k < 20; k++) {
        const a = rng() * Math.PI * 2;
        const r = Math.pow(rng(), 0.72);
        const dx = centerOffX + Math.cos(a) * (58 + rng() * 44) * r;
        const dy = centerOffY + Math.sin(a) * (52 + rng() * 40) * r;
        dabs.push({
          ...worldAnchor(targetX, targetY, depth, dx, dy),
          size: 38 + rng() * 22,
          angle: a + (rng() - 0.5) * 0.9,
          shade: rng(),
          phase: rng() * Math.PI * 2,
        });
      }

      const roses = [];
      const roseCount = 2 + Math.floor(rng() * 3);
      for (let r = 0; r < roseCount; r++) {
        const dx = centerOffX + (rng() - 0.5) * 78;
        const dy = centerOffY + (rng() - 0.5) * 68;
        const rosePalette = rng() < 0.45 ? [242, 134, 158] : rng() < 0.78 ? [255, 224, 218] : [224, 82, 118];
        roses.push({
          ...worldAnchor(targetX, targetY, depth, dx, dy),
          roseColor: rosePalette,
          roseSize: 22 + rng() * 14,
          phase: rng() * Math.PI * 2,
        });
      }

      this.roseClusters.push({ depth, dabs, roses });
    }
  }

  _drawKoi(ctx, b, koi, cam, time, viewW, viewH) {
    const ang = time * koi.speed + koi.phase;
    const wx = koi.cx + Math.cos(ang) * koi.rx;
    const wy = koi.cy + Math.sin(ang) * koi.ry;
    const p = worldToScreen(wx, wy, 0.92, cam, viewW, viewH);
    if (p.x < -120 || p.x > viewW + 120) return;

    const vx = -Math.sin(ang) * koi.rx * koi.speed;
    const vy = Math.cos(ang) * koi.ry * koi.speed;
    const dir = Math.atan2(vy, vx);
    const sc = p.scale * koi.scale;

    const segs = 5;
    for (let s = 0; s < segs; s++) {
      const u = s / (segs - 1);
      const wiggle = Math.sin(time * 7.5 + koi.phase - u * 2.8) * (4 + u * 8) * sc;
      const dist = -u * 38 * sc;
      const sx = p.x + Math.cos(dir) * dist - Math.sin(dir) * wiggle;
      const sy = p.y + Math.sin(dir) * dist + Math.cos(dir) * wiggle;
      const col = s % 2 === 0 ? koi.col1 : koi.col2;
      const len = lerp(20, 9, u) * sc;
      const thick = lerp(12, 4.5, u) * sc;
      b.stamp(ctx, "short", s % 4, sx, sy, len, thick, dir, col, 0.56, 0.15);
    }
    const tw = Math.sin(time * 7.5 + koi.phase - 3.2) * 12 * sc;
    const tx = p.x - Math.cos(dir) * 44 * sc - Math.sin(dir) * tw;
    const ty = p.y - Math.sin(dir) * 44 * sc + Math.cos(dir) * tw;
    b.stamp(ctx, "curved", 0, tx, ty, 18 * sc, 11 * sc, dir + 0.3, koi.col2, 0.45, 0.1);

    if (Math.sin(time * 2.2 + koi.phase) > 0.4) {
      const ripAlpha = (Math.sin(time * 2.2 + koi.phase) - 0.4) * 0.45;
      paintWaterRipple(ctx, b, p.x, p.y - 4 * sc, 24 * sc, 8 * sc, [206, 236, 224], ripAlpha, 260);
    }
  }

  _drawGirlOnBridge(ctx, b, bx, by, sc, time) {
    // Graceful Impressionist woman in cream & cerulean dress leaning gently by railing
    const sway = Math.sin(time * 1.4) * 2.5 * sc;
    // Cool periwinkle shadow in skirt folds
    b.stamp(ctx, "broad", 0, bx - 5 * sc, by - 26 * sc, 34 * sc, 52 * sc, 0.14, [122, 148, 198], 0.92, 0.35);
    // Sunlit ivory & soft cerulean dress skirt
    b.stamp(ctx, "broad", 1, bx + 5 * sc + sway * 0.4, by - 26 * sc, 30 * sc, 50 * sc, -0.08, [246, 242, 230], 0.94, 0.45);
    b.stamp(ctx, "short", 2, bx + 11 * sc + sway * 0.6, by - 16 * sc, 24 * sc, 28 * sc, -0.15, [255, 250, 234], 0.9, 0.48);
    // Bodice & cerulean sash
    b.stamp(ctx, "short", 0, bx + 2 * sc, by - 60 * sc, 20 * sc, 24 * sc, 0.05, [242, 238, 226], 0.95, 0.38);
    b.stamp(ctx, "knife", 1, bx + 2 * sc, by - 50 * sc, 22 * sc, 6.5 * sc, 0, [96, 148, 204], 0.92, 0.38);
    // Fluttering coral-rose scarf ribbon
    const ribX = bx - 15 * sc + Math.sin(time * 3.2) * 8 * sc;
    const ribY = by - 52 * sc + Math.cos(time * 2.8) * 3.5 * sc;
    b.stamp(ctx, "curved", 0, ribX, ribY, 28 * sc, 7 * sc, -0.32 + Math.sin(time * 3.0) * 0.2, [234, 126, 146], 0.9, 0.38);
    // Head & sunlit straw sunhat with rose ribbon
    b.stamp(ctx, "short", 1, bx + 4 * sc, by - 78 * sc, 14 * sc, 15 * sc, 0, [240, 204, 180], 0.95, 0.32);
    b.stamp(ctx, "knife", 0, bx + 4 * sc, by - 85 * sc, 38 * sc, 11 * sc, -0.1, [248, 222, 148], 0.96, 0.48);
    b.stamp(ctx, "short", 2, bx + 2 * sc, by - 90 * sc, 20 * sc, 9.5 * sc, -0.08, [226, 124, 148], 0.92, 0.42);
  }

  render(ctx, cam, time, viewW, viewH, atmosphere) {
    if (cam.x < 1750 || cam.x > 6300) return;

    const b = this.brushes;
    b.resetCtx(ctx);
    const horizonY = worldToScreen(0, 62, 0.25, cam, viewW, viewH).y;
    const sceneAlpha = smoothstep(1850, 2600, cam.x) * smoothstep(5750, 4950, cam.x);

    // 1. Morning Clouds
    const c1 = worldToScreen(worldAnchor(3600, -20, 0.18).wx + time * 7, -280, 0.18, cam, viewW, viewH);
    const c2 = worldToScreen(worldAnchor(4400, -20, 0.20).wx + time * 9, -240, 0.20, cam, viewW, viewH);
    ctx.save();
    ctx.globalAlpha = 0.85 * sceneAlpha;
    ctx.drawImage(this.clouds[0], c1.x - 240 * c1.scale, c1.y - 87 * c1.scale, 480 * c1.scale, 175 * c1.scale);
    ctx.drawImage(this.clouds[1], c2.x - 210 * c2.scale, c2.y - 80 * c2.scale, 420 * c2.scale, 160 * c2.scale);
    ctx.restore();

    // 2. Far Giverny Garden Bank (depth 0.42, faded cleanly behind Portals 1 & 2)
    b.resetCtx(ctx);
    if (sceneAlpha > 0.01) {
      const bankAnchor = worldAnchor(3900, -15, 0.42);
      const bankPos = worldToScreen(bankAnchor.wx - 1300, bankAnchor.wy - 190, 0.42, cam, viewW, viewH);
      ctx.save();
      ctx.globalAlpha = sceneAlpha;
      ctx.drawImage(this.gardenBank, bankPos.x, bankPos.y, this.gardenBank.width * bankPos.scale, this.gardenBank.height * bankPos.scale);
      ctx.restore();
    }

    // 3. Giverny Water Lily Pond Surface & Feathered Broken Reflections
    b.resetCtx(ctx);
    const pondLeft = Math.max(-40, worldToScreen(worldAnchor(2450, 0, 1.0).wx, 0, 1.0, cam, viewW, viewH).x);
    const pondRight = Math.min(viewW + 40, worldToScreen(worldAnchor(5450, 0, 1.0).wx, 0, 1.0, cam, viewW, viewH).x);
    const waterTop = Math.round(horizonY + 24 * cam.zoom);

    const bridgePos = worldToScreen(worldAnchor(3960, -15, 0.78).wx, 38, 0.78, cam, viewW, viewH);
    if (pondRight > pondLeft + 20 && sceneAlpha > 0.02) {
      paintAnimatedWater(ctx, b, { x: pondLeft, y: waterTop, w: pondRight - pondLeft, h: viewH - waterTop + 40 }, time, {
        baseColor: [58, 124, 134],
        deepColor: [34, 72, 96],
        highlightColor: [184, 224, 212],
        sunColX: bridgePos.x - 140 * bridgePos.scale,
        sunColor: [246, 242, 206],
        reflectionBands: [
          { x: bridgePos.x - 220 * bridgePos.scale, yTop: waterTop + 20, width: 120 * bridgePos.scale, height: 180, color: [88, 138, 102], waveAmp: 10, alpha: 0.55 },
          { x: bridgePos.x + 180 * bridgePos.scale, yTop: waterTop + 20, width: 140 * bridgePos.scale, height: 190, color: [122, 114, 178], waveAmp: 12, alpha: 0.45 },
          { x: bridgePos.x - 460 * bridgePos.scale, yTop: waterTop + 5, width: 180 * bridgePos.scale, height: 220, color: [48, 104, 82], waveAmp: 9, alpha: 0.5 },
        ],
        seed: 266,
        fadeLeft: pondLeft > -20 ? 240 : 0,
        fadeRight: pondRight < viewW + 20 ? 280 : 0,
      });
    }

    // 4. Swimming Koi beneath translucent water surface
    for (const koi of this.kois) {
      this._drawKoi(ctx, b, koi, cam, time, viewW, viewH);
    }

    // 5. Japanese Footbridge + Wisteria Racemes + Girl on Bridge (depth 0.78)
    if (bridgePos.x > -700 && bridgePos.x < viewW + 700) {
      const bs = bridgePos.scale;
      const bw = this.bridgeSprite.width * bs;
      const bh = this.bridgeSprite.height * bs;

      // Girl stands clearly framed off-center along the crest of the bridge
      this._drawGirlOnBridge(ctx, b, bridgePos.x - 44 * bs, bridgePos.y - 34 * bs, bs * 1.38, time);

      b.resetCtx(ctx);
      ctx.drawImage(this.bridgeSprite, bridgePos.x - bw * 0.5, bridgePos.y - bh * 0.52, bw, bh);

      // Olive wisteria vine runner + tapered lilac/lavender raceme clusters
      for (let i = 0; i < this.wisteriaClusters.length; i++) {
        const wc = this.wisteriaClusters[i];
        const sway = Math.sin(time * 1.5 + wc.phase) * 7 * bs;
        const wx = bridgePos.x + wc.relX * bs;
        const wy = bridgePos.y + wc.relY * bs;
        b.stamp(ctx, "curved", i % 3, wx, wy - 4 * bs, 28 * bs, 9 * bs, 0.1, [68, 118, 72], 0.85, 0.25);
        for (let k = 0; k < 5; k++) {
          const u = k / 4;
          const col = mixRgb([138, 102, 188], [224, 194, 246], wc.hue * 0.45 + u * 0.55);
          const rx = wx + sway * u + (k % 2 === 0 ? -3 : 3) * bs * (1 - u);
          const ry = wy + u * wc.len * bs;
          b.stamp(ctx, "short", (i + k) % 4, rx, ry, (22 - u * 11) * bs, (14 - u * 6) * bs, Math.PI * 0.5 + sway * 0.01, col, 0.9, 0.4);
        }
      }
    }

    // 6. Pond Willows cleanly framing the outer flanks of the bridge (depth 0.84)
    for (let i = 0; i < this.pondWillows.length; i++) {
      const pw = this.pondWillows[i];
      const p = worldToScreen(pw.wx, pw.wy, 0.84, cam, viewW, viewH);
      if (p.x < -140 || p.x > viewW + 140) continue;
      for (let d = 0; d < pw.dabs; d++) {
        const u = d / (pw.dabs - 1);
        const sway = Math.sin(time * 1.25 + pw.phase - u * 1.5) * (10 + u * 24) * p.scale;
        const arc = Math.sin(u * Math.PI * 0.8) * pw.curve * p.scale;
        const col = u < 0.38 ? [44, 94, 68] : u < 0.78 ? [88, 148, 76] : [164, 198, 96];
        const ang = Math.PI * 0.5 + sway * 0.004 + pw.curve * 0.002;
        b.stamp(ctx, "curved", (i + d) % 3, p.x + sway + arc, p.y + u * pw.len * p.scale, (44 + (d % 3) * 8) * p.scale, (18 + (d % 2) * 5) * p.scale, ang, col, 0.86, 0.35);
      }
    }

    // 7. Blooming Water Lilies & Solid Notched Lily Pads (depth 0.86 - 1.14)
    b.resetCtx(ctx);
    for (let i = 0; i < this.lilies.length; i++) {
      const li = this.lilies[i];
      const p = worldToScreen(li.wx, li.wy, li.depth, cam, viewW, viewH);
      if (p.x < -140 || p.x > viewW + 140) continue;
      const bobX = Math.sin(time * 1.1 + li.phase) * 3.5 * p.scale;
      const bobY = Math.cos(time * 1.4 + li.phase) * 2.2 * p.scale;
      const pad = this.padSprites[li.padIdx];
      const pw = pad.width * p.scale * li.scale;
      const ph = pad.height * p.scale * li.scale;
      ctx.drawImage(pad, p.x - pw * 0.5 + bobX, p.y - ph * 0.5 + bobY, pw, ph);

      if (li.hasFlower) {
        const fl = this.flowerSprites[li.flowerIdx];
        const fw = fl.width * p.scale * li.scale;
        const fh = fl.height * p.scale * li.scale;
        ctx.drawImage(fl, p.x - fw * 0.5 + bobX + 4 * p.scale, p.y - fh * 0.85 + bobY, fw, fh);
      }
    }

    // 8. Iridescent Blue Dragonflies hovering & darting over the lily pads
    for (let i = 0; i < this.dragonflies.length; i++) {
      const df = this.dragonflies[i];
      const hoverX = Math.sin(time * df.speed + df.phase) * 58 + Math.cos(time * 2.7 + df.phase) * 18;
      const hoverY = Math.cos(time * df.speed * 1.3 + df.phase) * 24;
      const p = worldToScreen(df.wx + hoverX, df.wy + hoverY, 1.05, cam, viewW, viewH);
      if (p.x < -60 || p.x > viewW + 60) continue;
      const s = p.scale;
      const wingBuzz = Math.sin(time * 38 + i);
      b.stamp(ctx, "knife", 0, p.x - 4 * s, p.y - 6 * s * (0.4 + 0.6 * wingBuzz), 24 * s, 6 * s, -0.45, [218, 246, 255], 0.58, 0.1);
      b.stamp(ctx, "knife", 1, p.x + 2 * s, p.y - 5 * s * (0.4 - 0.6 * wingBuzz), 22 * s, 5.5 * s, 0.45, [218, 246, 255], 0.58, 0.1);
      b.stamp(ctx, "knife", 2, p.x, p.y, 26 * s, 4.5 * s, 0.08, [46, 174, 212], 0.95, 0.4);
    }

    // 9. Portal 2: Lush Climbing Rose Arbor Foliage Clusters & Multi-Petal Monet Roses
    for (let c = 0; c < this.roseClusters.length; c++) {
      const cl = this.roseClusters[c];
      for (let i = 0; i < cl.dabs.length; i++) {
        const db = cl.dabs[i];
        const p = worldToScreen(db.wx, db.wy, cl.depth, cam, viewW, viewH);
        if (p.x < -120 || p.x > viewW + 120) continue;
        const sway = Math.sin(time * 1.4 + db.phase) * 7 * p.scale;
        const leafCol = db.shade < 0.35
          ? [44, 98, 62]
          : db.shade < 0.72
          ? [72, 138, 72]
          : [138, 178, 86];
        b.stamp(ctx, "short", (c + i) % 4, p.x + sway, p.y, db.size * p.scale, db.size * 0.66 * p.scale, db.angle + sway * 0.008, leafCol, 0.9, 0.35);
      }

      for (let r = 0; r < cl.roses.length; r++) {
        const rsObj = cl.roses[r];
        const p = worldToScreen(rsObj.wx, rsObj.wy, cl.depth, cam, viewW, viewH);
        if (p.x < -100 || p.x > viewW + 100) continue;
        const sway = Math.sin(time * 1.45 + rsObj.phase) * 8 * p.scale;
        const sx = p.x + sway;
        const sy = p.y;
        const rs = rsObj.roseSize * p.scale;
        const petalHi = mixRgb(rsObj.roseColor, [255, 244, 234], 0.45);
        const petalSh = mixRgb(rsObj.roseColor, [128, 52, 86], 0.35);
        b.stamp(ctx, "short", 0, sx - rs * 0.22, sy + rs * 0.14, rs * 0.85, rs * 0.65, -0.4, petalSh, 0.92, 0.4);
        b.stamp(ctx, "short", 1, sx + rs * 0.24, sy + rs * 0.08, rs * 0.85, rs * 0.65, 0.4, rsObj.roseColor, 0.94, 0.45);
        b.stamp(ctx, "short", 2, sx, sy - rs * 0.16, rs * 0.78, rs * 0.62, 0.1, petalHi, 0.95, 0.48);
        b.stamp(ctx, "short", 3, sx + rs * 0.05, sy, rs * 0.32, rs * 0.28, 0, [250, 212, 106], 0.95, 0.5);
      }
    }

    b.resetCtx(ctx);
  }
}

// Scene 1 (0s - 20s): Impression, Sunrise — Dawn Mist, Rowing Boatman, Egrets & Willow Portal
import { mulberry32, clamp, lerp, smoothstep } from "../core/noise.js";
import { mixRgb, jitterMonetColor } from "../core/palette.js";
import { worldToScreen, worldAnchor } from "../core/camera.js";
import { createPainterlyCloudSprite, createHillTreelineSprite, paintAnimatedWater, paintWaterRipple } from "../core/painter.js";

export class Scene1Dawn {
  constructor(brushes) {
    this.brushes = brushes;
    this._initSprites();
    this._initData();
  }

  _initSprites() {
    const b = this.brushes;
    // Soft rose-lavender dawn clouds
    this.clouds = [
      createPainterlyCloudSprite(b, 460, 170, [248, 204, 182], [142, 138, 178], 101),
      createPainterlyCloudSprite(b, 540, 190, [242, 192, 176], [134, 136, 174], 102),
      createPainterlyCloudSprite(b, 390, 150, [252, 214, 186], [150, 146, 184], 103),
    ];

    // Misty distant Seine riverbanks (soft atmospheric perspective)
    this.farBank = createHillTreelineSprite(
      b, 2600, 320,
      [92, 104, 138],   // misty slate-violet foliage
      [154, 158, 184],  // hazy lavender-blue highlights
      [126, 132, 168],
      201,
      { treeDensity: 0.9, poplars: true, hazeAlpha: 0.48 }
    );

    // Pre-painted distant moored sailboats in fog
    this.mistBoat = this._buildMistBoatSprite();
    // Pre-painted wooden hero skiff hull
    this.heroBoat = this._buildHeroBoatSprite();
  }

  _buildMistBoatSprite() {
    const c = document.createElement("canvas");
    c.width = 160; c.height = 190;
    const ctx = c.getContext("2d");
    const b = this.brushes;
    const rng = mulberry32(303);
    // Faint mast & ghostly lavender-ivory sails
    b.stamp(ctx, "knife", 0, 78, 86, 128, 5, Math.PI * 0.5, [104, 112, 148], 0.55, 0.2);
    for (let i = 0; i < 14; i++) {
      const y = lerp(34, 128, i / 13);
      const w = lerp(8, 52, i / 13);
      const col = jitterMonetColor([188, 184, 204], rng, 6, 6, 5);
      b.stamp(ctx, "broad", i % 3, 78 + w * 0.3, y, w, 14, 0.12, col, 0.42, 0.2);
    }
    // Hull
    b.stamp(ctx, "broad", 0, 80, 146, 86, 14, 0, [82, 88, 124], 0.68, 0.3);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    return c;
  }

  _buildHeroBoatSprite() {
    const c = document.createElement("canvas");
    c.width = 260; c.height = 104;
    const ctx = c.getContext("2d");
    const b = this.brushes;
    const rng = mulberry32(404);
    // Pointed wooden skiff hull silhouette (dark violet-umber + warm coral gunwale)
    for (let i = 0; i < 28; i++) {
      const u = i / 27;
      const px = lerp(24, 236, u);
      const pinch = Math.sin(u * Math.PI);
      const py = 62 - (1 - pinch) * 10;
      const h = 10 + pinch * 14;
      const col = jitterMonetColor(mixRgb([46, 42, 78], [98, 66, 74], u * 0.6), rng, 8, 8, 6);
      b.stamp(ctx, "broad", i % 3, px, py, 32, h, (u - 0.5) * 0.22, col, 0.94, 0.35);
    }
    // Sun-kissed coral-gold upper rim
    for (let i = 0; i < 14; i++) {
      const u = i / 13;
      const px = lerp(26, 234, u);
      const py = 50 - (1 - Math.sin(u * Math.PI)) * 10;
      b.stamp(ctx, "knife", i % 3, px, py, 28, 6.5, (u - 0.5) * 0.16, [232, 168, 128], 0.85, 0.45);
    }
    b.resetCtx(ctx);
    return c;
  }

  _initData() {
    const rng = mulberry32(501);
    // Foreground riverside reeds & cattails
    this.reeds = [];
    for (let i = 0; i < 140; i++) {
      const camAnchor = 350 + (i / 140) * 2350 + (rng() - 0.5) * 25;
      const depth = 1.22 + rng() * 0.18;
      this.reeds.push({
        ...worldAnchor(camAnchor, 0, depth, 0, 320 + rng() * 210),
        depth,
        h: 150 + rng() * 170,
        lean: (rng() - 0.45) * 0.25,
        phase: rng() * Math.PI * 2,
        hasCattail: rng() < 0.24,
        hueShift: rng(),
      });
    }

    // Portal 1: Dense, curved cascading Weeping Willow Curtain bridging Dawn River -> Giverny Pond
    this.willowCurtains = [];
    for (let i = 0; i < 84; i++) {
      const targetX = 2260 + (i / 83) * 720 + (rng() - 0.5) * 28;
      const depth = 1.32 + (i % 4) * 0.04;
      this.willowCurtains.push({
        ...worldAnchor(targetX, -10, depth, 0, -650 + (rng() - 0.5) * 120),
        depth,
        length: 860 + rng() * 480,
        curve: (rng() - 0.5) * 65,
        phase: rng() * Math.PI * 2,
        warmth: smoothstep(2300, 2920, targetX),
        dabs: 24 + Math.floor(rng() * 10),
      });
    }

    this.mistWisps = [];
    for (let i = 0; i < 28; i++) {
      this.mistWisps.push({
        wx: 350 + rng() * 2200,
        wy: 40 + rng() * 180,
        w: 220 + rng() * 280,
        h: 55 + rng() * 65,
        speed: 8 + rng() * 14,
        phase: rng() * Math.PI * 2,
      });
    }
  }

  render(ctx, cam, time, viewW, viewH, atmosphere) {
    // Active visibility window for Scene 1 + Portal 1 (vanishes cleanly behind willow curtain)
    if (cam.x > 3350) return;

    const b = this.brushes;
    b.resetCtx(ctx);
    const horizonY = worldToScreen(0, 62, 0.25, cam, viewW, viewH).y;

    // 1. Rising Sun (Impression, Sunrise!) clearly above the misty far bank
    const sunPos = worldToScreen(worldAnchor(1280, 0, 0.14).wx, -178, 0.14, cam, viewW, viewH);
    const sunVisible = smoothstep(3100, 2200, cam.x);
    if (sunVisible > 0.01) {
      ctx.save();
      ctx.globalAlpha = sunVisible;
      const halo = ctx.createRadialGradient(sunPos.x, sunPos.y, 10, sunPos.x, sunPos.y, 280 * sunPos.scale);
      halo.addColorStop(0, "rgba(255, 174, 102, 0.75)");
      halo.addColorStop(0.4, "rgba(255, 152, 114, 0.30)");
      halo.addColorStop(1, "rgba(255, 152, 114, 0)");
      ctx.fillStyle = halo;
      ctx.beginPath();
      ctx.arc(sunPos.x, sunPos.y, 280 * sunPos.scale, 0, Math.PI * 2);
      ctx.fill();

      const sr = 46 * sunPos.scale;
      for (let k = 0; k < 7; k++) {
        const a = (k / 7) * Math.PI * 2 + time * 0.05;
        b.stamp(ctx, "scumble", k % 3, sunPos.x + Math.cos(a) * sr * 0.24, sunPos.y + Math.sin(a) * sr * 0.24, sr * 1.65, sr * 1.35, a, [255, 134, 72], 0.72 * sunVisible, 0.35);
      }
      b.stamp(ctx, "scumble", 0, sunPos.x, sunPos.y, sr * 1.35, sr * 1.35, 0, [255, 198, 128], 0.78 * sunVisible, 0.3);
      ctx.restore();
    }

    // 2. Drifting Dawn Clouds
    b.resetCtx(ctx);
    const cloudDefs = [
      { idx: 0, wx: 360, wy: -275, depth: 0.18, speed: 6 },
      { idx: 1, wx: 890, wy: -325, depth: 0.20, speed: 9 },
      { idx: 2, wx: 1350, wy: -245, depth: 0.16, speed: 5 },
    ];
    for (const cl of cloudDefs) {
      const p = worldToScreen(cl.wx + time * cl.speed, cl.wy, cl.depth, cam, viewW, viewH);
      const spr = this.clouds[cl.idx];
      ctx.save();
      ctx.globalAlpha = 0.82 * sunVisible;
      ctx.drawImage(spr, p.x - spr.width * 0.5 * p.scale, p.y - spr.height * 0.5 * p.scale, spr.width * p.scale, spr.height * p.scale);
      ctx.restore();
    }

    // 3. Misty Far Seine Bank & Moored Sailboats (depth 0.34)
    b.resetCtx(ctx);
    const bankFade = smoothstep(3300, 2350, cam.x);
    if (bankFade > 0.01) {
      const bankPos = worldToScreen(worldAnchor(1350, 0, 0.34).wx - 1300, -195, 0.34, cam, viewW, viewH);
      ctx.save();
      ctx.globalAlpha = 0.88 * bankFade;
      ctx.drawImage(this.farBank, bankPos.x, bankPos.y, this.farBank.width * bankPos.scale, this.farBank.height * bankPos.scale);
      ctx.restore();
    }

    const mistBoats = [
      { targetCamX: 740, offsetX: -120, wy: -32, depth: 0.44, scale: 1.05 },
      { targetCamX: 1620, offsetX: 80, wy: -24, depth: 0.48, scale: 1.15 },
    ];
    for (const mb of mistBoats) {
      const a = worldAnchor(mb.targetCamX, 0, mb.depth, mb.offsetX, mb.wy);
      const p = worldToScreen(a.wx, a.wy, mb.depth, cam, viewW, viewH);
      const bob = Math.sin(time * 1.1 + mb.targetCamX) * 2.5;
      const bw = this.mistBoat.width * p.scale * mb.scale;
      const bh = this.mistBoat.height * p.scale * mb.scale;
      ctx.save();
      ctx.globalAlpha = 0.78 * bankFade;
      ctx.drawImage(this.mistBoat, p.x - bw * 0.5, p.y - bh * 0.82 + bob, bw, bh);
      ctx.restore();
    }

    // 4. Shimmering Animated Dawn River Surface (feathered smoothly on right edge at Portal 1)
    b.resetCtx(ctx);
    const waterTop = Math.round(horizonY + 18 * cam.zoom);
    const riverRight = worldToScreen(worldAnchor(2850, 0, 1.0).wx, 0, 1.0, cam, viewW, viewH).x;
    if (riverRight > 0 && bankFade > 0.01) {
      const rw = Math.min(viewW + 80, riverRight + 140);
      paintAnimatedWater(ctx, b, { x: -40, y: waterTop, w: rw, h: viewH - waterTop + 40 }, time, {
        baseColor: atmosphere.waterBase,
        deepColor: atmosphere.waterDeep,
        highlightColor: [232, 186, 174],
        sunColX: sunPos.x,
        sunColor: [255, 138, 76],
        reflectionBands: [
          { x: worldToScreen(worldAnchor(740, 0, 0.44, -120, 0).wx, 0, 0.44, cam, viewW, viewH).x, yTop: waterTop + 10, width: 65, height: 150, color: [116, 118, 152], waveAmp: 8, alpha: 0.58 },
          { x: worldToScreen(worldAnchor(1620, 0, 0.48, 80, 0).wx, 0, 0.48, cam, viewW, viewH).x, yTop: waterTop + 12, width: 72, height: 165, color: [110, 114, 148], waveAmp: 9, alpha: 0.58 },
        ],
        seed: 511,
        fadeRight: riverRight < viewW ? 240 : 0,
      });
    }

    // 5. Drifting Morning Mist Wisps over the Water
    for (let i = 0; i < this.mistWisps.length; i++) {
      const mw = this.mistWisps[i];
      const p = worldToScreen(mw.wx + time * mw.speed * 0.5, mw.wy, 0.72, cam, viewW, viewH);
      if (p.x < -300 || p.x > viewW + 300) continue;
      const alpha = (0.18 + 0.08 * Math.sin(time * 0.7 + mw.phase)) * smoothstep(3200, 2100, cam.x);
      b.stamp(ctx, "scumble", i % 3, p.x, p.y, mw.w * p.scale, mw.h * p.scale, 0, [224, 214, 228], alpha, 0.1);
    }

    // 6. Hero Wooden Skiff & Rowing Boatman (depth 0.85, gliding rightward through Scene 1)
    const boatWorldX = 820 + time * 42;
    const boatBob = Math.sin(time * 1.6) * 3.5;
    const boatPos = worldToScreen(boatWorldX, 195 + boatBob, 0.85, cam, viewW, viewH);
    if (boatPos.x > -300 && boatPos.x < viewW + 300) {
      const sc = boatPos.scale * 1.32;
      // Boat reflection in water
      b.stamp(ctx, "broad", 0, boatPos.x, boatPos.y + 34 * sc, 190 * sc, 24 * sc, 0, [68, 72, 116], 0.45, 0.2);

      // Expanding oar ripples behind/beside boat
      const strokeCycle = (time * 0.44) % 1;
      for (let r = 0; r < 2; r++) {
        const age = (strokeCycle + r * 0.5) % 1;
        const ripX = boatPos.x - 18 * sc - age * 36 * sc;
        const ripY = boatPos.y + 18 * sc;
        paintWaterRipple(ctx, b, ripX, ripY, (18 + age * 68) * sc, (5 + age * 17) * sc, [242, 188, 152], (1 - age) * 0.58, 700 + r);
      }

      // Hull (resetCtx ensures full opacity!)
      b.resetCtx(ctx);
      const hw = this.heroBoat.width * sc;
      const hh = this.heroBoat.height * sc;
      ctx.drawImage(this.heroBoat, boatPos.x - hw * 0.5, boatPos.y - hh * 0.55, hw, hh);

      // Boatman painted in Monet silhouette-violet & warm dawn rim-light + articulated rowing oar
      const rowPhase = Math.sin(time * 2.75);
      const leanX = rowPhase * 9 * sc;
      const bx = boatPos.x + 8 * sc;
      const by = boatPos.y - 12 * sc;
      // Cloak & torso
      b.stamp(ctx, "broad", 0, bx + leanX * 0.4, by - 22 * sc, 26 * sc, 36 * sc, -0.15 + leanX * 0.01, [54, 58, 96], 0.94, 0.35);
      // Warm dawn rim on shoulder/back
      b.stamp(ctx, "short", 1, bx + leanX * 0.4 + 6 * sc, by - 26 * sc, 16 * sc, 22 * sc, 0.2, [218, 148, 116], 0.7, 0.4);
      // Head & broad-brimmed French hat
      b.stamp(ctx, "short", 0, bx + leanX * 0.7, by - 46 * sc, 17 * sc, 18 * sc, 0, [58, 60, 98], 0.95, 0.3);
      b.stamp(ctx, "knife", 0, bx + leanX * 0.7, by - 53 * sc, 32 * sc, 9 * sc, -0.08, [68, 66, 106], 0.95, 0.35);
      b.stamp(ctx, "knife", 1, bx + leanX * 0.7 + 4 * sc, by - 55 * sc, 20 * sc, 5 * sc, -0.05, [224, 158, 122], 0.75, 0.4);
      // Animated wooden oar dipping into the river
      const oarTipX = bx - 38 * sc + Math.cos(time * 2.75) * 26 * sc;
      const oarTipY = boatPos.y + 18 * sc + Math.sin(time * 2.75) * 14 * sc;
      const oarAngle = Math.atan2(oarTipY - (by - 14 * sc), oarTipX - (bx + leanX * 0.3));
      const oarLen = Math.hypot(oarTipX - (bx + leanX * 0.3), oarTipY - (by - 14 * sc));
      b.stamp(ctx, "knife", 2, (bx + leanX * 0.3 + oarTipX) * 0.5, (by - 14 * sc + oarTipY) * 0.5, oarLen, 6 * sc, oarAngle, [136, 98, 88], 0.88, 0.3);
    }

    // 7. Pair of Graceful White Egrets lifting off at t=7.5s and flying into Scene 2!
    if (time > 6.5 && time < 21.5) {
      for (let e = 0; e < 2; e++) {
        const et = Math.max(0, time - 7.0 - e * 0.9);
        const exWorld = 1050 + et * 145;
        const eyWorld = 110 - Math.pow(et, 0.85) * 28 + Math.sin(time * 2.1 + e * 1.4) * 16;
        const ep = worldToScreen(exWorld, eyWorld, 0.92, cam, viewW, viewH);
        const flap = Math.sin(time * 7.8 + e * 1.7);
        const s = ep.scale * (1.0 - e * 0.14);
        // Body & graceful S-neck
        b.stamp(ctx, "curved", 0, ep.x, ep.y, 38 * s, 11 * s, -0.1, [246, 236, 230], 0.92, 0.4);
        b.stamp(ctx, "short", 1, ep.x + 18 * s, ep.y - 6 * s, 18 * s, 7 * s, -0.25, [252, 242, 232], 0.92, 0.4);
        // Trailing legs
        b.stamp(ctx, "knife", 0, ep.x - 24 * s, ep.y + 4 * s, 26 * s, 3.5 * s, 0.14, [134, 122, 148], 0.78, 0.2);
        // Articulated flapping wings (pale rose-white upper, cool lavender underwing)
        const wingAngle = flap * 0.85 - 0.35;
        b.stamp(ctx, "curved", 1, ep.x - 2 * s, ep.y - flap * 16 * s, 44 * s, 15 * s, wingAngle, [252, 240, 234], 0.9, 0.45);
        b.stamp(ctx, "curved", 2, ep.x + 2 * s, ep.y - flap * 11 * s, 34 * s, 11 * s, wingAngle * 0.75, [196, 198, 224], 0.75, 0.3);
      }
    }

    // 8. Foreground Riverside Reeds & Cattails (depth 1.22 - 1.40)
    for (let i = 0; i < this.reeds.length; i++) {
      const rd = this.reeds[i];
      const p = worldToScreen(rd.wx, rd.wy, rd.depth, cam, viewW, viewH);
      if (p.x < -80 || p.x > viewW + 80) continue;
      const sway = Math.sin(time * 1.45 + rd.phase + rd.wx * 0.005) * 14 * p.scale;
      const tipX = p.x + (rd.lean * rd.h + sway) * p.scale;
      const tipY = p.y - rd.h * p.scale;
      const midX = (p.x + tipX) * 0.5 + sway * 0.25;
      const midY = (p.y + tipY) * 0.5;
      const reedCol = mixRgb([44, 62, 88], [76, 98, 92], rd.hueShift);
      const ang = Math.atan2(tipY - p.y, tipX - p.x);
      b.stamp(ctx, "curved", i % 3, midX, midY, rd.h * p.scale * 1.05, 8.5 * p.scale, ang, reedCol, 0.85, 0.3);
      if (rd.hasCattail) {
        b.stamp(ctx, "short", 0, lerp(p.x, tipX, 0.76), lerp(p.y, tipY, 0.76), 24 * p.scale, 10 * p.scale, ang, [88, 56, 62], 0.92, 0.4);
      }
    }

    // 9. Portal 1: Lush Cascading Weeping Willow Curtain (bridges Scene 1 -> Scene 2 organically!)
    for (let i = 0; i < this.willowCurtains.length; i++) {
      const wc = this.willowCurtains[i];
      const p = worldToScreen(wc.wx, wc.wy, wc.depth, cam, viewW, viewH);
      if (p.x < -160 || p.x > viewW + 160) continue;

      const baseShadow = mixRgb([44, 72, 84], [38, 86, 62], wc.warmth);
      const baseMid = mixRgb([76, 118, 92], [86, 152, 74], wc.warmth);
      const baseTip = mixRgb([144, 174, 114], [186, 206, 94], wc.warmth);

      for (let d = 0; d < wc.dabs; d++) {
        const u = d / (wc.dabs - 1);
        const sway = Math.sin(time * 1.35 + wc.phase - u * 2.0) * (14 + u * 34) * p.scale;
        const arc = Math.sin(u * Math.PI * 0.85) * wc.curve * p.scale;
        const lx = p.x + sway + arc;
        const ly = p.y + u * wc.length * p.scale;
        const col = u < 0.35 ? baseShadow : u < 0.75 ? baseMid : baseTip;
        const ang = Math.PI * 0.5 + Math.cos(time * 1.2 + wc.phase - u) * 0.14 + (wc.curve * 0.0025);
        b.stamp(ctx, "curved", (i + d) % 3, lx, ly, (62 + (d % 3) * 14) * p.scale, (26 + (d % 2) * 8) * p.scale, ang, col, 0.90, 0.35);
      }
    }

    b.resetCtx(ctx);
  }
}

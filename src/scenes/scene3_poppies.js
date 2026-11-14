// Scene 3 (36s - 58s): Normandy Poppy Field, Woman with a Parasol, Child, Butterflies & Orchard Portal
import { mulberry32, clamp, lerp, smoothstep, fbm2D } from "../core/noise.js";
import { mixRgb, jitterMonetColor } from "../core/palette.js";
import { worldToScreen, worldAnchor } from "../core/camera.js";
import {
  createPainterlyCloudSprite,
  createHillTreelineSprite,
  createNormandyCottageSprite,
} from "../core/painter.js";

export class Scene3Poppies {
  constructor(brushes) {
    this.brushes = brushes;
    this._initSprites();
    this._initData();
  }

  _initSprites() {
    const b = this.brushes;
    // Billowing summer cumulus clouds (creamy sunlit tops, periwinkle shadows)
    this.clouds = [
      createPainterlyCloudSprite(b, 560, 220, [255, 252, 244], [156, 174, 218], 301),
      createPainterlyCloudSprite(b, 480, 190, [252, 248, 240], [164, 182, 222], 302),
      createPainterlyCloudSprite(b, 620, 230, [255, 250, 242], [150, 170, 216], 303),
    ];

    // Distant ridge with Normandy Lombardy poplars (wide enough to cover full frame)
    this.farRidge = createHillTreelineSprite(
      b, 3400, 380,
      [74, 134, 86],
      [164, 198, 102],
      [88, 114, 168],
      311,
      { treeDensity: 1.05, poplars: true, hazeAlpha: 0.22 }
    );

    // Normandy Cottages on the distant hill crest
    this.cottage1 = createNormandyCottageSprite(b, 240, 170, 321);
    this.cottage2 = createNormandyCottageSprite(b, 200, 150, 322);

    // Pre-painted rolling poppy meadow canvas base (world-anchored broad strokes!)
    this.meadowBase = this._buildMeadowBaseSprite();
  }

  _buildMeadowBaseSprite() {
    const w = 3100, h = 900;
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    const ctx = c.getContext("2d");
    const b = this.brushes;
    const rng = mulberry32(333);

    const hillTop = (x) => 130 + Math.sin(x * 0.0021) * 58 + fbm2D(x * 0.0018, 0.5, 3, 334) * 70;

    // 1. Winding ochre footpath curve through the meadow
    const pathCenter = (x) => {
      const u = x / w;
      return 340 + Math.sin(u * Math.PI * 1.4 - 0.3) * 115;
    };

    // 2. Solid feathered meadow underpainting (zero pinholes, zero rectangular cutoffs!)
    const stripW = 24;
    for (let x = 0; x < w; x += stripW) {
      const edgeFade = smoothstep(0, 340, x) * smoothstep(w, w - 340, x);
      if (edgeFade < 0.01) continue;
      const topY = hillTop(x);
      ctx.save();
      ctx.globalAlpha = edgeFade;
      const g = ctx.createLinearGradient(0, topY - 12, 0, h);
      g.addColorStop(0, "rgba(128, 174, 82, 0)");
      g.addColorStop(0.06, "rgba(116, 168, 82, 0.96)");
      g.addColorStop(0.55, "rgba(78, 146, 74, 0.98)");
      g.addColorStop(1, "rgba(58, 112, 86, 1)");
      ctx.fillStyle = g;
      ctx.fillRect(x, topY - 12, stripW + 1, h - topY + 12);
      ctx.restore();
    }

    // 3. Layered jittered directional grass & footpath strokes across the slope
    for (let y = 78; y < h; y += 19) {
      const v = clamp((y - 78) / (h - 78), 0, 1);
      for (let x = 20; x < w - 20; x += 24) {
        const edgeFade = smoothstep(0, 340, x) * smoothstep(w, w - 340, x);
        if (edgeFade < 0.02) continue;
        const topY = hillTop(x);
        const topFade = smoothstep(topY - 8, topY + 26, y);
        if (topFade < 0.02) continue;

        const pc = pathCenter(x);
        const distPath = Math.abs(y - pc);
        const onPath = distPath < lerp(26, 72, v);

        let baseCol;
        if (onPath) {
          baseCol = distPath > lerp(18, 48, v)
            ? [164, 146, 158]
            : [226, 198, 150];
        } else {
          const sunPatch = fbm2D(x * 0.003, y * 0.004, 3, 335);
          const colA = [58, 132, 70];
          const colB = [164, 202, 84];
          baseCol = mixRgb(colA, colB, clamp(0.45 + sunPatch * 0.55, 0, 1));
          if (v > 0.72) baseCol = mixRgb(baseCol, [56, 108, 90], (v - 0.72) * 0.6);
        }
        const col = jitterMonetColor(baseCol, rng, 12, 11, 8);
        const len = lerp(34, 70, v);
        const thick = lerp(15, 28, v);
        b.stamp(ctx, "broad", (x + y) % 3, x + (rng() - 0.5) * 18, y + (rng() - 0.5) * 14, len, thick, -0.22 + (rng() - 0.5) * 0.34, col, 0.84 * edgeFade * topFade, 0.3);
      }
    }

    b.resetCtx(ctx);
    return c;
  }

  _initData() {
    const rng = mulberry32(360);

    // Swaying grass tufts & wind-wave blades across the hero hillside
    this.windBlades = [];
    for (let i = 0; i < 240; i++) {
      const targetX = 5350 + rng() * 2550;
      const depth = 0.86 + rng() * 0.30;
      const wy = -125 + rng() * 520;
      this.windBlades.push({
        ...worldAnchor(targetX, -145, depth, 0, wy),
        depth,
        scale: lerp(0.55, 1.35, (wy + 125) / 520),
        phase: rng() * Math.PI * 2,
        warm: rng(),
      });
    }

    // Over 280 Scarlet/Vermilion/Coral Poppies + Wildflowers scattered artistically
    this.poppies = [];
    for (let i = 0; i < 285; i++) {
      const targetX = 5280 + rng() * 2650;
      const depth = 0.82 + rng() * 0.36;
      const wy = -85 + Math.pow(rng(), 0.78) * 490;
      const sc = lerp(0.52, 1.75, (wy + 85) / 490);
      const isPoppy = rng() < 0.75;
      const col = isPoppy
        ? (rng() < 0.55 ? [226, 48, 44] : rng() < 0.82 ? [244, 84, 54] : [196, 36, 62])
        : (rng() < 0.5 ? [248, 214, 78] : [156, 128, 212]);
      this.poppies.push({
        ...worldAnchor(targetX, -145, depth, 0, wy),
        depth,
        scale: sc,
        color: col,
        isPoppy,
        phase: rng() * Math.PI * 2,
      });
    }
    this.poppies.sort((a, b) => a.depth - b.depth);

    // Fluttering white & sulfur-yellow butterflies around the child & poppies
    this.butterflies = [];
    for (let i = 0; i < 14; i++) {
      this.butterflies.push({
        baseWx: 6050 + rng() * 1180,
        baseWy: -45 + rng() * 230,
        phase: rng() * Math.PI * 2,
        speed: 0.9 + rng() * 0.9,
        color: rng() < 0.65 ? [255, 250, 236] : [252, 232, 126],
      });
    }

    // Wind-borne drifting poppy petals & dandelion seeds
    this.petals = [];
    for (let i = 0; i < 36; i++) {
      this.petals.push({
        wx: 5500 + rng() * 2300,
        wy: -350 + rng() * 550,
        speedX: 38 + rng() * 34,
        speedY: -12 + rng() * 24,
        phase: rng() * Math.PI * 2,
        isPetal: rng() < 0.65,
      });
    }

    // Portal 3: Lush Overhead Normandy Orchard Canopies & Low Gnarled Hillside Trees (zero vertical sky poles!)
    this.orchardCanopies = [];
    for (let t = 0; t < 38; t++) {
      const targetX = 7580 + (t / 37) * 780 + (rng() - 0.5) * 40;
      const targetY = lerp(-134, -82, smoothstep(7580, 8360, targetX));
      const depth = 1.32 + (t % 4) * 0.04;
      const leafT = smoothstep(7580, 8360, targetX);
      // Frame transition organically: overhanging top canopies reaching down from above top edge + hillside orchard bushes
      const isTopCanopy = t % 3 !== 2;
      const crownOffY = isTopCanopy ? -540 + rng() * 380 : 120 + rng() * 280;
      const crownOffX = (rng() - 0.5) * 140;

      const leaves = [];
      for (let lf = 0; lf < 28; lf++) {
        const a = rng() * Math.PI * 2;
        const r = Math.pow(rng(), 0.72);
        const lx = crownOffX + Math.cos(a) * (82 + rng() * 48) * r;
        const ly = crownOffY + Math.sin(a) * (72 + rng() * 44) * r;
        leaves.push({
          ...worldAnchor(targetX, targetY, depth, lx, ly),
          size: 38 + rng() * 26,
          angle: a + (rng() - 0.5) * 1.1,
          shade: rng(),
          hasBlossom: rng() < 0.08,
          phase: rng() * Math.PI * 2,
        });
      }

      // Only add low crooked trunks for hillside shrubs anchored into the meadow ground
      const trunk = !isTopCanopy && t % 6 === 2
        ? {
            base: worldAnchor(targetX, targetY, depth, crownOffX - 18, crownOffY + 180),
            crown: worldAnchor(targetX, targetY, depth, crownOffX, crownOffY + 10),
          }
        : null;

      this.orchardCanopies.push({
        depth,
        leafT,
        trunk,
        leaves,
        phase: rng() * Math.PI * 2,
      });
    }
  }

  _drawWomanWithParasol(ctx, b, wx, wy, sc, time) {
    // Classic Monet "Woman with a Parasol" on sunlit hillside crest (crisp sculpted brushwork)
    const gust = Math.sin(time * 2.1) * 7 + Math.sin(time * 3.7) * 2.5;
    const walkBob = Math.abs(Math.sin(time * 2.2)) * 2.5 * sc;
    const y = wy - walkBob;

    // Ground cast shadow (cool Monet violet-cobalt!)
    b.stamp(ctx, "scumble", 0, wx - 40 * sc, wy + 7 * sc, 114 * sc, 24 * sc, -0.08, [74, 88, 158], 0.52, 0.15);

    // Billowing skirt strokes (periwinkle-cobalt shadow on left, crisp sunlit cream-ivory folds on right)
    const skirtSway = gust * 0.9 * sc;
    b.stamp(ctx, "broad", 0, wx - 13 * sc + skirtSway * 0.4, y - 50 * sc, 44 * sc, 72 * sc, 0.20, [118, 144, 206], 0.96, 0.42);
    b.stamp(ctx, "broad", 1, wx + 6 * sc + skirtSway * 0.25, y - 52 * sc, 40 * sc, 72 * sc, -0.08, [242, 238, 224], 0.97, 0.48);
    b.stamp(ctx, "short", 2, wx - 22 * sc + skirtSway * 0.85, y - 20 * sc, 48 * sc, 24 * sc, 0.12, [196, 208, 234], 0.94, 0.42);
    b.stamp(ctx, "knife", 0, wx + 18 * sc, y - 46 * sc, 48 * sc, 9 * sc, -1.42, [255, 250, 212], 0.95, 0.52);
    b.stamp(ctx, "knife", 1, wx + 4 * sc, y - 48 * sc, 44 * sc, 7 * sc, -1.48, [142, 166, 216], 0.72, 0.4);

    // Torso / bodice in cool lilac-blue shade beneath the parasol
    b.stamp(ctx, "short", 0, wx + 1 * sc, y - 98 * sc, 24 * sc, 32 * sc, 0.04, [138, 158, 210], 0.96, 0.4);
    b.stamp(ctx, "short", 1, wx + 9 * sc, y - 98 * sc, 14 * sc, 24 * sc, -0.08, [248, 242, 226], 0.94, 0.45);

    // Fluttering sheer scarf / veil blowing left in the breeze
    b.stamp(ctx, "knife", 2, wx - 26 * sc + skirtSway * 1.1, y - 116 * sc, 44 * sc, 9 * sc, -0.16 + Math.sin(time * 4.0) * 0.1, [248, 248, 255], 0.88, 0.35);

    // Head, facial warmth & Straw Bonnet with cobalt-blue ribbon
    b.stamp(ctx, "short", 2, wx + 2 * sc, y - 126 * sc, 16 * sc, 18 * sc, 0, [218, 184, 174], 0.97, 0.35);
    b.stamp(ctx, "knife", 1, wx + 1 * sc, y - 135 * sc, 32 * sc, 9 * sc, -0.16, [238, 212, 148], 0.97, 0.45);
    b.stamp(ctx, "knife", 0, wx + 2 * sc, y - 138 * sc, 18 * sc, 5 * sc, -0.14, [96, 134, 198], 0.92, 0.4);

    // Arm holding parasol handle
    b.stamp(ctx, "knife", 0, wx + 14 * sc, y - 112 * sc, 34 * sc, 6.5 * sc, -1.12, [146, 160, 206], 0.94, 0.35);

    // Translucent Sunlit Parasol (cool sage-teal interior shade, sculpted warm ivory dome, gold rim!)
    const px = wx + 20 * sc;
    const py = y - 168 * sc;
    const tilt = -0.30 + Math.sin(time * 1.6) * 0.04;
    b.stamp(ctx, "knife", 2, px - 5 * sc, py + 28 * sc, 72 * sc, 4.5 * sc, tilt + Math.PI * 0.5, [104, 84, 76], 0.95, 0.35);
    b.stamp(ctx, "curved", 0, px - 3 * sc, py + 5 * sc, 94 * sc, 28 * sc, tilt + Math.PI, [112, 168, 156], 0.94, 0.35);
    b.stamp(ctx, "curved", 1, px, py - 6 * sc, 98 * sc, 34 * sc, tilt + Math.PI, [248, 242, 212], 0.97, 0.48);
    b.stamp(ctx, "knife", 0, px + 6 * sc, py - 14 * sc, 64 * sc, 10 * sc, tilt, [255, 250, 224], 0.94, 0.52);
  }

  _drawChild(ctx, b, wx, wy, sc, time) {
    const hop = Math.abs(Math.sin(time * 3.1 + 1.0)) * 4 * sc;
    const y = wy - hop;
    b.stamp(ctx, "scumble", 0, wx - 16 * sc, wy + 6 * sc, 50 * sc, 16 * sc, 0, [78, 92, 160], 0.48, 0.15);
    b.stamp(ctx, "short", 0, wx, y - 24 * sc, 26 * sc, 34 * sc, 0.1, [122, 156, 214], 0.95, 0.35);
    b.stamp(ctx, "short", 1, wx + 4 * sc, y - 52 * sc, 26 * sc, 30 * sc, -0.05, [244, 236, 218], 0.95, 0.4);
    b.stamp(ctx, "knife", 0, wx + 18 * sc, y - 68 * sc, 26 * sc, 7.5 * sc, -0.75 + Math.sin(time * 4.5) * 0.18, [238, 210, 184], 0.94, 0.3);
    b.stamp(ctx, "short", 2, wx + 2 * sc, y - 74 * sc, 17 * sc, 17 * sc, 0, [236, 198, 174], 0.95, 0.3);
    b.stamp(ctx, "knife", 1, wx + 2 * sc, y - 82 * sc, 40 * sc, 12 * sc, -0.1, [248, 220, 132], 0.96, 0.45);
  }

  render(ctx, cam, time, viewW, viewH, atmosphere) {
    if (cam.x < 4550 || cam.x > 8900) return;

    const b = this.brushes;
    b.resetCtx(ctx);
    const sceneAlpha = smoothstep(4650, 5450, cam.x) * smoothstep(8550, 7700, cam.x);

    // 1. Billowing Afternoon Cumulus Clouds (positioned cleanly off-axis from the parasol!)
    const cloudDefs = [
      { idx: 0, targetCamX: 5900, wy: -395, depth: 0.18, speed: 9 },
      { idx: 1, targetCamX: 6260, wy: -390, depth: 0.20, speed: 12 },
      { idx: 2, targetCamX: 7450, wy: -410, depth: 0.17, speed: 7 },
    ];
    for (const cl of cloudDefs) {
      const anc = worldAnchor(cl.targetCamX, -145, cl.depth);
      const p = worldToScreen(anc.wx + time * cl.speed * 0.4, cl.wy, cl.depth, cam, viewW, viewH);
      const spr = this.clouds[cl.idx];
      ctx.save();
      ctx.globalAlpha = 0.88 * sceneAlpha;
      ctx.drawImage(spr, p.x - spr.width * 0.5 * p.scale, p.y - spr.height * 0.5 * p.scale, spr.width * p.scale, spr.height * p.scale);
      ctx.restore();
    }

    // 2. Distant Hillside Ridge & Normandy Cottages tucked neatly to the flanks (depth 0.44 - 0.48)
    b.resetCtx(ctx);
    if (sceneAlpha > 0.01) {
      ctx.save();
      ctx.globalAlpha = sceneAlpha;
      const ridgeAnc = worldAnchor(6600, -145, 0.44);
      const ridgePos = worldToScreen(ridgeAnc.wx - 1700, ridgeAnc.wy - 220, 0.44, cam, viewW, viewH);
      ctx.drawImage(this.farRidge, ridgePos.x, ridgePos.y, this.farRidge.width * ridgePos.scale, this.farRidge.height * ridgePos.scale);

      const cot1Anc = worldAnchor(5860, -145, 0.48, 0, -152);
      const cot1Pos = worldToScreen(cot1Anc.wx, cot1Anc.wy, 0.48, cam, viewW, viewH);
      ctx.drawImage(this.cottage1, cot1Pos.x, cot1Pos.y, this.cottage1.width * cot1Pos.scale, this.cottage1.height * cot1Pos.scale);

      const cot2Anc = worldAnchor(7440, -145, 0.47, 0, -156);
      const cot2Pos = worldToScreen(cot2Anc.wx, cot2Anc.wy, 0.47, cam, viewW, viewH);
      ctx.drawImage(this.cottage2, cot2Pos.x, cot2Pos.y, this.cottage2.width * cot2Pos.scale, this.cottage2.height * cot2Pos.scale);

      // 3. Rolling Sunlit Poppy Meadow Base (depth 0.86)
      const mAnc = worldAnchor(6600, -145, 0.86);
      const mPos = worldToScreen(mAnc.wx - 1550, mAnc.wy - 190, 0.86, cam, viewW, viewH);
      ctx.drawImage(this.meadowBase, mPos.x, mPos.y, this.meadowBase.width * mPos.scale, this.meadowBase.height * mPos.scale);
      ctx.restore();
    }

    // 4. Traveling Wind Waves across Meadow Grass Blades
    for (let i = 0; i < this.windBlades.length; i++) {
      const wb = this.windBlades[i];
      const p = worldToScreen(wb.wx, wb.wy, wb.depth, cam, viewW, viewH);
      if (p.x < -80 || p.x > viewW + 80) continue;
      const gust = Math.sin(wb.wx * 0.0055 - time * 2.5 + wb.phase * 0.25);
      const lean = 0.25 + gust * 0.28;
      const col = mixRgb([68, 144, 72], [184, 214, 92], clamp(0.4 + gust * 0.35 + wb.warm * 0.25, 0, 1));
      b.stamp(ctx, "curved", i % 3, p.x + gust * 6 * p.scale, p.y, 44 * p.scale * wb.scale, 15 * p.scale * wb.scale, -Math.PI * 0.5 + lean, col, 0.72 * sceneAlpha, 0.3);
    }

    // 5. Hero Characters Walking Slowly Along the Sunlit Path (depth 0.90)
    const walkOffset = (time - 45) * 14;
    const womanAnc = worldAnchor(6610, -145, 0.90, walkOffset, 32);
    const womanPos = worldToScreen(womanAnc.wx, womanAnc.wy, 0.90, cam, viewW, viewH);
    if (womanPos.x > -240 && womanPos.x < viewW + 240) {
      this._drawWomanWithParasol(ctx, b, womanPos.x, womanPos.y, womanPos.scale * 1.62, time);
    }

    const childAnc = worldAnchor(6850, -145, 0.92, walkOffset * 1.15, 102);
    const childPos = worldToScreen(childAnc.wx, childAnc.wy, 0.92, cam, viewW, viewH);
    if (childPos.x > -180 && childPos.x < viewW + 180) {
      this._drawChild(ctx, b, childPos.x, childPos.y, childPos.scale * 1.48, time);
    }

    // 6. Swaying Scarlet Poppies & Wildflowers (depth 0.82 - 1.18)
    for (let i = 0; i < this.poppies.length; i++) {
      const pp = this.poppies[i];
      const p = worldToScreen(pp.wx, pp.wy, pp.depth, cam, viewW, viewH);
      if (p.x < -70 || p.x > viewW + 70) continue;
      const gust = Math.sin(pp.wx * 0.0055 - time * 2.5 + pp.phase * 0.3);
      const swayX = gust * 9 * p.scale * pp.scale;
      const sc = p.scale * pp.scale;

      b.stamp(ctx, "knife", 0, p.x + swayX * 0.4, p.y - 12 * sc, 26 * sc, 3.8 * sc, -Math.PI * 0.5 + gust * 0.25, [76, 128, 66], 0.84 * sceneAlpha, 0.2);

      const bx = p.x + swayX;
      const by = p.y - 24 * sc;
      if (pp.isPoppy) {
        b.stamp(ctx, "short", i % 4, bx - 4.5 * sc, by, 19 * sc, 14 * sc, -0.35, pp.color, 0.94 * sceneAlpha, 0.45);
        b.stamp(ctx, "short", (i + 1) % 4, bx + 4.5 * sc, by - 2 * sc, 17 * sc, 13 * sc, 0.35, mixRgb(pp.color, [255, 152, 96], 0.35), 0.92 * sceneAlpha, 0.45);
        b.stamp(ctx, "short", 0, bx, by + 1 * sc, 6.5 * sc, 5.5 * sc, 0, [46, 30, 68], 0.9 * sceneAlpha, 0.3);
      } else {
        b.stamp(ctx, "short", i % 4, bx, by, 15 * sc, 12 * sc, 0.2, pp.color, 0.92 * sceneAlpha, 0.4);
      }
    }

    // 7. Fluttering Cabbage Butterflies dancing over the meadow
    for (let i = 0; i < this.butterflies.length; i++) {
      const bf = this.butterflies[i];
      const bx = bf.baseWx + Math.sin(time * bf.speed + bf.phase) * 95 + Math.cos(time * 0.5 + i) * 45;
      const by = bf.baseWy + Math.cos(time * bf.speed * 1.4 + bf.phase) * 38;
      const p = worldToScreen(bx, by, 0.96, cam, viewW, viewH);
      if (p.x < -50 || p.x > viewW + 50) continue;
      const flap = Math.abs(Math.sin(time * 14 + i * 2.1));
      const s = p.scale;
      b.stamp(ctx, "short", 0, p.x - 5 * s * flap, p.y - 4 * s, 15 * s, 10 * s * (0.35 + 0.65 * flap), -0.5, bf.color, 0.95, 0.3);
      b.stamp(ctx, "short", 1, p.x + 5 * s * flap, p.y - 4 * s, 15 * s, 10 * s * (0.35 + 0.65 * flap), 0.5, bf.color, 0.95, 0.3);
    }

    // 8. Wind-borne Drifting Poppy Petals & Dandelion Seeds
    for (let i = 0; i < this.petals.length; i++) {
      const pt = this.petals[i];
      const px = ((pt.wx + time * pt.speedX - 5300) % 2800) + 5300;
      const py = pt.wy + Math.sin(time * 1.8 + pt.phase) * 32 + time * pt.speedY * 0.3;
      const p = worldToScreen(px, py, 1.15, cam, viewW, viewH);
      if (p.x < -40 || p.x > viewW + 40) continue;
      const rot = time * 2.4 + pt.phase;
      if (pt.isPetal) {
        b.stamp(ctx, "short", i % 4, p.x, p.y, 13 * p.scale, 8 * p.scale, rot, [238, 72, 62], 0.82, 0.3);
      } else {
        b.stamp(ctx, "scumble", 0, p.x, p.y, 12 * p.scale, 12 * p.scale, rot, [255, 250, 232], 0.68, 0.1);
      }
    }

    // 9. Portal 3: Lush Overhead Normandy Orchard Canopies & Copper-Gold Foliage (bridges Poppy Field -> Haystacks!)
    for (let t = 0; t < this.orchardCanopies.length; t++) {
      const tree = this.orchardCanopies[t];
      if (tree.trunk) {
        const pb = worldToScreen(tree.trunk.base.wx, tree.trunk.base.wy, tree.depth, cam, viewW, viewH);
        const pc = worldToScreen(tree.trunk.crown.wx, tree.trunk.crown.wy, tree.depth, cam, viewW, viewH);
        if (pc.x > -240 && pc.x < viewW + 240) {
          const sway = Math.sin(time * 1.1 + tree.phase) * 7 * pc.scale;
          const dx = (pc.x + sway) - pb.x;
          const dy = pc.y - pb.y;
          const len = Math.hypot(dx, dy);
          const boughCol = mixRgb([76, 62, 74], [96, 68, 66], tree.leafT);
          b.stamp(ctx, "curved", t % 3, (pb.x + pc.x + sway) * 0.5, (pb.y + pc.y) * 0.5, len * 1.05, 22 * pc.scale, Math.atan2(dy, dx), boughCol, 0.88, 0.3);
        }
      }

      for (let i = 0; i < tree.leaves.length; i++) {
        const lf = tree.leaves[i];
        const p = worldToScreen(lf.wx, lf.wy, tree.depth, cam, viewW, viewH);
        if (p.x < -120 || p.x > viewW + 120) continue;
        const lSway = Math.sin(time * 1.4 + lf.phase) * 7 * p.scale;
        const coolGreen = lf.shade < 0.4 ? [48, 108, 62] : lf.shade < 0.75 ? [74, 134, 72] : [136, 176, 82];
        const warmAmber = lf.shade < 0.4 ? [146, 94, 58] : lf.shade < 0.75 ? [196, 138, 64] : [236, 184, 84];
        const col = mixRgb(coolGreen, warmAmber, tree.leafT);
        b.stamp(ctx, "short", i % 4, p.x + lSway, p.y, lf.size * p.scale, lf.size * 0.66 * p.scale, lf.angle, col, 0.9, 0.35);
        if (lf.hasBlossom) {
          b.stamp(ctx, "short", 0, p.x + lSway, p.y - 4 * p.scale, lf.size * 0.42 * p.scale, lf.size * 0.36 * p.scale, 0.2, [255, 226, 188], 0.92, 0.45);
        }
      }
    }

    b.resetCtx(ctx);
  }
}

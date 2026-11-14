// High-Craft Monet Impressionist Painterly Builders & Dynamic Element Renderers
import { mulberry32, clamp, lerp, smoothstep, fbm2D } from "./noise.js";
import { mixRgb, jitterMonetColor, monetShadow, monetHighlight } from "./palette.js";

// Paint a complete Impressionist sky strip + swirling multi-tone clouds onto a target canvas
export function paintMonetSkyLayer(ctx, brushes, w, h, atmosphere, seed = 101) {
  const rng = mulberry32(seed);
  // 1. Soft underpainting wash
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, `rgb(${atmosphere.skyTop.map(Math.round).join(",")})`);
  grad.addColorStop(0.56, `rgb(${atmosphere.skyMid.map(Math.round).join(",")})`);
  grad.addColorStop(1, `rgb(${atmosphere.skyHorizon.map(Math.round).join(",")})`);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, w, h);

  // 2. Broad criss-cross Monet sky brushstrokes (atmospheric air vibration)
  const stepX = 34;
  const stepY = 24;
  for (let y = 10; y < h * 0.96; y += stepY) {
    const v = y / h;
    const base = v < 0.56
      ? mixRgb(atmosphere.skyTop, atmosphere.skyMid, v / 0.56)
      : mixRgb(atmosphere.skyMid, atmosphere.skyHorizon, (v - 0.56) / 0.44);
    for (let x = 10; x < w; x += stepX) {
      const n = fbm2D(x * 0.004, y * 0.006, 3, seed);
      const col = jitterMonetColor(base, rng, 11, 10, 8);
      const angle = (n * 0.35) + (rng() - 0.5) * 0.25;
      const len = 58 + rng() * 44;
      const thick = 22 + rng() * 14;
      brushes.stamp(ctx, "broad", Math.floor(rng() * 3), x + (rng() - 0.5) * 18, y + (rng() - 0.5) * 12, len, thick, angle, col, 0.44 + rng() * 0.2, 0.25);
    }
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}

// Create a pre-painted painterly cloud sprite (billowing sunlit top + lavender-blue shadow belly)
export function createPainterlyCloudSprite(brushes, width, height, topColor, shadowColor, seed) {
  const c = document.createElement("canvas");
  c.width = width;
  c.height = height;
  const ctx = c.getContext("2d");
  const rng = mulberry32(seed);

  const cx = width * 0.5;
  const cy = height * 0.55;
  const lobes = 6 + Math.floor(rng() * 4);

  for (let i = 0; i < lobes; i++) {
    const t = i / (lobes - 1);
    const lx = lerp(width * 0.18, width * 0.82, t) + (rng() - 0.5) * width * 0.08;
    const arch = Math.sin(t * Math.PI);
    const ly = cy - arch * height * 0.22 + (rng() - 0.5) * height * 0.08;
    const rx = width * (0.14 + arch * 0.12);
    const ry = height * (0.18 + arch * 0.14);

    // Shadow underbelly strokes
    for (let s = 0; s < 14; s++) {
      const a = rng() * Math.PI;
      const r = rng() * 0.85;
      const px = lx + Math.cos(a) * rx * r;
      const py = ly + Math.sin(a) * ry * r * 0.75 + ry * 0.22;
      const col = jitterMonetColor(shadowColor, rng, 10, 12, 8);
      brushes.stamp(ctx, "scumble", Math.floor(rng() * 3), px, py, 52 + rng() * 36, 30 + rng() * 18, (rng() - 0.5) * 0.4, col, 0.46 + rng() * 0.18, 0.2);
    }

    // Sunlit billowing top strokes
    for (let s = 0; s < 18; s++) {
      const a = -rng() * Math.PI;
      const r = rng() * 0.9;
      const px = lx + Math.cos(a) * rx * r;
      const py = ly + Math.sin(a) * ry * r - ry * 0.12;
      const col = jitterMonetColor(topColor, rng, 8, 9, 7);
      brushes.stamp(ctx, "curved", Math.floor(rng() * 3), px, py, 44 + rng() * 32, 22 + rng() * 14, (rng() - 0.5) * 0.5, col, 0.55 + rng() * 0.22, 0.35);
    }
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  return c;
}

// Create a pre-painted distant Impressionist treeline / hillside ridge strip (horizontally feathered!)
export function createHillTreelineSprite(brushes, w, h, baseGreen, highlightGreen, shadowTint, seed, options = {}) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d");
  const rng = mulberry32(seed);
  const { treeDensity = 1.0, poplars = false, hazeAlpha = 0.0 } = options;

  const ridgeY = (x) => {
    const n1 = fbm2D(x * 0.0022, 1.3, 3, seed);
    const n2 = Math.sin(x * 0.0045 + seed) * 0.09;
    return h * (0.58 + n1 * 0.16 + n2);
  };

  // Fill hillside base with directional grass/foliage strokes (feathered at left/right edges)
  for (let x = 20; x < w - 20; x += 22) {
    const edgeFade = smoothstep(0, 260, x) * smoothstep(w, w - 260, x);
    if (edgeFade < 0.02) continue;
    const topY = ridgeY(x);
    for (let y = topY; y < h - 10; y += 16) {
      const v = (y - topY) / Math.max(1, h - topY);
      const botFade = smoothstep(h, h - 42, y);
      const base = mixRgb(highlightGreen, baseGreen, smoothstep(0, 0.6, v));
      const shaded = mixRgb(base, shadowTint, v * 0.28 + hazeAlpha);
      const col = jitterMonetColor(shaded, rng, 12, 10, 8);
      brushes.stamp(ctx, "broad", Math.floor(rng() * 3), x + (rng() - 0.5) * 14, y + (rng() - 0.5) * 10, 46 + rng() * 26, 22 + rng() * 10, -0.15 + (rng() - 0.5) * 0.4, col, 0.74 * edgeFade * botFade, 0.25);
    }
  }

  // Painted Impressionist tree clusters along the ridge
  const treeStep = Math.round(60 / treeDensity);
  for (let x = 80; x < w - 80; x += treeStep + Math.floor(rng() * 32)) {
    const edgeFade = smoothstep(40, 280, x) * smoothstep(w - 40, w - 280, x);
    if (edgeFade < 0.05) continue;
    const gy = ridgeY(x);
    const isPoplar = poplars && rng() < 0.38;
    const tw = isPoplar ? 36 + rng() * 22 : 68 + rng() * 54;
    const rawTh = isPoplar ? 105 + rng() * 55 : 62 + rng() * 48;
    const th = Math.min(rawTh, Math.max(36, gy - 20));
    const cy = gy - th * 0.48;

    const trunkCol = jitterMonetColor(mixRgb([86, 68, 56], shadowTint, 0.5), rng, 8, 8, 6);
    brushes.stamp(ctx, "knife", 0, x, gy - th * 0.15, th * 0.45, 7, Math.PI * 0.5 + (rng() - 0.5) * 0.1, trunkCol, 0.65 * edgeFade, 0.2);

    const count = isPoplar ? 28 : 34;
    for (let k = 0; k < count; k++) {
      const ang = rng() * Math.PI * 2;
      const rad = Math.pow(rng(), 0.6);
      const dx = Math.cos(ang) * tw * 0.5 * rad;
      const dy = Math.sin(ang) * th * 0.5 * rad;
      const sunFactor = clamp(0.5 + (dx / tw) * 0.6 - (dy / th) * 0.5, 0, 1);
      let col = mixRgb(monetShadow(baseGreen, shadowTint, 0.52), highlightGreen, sunFactor);
      if (hazeAlpha > 0) col = mixRgb(col, shadowTint, hazeAlpha * 0.45);
      col = jitterMonetColor(col, rng, 14, 12, 9);
      const strokeAngle = isPoplar ? -Math.PI * 0.5 + (rng() - 0.5) * 0.4 : (rng() - 0.5) * 1.4;
      brushes.stamp(ctx, "short", Math.floor(rng() * 4), x + dx, cy + dy, 24 + rng() * 18, 13 + rng() * 8, strokeAngle, col, (0.72 + rng() * 0.2) * edgeFade, 0.35);
    }
  }
  brushes.resetCtx(ctx);
  return c;
}

// Create an authentic Monet Normandy Cottage sprite (stone walls with violet shadows, terracotta roof, poplars)
export function createNormandyCottageSprite(brushes, w, h, seed) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d");
  const rng = mulberry32(seed);

  const bx = w * 0.24, bw = w * 0.52;
  const by = h * 0.46, bh = h * 0.42;

  for (let i = 0; i < 42; i++) {
    const px = bx + rng() * bw * 0.62;
    const py = by + rng() * bh;
    const col = jitterMonetColor([238, 226, 198], rng, 8, 8, 8);
    brushes.stamp(ctx, "short", Math.floor(rng() * 4), px, py, 26 + rng() * 16, 13 + rng() * 7, (rng() - 0.5) * 0.2, col, 0.88, 0.3);
  }
  for (let i = 0; i < 32; i++) {
    const px = bx + bw * 0.58 + rng() * bw * 0.42;
    const py = by + rng() * bh;
    const col = jitterMonetColor([158, 152, 184], rng, 10, 10, 8);
    brushes.stamp(ctx, "short", Math.floor(rng() * 4), px, py, 24 + rng() * 14, 12 + rng() * 6, (rng() - 0.5) * 0.2, col, 0.88, 0.3);
  }
  for (let i = 0; i < 46; i++) {
    const u = rng();
    const rx = lerp(bx - 12, bx + bw + 10, u);
    const roofTop = by - h * 0.24;
    const ry = lerp(roofTop, by + 6, rng());
    const baseRoof = u < 0.62 ? [196, 104, 78] : [132, 82, 98];
    const col = jitterMonetColor(baseRoof, rng, 10, 10, 8);
    brushes.stamp(ctx, "broad", Math.floor(rng() * 3), rx, ry, 28 + rng() * 16, 12 + rng() * 6, -0.25 + (rng() - 0.5) * 0.2, col, 0.88, 0.35);
  }
  brushes.stamp(ctx, "short", 0, bx + bw * 0.24, by + bh * 0.42, 15, 18, Math.PI * 0.5, [82, 94, 132], 0.88, 0.2);
  brushes.stamp(ctx, "short", 1, bx + bw * 0.42, by + bh * 0.42, 15, 18, Math.PI * 0.5, [242, 198, 126], 0.88, 0.2);
  brushes.stamp(ctx, "short", 2, bx + bw * 0.78, by + bh * 0.46, 14, 16, Math.PI * 0.5, [76, 82, 124], 0.88, 0.2);
  brushes.stamp(ctx, "knife", 0, bx + bw * 0.22, by - h * 0.24, 22, 11, Math.PI * 0.5, [176, 114, 98], 0.92, 0.3);

  brushes.resetCtx(ctx);
  return c;
}

// Create a richly painted, solidly filled notched Water Lily Pad sprite (NO donut hole!)
export function createLilyPadSprite(brushes, size, seed, twilight = false) {
  const c = document.createElement("canvas");
  c.width = size;
  c.height = Math.round(size * 0.58);
  const ctx = c.getContext("2d");
  const rng = mulberry32(seed);
  const cx = c.width * 0.5;
  const cy = c.height * 0.5;
  const rx = c.width * 0.42;
  const ry = c.height * 0.40;
  const notchAngle = (rng() - 0.5) * 0.9 + 0.35;

  const basePad = twilight ? [36, 76, 72] : [58, 134, 72];
  const hiPad = twilight ? [66, 112, 98] : [136, 184, 78];
  const rimPad = twilight ? [22, 46, 62] : [36, 86, 66];

  // 1. Solid notched organic underpainting ellipse so center is 100% filled
  ctx.fillStyle = `rgb(${basePad.join(",")})`;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.ellipse(cx, cy, rx * 0.9, ry * 0.9, 0, notchAngle + 0.22, notchAngle + Math.PI * 2 - 0.22);
  ctx.closePath();
  ctx.fill();

  // 2. Radial & concentric impasto brushstrokes across the whole pad (r = 0..0.92)
  for (let i = 0; i < 36; i++) {
    const a = rng() * Math.PI * 2;
    const da = Math.atan2(Math.sin(a - notchAngle), Math.cos(a - notchAngle));
    if (Math.abs(da) < 0.25) continue;
    const r = Math.sqrt(rng()) * 0.82;
    const px = cx + Math.cos(a) * rx * r;
    const py = cy + Math.sin(a) * ry * r;
    const light = clamp(0.5 + Math.cos(a + 0.8) * 0.45, 0, 1);
    let col = mixRgb(rimPad, mixRgb(basePad, hiPad, light), r < 0.72 ? 0.85 : 0.38);
    col = jitterMonetColor(col, rng, 10, 10, 7);
    brushes.stamp(ctx, "short", Math.floor(rng() * 4), px, py, size * 0.28, size * 0.16, a, col, 0.88, 0.35);
  }
  brushes.resetCtx(ctx);
  return c;
}

// Create a luminous multi-petal Water Lily Flower (Nymphéas) sprite
export function createLilyFlowerSprite(brushes, size, tintType, seed) {
  const c = document.createElement("canvas");
  c.width = size;
  c.height = Math.round(size * 0.72);
  const ctx = c.getContext("2d");
  const rng = mulberry32(seed);
  const cx = c.width * 0.5;
  const cy = c.height * 0.62;

  const outerBase = tintType === "pink" ? [232, 138, 166] : tintType === "rose" ? [216, 98, 138] : [238, 224, 228];
  const innerBase = tintType === "pink" ? [255, 228, 236] : tintType === "rose" ? [252, 198, 214] : [255, 250, 236];

  const petals = 10;
  for (let i = 0; i < petals; i++) {
    const t = i / (petals - 1);
    const ang = lerp(-Math.PI * 0.92, -Math.PI * 0.08, t) + (rng() - 0.5) * 0.1;
    const dist = size * (0.22 + (1 - Math.abs(t - 0.5) * 1.4) * 0.06);
    const px = cx + Math.cos(ang) * dist;
    const py = cy + Math.sin(ang) * dist * 0.62;
    const col = jitterMonetColor(outerBase, rng, 8, 10, 7);
    brushes.stamp(ctx, "short", Math.floor(rng() * 4), px, py, size * 0.32, size * 0.14, ang, col, 0.92, 0.45);
  }
  for (let i = 0; i < 6; i++) {
    const t = i / 5;
    const ang = lerp(-Math.PI * 0.8, -Math.PI * 0.2, t);
    const px = cx + Math.cos(ang) * size * 0.13;
    const py = cy + Math.sin(ang) * size * 0.10 - size * 0.04;
    const col = jitterMonetColor(innerBase, rng, 5, 6, 5);
    brushes.stamp(ctx, "short", Math.floor(rng() * 4), px, py, size * 0.24, size * 0.12, ang, col, 0.94, 0.45);
  }
  brushes.stamp(ctx, "short", 0, cx, cy - size * 0.03, size * 0.16, size * 0.11, 0, [248, 206, 86], 0.96, 0.5);
  brushes.resetCtx(ctx);
  return c;
}

// Render dynamic Monet broken-color water reflections & undulating wave dabs
export function paintAnimatedWater(ctx, brushes, rect, time, options) {
  const {
    baseColor,
    deepColor,
    highlightColor,
    sunColX = null,
    sunColor = null,
    reflectionBands = [],
    seed = 505,
    rippleScale = 1.0,
    fadeLeft = 0,
    fadeRight = 0,
  } = options;

  const { x: rx, y: ry, w: rw, h: rh } = rect;

  // Underpainting wash (silky feathered horizontally if fadeLeft/fadeRight > 0)
  ctx.save();
  const grad = ctx.createLinearGradient(0, ry, 0, ry + rh);
  grad.addColorStop(0, `rgb(${baseColor.map(Math.round).join(",")})`);
  grad.addColorStop(1, `rgb(${deepColor.map(Math.round).join(",")})`);
  ctx.fillStyle = grad;
  const solidStart = rx + fadeLeft;
  const solidEnd = rx + rw - fadeRight;
  if (solidEnd > solidStart) {
    ctx.fillRect(solidStart, ry, solidEnd - solidStart, rh);
  }
  const slicesEdge = 16;
  if (fadeLeft > 0) {
    const sw = fadeLeft / slicesEdge;
    for (let i = 0; i < slicesEdge; i++) {
      const t = (i + 0.5) / slicesEdge;
      ctx.globalAlpha = t * t * (3 - 2 * t);
      ctx.fillRect(rx + i * sw, ry, sw + 0.8, rh);
    }
  }
  if (fadeRight > 0) {
    const sw = fadeRight / slicesEdge;
    for (let i = 0; i < slicesEdge; i++) {
      const t = 1 - (i + 0.5) / slicesEdge;
      ctx.globalAlpha = t * t * (3 - 2 * t);
      ctx.fillRect(rx + rw - fadeRight + i * sw, ry, sw + 0.8, rh);
    }
  }
  ctx.restore();

  const edgeFadeAt = (px) => {
    let a = 1.0;
    if (fadeLeft > 0) a *= smoothstep(rx, rx + fadeLeft, px);
    if (fadeRight > 0) a *= smoothstep(rx + rw, rx + rw - fadeRight, px);
    return a;
  };

  const rng = mulberry32(seed);
  // 1. Interlocking staggered organic water dabs (perspective-scaled, non-grid!)
  const rows = 24;
  for (let r = 0; r < rows; r++) {
    const v = Math.pow(r / (rows - 1), 1.18);
    const pyBase = ry + v * rh;
    const dabW = lerp(46, 130, v) * rippleScale;
    const dabH = lerp(10, 26, v) * rippleScale;
    const cols = Math.ceil(rw / (dabW * 0.48)) + 3;
    const rowPhase = rng() * 10 + r * 1.3;

    for (let c = 0; c < cols; c++) {
      const staggerY = (rng() - 0.5) * dabH * 0.95;
      const basePx = rx + (c - 0.5) * (dabW * 0.52) + (rng() - 0.5) * dabW * 0.45;
      const waveX = Math.sin(time * 1.1 + pyBase * 0.035 + rowPhase + c * 0.45) * (7 + v * 14);
      const waveY = Math.cos(time * 1.35 + basePx * 0.015 + r) * (1.5 + v * 2.5);
      const px = basePx + waveX;
      const py = pyBase + staggerY + waveY;

      const edgeAlpha = edgeFadeAt(px);
      if (edgeAlpha < 0.02) continue;

      const mixT = clamp(0.35 + 0.35 * Math.sin(c * 0.65 + r * 1.3) + (rng() - 0.5) * 0.35, 0, 1);
      let col = mixRgb(baseColor, deepColor, mixT * 0.72);
      if (rng() < 0.32) col = mixRgb(col, highlightColor, 0.32 + 0.22 * Math.sin(time + c * 0.8));
      col = jitterMonetColor(col, rng, 11, 10, 7);

      brushes.stamp(ctx, "broad", (r + c) % 3, px, py, dabW * (0.85 + rng() * 0.35), dabH, (rng() - 0.5) * 0.09, col, (0.58 + rng() * 0.22) * edgeAlpha, 0.25);
    }
  }

  // 2. Reflection bands (willows, bridge, cottages, lanterns) broken into shimmering slices
  for (let b = 0; b < reflectionBands.length; b++) {
    const band = reflectionBands[b];
    const slices = Math.max(8, Math.round(band.height / 13));
    for (let s = 0; s < slices; s++) {
      const sv = s / (slices - 1);
      const sy = band.yTop + sv * band.height;
      if (sy < ry || sy > ry + rh) continue;
      const sway = Math.sin(time * 1.8 + sv * 10 + b) * (band.waveAmp || 12) * (0.4 + sv * 0.8);
      const bx = band.x + sway;
      const edgeAlpha = edgeFadeAt(bx);
      if (edgeAlpha < 0.02) continue;
      const sw = band.width * (0.65 + 0.35 * Math.sin(sv * Math.PI + time * 1.1));
      const col = jitterMonetColor(band.color, rng, 8, 8, 6);
      brushes.stamp(ctx, "broad", s % 3, bx, sy, sw, 11 + sv * 9, (rng() - 0.5) * 0.06, col, (0.36 + 0.22 * (1 - sv)) * (band.alpha ?? 1) * edgeAlpha, 0.2);
    }
  }

  // 3. Sun / Moon / Lantern shimmering impasto reflection column
  if (sunColX !== null && sunColor) {
    const slices = 38;
    for (let s = 0; s < slices; s++) {
      const sv = s / (slices - 1);
      const sy = lerp(ry + 6, ry + rh - 8, Math.pow(sv, 0.88));
      const spread = lerp(18, 98, sv);
      const wobble = Math.sin(time * 2.1 + sv * 14.0 + s * 0.6) * (6 + sv * 18);
      const shimmer = 0.55 + 0.45 * Math.sin(time * 3.1 + s * 1.7);
      const dabLen = lerp(26, 92, sv) * (0.65 + 0.45 * shimmer);
      const dabThick = lerp(6, 14, sv);
      const px = sunColX + wobble + (rng() - 0.5) * spread * 0.72;
      const edgeAlpha = edgeFadeAt(px);
      if (edgeAlpha < 0.02) continue;
      const col = mixRgb(sunColor, [255, 248, 224], shimmer * 0.48);
      brushes.stamp(ctx, "knife", s % 3, px, sy, dabLen, dabThick, (rng() - 0.5) * 0.06, col, (0.52 + shimmer * 0.36) * edgeAlpha, 0.55);
    }
  }
  brushes.resetCtx(ctx);
}

// Paint an expanding broken-brushstroke water ripple ring (for oars, swans, koi)
export function paintWaterRipple(ctx, brushes, cx, cy, rx, ry, color, alpha, seed = 1) {
  const rng = mulberry32(seed);
  const segs = 12;
  for (let i = 0; i < segs; i++) {
    const a = (i / segs) * Math.PI * 2 + (rng() - 0.5) * 0.15;
    // Stronger on front & sides
    const px = cx + Math.cos(a) * rx;
    const py = cy + Math.sin(a) * ry;
    const tang = a + Math.PI * 0.5;
    // Project ellipse tangent to screen angle
    const tx = -Math.sin(a) * rx;
    const ty = Math.cos(a) * ry;
    const screenAngle = Math.atan2(ty, tx);
    brushes.stamp(ctx, "knife", i % 3, px, py, Math.max(10, rx * 0.38), 4.5, screenAngle, color, alpha * (0.55 + 0.45 * Math.sin(a)), 0.4);
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}

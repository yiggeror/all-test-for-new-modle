// Procedural Impasto Bristle Brush Engine with Tinted Sprite Cache
import { mulberry32, clamp } from "./noise.js";

const BRUSH_SPECS = {
  broad:   { w: 96, h: 42, variants: 3 },
  short:   { w: 56, h: 34, variants: 4 },
  curved:  { w: 96, h: 44, variants: 3 },
  knife:   { w: 108, h: 26, variants: 3 },
  scumble: { w: 96, h: 72, variants: 3 },
};

function makeCanvas(w, h) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  return c;
}

// Build grayscale alpha + impasto ridge map for each brush mask
function generateBrushMask(type, variant) {
  const spec = BRUSH_SPECS[type];
  const { w, h } = spec;
  const rng = mulberry32(9001 + type.charCodeAt(0) * 131 + variant * 773);

  const maskCanvas = makeCanvas(w, h);
  const mctx = maskCanvas.getContext("2d");
  const img = mctx.createImageData(w, h);
  const data = img.data;

  // Generate 24-36 individual hog-bristle filaments along the stroke
  const numBristles = type === "knife" ? 12 : type === "scumble" ? 34 : 26;
  const bristles = [];
  for (let i = 0; i < numBristles; i++) {
    bristles.push({
      yNorm: (i + 0.5) / numBristles + (rng() - 0.5) * 0.045,
      weight: 0.55 + rng() * 0.45,
      freq: 1.5 + rng() * 2.5,
      phase: rng() * Math.PI * 2,
      startCut: rng() * 0.16,
      endCut: 1 - rng() * 0.18,
      ridge: (rng() - 0.5) * 2,
    });
  }

  for (let py = 0; py < h; py++) {
    const ny = (py / (h - 1)) * 2 - 1; // [-1, 1]
    for (let px = 0; px < w; px++) {
      const nx = (px / (w - 1)) * 2 - 1; // [-1, 1]
      const u = px / (w - 1);

      // Curved stroke bends y along x
      let localNy = ny;
      if (type === "curved") {
        const arc = (u - 0.5) * (u - 0.5) * 1.15 - 0.22;
        localNy = ny - arc * (variant % 2 === 0 ? 1 : -1);
      }

      // Base oval/rectangular envelope
      let envX = 1;
      let envY = 1;
      if (type === "scumble") {
        const r = Math.hypot(nx * 0.92, localNy * 0.92);
        envX = clamp(1 - Math.pow(r, 2.2), 0, 1);
      } else if (type === "knife") {
        envX = clamp(1 - Math.pow(Math.abs(nx), 4.5), 0, 1);
        envY = clamp(1 - Math.pow(Math.abs(localNy), 3.2), 0, 1);
      } else {
        // Tapered natural brush start/end
        envX = clamp(1 - Math.pow(Math.abs(nx), 2.8), 0, 1);
        envY = clamp(1 - Math.pow(Math.abs(localNy), 2.4), 0, 1);
      }

      // Accumulate bristle strands
      const vNorm = (localNy + 1) * 0.5;
      let bristleDensity = 0;
      let ridgeShade = 0;
      for (let b = 0; b < bristles.length; b++) {
        const br = bristles[b];
        if (u < br.startCut || u > br.endCut) continue;
        const dy = Math.abs(vNorm - br.yNorm);
        const width = type === "scumble" ? 0.095 : 0.055;
        if (dy < width) {
          const wgt = (1 - dy / width) * br.weight;
          const wobble = 0.8 + 0.2 * Math.sin(u * Math.PI * br.freq + br.phase);
          bristleDensity += wgt * wobble;
          ridgeShade += wgt * br.ridge;
        }
      }

      if (type === "knife") {
        // Palette knife: smooth creamy paint body with sharp impasto ridge on one edge
        bristleDensity = 0.78 + 0.22 * clamp(bristleDensity, 0, 1);
        ridgeShade = localNy < -0.55 ? 0.65 : localNy > 0.6 ? -0.45 : ridgeShade * 0.2;
      } else if (type === "scumble") {
        bristleDensity = clamp(bristleDensity * 0.75, 0, 1);
      } else {
        bristleDensity = clamp(0.28 + bristleDensity * 0.85, 0, 1);
      }

      const alpha = clamp(envX * envY * bristleDensity, 0, 1);
      // Store alpha and encode subtle impasto brightness into RGB (128 = neutral)
      const lum = clamp(Math.round(128 + ridgeShade * 34), 60, 220);
      const idx = (py * w + px) * 4;
      data[idx] = lum;
      data[idx + 1] = lum;
      data[idx + 2] = lum;
      data[idx + 3] = Math.round(alpha * 255);
    }
  }

  mctx.putImageData(img, 0, 0);
  return maskCanvas;
}

export class BrushEngine {
  constructor() {
    this.masks = {};
    for (const [type, spec] of Object.entries(BRUSH_SPECS)) {
      this.masks[type] = [];
      for (let v = 0; v < spec.variants; v++) {
        this.masks[type].push(generateBrushMask(type, v));
      }
    }
    this.cache = new Map();
    this.maxCache = 2600;
  }

  _getSprite(type, variant, rgb, impasto = 0.35) {
    const rq = clamp(Math.round(rgb[0] / 14) * 14, 0, 255);
    const gq = clamp(Math.round(rgb[1] / 14) * 14, 0, 255);
    const bq = clamp(Math.round(rgb[2] / 14) * 14, 0, 255);
    const iq = impasto > 0.2 ? 1 : 0;
    const key = `${type}|${variant}|${rq},${gq},${bq}|${iq}`;

    const hit = this.cache.get(key);
    if (hit) return hit;

    if (this.cache.size >= this.maxCache) {
      let n = 0;
      for (const k of this.cache.keys()) {
        this.cache.delete(k);
        if (++n >= 400) break;
      }
    }

    const mask = this.masks[type][variant % this.masks[type].length];
    const c = makeCanvas(mask.width, mask.height);
    const ctx = c.getContext("2d");

    ctx.drawImage(mask, 0, 0);
    ctx.globalCompositeOperation = "source-in";
    ctx.fillStyle = `rgb(${rq},${gq},${bq})`;
    ctx.fillRect(0, 0, c.width, c.height);

    if (iq) {
      ctx.globalCompositeOperation = "soft-light";
      ctx.globalAlpha = 0.42;
      ctx.drawImage(mask, 0, 0);
    }

    ctx.globalCompositeOperation = "source-over";
    ctx.globalAlpha = 1;
    this.cache.set(key, c);
    return c;
  }

  resetCtx(ctx) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = "source-over";
  }

  // Fast world/canvas brushstroke stamp (resets transform cleanly)
  stamp(ctx, type, variant, x, y, length, thickness, angle, rgb, alpha = 0.85, impasto = 0.35) {
    if (alpha <= 0.01 || length <= 0.5 || thickness <= 0.5) return;
    const sprite = this._getSprite(type, variant, rgb, impasto);
    const sx = length / sprite.width;
    const sy = thickness / sprite.height;
    const ca = Math.cos(angle);
    const sa = Math.sin(angle);

    ctx.globalAlpha = clamp(alpha, 0, 1);
    ctx.setTransform(ca * sx, sa * sx, -sa * sy, ca * sy, x, y);
    ctx.drawImage(sprite, -sprite.width * 0.5, -sprite.height * 0.5);
  }

  // Stamp inside an already-transformed context (preserves caller's current transform!)
  stampLocal(ctx, type, variant, x, y, length, thickness, angle, rgb, alpha = 0.85, impasto = 0.35) {
    if (alpha <= 0.01 || length <= 0.5 || thickness <= 0.5) return;
    const sprite = this._getSprite(type, variant, rgb, impasto);
    ctx.save();
    ctx.globalAlpha *= clamp(alpha, 0, 1);
    ctx.translate(x, y);
    if (angle !== 0) ctx.rotate(angle);
    ctx.drawImage(sprite, -length * 0.5, -thickness * 0.5, length, thickness);
    ctx.restore();
  }
}

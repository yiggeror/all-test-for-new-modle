// Linen Canvas Texture, Soft Impressionist Bloom & Atmospheric Glaze
import { mulberry32, clamp } from "./noise.js";

export class CanvasFX {
  constructor(width, height) {
    this.width = width;
    this.height = height;
    this.linenPattern = this._buildLinenPattern();
    this.bloomCanvas = document.createElement("canvas");
    this.bloomCanvas.width = Math.round(width / 4);
    this.bloomCanvas.height = Math.round(height / 4);
    this.bloomCtx = this.bloomCanvas.getContext("2d");
  }

  _buildLinenPattern() {
    const size = 256;
    const c = document.createElement("canvas");
    c.width = size;
    c.height = size;
    const ctx = c.getContext("2d");
    const img = ctx.createImageData(size, size);
    const d = img.data;
    const rng = mulberry32(4242);

    // Subtle woven French canvas warp & weft threads
    for (let y = 0; y < size; y++) {
      const weft = Math.sin((y / 3.0) * Math.PI * 2);
      for (let x = 0; x < size; x++) {
        const warp = Math.sin((x / 3.0) * Math.PI * 2);
        const weave = (warp * 0.55 + weft * 0.45) * 18;
        const slub = Math.sin(x * 0.13 + y * 0.05) * 6 + (rng() - 0.5) * 14;
        const v = clamp(Math.round(128 + weave + slub), 80, 180);
        const i = (y * size + x) * 4;
        d[i] = v;
        d[i + 1] = v - 2;
        d[i + 2] = v - 5;
        d[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    return ctx.createPattern(c, "repeat");
  }

  // Apply luminous dreamy Impressionist bloom + linen weave + gentle corner vignette
  apply(ctx, camX, camY, atmosphere, t) {
    const w = this.width;
    const h = this.height;

    ctx.setTransform(1, 0, 0, 1, 0, 0);

    // 1. Soft optical bloom (warm sunlit halation / dreamy Monet glow)
    const bw = this.bloomCanvas.width;
    const bh = this.bloomCanvas.height;
    this.bloomCtx.clearRect(0, 0, bw, bh);
    this.bloomCtx.filter = "blur(8px) brightness(1.06)";
    this.bloomCtx.drawImage(ctx.canvas, 0, 0, bw, bh);
    this.bloomCtx.filter = "none";

    ctx.save();
    ctx.globalCompositeOperation = "screen";
    ctx.globalAlpha = 0.16;
    ctx.drawImage(this.bloomCanvas, 0, 0, w, h);
    ctx.restore();

    // 2. Subtle linen canvas weave anchored softly to painting space
    ctx.save();
    ctx.globalCompositeOperation = "soft-light";
    ctx.globalAlpha = 0.16;
    // Slight offset anchored to slow-drifting canvas feel so it feels tactile, not static TV noise
    ctx.translate(-(camX * 0.12) % 256, -(camY * 0.12) % 256);
    ctx.fillStyle = this.linenPattern;
    ctx.fillRect(-256, -256, w + 512, h + 512);
    ctx.restore();

    // 3. Delicate warm/cool painterly vignette (never harsh black)
    ctx.save();
    const grad = ctx.createRadialGradient(w * 0.5, h * 0.48, w * 0.30, w * 0.5, h * 0.5, w * 0.72);
    grad.addColorStop(0, "rgba(0,0,0,0)");
    const [sr, sg, sb] = atmosphere.shadowTint;
    grad.addColorStop(1, `rgba(${Math.round(sr * 0.45)},${Math.round(sg * 0.45)},${Math.round(sb * 0.52)},0.24)`);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    // Very gentle opening breath (0..1.4s) & closing peaceful dusk settle (90..92s)
    if (t < 1.4) {
      const a = 1 - t / 1.4;
      ctx.fillStyle = `rgba(225, 218, 230, ${(a * a * 0.65).toFixed(3)})`;
      ctx.fillRect(0, 0, w, h);
    } else if (t > 90.0) {
      const a = clamp((t - 90.0) / 2.0, 0, 1);
      ctx.fillStyle = `rgba(14, 20, 44, ${(a * a * 0.55).toFixed(3)})`;
      ctx.fillRect(0, 0, w, h);
    }
    ctx.restore();
  }
}

// Deterministic PRNG & 2D Smooth Gradient Noise for World-Anchored Brushstrokes

export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function hash2(ix, iy, seed = 1337) {
  let n = Math.imul(ix, 374761393) + Math.imul(iy, 668265263) + Math.imul(seed, 1442695041);
  n = (n ^ (n >>> 13)) | 0;
  n = Math.imul(n, 1274126177);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
}

export function clamp(v, lo, hi) {
  return v < lo ? lo : v > hi ? hi : v;
}

export function lerp(a, b, t) {
  return a + (b - a) * t;
}

export function smoothstep(edge0, edge1, x) {
  const t = clamp((x - edge0) / (edge1 - edge0), 0, 1);
  return t * t * (3 - 2 * t);
}

export function smootherstep(edge0, edge1, x) {
  const t = clamp((x - edge0) / (edge1 - edge0), 0, 1);
  return t * t * t * (t * (t * 6 - 15) + 10);
}

// Continuous 2D gradient noise in [-1, 1]
function grad2(ix, iy, dx, dy, seed) {
  const h = hash2(ix, iy, seed) * Math.PI * 2;
  return Math.cos(h) * dx + Math.sin(h) * dy;
}

export function noise2D(x, y, seed = 101) {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const fx = x - ix;
  const fy = y - iy;
  const ux = fx * fx * fx * (fx * (fx * 6 - 15) + 10);
  const uy = fy * fy * fy * (fy * (fy * 6 - 15) + 10);

  const n00 = grad2(ix, iy, fx, fy, seed);
  const n10 = grad2(ix + 1, iy, fx - 1, fy, seed);
  const n01 = grad2(ix, iy + 1, fx, fy - 1, seed);
  const n11 = grad2(ix + 1, iy + 1, fx - 1, fy - 1, seed);

  const nx0 = lerp(n00, n10, ux);
  const nx1 = lerp(n01, n11, ux);
  return lerp(nx0, nx1, uy);
}

export function fbm2D(x, y, octaves = 4, seed = 101) {
  let val = 0;
  let amp = 0.5;
  let freq = 1;
  let norm = 0;
  for (let i = 0; i < octaves; i++) {
    val += amp * noise2D(x * freq, y * freq, seed + i * 97);
    norm += amp;
    amp *= 0.5;
    freq *= 2.03;
  }
  return val / norm;
}

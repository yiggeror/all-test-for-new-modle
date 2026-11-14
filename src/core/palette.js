// Monet Impressionist Color Theory & Time-of-Day Atmospheric Palette
import { clamp, lerp, smoothstep } from "./noise.js";

export function hexToRgb(hex) {
  const h = hex.replace("#", "");
  const n = parseInt(h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

export function rgbToHex(r, g, b) {
  const rr = clamp(Math.round(r), 0, 255).toString(16).padStart(2, "0");
  const gg = clamp(Math.round(g), 0, 255).toString(16).padStart(2, "0");
  const bb = clamp(Math.round(b), 0, 255).toString(16).padStart(2, "0");
  return `#${rr}${gg}${bb}`;
}

export function mixRgb(c1, c2, t) {
  return [
    lerp(c1[0], c2[0], t),
    lerp(c1[1], c2[1], t),
    lerp(c1[2], c2[2], t),
  ];
}

export function rgbStr(rgb, a = 1) {
  const r = clamp(Math.round(rgb[0]), 0, 255);
  const g = clamp(Math.round(rgb[1]), 0, 255);
  const b = clamp(Math.round(rgb[2]), 0, 255);
  if (a >= 0.999) return `rgb(${r},${g},${b})`;
  return `rgba(${r},${g},${b},${clamp(a, 0, 1).toFixed(3)})`;
}

export function rgbToHsl(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0, s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }
  return [h * 360, s * 100, l * 100];
}

export function hslToRgb(h, s, l) {
  h = ((h % 360) + 360) % 360 / 360;
  s = clamp(s, 0, 100) / 100;
  l = clamp(l, 0, 100) / 100;
  if (s === 0) {
    const v = l * 255;
    return [v, v, v];
  }
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  const hue2rgb = (t) => {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  return [hue2rgb(h + 1 / 3) * 255, hue2rgb(h) * 255, hue2rgb(h - 1 / 3) * 255];
}

// Monet optical color vibration: varies hue, saturation, lightness, and optional warm/cool split
export function jitterMonetColor(baseRgb, rng, hueJitter = 12, satJitter = 10, lightJitter = 9) {
  const [h, s, l] = rgbToHsl(baseRgb[0], baseRgb[1], baseRgb[2]);
  const nh = h + (rng() - 0.5) * 2 * hueJitter;
  const ns = clamp(s + (rng() - 0.5) * 2 * satJitter, 6, 94);
  const nl = clamp(l + (rng() - 0.5) * 2 * lightJitter, 8, 96);
  return hslToRgb(nh, ns, nl);
}

// Monet chromatic shadow: shifts toward violet/cobalt/teal rather than muddy black
export function monetShadow(baseRgb, shadowTint = [78, 86, 152], amount = 0.55) {
  return mixRgb(baseRgb, shadowTint, amount);
}

// Monet sunlit highlight: shifts toward luminous warm cream/gold/coral
export function monetHighlight(baseRgb, lightTint = [255, 240, 185], amount = 0.45) {
  return mixRgb(baseRgb, lightTint, amount);
}

// Keyframe atmosphere anchors mapped continuously across worldX [0 .. 12500]
const ATMO_ANCHORS = [
  {
    x: 900, // Scene 1: Impression Sunrise Dawn Mist
    skyTop: [122, 138, 174],      // misty pearl-slate blue
    skyMid: [178, 174, 196],      // lavender haze
    skyHorizon: [242, 186, 154],  // soft coral-peach dawn
    sunColor: [255, 132, 74],     // glowing cadmium orange-coral sun
    sunGlow: [255, 198, 136],
    mistColor: [218, 212, 224],
    mistDensity: 0.58,
    shadowTint: [76, 82, 136],    // cool slate-violet
    warmTint: [255, 196, 140],
    waterBase: [96, 122, 152],
    waterDeep: [58, 76, 114],
    starAlpha: 0.0,
  },
  {
    x: 3800, // Scene 2: Giverny Morning Sunlight
    skyTop: [104, 166, 218],      // bright morning cerulean
    skyMid: [164, 210, 232],      // airy sky blue
    skyHorizon: [236, 240, 214],  // soft sunlit cream-green horizon
    sunColor: [255, 246, 198],
    sunGlow: [255, 238, 180],
    mistColor: [224, 236, 228],
    mistDensity: 0.16,
    shadowTint: [64, 88, 146],    // luminous cobalt-teal shadow
    warmTint: [255, 244, 186],
    waterBase: [66, 128, 138],    // emerald-cerulean lily pond
    waterDeep: [38, 74, 96],
    starAlpha: 0.0,
  },
  {
    x: 6600, // Scene 3: Sunlit Normandy Afternoon (Poppy Field)
    skyTop: [82, 148, 216],       // radiant cobalt-cerulean
    skyMid: [152, 202, 238],      // luminous afternoon blue
    skyHorizon: [232, 238, 230],  // crisp bright haze
    sunColor: [255, 250, 212],
    sunGlow: [255, 245, 200],
    mistColor: [226, 234, 242],
    mistDensity: 0.10,
    shadowTint: [78, 92, 166],    // classic Monet periwinkle shadow
    warmTint: [255, 248, 198],
    waterBase: [78, 140, 178],
    waterDeep: [48, 86, 132],
    starAlpha: 0.0,
  },
  {
    x: 9300, // Scene 4: Golden Hour Haystacks
    skyTop: [126, 138, 186],      // cool evening periwinkle zenith
    skyMid: [228, 172, 156],      // warm rose-apricot mid-sky
    skyHorizon: [255, 206, 122],  // honey-amber sunset glow
    sunColor: [255, 178, 78],
    sunGlow: [255, 206, 118],
    mistColor: [248, 204, 162],
    mistDensity: 0.24,
    shadowTint: [88, 66, 138],    // rich Monet haystack violet-plum shadow
    warmTint: [255, 198, 108],
    waterBase: [118, 108, 146],
    waterDeep: [68, 58, 108],
    starAlpha: 0.04,
  },
  {
    x: 11700, // Scene 5: Twilight Lagoon & Starlit Nightfall
    skyTop: [28, 42, 94],         // deep Prussian & ultramarine dusk
    skyMid: [88, 78, 142],        // twilight violet-indigo
    skyHorizon: [204, 126, 148],  // fading dusk rose-magenta
    sunColor: [255, 224, 160],    // crescent moon & warm lantern tone
    sunGlow: [246, 196, 138],
    mistColor: [98, 96, 148],
    mistDensity: 0.22,
    shadowTint: [30, 38, 86],     // deep twilight indigo
    warmTint: [255, 196, 102],    // warm lantern amber
    waterBase: [38, 64, 104],
    waterDeep: [20, 36, 72],
    starAlpha: 0.92,
  },
];

export function getAtmosphere(worldX) {
  if (worldX <= ATMO_ANCHORS[0].x) return { ...ATMO_ANCHORS[0] };
  const last = ATMO_ANCHORS[ATMO_ANCHORS.length - 1];
  if (worldX >= last.x) return { ...last };

  let i = 0;
  while (i < ATMO_ANCHORS.length - 2 && worldX > ATMO_ANCHORS[i + 1].x) i++;
  const a = ATMO_ANCHORS[i];
  const b = ATMO_ANCHORS[i + 1];
  const t = smoothstep(a.x, b.x, worldX);

  return {
    skyTop: mixRgb(a.skyTop, b.skyTop, t),
    skyMid: mixRgb(a.skyMid, b.skyMid, t),
    skyHorizon: mixRgb(a.skyHorizon, b.skyHorizon, t),
    sunColor: mixRgb(a.sunColor, b.sunColor, t),
    sunGlow: mixRgb(a.sunGlow, b.sunGlow, t),
    mistColor: mixRgb(a.mistColor, b.mistColor, t),
    mistDensity: lerp(a.mistDensity, b.mistDensity, t),
    shadowTint: mixRgb(a.shadowTint, b.shadowTint, t),
    warmTint: mixRgb(a.warmTint, b.warmTint, t),
    waterBase: mixRgb(a.waterBase, b.waterBase, t),
    waterDeep: mixRgb(a.waterDeep, b.waterDeep, t),
    starAlpha: lerp(a.starAlpha, b.starAlpha, t),
  };
}

// Smooth C2-Continuous One-Take Camera Spline & 2.5D Parallax Projector
import { clamp } from "./noise.js";

export const DURATION_SEC = 92.0;
export const FPS = 30;
export const TOTAL_FRAMES = Math.round(DURATION_SEC * FPS);

// Keyframes: [timeSec, worldX, worldY, zoom]
const CAMERA_KEYFRAMES = [
  [0.0,   680,   0,    1.03],  // Scene 1: Dawn river mist start
  [8.0,   1420,  -2,   1.01],  // Passing rowing boat & sun reflection
  [16.0,  2280,  -6,   1.00],  // Approaching weeping willow curtain (Portal 1)
  [21.0,  3020,  -12,  1.00],  // Emerging into Giverny Lily Pond
  [28.5,  3950,  -20,  1.04],  // Lingering across Japanese Bridge, koi & lilies
  [35.0,  4860,  -32,  1.00],  // Gliding past bridge end toward rose arbor (Portal 2)
  [40.0,  5680,  -150, 0.99],  // Rising onto Normandy Poppy Hillside
  [47.5,  6680,  -146, 1.03],  // Woman with Parasol, child & butterflies
  [54.0,  7580,  -134, 1.00],  // Moving toward sun-dappled orchard arch (Portal 3)
  [59.0,  8380,  -82,  1.00],  // Entering Golden Hour Haystacks
  [66.5,  9350,  -78,  1.03],  // Monumental Haystacks, violet shadows, sheep & dog
  [72.5,  10200, -64,  1.00],  // Descending reed bank toward lagoon (Portal 4)
  [77.5,  10980, +8,   1.00],  // Arriving at Twilight Lagoon water level
  [85.0,  11760, +4,   1.03],  // Gliding swans, stone arch lanterns & fireflies
  [92.0,  12120, -56,  0.98],  // Final poetic upward drift into moonlit sky
];

function catmullRom(p0, p1, p2, p3, t) {
  const t2 = t * t;
  const t3 = t2 * t;
  return 0.5 * (
    (2 * p1) +
    (-p0 + p2) * t +
    (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
    (-p0 + 3 * p1 - 3 * p2 + p3) * t3
  );
}

export function getCamera(timeSec) {
  const t = clamp(timeSec, 0, DURATION_SEC);
  const kf = CAMERA_KEYFRAMES;

  let idx = 0;
  while (idx < kf.length - 2 && t > kf[idx + 1][0]) idx++;

  const t0 = kf[idx][0];
  const t1 = kf[idx + 1][0];
  const u = clamp((t - t0) / Math.max(0.0001, t1 - t0), 0, 1);

  const p0 = kf[Math.max(0, idx - 1)];
  const p1 = kf[idx];
  const p2 = kf[idx + 1];
  const p3 = kf[Math.min(kf.length - 1, idx + 2)];

  // Subtle organic floating breath
  const breathY = Math.sin(t * 0.42) * 3.5;
  const breathX = Math.sin(t * 0.25) * 2.0;

  return {
    t,
    x: catmullRom(p0[1], p1[1], p2[1], p3[1], u) + breathX,
    y: catmullRom(p0[2], p1[2], p2[2], p3[2], u) + breathY,
    zoom: catmullRom(p0[3], p1[3], p2[3], p3[3], u),
  };
}

// Convert world coordinates (wx, wy) at parallax depth d into screen pixels (sx, sy)
// Reference screen: 1920 x 1080
export function worldToScreen(wx, wy, depth, cam, viewW = 1920, viewH = 1080) {
  const scale = (viewW / 1920) * cam.zoom;
  const sx = (wx - cam.x * depth) * scale + viewW * 0.5;
  const sy = (wy - cam.y * depth) * scale + viewH * 0.5;
  return { x: sx, y: sy, scale };
}

// Compute world coordinates so an object at `depth` sits at screen offset (offsetX, offsetY)
// relative to screen center when camera is at (targetCamX, targetCamY)
export function worldAnchor(targetCamX, targetCamY, depth, offsetX = 0, offsetY = 0) {
  return {
    wx: targetCamX * depth + offsetX,
    wy: targetCamY * depth + offsetY,
  };
}


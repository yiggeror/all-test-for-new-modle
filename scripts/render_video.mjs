import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";

const ROOT = process.cwd();
const SRC_DIR = path.join(ROOT, "src");
const OUT_DIR = path.join(ROOT, "output");
fs.mkdirSync(OUT_DIR, { recursive: true });

const WIDTH = 1920;
const HEIGHT = 1080;
const FPS = 30;
const TOTAL_FRAMES = 2760; // 92.0s @ 30fps
const EXPECTED_FRAME_BYTES = WIDTH * HEIGHT * 4;

const AUDIO_PATH = path.join(ROOT, "assets", "audio", "master_92s.wav");
const OUT_1080P = path.join(OUT_DIR, "monet_un_jour_a_giverny_1080p.mp4");
const OUT_720P = path.join(OUT_DIR, "monet_un_jour_a_giverny_720p.mp4");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
};

function runFfmpeg720p() {
  return new Promise((resolve, reject) => {
    console.log("Generating 720p version via Lanczos downscale...");
    const args = [
      "-y",
      "-i", OUT_1080P,
      "-vf", "scale=1280:720:flags=lanczos",
      "-c:v", "libx264",
      "-preset", "slow",
      "-crf", "18",
      "-pix_fmt", "yuv420p",
      "-c:a", "copy",
      "-movflags", "+faststart",
      OUT_720P,
    ];
    const p = spawn("ffmpeg", args, { stdio: ["ignore", "inherit", "inherit"] });
    p.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`720p ffmpeg exited with code ${code}`));
    });
  });
}

const ffmpegArgs = [
  "-y",
  "-f", "rawvideo",
  "-pix_fmt", "rgba",
  "-s", `${WIDTH}x${HEIGHT}`,
  "-r", String(FPS),
  "-i", "pipe:0",
  "-i", AUDIO_PATH,
  "-map", "0:v",
  "-map", "1:a",
  "-c:v", "libx264",
  "-preset", "slow",
  "-crf", "18",
  "-pix_fmt", "yuv420p",
  "-c:a", "aac",
  "-b:a", "192k",
  "-shortest",
  "-movflags", "+faststart",
  OUT_1080P,
];

const ffmpeg = spawn("ffmpeg", ffmpegArgs, { stdio: ["pipe", "pipe", "pipe"] });
let ffmpegErr = "";
ffmpeg.stderr.on("data", (d) => {
  ffmpegErr += d.toString();
  if (ffmpegErr.length > 8000) ffmpegErr = ffmpegErr.slice(-8000);
});

const startMs = Date.now();
let receivedFrames = 0;
let chromeProc = null;

function writeToFfmpeg(chunk) {
  return new Promise((resolve) => {
    if (ffmpeg.stdin.write(chunk)) {
      resolve();
    } else {
      ffmpeg.stdin.once("drain", resolve);
    }
  });
}

let writeQueue = Promise.resolve();

const server = http.createServer((req, res) => {
  const urlPath = req.url.split("?")[0];

  if (urlPath === "/frame" && req.method === "POST") {
    const chunks = [];
    let byteLen = 0;
    req.on("data", (c) => {
      chunks.push(c);
      byteLen += c.length;
    });
    req.on("end", () => {
      if (byteLen !== EXPECTED_FRAME_BYTES) {
        res.writeHead(400);
        res.end(`bad frame size ${byteLen}`);
        return;
      }
      const buf = Buffer.concat(chunks, byteLen);
      writeQueue = writeQueue.then(() => writeToFfmpeg(buf)).then(() => {
        receivedFrames++;
        if (receivedFrames % 60 === 0 || receivedFrames === TOTAL_FRAMES) {
          const elapsed = (Date.now() - startMs) / 1000;
          const rate = receivedFrames / Math.max(0.01, elapsed);
          const eta = Math.round((TOTAL_FRAMES - receivedFrames) / Math.max(0.01, rate));
          console.log(
            `[Frame ${receivedFrames}/${TOTAL_FRAMES}] ${(receivedFrames / TOTAL_FRAMES * 100).toFixed(1)}% | ${rate.toFixed(2)} fps | elapsed ${Math.round(elapsed)}s | ETA ${eta}s`
          );
        }
        res.writeHead(200);
        res.end("ok");
        if (receivedFrames === TOTAL_FRAMES) {
          ffmpeg.stdin.end();
        }
      });
    });
    return;
  }

  if (urlPath === "/err" && req.method === "POST") {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      console.error("BROWSER ERROR:", Buffer.concat(chunks).toString());
      res.writeHead(200);
      res.end("ok");
    });
    return;
  }

  if (urlPath === "/render.html") {
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(`<!DOCTYPE html><html><body>
      <canvas id="stage" width="${WIDTH}" height="${HEIGHT}"></canvas>
      <script type="module">
        window.onerror = (m, s, l, c, e) => fetch("/err", { method: "POST", body: String(m) + " " + (e && e.stack || "") });
        window.onunhandledrejection = (ev) => fetch("/err", { method: "POST", body: String(ev.reason && ev.reason.stack || ev.reason) });
        import { MonetWorld } from "/world.js";
        import { TOTAL_FRAMES, FPS } from "/core/camera.js";
        const canvas = document.getElementById("stage");
        const ctx = canvas.getContext("2d", { willReadFrequently: true });
        const world = new MonetWorld(${WIDTH}, ${HEIGHT});
        for (let i = 0; i < TOTAL_FRAMES; i++) {
          world.renderFrame(ctx, i / FPS);
          const img = ctx.getImageData(0, 0, ${WIDTH}, ${HEIGHT});
          const resp = await fetch("/frame?i=" + i, { method: "POST", body: img.data.buffer });
          if (!resp.ok) throw new Error("Frame upload failed at " + i);
        }
      </script>
    </body></html>`);
    return;
  }

  const rel = urlPath === "/" ? "/index.html" : urlPath;
  const full = path.join(SRC_DIR, rel);
  if (fs.existsSync(full) && fs.statSync(full).isFile()) {
    const ext = path.extname(full);
    res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
    fs.createReadStream(full).pipe(res);
  } else {
    res.writeHead(404);
    res.end("not found");
  }
});

ffmpeg.on("close", async (code) => {
  if (chromeProc) chromeProc.kill();
  server.close();
  if (code !== 0) {
    console.error("FFmpeg 1080p failed:\n" + ffmpegErr);
    process.exit(code || 1);
  }
  console.log(`1080p video complete: ${OUT_1080P}`);
  await runFfmpeg720p();
  console.log(`720p video complete: ${OUT_720P}`);
  process.exit(0);
});

server.listen(0, "127.0.0.1", () => {
  const port = server.address().port;
  console.log(`Render server listening at http://127.0.0.1:${port}/render.html`);
  chromeProc = spawn("chromium", [
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    `http://127.0.0.1:${port}/render.html`,
  ], { stdio: ["ignore", "pipe", "pipe"] });

  chromeProc.stderr.on("data", (d) => {
    const s = d.toString();
    if (s.includes("CONSOLE") || (s.includes("ERROR") && !s.includes("dbus") && !s.includes("ssl"))) {
      process.stderr.write(s);
    }
  });
});

import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";

const ROOT = process.cwd();
const SRC_DIR = path.join(ROOT, "src");
const OUT_DIR = path.join(ROOT, "output", "keyframes");
fs.mkdirSync(OUT_DIR, { recursive: true });

const KEYFRAMES = [
  { name: "01_scene1_dawn_4s", t: 4.0 },
  { name: "02_scene1_egrets_12s", t: 12.0 },
  { name: "03_portal1_willow_18.5s", t: 18.5 },
  { name: "04_scene2_giverny_28s", t: 28.0 },
  { name: "05_portal2_roses_37.5s", t: 37.5 },
  { name: "06_scene3_poppies_47.5s", t: 47.5 },
  { name: "07_portal3_orchard_56.5s", t: 56.5 },
  { name: "08_scene4_haystacks_66.5s", t: 66.5 },
  { name: "09_portal4_reeds_74.5s", t: 74.5 },
  { name: "10_scene5_twilight_84.5s", t: 84.5 },
  { name: "11_scene5_finale_90.5s", t: 90.5 },
];

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
};

let saved = 0;
let chromeProc = null;

const server = http.createServer((req, res) => {
  const urlPath = req.url.split("?")[0];
  if (urlPath === "/save" && req.method === "POST") {
    const name = new URL(req.url, "http://127.0.0.1").searchParams.get("name");
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      const buf = Buffer.concat(chunks);
      fs.writeFileSync(path.join(OUT_DIR, `${name}.png`), buf);
      saved++;
      console.log(`[${saved}/${KEYFRAMES.length}] Saved ${name}.png (${(buf.length / 1024).toFixed(0)} KB)`);
      res.writeHead(200);
      res.end("ok");
      if (saved === KEYFRAMES.length) {
        setTimeout(() => {
          if (chromeProc) chromeProc.kill();
          server.close();
        }, 100);
      }
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

  if (urlPath === "/capture.html") {
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(`<!DOCTYPE html><html><body>
      <canvas id="stage" width="1920" height="1080"></canvas>
      <script type="module">
        window.onerror = (m, s, l, c, e) => fetch("/err", { method: "POST", body: String(m) + " " + (e && e.stack || "") });
        window.onunhandledrejection = (ev) => fetch("/err", { method: "POST", body: String(ev.reason && ev.reason.stack || ev.reason) });
        import { MonetWorld } from "/world.js";
        const canvas = document.getElementById("stage");
        const ctx = canvas.getContext("2d");
        const world = new MonetWorld(1920, 1080);
        const list = ${JSON.stringify(KEYFRAMES)};
        for (const item of list) {
          const t0 = performance.now();
          world.renderFrame(ctx, item.t);
          const renderMs = Math.round(performance.now() - t0);
          const blob = await new Promise((r) => canvas.toBlob(r, "image/png"));
          const buf = await blob.arrayBuffer();
          await fetch("/save?name=" + encodeURIComponent(item.name) + "&ms=" + renderMs, { method: "POST", body: buf });
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

server.listen(0, "127.0.0.1", () => {
  const port = server.address().port;
  console.log(`Keyframe server running at http://127.0.0.1:${port}/capture.html`);
  chromeProc = spawn("chromium", [
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    `http://127.0.0.1:${port}/capture.html`,
  ], { stdio: ["ignore", "pipe", "pipe"] });

  chromeProc.stderr.on("data", (d) => {
    const s = d.toString();
    if (s.includes("CONSOLE") || (s.includes("ERROR") && !s.includes("dbus") && !s.includes("ssl"))) {
      process.stderr.write(s);
    }
  });
});

"""Offline renderer for Les Heures de Lumiere.

Usage:
  python3 src/render.py still OUT.png T [H]
  python3 src/render.py audit OUTDIR [H]
  python3 src/render.py pipe START END [H]   -> streams raw RGB24 to stdout
"""
import os
import sys
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Ensure src/ is importable regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine
from world import Env, FPS, DUR, flat
import scenes

_TITLE_CACHE = {}


def _title_mask(H):
    if H not in _TITLE_CACHE:
        W = H * 16 // 9
        im = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(im)
        f_fr = ImageFont.truetype("/usr/share/fonts/opentype/urw-base35/P052-Italic.otf", int(H * 0.068))
        f_zh = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", int(H * 0.030))
        f_sub = ImageFont.truetype("/usr/share/fonts/opentype/urw-base35/P052-Italic.otf", int(H * 0.026))
        dr.text((W * 0.5, H * 0.445), "Les Heures de Lumi\u00e8re", font=f_fr, fill=255, anchor="mm")
        dr.text((W * 0.5, H * 0.535), "\u5149  \u9634  \u753b  \u5883", font=f_zh, fill=220, anchor="mm")
        dr.text((W * 0.5, H * 0.595), "d'apr\u00e8s Claude Monet", font=f_sub, fill=200, anchor="mm")
        im = im.filter(ImageFilter.GaussianBlur(max(0.5, H / 1080.0 * 0.7)))
        _TITLE_CACHE[H] = np.asarray(im, dtype=np.float32) / 255.0
    return _TITLE_CACHE[H]


def render_frame(t, H=1080):
    env = Env(t)
    batches = flat([s.emit(env) for s in scenes.SETS] + [a(env) for a in scenes.ACTORS])
    fade = float(engine.smooth(91.0, 93.8, t))
    im = engine.render(batches, H=H, tone_amt=0.09, relief=1.05, bloom=0.14, fade=fade)
    ta = float(engine.smooth(92.8, 94.2, t)) * float(engine.smooth(DUR, DUR - 0.7, t))
    if ta > 0.005:
        m = (_title_mask(H) * ta * 0.82)[..., None]
        ink = np.array([86.0, 74.0, 92.0], np.float32)
        im = np.clip(im.astype(np.float32) * (1.0 - m) + ink * m + 0.5, 0.0, 255.0).astype(np.uint8)
    return im


def main():
    mode = sys.argv[1]
    if mode == "still":
        out = sys.argv[2]
        t = float(sys.argv[3])
        H = int(sys.argv[4]) if len(sys.argv) > 4 else 1080
        t0 = time.time()
        im = render_frame(t, H=H)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        Image.fromarray(im).save(out)
        print(f"still t={t:.2f}s H={H} -> {out} ({time.time() - t0:.2f}s)", file=sys.stderr)
    elif mode == "audit":
        out_dir = sys.argv[2]
        H = int(sys.argv[3]) if len(sys.argv) > 3 else 1080
        os.makedirs(out_dir, exist_ok=True)
        marks = [
            ("00_open_1.5s",       1.5),
            ("01_s1_etretat_8s",   8.0),
            ("02_tr1_18.5s",      18.5),
            ("03_s2_argenteuil_28s", 28.0),
            ("04_tr2_38s",        38.0),
            ("05_s3_giverny_48s", 48.0),
            ("06_tr3_58s",        58.0),
            ("07_s4_rouen_68s",   68.0),
            ("08_tr4_77.5s",      77.5),
            ("09_s5_venice_87s",  87.0),
            ("10_title_94.5s",    94.5),
        ]
        for name, ts in marks:
            t0 = time.time()
            im = render_frame(ts, H=H)
            p = os.path.join(out_dir, f"{name}.png")
            Image.fromarray(im).save(p)
            print(f"{name}: {time.time() - t0:.2f}s -> {p}", file=sys.stderr)
    elif mode == "pipe":
        start = int(sys.argv[2])
        end = int(sys.argv[3])
        H = int(sys.argv[4]) if len(sys.argv) > 4 else 1080
        out = sys.stdout.buffer
        t0 = time.time()
        for fidx in range(start, end):
            im = render_frame(fidx / float(FPS), H=H)
            out.write(im.tobytes())
            if (fidx - start + 1) % 30 == 0:
                elapsed = time.time() - t0
                done = fidx - start + 1
                fps_eff = done / max(elapsed, 1e-6)
                print(f"[render] frame {fidx + 1}/{end} ({done} done in {elapsed:.1f}s, {fps_eff:.2f} fps)", file=sys.stderr, flush=True)
        out.flush()
    else:
        raise SystemExit(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()

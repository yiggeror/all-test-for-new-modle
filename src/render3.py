"""CLI Render & Audit Runner for Un Dimanche sur la Seine (v3).

Usage:
  python src/render3.py audit [out_dir] [height]
  python src/render3.py preview [out_mp4] [height]
  python src/render3.py segment <start_frame> <stop_frame> <out_mp4> [height] [crf]
"""
import os
import sys
import subprocess
import numpy as np
from anim import Config, Engine
from anim.output import png, video
from shots3 import FILM_DUR
from film3 import SeineFilmScene, SeinePaintBackend


def _make_engine(height=1080, fps=30, dur=FILM_DUR):
    width = height * 16 // 9
    return Engine(Config(width=width, height=height, fps=fps, duration=dur), SeineFilmScene(), SeinePaintBackend())


def run_audit(out_dir="output/audit_v3", height=1080):
    os.makedirs(out_dir, exist_ok=True)
    eng = _make_engine(height=height, fps=30)
    # Keyframe timestamps spanning every act, transition, under-bridge & dusk
    times = [
        ("00_open_title_1.5s", 1.5),
        ("01_poppy_kite_boy_12s", 12.0),
        ("02_poppy_crest_23s", 23.0),
        ("03_viaduct_steam_train_37s", 37.0),
        ("04_under_stone_arch_46s", 46.0),
        ("05_regatta_hero_sloop_62s", 62.0),
        ("06_willow_curtain_swans_76.5s", 76.5),
        ("07_guinguette_sunset_94s", 94.0),
        ("08_twilight_lanterns_107s", 107.0),
        ("09_finale_canvas_117.5s", 117.5),
    ]
    for label, t in times:
        idx = min(eng.config.count - 1, max(0, int(round(t * eng.config.fps))))
        p = png(eng, os.path.join(out_dir, f"{label}.png"), index=idx)
        print(f"Saved {p} (frame {idx}, t={t}s)")


def run_preview(out_mp4="output/preview_v3_15s.mp4", height=540):
    """Render a 15-second multi-act animated showcase preview (5 x 3s clips at 24fps) with spatial audio."""
    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    master_wav = "assets/audio/master_v3_120s.wav"
    if not os.path.exists(master_wav):
        from audio_mix3 import build_mix
        build_mix(master_wav)

    fps = 24
    eng = _make_engine(height=height, fps=fps)
    # Five 3-second continuous motion clips (72 frames each = 360 frames = 15.0s)
    windows = [
        (10.0, 13.0),   # Kite boy & dog running through poppy meadow
        (36.0, 39.0),   # Steam train & billowing plume crossing stone viaduct
        (45.5, 48.5),   # Swooping straight under central stone viaduct arch
        (60.0, 63.0),   # Hero sailboat heeling with wakes & swallows
        (93.0, 96.0),   # Sunset Guinguette lanterns & glowing water reflections
    ]
    seg_files = []
    for i, (t0, t1) in enumerate(windows):
        f0 = int(round(t0 * fps))
        f1 = int(round(t1 * fps))
        sp_vid = f"/tmp/v3_prev_{i}_vid.mp4"
        sp_mux = f"/tmp/v3_prev_{i}.mp4"
        video(eng, sp_vid, start=f0, stop=f1, crf=18)
        subprocess.run([
            "ffmpeg", "-y", "-v", "error",
            "-i", sp_vid,
            "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", master_wav,
            "-af", "afade=t=in:st=0:d=0.12,afade=t=out:st=2.85:d=0.15",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            sp_mux,
        ], check=True)
        seg_files.append(sp_mux)
        print(f"Rendered preview segment {i + 1}/5 ({t0}s..{t1}s) -> {sp_mux}")

    concat_txt = "/tmp/v3_prev_concat.txt"
    with open(concat_txt, "w") as fh:
        for sp in seg_files:
            fh.write(f"file '{sp}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_mp4,
    ], check=True)
    print(f"Wrote 15s spatial audio-video preview -> {out_mp4} ({os.path.getsize(out_mp4) / 1e6:.2f} MB)")


def run_segment(start, stop, out_mp4, height=1080, crf=14):
    eng = _make_engine(height=height, fps=30)
    video(eng, out_mp4, start=start, stop=stop, crf=crf)
    print(f"Rendered segment [{start}, {stop}) -> {out_mp4}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "audit"
    if mode == "audit":
        out = sys.argv[2] if len(sys.argv) > 2 else "output/audit_v3"
        h = int(sys.argv[3]) if len(sys.argv) > 3 else 1080
        run_audit(out, h)
    elif mode == "preview":
        out = sys.argv[2] if len(sys.argv) > 2 else "output/preview_v3_15s.mp4"
        h = int(sys.argv[3]) if len(sys.argv) > 3 else 540
        run_preview(out, h)
    elif mode == "segment":
        s0, s1 = int(sys.argv[2]), int(sys.argv[3])
        out = sys.argv[4]
        h = int(sys.argv[5]) if len(sys.argv) > 5 else 1080
        crf = int(sys.argv[6]) if len(sys.argv) > 6 else 14
        run_segment(s0, s1, out, h, crf)
    else:
        raise ValueError(f"Unknown mode: {mode}")

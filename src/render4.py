"""CLI renderer for Monet v4: tests, 12-frame 1080p audit, parallel segment rendering & ffmpeg muxing."""
import os
import sys
import time
import shutil
import subprocess
import multiprocessing as mp
import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import look4
import sc3_viaduct
from film4 import MonetDreamFilm

FPS = 30
TOTAL_FRAMES = int(round(look4.FILM_DUR * FPS))  # 3600 frames = 120.0s

_WORKER_FILM = None


def _init_worker():
    global _WORKER_FILM
    _WORKER_FILM = MonetDreamFilm()


def _render_idx(args):
    idx, H, out_dir = args
    t = idx / FPS
    rgb = _WORKER_FILM.render_frame(t, H=H)
    path = os.path.join(out_dir, f"f_{idx:05d}.png")
    # cv2.imwrite expects BGR
    cv2.imwrite(path, rgb[:, :, ::-1])
    return idx


def cmd_test():
    min_pier_clear, mast_clear = sc3_viaduct.check_boat_clearances(dur=20.0, steps=240)
    print(f"[check] Scene3 Viaduct min boat-to-pier clearance = {min_pier_clear:.2f} m (required >= 5.0 m)")
    print(f"[check] Scene3 Viaduct mast-to-arch-crown clearance = {mast_clear:.2f} m (required >= 2.0 m)")
    assert min_pier_clear >= 5.0, f"Pier collision risk: {min_pier_clear}"
    assert mast_clear >= 2.0, f"Arch crown collision risk: {mast_clear}"

    film = MonetDreamFilm()
    # Smoke render 1 frame from each of the 6 scenes at 360p
    for si, t in enumerate([10.0, 30.0, 50.0, 70.0, 90.0, 110.0], start=1):
        rgb = film.render_frame(t, H=360)
        assert rgb.shape == (360, 640, 3) and rgb.dtype == np.uint8
        mean_lum = float(rgb.mean())
        print(f"[smoke] Scene {si} @ {t:.1f}s -> shape={rgb.shape}, mean_luma={mean_lum:.1f}")
        assert 15.0 < mean_lum < 245.0, f"Unexpected brightness on scene {si}: {mean_lum}"
    print("[PASS] All geometry collision checks & 6-scene smoke tests passed!")


def cmd_audit(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    film = MonetDreamFilm()
    shots = [
        ("00_sc1_open_title_1.0s",     1.0),
        ("01_sc1_poppies_kite_10.5s", 10.5),
        ("02_sc1_poppy_hill_17.5s",   17.5),
        ("03_sc2_waterlilies_24.5s",  24.5),
        ("04_sc2_wisteria_bridge_33s",33.0),
        ("05_sc3_viaduct_arches_46s", 46.0),
        ("06_sc3_steam_regatta_53s",  53.0),
        ("07_sc4_cathedral_plaza_65s",65.0),
        ("08_sc4_rose_doves_74s",     74.0),
        ("09_sc5_lavender_waves_85s", 85.0),
        ("10_sc5_windmill_sunset_94s",94.0),
        ("11_sc6_venice_gondola_107s",107.0),
        ("12_sc6_finale_moon_115s",  115.0),
        ("13_sc6_finale_title_118.2s",118.2),
    ]
    for name, t in shots:
        t0 = time.time()
        rgb = film.render_frame(t, H=1080)
        p = os.path.join(out_dir, f"{name}.png")
        Image.fromarray(rgb).save(p)
        print(f"[audit] {name} ({t:.1f}s) -> {p} ({time.time() - t0:.2f}s)")


def cmd_segment(seg_idx: int, num_segs: int, H: int, out_mp4: str, workers: int = 0):
    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    per = (TOTAL_FRAMES + num_segs - 1) // num_segs
    start = seg_idx * per
    end = min(TOTAL_FRAMES, (seg_idx + 1) * per)
    frame_dir = out_mp4 + f".frames_{seg_idx}"
    os.makedirs(frame_dir, exist_ok=True)

    nw = workers if workers > 0 else max(1, (os.cpu_count() or 2))
    print(f"[segment {seg_idx}/{num_segs}] frames [{start}..{end}) at H={H} using {nw} workers")
    t0 = time.time()
    tasks = [(i, H, frame_dir) for i in range(start, end)]
    if nw == 1:
        _init_worker()
        for done, arg in enumerate(tasks, 1):
            _render_idx(arg)
            if done % 60 == 0 or done == len(tasks):
                print(f"  rendered {done}/{len(tasks)} ({time.time() - t0:.1f}s)")
    else:
        with mp.Pool(processes=nw, initializer=_init_worker) as pool:
            for done, _ in enumerate(pool.imap_unordered(_render_idx, tasks, chunksize=4), 1):
                if done % 60 == 0 or done == len(tasks):
                    print(f"  rendered {done}/{len(tasks)} ({time.time() - t0:.1f}s)")

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-start_number", str(start),
        "-i", os.path.join(frame_dir, "f_%05d.png"),
        "-frames:v", str(end - start),
        "-c:v", "libx264", "-preset", "slow", "-crf", "14",
        "-pix_fmt", "yuv420p",
        out_mp4,
    ]
    subprocess.run(cmd, check=True)
    shutil.rmtree(frame_dir, ignore_errors=True)
    print(f"[segment {seg_idx}] done -> {out_mp4} ({time.time() - t0:.1f}s total)")


def cmd_concat(audio_wav: str, out_1080p: str, out_720p: str, seg_files: list):
    os.makedirs(os.path.dirname(os.path.abspath(out_1080p)), exist_ok=True)
    list_txt = out_1080p + ".concat.txt"
    with open(list_txt, "w") as f:
        for p in seg_files:
            f.write(f"file '{os.path.abspath(p)}'\n")

    # High-bitrate 1080p master (CRF 15 + AAC 320k stereo)
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", list_txt,
        "-i", audio_wav,
        "-c:v", "libx264", "-preset", "slow", "-crf", "15",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
        "-movflags", "+faststart",
        "-shortest",
        out_1080p,
    ], check=True)

    # Crisp 720p version (Lanczos downscale, CRF 16 + AAC 256k)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", out_1080p,
        "-vf", "scale=1280:720:flags=lanczos",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
        "-movflags", "+faststart",
        out_720p,
    ], check=True)
    os.remove(list_txt)
    print(f"[concat] Built {out_1080p} and {out_720p}!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: render4.py [test | audit <dir> | segment <idx> <num> <H> <out_mp4> [workers] | concat <wav> <out1080> <out720> <segs...>]")
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "test":
        cmd_test()
    elif mode == "audit":
        cmd_audit(sys.argv[2] if len(sys.argv) > 2 else "output/audit_v4")
    elif mode == "segment":
        seg_idx = int(sys.argv[2])
        num_segs = int(sys.argv[3])
        H = int(sys.argv[4])
        out_mp4 = sys.argv[5]
        workers = int(sys.argv[6]) if len(sys.argv) > 6 else 0
        cmd_segment(seg_idx, num_segs, H, out_mp4, workers=workers)
    elif mode == "concat":
        cmd_concat(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
    else:
        raise SystemExit(f"Unknown mode: {mode}")

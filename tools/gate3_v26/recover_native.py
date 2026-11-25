#!/usr/bin/env python3
"""Recover the exact Gate 2.6 native RGB phase from a verified lossless MP4."""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from fractions import Fraction

import numpy as np

SCENES = ("spring", "summer", "autumn", "winter")
NATIVE_W, NATIVE_H, SCALE = 320, 180, 6
WIDTH, HEIGHT = NATIVE_W * SCALE, NATIVE_H * SCALE
LUMA_BYTES = WIDTH * HEIGHT
CHROMA_BYTES = LUMA_BYTES // 4
FRAME_BYTES = LUMA_BYTES + 2 * CHROMA_BYTES
FRAMES = 330
FINGERPRINTS = Path(__file__).resolve().with_name("native_fingerprints.json")
# LF-normalized so that Windows Git checkout line endings also work.
FINGERPRINTS_SHA256 = "ccf4cdb21ca521d3e7bc4eede91c2482d08b095984614dfe4f12090e468494e1"


def require_hash(path, expected, label):
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for segment in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(segment)
    actual = sha.hexdigest()
    if actual != expected:
        raise ValueError(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")
    return actual


def load_fingerprints(path=FINGERPRINTS):
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    actual = hashlib.sha256(raw).hexdigest()
    if actual != FINGERPRINTS_SHA256:
        raise ValueError(f"native fingerprints SHA-256 mismatch: got {actual}")
    doc = json.loads(raw)
    if set(doc) != set(SCENES):
        raise ValueError("native fingerprints must contain the four Gate 2.6 scenes")
    return doc


def build_palette(rows):
    """Prepare an exact Y:Cb:Cr lookup; zero marks any color not approved."""
    if not 1 <= len(rows) <= 255:
        raise ValueError("invalid native palette length")
    table = np.asarray(rows)
    if table.shape != (len(rows), 6) or table.dtype.kind not in "iub" or (
        (table < 0).any() or (table > 255).any()
    ):
        raise ValueError("invalid native palette byte values")
    packed = (table[:, 0] << 16) | (table[:, 1] << 8) | table[:, 2]
    if len(np.unique(packed)) != len(rows):
        raise ValueError("Y:Cb:Cr palette key collision")
    colors = np.zeros((len(rows) + 1, 3), dtype=np.uint8)
    colors[1:] = table[:, 3:]
    idx = np.zeros(1 << 24, dtype=np.uint8)
    idx[packed] = np.arange(1, len(rows) + 1, dtype=np.uint8)
    return colors, idx


def decode_native_frame(raw, palette):
    """Read center samples of each 6x6 luma / 3x3 chroma native block."""
    if len(raw) != FRAME_BYTES:
        raise ValueError(f"decoded frame has {len(raw)} bytes, expected {FRAME_BYTES}")
    # Keep decoded planar yuv420p values. Asking for RGB here silently rounds.
    sample_y = np.frombuffer(raw, np.uint8, count=LUMA_BYTES)
    sample_cb = np.frombuffer(raw, np.uint8, count=CHROMA_BYTES, offset=LUMA_BYTES)
    sample_cr = np.frombuffer(raw, np.uint8, count=CHROMA_BYTES, offset=LUMA_BYTES + CHROMA_BYTES)
    yy = sample_y.reshape(HEIGHT, WIDTH)[3::6, 3::6].astype(np.uint32)
    cb = sample_cb.reshape(HEIGHT // 2, WIDTH // 2)[1::3, 1::3].astype(np.uint32)
    cr = sample_cr.reshape(HEIGHT // 2, WIDTH // 2)[1::3, 1::3]
    key = (yy << 16) | (cb << 8) | cr
    colors, idx = palette
    matches = idx[key]
    if not np.all(matches):
        y, x = np.argwhere(matches == 0)[0]
        yuv = int(yy[y, x]), int(cb[y, x]), int(cr[y, x])
        raise ValueError(f"unknown decoded YUV {yuv} at native pixel ({x}, {y})")
    return colors[matches]


def frame_hashes(frames):
    return [hashlib.sha256(frame).digest() for frame in frames]


def hold_indices(frames, hashes=None):
    """Each index i equal to its prior phase, including cyclic boundary 329→0."""
    hashes = frame_hashes(frames) if hashes is None else hashes
    return tuple(i for i, item in enumerate(hashes) if item == hashes[i-1])


def verify_frozen_holds(scene, frames, expected, hashes=None):
    actual=hold_indices(frames, hashes)
    if actual != tuple(expected):
        raise ValueError(f'{scene}: source hold indices mismatch: got {actual}, expected {expected}')
    return actual


def verify_source_pts(src):
    probe=json.loads(subprocess.check_output([
        "ffprobe","-v","error","-show_streams","-show_packets","-show_entries",
        "stream=codec_name,codec_type,width,height,pix_fmt,avg_frame_rate,time_base,color_space,color_range:packet=pts,duration",
        "-of","json",str(src),
    ]))
    (v,)=probe["streams"]
    expected=("video","h264",1920,1080,"yuv420p","30/1","bt709","tv")
    keys=("codec_type","codec_name","width","height","pix_fmt","avg_frame_rate","color_space","color_range")
    if tuple(v.get(k) for k in keys)!=expected:
        raise ValueError("Gate 2.6 lossless source stream format differs from approval")
    step=1/(30*Fraction(v["time_base"]))
    pts=sorted(int(x["pts"]) for x in probe["packets"])
    if step.denominator!=1 or pts!=[i*step for i in range(2*FRAMES)] or any(
        int(x["duration"])!=step for x in probe["packets"]
    ):
        raise ValueError("Gate 2.6 lossless source PTS missing, duplicated or off cadence")
    return len(pts)


def recover(scene, src, output):
    """Decode one approved 330-frame phase and write a byte-verified NPY."""
    if src.resolve() == output.resolve():
        raise ValueError("output must not overwrite the Gate 2.6 input")
    pins = load_fingerprints()[scene]
    require_hash(src, pins["input_mp4_sha256"], f"{scene} Gate 2.6 lossless MP4 (not the proxy)")
    pts_checked=verify_source_pts(src)
    palette = build_palette(pins["yuv_to_rgb"])
    frames = np.empty((FRAMES, NATIVE_H, NATIVE_W, 3), dtype=np.uint8)
    command = [
        "ffmpeg", "-v", "error", "-nostdin", "-xerror", "-threads", "2", "-i", str(src),
        "-map", "0:v:0", "-an", "-sn", "-dn", 
        "-fps_mode", "passthrough", "-pix_fmt", "yuv420p", "-threads", "1",
        "-f", "rawvideo", "pipe:1",
    ]
    with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
        try:
            for i in range(2*FRAMES):
                raw = proc.stdout.read(FRAME_BYTES)
                try:
                    rgb=decode_native_frame(raw, palette)
                    if i<FRAMES:frames[i]=rgb
                    elif not np.array_equal(frames[i-FRAMES],rgb):
                        raise ValueError("cycle two differs from cycle one")
                except ValueError as exc:
                    raise ValueError(f"{scene} frame {i}: {exc}") from exc
            if proc.stdout.read(1):
                raise ValueError(f"{scene}: excess decoded bytes beyond 660 full frames")
            code = proc.wait()
            if code:
                raise ValueError(f"{scene} ffmpeg decode exited with code {code}")
        except BaseException:
            if proc.poll() is None:
                proc.kill()
            raise
    rgb_sha = hashlib.sha256(memoryview(frames)).hexdigest()
    if rgb_sha != pins["rgb_sha256"]:
        raise ValueError(f"{scene} raw RGB SHA-256 mismatch: got {rgb_sha}")
    hashes=frame_hashes(frames)
    order=hashlib.sha256(b"".join(hashes)).hexdigest()
    held=verify_frozen_holds(scene,frames,pins["adjacent_equal_cycle_indices"],hashes)
    unique=len(set(hashes))
    if unique!=pins["unique_rgb_frames"]:
        raise ValueError(f"{scene} unique source RGB frame count mismatch")
    if order != pins["ordered_rgb_frame_hashes_sha256"]:
        raise ValueError(f"{scene} ordered RGB frame fingerprints mismatch")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=output.parent, prefix=f".{output.name}.", suffix=".tmp", delete=False,
        ) as temporary:
            temporary_name = Path(temporary.name)
            np.lib.format.write_array(temporary, frames, version=(1, 0), allow_pickle=False)
        npy_sha = require_hash(temporary_name, pins["npy_sha256"], f"{scene} frozen NPY")
        temporary_name.replace(output)
    finally:
        if temporary_name is not None:
            temporary_name.unlink(missing_ok=True)
    return {
        "scene": scene, "frames": FRAMES, "full_decode_frames_checked": 2*FRAMES, "native_size": [NATIVE_W, NATIVE_H],
        "palette_colors": len(pins["yuv_to_rgb"]), "rgb_sha256": rgb_sha,
        "npy_sha256": npy_sha, "output": str(output), "source_pts_checked": pts_checked,
        "unique_rgb_frames": unique, "adjacent_equal_count": len(held),
        "adjacent_equal_cycle_indices": list(held),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", choices=SCENES, required=True)
    parser.add_argument("--input", type=Path, required=True, help="reassembled Gate 2.6 lossless MP4")
    parser.add_argument("--output", type=Path, required=True, help="330 native RGB frames as a NumPy NPY")
    args = parser.parse_args()
    try:
        outcome = recover(args.scene, args.input, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    print(json.dumps(outcome, ensure_ascii=False))


if __name__ == "__main__":
    main()

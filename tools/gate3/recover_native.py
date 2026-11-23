#!/usr/bin/env python3
"""Recover the exact Gate 2 native RGB phase from a verified lossless MP4."""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

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
FINGERPRINTS_SHA256 = "ab22ec53b5b389e2d7aa2062ef10d085a3294cf392fd1dd82130eeab69f8e11f"


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
        raise ValueError("native fingerprints must contain the four Gate 2 scenes")
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


def recover(scene, src, output):
    """Decode one approved 330-frame phase and write a byte-verified NPY."""
    if src.resolve() == output.resolve():
        raise ValueError("output must not overwrite the Gate 2 input")
    pins = load_fingerprints()[scene]
    require_hash(src, pins["input_mp4_sha256"], f"{scene} Gate 2 lossless MP4 (not the proxy)")
    palette = build_palette(pins["yuv_to_rgb"])
    frames = np.empty((FRAMES, NATIVE_H, NATIVE_W, 3), dtype=np.uint8)
    command = [
        "ffmpeg", "-v", "error", "-nostdin", "-xerror", "-threads", "2", "-i", str(src),
        "-map", "0:v:0", "-an", "-sn", "-dn", "-frames:v", str(FRAMES),
        "-fps_mode", "passthrough", "-pix_fmt", "yuv420p", "-threads", "1",
        "-f", "rawvideo", "pipe:1",
    ]
    with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
        try:
            for i in range(FRAMES):
                raw = proc.stdout.read(FRAME_BYTES)
                try:
                    frames[i] = decode_native_frame(raw, palette)
                except ValueError as exc:
                    raise ValueError(f"{scene} frame {i}: {exc}") from exc
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
        "scene": scene, "frames": FRAMES, "native_size": [NATIVE_W, NATIVE_H],
        "palette_colors": len(pins["yuv_to_rgb"]), "rgb_sha256": rgb_sha,
        "npy_sha256": npy_sha, "output": str(output),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", choices=SCENES, required=True)
    parser.add_argument("--input", type=Path, required=True, help="reassembled Gate 2 lossless MP4")
    parser.add_argument("--output", type=Path, required=True, help="330 native RGB frames as a NumPy NPY")
    args = parser.parse_args()
    try:
        outcome = recover(args.scene, args.input, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    print(json.dumps(outcome, ensure_ascii=False))


if __name__ == "__main__":
    main()

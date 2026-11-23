#!/usr/bin/env python3
"""Verify every clean Gate 1 still, its native source/palette, and presentation assets."""
import argparse
import hashlib
import json
from pathlib import Path

from check_grid import check
from PIL import Image
import numpy as np


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root):
    files = []
    for scene in ("spring", "summer", "autumn", "winter"):
        meta_path = root / f"{scene}.json"
        files.append(meta_path)
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["scene"] == scene and meta["samples_per_pixel"] == 9
        assert 0 <= meta["phase"] < 1 and 32 <= meta["fov_horizontal"] <= 44
        assert 48 <= meta["shared_palette_count"] <= 64
        master_palette = np.array(meta["palette_rgb"], dtype=np.uint8)
        assert len(master_palette) == meta["shared_palette_count"]
        assert len(np.unique(master_palette, axis=0)) == len(master_palette)
        assert [(x["native"], x["scale"]) for x in meta["frames"]] == [([320, 180], 6), ([384, 216], 5)]
        for fr in meta["frames"]:
            w, h = fr["native"]
            assert fr["filename"] == f"{scene}_{w}x{h}_1080p.png"
            native = root / f"{scene}_{w}x{h}_native.png"
            png = root / fr["filename"]
            strip = root / f"{scene}_{w}x{h}_palette.png"
            result = check(png, fr["scale"], native)
            assert result["ok"] and not result["ambiguous"], result
            assert fr["used_colors"] == result["unique_colors"]
            with Image.open(native) as im:
                pixels = np.unique(np.asarray(im.convert("RGB")).reshape(-1, 3), axis=0)
            assert set(map(tuple, pixels)) <= set(map(tuple, master_palette))
            with Image.open(strip) as im:
                assert im.height == 56 and len(master_palette) * 32 == im.width
                assert np.array_equal(np.asarray(im.convert("RGB"))[0, ::32], master_palette)
            files.extend((png, native, strip))
            digest_prefix = digest(png)[:12]
            print(f"{scene:6}  {w}x{h} {fr['scale']}x  {result['block_count']:5d} exact blocks  "
                  f"{len(pixels)} colors  sha256 {digest_prefix}…")
        motion = root / f"{scene}_motion_note.png"
        comp = root / f"{scene}_comparison.png"
        for path in (motion, comp):
            with Image.open(path) as im:
                assert im.mode == "RGB"
                im.load()
            files.append(path)
    for name in ("overview_A_320x180.png", "overview_B_384x216.png"):
        path = root / name
        with Image.open(path) as im:
            im.load()
        files.append(path)
    all_frames = [f for f in files if f.name.endswith("_1080p.png")]
    assert len(all_frames) == 8 and len({digest(f) for f in all_frames}) == 8
    return sorted(files)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dir", type=Path, default=Path(__file__).resolve().parent / "previews" / "gate_1")
    p.add_argument("--write-manifest", action="store_true")
    a = p.parse_args()
    files = verify(a.dir)
    if a.write_manifest:
        (a.dir / "SHA256SUMS.txt").write_text("".join(f"{digest(f)}  {f.name}\n" for f in files), encoding="utf-8")
    print(f"{len(files)} review files, eight clean 1080p images; A/B independent; all checks passed.")


if __name__ == "__main__":
    main()

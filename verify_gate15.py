#!/usr/bin/env python3
"""Gate 1.5 asset and regression checks, leaving Gate 1 untouched."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from check_grid import check
from verify_outputs import digest

HERE = Path(__file__).resolve().parent
SLUGS = ("spring", "summer", "autumn", "winter")


def verify(root, base, scenes):
    checked = []
    for s in scenes:
        prefix = f"{s}_320x180"
        still = root/f"{prefix}_1080p.png"
        native = root/f"{prefix}_native.png"
        palette = root/f"{prefix}_palette.png"
        motion = root/f"{s}_motion_note.png"
        meta_path = root/f"{s}.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        result = check(still, 6, native=native)
        assert result["ok"] and not result["ambiguous"], result
        assert meta["scene"] == s and meta["samples_per_pixel"] == 9
        assert len(meta["frames"]) == 1 and meta["frames"][0]["native"] == [320, 180]
        assert 48 <= result["unique_colors"] <= 64
        assert len(meta["palette_rgb"]) == meta["shared_palette_count"] <= 64
        original = base/f"{prefix}_1080p.png"
        assert digest(original) != digest(still), f"{s}: did not revise prior still"
        with Image.open(palette) as im:
            cols = np.asarray(im.convert("RGB"))[0, ::32]
            assert np.array_equal(cols, np.asarray(meta["palette_rgb"]))
        with Image.open(motion) as im:
            assert im.size == (1344, 969)
            im.load()
        print(f"{s:6} 320×180 → 1920×1080; {result['block_count']:,} exact RGB blocks; "
              f"{result['unique_colors']} colors; revised vs Gate 1")
        checked += [still, native, palette, motion, meta_path]
    if tuple(scenes) == SLUGS:
        overview = root/"overview_gate_1_5.png"
        with Image.open(overview) as im:
            assert im.size == (2032, 1424)
            im.load()
        checked.append(overview)
    return sorted(checked)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dir", type=Path, default=HERE/"previews"/"gate_1_5")
    p.add_argument("--before", type=Path, default=HERE/"previews"/"gate_1")
    p.add_argument("--scene", action="append", choices=SLUGS)
    p.add_argument("--write-manifest", action="store_true")
    a = p.parse_args()
    selected = tuple(a.scene) if a.scene else SLUGS
    checked = verify(a.dir, a.before, selected)
    if a.write_manifest:
        assert selected == SLUGS, "Manifest is only for the completed four-season set"
        (a.dir/"SHA256SUMS.txt").write_text("".join(f"{digest(f)}  {f.name}\n" for f in checked),
                                          encoding="utf-8")
    print(f"{len(checked)} Gate 1.5 files checked.")


if __name__ == "__main__":
    main()

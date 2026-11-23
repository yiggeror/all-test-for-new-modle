#!/usr/bin/env python3
"""Rebuild the 320×180 Gate 1.5 release candidates without touching Gate 1."""
import argparse
from pathlib import Path

import numpy as np
from PIL import ImageFont
import gate1

SCENES = {
    "spring": ("spring_g15.py", .31),
    "summer": ("summer_gate15.py", .20),
    "autumn": ("autumn_g15.py", .25),
    "winter": ("winter_gate15.py", .21),
}


def protect_cat_ear_rays(tag):
    """Denoise the backdrop but retain the authentic ray samples around the spring cat."""
    base_denoise = gate1.fx.denoise

    def preserved(plate, *args, **kwargs):
        cat = plate.get(f"tag{tag}")
        hits = np.argwhere(cat > 0) if cat is not None else np.empty((0, 2), dtype=int)
        if not len(hits):
            return base_denoise(plate, *args, **kwargs)
        y0, x0 = np.maximum(0, hits.min(0) - 1)
        y1, x1 = np.minimum(plate["sky"].shape, hits.max(0) + 2)
        region = np.s_[:, y0:y1, x0:x1, :]
        ray_pixels = plate["layers"][region].copy()
        result = base_denoise(plate, *args, **kwargs)
        plate["layers"][region] = ray_pixels
        return result

    return preserved


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("scene", choices=SCENES)
    p.add_argument("--out", type=Path, default=gate1.HERE/"previews"/"gate_1_5")
    a = p.parse_args()
    if (gate1.HERE/"previews"/"gate_1").resolve() == a.out.resolve():
        p.error("Gate 1 is archival; pick a new output dir")
    ImageFont.truetype = gate1.cjk_font_loader()
    filename, strength = SCENES[a.scene]
    sc = gate1.load_scene(a.scene, gate1.HERE/"shots"/filename)
    if a.scene == "spring":
        gate1.fx.denoise = protect_cat_ear_rays(sc.CAT_TAG)
    gate1.export(a.scene, sc, a.out, [320], float(sc.PHASE), 3, 60, "mix", strength)


if __name__ == "__main__":
    main()

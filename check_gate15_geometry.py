#!/usr/bin/env python3
"""Measure summer shelter silhouette and winter physical staging in logical pixels."""
import json
from math import pi
from pathlib import Path

import numpy as np
from PIL import ImageFont

import gate1
from engine.rt import Accel
from engine.world import roty
from shots import summer_world_gate15 as rain
from shots import winter_world_gate15 as snow

ROOT = Path(__file__).resolve().parent


def hits(world, cam):
    g = world.finalize()
    acc = Accel(g["v0"], g["v1"], g["v2"], g["tm"])
    xx, yy = np.meshgrid(np.arange(320) + .5, np.arange(180) + .5)
    dirs = cam.dirs(xx, yy).astype(np.float32).reshape(-1, 3)
    origin = np.broadcast_to(cam.pos, dirs.shape).astype(np.float32).copy()
    _, tris = acc.closest(origin, dirs)
    faces = g["tf"][np.maximum(tris, 0)]
    tags = np.where(tris >= 0, g["F"]["tag"][faces], -1).reshape(180, 320)
    mats = g["F"]["mat"][faces].reshape(180, 320)
    return tags, mats


def old_summer_roof_traffic_intrusions(world):
    g = world.finalize()
    face = g["tf"]
    metal = world.mats["metal"]
    old_shed = (g["F"]["mat"][face] == metal) & np.all(
        np.isclose(g["F"]["prm"][face], [.5, .18, 0, 0]), axis=1)
    if not np.any(old_shed):
        return 0
    xyz = np.stack([g[k][old_shed] for k in ("v0", "v1", "v2")], axis=1)
    lo, hi = xyz.min(axis=1), xyz.max(axis=1)
    x = (lo[:,0] < 13.0) & (hi[:,0] > 10.35)
    z = (lo[:,2] < 5.9) & (hi[:,2] > 1.05)
    y = (lo[:,1] < 3.0) & (hi[:,1] > 2.15)
    return int(np.count_nonzero(x & y & z))


def main():
    ImageFont.truetype = gate1.cjk_font_loader()
    results = {}
    sm = gate1.load_scene("summer", ROOT/"shots"/"summer_gate15.py")
    summer = sm.build()
    tags, material = hits(summer, sm.camera(320, 180))
    yy, xx = np.nonzero(tags == rain.SHELTER_CAT_TAG)
    assert len(xx) >= 28, "the shelter cat is mostly occluded"
    w, h = np.ptp(xx) + 1, np.ptp(yy) + 1
    assert 8 <= w <= 18 and 5 <= h <= 10, (w,h)
    assert tags[150,250] == rain.pr.TAG_GROUND, "highlight lands off the roadway"
    intrusive = old_summer_roof_traffic_intrusions(summer)
    assert not intrusive, "old corrugated shade geometry still occupies the wet street"
    names = {value:key for key,value in summer.mats.items()}
    results["summer"] = {
        "cat_visible_native_pixels": len(xx),
        "cat_visible_box_xywh": [int(xx.min()), int(yy.min()), int(w), int(h)],
        "red_puddle_probe_material": names[material[150,250]],
        "old_shed_roof_tris_intruding_into_street": intrusive,
    }
    win = gate1.load_scene("winter", ROOT/"shots"/"winter_gate15.py")
    camera = win.camera(320, 180)
    wx, wy, *_ = camera.project(win.reading_opening_world())
    assert 16 <= np.ptp(wx) <= 24 and 12 <= np.ptp(wy) <= 18
    # Inverse of the coal shed's placement, by WORLD construction. Horizontal roots only.
    shed_local = (np.array([(x,0,z) for x,z,_ in snow.TREES]) - [-6,0,-39]) @ roty(-pi/2)
    roots = ((shed_local[:,0]>=0) & (shed_local[:,0]<=6*2.6)
             & (shed_local[:,2]<=0) & (shed_local[:,2]>=-2.8))
    assert not roots.any(), "a trunk is inside the coal shed footprint"
    x,z,_ = snow.TREES[0]
    tree_x = camera.project((x,4.8,z))[0]
    pole_x = camera.project((-7.75,4.8,5.5))[0]
    assert pole_x - tree_x > 44, "foreground tree again overlaps the lamp pole"
    results["winter"] = {
        "opening_width_height_px": [round(np.ptp(wx),2), round(np.ptp(wy),2)],
        "foreground_tree_utility_pole_gap_px": round(pole_x-tree_x,2),
        "winter_trunk_bases_in_coal_shed": int(roots.sum()),
        "window_static_actor_anchor": gate1.anchors_norm(win,camera)["值班室暖窗伏案人"],
    }
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

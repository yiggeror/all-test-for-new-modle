"""冬 · 路灯下的家属院。静帧审构图；暖窗日常和蒸汽为后续落点。"""
import numpy as np
from engine.render import Camera
from engine.world import roty
from shots import winter_world_gate15 as snow

NAME = "winter"
PHASE = 0.36
GATE1_DSTR = 0.21
VIGNETTE = 0.07
GRADE = dict(snow.GRADE, exposure=2.82, contrast=1.13, sat=0.98, lift=(0.016, 0.024, 0.048))
PAL = dict(chroma_w=3.9, extra=[(0.78, 0.82, 0.88), (0.62, 0.68, 0.78), (0.90, 0.60, 0.39)])
DENOISE = dict(r=1, sl=0.11)
RENDER = dict(snow.RENDER, dirt=0.34, streak=0.25)
sky = snow.sky
setup = snow.setup
frame = snow.frame

def guard_world(point):
    return tuple(np.asarray(snow.GUARD_POS) + roty(snow.GUARD_YAW) @ np.asarray(point))


def reading_opening_world():
    xa, ya, xb, yb = snow.READING_OPENING
    w, d, _ = snow.GUARD_SIZE
    return [guard_world((x-w/2, y, d/2-.10)) for x in (xa, xb) for y in (ya, yb)]


ANCHORS = {
    "前景枯树": (-8.00, 5.30, 12.40),
    "左侧暖路灯": (-9.44, 7.22, 5.67),
    "雪地暖光池": (-10.95, 0.01, 3.20),
    "雪人": (0.65, 0.94, 2.40),
    "积雪长椅": (3.94, 0.58, 0.7),
    "值班室暖窗伏案人": guard_world((-.81, 1.68, 1.33)),
    "值班室小烟管": guard_world((1.23, 3.63, -.90)),
}


def camera(W, H):
    return Camera((-1.3, 6.8, 27.5), (-4.4, 3.7, -6.0), fov=44, W=W, H=H)


def build():
    return snow.build()

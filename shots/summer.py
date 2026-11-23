"""夏 · 雨棚街角。静帧审构图；雨棚滴水、避雨剪影为 Gate 2 落点。"""
from engine.render import Camera
from shots import summer_world as rain

NAME = "summer"
PHASE = 0.31
GATE1_DSTR = 0.25
VIGNETTE = 0.07
GRADE = dict(rain.GRADE, exposure=3.13, contrast=1.09, sat=1.02, lift=(0.012, 0.020, 0.040))
PAL = dict(chroma_w=4.2, extra=[(0.88, 0.29, 0.23), (0.98, 0.65, 0.39), (0.96, 0.87, 0.68)])
DENOISE = dict(rain.DENOISE, r=1)
RENDER = dict(rain.RENDER, dirt=0.36, streak=0.30, refl_clamp=2.4)
sky = rain.sky
setup = rain.setup
frame = rain.frame

ANCHORS = {
    "小卖部暖光雨棚": (3.7, 2.70, 1.50),
    "理发店灯柱": (1.72, 1.95, 0.20),
    "门前红汽车": (-2.8, 0.75, 3.00),
    "网吧红灯箱": (10.2, 5.45, 0.55),
    "同灯组湿地红倒光": (7.20, 0.03, 5.0),
    "雨棚滴水落点": (4.98, 0.16, 2.01),
    "避雨剪影预留（伞／猫二选一）": (4.6, 0.65, 1.48),
}


def camera(W, H):
    return Camera((-16.0, 5.05, 20.0), (2.4, 3.16, 0.7), fov=43, W=W, H=H)


def build():
    return rain.build()

"""冬 · 路灯下的家属院。静帧审构图；暖窗日常和蒸汽为后续落点。"""
from engine.render import Camera
from shots import winter_world as snow

NAME = "winter"
PHASE = 0.36
GATE1_DSTR = 0.25
VIGNETTE = 0.07
GRADE = dict(snow.GRADE, exposure=2.82, contrast=1.13, sat=0.98, lift=(0.016, 0.024, 0.048))
PAL = dict(chroma_w=3.9, extra=[(0.78, 0.82, 0.88), (0.62, 0.68, 0.78), (0.90, 0.60, 0.39)])
DENOISE = dict(r=1, sl=0.11)
RENDER = dict(snow.RENDER, dirt=0.34, streak=0.25)
sky = snow.sky
setup = snow.setup
frame = snow.frame

ANCHORS = {
    "前景枯树": (-6.15, 5.30, 12.50),
    "左侧暖路灯": (-9.44, 7.22, 5.67),
    "雪地暖光池": (-10.95, 0.01, 3.20),
    "雪人": (0.65, 0.94, 2.40),
    "积雪长椅": (3.94, 0.58, 0.7),
    "伏案暖窗预留": (17.64, 8.18, -44.88),
    "排气白烟预留": (-5.55, 3.90, -24.6),
}


def camera(W, H):
    return Camera((-1.3, 6.8, 27.5), (-4.4, 3.7, -6.0), fov=44, W=W, H=H)


def build():
    return snow.build()

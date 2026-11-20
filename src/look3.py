"""Impressionist lighting & color keyframes across the 120s Sunday on the Seine.

Built directly on CodePaint-Engine's anim.paint.light keyframe interpolator:
  0 - 28s  : Act I   — Misty poppy morning warming into bright cobalt & scarlet sunshine
 28 - 54s  : Act II  — Radiant late-morning stone viaduct, drifting cloud shadows, sunlit steam
 54 - 84s  : Act III — Breezy turquoise-emerald noon regatta & dappled golden willow shade
 84 - 120s : Act IV  — Amber-crimson sunset & deep cobalt-indigo twilight with glowing lanterns
"""
from anim.paint.light import KEYS, key, look, sundir, c
import numpy as np

KEYS.clear()

# 0s: Soft morning mist on the poppy hill, fading in from raw flax linen
key(
    0.0,
    sun=sundir(102, 22),
    zen=c(88, 142, 214),
    mid=c(146, 192, 234),
    hor=c(244, 218, 192),
    glow=c(255, 224, 178),
    glow_wide=0.14,
    glow_tight=0.28,
    cover=0.40,
    cloud_lit=c(255, 246, 232),
    cloud_sh=c(172, 184, 218),
    cloud_op=0.84,
    light=c(255, 244, 224),
    shade=c(184, 196, 228),
    haze=c(212, 214, 226),
    hazesun=c(255, 228, 196),
    vis=360.0,
    hazemax=0.84,
    water_tint=np.array([0.16, 0.34, 0.38, 0.22], np.float32),
    deep=c(46, 102, 118),
    mirror_gain=0.92,
    mirror_a=0.84,
    ripple=0.90,
    wind=0.95,
    wind_dir=0.45,
    sundisc=0.35,
    sun_col=c(255, 232, 190),
    stars=0.0,
    glitter=0.60,
    expo=1.02,
    sat=1.08,
    mist=0.20,
    cloudsh=0.38,
    lamps=0.0,
    fade=1.0,
    fade_rgb=c(230, 220, 198),
)

# 3.5s: Canvas fully revealed; fresh luminous Seine morning
key(3.5, fade=0.0, mist=0.06)

# 14s: Peak Act I — vibrant scarlet poppies, crisp azure sky, active cloud shadows
key(
    14.0,
    sun=sundir(115, 34),
    zen=c(64, 128, 214),
    mid=c(126, 184, 236),
    hor=c(224, 228, 222),
    glow=c(255, 240, 204),
    cover=0.42,
    cloud_lit=c(255, 252, 244),
    cloud_sh=c(164, 182, 218),
    light=c(255, 249, 236),
    shade=c(166, 184, 226),
    haze=c(192, 212, 234),
    hazesun=c(248, 236, 214),
    vis=440.0,
    hazemax=0.80,
    mist=0.0,
    cloudsh=0.48,
    wind=1.12,
    sundisc=0.22,
    glitter=0.72,
    sat=1.14,
)

# 34s: Act II — Stone railway viaduct & sunlit Seine basin
key(
    34.0,
    sun=sundir(130, 44),
    zen=c(58, 122, 212),
    mid=c(118, 178, 236),
    hor=c(216, 226, 228),
    glow=c(255, 244, 212),
    cover=0.45,
    cloud_lit=c(255, 253, 246),
    cloud_sh=c(158, 178, 216),
    light=c(255, 250, 240),
    shade=c(152, 176, 222),
    haze=c(184, 208, 232),
    hazesun=c(245, 238, 220),
    vis=470.0,
    deep=c(36, 98, 114),
    water_tint=np.array([0.14, 0.36, 0.38, 0.24], np.float32),
    glitter=0.88,
    cloudsh=0.52,
    wind=1.18,
    ripple=1.05,
    sundisc=0.15,
    sat=1.12,
)

# 58s: Act III — Breezy midday regatta with sparkling turquoise water & white sails
key(
    58.0,
    sun=sundir(148, 48),
    zen=c(54, 118, 208),
    mid=c(112, 176, 234),
    hor=c(214, 224, 228),
    cover=0.40,
    light=c(255, 252, 244),
    shade=c(146, 172, 222),
    deep=c(32, 92, 116),
    water_tint=np.array([0.12, 0.34, 0.40, 0.22], np.float32),
    glitter=0.95,
    wind=1.35,
    ripple=1.22,
    cloudsh=0.45,
    sat=1.15,
)

# 78s: Emerging from willow shade into golden afternoon light
key(
    78.0,
    sun=sundir(172, 26),
    zen=c(74, 114, 192),
    mid=c(154, 168, 212),
    hor=c(248, 204, 152),
    glow=c(255, 216, 146),
    glow_wide=0.18,
    glow_tight=0.35,
    cover=0.44,
    cloud_lit=c(255, 224, 176),
    cloud_sh=c(148, 138, 188),
    light=c(255, 224, 176),
    shade=c(142, 142, 202),
    haze=c(216, 188, 194),
    hazesun=c(255, 208, 150),
    vis=390.0,
    deep=c(34, 72, 94),
    water_tint=np.array([0.22, 0.28, 0.34, 0.25], np.float32),
    glitter=1.05,
    wind=0.85,
    ripple=0.92,
    sundisc=0.65,
    sun_col=c(255, 206, 134),
    lamps=0.25,
    sat=1.15,
)

# 94s: Act IV — Blazing Monet sunset at the Guinguette cafe; warm string lanterns light up
key(
    94.0,
    sun=sundir(184, 11),
    zen=c(46, 58, 134),
    mid=c(142, 94, 158),
    hor=c(252, 134, 78),
    glow=c(255, 156, 82),
    glow_wide=0.24,
    glow_tight=0.44,
    cover=0.38,
    cloud_lit=c(255, 170, 108),
    cloud_sh=c(112, 74, 138),
    light=c(255, 188, 122),
    shade=c(104, 98, 168),
    haze=c(196, 126, 146),
    hazesun=c(255, 150, 88),
    vis=360.0,
    deep=c(30, 44, 88),
    water_tint=np.array([0.26, 0.16, 0.30, 0.26], np.float32),
    mirror_gain=0.96,
    mirror_a=0.88,
    glitter=1.15,
    wind=0.55,
    ripple=0.78,
    sundisc=1.0,
    sun_col=c(255, 142, 62),
    lamps=1.0,
    stars=0.25,
    cloudsh=0.20,
    expo=1.02,
    sat=1.16,
)

# 108s: Deep cobalt-indigo & crimson-rose twilight, twinkling first stars & glowing water reflections
key(
    108.0,
    sun=sundir(188, 2),
    zen=c(20, 28, 84),
    mid=c(72, 54, 126),
    hor=c(216, 86, 82),
    glow=c(244, 114, 76),
    glow_wide=0.22,
    glow_tight=0.36,
    cover=0.32,
    cloud_lit=c(222, 118, 102),
    cloud_sh=c(64, 52, 108),
    light=c(236, 158, 116),
    shade=c(76, 78, 144),
    haze=c(116, 82, 130),
    hazesun=c(224, 106, 80),
    vis=390.0,
    deep=c(18, 26, 68),
    water_tint=np.array([0.18, 0.12, 0.28, 0.28], np.float32),
    glitter=0.65,
    wind=0.38,
    ripple=0.62,
    sundisc=0.50,
    sun_col=c(244, 102, 58),
    lamps=1.0,
    stars=1.0,
    cloudsh=0.0,
    expo=1.04,
    sat=1.15,
)

# 115.5s -> 120.0s: Painterly dissolve back to warm flax canvas
key(115.5, fade=0.0)
key(120.0, fade=1.0, fade_rgb=c(230, 220, 198))


def light_at(t):
    return look(float(t))

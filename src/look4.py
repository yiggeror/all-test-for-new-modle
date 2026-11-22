"""Vivid, jewel-toned Monet lighting & dreamy veil cross-dissolves across 6 scenes (120.0s)."""
import numpy as np
from anim.paint.light import c, sundir
from anim.paint.engine import smooth

FILM_DUR = 120.0
SCENE_DUR = 20.0


def _lerp_dict(a, b, w):
    w = float(w)
    w = w * w * (3.0 - 2.0 * w)
    out = {}
    for k in a:
        out[k] = a[k] * (1.0 - w) + b[k] * w
        if isinstance(out[k], np.ndarray) and k != "sun":
            out[k] = out[k].astype(np.float32)
    return out


# Scene-specific jewel-toned Impressionist palettes
def light_scene1(lt):
    # Radiant Rose-Gold Morning over Scarlet Poppies & Cornflowers
    a = dict(
        sun=sundir(108, 28),
        zen=c(54, 118, 212), mid=c(134, 186, 238), hor=c(252, 224, 198),
        glow=c(255, 228, 178), glow_wide=0.18, glow_tight=0.34,
        cover=0.42, cloud_lit=c(255, 248, 236), cloud_sh=c(176, 174, 218), cloud_op=0.86,
        light=c(255, 246, 226), shade=c(156, 176, 228),
        haze=c(206, 214, 236), hazesun=c(255, 234, 202), vis=390.0, hazemax=0.82,
        water_tint=np.array([0.14, 0.34, 0.42, 0.22], np.float32), deep=c(38, 96, 124),
        mirror_gain=0.94, mirror_a=0.84, ripple=0.9, wind=1.1, wind_dir=0.45,
        sundisc=0.45, sun_col=c(255, 232, 184), stars=0.0, moon=0.0, glitter=0.75,
        expo=1.03, sat=1.20, mist=0.14, cloudsh=0.45, lamps=0.0,
        ground=c(230, 220, 198), fade=0.0, fade_rgb=c(236, 226, 206),
    )
    b = dict(a)
    b.update(sun=sundir(116, 36), zen=c(46, 110, 214), mid=c(116, 180, 238), hor=c(236, 232, 220), mist=0.02, sat=1.22)
    return _lerp_dict(a, b, smooth(0.0, 14.0, lt))


def light_scene2(lt):
    # Giverny Enchanted Waterlily Pond — Emerald, Turquoise, Lilac Wisteria & Dappled Sun
    a = dict(
        sun=sundir(128, 42),
        zen=c(48, 118, 204), mid=c(118, 188, 232), hor=c(228, 234, 218),
        glow=c(255, 244, 196), glow_wide=0.18, glow_tight=0.34,
        cover=0.36, cloud_lit=c(255, 250, 240), cloud_sh=c(166, 178, 222), cloud_op=0.82,
        light=c(255, 248, 224), shade=c(138, 168, 216),
        haze=c(184, 214, 222), hazesun=c(252, 240, 206), vis=340.0, hazemax=0.78,
        water_tint=np.array([0.10, 0.36, 0.38, 0.24], np.float32), deep=c(24, 88, 102),
        mirror_gain=0.96, mirror_a=0.88, ripple=0.65, wind=0.75, wind_dir=0.5,
        sundisc=0.25, sun_col=c(255, 242, 192), stars=0.0, moon=0.0, glitter=0.85,
        expo=1.04, sat=1.24, mist=0.05, cloudsh=0.35, lamps=0.45,
        ground=c(230, 220, 198), fade=0.0, fade_rgb=c(244, 236, 222),
    )
    return a


def light_scene3(lt):
    # Radiant Noon Argenteuil Viaduct, Steam Train & Regatta Sails
    a = dict(
        sun=sundir(140, 46),
        zen=c(44, 112, 210), mid=c(112, 178, 236), hor=c(222, 232, 228),
        glow=c(255, 246, 212), glow_wide=0.14, glow_tight=0.30,
        cover=0.44, cloud_lit=c(255, 254, 248), cloud_sh=c(156, 176, 218), cloud_op=0.86,
        light=c(255, 252, 242), shade=c(142, 168, 222),
        haze=c(186, 212, 236), hazesun=c(248, 242, 222), vis=450.0, hazemax=0.78,
        water_tint=np.array([0.12, 0.36, 0.42, 0.22], np.float32), deep=c(30, 96, 122),
        mirror_gain=0.95, mirror_a=0.86, ripple=1.10, wind=1.25, wind_dir=0.55,
        sundisc=0.22, sun_col=c(255, 244, 206), stars=0.0, moon=0.0, glitter=0.95,
        expo=1.03, sat=1.18, mist=0.0, cloudsh=0.48, lamps=0.0,
        ground=c(230, 220, 198), fade=0.0, fade_rgb=c(244, 238, 226),
    )
    return a


def light_scene4(lt):
    # Rouen Cathedral — Iridescent Molten Gold & Royal Violet Sunset
    a = dict(
        sun=sundir(165, 18),
        zen=c(64, 72, 152), mid=c(164, 112, 174), hor=c(255, 162, 108),
        glow=c(255, 188, 116), glow_wide=0.24, glow_tight=0.42,
        cover=0.40, cloud_lit=c(255, 198, 136), cloud_sh=c(126, 92, 156), cloud_op=0.86,
        light=c(255, 206, 138), shade=c(112, 102, 178),
        haze=c(196, 144, 174), hazesun=c(255, 184, 122), vis=340.0, hazemax=0.76,
        water_tint=np.array([0.24, 0.18, 0.32, 0.24], np.float32), deep=c(42, 46, 94),
        mirror_gain=0.95, mirror_a=0.86, ripple=0.7, wind=0.75, wind_dir=0.4,
        sundisc=0.85, sun_col=c(255, 172, 84), stars=0.10, moon=0.0, glitter=0.6,
        expo=1.04, sat=1.24, mist=0.04, cloudsh=0.20, lamps=0.85,
        ground=c(230, 220, 198), fade=0.0, fade_rgb=c(250, 222, 192),
    )
    b = dict(a)
    b.update(sun=sundir(172, 12), zen=c(50, 56, 138), mid=c(148, 92, 162), hor=c(255, 142, 92), lamps=1.0, sat=1.26)
    return _lerp_dict(a, b, smooth(0.0, 18.0, lt))


def light_scene5(lt):
    # Provence Lavender Waves & Turning Windmill under Magenta-Coral Sunset
    a = dict(
        sun=sundir(180, 10),
        zen=c(48, 52, 132), mid=c(156, 86, 158), hor=c(255, 132, 82),
        glow=c(255, 162, 88), glow_wide=0.26, glow_tight=0.46,
        cover=0.38, cloud_lit=c(255, 174, 108), cloud_sh=c(116, 72, 144), cloud_op=0.88,
        light=c(255, 192, 124), shade=c(104, 88, 172),
        haze=c(196, 120, 156), hazesun=c(255, 148, 92), vis=370.0, hazemax=0.78,
        water_tint=np.array([0.26, 0.14, 0.30, 0.25], np.float32), deep=c(36, 38, 86),
        mirror_gain=0.95, mirror_a=0.86, ripple=0.8, wind=1.35, wind_dir=0.4,
        sundisc=1.0, sun_col=c(255, 144, 64), stars=0.28, moon=0.0, glitter=0.8,
        expo=1.05, sat=1.26, mist=0.03, cloudsh=0.25, lamps=0.95,
        ground=c(230, 220, 198), fade=0.0, fade_rgb=c(246, 206, 188),
    )
    return a


def light_scene6(lt):
    # Venice San Giorgio Twilight Lagoon — Crimson, Indigo, Stars, Crescent Moon & Lanterns
    a = dict(
        sun=sundir(188, 3),
        zen=c(22, 30, 92), mid=c(86, 56, 138), hor=c(236, 94, 84),
        glow=c(252, 126, 82), glow_wide=0.22, glow_tight=0.38,
        cover=0.34, cloud_lit=c(234, 122, 108), cloud_sh=c(64, 50, 114), cloud_op=0.84,
        light=c(244, 166, 122), shade=c(72, 74, 146),
        haze=c(122, 78, 134), hazesun=c(238, 112, 82), vis=380.0, hazemax=0.80,
        water_tint=np.array([0.18, 0.12, 0.30, 0.28], np.float32), deep=c(18, 28, 76),
        mirror_gain=0.98, mirror_a=0.90, ripple=0.62, wind=0.45, wind_dir=0.3,
        sundisc=0.48, sun_col=c(248, 106, 62), stars=0.95, moon=0.95, glitter=0.85,
        expo=1.06, sat=1.22, mist=0.02, cloudsh=0.0, lamps=1.0,
        ground=c(230, 220, 198), fade=0.0, fade_rgb=c(230, 220, 198),
    )
    b = dict(a)
    b.update(zen=c(16, 22, 74), mid=c(66, 44, 118), hor=c(210, 78, 82), stars=1.0, moon=1.0, sundisc=0.18)
    return _lerp_dict(a, b, smooth(0.0, 14.0, lt))


_SCENE_LIGHTS = [light_scene1, light_scene2, light_scene3, light_scene4, light_scene5, light_scene6]


def scene_index_and_local_t(t_film: float):
    t = float(np.clip(t_film, 0.0, FILM_DUR - 1e-6))
    idx = min(5, int(t // SCENE_DUR))
    lt = t - idx * SCENE_DUR
    return idx, lt


def look_global(t_film: float):
    idx, lt = scene_index_and_local_t(t_film)
    L = _SCENE_LIGHTS[idx](lt)

    # Opening canvas reveal (0..2.4s)
    if t_film < 2.4:
        L["fade"] = float(smooth(2.4, 0.3, t_film))
        L["fade_rgb"] = c(230, 220, 198)
        return L

    # Closing canvas dissolve (116.2..120.0s)
    if t_film > 116.2:
        L["fade"] = float(smooth(116.2, 119.5, t_film))
        L["fade_rgb"] = c(230, 220, 198)
        return L

    # Dreamy golden-pearl veil cross-dissolves at scene transitions (0.55s out / 0.55s in)
    fade_val = 0.0
    if idx > 0 and lt < 0.60:
        fade_val = max(fade_val, float(smooth(0.60, 0.0, lt)) * 0.88)
    if idx < 5 and lt > SCENE_DUR - 0.60:
        fade_val = max(fade_val, float(smooth(SCENE_DUR - 0.60, SCENE_DUR, lt)) * 0.88)
    if fade_val > 0.005:
        L["fade"] = fade_val
        L["fade_rgb"] = c(246, 232, 210) if idx < 3 else c(244, 214, 198)
    return L

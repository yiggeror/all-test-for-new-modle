"""Continuous 120s 3D Camera Path & TimeWarp Story Pacing for Un Dimanche sur la Seine."""
import numpy as np
from anim.time import TimeWarp
from anim.paint.world3 import Path, Env
from anim.paint.engine import smooth
from scene_geom import river_x, river_hw, terrain_y
from actors3 import boy_pos_at, train_x_at, boat_pos_at
from look3 import light_at

FILM_DUR = 120.0

_RAW_SPEEDS = [
    (0.0, 0.95),
    (8.0, 0.90),
    (22.0, 1.00),
    (32.0, 1.08),
    (44.0, 0.92),
    (54.0, 0.94),
    (72.0, 0.96),
    (84.0, 0.92),
    (96.0, 0.90),
    (112.0, 1.00),
    (120.0, 1.00),
]
_WARP_RAW = TimeWarp(_RAW_SPEEDS, steps=4096)


def film_to_story(t_film: float) -> float:
    return float(_WARP_RAW.to_story(np.clip(t_film, 0.0, FILM_DUR) * (_WARP_RAW.duration / FILM_DUR)))


def _build_keys():
    rx = lambda z: float(river_x(z))
    rhw = lambda z: float(river_hw(z))

    b0 = boy_pos_at(4.0)
    b1 = boy_pos_at(14.0)
    b2 = boy_pos_at(22.0)

    k = [
        # Act I: Morning mist over poppy hill -> swoop cleanly alongside kite boy & dog -> toward river
        (0.0,   rx(-26) - 42.0, 21.0, -26.0,   rx(18) - 22.0,  7.0,  18.0, 56.0),
        (5.5,   b0[0] + 18.0,   b0[1] + 2.8, b0[2] - 11.0,  b0[0] - 1.5, b0[1] + 3.2, b0[2] + 3.5, 55.0),
        (14.0,  b1[0] + 17.5,   b1[1] + 2.4, b1[2] - 9.0,   b1[0] - 1.5, b1[1] + 3.5, b1[2] + 4.0, 56.0),
        (22.0,  b2[0] + 19.0,   b2[1] + 3.6, b2[2] - 3.0,   b2[0] + 2.0, b2[1] + 3.5, b2[2] + 12.0, 55.0),
        (28.0,  rx(118) - 4.0,  10.2, 118.0,   rx(175) + 4.0,  6.8,  175.0, 54.0),

        # Act II: Across Seine watching steam locomotive -> swoop INTO & UNDER central stone arch (Z=202..222)
        (36.0,  rx(154) + 12.0,  7.4, 154.0,   rx(215) - 10.0, 12.8, 215.0, 52.0),
        (43.0,  rx(184) + 2.0,   4.6, 184.0,   rx(215),         9.6, 215.0, 54.0),
        (47.2,  rx(202),         3.5, 202.0,   rx(235),         5.8, 235.0, 58.0),
        (52.5,  rx(244) + 5.0,   3.2, 244.0,   rx(295) - 6.0,   3.2, 295.0, 55.0),

        # Act III: Alongside & overtaking hero racing sloop (16m abeam so whole mast fits!) -> willow cove
        (60.0,  rx(320) + 12.0,  3.2, 312.0,   rx(326) - 8.0,   3.5, 326.0, 56.0),
        (68.0,  rx(346) + 10.0,  3.2, 342.0,   rx(354) - 10.0,  3.2, 354.0, 56.0),
        (76.5,  rx(352) - rhw(352) + 13.5, 2.5, 336.0, rx(362) - rhw(362) + 8.5, 2.4, 368.0, 56.0),
        (83.0,  rx(378) - rhw(378) + 16.0, 3.0, 374.0, rx(402) + 20.0, 3.4, 402.0, 55.0),

        # Act IV: Sunset Guinguette lantern terrace -> glide left & crane up looking back at glowing cafe + boats + stars!
        (91.0,  rx(398) + rhw(398) - 22.0, 3.5, 392.0, rx(406) + rhw(406) + 14.0, 3.8, 406.0, 54.0),
        (99.0,  rx(416) - 6.0,   4.8, 412.0,   rx(406) + rhw(406) + 12.0, 4.4, 406.0, 55.0),
        (108.0, rx(420) - 34.0, 10.5, 428.0,   rx(402) + 28.0, 7.8, 396.0, 58.0),
        (116.0, rx(426) - 42.0, 17.0, 438.0,   rx(395) + 22.0, 9.8, 385.0, 60.0),
        (120.0, rx(428) - 44.0, 18.5, 442.0,   rx(390) + 20.0, 10.5, 380.0, 60.0),
    ]
    return k


PATH = Path(_build_keys(), sigma=1.15, hz=40)
PATH.warp = film_to_story


def _post_cam(t_story, C0, T0):
    T = T0.copy()
    C = C0.copy()
    ty = float(terrain_y(C[0], C[2]))
    C[1] = max(C[1], ty + 1.45, 1.35)

    # 1. Track boy + soaring kite midpoint during Act I
    w_boy = float(smooth(5.0, 8.5, t_story) * smooth(23.5, 19.5, t_story))
    if w_boy > 0.01:
        pb = boy_pos_at(t_story)
        aim_b = pb + np.array([-1.0, 3.4, 2.5])
        T = T * (1.0 - 0.55 * w_boy) + aim_b * (0.55 * w_boy)

    # 2. Glance toward steam locomotive on the viaduct
    w_trn = float(smooth(31.0, 35.0, t_story) * smooth(43.0, 39.5, t_story))
    if w_trn > 0.01:
        tx = train_x_at(t_story)
        aim_t = np.array([tx - 3.0, 15.8, 215.0])
        T = T * (1.0 - 0.48 * w_trn) + aim_t * (0.48 * w_trn)

    # 3. Track hero sailboat with full mast headroom
    w_sail = float(smooth(54.0, 57.5, t_story) * smooth(72.5, 68.5, t_story))
    if w_sail > 0.01:
        ps = boat_pos_at(0, t_story)
        aim_s = ps + np.array([0.0, 3.4, 1.2])
        T = T * (1.0 - 0.52 * w_sail) + aim_s * (0.52 * w_sail)

    return C, T


PATH.post = _post_cam


def make_env(t_film: float) -> Env:
    return Env(float(t_film), PATH, light_at)

"""Dynamic 3D Actors, Steam Locomotive + Billowing Plume, Racing Sailboats & Wildlife."""
import math
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, LENS, WASH, C, mix, smooth, jitter
from anim.paint.world3 import SB, RIPPLE, STAND, OVER, _PASS, shade, haze_of
from scene_geom import river_x, river_hw, terrain_y
from rig3 import add_running_kite_boy, add_galloping_dog, add_strolling_person, add_sailor_crew


def _norm3(v):
    v = np.asarray(v, np.float64)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12)


# --------------------------------------------------------------------------- Act I: Boy, Dog & Soaring Kite
def boy_pos_at(t):
    """Sprint path safely inland up on the sunlit poppy hillside (sd ~ 24-30m)."""
    u = float(np.clip(t / 26.0, 0.0, 1.0))
    z = 8.0 + u * 84.0
    x = float(river_x(z) - river_hw(z)) - 26.0 + 4.5 * math.sin(u * 2.2)
    y = float(terrain_y(x, z))
    return np.array([x, y, z], np.float64)


def emit_act1_characters(env):
    t = env.t
    if t > 34.0:
        return []
    rng = np.random.default_rng(701)
    sb = SB(rng)

    p_boy = boy_pos_at(t)
    p_next = boy_pos_at(t + 0.15)
    vel = p_next - p_boy
    yaw = math.atan2(vel[0], vel[2]) if np.linalg.norm(vel) > 1e-4 else 0.1
    g_boy = float(env.wind(np.array([p_boy[0]]), np.array([p_boy[2]]))[0])

    k_phase = t * 1.45
    kite_pos = p_boy + np.array([
        -3.5 + 1.8 * math.sin(k_phase) + 1.4 * g_boy,
        9.4 + 1.4 * math.cos(k_phase * 0.85) + 1.1 * g_boy,
        6.5 + 1.3 * math.sin(k_phase * 0.65),
    ], np.float64)

    hand = add_running_kite_boy(sb, p_boy, yaw, t * 7.8, g_boy, kite_pos - p_boy)

    dog_offset = np.array([
        math.sin(yaw) * 3.0 + math.cos(yaw) * (1.8 + 0.7 * math.sin(t * 1.7)),
        0.0,
        math.cos(yaw) * 3.0 - math.sin(yaw) * 1.8,
    ])
    dog_p = p_boy + dog_offset
    dog_p[1] = float(terrain_y(dog_p[0], dog_p[2]))
    add_galloping_dog(sb, dog_p, yaw + 0.25 * math.cos(t * 1.7), t * 11.2)

    k_bank = 0.35 * math.cos(k_phase) + 0.25 * (g_boy - 0.5)
    k_right = _norm3(np.array([math.cos(k_bank), math.sin(k_bank) * 0.4, -0.25], np.float64))
    k_up = _norm3(np.array([-0.15, 0.86, 0.48], np.float64))
    k_n = np.cross(k_right, k_up)

    quads = [
        (k_up * 0.48 + k_right * 0.28, C(172, 34, 42), C(246, 62, 54)),
        (k_up * 0.48 - k_right * 0.28, C(196, 138, 36), C(254, 212, 72)),
        (-k_up * 0.52 + k_right * 0.24, C(42, 74, 152), C(76, 132, 224)),
        (-k_up * 0.52 - k_right * 0.24, C(172, 34, 42), C(246, 62, 54)),
    ]
    for q_off, qsh, qli in quads:
        sb.add([kite_pos + q_off], D=k_up, L=1.15, W=0.68, spr=DAB + 1, csh=qsh, cli=qli, N=k_n, smin=2.6)
    sb.add([kite_pos], D=k_up, L=1.85, W=0.09, spr=DASH, csh=C(92, 70, 48), cli=C(164, 126, 84), N=k_n, smin=2.0)
    sb.add([kite_pos + k_up * 0.15], D=k_right, L=1.45, W=0.09, spr=DASH, csh=C(92, 70, 48), cli=C(164, 126, 84), N=k_n, smin=2.0)

    tail_root = kite_pos - k_up * 0.88
    for i in range(11):
        u = (i + 0.5) / 11.0
        wob = 0.55 * u * math.sin(t * 7.5 - i * 0.75 + g_boy * 3.0)
        tp = tail_root - k_up * (u * 3.8) + np.array([env.wdir[0], -0.25, env.wdir[2]]) * (u * 2.5) + k_right * wob
        col_sh = C(172, 34, 42) if i % 2 == 0 else C(196, 146, 40)
        col_li = C(246, 68, 56) if i % 2 == 0 else C(254, 220, 82)
        sb.add([tp], D=-k_up + k_right * 0.3, L=0.52, W=0.14 if i % 2 == 0 else 0.22, spr=DAB if i % 2 == 1 else DASH, csh=col_sh, cli=col_li, N=k_n, smin=1.8)

    n_str = 14
    for i in range(n_str):
        u0, u1 = i / n_str, (i + 1) / n_str
        p_a = hand * (1.0 - u0) + kite_pos * u0 + np.array([0.0, -0.70 * math.sin(u0 * math.pi), 0.0])
        p_b = hand * (1.0 - u1) + kite_pos * u1 + np.array([0.0, -0.70 * math.sin(u1 * math.pi), 0.0])
        sb.add([(p_a + p_b) * 0.5], D=_norm3(p_b - p_a), L=float(np.linalg.norm(p_b - p_a)) * 1.15, W=0.045, spr=DASH, csh=C(196, 188, 172), cli=C(248, 242, 224), N=(0, 1, 0), smin=1.4)

    zm = 62.0 + 0.85 * t
    xm = float(river_x(zm) - river_hw(zm)) - 15.0
    ym = float(terrain_y(xm, zm))
    add_strolling_person(
        sb, (xm, ym, zm), 0.15, t * 2.8,
        dress_sh=C(152, 162, 198), dress_li=C(246, 242, 232),
        hat_sh=C(196, 174, 124), hat_li=C(250, 234, 182),
        parasol_cols=(C(52, 134, 146), C(116, 212, 214)),
    )
    add_strolling_person(
        sb, (xm - 1.05, float(terrain_y(xm - 1.05, zm - 0.3)), zm - 0.3), 0.12, t * 3.6 + 1.0,
        dress_sh=C(186, 118, 134), dress_li=C(248, 182, 188),
        hat_sh=C(196, 174, 124), hat_li=C(250, 234, 182),
    )

    # 5. Grazing spotted Normandy cows in upper hillside pasture + faint farmstead chimney smoke
    cow_coords = [(-44.0, 48.0, 0.4), (-48.0, 56.0, 1.1), (-56.0, 82.0, -0.5), (-61.0, 91.0, 0.2)]
    for ci, (ox, cz, cyaw) in enumerate(cow_coords):
        cx_c = float(river_x(cz) - river_hw(cz)) + ox
        cy_c = float(terrain_y(cx_c, cz))
        cfwd = np.array([math.sin(cyaw), 0.0, math.cos(cyaw)], np.float64)
        nod = 0.22 * math.sin(t * 0.7 + ci * 1.9)
        sb.add([[cx_c, cy_c + 0.92, cz]], D=cfwd, L=1.85, W=0.95, spr=DAB + 1, csh=C(176, 174, 190), cli=C(250, 246, 236), N=(0, 0.85, 0.2), smin=3.2)
        sb.add([[cx_c + cfwd[0] * 0.2, cy_c + 0.98, cz + cfwd[2] * 0.2]], D=cfwd, L=0.95, W=0.72, spr=DAB, csh=C(106, 62, 46), cli=C(168, 96, 62), N=(0, 0.9, 0.1), smin=2.8)
        sb.add([[cx_c + cfwd[0] * 0.98, cy_c + 0.78 + nod, cz + cfwd[2] * 0.98]], D=cfwd - np.array([0, 0.3, 0]), L=0.68, W=0.48, spr=DAB, csh=C(106, 62, 46), cli=C(172, 102, 66), N=(0, 0.7, 0.3), smin=2.6)

    fx = float(river_x(104.0) - river_hw(104.0)) - 62.0 + 3.0
    fy = float(terrain_y(fx, 104.0)) + 6.8
    for si in range(10):
        age = (si / 10.0) * 5.0 + (t * 0.8) % 0.5
        sp = np.array([fx + env.wdir[0] * age * 1.6, fy + age * 1.15, 104.0 + env.wdir[2] * age * 1.6])
        sb.add([sp], D=(env.wdir[0], 0.6, env.wdir[2]), L=1.1 + age * 0.45, W=0.8 + age * 0.35, spr=SCUM + (si % 4), csh=C(168, 174, 198), cli=C(246, 244, 242), N=(0, 1, 0), a=max(0.05, 0.48 * (1.0 - age / 5.5)), smin=3.5)

    grp = sb.group(reflect=False, passid=STAND, name="act1_chars")
    return [shade(env, grp.lod(env), sway=False)] if grp and grp.visible(env) else []


# --------------------------------------------------------------------------- Act II: Steam Train & Billowing Smoke
def train_x_at(t):
    cx = float(river_x(215.0))
    return cx - 98.0 + (t - 24.0) * 6.4


def emit_steam_train(env):
    t = env.t
    if t < 18.0 or t > 62.0:
        return []

    rng = np.random.default_rng(702)
    sb = SB(rng)
    smoke_sb = SB(rng)

    zv = 215.0
    deck_y = 14.35
    lx = train_x_at(t)

    loco_sh = C(36, 68, 62)
    loco_li = C(74, 126, 98)
    brass_sh = C(152, 112, 52)
    brass_li = C(244, 198, 98)
    iron_sh = C(34, 36, 44)
    iron_li = C(74, 78, 92)

    for x in np.linspace(lx - 5.2, lx, 11):
        sb.add([[x, deck_y + 1.55, zv]], D=(1, 0, 0), L=1.15, W=1.38, spr=DAB, csh=loco_sh, cli=loco_li, N=(0, 0.5, -0.8), smin=3.5)
    sb.add([[lx - 2.6, deck_y + 2.45, zv]], D=(0, 1, 0), L=0.85, W=0.68, spr=DAB, csh=brass_sh, cli=brass_li, N=(0, 0.6, -0.8), smin=3.0)
    chimney_x = lx - 0.85
    sb.add([[chimney_x, deck_y + 2.85, zv]], D=(0, 1, 0), L=1.35, W=0.44, spr=DASH, csh=iron_sh, cli=iron_li, N=(0, 0.3, -0.9), smin=3.0)
    sb.add([[lx - 6.2, deck_y + 1.85, zv]], D=(0, 1, 0), L=2.4, W=1.9, spr=DAB + 1, csh=loco_sh, cli=loco_li, N=(0, 0.3, -0.9), smin=3.5)
    sb.add([[lx - 5.9, deck_y + 1.15, zv - 0.8]], D=(1, 0, 0), L=0.75, W=0.55, spr=LENS, csh=C(255, 132, 42), cli=C(255, 198, 86), N=(0, 0, -1), emis=0.95, smin=2.5)
    for wx_off in (-1.3, -3.1, -4.8):
        wx = lx + wx_off
        sb.add([[wx, deck_y + 0.58, zv - 0.85]], D=(1, 0, 0), L=1.15, W=1.12, spr=DAB + 2, csh=C(122, 42, 40), cli=C(196, 68, 56), N=(0, 0, -1), smin=2.8)
    rod_ang = lx * 1.4
    ry = deck_y + 0.58 + 0.26 * math.sin(rod_ang)
    rx = 0.26 * math.cos(rod_ang)
    sb.add([[lx - 3.05 + rx, ry, zv - 0.96]], D=(1, 0, 0), L=3.7, W=0.14, spr=DASH, csh=C(142, 146, 158), cli=C(238, 236, 224), N=(0, 0, -1), smin=2.2)

    for c_idx in range(4):
        cx_c = lx - 9.2 - c_idx * 8.6
        for x in np.linspace(cx_c - 3.5, cx_c + 3.5, 10):
            sb.add([[x, deck_y + 1.35, zv]], D=(1, 0, 0), L=1.35, W=1.28, spr=DAB, csh=C(92, 54, 48), cli=C(176, 98, 72), N=(0, 0.2, -0.95), smin=3.8)
            sb.add([[x, deck_y + 2.25, zv]], D=(1, 0, 0), L=1.35, W=0.86, spr=DAB + 1, csh=C(138, 134, 148), cli=C(236, 224, 198), N=(0, 0.4, -0.9), smin=3.6)
        sb.add([[cx_c, deck_y + 2.82, zv]], D=(1, 0, 0), L=7.8, W=0.55, spr=DASH, csh=C(68, 70, 84), cli=C(134, 136, 148), N=(0, 0.95, 0), smin=4.0)
        for wx_w in (-2.3, -0.8, 0.8, 2.3):
            sb.add([[cx_c + wx_w, deck_y + 2.15, zv - 0.92]], D=(1, 0, 0), L=0.84, W=0.58, spr=DAB, csh=C(72, 92, 128), cli=C(252, 222, 158), N=(0, 0.1, -1), emis=0.35, smin=2.8)

    n_puffs = 60
    for i in range(n_puffs):
        age = (i / n_puffs) * 7.5 + (t * 2.2 - math.floor(t * 2.2)) * (7.5 / n_puffs)
        t_emit = t - age
        sx_emit = train_x_at(t_emit) - 0.85
        rise = 2.6 * (age ** 0.72)
        px = sx_emit - 1.2 * age + env.wdir[0] * 1.45 * age + 0.65 * math.sin(i * 2.3 + t * 0.9)
        py = deck_y + 3.45 + rise + 0.35 * math.cos(i * 1.7 + t * 1.1)
        pz = zv + env.wdir[2] * 1.65 * age + 0.55 * math.sin(i * 3.1 + t * 0.8)
        sz = 0.95 + age * 0.72
        fade_a = max(0.0, (1.0 - age / 7.5)) ** 1.15 * 0.78
        if fade_a > 0.03:
            smoke_sb.add(
                [[px, py, pz]], D=(env.wdir[0] - 0.3, 0.45, env.wdir[2]),
                L=sz * 1.5, W=sz * 1.15, spr=SCUM + (i % 4),
                csh=C(164, 168, 194), cli=C(252, 248, 242), N=(0.2, 0.9, -0.3),
                a=fade_a, smin=4.5,
            )

    out = []
    grp = sb.group(reflect=True, passid=STAND, name="steam_train")
    if grp and grp.visible(env):
        A = grp.lod(env)
        out.append(shade(env, A, mirror=False, sway=False))
        out.append(shade(env, A, mirror=True, sway=False))
    sgrp = smoke_sb.group(reflect=True, passid=STAND, name="steam_smoke")
    if sgrp and sgrp.visible(env):
        As = sgrp.lod(env)
        out.append(shade(env, As, mirror=False, sway=False))
        out.append(shade(env, As, mirror=True, sway=False))
    return out


# --------------------------------------------------------------------------- Act III: Solid-Sail Racing Sailboats
_BOATS = [
    (0, 128.0, 3.25, -0.18, 1.28, C(34, 48, 72), C(82, 108, 146), C(186, 194, 218), C(255, 252, 242), True),
    (1, 152.0, 2.85,  0.22, 1.05, C(124, 42, 42), C(208, 76, 62), C(196, 190, 212), C(254, 246, 228), False),
    (2, 178.0, 2.55, -0.40, 0.95, C(46, 86, 82), C(96, 156, 134), C(186, 194, 218), C(252, 248, 236), False),
    (3, 210.0, 2.95,  0.34, 1.00, C(132, 92, 48), C(214, 156, 78), C(194, 188, 214), C(255, 244, 224), False),
    (4, 250.0, 2.40, -0.22, 0.92, C(44, 58, 96), C(88, 118, 176), C(188, 194, 216), C(252, 250, 240), False),
    (5, 290.0, 2.75,  0.14, 1.08, C(118, 48, 56), C(196, 82, 84), C(192, 196, 218), C(255, 250, 238), False),
    (6, 335.0, 2.20,  0.38, 0.88, C(62, 88, 72), C(122, 158, 118), C(186, 190, 212), C(248, 244, 230), False),
]


def boat_pos_at(idx, t):
    _, z0, spd, x_rat, _, _, _, _, _, _ = _BOATS[idx]
    z = z0 + t * spd + 3.5 * math.sin(t * 0.22 + idx)
    x = float(river_x(z)) + x_rat * float(river_hw(z)) + 4.2 * math.sin(t * 0.16 + idx * 1.4)
    return np.array([x, 0.0, z], np.float64)


def emit_sailboats(env):
    t = env.t
    rng = np.random.default_rng(703)
    sb = SB(rng)
    wake_pts = []
    lamps = float(env.L.get("lamps", 0.0))

    for b in _BOATS:
        idx, _, _, _, sc, h_sh, h_li, s_sh, s_li, is_hero = b
        p = boat_pos_at(idx, t)
        p_next = boat_pos_at(idx, t + 0.25)
        fwd = _norm3(p_next - p)
        right = np.array([fwd[2], 0.0, -fwd[0]], np.float64)
        up_w = np.array([0.0, 1.0, 0.0], np.float64)

        g = float(env.wind(np.array([p[0]]), np.array([p[2]]))[0])
        heel = (0.14 + 0.20 * g) * (1.0 if idx % 2 == 0 else -1.0)
        bob = 0.07 * math.sin(t * 2.1 + idx * 1.7)
        up = up_w * math.cos(heel) + right * math.sin(heel)
        right_h = right * math.cos(heel) - up_w * math.sin(heel)
        origin = p + np.array([0.0, bob + 0.18 * sc, 0.0])

        # Solid wood/painted hull (filled deck, gunwales, and crimson waterline — zero hollow gaps!)
        for u in np.linspace(-2.7, 2.8, 12):
            w_h = (1.0 - (u / 3.0) ** 2) ** 0.55 * 1.08 * sc
            # Centerline teak deck planks
            sb.add([origin + fwd * (u * sc) + up * 0.20 * sc], D=fwd, L=1.15 * sc, W=max(0.32, w_h * 1.15) * sc, spr=DASH, csh=C(108, 80, 56), cli=C(186, 144, 98), N=up, smin=2.8, a=0.96)
            for side in (-1.0, 1.0):
                hp = origin + fwd * (u * sc) + right_h * (side * w_h * 0.72) + up * 0.12 * sc
                sb.add([hp], D=fwd, L=1.15 * sc, W=0.58 * sc, spr=DASH + 1, csh=h_sh, cli=h_li, N=right_h * side + up * 0.35, smin=2.8, a=0.98)
            if abs(u) < 2.4:
                sb.add([origin + fwd * (u * sc) + right_h * (w_h * 0.78) - up * 0.06 * sc], D=fwd, L=1.1 * sc, W=0.26 * sc, spr=DASH, csh=C(128, 36, 36), cli=C(212, 62, 52), N=right_h, smin=2.4)

        # Mast & boom
        mast_h = 6.2 * sc
        mast_top = origin + up * mast_h
        for mu in np.linspace(0.05, 0.96, 7):
            sb.add([origin + up * (mu * mast_h)], D=up, L=1.25 * sc, W=0.18 * sc, spr=DASH, csh=C(92, 70, 52), cli=C(176, 138, 96), N=right_h, smin=2.2)
        sb.add([origin + up * 0.75 * sc - fwd * 1.5 * sc], D=fwd, L=3.3 * sc, W=0.16 * sc, spr=DASH, csh=C(92, 70, 52), cli=C(176, 138, 96), N=up, smin=2.2)

        # Dense, continuous billowing mainsail (no patchy gaps!)
        camber_dir = right_h * (1.0 if heel >= 0 else -1.0)
        n_rows = 12 if is_hero else 9
        for r_i in range(n_rows):
            v = (r_i + 0.5) / n_rows
            h_s = (0.82 + v * 5.0) * sc
            chord = (1.0 - v * 0.90) * 3.1 * sc
            nc = max(2, int(round((1.0 - v * 0.80) * (7 if is_hero else 5))))
            for c_i in range(nc):
                u_c = (c_i + 0.5) / nc
                billow = math.sin(u_c * math.pi) * (0.35 + 0.32 * g) * sc
                sp = origin + up * h_s - fwd * (u_c * chord - 0.12 * sc) + camber_dir * billow
                N_s = _norm3(camber_dir + up * 0.25 - fwd * 0.15)
                sb.add([sp], D=up - fwd * 0.28, L=1.18 * sc, W=0.88 * sc, spr=DASH + ((r_i + c_i) % 8), csh=s_sh, cli=s_li, N=N_s, smin=3.0, a=0.95)

        # Dense forward jib sail
        n_jib = 8 if is_hero else 6
        for r_i in range(n_jib):
            v = (r_i + 0.5) / n_jib
            h_s = (0.72 + v * 4.3) * sc
            chord_j = (1.0 - v * 0.85) * 1.8 * sc
            for c_i in range(max(1, int(round((1.0 - v * 0.7) * 3)))):
                uc = (c_i + 0.5) / max(1, int(round((1.0 - v * 0.7) * 3)))
                sp = origin + up * h_s + fwd * (0.35 * sc + (1.0 - uc) * chord_j) + camber_dir * (0.22 * math.sin(v * math.pi) * sc)
                sb.add([sp], D=up - fwd * 0.42, L=1.10 * sc, W=0.76 * sc, spr=DASH + (r_i % 6), csh=s_sh, cli=s_li, N=camber_dir, smin=2.8, a=0.94)

        # Fluttering masthead crimson pennant
        for k in range(5):
            u = (k + 0.5) / 5.0
            flut = 0.22 * u * math.sin(t * 9.5 - k * 1.1 + idx)
            fp = mast_top + up * 0.12 - fwd * (u * 1.45 * sc) + camber_dir * (u * 0.45 + flut)
            sb.add([fp], D=-fwd + camber_dir * 0.2, L=0.38 * sc, W=0.14 * sc, spr=DASH + 2, csh=C(164, 34, 42), cli=C(246, 68, 56), N=up, smin=1.8)

        if lamps > 0.05:
            sb.add([mast_top - up * 0.25], D=up, L=0.52 * sc, W=0.52 * sc, spr=LENS, csh=C(255, 194, 84), cli=C(255, 228, 128), N=up, emis=lamps, a=min(1.0, 0.35 + 0.65 * lamps), smin=2.2)

        if is_hero:
            add_sailor_crew(sb, origin - fwd * 0.65, fwd, right_h, up, camber_dir, t * 2.8)
            add_sailor_crew(sb, origin - fwd * 1.45, fwd, right_h, up, camber_dir, t * 2.8 + 1.4)
        else:
            add_sailor_crew(sb, origin - fwd * 0.85, fwd, right_h, up, camber_dir, t * 2.4 + idx)

        for w_i in range(14):
            wu = (w_i + 0.5) / 14.0
            wz_back = -2.2 * sc - wu * 11.5 * sc
            spread = (0.55 + wu * 3.1) * sc
            for side in (-1.0, 1.0):
                wp = p + fwd * wz_back + right * (side * spread)
                a_w = (1.0 - wu) ** 1.2 * 0.48
                wake_pts.append((wp[0], 0.04, wp[2], fwd[0] + right[0] * side * 0.35, fwd[2] + right[2] * side * 0.35, 1.25 * sc, 0.34 * sc, a_w))

    out = []
    grp = sb.group(reflect=True, passid=STAND, name="sailboats")
    if grp and grp.visible(env):
        A = grp.lod(env)
        out.append(shade(env, A, mirror=False, sway=False))
        out.append(shade(env, A, mirror=True, sway=False))

    if wake_pts:
        wp = np.array(wake_pts, np.float64)
        P = wp[:, 0:3]
        v = P - env.C
        vr, vu, vf = v @ env.rt, v @ env.up, v @ env.fw
        ok = vf > 0.35
        if ok.any():
            idx = np.nonzero(ok)[0]
            sc = env.f / vf[idx]
            x = 960.0 + vr[idx] * sc
            y = 540.0 - vu[idx] * sc
            vis = (x > -180) & (x < 2100) & (y > -180) & (y < 1260)
            if vis.any():
                ii = idx[vis]
                scv = sc[vis]
                col = mix(env.L["deep"][None, :], env.L["light"][None, :], np.full(len(ii), 0.72, np.float32))
                col = haze_of(env, col, np.maximum(vf[ii], 1.0), amt=0.85)
                out.append(dict(
                    x=x[vis].astype(np.float32),
                    y=y[vis].astype(np.float32),
                    ang=np.arctan2(-wp[ii, 4], wp[ii, 3]).astype(np.float32),
                    L=(wp[ii, 5] * scv).astype(np.float32),
                    W=(wp[ii, 6] * scv).astype(np.float32),
                    spr=np.full(len(ii), DASH + 2, np.int32),
                    rgb=np.clip(col, 0.0, 1.15).astype(np.float32),
                    a=wp[ii, 7].astype(np.float32),
                    hb=np.full(len(ii), 0.55, np.float32),
                    key=(RIPPLE * _PASS + 1e6 - vf[ii]).astype(np.float64),
                ))
    return out


# --------------------------------------------------------------------------- Swans, Swallows, Petals, Cafe Crowd & Fireflies
def emit_wildlife_and_cafe(env):
    t = env.t
    rng = np.random.default_rng(704)
    sb_ref = SB(rng)
    sb_over = SB(rng)
    rip_pts = []

    for s_i, (sz0, sx_off) in enumerate([(345.0, 12.0), (368.0, 15.5)]):
        sz = sz0 + math.sin(t * 0.14 + s_i) * 14.0
        sx = float(river_x(sz) - river_hw(sz)) + sx_off + math.cos(t * 0.18 + s_i) * 3.5
        vx = -3.5 * 0.18 * math.sin(t * 0.18 + s_i)
        vz = 14.0 * 0.14 * math.cos(t * 0.14 + s_i)
        fwd = _norm3(np.array([vx, 0.0, vz], np.float64))
        up = np.array([0.0, 1.0, 0.0])
        sp = np.array([sx, 0.18, sz])
        sb_ref.add([sp], D=fwd, L=0.95, W=0.52, spr=DAB + 1, csh=C(186, 192, 212), cli=C(254, 252, 246), N=up, smin=2.2)
        sb_ref.add([sp + up * 0.18 - fwd * 0.15], D=fwd, L=0.72, W=0.45, spr=DAB, csh=C(194, 198, 218), cli=C(255, 254, 250), N=up, smin=2.2)
        neck = sp + fwd * 0.38 + up * 0.42
        sb_ref.add([neck], D=up + fwd * 0.25, L=0.52, W=0.14, spr=DASH, csh=C(186, 192, 212), cli=C(254, 252, 246), N=up, smin=1.8)
        sb_ref.add([neck + up * 0.24 + fwd * 0.10], D=fwd, L=0.22, W=0.14, spr=DAB, csh=C(186, 192, 212), cli=C(254, 252, 246), N=up, smin=1.8)
        sb_ref.add([neck + up * 0.22 + fwd * 0.22], D=fwd, L=0.14, W=0.07, spr=DAB, csh=C(196, 102, 42), cli=C(248, 138, 48), N=up, smin=1.6)
        for r_k in range(3):
            rr = 0.65 + ((t * 0.6 + r_k * 0.33 + s_i * 0.5) % 1.0) * 2.2
            a_r = (1.0 - rr / 2.85) * 0.38
            if a_r > 0.04:
                for th in np.linspace(0, 2 * math.pi, 8, endpoint=False):
                    rip_pts.append((sx + math.cos(th) * rr, 0.03, sz + math.sin(th) * rr, -math.sin(th), math.cos(th), 0.75, 0.14, a_r))

    if t > 62.0:
        zc = 406.0
        qx = float(river_x(zc) + river_hw(zc)) + 4.5
        guests = [
            (qx + 1.5, zc - 8.0 + (t * 0.65) % 16.0, 0.05, C(46, 62, 108), C(86, 114, 178), C(48, 48, 56), C(88, 88, 98), None),
            (qx + 3.0, zc - 6.8 + (t * 0.65) % 16.0, -0.05, C(168, 72, 86), C(244, 136, 148), C(214, 192, 142), C(252, 236, 188), (C(186, 86, 98), C(248, 162, 168))),
            (qx + 5.8, zc + 10.0 - (t * 0.55) % 18.0, math.pi, C(78, 114, 92), C(138, 184, 142), C(196, 172, 124), C(248, 228, 176), None),
        ]
        for gx, gz, gyaw, dsh, dli, hsh, hli, pcols in guests:
            add_strolling_person(sb_ref, (gx, float(terrain_y(gx, gz)), gz), gyaw, t * 2.4, dsh, dli, hsh, hli, pcols)

    # Towpath couples & moored wooden skiffs along the right shore (Z = 180..418)
    for idx_w, (wz0, wspd, dcol, pcol) in enumerate([
        (165.0, 0.55, (C(164, 72, 84), C(242, 132, 142)), (C(54, 126, 138), C(118, 206, 208))),
        (268.0, -0.45, (C(64, 92, 142), C(118, 158, 218)), None),
        (318.0, 0.50, (C(178, 148, 82), C(248, 218, 134)), (C(182, 76, 88), C(248, 152, 162))),
    ]):
        wz = wz0 + ((t * wspd) % 24.0)
        wx = float(river_x(wz) + river_hw(wz)) + 8.0 + idx_w * 0.8
        add_strolling_person(sb_ref, (wx, float(terrain_y(wx, wz)), wz), 0.0 if wspd > 0 else math.pi, t * 2.2, dcol[0], dcol[1], C(196, 174, 124), C(250, 234, 182), pcol)

    # Moored wooden skiffs gently rocking by Guinguette pier & regatta bank
    for ms_i, (mz, mx_off, myaw) in enumerate([(390.5, -5.5, 0.2), (396.5, -4.2, -0.15), (275.0, -4.8, 0.1)]):
        mx = float(river_x(mz) + river_hw(mz)) + mx_off
        pitch = 0.08 * math.sin(t * 1.8 + ms_i * 1.7)
        fwd_s = np.array([math.sin(myaw), pitch, math.cos(myaw)], np.float64)
        for u in np.linspace(-1.6, 1.6, 5):
            sb_ref.add([[mx + fwd_s[0] * u, 0.22 + pitch * u, mz + fwd_s[2] * u]], D=fwd_s, L=1.05, W=0.82 * (1.0 - 0.4 * (u / 1.8) ** 2), spr=DASH + 1, csh=C(88, 62, 52), cli=C(166, 124, 86), N=(0, 0.9, 0.2), smin=2.8)

    # Two twilight drifting rowboats with warm bow lanterns gliding across the Seine in Act IV
    lamps_tw = float(env.L.get("lamps", 0.0))
    if t > 74.0:
        for tb_i, (tz0, tspd, tx_r) in enumerate([(352.0, 0.85, -0.10), (384.0, -0.65, 0.22)]):
            tz = tz0 + (t - 74.0) * tspd
            tx = float(river_x(tz)) + tx_r * float(river_hw(tz))
            bob = 0.06 * math.sin(t * 2.0 + tb_i)
            sb_ref.add([[tx, 0.24 + bob, tz]], D=(0, 0, 1), L=3.4, W=0.95, spr=DASH, csh=C(48, 44, 58), cli=C(112, 86, 72), N=(0, 0.9, 0.2), smin=3.0)
            sb_ref.add([[tx, 0.72 + bob, tz - 0.2]], D=(0, 1, 0), L=0.85, W=0.35, spr=DAB, csh=C(44, 52, 78), cli=C(92, 108, 146), N=(0, 0.8, 0.3), smin=2.4)
            if lamps_tw > 0.08:
                sb_ref.add([[tx, 0.85 + bob, tz + 1.1]], D=(0, 1, 0), L=0.45, W=0.45, spr=LENS, csh=C(255, 202, 92), cli=C(255, 236, 148), N=(0, 1, 0), emis=lamps_tw, a=min(1.0, 0.3 + 0.7 * lamps_tw), smin=2.2)

    for b_i in range(28):
        z_base = 25.0 + (b_i / 28.0) * 410.0
        orbit_t = t * (0.45 + 0.08 * (b_i % 5)) + b_i * 1.37
        bx = float(river_x(z_base)) + math.sin(orbit_t) * (24.0 + (b_i % 4) * 7.0)
        bz = z_base + math.cos(orbit_t * 0.85) * 18.0
        by = 6.5 + (b_i % 5) * 2.2 + 2.4 * math.sin(orbit_t * 1.7)
        vx = math.cos(orbit_t) * 8.0
        vz = -math.sin(orbit_t * 0.85) * 8.0
        fwd = _norm3(np.array([vx, 0.0, vz]))
        right = np.array([fwd[2], 0.0, -fwd[0]])
        flap = math.sin(t * 13.0 + b_i * 2.1) * 0.28
        sb_over.add([[bx, by, bz]], D=fwd, L=0.52, W=0.16, spr=DASH, csh=C(36, 44, 72), cli=C(74, 88, 128), N=(0, 1, 0), smin=2.0)
        for sgn in (-1.0, 1.0):
            sb_over.add(
                [[bx + right[0] * sgn * 0.28, by + flap * 0.35, bz + right[2] * sgn * 0.28]],
                D=right * sgn - fwd * 0.35 + np.array([0.0, flap, 0.0]),
                L=0.58, W=0.14, spr=DASH + 1, csh=C(36, 44, 72), cli=C(82, 96, 138), N=(0, 1, 0), smin=1.8,
            )

    cam = env.C
    for p_i in range(45):
        ph = p_i * 2.31
        age = (t * 0.55 + p_i * 0.37) % 5.0
        px = cam[0] + math.sin(ph) * 16.0 + env.wdir[0] * age * 2.8 + math.sin(t * 2.1 + ph) * 0.8
        pz = cam[2] + 9.0 + math.cos(ph * 1.4) * 16.0 + env.wdir[2] * age * 2.8
        py = max(0.3, 1.5 + (p_i % 7) * 0.85 + math.sin(t * 1.6 + ph) * 0.65 - age * 0.12)
        is_poppy = (t < 32.0) and (p_i % 3 != 0)
        col_sh = C(172, 34, 42) if is_poppy else C(192, 184, 118)
        col_li = C(248, 72, 56) if is_poppy else C(252, 236, 162)
        psz = 0.22 if is_poppy else 0.14
        sb_over.add([[px, py, pz]], D=(math.cos(t * 2 + ph), 0.3, math.sin(t * 2 + ph)), L=psz, W=psz * 0.58, spr=DAB, csh=col_sh, cli=col_li, N=(0, 1, 0), a=0.68 * smooth(0.0, 0.6, age) * smooth(5.0, 4.0, age), smin=1.2)

    lamps = float(env.L.get("lamps", 0.0))
    if lamps > 0.15:
        for f_i in range(48):
            fz = 335.0 + (f_i / 48.0) * 105.0
            fx = float(river_x(fz)) + ( -float(river_hw(fz)) + 6.0 if f_i % 2 == 0 else float(river_hw(fz)) + 4.0 ) + math.sin(t * 0.9 + f_i) * 5.0
            fy = 0.9 + (f_i % 5) * 0.9 + 0.6 * math.sin(t * 1.4 + f_i * 1.7)
            pulse = max(0.0, math.sin(t * (2.6 + (f_i % 4) * 0.7) + f_i * 1.9)) ** 2
            if pulse > 0.08:
                sb_over.add([[fx, fy, fz]], D=(1, 0, 0), L=0.38, W=0.38, spr=LENS, csh=C(255, 224, 112), cli=C(255, 244, 156), N=(0, 1, 0), emis=1.0, a=0.95 * lamps * pulse, smin=1.8)

    out = []
    g1 = sb_ref.group(reflect=True, passid=STAND, name="swans_cafe_guests")
    if g1 and g1.visible(env):
        A = g1.lod(env)
        out.append(shade(env, A, mirror=False, sway=False))
        out.append(shade(env, A, mirror=True, sway=False))

    g2 = sb_over.group(reflect=False, passid=OVER, name="birds_petals_fireflies")
    if g2 and g2.visible(env):
        out.append(shade(env, g2.lod(env), mirror=False, sway=False))

    if rip_pts:
        rp = np.array(rip_pts, np.float64)
        v = rp[:, 0:3] - env.C
        vr, vu, vf = v @ env.rt, v @ env.up, v @ env.fw
        ok = vf > 0.3
        if ok.any():
            idx = np.nonzero(ok)[0]
            sc = env.f / vf[idx]
            x = 960.0 + vr[idx] * sc
            y = 540.0 - vu[idx] * sc
            col = mix(env.L["deep"][None, :], env.L["light"][None, :], np.full(len(idx), 0.7, np.float32))
            col = haze_of(env, col, np.maximum(vf[idx], 1.0), amt=0.8)
            out.append(dict(
                x=x.astype(np.float32), y=y.astype(np.float32),
                ang=np.arctan2(-rp[idx, 4], rp[idx, 3]).astype(np.float32),
                L=(rp[idx, 5] * sc).astype(np.float32), W=(rp[idx, 6] * sc).astype(np.float32),
                spr=np.full(len(idx), DASH + 1, np.int32),
                rgb=np.clip(col, 0.0, 1.1).astype(np.float32),
                a=rp[idx, 7].astype(np.float32),
                hb=np.full(len(idx), 0.5, np.float32),
                key=(RIPPLE * _PASS + 1e6 - vf[idx]).astype(np.float64),
            ))
    return out

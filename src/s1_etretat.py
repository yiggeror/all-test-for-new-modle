"""Scene 1 (0s - 19s): Falaise d'Etretat, Morning Tide (Pass 2 refined).

Dense sculpted chalk limestone sea arch (Porte d'Aval) & needle stack (L'Aiguille)
with opaque geological strata, frothy surf breaking at rock bases, rocking
fishing luggers, wheeling gulls, and smooth sea -> Seine transition.
"""
import numpy as np
from engine import Batch, smooth, mix, noise, C, pal, pick, jitter, DASH, DAB, SCUM
from world import Set, ground_rows, rnd_fields, scene_coord, scene_of, B1, BW
from sky_atmo import sky_rgb, dawn_sun_pos, PS

SEA_PAL = pal(
    (36, 98, 114), (52, 122, 132), (28, 78, 98),
    (74, 146, 144), (96, 166, 158), (44, 88, 122),
)
SEINE_PAL = pal(
    (32, 92, 158), (46, 118, 178), (38, 132, 146),
    (64, 152, 168), (28, 72, 136), (92, 174, 198),
)
CHALK_LIT = pal((246, 228, 198), (236, 208, 174), (252, 238, 214), (222, 194, 168))
CHALK_SHD = pal((140, 148, 180), (114, 126, 164), (164, 164, 192), (96, 108, 148))
TURF_PAL = pal((78, 122, 68), (104, 144, 78), (62, 100, 60), (130, 160, 88))
PEBBLE_PAL = pal((138, 132, 128), (168, 156, 144), (108, 112, 124), (192, 174, 156), (92, 98, 114))


def _sea_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    t = env.t
    u = scene_coord(X, p, env.camX)
    d = scene_of(u)
    wp = np.clip(d, 0.0, 1.0)

    rx = sx - 960.0
    ly = -(sy - env.hz) / env.zoom * 1.12 - 6.0
    skyc = sky_rgb(rx, ly, rx + env.camX * PS, env, rnd)

    near = smooth(0.10, 1.85, p)
    sea_base = mix(skyc, pick(SEA_PAL, rnd[:, 0], [3, 3, 2, 2, 1.5, 1.5]), 0.34 + 0.44 * near)

    wave_phase = p * 5.2 - t * 0.85 + 0.35 * noise(X / 900.0, p * 0.7, 1)
    crest = smooth(0.62, 0.96, np.sin(wave_phase * 2.0 * np.pi) * 0.5 + 0.5)
    foam_mask = crest * smooth(0.32, 0.85, p) * (1.0 - wp) * smooth(0.45, 0.88, rnd[:, 1] + 0.32 * crest)
    sea_col = mix(sea_base, C(246, 242, 234), 0.75 * foam_mask)

    shore = smooth(1.32, 2.05, p) * (1.0 - wp) * smooth(0.25, 0.75, rnd[:, 2] + 0.2 * noise(X / 220.0, p, 2))
    peb_col = mix(pick(PEBBLE_PAL, rnd[:, 3]), C(228, 198, 178), 0.25 * (1.0 - near))
    sea_col = mix(sea_col, peb_col, 0.76 * shore)

    sx0, sy0 = dawn_sun_pos(env)
    below = np.maximum(sy - env.hz, 0.0)
    wcol = 18.0 + 0.12 * below + 20.0 * noise(below / 95.0, t * 0.14, 3)
    gx = np.exp(-((sx - (960.0 + sx0 + 10.0 * np.sin(below * 0.03 + t * 0.95))) / wcol) ** 2)
    fl = 0.5 + 0.5 * np.sin(t * (1.8 + 2.0 * rnd[:, 1]) + rnd[:, 3] * 6.28 + below * 0.022)
    glit = smooth(0.26, 0.78, gx * (0.55 + 0.65 * fl) * 1.2 - rnd[:, 0] * 0.52) * smooth(4.0, 24.0, below) * (1.0 - wp)
    sea_col = mix(sea_col, mix(C(252, 138, 72), C(255, 224, 152), fl * rnd[:, 2]), glit)

    if wp.max() > 0.0:
        seine_base = mix(skyc, pick(SEINE_PAL, rnd[:, 1], [3, 3, 2.5, 2, 1.8, 1.4]), 0.36 + 0.45 * near)
        rip = smooth(0.72, 0.94, rnd[:, 0] + 0.18 * np.sin(t * 2.2 + X * 0.015 + p * 8.0))
        seine_col = mix(seine_base, mix(skyc, C(255, 248, 226), 0.65), 0.52 * rip)
        sea_col = mix(sea_col, seine_col, wp)

    sea_col = jitter(sea_col, rnd, 0.05, 0.025)
    sway = np.sin(t * (0.65 + 0.5 * rnd[:, 2]) + rnd[:, 3] * 6.28)
    x = sx + (3.5 + 5.0 * near) * sway
    y = sy + 1.4 * np.sin(t * 0.9 + rnd[:, 1] * 6.28) * near - 3.5 * foam_mask
    ang = (rnd[:, 0] - 0.5) * 0.11
    rev = smooth(0.0, 0.75, t * 1.15 - 0.5 - 1.3 * rnd[:, 1] - 0.35 * g["lvl"])
    a = g["a"] * rev * smooth(B1 + BW + 700.0, B1 + BW - 200.0, env.camX)
    return Batch(x, y, ang, g["L"] * sc * (1.0 + 0.12 * sway), g["W"] * sc, g["spr"], sea_col, a, g["zo"] + p * 0.06, hb=0.72)


def _cliff_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    fade_out = float(smooth(B1 + BW + 300.0, B1 + 100.0, env.camX))
    if fade_out <= 0.01:
        return None
    rev = smooth(0.0, 0.85, env.t - 0.35 - 1.1 * rnd[:, 0])
    col = mix(g["rgb"], C(196, 192, 212), 0.12 * (1.0 - smooth(0.28, 0.65, p)))
    col = jitter(col, rnd, 0.045, 0.02)
    mist = smooth(-28.0, 22.0, Y)
    col = mix(col, C(240, 224, 214), 0.18 * mist)
    return Batch(sx, sy, g["ang"], g["L"] * sc, g["W"] * sc, g["spr"], col, g["a"] * rev * fade_out, g["zo"], hb=0.85)


def _refl_cliff_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    fade_out = float(smooth(B1 + BW + 200.0, B1 + 50.0, env.camX))
    if fade_out <= 0.01:
        return None
    t = env.t
    rev = smooth(0.0, 0.85, t - 0.6 - 1.1 * rnd[:, 0])
    x_rip = sx + 7.5 * np.sin(t * 1.4 + sy * 0.05 + rnd[:, 1] * 3.0)
    col = mix(g["rgb"], C(64, 122, 132), 0.38)
    return Batch(x_rip, sy, (rnd[:, 2] - 0.5) * 0.14, g["L"] * sc * 1.35, g["W"] * sc * 0.72, g["spr"], col, g["a"] * 0.52 * rev * fade_out, 2.25, hb=0.45)


def _etretat_actors(env):
    batches = []
    t = env.t
    vis = float(smooth(B1 + BW + 350.0, B1 - 150.0, env.camX))
    if vis <= 0.01:
        return batches
    rev = float(smooth(0.8, 2.4, t))

    # 1. Three rocking Normandy fishing luggers
    boats = [
        (320.0, -40.0, 0.56, 1.0),
        (1240.0, -58.0, 0.46, 0.85),
        (2360.0, -28.0, 0.64, -1.0),
    ]
    bx_l, by_l, ba_l, bL_l, bW_l, bsp_l, bc_l, bal_l, bzo_l = [], [], [], [], [], [], [], [], []
    for i, (X0, Y0, p, dir_s) in enumerate(boats):
        X = X0 + t * (16.0 if dir_s > 0 else -12.0)
        bob = 3.8 * np.sin(t * 1.5 + i * 2.1)
        roll = 0.07 * np.sin(t * 1.2 + i * 1.7)
        sx, sy, sc = env.project(X, Y0 + bob, p)
        if not (-200 < sx < 2120):
            continue
        # Hull + deck
        bx_l.extend([sx, sx]); by_l.extend([sy, sy + 6.0 * sc])
        ba_l.extend([roll, roll]); bL_l.extend([98.0 * sc, 82.0 * sc]); bW_l.extend([22.0 * sc, 13.0 * sc])
        bsp_l.extend([DASH, DASH + 1]); bc_l.extend([C(46, 40, 46), C(76, 66, 70)])
        bal_l.extend([0.95 * vis * rev, 0.62 * vis * rev]); bzo_l.extend([3.3, 2.28])
        # Multi-dab rust-ochre lugsail
        for s_k in range(3):
            bx_l.append(sx + (-8.0 + s_k * 8.0) * sc * dir_s)
            by_l.append(sy - (34.0 + s_k * 20.0) * sc)
            ba_l.append(1.48 + roll)
            bL_l.append((58.0 - s_k * 10.0) * sc); bW_l.append((34.0 - s_k * 5.0) * sc)
            bsp_l.append(DAB + s_k)
            bc_l.append(mix(C(176, 82, 54), C(226, 138, 82), s_k / 2.0))
            bal_l.extend([0.92 * vis * rev]); bzo_l.extend([3.35 + 0.01 * s_k])
        # Reflection
        bx_l.append(sx + 5.0 * np.sin(t * 2.1 + i)); by_l.append(sy + 36.0 * sc); ba_l.append(0.0)
        bL_l.append(58.0 * sc); bW_l.append(18.0 * sc); bsp_l.append(SCUM)
        bc_l.append(C(170, 96, 74)); bal_l.append(0.45 * vis * rev); bzo_l.append(2.26)

    if bx_l:
        batches.append(Batch(np.array(bx_l, np.float32), np.array(by_l, np.float32), np.array(ba_l, np.float32),
                             np.array(bL_l, np.float32), np.array(bW_l, np.float32), np.array(bsp_l, np.int32),
                             np.array(bc_l, np.float32), np.array(bal_l, np.float32), np.array(bzo_l, np.float32), hb=0.75))

    # 2. Wheeling Normandy sea gulls above arch & surf
    gx, gy, ga, gL, gW, gsp, gc = [], [], [], [], [], [], []
    for k in range(16):
        X = -150.0 + k * 230.0 + t * (48.0 + 18.0 * (k % 3)) + 90.0 * np.sin(t * 0.4 + k)
        Y = -360.0 - 95.0 * np.sin(t * 0.55 + k * 1.1) - (k % 4) * 42.0
        p = 0.50 + 0.14 * (k % 4)
        sx, sy, sc = env.project(X, Y, p)
        if not (-120 < sx < 2040):
            continue
        flap = 0.48 * np.sin(t * (4.8 + 0.6 * (k % 3)) + k * 1.4)
        wlen = 28.0 * sc
        gx.extend([sx - wlen * 0.45, sx + wlen * 0.45])
        gy.extend([sy - flap * 8.0 * sc, sy - flap * 8.0 * sc])
        ga.extend([-0.25 + flap, 0.25 - flap])
        gL.extend([wlen, wlen]); gW.extend([8.5 * sc, 8.5 * sc])
        gsp.extend([DAB + (k % 4), DAB + ((k + 1) % 4)])
        col = C(252, 248, 242) if k % 2 == 0 else C(232, 224, 228)
        gc.extend([col, col])
    if gx:
        batches.append(Batch(np.array(gx, np.float32), np.array(gy, np.float32), np.array(ga, np.float32),
                             np.array(gL, np.float32), np.array(gW, np.float32), np.array(gsp, np.int32),
                             np.array(gc, np.float32), 0.92 * vis * rev, 3.6, hb=0.55))

    # 3. White surf splashes breaking right around base of Porte d'Aval & L'Aiguille
    fx, fy, fL, fW, fsp, fc = [], [], [], [], [], []
    for k in range(36):
        fx0 = 860.0 + (k % 24) * 65.0 if k < 24 else 2530.0 + (k - 24) * 24.0
        fp = 0.53 if k < 24 else 0.59
        sx, sy, sc = env.project(fx0 + 18.0 * np.sin(t * 1.8 + k), 10.0 + 5.0 * np.sin(t * 2.2 + k), fp)
        if -150 < sx < 2070:
            fx.append(sx); fy.append(sy)
            fL.append((85.0 + 35.0 * np.sin(t * 2.5 + k)) * sc); fW.append(22.0 * sc)
            fsp.append(SCUM + (k % 6)); fc.append(C(250, 244, 236))
    if fx:
        batches.append(Batch(np.array(fx, np.float32), np.array(fy, np.float32), np.zeros(len(fx), np.float32),
                             np.array(fL, np.float32), np.array(fW, np.float32), np.array(fsp, np.int32),
                             np.array(fc, np.float32), 0.80 * vis * rev, 2.78, hb=0.65))

    return batches


def _build_arch_strokes(rng):
    Xs, Ys, ps, Ls, Ws, angs, sprs, rgbs, alps, zos = [], [], [], [], [], [], [], [], [], []

    def add_rock(X_arr, Y_arr, p_val, lit_mask, base_L, base_W, zo_val, turf_top=None, alpha_lo=0.88):
        n = len(X_arr)
        lit_c = pick(CHALK_LIT, rng.random(n))
        shd_c = pick(CHALK_SHD, rng.random(n))
        col = mix(shd_c, lit_c, lit_mask[:, None])
        strata = np.sin(Y_arr * 0.14 + 0.4 * np.sin(X_arr * 0.015))
        col = np.where((strata > 0.68)[:, None] & (rng.random((n, 1)) < 0.48), col * 0.78, col)
        if turf_top is not None:
            col = mix(col, pick(TURF_PAL, rng.random(n)), turf_top[:, None])
        Xs.append(X_arr); Ys.append(Y_arr); ps.append(np.full(n, p_val, np.float32))
        Ls.append(rng.uniform(base_L * 0.75, base_L * 1.4, n))
        Ws.append(rng.uniform(base_W * 0.75, base_W * 1.35, n))
        angs.append(np.where(turf_top is not None, (rng.random(n) - 0.5) * 0.35, (rng.random(n) - 0.5) * 0.22 + 0.10))
        sprs.append(np.where(rng.random(n) < 0.55, DAB + rng.integers(0, 6, n), DASH + rng.integers(0, 8, n)))
        rgbs.append(col); alps.append(rng.uniform(alpha_lo, 0.98, n)); zos.append(np.full(n, zo_val, np.float32))

    # 1. Distant headland cliff wall left/behind arch (compact X = -650..950, dense opaque fill!)
    n_bg = 1250
    x_bg = rng.uniform(-650.0, 950.0, n_bg)
    top_bg = -430.0 - 75.0 * np.sin((x_bg + 500.0) * 0.0026) + 35.0 * np.sin(x_bg * 0.009)
    y_bg = top_bg + rng.random(n_bg) * (-top_bg + 30.0)
    lit_bg = smooth(-500.0, 800.0, x_bg) * 0.42 + 0.25 * (1.0 - (y_bg - top_bg) / 420.0)
    turf_bg = smooth(32.0, 0.0, y_bg - top_bg)
    add_rock(x_bg, y_bg, 0.36, lit_bg, 98.0, 52.0, 2.38, turf_bg, alpha_lo=0.92)

    # 2. Porte d'Aval Sea Arch (p = 0.52, X = 720..2260) — dense underpainting + sculpted strata
    for pass_i, (n_arch, bL, bW, zv, alo) in enumerate([(1350, 110.0, 58.0, 2.46, 0.94), (2400, 64.0, 30.0, 2.52, 0.88)]):
        ax = rng.uniform(720.0, 2260.0, n_arch)
        arch_top = -540.0 + 185.0 * smooth(1540.0, 2260.0, ax) - 42.0 * np.sin((ax - 750.0) * 0.005)
        ay = arch_top + rng.random(n_arch) * (-arch_top + 28.0)
        hole_dx = (ax - 1660.0) / 265.0
        hole_dy = (ay - 30.0) / 305.0
        keep = ~((hole_dx ** 2 + hole_dy ** 2 < 1.0) & (ay > -285.0))
        ax, ay, arch_top = ax[keep], ay[keep], arch_top[keep]
        lit_a = smooth(780.0, 1180.0, ax) * 0.35 + smooth(-220.0, -520.0, ay) * 0.55
        under = smooth(320.0, 220.0, np.hypot((ax - 1660.0) * 0.85, ay + 120.0))
        lit_a = np.clip(lit_a - 0.65 * under + 0.25 * (ax < 1380.0), 0.0, 1.0)
        turf_a = smooth(34.0, 0.0, ay - arch_top) * smooth(2100.0, 1700.0, ax)
        add_rock(ax, ay, 0.52, lit_a, bL, bW, zv, turf_a, alpha_lo=alo)

    # 3. L'Aiguille sea stack (X = 2660, p = 0.58)
    for n_needle, bL, bW, zv in [(360, 88.0, 44.0, 2.66), (620, 52.0, 26.0, 2.72)]:
        t_h = rng.random(n_needle)
        ny = -610.0 + t_h * 638.0
        half_w = 18.0 + 165.0 * (t_h ** 0.72)
        nx = 2660.0 + (rng.random(n_needle) * 2.0 - 1.0) * half_w
        lit_n = smooth(0.45, -0.55, (nx - 2660.0) / np.maximum(half_w, 1.0)) * 0.75 + 0.20 * (1.0 - t_h)
        add_rock(nx, ny, 0.58, lit_n, bL, bW, zv, None, alpha_lo=0.90)

    X = np.concatenate(Xs).astype(np.float32); Y = np.concatenate(Ys).astype(np.float32)
    p = np.concatenate(ps).astype(np.float32); L = np.concatenate(Ls).astype(np.float32)
    W = np.concatenate(Ws).astype(np.float32); ang = np.concatenate(angs).astype(np.float32)
    spr = np.concatenate(sprs).astype(np.int32); rgb = np.concatenate(rgbs).astype(np.float32)
    alp = np.concatenate(alps).astype(np.float32); zo = np.concatenate(zos).astype(np.float32)

    r_keep = (Y < -10.0) & (rng.random(len(X)) < 0.45)
    return (
        Set("etretat_cliffs", _cliff_shader, X, Y, p, cam=(-1e9, B1 + BW + 400.0), margin=380.0,
            rnd=rnd_fields(rng, len(X)), L=L, W=W, ang=ang, spr=spr, rgb=rgb, a=alp, zo=zo),
        Set("etretat_cliff_refl", _refl_cliff_shader, X[r_keep], -Y[r_keep] * 0.72, p[r_keep],
            cam=(-1e9, B1 + BW + 300.0), margin=360.0,
            rnd=rnd_fields(rng, int(r_keep.sum())), L=L[r_keep], W=W[r_keep], spr=spr[r_keep], rgb=rgb[r_keep], a=alp[r_keep]),
    )


def build(rng):
    sets = []
    X_end = B1 + BW + 600.0
    for lvl, (bl, asp, a, pm) in enumerate([(145.0, 3.2, 0.94, 0.03), (72.0, 3.6, 0.90, 0.10), (38.0, 3.9, 0.86, 0.34)]):
        X, p, L, W = ground_rows(rng, -350.0, X_end, pm, 2.6, bl, asp, min_len=(56, 38, 24)[lvl])
        n = len(X)
        rnd = rnd_fields(rng, n)
        spr = np.where(rnd[:, 0] < (0.30 if lvl == 0 else 0.12), SCUM + rng.integers(0, 6, n), DASH + rng.integers(0, 8, n)).astype(np.int32)
        sets.append(Set(f"sea{lvl}", _sea_shader, X, np.zeros(n), p, cam=(-1e9, B1 + BW + 800.0),
                        rnd=rnd, L=L, W=W, spr=spr, a=a, zo=np.float32(1.85 + 0.10 * lvl), lvl=float(lvl)))

    cliff_set, refl_set = _build_arch_strokes(rng)
    sets.extend([cliff_set, refl_set])
    return sets, [_etretat_actors]

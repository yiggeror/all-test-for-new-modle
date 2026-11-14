"""Scene 2 (18s - 39s): Regatta at Argenteuil (Pass 2 refined).

Lush green far riverbank & poplar reflections properly depth-sorted above Seine
water, sunlit Argenteuil villas & red roofs, solid multi-layer sailboats with
triangular sails & fluttering pennants, and organic curving shoreline into Giverny.
"""
import numpy as np
from engine import Batch, smooth, mix, noise, C, pal, pick, jitter, DASH, DAB, SCUM
from world import Set, ground_rows, rnd_fields, scene_coord, scene_of, B1, B2, BW
from sky_atmo import sky_rgb, PS

SEINE_WATER = pal(
    (28, 86, 152), (44, 118, 180), (36, 134, 148),
    (68, 158, 174), (24, 68, 128), (112, 186, 206),
)
LEAF_POPLAR = pal(
    (58, 114, 52), (84, 144, 64), (112, 164, 72),
    (44, 90, 50), (140, 178, 84), (68, 128, 88),
)
MEADOW_PAL = pal((74, 132, 58), (98, 156, 68), (126, 174, 78), (58, 108, 50), (154, 186, 94))
VILLA_WALL = pal((246, 232, 204), (236, 214, 184), (248, 238, 218), (222, 198, 174))
ROOF_RED = pal((196, 86, 58), (178, 72, 48), (214, 106, 68), (156, 62, 44))


def _seine_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    t = env.t
    vis = float(smooth(B1 - BW - 300.0, B1 - 100.0, env.camX)) * float(smooth(B2 + BW + 600.0, B2 + BW - 200.0, env.camX))
    if vis <= 0.01:
        return None

    # Organic winding shoreline across B2 +/- BW so river curves naturally into meadow!
    wiggle = 260.0 * np.sin(p * 3.1 + 0.6) + 180.0 * noise(X / 600.0, p * 1.4, 2)
    u = scene_coord(X + wiggle, p, env.camX)
    d = scene_of(u)
    t_to_g = smooth(1.22, 1.88, d)

    rx = sx - 960.0
    ly = -(sy - env.hz) / env.zoom * 1.12 - 6.0
    skyc = sky_rgb(rx, ly, rx + env.camX * PS, env, rnd)

    near = smooth(0.08, 1.85, p)
    riv = mix(skyc, pick(SEINE_WATER, rnd[:, 0], [3, 3, 2.5, 2, 1.5, 1.2]), 0.34 + 0.48 * near)
    glint = smooth(0.76, 0.96, rnd[:, 1] + 0.22 * np.sin(t * 2.4 + X * 0.014 + p * 6.0))
    riv = mix(riv, mix(skyc, C(255, 250, 232), 0.72), 0.56 * glint)

    # Dark bank mud/reeds right at the water-meadow border (0.15 < t_to_g < 0.65)
    shore_band = smooth(0.08, 0.35, t_to_g) * smooth(0.75, 0.40, t_to_g)
    riv = mix(riv, C(78, 114, 58), 0.65 * shore_band)

    if t_to_g.max() > 0.0:
        lawn = pick(MEADOW_PAL, rnd[:, 2])
        lateral = np.abs(sx - 960.0) / np.maximum(p, 0.2)
        in_path = smooth(260.0, 95.0, lateral + 45.0 * np.sin(X * 0.002)) * smooth(1.65, 1.95, d)
        gravel = mix(C(222, 206, 178), C(240, 224, 196), rnd[:, 3])
        gard = mix(lawn, gravel, 0.78 * in_path)
        riv = mix(riv, gard, t_to_g)

    col = jitter(riv, rnd, 0.055, 0.025)
    sway = np.sin(t * (0.7 + 0.5 * rnd[:, 2]) + rnd[:, 3] * 6.28)
    x = sx + (3.2 + 4.5 * near) * sway * (1.0 - 0.7 * t_to_g)
    y = sy + 1.2 * np.sin(t * 0.95 + rnd[:, 1] * 6.28) * near * (1.0 - t_to_g)
    ang = (rnd[:, 0] - 0.5) * 0.10
    return Batch(x, y, ang, g["L"] * sc * (1.0 + 0.1 * sway), g["W"] * sc, g["spr"], col, g["a"] * vis, g["zo"] + p * 0.06, hb=0.72)


def _poplar_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    vis = float(smooth(B1 - BW - 250.0, B1 - 50.0, env.camX)) * float(smooth(B2 + BW + 450.0, B2 + 100.0, env.camX))
    if vis <= 0.01:
        return None
    w = env.wind(X, p)
    sway_x = (w - 0.45) * 16.0 * sc * g["flex"] + 2.8 * sc * np.sin(env.t * 2.1 + X * 0.02 + rnd[:, 0] * 6.28)
    col = mix(g["rgb"], C(190, 208, 148), 0.12 * (1.0 - smooth(0.28, 0.72, p)))
    col = jitter(col, rnd, 0.048, 0.022)
    return Batch(sx + sway_x, sy, g["ang"] + (w - 0.45) * 0.12 * g["flex"], g["L"] * sc, g["W"] * sc, g["spr"], col, g["a"] * vis, g["zo"], hb=0.80)


def _bank_refl_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    vis = float(smooth(B1 - BW - 200.0, B1, env.camX)) * float(smooth(B2 + 100.0, B2 - 400.0, env.camX))
    if vis <= 0.01:
        return None
    t = env.t
    x_rip = sx + 5.5 * np.sin(t * 1.8 + sy * 0.06 + rnd[:, 0] * 3.0)
    col = mix(g["rgb"], C(38, 102, 148), 0.35)
    return Batch(x_rip, sy, (rnd[:, 1] - 0.5) * 0.15, g["L"] * sc * 1.2, g["W"] * sc * 0.65, g["spr"], col, 0.48 * vis, 2.24, hb=0.45)


def _reed_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    vis = float(smooth(B1 - 300.0, B1 + 150.0, env.camX)) * float(smooth(B2 + BW + 300.0, B2 - 100.0, env.camX))
    if vis <= 0.01:
        return None
    w = env.wind(X, p)
    gust = (w - 0.35) * 0.44 + 0.08 * np.sin(env.t * 2.6 + X * 0.03 + rnd[:, 0] * 6.28)
    lean = gust * g["hnorm"]
    x = sx + lean * 28.0 * sc
    y = sy + np.abs(lean) * 6.0 * sc
    ang = 1.5708 - lean * 0.65 + (rnd[:, 1] - 0.5) * 0.12
    col = jitter(g["rgb"], rnd, 0.05, 0.025)
    return Batch(x, y, ang, g["L"] * sc, g["W"] * sc, g["spr"], col, g["a"] * vis, 3.35 + p * 0.25, hb=0.82)


def _regatta_actors(env):
    batches = []
    t = env.t
    vis = float(smooth(B1 - 400.0, B1 + 250.0, env.camX)) * float(smooth(B2 + BW + 200.0, B2 - 150.0, env.camX))
    if vis <= 0.01:
        return batches

    fleet = [
        (4500.0, -28.0, 0.46,  34.0, 0.90, C(178, 52, 46),   C(224, 58, 48)),
        (5180.0, -14.0, 0.65,  46.0, 1.12, C(42, 68, 128),   C(238, 192, 64)),
        (5820.0, -42.0, 0.40,  26.0, 0.78, C(118, 68, 48),   C(218, 62, 52)),
        (6200.0,  -4.0, 0.80,  52.0, 1.24, C(236, 228, 210), C(216, 48, 44)),
        (6950.0, -20.0, 0.56,  40.0, 1.02, C(52, 92, 74),    C(240, 178, 58)),
        (7420.0, -14.0, 0.68,  32.0, 1.12, C(168, 64, 52),   C(58, 118, 214)),
    ]

    xs, ys, angs, Ls, Ws, sprs, rgbs, alps, zos = [], [], [], [], [], [], [], [], []
    for i, (X0, Y0, p, spd, sz, hcol, pcol) in enumerate(fleet):
        dt = max(0.0, t - 15.0)
        X = X0 + dt * spd
        bob = 3.0 * np.sin(t * 1.9 + i * 1.4)
        w = float(env.wind(np.array([X], np.float32), p)[0])
        heel = 0.04 + 0.07 * (w - 0.4)
        sx, sy, sc = env.project(X, Y0 + bob, p)
        sc *= sz
        if not (-280 < sx < 2200):
            continue
        zb = 2.75 + p * 0.5

        # 1. Broken shimmering vertical reflection in the Seine
        for k in range(8):
            ry = sy + (16.0 + k * 21.0) * sc
            rx = sx + (4.5 + k * 1.6) * np.sin(t * 2.4 + k * 0.9 + i) * sc
            rcol = mix(C(248, 242, 226), C(90, 148, 184), k / 8.0)
            if k == 0:
                rcol = mix(hcol, C(42, 96, 148), 0.30)
            xs.append(rx); ys.append(ry); angs.append(0.07 * np.sin(t + k))
            Ls.append((86.0 - k * 7.0) * sc); Ws.append((22.0 + k * 1.5) * sc)
            sprs.append(DASH + (k % 8)); rgbs.append(rcol); alps.append((0.60 - 0.05 * k) * vis); zos.append(2.28)

        # 2. Hull + sunlit gunwale
        xs.extend([sx, sx + 3.0 * sc]); ys.extend([sy + 3.0 * sc, sy - 4.0 * sc])
        angs.extend([heel * 0.3, heel * 0.3]); Ls.extend([126.0 * sc, 114.0 * sc]); Ws.extend([24.0 * sc, 11.0 * sc])
        sprs.extend([DASH + 1, DASH + 3]); rgbs.extend([hcol, mix(hcol, C(252, 240, 218), 0.55)])
        alps.extend([0.97 * vis, 0.94 * vis]); zos.extend([zb, zb + 0.02])

        # 3. Mast & Boom
        xs.extend([sx - 4.0 * sc + np.sin(heel) * 85.0 * sc, sx - 26.0 * sc])
        ys.extend([sy - 88.0 * sc, sy - 18.0 * sc])
        angs.extend([1.5708 - heel, heel * 0.2])
        Ls.extend([174.0 * sc, 82.0 * sc]); Ws.extend([5.5 * sc, 5.0 * sc])
        sprs.extend([DASH, DASH + 2]); rgbs.extend([C(88, 66, 48), C(88, 66, 48)])
        alps.extend([0.94 * vis, 0.92 * vis]); zos.extend([zb + 0.03, zb + 0.03])

        # 4. Crisp solid-filled Mainsail triangle (10 overlapping vertical-angled strokes)
        for seg in range(10):
            frac = seg / 9.0
            s_w = (76.0 - 62.0 * frac) * sc
            s_x = sx + (-24.0 + 18.0 * frac) * sc + np.sin(heel) * (20.0 + frac * 118.0) * sc
            s_y = sy - (26.0 + frac * 128.0) * sc
            sail_c = mix(C(224, 228, 240), C(255, 250, 232), 0.45 + 0.55 * (1.0 - frac * 0.35))
            xs.append(s_x); ys.append(s_y); angs.append(0.14 - heel)
            Ls.append(s_w); Ws.append(36.0 * sc)
            sprs.append(DAB + (seg % 6)); rgbs.append(sail_c); alps.append(0.95 * vis); zos.append(zb + 0.04)

        # Foresail jib triangle (6 overlapping strokes)
        for seg in range(6):
            frac = seg / 5.0
            xs.append(sx + (28.0 - 16.0 * frac) * sc + np.sin(heel) * (35.0 + frac * 78.0) * sc)
            ys.append(sy - (28.0 + frac * 94.0) * sc)
            angs.append(-0.32 - heel)
            Ls.append((48.0 - 30.0 * frac) * sc); Ws.append(24.0 * sc)
            sprs.append(DAB + ((seg + 2) % 6)); rgbs.append(C(252, 246, 226))
            alps.append(0.93 * vis); zos.append(zb + 0.05)

        # 5. Fluttering masthead regatta pennant
        flut = 0.22 * np.sin(t * (7.5 + 3.0 * w) + i * 2.0)
        xs.append(sx - 24.0 * sc + np.sin(heel) * 168.0 * sc)
        ys.append(sy - 170.0 * sc + flut * 8.0 * sc)
        angs.append(flut); Ls.append(42.0 * sc); Ws.append(11.0 * sc)
        sprs.append(DASH + 2); rgbs.append(pcol); alps.append(0.96 * vis); zos.append(zb + 0.06)

    if xs:
        batches.append(Batch(np.array(xs, np.float32), np.array(ys, np.float32), np.array(angs, np.float32),
                             np.array(Ls, np.float32), np.array(Ws, np.float32), np.array(sprs, np.int32),
                             np.array(rgbs, np.float32), np.array(alps, np.float32), np.array(zos, np.float32), hb=0.80))
    return batches


def build(rng):
    sets = []
    cam_lim = (B1 - BW - 400.0, B2 + BW + 700.0)

    for lvl, (bl, asp, a, pm) in enumerate([(140.0, 3.2, 0.94, 0.03), (70.0, 3.6, 0.90, 0.10), (36.0, 3.9, 0.86, 0.34)]):
        X, p, L, W = ground_rows(rng, B1 - 600.0, B2 + BW + 400.0, pm, 2.5, bl, asp, min_len=(54, 36, 22)[lvl])
        n = len(X)
        rnd = rnd_fields(rng, n)
        spr = np.where(rnd[:, 0] < 0.22, SCUM + rng.integers(0, 6, n), DASH + rng.integers(0, 8, n)).astype(np.int32)
        sets.append(Set(f"seine{lvl}", _seine_shader, X, np.zeros(n), p, cam=cam_lim,
                        rnd=rnd, L=L, W=W, spr=spr, a=a, zo=np.float32(1.88 + 0.10 * lvl)))

    px_l, py_l, pp_l, pL_l, pW_l, pa_l, psp_l, pc_l, pzo_l, pflex_l = [], [], [], [], [], [], [], [], [], []

    # Continuous green grassy far shoreline band (so trees & villas sit on solid riverbank!)
    nb = 520
    bx_b = rng.uniform(3550.0, 9550.0, nb)
    px_l.append(bx_b); py_l.append(rng.uniform(-45.0, 12.0, nb)); pp_l.append(np.full(nb, 0.28))
    pL_l.append(rng.uniform(140.0, 220.0, nb)); pW_l.append(rng.uniform(42.0, 70.0, nb))
    pa_l.append(rng.uniform(-0.12, 0.12, nb)); psp_l.append(DASH + rng.integers(0, 8, nb))
    pc_l.append(pick(MEADOW_PAL, rng.random(nb))); pzo_l.append(np.full(nb, 2.38)); pflex_l.append(np.zeros(nb))

    # Argenteuil villas along far bank peeking clearly through tree clearings (zo = 2.58 > tree zo)
    villas = [4350.0, 5380.0, 6520.0, 7700.0]
    for vx in villas:
        vp = 0.295
        nw = 95
        px_l.append(vx + rng.uniform(-175.0, 175.0, nw)); py_l.append(rng.uniform(-155.0, -5.0, nw))
        pp_l.append(np.full(nw, vp)); pL_l.append(rng.uniform(76.0, 118.0, nw)); pW_l.append(rng.uniform(48.0, 76.0, nw))
        pa_l.append(rng.uniform(-0.10, 0.10, nw)); psp_l.append(DAB + rng.integers(0, 6, nw))
        pc_l.append(pick(VILLA_WALL, rng.random(nw))); pzo_l.append(np.full(nw, 2.57)); pflex_l.append(np.zeros(nw))
        nr = 65
        px_l.append(vx + rng.uniform(-190.0, 190.0, nr)); py_l.append(rng.uniform(-225.0, -140.0, nr))
        pp_l.append(np.full(nr, vp)); pL_l.append(rng.uniform(80.0, 122.0, nr)); pW_l.append(rng.uniform(36.0, 56.0, nr))
        pa_l.append(rng.uniform(-0.15, 0.15, nr)); psp_l.append(DAB + rng.integers(0, 6, nr))
        pc_l.append(pick(ROOF_RED, rng.random(nr))); pzo_l.append(np.full(nr, 2.59)); pflex_l.append(np.zeros(nr))
        # Dark shutter windows on villas
        for wx_off in [-85.0, 0.0, 85.0]:
            px_l.append(np.array([vx + wx_off])); py_l.append(np.array([-85.0])); pp_l.append(np.array([vp]))
            pL_l.append(np.array([46.0])); pW_l.append(np.array([28.0])); pa_l.append(np.array([1.57]))
            psp_l.append(np.array([DAB])); pc_l.append(np.array([C(76, 86, 98)])); pzo_l.append(np.array([2.60])); pflex_l.append(np.array([0.0]))

    # Tall Normandy poplar trees + trunks grounded on far bank (parting slightly around villas)
    for tx in np.linspace(3500.0, 9400.0, 34):
        if any(abs(tx - vx) < 120.0 for vx in villas):
            continue
        tp = rng.uniform(0.25, 0.33)
        th = rng.uniform(380.0, 720.0)
        tw = rng.uniform(125.0, 195.0)
        nt = 8
        px_l.append(np.full(nt, tx) + rng.uniform(-14.0, 14.0, nt))
        py_l.append(np.linspace(-25.0, -th * 0.55, nt))
        pp_l.append(np.full(nt, tp)); pL_l.append(rng.uniform(70.0, 115.0, nt)); pW_l.append(rng.uniform(18.0, 28.0, nt))
        pa_l.append(np.full(nt, 1.57) + rng.uniform(-0.08, 0.08, nt))
        psp_l.append(DASH + rng.integers(0, 8, nt))
        pc_l.append(np.broadcast_to(C(84, 68, 56), (nt, 3))); pzo_l.append(np.full(nt, 2.50))
        pflex_l.append(np.linspace(0.05, 0.4, nt))
        nk = 82
        u_h = rng.random(nk)
        ang = rng.uniform(0.0, 6.28, nk)
        px_l.append(tx + np.cos(ang) * tw * (0.35 + 0.65 * np.sin(u_h * np.pi)))
        py_l.append(-20.0 - u_h * th)
        pp_l.append(np.full(nk, tp)); pL_l.append(rng.uniform(82.0, 140.0, nk)); pW_l.append(rng.uniform(54.0, 96.0, nk))
        pa_l.append(1.57 + rng.uniform(-0.5, 0.5, nk))
        psp_l.append(np.where(rng.random(nk) < 0.45, SCUM + rng.integers(0, 6, nk), DAB + rng.integers(0, 6, nk)))
        c_tree = mix(C(44, 88, 52), pick(LEAF_POPLAR, rng.random(nk)), u_h[:, None] * 0.75 + 0.25)
        pc_l.append(c_tree); pzo_l.append(np.full(nk, 2.52 + tp * 0.12)); pflex_l.append(u_h)

    X_p = np.concatenate(px_l).astype(np.float32); Y_p = np.concatenate(py_l).astype(np.float32)
    p_p = np.concatenate(pp_l).astype(np.float32); C_p = np.concatenate(pc_l).astype(np.float32)
    L_p = np.concatenate(pL_l).astype(np.float32); W_p = np.concatenate(pW_l).astype(np.float32)
    spr_p = np.concatenate(psp_l).astype(np.int32)
    sets.append(Set("poplars_villas", _poplar_shader, X_p, Y_p, p_p, cam=cam_lim, margin=360.0,
                    rnd=rnd_fields(rng, len(X_p)), L=L_p, W=W_p, ang=np.concatenate(pa_l).astype(np.float32),
                    spr=spr_p, rgb=C_p, a=0.93, zo=np.concatenate(pzo_l).astype(np.float32),
                    flex=np.concatenate(pflex_l).astype(np.float32)))

    # Far bank reflections in water
    rk = (Y_p < -20.0) & (rng.random(len(X_p)) < 0.35)
    sets.append(Set("poplar_refl", _bank_refl_shader, X_p[rk], -Y_p[rk] * 0.65, p_p[rk], cam=cam_lim, margin=350.0,
                    rnd=rnd_fields(rng, int(rk.sum())), L=L_p[rk], W=W_p[rk], spr=spr_p[rk], rgb=C_p[rk]))

    # Foreground riverbank reeds (cluster denser near B2 shoreline transition!)
    n_reed = 1100
    rx_r = rng.uniform(3900.0, 9200.0, n_reed)
    rp_r = rng.uniform(1.22, 1.95, n_reed)
    ry_r = rng.uniform(12.0, 95.0, n_reed)
    r_h = rng.uniform(0.35, 1.0, n_reed)
    sets.append(Set("argenteuil_reeds", _reed_shader, rx_r, ry_r, rp_r, cam=cam_lim, margin=260.0,
                    rnd=rnd_fields(rng, n_reed), L=rng.uniform(75.0, 155.0, n_reed).astype(np.float32),
                    W=rng.uniform(10.0, 18.0, n_reed).astype(np.float32),
                    spr=(DASH + rng.integers(0, 8, n_reed)).astype(np.int32),
                    rgb=pick(LEAF_POPLAR, rng.random(n_reed)).astype(np.float32), a=0.90, hnorm=r_h.astype(np.float32)))

    return sets, [_regatta_actors]

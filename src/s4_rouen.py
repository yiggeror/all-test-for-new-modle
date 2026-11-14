"""Scene 4 (57s - 78s): Cathedrale de Rouen, Sunset Light (Pass 2 refined).

Dense golden-ochre & cobalt-violet stone underpainting beneath ~4,600 sculpted
impasto dabs so Gothic facade, twin towers, spire, rose window, and triple
portals read as solid carved stone glowing in deepening sunset light, flanked by
warm Rouen square roofs and circling doves.
"""
import numpy as np
from engine import Batch, smooth, mix, noise, C, pal, pick, jitter, DASH, DAB
from world import Set, ground_rows, rnd_fields, scene_coord, scene_of, B3, B4, BW
from sky_atmo import sky_rgb, PS

STONE_GOLD_AM = pal((248, 212, 146), (242, 192, 134), (254, 228, 174), (232, 174, 128))
STONE_GOLD_PM = pal((246, 162, 98), (238, 136, 108), (252, 188, 118), (218, 118, 112))
STONE_SHD_AM = pal((124, 124, 168), (146, 136, 182), (98, 102, 152), (164, 150, 188))
STONE_SHD_PM = pal((88, 76, 136), (112, 86, 146), (68, 62, 118), (132, 96, 150))

COBBLE_PAL = pal((196, 168, 158), (218, 184, 162), (154, 142, 168), (230, 196, 168), (130, 124, 154))
LAGOON_PAL = pal((34, 48, 98), (48, 62, 118), (72, 68, 128), (28, 38, 84), (92, 74, 136))


def _plaza_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    vis = float(smooth(B3 - BW - 250.0, B3, env.camX)) * float(smooth(B4 + BW + 600.0, B4 + BW - 150.0, env.camX))
    if vis <= 0.01:
        return None
    wiggle = 200.0 * np.sin(p * 2.5) + 140.0 * noise(X / 600.0, p * 1.1, 2)
    u = scene_coord(X + wiggle, p, env.camX)
    d = scene_of(u)
    to_lagoon = smooth(3.25, 3.92, d)

    near = smooth(0.08, 1.85, p)
    cob = pick(COBBLE_PAL, rnd[:, 0])
    cast = smooth(0.28, 0.78, noise((X + Y) / 960.0 + p * 0.20, p * 0.75, 0))
    cob = mix(cob * 0.85, cob * 1.07, cast)
    late = float(smooth(58.0, 77.0, env.t))
    cob = mix(cob, C(238, 146, 108), 0.22 * late * cast)

    if to_lagoon.max() > 0.0:
        rx = sx - 960.0
        ly = -(sy - env.hz) / env.zoom * 1.12 - 6.0
        skyc = sky_rgb(rx, ly, rx + env.camX * PS, env, rnd)
        lag = mix(skyc, pick(LAGOON_PAL, rnd[:, 1]), 0.30 + 0.46 * near)
        rip = smooth(0.75, 0.95, rnd[:, 2] + 0.18 * np.sin(env.t * 1.8 + X * 0.012 + p * 6.0))
        lag = mix(lag, mix(skyc, C(255, 168, 104), 0.55), 0.48 * rip)
        cob = mix(cob, lag, to_lagoon)

    col = jitter(cob, rnd, 0.055, 0.025)
    sway = np.sin(env.t * (0.6 + 0.5 * rnd[:, 2]) + rnd[:, 3] * 6.28) * to_lagoon
    return Batch(sx + 4.0 * sway, sy, (rnd[:, 0] - 0.5) * 0.14, g["L"] * sc, g["W"] * sc, g["spr"], col, g["a"] * vis, 1.90 + 0.08 * g["lvl"] + p * 0.04, hb=0.72)


def _cathedral_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    vis = float(smooth(B3 - BW - 200.0, B3 - 50.0, env.camX)) * float(smooth(B4 + BW + 300.0, B4 - 100.0, env.camX))
    if vis <= 0.01:
        return None
    late = float(smooth(58.0, 77.0, env.t))
    lit_c = mix(pick(STONE_GOLD_AM, rnd[:, 0]), pick(STONE_GOLD_PM, rnd[:, 0]), late)
    shd_c = mix(pick(STONE_SHD_AM, rnd[:, 1]), pick(STONE_SHD_PM, rnd[:, 1]), late)
    col = mix(shd_c, lit_c, g["sun"][:, None])
    glow_m = g["is_rose"]
    if glow_m.max() > 0.0:
        rose_c = mix(C(252, 166, 86), C(222, 92, 128), rnd[:, 2])
        col = mix(col, rose_c, 0.72 * glow_m[:, None] * (0.55 + 0.45 * late))
    col = jitter(col, rnd, 0.045, 0.024)
    return Batch(sx, sy, g["ang"], g["L"] * sc, g["W"] * sc, g["spr"], col, g["a"] * vis, g["zo"], hb=0.90)


def _rouen_doves(env):
    batches = []
    vis = float(smooth(B3 - 300.0, B3 + 200.0, env.camX)) * float(smooth(B4 + 350.0, B4 - 150.0, env.camX))
    if vis <= 0.01:
        return batches
    t = env.t
    dx, dy, dang, dL, dW, dsp, dc = [], [], [], [], [], [], []
    for k in range(18):
        theta = t * (0.55 + 0.08 * (k % 3)) + k * 0.40
        X = 16050.0 + 980.0 * np.cos(theta) + 80.0 * np.sin(theta * 2.0 + k)
        Y = -720.0 + 145.0 * np.sin(theta) - (k % 4) * 55.0
        p = 0.48 + 0.08 * np.sin(theta)
        sx, sy, sc = env.project(X, Y, p)
        if not (-100 < sx < 2020):
            continue
        flap = 0.50 * np.sin(t * (5.6 + 0.5 * (k % 3)) + k * 1.3)
        wl = 24.0 * sc
        col = C(255, 224, 186) if np.cos(theta) > 0 else C(172, 152, 186)
        dx.extend([sx - wl * 0.4, sx + wl * 0.4])
        dy.extend([sy - flap * 6.0 * sc, sy - flap * 6.0 * sc])
        dang.extend([-0.28 + flap, 0.28 - flap])
        dL.extend([wl, wl]); dW.extend([7.0 * sc, 7.0 * sc])
        dsp.extend([DAB + (k % 4), DAB + ((k + 1) % 4)])
        dc.extend([col, col])
    if dx:
        batches.append(Batch(np.array(dx, np.float32), np.array(dy, np.float32), np.array(dang, np.float32),
                             np.array(dL, np.float32), np.array(dW, np.float32), np.array(dsp, np.int32),
                             np.array(dc, np.float32), 0.90 * vis, 3.3, hb=0.55))
    return batches


def build(rng):
    sets = []
    cam_lim = (B3 - BW - 300.0, B4 + BW + 650.0)

    for lvl, (bl, asp, a, pm) in enumerate([(135.0, 2.9, 0.94, 0.05), (68.0, 3.3, 0.90, 0.12), (35.0, 3.6, 0.86, 0.35)]):
        X, p, L, W = ground_rows(rng, B3 - 400.0, B4 + BW + 400.0, pm, 2.4, bl, asp, min_len=(48, 32, 20)[lvl])
        n = len(X)
        rnd = rnd_fields(rng, n)
        spr = np.where(rnd[:, 0] < 0.35, DAB + rng.integers(0, 6, n), DASH + rng.integers(0, 8, n)).astype(np.int32)
        sets.append(Set(f"rouen_plaza{lvl}", _plaza_shader, X, np.zeros(n), p, cam=cam_lim,
                        rnd=rnd, L=L, W=W, spr=spr, a=a, lvl=float(lvl)))

    cx = 16050.0
    Xs, Ys, ps, Ls, Ws, angs, sprs, suns, roses, alps, zos = [], [], [], [], [], [], [], [], [], [], []

    def add_block(x0, x1, y0, y1, p_v, count, sun_bias, base_L, base_W, ang_mu, zo_val, alo=0.90, is_rose=0.0):
        bx = rng.uniform(x0, x1, count)
        by = rng.uniform(y0, y1, count)
        rib = 0.5 + 0.5 * np.sin((bx - cx) * 0.055)
        sun = np.clip(sun_bias * 0.65 + 0.35 * rib + rng.uniform(-0.16, 0.16, count), 0.0, 1.0)
        Xs.append(bx); Ys.append(by); ps.append(np.full(count, p_v))
        Ls.append(rng.uniform(base_L * 0.75, base_L * 1.35, count))
        Ws.append(rng.uniform(base_W * 0.75, base_W * 1.35, count))
        angs.append(ang_mu + rng.uniform(-0.24, 0.24, count))
        sprs.append(np.where(rng.random(count) < 0.65, DAB + rng.integers(0, 6, count), DASH + rng.integers(0, 8, count)))
        suns.append(sun); roses.append(np.full(count, is_rose)); alps.append(rng.uniform(alo, 0.99, count)); zos.append(np.full(count, zo_val))

    # Flanking solid gabled medieval Rouen townhouses left & right of square (p = 0.36, zo = 2.34)
    for hx0, hx1, h_top, sb in [
        (cx - 2650.0, cx - 2150.0, -340.0, 0.32), (cx - 2150.0, cx - 1650.0, -450.0, 0.42), (cx - 1650.0, cx - 1160.0, -380.0, 0.35),
        (cx + 1160.0, cx + 1680.0, -410.0, 0.25), (cx + 1680.0, cx + 2200.0, -480.0, 0.30), (cx + 2200.0, cx + 2650.0, -320.0, 0.20),
    ]:
        add_block(hx0, hx1, h_top, 20.0, 0.36, 175, sb, 130.0, 78.0, 1.57, 2.34, alo=0.96)
        # Gable roof crown
        ng = 45
        tg = rng.random(ng)
        gy = h_top - 140.0 + tg * 150.0
        gx = 0.5 * (hx0 + hx1) + (rng.random(ng) * 2.0 - 1.0) * 0.52 * (hx1 - hx0) * tg
        Xs.append(gx); Ys.append(gy); ps.append(np.full(ng, 0.36))
        Ls.append(rng.uniform(72.0, 110.0, ng)); Ws.append(rng.uniform(44.0, 66.0, ng))
        angs.append(rng.uniform(-0.2, 0.2, ng)); sprs.append((DAB + rng.integers(0, 6, ng)).astype(np.int32))
        suns.append(np.full(ng, sb * 0.7)); roses.append(np.zeros(ng)); alps.append(np.full(ng, 0.96)); zos.append(np.full(ng, 2.35))

    # OPAQUE SOLID STONE UNDERPAINTING for Rouen Cathedral (zo = 2.40, dense big overlapping dabs so zero sky gaps!)
    add_block(cx - 860.0, cx + 860.0, -760.0, 20.0, 0.42, 1150, 0.60, 155.0, 96.0, 1.57, 2.40, alo=0.98)
    add_block(cx - 1080.0, cx - 540.0, -1180.0, 20.0, 0.42, 480, 0.72, 145.0, 90.0, 1.57, 2.40, alo=0.98)
    add_block(cx + 540.0, cx + 1090.0, -1280.0, 20.0, 0.42, 520, 0.50, 145.0, 90.0, 1.57, 2.40, alo=0.98)

    # SCULPTED GOTHIC IMPASTO DETAILS (zo = 2.46 .. 2.55)
    add_block(cx - 860.0, cx + 860.0, -760.0, 25.0, 0.42, 1550, 0.64, 58.0, 30.0, 1.57, 2.46, alo=0.88)
    add_block(cx - 1080.0, cx - 540.0, -1180.0, 25.0, 0.42, 650, 0.74, 52.0, 26.0, 1.57, 2.48, alo=0.88)

    # Tapered left spire (underpaint + detail)
    for n_sp1, bL, bW, zv, alo in [(140, 82.0, 48.0, 2.42, 0.94), (240, 40.0, 22.0, 2.50, 0.88)]:
        t1 = rng.random(n_sp1)
        sy1 = -1530.0 + t1 * 370.0
        sx1 = cx - 810.0 + (rng.random(n_sp1) * 2.0 - 1.0) * (16.0 + 190.0 * t1)
        Xs.append(sx1); Ys.append(sy1); ps.append(np.full(n_sp1, 0.42))
        Ls.append(rng.uniform(bL * 0.7, bL * 1.3, n_sp1)); Ws.append(rng.uniform(bW * 0.7, bW * 1.3, n_sp1))
        angs.append(1.57 + rng.uniform(-0.22, 0.22, n_sp1))
        sprs.append((DAB + rng.integers(0, 6, n_sp1)).astype(np.int32))
        suns.append(np.clip(0.85 - 0.55 * ((sx1 - (cx - 810.0)) / 185.0), 0.1, 1.0))
        roses.append(np.zeros(n_sp1)); alps.append(np.full(n_sp1, alo)); zos.append(np.full(n_sp1, zv))

    # Right Tower (Tour de Beurre) + crown pinnacles
    add_block(cx + 540.0, cx + 1090.0, -1280.0, 25.0, 0.42, 780, 0.52, 52.0, 26.0, 1.57, 2.48, alo=0.88)
    for px0 in [cx + 600.0, cx + 815.0, cx + 1030.0]:
        add_block(px0 - 55.0, px0 + 55.0, -1430.0, -1260.0, 0.42, 75, 0.72, 42.0, 24.0, 1.57, 2.51, alo=0.92)

    # Central triangular gable
    for n_g, bL, bW, zv, alo in [(150, 82.0, 48.0, 2.43, 0.94), (240, 42.0, 22.0, 2.51, 0.88)]:
        tg = rng.random(n_g)
        gy = -1050.0 + tg * 310.0
        gx = cx + (rng.random(n_g) * 2.0 - 1.0) * (20.0 + 350.0 * tg)
        Xs.append(gx); Ys.append(gy); ps.append(np.full(n_g, 0.42))
        Ls.append(rng.uniform(bL * 0.7, bL * 1.3, n_g)); Ws.append(rng.uniform(bW * 0.7, bW * 1.3, n_g))
        angs.append(1.57 + rng.uniform(-0.22, 0.22, n_g)); sprs.append((DAB + rng.integers(0, 6, n_g)).astype(np.int32))
        suns.append(np.clip(0.88 - 0.5 * ((gx - cx) / 340.0), 0.15, 1.0))
        roses.append(np.zeros(n_g)); alps.append(np.full(n_g, alo)); zos.append(np.full(n_g, zv))

    # Central Rose Window (center cx, y = -540)
    n_rw = 340
    r_th = rng.uniform(0.0, 6.28, n_rw)
    r_rad = np.sqrt(rng.random(n_rw)) * 215.0
    Xs.append(cx + np.cos(r_th) * r_rad); Ys.append(-540.0 + np.sin(r_th) * r_rad); ps.append(np.full(n_rw, 0.42))
    Ls.append(rng.uniform(28.0, 46.0, n_rw)); Ws.append(rng.uniform(18.0, 30.0, n_rw))
    angs.append(r_th + 1.57); sprs.append((DAB + rng.integers(0, 6, n_rw)).astype(np.int32))
    suns.append(np.full(n_rw, 0.35)); roses.append((r_rad < 175.0).astype(np.float32))
    alps.append(np.full(n_rw, 0.94)); zos.append(np.full(n_rw, 2.55))

    # Deep pointed arch portals
    for px_c, pw, ph in [(cx - 430.0, 175.0, 290.0), (cx, 235.0, 360.0), (cx + 430.0, 175.0, 290.0)]:
        np_c = 190
        px_a = rng.uniform(px_c - pw, px_c + pw, np_c)
        arch_lim = -ph * np.sqrt(np.maximum(0.0, 1.0 - ((px_a - px_c) / pw) ** 2))
        py_a = arch_lim + rng.random(np_c) * (-arch_lim + 25.0)
        Xs.append(px_a); Ys.append(py_a); ps.append(np.full(np_c, 0.42))
        Ls.append(rng.uniform(42.0, 66.0, np_c)); Ws.append(rng.uniform(26.0, 40.0, np_c))
        angs.append(1.57 + rng.uniform(-0.2, 0.2, np_c)); sprs.append((DAB + rng.integers(0, 6, np_c)).astype(np.int32))
        suns.append(np.full(np_c, 0.06))
        roses.append(np.where((np.abs(px_a - px_c) < 38.0) & (py_a > -110.0), 0.35, 0.0))
        alps.append(np.full(np_c, 0.96)); zos.append(np.full(np_c, 2.54))

    X_c = np.concatenate(Xs).astype(np.float32); Y_c = np.concatenate(Ys).astype(np.float32)
    sets.append(Set("rouen_cathedral", _cathedral_shader, X_c, Y_c, np.concatenate(ps).astype(np.float32),
                    cam=cam_lim, margin=480.0, rnd=rnd_fields(rng, len(X_c)),
                    L=np.concatenate(Ls).astype(np.float32), W=np.concatenate(Ws).astype(np.float32),
                    ang=np.concatenate(angs).astype(np.float32), spr=np.concatenate(sprs).astype(np.int32),
                    sun=np.concatenate(suns).astype(np.float32), is_rose=np.concatenate(roses).astype(np.float32),
                    a=np.concatenate(alps).astype(np.float32), zo=np.concatenate(zos).astype(np.float32)))

    return sets, [_rouen_doves]

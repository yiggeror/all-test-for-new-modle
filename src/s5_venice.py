"""Scene 5 (76s - 96s): San Giorgio Maggiore au Crepuscule (Pass 2 refined).

Dense violet-indigo island monastery, Palladian facade, grand dome, and tall
campanile properly depth-sorted above the Venetian lagoon so the entire island
sits solidly on the water with sunset rim-light, illuminated palazzi windows,
rippling reflections, and three gliding lantern-lit gondolas.
"""
import numpy as np
from engine import Batch, smooth, mix, noise, C, pal, pick, jitter, DASH, DAB, SCUM, GLOW
from world import Set, ground_rows, rnd_fields, B4, BW
from sky_atmo import sky_rgb, venice_sun_pos, PS

LAGOON_PAL = pal((34, 46, 98), (52, 54, 114), (82, 60, 124), (118, 66, 118), (26, 36, 82))
BASILICA_SHD = pal((42, 38, 86), (56, 48, 102), (34, 32, 76), (70, 54, 110))
BASILICA_RIM = pal((198, 90, 92), (230, 124, 78), (158, 76, 112), (244, 156, 94))


def _lagoon_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    t = env.t
    vis = float(smooth(B4 - BW - 250.0, B4 - 50.0, env.camX))
    if vis <= 0.01:
        return None
    rx = sx - 960.0
    ly = -(sy - env.hz) / env.zoom * 1.12 - 6.0
    skyc = sky_rgb(rx, ly, rx + env.camX * PS, env, rnd)

    near = smooth(0.08, 1.85, p)
    lag = mix(skyc, pick(LAGOON_PAL, rnd[:, 0]), 0.24 + 0.42 * near)

    sx4, sy4 = venice_sun_pos(env)
    below = np.maximum(sy - env.hz, 0.0)
    wcol = 24.0 + 0.14 * below + 22.0 * noise(below / 85.0, t * 0.14, 2)
    gx = np.exp(-((sx - (960.0 + sx4 + 12.0 * np.sin(below * 0.032 + t * 0.9))) / wcol) ** 2)
    fl = 0.5 + 0.5 * np.sin(t * (1.7 + 2.1 * rnd[:, 1]) + rnd[:, 3] * 6.28 + below * 0.025)
    glit = smooth(0.22, 0.76, gx * (0.55 + 0.65 * fl) * 1.25 - rnd[:, 0] * 0.48) * smooth(4.0, 22.0, below)
    lag = mix(lag, mix(C(250, 98, 66), C(255, 206, 116), fl * rnd[:, 2]), glit)

    rip = smooth(0.78, 0.96, rnd[:, 2] + 0.16 * np.sin(t * 1.6 + X * 0.012 + p * 7.0))
    lag = mix(lag, mix(skyc, C(238, 146, 152), 0.5), 0.42 * rip)

    col = jitter(lag, rnd, 0.05, 0.025)
    sway = np.sin(t * (0.55 + 0.45 * rnd[:, 2]) + rnd[:, 3] * 6.28)
    return Batch(sx + (3.5 + 4.5 * near) * sway, sy + 1.1 * np.sin(t * 0.8 + rnd[:, 1] * 6.28) * near,
                 (rnd[:, 0] - 0.5) * 0.10, g["L"] * sc * (1.0 + 0.1 * sway), g["W"] * sc,
                 g["spr"], col, g["a"] * vis, 1.88 + 0.10 * g["lvl"] + p * 0.06, hb=0.70)


def _san_giorgio_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    vis = float(smooth(B4 - BW - 150.0, B4 + 100.0, env.camX))
    if vis <= 0.01:
        return None
    rim = g["rim"]
    col = mix(pick(BASILICA_SHD, rnd[:, 0]), pick(BASILICA_RIM, rnd[:, 1]), rim[:, None])
    win_m = g["is_win"]
    if win_m.max() > 0.0:
        flick = 0.82 + 0.18 * np.sin(env.t * 3.8 + rnd[:, 2] * 6.28)
        wcol = mix(C(255, 166, 64), C(255, 224, 132), rnd[:, 3]) * flick[:, None]
        col = mix(col, wcol, win_m[:, None])
    col = jitter(col, rnd, 0.04, 0.02)
    mist = smooth(-32.0, 12.0, Y) * (1.0 - win_m)
    col = mix(col, C(168, 92, 134), 0.28 * mist)
    return Batch(sx, sy, g["ang"], g["L"] * sc, g["W"] * sc, g["spr"], col, g["a"] * vis, g["zo"], hb=0.75)


def _san_giorgio_refl_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    vis = float(smooth(B4 - BW - 150.0, B4 + 100.0, env.camX))
    if vis <= 0.01:
        return None
    t = env.t
    x_rip = sx + 6.5 * np.sin(t * 1.5 + sy * 0.05 + rnd[:, 1] * 3.0)
    col = mix(pick(BASILICA_SHD, rnd[:, 0]), C(46, 50, 102), 0.25)
    win_m = g["is_win"]
    if win_m.max() > 0.0:
        col = mix(col, C(255, 178, 86), 0.85 * win_m[:, None])
    return Batch(x_rip, sy, (rnd[:, 2] - 0.5) * 0.12, g["L"] * sc * 1.25, g["W"] * sc * 0.8,
                 g["spr"], col, g["a"] * 0.56 * vis, 2.24, hb=0.45)


def _venice_actors(env):
    batches = []
    vis = float(smooth(B4 - 300.0, B4 + 250.0, env.camX))
    if vis <= 0.01:
        return batches
    t = env.t
    dt = max(0.0, t - 74.0)

    gondolas = [
        (19450.0,  22.0, 0.78,  34.0, 1.12,  1.0),
        (20650.0, -14.0, 0.58, -28.0, 0.94, -1.0),
        (21300.0,  38.0, 0.92, -38.0, 1.22, -1.0),
    ]
    xs, ys, angs, Ls, Ws, sprs, rgbs, alps, zos = [], [], [], [], [], [], [], [], []
    for i, (X0, Y0, p, vx, sz, face) in enumerate(gondolas):
        X = X0 + dt * vx
        bob = 2.0 * np.sin(t * 1.6 + i * 2.1)
        sx, sy, sc = env.project(X, Y0 + bob, p)
        sc *= sz
        if not (-280 < sx < 2200):
            continue
        zb = 2.85 + p * 0.4

        for k in range(5):
            wx = sx - face * (65.0 + k * 28.0) * sc
            for sgn in [-1.0, 1.0]:
                wy = sy + (12.0 + sgn * (4.0 + k * 4.5)) * sc
                xs.append(wx); ys.append(wy); angs.append(sgn * 0.12 * face)
                Ls.append((46.0 + k * 10.0) * sc); Ws.append(8.0 * sc)
                sprs.append(DASH + (k % 8))
                rgbs.append(mix(C(246, 178, 134), C(152, 132, 188), k / 5.0))
                alps.append((0.54 - 0.08 * k) * vis); zos.append(2.30)

        xs.extend([sx, sx + face * 74.0 * sc, sx - face * 72.0 * sc])
        ys.extend([sy, sy - 12.0 * sc, sy - 10.0 * sc])
        angs.extend([0.0, -face * 0.45, face * 0.35])
        Ls.extend([166.0 * sc, 44.0 * sc, 38.0 * sc])
        Ws.extend([21.0 * sc, 12.0 * sc, 11.0 * sc])
        sprs.extend([DASH, DAB, DAB + 1])
        rgbs.extend([C(28, 24, 48), C(36, 30, 56), C(36, 30, 56)])
        alps.extend([0.97 * vis, 0.95 * vis, 0.95 * vis])
        zos.extend([zb, zb + 0.01, zb + 0.01])

        xs.append(sx + 3.0 * np.sin(t * 2.1 + i)); ys.append(sy + 18.0 * sc); angs.append(0.0)
        Ls.append(144.0 * sc); Ws.append(16.0 * sc); sprs.append(SCUM)
        rgbs.append(C(36, 34, 72)); alps.append(0.55 * vis); zos.append(2.28)

        gx = sx - face * 44.0 * sc
        oar_ang = face * (0.85 + 0.28 * np.sin(t * 2.2 + i))
        xs.extend([gx, gx, gx + face * 8.0 * sc])
        ys.extend([sy - 32.0 * sc, sy - 58.0 * sc, sy - 10.0 * sc])
        angs.extend([1.57, 0.0, oar_ang])
        Ls.extend([48.0 * sc, 15.0 * sc, 74.0 * sc])
        Ws.extend([14.0 * sc, 14.0 * sc, 5.0 * sc])
        sprs.extend([DAB + 2, DAB, DASH + 1])
        rgbs.extend([C(34, 30, 58), C(34, 30, 58), C(86, 62, 68)])
        alps.extend([0.96 * vis, 0.96 * vis, 0.90 * vis])
        zos.extend([zb + 0.02, zb + 0.03, zb + 0.02])

        lx = sx + face * 54.0 * sc
        ly = sy - 16.0 * sc
        flick = 0.88 + 0.12 * np.sin(t * 6.5 + i * 3.0)
        xs.extend([lx, lx]); ys.extend([ly, ly]); angs.extend([0.0, 0.0])
        Ls.extend([46.0 * sc * flick, 14.0 * sc]); Ws.extend([46.0 * sc * flick, 14.0 * sc])
        sprs.extend([GLOW, DAB]); rgbs.extend([C(255, 168, 68), C(255, 240, 178)])
        alps.extend([0.52 * vis, 0.97 * vis]); zos.extend([zb + 0.04, zb + 0.05])

        for rk in range(4):
            xs.append(lx + 4.0 * np.sin(t * 2.8 + rk + i)); ys.append(sy + (22.0 + rk * 18.0) * sc)
            angs.append(0.0); Ls.append((28.0 - rk * 3.0) * sc); Ws.append(8.0 * sc)
            sprs.append(DASH + rk); rgbs.append(mix(C(255, 212, 118), C(242, 142, 64), rk / 4.0))
            alps.append((0.74 - 0.14 * rk) * vis); zos.append(2.32)

    if xs:
        batches.append(Batch(np.array(xs, np.float32), np.array(ys, np.float32), np.array(angs, np.float32),
                             np.array(Ls, np.float32), np.array(Ws, np.float32), np.array(sprs, np.int32),
                             np.array(rgbs, np.float32), np.array(alps, np.float32), np.array(zos, np.float32), hb=0.72))
    return batches


def build(rng):
    sets = []
    cam_lim = (B4 - BW - 300.0, 25000.0)

    for lvl, (bl, asp, a, pm) in enumerate([(145.0, 3.2, 0.94, 0.03), (72.0, 3.6, 0.90, 0.10), (38.0, 3.9, 0.86, 0.34)]):
        X, p, L, W = ground_rows(rng, B4 - 400.0, 22600.0, pm, 2.5, bl, asp, min_len=(56, 38, 24)[lvl])
        n = len(X)
        rnd = rnd_fields(rng, n)
        spr = np.where(rnd[:, 0] < 0.25, SCUM + rng.integers(0, 6, n), DASH + rng.integers(0, 8, n)).astype(np.int32)
        sets.append(Set(f"lagoon{lvl}", _lagoon_shader, X, np.zeros(n), p, cam=cam_lim,
                        rnd=rnd, L=L, W=W, spr=spr, a=a, lvl=float(lvl)))

    cx = 20450.0
    Xs, Ys, Ls, Ws, angs, sprs, rims, wins, alps, zos = [], [], [], [], [], [], [], [], [], []

    def add_sil(x0, x1, y0, y1, count, base_L, base_W, rim_bias, zo_v, alo=0.92, is_win=0.0):
        bx = rng.uniform(x0, x1, count)
        by = rng.uniform(y0, y1, count)
        Xs.append(bx); Ys.append(by)
        Ls.append(rng.uniform(base_L * 0.75, base_L * 1.35, count))
        Ws.append(rng.uniform(base_W * 0.75, base_W * 1.35, count))
        angs.append(1.57 + rng.uniform(-0.22, 0.22, count))
        sprs.append(np.where(rng.random(count) < 0.6, DAB + rng.integers(0, 6, count), DASH + rng.integers(0, 8, count)))
        rim = np.clip(rim_bias + 0.45 * smooth(cx - 200.0, cx + 800.0, bx) * smooth(-600.0, -80.0, -np.abs(by + 300.0)), 0.0, 1.0)
        rims.append(rim); wins.append(np.full(count, is_win)); alps.append(rng.uniform(alo, 0.99, count)); zos.append(np.full(count, zo_v))

    # Dense opaque island monastery & basilica core (large overlapping strokes, zo = 2.40..2.43)
    add_sil(cx - 2100.0, cx + 2100.0, -215.0, 14.0, 1050, 128.0, 74.0, 0.14, 2.40, alo=0.98)
    add_sil(cx - 500.0, cx + 500.0, -455.0, 12.0, 480, 108.0, 66.0, 0.24, 2.43, alo=0.98)
    # Pediment
    npd = 115
    tp = rng.random(npd)
    py_p = -565.0 + tp * 125.0
    px_p = cx + (rng.random(npd) * 2.0 - 1.0) * (20.0 + 470.0 * tp)
    Xs.append(px_p); Ys.append(py_p); Ls.append(rng.uniform(68.0, 102.0, npd)); Ws.append(rng.uniform(38.0, 56.0, npd))
    angs.append(rng.uniform(-0.2, 0.2, npd)); sprs.append((DAB + rng.integers(0, 6, npd)).astype(np.int32))
    rims.append(np.full(npd, 0.35)); wins.append(np.zeros(npd)); alps.append(np.full(npd, 0.98)); zos.append(np.full(npd, 2.45))

    # Central Dome (thick solid core underpaint + sculpted painterly ribs)
    for ndm, bL, bW, zv, alo in [(240, 124.0, 78.0, 2.42, 0.99), (300, 54.0, 34.0, 2.46, 0.94)]:
        th_d = rng.uniform(0.0, np.pi, ndm)
        rr_d = np.sqrt(rng.random(ndm))
        dx_d = (cx - 40.0) + np.cos(th_d) * 335.0 * rr_d
        dy_d = -430.0 - np.sin(th_d) * 325.0 * rr_d
        Xs.append(dx_d); Ys.append(dy_d); Ls.append(rng.uniform(bL * 0.75, bL * 1.25, ndm))
        Ws.append(rng.uniform(bW * 0.75, bW * 1.25, ndm)); angs.append(th_d + 1.57)
        sprs.append((DAB + rng.integers(0, 6, ndm)).astype(np.int32))
        rims.append(np.clip(0.55 * smooth(-80.0, 260.0, dx_d - (cx - 40.0)), 0.0, 1.0))
        wins.append(np.zeros(ndm)); alps.append(np.full(ndm, alo)); zos.append(np.full(ndm, zv))
    add_sil(cx - 85.0, cx + 5.0, -860.0, -740.0, 65, 52.0, 34.0, 0.45, 2.47, alo=0.98)

    # Tall Campanile tower (solid core + painterly texture) + spire
    add_sil(cx + 465.0, cx + 695.0, -1040.0, 14.0, 440, 92.0, 56.0, 0.36, 2.48, alo=0.98)
    nsp = 145
    ts = rng.random(nsp)
    sy_s = -1400.0 + ts * 365.0
    sx_s = (cx + 580.0) + (rng.random(nsp) * 2.0 - 1.0) * (14.0 + 112.0 * ts)
    Xs.append(sx_s); Ys.append(sy_s); Ls.append(rng.uniform(52.0, 82.0, nsp)); Ws.append(rng.uniform(28.0, 44.0, nsp))
    angs.append(1.57 + rng.uniform(-0.2, 0.2, nsp)); sprs.append((DAB + rng.integers(0, 6, nsp)).astype(np.int32))
    rims.append(np.clip(0.65 * smooth(-40.0, 80.0, sx_s - (cx + 580.0)), 0.0, 1.0))
    wins.append(np.zeros(nsp)); alps.append(np.full(nsp, 0.98)); zos.append(np.full(nsp, 2.50))

    # Warm glowing lantern windows
    for wx, wy in [
        (cx + 580.0, -960.0), (cx - 1250.0, -85.0), (cx - 1020.0, -90.0),
        (cx - 740.0, -95.0), (cx + 1020.0, -85.0), (cx + 1260.0, -95.0), (cx + 1520.0, -85.0),
    ]:
        Xs.append(np.array([wx])); Ys.append(np.array([wy]))
        Ls.append(np.array([50.0])); Ws.append(np.array([36.0]))
        angs.append(np.array([1.57])); sprs.append(np.array([DAB]))
        rims.append(np.array([0.0])); wins.append(np.array([1.0]))
        alps.append(np.array([0.98])); zos.append(np.array([2.55]))

    X_sg = np.concatenate(Xs).astype(np.float32); Y_sg = np.concatenate(Ys).astype(np.float32)
    wins_a = np.concatenate(wins).astype(np.float32)
    sets.append(Set("san_giorgio", _san_giorgio_shader, X_sg, Y_sg, np.full(len(X_sg), 0.36, np.float32),
                    cam=cam_lim, margin=450.0, rnd=rnd_fields(rng, len(X_sg)),
                    L=np.concatenate(Ls).astype(np.float32), W=np.concatenate(Ws).astype(np.float32),
                    ang=np.concatenate(angs).astype(np.float32), spr=np.concatenate(sprs).astype(np.int32),
                    rim=np.concatenate(rims).astype(np.float32), is_win=wins_a,
                    a=np.concatenate(alps).astype(np.float32), zo=np.concatenate(zos).astype(np.float32)))

    rk = (Y_sg < -15.0) & ((rng.random(len(X_sg)) < 0.44) | (wins_a > 0.5))
    sets.append(Set("san_giorgio_refl", _san_giorgio_refl_shader, X_sg[rk], -Y_sg[rk] * 0.72,
                    np.full(int(rk.sum()), 0.36, np.float32), cam=cam_lim, margin=420.0,
                    rnd=rnd_fields(rng, int(rk.sum())), L=np.concatenate(Ls)[rk].astype(np.float32),
                    W=np.concatenate(Ws)[rk].astype(np.float32), spr=np.concatenate(sprs)[rk].astype(np.int32),
                    is_win=wins_a[rk], a=0.80))

    return sets, [_venice_actors]

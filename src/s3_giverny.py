"""Scene 3 (38s - 58s): Le Jardin de l'Artiste a Giverny (Pass 3 refined).

True world-anchored gravel Grande Allee leading straight to Monet's solid
pink-stucco & slate-roofed house with emerald shutters; 4 lush rose arches with
trellis posts rooted in foliage beds; clean flower-bed borders flanking the
gravel path with zero flowers standing inside the center walk.
"""
import numpy as np
from engine import Batch, smooth, mix, noise, C, pal, pick, jitter, DASH, DAB, SCUM
from world import Set, ground_rows, rnd_fields, scene_coord, scene_of, B2, B3, BW

LAWN_PAL = pal((62, 120, 52), (88, 146, 62), (114, 166, 74), (48, 94, 46), (140, 176, 84))
GRAVEL_PAL = pal((226, 208, 178), (240, 224, 194), (206, 188, 162), (246, 234, 208))
COBBLE_PAL = pal((196, 176, 166), (218, 192, 174), (162, 152, 168), (232, 206, 182), (138, 134, 158))
IRIS_PAL = pal((118, 86, 188), (148, 116, 214), (90, 62, 158), (178, 152, 232), (136, 98, 200))
NAST_PAL = pal((246, 158, 48), (242, 108, 44), (252, 206, 72), (232, 82, 46))
ROSE_PAL = pal((246, 166, 182), (236, 122, 148), (254, 214, 220), (222, 92, 124), (255, 240, 234))
GARDEN_LEAF = pal((48, 102, 46), (72, 128, 56), (96, 152, 66), (38, 82, 42), (122, 170, 76))


def path_center_X(p):
    """World-space Grande Allee leading toward Monet's Giverny house (X=11450 at p=0.28)."""
    return 11450.0 - 290.0 * (p - 0.28) + 60.0 * np.sin(p * 2.2)


def path_half_w(p):
    return 165.0 / np.maximum(p, 0.25)


def _garden_ground_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    vis = float(smooth(B2 - BW - 250.0, B2, env.camX)) * float(smooth(B3 + BW + 550.0, B3 + BW - 200.0, env.camX))
    if vis <= 0.01:
        return None
    wiggle = 220.0 * np.sin(p * 2.8) + 150.0 * noise(X / 600.0, p * 1.2, 1)
    u = scene_coord(X + wiggle, p, env.camX)
    d = scene_of(u)
    to_cobble = smooth(2.25, 2.92, d)

    lat_w = np.abs(X - path_center_X(p))
    hw = path_half_w(p)
    in_path = smooth(hw * 1.18, hw * 0.62, lat_w) * (1.0 - to_cobble)

    lawn = pick(LAWN_PAL, rnd[:, 0])
    gravel = pick(GRAVEL_PAL, rnd[:, 1])
    dapple = noise(X / 240.0 + env.t * 0.02, p * 2.5, 0)
    gravel = mix(gravel * 0.80, gravel * 1.06, smooth(0.32, 0.68, dapple))
    col = mix(lawn, gravel, 0.88 * in_path)

    edge_spill = smooth(hw * 1.32, hw * 0.92, lat_w) * smooth(hw * 0.55, hw * 0.88, lat_w) * smooth(0.45, 0.85, rnd[:, 2]) * (1.0 - to_cobble)
    col = mix(col, pick(NAST_PAL, rnd[:, 3]), 0.65 * edge_spill)

    if to_cobble.max() > 0.0:
        cob = pick(COBBLE_PAL, rnd[:, 2])
        sun_p = smooth(0.30, 0.76, noise(X / 680.0, p * 1.4, 1))
        cob = mix(cob * 0.84, cob * 1.07, sun_p)
        col = mix(col, cob, to_cobble)

    col = jitter(col, rnd, 0.055, 0.024)
    return Batch(sx, sy, (rnd[:, 0] - 0.5) * 0.18, g["L"] * sc, g["W"] * sc, g["spr"], col, g["a"] * vis, 1.92 + 0.08 * g["lvl"] + p * 0.04, hb=0.72)


def _sway_flower_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    vis = float(smooth(B2 - 300.0, B2 + 250.0, env.camX)) * float(smooth(B3 + BW + 250.0, B3 - 100.0, env.camX))
    if vis <= 0.01:
        return None
    w = env.wind(X, p)
    gust = (w - 0.35) * 0.44 + 0.08 * np.sin(env.t * 2.5 + X * 0.025 + rnd[:, 0] * 6.28)
    flex = g["flex"]
    dx = gust * 24.0 * sc * flex
    dy = np.abs(gust) * 4.5 * sc * flex
    ang = g["ang"] + gust * 0.40 * flex
    col = jitter(g["rgb"], rnd, 0.05, 0.026)
    return Batch(sx + dx, sy + dy, ang, g["L"] * sc, g["W"] * sc, g["spr"], col, g["a"] * vis, g["zo"] + p * 0.10, hb=0.84)


def _house_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    vis = float(smooth(B2 - 200.0, B2 + 350.0, env.camX)) * float(smooth(B3 + 300.0, B3 - 250.0, env.camX))
    if vis <= 0.01:
        return None
    col = jitter(g["rgb"], rnd, 0.04, 0.018)
    return Batch(sx, sy, g["ang"], g["L"] * sc, g["W"] * sc, g["spr"], col, g["a"] * vis, g["zo"], hb=0.82)


def build(rng):
    sets = []
    cam_lim = (B2 - BW - 300.0, B3 + BW + 600.0)

    for lvl, (bl, asp, a, pm) in enumerate([(130.0, 2.8, 0.94, 0.05), (66.0, 3.2, 0.90, 0.12), (34.0, 3.4, 0.86, 0.36)]):
        X, p, L, W = ground_rows(rng, B2 - 400.0, B3 + BW + 400.0, pm, 2.4, bl, asp, min_len=(48, 32, 20)[lvl])
        n = len(X)
        rnd = rnd_fields(rng, n)
        spr = np.where(rnd[:, 0] < 0.35, DAB + rng.integers(0, 6, n), DASH + rng.integers(0, 8, n)).astype(np.int32)
        sets.append(Set(f"gard_ground{lvl}", _garden_ground_shader, X, np.zeros(n), p, cam=cam_lim,
                        rnd=rnd, L=L, W=W, spr=spr, a=a, lvl=float(lvl)))

    # 2. Monet's Giverny House (X = 11450, p = 0.28, solid underpainting + pink stucco + crisp slate roof + shutters)
    hx, hy, hp, hL, hW, hang, hspr, hc, hzo = [], [], [], [], [], [], [], [], []
    for tx in np.linspace(8900.0, 13900.0, 38):
        if 10380.0 < tx < 12520.0:
            continue
        nt = 55
        th = rng.uniform(380.0, 740.0)
        u_h = rng.random(nt)
        ang = rng.uniform(0.0, 6.28, nt)
        hx.append(tx + np.cos(ang) * rng.uniform(95.0, 165.0) * (0.4 + 0.6 * np.sin(u_h * np.pi)))
        hy.append(-u_h * th); hp.append(np.full(nt, 0.27))
        hL.append(rng.uniform(95.0, 160.0, nt)); hW.append(rng.uniform(62.0, 105.0, nt))
        hang.append(1.57 + rng.uniform(-0.5, 0.5, nt))
        hspr.append(np.where(rng.random(nt) < 0.5, SCUM + rng.integers(0, 6, nt), DAB + rng.integers(0, 6, nt)))
        hc.append(mix(C(38, 84, 46), pick(GARDEN_LEAF, rng.random(nt)), u_h[:, None] * 0.7 + 0.3))
        hzo.append(np.full(nt, 2.38))

    # Solid opaque pink stucco underpaint + sculpted facade (zo = 2.42 .. 2.45)
    for n_h, bL, bW, zv in [(220, 195.0, 115.0, 2.42), (240, 95.0, 56.0, 2.45)]:
        hx.append(rng.uniform(10410.0, 12490.0, n_h)); hy.append(rng.uniform(-430.0, 5.0, n_h))
        hp.append(np.full(n_h, 0.28)); hL.append(rng.uniform(bL * 0.8, bL * 1.25, n_h)); hW.append(rng.uniform(bW * 0.8, bW * 1.25, n_h))
        hang.append(rng.uniform(-0.1, 0.1, n_h)); hspr.append(DAB + rng.integers(0, 6, n_h))
        hc.append(pick(pal((238, 178, 168), (228, 164, 156), (246, 194, 180)), rng.random(n_h)))
        hzo.append(np.full(n_h, zv))

    # Solid pitched slate-blue roof (tapered trapezoid Y = -595..-415, zo = 2.44..2.47)
    for n_r, bL, bW, zv in [(150, 170.0, 92.0, 2.44), (160, 95.0, 48.0, 2.47)]:
        t_ry = rng.random(n_r)
        ry = -595.0 + t_ry * 185.0
        half_rw = 880.0 + 210.0 * t_ry
        rx = 11450.0 + (rng.random(n_r) * 2.0 - 1.0) * half_rw
        hx.append(rx); hy.append(ry); hp.append(np.full(n_r, 0.28))
        hL.append(rng.uniform(bL * 0.8, bL * 1.2, n_r)); hW.append(rng.uniform(bW * 0.8, bW * 1.2, n_r))
        hang.append(rng.uniform(-0.12, 0.12, n_r)); hspr.append(DAB + rng.integers(0, 6, n_r))
        hc.append(pick(pal((80, 92, 124), (96, 108, 140), (68, 78, 108)), rng.random(n_r)))
        hzo.append(np.full(n_r, zv))

    # Warm cream dormer windows & iconic green shutters
    for wx in [10720.0, 11085.0, 11450.0, 11815.0, 12180.0]:
        for wy in [-325.0, -165.0]:
            hx.append(np.array([wx])); hy.append(np.array([wy])); hp.append(np.array([0.28]))
            hL.append(np.array([86.0])); hW.append(np.array([94.0])); hang.append(np.array([1.57]))
            hspr.append(np.array([DAB])); hc.append(np.array([C(246, 224, 172)])); hzo.append(np.array([2.49]))
            for sgn in [-64.0, 64.0]:
                hx.append(np.array([wx + sgn])); hy.append(np.array([wy])); hp.append(np.array([0.28]))
                hL.append(np.array([92.0])); hW.append(np.array([48.0])); hang.append(np.array([1.57]))
                hspr.append(np.array([DASH + 1])); hc.append(np.array([C(52, 128, 74)])); hzo.append(np.array([2.50]))

    X_h = np.concatenate(hx).astype(np.float32); Y_h = np.concatenate(hy).astype(np.float32)
    sets.append(Set("giverny_house", _house_shader, X_h, Y_h, np.concatenate(hp).astype(np.float32),
                    cam=cam_lim, margin=360.0, rnd=rnd_fields(rng, len(X_h)),
                    L=np.concatenate(hL).astype(np.float32), W=np.concatenate(hW).astype(np.float32),
                    ang=np.concatenate(hang).astype(np.float32), spr=np.concatenate(hspr).astype(np.int32),
                    rgb=np.concatenate(hc).astype(np.float32), a=0.96, zo=np.concatenate(hzo).astype(np.float32)))

    # 3. Swaying Iris, Nasturtium & Rose-Arch Flora strictly outside Grande Allee gravel corridor!
    fx, fy, fp, fL, fW, fang, fspr, fc, fzo, fflex = [], [], [], [], [], [], [], [], [], []
    n_bed = 3400
    bp = rng.uniform(0.32, 1.85, n_bed)
    bx = rng.uniform(B2 - 200.0, B3 + 450.0, n_bed)
    # Exclude center of the Grande Allee gravel path in true world space!
    keep = np.abs(bx - path_center_X(bp)) > path_half_w(bp) * 0.94
    bx, bp = bx[keep], bp[keep]
    n_k = len(bx)
    by_stem = -rng.uniform(22.0, 92.0, n_k) / np.sqrt(bp)

    fx.append(bx); fy.append(by_stem * 0.5); fp.append(bp)
    fL.append(np.abs(by_stem) * 1.15); fW.append(rng.uniform(6.0, 11.0, n_k))
    fang.append(np.full(n_k, 1.57) + rng.uniform(-0.18, 0.18, n_k))
    fspr.append((DASH + rng.integers(0, 8, n_k)).astype(np.int32))
    fc.append(pick(GARDEN_LEAF, rng.random(n_k)))
    fzo.append(np.full(n_k, 2.75)); fflex.append(np.full(n_k, 0.6))

    kind_r = rng.random(n_k)
    bcol = np.where(
        (kind_r < 0.55)[:, None], pick(IRIS_PAL, rng.random(n_k)),
        np.where((kind_r < 0.82)[:, None], pick(NAST_PAL, rng.random(n_k)), pick(ROSE_PAL, rng.random(n_k))),
    )
    fx.append(bx + rng.uniform(-10.0, 10.0, n_k)); fy.append(by_stem); fp.append(bp)
    fL.append(rng.uniform(24.0, 44.0, n_k) / (bp ** 0.25))
    fW.append(rng.uniform(15.0, 28.0, n_k) / (bp ** 0.25))
    fang.append(rng.uniform(-0.8, 0.8, n_k))
    fspr.append((DAB + rng.integers(0, 6, n_k)).astype(np.int32))
    fc.append(bcol); fzo.append(np.full(n_k, 2.82)); fflex.append(np.full(n_k, 1.0))

    # Four Rose-Draped Arches aligned along the Grande Allee with grounded wooden trellis posts & shrub feet
    arches = [(path_center_X(0.72), 0.72), (path_center_X(0.86), 0.86), (path_center_X(1.00), 1.00), (path_center_X(1.16), 1.16)]
    for ax0, ap in arches:
        rad_x = 390.0 / ap
        arch_base_y = -210.0 / ap
        arch_ry = 360.0 / ap
        for sgn in [-1.0, 1.0]:
            # Grounded dark-olive trellis post all the way into the soil (Y = +18 .. arch_base_y)
            np_post = 6
            fx.append(np.full(np_post, ax0 + sgn * rad_x))
            fy.append(np.linspace(arch_base_y, 18.0, np_post))
            fp.append(np.full(np_post, ap))
            fL.append(np.full(np_post, 90.0 / ap)); fW.append(np.full(np_post, 14.0 / ap))
            fang.append(np.full(np_post, 1.57)); fspr.append(np.full(np_post, DASH, np.int32))
            fc.append(np.broadcast_to(C(66, 92, 54), (np_post, 3)))
            fzo.append(np.full(np_post, 2.98)); fflex.append(np.zeros(np_post))

            npil = 60
            px_pil = ax0 + sgn * rad_x + rng.uniform(-34.0 / ap, 34.0 / ap, npil)
            py_pil = rng.uniform(arch_base_y, 18.0, npil)
            fx.append(px_pil); fy.append(py_pil); fp.append(np.full(npil, ap))
            fL.append(rng.uniform(46.0, 76.0, npil) / ap); fW.append(rng.uniform(32.0, 52.0, npil) / ap)
            fang.append(1.57 + rng.uniform(-0.35, 0.35, npil))
            fspr.append((SCUM + rng.integers(0, 6, npil)).astype(np.int32))
            fc.append(pick(GARDEN_LEAF, rng.random(npil))); fzo.append(np.full(npil, 3.02)); fflex.append(np.full(npil, 0.35))

            nrp = 38
            fx.append(ax0 + sgn * rad_x + rng.uniform(-36.0 / ap, 36.0 / ap, nrp))
            fy.append(rng.uniform(arch_base_y, 10.0, nrp)); fp.append(np.full(nrp, ap))
            fL.append(rng.uniform(28.0, 44.0, nrp) / ap); fW.append(rng.uniform(22.0, 34.0, nrp) / ap)
            fang.append(rng.uniform(0.0, 3.14, nrp)); fspr.append((DAB + rng.integers(0, 6, nrp)).astype(np.int32))
            fc.append(pick(ROSE_PAL, rng.random(nrp))); fzo.append(np.full(nrp, 3.08)); fflex.append(np.full(nrp, 0.5))

        na = 190
        th = rng.uniform(0.0, np.pi, na)
        ax = ax0 + np.cos(th) * (rad_x + rng.uniform(-38.0 / ap, 38.0 / ap, na))
        ay = arch_base_y - np.sin(th) * (arch_ry + rng.uniform(-32.0 / ap, 32.0 / ap, na))
        fx.append(ax); fy.append(ay); fp.append(np.full(na, ap))
        fL.append(rng.uniform(52.0, 82.0, na) / ap); fW.append(rng.uniform(34.0, 56.0, na) / ap)
        fang.append(th + 1.57 + rng.uniform(-0.4, 0.4, na))
        fspr.append((SCUM + rng.integers(0, 6, na)).astype(np.int32))
        fc.append(pick(GARDEN_LEAF, rng.random(na))); fzo.append(np.full(na, 3.04)); fflex.append(np.full(na, 0.45))

        nr_c = 160
        thr = rng.uniform(0.0, np.pi, nr_c)
        rx = ax0 + np.cos(thr) * (rad_x + rng.uniform(-40.0 / ap, 40.0 / ap, nr_c))
        ry = arch_base_y - np.sin(thr) * (arch_ry + rng.uniform(-34.0 / ap, 34.0 / ap, nr_c))
        fx.append(rx); fy.append(ry); fp.append(np.full(nr_c, ap))
        fL.append(rng.uniform(30.0, 48.0, nr_c) / ap); fW.append(rng.uniform(22.0, 36.0, nr_c) / ap)
        fang.append(rng.uniform(0.0, 3.14, nr_c)); fspr.append((DAB + rng.integers(0, 6, nr_c)).astype(np.int32))
        fc.append(pick(ROSE_PAL, rng.random(nr_c))); fzo.append(np.full(nr_c, 3.12)); fflex.append(np.full(nr_c, 0.65))

    X_f = np.concatenate(fx).astype(np.float32); Y_f = np.concatenate(fy).astype(np.float32)
    p_f = np.concatenate(fp).astype(np.float32)
    sets.append(Set("giverny_flora", _sway_flower_shader, X_f, Y_f, p_f, cam=cam_lim, margin=360.0,
                    rnd=rnd_fields(rng, len(X_f)), L=np.concatenate(fL).astype(np.float32),
                    W=np.concatenate(fW).astype(np.float32), ang=np.concatenate(fang).astype(np.float32),
                    spr=np.concatenate(fspr).astype(np.int32), rgb=np.concatenate(fc).astype(np.float32),
                    a=0.93, zo=np.concatenate(fzo).astype(np.float32), flex=np.concatenate(fflex).astype(np.float32)))

    return sets, []

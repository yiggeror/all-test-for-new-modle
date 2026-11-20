"""Dense, deeply layered 3D French countryside, village houses, church steeple, stone viaduct,
hedgerows, orchards, weeping willows & Guinguette cafe for Un Dimanche sur la Seine.

Every static group is built with rich Monet shadow-vs-light color contrast and bold ridge
visibility (smin calibrated for distance) so both foreground and far horizon feel fully lived-in.
"""
import math
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, LENS, WASH, C, mix, jitter
from anim.paint.world3 import SB, STAND, OVER
from scene_geom import river_x, river_hw, terrain_y


def _norm3(v):
    v = np.asarray(v, np.float64)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12)


def _add_canopy_cluster(sb, rng, cx, cy, cz, rx, ry, rz, n, csh, cli, smin=5.8, L0=1.45, W0=0.88, flex=0.14):
    u = rng.normal(0.0, 0.48, (n, 3))
    r = np.linalg.norm(u, axis=1, keepdims=True)
    scale = np.minimum(1.0, 0.88 / (r + 1e-6)) * (0.42 + 0.58 * rng.random((n, 1)))
    u = u * scale
    P = np.column_stack([cx + u[:, 0] * rx, cy + u[:, 1] * ry, cz + u[:, 2] * rz])
    N = _norm3(np.column_stack([u[:, 0] / max(rx, 0.1), (u[:, 1] + 0.38) / max(ry, 0.1), u[:, 2] / max(rz, 0.1)]))
    D = _norm3(np.column_stack([-u[:, 2] + rng.normal(0, 0.3, n), 0.35 + rng.normal(0, 0.35, n), u[:, 0] + rng.normal(0, 0.3, n)]))
    edge = np.clip(np.linalg.norm(u[:, [0, 2]], axis=1), 0.0, 1.0)
    rnd = rng.random((n, 3)).astype(np.float32)
    csh_arr = jitter(np.tile(csh, (n, 1)), rnd, val=0.06, chroma=0.04)
    cli_arr = jitter(np.tile(cli, (n, 1)), rnd, val=0.06, chroma=0.04)
    spr = np.where(rng.random(n) < 0.55, DAB + rng.integers(0, 4, n), SCUM + rng.integers(0, 4, n))
    sb.add(
        P, D=D,
        L=L0 * (0.72 + 0.65 * rng.random(n)),
        W=W0 * (0.72 + 0.55 * rng.random(n)),
        spr=spr, csh=csh_arr, cli=cli_arr, N=N,
        flex=flex * (0.4 + 0.8 * edge), smin=smin, a=0.95,
    )


def _add_trunk(sb, rng, x, y0, z, h, r_bot, csh, cli, lean_x=0.0):
    segs = 6
    pts, dirs, Ls, Ws = [], [], [], []
    for k in range(segs):
        u0, u1 = k / segs, (k + 1) / segs
        ym = y0 + (u0 + u1) * 0.5 * h
        xm = x + lean_x * (u0 + u1) * 0.5
        for j in range(3):
            a = j * 2.094 + k * 0.7
            rad = r_bot * (1.0 - 0.6 * u0) * 0.45
            pts.append([xm + math.cos(a) * rad, ym, z + math.sin(a) * rad])
            dirs.append([lean_x / max(h, 1.0), 1.0, 0.08 * math.sin(a)])
            Ls.append((h / segs) * 1.45)
            Ws.append(r_bot * (1.85 - 0.9 * u0))
    P = np.array(pts, np.float64)
    D = _norm3(dirs)
    N = _norm3(np.column_stack([P[:, 0] - x, np.full(len(P), 0.25), P[:, 2] - z]))
    sb.add(P, D=D, L=np.array(Ls), W=np.array(Ws), spr=DASH + 1, csh=csh, cli=cli, N=N, flex=0.02, smin=5.2)


def _add_cottage(sb, lamps_sb, rng, x, z, w, d, h, yaw, wall_sh, wall_li, roof_sh, roof_li, windows=True):
    """Build a solid 3D French cottage/townhouse seated cleanly on terrain_y(x, z)."""
    y0 = float(terrain_y(x, z)) - 0.25
    ax = np.array([math.cos(yaw), 0.0, math.sin(yaw)], np.float64)
    az = np.array([-math.sin(yaw), 0.0, math.cos(yaw)], np.float64)
    up = np.array([0.0, 1.0, 0.0], np.float64)
    origin = np.array([x, y0, z], np.float64)

    # Four solid plaster/stone walls
    step_u, step_v = 1.15, 0.95
    nw = max(4, int(round(w / step_u)))
    nd = max(3, int(round(d / step_u)))
    nh = max(3, int(round(h / step_v)))

    for u in np.linspace(-0.5, 0.5, nw):
        for v in np.linspace(0.08, 0.95, nh):
            for sgn in (-1.0, 1.0):
                p = origin + ax * (u * w) + az * (sgn * d * 0.5) + up * (v * h)
                sb.add([p], D=ax, L=1.55, W=1.18, spr=DAB + rng.integers(0, 4), csh=wall_sh, cli=wall_li, N=az * sgn + up * 0.1, smin=5.0, a=0.98)
    for w_u in np.linspace(-0.5, 0.5, nd):
        for v in np.linspace(0.08, 0.95, nh):
            for sgn in (-1.0, 1.0):
                p = origin + ax * (sgn * w * 0.5) + az * (w_u * d) + up * (v * h)
                sb.add([p], D=az, L=1.55, W=1.18, spr=DAB + rng.integers(0, 4), csh=wall_sh, cli=wall_li, N=ax * sgn + up * 0.1, smin=5.0, a=0.98)

    # Pitched hipped/gabled roof
    rh = max(1.8, d * 0.42)
    nr = max(4, int(round(d * 0.5 / 0.85)))
    for r_i in np.linspace(0.0, 1.0, nr):
        ry = h + r_i * rh
        z_off = (1.0 - r_i) * d * 0.54
        for u in np.linspace(-0.52, 0.52, nw + 1):
            for sgn in (-1.0, 1.0):
                p = origin + ax * (u * w) + az * (sgn * z_off) + up * ry
                n_r = _norm3(az * sgn * 0.7 + up * 0.7)
                sb.add([p], D=ax, L=1.65, W=1.08, spr=DASH + 1, csh=roof_sh, cli=roof_li, N=n_r, smin=5.2, a=0.98)

    # Chimney
    cp = origin + ax * (w * 0.28) + up * (h + rh + 0.4)
    sb.add([cp], D=up, L=1.4, W=0.65, spr=DASH, csh=wall_sh * 0.85, cli=wall_li * 0.9, N=(0.5, 0.7, 0.3), smin=4.5)

    # Warm dusk windows facing outward (-az)
    if windows and lamps_sb is not None:
        nwin = max(2, int(round(w / 3.4)))
        for k in range(nwin):
            wu = -0.35 + 0.70 * (k / max(1, nwin - 1))
            for wy in (h * 0.36, h * 0.74) if h > 4.4 else (h * 0.52,):
                wp = origin + ax * (wu * w) - az * (d * 0.5 + 0.12) + up * wy
                sb.add([wp], D=up, L=0.95, W=0.65, spr=DASH, csh=C(54, 62, 82), cli=C(88, 96, 122), N=-az, smin=4.5)
                lamps_sb.add([wp - az * 0.05], D=up, L=0.78, W=0.52, spr=DAB, csh=C(255, 194, 88), cli=C(255, 224, 128), N=-az, emis=1.0, smin=4.0)


def _add_stone_wall_or_hedge(sb, rng, x0, z0, x1, z1, is_hedge=True):
    """Add organic dry-stone farm wall or flowering hawthorn hedgerow along hillside plots."""
    dist = math.hypot(x1 - x0, z1 - z0)
    n = max(4, int(dist / 1.4))
    for i in range(n):
        u = (i + 0.5) / n
        x = x0 * (1 - u) + x1 * u + rng.uniform(-0.25, 0.25)
        z = z0 * (1 - u) + z1 * u + rng.uniform(-0.25, 0.25)
        y = float(terrain_y(x, z)) + (0.65 if is_hedge else 0.48)
        if is_hedge:
            sb.add(
                [[x, y, z]], D=(x1 - x0, 0.2, z1 - z0), L=1.85, W=1.25,
                spr=SCUM + (i % 4), csh=C(40, 78, 56), cli=C(108, 152, 68),
                N=(0.2, 0.95, 0.1), flex=0.08, smin=5.5, a=0.95,
            )
            if i % 3 == 0:
                sb.add(
                    [[x + rng.uniform(-0.4, 0.4), y + 0.45, z + rng.uniform(-0.4, 0.4)]],
                    D=(1, 0, 0), L=0.68, W=0.56, spr=DAB,
                    csh=C(196, 186, 206), cli=C(254, 244, 232), N=(0, 1, 0), smin=4.5,
                )
        else:
            sb.add(
                [[x, y, z]], D=(x1 - x0, 0.0, z1 - z0), L=1.75, W=0.82,
                spr=DASH + (i % 6), csh=C(106, 102, 124), cli=C(208, 192, 168),
                N=(0.1, 0.9, 0.2), smin=5.2, a=0.96,
            )


def _build_viaduct(rng):
    """5-arch Stone Railway Viaduct at Z=215 with organic ashlar stonework."""
    sb = SB(rng)
    zv = 215.0
    cx = float(river_x(zv))
    arch_centers = [cx - 42.0, cx - 21.0, cx, cx + 21.0, cx + 42.0]
    pier_xs = [cx - 52.5, cx - 31.5, cx - 10.5, cx + 10.5, cx + 31.5, cx + 52.5]
    deck_y = 13.8
    arch_crown = 10.6
    arch_spring = 3.2
    half_span = 8.4

    stone_sh = C(116, 108, 132)
    stone_li = C(228, 206, 174)
    vault_sh = C(72, 70, 98)
    vault_li = C(142, 132, 134)

    for px in pier_xs:
        n_st = 220
        sx = px + rng.uniform(-2.1, 2.1, n_st)
        sy = rng.uniform(-0.1, deck_y - 0.2, n_st)
        sz = zv + rng.uniform(-3.6, 3.6, n_st)
        surf = (np.abs(sx - px) > 1.1) | (np.abs(sz - zv) > 2.2)
        P = np.column_stack([sx[surf], sy[surf], sz[surf]])
        N = _norm3(np.column_stack([(P[:, 0] - px) * 0.6, np.full(len(P), 0.2), (P[:, 2] - zv) * 0.9]))
        D = _norm3(np.column_stack([np.ones(len(P)), rng.uniform(-0.08, 0.08, len(P)), np.zeros(len(P))]))
        rnd = rng.random((len(P), 3)).astype(np.float32)
        sb.add(
            P, D=D, L=rng.uniform(1.6, 2.5, len(P)), W=rng.uniform(0.75, 1.15, len(P)),
            spr=DASH + rng.integers(0, 8, len(P)),
            csh=jitter(np.tile(stone_sh, (len(P), 1)), rnd, 0.08, 0.03),
            cli=jitter(np.tile(stone_li, (len(P), 1)), rnd, 0.08, 0.03),
            N=N, smin=5.0, a=0.96,
        )

    for ac in arch_centers:
        ang = np.linspace(0.0, math.pi, 32)
        zs = np.linspace(zv - 3.4, zv + 3.4, 9)
        ag, zg = np.meshgrid(ang, zs, indexing="ij")
        vx = ac - half_span * np.cos(ag) + rng.normal(0.0, 0.12, ag.shape)
        vy = arch_spring + (arch_crown - arch_spring) * np.sin(ag) + rng.normal(0.0, 0.10, ag.shape)
        P = np.column_stack([vx.ravel(), vy.ravel(), zg.ravel()])
        N = _norm3(np.column_stack([np.cos(ag.ravel()) * 0.5, -np.sin(ag.ravel()), np.zeros(len(P))]))
        D = np.column_stack([-np.sin(ag.ravel()), np.cos(ag.ravel()) * 0.5, np.zeros(len(P))])
        sb.add(P, D=D, L=1.65, W=1.15, spr=DASH + 2, csh=vault_sh, cli=vault_li, N=N, smin=5.0, occ=0.72, a=0.96)

        for zface, nz in ((zv - 3.65, -1.0), (zv + 3.65, 1.0)):
            ar = np.linspace(0.05, math.pi - 0.05, 22)
            ax = ac - (half_span + 0.55) * np.cos(ar)
            ay = arch_spring + (arch_crown - arch_spring + 0.55) * np.sin(ar)
            Pa = np.column_stack([ax, ay, np.full_like(ax, zface)])
            Da = np.column_stack([np.cos(ar), np.sin(ar), np.zeros_like(ax)])
            sb.add(Pa, D=Da, L=1.45, W=0.82, spr=DASH + 1, csh=C(98, 92, 118), cli=C(238, 218, 184), N=(0, 0.2, nz), smin=4.8, a=0.96)

            n_sp = 260
            sx = rng.uniform(ac - 10.5, ac + 10.5, n_sp)
            sy = rng.uniform(arch_spring, deck_y, n_sp)
            dx = np.abs(sx - ac) / half_span
            ymin = np.where(dx < 1.0, arch_spring + (arch_crown - arch_spring) * np.sqrt(np.maximum(0.0, 1.0 - dx * dx)), arch_spring)
            keep = sy >= ymin + 0.2
            if keep.any():
                Psp = np.column_stack([sx[keep], sy[keep], np.full(keep.sum(), zface)])
                rnd = rng.random((len(Psp), 3)).astype(np.float32)
                sb.add(
                    Psp, D=(1.0, 0.0, 0.0), L=rng.uniform(1.8, 3.0, len(Psp)), W=rng.uniform(0.75, 1.25, len(Psp)),
                    spr=DASH + rng.integers(0, 8, len(Psp)),
                    csh=jitter(np.tile(stone_sh, (len(Psp), 1)), rnd, 0.08, 0.03),
                    cli=jitter(np.tile(stone_li, (len(Psp), 1)), rnd, 0.08, 0.03),
                    N=(0, 0.15, nz), smin=5.0, a=0.95,
                )

    xs_deck = np.linspace(cx - 115.0, cx + 115.0, 175)
    for zface, nz in ((zv - 3.8, -1.0), (zv + 3.8, 1.0)):
        P = np.column_stack([xs_deck, np.full_like(xs_deck, deck_y + 0.52), np.full_like(xs_deck, zface)])
        sb.add(P, D=(1, 0, 0), L=1.9, W=0.68, spr=DASH, csh=C(138, 128, 144), cli=C(244, 224, 190), N=(0, 0.5, nz), smin=5.0)
        xp = xs_deck[::4]
        Pp = np.column_stack([xp, np.full_like(xp, deck_y + 1.12), np.full_like(xp, zface)])
        sb.add(Pp, D=(0, 1, 0), L=0.82, W=0.14, spr=DASH + 3, csh=C(52, 58, 72), cli=C(92, 98, 114), N=(0, 0.3, nz), smin=4.5)

    for sign in (-1.0, 1.0):
        n_ab = 260
        ax = cx + sign * rng.uniform(53.0, 82.0, n_ab)
        ay = rng.uniform(0.5, deck_y, n_ab)
        yb = terrain_y(ax, np.full(n_ab, zv))
        keep = ay >= yb - 0.5
        if keep.any():
            for zface, nz in ((zv - 3.5, -1.0), (zv + 3.5, 1.0)):
                Pa = np.column_stack([ax[keep], ay[keep], np.full(keep.sum(), zface)])
                rnd = rng.random((len(Pa), 3)).astype(np.float32)
                sb.add(
                    Pa, D=(1, 0, 0), L=rng.uniform(2.0, 3.4, len(Pa)), W=rng.uniform(0.9, 1.4, len(Pa)),
                    spr=DASH + rng.integers(0, 8, len(Pa)),
                    csh=jitter(np.tile(stone_sh, (len(Pa), 1)), rnd, 0.08, 0.03),
                    cli=jitter(np.tile(stone_li, (len(Pa), 1)), rnd, 0.08, 0.03),
                    N=(0, 0.2, nz), smin=5.5, a=0.94,
                )

    return sb.group(reflect=True, passid=STAND, name="viaduct", span=(-1e9, 1e9))


def _build_countryside_trees_and_hedges(rng):
    """Dense multi-layer tree groves, orchard rows, stone walls, hedgerows, and full horizon forest."""
    sb_stand = SB(rng)
    sb_willow_over = SB(rng)

    bark_sh = C(68, 54, 62)
    bark_li = C(132, 108, 86)

    # 1. Act I Poppy Hill: Umbrella pines, orchard trees, hedgerows & stone paddock walls (kept uphill of boy's sprint!)
    pine_coords = [
        (-86, 20, 1.15), (-96, 56, 1.32), (-88, 92, 1.12),
        (-94, 124, 1.28), (-78, 154, 1.15), (-106, 14, 1.24),
        (-112, 46, 1.35), (-110, 86, 1.25), (-114, 134, 1.40),
    ]
    for ox, oz, sc in pine_coords:
        x = float(river_x(oz)) + ox
        y0 = float(terrain_y(x, oz))
        h = 11.2 * sc
        _add_trunk(sb_stand, rng, x, y0, oz, h, 0.68 * sc, bark_sh, bark_li, lean_x=0.7)
        _add_canopy_cluster(sb_stand, rng, x + 0.7, y0 + h * 0.92, oz, 6.2 * sc, 2.8 * sc, 5.8 * sc, 150, C(40, 78, 76), C(108, 154, 76), smin=6.0, L0=1.65, W0=0.95, flex=0.14)
        _add_canopy_cluster(sb_stand, rng, x + 2.2, y0 + h * 0.78, oz + 1.5, 4.2 * sc, 2.1 * sc, 4.0 * sc, 85, C(46, 84, 74), C(124, 168, 82), smin=6.0, L0=1.5, W0=0.88, flex=0.16)

    # Orchard rows & hawthorn hedgerows flanking left hillside farmstead (Z = 35..148)
    for oz in np.linspace(38.0, 142.0, 9):
        ox_base = float(river_x(oz) - river_hw(oz)) - rng.uniform(54.0, 68.0)
        y0 = float(terrain_y(ox_base, oz))
        _add_trunk(sb_stand, rng, ox_base, y0, oz, 4.0, 0.36, bark_sh, bark_li)
        _add_canopy_cluster(sb_stand, rng, ox_base, y0 + 4.4, oz, 3.2, 2.2, 3.2, 75, C(46, 88, 68), C(148, 186, 86), smin=5.5, L0=1.35, W0=0.82, flex=0.18)

    # Stone paddock walls & hawthorn hedgerows dividing hillside fields
    cx0 = float(river_x(55.0) - river_hw(55.0))
    _add_stone_wall_or_hedge(sb_stand, rng, cx0 - 46, 36.0, cx0 - 84, 52.0, is_hedge=False)
    _add_stone_wall_or_hedge(sb_stand, rng, cx0 - 48, 92.0, cx0 - 94, 108.0, is_hedge=True)
    _add_stone_wall_or_hedge(sb_stand, rng, cx0 - 78, 48.0, cx0 - 82, 118.0, is_hedge=True)

    # 2. Double avenue of swaying Lombardy poplars & oaks along right bank towpath (Z = 45..335)
    for oz in np.linspace(48.0, 332.0, 18):
        x = float(river_x(oz) + river_hw(oz)) + rng.uniform(15.0, 22.0)
        y0 = float(terrain_y(x, oz))
        h = rng.uniform(14.5, 19.0)
        _add_trunk(sb_stand, rng, x, y0, oz, h * 0.82, 0.48, bark_sh, bark_li)
        _add_canopy_cluster(sb_stand, rng, x, y0 + h * 0.54, oz, 2.5, h * 0.46, 2.5, 165, C(52, 98, 76), C(150, 186, 74), smin=5.6, L0=1.50, W0=0.85, flex=0.24)
        if int(round(oz)) % 2 == 0:
            x2 = x + rng.uniform(14.0, 24.0)
            y2 = float(terrain_y(x2, oz))
            _add_trunk(sb_stand, rng, x2, y2, oz + 4.0, 7.5, 0.55, bark_sh, bark_li)
            _add_canopy_cluster(sb_stand, rng, x2, y2 + 8.0, oz + 4.0, 5.2, 3.6, 5.0, 110, C(44, 82, 72), C(124, 166, 78), smin=5.8, L0=1.75, W0=1.0, flex=0.14)

    # 3. Weeping willows overhanging the left bank cove (Z = 328 .. 395) + riverside alder grove
    for wz in [332.0, 352.0, 372.0, 390.0]:
        wx = float(river_x(wz) - river_hw(wz)) - 2.5
        wy = float(terrain_y(wx, wz))
        _add_trunk(sb_stand, rng, wx, wy, wz, 7.2, 0.85, bark_sh, bark_li, lean_x=2.2)
        _add_canopy_cluster(sb_stand, rng, wx + 2.8, wy + 7.6, wz, 6.4, 3.6, 5.8, 165, C(56, 102, 76), C(166, 196, 86), smin=5.8, L0=1.50, W0=0.84, flex=0.22)
        if wz < 382.0:
            for _ in range(34):
                ang = rng.uniform(-1.3, 1.3)
                rad = rng.uniform(1.8, 6.5)
                sx = wx + 3.0 + math.cos(ang) * rad
                sz = wz + math.sin(ang) * rad
                top_y = wy + rng.uniform(6.4, 8.8)
                bot_y = max(0.35, top_y - rng.uniform(4.2, 6.8))
                m = 9
                ys = np.linspace(top_y, bot_y, m)
                P = np.column_stack([np.full(m, sx) + (np.arange(m) * 0.08), ys, np.full(m, sz)])
                fl = np.linspace(0.06, 0.55, m)
                sb_willow_over.add(P, D=(0.08, -1.0, 0.04), L=1.25, W=0.24, spr=DASH + 4, csh=C(72, 118, 72), cli=C(196, 212, 96), N=(0.4, 0.8, 0.2), flex=fl, smin=4.5, a=0.88)

    # 4. Left-bank wooded riverbank behind sailboats & opposite twilight cove (Z = 240 .. 460)
    for oz in np.linspace(245.0, 465.0, 15):
        wx = float(river_x(oz) - river_hw(oz)) - rng.uniform(16.0, 44.0)
        wy = float(terrain_y(wx, oz))
        sc = rng.uniform(0.95, 1.45)
        _add_trunk(sb_stand, rng, wx, wy, oz, 8.0 * sc, 0.55 * sc, bark_sh, bark_li)
        _add_canopy_cluster(sb_stand, rng, wx, wy + 8.5 * sc, oz, 5.8 * sc, 4.0 * sc, 5.5 * sc, 105, C(46, 84, 74), C(128, 168, 78), smin=5.8, L0=1.85, W0=1.05, flex=0.14)

    # 5. BOLD Horizon Ridge Woodland Band & Skyline Crest Silhouettes across BOTH valley skylines
    for oz in np.linspace(-50.0, 520.0, 52):
        for side in (-1.0, 1.0):
            for layer in (0, 1, 2):
                dist_out = rng.uniform(58.0, 104.0) if layer == 0 else (rng.uniform(112.0, 158.0) if layer == 1 else rng.uniform(168.0, 210.0))
                x = float(river_x(oz)) + side * (float(river_hw(oz)) + dist_out)
                y0 = float(terrain_y(x, oz))
                if rng.random() < 0.24:
                    _add_canopy_cluster(sb_stand, rng, x, y0 + 9.2, oz, 3.0, 8.8, 3.0, 44, C(32, 58, 66), C(72, 112, 76), smin=5.4, L0=3.0, W0=1.5, flex=0.10)
                else:
                    _add_canopy_cluster(sb_stand, rng, x, y0 + 6.0, oz, 11.5, 6.2, 10.5, 52, C(42, 76, 74), C(112, 148, 80), smin=5.4, L0=3.5, W0=2.1, flex=0.06)

    # 6. Lush riverbank reeds & waterlily shore cushions
    for oz in np.concatenate([np.linspace(15, 120, 26), np.linspace(315, 445, 34)]):
        rx = float(river_x(oz) - river_hw(oz)) + rng.uniform(-1.0, 1.6)
        for j in range(11):
            jx = rx + rng.uniform(-1.6, 1.6)
            jz = oz + rng.uniform(-2.0, 2.0)
            h = rng.uniform(1.1, 2.2)
            sb_stand.add([[jx, h * 0.5, jz]], D=(rng.uniform(-0.18, 0.18), 1.0, rng.uniform(-0.18, 0.18)), L=h, W=0.15, spr=DASH + (j % 6), csh=C(58, 102, 68), cli=C(166, 188, 82), N=(0.2, 0.95, 0.1), flex=0.28, smin=4.2)

    return (
        sb_stand.group(reflect=True, passid=STAND, name="countryside_trees"),
        sb_willow_over.group(reflect=False, passid=OVER, name="willow_curtain"),
    )


def _build_villages_and_guinguette(rng):
    """Hillside Normandy farmstead, Argenteuil riverside village + church steeple, and Guinguette cafe."""
    sb = SB(rng)
    lamps_sb = SB(rng)

    # 1. Act I Hillside Farmstead on left upper meadow (Z ~ 96..118, visible behind kite boy!)
    fx = float(river_x(104.0) - river_hw(104.0)) - 62.0
    _add_cottage(sb, None, rng, fx, 104.0, w=11.0, d=6.0, h=4.4, yaw=0.15, wall_sh=C(164, 152, 154), wall_li=C(244, 228, 206), roof_sh=C(126, 62, 54), roof_li=C(204, 104, 68), windows=False)
    _add_cottage(sb, None, rng, fx - 10.0, 114.0, w=8.0, d=5.0, h=3.6, yaw=0.35, wall_sh=C(156, 146, 150), wall_li=C(234, 222, 198), roof_sh=C(72, 74, 98), roof_li=C(138, 142, 168), windows=False)

    # 2. Argenteuil Riverside Village Houses & Stone Church Steeple (right bank Z = 250..465!)
    village_specs = [
        # (z, back_dist, w, d, h, yaw, wall_sh, wall_li, roof_sh, roof_li)
        (256.0, 26.0, 10.5, 6.2, 4.6, math.pi / 2 + 0.1, C(166, 150, 154), C(244, 226, 202), C(124, 58, 52), C(208, 98, 66)),
        (274.0, 30.0, 12.0, 6.5, 5.2, math.pi / 2 - 0.1, C(168, 134, 142), C(246, 214, 196), C(64, 68, 96), C(128, 138, 166)),
        (292.0, 40.0,  9.5, 5.8, 4.5, math.pi / 2 + 0.2, C(158, 154, 156), C(238, 232, 214), C(128, 64, 56), C(212, 106, 72)),
        (312.0, 32.0, 11.5, 6.2, 5.0, math.pi / 2,       C(172, 146, 134), C(248, 222, 186), C(62, 66, 94), C(124, 134, 164)),
        (344.0, 38.0, 10.0, 6.0, 4.8, math.pi / 2 - 0.15, C(164, 144, 148), C(242, 220, 204), C(122, 58, 52), C(204, 96, 66)),
        # Flanking village cottages around the Guinguette cafe (Z = 370..452) so cafe sits inside a living town!
        (376.0, 24.0, 11.0, 6.4, 5.0, math.pi / 2 + 0.08, C(166, 152, 148), C(244, 228, 202), C(126, 62, 54), C(210, 102, 68)),
        (384.0, 48.0, 13.0, 7.0, 5.6, math.pi / 2 - 0.05, C(162, 146, 152), C(238, 222, 204), C(64, 68, 96), C(128, 138, 166)),
        (428.0, 26.0, 11.5, 6.4, 5.0, math.pi / 2 - 0.10, C(170, 144, 138), C(246, 220, 194), C(122, 60, 52), C(206, 100, 68)),
        (438.0, 46.0, 12.5, 6.8, 5.4, math.pi / 2 + 0.12, C(158, 148, 154), C(236, 224, 206), C(64, 68, 96), C(128, 138, 166)),
        (454.0, 30.0, 10.0, 6.0, 4.6, math.pi / 2,        C(168, 142, 146), C(244, 218, 198), C(126, 62, 54), C(208, 102, 68)),
    ]
    for vz, back, vw, vd, vh, vyaw, wsh, wli, rsh, rli in village_specs:
        vx = float(river_x(vz) + river_hw(vz)) + back
        _add_cottage(sb, lamps_sb, rng, vx, vz, vw, vd, vh, vyaw, wsh, wli, rsh, rli, windows=True)

    # Village Stone Church & Slate Spire rising above the cottages on the slope (Z = 418, back = 68m)
    ch_z = 418.0
    ch_x = float(river_x(ch_z) + river_hw(ch_z)) + 66.0
    _add_cottage(sb, lamps_sb, rng, ch_x, ch_z, w=14.0, d=8.5, h=7.2, yaw=math.pi / 2, wall_sh=C(146, 138, 152), wall_li=C(234, 218, 192), roof_sh=C(62, 66, 94), roof_li=C(124, 134, 164), windows=True)
    ch_y = float(terrain_y(ch_x, ch_z))
    # Solid stone bell tower + pointed slate spire
    for ty in np.linspace(ch_y + 7.0, ch_y + 16.5, 11):
        for dx, dz in ((-1.3, 0.0), (1.3, 0.0), (0.0, -1.3), (0.0, 1.3), (0.0, 0.0)):
            sb.add([[ch_x + dx, ty, ch_z + dz]], D=(0, 1, 0), L=1.85, W=2.4, spr=DAB, csh=C(138, 130, 146), cli=C(228, 214, 188), N=(-0.6, 0.3, 0.2), smin=5.2, a=0.98)
    lamps_sb.add([[ch_x - 1.5, ch_y + 12.8, ch_z]], D=(0, 1, 0), L=1.4, W=0.8, spr=DAB, csh=C(255, 194, 88), cli=C(255, 224, 128), N=(-1, 0, 0), emis=0.8, smin=4.0)
    for sp_u in np.linspace(0.0, 1.0, 9):
        sy = ch_y + 16.5 + sp_u * 8.0
        sw = (1.0 - sp_u * 0.9) * 2.4
        sb.add([[ch_x, sy, ch_z]], D=(0, 1, 0), L=1.45, W=max(0.3, sw), spr=DASH, csh=C(54, 58, 88), cli=C(118, 128, 160), N=(-0.6, 0.6, 0.2), smin=5.0)

    # Stone quay garden walls & shoreline streetlamps from Z = 360..448
    for lz in np.linspace(364.0, 446.0, 9):
        lx = float(river_x(lz) + river_hw(lz)) + 3.0
        ly = float(terrain_y(lx, lz))
        sb.add([[lx, ly + 1.9, lz]], D=(0, 1, 0), L=3.8, W=0.22, spr=DASH, csh=C(42, 46, 56), cli=C(82, 88, 104), N=(-1, 0, 0), smin=4.2)
        lamps_sb.add([[lx - 0.15, ly + 3.9, lz]], D=(0, 1, 0), L=0.62, W=0.58, spr=LENS, csh=C(255, 198, 92), cli=C(255, 236, 148), N=(0, 1, 0), emis=1.0, smin=3.2)

    # 3. Hero Argenteuil Guinguette Cafe Pavilion at Z = 406
    zc = 406.0
    qx = float(river_x(zc) + river_hw(zc)) + 16.0
    qy = float(terrain_y(qx, zc))
    bx, bz = qx + 7.5, zc
    wall_sh = C(172, 134, 142)
    wall_li = C(248, 222, 198)
    roof_sh = C(62, 66, 94)
    roof_li = C(126, 136, 166)

    for xf in np.linspace(bx - 5.6, bx + 4.4, 14):
        for zf in np.linspace(bz - 8.2, bz + 8.2, 22):
            if abs(xf - (bx - 5.6)) < 0.8 or abs(zf - (bz - 8.2)) < 0.8 or abs(zf - (bz + 8.2)) < 0.8:
                for yf in np.linspace(qy + 0.3, qy + 6.5, 11):
                    c_sh = C(124, 118, 134) if yf < qy + 1.0 else wall_sh
                    c_li = C(212, 198, 174) if yf < qy + 1.0 else wall_li
                    nrm = (-1, 0.1, 0) if abs(xf - (bx - 5.6)) < 0.8 else (0, 0.1, -1 if zf < bz else 1)
                    drc = (0, 0, 1) if abs(xf - (bx - 5.6)) < 0.8 else (1, 0, 0)
                    sb.add([[xf + rng.uniform(-0.15, 0.15), yf + rng.uniform(-0.12, 0.12), zf + rng.uniform(-0.15, 0.15)]],
                           D=drc, L=1.65, W=1.18, spr=DAB + rng.integers(0, 4), csh=c_sh, cli=c_li, N=nrm, smin=5.0, a=0.98)

    for u in np.linspace(0.0, 1.0, 9):
        rx = bx - 6.1 + u * 5.2
        ry = qy + 6.7 + u * 2.9
        for zf in np.linspace(bz - 8.6, bz + 8.6, 24):
            sb.add([[rx, ry, zf]], D=(0, 0, 1), L=1.55, W=1.05, spr=DASH + 1, csh=roof_sh, cli=roof_li, N=(-0.7, 0.7, 0), smin=5.5, a=0.98)

    for wz in (bz - 5.2, bz - 1.8, bz + 1.8, bz + 5.2):
        for wy in (qy + 2.2, qy + 4.9):
            sb.add([[bx - 5.75, wy, wz]], D=(0, 1, 0), L=1.45, W=0.98, spr=DASH, csh=C(58, 66, 86), cli=C(92, 102, 128), N=(-1, 0, 0), smin=4.5)
            lamps_sb.add([[bx - 5.82, wy, wz]], D=(0, 1, 0), L=1.18, W=0.78, spr=DAB + 1, csh=C(255, 198, 96), cli=C(255, 228, 138), N=(-1, 0, 0), emis=1.0, smin=4.5)
            for dz in (-0.72, 0.72):
                sb.add([[bx - 5.78, wy, wz + dz]], D=(0, 1, 0), L=1.42, W=0.44, spr=DASH + 2, csh=C(46, 94, 82), cli=C(86, 148, 114), N=(-1, 0, 0), smin=4.5)

    for i, zf in enumerate(np.linspace(bz - 8.3, bz + 8.3, 28)):
        col_sh = C(168, 50, 48) if i % 2 == 0 else C(208, 198, 182)
        col_li = C(238, 74, 62) if i % 2 == 0 else C(254, 244, 224)
        for u in np.linspace(0.0, 1.0, 6):
            sb.add([[bx - 5.6 - u * 4.0, qy + 3.4 - u * 0.92, zf]], D=(1, -0.23, 0), L=1.25, W=0.78, spr=DASH, csh=col_sh, cli=col_li, N=(-0.2, 0.95, 0), smin=4.8, a=0.96)
    for vz in (bz - 7.8, bz - 2.6, bz + 2.6, bz + 7.8):
        sb.add([[bx - 9.5, qy + 1.25, vz]], D=(0, 1, 0), L=2.5, W=0.22, spr=DASH, csh=C(72, 54, 48), cli=C(138, 106, 82), N=(-1, 0, 0), smin=4.0)

    edge_x = float(river_x(zc) + river_hw(zc)) + 1.2
    for zf in np.linspace(zc - 22.0, zc + 22.0, 40):
        sb.add([[edge_x, qy + 0.88, zf]], D=(0, 0, 1), L=1.55, W=0.40, spr=DASH, csh=C(134, 128, 142), cli=C(238, 224, 196), N=(-0.4, 0.9, 0), smin=4.5)
        if int(round(zf)) % 3 == 0:
            sb.add([[edge_x, qy + 0.44, zf]], D=(0, 1, 0), L=0.92, W=0.35, spr=DAB, csh=C(124, 118, 132), cli=C(224, 210, 184), N=(-1, 0, 0), smin=4.5)

    pier_z = zc - 12.5
    for px in np.linspace(edge_x - 8.5, edge_x + 0.5, 12):
        sb.add([[px, 0.42, pier_z]], D=(0, 0, 1), L=2.3, W=0.88, spr=DASH + 1, csh=C(92, 74, 62), cli=C(176, 144, 108), N=(0, 1, 0), smin=4.5)

    for tz in (bz - 6.0, bz - 2.0, bz + 2.0, bz + 6.0):
        tx = bx - 7.8
        sb.add([[tx, qy + 0.88, tz]], D=(1, 0, 0), L=1.25, W=1.1, spr=DAB + 1, csh=C(196, 194, 212), cli=C(252, 246, 232), N=(0, 1, 0), smin=4.0)
        sb.add([[tx, qy + 0.42, tz]], D=(0, 1, 0), L=0.85, W=0.20, spr=DASH, csh=C(58, 56, 68), cli=C(94, 92, 108), N=(-1, 0, 0), smin=4.0)
        lamps_sb.add([[tx, qy + 1.05, tz]], D=(0, 1, 0), L=0.28, W=0.28, spr=LENS, csh=C(255, 204, 96), cli=C(255, 236, 148), N=(0, 1, 0), emis=1.0, smin=3.0)

    post_zs = [zc - 13.0, zc - 4.5, zc + 4.5, zc + 13.0]
    for pz in post_zs:
        sb.add([[edge_x, qy + 2.1, pz]], D=(0, 1, 0), L=3.6, W=0.24, spr=DASH, csh=C(46, 52, 62), cli=C(88, 94, 108), N=(-1, 0, 0), smin=4.5)
    for i in range(len(post_zs)):
        p0 = np.array([edge_x, qy + 3.7, post_zs[i]])
        p1 = np.array([bx - 9.4, qy + 3.2, post_zs[i] + (1.4 if i % 2 == 0 else -1.4)])
        for k in range(6):
            u = (k + 0.5) / 6.0
            cp = p0 * (1.0 - u) + p1 * u - np.array([0.0, 0.52 * math.sin(u * math.pi), 0.0])
            sb.add([cp], D=_norm3(p1 - p0), L=1.8, W=0.08, spr=DASH, csh=C(38, 36, 44), cli=C(68, 64, 72), N=(0, 1, 0), smin=2.5)
        for k in range(5):
            u = (k + 0.5) / 5.0
            lp = p0 * (1.0 - u) + p1 * u - np.array([0.0, 0.52 * math.sin(u * math.pi) + 0.14, 0.0])
            lamps_sb.add([lp], D=(0, 1, 0), L=0.56, W=0.52, spr=LENS + (k % 4), csh=C(255, 192, 86), cli=C(255, 232, 134), N=(0, 1, 0), emis=1.0, smin=3.2)

    for gz_t in (zc - 16.0, zc + 16.0, zc - 28.0, zc + 28.0):
        tx_t = bx + rng.uniform(1.0, 5.0)
        ty_t = float(terrain_y(tx_t, gz_t))
        _add_trunk(sb, rng, tx_t, ty_t, gz_t, 9.0, 0.65, C(68, 54, 62), C(132, 108, 86))
        _add_canopy_cluster(sb, rng, tx_t - 1.5, ty_t + 9.2, gz_t, 5.8, 3.6, 5.5, 125, C(48, 88, 68), C(136, 172, 78), smin=6.0, L0=1.55, W0=0.88, flex=0.14)

    return (
        sb.group(reflect=True, passid=STAND, name="village_guinguette"),
        lamps_sb.group(reflect=True, passid=STAND, name="guinguette_lamps"),
    )


def build_static_groups():
    rng = np.random.default_rng(303)
    viaduct = _build_viaduct(rng)
    trees, willow_over = _build_countryside_trees_and_hedges(rng)
    guinguette, lamps = _build_villages_and_guinguette(rng)
    return dict(
        viaduct=viaduct,
        trees=trees,
        willow_over=willow_over,
        guinguette=guinguette,
        lamps=lamps,
    )

"""Static 3D world architecture, trees, weeping willows, stone viaduct & Guinguette cafe."""
import math
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, LENS, WASH, C, mix, jitter
from anim.paint.world3 import SB, STAND, OVER
from scene_geom import river_x, river_hw, terrain_y


def _norm3(v):
    v = np.asarray(v, np.float64)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12)


def _add_canopy_cluster(sb, rng, cx, cy, cz, rx, ry, rz, n, csh, cli, smin=6.0, L0=1.35, W0=0.82, flex=0.14):
    u = rng.normal(0.0, 0.46, (n, 3))
    r = np.linalg.norm(u, axis=1, keepdims=True)
    scale = np.minimum(1.0, 0.85 / (r + 1e-6)) * (0.40 + 0.60 * rng.random((n, 1)))
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
        flex=flex * (0.4 + 0.8 * edge), smin=smin, a=0.94,
    )


def _add_trunk(sb, rng, x, y0, z, h, r_bot, csh, cli, lean_x=0.0):
    segs = 7
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
    sb.add(P, D=D, L=np.array(Ls), W=np.array(Ws), spr=DASH + 1, csh=csh, cli=cli, N=N, flex=0.02, smin=5.5)


def _build_viaduct(rng):
    """5-arch Stone Railway Viaduct at Z=215 with organic painterly ashlar masonry (no dot grids!)."""
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

    # 1. Cut-stone piers standing in the river (random staggered horizontal ashlar DASH strokes)
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

    # 2. Arch voussoirs, vaulted soffit, and organic stone spandrel faces
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

        # Voussoir arch ring facing front/back + random spandrel masonry
        for zface, nz in ((zv - 3.65, -1.0), (zv + 3.65, 1.0)):
            # Radial stone arch ring
            ar = np.linspace(0.05, math.pi - 0.05, 22)
            ax = ac - (half_span + 0.55) * np.cos(ar)
            ay = arch_spring + (arch_crown - arch_spring + 0.55) * np.sin(ar)
            Pa = np.column_stack([ax, ay, np.full_like(ax, zface)])
            Da = np.column_stack([np.cos(ar), np.sin(ar), np.zeros_like(ax)])
            sb.add(Pa, D=Da, L=1.45, W=0.82, spr=DASH + 1, csh=C(98, 92, 118), cli=C(238, 218, 184), N=(0, 0.2, nz), smin=4.8, a=0.96)

            # Scattered overlapping horizontal ashlar stones in spandrel
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

    # 3. Parapet cornice, iron handrail & modest sloped stone wing-walls into hills
    xs_deck = np.linspace(cx - 115.0, cx + 115.0, 175)
    for zface, nz in ((zv - 3.8, -1.0), (zv + 3.8, 1.0)):
        P = np.column_stack([xs_deck, np.full_like(xs_deck, deck_y + 0.52), np.full_like(xs_deck, zface)])
        sb.add(P, D=(1, 0, 0), L=1.9, W=0.68, spr=DASH, csh=C(138, 128, 144), cli=C(244, 224, 190), N=(0, 0.5, nz), smin=5.0)
        xp = xs_deck[::4]
        Pp = np.column_stack([xp, np.full_like(xp, deck_y + 1.12), np.full_like(xp, zface)])
        sb.add(Pp, D=(0, 1, 0), L=0.82, W=0.14, spr=DASH + 3, csh=C(52, 58, 72), cli=C(92, 98, 114), N=(0, 0.3, nz), smin=4.5)

    # Compact textured stone abutments only near banks (|x - cx| in 53..82), blending into hillside bushes
    for sign in (-1.0, 1.0):
        n_ab = 280
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


def _build_trees(rng):
    """Poppy hillside pines, Argenteuil poplars, and willow curtains along the Seine."""
    sb_stand = SB(rng)
    sb_willow_over = SB(rng)

    bark_sh = C(68, 54, 62)
    bark_li = C(132, 108, 86)

    # 1. Umbrella pines & lush bushes crowning the Act I Poppy Hill (left bank)
    pine_coords = [
        (-54, 24, 1.15), (-68, 58, 1.32), (-52, 94, 1.08),
        (-74, 122, 1.25), (-58, 152, 1.12), (-82, 16, 1.22),
    ]
    for ox, oz, sc in pine_coords:
        x = float(river_x(oz)) + ox
        y0 = float(terrain_y(x, oz))
        h = 11.2 * sc
        _add_trunk(sb_stand, rng, x, y0, oz, h, 0.70 * sc, bark_sh, bark_li, lean_x=0.8)
        _add_canopy_cluster(sb_stand, rng, x + 0.8, y0 + h * 0.92, oz, 6.2 * sc, 2.8 * sc, 5.8 * sc, 165, C(42, 82, 74), C(112, 156, 78), smin=6.5, L0=1.6, W0=0.92, flex=0.14)
        _add_canopy_cluster(sb_stand, rng, x + 2.2, y0 + h * 0.78, oz + 1.5, 4.2 * sc, 2.1 * sc, 4.0 * sc, 95, C(46, 88, 72), C(128, 170, 82), smin=6.5, L0=1.45, W0=0.85, flex=0.16)

    # 2. Lush swaying Lombardy poplars along the right bank towpath (stopping at Z=332 before cafe quay!)
    poplar_zs = [65, 92, 118, 146, 178, 248, 276, 304, 332]
    for oz in poplar_zs:
        x = float(river_x(oz) + river_hw(oz)) + rng.uniform(16.0, 22.0)
        y0 = float(terrain_y(x, oz))
        h = rng.uniform(14.5, 18.5)
        _add_trunk(sb_stand, rng, x, y0, oz, h * 0.82, 0.50, bark_sh, bark_li)
        _add_canopy_cluster(
            sb_stand, rng, x, y0 + h * 0.54, oz, 2.5, h * 0.46, 2.5, 175,
            C(54, 102, 74), C(152, 188, 74), smin=5.8, L0=1.45, W0=0.82, flex=0.24,
        )

    # 3. Weeping willows overhanging the left bank cove (Z = 335 .. 388)
    willow_zs = [338.0, 358.0, 378.0]
    for wz in willow_zs:
        wx = float(river_x(wz) - river_hw(wz)) - 2.5
        wy = float(terrain_y(wx, wz))
        _add_trunk(sb_stand, rng, wx, wy, wz, 7.2, 0.85, bark_sh, bark_li, lean_x=2.2)
        _add_canopy_cluster(
            sb_stand, rng, wx + 2.8, wy + 7.6, wz, 6.4, 3.6, 5.8, 170,
            C(58, 106, 76), C(168, 198, 86), smin=6.0, L0=1.45, W0=0.80, flex=0.22,
        )
        for s in range(36):
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
            sb_willow_over.add(
                P, D=(0.08, -1.0, 0.04), L=1.25, W=0.24, spr=DASH + 4,
                csh=C(72, 118, 72), cli=C(196, 212, 96), N=(0.4, 0.8, 0.2),
                flex=fl, smin=4.5, a=0.88,
            )

    return (
        sb_stand.group(reflect=True, passid=STAND, name="trees"),
        sb_willow_over.group(reflect=False, passid=OVER, name="willow_curtain"),
    )


def _build_guinguette(rng):
    """Solid Argenteuil Guinguette riverside cafe, stone plinth, warm shuttered windows & festoon garlands."""
    sb = SB(rng)
    lamps_sb = SB(rng)

    zc = 406.0
    qx = float(river_x(zc) + river_hw(zc)) + 16.0
    qy = float(terrain_y(qx, zc))
    bx, bz = qx + 7.5, zc

    wall_sh = C(172, 134, 142)
    wall_li = C(248, 222, 198)
    roof_sh = C(62, 66, 94)
    roof_li = C(126, 136, 166)

    # 1. Solid stone foundation + dense plaster facade & side walls (zero transparency gaps!)
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

    # Solid mansard roof
    for u in np.linspace(0.0, 1.0, 9):
        rx = bx - 6.1 + u * 5.2
        ry = qy + 6.7 + u * 2.9
        for zf in np.linspace(bz - 8.6, bz + 8.6, 24):
            sb.add([[rx, ry, zf]], D=(0, 0, 1), L=1.55, W=1.05, spr=DASH + 1, csh=roof_sh, cli=roof_li, N=(-0.7, 0.7, 0), smin=5.5, a=0.98)

    # Shuttered rectangular windows & warm interior light
    for wz in (bz - 5.2, bz - 1.8, bz + 1.8, bz + 5.2):
        for wy in (qy + 2.2, qy + 4.9):
            # Dark window frame + warm lit glass pane
            sb.add([[bx - 5.75, wy, wz]], D=(0, 1, 0), L=1.45, W=0.98, spr=DASH, csh=C(58, 66, 86), cli=C(92, 102, 128), N=(-1, 0, 0), smin=4.5)
            lamps_sb.add([[bx - 5.82, wy, wz]], D=(0, 1, 0), L=1.18, W=0.78, spr=DAB + 1, csh=C(255, 198, 96), cli=C(255, 228, 138), N=(-1, 0, 0), emis=1.0, smin=4.5)
            for dz in (-0.72, 0.72):
                sb.add([[bx - 5.78, wy, wz + dz]], D=(0, 1, 0), L=1.42, W=0.44, spr=DASH + 2, csh=C(46, 94, 82), cli=C(86, 148, 114), N=(-1, 0, 0), smin=4.5)

    # Red-and-cream striped terrace awning + wooden veranda posts
    for i, zf in enumerate(np.linspace(bz - 8.3, bz + 8.3, 28)):
        col_sh = C(168, 50, 48) if i % 2 == 0 else C(208, 198, 182)
        col_li = C(238, 74, 62) if i % 2 == 0 else C(254, 244, 224)
        for u in np.linspace(0.0, 1.0, 6):
            sb.add([[bx - 5.6 - u * 4.0, qy + 3.4 - u * 0.92, zf]], D=(1, -0.23, 0), L=1.25, W=0.78, spr=DASH, csh=col_sh, cli=col_li, N=(-0.2, 0.95, 0), smin=4.8, a=0.96)
    for vz in (bz - 7.8, bz - 2.6, bz + 2.6, bz + 7.8):
        sb.add([[bx - 9.5, qy + 1.25, vz]], D=(0, 1, 0), L=2.5, W=0.22, spr=DASH, csh=C(72, 54, 48), cli=C(138, 106, 82), N=(-1, 0, 0), smin=4.0)

    # Waterfront stone balustrade & wooden jetty dock
    edge_x = float(river_x(zc) + river_hw(zc)) + 1.2
    for zf in np.linspace(zc - 18.0, zc + 18.0, 34):
        sb.add([[edge_x, qy + 0.88, zf]], D=(0, 0, 1), L=1.55, W=0.40, spr=DASH, csh=C(134, 128, 142), cli=C(238, 224, 196), N=(-0.4, 0.9, 0), smin=4.5)
        if int(round(zf)) % 3 == 0:
            sb.add([[edge_x, qy + 0.44, zf]], D=(0, 1, 0), L=0.92, W=0.35, spr=DAB, csh=C(124, 118, 132), cli=C(224, 210, 184), N=(-1, 0, 0), smin=4.5)

    pier_z = zc - 12.5
    for px in np.linspace(edge_x - 8.5, edge_x + 0.5, 12):
        sb.add([[px, 0.42, pier_z]], D=(0, 0, 1), L=2.3, W=0.88, spr=DASH + 1, csh=C(92, 74, 62), cli=C(176, 144, 108), N=(0, 1, 0), smin=4.5)

    # Bistro tables + glowing tabletop candles
    for tz in (bz - 6.0, bz - 2.0, bz + 2.0, bz + 6.0):
        tx = bx - 7.8
        sb.add([[tx, qy + 0.88, tz]], D=(1, 0, 0), L=1.25, W=1.1, spr=DAB + 1, csh=C(196, 194, 212), cli=C(252, 246, 232), N=(0, 1, 0), smin=4.0)
        sb.add([[tx, qy + 0.42, tz]], D=(0, 1, 0), L=0.85, W=0.20, spr=DASH, csh=C(58, 56, 68), cli=C(94, 92, 108), N=(-1, 0, 0), smin=4.0)
        lamps_sb.add([[tx, qy + 1.05, tz]], D=(0, 1, 0), L=0.28, W=0.28, spr=LENS, csh=C(255, 204, 96), cli=C(255, 236, 148), N=(0, 1, 0), emis=1.0, smin=3.0)

    # Garland poles + visible dark festoon cords + glowing amber lanterns
    post_zs = [zc - 13.0, zc - 4.5, zc + 4.5, zc + 13.0]
    for pz in post_zs:
        sb.add([[edge_x, qy + 2.1, pz]], D=(0, 1, 0), L=3.6, W=0.24, spr=DASH, csh=C(46, 52, 62), cli=C(88, 94, 108), N=(-1, 0, 0), smin=4.5)
    for i in range(len(post_zs)):
        p0 = np.array([edge_x, qy + 3.7, post_zs[i]])
        p1 = np.array([bx - 9.4, qy + 3.2, post_zs[i] + (1.4 if i % 2 == 0 else -1.4)])
        # Visible dark garland cord between pole & awning
        for k in range(6):
            u = (k + 0.5) / 6.0
            cp = p0 * (1.0 - u) + p1 * u - np.array([0.0, 0.52 * math.sin(u * math.pi), 0.0])
            sb.add([cp], D=_norm3(p1 - p0), L=1.8, W=0.08, spr=DASH, csh=C(38, 36, 44), cli=C(68, 64, 72), N=(0, 1, 0), smin=2.5)
        for k in range(5):
            u = (k + 0.5) / 5.0
            lp = p0 * (1.0 - u) + p1 * u - np.array([0.0, 0.52 * math.sin(u * math.pi) + 0.14, 0.0])
            lamps_sb.add([lp], D=(0, 1, 0), L=0.56, W=0.52, spr=LENS + (k % 4), csh=C(255, 192, 86), cli=C(255, 232, 134), N=(0, 1, 0), emis=1.0, smin=3.2)

    # Lush warm oak trees flanking the Guinguette behind it (frame the building beautifully!)
    for gz_t in (zc - 16.0, zc + 16.0):
        tx_t = bx + 2.0
        ty_t = float(terrain_y(tx_t, gz_t))
        _add_trunk(sb, rng, tx_t, ty_t, gz_t, 9.0, 0.65, C(68, 54, 62), C(132, 108, 86))
        _add_canopy_cluster(sb, rng, tx_t - 1.5, ty_t + 9.2, gz_t, 5.8, 3.6, 5.5, 130, C(48, 88, 68), C(136, 172, 78), smin=6.0, L0=1.5, W0=0.85, flex=0.14)

    return (
        sb.group(reflect=True, passid=STAND, name="guinguette"),
        lamps_sb.group(reflect=True, passid=STAND, name="guinguette_lamps"),
    )


def _build_far_hills_and_reeds(rng):
    """Distant textured hillside copses + shore reed beds for deep valley framing."""
    sb = SB(rng)
    for oz in np.linspace(-40.0, 500.0, 26):
        for side in (-1.0, 1.0):
            dist_out = rng.uniform(78.0, 138.0)
            x = float(river_x(oz)) + side * (float(river_hw(oz)) + dist_out)
            y0 = float(terrain_y(x, oz))
            _add_canopy_cluster(
                sb, rng, x, y0 + 4.5, oz, 12.0, 5.5, 10.0, 38,
                C(54, 92, 82), C(124, 158, 86), smin=8.0, L0=2.8, W0=1.6, flex=0.06,
            )

    for oz in np.concatenate([np.linspace(15, 115, 24), np.linspace(315, 425, 28)]):
        rx = float(river_x(oz) - river_hw(oz)) + rng.uniform(-1.2, 1.5)
        for j in range(10):
            jx = rx + rng.uniform(-1.6, 1.6)
            jz = oz + rng.uniform(-2.0, 2.0)
            h = rng.uniform(1.1, 2.1)
            sb.add(
                [[jx, h * 0.5, jz]], D=(rng.uniform(-0.18, 0.18), 1.0, rng.uniform(-0.18, 0.18)),
                L=h, W=0.15, spr=DASH + (j % 6),
                csh=C(58, 102, 68), cli=C(166, 188, 82), N=(0.2, 0.95, 0.1),
                flex=0.28, smin=4.2,
            )
    return sb.group(reflect=True, passid=STAND, name="hills_and_reeds")


def build_static_groups():
    rng = np.random.default_rng(303)
    viaduct = _build_viaduct(rng)
    trees, willow_over = _build_trees(rng)
    guinguette, lamps = _build_guinguette(rng)
    hills_reeds = _build_far_hills_and_reeds(rng)
    return dict(
        viaduct=viaduct,
        trees=trees,
        willow_over=willow_over,
        guinguette=guinguette,
        lamps=lamps,
        hills_reeds=hills_reeds,
    )

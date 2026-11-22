"""Shared 3D Impressionist props, trees, cottages, blossoms, lanterns & dream particles for v4."""
import math
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, LENS, WASH, C, jitter, mix, smooth
from anim.paint.world3 import OVER, STAND, _PASS, shade


def norm3(v):
    v = np.asarray(v, np.float64)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12)


def add_canopy(sb, rng, cx, cy, cz, rx, ry, rz, n, csh, cli, smin=5.6, L0=1.45, W0=0.88, flex=0.14):
    u = rng.normal(0.0, 0.46, (n, 3))
    r = np.linalg.norm(u, axis=1, keepdims=True)
    scale = np.minimum(1.0, 0.86 / (r + 1e-6)) * (0.40 + 0.60 * rng.random((n, 1)))
    u = u * scale
    P = np.column_stack([cx + u[:, 0] * rx, cy + u[:, 1] * ry, cz + u[:, 2] * rz])
    N = norm3(np.column_stack([u[:, 0] / max(rx, 0.1), (u[:, 1] + 0.38) / max(ry, 0.1), u[:, 2] / max(rz, 0.1)]))
    D = norm3(np.column_stack([-u[:, 2] + rng.normal(0, 0.3, n), 0.35 + rng.normal(0, 0.35, n), u[:, 0] + rng.normal(0, 0.3, n)]))
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


def add_trunk(sb, rng, x, y0, z, h, r_bot, csh, cli, lean_x=0.0):
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
    D = norm3(dirs)
    N = norm3(np.column_stack([P[:, 0] - x, np.full(len(P), 0.25), P[:, 2] - z]))
    sb.add(P, D=D, L=np.array(Ls), W=np.array(Ws), spr=DASH + 1, csh=csh, cli=cli, N=N, flex=0.02, smin=5.2)


def add_cottage(sb, lamps_sb, rng, x, y0, z, w, d, h, yaw, wall_sh, wall_li, roof_sh, roof_li, windows=True):
    ax = np.array([math.cos(yaw), 0.0, math.sin(yaw)], np.float64)
    az = np.array([-math.sin(yaw), 0.0, math.cos(yaw)], np.float64)
    up = np.array([0.0, 1.0, 0.0], np.float64)
    origin = np.array([x, y0 - 0.2, z], np.float64)

    nw = max(6, int(round(w / 0.68)))
    nd = max(5, int(round(d / 0.68)))
    nh = max(4, int(round(h / 0.62)))

    for u in np.linspace(-0.5, 0.5, nw):
        for v in np.linspace(0.06, 0.96, nh):
            for sgn in (-1.0, 1.0):
                p = origin + ax * (u * w) + az * (sgn * d * 0.5) + up * (v * h)
                sb.add([p], D=ax, L=1.65, W=1.35, spr=DASH + rng.integers(0, 4), csh=wall_sh, cli=wall_li, N=az * sgn + up * 0.1, smin=5.0, a=0.99)
    for w_u in np.linspace(-0.5, 0.5, nd):
        for v in np.linspace(0.06, 0.96, nh):
            for sgn in (-1.0, 1.0):
                p = origin + ax * (sgn * w * 0.5) + az * (w_u * d) + up * (v * h)
                sb.add([p], D=az, L=1.65, W=1.35, spr=DASH + rng.integers(0, 4), csh=wall_sh, cli=wall_li, N=ax * sgn + up * 0.1, smin=5.0, a=0.99)

    rh = max(1.8, d * 0.42)
    nr = max(5, int(round(d * 0.5 / 0.55)))
    for r_i in np.linspace(0.0, 1.0, nr):
        ry = h + r_i * rh
        z_off = (1.0 - r_i) * d * 0.54
        for u in np.linspace(-0.52, 0.52, nw + 2):
            for sgn in (-1.0, 1.0):
                p = origin + ax * (u * w) + az * (sgn * z_off) + up * ry
                sb.add([p], D=ax, L=1.75, W=1.22, spr=DASH + 1, csh=roof_sh, cli=roof_li, N=norm3(az * sgn * 0.7 + up * 0.7), smin=5.2, a=0.99)

    cp = origin + ax * (w * 0.28) + up * (h + rh + 0.4)
    sb.add([cp], D=up, L=1.4, W=0.65, spr=DASH, csh=wall_sh * 0.85, cli=wall_li * 0.9, N=(0.5, 0.7, 0.3), smin=4.5)

    if windows and lamps_sb is not None:
        nwin = max(2, int(round(w / 3.2)))
        for k in range(nwin):
            wu = -0.35 + 0.70 * (k / max(1, nwin - 1))
            for wy in (h * 0.36, h * 0.74) if h > 4.4 else (h * 0.52,):
                wp = origin + ax * (wu * w) - az * (d * 0.5 + 0.12) + up * wy
                sb.add([wp], D=up, L=0.95, W=0.65, spr=DASH, csh=C(54, 62, 82), cli=C(88, 96, 122), N=-az, smin=4.5)
                lamps_sb.add([wp - az * 0.05], D=up, L=0.78, W=0.52, spr=DAB, csh=C(255, 194, 88), cli=C(255, 224, 128), N=-az, emis=1.0, smin=4.0)


def emit_sunbeams(env, origins, dir_vec, col, alpha=0.14):
    """Emit translucent slanting golden-dream sunbeams in screen space."""
    beams = []
    dir_n = norm3(dir_vec)
    for ox, oy, oz, width, length in origins:
        for u in np.linspace(0.1, 0.95, 7):
            p = np.array([ox, oy, oz], np.float64) + dir_n * (u * length)
            beams.append((p[0], p[1], p[2], width * (0.7 + 0.6 * u), length * 0.26))
    P = np.array([b[:3] for b in beams], np.float64)
    v = P - env.C
    vr, vu, vf = v @ env.rt, v @ env.up, v @ env.fw
    ok = vf > 0.6
    if not ok.any():
        return None
    idx = np.nonzero(ok)[0]
    sc = env.f / vf[idx]
    x = 960.0 + vr[idx] * sc
    y = 540.0 - vu[idx] * sc
    Dr, Du, Df = dir_n @ env.rt, dir_n @ env.up, dir_n @ env.fw
    ang = np.arctan2(-(Du * vf[idx] - vu[idx] * Df), Dr * vf[idx] - vr[idx] * Df)
    wb = np.array([beams[i][3] for i in idx]) * sc
    lb = np.array([beams[i][4] for i in idx]) * sc
    return dict(
        x=x.astype(np.float32), y=y.astype(np.float32),
        ang=ang.astype(np.float32), L=lb.astype(np.float32), W=wb.astype(np.float32),
        spr=np.full(len(idx), LENS, np.int32),
        rgb=np.tile(col, (len(idx), 1)).astype(np.float32),
        a=np.full(len(idx), alpha, np.float32),
        hb=np.full(len(idx), 0.5, np.float32),
        key=(OVER * _PASS + 2e5 - vf[idx]).astype(np.float64),
    )


def emit_drifting_petals(env, count, pal_sh, pal_li, scale=0.22, height_range=(0.5, 6.0)):
    t = env.t
    cam = env.C
    rng = np.random.default_rng(909)
    from anim.paint.world3 import SB
    sb = SB(rng)
    for i in range(count):
        ph = i * 2.17
        age = (t * 0.55 + i * 0.31) % 5.0
        px = cam[0] + math.sin(ph) * 14.0 + env.wdir[0] * age * 2.4 + math.sin(t * 2.0 + ph) * 0.7
        pz = cam[2] + 8.5 + math.cos(ph * 1.35) * 14.0 + env.wdir[2] * age * 2.4
        py = max(0.25, height_range[0] + (i % 7) * ((height_range[1] - height_range[0]) / 7.0) + math.sin(t * 1.5 + ph) * 0.55 - age * 0.1)
        csh = pal_sh[i % len(pal_sh)]
        cli = pal_li[i % len(pal_li)]
        sb.add([[px, py, pz]], D=(math.cos(t * 2 + ph), 0.35, math.sin(t * 2 + ph)), L=scale, W=scale * 0.65, spr=DAB, csh=csh, cli=cli, N=(0, 1, 0), a=0.78 * float(smooth(0.0, 0.5, age) * smooth(5.0, 4.0, age)), smin=1.3)
    g = sb.group(reflect=False, passid=OVER, name="petals")
    return shade(env, g.lod(env), mirror=False, sway=False) if g and g.visible(env) else None


def emit_fireflies(env, xs, zs, y_base=1.1, col=(1.1, 0.92, 0.44), amt=1.0):
    if amt < 0.05:
        return None
    t = env.t
    from anim.paint.world3 import SB
    sb = SB(np.random.default_rng(911))
    for i, (x, z) in enumerate(zip(xs, zs)):
        fx = x + math.sin(t * 0.9 + i * 1.3) * 2.5
        fz = z + math.cos(t * 0.8 + i * 1.7) * 2.5
        fy = y_base + (i % 5) * 0.65 + 0.55 * math.sin(t * 1.4 + i * 2.1)
        pulse = max(0.0, math.sin(t * (2.5 + (i % 4) * 0.6) + i * 1.8)) ** 2
        if pulse > 0.08:
            sb.add([[fx, fy, fz]], D=(1, 0, 0), L=0.36, W=0.36, spr=LENS, csh=np.array(col, np.float32), cli=np.array(col, np.float32) * 1.08, N=(0, 1, 0), emis=1.0, a=0.94 * amt * pulse, smin=1.6)
    g = sb.group(reflect=False, passid=OVER, name="fireflies")
    return shade(env, g.lod(env), mirror=False, sway=False) if g and g.visible(env) else None

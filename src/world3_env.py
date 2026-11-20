"""Endless 3D world-anchored Water, Patchwork Valley Turf & Swaying Poppy/Wildflower Fields."""
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, WASH, C, mix, smooth, jitter, noise
from anim.paint.world3 import WATER, GROUND, Field, cloud_shadow, haze_of
from scene_geom import bank_signed_dist, river_x, river_dx_dz, river_hw, terrain_y, terrain_normal
from sky3 import sky_dir_rgb


def _water_shader(env, X, Z, Rn, dist):
    sd = bank_signed_dist(X, Z)
    in_water = sd < 1.2
    if not in_water.any():
        return None

    L = env.L
    t = env.t
    n = len(X)
    g = env.wind(X, Z)

    vx = env.C[0] - X
    vy = max(env.C[1], 0.25)
    vz = env.C[2] - Z
    vlen = np.sqrt(vx * vx + vy * vy + vz * vz) + 1e-9
    ivx, ivy, ivz = vx / vlen, vy / vlen, vz / vlen

    rp = float(L.get("ripple", 1.0))
    wamp = (0.045 + 0.085 * g) * rp
    nx = wamp * (0.65 * np.sin(X * 0.85 + Z * 0.35 - t * 2.5) + 0.35 * np.cos(X * 2.1 - t * 3.4 + Rn[:, 2] * 6.28))
    nz = wamp * (0.65 * np.cos(Z * 0.75 - X * 0.25 + t * 2.1) + 0.35 * np.sin(Z * 1.9 + t * 3.1 + Rn[:, 3] * 6.28))
    ny = np.ones(n, np.float64)
    nlen = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / nlen, ny / nlen, nz / nlen

    dot_vn = ivx * nx + ivy * ny + ivz * nz
    rx = 2.0 * dot_vn * nx - ivx
    ry = np.maximum(2.0 * dot_vn * ny - ivy, 0.015)
    rz = 2.0 * dot_vn * nz - ivz
    sky_col = sky_dir_rgb(env, rx, ry, rz)

    fresnel = 0.20 + 0.74 * np.clip(1.0 - np.abs(ivy), 0.0, 1.0) ** 3.2
    deep = L["deep"][None, :] * (0.86 + 0.28 * Rn[:, 1])[:, None]
    rgb = deep * (1.0 - fresnel[:, None]) + sky_col * fresnel[:, None]

    S = env.sun
    spec = np.clip(rx * float(S[0]) + ry * float(S[1]) + rz * float(S[2]), 0.0, 1.0)
    glit = float(L.get("glitter", 0.7))
    spark = (spec ** 26.0) * (Rn[:, 4] > 0.56) * glit
    rgb = rgb + L["sun_col"][None, :] * (spark * 0.95)[:, None]

    # Warm dusk reflections near Guinguette quay & village waterfront (Z = 355..445)
    lamps = float(L.get("lamps", 0.0))
    if lamps > 0.02:
        ql = np.exp(-((Z - 404.0) / 48.0) ** 2) * np.exp(-((X - (river_x(Z) + river_hw(Z) - 10.0)) / 32.0) ** 2)
        shimmer = ql * (0.4 + 0.6 * np.sin(Z * 1.7 + t * 3.2 + Rn[:, 2] * 6.28) ** 2) * lamps
        rgb = rgb + np.array([[1.08, 0.64, 0.18]], np.float32) * (shimmer * 0.58)[:, None]

    shore = np.exp(-((sd + 0.7) / 1.1) ** 2) * (sd < 0.9)
    rgb = mix(rgb, L["light"][None, :] * np.array([0.85, 0.90, 0.86], np.float32), shore * 0.24)

    rgb[:, 0] += (Rn[:, 2] - 0.5) * 0.045
    rgb[:, 2] -= (Rn[:, 2] - 0.5) * 0.035

    hx = ((X - env.C[0]) * float(S[0]) + (-env.C[1]) * float(S[1]) + (Z - env.C[2]) * float(S[2])) / np.maximum(dist, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.92)

    a = np.where(in_water, 0.96 * (1.0 - 0.35 * smooth(-0.2, 1.2, sd)), 0.0).astype(np.float32)
    spr = np.where(spark > 0.22, DAB + (Rn[:, 5] * 4).astype(np.int32), DASH + (Rn[:, 5] * 8).astype(np.int32))
    D = np.stack([np.ones(n), np.zeros(n), np.zeros(n)], axis=1)
    kl = np.where(spark > 0.22, 0.55, 1.15 + 0.35 * Rn[:, 3])
    kw = np.where(spark > 0.22, 0.85, 0.80 + 0.25 * Rn[:, 4])

    return dict(rgb=np.clip(rgb, 0.0, 1.18).astype(np.float32), a=a, D=D, kl=kl, kw=kw, spr=spr)


def _turf_base_shader(env, X, Z, Rn, dist):
    """Rich Monet patchwork countryside floor (meadows, golden hayfields, vineyard furrows, stone quay & towpath)."""
    sd = bank_signed_dist(X, Z)
    on_land = sd > -0.8
    if not on_land.any():
        return None

    L = env.L
    n = len(X)
    y = terrain_y(X, Z)
    N = terrain_normal(X, Z)

    S = env.sun
    nd = N[:, 0] * float(S[0]) + N[:, 1] * float(S[1]) + N[:, 2] * float(S[2])
    lit = np.clip(0.50 + 0.62 * nd + (Rn[:, 1] - 0.5) * 0.28, 0.0, 1.0)
    lit = lit * lit * (3.0 - 2.0 * lit)

    csh_amt = float(L.get("cloudsh", 0.0))
    if csh_amt > 0.01:
        lit = lit * (1.0 - 0.56 * csh_amt * cloud_shadow(env, X, Z))

    cx_r = river_x(Z)
    left_bank = X < cx_r
    towpath = (~left_bank) & (sd > 3.2) & (sd < 14.8) & (Z > 20.0) & (Z < 362.0)
    quay = (~left_bank) & (sd > -0.2) & (sd < 34.0) & (Z >= 362.0) & (Z < 458.0)

    # Patchwork agricultural plots across the hillsides (so distant hills are richly divided!)
    plot_id = (np.floor((X + 18.0 * noise(X / 90.0, Z / 90.0, 0)) / 36.0) * 7 + np.floor(Z / 42.0) * 13).astype(np.int32) % 5
    furrow = 0.5 + 0.5 * np.sin((X * 0.35 + Z * 0.22) * 1.4)

    # 0: Emerald meadow, 1: Golden wheat/hayfield, 2: Sage-olive vineyard rows, 3: Warm clover pasture, 4: Wildflower/mustard strip
    sh_pal = np.array([
        [0.16, 0.34, 0.26],  # cool emerald shadow
        [0.42, 0.36, 0.24],  # ochre-lavender wheat shadow
        [0.18, 0.30, 0.28],  # sage vineyard shadow
        [0.20, 0.37, 0.24],  # clover shadow
        [0.36, 0.38, 0.22],  # mustard shadow
    ], np.float32)
    li_pal = np.array([
        [0.46, 0.66, 0.24],  # bright emerald-chartreuse
        [0.86, 0.74, 0.34],  # sunlit golden hay
        [0.52, 0.64, 0.30],  # sunlit vineyard green
        [0.58, 0.72, 0.30],  # warm meadow
        [0.82, 0.76, 0.28],  # warm yellow-ochre wildflowers
    ], np.float32)

    # Keep foreground poppy meadow (left_bank Z<175, sd<68) lush meadow green under poppies
    fg_poppy = left_bank & (Z < 175.0) & (sd < 68.0)
    pid = np.where(fg_poppy, 0, plot_id)
    g_sh = sh_pal[pid]
    g_li = li_pal[pid]
    # Add vineyard row striping on plot 2
    g_li = np.where((pid == 2)[:, None], g_li * (0.86 + 0.22 * furrow[:, None]), g_li)

    rgb_base = g_sh * (1.0 - lit[:, None]) + g_li * lit[:, None]

    # Subtle hillside woodland moss darkening along upper ridges
    wood_patch = smooth(0.45, 0.75, noise(X / 65.0, Z / 65.0, 2)) * smooth(12.0, 34.0, sd)
    rgb_base = mix(rgb_base, C(46, 74, 64), wood_patch * 0.32)

    path_col = C(142, 134, 128) * (1.0 - lit[:, None]) + C(222, 206, 174) * lit[:, None]
    quay_col = C(110, 110, 128) * (1.0 - lit[:, None]) + C(188, 174, 156) * lit[:, None]

    rgb = np.where(towpath[:, None], path_col, rgb_base)
    rgb = np.where(quay[:, None], quay_col, rgb)

    tint = L["shade"][None, :] * (1.0 - lit[:, None]) + L["light"][None, :] * lit[:, None]
    rgb = rgb * tint

    lamps = float(L.get("lamps", 0.0))
    if lamps > 0.02:
        qx = river_x(Z) + river_hw(Z) + 14.0
        lq = np.exp(-((X - qx) ** 2 + (Z - 404.0) ** 2) / 680.0) * lamps
        rgb = rgb + np.array([[1.02, 0.62, 0.18]], np.float32) * (lq * 0.55)[:, None]

    rgb = jitter(rgb, Rn[:, 2:5], val=0.05, chroma=0.03)
    hx = ((X - env.C[0]) * float(S[0]) + (y - env.C[1]) * float(S[1]) + (Z - env.C[2]) * float(S[2])) / np.maximum(dist, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.95)

    slope_dir = river_dx_dz(Z)
    D = np.stack([slope_dir, np.zeros(n), np.ones(n)], axis=1)
    D /= np.linalg.norm(D, axis=1, keepdims=True) + 1e-9
    spr = np.where(dist > 80.0, WASH + (Rn[:, 5] * 4).astype(np.int32), DAB + (Rn[:, 5] * 4).astype(np.int32))
    a = np.where(on_land, 0.98 * smooth(-0.8, 0.3, sd), 0.0).astype(np.float32)
    return dict(rgb=np.clip(rgb, 0.0, 1.18).astype(np.float32), a=a, y=y, D=D, kl=1.25, kw=1.18, spr=spr)


def _poppy_tufts_shader(env, X, Z, Rn, dist):
    """Crisp upright swaying grass blades, scarlet poppies, daisies & golden meadow wildflowers."""
    sd = bank_signed_dist(X, Z)
    cx_r = river_x(Z)
    left_bank = X < cx_r
    towpath = (~left_bank) & (sd > 3.2) & (sd < 14.8) & (Z > 20.0) & (Z < 362.0)
    quay = (~left_bank) & (sd > -0.2) & (sd < 34.0) & (Z >= 362.0) & (Z < 458.0)

    active = (sd > 0.3) & (~towpath) & (~quay) & (dist < 165.0)
    if not active.any():
        return None

    L = env.L
    t = env.t
    n = len(X)
    y = terrain_y(X, Z) + 0.12
    N = terrain_normal(X, Z)
    g = env.wind(X, Z)

    S = env.sun
    nd = N[:, 0] * float(S[0]) + N[:, 1] * float(S[1]) + N[:, 2] * float(S[2])
    lit = np.clip(0.52 + 0.60 * nd + (Rn[:, 1] - 0.5) * 0.30, 0.0, 1.0)
    lit = lit * lit * (3.0 - 2.0 * lit)
    csh_amt = float(L.get("cloudsh", 0.0))
    if csh_amt > 0.01:
        lit = lit * (1.0 - 0.56 * csh_amt * cloud_shadow(env, X, Z))

    poppy_zone = left_bank & (sd > 2.2) & (Z < 175.0) & (sd < 66.0)
    poppy_patch = poppy_zone & (Rn[:, 0] < 0.25) & (np.sin(X * 0.14 + Z * 0.09) + 0.45 * np.cos(X * 0.05 - Z * 0.11) > -0.24)
    daisy_patch = (~poppy_patch) & (sd > 2.0) & (Rn[:, 0] > 0.92)
    gold_flower = (~poppy_patch) & (~daisy_patch) & (~poppy_zone) & (Rn[:, 0] < 0.10)

    g_sh = mix(C(44, 88, 62), C(58, 106, 58), Rn[:, 2])
    g_li = mix(C(124, 174, 62), C(178, 194, 76), Rn[:, 3])
    rgb_grass = g_sh * (1.0 - lit[:, None]) + g_li * lit[:, None]

    pop_pal = np.array([
        [0.93, 0.15, 0.13],
        [0.98, 0.27, 0.15],
        [0.82, 0.10, 0.18],
        [0.98, 0.35, 0.18],
    ], np.float32)
    pop_col = pop_pal[(Rn[:, 4] * 4).astype(np.int32) % 4] * (0.72 + 0.40 * lit[:, None])
    daisy_col = np.array([0.98, 0.96, 0.84], np.float32)[None, :] * (0.76 + 0.34 * lit[:, None])
    gold_col = np.array([0.96, 0.80, 0.26], np.float32)[None, :] * (0.74 + 0.36 * lit[:, None])

    rgb = np.where(poppy_patch[:, None], pop_col, rgb_grass)
    rgb = np.where(daisy_patch[:, None], daisy_col, rgb)
    rgb = np.where(gold_flower[:, None], gold_col, rgb)
    tint = L["shade"][None, :] * (1.0 - lit[:, None]) + L["light"][None, :] * lit[:, None]
    rgb = jitter(rgb * tint, Rn[:, 2:5], val=0.04, chroma=0.03)

    hx = ((X - env.C[0]) * float(S[0]) + (y - env.C[1]) * float(S[1]) + (Z - env.C[2]) * float(S[2])) / np.maximum(dist, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.95)

    flw = poppy_patch | daisy_patch | gold_flower
    upright = np.where(flw, 0.65, 0.95)
    lean = (0.28 * g + 0.14 * np.sin(t * (2.6 + 1.8 * Rn[:, 1]) + Rn[:, 2] * 6.28) * (0.35 + g)).astype(np.float32)
    spr = np.where(flw, DAB + (Rn[:, 5] * 4).astype(np.int32), DASH + (Rn[:, 5] * 8).astype(np.int32))
    kl = np.where(flw, 0.65, 0.92)
    kw = np.where(flw, 1.15, 0.48)
    a = np.where(active, 0.88 * smooth(165.0, 110.0, dist), 0.0).astype(np.float32)

    return dict(
        rgb=np.clip(rgb, 0.0, 1.18).astype(np.float32),
        a=a, y=y, D=np.broadcast_to(np.array([0.0, 0.0, 1.0]), (n, 3)),
        kl=kl, kw=kw, spr=spr, upright=upright.astype(np.float32), lean=lean,
    )


def build_fields():
    water = Field(seed=101, S=15.0, shader=_water_shader, passid=WATER, c0=0.055, kmax=14, kl=2.5, kw=1.25, wmin=3.6, y0=0.0, maxdist=1600.0)
    turf = Field(seed=202, S=14.5, shader=_turf_base_shader, passid=GROUND, c0=0.06, kmax=14, kl=2.7, kw=2.0, wmin=4.2, y0=0.0, order=0.0, maxdist=1800.0, yfun=terrain_y)
    tufts = Field(seed=203, S=19.0, shader=_poppy_tufts_shader, passid=GROUND, c0=0.05, kmax=11, kl=1.85, kw=0.65, wmin=3.0, y0=0.0, order=1.5, maxdist=170.0, yfun=terrain_y)
    return water, turf, tufts

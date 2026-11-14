"""Sky, Drifting Clouds, Sun/Dusk Disc, and Stars across the 5 Hours of Light.

d = 0 : Etretat Normandy Dawn (pearl coral-gold horizon, misty slate-blue zenith)
d = 1 : Argenteuil Summer Midday (buttercream horizon, crisp cerulean-cobalt sky)
d = 2 : Giverny Afternoon (warm apricot mist, luminous cerulean-lavender sky)
d = 3 : Rouen Cathedral Golden Hour (amber-peach glow, dusty rose, violet-slate top)
d = 4 : Venice San Giorgio Dusk (crimson-tangerine horizon, magenta-indigo twilight + stars)
"""
import numpy as np
from engine import Batch, smooth, mix, noise, ramp, C, pal, pick, jitter, DASH, DAB, SCUM, GLOW
from world import Set, jgrid, rnd_fields, scene_of, window

PS = 0.095  # slow sky parallax factor

_STOPS = [
    # 0 Etretat Dawn
    [(0.00, (242, 188, 160)), (0.20, (226, 178, 186)), (0.48, (166, 172, 212)), (0.85, (112, 144, 186)), (1.0, (92, 126, 170))],
    # 1 Argenteuil Summer
    [(0.00, (244, 232, 206)), (0.18, (206, 228, 244)), (0.46, (124, 178, 230)), (0.85, (76, 134, 206)), (1.0, (58, 112, 188))],
    # 2 Giverny Afternoon
    [(0.00, (250, 224, 184)), (0.20, (224, 216, 206)), (0.50, (132, 182, 224)), (0.85, (88, 138, 204)), (1.0, (70, 116, 186))],
    # 3 Rouen Sunset
    [(0.00, (250, 182, 114)), (0.22, (238, 152, 136)), (0.52, (176, 122, 168)), (0.85, (94, 102, 168)), (1.0, (66, 76, 142))],
    # 4 Venice Dusk
    [(0.00, (246, 122, 70)), (0.18, (232, 86, 112)), (0.44, (154, 80, 148)), (0.78, (58, 62, 126)), (1.0, (34, 42, 96))],
]


def dawn_sun_pos(env):
    """Low Normandy morning sun rising slowly above the Etretat horizon."""
    sx = -220.0 + env.t * 4.5 - env.camX * 0.045
    sy = -95.0 - 2.2 * min(env.t, 20.0)
    return sx, sy


def venice_sun_pos(env):
    """Blazing low Venetian sun sinking toward San Giorgio lagoon horizon."""
    dt = max(0.0, env.t - 76.0)
    sx = 210.0 - dt * 6.0
    sy = -58.0 + dt * 2.1
    return sx, sy


def sky_rgb(rx, ly, wx, env, rnd=None):
    """Continuous multi-hour Monet sky color at screen-relative (rx, ly)."""
    d = np.clip(env.d, 0.0, 4.0)
    k0 = min(int(np.floor(d)), 3)
    f = d - k0
    h = np.clip(-ly / 560.0, 0.0, 1.0)
    c0 = ramp(_STOPS[k0], h)
    c1 = ramp(_STOPS[k0 + 1], h)
    col = mix(c0, c1, f)

    # Atmospheric brushstroke mottling (subtle broken hue shifts)
    m1 = noise(wx / 700.0 + 1.3, h * 2.2, 0)
    m2 = noise(wx / 320.0, h * 4.0 + 2.1, 1)
    warmth = (m1 - 0.5) * 0.09 + (m2 - 0.5) * 0.05
    col[:, 0] = np.clip(col[:, 0] + warmth * 0.8, 0.0, 1.0)
    col[:, 2] = np.clip(col[:, 2] - warmth * 0.6, 0.0, 1.0)

    # Dawn sun warmth in Etretat (d ~ 0)
    w0 = float(window(d, 0.0, 0.9))
    if w0 > 0.0:
        sx0, sy0 = dawn_sun_pos(env)
        dist = np.hypot(rx - sx0, ly - sy0)
        glow = np.exp(-(dist / 240.0) ** 2) * w0
        col = col + glow[:, None] * np.array([0.24, 0.13, 0.02], np.float32)

    # Venetian crimson-gold glow (d ~ 4)
    w4 = float(window(d, 4.0, 1.0))
    if w4 > 0.0:
        sx4, sy4 = venice_sun_pos(env)
        dist = np.hypot((rx - sx4) * 0.75, ly - sy4)
        glow = np.exp(-(dist / 320.0) ** 2) * w4
        col = col + glow[:, None] * np.array([0.30, 0.12, 0.04], np.float32)

    if rnd is not None:
        col = jitter(col, rnd, 0.045, 0.024)
    return np.clip(col, 0.0, 1.0)


def _sky_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    rx = sx - 960.0
    ly = (sy - env.hz) / env.zoom
    col = sky_rgb(rx, ly, rx + env.camX * PS, env, rnd)

    # Subtle curved painterly brushstroke angle across the vault
    h = np.clip(-ly / 560.0, 0.0, 1.0)
    ang = 0.09 * np.sin(rx * 0.0022 + h * 1.4) + (rnd[:, 0] - 0.5) * 0.24
    # Organic canvas reveal over first 2.2s
    rev = smooth(0.0, 0.65, env.t * 1.1 - 0.25 - 1.3 * rnd[:, 2] - 0.35 * (1.0 - h))
    a = 0.94 * rev
    L = g["L"] * sc * (0.72 + 0.28 * rev)
    W = g["W"] * sc
    return Batch(sx, sy, ang, L, W, g["spr"], col, a, 0.5 + 0.2 * rnd[:, 3], hb=0.45)


def _cloud_shader(env, X, Y, p, sx, sy, sc, g):
    rnd = g["rnd"]
    d = env.d
    t = env.t
    top = g["top"]  # 0 = shadowed underside, 1 = sunlit crest

    # Palette shifts across hours of light
    lit0 = C(255, 224, 198)
    shd0 = C(172, 166, 204)
    lit1 = C(255, 252, 244)
    shd1 = C(176, 196, 228)
    lit2 = C(255, 244, 222)
    shd2 = C(186, 186, 218)
    lit3 = C(255, 206, 152)
    shd3 = C(168, 128, 174)
    lit4 = C(255, 166, 118)
    shd4 = C(116, 76, 138)

    k = min(int(np.floor(np.clip(d, 0.0, 3.999))), 3)
    f = np.clip(d - k, 0.0, 1.0)
    lits = [lit0, lit1, lit2, lit3, lit4]
    shds = [shd0, shd1, shd2, shd3, shd4]
    lit = mix(lits[k], lits[k + 1], f)
    shd = mix(shds[k], shds[k + 1], f)

    col = mix(shd, lit, top)
    col = jitter(col, rnd, 0.05, 0.025)

    # Gentle drift with wind + subtle breathing puffs
    drift_x = sx + (t * (5.5 + 4.0 * rnd[:, 1]) % 320.0) * 0.15
    drift_y = sy + 2.5 * np.sin(t * 0.35 + rnd[:, 2] * 6.28)
    rev = smooth(0.0, 0.8, t - 0.6 - 1.1 * rnd[:, 0])
    ang = (rnd[:, 3] - 0.5) * 0.32
    a = g["a"] * rev
    return Batch(drift_x, drift_y, ang, g["L"] * sc, g["W"] * sc, g["spr"], col, a, 1.05 + 0.1 * top, hb=0.65)


def _celestial_actor(env):
    """Dawn sun (Etretat), glowing afternoon haze, crimson Venice sun & twilight stars."""
    batches = []
    t = env.t
    d = env.d

    # 1. Normandy Dawn Sun + broken halo rings (d ~ 0)
    w0 = float(window(d, 0.0, 0.85))
    if w0 > 0.01:
        sx0, sy0 = dawn_sun_pos(env)
        cx, cy = 960.0 + sx0 * env.zoom, env.hz + sy0 * env.zoom
        ang = np.linspace(0.0, 2.0 * np.pi, 14, endpoint=False, dtype=np.float32) + t * 0.05
        rr = 34.0 + 18.0 * np.sin(np.arange(14) * 2.1 + 0.5)
        hx = cx + np.cos(ang) * rr * env.zoom
        hy = cy + np.sin(ang) * rr * env.zoom
        halo_col = mix(C(255, 174, 102), C(255, 226, 174), (np.arange(14) % 2).astype(np.float32))
        batches.append(Batch(hx, hy, ang + 1.57 + 0.35 * np.cos(np.arange(14)), 44.0 * env.zoom, 20.0 * env.zoom, SCUM + (np.arange(14) % 6), halo_col, 0.28 * w0, 1.18, hb=0.70))
        # Sun core dabs
        core_ang = np.linspace(0.0, np.pi, 6, dtype=np.float32)
        batches.append(
            Batch(
                np.full(6, cx, np.float32) + np.cos(core_ang) * 6.0,
                np.full(6, cy, np.float32) + np.sin(core_ang) * 5.0,
                core_ang,
                42.0 * env.zoom,
                32.0 * env.zoom,
                np.full(6, DAB, np.int32),
                mix(C(255, 146, 68), C(255, 228, 160), np.linspace(0.0, 1.0, 6)),
                0.86 * w0,
                1.22,
                hb=0.95,
            )
        )

    # 2. Venice Crimson Sunset Disc & Glow (d ~ 4)
    w4 = float(window(d, 4.0, 0.9))
    if w4 > 0.01:
        sx4, sy4 = venice_sun_pos(env)
        cx, cy = 960.0 + sx4 * env.zoom, env.hz + sy4 * env.zoom
        batches.append(
            Batch(
                np.array([cx, cx - 8.0, cx + 10.0], np.float32),
                np.array([cy, cy + 4.0, cy - 3.0], np.float32),
                np.array([0.0, 0.3, -0.2], np.float32),
                np.array([150.0, 90.0, 75.0], np.float32) * env.zoom,
                np.array([110.0, 68.0, 56.0], np.float32) * env.zoom,
                np.array([GLOW, GLOW + 1, DAB], np.int32),
                np.array([C(255, 130, 72), C(255, 188, 108), C(255, 226, 158)], np.float32),
                np.array([0.38, 0.62, 0.88], np.float32) * w4,
                1.20,
                hb=0.80,
            )
        )

    # 3. Emerging Twilight Stars in Scene 5 (d > 3.3)
    ws = float(smooth(3.35, 3.95, d))
    if ws > 0.01:
        rng = np.random.default_rng(777)
        ns = 44
        sx_s = rng.uniform(60.0, 1860.0, ns).astype(np.float32)
        sy_s = rng.uniform(25.0, 310.0, ns).astype(np.float32)
        phase = rng.uniform(0.0, 6.28, ns).astype(np.float32)
        twinkle = 0.55 + 0.45 * np.sin(t * rng.uniform(1.5, 3.4, ns) + phase)
        sz = rng.uniform(5.0, 10.5, ns).astype(np.float32) * env.zoom
        star_col = mix(C(255, 240, 200), C(214, 232, 255), rng.random(ns).astype(np.float32))
        batches.append(Batch(sx_s, sy_s, phase, sz, sz, np.full(ns, GLOW + 2, np.int32), star_col, ws * 0.85 * twinkle, 1.25, hb=0.4))

    return batches


def build(rng):
    sets = []

    # 1. Sky vault grid (world-coupled via slow PS parallax so sky flows seamlessly across 96s)
    xs, ys = jgrid(rng, -1350.0, 3400.0, -760.0, 80.0, 28.0, jit=0.9)
    n = len(xs)
    rnd = rnd_fields(rng, n)
    L = rng.uniform(92.0, 148.0, n).astype(np.float32) / PS
    W = (L * rng.uniform(0.42, 0.58, n)).astype(np.float32)
    spr = np.where(rnd[:, 0] < 0.25, DAB + rng.integers(0, 6, n), DASH + rng.integers(0, 8, n)).astype(np.int32)
    sets.append(Set("sky_vault", _sky_shader, xs / PS, ys / PS, np.full(n, PS, np.float32), margin=260.0, rnd=rnd, L=L, W=W, spr=spr))

    # 2. Painterly drifting cloud banks across the entire 96s sky
    cx_list, cy_list, top_list, L_list, W_list, a_list, spr_list = [], [], [], [], [], [], []
    cloud_centers = [
        (-50, -390, 260, 48), (680, -340, 310, 56), (1380, -430, 280, 50),
        (2200, -360, 340, 60), (3050, -410, 260, 46), (3900, -350, 320, 54),
        (4850, -380, 290, 52), (5700, -430, 350, 62), (6550, -330, 250, 44),
        (7450, -390, 320, 58), (8350, -340, 280, 48), (9250, -410, 310, 56),
        (10200, -350, 270, 50), (11150, -400, 340, 58), (12100, -340, 260, 48),
        (13100, -390, 320, 55), (14100, -360, 290, 52), (15150, -410, 330, 58),
        (16200, -340, 270, 48), (17250, -380, 340, 60), (18300, -350, 290, 52),
        (19300, -390, 330, 56), (20250, -350, 280, 50),
    ]
    p_cld = 0.14
    for cx0, cy0, rx0, ry0 in cloud_centers:
        k = 72
        ang = rng.uniform(0.0, 2.0 * np.pi, k)
        rad = np.sqrt(rng.random(k))
        py = cy0 + np.sin(ang) * ry0 * rad
        top = np.clip(0.55 - np.sin(ang) * rad * 0.7 + rng.uniform(-0.15, 0.15, k), 0.0, 1.0)
        cx_list.append(cx0 + np.cos(ang) * (rx0 / p_cld) * rad)
        cy_list.append(py / p_cld)
        top_list.append(top)
        L_list.append(rng.uniform(48.0, 92.0, k) / p_cld)
        W_list.append(rng.uniform(22.0, 42.0, k) / p_cld)
        a_list.append(rng.uniform(0.32, 0.58, k))
        spr_list.append(np.where(rng.random(k) < 0.65, SCUM + rng.integers(0, 6, k), DAB + rng.integers(0, 6, k)))

    cX = np.concatenate(cx_list).astype(np.float32)
    cY = np.concatenate(cy_list).astype(np.float32)
    ctop = np.concatenate(top_list).astype(np.float32)
    cL = np.concatenate(L_list).astype(np.float32)
    cW = np.concatenate(W_list).astype(np.float32)
    ca = np.concatenate(a_list).astype(np.float32)
    cspr = np.concatenate(spr_list).astype(np.int32)
    crnd = rnd_fields(rng, len(cX))
    sets.append(Set("clouds", _cloud_shader, cX, cY, np.full(len(cX), p_cld, np.float32), margin=420.0, rnd=crnd, top=ctop, L=cL, W=cW, a=ca, spr=cspr))

    return sets, [_celestial_actor]

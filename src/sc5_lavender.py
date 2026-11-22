"""Scene 5 (80-100s): Provence Royal-Violet Lavender Waves, Cypresses & Turning Windmill."""
import math
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, LENS, C, jitter, mix, smooth
from anim.paint.world3 import Field, Path, SB, GROUND, STAND, OVER, shade, compose, haze_of
from sky3 import SkyDome
from common4 import norm3, add_canopy, add_trunk, add_cottage, emit_sunbeams, emit_fireflies, emit_drifting_petals


def terrain_y(x, z):
    """Smooth rising Provence lavender plateau along +Z (zero background bleed)."""
    x = np.asarray(x, np.float64)
    z = np.asarray(z, np.float64)
    rise = np.where(z > -15.0, 0.105 * (z + 15.0) + 5.2 * np.maximum(0.0, (z - 30.0) / (np.maximum(z - 30.0, 0.0) + 85.0)), 0.0)
    undul = 0.32 * np.sin(x * 0.055) * np.exp(-np.maximum(z, 0.0) * 0.01)
    return rise + undul


def camera_path():
    # Serene low-to-crest float over undulating rows of violet lavender toward the golden windmill & sunset
    return Path([
        (0.0,  -6.5, float(terrain_y(-6.5,  0.0)) + 2.35,  0.0,   1.5, float(terrain_y(1.5, 36.0)) + 4.8, 36.0, 52.0),
        (5.5,  -3.2, float(terrain_y(-3.2,  4.2)) + 2.50,  4.2,   2.8, float(terrain_y(2.8, 38.0)) + 5.1, 38.0, 50.0),
        (11.0,  0.2, float(terrain_y( 0.2,  8.5)) + 2.85,  8.5,   4.0, float(terrain_y(4.0, 40.0)) + 5.5, 40.0, 49.0),
        (16.0,  3.0, float(terrain_y( 3.0, 12.2)) + 3.25, 12.2,   5.2, float(terrain_y(5.2, 42.0)) + 6.0, 42.0, 48.0),
        (20.0,  4.8, float(terrain_y( 4.8, 14.5)) + 3.60, 14.5,   6.0, float(terrain_y(6.0, 44.0)) + 6.4, 44.0, 48.0),
    ], sigma=1.5)


def _row_phase(X, Z):
    # Slightly sweeping curved plantation rows converging gracefully into the sunset hill
    curve_x = X - 0.14 * Z + 1.8 * np.sin(Z * 0.06)
    return 0.5 + 0.5 * np.cos(curve_x * (2.0 * math.pi / 2.25))


def _soil_shader(env, X, Z, Rn, dist):
    n = len(X)
    y = terrain_y(X, Z)
    row = _row_phase(X, Z)
    furrow_col = np.column_stack([
        0.52 + 0.14 * Rn[:, 2],
        0.34 + 0.10 * Rn[:, 3],
        0.38 + 0.12 * Rn[:, 4],
    ])
    lav_base = mix(C(108, 44, 152), C(196, 86, 178), np.clip(row, 0.0, 1.0)[:, None])
    rgb = mix(furrow_col, lav_base, np.clip(row * 1.15, 0.0, 1.0)[:, None])

    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.88)
    return dict(
        y=y,
        D=np.column_stack([np.full(n, 0.25), np.zeros(n), np.full(n, 0.97)]),
        rgb=np.clip(rgb, 0.0, 1.2),
        spr=DAB + (Rn[:, 3] * 4).astype(np.int32) % 4,
        kl=np.full(n, 1.45), kw=np.full(n, 1.05),
        depth_order=np.zeros(n, np.float32),
    )


def _lavender_shader(env, X, Z, Rn, dist):
    n = len(X)
    row = _row_phase(X, Z)
    on_row = row > 0.36
    y = terrain_y(X, Z) + 0.34 + 0.18 * Rn[:, 3]

    # Sunset rim-lit lavender palette: deep royal violet core -> radiant orchid & rose-coral tips!
    sun_kiss = np.clip((Rn[:, 4] * 0.7 + 0.3 * np.sin(X * 0.15 + Z * 0.1)), 0.0, 1.0)
    deep_v = C(88, 36, 148)
    mid_v = C(148, 62, 198)
    rose_v = C(236, 114, 186)
    rgb = np.where((sun_kiss < 0.52)[:, None], mix(deep_v, mid_v, (sun_kiss * 1.9)[:, None]), mix(mid_v, rose_v, ((sun_kiss - 0.52) * 2.08)[:, None]))

    # Occasional warm golden wheat/marigold fringe along near edge
    rim_gold = (Z < 10.0) & (np.abs(X) > 7.5) & (Rn[:, 5] > 0.65)
    rgb[rim_gold] = C(248, 178, 56)

    sway = 0.28 * np.sin(env.t * 2.3 + X * 0.28 + Z * 0.18)
    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.86)
    return dict(
        y=y,
        rgb=np.clip(rgb, 0.0, 1.25),
        a=np.where(on_row, 0.94, 0.0).astype(np.float32),
        spr=DAB + (Rn[:, 3] * 4).astype(np.int32) % 4,
        upright=np.full(n, 0.88),
        lean=sway.astype(np.float32),
        kl=np.full(n, 1.15), kw=np.full(n, 0.62),
        depth_order=np.full(n, 0.04, np.float32),
    )


def _add_cypress(sb, rng, x, y0, z, h):
    """Lush flame-shaped Provençal Mediterranean cypress catching magenta-gold sunset light."""
    add_trunk(sb, rng, x, y0, z, h * 0.22, 0.35, C(58, 42, 46), C(102, 72, 68))
    for k in range(54):
        u = rng.uniform(0.12, 0.98)
        rad = (0.42 + 1.55 * math.sin(u * math.pi) ** 0.75) * (1.0 - 0.55 * u)
        ang = rng.uniform(0, 2 * math.pi)
        px = x + math.cos(ang) * rad * 0.72
        pz = z + math.sin(ang) * rad * 0.72
        py = y0 + u * h
        sb.add([[px, py, pz]], D=(0.06 * math.cos(ang), 1.0, 0.06 * math.sin(ang)),
               L=h * 0.18, W=max(0.65, rad * 1.45), spr=DASH + 2,
               csh=C(26, 46, 56), cli=C(92, 122, 86), N=(math.cos(ang) * 0.7, 0.4, math.sin(ang) * 0.7), flex=0.14, smin=3.4, a=0.99)


class Scene5Lavender:
    def __init__(self):
        self.sky = SkyDome(seed=55)
        self.soil_f = Field(501, 44.0, _soil_shader, GROUND, c0=0.45, kmax=20, kl=1.48, kw=1.18, wmin=4.2, maxdist=280.0, yfun=terrain_y)
        self.lav_f = Field(502, 24.0, _lavender_shader, GROUND, c0=0.30, kmax=18, kl=1.15, kw=0.72, wmin=2.8, maxdist=165.0, yfun=terrain_y)

        rng = np.random.default_rng(5005)
        sb = SB(rng)
        lamps = SB(rng)

        self.wx, self.wz = 8.2, 44.0
        self.wy = float(terrain_y(self.wx, self.wz))
        for k in range(11):
            u = k / 10.0
            rad = 2.45 * (1.0 - 0.25 * u)
            py = self.wy + k * 0.70
            for a in np.linspace(0, 2 * math.pi, 16, endpoint=False):
                nx, nz = math.cos(a), math.sin(a)
                sb.add([[self.wx + nx * rad, py, self.wz + nz * rad]], D=(0, 1, 0), L=1.45, W=1.65,
                       spr=DASH + (k % 4), csh=C(138, 108, 134), cli=C(246, 198, 152), N=(nx, 0.2, nz), smin=3.6, a=0.99)
        for r_u in np.linspace(0.0, 1.0, 6):
            r_c = 2.15 * (1.0 - r_u)
            py = self.wy + 7.2 + r_u * 2.4
            for a in np.linspace(0, 2 * math.pi, 14, endpoint=False):
                sb.add([[self.wx + math.cos(a) * r_c, py, self.wz + math.sin(a) * r_c]], D=(0, 1, 0), L=1.15, W=1.35,
                       spr=DASH + 1, csh=C(128, 52, 62), cli=C(228, 112, 78), N=(math.cos(a), 0.7, math.sin(a)), smin=3.2, a=0.99)
        lamps.add([[self.wx - 0.6, self.wy + 2.4, self.wz - 2.35]], D=(0, 1, 0), L=1.1, W=0.72,
                  spr=LENS, csh=C(255, 186, 72), cli=C(255, 228, 128), N=(0, 0, -1), emis=1.0, smin=2.6)

        add_cottage(sb, lamps, rng, -14.5, float(terrain_y(-14.5, 48.0)), 48.0, 10.5, 6.8, 4.8, 0.28,
                    C(152, 118, 136), C(248, 206, 162), C(138, 58, 58), C(228, 106, 74))

        for cx, cz, ch in [(-18.5, 42.0, 13.5), (-16.0, 44.5, 11.5), (-6.5, 52.0, 14.0),
                           (14.0, 46.0, 12.8), (18.5, 49.0, 14.5), (24.0, 54.0, 11.5),
                           (-26.0, 32.0, 12.0), (26.0, 36.0, 12.2)]:
            _add_cypress(sb, rng, cx, float(terrain_y(cx, cz)), cz, ch)

        for ox in np.linspace(-65.0, 65.0, 26):
            oz = 82.0 + rng.uniform(-8.0, 12.0)
            oy = float(terrain_y(ox, oz))
            add_canopy(sb, rng, ox, oy + 3.2, oz, 3.8, 2.4, 3.6, 28, C(78, 72, 114), C(168, 136, 148), smin=4.5, L0=1.6, W0=1.1)

        for _ in range(32):
            fx = -4.2 + rng.uniform(-2.6, 2.2)
            fz = 10.5 + rng.uniform(-2.5, 3.5)
            fy = float(terrain_y(fx, fz))
            h = rng.uniform(0.9, 1.45)
            sb.add([[fx, fy + h * 0.5, fz]], D=(0, 1, 0), L=h, W=0.09, spr=DASH, csh=C(48, 86, 44), cli=C(108, 148, 62), N=(0, 1, 0), flex=0.22, smin=1.8)
            sb.add([[fx, fy + h, fz]], D=(1, 0.2, 0), L=0.45, W=0.45, spr=DAB, csh=C(218, 136, 32), cli=C(255, 218, 68), N=(0, 0.4, -0.9), flex=0.25, smin=2.4)

        self.static_g = sb.group(reflect=False, passid=STAND, name="sc5_static")
        self.lamps_g = lamps.group(reflect=False, passid=STAND, name="sc5_lamps")

    def render_frame(self, env, lt):
        parts = list(self.sky.emit(env))

        sf = self.soil_f.emit(env)
        if sf is not None:
            parts.append(sf)
        lf = self.lav_f.emit(env)
        if lf is not None:
            parts.append(lf)

        if self.static_g and self.static_g.visible(env):
            parts.append(shade(env, self.static_g.lod(env), mirror=False))
        if self.lamps_g and self.lamps_g.visible(env):
            parts.append(shade(env, self.lamps_g.lod(env), mirror=False, grade=False))

        # Rotating 4 wooden lattice windmill sails turning lazily against the sunset sky!
        rng = np.random.default_rng(705)
        dyn = SB(rng)
        hub = np.array([self.wx, self.wy + 6.8, self.wz - 2.35], np.float64)
        base_ang = lt * 0.36
        for b_i in range(4):
            a = base_ang + b_i * (math.pi * 0.5)
            b_dir = np.array([math.cos(a), math.sin(a), 0.0], np.float64)
            b_perp = np.array([-math.sin(a), math.cos(a), 0.0], np.float64)
            # Main spar
            dyn.add([hub + b_dir * 2.9], D=b_dir, L=5.8, W=0.22, spr=DASH,
                    csh=C(84, 58, 52), cli=C(168, 118, 78), N=(0, 0, -1), smin=2.6)
            # Sun-catching canvas sail panels along outer 75% of each blade
            for r_s in np.linspace(1.6, 5.4, 5):
                dyn.add([hub + b_dir * r_s + b_perp * 0.55], D=b_dir, L=1.15, W=0.95, spr=DAB + (b_i % 4),
                        csh=C(146, 112, 138), cli=C(255, 212, 168), N=(0, 0, -1), smin=2.8)

        dg = dyn.group(reflect=False, passid=STAND, name="sc5_windmill")
        if dg and dg.visible(env):
            parts.append(shade(env, dg.lod(env), mirror=False))

        # Glowing twilight sunset fireflies & drifting orchid-violet petals
        ff = emit_fireflies(
            env,
            xs=np.linspace(-10.0, 12.0, 32),
            zs=np.linspace(6.0, 34.0, 32),
            y_base=1.1,
            col=(1.12, 0.88, 0.44),
            amt=0.90,
        )
        if ff is not None:
            parts.append(ff)

        petals = emit_drifting_petals(
            env, 26,
            pal_sh=[C(168, 74, 212), C(228, 116, 198)],
            pal_li=[C(228, 148, 255), C(255, 192, 228)],
            scale=0.16, height_range=(0.5, 4.0),
        )
        if petals is not None:
            parts.append(petals)

        return compose(parts)

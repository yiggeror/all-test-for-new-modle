"""Scene 2 (20-40s): Giverny Enchanted Waterlily Pond, Emerald Wisteria Bridge & Koi."""
import math
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, LENS, C, jitter, mix, smooth
from anim.paint.world3 import Field, Path, SB, WATER, MIRROR, RIPPLE, GROUND, STAND, OVER, shade, compose, haze_of, _PASS
from sky3 import SkyDome
from rig3 import add_strolling_person
from common4 import norm3, add_canopy, add_trunk, add_cottage, emit_sunbeams, emit_drifting_petals


def _pond_signed_dist(x, z):
    """Negative inside pond, positive on garden banks."""
    # Gentle crescent pond centered around (x=0, z=20) with rx=24, rz=21
    cx = 1.5 * np.sin(z * 0.08)
    r = np.sqrt(((x - cx) / 23.5) ** 2 + ((z - 20.5) / 21.5) ** 2)
    return (r - 1.0) * 18.0


def bank_y(x, z):
    d = np.maximum(0.0, _pond_signed_dist(np.asarray(x, np.float64), np.asarray(z, np.float64)))
    return 0.14 + 3.4 * (d / (d + 11.0)) + 0.18 * np.sin(np.asarray(x) * 0.15)


def camera_path():
    # Serene floating boat-glide across the emerald mirror pond admiring the wisteria Japanese bridge
    return Path([
        (0.0,  -5.5, 2.05,  0.5,   0.0, 2.65, 22.0, 52.0),
        (5.5,  -2.8, 1.95,  3.8,   0.3, 2.75, 22.0, 51.0),
        (11.0,  0.2, 1.95,  6.8,   0.4, 2.85, 22.5, 50.0),
        (16.0,  3.2, 2.15,  9.0,   0.0, 2.95, 23.0, 49.0),
        (20.0,  5.5, 2.40, 10.6,  -0.4, 3.05, 23.5, 49.0),
    ], sigma=1.5)


def _water_base_shader(env, X, Z, Rn, dist):
    n = len(X)
    sd = _pond_signed_dist(X, Z)
    in_pond = sd < 0.8
    d_norm = np.clip(-sd / 10.0, 0.0, 1.0)
    edge_col = C(18, 76, 72)
    deep_col = C(20, 58, 114)
    rgb = edge_col[None, :] * (1.0 - d_norm[:, None]) + deep_col[None, :] * d_norm[:, None]
    rgb = rgb + (Rn[:, 2:5] - 0.5) * 0.08
    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.52)
    return dict(
        y=np.zeros(n, np.float64),
        D=np.column_stack([np.ones(n), np.zeros(n), np.full(n, 0.15)]),
        rgb=np.clip(rgb, 0.0, 1.1),
        a=np.where(in_pond, 0.96, 0.0).astype(np.float32),
        spr=DAB + (Rn[:, 2] * 4).astype(np.int32) % 4,
        kl=np.full(n, 1.6), kw=np.full(n, 1.1),
        depth_order=np.zeros(n, np.float32),
    )


def _ripple_shader(env, X, Z, Rn, dist):
    n = len(X)
    sd = _pond_signed_dist(X, Z)
    in_pond = sd < 0.2
    wave = np.sin(Z * 1.1 - env.t * 1.5 + X * 0.4 + Rn[:, 1] * 2.5)
    glint = np.clip(wave * 0.5 + 0.5, 0.0, 1.0) ** 3.2
    rgb = mix(C(38, 114, 124), C(255, 246, 198), glint[:, None])
    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.45)
    return dict(
        y=np.full(n, 0.01, np.float64),
        D=np.column_stack([np.ones(n), np.zeros(n), 0.12 * np.sin(X * 0.3 + env.t)]),
        rgb=np.clip(rgb, 0.0, 1.25),
        a=np.where(in_pond, 0.22 + 0.38 * glint, 0.0).astype(np.float32),
        spr=DASH + 2,
        kl=np.full(n, 1.4), kw=np.full(n, 0.36),
        depth_order=np.zeros(n, np.float32),
    )


def _bank_shader(env, X, Z, Rn, dist):
    n = len(X)
    sd = _pond_signed_dist(X, Z)
    on_bank = sd > -0.35
    y = bank_y(X, Z)
    flower_zone = (sd > 0.2) & (sd < 7.5) & (Rn[:, 2] > 0.64)
    rgb = np.column_stack([
        0.16 + 0.14 * Rn[:, 3],
        0.48 + 0.20 * Rn[:, 4],
        0.15 + 0.10 * Rn[:, 5],
    ])
    fc = np.where((Rn[:, 2] < 0.38)[:, None], C(142, 74, 212),
                  np.where((Rn[:, 2] < 0.74)[:, None], C(236, 94, 148), C(252, 206, 62)))
    rgb[flower_zone] = fc[flower_zone]
    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.80)
    return dict(
        y=y,
        D=np.column_stack([np.full(n, 0.6), np.zeros(n), np.full(n, 0.8)]),
        rgb=np.clip(rgb, 0.0, 1.2),
        a=np.where(on_bank, 0.98, 0.0).astype(np.float32),
        spr=DAB + (Rn[:, 5] * 4).astype(np.int32) % 4,
        kl=np.full(n, 1.45), kw=np.full(n, 1.15),
        depth_order=np.where(flower_zone, 0.04, 0.0).astype(np.float32),
    )


def _build_japanese_bridge(sb, rng):
    """Giverny emerald Japanese bridge at z=22 spanning x in [-10.5, 10.5] draped with violet wisteria."""
    bz = 22.0
    xs = np.linspace(-10.5, 10.5, 56)
    def arch_y(x):
        u = np.clip(x / 10.5, -1.0, 1.0)
        return 0.65 + 2.25 * np.cos(u * math.pi * 0.5) ** 1.15

    wood_sh = C(46, 118, 92)
    wood_li = C(104, 188, 134)
    deck_sh = C(62, 126, 96)
    deck_li = C(124, 198, 142)

    for x in xs:
        y = float(arch_y(x))
        sb.add([[x, y, bz]], D=(0, 0, 1), L=2.65, W=0.45, spr=DASH + 1, csh=deck_sh, cli=deck_li, N=(0, 1, 0), smin=3.4)
        for sz in (-1.25, 1.25):
            sb.add([[x, y - 0.14, bz + sz]], D=(1, 0, 0), L=0.58, W=0.22, spr=DASH, csh=wood_sh, cli=wood_li, N=(0, 0.3, sz), smin=2.8)
            sb.add([[x, y + 0.98, bz + sz]], D=(1, 0, 0), L=0.58, W=0.14, spr=DASH, csh=wood_sh, cli=wood_li, N=(0, 1, 0), smin=2.6)
            sb.add([[x, y + 0.52, bz + sz]], D=(1, 0, 0), L=0.58, W=0.09, spr=DASH, csh=wood_sh, cli=wood_li, N=(0, 0.5, sz), smin=2.2)

    for px in np.linspace(-9.8, 9.8, 11):
        py = float(arch_y(px))
        for sz in (-1.25, 1.25):
            sb.add([[px, py + 0.52, bz + sz]], D=(0, 1, 0), L=1.18, W=0.15, spr=DASH, csh=wood_sh, cli=wood_li, N=(0, 0, sz), smin=2.4)
            if abs(px) in (9.8,) or abs(abs(px) - 5.88) < 0.3:
                sb.add([[px, py * 0.45, bz + sz * 0.9]], D=(0, 1, 0), L=py + 0.4, W=0.38, spr=DASH + 1, csh=C(72, 92, 86), cli=C(128, 152, 134), N=(0, 0, -1), smin=2.8)

    for x in np.linspace(-8.2, 8.2, 34):
        y = float(arch_y(x)) + 2.35
        add_canopy(sb, rng, x, y + 0.15, bz, 0.85, 0.55, 1.65, 5, C(58, 128, 64), C(124, 198, 92), smin=3.2, L0=0.82, W0=0.58, flex=0.18)
        for c_i in range(3):
            cx = x + rng.uniform(-0.35, 0.35)
            cz = bz + rng.uniform(-1.45, 1.45)
            clen = rng.uniform(0.65, 1.35)
            steps = 5
            for s in range(steps):
                u = s / (steps - 1)
                wy = y - 0.05 - u * clen
                wsh = mix(C(118, 58, 186), C(204, 148, 242), u)
                wli = mix(C(186, 114, 244), C(250, 208, 255), u)
                sb.add([[cx, wy, cz]], D=(0.08 * math.sin(s), -1.0, 0.08),
                       L=0.34 * (1.15 - 0.45 * u), W=0.22 * (1.15 - 0.5 * u),
                       spr=DAB + rng.integers(0, 4), csh=wsh, cli=wli, N=(0, 0.2, -1), flex=0.34 * u, smin=2.4)


def _build_waterlilies(sb, rng):
    """Build 320 vibrant lily pads & multi-petal pink/coral/ivory waterlilies."""
    pad_sh = [C(28, 92, 58), C(38, 114, 72), C(46, 124, 88)]
    pad_li = [C(72, 168, 86), C(94, 188, 96), C(82, 162, 118)]
    bloom_pairs = [
        (C(218, 72, 118), C(255, 168, 198)),
        (C(238, 112, 128), C(255, 206, 212)),
        (C(222, 206, 194), C(255, 248, 234)),
        (C(216, 168, 78), C(255, 232, 118)),
    ]

    clusters = [
        (-5.5, 9.5, 4.2, 42), (3.8, 11.0, 4.5, 48), (-1.2, 14.5, 4.0, 42),
        (-9.5, 16.5, 4.8, 44), (8.2, 16.0, 4.8, 44), (-4.0, 27.5, 5.2, 36),
        (5.5, 28.0, 5.0, 36), (0.0, 6.5, 3.2, 32),
    ]
    for cx, cz, rad, cnt in clusters:
        for _ in range(cnt):
            ang = rng.uniform(0.0, 2.0 * math.pi)
            rr = rad * math.sqrt(rng.random())
            lx = cx + math.cos(ang) * rr
            lz = cz + math.sin(ang) * rr
            if _pond_signed_dist(lx, lz) > -0.8:
                continue
            ci = int(rng.integers(0, 3))
            psz = rng.uniform(0.55, 1.05)
            sb.add([[lx, 0.03, lz]], D=(math.cos(ang), 0.0, math.sin(ang)), L=psz, W=psz * 0.88,
                   spr=DAB + rng.integers(0, 4), csh=pad_sh[ci], cli=pad_li[ci], N=(0, 1, 0), smin=2.4)
            if rng.random() < 0.56:
                bi = int(rng.integers(0, len(bloom_pairs)))
                bsh, bli = bloom_pairs[bi]
                sb.add([[lx + rng.uniform(-0.1, 0.1), 0.08, lz + rng.uniform(-0.1, 0.1)]],
                       D=(math.sin(ang), 0.25, math.cos(ang)), L=psz * 0.42, W=psz * 0.36,
                       spr=DAB + rng.integers(0, 4), csh=bsh, cli=bli, N=(0, 1, 0), smin=2.2)
                sb.add([[lx, 0.11, lz]], D=(1, 0, 0), L=psz * 0.18, W=psz * 0.18,
                       spr=DAB, csh=C(238, 178, 46), cli=C(255, 238, 108), N=(0, 1, 0), smin=1.6)


class Scene2Waterlilies:
    def __init__(self):
        self.sky = SkyDome(seed=22)
        self.water_f = Field(201, 46.0, _water_base_shader, WATER, c0=0.45, kmax=20, kl=1.55, kw=1.18, wmin=4.2, y0=0.0, maxdist=160.0)
        self.ripple_f = Field(202, 30.0, _ripple_shader, RIPPLE, c0=0.35, kmax=18, kl=1.40, kw=0.58, wmin=2.8, y0=0.01, maxdist=120.0)
        self.bank_f = Field(203, 44.0, _bank_shader, GROUND, c0=0.42, kmax=20, kl=1.45, kw=1.18, wmin=4.0, maxdist=220.0, yfun=bank_y)

        rng = np.random.default_rng(2002)
        sb_refl = SB(rng)   # Reflected in pond water (bridge, willows, villa, iris banks, lily pads!)
        sb_no_refl = SB(rng)
        sb_lamps = SB(rng)

        _build_japanese_bridge(sb_refl, rng)
        _build_waterlilies(sb_refl, rng)

        # Giverny Pink Stucco Villa with Emerald Shutters nestled on upper garden terrace (z = 47)
        add_cottage(sb_refl, sb_lamps, rng, 11.5, float(bank_y(11.5, 47.0)), 47.0, 12.5, 6.8, 5.4, -0.18,
                    C(218, 146, 152), C(255, 202, 206), C(96, 66, 76), C(142, 102, 112))

        # 11 Sweeping Weeping Willows curving over the pond banks with lush emerald-gold cascades
        willows = [
            (-16.5, 16.0), (-19.5, 24.5), (-14.5, 32.0), (-7.5, 39.5),
            (16.5, 15.0), (19.0, 24.0), (15.5, 33.0), (2.5, 41.0),
            (-24.0, 28.0), (24.0, 26.0), (-11.0, 44.0),
        ]
        for wi, (wx, wz) in enumerate(willows):
            wy = float(bank_y(wx, wz))
            lean = -1.2 if wx > 0 else 1.2
            add_trunk(sb_refl, rng, wx, wy, wz, 5.6, 0.48, C(78, 66, 54), C(128, 108, 84), lean_x=lean)
            # Crown
            add_canopy(sb_refl, rng, wx + lean * 0.9, wy + 5.6, wz, 4.4, 2.8, 4.2, 62,
                       C(54, 124, 58), C(148, 212, 92), smin=4.8, L0=1.25, W0=0.88, flex=0.22)
            # Hanging willow leaf strands trailing toward the water
            for f_i in range(28):
                ang_f = rng.uniform(0, 2 * math.pi)
                rf = rng.uniform(1.5, 4.2)
                fx = wx + lean * 0.9 + math.cos(ang_f) * rf
                fz = wz + math.sin(ang_f) * rf
                hang = rng.uniform(2.6, 4.6)
                for s in range(4):
                    u = s / 3.0
                    sb_refl.add([[fx, wy + 5.2 - u * hang, fz]], D=(0.06, -1.0, 0.04),
                                L=1.15, W=0.28, spr=DASH + 2,
                                csh=C(52, 122, 58), cli=C(156, 224, 96),
                                N=(0, 0.2, -1), flex=0.35 * (0.3 + 0.7 * u), smin=2.4)

        # Blooming purple iris, magenta rhododendron & golden bamboo groves along near & far banks
        for _ in range(160):
            ang = rng.uniform(-math.pi * 0.88, math.pi * 0.88)
            rr = rng.uniform(0.98, 1.32)
            fx = 1.5 * math.sin(20.5 * 0.08) + math.cos(ang) * 23.5 * rr
            fz = 20.5 + math.sin(ang) * 21.5 * rr
            if fz < 2.0:
                continue
            fy = float(bank_y(fx, fz))
            c_idx = int(rng.integers(0, 3))
            if c_idx == 0:
                sh, li = C(118, 48, 186), C(188, 118, 248)  # Royal Iris
            elif c_idx == 1:
                sh, li = C(214, 56, 118), C(255, 142, 186)  # Azalea Rose
            else:
                sh, li = C(228, 152, 42), C(255, 226, 98)   # Golden Marigold/Daylily
            sb_refl.add([[fx, fy + 0.45, fz]], D=(0, 1, 0), L=0.82, W=0.48, spr=DAB + rng.integers(0, 4),
                        csh=sh, cli=li, N=(0, 1, 0), flex=0.22, smin=2.6)

        # Moored painted green-and-ochre wooden rowboat near left willow bank (-13.5, 15.0)
        bx, bz = -13.5, 15.0
        for u in np.linspace(-1.4, 1.4, 7):
            w_hull = 0.72 * math.cos(u * 0.85)
            sb_no_refl.add([[bx + u * 0.65, 0.22, bz + u * 0.85]], D=(0.65, 0, 0.85), L=0.85, W=max(0.28, w_hull),
                           spr=DASH + 1, csh=C(38, 94, 78), cli=C(92, 162, 128), N=(0, 1, 0), smin=2.6)

        self.refl_g = sb_refl.group(reflect=True, passid=STAND, name="sc2_refl")
        self.norefl_g = sb_no_refl.group(reflect=False, passid=STAND, name="sc2_norefl")
        self.lamps_g = sb_lamps.group(reflect=True, passid=STAND, name="sc2_lamps")

    def render_frame(self, env, lt):
        t = lt
        parts = list(self.sky.emit(env))

        wf = self.water_f.emit(env)
        if wf is not None:
            parts.append(wf)

        # Pond reflections drawn in MIRROR pass BEFORE ripples & floating lily pads!
        if self.refl_g and self.refl_g.visible(env, mirror=True):
            parts.append(shade(env, self.refl_g.lod(env, mirror=True), mirror=True))
        if self.lamps_g and self.lamps_g.visible(env, mirror=True):
            parts.append(shade(env, self.lamps_g.lod(env, mirror=True), mirror=True, grade=False))

        # Swimming Golden & Crimson Koi fish gliding smoothly beneath the pond ripples
        rng = np.random.default_rng(702)
        koi_sb = SB(rng)
        koi_routes = [
            (-2.0, 9.5, 3.2, 0.35, 0.0, C(218, 72, 28), C(255, 168, 56)),
            (2.4, 11.8, 3.8, 0.28, 2.1, C(232, 138, 34), C(255, 224, 96)),
            (-4.2, 14.0, 2.8, 0.32, 4.2, C(224, 48, 38), C(255, 126, 78)),
            (1.2, 8.2, 2.6, 0.40, 1.1, C(244, 198, 74), C(255, 242, 168)),
        ]
        for kx0, kz0, rad, spd, ph, ksh, kli in koi_routes:
            th = t * spd + ph
            for seg in range(5):
                s_th = th - seg * 0.11
                fx = kx0 + math.cos(s_th) * rad + 0.14 * seg * math.sin(t * 7.5 - seg * 0.9 + ph)
                fz = kz0 + math.sin(s_th) * (rad * 0.65)
                dx = -math.sin(s_th) * rad
                dz = math.cos(s_th) * (rad * 0.65)
                w_seg = 0.22 * (1.0 - 0.16 * seg)
                koi_sb.add([[fx, 0.005, fz]], D=(dx, 0.0, dz), L=0.34, W=w_seg, spr=DAB,
                           csh=ksh, cli=kli, N=(0, 1, 0), a=0.72, smin=1.8)
        kg = koi_sb.group(reflect=False, passid=WATER, name="sc2_koi")
        if kg and kg.visible(env):
            parts.append(shade(env, kg.lod(env), mirror=False, sway=False))

        rf = self.ripple_f.emit(env)
        if rf is not None:
            parts.append(rf)
        bf = self.bank_f.emit(env)
        if bf is not None:
            parts.append(bf)

        if self.refl_g and self.refl_g.visible(env, mirror=False):
            parts.append(shade(env, self.refl_g.lod(env, mirror=False), mirror=False))
        if self.norefl_g and self.norefl_g.visible(env):
            parts.append(shade(env, self.norefl_g.lod(env), mirror=False))
        if self.lamps_g and self.lamps_g.visible(env):
            parts.append(shade(env, self.lamps_g.lod(env), mirror=False, grade=False))

        # Two leisurely admirers walking slowly across the emerald Japanese bridge
        dyn = SB(rng)
        bx1 = -4.2 + t * 0.34
        by1 = 0.65 + 2.25 * math.cos(np.clip(bx1 / 10.5, -1, 1) * math.pi * 0.5) ** 1.15
        add_strolling_person(dyn, (bx1, by1 + 0.06, 21.8), math.pi * 0.5, t * 2.8,
                             C(186, 128, 178), C(250, 212, 238),
                             hat_sh=C(212, 186, 134), hat_li=C(252, 234, 182),
                             parasol_cols=(C(238, 132, 168), C(255, 218, 232)))
        add_strolling_person(dyn, (bx1 - 1.35, by1 + 0.02, 22.4), math.pi * 0.45, t * 2.8 + 0.8,
                             C(64, 92, 148), C(124, 162, 224),
                             hat_sh=C(196, 172, 122), hat_li=C(246, 224, 168), parasol_cols=None)

        dg = dyn.group(reflect=True, passid=STAND, name="sc2_bridge_people")
        if dg and dg.visible(env, mirror=True):
            parts.append(shade(env, dg.lod(env, mirror=True), mirror=True))
        if dg and dg.visible(env, mirror=False):
            parts.append(shade(env, dg.lod(env, mirror=False), mirror=False))

        # Sunbeams filtering diagonally through willow canopy onto the lotus pond
        beams = emit_sunbeams(
            env,
            origins=[(-10.0, 14.0, 24.0, 4.4, 24.0), (0.0, 16.0, 26.0, 5.2, 26.0), (11.0, 14.5, 22.0, 4.2, 23.0)],
            dir_vec=(0.38, -0.84, -0.38),
            col=(1.05, 0.98, 0.74),
            alpha=0.10,
        )
        if beams is not None:
            parts.append(beams)

        petals = emit_drifting_petals(
            env, 30,
            pal_sh=[C(196, 118, 242), C(248, 162, 206), C(255, 236, 246)],
            pal_li=[C(242, 206, 255), C(255, 222, 238), C(255, 252, 255)],
            scale=0.18, height_range=(0.6, 5.5),
        )
        if petals is not None:
            parts.append(petals)

        return compose(parts)

"""Scene 4 (60-80s): Rouen Gothic Cathedral — Molten Gold & Royal Violet Sunset."""
import math
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, LENS, C, jitter, mix, smooth
from anim.paint.world3 import Field, Path, SB, GROUND, STAND, OVER, shade, compose, haze_of
from sky3 import SkyDome
from rig3 import add_strolling_person
from common4 import norm3, add_cottage, emit_sunbeams, emit_fireflies

CATH_Z = 34.0


def plaza_y(x, z):
    return np.zeros_like(np.asarray(x, np.float64))


def camera_path():
    # Majestic low-angle glide across Rouen sunset square framing plaza strollers, flower stalls, portals, Rose Window & spires
    return Path([
        (0.0,  -9.0, 2.65, -20.0,   0.0, 13.8, CATH_Z, 58.0),
        (6.0,  -4.5, 2.60, -16.5,   0.2, 14.4, CATH_Z, 57.0),
        (12.0,  0.5, 2.70, -12.5,   0.4, 15.0, CATH_Z, 55.0),
        (17.0,  3.8, 2.85,  -9.5,   0.2, 15.5, CATH_Z, 54.0),
        (20.0,  5.2, 3.00,  -8.0,   0.0, 16.0, CATH_Z, 54.0),
    ], sigma=1.5)


def _plaza_shader(env, X, Z, Rn, dist):
    n = len(X)
    gold_pool = np.exp(-((X) / 15.0) ** 2 - ((Z - 16.0) / 13.0) ** 2)
    base_col = np.column_stack([
        0.32 + 0.14 * Rn[:, 2],
        0.24 + 0.10 * Rn[:, 3],
        0.44 + 0.14 * Rn[:, 4],
    ])
    sun_cobble = np.column_stack([
        0.86 + 0.10 * Rn[:, 2],
        0.52 + 0.12 * Rn[:, 3],
        0.34 + 0.08 * Rn[:, 4],
    ])
    rgb = base_col * (1.0 - 0.65 * gold_pool[:, None]) + sun_cobble * (0.65 * gold_pool[:, None])
    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.55)
    return dict(
        y=np.zeros(n, np.float64),
        D=np.column_stack([np.ones(n), np.zeros(n), 0.25 * Rn[:, 5]]),
        rgb=np.clip(rgb, 0.0, 1.2),
        spr=DAB + (Rn[:, 5] * 4).astype(np.int32) % 4,
        kl=np.full(n, 1.45), kw=np.full(n, 1.18),
        depth_order=np.zeros(n, np.float32),
    )


def _build_rouen_cathedral(sb, glow_sb, rng):
    """Solid Gothic Rouen Cathedral facade with twin asymmetric towers, spire, triple portals & Rose Window."""
    stone_sh = C(88, 76, 138)
    stone_li = C(255, 192, 114)
    tracery_sh = C(74, 64, 126)
    tracery_li = C(255, 222, 154)
    dark_niche_sh = C(34, 30, 70)
    dark_niche_li = C(88, 68, 112)

    # 1. Solid main lower & gallery facade massif (tightly overlapping vertical masonry!)
    for x in np.linspace(-13.2, 13.2, 36):
        for y in np.linspace(0.8, 22.8, 22):
            z_off = -0.65 if min(abs(x - bx) for bx in (-12.6, -5.2, 5.2, 12.6)) < 1.05 else 0.0
            sb.add([[x + rng.uniform(-0.10, 0.10), y, CATH_Z + z_off]],
                   D=(0, 1, 0), L=1.85, W=1.45, spr=DASH + rng.integers(0, 4),
                   csh=stone_sh, cli=stone_li, N=(0.35, 0.25, -0.9), smin=4.0, a=0.99)

    # 2. Three recessed Gothic pointed portals at street level
    for px, pw, ph in [(-8.0, 2.8, 6.8), (0.0, 4.2, 9.2), (8.0, 2.8, 6.8)]:
        for k in np.linspace(-0.5, 0.5, 8):
            for y in np.linspace(0.5, ph * (1.0 - 0.52 * abs(k)), 9):
                sb.add([[px + k * pw, y, CATH_Z - 0.55]], D=(0, 1, 0), L=1.35, W=0.85, spr=DASH + 1,
                       csh=dark_niche_sh, cli=dark_niche_li, N=(0, 0.1, -1), smin=3.4, a=0.99)
        for u in np.linspace(-1.0, 1.0, 13):
            gx = px + u * (pw * 0.62)
            gy = ph + (1.0 - abs(u)) * 3.6
            sb.add([[gx, gy, CATH_Z - 0.85]], D=(1, -math.copysign(1.2, u), 0), L=1.35, W=0.68, spr=DASH,
                   csh=tracery_sh, cli=tracery_li, N=(0.3, 0.3, -0.9), smin=3.2)

    # 3. Gallery of Kings horizontal Gothic arcade
    for x in np.linspace(-12.0, 12.0, 26):
        sb.add([[x, 12.8, CATH_Z - 0.95]], D=(0, 1, 0), L=2.1, W=0.78, spr=DASH + 1,
               csh=tracery_sh, cli=tracery_li, N=(0.4, 0.3, -0.85), smin=3.0)

    # 4. Luminous Iridescent Circular Rose Window set in dark Gothic stone surround at (0, 17.6, CATH_Z - 1.05)
    ry = 17.6
    rz = CATH_Z - 1.05
    for ang in np.linspace(0, 2 * math.pi, 32, endpoint=False):
        sb.add([[math.cos(ang) * 3.45, ry + math.sin(ang) * 3.45, rz + 0.08]],
               D=(-math.sin(ang), math.cos(ang), 0), L=1.05, W=0.72, spr=DASH,
               csh=dark_niche_sh, cli=tracery_li, N=(0.3, 0.2, -0.9), smin=3.2)
    jewel_cols = [C(255, 68, 92), C(68, 138, 255), C(255, 198, 64), C(72, 218, 152), C(222, 92, 255)]
    for ring_r, cnt in [(0.75, 1), (1.58, 10), (2.58, 18)]:
        for i in range(cnt):
            ang = i * (2 * math.pi / cnt)
            jc = jewel_cols[(i + int(ring_r * 2)) % len(jewel_cols)]
            glow_sb.add([[math.cos(ang) * ring_r, ry + math.sin(ang) * ring_r, rz - 0.14]],
                        D=(math.cos(ang), math.sin(ang), 0), L=0.82, W=0.72, spr=DAB + (i % 4),
                        csh=jc * 0.9, cli=jc, N=(0, 0, -1), emis=0.82, smin=2.8)

    # 5. Twin Asymmetric Towers: Tour Saint-Romain (x=-10.2, h=30.5m) & Tour de Beurre (x=+10.4, h=33.5m)
    for tx, th, tw, has_crown in [(-10.2, 30.5, 4.4, False), (10.4, 33.5, 4.6, True)]:
        for x in np.linspace(tx - tw * 0.5, tx + tw * 0.5, 7):
            for y in np.linspace(22.0, th, int((th - 22.0) / 0.9)):
                is_win = abs(x - tx) < tw * 0.22 and (y < th - 3.2)
                sb.add([[x, y, CATH_Z - 0.5]], D=(0, 1, 0), L=1.75, W=1.22, spr=DASH + 1,
                       csh=dark_niche_sh if is_win else stone_sh,
                       cli=dark_niche_li if is_win else stone_li,
                       N=(0.35, 0.25, -0.9), smin=3.6, a=0.99)
        crown_h = 5.4 if has_crown else 3.8
        for px in (tx - tw * 0.44, tx, tx + tw * 0.44):
            for k in range(5):
                u = k / 4.0
                sb.add([[px, th + u * crown_h, CATH_Z - 0.5]], D=(0, 1, 0),
                       L=crown_h * 0.34, W=1.12 * (1.0 - 0.72 * u), spr=DASH,
                       csh=tracery_sh, cli=tracery_li, N=(0.3, 0.25, -0.9), smin=3.0)

    # 6. Central Flèche Spire soaring behind nave to y = 41m
    for u in np.linspace(0.0, 1.0, 14):
        sy = 23.0 + u * 18.0
        sb.add([[0.0, sy, CATH_Z + 4.5]], D=(0, 1, 0), L=2.2, W=2.2 * (1.0 - 0.88 * u),
               spr=DASH, csh=tracery_sh, cli=tracery_li, N=(0.4, 0.2, -0.9), smin=3.2)


class Scene4Cathedral:
    def __init__(self):
        self.sky = SkyDome(seed=44)
        self.plaza_f = Field(401, 44.0, _plaza_shader, GROUND, c0=0.45, kmax=20, kl=1.45, kw=1.18, wmin=4.0, y0=0.0, maxdist=160.0)

        rng = np.random.default_rng(4004)
        sb = SB(rng)
        glow_sb = SB(rng)

        _build_rouen_cathedral(sb, glow_sb, rng)

        # Flanking half-timbered medieval Rouen townhouses & sunset cafés along left and right of plaza
        houses = [
            (-21.5, 16.0, 8.2, 6.2, 8.5, 1.48, C(118, 92, 128), C(228, 174, 142), C(86, 56, 88), C(168, 94, 98)),
            (-22.5, 26.0, 8.5, 6.4, 9.2, 1.52, C(112, 86, 122), C(218, 164, 136), C(78, 54, 84), C(156, 88, 94)),
            (21.5,  15.5, 8.2, 6.2, 8.6, -1.48, C(124, 96, 132), C(236, 182, 146), C(86, 58, 90), C(172, 98, 102)),
            (22.5,  25.5, 8.6, 6.4, 9.4, -1.52, C(116, 88, 124), C(224, 168, 138), C(80, 54, 86), C(158, 90, 96)),
        ]
        for hx, hz, hw, hd, hh, yaw, wsh, wli, rsh, rli in houses:
            add_cottage(sb, glow_sb, rng, hx, 0.0, hz, hw, hd, hh, yaw, wsh, wli, rsh, rli)

        # Colorful sunset flower market stalls along the right-side archway
        flower_pals = [(C(228, 44, 62), C(255, 122, 118)), (C(238, 174, 42), C(255, 234, 98)), (C(146, 58, 208), C(224, 148, 255))]
        for si, (sx, sz) in enumerate([(13.8, 18.0), (14.5, 22.5), (-14.2, 19.5)]):
            # Striped awning
            sb.add([[sx, 2.35, sz]], D=(0, 0, 1), L=3.4, W=1.8, spr=DAB,
                   csh=C(168, 52, 62) if si % 2 == 0 else C(68, 96, 164),
                   cli=C(246, 114, 92) if si % 2 == 0 else C(132, 174, 242), N=(0, 1, 0), smin=3.0)
            for k in range(18):
                sh, li = flower_pals[(si + k) % 3]
                sb.add([[sx + rng.uniform(-1.1, 1.1), rng.uniform(0.55, 1.35), sz + rng.uniform(-1.3, 1.3)]],
                       D=(1, 0, 0), L=0.58, W=0.45, spr=DAB + (k % 4), csh=sh, cli=li, N=(0, 1, 0), smin=2.4)

        # Glowing warm plaza street lanterns flanking cathedral forecourt
        for lx, lz in [(-14.5, 14.0), (-14.5, 26.0), (14.5, 14.0), (14.5, 26.0)]:
            sb.add([[lx, 1.8, lz]], D=(0, 1, 0), L=3.6, W=0.22, spr=DASH, csh=C(48, 44, 64), cli=C(92, 84, 108), N=(0, 0, -1), smin=2.2)
            glow_sb.add([[lx, 3.7, lz]], D=(0, 1, 0), L=0.65, W=0.65, spr=LENS, csh=C(255, 188, 72), cli=C(255, 228, 128), N=(0, 0, -1), emis=1.0, smin=2.8)

        self.static_g = sb.group(reflect=False, passid=STAND, name="sc4_cathedral")
        self.glow_g = glow_sb.group(reflect=False, passid=STAND, name="sc4_glow")

    def render_frame(self, env, lt):
        parts = list(self.sky.emit(env))

        pf = self.plaza_f.emit(env)
        if pf is not None:
            parts.append(pf)

        if self.static_g and self.static_g.visible(env):
            parts.append(shade(env, self.static_g.lod(env), mirror=False))
        if self.glow_g and self.glow_g.visible(env):
            parts.append(shade(env, self.glow_g.lod(env), mirror=False, grade=False))

        # Citizens & evening strollers crossing cathedral square + 32 spiraling sunset doves!
        rng = np.random.default_rng(704)
        dyn = SB(rng)

        strollers = [
            (-5.5, 16.5, 0.32, 0.25, C(112, 84, 148), C(222, 166, 206), (C(242, 134, 148), C(255, 212, 196))),
            (-4.2, 17.2, 0.30, 0.28, C(52, 68, 118),  C(124, 142, 198), None),
            (4.8,  20.5, -0.28, -0.35, C(168, 86, 98), C(246, 174, 148), None),
            (1.5,  24.0, 0.24, 0.15, C(188, 172, 188), C(252, 232, 218), (C(246, 196, 108), C(255, 238, 174))),
        ]
        for x0, z0, vx, yaw, dsh, dli, pcols in strollers:
            add_strolling_person(dyn, (x0 + vx * lt, 0.0, z0 + 0.15 * lt), yaw, lt * 2.9, dsh, dli,
                                 hat_sh=C(186, 152, 118), hat_li=C(252, 224, 168), parasol_cols=pcols)

        # 32 White-and-Rose-Lit Doves wheeling in joyous spirals around the Cathedral spires & Rose Window!
        for d_i in range(32):
            ang = lt * 0.62 + d_i * (2 * math.pi / 32.0)
            rad = 9.0 + 7.5 * math.sin(d_i * 1.4 + lt * 0.25)
            dx = math.cos(ang) * rad
            dz = (CATH_Z - 6.0) + math.sin(ang) * (rad * 0.55)
            dy = 17.5 + 11.5 * (d_i / 32.0) + 1.8 * math.sin(lt * 1.4 + d_i)
            flap = 0.22 * math.sin(lt * 11.0 + d_i * 1.9)
            tx = -math.sin(ang)
            tz = math.cos(ang)
            dyn.add([[dx - 0.24, dy + flap, dz], [dx + 0.24, dy + flap, dz]],
                    D=(tx, 0.15, tz), L=0.52, W=0.16, spr=DASH + 2,
                    csh=C(196, 172, 212), cli=C(255, 236, 206), N=(0, 1, 0), smin=2.0)

        dg = dyn.group(reflect=False, passid=STAND, name="sc4_actors")
        if dg and dg.visible(env):
            parts.append(shade(env, dg.lod(env), mirror=False))

        # Molten sunset sunbeams & floating golden plaza motes
        beams = emit_sunbeams(
            env,
            origins=[(-18.0, 32.0, 26.0, 5.5, 34.0), (-6.0, 36.0, 28.0, 6.2, 36.0)],
            dir_vec=(0.56, -0.76, -0.32),
            col=(1.08, 0.82, 0.52),
            alpha=0.11,
        )
        if beams is not None:
            parts.append(beams)

        motes = emit_fireflies(
            env,
            xs=np.linspace(-13.0, 13.0, 24),
            zs=np.linspace(12.0, 30.0, 24),
            y_base=1.8,
            col=(1.08, 0.86, 0.48),
            amt=0.65,
        )
        if motes is not None:
            parts.append(motes)

        return compose(parts)

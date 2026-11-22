"""Scene 3 (40-60s): Argenteuil 5-Arch Stone Viaduct, Steam Train & Collision-Free Regatta."""
import math
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, LENS, C, jitter, mix, smooth
from anim.paint.world3 import Field, Path, SB, WATER, MIRROR, RIPPLE, GROUND, STAND, OVER, shade, compose, haze_of
from sky3 import SkyDome
from rig3 import add_sailor_crew, add_strolling_person
from common4 import norm3, add_canopy, add_trunk, add_cottage, emit_sunbeams

BRIDGE_Z = 42.0
BRIDGE_DECK_Y = 9.4
ARCH_CROWN_Y = 7.6
PIER_XS = (-52.5, -31.5, -10.5, 10.5, 31.5, 52.5)
PIER_HALF_W = 1.45
PIER_HALF_D = 2.20
RIVER_HALF_W = 54.0


def bank_y(x, z):
    ax = np.abs(np.asarray(x, np.float64))
    d = np.maximum(0.0, ax - RIVER_HALF_W)
    return 0.35 + 4.8 * (d / (d + 14.0)) + 0.25 * np.sin(np.asarray(z) * 0.08)


def boat_state(idx, lt):
    """Deterministic arch-centered regatta lanes with guaranteed pier clearance (>6m)."""
    lanes = [
        # (arch_cx, z_start, speed_z, sway_amp, sway_freq, ph, mast_h, hull_sh, hull_li, sail_sh, sail_li, trim_col)
        (0.0,   58.0, -2.05, 1.35, 0.48, 0.0, 5.2, C(168, 42, 42),  C(238, 92, 68),  C(222, 226, 240), C(255, 250, 240), C(238, 62, 54)),
        (-21.0, 62.0, -1.78, 1.45, 0.42, 1.1, 4.9, C(38, 72, 148),  C(86, 138, 224), C(228, 222, 206), C(255, 246, 212), C(252, 198, 54)),
        (21.0,  55.0, -1.68, 1.40, 0.50, 2.3, 4.8, C(34, 114, 96),  C(72, 178, 148), C(234, 218, 224), C(255, 236, 240), C(236, 86, 128)),
        (-42.0, 50.0, -1.45, 1.25, 0.38, 0.6, 4.6, C(132, 74, 46),  C(202, 126, 72), C(218, 228, 238), C(252, 248, 238), C(56, 152, 226)),
        (42.0,  64.0, -1.85, 1.25, 0.45, 3.1, 4.7, C(58, 62, 118),  C(108, 118, 196),C(236, 224, 210), C(255, 244, 214), C(244, 118, 48)),
    ]
    cx, z0, vz, amp, freq, ph, mh, hsh, hli, ssh, sli, tcol = lanes[idx]
    z = z0 + vz * lt
    x = cx + amp * math.sin(lt * freq + ph)
    vx = amp * freq * math.cos(lt * freq + ph)
    yaw = math.atan2(vx, vz)
    return dict(x=x, z=z, yaw=yaw, mast_h=mh, hull_sh=hsh, hull_li=hli, sail_sh=ssh, sail_li=sli, trim_col=tcol, idx=idx)


def check_boat_clearances(dur=20.0, steps=120):
    """Verify every sailboat stays well clear of all stone viaduct piers and mast < arch crown."""
    min_pier_clear = 1e9
    max_mast = 0.0
    for s in range(steps + 1):
        lt = dur * (s / steps)
        for bi in range(5):
            st = boat_state(bi, lt)
            max_mast = max(max_mast, st["mast_h"])
            if abs(st["z"] - BRIDGE_Z) < 6.5:
                for px in PIER_XS:
                    clear = abs(st["x"] - px) - PIER_HALF_W
                    min_pier_clear = min(min_pier_clear, clear)
    return min_pier_clear, ARCH_CROWN_Y - max_mast


def camera_path():
    # Grand Argenteuil promenade-to-river glide framing viaduct arches, steam train & sailboats
    return Path([
        (0.0,   14.5, 4.0, -3.5,   0.0, 5.4, 38.0, 54.0),
        (5.5,   11.0, 3.8,  0.5,  -0.5, 5.5, 39.0, 53.0),
        (11.0,   6.5, 3.6,  4.5,  -1.0, 5.6, 40.0, 51.0),
        (16.0,   2.6, 3.5,  8.0,  -0.4, 5.6, 40.5, 50.0),
        (20.0,   0.2, 3.6, 10.2,   0.0, 5.8, 41.0, 50.0),
    ], sigma=1.4)


def _seine_water_shader(env, X, Z, Rn, dist):
    n = len(X)
    in_river = np.abs(X) < (RIVER_HALF_W + 0.6)
    u = np.clip(np.abs(X) / RIVER_HALF_W, 0.0, 1.0)
    mid_col = C(32, 92, 142)
    bank_col = C(38, 122, 114)
    rgb = mid_col[None, :] * (1.0 - 0.45 * u[:, None]) + bank_col[None, :] * (0.45 * u[:, None])
    rgb = rgb + (Rn[:, 2:5] - 0.5) * 0.09
    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.68)
    return dict(
        y=np.zeros(n, np.float64),
        D=np.column_stack([np.ones(n), np.zeros(n), 0.1 * np.sin(Z * 0.2)]),
        rgb=np.clip(rgb, 0.0, 1.15),
        a=np.where(in_river, 0.98, 0.0).astype(np.float32),
        spr=DAB + (Rn[:, 3] * 4).astype(np.int32) % 4,
        kl=np.full(n, 1.65), kw=np.full(n, 1.12),
        depth_order=np.zeros(n, np.float32),
    )


def _seine_ripple_shader(env, X, Z, Rn, dist):
    n = len(X)
    in_river = np.abs(X) < RIVER_HALF_W
    wave = np.sin(Z * 0.85 + env.t * 2.2 + X * 0.28 + Rn[:, 1] * 2.0)
    glint = np.clip(wave * 0.5 + 0.5, 0.0, 1.0) ** 3.0
    rgb = mix(C(52, 128, 174), C(255, 248, 214), glint[:, None])
    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.52)
    return dict(
        y=np.full(n, 0.015, np.float64),
        D=np.column_stack([np.ones(n), np.zeros(n), 0.18 * np.cos(X * 0.2 + env.t)]),
        rgb=np.clip(rgb, 0.0, 1.25),
        a=np.where(in_river, 0.22 + 0.38 * glint, 0.0).astype(np.float32),
        spr=DASH + 2,
        kl=np.full(n, 1.45), kw=np.full(n, 0.36),
        depth_order=np.zeros(n, np.float32),
    )


def _bank_grass_shader(env, X, Z, Rn, dist):
    n = len(X)
    on_bank = np.abs(X) > (RIVER_HALF_W - 0.5)
    y = bank_y(X, Z)
    rgb = np.column_stack([
        0.24 + 0.16 * Rn[:, 2],
        0.54 + 0.18 * Rn[:, 3],
        0.18 + 0.10 * Rn[:, 4],
    ])
    pop = (np.abs(X) > RIVER_HALF_W + 1.5) & (Rn[:, 5] > 0.78)
    rgb[pop] = mix(C(234, 58, 52), C(255, 206, 68), Rn[:, 3][pop, None])
    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.82)
    return dict(
        y=y,
        D=np.column_stack([np.full(n, 0.5), np.zeros(n), np.full(n, 0.86)]),
        rgb=np.clip(rgb, 0.0, 1.2),
        a=np.where(on_bank, 0.98, 0.0).astype(np.float32),
        spr=DAB + (Rn[:, 3] * 4).astype(np.int32) % 4,
        kl=np.full(n, 1.45), kw=np.full(n, 1.15),
        depth_order=np.where(pop, 0.04, 0.0).astype(np.float32),
    )


def _build_viaduct(sb, rng):
    """Argenteuil 5-arch cream-ochre stone viaduct spanning x in [-66, 66] at z = 42."""
    stone_sh = C(142, 132, 148)
    stone_li = C(242, 224, 188)
    trim_sh = C(124, 118, 136)
    trim_li = C(228, 212, 184)

    for px in PIER_XS:
        for py in np.linspace(0.2, BRIDGE_DECK_Y - 0.3, 14):
            for ox in (-0.55, 0.55):
                for oz in (-1.2, 0.0, 1.2):
                    sb.add([[px + ox, py, BRIDGE_Z + oz]], D=(0, 1, 0), L=1.35, W=1.75, spr=DASH + rng.integers(0, 4),
                           csh=stone_sh, cli=stone_li, N=(0, 0.2, -1 if oz <= 0 else 1), smin=3.8, a=0.99)
        sb.add([[px, 1.4, BRIDGE_Z - PIER_HALF_D - 0.25]], D=(0, 1, 0), L=3.0, W=1.45, spr=DASH + 1,
               csh=trim_sh, cli=trim_li, N=(0, 0.3, -1), smin=3.4)

    for i in range(len(PIER_XS) - 1):
        cx = 0.5 * (PIER_XS[i] + PIER_XS[i + 1])
        half_span = 9.05
        for x in np.linspace(cx - half_span, cx + half_span, 34):
            u = np.clip((x - cx) / half_span, -1.0, 1.0)
            y_soffit = 3.2 + (ARCH_CROWN_Y - 3.2) * math.sqrt(max(0.0, 1.0 - u * u))
            for oz in (-1.4, 1.4):
                sb.add([[x, y_soffit, BRIDGE_Z + oz]], D=(1, -u * 0.6, 0), L=1.15, W=0.82, spr=DASH,
                       csh=trim_sh, cli=trim_li, N=(0, 0.3, -1 if oz < 0 else 1), smin=3.4, a=0.99)
                for sy in np.linspace(y_soffit + 0.45, BRIDGE_DECK_Y - 0.15, max(3, int((BRIDGE_DECK_Y - y_soffit) / 0.55))):
                    sb.add([[x, sy, BRIDGE_Z + oz]], D=(1, 0, 0), L=1.18, W=0.95, spr=DASH + rng.integers(0, 4),
                           csh=stone_sh, cli=stone_li, N=(0, 0.2, -1 if oz < 0 else 1), smin=3.6, a=0.99)

    for x in np.linspace(-72.0, 72.0, 110):
        sb.add([[x, BRIDGE_DECK_Y, BRIDGE_Z]], D=(1, 0, 0), L=1.95, W=3.6, spr=DASH + 1,
               csh=trim_sh, cli=trim_li, N=(0, 1, 0), smin=4.0, a=0.99)
        sb.add([[x, BRIDGE_DECK_Y + 0.55, BRIDGE_Z - 1.75]], D=(1, 0, 0), L=1.7, W=0.40, spr=DASH,
               csh=C(72, 82, 102), cli=C(148, 162, 184), N=(0, 0.4, -1), smin=2.8)


def _draw_sailboat(sb, st, t):
    x, z, yaw = st["x"], st["z"], st["yaw"]
    fwd = np.array([math.sin(yaw), 0.0, math.cos(yaw)], np.float64)
    right = np.array([math.cos(yaw), 0.0, -math.sin(yaw)], np.float64)
    up = np.array([0.0, 1.0, 0.0], np.float64)
    bob = 0.08 * math.sin(t * 2.4 + st["idx"] * 1.5)
    heel = 0.14 * math.sin(t * 1.3 + st["idx"])
    origin = np.array([x, 0.16 + bob, z], np.float64)
    mast_up = norm3(up + right * heel)

    for u in np.linspace(-1.0, 1.0, 11):
        hw = 0.85 * math.cos(u * 1.15)
        hp = origin + fwd * (u * 2.15)
        sb.add([hp], D=fwd, L=0.68, W=max(0.24, hw), spr=DASH + 1,
               csh=st["hull_sh"], cli=st["hull_li"], N=up, smin=2.8)
        sb.add([hp + up * 0.16 + right * (hw * 0.45)], D=fwd, L=0.65, W=0.14, spr=DASH,
               csh=st["trim_col"] * 0.78, cli=st["trim_col"], N=right, smin=2.0)

    mh = st["mast_h"]
    sb.add([origin + mast_up * (mh * 0.5)], D=mast_up, L=mh, W=0.13, spr=DASH,
           csh=C(112, 74, 46), cli=C(186, 128, 72), N=right, smin=2.2)
    sb.add([origin + mast_up * 1.15 - fwd * 1.15], D=fwd, L=2.4, W=0.10, spr=DASH,
           csh=C(112, 74, 46), cli=C(186, 128, 72), N=up, smin=2.0)

    # Smooth sculptural overlapping triangular mainsail & clean slim jib
    for v_s in np.linspace(0.05, 0.94, 9):
        max_u = 1.0 - v_s * 0.90
        for u_s in np.linspace(0.0, max_u, 5):
            belly = 0.34 * math.sin(u_s * math.pi / max(0.2, max_u)) * (1.0 - 0.5 * v_s)
            sp = origin + mast_up * (1.1 + v_s * (mh - 1.25)) - fwd * (u_s * 2.1) + right * belly
            sb.add([sp], D=mast_up, L=0.82, W=0.65, spr=DASH + ((int(v_s * 10 + u_s * 7)) % 4),
                   csh=st["sail_sh"], cli=st["sail_li"], N=right * 0.7 - fwd * 0.4, smin=2.6, a=0.98)
    for v_s in np.linspace(0.12, 0.88, 6):
        sp = origin + mast_up * (0.9 + v_s * (mh - 1.5)) + fwd * (0.82 * (1.0 - v_s)) + right * 0.16
        sb.add([sp], D=mast_up - fwd * 0.32, L=0.72, W=0.45 * (1.0 - 0.65 * v_s), spr=DASH,
               csh=st["sail_sh"] * 0.94, cli=st["sail_li"], N=right, smin=2.2, a=0.96)

    sb.add([origin + mast_up * (mh + 0.15) - fwd * 0.28], D=-fwd + right * (0.3 * math.sin(t * 7.0 + st["idx"])),
           L=0.65, W=0.14, spr=DASH + 2, csh=st["trim_col"] * 0.8, cli=st["trim_col"], N=up, smin=2.0)

    if st["idx"] == 0:
        add_sailor_crew(sb, origin, fwd, right, up, right * math.copysign(1.0, heel), t * 2.8)


def _draw_steam_train(sb, lt):
    """Vivid emerald-and-brass 1874 locomotive + 4 cream/mahogany carriages crossing center viaduct."""
    tx = -44.0 + (lt / 20.0) * 84.0
    ty = BRIDGE_DECK_Y + 0.42
    tz = BRIDGE_Z - 0.15

    sb.add([[tx, ty + 0.88, tz]], D=(1, 0, 0), L=4.6, W=1.30, spr=DASH + 1, csh=C(32, 92, 68), cli=C(72, 162, 108), N=(0, 0.5, -1), smin=3.2)
    sb.add([[tx + 1.8, ty + 1.65, tz]], D=(0, 1, 0), L=1.25, W=0.45, spr=DASH, csh=C(48, 52, 66), cli=C(108, 114, 134), N=(0, 0.3, -1), smin=2.6)
    sb.add([[tx + 0.6, ty + 1.55, tz]], D=(0, 1, 0), L=0.62, W=0.52, spr=DAB, csh=C(196, 152, 48), cli=C(255, 224, 96), N=(0, 1, 0), smin=2.4)
    for wx in (-1.4, 0.0, 1.4):
        sb.add([[tx + wx, ty + 0.16, tz - 0.72]], D=(1, 0, 0), L=0.78, W=0.78, spr=DAB, csh=C(164, 34, 34), cli=C(234, 68, 52), N=(0, 0, -1), smin=2.2)

    for c_i in range(4):
        cx = tx - 5.2 - c_i * 4.8
        sb.add([[cx, ty + 0.88, tz]], D=(1, 0, 0), L=4.2, W=1.28, spr=DASH + 1, csh=C(118, 56, 44), cli=C(192, 98, 68), N=(0, 0.5, -1), smin=3.0)
        sb.add([[cx, ty + 1.52, tz]], D=(1, 0, 0), L=4.3, W=0.52, spr=DASH, csh=C(198, 186, 168), cli=C(250, 240, 218), N=(0, 1, 0), smin=2.6)

    for p_i in range(22):
        age = p_i * 0.22
        px = (tx + 1.8) - age * 2.8 - 0.4 * math.sin(lt * 1.8 + p_i)
        py = ty + 2.15 + age * 1.15 + 0.25 * math.sin(lt * 2.1 + p_i)
        pz = tz + 0.35 * math.cos(p_i * 1.3)
        rad = 0.92 + age * 0.74
        alpha = max(0.10, 0.90 * (1.0 - age / 4.8))
        sb.add([[px, py, pz]], D=(1, 0.25, 0), L=rad * 1.4, W=rad, spr=SCUM + (p_i % 4),
               csh=C(152, 158, 198), cli=C(255, 250, 242), N=(0, 0.85, -0.4), a=alpha, smin=3.4)


class Scene3Viaduct:
    def __init__(self):
        self.sky = SkyDome(seed=33)
        self.water_f = Field(301, 48.0, _seine_water_shader, WATER, c0=0.48, kmax=20, kl=1.65, kw=1.18, wmin=4.2, y0=0.0, maxdist=240.0)
        self.ripple_f = Field(302, 32.0, _seine_ripple_shader, RIPPLE, c0=0.36, kmax=18, kl=1.40, kw=0.58, wmin=2.8, y0=0.015, maxdist=160.0)
        self.bank_f = Field(303, 46.0, _bank_grass_shader, GROUND, c0=0.45, kmax=20, kl=1.55, kw=1.18, wmin=4.0, maxdist=260.0, yfun=bank_y)

        rng = np.random.default_rng(3003)
        sb_refl = SB(rng)
        sb_lamps = SB(rng)
        _build_viaduct(sb_refl, rng)

        # Argenteuil colorful riverside houses & poplars along left & right embankments
        houses = [
            (-62.0, 28.0, 10.5, 6.8, 5.2, 1.35, C(218, 196, 174), C(255, 238, 212), C(164, 62, 48), C(238, 104, 68)),
            (-64.0, 56.0, 11.5, 7.2, 5.6, 1.45, C(232, 168, 156), C(255, 216, 202), C(86, 98, 134), C(142, 158, 204)),
            (62.0,  32.0, 11.0, 7.0, 5.4, -1.35, C(208, 188, 156), C(255, 234, 194), C(158, 66, 48), C(228, 108, 72)),
            (65.0,  58.0, 12.0, 7.5, 5.8, -1.42, C(196, 206, 218), C(246, 248, 252), C(168, 62, 48), C(242, 108, 72)),
        ]
        for hx, hz, hw, hd, hh, yaw, wsh, wli, rsh, rli in houses:
            add_cottage(sb_refl, sb_lamps, rng, hx, float(bank_y(hx, hz)), hz, hw, hd, hh, yaw, wsh, wli, rsh, rli)

        # Riverside poplars & golden-green riverside trees on both embankments
        for side in (-1.0, 1.0):
            for z in np.linspace(12.0, 78.0, 11):
                tx = side * (RIVER_HALF_W + rng.uniform(2.5, 11.5))
                ty = float(bank_y(tx, z))
                h = rng.uniform(6.5, 10.5)
                add_trunk(sb_refl, rng, tx, ty, z, h * 0.45, 0.36, C(82, 68, 58), C(132, 108, 86))
                add_canopy(sb_refl, rng, tx, ty + h * 0.65, z, 2.8, h * 0.42, 2.8, 36,
                           C(58, 124, 62), C(142, 208, 92), smin=4.5, L0=1.35, W0=0.95, flex=0.18)

        # Near-foreground sunlit right-bank promenade trees framing upper corners gently
        for tx, tz in [(22.5, 9.5), (27.0, 18.0)]:
            ty = float(bank_y(tx, tz))
            add_trunk(sb_refl, rng, tx, ty, tz, 4.8, 0.34, C(84, 68, 58), C(134, 112, 88))
            add_canopy(sb_refl, rng, tx - 0.8, ty + 5.2, tz, 3.4, 2.5, 3.2, 42, C(62, 132, 64), C(156, 218, 96), smin=4.6, L0=1.25, W0=0.88, flex=0.18)

        self.refl_g = sb_refl.group(reflect=True, passid=STAND, name="sc3_static")
        self.lamps_g = sb_lamps.group(reflect=True, passid=STAND, name="sc3_lamps")

    def render_frame(self, env, lt):
        parts = list(self.sky.emit(env))

        wf = self.water_f.emit(env)
        if wf is not None:
            parts.append(wf)

        # Static bridge & dynamic boats/train reflections!
        rng = np.random.default_rng(703)
        dyn = SB(rng)
        for bi in range(5):
            st = boat_state(bi, lt)
            _draw_sailboat(dyn, st, lt)
        _draw_steam_train(dyn, lt)

        dg = dyn.group(reflect=True, passid=STAND, name="sc3_dyn")

        if self.refl_g and self.refl_g.visible(env, mirror=True):
            parts.append(shade(env, self.refl_g.lod(env, mirror=True), mirror=True))
        if dg and dg.visible(env, mirror=True):
            parts.append(shade(env, dg.lod(env, mirror=True), mirror=True))

        rf = self.ripple_f.emit(env)
        if rf is not None:
            parts.append(rf)
        bf = self.bank_f.emit(env)
        if bf is not None:
            parts.append(bf)

        if self.refl_g and self.refl_g.visible(env, mirror=False):
            parts.append(shade(env, self.refl_g.lod(env, mirror=False), mirror=False))
        if dg and dg.visible(env, mirror=False):
            parts.append(shade(env, dg.lod(env, mirror=False), mirror=False))
        if self.lamps_g and self.lamps_g.visible(env):
            parts.append(shade(env, self.lamps_g.lod(env), mirror=False, grade=False))

        # Sunbeams angling cleanly across the steam cloud and river sails
        beams = emit_sunbeams(
            env,
            origins=[(-18.0, 26.0, 44.0, 6.0, 34.0), (4.0, 28.0, 46.0, 6.5, 36.0)],
            dir_vec=(0.45, -0.82, -0.35),
            col=(1.04, 0.96, 0.78),
            alpha=0.085,
        )
        if beams is not None:
            parts.append(beams)

        return compose(parts)

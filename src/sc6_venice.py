"""Scene 6 (100-120s): Venice San Giorgio Maggiore Twilight Lagoon, Gondolas, Moon & Stars."""
import math
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, LENS, C, jitter, mix, smooth
from anim.paint.world3 import Field, Path, SB, WATER, MIRROR, RIPPLE, GROUND, STAND, OVER, shade, compose, haze_of
from sky3 import SkyDome
from common4 import norm3, add_cottage, emit_fireflies


def camera_path():
    # Serene nocturnal gondola glide framing ENTIRE San Giorgio Campanile spire, dome, gondolas, moon & stars
    return Path([
        (0.0,   -7.5, 2.40, -2.5,   0.5,  8.8, 52.0, 54.0),
        (6.0,   -4.2, 2.40,  0.5,   0.8,  9.2, 54.0, 53.0),
        (12.0,  -0.5, 2.50,  3.8,   1.0,  9.6, 55.0, 51.0),
        (17.0,   2.2, 2.65,  6.4,   0.6, 10.2, 56.0, 50.0),
        (20.0,   3.5, 2.80,  8.0,   0.2, 10.6, 56.0, 50.0),
    ], sigma=1.6)


def _lagoon_water_shader(env, X, Z, Rn, dist):
    n = len(X)
    rgb = np.column_stack([
        0.09 + 0.08 * Rn[:, 2] + 0.08 * np.exp(-((X) / 28.0) ** 2),
        0.13 + 0.08 * Rn[:, 3],
        0.34 + 0.14 * Rn[:, 4],
    ])
    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.70)
    return dict(
        y=np.zeros(n, np.float64),
        D=np.column_stack([np.ones(n), np.zeros(n), 0.12 * np.sin(Z * 0.25)]),
        rgb=np.clip(rgb, 0.0, 1.1),
        a=np.full(n, 0.98, np.float32),
        spr=DAB + (Rn[:, 5] * 4).astype(np.int32) % 4,
        kl=np.full(n, 1.65), kw=np.full(n, 1.15),
        depth_order=np.zeros(n, np.float32),
    )


def _lagoon_ripple_shader(env, X, Z, Rn, dist):
    n = len(X)
    wave = np.sin(Z * 1.15 - env.t * 1.4 + X * 0.32 + Rn[:, 1] * 2.2)
    glint = np.clip(wave * 0.5 + 0.5, 0.0, 1.0) ** 3.4
    moon_path = np.exp(-((X - 2.0) / 14.0) ** 2)
    glint_col = mix(C(238, 124, 96), C(255, 224, 148), moon_path[:, None])
    rgb = mix(C(44, 56, 128), glint_col, glint[:, None])
    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.52)
    return dict(
        y=np.full(n, 0.012, np.float64),
        D=np.column_stack([np.ones(n), np.zeros(n), 0.14 * np.cos(X * 0.3 + env.t)]),
        rgb=np.clip(rgb, 0.0, 1.25),
        a=(0.24 + 0.44 * glint).astype(np.float32),
        spr=DASH + 2,
        kl=np.full(n, 1.48), kw=np.full(n, 0.38),
        depth_order=np.zeros(n, np.float32),
    )


def _build_san_giorgio(sb, lamps, rng):
    """San Giorgio Maggiore island quay, Palladian basilica, turquoise dome & solid brick Campanile at z=56."""
    iz = 56.0
    for x in np.linspace(-38.0, 38.0, 56):
        sb.add([[x, 0.55, iz - 4.2]], D=(1, 0, 0), L=1.95, W=1.45, spr=DASH + 1,
               csh=C(108, 92, 124), cli=C(236, 184, 152), N=(0, 0.4, -1), smin=3.4)
        if abs(x) % 9.0 < 1.5:
            lamps.add([[x, 2.2, iz - 4.0]], D=(0, 1, 0), L=0.68, W=0.68, spr=LENS,
                      csh=C(255, 192, 74), cli=C(255, 232, 134), N=(0, 0, -1), emis=1.0, smin=2.8)

    marb_sh = C(118, 96, 146)
    marb_li = C(248, 198, 166)
    col_sh = C(156, 134, 178)
    col_li = C(255, 224, 196)
    for x in np.linspace(-7.6, 7.6, 22):
        for y in np.linspace(1.0, 8.6, 10):
            sb.add([[x, y, iz]], D=(0, 1, 0), L=1.75, W=1.45, spr=DASH + rng.integers(0, 4),
                   csh=marb_sh, cli=marb_li, N=(0.25, 0.2, -0.9), smin=3.6, a=0.99)
    # Four Palladian Corinthian engaged columns + triangular temple pediment
    for cx_col in (-4.4, -1.6, 1.6, 4.4):
        for cy_col in np.linspace(1.2, 8.6, 8):
            sb.add([[cx_col, cy_col, iz - 0.55]], D=(0, 1, 0), L=1.45, W=0.68, spr=DASH,
                   csh=col_sh, cli=col_li, N=(0.3, 0.2, -0.92), smin=3.0, a=0.99)
    for u in np.linspace(-1.0, 1.0, 15):
        px = u * 4.9
        py = 8.8 + (1.0 - abs(u)) * 3.0
        sb.add([[px, py, iz - 0.55]], D=(1, 0, 0), L=1.35, W=0.95, spr=DASH,
               csh=col_sh, cli=col_li, N=(0, 0.4, -1), smin=3.2, a=0.99)

    dome_sh = C(54, 108, 118)
    dome_li = C(132, 206, 188)
    for v_a in np.linspace(0.0, math.pi * 0.48, 9):
        rad = 4.6 * math.cos(v_a)
        dy = 10.6 + 5.0 * math.sin(v_a)
        for ang in np.linspace(0, 2 * math.pi, 22, endpoint=False):
            nx, nz = math.cos(ang), math.sin(ang)
            sb.add([[nx * rad, dy, iz + 3.5 + nz * rad]], D=(0, 1, 0), L=1.55, W=1.55,
                   spr=DASH + 1, csh=dome_sh, cli=dome_li, N=(nx, 0.4, nz), smin=3.4, a=0.99)
    lamps.add([[0.0, 16.5, iz + 3.5]], D=(0, 1, 0), L=1.2, W=0.78, spr=LENS,
              csh=C(255, 204, 108), cli=C(255, 238, 168), N=(0, 0, -1), emis=0.9, smin=2.8)

    # Solid single-massif Brick-and-Crimson Campanile Bell Tower at (cx = 12.5, iz + 1.5), pinnacle at y = 24.5m!
    cx = 12.5
    brick_sh = C(118, 54, 72)
    brick_li = C(242, 128, 96)
    for y in np.linspace(1.0, 16.5, 16):
        for ox in (-0.85, 0.0, 0.85):
            sb.add([[cx + ox, y, iz + 1.5]], D=(0, 1, 0), L=1.75, W=1.65, spr=DASH + 1,
                   csh=brick_sh, cli=brick_li, N=(0.3, 0.15, -0.9), smin=3.6, a=0.99)
    for ox in (-0.9, 0.0, 0.9):
        sb.add([[cx + ox, 17.8, iz + 1.5]], D=(0, 1, 0), L=2.0, W=1.35, spr=DASH,
               csh=marb_sh, cli=marb_li, N=(0, 0.2, -1), smin=3.2, a=0.99)
    lamps.add([[cx, 17.8, iz + 0.8]], D=(0, 1, 0), L=1.25, W=1.25, spr=LENS,
              csh=C(255, 198, 86), cli=C(255, 234, 148), N=(0, 0, -1), emis=0.95, smin=2.8)
    for u in np.linspace(0.0, 1.0, 9):
        sb.add([[cx, 19.2 + u * 5.4, iz + 1.5]], D=(0, 1, 0), L=1.15, W=2.5 * (1.0 - 0.88 * u),
               spr=DASH, csh=C(164, 148, 174), cli=C(252, 224, 192), N=(0.3, 0.2, -0.9), smin=3.0)

    wings = [
        (-21.5, iz + 1.0, 16.0, 7.0, 6.8, 0.0, C(148, 84, 96), C(244, 152, 118), C(96, 54, 68), C(174, 96, 84)),
        (24.5,  iz + 1.0, 14.0, 7.0, 7.4, 0.0, C(136, 92, 108), C(238, 168, 128), C(92, 56, 72), C(168, 98, 88)),
    ]
    for hx, hz, hw, hd, hh, yaw, wsh, wli, rsh, rli in wings:
        add_cottage(sb, lamps, rng, hx, 0.4, hz, hw, hd, hh, yaw, wsh, wli, rsh, rli)


def _draw_gondola(sb, lamps, x, z, yaw, oar_phase, idx):
    fwd = np.array([math.sin(yaw), 0.0, math.cos(yaw)], np.float64)
    right = np.array([math.cos(yaw), 0.0, -math.sin(yaw)], np.float64)
    up = np.array([0.0, 1.0, 0.0], np.float64)
    origin = np.array([x, 0.14 + 0.04 * math.sin(oar_phase + idx), z], np.float64)

    for u in np.linspace(-1.0, 1.0, 11):
        bow_rise = 0.72 * (abs(u) ** 2.6)
        hw = 0.62 * math.cos(u * 1.2)
        sb.add([origin + fwd * (u * 3.1) + up * bow_rise], D=fwd, L=0.82, W=max(0.18, hw),
               spr=DASH + 1, csh=C(22, 24, 38), cli=C(58, 62, 92), N=up, smin=2.4)
    sb.add([origin + fwd * 3.25 + up * 0.92], D=up + fwd * 0.25, L=0.72, W=0.20,
           spr=DASH, csh=C(168, 178, 206), cli=C(244, 248, 255), N=right, smin=2.0)
    sb.add([origin + up * 0.28], D=fwd, L=1.35, W=0.68, spr=DAB,
           csh=C(138, 28, 48), cli=C(218, 68, 86), N=up, smin=2.4)

    lantern_pos = origin + fwd * 2.55 + up * 0.65
    lamps.add([lantern_pos], D=up, L=0.55, W=0.55, spr=LENS,
              csh=C(255, 192, 68), cli=C(255, 232, 134), N=up, emis=1.0, smin=2.4)

    gpos = origin - fwd * 1.75 + up * 0.35
    sway = 0.14 * math.sin(oar_phase)
    torso_top = gpos + up * 1.05 + fwd * sway
    sb.add([gpos + up * 0.48], D=up, L=0.68, W=0.28, spr=DASH, csh=C(28, 34, 68), cli=C(68, 78, 128), N=up, smin=2.0)
    sb.add([torso_top - up * 0.25], D=up + fwd * sway, L=0.58, W=0.34, spr=DAB, csh=C(196, 192, 202), cli=C(252, 246, 236), N=up, smin=2.0)
    sb.add([torso_top + up * 0.14], D=up, L=0.22, W=0.20, spr=DAB, csh=C(186, 134, 114), cli=C(244, 198, 168), N=up, smin=1.8)
    sb.add([torso_top + up * 0.25], D=fwd, L=0.40, W=0.34, spr=DAB, csh=C(188, 158, 108), cli=C(248, 224, 162), N=up, smin=1.8)
    oar_tip = gpos + right * (1.55 + 0.25 * math.cos(oar_phase)) - fwd * (0.95 - 0.55 * math.sin(oar_phase)) - up * 0.36
    oar_hand = torso_top + right * 0.35 - up * 0.15
    oar_vec = oar_tip - oar_hand
    sb.add([(oar_hand + oar_tip) * 0.5], D=norm3(oar_vec), L=float(np.linalg.norm(oar_vec)), W=0.08,
           spr=DASH, csh=C(102, 68, 44), cli=C(174, 118, 74), N=up, smin=1.8)


class Scene6Venice:
    def __init__(self):
        self.sky = SkyDome(seed=66)
        self.water_f = Field(601, 48.0, _lagoon_water_shader, WATER, c0=0.48, kmax=20, kl=1.65, kw=1.18, wmin=4.2, y0=0.0, maxdist=240.0)
        self.ripple_f = Field(602, 32.0, _lagoon_ripple_shader, RIPPLE, c0=0.36, kmax=18, kl=1.45, kw=0.58, wmin=2.8, y0=0.012, maxdist=160.0)

        rng = np.random.default_rng(6006)
        sb_refl = SB(rng)
        lamps_refl = SB(rng)
        _build_san_giorgio(sb_refl, lamps_refl, rng)

        self.refl_g = sb_refl.group(reflect=True, passid=STAND, name="sc6_san_giorgio")
        self.lamps_g = lamps_refl.group(reflect=True, passid=STAND, name="sc6_lamps")

    def render_frame(self, env, lt):
        parts = list(self.sky.emit(env))

        wf = self.water_f.emit(env)
        if wf is not None:
            parts.append(wf)

        # 3 Animated Venetian Gondolas gliding across the lagoon mirror
        rng = np.random.default_rng(706)
        dyn = SB(rng)
        dyn_lamps = SB(rng)
        gondolas = [
            (-5.5 + lt * 0.52, 16.5 + 0.8 * math.sin(lt * 0.3),  1.32, lt * 1.6, 0),
            (6.8 - lt * 0.38,  24.0 + 0.6 * math.cos(lt * 0.25),-1.42, lt * 1.4 + 1.2, 1),
            (-12.0 + lt * 0.30, 32.0,                            1.48, lt * 1.5 + 2.4, 2),
        ]
        for gx, gz, gyaw, oph, gi in gondolas:
            _draw_gondola(dyn, dyn_lamps, gx, gz, gyaw, oph, gi)

        dg = dyn.group(reflect=True, passid=STAND, name="sc6_gondolas")
        dlg = dyn_lamps.group(reflect=True, passid=STAND, name="sc6_gondola_lamps")

        # MIRROR reflections BEFORE lagoon ripples
        if self.refl_g and self.refl_g.visible(env, mirror=True):
            parts.append(shade(env, self.refl_g.lod(env, mirror=True), mirror=True))
        if self.lamps_g and self.lamps_g.visible(env, mirror=True):
            parts.append(shade(env, self.lamps_g.lod(env, mirror=True), mirror=True, grade=False))
        if dg and dg.visible(env, mirror=True):
            parts.append(shade(env, dg.lod(env, mirror=True), mirror=True))
        if dlg and dlg.visible(env, mirror=True):
            parts.append(shade(env, dlg.lod(env, mirror=True), mirror=True, grade=False))

        rf = self.ripple_f.emit(env)
        if rf is not None:
            parts.append(rf)

        if self.refl_g and self.refl_g.visible(env, mirror=False):
            parts.append(shade(env, self.refl_g.lod(env, mirror=False), mirror=False))
        if self.lamps_g and self.lamps_g.visible(env, mirror=False):
            parts.append(shade(env, self.lamps_g.lod(env, mirror=False), mirror=False, grade=False))
        if dg and dg.visible(env, mirror=False):
            parts.append(shade(env, dg.lod(env, mirror=False), mirror=False))
        if dlg and dlg.visible(env, mirror=False):
            parts.append(shade(env, dlg.lod(env, mirror=False), mirror=False, grade=False))

        # Drifting warm golden Venice evening embers / lanterns near waterfront
        ff = emit_fireflies(
            env,
            xs=np.linspace(-20.0, 20.0, 20),
            zs=np.linspace(18.0, 48.0, 20),
            y_base=1.8,
            col=(1.10, 0.84, 0.42),
            amt=0.75,
        )
        if ff is not None:
            parts.append(ff)

        return compose(parts)

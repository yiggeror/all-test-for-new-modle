"""Scene 1 (0-20s): Argenteuil Poppy & Cornflower Hillside — Sunlit Morning Dream."""
import math
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, LENS, C, jitter, mix, noise, smooth
from anim.paint.world3 import Field, Path, SB, GROUND, STAND, OVER, shade, compose, haze_of
from sky3 import SkyDome
from rig3 import add_running_kite_boy, add_galloping_dog, add_strolling_person
from common4 import norm3, add_canopy, add_trunk, add_cottage, emit_sunbeams, emit_drifting_petals


def terrain_y(x, z):
    """Monotonic upward-sloping hillside along +Z (prevents any background bleed-through)."""
    x = np.asarray(x, np.float64)
    z = np.asarray(z, np.float64)
    # Base gradual climb + gentle horizon mountain step; dy/dz > 0 everywhere for z > -20
    rise = np.where(z > -20.0, 0.115 * (z + 20.0) + 6.5 * np.maximum(0.0, (z - 35.0) / (np.maximum(z - 35.0, 0.0) + 95.0)), 0.0)
    undul = 0.42 * np.sin(x * 0.048) * np.exp(-np.maximum(z, 0.0) * 0.008)
    shoulder = 1.6 * np.exp(-((x + 38.0) / 28.0) ** 2 - ((z - 55.0) / 42.0) ** 2)
    return rise + undul + shoulder


def _path_center_x(z):
    return -2.8 + 4.2 * np.sin(z * 0.045) + 0.10 * z


def camera_path():
    # Calm, poetic dolly-arc across the scarlet poppy meadow keeping kite boy, kite & farmhouse framed
    return Path([
        (0.0,  -9.0,  float(terrain_y(-9.0, -3.0)) + 2.35,  -3.0,   1.4, float(terrain_y(1.4, 22.0)) + 2.5,  22.0, 52.0),
        (5.5,  -5.5,  float(terrain_y(-5.5,  0.5)) + 2.30,   0.5,   2.8, float(terrain_y(2.8, 26.0)) + 2.8,  26.0, 51.0),
        (11.0, -1.8,  float(terrain_y(-1.8,  4.2)) + 2.45,   4.2,   4.2, float(terrain_y(4.2, 31.0)) + 3.2,  31.0, 50.0),
        (16.0,  1.8,  float(terrain_y( 1.8,  8.0)) + 2.75,   8.0,   5.6, float(terrain_y(5.6, 37.0)) + 3.8,  37.0, 49.0),
        (20.0,  4.6,  float(terrain_y( 4.6, 10.8)) + 3.05,  10.8,   6.5, float(terrain_y(6.5, 42.0)) + 4.3,  42.0, 48.0),
    ], sigma=1.4)


def _meadow_shader(env, X, Z, Rn, dist):
    n = len(X)
    y = terrain_y(X, Z)
    pcx = _path_center_x(Z)
    on_path = np.abs(X - pcx) < (1.55 + 0.35 * np.sin(Z * 0.14))

    patch_poppy = noise(X * 0.11 + 3.1, Z * 0.11 - 1.7)
    patch_blue = noise(X * 0.13 - 5.2, Z * 0.13 + 4.4)
    shadow_mod = 0.86 + 0.14 * np.sin(X * 0.08 + Z * 0.06)

    grass_base = np.column_stack([
        0.22 + 0.16 * Rn[:, 2] + 0.06 * np.sin(X * 0.09),
        0.54 + 0.18 * Rn[:, 3] + 0.08 * np.cos(Z * 0.08),
        0.15 + 0.08 * Rn[:, 4],
    ])
    path_col = np.column_stack([
        0.82 + 0.10 * Rn[:, 2],
        0.68 + 0.09 * Rn[:, 3],
        0.48 + 0.07 * Rn[:, 4],
    ])

    rgb = np.where(on_path[:, None], path_col, grass_base) * shadow_mod[:, None]
    far_floral = (~on_path) & (dist > 28.0) & (patch_poppy > 0.52)
    rgb[far_floral] = mix(rgb[far_floral], C(236, 56, 44), 0.62)
    far_blue = (~on_path) & (dist > 28.0) & (~far_floral) & (patch_blue > 0.60)
    rgb[far_blue] = mix(rgb[far_blue], C(62, 128, 232), 0.48)

    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.90)

    return dict(
        y=y,
        D=np.column_stack([np.full(n, 0.65), np.zeros(n), np.full(n, 0.76)]),
        rgb=np.clip(rgb, 0.0, 1.2),
        spr=np.where(Rn[:, 0] < 0.5, DAB + (Rn[:, 2] * 4).astype(np.int32) % 4, SCUM + (Rn[:, 2] * 4).astype(np.int32) % 4),
        kl=np.where(on_path, 1.25, 1.35),
        kw=np.where(on_path, 0.95, 1.15),
        depth_order=np.zeros(n, np.float32),
    )


def _wildflower_shader(env, X, Z, Rn, dist):
    n = len(X)
    pcx = _path_center_x(Z)
    on_path = np.abs(X - pcx) < 1.35
    patch_poppy = noise(X * 0.11 + 3.1, Z * 0.11 - 1.7)
    patch_blue = noise(X * 0.13 - 5.2, Z * 0.13 + 4.4)
    patch_gold = noise(X * 0.16 + 9.4, Z * 0.16 - 3.3)

    is_poppy = (~on_path) & (patch_poppy > 0.44) & (Rn[:, 2] > 0.22)
    is_blue = (~on_path) & (~is_poppy) & (patch_blue > 0.52) & (Rn[:, 2] > 0.34)
    is_daisy = (~on_path) & (~is_poppy) & (~is_blue) & (patch_gold > 0.48) & (Rn[:, 2] > 0.40)

    y = terrain_y(X, Z) + np.where(is_poppy | is_blue | is_daisy, 0.30 + 0.18 * Rn[:, 3], 0.16 + 0.10 * Rn[:, 3])
    rgb = np.zeros((n, 3), np.float32)
    rgb[:] = np.column_stack([
        0.24 + 0.14 * Rn[:, 4],
        0.58 + 0.18 * Rn[:, 5],
        0.16 + 0.08 * Rn[:, 2],
    ])
    pop_col = mix(C(224, 28, 28), C(255, 88, 42), Rn[:, 5][:, None])
    rgb[is_poppy] = pop_col[is_poppy]
    blue_col = mix(C(38, 92, 224), C(96, 162, 255), Rn[:, 5][:, None])
    rgb[is_blue] = blue_col[is_blue]
    daisy_col = mix(C(255, 246, 198), C(255, 206, 52), Rn[:, 5][:, None])
    rgb[is_daisy] = daisy_col[is_daisy]

    a = np.where(on_path, 0.0, np.where(is_poppy | is_blue | is_daisy, 0.96, 0.82))
    sway = 0.24 * np.sin(env.t * 2.1 + X * 0.22 + Z * 0.15)
    hx = np.clip(env.sun[0] * (X - env.C[0]) / np.maximum(dist, 1.0) + env.sun[2] * (Z - env.C[2]) / np.maximum(dist, 1.0), 0.0, 1.0)
    rgb = haze_of(env, rgb, dist, hx=hx, amt=0.88)

    return dict(
        y=y,
        rgb=np.clip(rgb, 0.0, 1.25),
        a=a.astype(np.float32),
        spr=np.where(is_poppy | is_blue | is_daisy, DAB + (Rn[:, 2] * 4).astype(np.int32) % 4, DASH + 1),
        upright=np.where(is_poppy | is_blue | is_daisy, 0.0, 0.85),
        lean=sway.astype(np.float32),
        kl=np.where(is_poppy, 0.85, np.where(is_blue | is_daisy, 0.72, 1.05)),
        kw=np.where(is_poppy, 0.80, np.where(is_blue | is_daisy, 0.68, 0.45)),
        depth_order=np.full(n, 0.04, np.float32),
    )


class Scene1Poppies:
    def __init__(self):
        self.sky = SkyDome(seed=11)
        self.field_ground = Field(101, 48.0, _meadow_shader, GROUND, c0=0.40, kmax=20, kl=1.68, kw=1.35, wmin=4.5, maxdist=320.0, yfun=terrain_y)
        self.field_flowers = Field(102, 24.0, _wildflower_shader, GROUND, c0=0.30, kmax=18, kl=1.08, kw=0.82, wmin=2.8, maxdist=165.0, yfun=terrain_y)

        rng = np.random.default_rng(1001)
        sb = SB(rng)
        sb_lamps = SB(rng)

        for i in range(44):
            px = -95.0 + i * 4.4 + rng.uniform(-1.5, 1.5)
            pz = 118.0 + rng.uniform(-8.0, 26.0)
            py = float(terrain_y(px, pz))
            h = rng.uniform(7.5, 12.5)
            add_trunk(sb, rng, px, py, pz, h * 0.45, 0.35, C(78, 86, 124), C(124, 134, 152))
            add_canopy(sb, rng, px, py + h * 0.68, pz, 2.2, h * 0.42, 2.2, 18, C(72, 126, 142), C(142, 198, 128), smin=4.5, L0=1.6, W0=1.1)

        fx, fz = 16.5, 62.0
        fy = float(terrain_y(fx, fz))
        add_cottage(sb, sb_lamps, rng, fx, fy, fz, 11.0, 7.2, 5.2, -0.32,
                    C(186, 162, 146), C(250, 224, 186), C(152, 62, 48), C(228, 108, 72))
        add_cottage(sb, None, rng, 28.0, float(terrain_y(28.0, 68.0)), 68.0, 7.5, 5.5, 3.8, -0.25,
                    C(174, 154, 142), C(238, 214, 182), C(138, 58, 46), C(208, 98, 68), windows=False)

        orchard_spots = [
            (-15.5, 22.0), (-21.0, 32.0), (-12.5, 38.0), (-26.0, 48.0), (-16.5, 52.0),
            (-5.0, 56.0), (5.5, 52.0), (24.0, 48.0), (31.0, 38.0), (19.0, 34.0),
            (13.0, 43.0), (-31.0, 62.0), (-22.0, 72.0), (-9.0, 76.0), (8.0, 82.0),
            (36.0, 62.0), (-38.0, 36.0), (38.0, 50.0),
        ]
        for idx, (tx, tz) in enumerate(orchard_spots):
            ty = float(terrain_y(tx, tz))
            sc = rng.uniform(0.85, 1.32)
            add_trunk(sb, rng, tx, ty, tz, 3.2 * sc, 0.34 * sc, C(96, 72, 64), C(148, 114, 88), lean_x=rng.uniform(-0.4, 0.4))
            is_pink = (idx % 3 != 0)
            if is_pink:
                c_sh = C(214, 128, 156) if idx % 2 == 0 else C(232, 168, 186)
                c_li = C(255, 212, 224) if idx % 2 == 0 else C(255, 238, 244)
            else:
                c_sh = C(86, 148, 84)
                c_li = C(168, 224, 116)
            add_canopy(sb, rng, tx, ty + 3.6 * sc, tz, 3.2 * sc, 2.3 * sc, 3.1 * sc, 52, c_sh, c_li, smin=5.2, L0=1.25, W0=0.92, flex=0.18)

        for cx, cz, yaw in [(-7.5, 45.0, 0.7), (-3.8, 47.5, -0.4), (3.5, 49.0, 1.1), (-11.0, 50.0, 0.3)]:
            cy = float(terrain_y(cx, cz))
            fwd = np.array([math.sin(yaw), 0.0, math.cos(yaw)])
            body = np.array([cx, cy + 0.95, cz])
            sb.add([body], D=fwd, L=1.75, W=0.88, spr=DAB, csh=C(194, 188, 182), cli=C(252, 246, 236), N=(0, 1, 0), smin=3.2)
            sb.add([body + fwd * 0.25 + np.array([0, 0.1, 0])], D=fwd, L=0.85, W=0.65, spr=DAB + 1, csh=C(112, 62, 42), cli=C(166, 94, 58), N=(0, 1, 0), smin=2.8)
            sb.add([body + fwd * 0.95 - np.array([0, 0.22, 0])], D=fwd, L=0.58, W=0.45, spr=DAB, csh=C(168, 148, 136), cli=C(238, 224, 206), N=(0, 1, 0), smin=2.6)

        for _ in range(180):
            fz = rng.uniform(1.0, 26.0)
            side = -1.0 if rng.random() < 0.5 else 1.0
            fxp = float(_path_center_x(fz)) + side * rng.uniform(1.5, 11.5)
            fyp = float(terrain_y(fxp, fz))
            h_f = rng.uniform(0.45, 0.85)
            sb.add([[fxp, fyp + h_f * 0.45, fz]], D=(0.08 * side, 1.0, 0.0), L=h_f, W=0.06, spr=DASH + 1,
                   csh=C(48, 108, 48), cli=C(108, 178, 72), N=(0, 1, 0), flex=0.22, smin=1.6)
            kind = rng.random()
            if kind < 0.58:
                csh, cli = C(208, 22, 28), C(255, 76, 48)
                sz = rng.uniform(0.24, 0.38)
            elif kind < 0.82:
                csh, cli = C(36, 78, 204), C(96, 162, 255)
                sz = rng.uniform(0.18, 0.28)
            else:
                csh, cli = C(242, 232, 168), C(255, 252, 226)
                sz = rng.uniform(0.18, 0.26)
            sb.add([[fxp, fyp + h_f, fz]], D=(1, 0, 0), L=sz, W=sz * 0.92, spr=DAB + rng.integers(0, 4),
                   csh=csh, cli=cli, N=(0, 1, 0), flex=0.25, smin=2.2)

        self.static_g = sb.group(reflect=False, passid=STAND, name="sc1_static")
        self.lamps_g = sb_lamps.group(reflect=False, passid=STAND, name="sc1_lamps")

    def render_frame(self, env, lt):
        t = lt
        parts = list(self.sky.emit(env))

        fg = self.field_ground.emit(env)
        if fg is not None:
            parts.append(fg)
        ff = self.field_flowers.emit(env)
        if ff is not None:
            parts.append(ff)

        if self.static_g and self.static_g.visible(env):
            parts.append(shade(env, self.static_g.lod(env), mirror=False))
        if self.lamps_g and self.lamps_g.visible(env):
            parts.append(shade(env, self.lamps_g.lod(env), mirror=False, grade=False))

        rng = np.random.default_rng(701)
        dyn = SB(rng)

        u_boy = smooth(0.0, 20.0, t)
        boy_z = 8.0 + u_boy * 13.5
        boy_x = float(_path_center_x(boy_z)) + 0.55
        boy_y = float(terrain_y(boy_x, boy_z))
        dx_dz = (float(_path_center_x(boy_z + 0.6)) - float(_path_center_x(boy_z - 0.6))) / 1.2
        boy_yaw = math.atan2(dx_dz, 1.0)

        kite_pos = np.array([
            boy_x - 2.2 + 0.9 * math.sin(t * 1.4),
            boy_y + 4.5 + 0.55 * math.cos(t * 1.9),
            boy_z + 4.2,
        ], np.float64)
        k_vec = kite_pos - np.array([boy_x, boy_y + 1.2, boy_z])
        hand = add_running_kite_boy(dyn, (boy_x, boy_y, boy_z), boy_yaw, t * 7.2, 1.0, k_vec)

        # Glowing diamond kite + fluttering crimson tail ribbons + taut white twine
        k_dir = norm3(k_vec)
        dyn.add([kite_pos], D=(0.25, 0.96, 0.1), L=1.05, W=0.88, spr=DAB, csh=C(218, 42, 46), cli=C(255, 112, 68), N=(0, 0.4, -0.9), smin=3.0)
        dyn.add([kite_pos + np.array([0.08, 0.08, -0.02])], D=(0.9, 0.3, 0.0), L=0.58, W=0.45, spr=DAB, csh=C(238, 186, 48), cli=C(255, 232, 92), N=(0, 0.4, -0.9), smin=2.6)
        for j in range(1, 7):
            u = j / 7.0
            tp = kite_pos - np.array([0.15 * u + 0.28 * math.sin(t * 3.8 - j * 0.7), 0.55 * j, -0.25 * u])
            rc = C(244, 62, 58) if j % 2 else C(255, 214, 72)
            dyn.add([tp], D=(0.3, -1.0, 0.0), L=0.42, W=0.14, spr=DASH + 2, csh=rc * 0.85, cli=rc, N=(0, 1, 0), smin=1.8)
        for s_i in range(1, 9):
            sp = hand + k_vec * (s_i / 9.0)
            dyn.add([sp], D=k_dir, L=float(np.linalg.norm(k_vec)) / 8.5, W=0.035, spr=DASH, csh=C(236, 228, 214), cli=C(255, 250, 240), N=(0, 1, 0), smin=1.2)

        # Bounding terrier beside the boy
        dog_z = boy_z - 1.35
        dog_x = boy_x - 1.45 + 0.25 * math.sin(t * 2.1)
        dog_y = float(terrain_y(dog_x, dog_z))
        add_galloping_dog(dyn, (dog_x, dog_y, dog_z), boy_yaw - 0.12, t * 8.6)

        # Two leisurely strollers with sunlit parasols near the top of the ridge
        for sx0, sz0, speed, dsh, dli, psh, pli in [
            (-5.5, 28.0, 0.32, C(168, 178, 214), C(248, 244, 240), C(236, 128, 148), C(255, 216, 224)),
            (-4.2, 29.0, 0.30, C(78, 118, 176), C(132, 176, 232), None, None),
        ]:
            sz = sz0 + t * speed
            sx = sx0 + 0.8 * math.sin(t * 0.25)
            sy = float(terrain_y(sx, sz))
            p_cols = (psh, pli) if psh is not None else None
            add_strolling_person(dyn, (sx, sy, sz), 0.15, t * 3.1, dsh, dli,
                                 hat_sh=C(208, 184, 128), hat_li=C(252, 232, 176), parasol_cols=p_cols)

        # Swallows soaring across upper blue sky
        for b_i in range(7):
            ang_b = t * 0.42 + b_i * 0.9
            bx = 6.0 + 18.0 * math.cos(ang_b)
            bz = 46.0 + 12.0 * math.sin(ang_b)
            by = 19.0 + 2.5 * math.sin(t * 1.1 + b_i)
            flap = 0.22 * math.sin(t * 9.5 + b_i * 1.7)
            dyn.add([[bx - 0.32, by + flap, bz], [bx + 0.32, by + flap, bz]],
                    D=(-0.7, 0.2, 0.0), L=0.65, W=0.14, spr=DASH + 2, csh=C(38, 42, 68), cli=C(82, 86, 118), N=(0, 1, 0), smin=1.8)

        dg = dyn.group(reflect=False, passid=STAND, name="sc1_actors")
        if dg and dg.visible(env):
            parts.append(shade(env, dg.lod(env), mirror=False))

        # Dreamy morning sunbeams & swirling orchard petals
        sb_beams = emit_sunbeams(
            env,
            origins=[(-18.0, 22.0, 36.0, 5.5, 32.0), (-8.0, 24.0, 44.0, 6.2, 34.0), (2.0, 23.0, 40.0, 4.8, 30.0)],
            dir_vec=(0.52, -0.78, -0.35),
            col=(1.08, 0.96, 0.72),
            alpha=0.11,
        )
        if sb_beams is not None:
            parts.append(sb_beams)

        petals = emit_drifting_petals(
            env, 34,
            pal_sh=[C(244, 156, 182), C(255, 228, 236), C(238, 64, 58)],
            pal_li=[C(255, 224, 236), C(255, 250, 252), C(255, 134, 96)],
            scale=0.20, height_range=(0.7, 5.2),
        )
        if petals is not None:
            parts.append(petals)

        return compose(parts)

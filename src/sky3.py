"""3D Spherical Sky Dome, Sculpted Cumulus Clouds, Sun Disc, Crescent Moon & Twinkling Stars."""
import math
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, LENS, WASH, jitter, mix, smooth
from anim.paint.world3 import SKY, _PASS


def sky_dir_rgb(env, dx, dy, dz):
    """Evaluate vivid Impressionist sky color along unit direction(s) (dx, dy, dz)."""
    L = env.L
    dy = np.asarray(dy, np.float32)
    dx = np.asarray(dx, np.float32)
    dz = np.asarray(dz, np.float32)
    el = np.clip(dy, 0.0, 1.0)

    t_low = smooth(0.0, 0.34, el)[:, None]
    t_high = smooth(0.26, 0.86, el)[:, None]
    col = L["hor"][None, :] * (1.0 - t_low) + L["mid"][None, :] * t_low
    col = col * (1.0 - t_high) + L["zen"][None, :] * t_high

    S = env.sun
    cos_s = np.clip(dx * float(S[0]) + dy * float(S[1]) + dz * float(S[2]), 0.0, 1.0)
    wide = (cos_s ** 3.0) * float(L.get("glow_wide", 0.16))
    tight = (cos_s ** 16.0) * float(L.get("glow_tight", 0.32))
    col = col + L["glow"][None, :] * (wide + tight)[:, None]
    return np.clip(col, 0.0, 1.18).astype(np.float32)


class SkyDome:
    """3D directional brushstroke sky dome, drifting cumulus banks, sun, crescent moon & stars."""

    def __init__(self, seed=7):
        rng = np.random.default_rng(seed)

        # 1A. Dense overlapping WASH sky undercoat (100% opaque sky)
        n_el, n_az = 22, 64
        els = np.linspace(-0.08, 1.02, n_el)
        azs = np.linspace(0.0, 2.0 * np.pi, n_az, endpoint=False)
        el_g, az_g = np.meshgrid(els, azs, indexing="ij")
        el_f = np.clip(el_g.ravel() + (rng.random(n_el * n_az) - 0.5) * 0.03, -0.08, 1.05)
        az_f = az_g.ravel() + (rng.random(n_el * n_az) - 0.5) * (2.0 * np.pi / n_az) * 0.5

        cy = np.sin(el_f * 1.48)
        rc = np.cos(el_f * 1.48)
        self.base_dir = np.stack([rc * np.cos(az_f), cy, rc * np.sin(az_f)], axis=1).astype(np.float64)
        self.base_rnd = rng.random((len(el_f), 4)).astype(np.float32)
        self.base_spr = (WASH + rng.integers(0, 4, len(el_f))).astype(np.int32)
        self.base_L = (360.0 + 130.0 * (1.0 - np.clip(el_f, 0.0, 1.0))).astype(np.float32)
        self.base_W = (240.0 + 70.0 * (1.0 - np.clip(el_f, 0.0, 1.0))).astype(np.float32)
        self.base_el = el_f.astype(np.float32)

        # 1B. Painterly broken-color Impressionist sky brushstrokes layered over the vault
        n_ov = 1150
        o_el = rng.uniform(-0.02, 0.96, n_ov)
        o_az = rng.uniform(0.0, 2.0 * np.pi, n_ov)
        ocy = np.sin(o_el * 1.48)
        orc = np.cos(o_el * 1.48)
        self.ov_dir = np.stack([orc * np.cos(o_az), ocy, orc * np.sin(o_az)], axis=1).astype(np.float64)
        self.ov_rnd = rng.random((n_ov, 4)).astype(np.float32)
        self.ov_spr = np.where(self.ov_rnd[:, 0] < 0.6, DASH + rng.integers(0, 8, n_ov), DAB + rng.integers(0, 4, n_ov)).astype(np.int32)
        self.ov_L = (120.0 + 110.0 * self.ov_rnd[:, 1]).astype(np.float32)
        self.ov_W = (46.0 + 38.0 * self.ov_rnd[:, 2]).astype(np.float32)
        self.ov_el = o_el.astype(np.float32)

        # 2. Feathered multi-puff 3D cumulus cloud clusters drifting across the sky dome
        n_banks = 38
        bank_az = rng.uniform(0.0, 2.0 * np.pi, n_banks)
        bank_el = rng.uniform(0.08, 0.44, n_banks)
        bank_speed = rng.uniform(0.0022, 0.0046, n_banks)
        puffs = []
        for i in range(n_banks):
            m = int(rng.integers(20, 32))
            daz = rng.normal(0.0, 0.045, m)
            delv = rng.normal(0.0, 0.018, m)
            top = np.clip(0.52 + delv / 0.026 + rng.normal(0.0, 0.14, m), 0.0, 1.0)
            for j in range(m):
                puffs.append((
                    bank_az[i] + daz[j],
                    np.clip(bank_el[i] + delv[j], 0.05, 0.62),
                    top[j],
                    bank_speed[i],
                    rng.uniform(0.55, 1.15),
                ))
        puffs = np.array(puffs, np.float64)
        self.cl_az0 = puffs[:, 0]
        self.cl_el = puffs[:, 1]
        self.cl_top = puffs[:, 2].astype(np.float32)
        self.cl_spd = puffs[:, 3]
        self.cl_sz = puffs[:, 4].astype(np.float32)
        self.cl_rnd = rng.random((len(puffs), 4)).astype(np.float32)
        self.cl_spr = np.where(self.cl_rnd[:, 0] < 0.45, LENS + rng.integers(0, 4, len(puffs)), SCUM + rng.integers(0, 4, len(puffs))).astype(np.int32)

        # 3. Twilight stars
        n_st = 140
        s_az = rng.uniform(0.0, 2.0 * np.pi, n_st)
        s_el = rng.uniform(0.14, 0.88, n_st)
        scy = np.sin(s_el * 1.45)
        src = np.cos(s_el * 1.45)
        self.st_dir = np.stack([src * np.cos(s_az), scy, src * np.sin(s_az)], axis=1).astype(np.float64)
        self.st_rnd = rng.random((n_st, 3)).astype(np.float32)

    def _proj_dir(self, env, dirs):
        vr = dirs @ env.rt
        vu = dirs @ env.up
        vf = dirs @ env.fw
        ok = vf > 0.08
        if not ok.any():
            return None
        idx = np.nonzero(ok)[0]
        vr, vu, vf = vr[idx], vu[idx], vf[idx]
        sc = env.f / vf
        x = 960.0 + vr * sc
        y = 540.0 - vu * sc
        return idx, x, y, vf

    def emit(self, env):
        L = env.L
        parts = []
        sc_f = env.f / 1840.0

        res = self._proj_dir(env, self.base_dir)
        if res is not None:
            idx, x, y, _ = res
            mg = self.base_L[idx] * 0.8 + 120.0
            vis = (x > -mg) & (x < 1920 + mg) & (y > -mg) & (y < 1080 + mg)
            if vis.any():
                ii = idx[vis]
                col = sky_dir_rgb(env, self.base_dir[ii, 0], self.base_dir[ii, 1], self.base_dir[ii, 2])
                col = jitter(col, self.base_rnd[ii], val=0.03, chroma=0.015)
                n = len(ii)
                parts.append(dict(
                    x=x[vis].astype(np.float32),
                    y=y[vis].astype(np.float32),
                    ang=((self.base_rnd[ii, 3] - 0.5) * 0.18).astype(np.float32),
                    L=(self.base_L[ii] * sc_f).astype(np.float32),
                    W=(self.base_W[ii] * sc_f).astype(np.float32),
                    spr=self.base_spr[ii],
                    rgb=np.clip(col, 0.0, 1.15).astype(np.float32),
                    a=np.ones(n, np.float32),
                    hb=np.full(n, 0.28, np.float32),
                    key=(SKY * _PASS + 40.0 + (1.0 - self.base_el[ii]) * 20.0).astype(np.float64),
                ))

        res_o = self._proj_dir(env, self.ov_dir)
        if res_o is not None:
            idx, x, y, _ = res_o
            mg = self.ov_L[idx] * 0.7 + 60.0
            vis = (x > -mg) & (x < 1920 + mg) & (y > -mg) & (y < 1080 + mg)
            if vis.any():
                ii = idx[vis]
                xv = x[vis]
                col = sky_dir_rgb(env, self.ov_dir[ii, 0], self.ov_dir[ii, 1], self.ov_dir[ii, 2])
                col = jitter(col, self.ov_rnd[ii], val=0.055, chroma=0.035)
                ang = (self.ov_rnd[ii, 3] - 0.5) * 0.40 + 0.09 * np.sin(xv * 0.0025)
                n = len(ii)
                parts.append(dict(
                    x=xv.astype(np.float32),
                    y=y[vis].astype(np.float32),
                    ang=ang.astype(np.float32),
                    L=(self.ov_L[ii] * sc_f).astype(np.float32),
                    W=(self.ov_W[ii] * sc_f).astype(np.float32),
                    spr=self.ov_spr[ii],
                    rgb=np.clip(col, 0.0, 1.15).astype(np.float32),
                    a=np.full(n, 0.65, np.float32),
                    hb=np.full(n, 0.42, np.float32),
                    key=(SKY * _PASS + 120.0 + (1.0 - self.ov_el[ii]) * 30.0).astype(np.float64),
                ))

        stars_amt = float(L.get("stars", 0.0))
        if stars_amt > 0.02:
            res_s = self._proj_dir(env, self.st_dir)
            if res_s is not None:
                idx, x, y, _ = res_s
                vis = (x > 10) & (x < 1910) & (y > 10) & (y < 860)
                if vis.any():
                    ii = idx[vis]
                    tw = 0.55 + 0.45 * np.sin(env.t * (2.4 + 3.2 * self.st_rnd[ii, 0]) + self.st_rnd[ii, 1] * 6.28)
                    sz = (7.5 + 7.5 * self.st_rnd[ii, 2]) * (0.65 + 0.35 * tw)
                    col = np.tile(np.array([1.14, 1.08, 0.88], np.float32), (len(ii), 1))
                    parts.append(dict(
                        x=x[vis].astype(np.float32),
                        y=y[vis].astype(np.float32),
                        ang=(self.st_rnd[ii, 1] * 3.14).astype(np.float32),
                        L=sz.astype(np.float32),
                        W=(sz * 0.78).astype(np.float32),
                        spr=np.full(len(ii), LENS, np.int32),
                        rgb=col,
                        a=(0.90 * stars_amt * tw).astype(np.float32),
                        hb=np.full(len(ii), 0.80, np.float32),
                        key=np.full(len(ii), SKY * _PASS + 250.0, np.float64),
                    ))

        cover = float(L.get("cover", 0.45))
        if cover > 0.02:
            az = self.cl_az0 + env.t * self.cl_spd
            el = self.cl_el
            cy = np.sin(el * 1.48)
            rc = np.cos(el * 1.48)
            cdir = np.stack([rc * np.cos(az), cy, rc * np.sin(az)], axis=1)
            res_c = self._proj_dir(env, cdir)
            if res_c is not None:
                idx, x, y, _ = res_c
                sz = self.cl_sz[idx] * (78.0 + 62.0 * (1.0 - el[idx])) * sc_f
                mg = sz * 0.8 + 60.0
                vis = (x > -mg) & (x < 1920 + mg) & (y > -mg) & (y < 1080 + mg)
                if vis.any():
                    ii = idx[vis]
                    sdot = np.clip((cdir[ii] @ env.sun) * 0.5 + 0.5, 0.0, 1.0)
                    lit_w = np.clip(0.32 * sdot + 0.68 * self.cl_top[ii], 0.0, 1.0)
                    col = mix(L["cloud_sh"][None, :], L["cloud_lit"][None, :], lit_w)
                    col = jitter(col, self.cl_rnd[ii], val=0.05, chroma=0.025)
                    hblend = smooth(0.18, 0.04, el[ii])[:, None] * 0.45
                    col = col * (1.0 - hblend) + L["hor"][None, :] * hblend
                    n = len(ii)
                    parts.append(dict(
                        x=x[vis].astype(np.float32),
                        y=y[vis].astype(np.float32),
                        ang=((self.cl_rnd[ii, 1] - 0.5) * 0.36).astype(np.float32),
                        L=sz[vis].astype(np.float32),
                        W=(sz[vis] * (0.48 + 0.18 * self.cl_rnd[ii, 2])).astype(np.float32),
                        spr=self.cl_spr[ii],
                        rgb=np.clip(col, 0.0, 1.15).astype(np.float32),
                        a=(float(L["cloud_op"]) * cover * (0.42 + 0.36 * self.cl_rnd[ii, 3])).astype(np.float32),
                        hb=np.full(n, 0.62, np.float32),
                        key=(SKY * _PASS + 400.0 + (1.0 - el[ii]) * 120.0 + self.cl_top[ii] * 25.0).astype(np.float64),
                    ))

        sd = float(L.get("sundisc", 0.0))
        if sd > 0.02:
            res_sun = self._proj_dir(env, env.sun[None, :])
            if res_sun is not None:
                _, sx, sy, _ = res_sun
                cx, cy = float(sx[0]), float(sy[0])
                if -280 < cx < 2200 and -280 < cy < 1360:
                    k = 12
                    ang = np.linspace(0.0, 2.0 * np.pi, k, endpoint=False, dtype=np.float32) + env.t * 0.06
                    rr = (46.0 + 14.0 * np.sin(np.arange(k) * 2.3)) * sc_f
                    parts.append(dict(
                        x=(cx + np.cos(ang) * rr).astype(np.float32),
                        y=(cy + np.sin(ang) * rr).astype(np.float32),
                        ang=(ang + 1.57).astype(np.float32),
                        L=np.full(k, 62.0 * sc_f, np.float32),
                        W=np.full(k, 30.0 * sc_f, np.float32),
                        spr=(SCUM + (np.arange(k) % 4)).astype(np.int32),
                        rgb=np.tile(L["glow"], (k, 1)).astype(np.float32),
                        a=np.full(k, 0.40 * sd, np.float32),
                        hb=np.full(k, 0.72, np.float32),
                        key=np.full(k, SKY * _PASS + 650.0, np.float64),
                    ))
                    ca = np.linspace(0.0, math.pi, 6, dtype=np.float32)
                    parts.append(dict(
                        x=(cx + np.cos(ca) * 7.0 * sc_f).astype(np.float32),
                        y=(cy + np.sin(ca) * 6.0 * sc_f).astype(np.float32),
                        ang=ca,
                        L=np.full(6, 58.0 * sc_f, np.float32),
                        W=np.full(6, 46.0 * sc_f, np.float32),
                        spr=np.full(6, DAB, np.int32),
                        rgb=np.tile(np.clip(L["sun_col"] * 1.15, 0.0, 1.18), (6, 1)).astype(np.float32),
                        a=np.full(6, 0.94 * sd, np.float32),
                        hb=np.full(6, 0.92, np.float32),
                        key=np.full(6, SKY * _PASS + 700.0, np.float64),
                    ))

        # Optional Crescent Moon (for Venice twilight finale)
        moon_amt = float(L.get("moon", 0.0))
        if moon_amt > 0.02:
            m_dir = np.array([-0.24, 0.28, 0.93], np.float64)
            m_dir /= np.linalg.norm(m_dir)
            res_m = self._proj_dir(env, m_dir[None, :])
            if res_m is not None:
                _, mx, my, _ = res_m
                cx, cy = float(mx[0]), float(my[0])
                if -200 < cx < 2120 and -200 < cy < 1200:
                    # Soft painterly moon aureole (concentric soft SCUM petals, zero boxy halo)
                    mk = 10
                    ma = np.linspace(0.0, 2.0 * np.pi, mk, endpoint=False, dtype=np.float32)
                    parts.append(dict(
                        x=(cx + np.cos(ma) * 16.0 * sc_f).astype(np.float32),
                        y=(cy + np.sin(ma) * 16.0 * sc_f).astype(np.float32),
                        ang=(ma + 1.57).astype(np.float32),
                        L=np.full(mk, 46.0 * sc_f, np.float32), W=np.full(mk, 32.0 * sc_f, np.float32),
                        spr=(SCUM + (np.arange(mk) % 4)).astype(np.int32),
                        rgb=np.tile(np.array([1.06, 0.94, 0.74], np.float32), (mk, 1)),
                        a=np.full(mk, 0.22 * moon_amt, np.float32),
                        hb=np.full(mk, 0.75, np.float32),
                        key=np.full(mk, SKY * _PASS + 730.0, np.float64),
                    ))
                    # Glowing crescent arc strokes
                    thetas = np.linspace(-1.05, 1.25, 9, dtype=np.float32)
                    px = cx + np.cos(thetas) * 19.0 * sc_f
                    py = cy + np.sin(thetas) * 19.0 * sc_f
                    parts.append(dict(
                        x=px, y=py, ang=thetas + 1.57,
                        L=np.full(9, 18.0 * sc_f, np.float32), W=np.full(9, 11.0 * sc_f, np.float32),
                        spr=np.full(9, DAB, np.int32),
                        rgb=np.tile(np.array([1.14, 1.08, 0.84], np.float32), (9, 1)),
                        a=np.full(9, 0.96 * moon_amt, np.float32),
                        hb=np.full(9, 0.92, np.float32),
                        key=np.full(9, SKY * _PASS + 760.0, np.float64),
                    ))

        return parts

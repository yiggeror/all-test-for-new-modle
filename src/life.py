"""Continuous Living Details across Depth Planes (0s - 96s):

- Scene 1 (Etretat): drifting salty sea-mist motes & chalk cliff fluff
- Scene 2 (Argenteuil): summer river swallows & cottonwood seeds
- Scene 3 (Giverny): drifting pink rose petals, golden pollen & fluttering white butterflies
- Scene 4 (Rouen): sunlit amber dust motes drifting across the plaza
- Scene 5 (Venice): softly blinking warm twilight fireflies rising above the lagoon
"""
import numpy as np
from engine import Batch, smooth, mix, C, pal, DAB, GLOW
from world import window


def make_wind_life(rng, n=130):
    ph = rng.random((n, 8)).astype(np.float32)
    kinds = [
        pal((246, 232, 222), (255, 246, 238), (222, 232, 240)),                 # 0 Etretat sea spray / fluff
        pal((255, 250, 238), (242, 246, 230), (255, 240, 206)),                 # 1 Argenteuil summer seeds
        pal((252, 184, 198), (244, 140, 166), (255, 224, 228), (254, 218, 118)),# 2 Giverny rose petals & pollen
        pal((255, 212, 134), (255, 182, 108), (248, 228, 178)),                 # 3 Rouen sunset motes
        pal((255, 226, 118), (246, 252, 152), (255, 192, 92)),                  # 4 Venice warm fireflies
    ]

    def actor(env):
        t = env.t
        d = env.d
        if t < 1.2:
            return None
        p = 0.60 + 1.50 * ph[:, 0]
        span = 2600.0
        speed = 55.0 + 140.0 * ph[:, 1]
        ox = (ph[:, 2] * span + speed * t + 115.0 * np.sin(t * 0.65 + 6.28 * ph[:, 3])) % span - span * 0.5
        Y = -80.0 - 590.0 * ph[:, 4] + 55.0 * np.sin(t * (0.55 + ph[:, 5]) + 6.28 * ph[:, 6]) + 22.0 * np.sin(t * 2.2 + 6.28 * ph[:, 7])
        sx = 960.0 + ox * (0.5 + 0.5 * p / 2.1)
        sy = env.hz + (Y + env.Hc) * (0.35 + 0.65 * p / 2.1) * 0.9

        k = int(np.clip(round(d), 0, 4))
        cidx = (ph[:, 3] * 3.99).astype(int)
        pal_k = kinds[k]
        cols = np.array([pal_k[c % len(pal_k)] for c in cidx], np.float32)

        tum = np.sin(t * (2.0 + 3.0 * ph[:, 5]) + 6.28 * ph[:, 6])
        size = (8.5 + 11.5 * ph[:, 7]) * (0.5 + 0.5 * p)
        gust = env.wind(env.camX + ox, 1.0)
        a = (0.35 + 0.65 * smooth(0.25, 0.72, gust)) * float(smooth(1.2, 2.8, t))

        # Scene 5 fireflies pulse softly with glow sprite
        is_ff = float(smooth(3.45, 3.95, d))
        if is_ff > 0.05:
            pulse = 0.35 + 0.65 * np.clip(np.sin(t * (2.4 + 2.5 * ph[:, 5]) + 6.28 * ph[:, 6]), 0.0, 1.0)
            a = a * (1.0 - is_ff + is_ff * pulse)
        spr = np.where(is_ff > 0.5, GLOW + (cidx % 4), DAB + (cidx % 6)).astype(np.int32)
        W_sz = np.where(is_ff > 0.5, size, size * (0.35 + 0.4 * np.abs(tum)))
        return Batch(sx, sy, tum * 1.4 + ph[:, 2] * 6.28, size, W_sz, spr, cols, 0.88 * a, 3.25 + p * 0.3, hb=0.45)

    return actor


def make_butterflies(rng, n=12):
    """Twelve cabbage-white & saffron butterflies weaving through Giverny flowerbeds."""
    ph = rng.random((n, 6)).astype(np.float32)

    def actor(env):
        w = float(window(env.d, 2.0, 0.85))
        if w <= 0.02:
            return None
        t = env.t
        bx, by, ba, bL, bW, bsp, bc = [], [], [], [], [], [], []
        for i in range(n):
            X = 9300.0 + ph[i, 0] * 4600.0 + 180.0 * np.sin(t * 0.42 + i * 1.7) + t * 18.0
            Y = -125.0 - 110.0 * ph[i, 1] + 45.0 * np.sin(t * 1.5 + i * 2.3)
            p = 0.65 + 0.75 * ph[i, 2]
            sx, sy, sc = env.project(X, Y, p)
            if not (-80 < sx < 2000):
                continue
            wing = np.abs(np.sin(t * (8.5 + 3.0 * ph[i, 3]) + i * 1.9))
            col = C(255, 250, 232) if i % 3 != 0 else C(255, 224, 118)
            sz = (15.0 + 5.0 * ph[i, 4]) * sc
            bx.extend([sx - 4.0 * sc * wing, sx + 4.0 * sc * wing])
            by.extend([sy, sy])
            ba.extend([-0.45 - 0.55 * wing, 0.45 + 0.55 * wing])
            bL.extend([sz, sz])
            bW.extend([sz * (0.45 + 0.35 * wing), sz * (0.45 + 0.35 * wing)])
            bsp.extend([DAB + (i % 4), DAB + ((i + 1) % 4)])
            bc.extend([col, col])
        if not bx:
            return None
        return Batch(np.array(bx, np.float32), np.array(by, np.float32), np.array(ba, np.float32),
                     np.array(bL, np.float32), np.array(bW, np.float32), np.array(bsp, np.int32),
                     np.array(bc, np.float32), 0.92 * w, 3.45, hb=0.55)

    return actor


def build(rng):
    return [], [make_wind_life(rng), make_butterflies(rng)]

"""Continuous 3D Multiplane World, Camera Spline, and Travelling Wind Field.

Five seamless Impressionist worlds along a single camera track (camX: 0 -> 20800):
  d = 0 : Etretat Morning Tide (Normandy chalk sea arch, surf, gulls)
  d = 1 : Regatta at Argenteuil (Seine sailboats, pennants, poplars)
  d = 2 : Giverny Flower Path (rose trellises, irises, pink house, butterflies)
  d = 3 : Rouen Cathedral (golden sunset facade melting in impasto light, doves)
  d = 4 : Venice Dusk — San Giorgio Maggiore (crimson-violet lagoon, gondolas, stars)
"""
import numpy as np
from engine import smooth, noise

FPS = 30
DUR = 96.0  # 2880 frames @ 30 fps

# Continuous world boundaries (wide overlap BW = 720 for natural cross-dissolve in space)
B1, B2, B3, B4 = 4200.0, 9000.0, 14000.0, 18400.0
BW = 720.0


def scene_of(u):
    u = np.asarray(u, np.float32)
    return (
        smooth(B1 - BW, B1 + BW, u)
        + smooth(B2 - BW, B2 + BW, u)
        + smooth(B3 - BW, B3 + BW, u)
        + smooth(B4 - BW, B4 + BW, u)
    )


def scene_coord(X, p, camX):
    """Near objects stay anchored in space; distant horizons smoothly transition with camera."""
    g = smooth(0.20, 0.68, p)
    return camX + (X - camX) * g


def window(d, k, soft=1.0):
    return np.clip(1.0 - np.abs(np.asarray(d, np.float32) - k) / soft, 0.0, 1.0)


def _pchip_slopes(x, y):
    """Fritsch-Carlson monotone piecewise cubic Hermite tangents (pure NumPy)."""
    n = len(x)
    h = np.diff(x)
    delta = np.diff(y) / h
    d = np.zeros(n, dtype=np.float64)
    for k in range(1, n - 1):
        if delta[k - 1] * delta[k] > 0.0:
            w1 = 2.0 * h[k] + h[k - 1]
            w2 = h[k] + 2.0 * h[k - 1]
            d[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])
    # Endpoint slopes
    d0 = ((2.0 * h[0] + h[1]) * delta[0] - h[0] * delta[1]) / (h[0] + h[1])
    if d0 * delta[0] <= 0.0:
        d0 = 0.0
    elif abs(d0) > 3.0 * abs(delta[0]):
        d0 = 3.0 * delta[0]
    dn = ((2.0 * h[-1] + h[-2]) * delta[-1] - h[-1] * delta[-2]) / (h[-1] + h[-2])
    if dn * delta[-1] <= 0.0:
        dn = 0.0
    elif abs(dn) > 3.0 * abs(delta[-1]):
        dn = 3.0 * delta[-1]
    d[0], d[-1] = d0, dn
    return d


def _eval_pchip(x, y, d, t):
    i = int(np.clip(np.searchsorted(x, t, side="right") - 1, 0, len(x) - 2))
    h = x[i + 1] - x[i]
    s = (t - x[i]) / h
    h00 = (1.0 + 2.0 * s) * (1.0 - s) ** 2
    h10 = s * (1.0 - s) ** 2
    h01 = s * s * (3.0 - 2.0 * s)
    h11 = s * s * (s - 1.0)
    return h00 * y[i] + h10 * h * d[i] + h01 * y[i + 1] + h11 * h * d[i + 1]


# Camera spline keyframes: t, camX, Hc (eye height), hz (horizon y), zoom
_KEYS = np.array([
    #  t      camX     Hc    hz    zoom
    [0.0,     0.0,   255,  450,  1.00],
    [4.5,   180.0,   255,  450,  1.02],
    [15.5, 2950.0,   265,  445,  1.04],
    [21.0, 4650.0,   315,  420,  1.00],
    [30.0, 6600.0,   325,  415,  1.02],
    [36.5, 8300.0,   330,  425,  1.00],
    [41.5, 9650.0,   365,  465,  1.00],
    [50.0, 11500.0,  375,  475,  1.03],
    [56.5, 13200.0,  365,  470,  1.00],
    [61.5, 14650.0,  340,  580,  1.00],
    [69.5, 16150.0,  330,  590,  1.05],
    [76.0, 17750.0,  310,  560,  1.00],
    [81.5, 19100.0,  275,  485,  1.00],
    [89.5, 20450.0,  270,  480,  1.06],
    [94.5, 20760.0,  270,  480,  1.09],
    [96.0, 20790.0,  270,  480,  1.10],
], dtype=np.float64)

_KT = _KEYS[:, 0]
_SLOPES = [_pchip_slopes(_KT, _KEYS[:, j]) for j in range(1, 5)]


class Env:
    def __init__(self, t):
        self.t = float(t)
        tt = min(max(self.t, 0.0), DUR)
        self.camX = float(_eval_pchip(_KT, _KEYS[:, 1], _SLOPES[0], tt))
        self.Hc = float(_eval_pchip(_KT, _KEYS[:, 2], _SLOPES[1], tt))
        self.hz = float(_eval_pchip(_KT, _KEYS[:, 3], _SLOPES[2], tt))
        self.zoom = float(_eval_pchip(_KT, _KEYS[:, 4], _SLOPES[3], tt))
        self.d = float(scene_of(self.camX))

    def wind(self, X, p=1.0):
        """Coherent travelling wind gusts (0..1) sweeping across grass, petals, flags & water."""
        t = self.t
        return (
            0.55 * noise(X / 1600.0 - t * 0.12, 0.4 + t * 0.015, 2)
            + 0.45 * noise(X / 480.0 - t * 0.28, 1.9, 3)
        )

    def project(self, X, Y, p):
        sc = p * self.zoom
        return 960.0 + (X - self.camX) * sc, self.hz + (Y + self.Hc) * sc, sc


class Set:
    """World-space stroke batch with frustum culling and dynamic per-frame shader."""

    def __init__(self, name, shader, X, Y, p, cam=(-1e9, 1e9), margin=280.0, **fields):
        self.name = name
        self.shader = shader
        self.X = np.asarray(X, np.float32)
        self.Y = np.asarray(Y, np.float32)
        n = len(self.X)
        self.p = np.broadcast_to(np.asarray(p, np.float32), (n,)).copy()
        self.cam = cam
        self.margin = margin
        self.f = {k: (np.asarray(v) if not np.isscalar(v) else v) for k, v in fields.items()}
        self.n = n

    def emit(self, env):
        if not (self.cam[0] <= env.camX <= self.cam[1]) or self.n == 0:
            return None
        sx, sy, sc = env.project(self.X, self.Y, self.p)
        m = self.margin
        idx = np.nonzero((sx > -m) & (sx < 1920.0 + m) & (sy > -m) & (sy < 1080.0 + m))[0]
        if len(idx) == 0:
            return None
        g = {
            k: (v[idx] if isinstance(v, np.ndarray) and v.shape[:1] == (self.n,) else v)
            for k, v in self.f.items()
        }
        return self.shader(env, self.X[idx], self.Y[idx], self.p[idx], sx[idx], sy[idx], sc[idx], g)


def flat(items):
    out = []
    for item in items:
        if item is None:
            continue
        if isinstance(item, (list, tuple)):
            out.extend(flat(item))
        else:
            out.append(item)
    return out


def rnd_fields(rng, n):
    return rng.random((n, 4)).astype(np.float32)


def jgrid(rng, x0, x1, y0, y1, cell, jit=0.88):
    nx = max(1, int((x1 - x0) / cell))
    ny = max(1, int((y1 - y0) / cell))
    gx, gy = np.meshgrid(np.arange(nx), np.arange(ny))
    x = x0 + (gx.ravel() + 0.5 + (rng.random(nx * ny) - 0.5) * jit) * (x1 - x0) / nx
    y = y0 + (gy.ravel() + 0.5 + (rng.random(nx * ny) - 0.5) * jit) * (y1 - y0) / ny
    perm = rng.permutation(nx * ny)
    return x[perm].astype(np.float32), y[perm].astype(np.float32)


def ground_rows(
    rng, X0, X1, pmin, pmax, base_len, aspect,
    cover=0.52, cover_y=0.55, size_pow=0.55, Hc_ref=320.0, min_len=20.0,
):
    """Receding perspective ground rows sorted far-to-near for dense painterly ground planes."""
    Xs, ps, Ls, Ws = [], [], [], []
    p = pmin
    while p < pmax:
        ls = max(base_len * (p ** size_pow), min_len)
        ws = ls / aspect
        dp = ws * cover_y / Hc_ref
        dX = ls * cover / p
        a = X0 - 1150.0 / p
        b = X1 + 1150.0 / p
        n = int((b - a) / dX) + 1
        x = a + (np.arange(n) + rng.random(n)) * dX
        Xs.append(x)
        ps.append(p + (rng.random(n) - 0.5) * dp * 1.5)
        Ls.append(np.full(n, ls / p) * np.clip(np.exp(rng.normal(0.0, 0.36, n)), 0.5, 2.3))
        Ws.append(np.full(n, ws / p) * (0.8 + 0.4 * rng.random(n)))
        p += dp
    X = np.concatenate(Xs).astype(np.float32)
    p = np.maximum(np.concatenate(ps), pmin * 0.6).astype(np.float32)
    L = np.concatenate(Ls).astype(np.float32)
    Wd = np.concatenate(Ws).astype(np.float32)
    order = np.argsort(p, kind="stable")
    return X[order], p[order], L[order], Wd[order]

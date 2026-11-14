"""Pure-NumPy + Native C++17 Oil Brush Engine.

Every element on screen is projected as world-space impasto brush strokes,
sorted back-to-front by depth order, rasterized via build/libbrush.so with
multi-level bristle-streaked alpha & paint-thickness sprites, then shaded
with directional Sobel relief, flax canvas weave, optical bloom, and vignette.
"""
import ctypes
import os
import subprocess
import numpy as np

W0, H0 = 1920, 1080
CANVAS = np.array([232, 222, 202], np.float32) / 255.0

# --------------------------------------------------------------------------- FFT helpers (pure NumPy)
def _gauss_1d(arr, sigma, axis=-1, mode="wrap"):
    if sigma <= 0.15:
        return arr.astype(np.float32, copy=True)
    n = arr.shape[axis]
    if mode == "reflect":
        pad = int(np.ceil(sigma * 3.0))
        pad_width = [(0, 0)] * arr.ndim
        pad_width[axis] = (pad, pad)
        work = np.pad(arr, pad_width, mode="reflect")
        m = work.shape[axis]
        freq = np.fft.rfftfreq(m)
        kern = np.exp(-2.0 * (np.pi * sigma * freq) ** 2)
        shape = [1] * work.ndim
        shape[axis] = len(kern)
        out = np.fft.irfft(np.fft.rfft(work, axis=axis) * kern.reshape(shape), n=m, axis=axis)
        sl = [slice(None)] * arr.ndim
        sl[axis] = slice(pad, pad + n)
        return out[tuple(sl)].astype(np.float32)
    freq = np.fft.rfftfreq(n)
    kern = np.exp(-2.0 * (np.pi * sigma * freq) ** 2)
    shape = [1] * arr.ndim
    shape[axis] = len(kern)
    return np.fft.irfft(np.fft.rfft(arr, axis=axis) * kern.reshape(shape), n=n, axis=axis).astype(np.float32)


def _gauss_2d(arr, sigmas, mode="wrap"):
    sy, sx = sigmas
    out = _gauss_1d(arr, sx, axis=1, mode=mode)
    return _gauss_1d(out, sy, axis=0, mode=mode)


# --------------------------------------------------------------------------- Tileable 1/f noise
_NS = 1024
_NCELL = 128.0


def _make_noise(seed, beta=1.9, lowcut=6.0):
    rng = np.random.default_rng(seed)
    f = np.fft.fftfreq(_NS) * _NS
    fx, fy = np.meshgrid(f, f)
    r = np.sqrt(fx * fx + fy * fy)
    amp = np.where(r >= lowcut, 1.0 / np.maximum(r, 1.0) ** beta, 0.0)
    ph = rng.uniform(0.0, 2.0 * np.pi, (_NS, _NS))
    img = np.real(np.fft.ifft2(amp * np.exp(1j * ph)))
    flat = img.ravel()
    order = flat.argsort()
    ranks = np.empty(flat.size, np.float32)
    ranks[order] = np.linspace(0.0, 1.0, flat.size, dtype=np.float32)
    return ranks.reshape(_NS, _NS)


NOISE = [_make_noise(101 + i) for i in range(4)]


def noise(x, y, ch=0):
    """Tileable smooth fbm-ranked noise in [0, 1]. Feature scale ~ 1.0 world unit."""
    tex = NOISE[ch % 4]
    fx = np.mod(np.asarray(x, np.float64) * _NCELL, _NS)
    fy = np.mod(np.asarray(y, np.float64) * _NCELL, _NS)
    x0 = fx.astype(np.int64) % _NS
    y0 = fy.astype(np.int64) % _NS
    tx = (fx - np.floor(fx)).astype(np.float32)
    ty = (fy - np.floor(fy)).astype(np.float32)
    x1 = (x0 + 1) % _NS
    y1 = (y0 + 1) % _NS
    a = tex[y0, x0] * (1.0 - tx) + tex[y0, x1] * tx
    b = tex[y1, x0] * (1.0 - tx) + tex[y1, x1] * tx
    return a * (1.0 - ty) + b * ty


# --------------------------------------------------------------------------- Color & math helpers
def smooth(a, b, x):
    t = np.clip((np.asarray(x, np.float32) - a) / (b - a + 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def mix(a, b, w):
    w = np.asarray(w, np.float32)
    if w.ndim == 1 and np.ndim(a) + np.ndim(b) >= 2:
        w = w[:, None]
    return a * (1.0 - w) + b * w


def C(*rgb):
    return np.array(rgb, np.float32) / 255.0


def pal(*cols):
    return np.array(cols, np.float32) / 255.0


def pick(palette, rnd, weights=None):
    """Broken-color palette selection per stroke."""
    k = len(palette)
    if weights is None:
        idx = np.minimum((rnd * k).astype(np.int32), k - 1)
    else:
        cw = np.cumsum(np.asarray(weights, np.float64))
        cw /= cw[-1]
        idx = np.minimum(np.searchsorted(cw, rnd), k - 1)
    return palette[idx]


def ramp(stops, x):
    xs = np.array([s[0] for s in stops], np.float32)
    cs = np.array([s[1] for s in stops], np.float32) / 255.0
    x = np.asarray(x, np.float32)
    out = np.empty(x.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(x, xs, cs[:, c])
    return out


def jitter(rgb, rnd, val=0.06, chroma=0.035):
    r1, r2, r3 = rnd[:, 0], rnd[:, 1], rnd[:, 2]
    out = rgb * (1.0 + (r1[:, None] - 0.5) * 2.0 * val)
    out[:, 0] += (r2 - 0.5) * 2.0 * chroma
    out[:, 1] += (r3 - 0.5) * chroma
    out[:, 2] -= (r2 - 0.5) * 2.0 * chroma
    return np.clip(out, 0.0, 1.15)


# --------------------------------------------------------------------------- Procedural Oil Brush Sprites
SW, SH = 192, 64
DASH, DAB, SCUM, GLOW = 0, 8, 14, 20
NSPR = 24


def _bristles(rng, streaks, along):
    g = rng.standard_normal((SH, SW)).astype(np.float32)
    g = _gauss_2d(g, (SH / streaks / 2.3, SW * along), mode="reflect")
    return g / (g.std() + 1e-9)


def _n1(rng, n, sigma):
    g = _gauss_1d(rng.standard_normal(n).astype(np.float32), sigma, axis=0, mode="wrap")
    return g / (g.std() + 1e-9)


def _downsample_half(arr):
    # Box-filter 2x2 downsample for crisp mip-maps without aliasing
    k, h, w = arr.shape
    return arr.reshape(k, h // 2, 2, w // 2, 2).mean(axis=(2, 4)).astype(np.float32)


def _build_sprites(seed=37):
    rng = np.random.default_rng(seed)
    u = np.linspace(-1.0, 1.0, SW, dtype=np.float32)[None, :]
    v = np.linspace(-1.0, 1.0, SH, dtype=np.float32)[:, None]
    A = np.zeros((NSPR, SH, SW), np.float32)
    T = np.zeros((NSPR, SH, SW), np.float32)

    for k in range(NSPR):
        br = _bristles(rng, rng.uniform(10.0, 16.0), rng.uniform(0.09, 0.21))
        fine = _bristles(rng, 28.0, 0.045)
        e_top = 1.0 + 0.11 * _n1(rng, SW, 9.0)[None, :]
        e_bot = 1.0 + 0.11 * _n1(rng, SW, 9.0)[None, :]
        edge = np.where(v < 0.0, e_top, e_bot)
        bend = 0.08 * np.sin(u * np.pi * 0.5) * rng.uniform(-1.0, 1.0)

        if k < DAB:
            # Loaded oil dash with dry-brush tail taper
            p_pow = rng.uniform(2.3, 3.8)
            taper = rng.uniform(0.05, 0.35)
            env = np.clip(1.0 - np.abs(u) ** p_pow, 0.0, 1.0) ** 0.55
            env *= (1.0 - taper * (u * 0.5 + 0.5)) * 0.94
            vy = np.abs(v - bend) / (0.84 * edge)
            cross = np.clip(1.0 - vy ** 2.6, 0.0, 1.0) ** 0.72
            dry = np.clip(0.82 + 0.28 * br + 0.10 * fine - 0.30 * smooth(0.25, 0.98, u), 0.0, 1.0)
            a = np.clip(env * cross * dry, 0.0, 1.0)
            t = (0.55 * br + 0.25 * fine) * (0.4 + 0.6 * cross) + 0.30 * (1.0 - vy) - 0.18 * u
        elif k < SCUM:
            # Short comma / petal / architectural impasto dab
            r2 = (u / 0.92) ** 2 + ((v - bend * 0.6) / (0.82 * edge)) ** 2
            base = np.clip(1.0 - r2, 0.0, 1.0) ** 0.55
            a = np.clip(base * (0.84 + 0.22 * br + 0.10 * fine), 0.0, 1.0)
            # Thick pigment rim + bristle valleys
            rim = np.exp(-((np.sqrt(np.maximum(r2, 1e-6)) - 0.78) / 0.18) ** 2)
            t = 0.45 * br + 0.22 * fine + 0.42 * rim
        elif k < GLOW:
            # Broken dry-brush scumble (foliage/clouds/mist texture)
            r2 = (u / 0.96) ** 2 + (v / (0.86 * edge)) ** 2
            base = np.clip(1.0 - r2, 0.0, 1.0) ** 0.85
            speck = _gauss_2d(rng.standard_normal((SH, SW)).astype(np.float32), (2.2, 4.5), mode="reflect")
            speck /= speck.std() + 1e-9
            a = np.clip(base * smooth(-0.35, 0.65, 0.55 * br + 0.45 * speck + 0.35 * base), 0.0, 1.0) * 0.85
            t = 0.5 * br + 0.35 * speck
        else:
            # Feathered atmospheric glow / mist / halo dab
            r2 = (u / 0.98) ** 2 + (v / 0.94) ** 2
            a = np.exp(-2.6 * r2) * np.clip(1.0 - r2, 0.0, 1.0) ** 0.45
            t = 0.12 * br

        A[k] = a.astype(np.float32)
        T[k] = np.clip(t, -1.6, 1.6).astype(np.float32)

    mipsA = [A]
    mipsT = [T]
    for _ in range(3):
        mipsA.append(_downsample_half(mipsA[-1]))
        mipsT.append(_downsample_half(mipsT[-1]))
    return mipsA, mipsT


SPR_A, SPR_T = _build_sprites()


# --------------------------------------------------------------------------- Load compiled C++17 library
def _load_native():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    so_path = os.path.join(root, "build", "libbrush.so")
    cpp_path = os.path.join(root, "src", "brush_native.cpp")
    if not os.path.exists(so_path) or os.path.getmtime(cpp_path) > os.path.getmtime(so_path):
        os.makedirs(os.path.dirname(so_path), exist_ok=True)
        subprocess.check_call(
            ["g++", "-O3", "-march=native", "-ffast-math", "-funroll-loops", "-std=c++17", "-pthread", "-shared", "-fPIC", cpp_path, "-o", so_path]
        )
    lib = ctypes.CDLL(so_path)
    c_fp = ctypes.POINTER(ctypes.c_float)
    c_ip = ctypes.POINTER(ctypes.c_int32)
    c_u8p = ctypes.POINTER(ctypes.c_uint8)
    lib.render_frame_native.argtypes = [
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        c_fp, c_fp, c_fp, c_fp,
        c_fp, c_fp, c_fp, c_fp,
        ctypes.c_int,
        c_fp, c_fp, c_fp, c_fp, c_fp, c_ip,
        c_fp, c_fp, c_fp, c_fp,
        c_fp, c_fp, c_fp, c_fp,
        ctypes.c_float, ctypes.c_float, ctypes.c_float,
        ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
        c_u8p,
    ]
    lib.render_frame_native.restype = None
    return lib


_LIB = _load_native()


# --------------------------------------------------------------------------- Batch & Canvas weave cache
class Batch:
    __slots__ = ("x", "y", "ang", "L", "W", "spr", "rgb", "a", "hb", "zo")

    def __init__(self, x, y, ang, L, W, spr, rgb, a, zo, hb=0.72):
        n = len(x)
        self.x = np.asarray(x, np.float32)
        self.y = np.asarray(y, np.float32)
        self.ang = np.broadcast_to(np.asarray(ang, np.float32), (n,))
        self.L = np.broadcast_to(np.asarray(L, np.float32), (n,))
        self.W = np.broadcast_to(np.asarray(W, np.float32), (n,))
        self.spr = np.broadcast_to(np.asarray(spr, np.int32), (n,))
        rgb_arr = np.asarray(rgb, np.float32)
        if rgb_arr.ndim == 1:
            rgb_arr = np.broadcast_to(rgb_arr[None, :], (n, 3))
        self.rgb = rgb_arr
        self.a = np.broadcast_to(np.asarray(a, np.float32), (n,))
        self.hb = np.broadcast_to(np.asarray(hb, np.float32), (n,))
        self.zo = np.broadcast_to(np.asarray(zo, np.float32), (n,))


_WEAVE = {}


def _weave(H, W):
    key = (H, W)
    if key not in _WEAVE:
        rs = H / float(H0)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        per = 5.0 * max(rs, 0.5)
        wv = (
            0.5 * np.sin(xx * 2.0 * np.pi / per) * (0.6 + 0.4 * np.sin(yy * 2.0 * np.pi / per / 2.0))
            + 0.5 * np.sin(yy * 2.0 * np.pi / per) * (0.6 + 0.4 * np.sin(xx * 2.0 * np.pi / per / 2.0))
        ).astype(np.float32)
        rng = np.random.default_rng(17)
        gr = _gauss_2d(rng.standard_normal((H, W)).astype(np.float32), (0.8 * max(rs, 0.5), 0.8 * max(rs, 0.5)), mode="wrap")
        gr = (gr / (gr.std() + 1e-9)).astype(np.float32)
        lo = _gauss_2d(rng.standard_normal((H, W)).astype(np.float32), (38.0 * rs, 38.0 * rs), mode="wrap")
        lo = (lo / (lo.std() + 1e-9)).astype(np.float32)
        vig = (1.0 - 0.15 * (((xx / W - 0.5) * 2.0) ** 2 + ((yy / H - 0.5) * 2.0) ** 2) ** 1.25).astype(np.float32)
        _WEAVE[key] = (
            np.ascontiguousarray(wv),
            np.ascontiguousarray(gr),
            np.ascontiguousarray(lo),
            np.ascontiguousarray(vig),
        )
    return _WEAVE[key]


def render(batches, H=1080, tone_amt=0.09, relief=1.05, bloom=0.14, fade=0.0):
    W = H * W0 // H0
    rs = np.float32(H / float(H0))
    wv, gr, lo, vig = _weave(H, W)

    bs = [b for b in batches if b is not None and len(b.x) > 0]
    if bs:
        sx = np.ascontiguousarray(np.concatenate([b.x for b in bs]) * rs, dtype=np.float32)
        sy = np.ascontiguousarray(np.concatenate([b.y for b in bs]) * rs, dtype=np.float32)
        ang = np.ascontiguousarray(np.concatenate([b.ang for b in bs]), dtype=np.float32)
        L = np.ascontiguousarray(np.concatenate([b.L for b in bs]) * rs, dtype=np.float32)
        Wd = np.ascontiguousarray(np.concatenate([b.W for b in bs]) * rs, dtype=np.float32)
        spr = np.ascontiguousarray(np.concatenate([b.spr for b in bs]), dtype=np.int32)
        rgb = np.ascontiguousarray(np.concatenate([b.rgb for b in bs]), dtype=np.float32)
        alp = np.ascontiguousarray(np.concatenate([b.a for b in bs]), dtype=np.float32)
        hb = np.ascontiguousarray(np.concatenate([b.hb for b in bs]), dtype=np.float32)
        zo = np.ascontiguousarray(np.concatenate([b.zo for b in bs]), dtype=np.float32)
        N = len(sx)
    else:
        empty_f = np.zeros(1, dtype=np.float32)
        empty_i = np.zeros(1, dtype=np.int32)
        sx = sy = ang = L = Wd = rgb = alp = hb = zo = empty_f
        spr = empty_i
        N = 0

    out = np.empty((H, W, 3), dtype=np.uint8)
    fp = lambda a: a.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    ip = lambda a: a.ctypes.data_as(ctypes.POINTER(ctypes.c_int32))
    u8p = lambda a: a.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))

    _LIB.render_frame_native(
        W, H, NSPR, SW, SH,
        fp(SPR_A[0]), fp(SPR_A[1]), fp(SPR_A[2]), fp(SPR_A[3]),
        fp(SPR_T[0]), fp(SPR_T[1]), fp(SPR_T[2]), fp(SPR_T[3]),
        N,
        fp(sx), fp(sy), fp(ang), fp(L), fp(Wd), ip(spr),
        fp(rgb), fp(alp), fp(hb), fp(zo),
        fp(wv), fp(gr), fp(lo), fp(vig),
        float(CANVAS[0]), float(CANVAS[1]), float(CANVAS[2]),
        float(tone_amt), float(relief), float(bloom), float(fade),
        u8p(out),
    )
    return out

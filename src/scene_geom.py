"""3D terrain, curved Seine river channel, and bank geometry for Un Dimanche sur la Seine.

World coordinate conventions:
  Y = 0.0 : Seine water plane
  Z       : River valley axis (-100 .. +600)
  X       : Cross-valley axis (left bank poppy hill < 0, right bank towpath/cafe > 0)
"""
import numpy as np


def _sstep(a, b, x):
    t = np.clip((np.asarray(x, np.float64) - a) / (b - a + 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def river_x(z):
    """Center X of the Seine river channel along valley axis Z."""
    z = np.asarray(z, np.float64)
    return 24.0 * np.cos(z * 0.0085) + 8.0 * np.sin(z * 0.0038 + 0.4)


def river_dx_dz(z):
    """Derivative d(river_x)/dz for tangent orientation along the river."""
    z = np.asarray(z, np.float64)
    return -24.0 * 0.0085 * np.sin(z * 0.0085) + 8.0 * 0.0038 * np.cos(z * 0.0038 + 0.4)


def river_hw(z):
    """Half-width of the Seine water channel (wider at regatta basin Z ~ 260..420)."""
    z = np.asarray(z, np.float64)
    basin = np.exp(-((z - 330.0) / 130.0) ** 2)
    return 40.0 + 16.0 * basin


def bank_signed_dist(x, z):
    """Distance outward from the nearest riverbank (< 0 inside water, > 0 on land)."""
    x = np.asarray(x, np.float64)
    z = np.asarray(z, np.float64)
    return np.abs(x - river_x(z)) - river_hw(z)


def terrain_y(x, z):
    """Smooth continuous 3D height of banks, poppy hillside, towpath, and far valley ridges."""
    x = np.asarray(x, np.float64)
    z = np.asarray(z, np.float64)
    cx = river_x(z)
    hw = river_hw(z)
    dx = x - cx
    sd = np.abs(dx) - hw  # > 0 on land, <= 0 underwater

    # Gentle, completely smooth riverbank rise (no cliff jump at sd=0!)
    bank = 0.95 * _sstep(-0.8, 11.0, sd)

    # Left bank poppy hillside (smooth gentle climb inland Z = -60 .. +175)
    left_mask = _sstep(4.0, -4.0, dx) * _sstep(190.0, 125.0, z)
    hill_dist = np.maximum(-dx - hw - 3.0, 0.0)
    poppy_hill = left_mask * (
        0.16 * np.minimum(hill_dist, 72.0)
        + 1.8 * np.sin(x * 0.05 + 0.4) * np.cos(z * 0.03) * _sstep(6.0, 28.0, hill_dist)
    )

    # Right bank gentle towpath terrace & Guinguette quay apron
    right_mask = _sstep(-4.0, 4.0, dx)
    rdist = np.maximum(dx - hw, 0.0)
    quay_zone = _sstep(350.0, 375.0, z) * _sstep(465.0, 440.0, z)
    flat_margin = 24.0 + 26.0 * quay_zone
    right_rise = right_mask * 0.12 * np.maximum(rdist - flat_margin, 0.0)

    # Gentle flattening near viaduct abutments (Z ~ 215)
    viaduct_flat = 1.0 - 0.80 * np.exp(-((z - 215.0) / 16.0) ** 2) * _sstep(35.0, 14.0, sd)

    # Far valley hills framing both horizons (|sd| > 55)
    far_ridge = _sstep(55.0, 195.0, sd) * (
        16.0 + 6.5 * np.sin(z * 0.014 + 0.7) + 3.5 * np.cos(x * 0.021)
    ) * (1.0 - 0.65 * quay_zone * _sstep(65.0, 35.0, rdist))

    # Smooth underwater slope
    bed = -0.9 * _sstep(0.5, -7.0, sd)

    land_y = bank + poppy_hill * viaduct_flat + right_rise + far_ridge
    return np.where(sd > 0.0, land_y, land_y * _sstep(-1.0, 0.5, sd) + bed)


def terrain_normal(x, z, eps=0.6):
    """Finite-difference surface normal (N_x, N_y, N_z) for sunlight shading."""
    x = np.asarray(x, np.float64)
    z = np.asarray(z, np.float64)
    yx = (terrain_y(x + eps, z) - terrain_y(x - eps, z)) / (2.0 * eps)
    yz = (terrain_y(x, z + eps) - terrain_y(x, z - eps)) / (2.0 * eps)
    n = np.stack([-yx, np.ones_like(yx), -yz], axis=-1)
    return n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12)

"""Articulated 3D Impressionist character & animal stroke builders.

All characters emit 3D world-space brushstroke records into anim.paint.world3.SB
so they participate seamlessly in 3D perspective, sunlight/shade grading, aerial haze,
and broken water reflections.
"""
import math
import numpy as np
from anim.paint.engine import DASH, DAB, SCUM, C


def _rot_yaw(v, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c], np.float64)


def _limb(sb, p0, p1, w, csh, cli, spr=DASH + 1, smin=2.4):
    p0 = np.asarray(p0, np.float64)
    p1 = np.asarray(p1, np.float64)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    if L < 1e-4:
        return
    dn = d / L
    mid = (p0 + p1) * 0.5
    # Two slightly overlapping dabs for tactile painterly silhouette
    sb.add(
        [mid - dn * (L * 0.16), mid + dn * (L * 0.16)],
        D=dn, L=L * 0.78, W=w, spr=spr, csh=csh, cli=cli, N=(0.3, 0.85, 0.3), smin=smin,
    )


def add_running_kite_boy(sb, base_pos, yaw, phase, wind_val, kite_dir_world):
    """Articulated 3D boy in straw boater & sailor suit running while flying a kite."""
    x0, y0, z0 = base_pos
    fwd = np.array([math.sin(yaw), 0.0, math.cos(yaw)], np.float64)
    right = np.array([math.cos(yaw), 0.0, -math.sin(yaw)], np.float64)
    up = np.array([0.0, 1.0, 0.0], np.float64)

    bob = 0.085 * abs(math.sin(phase))
    lean = 0.22  # energetic forward sprint tilt
    hip_c = np.array([x0, y0 + 0.72 + bob, z0], np.float64)
    sh_c = hip_c + up * 0.44 + fwd * lean

    # Articulated legs (thigh + shin)
    skin_sh = C(186, 128, 108)
    skin_li = C(244, 198, 166)
    pants_sh = C(54, 72, 118)
    pants_li = C(98, 126, 186)
    shirt_sh = C(178, 184, 206)
    shirt_li = C(250, 246, 236)
    hat_sh = C(192, 162, 112)
    hat_li = C(248, 224, 164)

    for side, ph_off in ((-1.0, 0.0), (1.0, math.pi)):
        ang = phase + ph_off
        hip = hip_c + right * (side * 0.11)
        thigh_a = 0.65 * math.sin(ang)
        knee = hip + fwd * (0.36 * math.sin(thigh_a)) - up * (0.36 * math.cos(thigh_a))
        shin_a = thigh_a - max(0.0, -math.cos(ang)) * 0.95 - 0.15
        foot = knee + fwd * (0.36 * math.sin(shin_a)) - up * (0.36 * math.cos(shin_a))
        _limb(sb, hip, knee, 0.14, pants_sh, pants_li, spr=DASH + 2)
        _limb(sb, knee, foot, 0.11, skin_sh, skin_li, spr=DASH + 1)
        sb.add([foot + fwd * 0.05], D=fwd, L=0.22, W=0.11, spr=DAB, csh=C(52, 44, 48), cli=C(88, 72, 66), N=(0, 1, 0), smin=2.2)

    # Torso + blue sailor collar
    _limb(sb, hip_c, sh_c, 0.28, shirt_sh, shirt_li, spr=DAB + 1)
    sb.add([sh_c + fwd * 0.03 - up * 0.05], D=right, L=0.34, W=0.16, spr=DAB, csh=C(42, 74, 146), cli=C(72, 118, 210), N=up, smin=2.2)

    # Left arm pumping naturally
    l_sh = sh_c - right * 0.16
    la = -0.6 * math.sin(phase)
    l_elb = l_sh + fwd * (0.24 * math.sin(la)) - up * (0.24 * math.cos(la))
    l_hnd = l_elb + fwd * (0.22 * math.sin(la + 0.7)) - up * (0.22 * math.cos(la + 0.7))
    _limb(sb, l_sh, l_elb, 0.11, shirt_sh, shirt_li)
    _limb(sb, l_elb, l_hnd, 0.09, skin_sh, skin_li)

    # Right arm raised holding kite reel toward kite_dir_world!
    r_sh = sh_c + right * 0.16
    kdir = np.asarray(kite_dir_world, np.float64)
    kdir /= np.linalg.norm(kdir) + 1e-9
    r_elb = r_sh + kdir * 0.25 + right * 0.05
    r_hnd = r_elb + kdir * 0.26
    _limb(sb, r_sh, r_elb, 0.11, shirt_sh, shirt_li)
    _limb(sb, r_elb, r_hnd, 0.09, skin_sh, skin_li)

    # Head tilted slightly up toward kite + Straw boater with red ribbon fluttering
    head = sh_c + up * 0.22 + fwd * 0.05
    sb.add([head], D=up, L=0.25, W=0.22, spr=DAB + 2, csh=skin_sh, cli=skin_li, N=up, smin=2.0)
    hat_c = head + up * 0.12 - fwd * 0.02
    sb.add([hat_c], D=fwd, L=0.44, W=0.38, spr=DAB, csh=hat_sh, cli=hat_li, N=up, smin=2.0)
    # Fluttering crimson hat ribbon
    rib_p = hat_c - fwd * 0.22 - right * (0.08 * math.sin(phase * 1.3 + wind_val * 3.0))
    sb.add([rib_p], D=-fwd + up * 0.18, L=0.32, W=0.06, spr=DASH + 3, csh=C(168, 36, 44), cli=C(238, 64, 62), N=up, smin=1.8)

    return r_hnd


def add_galloping_dog(sb, base_pos, yaw, phase):
    """Bounding small white-and-chestnut terrier running alongside the boy."""
    x0, y0, z0 = base_pos
    fwd = np.array([math.sin(yaw), 0.0, math.cos(yaw)], np.float64)
    up = np.array([0.0, 1.0, 0.0], np.float64)
    right = np.array([math.cos(yaw), 0.0, -math.sin(yaw)], np.float64)

    hop = 0.14 * max(0.0, math.sin(phase))
    pitch = 0.26 * math.cos(phase)
    body_c = np.array([x0, y0 + 0.34 + hop, z0], np.float64)
    chest = body_c + fwd * 0.22 + up * (0.12 * pitch)
    rump = body_c - fwd * 0.22 - up * (0.12 * pitch)

    w_sh = C(188, 186, 198)
    w_li = C(252, 248, 238)
    spot_sh = C(124, 72, 48)
    spot_li = C(194, 122, 74)

    _limb(sb, rump, chest, 0.22, w_sh, w_li, spr=DAB + 1, smin=2.0)
    sb.add([body_c + right * 0.06 + up * 0.04], D=fwd, L=0.22, W=0.16, spr=DAB, csh=spot_sh, cli=spot_li, N=up, smin=1.8)
    # Head & ears
    head = chest + fwd * 0.16 + up * 0.18
    sb.add([head], D=fwd, L=0.24, W=0.18, spr=DAB + 2, csh=w_sh, cli=w_li, N=up, smin=1.8)
    sb.add([head - fwd * 0.04 + up * 0.10], D=up - fwd * 0.3, L=0.14, W=0.09, spr=DAB, csh=spot_sh, cli=spot_li, N=up, smin=1.6)
    # Wagging tail
    wag = 0.35 * math.sin(phase * 2.2)
    tail_end = rump - fwd * 0.16 + up * 0.22 + right * wag
    _limb(sb, rump, tail_end, 0.07, w_sh, w_li, smin=1.6)
    # 4 bounding legs
    for is_front, ox in ((True, 0.0), (False, math.pi * 0.7)):
        root = chest if is_front else rump
        for side in (-1.0, 1.0):
            s_ph = phase + ox + (0.25 if side > 0 else 0.0)
            paw = root + right * (side * 0.08) + fwd * (0.22 * math.sin(s_ph)) - up * (0.26 - 0.10 * math.cos(s_ph))
            _limb(sb, root + right * (side * 0.07), paw, 0.08, w_sh, w_li, smin=1.6)


def add_strolling_person(sb, base_pos, yaw, phase, dress_sh, dress_li, hat_sh=None, hat_li=None, parasol_cols=None):
    """Sunday promenader with articulated stride and optional glowing Impressionist parasol."""
    x0, y0, z0 = base_pos
    fwd = np.array([math.sin(yaw), 0.0, math.cos(yaw)], np.float64)
    right = np.array([math.cos(yaw), 0.0, -math.sin(yaw)], np.float64)
    up = np.array([0.0, 1.0, 0.0], np.float64)

    bob = 0.03 * abs(math.sin(phase))
    hip = np.array([x0, y0 + 0.85 + bob, z0], np.float64)
    sh = hip + up * 0.50

    skin_sh = C(182, 132, 114)
    skin_li = C(244, 202, 174)

    # Flowing dress/coat skirt + stride legs
    for side, ph_off in ((-1.0, 0.0), (1.0, math.pi)):
        ang = phase + ph_off
        foot = np.array([x0, y0 + 0.06, z0]) + right * (side * 0.10) + fwd * (0.25 * math.sin(ang)) + up * max(0.0, 0.08 * math.cos(ang))
        _limb(sb, hip + right * (side * 0.10), foot, 0.15, dress_sh * 0.88, dress_li * 0.92, spr=DASH + 2)

    _limb(sb, hip - up * 0.34, sh, 0.34, dress_sh, dress_li, spr=DAB + 1, smin=2.4)
    head = sh + up * 0.22
    sb.add([head], D=up, L=0.24, W=0.21, spr=DAB, csh=skin_sh, cli=skin_li, N=up, smin=2.0)
    if hat_sh is not None:
        sb.add([head + up * 0.11], D=fwd, L=0.40, W=0.34, spr=DAB + 1, csh=hat_sh, cli=hat_li, N=up, smin=2.0)

    # Arms + optional twirling parasol
    _limb(sb, sh - right * 0.18, hip - right * 0.20 - fwd * (0.14 * math.sin(phase)), 0.10, dress_sh, dress_li)
    r_sh = sh + right * 0.18
    if parasol_cols is not None:
        p_sh, p_li = parasol_cols
        hand = r_sh + fwd * 0.20 + up * 0.16
        _limb(sb, r_sh, hand, 0.09, dress_sh, dress_li)
        top = hand + up * 0.88 - fwd * 0.06
        _limb(sb, hand, top, 0.04, C(80, 62, 54), C(132, 102, 82), smin=1.6)
        # Dome canopy of 9 directional petal strokes
        angs = np.linspace(0.0, 2.0 * math.pi, 9, endpoint=False)
        for a in angs:
            dir_r = right * math.cos(a) + fwd * math.sin(a)
            p_rib = top + dir_r * 0.42 - up * 0.12
            sb.add([p_rib], D=dir_r - up * 0.25, L=0.68, W=0.46, spr=DAB + 2, csh=p_sh, cli=p_li, N=(dir_r * 0.4 + up * 0.9), smin=2.4)
    else:
        _limb(sb, r_sh, hip + right * 0.20 + fwd * (0.14 * math.sin(phase)), 0.10, dress_sh, dress_li)


def add_sailor_crew(sb, origin, fwd, right, up, heel_dir, pull_phase):
    """Articulated sailboat crew leaning back on the windward rail hauling sheets."""
    p0 = origin + right * 0.35 + up * 0.35
    lean = -heel_dir * 0.45 + up * 0.88
    lean /= np.linalg.norm(lean) + 1e-9
    sh = p0 + lean * 0.62
    pull = 0.14 * math.sin(pull_phase)

    sb.add([p0 + lean * 0.30], D=lean, L=0.65, W=0.28, spr=DAB + 1, csh=C(48, 66, 114), cli=C(238, 236, 224), N=up, smin=2.2)
    sb.add([sh + lean * 0.18], D=up, L=0.23, W=0.21, spr=DAB, csh=C(186, 134, 112), cli=C(246, 206, 174), N=up, smin=2.0)
    sb.add([sh + lean * 0.28], D=fwd, L=0.38, W=0.32, spr=DAB + 2, csh=C(196, 168, 116), cli=C(250, 228, 168), N=up, smin=2.0)
    # Hauling arms reaching toward cockpit center
    hand = origin + up * (0.55 + pull) - fwd * 0.15
    _limb(sb, sh + fwd * 0.12, hand, 0.09, C(168, 174, 198), C(244, 240, 228), smin=1.8)
    _limb(sb, sh - fwd * 0.12, hand - fwd * 0.12, 0.09, C(168, 174, 198), C(244, 240, 228), smin=1.8)

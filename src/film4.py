"""v4 Dreamworld Film orchestrator: 6 curated 3D Impressionist scenes (120.0s @ 30fps)."""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from anim.paint.engine import render, smooth
from anim.paint.world3 import Env

import look4
import sc1_poppies
import sc2_waterlilies
import sc3_viaduct
import sc4_cathedral
import sc5_lavender
import sc6_venice

_FONT_CANDIDATES_BOLD = [
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
]
_FONT_CANDIDATES_REG = [
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
]


def _load_font(candidates, size):
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _overlay_title(rgb_u8, t_film):
    """Subtle gallery oil-charcoal typography on warm linen reveal / finale."""
    H, W, _ = rgb_u8.shape
    op = 0.0
    is_open = t_film < 2.8
    is_close = t_film > 115.6
    if is_open:
        op = float(smooth(0.15, 0.75, t_film) * smooth(2.8, 1.85, t_film))
    elif is_close:
        op = float(smooth(115.8, 117.2, t_film) * smooth(120.0, 119.65, t_film))
    if op <= 0.01:
        return rgb_u8

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    sc = H / 1080.0
    f_zh = _load_font(_FONT_CANDIDATES_BOLD, int(round(78 * sc)))
    f_fr = _load_font(_FONT_CANDIDATES_REG, int(round(32 * sc)))
    f_sub = _load_font(_FONT_CANDIDATES_REG, int(round(24 * sc)))

    if is_open:
        zh = "莫 奈 光 影 梦 境"
        fr = "RÊVERIES DE MONET · SIX TOILES VIVANTES"
        sub = "Argenteuil · Giverny · Rouen · Provence · Venise"
        y_center = H * 0.46
        ink = (56, 46, 52, int(230 * op))
        gold = (138, 92, 48, int(205 * op))
    else:
        zh = "光 影 永 驻 画 境"
        fr = "POUR CLAUDE MONET (1840 – 1926)"
        sub = "CodePaint-Engine · 100% Pure Code Brushwork"
        y_center = H * 0.47
        ink = (52, 44, 52, int(235 * op))
        gold = (146, 94, 48, int(210 * op))

    def _cx(txt, font):
        bb = draw.textbbox((0, 0), txt, font=font)
        return (W - (bb[2] - bb[0])) * 0.5

    draw.text((_cx(zh, f_zh), y_center - 68 * sc), zh, font=f_zh, fill=ink)
    draw.text((_cx(fr, f_fr), y_center + 30 * sc), fr, font=f_fr, fill=gold)
    draw.text((_cx(sub, f_sub), y_center + 82 * sc), sub, font=f_sub, fill=ink)

    base = Image.fromarray(rgb_u8).convert("RGBA")
    out = Image.alpha_composite(base, overlay).convert("RGB")
    return np.asarray(out, dtype=np.uint8)


class MonetDreamFilm:
    def __init__(self):
        self.scenes = [
            sc1_poppies.Scene1Poppies(),
            sc2_waterlilies.Scene2Waterlilies(),
            sc3_viaduct.Scene3Viaduct(),
            sc4_cathedral.Scene4Cathedral(),
            sc5_lavender.Scene5Lavender(),
            sc6_venice.Scene6Venice(),
        ]
        self.paths = [
            sc1_poppies.camera_path(),
            sc2_waterlilies.camera_path(),
            sc3_viaduct.camera_path(),
            sc4_cathedral.camera_path(),
            sc5_lavender.camera_path(),
            sc6_venice.camera_path(),
        ]

    def render_frame(self, t_film: float, H: int = 1080):
        idx, lt = look4.scene_index_and_local_t(t_film)
        L = look4.look_global(t_film)
        env = Env(lt, self.paths[idx], lambda _t: L)
        S = self.scenes[idx].render_frame(env, lt)
        rgb = render(
            S,
            H,
            tone_amt=0.088,
            relief=1.02,
            bloom=0.18,
            fade=float(L.get("fade", 0.0)),
            fade_rgb=L.get("fade_rgb"),
            ground=L.get("ground"),
        )
        return _overlay_title(rgb, t_film)

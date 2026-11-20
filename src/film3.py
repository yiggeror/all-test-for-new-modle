"""Film Scene & Backend built cleanly on CodePaint-Engine's Config / Engine / Paint."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from anim.paint import engine as pe
from anim.paint.world3 import compose, shade
from shots3 import make_env, FILM_DUR
from sky3 import SkyDome
from world3_env import build_fields
from sc_props import build_static_groups
from actors3 import emit_act1_characters, emit_steam_train, emit_sailboats, emit_wildlife_and_cafe


def _find_font(size):
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


class SeineFilmScene:
    """Implements anim.core.Scene.sample(t) using world3 static groups, fields, sky, and actors."""

    def __init__(self):
        self.sky = SkyDome(seed=7)
        self.water, self.turf, self.tufts = build_fields()
        self.groups = build_static_groups()

    def sample(self, t_film: float):
        env = make_env(t_film)
        L = env.L
        parts = []

        # 1. 3D Sky dome, clouds, sun & twilight stars
        parts.extend(self.sky.emit(env))

        # 2. Infinite dynamic water, opaque turf undercoat & swaying poppy/grass tufts
        parts.append(self.water.emit(env))
        parts.append(self.turf.emit(env))
        parts.append(self.tufts.emit(env))

        # 3. Static world architecture & trees (with automatic MIRROR reflections!)
        for key_name in ("viaduct", "trees", "guinguette", "hills_reeds"):
            grp = self.groups[key_name]
            if grp is not None and grp.visible(env):
                A = grp.lod(env)
                if A is not None:
                    parts.append(shade(env, A, mirror=False, sway=True))
                    if grp.reflect:
                        Am = grp.lod(env, mirror=True)
                        if Am is not None:
                            parts.append(shade(env, Am, mirror=True, sway=True))

        # Hanging willow tendrils in OVER pass
        willow_over = self.groups["willow_over"]
        if willow_over is not None and willow_over.visible(env):
            Ao = willow_over.lod(env)
            if Ao is not None:
                parts.append(shade(env, Ao, mirror=False, sway=True))

        # Glowing Guinguette lamps & windows fade in smoothly with L['lamps']
        lamps_amt = float(L.get("lamps", 0.0))
        if lamps_amt > 0.04:
            lgrp = self.groups["lamps"]
            if lgrp is not None and lgrp.visible(env):
                Al = lgrp.lod(env)
                if Al is not None:
                    for mir in (False, True):
                        sh = shade(env, Al, mirror=mir, sway=False)
                        if sh is not None:
                            sh["a"] = sh["a"] * min(1.0, lamps_amt * 1.15)
                            parts.append(sh)

        # 4. Dynamic living characters, steam train + smoke, sailboats + wakes, wildlife
        parts.extend(emit_act1_characters(env))
        parts.extend(emit_steam_train(env))
        parts.extend(emit_sailboats(env))
        parts.extend(emit_wildlife_and_cafe(env))

        composed = compose(parts)
        return dict(strokes=composed, env=env)


class SeinePaintBackend:
    """Implements anim.core.Backend.draw() wrapping anim.paint.engine.render with per-frame L grading & title card."""

    def __init__(self, bloom=0.16, relief=1.0, tone_amt=0.088):
        self.bloom = bloom
        self.relief = relief
        self.tone_amt = tone_amt

    def draw(self, sample_data, cfg):
        strokes = sample_data["strokes"]
        env = sample_data["env"]
        L = env.L

        # Render via exact CodePaint-Engine paint/engine.py rasterizer (fade handled cleanly after expo/sat)
        img = pe.render(
            strokes,
            cfg.height,
            tone_amt=self.tone_amt,
            relief=self.relief,
            bloom=self.bloom,
            fade=0.0,
            ground=L.get("ground", pe.CANVAS),
        )

        # Subtle exposure & Impressionist color richness from env.L (applied before canvas fade)
        expo = float(L.get("expo", 1.0))
        sat = float(L.get("sat", 1.0))
        mist = float(L.get("mist", 0.0))
        fade = float(L.get("fade", 0.0))

        if abs(expo - 1.0) > 1e-3 or abs(sat - 1.0) > 1e-3 or mist > 1e-3 or fade > 1e-3:
            f = img.astype(np.float32) / 255.0
            if mist > 1e-3:
                f = f * (1.0 - 0.35 * mist) + L["hor"][None, None, :] * (0.35 * mist)
            if abs(expo - 1.0) > 1e-3:
                f *= expo
            if abs(sat - 1.0) > 1e-3:
                lum = (0.299 * f[:, :, 0] + 0.587 * f[:, :, 1] + 0.114 * f[:, :, 2])[:, :, None]
                f = lum + (f - lum) * sat
            if fade > 1e-3:
                fc = np.asarray(L.get("fade_rgb", pe.CANVAS), np.float32)
                wv, _, lo, _ = pe._weave(cfg.height, cfg.width)
                canvas_tex = fc[None, None, :] * (1.0 + 0.014 * lo[:, :, None]) * (1.0 + 0.024 * wv[:, :, None])
                f = f * (1.0 - fade) + canvas_tex * fade
            img = (np.clip(f, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)

        # Clean Impressionist title card on opening canvas (0..3.6s) and closing canvas (116..120s)
        t = env.t
        if t < 3.6 or t > FILM_DUR - 4.2:
            if t < 3.6:
                alpha_t = float(pe.smooth(0.15, 0.85, t) * pe.smooth(3.6, 2.5, t))
                title = "UN DIMANCHE SUR LA SEINE"
                sub = "塞纳河畔的星期日  ·  Claude Monet Impressionist Study"
            else:
                alpha_t = float(pe.smooth(FILM_DUR - 4.2, FILM_DUR - 2.6, t))
                title = "FIN"
                sub = "Un Dimanche sur la Seine  ·  CodePaint-Engine 3D"
            if alpha_t > 0.02:
                pil = Image.fromarray(img, "RGB").convert("RGBA")
                ov = Image.new("RGBA", pil.size, (0, 0, 0, 0))
                dr = ImageDraw.Draw(ov)
                sc = cfg.height / 1080.0
                f_big = _find_font(max(14, int(round(56 * sc))))
                f_sub = _find_font(max(10, int(round(24 * sc))))
                a_i = int(round(215 * alpha_t))
                dr.text((cfg.width // 2, int(cfg.height * 0.45)), title, fill=(58, 52, 62, a_i), font=f_big, anchor="mm")
                dr.text((cfg.width // 2, int(cfg.height * 0.53)), sub, fill=(96, 84, 86, int(a_i * 0.88)), font=f_sub, anchor="mm")
                img = np.asarray(Image.alpha_composite(pil, ov).convert("RGB"), dtype=np.uint8)

        return img

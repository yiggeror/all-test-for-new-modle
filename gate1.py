#!/usr/bin/env python3
"""Render matched Rainroji Gate 1 previews; stills only, no reused legacy plates."""
import argparse
import glob
import importlib
import importlib.util
import inspect
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFont

HERE = Path(__file__).resolve().parent
PROTOTYPE = HERE / "prototype" / "film"
sys.path.insert(0, str(PROTOTYPE))
from engine import fx, pix
from engine import render as ray

SCENES = ("spring", "summer", "autumn", "winter")
ALIASES = {"rain": "summer", "snow": "winter"}
LEGACY = {v: k for k, v in ALIASES.items()}


def grid(width):
    try:
        return {320: (320, 180, 6), 384: (384, 216, 5)}[width]
    except KeyError:
        raise ValueError("Gate 1 compares only 320×180 and 384×216") from None


def upscale1080(native):
    if native.ndim != 3 or native.shape[2] != 3 or native.dtype != np.uint8:
        raise ValueError("expected native 8-bit RGB pixels")
    h, w = native.shape[:2]
    _, expected_h, factor = grid(w)
    if h != expected_h:
        raise ValueError("native image is not the specified 16:9 size")
    return pix.upscale(native, factor)


def camera_signature(camera):
    """Physical position and normalized projection, without native W/H."""
    return np.r_[camera.pos, camera.f, camera.r, camera.u, camera.th, camera.tv, camera.shift]


def cjk_font_loader():
    """Use the prototype's fonts when present; otherwise a verified CJK font."""
    original = ImageFont.truetype
    fallback = {
        "ukai.ttc": ("serif", "ukai.ttc"),
        "uming.ttc": ("serif", "uming.ttc"),
        "wqy-zenhei.ttc": ("sans", "wqy-zenhei.ttc"),
    }
    fonts = {
        "serif": "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "sans": "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    }

    def load(font, size=10, index=0, *args, **kwargs):
        try:
            return original(font, size, index, *args, **kwargs)
        except OSError:
            name = Path(font).name if isinstance(font, (str, Path)) else None
            family = fallback.get(name, (None, ""))[0]
            if family is None:
                raise
            path = fonts[family]
            if not Path(path).is_file():
                paths = sorted(glob.glob("/usr/share/fonts/**/" + name, recursive=True))
                if not paths:
                    raise
                return original(paths[0], size, index, *args, **kwargs)
            return original(path, size, 2, *args, **kwargs)  # Noto collection: Simplified Chinese

    return load


def load_scene(name, module=None):
    local = HERE / "shots" / f"{name}.py"
    if module or local.is_file():
        path = Path(module or local).resolve()
        spec = importlib.util.spec_from_file_location(f"gate1_scene_{name}", path)
        sc = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = sc
        spec.loader.exec_module(sc)
        return sc
    return importlib.import_module("scenes." + LEGACY.get(name, name))


def scene_camera(sc, width, height):
    try:
        inspect.signature(sc.camera).bind(width, height)
    except TypeError:
        camera = sc.camera()  # legacy camera, same 16:9 aspect
        camera.W, camera.H = width, height
        camera.tv = camera.th * height / width
    else:
        camera = sc.camera(width, height)
    if (camera.W, camera.H) != (width, height):
        raise ValueError("scene camera did not use the declared native grid")
    return camera


def render_graded(sc, cam, phase, samples):
    # fx.SC controls the size of screen-space effects; their world-space positions still use Camera.project.
    fx.SC = cam.W / 480.0
    w = sc.build()
    plate, tracer = ray.render(w, cam, sc.sky, S=samples, **sc.RENDER)
    plate["lights"] = w.lights
    if hasattr(w, "chim"):
        plate["chim"] = w.chim
    if getattr(sc, "TWO_PASS", False):
        from engine.world import MASK_NEAR
        plate["far"], _ = ray.render(w, cam, sc.sky, S=samples, cam_mask=MASK_NEAR, acc=tracer, **sc.RENDER)
    denoise = getattr(sc, "DENOISE", {})
    if denoise is not None:
        fx.denoise(plate, **denoise)
        if "far" in plate:
            fx.denoise(plate["far"], **denoise)
    ctx = sc.setup(plate, cam)
    rgb = sc.frame(ctx, phase)
    if rgb.shape != (cam.H, cam.W, 3) or not np.isfinite(rgb).all():
        raise RuntimeError("scene returned invalid native linear RGB")
    vignette = fx.vignette(cam.H, cam.W, getattr(sc, "VIGNETTE", 0.15))
    return pix.tonemap(rgb * vignette, **sc.GRADE)


def anchors_norm(sc, camera):
    result = {}
    for label, point in getattr(sc, "ANCHORS", {}).items():
        x, y, _, depth = camera.project(point)
        result[label] = {"x": round(float(x) / camera.W, 5),
                         "y": round(float(y) / camera.H, 5), "in_front": bool(depth > 0)}
    return result


def export(scene, sc, out, sizes, phase, samples, max_colors, dither, strength):
    cams = [scene_camera(sc, width, grid(width)[1]) for width in sizes]
    signature = camera_signature(cams[0])
    if any(not np.allclose(signature, camera_signature(c), rtol=0, atol=1e-10) for c in cams):
        raise ValueError("A/B requires the same physical camera and framing")
    graded = []
    for cam in cams:
        print(f"{scene}: ray tracing {cam.W}x{cam.H}, {samples}×{samples} samples, phase {phase:.3f}", flush=True)
        graded.append(render_graded(sc, cam, phase, samples))
    options = getattr(sc, "PAL", {})
    extra = options.get("extra") or []
    if len(extra) > max_colors - 4:
        raise ValueError("scene forced colors exceed its palette budget")
    fitted = pix.fit_palette(graded, k=max_colors - len(extra), chroma_w=options.get("chroma_w", 4.0),
                             extra=extra, nsamp=17000, iters=15, seed=120)
    _, first = np.unique(fitted["rgb"], axis=0, return_index=True)
    keep = np.sort(first)
    pal = {name: colors[keep] for name, colors in fitted.items()}
    # Color chips describe the delivered palette; no text is burnt onto scene frames.
    strip = np.repeat(np.repeat(pal["rgb"][None], 56, axis=0), 32, axis=1)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for cam, image in zip(cams, graded):
        w, h, factor = grid(cam.W)
        thr = pix.threshold_map(h, w, dither, seed=177)
        native = pix.quantize(image, pal, thr, strength)
        prefix = f"{scene}_{w}x{h}"
        Image.fromarray(native, mode="RGB").save(out / f"{prefix}_native.png")
        Image.fromarray(upscale1080(native), mode="RGB").save(out / f"{prefix}_1080p.png")
        Image.fromarray(strip, mode="RGB").save(out / f"{prefix}_palette.png")
        used = len(np.unique(native.reshape(-1, 3), axis=0))
        results.append({"native": [w, h], "scale": factor, "filename": f"{prefix}_1080p.png", "used_colors": used})
        print(f"{saved_label(out, prefix)} ({used} colors)", flush=True)
    meta = {
        "scene": scene, "phase": phase, "samples_per_pixel": samples * samples,
        "dither": dither, "dither_strength": strength, "max_colors": max_colors,
        "shared_palette_count": len(pal["rgb"]),
        "camera_pos": cams[0].pos.tolist(), "camera_forward": cams[0].f.tolist(),
        "fov_horizontal": round(math.degrees(2 * math.atan(cams[0].th)), 4),
        "camera_signature": signature.tolist(),
        "anchors_normalized": anchors_norm(sc, cams[0]),
        "scene_module": Path(sc.__file__).name,
        "palette_rgb": pal["rgb"].tolist(),
        "frames": results,
    }
    (out / f"{scene}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return results


def saved_label(out, prefix):
    return f"saved {out / (prefix + '_1080p.png')}"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scene", required=True, choices=(*SCENES, *ALIASES))
    p.add_argument("--module", help="scene .py with the Rainroji build/sky/setup/frame interface")
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--size", choices=["320", "384", "both"], default="both")
    p.add_argument("--samples", type=int, choices=[1, 2, 3, 4], default=3, help="jittered ray samples per pixel side")
    p.add_argument("--phase", type=float, help="normalized still phase; defaults to the scene's PHASE")
    p.add_argument("--colors", type=int, choices=range(48, 65), default=60, metavar="48..64")
    p.add_argument("--dither", choices=["mix", "bayer", "blue"], default="mix")
    p.add_argument("--strength", type=float, help="ordered dither strength 0..1")
    args = p.parse_args()
    ImageFont.truetype = cjk_font_loader()
    scene = ALIASES.get(args.scene, args.scene)
    sc = load_scene(scene, args.module)
    phase = float(getattr(sc, "PHASE", 0.30) if args.phase is None else args.phase)
    strength = float(getattr(sc, "GATE1_DSTR", 0.29) if args.strength is None else args.strength)
    if not 0 <= phase < 1 or not 0 <= strength <= 1:
        p.error("phase must be in [0,1), and strength in [0,1]")
    sizes = [320, 384] if args.size == "both" else [int(args.size)]
    export(scene, sc, args.out, sizes, phase, args.samples, args.colors, args.dither, strength)


if __name__ == "__main__":
    main()

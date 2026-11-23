#!/usr/bin/env python3
"""Build Gate 1 review sheets separately from the eight untouched PNGs."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
BG, PANEL, LINE, COPY, MUTED = "#141b26", "#1f2a38", "#334053", "#f4e8d6", "#bbc5ce"
TITLES = (
    ("spring", "01  春 · 老巷暮色落花", "#eab4c9", "砖门楼 · 暖路灯 · 粉色花树"),
    ("summer", "02  夏 · 雨夜街角小店", "#f4bc81", "暖棚小店 · 红车 · 雨夜网吧"),
    ("autumn", "03  秋 · 梧桐黄昏大道", "#f0c275", "梧桐树冠 · 粉紫天光 · 报刊亭"),
    ("winter", "04  冬 · 雪夜家属院", "#acd6ee", "树影与灯雾 · 雪人与石凳 · 暖窗"),
)
GRIDS = ((320, 180, 6, "#efbc7e"), (384, 216, 5, "#a6d9e2"))
MOTION = {
    "spring": (
        ("睡猫落点", "门楼瓦脊：静卧，只做很轻的呼吸和偶尔摆尾。", None),
        ("飞蛾落点", "主路灯光晕：几粒小蛾缓慢绕行，离开暖光即隐。", None),
    ),
    "summer": (
        ("雨棚滴水落点", "雨棚边缘落水：一串短滴落到湿地，涟漪只在落点显形。", None),
        ("避雨剪影预留（伞／猫二选一）", "雨棚内侧：保留一小处避雨剪影，以轻呼吸或轻摆尾为限。", None),
    ),
    "autumn": (
        ("热茶水汽落点", "左侧报刊亭边：热茶只冒一缕暖汽。", None),
        ("晚鸟落点", "树冠间的粉紫天空：两三只归鸟从远处缓缓掠过。", (0.485, 0.085)),
    ),
    "winter": (
        ("伏案暖窗预留", "右侧有光的窗格：伏案剪影偶尔抬手翻页，室内暖光不跳。", None),
        ("排气白烟预留", "中景小棚附近：只在暖光附近看见缓慢升起的一缕白汽。", None),
    ),
}


def font(size, bold=False):
    name = "Bold" if bold else "Regular"
    return ImageFont.truetype(f"/usr/share/fonts/opentype/noto/NotoSansCJK-{name}.ttc", size, index=2)


def open_rgb(root, relative):
    with Image.open(root / relative) as im:
        return im.convert("RGB")


def overview(root, w, h, factor, accent):
    margin, width, img_h, gutter = 40, 960, 540, 24
    top, row_h = 129, 641
    out = Image.new("RGB", (2 * (margin + width) + gutter, top + 2 * row_h + 30), BG)
    d = ImageDraw.Draw(out)
    d.text((40, 21), "四季像素短片 · 第一轮构图", font=font(40, True), fill=COPY)
    letter = "A" if w == 320 else "B"
    d.rounded_rectangle((1510, 25, out.width - 40, 76), radius=12, fill=PANEL, outline=LINE, width=2)
    d.text((1528, 32), f"{letter}   {w}×{h}  ·  {factor}× 导出 1080p", font=font(26, True), fill=accent)
    d.text((42, 85), "同一构图、同一取样时相。四宫格用于整体比较，像素边界请看独立 1080p 净图。", font=font(22), fill=MUTED)
    for ix, (slug, title, season, details) in enumerate(TITLES):
        x = margin + (ix % 2) * (width + gutter)
        y = top + (ix // 2) * row_h
        d.text((x, y), title, font=font(29, True), fill=season)
        im = open_rgb(root, f"{slug}_{w}x{h}_1080p.png")
        im = im.resize((width, img_h), Image.Resampling.NEAREST)
        out.paste(im, (x, y + 43))
        strip = open_rgb(root, f"{slug}_{w}x{h}_palette.png")
        out.paste(strip.resize((width, 12), Image.Resampling.NEAREST), (x, y + 589))
        d.text((x, y + 606), details, font=font(20), fill=MUTED)
    out.save(root / f"overview_{letter}_{w}x{h}.png")


def paired(root, slug, title, season, details):
    # Full 1:1 images in this sheet, not rescaled. The originals remain the comparison source.
    margin, gap = 36, 26
    width, height = 1920, 1080
    header = 170
    out = Image.new("RGB", (2 * (margin + width) + gap, header + height + 96), BG)
    d = ImageDraw.Draw(out)
    d.text((margin, 17), title, font=font(53, True), fill=season)
    d.text((margin + 860, 38), details, font=font(31), fill=MUTED)
    for i, (w, h, factor, accent) in enumerate(GRIDS):
        x = margin + i * (width + gap)
        letter = "AB"[i]
        d.text((x, 112), f"{letter}   {w}×{h} 原生 / {factor}× 最近邻", font=font(32, True), fill=accent)
        out.paste(open_rgb(root, f"{slug}_{w}x{h}_1080p.png"), (x, header))
        strip = open_rgb(root, f"{slug}_{w}x{h}_palette.png")
        out.paste(strip.resize((width, 44), Image.Resampling.NEAREST), (x, header + height + 16))
    out.save(root / f"{slug}_comparison.png")


def motion_card(root, slug, title):
    actions = MOTION[slug]
    meta = json.loads((root / f"{slug}.json").read_text(encoding="utf-8"))
    im = open_rgb(root, f"{slug}_384x216_native.png").resize((1152, 648), Image.Resampling.NEAREST)
    out = Image.new("RGB", (1216, 891), BG)
    d = ImageDraw.Draw(out)
    d.text((32, 21), title, font=font(35, True), fill=COPY)
    d.text((32, 69), "Gate 1 静帧预览 · 圈为后续动作的计划位置，净图不含标记", font=font(21), fill=MUTED)
    out.paste(im, (32, 108))
    for n, (key, caption, override) in enumerate(actions, 1):
        data = meta["anchors_normalized"][key]
        u, v = override or (data["x"], data["y"])
        if not data["in_front"] or not (0 < u < 1 and 0 < v < 1):
            raise ValueError(f"motion anchor {key} is outside its camera")
        x, y = round(u * im.width) + 32, round(v * im.height) + 108
        c = GRIDS[n - 1][3]
        d.ellipse((x - 15, y - 15, x + 15, y + 15), outline=BG, width=7)
        d.ellipse((x - 15, y - 15, x + 15, y + 15), outline=c, width=3)
        num_x = x + 21 if u < 0.95 else x - 36
        d.text((num_x, y - 19), str(n), font=font(23, True), fill=c, stroke_width=3, stroke_fill=BG)
        yy = 772 + (n - 1) * 43
        d.rounded_rectangle((32, yy, 62, yy + 30), radius=5, fill=c)
        d.text((42, yy + 1), str(n), font=font(20, True), fill=BG)
        d.text((78, yy - 1), caption, font=font(24), fill=COPY)
    out.save(root / f"{slug}_motion_note.png")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dir", type=Path, default=HERE / "previews" / "gate_1")
    p.add_argument("--partial", action="store_true", help="only build per-season pages for finished seasons")
    args = p.parse_args()
    root = args.dir
    for slug, title, season, details in TITLES:
        if args.partial and not (root / f"{slug}_384x216_1080p.png").exists():
            continue
        paired(root, slug, title, season, details)
        if slug in MOTION:
            motion_card(root, slug, title)
    if not args.partial:
        for w, h, factor, accent in GRIDS:
            overview(root, w, h, factor, accent)


if __name__ == "__main__":
    main()

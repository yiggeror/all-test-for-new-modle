#!/usr/bin/env python3
"""Gate 1.5: create one four-season sheet and separate static motion-location cards."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw
from make_review_cards import BG, COPY, MUTED, TITLES, font, open_rgb

HERE = Path(__file__).resolve().parent
POINTS = ("#efbb7d", "#a3d6e2")
FEATURES = {
    "spring": "粉紫暮空 · 暖金路灯 · 门楼瓦脊",
    "summer": "奶油色店招 · 雨棚避雨猫 · 右下红霓虹倒影",
    "autumn": "金叶团簇 · 粉紫暮空 · 报刊亭",
    "winter": "完整橘光池 · 雪人与石凳 · 值班室暖窗",
}
MOTION = {
    "spring": (
        (("瓦脊卧猫", "睡猫落点", "暖光下蜷卧小猫"),
         "门楼瓦脊：只设想背部轻呼吸，尾尖偶尔垂摆。", None),
        (("小蛾落点", "飞蛾落点"),
         "主路灯光晕：几粒小蛾缓绕，飞离暖光后隐去。", None),
    ),
    "summer": (
        (("雨棚滴水落点",),
         "雨棚前缘落水：涟漪从湿地的接水点散开。", None),
        (("暖光货架前避雨猫",),
         "暖色货架正前方：避雨猫蹲在柜面，留背光和微摆尾空间。", None),
    ),
    "autumn": (
        (("热茶水汽落点", "报刊亭白汽落点"),
         "左边报刊亭灯下：热茶缓缓冒一缕白汽。", None),
        (("晚鸟落点", "远鸟落点", "归鸟落点"), 
         "扩开的粉紫天空：两三只远鸟缓缓归巢。", None),
    ),
    "winter": (
        (("值班室暖窗伏案人",),
         "右中景暖窗：伏案剪影留出手肘和书页，不在远窗做噪点式闪动。", None),
        (("值班室小烟管",),
         "值班室顶端：只计划一缕很薄的小暖烟，景外不叠厚雾。", None),
    ),
}


def motion(root, scene, title, accent):
    meta = json.loads((root / f"{scene}.json").read_text(encoding="utf-8"))
    im = open_rgb(root, f"{scene}_320x180_native.png")
    assert im.size == (320, 180)
    im = im.resize((1280, 720), Image.Resampling.NEAREST)
    out = Image.new("RGB", (1344, 969), BG)
    d = ImageDraw.Draw(out)
    d.text((32, 19), title, font=font(36, True), fill=accent)
    d.text((32, 72), "Gate 1.5 · 320×180 静帧／动作位置另标，尚未制作动画", font=font(22), fill=MUTED)
    out.paste(im, (32, 114))
    for n, (keys, caption, point) in enumerate(MOTION[scene], 1):
        anchors = meta["anchors_normalized"]
        data = next((anchors[k] for k in keys if k in anchors), None)
        if data is None:
            raise KeyError(f"{scene}: missing any of {keys}; available: {list(anchors)}")
        u, v = point or (data["x"], data["y"])
        if not (0 < u < 1 and 0 < v < 1 and data["in_front"]):
            raise ValueError(f"{scene}: {keys[0]} outside active frame")
        x, y = round(u * im.width) + 32, round(v * im.height) + 114
        c = POINTS[n - 1]
        d.ellipse((x-18,y-18,x+18,y+18), outline=BG, width=8)
        d.ellipse((x-18,y-18,x+18,y+18), outline=c, width=3)
        offx = 22 if u < .93 else -39
        d.text((x+offx,y-19), str(n), font=font(26, True), fill=c, stroke_width=3, stroke_fill=BG)
        yy = 852 + 48 * (n - 1)
        d.rounded_rectangle((32, yy, 69, yy+34), radius=5, fill=c)
        d.text((45,yy+1), str(n), font=font(22, True), fill=BG)
        d.text((88,yy), caption, font=font(24), fill=COPY)
    out.save(root / f"{scene}_motion_note.png")


def overview(root):
    iw, ih = 960, 540
    out = Image.new("RGB", (2032, 1424), BG)
    d = ImageDraw.Draw(out)
    d.text((32,24), "四季像素短片 · 构图与光影精修", font=font(42, True), fill=COPY)
    d.text((34,87), "原生 320×180  ·  最近邻 6×  ·  1080p 静帧", font=font(24), fill=MUTED)
    d.text((1650,49), "GATE 1.5", font=font(35, True), fill=POINTS[0])
    for idx, (scene,title,color,_) in enumerate(TITLES):
        x,y = 32+(idx%2)*1008, 139+(idx//2)*631
        d.text((x,y), title, font=font(28,True), fill=color)
        im = open_rgb(root, f"{scene}_320x180_native.png").resize((iw,ih), Image.Resampling.NEAREST)
        out.paste(im, (x,y+39))
        palette = open_rgb(root, f"{scene}_320x180_palette.png").resize((iw,10), Image.Resampling.NEAREST)
        out.paste(palette,(x,y+584))
        d.text((x,y+600), FEATURES[scene], font=font(19), fill=MUTED)
    out.save(root / "overview_gate_1_5.png")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dir", type=Path, default=HERE/"previews"/"gate_1_5")
    p.add_argument("--scene", choices=[row[0] for row in TITLES])
    a = p.parse_args()
    for slug, title, color, _ in TITLES:
        if not a.scene or a.scene == slug:
            motion(a.dir, slug, title, color)
    if not a.scene:
        overview(a.dir)


if __name__ == "__main__":
    main()

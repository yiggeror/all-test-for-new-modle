"""Lay out review frames rendered from the same Phase B geometry."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans'
def font(px,bold=False):return ImageFont.truetype(FONT+('-Bold' if bold else '')+'.ttf',px)
def make(root,dest,name,title,sub,row_labels,rows,w):
    margin,gutter,head,foot=27,14,88,43
    cols=len(rows[0])
    d=Image.new('RGB',(2*margin+cols*w+(cols-1)*gutter,head+len(rows)*(w+38)+foot),'#262b35')
    draw=ImageDraw.Draw(d)
    draw.text((margin,20),title,font=font(26,True),fill='#eff2f8')
    draw.text((margin,54),sub,font=font(15),fill='#b9c4d3')
    for j,row in enumerate(rows):
        for i,(f,label) in enumerate(row):
            x=margin+i*(w+gutter);y=head+j*(w+38)
            im=Image.open(root/(f+'.png')).convert('RGB')
            im.thumbnail((w,w),Image.Resampling.LANCZOS)
            d.paste(im,(x+(w-im.width)//2,y+(w-im.height)//2))
            draw.rectangle((x,y,x+w-1,y+w-1),outline='#546071')
            draw.text((x+3,y+w+9),(row_labels[j]+label),font=font(14,True),fill='#e0e8f5')
    draw.text((margin,d.height-29),'SUZU HOSHINO    /    PHASE B',font=font(12,True),fill='#a3b0c4')
    dest.mkdir(parents=True,exist_ok=True);d.save(dest/(name+'.png'),optimize=True)
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('raw',type=Path);ap.add_argument('out',type=Path)
ap.add_argument('--wip',action='store_true');ap.add_argument('--gray',action='store_true')
a=ap.parse_args()
if a.wip:
    make(a.raw,a.out,'01-hair-profile-wip','Suzu Hoshino / Hair silhouette','FIRST FIT  •  FRONT, THREE-QUARTER AND REAR  •  WORK IN PROGRESS',[''],
        [[('front','Front'),('threeq','Left three-quarter'),('back','Back')]],440)
else:
    views=[('front','Front'),('threeq','Left three-quarter'),('left','Left profile'),('right','Right profile'),('back','Back')]
    make(a.raw,a.out,'head_5view_npr_and_clay','Suzu Hoshino / Hair and headwear',
        'MATCHED CAMERAS  •  CLAY ABOVE / NPR BELOW',['Clay / ','NPR / '],
        [[(m+'_'+stem,lab) for stem,lab in views] for m in ('clay','npr')],365)
    make(a.raw,a.out,'hair_deadangles_and_props','Suzu Hoshino / Oblique and detail studies',
        'TOP, UNDERSIDE AND REAR  •  SEPARATE MOUNTS AND REAL GEOMETRY',['',''],
        [[('crown','Crown from above'),('low_clip','Clip from below'),('back_depth','Hair and shoulder clearance')],
         [('moon','Gilded crescent'),('star','Faceted sapphire'),('bow','Violet ribbon knot')]],460)
    make(a.raw,a.out,'expressions_with_hair','Suzu Hoshino / Expressions with hair',
        'FOUR NATIVE EXPRESSION PRESETS  •  ONE CHARACTER AND FIT',[''],
        [[('gentle','Gentle smile'),('laugh','Open laugh'),('closed','Eyes-closed smile'),('surprise','Surprised')]],410)

"""Compose Phase A review boards using the named Blender render passes."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import argparse

FORMATS = {
    'body_4view_clay': ('Suzu Hoshino / Body Proportions',
                        'PHASE A  •  CLAY  •  1.600 m reference',
                        ['Front', 'Three-quarter', 'Left profile', 'Back'],
                        [('body_000','body_045','body_090','body_180')]),
    'face_clay_vs_npr': ('Suzu Hoshino / Shape and Makeup',
                        'PHASE A  •  SAME HEAD AND CAMERAS  •  CLAY ABOVE / NPR BELOW',
                        ['Front', 'Left three-quarter', 'Left profile', 'Right three-quarter'],
                        [('clay_000','clay_045','clay_090','clay_315'),
                         ('npr_000','npr_045','npr_090','npr_315')]),
    'expressions_quickcheck': ('Suzu Hoshino / Expression Check',
                               'PHASE A  •  NATIVE EXPRESSION TARGETS  •  ACTUAL 3D RENDERS',
                               ['Gentle smile', 'Open laugh', 'Eyes-closed smile', 'Surprised'],
                               [('gentle','laugh','closed','surprise')])
}
SIZES={'body_4view_clay':(360,705),'face_clay_vs_npr':(395,395),
       'expressions_quickcheck':(395,440)}
BACKGROUND='#292c35'; TEXT='#ecf1f6'; DIM='#b6c1cf'; STROKE='#566174'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans'
def f(px,bold=False): return ImageFont.truetype(FONT+('-Bold' if bold else '')+'.ttf',px)

def layout(kind,src,dest):
    title,subtitle,labels,rows=FORMATS[kind]
    w,h=SIZES[kind]
    m,g,top,bottom=28,13,88,54
    row_h=h+39
    sheet=Image.new('RGB',(4*w+2*m+3*g,top+len(rows)*row_h+bottom),BACKGROUND)
    d=ImageDraw.Draw(sheet)
    d.text((m,17),title,font=f(28,True),fill=TEXT)
    d.text((m,55),subtitle,font=f(15),fill=DIM)
    for j,row in enumerate(rows):
        y=top+j*row_h
        for i,stem in enumerate(row):
            x=m+i*(w+g)
            im=Image.open(src/(stem+'.png')).convert('RGBA')
            im.thumbnail((w,h),Image.Resampling.LANCZOS)
            px,py=x+(w-im.width)//2,y+(h-im.height)//2
            if kind=='body_4view_clay':
                d.rectangle((x,y,x+w-1,y+h-1),fill=(218,224,229))
                y0=py+round(im.height*(.5+.810/1.724))
                y16=py+round(im.height*(.5+(.810-1.600)/1.724))
                d.line((x+12,y0,x+w-12,y0),fill='#8a98a7',width=1)
                d.line((x+14,y16,x+14,y0),fill='#637489',width=1)
                for step in range(5):
                    yy=y0+round((y16-y0)*step/4)
                    d.line((x+14,yy,x+(25 if step in (0,4) else 20),yy),fill='#637489',width=1)
                if i==0:
                    d.text((x+28,y16-10),'1.60 m',font=f(12,True),fill='#43576e')
                    d.text((x+28,y0+2),'0.00 m',font=f(12),fill='#43576e')
            sheet.paste(im,(px,py),im)
            d.rectangle((x,y,x+w-1,y+h-1),outline=STROKE)
            d.text((x+2,y+h+10),labels[i],font=f(15,True),fill=TEXT)
    d.text((m,sheet.height-31),'SUZU HOSHINO   /   PHASE A',font=f(13,True),fill=DIM)
    dest.mkdir(parents=True,exist_ok=True)
    sheet.save(dest/(kind+'.png'),optimize=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('src',type=Path)
    ap.add_argument('dest',type=Path)
    ap.add_argument('--only',choices=tuple(FORMATS))
    a=ap.parse_args()
    for kind in ([a.only] if a.only else FORMATS): layout(kind,a.src,a.dest)

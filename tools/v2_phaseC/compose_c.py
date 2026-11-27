"""Compose review boards from rendered outfit and natural motion stills."""
from pathlib import Path
import argparse
from PIL import Image,ImageDraw,ImageFont
F='/usr/share/fonts/truetype/dejavu/DejaVuSans'
def ft(px,heavy=False):return ImageFont.truetype(F+('-Bold' if heavy else '')+'.ttf',px)
def write(src,out,filename,title,caption,rows,tile,scale=False,headlite=False):
    w,h=tile;pad=26;g=13;top=86;rh=h+40;footer=44
    cols=len(rows[0]);assert all(len(q)==cols for q in rows)
    paper=Image.new('RGB',(2*pad+w*cols+g*(cols-1),top+rh*len(rows)+footer),'#272d38')
    d=ImageDraw.Draw(paper)
    d.text((pad,18),title,font=ft(27,True),fill='#eaf0f7')
    d.text((pad,54),caption,font=ft(15),fill='#bac8d9')
    for j,row in enumerate(rows):
      for i,(stem,label) in enumerate(row):
        xx=pad+(w+g)*i;yy=top+rh*j
        im=Image.open(src/(stem+'.png')).convert('RGB');im.thumbnail((w,h),Image.Resampling.LANCZOS)
        px=xx+(w-im.width)//2;py=yy+(h-im.height)//2
        paper.paste(im,(px,py))
        if headlite:
            sub=Image.open(src/('face_'+stem+'.png')).convert('RGB');sub.thumbnail((round(w*.31),round(h*.31)),Image.Resampling.LANCZOS)
            sx=xx+w-sub.width-8;sy=yy+8
            paper.paste(sub,(sx,sy));d.rectangle((sx-1,sy-1,sx+sub.width,sy+sub.height),outline='#879aaa')
        if scale:
            z0=py+round(im.height*(.5+.833/1.83))
            z1=py+round(im.height*(.5+(.833-1.60)/1.83))
            d.line((xx+13,z0,xx+w-5,z0),fill='#8a99ac',width=1)
            d.line((xx+14,z1,xx+14,z0),fill='#a3b4c9',width=1)
            for a in range(5):
                z=round(z1+(z0-z1)*a/4.)
                d.line((xx+14,z,xx+(25 if a in (0,4) else 20),z),fill='#a3b4c9',width=1)
            if i==0:d.text((xx+26,z1-10),'1.60 m',font=ft(10,True),fill='#e2e9f6')
        d.rectangle((xx,yy,xx+w-1,yy+h-1),outline='#4f5c72')
        d.text((xx+3,yy+h+8),label,font=ft(14,True),fill='#e8eef6')
    d.text((pad,paper.height-30),'SUZU HOSHINO   /   PHASE C',font=ft(12,True),fill='#a4b1c3')
    out.mkdir(parents=True,exist_ok=True);paper.save(out/(filename+'.png'),optimize=True)
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('src',type=Path);ap.add_argument('out',type=Path);ap.add_argument('--wip',action='store_true');ap.add_argument('--round6',action='store_true')
a=ap.parse_args();r=lambda *args,**kwargs:write(a.src,a.out,*args,**kwargs)
allv=[(0,'Front'),(45,'Left three-quarter'),(90,'Left side'),(135,'Left rear'),(180,'Back'),(225,'Right rear'),(270,'Right side'),(315,'Right three-quarter')]
four=[allv[i] for i in (0,1,2,4)]
if a.wip:
    r('01-outfit-fit-npr','Suzu Hoshino / Outfit fit','WORK IN PROGRESS  •  FOUR MATCHED ORTHOGRAPHIC CAMERAS',
      [[(f'npr_{x:03}',name) for x,name in four]],(350,566))
else:
    r('turnaround_8view_npr','Suzu Hoshino / Couture Turnaround','08 VIEWS  •  FULL-BODY NPR  •  1.60M HEIGHT REFERENCE',
      [[(f'npr_{x:03}',name) for x,name in z] for z in [allv[:4],allv[4:]]],(310,516),scale=True)
    if not a.round6:r('turnaround_4view_clay_and_wire','Suzu Hoshino / Clay and topology','MATCHED FULL-BODY VIEWS  •  MESH EDGES FROM THE REAL ASSET',
      [[(f'{m}_{x:03}',m.title()+' / '+name) for x,name in four] for m in ('clay','wire')],(330,526))
    r('lighting_stress_test','Suzu Hoshino / Directional light study','FIVE MATCHED LIGHT SETUPS  •  FULL-BODY AND FACE CLOSE-UP',
      [[('light_'+k,n) for k,n in [('front','Front'),('left','Left 45°'),('right','Right 45°'),('top','Top'),('rim','Back edge')]]],(290,470),headlite=True)
    r('details_npr','Suzu Hoshino / Couture details','REAL MESH DETAILS  •  WAIST, TRIMS AND HARDWARE',
      [[('chest','Collar, bow and astrolabe'),('sleeve','Cuff and five fingers'),('hem','Pleated skirt and lining'),('garter','Right-thigh star garter'),('shoes','Round-toed Mary Janes')]],(340,300))

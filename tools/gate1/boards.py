"""Compose aligned, full-size review plates from actual Blender PNG renders."""
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw
import sys
src,dest=map(Path,sys.argv[1:3]); dest.mkdir(parents=True,exist_ok=True)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def ft(px,heavy=False): return ImageFont.truetype(bold if heavy else font,px)
def compose(title,sub,items,cols,name,scale=False):
    items=[(Image.open(src/(file+'.png')).convert('RGB'),label)for file,label in items]
    w,h=items[0][0].size
    gap,margin,top,footer=14,32,96,52
    rowh=h+40
    board=Image.new('RGB',(margin*2+w*cols+gap*(cols-1),top+rowh*((len(items)+cols-1)//cols)+footer),(28,34,42))
    d=ImageDraw.Draw(board)
    d.text((margin,25),title,font=ft(28,True),fill=(235,241,246))
    d.text((margin,61),sub,font=ft(15),fill=(177,197,214))
    for idx,(im,label) in enumerate(items):
        x=margin+(idx%cols)*(w+gap); y=top+(idx//cols)*rowh
        board.paste(im,(x,y));d.rectangle((x,y,x+w-1,y+h-1),outline=(88,101,116))
        d.text((x+3,y+h+10),label,font=ft(17,True),fill=(204,221,233))
        if scale:
            floor=y+round(h*(.5+.826/1.76));topline=y+round(h*(.5+(.826-1.600)/1.76))
            d.line((x+25,floor,x+w-6,floor),fill=(106,121,136),width=1)
            d.line((x+9,topline,x+9,floor),fill=(142,164,178),width=1)
            for t in range(5):
                yy=floor+round((topline-floor)*t/4)
                d.line((x+9,yy,x+(23 if t in (0,4) else 17),yy),fill=(166,181,194),width=1)
            d.text((x+14,topline+4),'1.60 m',font=ft(10),fill=(184,197,211))
    d.text((margin,board.height-40),'SUZU HOSHINO  /  GATE 01   •   ORTHOGRAPHIC CLAY STUDY',font=ft(13,True),fill=(151,166,181))
    board.save(dest/name,optimize=True)
labels=['Front 000°','Left 3/4 045°','Left profile 090°','Left rear 135°','Back 180°','Right rear 225°','Right profile 270°','Right 3/4 315°']
if len(sys.argv)>3 and sys.argv[3]=='fit':
    frames=[('fit_000','Front 000°'),('fit_035','Left 3/4 035°'),('fit_090','Left profile 090°'),('fit_180','Back 180°')]
    compose('Suzu Hoshino / Fitting Study','WORK IN PROGRESS  •  Proportions, clothing layers and clearance',frames,4,'04-fit-clay.png',True)
    sys.exit()
if len(sys.argv)>3 and sys.argv[3]=='wip':
    frames=[('clay_000','Front'),('clay_090','Left'),('clay_270','Right')]
    compose('Suzu Hoshino / Clay Preview','WORK IN PROGRESS  •  Geometry, proportions, silhouette',frames,3,'clay_wip.png',True)
    compose('Suzu Hoshino / Head Study','WORK IN PROGRESS  •  Form and profiles',[(f'face_{a:03}',v) for a,v in [(0,'Front'),(90,'Left profile'),(270,'Right profile')]],3,'face_wip.png')
    sys.exit()
compose('Suzu Hoshino / Character Turnaround','08 VIEWS  •  Full-body proportions and silhouette',[(f'clay_{i*45:03d}',l) for i,l in enumerate(labels)],4,'turnaround_8view_clay.png',True)
compose('Suzu Hoshino / Topology','04 VIEWS  •  Mesh-flow overlay',[(f'wire_{i*45:03d}',labels[i]) for i in (0,1,2,4)],2,'turnaround_4view_wireframe.png',True)
compose('Suzu Hoshino / Face Study','05 VIEWS  •  Objective orthographic close-ups',[(f'face_{a:03d}',label)for a,label in [(0,'Front'),(35,'Left 3/4'),(325,'Right 3/4'),(90,'Left profile'),(270,'Right profile')]],3,'face_5view_clay.png')
compose('Suzu Hoshino / Detail Atlas','06 STUDIES  •  Real geometry, untextured',list(zip(['hands','chest','hairpin','skirt','garter','shoes'],['Five fingers','Bow and orrery brooch','Crescent and blue star','Double skirt layers','Right garter','Mary Jane shoes'])),3,'details_clay.png')

compose('Suzu Hoshino / Oblique Inspection','HIGH / LOW ANGLES  •  Hair overlaps, anchor points and contact',list(zip(['audit_crown','audit_pin','audit_back','audit_shoes'],['High 3/4 crown','Low 3/4 clip and eye','Back shoulder clearance','Shoe contact plane'])),2,'inspection_4view_clay.png')

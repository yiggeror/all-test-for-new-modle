"""Compose a proof sheet from actual Chromium screenshots."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('screens',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    pairs=[('01-shaded.png','01 / SHADING · FULL BODY'),
           ('02-clay.png','02 / CLAY · HALF BODY'),
           ('03-wire.png','03 / LIVE WIREFRAME'),
           ('04-closed.png','04 / NATIVE MORPH · CLOSED-EYE SMILE')]
    panel=Image.new('RGB',(1964,1530),'#161b28')
    g=ImageDraw.Draw(panel)
    ft='/usr/share/fonts/truetype/dejavu/DejaVuSans'
    g.text((24,18),'SUZU HOSHINO   /   ASTRAL ACADEMY VIEWER',font=ImageFont.truetype(ft+'-Bold.ttf',32),fill='#e8eaf0')
    g.text((24,56),'Actual Chromium renders • signed GLB • four live inspection states',font=ImageFont.truetype(ft+'.ttf',18),fill='#e1bd83')
    for i,(name,label) in enumerate(pairs):
        x=24+(i%2)*974;y=96+(i//2)*714
        g.text((x,y),label,font=ImageFont.truetype(ft+'-Bold.ttf',18),fill='#b9c5db')
        with Image.open(args.screens/name) as im:
            im=im.convert('RGB');im.thumbnail((942,667),Image.Resampling.LANCZOS);panel.paste(im,(x,y+27))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    panel.save(args.output,optimize=True)

if __name__=='__main__':
    main()

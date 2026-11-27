"""Encode the genuine Blender frame sequences with the original empty surround."""
from pathlib import Path
from PIL import Image
import json,subprocess,sys
r=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
for stem,n,dest in [('orbit',360,'turntable_npr_1080p.mp4'),('motion',342,'motion_expression_showcase.mp4')]:
 files=[r/(f'{stem}_{i:04d}.png') for i in range(1,n+1)]
 assert all(x.is_file() for x in files)
 prox=Image.open(files[0]).convert('RGB');w,h=prox.size
 assert h==1080 and w<=1920 and w>=900
 color=prox.getpixel((0,0))
 if w!=1920:
    for f in files[::10]:
      with Image.open(f) as im:
       assert im.size==(w,h) and max(abs(x-y) for x,y in zip(im.getpixel((0,0))[:3],color))<=1
       # No geometry may intersect the true framing seam.
       for y in range(30,h-1,54):
        for x in (0,w-1):
         assert max(abs(a-b) for a,b in zip(im.getpixel((x,y))[:3],color))<=3,(f,x,y)
    blank='0x'+''.join(f'{x:02x}' for x in color)
    vf=f'pad=1920:1080:(ow-iw)/2:0:color={blank}'
 else:vf='format=yuv420p'
 d=out/dest
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','30','-start_number','1',
                 '-i',str(r/(f'{stem}_%04d.png')),'-frames:v',str(n),'-vf',vf,'-c:v','libx264','-pix_fmt','yuv420p',
                 '-crf','17','-preset','medium','-movflags','+faststart',str(d)],check=True)
 meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_streams','-of','json',str(d)]))
 s=meta['streams'][0]
 assert (s['width'],s['height'],s['avg_frame_rate'])==(1920,1080,'30/1')
 assert abs(float(s['duration'])-n/30)<.02 and int(s['nb_frames'])==n
 subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(d),'-f','null','-'],check=True)
 print(d.name,n,'genuine frames, duration',s['duration'])

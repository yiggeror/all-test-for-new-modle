"""Encode the numbered actual Blender frames and restore their exact studio canvas."""
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
import numpy as np
from PIL import Image

def parse():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('frames',type=Path);p.add_argument('output',type=Path)
 p.add_argument('--first',type=int,default=1);p.add_argument('--last',type=int,default=360)
 p.add_argument('--manifest',type=Path);p.add_argument('--wait',action='store_true')
 return p.parse_args()
def get_frame(p,wait):
 while True:
  if p.is_file():
   try:
    with Image.open(p) as f:
     f.load();return np.asarray(f.convert('RGB'))
   except (OSError,ValueError):
    if not wait:raise
  if not wait:raise FileNotFoundError(p)
  time.sleep(.45)

def main():
 a=parse();W,H,FPS=1920,1080,30
 if not a.wait:
  missing=[k for k in range(a.first,a.last+1) if not (a.frames/f'orbit_{k:04d}.png').is_file()]
  if missing:raise SystemExit(f'Missing real frames ({len(missing)}): {missing[:18]}')
 target=a.output.resolve();target.parent.mkdir(parents=True,exist_ok=True)
 temporary=target.with_name(target.stem+'.encoding'+target.suffix)
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
 '-s:v',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0',
 '-vf','scale=out_color_matrix=bt709:out_range=tv,format=yuv420p','-an',
 '-c:v','libx264','-threads','2','-preset','medium','-crf','17',
 '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv',
 '-movflags','+faststart',str(temporary)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 rows=[];digests=set()
 try:
  for k in range(a.first,a.last+1):
   path=a.frames/f'orbit_{k:04d}.png'
   rgb=get_frame(path,a.wait);h,w,_=rgb.shape
   if h!=H or not (904<=w<=W) or (W-w)%2:
    raise ValueError((k,rgb.shape,'retain exact 1080p review camera geometry'))
   allpix=(rgb.tobytes())
   fingerprint=hashlib.sha256(allpix).hexdigest()
   if fingerprint in digests:raise ValueError((k,'duplicate rendered camera frame'))
   digests.add(fingerprint)
   near=np.concatenate((rgb[:,:9,:].reshape((-1,3)),rgb[:,-9:,:].reshape((-1,3))))
   backdrop=np.median(near,axis=0).astype(np.uint8)
   border_delta=np.abs(near.astype(np.int16)-backdrop).max()
   if border_delta>3:raise ValueError((k,'character reached the rendered X border',int(border_delta)))
   # This pads only the opaque, flat studio world seen on both camera edges.
   # No subject pixels are resized, composited, or duplicated between frames.
   canvas=np.empty((H,W,3),dtype=np.uint8);canvas[:]=backdrop
   left=(W-w)//2;canvas[:,left:left+w]=rgb
   p.stdin.write(canvas.tobytes())
   if k<=240:seg,az='full',(k-1)*1.5
   else:seg,az='upper',(k-241)*3.
   rows.append({'frame':k,'actual_rgb_sha256':fingerprint,'shot':seg,'camera_azimuth_degrees':az,
     'render_crop':[w,h],'world_rgb':backdrop.tolist(),'border_max_delta':int(border_delta)})
  p.stdin.close()
  if p.wait():raise RuntimeError('FFmpeg encode failed')
 except BaseException:
  if p.poll() is None:p.kill()
  if temporary.exists():temporary.unlink()
  raise
 os.replace(temporary,target)
 manifest=a.manifest or target.with_suffix('.frames.json')
 manifest.write_text(json.dumps({'fps':FPS,'frame_size':[W,H],'frames':rows},indent=2),encoding='utf-8')
 print(f'Encoded {len(rows)} unique actual Blender frames → {target.name}',flush=True)

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Compare native RGB against all 660 decoded pixels, not only metadata or sprites."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np


def sha(f):
    with f.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def run_hash(args,frames=None):
    cmd=['ffmpeg','-v','error','-nostdin','-xerror','-filter_threads','2','-threads','4',*args,
         '-an','-f','framehash','-hash','sha256','-']
    r=subprocess.run(cmd,input=frames,stdout=subprocess.PIPE,check=True)
    hashes=[x.rsplit(',',1)[-1].strip() for x in r.stdout.decode().splitlines() if x and not x.startswith('#')]
    return hashes


def exact_master(scene,native,master):
    a=np.load(native,mmap_mode='r',allow_pickle=False)
    if a.shape!=(330,180,320,3) or a.dtype!=np.uint8:
        raise ValueError(f'{scene}: not 330 RGB uint8 320×180 frames')
    p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(master)]))
    v,=p['streams']
    spec=(v['codec_type'],v['codec_name'],v['width'],v['height'],v['avg_frame_rate'],
          v['nb_frames'],v['pix_fmt'],v['color_space'],v['color_range'])
    if spec!=('video','h264',1920,1080,'30/1','660','yuv420p','bt709','tv'):
        raise ValueError(f'{scene}: unexpected master format {spec}')
    if Fraction(v['time_base'])*v['duration_ts']!=22:
        raise ValueError(f'{scene}: not two 11 s cycles')
    oracle=run_hash(['-f','rawvideo','-pixel_format','rgb24','-video_size','320x180','-framerate','30','-i','pipe:0',
                     '-vf','scale=1920:1080:flags=neighbor:out_color_matrix=bt709:out_range=tv,format=yuv420p'],a.tobytes())
    dec=run_hash(['-i',str(master),'-map','0:v:0','-pix_fmt','yuv420p'])
    if len(oracle)!=330 or len(dec)!=660 or oracle+oracle!=dec:
        bad=[n for n,(x,y) in enumerate(zip(oracle+oracle,dec)) if x!=y]
        raise ValueError(f'{scene}: reconstructed vs decoded frame bytes differ ({len(bad)} mismatches, first {bad[:7]})')
    dif=[]
    for i in range(322,339):
        nxt,prev=a[i%330].astype(np.int16),a[(i-1)%330].astype(np.int16)
        d=np.abs(nxt-prev)
        dif.append({'from_frame':(i-1)%330,'to_frame':i%330,
                    'mae_rgb':round(float(d.mean()),6),'changed_native_pixels':int(np.count_nonzero(np.any(d,axis=2)))})
    if dec[329]==dec[330]:
        raise ValueError(f'{scene}: identical actual last/first frame')
    c=np.unique(a.reshape(-1,3),axis=0)
    return {'scene':scene,'native_count':330,'master_count':660,'first_cycle_seconds':11,'npy_sha256':sha(native),
            'master_sha256':sha(master),'master_bytes':master.stat().st_size,'actual_native_palette_size':len(c),
            'actual_palette_rgb':c.tolist(),'decoded_equal_to_native_rgb_plus_locked_Bt709_exact_6x_filter':660,
            'second_cycle_byte_identical_to_first_frames':330,
            'maximum_near_native_seam_mae_rgb':max(r['mae_rgb'] for r in dif if r['to_frame']!=0),
            'seam_neighborhood_steps':dif}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scene');p.add_argument('native',type=Path);p.add_argument('master',type=Path);p.add_argument('report',type=Path)
    a=p.parse_args();result=exact_master(a.scene,a.native,a.master)
    a.report.parent.mkdir(exist_ok=True,parents=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(a.scene,result['master_bytes'],result['master_sha256'],f"{result['decoded_equal_to_native_rgb_plus_locked_Bt709_exact_6x_filter']}/660 exact")


if __name__=='__main__':main()

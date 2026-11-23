#!/usr/bin/env python3
"""Native-to-master only. No video stream is accepted as a source."""
from pathlib import Path
from dataclasses import dataclass
from decimal import Decimal,ROUND_HALF_UP
import hashlib, subprocess, json, os, time, math,argparse
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
FPS=30;NATIVE=(320,180);FRAME_LIMIT=5917;SAMPLE_MUSIC=Decimal('197.214');CYCLE=330
SOURCE_ORDER=('spring','summer','autumn','winter')
NAMES=('春','夏','秋','冬')
SOURCES={
 'spring':('alltest_gate2_spring_autumn','7e7a60f2731ad075515cfb1505607c36633dae9a5645bc4796806a3276629778','b09f6912a0d04a319d4b4644a545f5cae8c8e01e3d4ca6880d6f52eefabee355'),
 'summer':('alltest_gate2_summer_winter','c77b8e16184a02cfcf0b265560bf0ddaf0e8522c37d8075a1a2e3bd57de08cd9','b40f9e32a0b2b4fba72d988803eab9927c2fdb619d9cefe9a841f481fbdcdc98'),
 'autumn':('alltest_gate2_spring_autumn','6b1335a327a47929ea80c4264a7c4b18b1f5c9fab2a5349edddc8f8f26eb26d1','7d115d019329aea7b50f02b267552e35d6a3d3c686f642ec4c8373f73ea87eba'),
 'winter':('alltest_gate2_summer_winter','ceb6208d32aa5ef64450819d9a3cbf5364ae0d6aff2ae52302d2f7a86c46d9bd','14568ddf327751dbab81961ba7136e3ee33e2860fece6815020efa3a04b93c41'),
}
ENCODE_ARGS=['-map','0:v:0','-an','-vf','scale=1920:1080:flags=neighbor:out_color_matrix=bt709,format=yuv420p',
 '-c:v','libx264','-profile:v','high','-level:v','4.0','-crf','14','-preset','slow','-pix_fmt','yuv420p',
 '-g','60','-keyint_min','30','-refs','4','-threads','6','-color_range','tv','-colorspace','bt709',
 '-color_primaries','bt709','-color_trc','bt709','-movflags','+faststart']
x=np.arange(256,dtype=np.float32)/255.
LINEAR=np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4).astype(np.float32)

def smooth(t):
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)

@dataclass(frozen=True)
class Plan:
    centers:tuple
    dissolve:int=60
    head:int=45
    tail:int=108
    frames:int=FRAME_LIMIT
    @property
    def intervals(self):
        return tuple((c-self.dissolve//2,c+self.dissolve//2) for c in self.centers)
    @property
    def origins(self):
        return (0,)+tuple(a for a,b in self.intervals)
    @property
    def tail_begin(self):
        return self.frames-1-self.tail
    def at(self,i):
        if not 0<=i<self.frames:raise ValueError(i)
        phases=tuple((i-origin)%CYCLE for origin in self.origins)
        mix=np.zeros(4,dtype=np.float64);j=0
        for k,(lo,hi) in enumerate(self.intervals):
            if i>=hi:
                j=k+1;continue
            if i>=lo:
                a=smooth((i-lo)/self.dissolve);mix[k+1]=a
                mix[k]=1-a
                break
            mix[k]=1
            break
        else:mix[j]=1
        light=smooth(i/self.head)*smooth((self.frames-1-i)/self.tail)
        return phases,mix,light
    def validate(self):
        if len(self.centers)!=3 or self.dissolve%2 or not 46<=self.dissolve<=60:
            raise ValueError('three centers and an even 46–60 frame dissolve required')
        if not 90<=self.tail<=120 or self.head!=45 or self.frames!=5917:
            raise ValueError('45-frame head, 90–120 frame tail, and 5917 locked total')
        intervals=self.intervals
        if not intervals[0][0]>self.head or not intervals[-1][-1]<self.tail_begin:
            raise ValueError('season dissolve overlaps head or tail')
        if not all(a>b for (a,_),(_,b) in zip(intervals[1:],intervals[:-1])):
            raise ValueError('overlapping season transitions')
        last=None; phases_since=[[] for _ in SOURCE_ORDER]; cycle_edges=[]
        for i in range(self.frames):
            q,w,l=self.at(i)
            if not np.isclose(w.sum(),1,atol=1e-12) or not 0<=l<=1:raise ValueError(i)
            if last is not None:
                q0,w0,_=last
                for s in range(4):
                    if w0[s]>0 and w[s]>0:
                        if (q[s]-q0[s])%CYCLE!=1:raise ValueError(('phase repetition/skip',i,s,q,q0))
                        if q0[s]==CYCLE-1:
                            cycle_edges.append({'film_frame':i,'season':SOURCE_ORDER[s],'from':q0[s],'to':q[s]})
            for s in np.flatnonzero(w>0):
                phases_since[s].append(i)
            last=(q,w,l)
        return cycle_edges,[[i[0],i[-1]] for i in phases_since]

def seconds2frames(x):
    return int((Decimal(x)*FPS).quantize(Decimal('1'),rounding=ROUND_HALF_UP))

def compose(p,arrs,i):
    phases,weights,lit=p.at(i)
    effective=weights*lit
    nz=np.flatnonzero(effective>0)
    if not len(nz):return np.zeros((180,320,3),np.uint8)
    if len(nz)==1 and effective[nz[0]]==1:
        return np.asarray(arrs[nz[0]][phases[nz[0]]])
    out=np.zeros((180,320,3),np.float32)
    for j in nz:
        out+=LINEAR[arrs[j][phases[j]]]*np.float32(effective[j])
    bounds=np.clip(out,0,1)
    srgb=np.where(bounds<=.0031308,12.92*bounds,1.055*bounds**(1/2.4)-.055)
    return np.clip(np.rint(srgb*255),0,255).astype(np.uint8)

def load_sources():
    data=[];rows={}
    for name in SOURCE_ORDER:
        sub,full,payload=SOURCES[name]
        path=HERE.parent/sub/'qa'/f'{name}_native.npy'
        with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=full:raise ValueError(f'{name}: frozen NPY mismatch {actual}')
        a=np.load(path,mmap_mode='r',allow_pickle=False)
        if a.shape!=(330,180,320,3) or a.dtype!=np.uint8 or not a.flags.c_contiguous:
            raise ValueError(f'{name}: invalid 320×180 native RGB')
        ach=hashlib.sha256(b''.join(hashlib.sha256(frame).digest() for frame in a)).hexdigest()
        if ach!=payload:raise ValueError(f'{name}: different from independent Gate 2 RGB payload')
        if not all(not np.array_equal(a[i-1],a[i]) for i in range(330)):
            raise ValueError(f'{name}: repeated whole RGB frame')
        data.append(a)
        rows[name]={'relative':f'../{sub}/qa/{name}_native.npy','NPY_SHA256':actual,
                    'SHA256_of_ordered_RGB_frame_hashes':ach,'size':list(a.shape),'bytes':path.stat().st_size}
    return data,rows

def font(size):
    opt=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    return ImageFont.truetype(str(opt) if opt.is_file() else 'DejaVuSans.ttf',size,index=2 if opt.is_file() else 0)

def story(p,a,name):
    indices=[[p.intervals[j][0]-10,p.centers[j]-15,p.centers[j],p.centers[j]+15,p.intervals[j][1]+10] for j in range(3)]
    r=Image.new('RGB',(1660,824),'#1d2931');d=ImageDraw.Draw(r)
    d.text((24,7),'Gate 3 / 四季原生叠化时间表',font=font(28),fill='#fff0da')
    d.text((26,48),'同相位 320×180 RGB 原帧；叠化后才放大。下面的文字仅出现在核查表。',font=font(18),fill='#bfd0d0')
    for j,row in enumerate(indices):
        top=99+j*238
        d.text((24,top-27),f'{NAMES[j]} → {NAMES[j+1]}  中心 {p.centers[j]/FPS:.3f} s',font=font(15),fill='#ffecbd')
        for k,i in enumerate(row):
            xx=24+k*327
            r.paste(Image.fromarray(compose(p,a,i)),(xx,top))
            q,w,l=p.at(i)
            d.text((xx+1,top+181),f'{i/FPS:07.3f}s · #{i}  [α:{w[j+1]:.2f}]',font=font(15),
                   fill='#ffbc74' if k==2 else '#bbcbca')
    r.save(name,quality=94,subsampling=0)

def write_plan(p,rows,author_audio,notes):
    edges,spans=p.validate()
    entries=[]
    for i,(f,(lo,hi)) in enumerate(zip(p.centers,p.intervals)):
        entries.append({'from':SOURCE_ORDER[i],'to':SOURCE_ORDER[i+1],
                        'center_frame':f,'center_sec':f/FPS,'first_frame':lo,
                        'first_sec':lo/FPS,'end_frame_exclusive':hi,'end_exclusive_sec':hi/FPS,
                        'duration_frames':p.dissolve,'duration_sec':p.dissolve/FPS})
    return {'scope':'picture only; encode directly from pinned native NPY',
        'source_commit':'d8796e0',
        'reviewer_commit':'2ba3d65f4bab7a6fd479a662b369858ddaeb9572',
        'fps':FPS,'native_width':320,'native_height':180,'scale_neighbor':6,'frame_count':p.frames,
        'video_seconds':p.frames/FPS,'author_music_seconds':float(author_audio),'video_roundup_seconds':float(Decimal(p.frames)/FPS-author_audio),
        'head_fade_frames':p.head,'tail_fade_frames':p.tail,'tail_begin_frame':p.tail_begin,'tail_start_sec':p.tail_begin/FPS,
        'alpha':'smoothstep input in linear-light sRGB, then 8-bit RGB before NN',
        'visible_ranges_inclusive':dict(zip(SOURCE_ORDER,spans)),'picture_loop_origin_frames':dict(zip(SOURCE_ORDER,p.origins)),
        't':entries,'verified_internal_phase_wraps':edges,
        'native_inputs':rows,'notes':notes}

def run_encode(p,a,out):
    progress=HERE/'qa'/'encode_progress.log'
    fferr=HERE/'qa'/'encode.log'
    tmp=out.with_suffix('.part.mp4')
    if out.exists():raise FileExistsError("picture master is already frozen; will not overwrite")
    cmd=['ffmpeg','-nostdin','-hide_banner','-loglevel','info','-y','-stats_period','5',
        '-progress',str(progress),'-filter_threads','2','-f','rawvideo','-pixel_format','rgb24',
        '-video_size','320x180','-framerate','30','-i','pipe:0',*ENCODE_ARGS,str(tmp)]
    sha=hashlib.sha256()
    first=time.monotonic()
    with fferr.open('wb') as f:
        f.write((' '.join(cmd)+'\n').encode());f.flush()
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=f,bufsize=2_000_000)
        count=0
        try:
            for i in range(p.frames):
                src=compose(p,a,i)
                buf=memoryview(src).cast('B')
                sha.update(buf)
                proc.stdin.write(buf)
                count+=1
                if i%900==899:
                    print(f'PIPE {count}/{p.frames} elapsed {time.monotonic()-first:.1f}s',flush=True)
            proc.stdin.close()
        except BaseException:
            proc.kill();proc.wait();raise
        err=proc.wait()
    if err!=0 or count!=p.frames:raise RuntimeError((err,count,'see encode.log'))
    os.replace(tmp,out)
    with out.open('rb') as f:finalsha=hashlib.file_digest(f,'sha256').hexdigest()
    return {'filename':out.name,'bytes':out.stat().st_size,'sha256':finalsha,
            'count_written':count,'assembled_native_stream_sha256':sha.hexdigest(),
            'elapsed_s':round(time.monotonic()-first,3),'ffmpeg_args':cmd}

def main():
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument('--centers-frame',type=int,nargs=3)
    arg.add_argument('--tail-frames',type=int,default=108)
    arg.add_argument('--transition-frames',type=int,default=60)
    arg.add_argument('--audio-seconds',type=Decimal,default=SAMPLE_MUSIC)
    arg.add_argument('--notes',default='')
    arg.add_argument('--preflight-only',action='store_true')
    args=arg.parse_args()
    if not args.preflight_only and not args.centers_frame:
        arg.error('actual music phrase centers must be supplied from the audio review')
    a,rows=load_sources()
    c=tuple(args.centers_frame or (1440,2880,4320))
    p=Plan(c,dissolve=args.transition_frames,tail=args.tail_frames)
    qa=HERE/'qa';qa.mkdir(exist_ok=True);outdir=HERE/'out';outdir.mkdir(exist_ok=True)
    plan=write_plan(p,rows,args.audio_seconds,args.notes)
    (qa/'picture_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    story(p,a,qa/'transition_storyboard.jpg')
    print('PREFLIGHT_OK',len(plan['verified_internal_phase_wraps']),c,flush=True)
    if not args.preflight_only:
        result=run_encode(p,a,outdir/'four_seasons_gate3_picture_only.mp4')
        (qa/'picture_render.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print('ENCODED',json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':main()

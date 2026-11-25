#!/usr/bin/env python3
"""Native-to-master only. No video stream is accepted as a source."""
from pathlib import Path
from dataclasses import dataclass
import hashlib, json, subprocess, time
import numpy as np

HERE=Path(__file__).resolve().parent
FPS=30;NATIVE=(320,180);FRAME_LIMIT=5917;CYCLE=330
SOURCE_ORDER=('spring','summer','autumn','winter')
SOURCE_COMMIT='03b5d2cef53f60a97b095e54323e35d22bd8e794'
REVIEW_COMMIT='a0d0e108f04f5f2d92455cb0eada3ee1c2f2adc1'
AUTUMN_RGB='60273e5639377f2beb915787cf65d5ae66f9302b2647b1813812473a0f5bfb09'
DOMAINS={
    'spring':(0,1410), 'blend_spring_summer':(1411,1469), 'summer':(1470,2850),
    'blend_summer_autumn':(2851,2909), 'autumn':(2910,4290),
    'blend_autumn_winter':(4291,4349), 'winter':(4350,5916),
}
ENCODE_ARGS=['-map','0:v:0','-an','-vf','scale=1920:1080:flags=neighbor:out_color_matrix=bt709:out_range=tv,format=yuv420p',
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
    tail:int=114
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

PLAN = Plan((1440,2880,4320))

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

def picture_plan(p, rows):
    edges, spans = p.validate()
    entries = [
        {'from':SOURCE_ORDER[i], 'to':SOURCE_ORDER[i+1], 'center_frame':center,
         'first_frame':lo, 'end_frame_exclusive':hi, 'duration_frames':hi-lo, 'duration_sec':(hi-lo)/FPS}
        for i,(center,(lo,hi)) in enumerate(zip(p.centers,p.intervals))
    ]
    return {'source_commit':SOURCE_COMMIT,'review_commit':REVIEW_COMMIT,
            'fps':FPS,'native_width':320,'native_height':180,'scale_neighbor':6,
            'frame_count':p.frames,'exact_duration':'5917/30','video_seconds':p.frames/FPS,
            'head_fade_frames':p.head,'tail_fade_frames':p.tail,
            'tail_begin_frame':p.tail_begin,'tail_start_sec':p.tail_begin/FPS,
            'tail_zero_frame':p.frames-1,'tail_zero_sec':(p.frames-1)/FPS,
            'alpha':'smoothstep weights in linear-light sRGB; quantize native to RGB24, then 6x NN',
            'visible_ranges_inclusive':dict(zip(SOURCE_ORDER,spans)),
            'picture_loop_origin_frames':dict(zip(SOURCE_ORDER,p.origins)),
            'transitions':entries,'verified_internal_phase_wraps':edges,'native_inputs':rows}


RGB_LOCK_SHA256='60afa87a2c757e3dd39ed6ddda27d4a572a01732acd507366f40260dbf2c96d9'


def rgb_locks():
    raw = (HERE/'rgb_locks.json').read_bytes().replace(b'\r\n',b'\n')
    if hashlib.sha256(raw).hexdigest()!=RGB_LOCK_SHA256:
        raise ValueError('独审预编码锁文件 SHA-256 未匹配')
    locks = json.loads(raw)
    if set(locks['domains']) != set(DOMAINS):
        raise ValueError('独审的预编码时间域不完整')
    for label, span in DOMAINS.items():
        if tuple(locks['domains'][label]['frames_inclusive']) != span:
            raise ValueError('独审的预编码范围错误：'+label)
    a = locks['domains']['autumn']
    if a['rgb_sha256'] != AUTUMN_RGB or a['prior_rgb_sha256'] != AUTUMN_RGB or a['native_changed_pixels_summed']:
        raise ValueError('秋景预编码范围与已签收版不同')
    return locks


def run_encode(p, arrays, out, qa):
    progress=qa/'encode_progress.log'; fferr=qa/'encode.log'
    cmd=['ffmpeg','-nostdin','-hide_banner','-loglevel','info','-n','-stats_period','5',
         '-progress',str(progress),'-filter_threads','2','-f','rawvideo','-pixel_format','rgb24',
         '-video_size','320x180','-framerate','30','-i','pipe:0',*ENCODE_ARGS,str(out)]
    locks=rgb_locks()
    sha=hashlib.sha256()
    domain_hashes={name:hashlib.sha256() for name in DOMAINS}
    frame_keys=[key for key,(a,b) in DOMAINS.items() for _ in range(a,b+1)]
    before=time.monotonic()
    previous,held=None,[]
    frame_hashes={}
    with fferr.open('wb') as f:
        f.write((' '.join(cmd)+'\n').encode());f.flush()
        with subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=f,bufsize=2<<20) as proc:
            try:
                for i in range(p.frames):
                    src=compose(p,arrays,i)
                    buf=memoryview(src).cast('B')
                    sha.update(buf)
                    domain_hashes[frame_keys[i]].update(buf)
                    h=hashlib.sha256(buf).hexdigest()
                    if h==previous:held.append(i)
                    previous=h
                    if str(i) in locks['boundary_frame_rgb_sha256']:
                        frame_hashes[str(i)]=h
                    proc.stdin.write(buf)
                    if (i+1)%900==0:
                        print(f'PIPE {i+1}/{p.frames} · {time.monotonic()-before:.1f}s',flush=True)
                proc.stdin.close()
            except BaseException:
                proc.kill()
                proc.wait()
                raise
            if proc.wait()!=0:
                raise RuntimeError('画面编码失败，见 encode.log')
    expected=locks['rgb_sha256']
    domains={key:{'frames_inclusive':list(span),'rgb_sha256':domain_hashes[key].hexdigest()} for key,span in DOMAINS.items()}
    for key,stat in domains.items():
        if stat['rgb_sha256']!=locks['domains'][key]['rgb_sha256']:
            raise ValueError('实际进入编码器的 RGB 时间域与独审不同：'+key)
    if frame_hashes != locks['boundary_frame_rgb_sha256'] or sha.hexdigest() != expected:
        raise ValueError('实际进入编码器的完整 RGB 或边界帧 SHA-256 与独审不同')
    with out.open('rb') as f:
        encoded=hashlib.file_digest(f,'sha256').hexdigest()
    return {'filename':out.name,'bytes':out.stat().st_size,'sha256':encoded,'count_written':p.frames,
            'assembled_native_stream_sha256':sha.hexdigest(),'scored_rgb_domains':domains,
            'boundary_frame_rgb_sha256':frame_hashes,'preencode_adjacent_equal_count':len(held),
            'preencode_adjacent_equal_indices':held,'elapsed_s':round(time.monotonic()-before,3)}

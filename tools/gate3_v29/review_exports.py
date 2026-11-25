"""Timecoded review views decoded from the completed v2.9 mux."""
from fractions import Fraction
import json
from pathlib import Path
import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from assemble import FRAME_LIMIT, FPS, compose
from audio_lock import digest

W, H = 1920, 1080
STRIDE = W * H * 3
RATE = 48_000
ASSET_LIMIT = 8_500_000  # decimal bytes
HEROES = {'spring':120,'summer':1534,'autumn':3005,'winter':4456}
DETAILS = (
    ('spring','street',120,(119,74,56,38)),
    ('spring','yard',120,(235,98,56,38)),
    ('summer','street',1534,(29,3,56,57)),
    ('winter','street',4456,(38,15,56,57)),
)
STORY = (
    ('OPEN / SPRING',(0,11,22,45,120)),
    ('SPRING / SUMMER',(1400,1425,1440,1455,1480)),
    ('SUMMER / AUTUMN',(2840,2865,2880,2895,2920)),
    ('AUTUMN / WINTER',(4280,4305,4320,4335,4360)),
    ('WINTER / BLACK',(5760,5802,5848,5870,5916)),
)
EXCERPTS = (
    ('01_head_spring',0,135),
    ('02_spring_summer',1395,1560),
    ('03_summer_autumn',2835,2945),
    ('04_autumn_winter',4275,4500),
    ('05_winter_outro',5760,5917),
)

MATRIX = 'scale=in_color_matrix=bt709:in_range=tv:out_range=pc'
COLOR = ['-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709']


def media_clock(n):
    ms = (n * 1000 + FPS//2)//FPS
    s, milli = divmod(ms, 1000)
    m, seconds = divmod(s, 60)
    hours, minutes = divmod(m, 60)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}.{milli:03d}'


def cue(n):
    return {'film_frame_zero_based':n,'pts_seconds_exact':f'{n}/30','timecode':media_clock(n)}


def identity(path):
    n=path.stat().st_size
    if not 0 < n <= ASSET_LIMIT:
        raise ValueError(f'{path.name}: 审片文件大小超限（{n} 字节）')
    return {'file':path.name,'bytes':n,'sha256':digest(path)}


def showinfo_frames(log):
    base=re.findall(r'config in time_base:\s*(\d+/\d+)',log)
    regs=r'\bn:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:[^\n]*?\bplane_checksum:\[([0-9a-fA-F ]+)\]'
    rows=re.findall(regs,log)
    if not base or len(set(base)) != 1 or not rows or any(int(n)!=i for i,(n,_,_) in enumerate(rows)):
        raise ValueError('FFmpeg showinfo 缺少连续记录、时间戳或分量校验和')
    return Fraction(base[0]),[(int(p),s) for _,p,s in rows]


def font(sz):
    for name in ('DejaVuSans.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','LiberationSans-Regular.ttf'):
        try:
            return ImageFont.truetype(name,sz)
        except OSError:
            pass
    return ImageFont.load_default(size=sz)


def checked_stills(finished, qa, plan, native):
    wanted=set(HEROES.values()) | {n for _,row in STORY for n in row}
    wanted |= {a for _,a,_ in EXCERPTS} | {b-1 for _,_,b in EXCERPTS}
    wanted |= {1410,1470,2850,2910,4290,4350,4446,4459}
    indices=sorted(wanted)
    filt='+'.join(f'eq(n,{i})' for i in indices)
    cmd=['ffmpeg','-v','info','-hide_banner','-nostdin','-xerror','-threads','4','-filter_threads','2',
         '-i',str(finished),'-map','0:v:0','-an','-vf',f"select='{filt}',showinfo,{MATRIX}",
         '-fps_mode','passthrough','-pix_fmt','rgb24','-threads','1','-f','rawvideo','pipe:1']
    preview={}; hero={}; measurements={}; black={}
    log=qa/'extract.log'
    names={i:s for s,i in HEROES.items()}
    board_indices={n for _,row in STORY for n in row}
    with log.open('wb') as err, subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=err,bufsize=8<<20) as proc:
        for n in indices:
            raw=proc.stdout.read(STRIDE)
            if len(raw)!=STRIDE:
                raise ValueError(f'实解码帧 F{n:04d} 缺失')
            rgb=np.frombuffer(raw,np.uint8).reshape(H,W,3)
            sampled=rgb[3::6,3::6].astype(np.int16)
            err_rgb=np.abs(sampled-compose(plan,native,n))
            mae=float(err_rgb.mean()); over12=float((err_rgb.max(axis=2)>12).mean())
            if mae>3.0 or over12>.035:
                raise ValueError(f'F{n:04d} 实解码像素与锁定构图不符：MAE {mae} / >12 比例 {over12}')
            measurements[str(n)]={'decoded_center_rgb_mae':round(mae,6),'pixels_with_a_channel_error_above_12':round(over12,8)}
            if n in (0,FRAME_LIMIT-1):
                black[str(n)]=int(rgb.max())
                if black[str(n)]>1:
                    raise ValueError(f'F{n:04d} 实解码首末帧不是黑场')
            if n in names or n in board_indices:
                im=Image.frombytes('RGB',(W,H),raw)
                if n in board_indices:
                    preview[n]=im.resize((320,180),Image.Resampling.NEAREST)
                if n in names:
                    s=names[n]; target=qa/f'{s}_F{n:04d}_1080p.png'
                    im.save(target,optimize=True)
                    hero[s]={**identity(target),**cue(n),'dimensions':[W,H],'derived_from_final_mux':True,'no_overlay':True}
        if proc.stdout.read(1) or proc.wait():
            raise ValueError('成片实解码结束或帧数异常')
    tick,records=showinfo_frames(log.read_text(encoding='utf8',errors='replace'))
    log.unlink()
    if len(records)!=len(indices) or any(Fraction(p)*tick!=Fraction(i,30) for i,(p,_) in zip(indices,records)):
        raise ValueError('实解码抽帧的绝对画面时码未匹配')
    sums={n:h for n,(_,h) in zip(indices,records)}
    return preview,hero,sums,measurements,black


def board_transitions(qa, thumbs):
    gutters=10; margin=28; content_top=98; row_h=238
    board=Image.new('RGB',(2*margin+5*320+4*gutters,content_top+5*row_h+14),'#1b232d')
    d=ImageDraw.Draw(board)
    d.text((28,17),'RAINROJI / FOUR SEASONS',font=font(31),fill='#f3e9d6')
    d.text((29,60),'v2.9 / 30 fps / Actual 1080p final decode / No titles in the film',font=font(17),fill='#afc1cb')
    for r,(label,row) in enumerate(STORY):
        y=content_top+r*row_h
        d.text((28,y),label,font=font(13),fill='#dcc39a')
        for c,n in enumerate(row):
            x=margin+c*(320+gutters)
            board.paste(thumbs[n],(x,y+22))
            d.text((x+1,y+206),f'{media_clock(n)}    F{n:04d}',font=font(14),fill='#e7c388' if c==2 else '#bac5cc')
    out=qa/'transition_timeline.jpg'
    board.save(out,quality=94,subsampling=0)
    return {**identity(out),'thumbnail_size':[320,180],'from_released_size_decode':True,
            'rows':[{'label':title,'frames':[cue(n) for n in ids]} for title,ids in STORY]}


def board_lamps(qa, hero):
    margin=28; col_w=464; header=99; caption_h=54; gutter=27
    row_dims=[max(x[3][3] for x in row)*8 for row in (DETAILS[:2],DETAILS[2:])]
    row_starts=(header,header+caption_h+row_dims[0]+gutter)
    board=Image.new('RGB',(margin*2+col_w*2,row_starts[1]+caption_h+row_dims[1]+margin),'#18232a')
    d=ImageDraw.Draw(board)
    d.text((margin,14),'RAINROJI / LAMP FIXTURES',font=font(31),fill='#f3e9d6')
    d.text((margin,59),'v2.9 / 1080p final decode / 8x against the 320x180 native grid',font=font(16),fill='#afc1cb')
    parts=[]
    for j,(s,kind,n,rect) in enumerate(DETAILS):
        x0=margin+(j%2)*col_w;y0=row_starts[j//2]
        x,y,w,h=rect
        info=hero[s]
        if info['film_frame_zero_based']!=n:raise ValueError('灯具局部与 1080p 静帧不是同一帧')
        with Image.open(qa/info['file']) as im:
            crop=im.crop((x*6,y*6,(x+w)*6,(y+h)*6)).resize((w*8,h*8),Image.Resampling.NEAREST)
        out=qa/f'Lamp_{s}_{kind}_F{n:04d}_8x.png'
        crop.save(out,optimize=True)
        d.text((x0,y0),f'{s.upper()} / {kind.upper()}',font=font(15),fill='#e8cba2')
        d.text((x0,y0+26),f'{media_clock(n)}    F{n:04d}',font=font(15),fill='#b8c9d3')
        board.paste(crop,(x0,y0+caption_h))
        parts.append({**identity(out),**cue(n),'season':s,'fixture':kind,'native_crop_xywh':list(rect),
                      'source_1080p_crop_xywh':[v*6 for v in rect],'output_px_per_native_px':8,
                      'actual_scale_relative_to_1080p_decode':'8/6 nearest','source_still':info['file']})
    out=qa/'lamp_fixtures_8x.png'
    board.save(out,optimize=True)
    return {'board':identity(out),'details':parts}


def source_pcm(path, start, end):
    b=subprocess.check_output(['ffmpeg','-hide_banner','-v','error','-xerror','-nostdin','-i',str(path),'-map','0:a:0',
        '-af',f'atrim=start_sample={start}:end_sample={end}','-c:a','pcm_f32le','-f','f32le','pipe:1'])
    result=np.frombuffer(b,'<f4').reshape(-1,2)
    if len(result)!=end-start:raise ValueError(f'{path.name}: 审片音频有效样点不符')
    return result.mean(axis=1,dtype=np.float64)


def verify_clip(finished, path, a, b):
    v,s=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(path)]))['streams']
    n=b-a; samples=n*(RATE//FPS)
    if (v['codec_type'],v['width'],v['height'],v['nb_frames'],v['avg_frame_rate'],v['start_pts'],v['color_space'],v['color_range'])!=(
            'video',W,H,str(n),'30/1',0,'bt709','tv'):
        raise ValueError(f'{path.name}: 非 1080p30 原倍速审片')
    if Fraction(v['time_base'])*v['duration_ts']!=Fraction(n,30):
        raise ValueError(f'{path.name}: 视频时长或帧时间基准不符')
    if (s['codec_name'],s['sample_rate'],s['start_pts'],s['duration_ts'],s['time_base'])!=('aac',str(RATE),0,samples,'1/48000'):
        raise ValueError(f'{path.name}: 审片音轨样点或时长不符')
    on=source_pcm(path,0,samples)
    ref=source_pcm(finished,a*1600,b*1600)
    # Edge guard excludes AAC preroll and the final encoder's presentation pad.
    rec=on[1024:-1024]; rec-=rec.mean(); nr=np.sqrt((rec**2).sum())
    def similarity(lag):
        r=ref[1024+lag:samples-1024+lag].copy(); r-=r.mean()
        return float((rec*r).sum()/(nr*np.sqrt((r**2).sum())))
    value,lag=max((similarity(i),i) for i in range(-8,9))
    if abs(lag)>1 or value<.985:
        raise ValueError(f'{path.name}: 音频对齐未匹配成片：{lag} samples, r={value:.6f}')
    return {'frames':n,'dimensions':[W,H],'fps':'30/1','duration_seconds_exact':f'{n}/30',
            'clip_audio_samples':samples,'pcm_comparison_peak_lag_samples':lag,'pcm_comparison_r':round(value,8)}


def clip_rate_args():
    # setpts can clear the last frame's inferred duration unless the MP4
    # encoder is given the already-verified cadence explicitly.
    return ['-r',str(FPS),'-fps_mode','cfr']


def excerpt(finished, qa, label, a, b, sums):
    name=qa/f'{label}_F{a:04d}-F{b-1:04d}_1080p_1x.mp4'
    t=max(0,a//FPS-1)  # Exact whole-second anchor; showinfo verifies the true source range.
    head,tail=a-t*FPS,b-t*FPS
    graph=(f'[0:v:0]trim=start_frame={head}:end_frame={tail},showinfo,setpts=PTS-STARTPTS[v];'
           f'[1:a:0]atrim=start_sample={a*1600}:end_sample={b*1600},asetpts=PTS-STARTPTS[a]')
    for crf in (18,20,22,24):
        cmd=['ffmpeg','-hide_banner','-nostdin','-v','info','-xerror','-n','-threads','3','-ss',str(t),'-i',str(finished),
             '-threads','1','-i',str(finished),'-filter_complex_threads','2','-filter_complex',graph,
             '-map','[v]','-map','[a]','-c:v','libx264','-preset','fast','-crf',str(crf),
             '-profile:v','high','-pix_fmt','yuv420p','-threads','3',*clip_rate_args(),*COLOR,
             '-c:a','aac','-b:a','224k','-ar',str(RATE),'-movie_timescale','48000','-movflags','+faststart',str(name)]
        p=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,check=True)
        if name.stat().st_size<=ASSET_LIMIT:break
        name.unlink()
    else: raise ValueError(f'{name.name}: 1080p 片段大小超过 8.5 MB')
    tick,rows=showinfo_frames(p.stderr)
    if len(rows)!=b-a or any(Fraction(pts)*tick+t!=Fraction(i,30) for i,(pts,_) in enumerate(rows,a)):
        raise ValueError(f'{name.name}: 审片片段源帧时码错位')
    if (rows[0][1],rows[-1][1])!=(sums[a],sums[b-1]):
        raise ValueError(f'{name.name}: 片段端点画面不是原成片同时间点')
    return {**identity(name),**verify_clip(finished,name,a,b),'source_frame_range_half_open':[a,b],
            'source_first':cue(a),'source_last':cue(b-1),'pre_reencode_yuv_endpoint_checksums':[sums[a],sums[b-1]],
            'review_only_crf':crf,'speed':1,'no_overlay':True}


def export_reviews(finished, qa, plan, native):
    thumbs,hero,sums,metrics,black=checked_stills(finished,qa,plan,native)
    maps={'hero_stills':hero,'lamp_fixtures':board_lamps(qa,hero),'transition_timeline':board_transitions(qa,thumbs)}
    maps['full_speed_clips']=[]
    for name,a,b in EXCERPTS:
        item=excerpt(finished,qa,name,a,b,sums)
        maps['full_speed_clips'].append(item)
        print('REVIEW',item['file'],item['bytes'],'sync',item['pcm_comparison_peak_lag_samples'],flush=True)
    return {**maps,'full_sequential_decode_without_errors':True,'decoded_black_endpoints':black,
            'frame_metrics':metrics,'source':'finished H.264/AAC mux','coordinate_system':'0-based film frames at 30 fps'}

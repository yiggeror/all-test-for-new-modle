#!/usr/bin/env python3
"""Gate 3 independent picture-only structural and decoded QA."""
import argparse,hashlib,json,math,struct,subprocess
from fractions import Fraction
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from assemble import FPS,Plan,load_sources,compose,font,FRAME_LIMIT
from review_cues import SAMPLES

W,H=1920,1080
Y=W*H;C=Y//4
SRC_FILTER='scale=1920:1080:flags=neighbor:out_color_matrix=bt709:out_range=tv,format=yuv420p'
FAST_DECODE_THREADS='5'

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def structure(p):
    cmd=['ffprobe','-v','error','-show_format','-show_streams','-show_packets','-show_entries',
         'format:stream=index,codec_name,codec_type,profile,level,codec_tag_string,width,height,pix_fmt,r_frame_rate,avg_frame_rate,duration,nb_frames,time_base,color_space,color_range,has_b_frames:packet=flags,pts,duration',
         '-of','json',str(p)]
    raw=json.loads(subprocess.check_output(cmd))
    streams=raw['streams']
    assert len(streams)==1 and streams[0]['codec_type']=='video','video-only exactly'
    m=streams[0];arr=raw['packets']
    assert (m['codec_name'],m['profile'],m['width'],m['height'],m['pix_fmt'],m['avg_frame_rate'])==('h264','High',1920,1080,'yuv420p','30/1'),m
    assert m['color_space']=='bt709' and m['color_range']=='tv',m
    tick=Fraction(m['time_base']);one=1/Fraction(FPS)/tick
    assert len(arr)==FRAME_LIMIT and int(m['nb_frames'])==FRAME_LIMIT,(len(arr),m)
    pts=sorted(int(x['pts']) for x in arr)
    assert pts==[i*one for i in range(FRAME_LIMIT)],'no gap, duplicate, dropped frame or nonzero first PTS'
    assert all(int(x['duration'])==one for x in arr),'non-CFR packet duration'
    assert abs(float(m['duration'])-FRAME_LIMIT/FPS)<1e-5
    key=[int(x['pts'])/int(one) for x in arr if 'K' in x.get('flags','')]
    assert key[0]==0 and max(np.diff(key))<=60,key
    flags={}
    with p.open('rb') as f:
        while f.tell()<p.stat().st_size:
            off=f.tell();size,tag=struct.unpack('>I4s',f.read(8))
            if size==1:size=struct.unpack('>Q',f.read(8))[0]
            flags[tag.decode('ascii','replace')]=off
            if size==0:break
            f.seek(off+size)
    assert flags['moov']<flags['mdat']
    return dict(resolution=[m['width'],m['height']],profile=m['profile'],codec=m['codec_name'],pix_fmt=m['pix_fmt'],
                fps=m['avg_frame_rate'],bt709=True,faststart=True,pts_checked=len(pts),timing_exact=True,
                duration_s=int(len(pts))/FPS,sha256=digest(p),bytes=p.stat().st_size,
                packet_step=int(one),max_gop=int(max(np.diff(key))),bit_rate_bps=int(raw['format']['bit_rate']),
                video_only=True,max_positive_pts=int(pts[-1]))

def read_config(qa):
    j=json.loads((qa/'picture_plan.json').read_text(encoding='utf-8'))
    p=Plan(tuple(x['center_frame'] for x in j['t']),dissolve=j['t'][0]['duration_frames'],tail=j['tail_fade_frames'])
    p.validate()
    return p,j

def rgb_oracle(p,arrs,inds):
    frames=np.stack([compose(p,arrs,i) for i in inds])
    cmd=['ffmpeg','-v','error','-nostdin','-filter_threads','1','-f','rawvideo','-pixel_format','rgb24',
         '-video_size','320x180','-framerate','30','-i','pipe:0','-vf','scale=1920:1080:flags=neighbor',
         '-f','rawvideo','-pix_fmt','rgb24','-threads','1','pipe:1']
    r=subprocess.run(cmd,input=frames.tobytes(),stdout=subprocess.PIPE,check=True).stdout
    a=np.frombuffer(r,np.uint8).reshape(len(inds),H,W,3)
    for b,c in zip(a,frames):
        expected=np.repeat(np.repeat(c,6,axis=0),6,axis=1)
        assert np.array_equal(b,expected),'pre-encode FFmpeg transform was not literal 6× NN'
    return dict(sample_frames=inds,channel_differences_against_explicit_repeat=0)

def yuv_expected(p,arrs,inds):
    frames=np.stack([compose(p,arrs,i) for i in inds])
    cmd=['ffmpeg','-v','error','-nostdin','-filter_threads','1','-f','rawvideo','-pixel_format','rgb24',
         '-video_size','320x180','-framerate','30','-i','pipe:0','-vf',SRC_FILTER,'-f','rawvideo','-pix_fmt','yuv420p','-threads','1','pipe:1']
    raw=subprocess.run(cmd,input=frames.tobytes(),stdout=subprocess.PIPE,check=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(len(inds),Y+2*C)

def poster_yuv_to_rgb(raw):
    # Only for the review contact card; QA metrics above compare all exact YUV bytes.
    yc=raw[:Y].reshape(H,W)[3::6,3::6]
    uc=raw[Y:Y+C].reshape(H//2,W//2)[1::3,1::3]
    vc=raw[Y+C:].reshape(H//2,W//2)[1::3,1::3]
    c=np.maximum(0.,(yc.astype(np.float32)-16)*255/219)
    d=(uc.astype(np.float32)-128)*255/224;e=(vc.astype(np.float32)-128)*255/224
    return np.rint(np.clip(np.stack([c+1.5748*e,c-.187324*d-.468124*e,c+1.8556*d],axis=2),0,255)).astype(np.uint8)

def scan_decode(file,p,arr,inds,storyidx):
    ref=yuv_expected(p,arr,inds)
    sel='+'.join(f'eq(n,{n})' for n in inds)
    cmd=['ffmpeg','-v','error','-xerror','-nostdin','-threads',FAST_DECODE_THREADS,'-i',str(file),
         '-vf',f"select='{sel}'",'-fps_mode','passthrough','-pix_fmt','yuv420p','-f','rawvideo','-threads','1','pipe:1']
    ff=subprocess.Popen(cmd,stdout=subprocess.PIPE)
    mae={};cards={}
    for k,i in enumerate(inds):
        b=ff.stdout.read(Y+2*C)
        assert len(b)==Y+2*C,(i,len(b))
        a=np.frombuffer(b,np.uint8)
        dx=np.abs(a.astype(np.int16)-ref[k])
        mae[i]={'Y_RGB_ffmpeg_BT709_mean_abs_diff':float(dx[:Y].mean()),
                 'U_mean_abs_diff':float(dx[Y:Y+C].mean()),
                 'V_mean_abs_diff':float(dx[Y+C:].mean()),
                 'Y_greater_than_12_share':float(np.mean(dx[:Y]>12))}
        if i in storyidx:cards[i]=poster_yuv_to_rgb(a)
        if i in (0,FRAME_LIMIT-1):
            assert np.max(np.abs(a[:Y].astype(np.int16)-16))<=1 and np.max(np.abs(a[Y:].astype(np.int16)-128))<=1
    assert not ff.stdout.read(1) and ff.wait()==0,'full H.264 stream did not decode cleanly'
    return mae,cards

def poster(p,cards,order,path):
    d=Image.new('RGB',(1660,722),'#1b272d');draw=ImageDraw.Draw(d)
    draw.text((20,10),'Gate 3.5 / v2.5 成片转场 · 实解码抽帧',font=font(29),fill='#fff0d6')
    draw.text((21,50),'每行是同一转场的五个时刻。图上的文字不在成片里。',font=font(18),fill='#aebfbf')
    for j in range(3):
        y=91+j*209
        for n,k in enumerate(order[j]):
            x=20+326*n
            d.paste(Image.fromarray(cards[k]),(x,y))
            draw.text((x+1,y+182),f'{k/FPS:07.3f}s · {k}',font=font(15),fill='#edbc89' if n==2 else '#cbd6d6')
    d.save(path,quality=95,subsampling=0)

def main():
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument('--native-dir',type=Path,required=True)
    arg.add_argument('--qa-dir',type=Path,required=True)
    arg.add_argument('--picture',type=Path)
    arg.add_argument('--pre-encode-only',action='store_true')
    a=arg.parse_args()
    if not a.pre_encode_only and a.picture is None:
        arg.error('--picture is required unless --pre-encode-only')
    qa=a.qa_dir;p,j=read_config(qa);arr,rows=load_sources(a.native_dir)
    holds={scene:{'count':row['adjacent_equal_count'],'indices':row['adjacent_equal_cycle_indices']} for scene,row in rows.items()}
    nc=[0,15,45,*p.centers,3450,4454,4800,p.tail_begin,FRAME_LIMIT-1]
    orig=rgb_oracle(p,arr,nc)
    (qa/'nearest_neighbor_native_qa.json').write_text(json.dumps(orig,indent=2)+'\n')
    if a.pre_encode_only:
        print('NEAREST_NN_PASS',orig);return
    f=a.picture
    stat=structure(f)
    (qa/'picture_structural_qa.json').write_text(json.dumps(stat,indent=2)+'\n')
    print('STRUCTURAL_OK',stat,flush=True)
    order=[[lo-10,c-15,c,c+15,hi+10] for c,(lo,hi) in zip(p.centers,p.intervals)]
    days=[n for group in order for n in group]
    wr=[]
    for e in j['verified_internal_phase_wraps']:
        n=e['film_frame']
        wr.extend([n-1,n])
    in_diss=[n for lo,hi in p.intervals for n in (lo-1,lo,hi-1,hi)]
    reds=[1534,1563,1600,1604,2601]
    inds=sorted(set([0,5,25,45,225,1070,*days,*in_diss,*wr,*reds,p.tail_begin,5870,FRAME_LIMIT-1,*(i for _,i in SAMPLES)]))
    qa_dec,cards=scan_decode(f,p,arr,inds,days)
    poster(p,cards,order,qa/'encoded_transition_storyboard.jpg')
    report=dict(structure=stat,input_nn_check=orig,decoded_frames=inds,changed_bytes={'reason':'Expected CRF14 loss after correct NN; no resized-input blend or decode before production composition','stats':qa_dec},
       full_decode_without_ffmpeg_errors=True,black_open_and_close=True,loop_wrap_sample_frames=wr,
       source_native_adjacent_equal_holds=holds,
       hold_policy="Scheduled source holds retained as separate 30fps picture frames; independently verify packet PTS, not pixel inequality.",
       mean_luma_mae=float(np.mean([a['Y_RGB_ffmpeg_BT709_mean_abs_diff'] for a in qa_dec.values()])),
       target_red_season_luma_mae={i:qa_dec[i]['Y_RGB_ffmpeg_BT709_mean_abs_diff'] for i in reds})
    (qa/'picture_complete_qa.json').write_text(json.dumps(report,indent=2)+'\n')
    print('DECODE_QA_OK',len(inds),round(report['mean_luma_mae'],5),report['target_red_season_luma_mae'],flush=True)

if __name__=='__main__':main()

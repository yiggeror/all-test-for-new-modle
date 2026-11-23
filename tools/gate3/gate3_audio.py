#!/usr/bin/env python3
"""Gate 3 春夏秋冬完整配乐。Python 3 + NumPy + SciPy + FFmpeg 7；只读已核验的本地原曲。
例：python tools/gate3_audio.py --music /path/green.mp3 --out delivery --scratch lab/mix
不截短、移调、加速或循环音乐。环境声与拟音均为确定性程序合成，不需外部采样。
"""
import argparse, hashlib, json, math, os, re, subprocess as sp
from pathlib import Path
import numpy as np
from scipy import ndimage, signal
from scipy.io import wavfile

SR=48000
SYN_SR=24000
FPS=30
PICTURE_FRAMES=5917
ORIGINAL_SAMPLES=9466286
TOTAL=PICTURE_FRAMES*SR//FPS
SOURCE_HASH='f6feac60dc29b89ea1513e04d0b30addf86f9c8576827e7566e27b5abd522e71'
AUDIO_URL='https://html-classic.itch.zone/html/19949767/media/Green%20Tea.mp3'
LICENSE_PAGE='https://purrplecat.itch.io/bloom'
LICENSE='https://creativecommons.org/licenses/by/4.0/'
TRANSITIONS=(48,96,144)
PICTURE_TAIL_START=193.4
PICTURE_TAIL_BLACK=197.2
AMBIENCE_HEAD_END=1.5
WIDTH=2.
WINTER_ORIGIN=143.
SUMMER_ORIGIN=47.
PICTURE_LOOP=11.
SOURCE_PAPER_WINDOW=(4.30,6.90)
SOURCE_PAPER_CENTERS=(5.21,5.64,6.28)
START=(0,47,95,143)
END=(49,97,145,TOTAL/SR)
SEASONS=('spring','summer','autumn','winter')


def ff(*args):return ['ffmpeg','-hide_banner','-v','error','-y',*map(str,args)]
def check(cmd,**kwargs):return sp.run(cmd,check=True,**kwargs)
def db(x):return 10.0**(x/20.)
def time(n):return np.arange(n,dtype=np.float64)/SYN_SR
def n_at(t,sr=SR):return int(round(t*sr))
def digest(path):
    with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rmsdb(a):return 20*math.log10(max(1e-12,float(np.sqrt(np.mean(np.square(a,dtype=np.float64))))))
def write(path,y):wavfile.write(str(path),SR,y.astype(np.float32,copy=False))
def export_flac(p,y):
    cmd=ff('-f','f32le','-ar',SR,'-ac',2,'-i','-','-c:a','flac','-sample_fmt','s32','-bits_per_raw_sample',24,'-compression_level',8,p)
    check(cmd,input=np.ascontiguousarray(y,dtype='<f4').tobytes())
def decode(src,eq=None):
    cmd=ff('-threads',1,'-i',src,'-map','0:a:0','-vn','-af',eq or 'anull','-ar',SR,'-ac',2,'-f','f32le','-')
    return np.frombuffer(sp.check_output(cmd),'<f4').reshape(-1,2).copy()
def probe(src):
    return json.loads(sp.check_output(['ffprobe','-v','error','-select_streams','a:0','-show_streams','-show_format','-of','json',str(src)]))


def measured_lufs(a):
    # BS.1770 K-weighting 48 kHz, 0.4 s blocks / 0.1 s advance, stereo unit channel weights.
    sos=np.array([[1.53512485958697,-2.69169618940638,1.19839281085285,1.,-1.69065929318241,.73248077421585],
                  [1.,-2.,1.,1.,-1.99004745483398,.99007225036621]],dtype=np.float32)
    filtered=signal.sosfilt(sos,a,axis=0)
    hop=4800;m=len(filtered)//hop
    e=np.square(filtered[:m*hop],dtype=np.float32).reshape(m,hop,2).sum(axis=(1,2),dtype=np.float64)/hop
    blocks=np.convolve(e,np.ones(4)*.25,mode='valid')
    a_mask=blocks>=10**((-70+.691)/10)
    if not a_mask.any():return -100.
    gate=max(10**((-70+.691)/10),blocks[a_mask].mean()*.1)
    return float(-.691+10*np.log10(blocks[blocks>=gate].mean()))


def true_meter(src):
    cmd=['ffmpeg','-hide_banner','-nostats','-i',str(src),'-map','0:a:0','-vn','-af','loudnorm=print_format=json','-f','null','-']
    st=check(cmd,capture_output=True,text=True).stderr;r=json.loads(st[st.rfind('{'):st.rfind('}')+1]); return {'integrated_lufs':float(r['input_i']),'lra_lu':float(r['input_lra']),'true_peak_dbtp':float(r['input_tp'])}


def filtering(a,lo=None,hi=None,order=3):
    kind='bandpass' if lo and hi else 'highpass' if lo else 'lowpass'
    w=[lo,hi] if lo and hi else lo if lo else hi
    return signal.sosfilt(signal.butter(order,w,fs=SYN_SR,btype=kind,output='sos').astype(np.float32),a,axis=0)

def white(rng,n):return rng.standard_normal(n,dtype=np.float32)
def norm(a):return a/max(1.e-8,float(np.sqrt(np.mean(np.square(a,dtype=np.float32)))))
def noise(rng,n,lo,hi,order=3):return norm(filtering(white(rng,n),lo,hi,order))
def smooth_shape(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def slow_drift(rng,t,spans=(3.2,11.4),strength=(.06,.10)):
    result=np.ones(len(t),np.float32)
    for pace,amp in zip(spans,strength):
        knots=np.arange(-pace,float(t[-1])+2*pace,pace)
        v=rng.uniform(-1.,1.,len(knots));i=np.searchsorted(knots,t,side='right')-1
        u=smooth_shape((t-knots[i])/pace);result+=amp*(v[i]+(v[i+1]-v[i])*u).astype(np.float32)
    return result

def pan(x,p):
    a=float(np.pi/4)*(p+1.);return np.stack((x*np.cos(a),x*np.sin(a)),1)

def diffuse(rng,n,lo,hi,side):
    mid=noise(rng,n,lo,hi);l=noise(rng,n,lo*1.12,hi*.90);r=noise(rng,n,lo*1.09,hi*.94)
    l1=math.sqrt(1.-side**2)*mid + side*l
    r1=math.sqrt(1.-side**2)*mid + side*r
    return np.stack((l1,r1),1)

def edge_ramp(x,first=.055,last=.10):
    x=x.copy();n=n_at(first,SYN_SR);m=n_at(last,SYN_SR)
    x[:n]*=smooth_shape(np.linspace(0.,1.,n))[:,None]
    x[-m:]*=smooth_shape(np.linspace(1.,0.,m))[:,None]
    return x

def add_event(dst,tstart,event):
    i=n_at(tstart,SYN_SR);j=min(i+len(event),len(dst));lo=max(0,i)
    if j>lo:dst[lo:j]+=event[lo-i:j-i]


def spring(n):
    rng=np.random.default_rng(12611);t=time(n)
    both=diffuse(rng,n,105,560,.33)*.74+diffuse(rng,n,230,1050,.60)*.20
    swell=slow_drift(rng,t,(2.4,7.9,13.1),(.12,.15,.06))
    body=both*swell[:,None]
    # 枝头远处叶尖随同一阵轻风抬起，起落不刻意描绘单朵花。
    for sec,dur,amt,pos in ((5.7,1.9,.085,-.32),(13.8,2.8,.095,.28),(24.2,2.1,.10,-.43),(35.4,2.4,.087,.22),(42.2,2.0,.074,-.20)):
        nt=n_at(dur,SYN_SR);x=np.linspace(0,1,nt);g=np.sin(np.pi*x)**2
        grain=noise(rng,nt,460,1390)*g
        add_event(body,sec,pan(grain*amt,pos))
    return edge_ramp(body),[]


def summer(n):
    rng=np.random.default_rng(40969);t=time(n)
    near=diffuse(rng,n,240,1650,.60)*.77
    road=diffuse(rng,n,125,600,.37)*.32
    glo=slow_drift(rng,t,(2.8,7.1,19.6),(.065,.095,.045));body=(near+road)*glo[:,None]
    # 雨在棚与湿街两种表面；同一初始化种子，滴点不循环复用。
    rain_ev=[]
    # 可见檐滴的一部分比路面略近，其他小滴属场景内远雨。
    for k in range(5):
        root=k*PICTURE_LOOP
        for t0 in (2.53,4.35,7.87):
            sec=root+t0 + rng.uniform(-.035,.042)
            if sec>=float(t[-1])-.18:continue
            dur=float(rng.uniform(.055,.113));nt=n_at(dur,SYN_SR);u=time(nt)
            f=float(rng.uniform(418,713));v=float(rng.uniform(130,.41*1000))
            resonance=np.sin(2*np.pi*f*u)*np.exp(-u/float(rng.uniform(.009,.026)))
            sound=(.38*noise(rng,nt,440,1570)*np.exp(-u/.012)+.17*resonance+.05*np.sin(2*np.pi*v*u)*np.exp(-u/.034))
            sound*=smooth_shape(u/.007)*smooth_shape((dur-u)/.025)
            amp=float(rng.uniform(.30,.54));pos=float(rng.uniform(-.46,-.13))
            add_event(body,sec,pan(sound*amp,pos))
            rain_ev.append(round(SUMMER_ORIGIN+sec,4))
    # 留下滴水质感，滤掉表面白噪声。4阶低通后再叠3阶高切。
    body=filtering(filtering(body,hi=1650,order=4),hi=2250,order=3).astype(np.float32)
    return edge_ramp(body),rain_ev


def autumn(n):
    rng=np.random.default_rng(87203);t=time(n)
    main=diffuse(rng,n,150,770,.38)*.67+diffuse(rng,n,300,1160,.62)*.24
    body=main*slow_drift(rng,t,(3.1,7.9,14.2),(.13,.17,.08))[:,None]
    leaf_times=(4.08,6.73,11.42,17.6,20.25,23.82,28.21,33.85,37.1,42.9,46.82)
    for place in leaf_times:
        side=float(rng.uniform(-.61,.58));dur=float(rng.uniform(.73,1.73));nt=n_at(dur,SYN_SR); x=np.linspace(0.,1.,nt)
        soft=np.sin(np.pi*x)**2
        texture=(.65*noise(rng,nt,590,1760)+.35*noise(rng,nt,980,2100))*soft
        for _ in range(int(rng.integers(6,14))):
            p=float(rng.uniform(.10,.91));w=float(rng.uniform(.014,.033));texture+=.20*noise(rng,nt,620,1820)*np.exp(-.5*((x-p)/w)**2)
        add_event(body,place,pan(texture*float(rng.uniform(.14,.27)),side))
    return edge_ramp(body),[round(START[2]+x,4) for x in leaf_times]


def winter(n):
    rng=np.random.default_rng(20171223);t=time(n)
    common=noise(rng,n,94,630);l=noise(rng,n,155,1160);r=noise(rng,n,170,1090)
    extra=slow_drift(rng,t,(3.6,12.7,21.),(.12,.15,.05));gust=(.72+.085*np.sin(2*np.pi*t/10.7+.8)+.060*np.sin(2*np.pi*t/6.3))*extra
    # 保留 Gate 2 雪院风的可识别声底，不把低频风写成持续的音乐音符。
    body=np.stack((gust*(.84*common+.26*l),gust*(.84*common+.29*r)),1).astype(np.float32)
    hum=(np.sin(2*np.pi*112*t)+.31*np.sin(2*np.pi*224*t+.23))*(1+.07*np.sin(2*np.pi*.14*t));body+=np.stack((.021*hum,.047*hum),1).astype(np.float32)
    cues=[]
    for cycle in range(5):
        offset=cycle*PICTURE_LOOP;event_group=[]
        strengths=np.array([.33,.67,.36])*float(rng.uniform(.81,1.10))*(.84 if cycle==4 else 1.)
        for j,(center,width) in enumerate(zip(SOURCE_PAPER_CENTERS,(.077,.149,.083))):
            tau=(float(center)+offset);length=width*8.; nt=n_at(length,SYN_SR); u=time(nt)-length/2
            rough=.62*noise(rng,nt,485,1450)+.38*noise(rng,nt,765,2600)
            rough=filtering(rough,hi=1910,order=3)
            env=np.exp(-.5*(u/width)**2);grain=.83+.17*np.sin(2*np.pi*(19.5+j)*u+.27*np.sin(2*np.pi*8.4*u))
            roll=rough*env*grain*strengths[j]
            # 暖窗偏右，透玻璃，最弱三笔，不冒充在室内听雪。
            a=np.stack((roll*.27,roll*.80),1)
            add_event(body,tau-length*.5,a)
            event_group.append(round(WINTER_ORIGIN+tau,5))
        start=WINTER_ORIGIN+offset
        cues.append({'visible_window_s':[round(start+x,5) for x in SOURCE_PAPER_WINDOW],'brush_center_s':event_group,'brush_center_frames':[round(x*FPS) for x in event_group]})
    return edge_ramp(body),cues


def tr_range(j):
    return n_at(START[j]),n_at(END[j])

def weights(n,start_frame,end_frame):
    u=(np.arange(end_frame-start_frame,dtype=np.float64)/float(end_frame-start_frame))
    return np.cos(np.pi/2*u).astype(np.float32),np.sin(np.pi/2*u).astype(np.float32)

def ambience(full_mix_dir):
    amb=np.zeros((TOTAL,2),np.float32);ev={};per_season={};cues=[];err=[]
    dry=[]
    for j,fn in enumerate((spring,summer,autumn,winter)):
        a,b=tr_range(j); n=b-a
        base,ev[SEASONS[j]]=fn((n+1)//2)
        band=signal.resample_poly(base,2,1,axis=0,window=('kaiser',8.5))[:n].astype(np.float32)
        local_lu=measured_lufs(band)
        target=(-31.1,-30.75,-31.45,-31.35)[j]
        band*=db(target-local_lu)
        per_season[SEASONS[j]]={'film_support_sec':[START[j],END[j]],'approx_calibration_lufs_before_fades':round(measured_lufs(band),2),'raw_rms_dbfs_before_fades':round(rmsdb(band),2)}
        if j:
            lo,hi=[n_at(TRANSITIONS[j-1]+d) for d in (-WIDTH/2.,WIDTH/2.)]; w_out,w_in=weights(n,lo,hi)
            band[:hi-lo]*=w_in[:,None]
            err.append(float(np.max(np.abs(w_out**2+w_in**2-1.))))
            cues.append({'center_s':TRANSITIONS[j-1], 'center_frame':TRANSITIONS[j-1]*FPS,'window_s':[(lo/SR),(hi/SR)], 'sample_range_half_open':[lo,hi], 'overlap_samples':hi-lo,'law':'cos/sin equal power; both gains 0.7071068 at midpoint'})
        if j<3:
            lo,hi=[n_at(TRANSITIONS[j]+d) for d in (-WIDTH/2.,WIDTH/2.)];w_out,_=weights(n,lo,hi);band[-(hi-lo):]*=w_out[:,None]
        if j==0:
            # 同步画面 1.5 秒柔入；音轨 0 点本身已有原曲极轻暖头，不淡入或修改原曲。
            h=n_at(AMBIENCE_HEAD_END);band[:h]*=np.sin(.5*np.pi*np.arange(h)/h)[:,None]**2
        if j==3:
            z0=n_at(PICTURE_TAIL_START)-a;z1=n_at(PICTURE_TAIL_BLACK)-a
            band[z0:z1]*=(np.cos(.5*np.pi*np.arange(z1-z0)/(z1-z0))**2)[:,None];band[z1:]=0
        # 过于响的片首尾环境会孤立音乐。只做缓慢手工场景声电平包络，不动态压缩乐轨。
        nodes=np.array([0,3,8,14,22,166,174,179,185,191.3,193.4,197.233333333]); vals=np.array([-6.2,-5,-3.7,-1.7,0,0,-1.1,-2.4,-5.3,-11.4,-13.2,-14.0]);
        ar=np.arange(a,b,dtype=np.float64)/SR; i=np.clip(np.searchsorted(nodes,ar,side='right')-1,0,len(nodes)-2); u=smooth_shape((ar-nodes[i])/(nodes[i+1]-nodes[i])); envelope=db(vals[i]+(vals[i+1]-vals[i])*u)
        band*=envelope.astype(np.float32)[:,None]
        amb[a:b]+=band
        dry.append((a,b,band))
    # 整体目标约比音乐 −15 LU，计算采用与成片相同的K计权并门限。
    amb_gain=db(-31.20-measured_lufs(amb));amb*=amb_gain
    # 文件长度保留独立章节的实际时间段，另有全片统一时间基准的环境总轨。
    for j,(a,b,y) in enumerate(dry):
        y*=amb_gain;per_season[SEASONS[j]]['lufs_with_fades_and_full_length_relative_to_support']=round(measured_lufs(y),3)
        if full_mix_dir:write(full_mix_dir/(SEASONS[j]+'_ambience_faded.wav'),y)
    return amb,{'season_metrics':per_season,'transition_cues':cues,'max_equal_power_error_float32':max(err),'source_visual_action_s':ev,'initial_fade_s':[0,AMBIENCE_HEAD_END],'winter_air_tail_fade_s':[PICTURE_TAIL_START,PICTURE_TAIL_BLACK],'quiet_ride_time_s':nodes.tolist(),'quiet_ride_adjustment_db':vals.tolist()}


def release_aac(wav,p):
    check(ff('-i',wav,'-map','0:a','-vn','-c:a','aac','-profile:a','aac_low','-aac_coder','twoloop','-b:a','256k','-ar',SR,'-ac',2,'-movie_timescale','48000','-movflags','+faststart','-metadata','title=Four seasons | Green Tea', '-metadata','artist=Purrple Cat (music); project (sound design)', '-metadata','comment=Original Green Tea by Purrple Cat; https://purrplecat.itch.io/bloom ; CC BY 4.0 https://creativecommons.org/licenses/by/4.0/ ; full song, level and mild EQ, season ambience, synced to picture.',p))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--music',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--scratch',type=Path,required=True);ap.add_argument('--no-stems',action='store_true');args=ap.parse_args();out,tmp=args.out,args.scratch;out.mkdir(exist_ok=True,parents=True);tmp.mkdir(exist_ok=True,parents=True)
    source=args.music;sha=digest(source)
    if sha!=SOURCE_HASH:raise ValueError(f'驳回原曲版本: SHA256 {sha}')
    y0=decode(source,'aresample=48000,bass=g=-1.5:f=150:w=0.7');n_raw=len(y0)
    if n_raw!=ORIGINAL_SAMPLES:raise ValueError(f'原曲未全长解码 {n_raw}')
    orig_i=measured_lufs(y0)
    m=np.pad(y0,((0,TOTAL-n_raw),(0,0)));mg=-16.18-orig_i;m*=db(mg);del y0
    print(f'Complete music {n_raw} frames @48k, {orig_i:.2f} LUFS pre-gain; synth environment',flush=True)
    env,env_report=ambience(None if args.no_stems else tmp)
    total=m+env;g=-16.00-measured_lufs(total);total*=db(g);m*=db(g);env*=db(g)
    # 分别量化总轨及音乐/环境分轨；没有强制动态压缩或削波以求整数响度。
    if np.max(abs(total))>=1.:raise ValueError('master would clip')
    wav=tmp/'full_pcm_float.wav'; write(wav,total)
    temp_aac=tmp/'green_tea_gate3.m4a';release_aac(wav,temp_aac)
    print(f'AAC written {temp_aac.stat().st_size} bytes; reference meter and comparison',flush=True)
    meter=true_meter(temp_aac)
    if not (-16.5<=meter['integrated_lufs']<=-15.5 and meter['true_peak_dbtp']<=-1.5):raise ValueError(meter)
    p=out/'green_tea_gate3.m4a';part=out/'green_tea_gate3.part.m4a';part.write_bytes(temp_aac.read_bytes());os.replace(part,p)
    exported=probe(p);stream=exported['streams'][0]
    dec0=decode(p);dec=dec0[:TOTAL];diff=dec-total
    if len(dec)!=TOTAL or not np.isfinite(dec).all():raise ValueError('missing/invalid AAC samples')
    check_timing=signal.correlate(dec[48000:100000,0],total[48000:100000,0],method='fft');lag=int(np.argmax(check_timing)-(52000-1))
    if lag!=0:raise ValueError(('AAC shift from PCM',lag))
    nonzero=np.flatnonzero(np.max(np.abs(m[:ORIGINAL_SAMPLES]),axis=1)>db(-100));last_music=round(float(nonzero[-1])/SR,8)
    if not np.all(m[ORIGINAL_SAMPLES:]==0):raise ValueError('music stem carries past origin')
    maxjump=[]; local_pairs={}
    for cue in env_report['transition_cues']:
        for s in cue['window_s']:
            i=n_at(s); zz=env[i-1:i+1]; near=abs(np.diff(env[i-9600:i+9600],axis=0)).ravel();j=float(np.max(abs(zz[1]-zz[0])));maxjump.append({'boundary_s':s,'step':round(j,9),'p99_local_steps':round(float(np.quantile(near,.99)),9),'music_elapsed_s':s})
    ranges=[(6,43),(50,94),(98,142),(146,187)]
    for name,(a,b) in zip(SEASONS,ranges):
        i,j=n_at(a),n_at(b); ms,es=measured_lufs(m[i:j]),measured_lufs(env[i:j]);local_pairs[name]={'interval_s':[a,b], 'music_i_lufs':round(ms,3),'ambience_i_lufs':round(es,3),'difference_lu':round(ms-es,3)}
    f,ps=signal.welch(env[n_at(56):n_at(87)],fs=SR,axis=0,nperseg=4096,noverlap=2048);ps=ps.mean(1); rain={f'{cut}hz_and_above_pct':round(100*float(ps[f>=cut].sum()/ps.sum()),8) for cut in (2000,4000,6000)}
    lufs_m,lufs_a=measured_lufs(m),measured_lufs(env)
    result={'source':{'title':'Green Tea','author':'Purrple Cat','source_page':LICENSE_PAGE,'license_deed':LICENSE,'direct_author_recording_url':AUDIO_URL,'recording_sha256':sha,'whole_recording_kept':True,'source_duration_sec':n_raw/SR,'decoded_source_samples_48000':n_raw,'video_alignment_padding_samples':TOTAL-n_raw,'source_routine':'320 kb/s 44.1 kHz author MP3 -> 48 kHz float and small bass EQ. No trims, rearrangement, music fades or time stretching.', 'music_last_above_minus_100dBFS_after_gain_sec':last_music,'retained_author_silence_sec':(n_raw-1)/SR-last_music},'picture_sync':{'fps':FPS,'frames':PICTURE_FRAMES,'duration_sec':TOTAL/SR,'music_grid_bpm':80,'musical_bar_length_sec':3.,'three_center_bars_numbered_from_1':[17,33,49],'winter_phase_zero_frame':int(WINTER_ORIGIN*FPS),'winter_cycle_frames':int(PICTURE_LOOP*FPS)},'sound_design':env_report,'mastering':{'music_gain_db':round(mg+g,4),'music_bass_shelf_db':-1.5,'bass_shelf_corner_hz':150,'global_mix_gain_db':round(g,4),'mix_untouched_by_limiter':True,'metering':'AAC replay with FFmpeg loudnorm (EBU R128 meter); stem and per-section K-weighted ITU BS.1770 gated integrated.', 'master_pcm_rms_dbfs':round(rmsdb(total),3),'music_i_lufs':round(lufs_m,4),'ambience_i_lufs':round(lufs_a,4),'overall_difference_lu':round(lufs_m-lufs_a,4),'local_pairs':local_pairs,'rain_hf_analysis':rain,'crossfade_audio_step_qa':maxjump},'aac':{'name':p.name,'codec':stream['codec_name'],'profile':stream['profile'],'channels':stream['channels'],'sample_rate_hz':int(stream['sample_rate']),'configured_bitrate_kbps':256,'measured_stream_bitrate_bps':int(stream['bit_rate']),'duration_sec':float(stream['duration']),'start_sec':float(stream['start_time']),'sha256':digest(p),'bytes':p.stat().st_size,'header_hex':p.read_bytes()[:32].hex(' '),'frame_decode_sample_count_including_codec_tail':len(dec0),'timeline_sample_count':TOTAL,'extra_decoder_padding_samples':len(dec0)-TOTAL,'decoded_pcm_rms_dbfs':round(rmsdb(dec),4),'decoded_vs_pcm_snr_db':round(rmsdb(total)-rmsdb(diff),4),'alignment_pcm_vs_decoded_samples':lag,'decoded_sample_peak_abs':round(float(np.max(np.abs(dec))),8),'zero_or_more_clipped_samples_n':int(np.sum(np.abs(dec)>=1)),**meter}}
    if not 14<=result['mastering']['overall_difference_lu']<=16:raise ValueError('overall ambience level outside reviewer target')
    (out/'audio_mix_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result['aac'],ensure_ascii=False),flush=True)
    if not args.no_stems:
        stm=out/'stems';stm.mkdir(exist_ok=True);print('rendering 24-bit lossless deliverable stems',flush=True)
        for x,p0 in ((m,'music_full.flac'),(env,'ambience_full.flac'),(total,'mix_full.flac')):export_flac(stm/p0,x)
        manifest={n.name:{'bytes':n.stat().st_size,'sha256':digest(n),'sample_rate_hz':SR,'samples':TOTAL} for n in sorted(stm.glob('*.flac'))};(stm/'SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()

"""Make review-only crops and A/B images from the *finished*, synchronized mux."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from review_cues import WINDOW_NATIVE_XYWH,REVIEW_START,REVIEW_FRAMES,WINTER_ORIGIN,WINTER_FOLEY_PHASES

W,H=1920,1080
X,Y,CW,CH=(v*6 for v in WINDOW_NATIVE_XYWH)
RATE=48_000
STOP=REVIEW_START+REVIEW_FRAMES
SAMPLE_START,SAMPLE_STOP=REVIEW_START*1600,STOP*1600
CUT=f'trim=start_frame={REVIEW_START}:end_frame={STOP},setpts=PTS-STARTPTS'
CROP=f'crop={CW}:{CH}:{X}:{Y}'
DETAIL=f'{CROP},scale={CW*5}:{CH*5}:flags=neighbor,format=yuv420p'
ATRIM=f'atrim=start_sample={SAMPLE_START}:end_sample={SAMPLE_STOP},asetpts=PTS-STARTPTS'
COLOR=['-color_range','tv','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709']
OUT_OPTIONS=['-pix_fmt','yuv420p',*COLOR,'-r','30','-movie_timescale','48000','-movflags','+faststart',
             '-c:a','aac','-b:a','224k','-ar','48000']

def sha(path):
    with Path(path).open('rb') as p:return hashlib.file_digest(p,'sha256').hexdigest()

def review_clips(finished,out):
    plain=out/'review_winter_1080p_1x.mp4'
    near=out/'review_winter_reader_5x_1x.mp4'
    graph=(f'[0:v:0]{CUT},split=2[vfull][vc];[vc]{DETAIL}[vnear];'
           f'[0:a:0]{ATRIM},asplit=2[afull][anear]')
    subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','error','-xerror','-threads','4',
                    '-filter_complex_threads','2','-i',str(finished),'-filter_complex',graph,
                    '-map','[vfull]','-map','[afull]','-c:v','libx264','-preset','fast','-threads','3',
                    '-crf','18','-profile:v','high',*OUT_OPTIONS,str(plain),
                    '-map','[vnear]','-map','[anear]','-c:v','libx264','-preset','veryfast','-threads','2',
                    '-qp','0',*OUT_OPTIONS,str(near)],check=True)
    return plain,near

def crop_frames(path,nframes):
    selected='+'.join(f'eq(n,{fr})' for fr in nframes)
    command=['ffmpeg','-v','error','-xerror','-nostdin','-threads','4','-filter_threads','2','-i',str(path),'-map','0:v:0','-an',
             '-vf',f"select='{selected}',{CROP},scale=in_color_matrix=bt709:in_range=tv:out_range=pc",
             '-fps_mode','passthrough','-frames:v',str(len(nframes)),'-threads','1','-pix_fmt','rgb24','-f','rawvideo','pipe:1']
    r=subprocess.check_output(command)
    if len(r)!=len(nframes)*CW*CH*3:raise ValueError('Encoded window A/B packet count does not match')
    return np.frombuffer(r,dtype='uint8').reshape(len(nframes),CH,CW,3)

def comparison(finished,prior,out):
    slices=list(range(120,213,4));indices=[WINTER_ORIGIN+s for s in slices]
    old=crop_frames(prior,indices);new=crop_frames(finished,indices)
    cols=6;margin=89;top=45;gutter=8;ystep=CH*2+37
    panel=Image.new('RGB',(margin+(CW+gutter)*cols+14,top+ystep*4+10),(26,31,43));draw=ImageDraw.Draw(panel)
    try:
        font=ImageFont.truetype('DejaVuSans.ttf',13);header=ImageFont.truetype('DejaVuSans.ttf',19)
    except OSError:font=header=ImageFont.load_default()
    draw.text((margin,13),'Winter reader / 1080p delivery decode / matched frames',fill=(234,225,210),font=header)
    for j,(phase,absolute) in enumerate(zip(slices,indices)):
        x=margin+j%cols*(CW+gutter);y=top+j//cols*ystep
        draw.text((x,y),f'F{absolute}  /  f{phase:03d}',fill=(200,209,218),font=font)
        for k,part in enumerate((old,new)):
            Y0=y+20+k*(CH+2);panel.paste(Image.fromarray(part[j]),(x,Y0))
            if j%cols==0:draw.text((22,Y0+CH//2-8),('v2.7','v2.8')[k],fill=((167,185,208),(231,186,136))[k],font=header)
    target=out/'reader_v27_v28_decoded_compare.png';panel.save(target)
    return {'file':target.name,'source_window_1080p_xywh':[X,Y,CW,CH],'frames':indices,'bytes':target.stat().st_size,'sha256':sha(target)}

def probe(path,width,height):
    m=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(path)]))['streams']
    v,a=m
    if (v['codec_type'],v['width'],v['height'],int(v['nb_frames']),v['avg_frame_rate'])!=('video',width,height,REVIEW_FRAMES,'30/1'):
        raise ValueError(f'{path.name}: review geometry or CFR mismatch')
    if Fraction(v['time_base'])*int(v['duration_ts'])!=Fraction(REVIEW_FRAMES,30) or v['start_pts']!=0:
        raise ValueError(f'{path.name}: review picture start/duration changed')
    if (a['codec_type'],a['sample_rate'],int(a['duration_ts']),a['start_pts'],a['time_base'])!=('audio','48000',SAMPLE_STOP-SAMPLE_START,0,'1/48000'):
        raise ValueError(f'{path.name}: missing or shifted clip audio ({a})')
    return {'width':width,'height':height,'duration':v['duration'],'fps':v['avg_frame_rate'],'frames':int(v['nb_frames']),
            'clip_audio_samples':a['duration_ts'],'clip_audio_rate':a['sample_rate'],'clip_start_pts_video_and_audio':[v['start_pts'],a['start_pts']]}

def pcm(path,phase_start,phase_end):
    filt=f'atrim=start_sample={phase_start}:end_sample={phase_end}'
    a=subprocess.check_output(['ffmpeg','-v','error','-xerror','-nostdin','-i',str(path),'-map','0:a:0','-vn',
                               '-af',filt,'-c:a','pcm_f32le','-f','f32le','pipe:1'])
    y=np.frombuffer(a,'<f4').reshape(-1,2)
    if len(y)!=phase_end-phase_start:raise ValueError(f'{path.name}: review clip PCM length mismatch')
    return y.mean(axis=1,dtype=np.float64)

def audio_check(on,ref):
    # Correlate the speech-free music / foley at the two cue centers ±128 samples.
    # This catches differences below a single video frame, even if review AAC is re-encoded.
    def lag(cue):
        j=(WINTER_ORIGIN+cue-REVIEW_START)*1600
        span=24_000;guard=128
        rec=on[j-span:j+span].copy(); rec-=rec.mean()
        refset=ref[j-span-guard:j+span+guard]
        # Full-mask convolution computes all positions in a single FFT. Integrals normalize
        # each candidate window; rec is already zero mean so no mean term in the numerator.
        n=len(rec); m=len(refset); fft_size=1<<(n+m-2).bit_length()
        dot=np.fft.irfft(np.fft.rfft(refset,fft_size)*np.fft.rfft(rec[::-1],fft_size),fft_size)[n-1:m]
        integ=np.r_[0.,np.cumsum(refset)]; sq=np.r_[0.,np.cumsum(refset*refset)]
        window_sum=integ[n:]-integ[:-n]
        centered_energy=np.maximum(sq[n:]-sq[:-n]-window_sum**2/n,1e-15)
        vals=dot/(np.linalg.norm(rec)*np.sqrt(centered_energy))
        q=int(np.argmax(vals));return {'cue_film_frame':WINTER_ORIGIN+cue,'lag_in_samples':q-guard,'correlation':float(vals[q])}
    m=[lag(f) for f in WINTER_FOLEY_PHASES]
    if any(abs(x['lag_in_samples'])>1 or x['correlation']<.99 for x in m):
        raise ValueError(f'review excerpt does not correlate with the finished mix: {m}')
    return m

def frame_payloads(path,filt=None):
    cmd=['ffmpeg','-nostdin','-v','error','-xerror','-threads','4','-filter_threads','2','-i',str(path),
         '-map','0:v:0','-an']
    if filt is not None:cmd+=['-vf',filt,'-frames:v',str(REVIEW_FRAMES)]
    cmd+=['-pix_fmt','yuv420p','-threads','1','-f','framemd5','pipe:1']
    b=subprocess.check_output(cmd,text=True)
    return [row.split(',')[-1].strip() for row in b.splitlines() if not row.startswith('#')]

def export_reviews(finished,prior,out):
    clip_paths=review_clips(finished,out)
    ref=pcm(finished,SAMPLE_START,SAMPLE_STOP)
    info={}
    for path,(w,h) in zip(clip_paths,((W,H),(CW*5,CH*5))):
        info[path.name]={**probe(path,w,h),'encoded_from_finished_mux':True,'bytes':path.stat().st_size,'sha256':sha(path),
                         'source_sound_cue_pcm_compare':audio_check(pcm(path,0,SAMPLE_STOP-SAMPLE_START),ref)}
    original=frame_payloads(finished,f'{CUT},{DETAIL}')
    got=frame_payloads(clip_paths[1])
    if len(got)!=REVIEW_FRAMES or got!=original:raise ValueError('Encoded QP0 crop is not frame-for-frame identical to the actual film crop')
    info[clip_paths[1].name]['exact_decoded_YUV_matches_direct_crop_all_330']=True
    return {'source_film_frame_half_open':[REVIEW_START,STOP],'source_audio_sample_half_open':[SAMPLE_START,SAMPLE_STOP],
            'no_text_no_speed_change':True,'full_presentation_sound_from_finished_mux':True,
            'full_size_original_crop_xywh':[X,Y,CW,CH],'detail_integer_magnification_from_final':5,
            'first_paper_foley_cue_source_frames':[WINTER_ORIGIN+x for x in WINTER_FOLEY_PHASES],
            'review_aac_only_recompressed_main_9247_packets_not_touched':True,
            'clips':info,'comparison':comparison(finished,prior,out)}

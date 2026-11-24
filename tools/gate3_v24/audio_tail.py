#!/usr/bin/env python3
"""Rainroji v2.4: sample-locked full Green Tea and a winter-weather-only outro.

python tools/gate3_v24/audio_tail.py --music Green-Tea.mp3 --out final_audio.m4a --report audio_tail_report.json
Optional --preview-dir exports 3:00-to-end lossless A/B and an actual stem-energy chart.
Only this module is new; tools/gate3/gate3_audio.py is the immutable v2.0 recipe.
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess as sp
import sys
import tempfile

import numpy as np
from scipy import signal

SR = 48_000
FRAMES = 5917
COUNT = 9_467_200
ORIGINAL = 9_466_286
ORIGINAL_BYTES = 8_245_791
SOURCE_SHA = 'f6feac60dc29b89ea1513e04d0b30addf86f9c8576827e7566e27b5abd522e71'
SOURCE_URL = 'https://html-classic.itch.zone/html/19949767/media/Green%20Tea.mp3'
SOURCE_PAGE = 'https://purrplecat.itch.io/bloom'
LEGACY_SCRIPT_SHA = '714968f7637f14cb9950da582f7a15d00e2339d5b1b07508e9cfe4f756ae0200'
LEGACY_PCM_WAV_SHA = '7efa6318c001e3b2f396796b5cae0448f638b320472ad85397f27f4480c91403'
EQ = 'aresample=48000,bass=g=-1.5:f=150:w=0.7'
START = 185 * SR
RISE_END = 9_225_600
FADE_START = 9_336_000
BLACK = 9_465_600
REVIEW_START = 180 * SR
WINTER_START = 143 * SR
RISE_DB = 8.0
JOIN_DB = -5.3
K_SOS = np.array([
    [1.53512485958697, -2.69169618940638, 1.19839281085285, 1., -1.69065929318241, .73248077421585],
    [1., -2., 1., 1., -1.99004745483398, .99007225036621],
], dtype='f8')


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def pcm_sha(x):
    return hashlib.sha256(np.ascontiguousarray(x, dtype='<f4').view('u1')).hexdigest()


def packet_probe(path):
    ff = ['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_streams', '-show_packets',
          '-show_data_hash', 'sha256',
          '-show_entries',
          'stream=codec_name,profile,sample_rate,channels,channel_layout,time_base,start_pts,duration_ts,bit_rate,extradata_hash:'
          'packet=pts,dts,duration,side_data_list,data_hash', '-of', 'json', str(path)]
    d = json.loads(sp.check_output(ff))
    if len(d.get('streams', [])) != 1:
        raise ValueError('expected a unique AAC track')
    a, frames = d['streams'][0], d['packets']
    core = (a['codec_name'], a['profile'], int(a['sample_rate']), a['channels'],
            a['channel_layout'], a['time_base'], a['start_pts'], a['duration_ts'])
    if core != ('aac', 'LC', SR, 2, 'stereo', '1/48000', 0, COUNT):
        raise ValueError(f'bad stream timing/profile: {core}')
    if float(a['bit_rate']) < 237000 or float(a['bit_rate']) > 275000:
        raise ValueError(f'wrong AAC stream bit rate: {a}')
    if len(frames) != 9247:
        raise ValueError('unexpected audio packet count')
    for i, pkt in enumerate(frames):
        pos = (i-1)*1024
        if (pkt['pts'],pkt['dts'],pkt['duration']) != (pos,pos,min(1024,COUNT-pos)):
            raise ValueError(f'non-uniform timestamp lattice at AAC packet {i}')
    if not any(x.get('skip_samples') == 1024 for x in frames[0].get('side_data_list', [])):
        raise ValueError('encoder priming not removed by timestamp/skip edit')
    stable = '\n'.join(v['data_hash'] for v in frames).encode()
    return {**a, 'codec_configured_bitrate_kbps':256, 'packets':len(frames),
            'packet_payload_sequence_sha256':hashlib.sha256(stable).hexdigest(),
            'first_packet':frames[0], 'last_packet':frames[-1]}


def load_legacy(p):
    if sha(p) != LEGACY_SCRIPT_SHA:
        raise ValueError(f'old audio generator does not match the reviewed blob: {p}')
    spec = importlib.util.spec_from_file_location('frozen_gate3_audio', p)
    module = importlib.util.module_from_spec(spec)
    saved = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = saved
    return module


def db(x):
    return np.power(10., np.asanyarray(x)/20.)


def sample(x):
    return round(x*SR)


def weather_gain(s):
    """Linear voltage gain of the replacement tail envelope, from the inherited bed calibration."""
    s = np.asarray(s, dtype='f8')
    u = np.clip((s - START)/(RISE_END - START), 0., 1.)
    smooth = u*u*(3.-2.*u)
    plateau = db(JOIN_DB + RISE_DB*smooth**2)
    f = np.clip((s - FADE_START)/(BLACK - FADE_START), 0., 1.)
    return np.where(s < BLACK, plateau*np.cos(.5*np.pi*f)**2, 0.)


def apply_weather_delta(b, old, new, start):
    if start < 0 or b[start:].shape != old.shape or old.shape != new.shape:
        raise ValueError('unaligned weather delta')
    full = b.copy()
    full[start:] += new - old
    return full


def zero_verified_black_pcm(x):
    """Clear only denormal IIR residue in the author's digitally silent tail."""
    amplitude = float(np.max(np.abs(x), initial=0))
    if not math.isfinite(amplitude) or amplitude >= np.finfo(x.dtype).tiny:
        raise ValueError(f'actual signal at black frame: peak {amplitude}')
    x.fill(0.)
    return amplitude


def recover_f32_gain(x,y):
    """Find the unique f32 multiplier of the actual legacy reference weather window; no refit."""
    x, y = np.asarray(x, dtype='f4'), np.asarray(y, dtype='f4')
    mask = np.abs(x) > 5e-5
    if x.shape != y.shape or np.count_nonzero(mask) < 16:
        raise ValueError('calibration window is too small/quiet')
    rough = np.float32(np.median(y[mask].astype('f8')/x[mask]))
    candidates=[rough]
    lo=hi=rough
    for _ in range(3):
        lo=np.nextafter(lo,np.float32(-np.inf)); hi=np.nextafter(hi,np.float32(np.inf))
        candidates.extend((lo,hi))
    matches=[v for v in candidates if v > 0. and np.array_equal(x*v,y)]
    if len(matches) != 1:
        raise ValueError('original winter calibration did not have one exact f32 gain')
    return matches[0]


def old_and_weather(legacy, music):
    """Rebuild original PCM and isolate the unchanged underlying weather with full RNG history."""
    unpitched = legacy.decode(music, EQ)
    if len(unpitched) != ORIGINAL:
        raise ValueError(f'artist source was trimmed/padded by the decoder: {len(unpitched)}')
    music_gain = legacy.db(-16.18-legacy.measured_lufs(unpitched))
    music_full = np.pad(unpitched,((0,COUNT-ORIGINAL),(0,0)))
    music_full *= music_gain
    del unpitched
    e, history = legacy.ambience(None)
    total = music_full + e
    old_master_gain = legacy.db(-16.-legacy.measured_lufs(total))

    n = COUNT-WINTER_START
    nh = (n+1)//2
    wax, paper_timing = legacy.winter(nh)
    if history['source_visual_action_s']['winter'] != paper_timing:
        raise ValueError('winter source cue schedule changed')
    old_uncalibrated = signal.resample_poly(wax,2,1,axis=0,window=('kaiser',8.5))[:n].astype('f4')
    del wax
    season_gain = legacy.db(-31.35-legacy.measured_lufs(old_uncalibrated))
    a,b = sample(151),sample(153)
    calibration = old_uncalibrated[a-WINTER_START:b-WINTER_START]*season_gain
    old_ambi_gain = recover_f32_gain(calibration,e[a:b])
    del old_uncalibrated, calibration

    # Original storm body before the three page envelopes are added.
    # Keep full n and identical random draws/order, not just the last 12 s.
    rng=np.random.default_rng(20171223); t=legacy.time(nh)
    common=legacy.noise(rng,nh,94,630); l=legacy.noise(rng,nh,155,1160); r=legacy.noise(rng,nh,170,1090)
    extra=legacy.slow_drift(rng,t,(3.6,12.7,21.),(.12,.15,.05))
    gust=(.72+.085*np.sin(2*np.pi*t/10.7+.8)+.060*np.sin(2*np.pi*t/6.3))*extra
    body=np.stack((gust*(.84*common+.26*l),gust*(.84*common+.29*r)),1).astype('f4')
    hum=(np.sin(2*np.pi*112*t)+.31*np.sin(2*np.pi*224*t+.23))*(1+.07*np.sin(2*np.pi*.14*t))
    body+=np.stack((.021*hum,.047*hum),1).astype('f4')
    weather48=signal.resample_poly(legacy.edge_ramp(body),2,1,axis=0,window=('kaiser',8.5))[:n].astype('f4')
    del body, common, l, r, extra, gust, hum, t
    basis=weather48[REVIEW_START-WINTER_START:].copy()
    del weather48
    basis*=season_gain

    nidx=np.arange(REVIEW_START,COUNT,dtype='f8')
    t=nidx/SR
    nodes=np.array(history['quiet_ride_time_s']); vals=np.array(history['quiet_ride_adjustment_db'])
    j=np.clip(np.searchsorted(nodes,t,side='right')-1,0,len(nodes)-2)
    u=legacy.smooth_shape((t-nodes[j])/(nodes[j+1]-nodes[j]))
    old_ride=legacy.db(vals[j]+(vals[j+1]-vals[j])*u).astype('f4')
    w0=basis.copy()
    a,b=sample(193.4)-REVIEW_START,BLACK-REVIEW_START
    w0[a:b]*=(np.cos(.5*np.pi*np.arange(b-a)/(b-a))**2)[:,None]
    w0[b:]=0
    w0*=old_ride[:,None]
    w0*=old_ambi_gain
    w0*=old_master_gain
    off=START-REVIEW_START
    w1=w0.copy()
    w1[off:]=basis[off:] * weather_gain(nidx[off:]).astype('f4')[:,None]
    w1[off:]*=old_ambi_gain
    w1[off:]*=old_master_gain
    if not np.array_equal(w0[off],w1[off]):
        raise ValueError('weather gain does not join the existing mix at the exact onset sample')
    total*=old_master_gain
    e*=old_master_gain
    music_full*=old_master_gain
    old_paper=e[REVIEW_START:]-w0
    e1=apply_weather_delta(e[REVIEW_START:],w0[off:],w1[off:],off)
    new_mix=apply_weather_delta(total,w0[off:],w1[off:],START)
    if not np.array_equal(total[:START],new_mix[:START]):
        raise ValueError('the new weather altered the PCM prefix')
    if np.max(abs(new_mix))>=1. or not np.isfinite(new_mix).all():
        raise ValueError('PCM clipped or nonfinite')
    flushed_denormal_peak=zero_verified_black_pcm(new_mix[BLACK:])
    if np.any(music_full[ORIGINAL:]):
        raise ValueError('music alignment padding is not silence')
    paper_resid=float(np.max(np.abs((e1-w1)-old_paper)))
    if paper_resid>5e-8:
        raise ValueError('pre-existing paper changed or was amplified')
    music_closure=float(np.max(np.abs(new_mix[REVIEW_START:]-e1-music_full[REVIEW_START:])))
    if music_closure>5e-8:
        raise ValueError('source music timing or amplitude changed')
    basis*=old_ambi_gain
    basis*=old_master_gain
    return {'legacy':total,'mix':new_mix,'music':music_full,'weather_before':w0,'weather_after':w1,
            'weather_unautomated':basis,
            'old_env_tail':e[REVIEW_START:].copy(),'new_env_tail':e1,'inherited_paper':old_paper,
            'season_gain':float(season_gain),'ambient_gain':float(old_ambi_gain),
            'old_master_gain':float(old_master_gain),'inherited_paper_delta_roundoff_peak':paper_resid,
            'music_additivity_roundoff_peak':music_closure,'audio_transition_cues':history['transition_cues'],
            'paper_cues':paper_timing,'synthetic_winter_source_samples_24k':nh,
            'flushed_eq_black_denormal_peak':flushed_denormal_peak}


def dpm(p):
    return round(10*math.log10(p),5) if p > 0. else None


def peak_db(a):
    return dpm(float(np.max(np.abs(a)))**2)


def section(xs, begin, end):
    return xs[sample(begin)-REVIEW_START:sample(end)-REVIEW_START]


def weighted(xs):
    return signal.sosfilt(K_SOS, xs, axis=0)


def power_row(xs, kw):
    return {
        'rms_dBFS': dpm(float(np.mean(np.square(xs, dtype='f8')))),
        'ungated_LKFS': dpm(float(np.mean(np.sum(kw*kw,axis=1))*10**(-.691/10))),
        'peak_dBFS': peak_db(xs),
    }


def stable_powers(audio):
    raw={'music':audio['music'][REVIEW_START:],'old_winter_weather':audio['weather_before'],
         'new_winter_weather':audio['weather_after'],'old_environment':audio['old_env_tail'],
         'new_environment':audio['new_env_tail'],'inherited_page_only':audio['inherited_paper'],
         'old_mix':audio['legacy'][REVIEW_START:],'new_mix':audio['mix'][REVIEW_START:]}
    weight={k:weighted(v) for k,v in raw.items()}
    parts={
        'old_bed_during_music_ramp_anchor':[184.,185.],
        'new_weather_during_music_ramp_anchor':[184.,185.],
        'music_handover':[185.,190.],
        'music_last_quarter_second':[191.,191.25],
        'measured_pure_weather_plateau':[192.2,194.5],
        'end_fade_first_half':[194.5,195.85],
        'end_fade_last_half':[195.85,197.2],
        'black_frame_silence':[197.2,COUNT/SR],
    }
    result={}
    for k,(a,b) in parts.items():
        result[k]={'s':[a,b],'samples_half_open':[sample(a),sample(b)],
                   **{name:power_row(section(v,a,b),section(weight[name],a,b)) for name,v in raw.items()}}
    a=result['old_bed_during_music_ramp_anchor']['old_winter_weather']['ungated_LKFS']
    b=result['measured_pure_weather_plateau']['new_winter_weather']['ungated_LKFS']
    if not 6 <= b-a <= 9:
        raise ValueError(f'actual bed rise relative to reference anchor outside 6–9 dB: {b-a}')
    freq, ps = signal.welch(section(audio['weather_after'],192.2,194.5),SR,
                            nperseg=4096,noverlap=2048,axis=0)
    p=ps.mean(axis=1)
    hf=100*float(p[freq>=2000].sum()/p.sum())
    if hf >= .2:
        raise ValueError(f'winter tail has too much high-frequency energy: {hf}% at ≥2 kHz')
    t=np.arange(180.1,197.101,.1)
    levels=[]
    for x in t:
        ix, iy = sample(x-.10)-REVIEW_START,sample(x+.10)-REVIEW_START
        levels.append({'s':round(float(x),3),**{
            k:dpm(float(np.mean(np.sum(v[ix:iy]**2,axis=1))*10**(-.691/10))) for k,v in weight.items()
        }})
    return result, levels, round(b-a,5), hf


def make_chart(path, levels, measured_rise):
    from PIL import Image, ImageDraw, ImageFont
    W,H=1400,780
    bg='#151e2c'; lines='#33455b'; fg='#f0e6d8'; quiet='#9db4cc'
    colors={'music':'#eec68d','old_winter_weather':'#9e91af','new_winter_weather':'#6bd4e5','new_mix':'#dbe8ec'}
    img=Image.new('RGB',(W,H),bg)
    d=ImageDraw.Draw(img)
    def font(n):
        p=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
        return ImageFont.truetype(str(p),n) if p.is_file() else ImageFont.load_default(size=n)
    d.text((50,30),'RAINROJI V2.4  |  THE WINTER HANDOVER',font=font(31),fill=fg)
    d.text((52,79),f'Decoded 48 kHz mix stems; same timebase and level. Weather plateau rises {measured_rise:+.2f} dB.',font=font(17),fill=quiet)
    x0,x1,y0,y1=103,1338,146,613
    def X(t): return x0+(t-180)/(COUNT/SR-180)*(x1-x0)
    def Y(db): return y0+(min(-18.,max(-83.,db))+18)/(-65)*(y1-y0)
    d.rectangle((X(191.2678125),y0,X(194.5),y1),fill='#233146')
    d.rectangle((X(194.5),y0,X(197.2),y1),fill='#202b3b')
    for i in range(180,198,2):
        x=X(i); d.line((x,y0,x,y1),fill=lines,width=1)
        d.text((x-19,y1+11),f'{i//60}:{i%60:02d}',font=font(15),fill=quiet)
    for i in (-20,-30,-40,-50,-60,-70,-80):
        y=Y(i); d.line((x0,y,x1,y),fill=lines,width=1)
        d.text((50,y-9),str(i),font=font(15),fill=quiet)
    for t0,n,label in [(185,175,'rise begins'),(191.2678125,180,'song silent'),(194.5,192,'fade starts'),(197.2,136,'black')]:
        x=X(t0);d.line((x,y0,x,y1),fill='#536b85',width=2)
        d.text((x+5 if t0<196 else x-63,y0+25),label,font=font(13),fill=quiet)
    for k in ('new_mix','old_winter_weather','new_winter_weather','music'):
        points=[(X(item['s']),Y(item[k] if item[k] is not None else -83)) for item in levels]
        d.line(points,fill=colors[k],width=4 if k!='new_mix' else 2)
    notes=('Music, unchanged','Old winter weather','New winter weather','v2.4 mix')
    for c,(k,lbl) in enumerate(zip(colors,notes)):
        x=135+c*301;d.line((x,674,x+36,674),fill=colors[k],width=4)
        d.text((x+47,663),lbl,font=font(17),fill=fg)
    d.text((82,729),'Units: ungated BS.1770 K-weighted level (LKFS), 200 ms windows. Below −83 hidden at chart floor.',font=font(15),fill=quiet)
    img.save(path,compress_level=8)


def export_media(legacy, scratch, previews, report_path, output, copy_stems):
    legacy_script, artist = scratch[1], scratch[2]
    work=scratch[0]; work.mkdir(parents=True,exist_ok=True)
    if artist.stat().st_size != ORIGINAL_BYTES or sha(artist)!=SOURCE_SHA:
        raise ValueError('wrong artist source: approved complete 320 kbps Green Tea MP3 is required')
    data=old_and_weather(legacy,artist)
    before_file, after_file = work/'baseline_float.wav', work/'final_float.wav'
    legacy.write(before_file,data['legacy'])
    legacy.write(after_file,data['mix'])
    windows,levels,actual_rise,hf=stable_powers(data)
    if copy_stems:
        for k,v in {
            'tail_music':data['music'][REVIEW_START:],'tail_winter_bed_before':data['weather_before'],
            'tail_winter_bed_after':data['weather_after'],'tail_page_foley':data['inherited_paper'],
            'tail_winter_bed_basis':data['weather_unautomated'],
            'tail_environment_before':data['old_env_tail'],'tail_environment_after':data['new_env_tail'],
        }.items():
            legacy.write(work/(k+'.wav'),v)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.audio_tail_',dir=output.parent) as temp:
        staged=Path(temp)/'candidate.m4a'
        legacy.release_aac(after_file,staged)
        packets=packet_probe(staged)
        loud=legacy.true_meter(staged)
        if not (-16.5 <= loud['integrated_lufs'] <= -15.5 and loud['true_peak_dbtp'] <= -1.5):
            raise ValueError(f'encoded AAC loudness/peak outside approval: {loud}')
        dec0=legacy.decode(staged)
        if len(dec0)<COUNT: raise ValueError(f'encoded music was truncated at {len(dec0)} samples')
        dec=dec0[:COUNT]
        m=data['mix']
        align=signal.correlate(dec[48_000:100_000,0],m[48_000:100_000,0],method='fft')
        lag=int(np.argmax(align)-51_999)
        decoded_black_peak=peak_db(dec[BLACK:])
        if (lag!=0 or not np.isfinite(dec).all() or float(np.max(np.abs(dec)))>=1.
            or (decoded_black_peak is not None and decoded_black_peak > -100.)):
            raise ValueError(f'encoded AAC shifted, clipped, or audible in black frame: {lag} / {decoded_black_peak}')
        if previews is not None:
            previews.mkdir(parents=True,exist_ok=True)
            legacy.export_flac(previews/'tail_before.flac',data['legacy'][REVIEW_START:])
            legacy.export_flac(previews/'tail_after.flac',m[REVIEW_START:])
            legacy.export_flac(previews/'tail_after_encoded.flac',dec[REVIEW_START:])
            with (previews/'tail_energy.csv').open('w',newline='') as f:
                csv_writer=csv.DictWriter(f,fieldnames=list(levels[0]))
                csv_writer.writeheader();csv_writer.writerows(levels)
            make_chart(previews/'tail_energy.png',levels,actual_rise)
        out = {
            'review_commit':'1fa86680089be1b6ee8a07dab2a13d865de05dd6',
            'source':{'title':'Green Tea','author':'Purrple Cat','license':'CC BY 4.0','source_page':SOURCE_PAGE,
                      'author_mp3':SOURCE_URL,'sha256':SOURCE_SHA,'bytes':ORIGINAL_BYTES,'complete_unchanged_samples':ORIGINAL,
                      'duration_s':ORIGINAL/SR,'alignment_zero_pad_samples':COUNT-ORIGINAL,
                      'prior_EQ_unchanged':EQ,'last_unprocessed_source_sample_above_minus100_s_measured':191.233958333,
                      'exact_unprocessed_digital_silence_from_s_measured':191.2678125,
                      'frozen_music_full_pcm_f32le_sha256':pcm_sha(data['music'])},
            'legacy_recipe_sha256':sha(legacy_script),
            'baseline_float_wav_sha256':sha(before_file),'baseline_float_wav_matches_previous_exact_local_rebuild':sha(before_file)==LEGACY_PCM_WAV_SHA,
            'new_float_wav_sha256':sha(after_file),
            'prefix_PCM_before_weather_change':{'exact_samples_per_channel':START,'exact_duration_s':START/SR,
                'byte_identical_before_after':True,'pcm_f32le_sha256':pcm_sha(m[:START])},
            'mix_changed_float_frames':int(np.count_nonzero(np.any(data['legacy'][START:]!=m[START:],axis=1))),
            'winter_weather':{'onset_rise_plateau_fade_finish_sample_positions':
                 [START,RISE_END,FADE_START,BLACK,COUNT],'same_existing_winter_rng_seed':20171223,
                 'old_original_winter_source_samples_24000':data['synthetic_winter_source_samples_24k'],
                 'raised_db_relative_to_tail_anchor':RISE_DB,'measured_plateau_minus_anchor_ungated_dB':actual_rise,
                 'new_weather_plateau_at_or_over_2000_hz_percent':round(hf,7),
                 'automation':'squared smoothstep in dB, hold, cos-squared amplitude; prior winter bed and room hum only',
                 'prior_calibration_multipliers':{k:data[k] for k in ('season_gain','ambient_gain','old_master_gain')},
                 'paper_foley_no_amplitude_or_time_modification':data['paper_cues'],
                 'paper_delta_roundoff_peak':data['inherited_paper_delta_roundoff_peak'],
                 'music_additivity_roundoff_peak':data['music_additivity_roundoff_peak']},
            'transitions':data['audio_transition_cues'],
            'timing':{'audio_samples_per_channel':COUNT,'video_frames':FRAMES,'fps':30,'exact_seconds_fraction':str(Fraction(FRAMES,30)),
                      'last_black_pcm_silence_samples':COUNT-BLACK,'black_eq_flushed_denormal_peak_amplitude':data['flushed_eq_black_denormal_peak'],
                      'A_B_audio_from':180,'A_B_samples_per_channel':COUNT-REVIEW_START},
            'encoded_aac':{'file':output.name,'bytes':staged.stat().st_size,'sha256':sha(staged),'alignment_lag_samples':lag,
                'dec_not_clipped':True,'decoded_samples_including_decoder_padding':len(dec0),'decoded_black_peak_dBFS':decoded_black_peak,
                'meter':loud,'stream':packets},
            'validation_windows':windows,
            'export_versions':{'numpy':np.__version__,'ffmpeg':sp.check_output(['ffmpeg','-version'],text=True).splitlines()[0]},
        }
        report_path.parent.mkdir(parents=True,exist_ok=True)
        part_path=report_path.with_suffix(report_path.suffix+'.part')
        part_path.write_text(json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
        staged.replace(output)
        part_path.replace(report_path)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--music',type=Path,required=True,help='complete source MP3 with locked artist SHA-256')
    p.add_argument('--out','--output',type=Path,required=True,dest='output')
    g=p.add_mutually_exclusive_group()
    g.add_argument('--report',type=Path)
    g.add_argument('--qa-dir',type=Path)
    p.add_argument('--legacy-script','--legacy-audio-script',type=Path,
                   default=Path(__file__).resolve().parent.parent/'gate3'/'gate3_audio.py')
    p.add_argument('--scratch',type=Path,help='preserve full float before and after here; otherwise temporary')
    p.add_argument('--preview-dir',type=Path,help='independent lossless before/after FLAC, PNG and CSV evidence')
    p.add_argument('--retain-tail-stems',action='store_true',help='write detailed tail PCM stems to --scratch')
    a=p.parse_args()
    if a.retain_tail_stems and a.scratch is None:
        p.error('--retain-tail-stems requires an explicit --scratch')
    report=a.report or ((a.qa_dir or a.output.parent)/'audio_tail_report.json')
    if a.output.resolve()==a.music.resolve() or report.resolve() in (a.output.resolve(),a.music.resolve()):
        raise ValueError('output paths must not overwrite the source or each other')
    legacy=load_legacy(a.legacy_script)
    with tempfile.TemporaryDirectory(prefix='rainroji_gate34_audio_') as fd:
        scratch=(a.scratch or Path(fd),a.legacy_script,a.music)
        out=export_media(legacy,scratch,a.preview_dir,report,a.output,a.retain_tail_stems)
    print(json.dumps({k:out[k] for k in ('encoded_aac','timing','prefix_PCM_before_weather_change')},ensure_ascii=False,indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

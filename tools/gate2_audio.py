#!/usr/bin/env python3
"""Gate 2 试听素材与冬景混音复现工具。依赖 Python3 / numpy / scipy / FFmpeg（含 libmp3lame、libx264）。
示例：python tools/gate2_audio.py --masters local-masters --winter previews/gate_2/winter_loop.mp4 --out previews/gate_2 --tmp /tmp/gate2_sound
作者原件地址、文件名及 SHA256 存于 music_sources.json；本脚本不联网。无终混、无外部采样。
"""
import argparse, hashlib, json, subprocess as sp, tempfile
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile

S=48000
# 条目名、输入名、作者、曲名、截取起点与长度。所有时间均为秒。
PICKS=[('01_green_tea','green.mp3','Purrple Cat','Green Tea',12,36),('02_guitar_beat','seth.mp3','Seth_Makes_Sounds','lofibeat_70bpm.wav',12*60/70,40*60/70),('03_first_light','yoi.wav','Yoiyami','First Light Particles',14,38),('04_forget_me_not','forget.ogg','Kistol','Forget Me Not (tape study)',24,38.4)]
CCBY='https://creativecommons.org/licenses/by/4.0/'; CC0='https://creativecommons.org/publicdomain/zero/1.0/'
URLS=['https://purrplecat.itch.io/bloom','https://freesound.org/people/Seth_Makes_Sounds/sounds/664145/','https://opengameart.org/node/182244','https://opengameart.org/content/forget-me-not']

def run(a,**kw): return sp.run(a,check=True,**kw)
def probe(path): return json.loads(sp.check_output(['ffprobe','-v','error','-select_streams','a:0','-show_streams','-show_format','-of','json',path]))
def ff(*args):return ['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)]
def cut(src,start,length,filters=None):
 cmd=ff('-threads',1,'-ss',f'{start:.9f}','-i',src,'-t',f'{length:.9f}','-map','0:a:0','-vn','-af',filters or 'anull','-ac',2,'-ar',S,'-f','f32le','-');a=np.frombuffer(sp.check_output(cmd),'<f4').reshape(-1,2).copy(); n=round(length*S)
 if len(a)<n: a=np.pad(a,((0,n-len(a)),(0,0)))
 return a[:n]
def write(p,a): wavfile.write(str(p),S,a.astype(np.float32))
def loud(p):
 r=run(['ffmpeg','-v','info','-nostats','-i',p,'-map','0:a:0','-vn','-af','loudnorm=print_format=json','-f','null','-'],capture_output=True,text=True).stderr
 d=json.loads(r[r.rfind('{'):r.rfind('}')+1]);return {k:float(d[k]) for k in ('input_i','input_lra','input_tp')}
def gain(a,db):return a*(10.0**(db/20.))
def rmsdb(a):return 20*np.log10(max(1e-10,float(np.sqrt(np.mean(np.square(a,dtype=np.float64))))))
def level(a,tmp,target):
 write(tmp,a); before=loud(tmp);g=target-before['input_i'];return gain(a,g),g

def fade(a,lead,tail):
 b=a.copy();n=round(lead*S);m=round(tail*S)
 if n:b[:n] *= np.sin(np.linspace(0,np.pi/2,n))[:,None]**2
 if m:b[-m:] *= np.cos(np.linspace(0,np.pi/2,m))[:,None]**2
 return b

def tape(a):
 # 轻磁带偏转：0.29Hz / 0.28ms 和 3.8Hz / 0.014ms，约 ±1.5 音分上限；不是原作者录制介质。
 ix=np.arange(len(a));t=ix/S;rng=np.random.default_rng(124315)
 lag=.00028*np.sin(2*np.pi*.29*t)+.000014*np.sin(2*np.pi*3.8*t+.4)
 b=np.stack([np.interp(ix-S*lag,ix,a[:,c]) for c in range(2)],axis=1)
 # 极浅的左右串音与底噪；不把柔和琴音磨成一层嘶声。
 b=.982*b+.018*b[:,::-1]; h=signal.sosfilt(signal.butter(2,[1400,5400],fs=S,btype='bandpass',output='sos'),rng.normal(size=(len(a),2)),axis=0)
 return b+.00012*h

def air(n):
 # 户外风而非「落雪音效」：低频干净、远处风口连贯、左右声场去相关。书页拟音用窄带噪声与三次微摩擦生成，无素材库录音。
 rng=np.random.default_rng(20171223);t=np.arange(n)/S
 def band(v,lo,hi):return signal.sosfilt(signal.butter(3,[lo,hi],fs=S,btype='bandpass',output='sos'),v)
 def unit(z):return z/(np.sqrt(np.mean(z*z))+1e-12)
 common=unit(band(rng.normal(size=n),94,630)); left=unit(band(rng.normal(size=n),155,1160));right=unit(band(rng.normal(size=n),170,1090))
 gust=.68+.12*np.sin(2*np.pi*t/10.7+.8)+.09*np.sin(2*np.pi*t/6.3)
 bed=np.stack([gust*(.84*common+.26*left),gust*(.84*common+.29*right)],axis=1)
 # 值班室暖窗靠右，远方风口只在 112/224Hz 留很轻的谐音，不模拟机器贴耳嗡鸣。
 hum=(np.sin(2*np.pi*112*t)+.31*np.sin(2*np.pi*224*t+.23))*(1+.09*np.sin(2*np.pi*.14*t));bed+=np.stack([.026*hum,.057*hum],1)
 scrape=np.zeros(n);raw=unit(band(rng.normal(size=n),780,3500));fine=unit(band(rng.normal(size=n),450,1380))
 for center,width,amt in ((9.21,.080,.34),(9.64,.154,.70),(10.28,.087,.37)):
  env=amt*np.exp(-.5*((t-center)/width)**2);grain=.82+.18*np.sin(2*np.pi*21*t+0.3*np.sin(2*np.pi*9*t));scrape+=env*grain*(.43*raw+.57*fine)
 bed+=np.stack([scrape*.27,scrape*.86],1)
 return fade(bed,.12,.32)

def hash256(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--masters',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);ap.add_argument('--tmp',required=True,type=Path);ap.add_argument('--winter',type=Path);args=ap.parse_args();out=args.out;tmp=args.tmp;out.mkdir(parents=True,exist_ok=True);tmp.mkdir(parents=True,exist_ok=True);cf=out/'music_candidates';cf.mkdir(exist_ok=True)
 report={'samples':{}};reg=tmp/'measure.wav'
 for i,(stem,master,artist,title,start,dur) in enumerate(PICKS):
  path=args.masters/master;a=cut(path,start,dur);a=tape(a) if i==3 else a
  a=fade(a,.08,.42);a,g=level(a,reg,-18.5);wav=tmp/(stem+'.wav');write(wav,a)
  p=cf/(stem+'.mp3'); r=run(ff('-i',wav,'-map','0:a:0','-map_metadata','-1','-c:a','libmp3lame','-b:a','224k','-ar','48000','-id3v2_version',3,'-metadata','title='+title,'-metadata','artist='+artist,'-metadata','copyright='+((CCBY if i==0 else CC0)),'-metadata','comment=Gate 2 excerpt; '+('project tape treatment; ' if i==3 else '')+'gain and fades; source: '+URLS[i],p));
  report['samples'][stem]={'source':master,'source_sha256':hash256(path),'encoded_sha256':hash256(p),'source_start_s':round(start,6),'excerpt_s':round(dur,6),'gain_db':round(g,2),'rms_dbfs':round(rmsdb(a),2),'encoded_meter':loud(p),'bytes':p.stat().st_size}
 if args.winter:
  dur=18;music=cut(args.masters/'green.mp3',30,dur,'bass=g=-1.5:f=150:w=0.7');music=fade(music,.18,.82);music,mg=level(music,reg,-16.2)
  room,rg=level(air(len(music)),reg,-31.2);mix=music+room
  for nm,z in [('music',music),('courtyard',room),('mix',mix)]:write(tmp/(nm+'.wav'),z)
  p=out/'winter_music_audition.mp4'
  # 从冬景时码 7.000 开始，跨真实循环两次；样片内仅一次完整翻页。保留真实正式 1080p30 画面，不用代理。
  run(ff('-stream_loop','1','-threads','2','-i',args.winter,'-i',tmp/'mix.wav','-filter_complex','[0:v]trim=start_frame=210:end_frame=750,setpts=PTS-STARTPTS[v]','-map','[v]','-map','1:a:0','-t','18','-c:v','libx264','-threads','3','-preset','medium','-crf','17','-tune','animation','-pix_fmt','yuv420p','-flags','+cgop','-x264-params','keyint=90:min-keyint=90:scenecut=0','-c:a','aac','-b:a','224k','-ar',S,'-metadata','title=Winter courtyard | Green Tea | Gate 2 audition','-metadata','artist=Purrple Cat (music); project (ambience and sequence)','-metadata','comment=Green Tea by Purrple Cat | https://purrplecat.itch.io/bloom | CC BY 4.0 https://creativecommons.org/licenses/by/4.0/ | 30-48 s, EQ, fades, gain, original ambience and picture sync.','-movflags','+faststart',p))
  report['mix']={'source_video_sha256':hash256(args.winter),'video_sha256':hash256(p),'video_bytes':p.stat().st_size,'audio_source':'green.mp3','video_crop_s':[7,25],'music_crop_s':[30,48],'raw_music_gain_db':round(mg,2),'ambience_db_below_music':15,'output':loud(p),'stems':{nm:{**loud(tmp/(nm+'.wav')),'rms_dbfs':round(rmsdb(z),2)} for nm,z in [('music',music),('courtyard',room),('mix',mix)]}}
 (tmp/'measurements.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

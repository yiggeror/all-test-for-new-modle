"""Pinned original author asset and sample-exact handoff to the Gate 3.4 AAC mixer."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

AUDIO_URL='https://html-classic.itch.zone/html/19949767/media/Green%20Tea.mp3'
AUDIO_BYTES=8_245_791
MUSIC_SHA256='f6feac60dc29b89ea1513e04d0b30addf86f9c8576827e7566e27b5abd522e71'
LEGACY_AUDIO_SHA256='714968f7637f14cb9950da582f7a15d00e2339d5b1b07508e9cfe4f756ae0200'
MIXER_SHA256='f6d3a31932246e2bb518c0167b6ae82030d574539d4b09f55bb8e376f39bec19'
ORIGINAL_SAMPLES=9_466_286
SR=48_000
TOTAL=9_467_200
AAC_PACKETS=(TOTAL+1023)//1024+1
ALLOW_HOSTS={'html-classic.itch.zone'}

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


class AuthorDownload(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        a=urlsplit(newurl)
        if a.scheme!='https' or a.hostname not in ALLOW_HOSTS or a.username or a.password:
            raise ValueError('作者原曲指向未核验主机，拒绝重定向')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def acquire_author_track(destination, cache=None):
    source=destination if cache is None else cache
    if cache is None:
        request=Request(AUDIO_URL,headers={'User-Agent':'Rainroji-Gate34-Repro/2.4','Accept':'audio/mpeg, application/octet-stream'})
        total=0
        with build_opener(AuthorDownload()).open(request,timeout=80) as r, destination.open('xb') as f:
            while block:=r.read(1<<20):
                total+=len(block)
                if total>AUDIO_BYTES:raise ValueError('作者原曲比审核字节数大')
                f.write(block)
    length=source.stat().st_size
    sha=digest(source)
    if (length,sha)!=(AUDIO_BYTES,MUSIC_SHA256):
        raise ValueError(f'不是核验的完整作者原曲 Green Tea：{length} 字节，SHA-256 {sha}')
    return source,dict(author='Purrple Cat',title='Green Tea',url=AUDIO_URL,license='CC BY 4.0',
                       bytes=length,sha256=sha,pcm_original_samples_at_48k=ORIGINAL_SAMPLES,
                       used_verified_local_cache=cache is not None)


def packet_identity(doc):
    audio,=doc['streams']
    p=doc['packets']
    need={'codec_type':'audio','codec_name':'aac','profile':'LC','sample_rate':'48000','channels':2,
          'time_base':'1/48000','start_pts':0,'duration_ts':TOTAL}
    wrong={k:[audio.get(k),v] for k,v in need.items() if audio.get(k)!=v}
    if wrong:raise ValueError(f'实际 AAC 流规格或时长不匹配：{wrong}')
    if not 211_000<=int(audio['bit_rate'])<=291_000:
        raise ValueError('不是约定 256 kbps AAC-LC 编码的合理实测码率范围')
    if len(p)!=AAC_PACKETS:raise ValueError(f'实际 AAC 包数 {len(p)}，预期 {AAC_PACKETS}')
    serial=[]; ordered=[]; timing=[]
    for i,d in enumerate(p):
        fields=tuple(int(d[k]) for k in ('pts','dts','duration','size'))
        t=(i-1)*1024
        end=TOTAL%1024 if i==AAC_PACKETS-1 and TOTAL%1024 else 1024
        if fields[:3]!=(t,t,end):raise ValueError(f'AAC {i} 包时基/有效时长变动：{fields[:3]}')
        payload=d['data_hash']
        if fields[3]<=0 or not re.fullmatch(r'SHA256:[0-9a-fA-F]{64}',payload):
            raise ValueError('缺失一个 AAC 包的实际字节指纹')
        ordered.append(payload.lower())
        timing.append(fields[:3])
        serial.append((fields,payload.lower(),d.get('flags',''),d.get('side_data_list',[])))
    priming=[r for r in p[0].get('side_data_list',[]) if r['side_data_type']=='Skip Samples']
    if len(priming)!=1 or priming[0].get('skip_samples')!=1024 or priming[0].get('discard_padding')!=0:
        raise ValueError('新混音 AAC 起始延迟不符，不能精确保留样本')
    config=audio.get('extradata_hash','')
    if not re.fullmatch(r'SHA256:[0-9a-fA-F]{64}',config):
        raise ValueError('没读到实际 AAC 配置字节 SHA-256')
    def hashed(arr):
        return hashlib.sha256(json.dumps(arr,sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest()
    return {'codec':'aac','profile':'LC','sample_rate_hz':SR,'channels':2,
            'effective_samples':TOTAL,'duration_exact_seconds':str(Fraction(TOTAL,SR)),'packet_count':len(p),
            'first_packet_pts_samples':int(p[0]['pts']),'last_packet_duration_samples':int(p[-1]['duration']),
            'priming_samples':priming[0]['skip_samples'],'discard_padding':priming[0]['discard_padding'],
            'audiocfg_sha256':config.split(':',1)[1].lower(),'timings_sha256':hashed(timing),
            'ordered_payloads_sha256':hashed(ordered),'ordered_full_identity_sha256':hashed(serial)}


def verify_aac(path):
    args=['ffprobe','-v','error','-show_streams','-show_packets','-show_data_hash','sha256','-select_streams','a:0','-of','json',str(path)]
    p=json.loads(subprocess.check_output(args))
    af=packet_identity(p)
    adts=subprocess.check_output(['ffmpeg','-v','error','-xerror','-nostdin','-i',str(path),'-map','0:a:0',
                                  '-c','copy','-f','adts','pipe:1'])
    af['adts_sha256']=hashlib.sha256(adts).hexdigest()
    return af


def mixer_command(entry,music,m4a,report):
    """Mix once from pinned author bytes and existing procedural legacy source."""
    import sys
    return [sys.executable,str(entry),'--music',str(music),'--out',str(m4a),'--report',str(report)]


def validate_mix_report(report, m4a_sha):
    src=report['source'];timing=report['timing'];winter=report['winter_weather']
    if (src['sha256'],src['complete_unchanged_samples'],src['alignment_zero_pad_samples'])!=(MUSIC_SHA256,ORIGINAL_SAMPLES,TOTAL-ORIGINAL_SAMPLES):
        raise ValueError('实际混音没有保留作者全曲和精确静音尾样本')
    if report['legacy_recipe_sha256']!=LEGACY_AUDIO_SHA256:
        raise ValueError('实际混音的程序拟音版本不符')
    if (timing['audio_samples_per_channel'],timing['video_frames'],timing['fps'])!=(TOTAL,5917,30):
        raise ValueError('实际混音未锁定 5917/30 秒声画时基')
    start,rise,fade,black,end=map(int,winter['onset_rise_plateau_fade_finish_sample_positions'])
    prefix=report['prefix_PCM_before_weather_change']
    if (not prefix['byte_identical_before_after'] or prefix['exact_samples_per_channel']!=start or not
        184*SR<=start<=185.5*SR<rise<=193.4*SR<fade<black==9_465_600<end==TOTAL):
        raise ValueError('早段不应改变，冬夜接棒、淡黑相位或时长不符')
    if not 2.5<=(black-fade)/SR<=3.0:
        raise ValueError('冬底最后的淡出未匹配 2.5–3 秒时窗')
    if not (6.<=winter['raised_db_relative_to_tail_anchor']<=9. and
            6.<=winter['measured_plateau_minus_anchor_ungated_dB']<=9.25):
        raise ValueError('实测冬夜室外底声抬升与审核范围不同')
    a=report['encoded_aac'];meter=a['meter'];peak=a['decoded_black_peak_dBFS']
    if a['sha256']!=m4a_sha or a['alignment_lag_samples']!=0 or (peak is not None and peak>-100.):
        raise ValueError('混音音轨非报告所验的真实文件、时钟偏移或尾黑期有残留')
    if not (-16.22<=meter['integrated_lufs']<=-15.82 and meter['true_peak_dbtp']<=-1.5):
        raise ValueError('混音真实测量的响度/真峰超出交付约定')


def mix_author_track(entry,legacy,music,m4a,report,log):
    if digest(entry)!=MIXER_SHA256:
        raise ValueError('实际尾混脚本不同于 Gate 3.4 已核验源码')
    if digest(legacy)!=LEGACY_AUDIO_SHA256:
        raise ValueError('老版确定性环境与拟音源码不是已有签收的 Gate 3 版本')
    if m4a.exists() or report.exists():raise ValueError('拒绝覆盖既有一次混音')
    with log.open('w',encoding='utf8') as out:
        p=subprocess.run(mixer_command(entry,music,m4a,report),stdout=out,stderr=subprocess.STDOUT)
    if p.returncode!=0:
        raise RuntimeError(f'尾声混音失败（退出 {p.returncode}）：'+log.read_text(errors='replace')[-900:])
    if not report.is_file() or not m4a.is_file(): raise ValueError('尾声混音缺音轨或实际量化报告')
    validate_mix_report(json.loads(report.read_bytes()),digest(m4a))
    stream=verify_aac(m4a)
    if stream['adts_sha256']=='3eb43b1c07211e4ece9173fae7ff25e73e4195f50c430e2f388285971725693d':
        raise ValueError('检测到旧版 v2.0–v2.3 AAC，Gate 3.4 必须重混冬夜尾声')
    return stream

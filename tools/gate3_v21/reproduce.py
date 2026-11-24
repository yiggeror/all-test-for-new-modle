#!/usr/bin/env python3
"""从 Gate 2.1 无损分卷和已签收 v2.0 AAC 一键生成 Rainroji v2.1。"""
import argparse
from fractions import Fraction
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory

from audio_lock import acquire, digest, verify_aac
from recover_native import SCENES, load_fingerprints, recover

HERE=Path(__file__).resolve().parent
MASTER='Rainroji_Lofi_V2.1_1080p.mp4'
PART_MANIFEST_SHA256='d858e6eb31bab1a268fe41cb2f771495c1507584675ad5b8cb3a9fedc77e4822'
INDEPENDENT_RGB_SHA256='e875a665d4333c0c3054bd848bf83a9dc6653afd2518d9094d84c4813cb27b9d'
CENTERS=(1440,2880,4320)
N=5917
TAIL=114


def root():
    return HERE.parents[1]


def picture_args(native,picture,qa):
    return ('--native-dir',native,'--output',picture,'--qa-dir',qa,
            '--centers-frame',*CENTERS,'--transition-frames',60,'--tail-frames',TAIL,'--no-storyboard')


def mux_command(picture,release,final):
    return ['ffmpeg','-v','error','-nostdin','-n','-i',str(picture),'-i',str(release),
            '-map','0:v:0','-map','1:a:0','-c','copy','-movie_timescale','48000',
            '-movflags','+faststart','-metadata','creation_time=2026-11-24T00:00:00Z',str(final)]


def toolchain():
    return {'python':sys.version.split()[0],'machine':platform.machine(),'os':platform.platform(),
            'packages':{name:metadata.version(name) for name in ('numpy','Pillow')},
            **{name:subprocess.check_output([name,'-version'],text=True).splitlines()[0] for name in ('ffmpeg','ffprobe')}}


def verify_faststart(path):
    end=path.stat().st_size; pos=0; source=[]
    with path.open('rb') as file:
        while pos<end:
            file.seek(pos); raw=file.read(8)
            if len(raw)!=8:raise ValueError('MP4 盒被截断')
            n,k=struct.unpack('>I4s',raw); hdr=8
            if n==0:n=end-pos
            elif n==1:
                raw=file.read(8)
                if len(raw)!=8:raise ValueError('MP4 64 位盒长度被截断')
                n=struct.unpack('>Q',raw)[0];hdr=16
            if n<hdr or pos+n>end:raise ValueError('MP4 盒长度无效')
            source.append(k);pos+=n
    if b'moov' not in source or b'mdat' not in source or source.index(b'moov')>source.index(b'mdat'):
        raise ValueError('未取得 faststart MP4')


def verify_final(path):
    verify_faststart(path)
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
    v,a=data['streams']
    keys={'codec_type':'video','codec_name':'h264','profile':'High','width':1920,'height':1080,
          'pix_fmt':'yuv420p','avg_frame_rate':'30/1','nb_frames':'5917','color_space':'bt709',
          'color_range':'tv','start_pts':0}
    wrong={k:[v.get(k),z] for k,z in keys.items() if v.get(k)!=z}
    if wrong:raise ValueError(f'画面规格不符：{wrong}')
    keys.update({k:v.get(k) for k in ('color_transfer','color_primaries')})
    tick=Fraction(v['time_base']); cadence=1/(30*tick)
    if tick*v['duration_ts']!=Fraction(N,30) or cadence.denominator!=1 or a['codec_type']!='audio':
        raise ValueError('画面时长或音轨数不符')
    vp=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_packets',
                  '-show_entries','packet=pts,duration','-of','json',str(path)]))['packets']
    if sorted(int(p['pts']) for p in vp)!=[i*int(cadence) for i in range(N)] or any(int(p['duration'])!=cadence for p in vp):
        raise ValueError('画面 PTS 有间断、丢失或重复')
    subprocess.run(['ffmpeg','-v','error','-xerror','-nostdin','-threads','4','-i',str(path),
                    '-map','0:v:0','-map','0:a:0','-f','null','-'],check=True)
    measured=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-nostats','-i',str(path),'-map','0:a:0','-vn',
                 '-af','loudnorm=print_format=json','-f','null','-'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    found=re.search(r'\{[^{}]*"input_i"[^{}]*\}',measured.stderr)
    if not found:raise ValueError('最终响度缺少读数')
    loud=json.loads(found[0]); i,p,lra=map(float,(loud['input_i'],loud['input_tp'],loud['input_lra']))
    if not (-16.14<=i<=-15.94 and p<=-1.5):raise ValueError(f'成片实测响度超出锁定值：{i} / {p}')
    return {'video':keys,'pts_checked':len(vp),'duration':v['duration'],'full_audio_video_decode':True,
            'faststart':True,'lufs_i':i,'dbtp':p,'lra_lu':lra,'bitrate_bps':int(data['format']['bit_rate']),
            'muxer':data['format']['tags']['encoder']}


def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def gate21_inputs(repo):
    source=repo/'previews'/'gate_2_1'
    path=source/'lossless_parts'/'MANIFEST.json'
    restore=source/'tools'/'restore_lossless.py'
    if not path.is_file() or not restore.is_file():
        raise ValueError('缺少审批版 Gate 2.1 分卷或还原工具；请检出完整仓库分支')
    raw=path.read_bytes().replace(b'\r\n',b'\n')
    if hashlib.sha256(raw).hexdigest()!=PART_MANIFEST_SHA256:
        raise ValueError('Gate 2.1 分卷清单不是 Round 7 审查版')
    m=json.loads(raw);pins=load_fingerprints()
    if set(m)!=set(SCENES):raise ValueError('Gate 2.1 缺季或混入未知样片')
    for sc in SCENES:
        got=m[sc]; lock=pins[sc]
        if (got['output'],got['bytes'],got['sha256'])!=(sc+'_loop.mp4',lock['input_mp4_bytes'],lock['input_mp4_sha256']):
            raise ValueError(f'{sc} 不是已审 Gate 2.1 无损母版')
    return restore,m


def finish_video(picture,release,muxed,qa,tc,native_info,origin,old_audio):
    cut=json.loads((qa/'picture_render.json').read_text(encoding='utf8'))
    if cut['count_written']!=N or picture.stat().st_size!=cut['bytes'] or digest(picture)!=cut['sha256']:
        raise ValueError('画面轨未匹配实际编码链记录')
    log=(qa/'encode.log').read_text(encoding='utf8',errors='replace')
    core=re.search(r'264 - core [^\s]+ r\d+ [0-9a-f]+',log)
    if core:tc['x264']=core[0]
    rgb=cut['assembled_native_stream_sha256']
    same_build=(tc['machine']=='x86_64' and tc['python']=='3.12.14' and tc['packages']['numpy']=='2.3.5'
                and '7.1.5-0+deb13u1' in tc['ffmpeg'])
    match=rgb==INDEPENDENT_RGB_SHA256
    if not match:
        if same_build:raise ValueError(f'本地参考构建的原生叠化 RGB24 未匹配独审：{rgb}')
        print('此工具链的原生过渡舍入与 Debian 参考 SHA 不同，需要在发布前抽帧复查。',file=sys.stderr,flush=True)
    print('RAW RGB24 SHA',rgb,'MATCHES_INDEPENDENT',match,flush=True)

    print('4/5 stream copy 封装；检查音轨逐包身份、PTS、全解码与响度',flush=True)
    subprocess.run(mux_command(picture,release,muxed),check=True)
    new_audio=verify_aac(muxed)
    if new_audio!=old_audio:raise ValueError('封装后 AAC 证据不等于基准')
    final_qa=verify_final(muxed)
    proof={'output':MASTER,'sha256':digest(muxed),'bytes':muxed.stat().st_size,'toolchain':tc,
           'input_manifest_sha256':PART_MANIFEST_SHA256,'native_inputs':native_info,
           'picture_only':{'sha256':cut['sha256'],'bytes':cut['bytes'],'count':cut['count_written']},
           'preencode_native_rgb':{'scope':'5917 ordered frames, 320x180, packed RGB24 byte stream no headers',
                'local_sha256':rgb,'reference_sha256_this_build':INDEPENDENT_RGB_SHA256,
                'reference_toolchain':same_build,'matches_independent_reference':match},
           'audio_source':origin,'audio_packets_preserved':new_audio,'technical_qa':final_qa}
    cut.pop('ffmpeg_args',None)
    return proof,cut


def reproduce(cache,keep_picture):
    repo=root(); restore,manifest=gate21_inputs(repo)
    dist=repo/'dist'; dist.mkdir(exist_ok=True)
    final=dist/MASTER; outqa=dist/'gate3_v21_qa'
    if final.exists() or outqa.exists():raise ValueError(f'已存在尺寸报告或正式文件，请先移出旧文件：{dist}')
    tc=toolchain()
    with TemporaryDirectory(prefix='.gate31-',dir=dist) as workdir:
        work=Path(workdir)
        print('1/5 获取并验证 v2.0 已签收 AAC 音轨',flush=True)
        release,origin=acquire(work/'v20_official.mp4',cache)
        old_audio=verify_aac(release)
        print('AAC LOCK OK',old_audio['packet_count'],old_audio['adts_sha256'],flush=True)
        print('2/5 验证并按序拼接 19 个无损分卷，恢复原生 RGB',flush=True)
        parts,native,qa=work/'lossless',work/'native',work/'qa'
        subprocess.run([sys.executable,str(restore),'--out-dir',str(parts)],check=True)
        native_info={}
        for s in SCENES:
            n=recover(s,parts/manifest[s]['output'],native/(s+'_native.npy'))
            del n['output']; native_info[s]=n
            print('RGB OK',s,n['palette_colors'],n['npy_sha256'],flush=True)

        print('3/5 以已审 v2.0 叠化曲线合成 5917 帧，6× 近邻，只编画面一次',flush=True)
        picture=work/'picture_only.mp4'
        subprocess.run([sys.executable,str(HERE/'assemble.py'),*map(str,picture_args(native,picture,qa))],check=True)
        muxed=work/MASTER
        proof,cut=finish_video(picture,release,muxed,qa,tc,native_info,origin,old_audio)
        proofdir=work/'proof';proofdir.mkdir()
        # Reports intended for the repository contain no absolute host paths.
        write_json(proofdir/'picture_render.json',cut)
        shutil.copyfile(qa/'picture_plan.json',proofdir/'picture_plan.json')
        write_json(proofdir/'reproduction_qa.json',proof)
        if keep_picture:picture.replace(proofdir/'picture-only.mp4')
        if final.exists() or outqa.exists():raise ValueError('待放置最终文件期间目标已经存在；不覆盖')
        muxed.replace(final); proofdir.replace(outqa)
        print('5/5 已重建并校验',final,proof['bytes'],'SHA-256',proof['sha256'],flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--v20-release-cache',type=Path,help='可选，官方 v2.0 完整 MP4 本地缓存；仍按正式 SHA-256 和逐包验证')
    ap.add_argument('--keep-picture',action='store_true',help='一并保留画面母轨，供进一步独立审片')
    a=ap.parse_args()
    try:reproduce(a.v20_release_cache,a.keep_picture)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as e:
        ap.exit(1,f'Gate 3.1 重建失败：{e}\n')


if __name__=='__main__':main()

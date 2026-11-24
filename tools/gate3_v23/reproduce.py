#!/usr/bin/env python3
"""从 Gate 2.3 无损分卷和已签收 v2.0 AAC 一键生成 Rainroji v2.3。"""
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
from review_cues import SAMPLES, CUE_DETAIL

HERE=Path(__file__).resolve().parent
MASTER='Rainroji_Lofi_V2.3_1080p.mp4'
PART_MANIFEST_SHA256='1ee82bfb9686b228c7eb57bc6abb5174621e8cd096792524a494938794e55dcc'
SOURCE_COMMIT='d491fe13aaa2ff4b5addd296d42f1a40b73c85fc'
REVIEW_COMMIT='8fbb28eb7a61329ffa218c6e7f92b4f72d19c6ee'
INDEPENDENT_RGB_SHA256='a3866b5b2ebb58b5c0c14e61f84dbcb8790a07c3db2bc7a4fc2d1aa3142c7b6a'
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
          'pix_fmt':'yuv420p','r_frame_rate':'30/1','avg_frame_rate':'30/1','nb_frames':'5917','color_space':'bt709',
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


def gate23_inputs(repo):
    """Accept only the four input MP4s exactly identified by the approved split manifest."""
    source=repo/'previews'/'gate_2_3'
    path=source/'lossless_parts'/'MANIFEST.json'
    if not path.is_file():
        raise ValueError('缺少已审批的 Gate 2.3 无损分卷；请检出完整项目分支')
    raw=path.read_bytes().replace(b'\r\n',b'\n')
    if hashlib.sha256(raw).hexdigest()!=PART_MANIFEST_SHA256:
        raise ValueError('Gate 2.3 分卷清单不是 Round 13 审查版')
    m=json.loads(raw);pins=load_fingerprints()
    if set(m)!=set(SCENES) or sum(len(m[s]['parts']) for s in SCENES)!=16:
        raise ValueError('Gate 2.3 缺季、缺卷或混入未知样片')
    for sc in SCENES:
        got=m[sc];lock=pins[sc]
        if (got['output'],got['bytes'],got['sha256'])!=(sc+'_loop.mp4',lock['input_mp4_bytes'],lock['input_mp4_sha256']):
            raise ValueError(f'{sc} 不是已审 Gate 2.3 无损母版')
    return source,m


def restore_scene(source,scene,item,outdir):
    if scene not in SCENES or item['output']!=scene+'_loop.mp4' or not item['parts']:
        raise ValueError('分卷场景与输出路径无法验证')
    outdir.mkdir(exist_ok=True,parents=True)
    out=outdir/item['output']
    staging=out.with_suffix('.assembling')
    whole=hashlib.sha256();counts=0
    try:
        with staging.open('xb') as result:
            for index,row in enumerate(item['parts']):
                expected=f'lossless_parts/{scene}/part-{index:02d}.bin'
                if row['path']!=expected:raise ValueError(f'分卷顺序或相对路径无效：{scene} {index}')
                path=(source/expected).resolve(strict=True)
                if not path.is_relative_to(source.resolve()):
                    raise ValueError('分卷路径在仓库之外')
                sub=hashlib.sha256();bytes_=0
                with path.open('rb') as src:
                    while piece:=src.read(1<<20):
                        sub.update(piece);whole.update(piece);result.write(piece)
                        bytes_+=len(piece)
                if (bytes_,sub.hexdigest())!=(row['bytes'],row['sha256']):
                    raise ValueError(f'分卷字节或 SHA-256 不符：{scene} {index}')
                counts+=bytes_
        if (counts,whole.hexdigest())!=(item['bytes'],item['sha256']):
            raise ValueError(f'完整分卷合计未等于审批正本：{scene}')
        if out.exists():raise ValueError(f'拒绝覆盖已经还原的 {scene}')
        staging.replace(out)
    finally:
        staging.unlink(missing_ok=True)
    return out


def video_packets(path):
    payload=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
             '-show_packets','-show_entries','packet=data_hash','-show_data_hash','sha256','-of','json',str(path)]))
    p=payload['packets']
    if len(p)!=N:
        raise ValueError('用于复核的 H.264 包数不符')
    return hashlib.sha256('\n'.join(q['data_hash'] for q in p).encode('ascii')).hexdigest()


def export_decoded(final,where):
    """Unadorned full resolution stills from the actual final mux, not the preencode palette."""
    sample=tuple(sorted(SAMPLES,key=lambda x:x[1]))
    sel='+'.join(f'eq(n,{i})' for _,i in sample)
    subprocess.run(['ffmpeg','-v','error','-xerror','-nostdin','-threads','4','-filter_threads','2','-i',str(final),
              '-map','0:v:0','-an','-vf',f"select='{sel}',scale=in_color_matrix=bt709:in_range=tv:out_range=pc",
              '-fps_mode','passthrough','-frames:v',str(len(sample)),'-threads','1','-start_number','0','-pix_fmt','rgb24',
              str(where/'frame_%02d.png')],check=True)
    evidence={}
    from PIL import Image
    for k,(name,i) in enumerate(sample):
        loc=where/f'frame_{k:02d}.png';title=where/f'decoded_{name}.png'
        with Image.open(loc) as im:
            if im.size!=(1920,1080):raise ValueError('实解码证据分辨率有误')
            im.verify()
        loc.rename(title)
        evidence[title.name]={'frame':i,'seconds':round(i/30,6),'bytes':title.stat().st_size,'sha256':digest(title)}
    return evidence


def finish_video(picture,release,muxed,qa,tc,native_info,origin,old_audio):
    cut=json.loads((qa/'picture_render.json').read_text(encoding='utf8'))
    if cut['count_written']!=N or picture.stat().st_size!=cut['bytes'] or digest(picture)!=cut['sha256']:
        raise ValueError('画面轨未匹配实际编码链记录')
    log=(qa/'encode.log').read_text(encoding='utf8',errors='replace')
    core=re.search(r'264 - core [^\s]+ r\d+ [0-9a-f]+',log)
    if core:tc['x264']=core[0]
    if not re.search(r'\bcrf=14(?:\.0+)?(?:\s|$)',log):
        raise ValueError('实际 H.264 编码日志不含 CRF14')
    rgb=cut['assembled_native_stream_sha256']
    same_build=(tc['machine']=='x86_64' and tc['python']=='3.12.14' and tc['packages']['numpy']=='2.3.5'
                and '7.1.5-0+deb13u1' in tc['ffmpeg'])
    match=rgb==INDEPENDENT_RGB_SHA256
    if not match:
        raise ValueError(f'原生叠化 RGB24 未匹配独审：{rgb}；请核固定 NumPy/计算环境，禁止静默选择不同帧')
    print('RAW RGB24 SHA',rgb,'MATCHES_INDEPENDENT',match,flush=True)

    print('4/5 stream copy 封装；检查音轨逐包身份、PTS、全解码与响度',flush=True)
    subprocess.run(mux_command(picture,release,muxed),check=True)
    new_audio=verify_aac(muxed)
    if new_audio!=old_audio:raise ValueError('封装后 AAC 证据不等于基准')
    video_hash=video_packets(picture)
    if video_packets(muxed)!=video_hash:
        raise ValueError('封装改变了 H.264 视频包')
    final_qa=verify_final(muxed)
    final_qa['video_packet_payload_sequence_sha256']=video_hash
    proof={'output':MASTER,'sha256':digest(muxed),'bytes':muxed.stat().st_size,'toolchain':tc,
           'source_commit':SOURCE_COMMIT,'review_commit':REVIEW_COMMIT,
           'picture_input_policy':'16 pinned Gate 2.3 lossless split parts only; no previous cut, viewing proxy or authored NPY',
           'input_manifest_sha256':PART_MANIFEST_SHA256,'native_inputs':native_info,
           'picture_only':{'sha256':cut['sha256'],'bytes':cut['bytes'],'count':cut['count_written']},
           'preencode_native_rgb':{'scope':'5917 ordered frames, 320x180, packed RGB24 byte stream no headers',
                'local_sha256':rgb,'reference_sha256_this_build':INDEPENDENT_RGB_SHA256,
                'local_toolchain_matches_reference_environment':same_build,'matches_independent_reference':match,
                'adjacent_equal_count':cut['preencode_adjacent_equal_count'],
                'adjacent_equal_timeline_indices':cut['preencode_adjacent_equal_indices']},
           'audio_source':origin,'audio_packets_preserved':new_audio,'technical_qa':final_qa}
    cut.pop('ffmpeg_args',None)
    return proof,cut


def reproduce(cache,keep_picture):
    repo=root(); source,manifest=gate23_inputs(repo)
    dist=repo/'dist'; dist.mkdir(exist_ok=True)
    final=dist/MASTER; outqa=dist/'gate3_v23_qa'
    if final.exists() or outqa.exists():raise ValueError(f'已存在尺寸报告或正式文件，请先移出旧文件：{dist}')
    tc=toolchain()
    with TemporaryDirectory(prefix='.gate33-',dir=dist) as workdir:
        work=Path(workdir)
        print('1/5 获取并验证 v2.0 已签收 AAC 音轨',flush=True)
        release,origin=acquire(work/'v20_official.mp4',cache)
        old_audio=verify_aac(release)
        print('AAC LOCK OK',old_audio['packet_count'],old_audio['adts_sha256'],flush=True)
        print('2/5 验证并按序拼接 16 个无损分卷，恢复原生 RGB',flush=True)
        parts,native,qa=work/'lossless',work/'native',work/'qa'
        native_info={}
        for s in SCENES:
            n=recover(s,restore_scene(source,s,manifest[s],parts),native/(s+'_native.npy'))
            del n['output']; native_info[s]=n
            print('RGB OK',s,n['palette_colors'],n['npy_sha256'],flush=True)

        print('3/5 以已审 v2.0 叠化曲线合成 5917 帧，6× 近邻，只编画面一次',flush=True)
        picture=work/'picture_only.mp4'
        subprocess.run([sys.executable,str(HERE/'assemble.py'),*map(str,picture_args(native,picture,qa))],check=True)
        muxed=work/MASTER
        proof,cut=finish_video(picture,release,muxed,qa,tc,native_info,origin,old_audio)
        proofdir=work/'proof';proofdir.mkdir()
        # Full decoded evidence up to this point is checked against the actual final mux.
        stills=export_decoded(muxed,proofdir)
        subprocess.run([sys.executable,str(HERE/'check_picture.py'),'--native-dir',str(native),
                        '--qa-dir',str(qa),'--picture',str(picture)],check=True)
        for f in ('encoded_transition_storyboard.jpg','picture_complete_qa.json','encode_progress.log','nearest_neighbor_native_qa.json','picture_structural_qa.json'):
            shutil.copyfile(qa/f,proofdir/f)
        log=(qa/'encode.log').read_text(encoding='utf8',errors='replace')
        (proofdir/'encode.log').write_text(log.replace(str(work),'<build-work>'),encoding='utf8')
        write_json(proofdir/'decoded_frame_manifest.json',stills)
        write_json(proofdir/'art_cue_map.json',CUE_DETAIL)
        # Reports intended for the repository contain no absolute host paths.
        write_json(proofdir/'picture_render.json',cut)
        shutil.copyfile(qa/'picture_plan.json',proofdir/'picture_plan.json')
        write_json(proofdir/'reproduction_qa.json',proof)
        if keep_picture:picture.replace(proofdir/'picture-only.mp4')
        evidence={f.name:{'bytes':f.stat().st_size,'sha256':digest(f)} for f in sorted(proofdir.iterdir()) if f.suffix!='.mp4'}
        write_json(proofdir/'evidence_manifest.json',evidence)
        if final.exists() or outqa.exists():raise ValueError('待放置最终文件期间目标已经存在；不覆盖')
        muxed.replace(final); proofdir.replace(outqa)
        print('5/5 已重建并校验',final,proof['bytes'],'SHA-256',proof['sha256'],flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--v20-release-cache',type=Path,help='可选，官方 v2.0 完整 MP4 本地缓存；仍按正式 SHA-256 和逐包验证')
    ap.add_argument('--keep-picture',action='store_true',help='一并保留画面母轨，供进一步独立审片')
    a=ap.parse_args()
    try:reproduce(a.v20_release_cache,a.keep_picture)
    except (OSError,ValueError,KeyError,RuntimeError,subprocess.SubprocessError) as e:
        ap.exit(1,f'Gate 3.3 重建失败：{e}\n')


if __name__=='__main__':main()

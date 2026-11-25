#!/usr/bin/env python3
"""从 Gate 2.9 无损分卷和已签收 v2.8 AAC 一键生成 Rainroji v2.9。"""
import argparse
from fractions import Fraction
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory

from audio_lock import acquire, digest, verify_aac, verify_pcm
from recover_native import SCENES, load_fingerprints, decode
from assemble import PLAN, SOURCE_COMMIT, REVIEW_COMMIT, picture_plan, rgb_locks, run_encode

HERE=Path(__file__).resolve().parent
MASTER='Rainroji_Lofi_V2.9_1080p.mp4'
PART_MANIFEST_SHA256='5bd9cb10e58907d10a28e338677fc2c3f70ae691de9f724bec418225f9cc0739'
N=5917


def root():
    return HERE.parents[1]


def mux_command(picture,release,final):
    return ['ffmpeg','-v','error','-nostdin','-n','-i',str(picture),'-i',str(release),
            '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy','-movie_timescale','48000',
            '-movflags','+faststart','-metadata','creation_time=2026-11-25T00:00:00Z',str(final)]


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
    # The approved cross-platform FFmpeg variants agree on matrix/range;
    # some libx264 wrappers leave the transfer and primaries unspecified.
    tags={k:v.get(k,'unspecified') for k in ('color_transfer','color_primaries')}
    if any(t not in ('bt709','unknown','unspecified') for t in tags.values()):
        raise ValueError(f'Non-BT.709 colour profile signalled by the video stream: {tags}')
    keys.update(tags)
    tick=Fraction(v['time_base']); cadence=1/(30*tick)
    if tick*v['duration_ts']!=Fraction(N,30) or cadence.denominator!=1 or a['codec_type']!='audio' or tick*v['duration_ts']!=Fraction(a['duration_ts'])*Fraction(a['time_base']):
        raise ValueError('画面时长或音轨数不符')
    vp=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_packets',
                  '-show_entries','packet=pts,duration','-of','json',str(path)]))['packets']
    if sorted(int(p['pts']) for p in vp)!=[i*int(cadence) for i in range(N)] or any(int(p['duration'])!=cadence for p in vp):
        raise ValueError('画面 PTS 有间断、丢失或重复')
    measured=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-nostats','-i',str(path),'-map','0:a:0','-vn',
                 '-af','loudnorm=print_format=json','-f','null','-'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    found=re.search(r'\{[^{}]*"input_i"[^{}]*\}',measured.stderr)
    if not found:raise ValueError('最终响度缺少读数')
    loud=json.loads(found[0]); i,p,lra=map(float,(loud['input_i'],loud['input_tp'],loud['input_lra']))
    if not (-16.25<=i<=-15.85 and -5.00<=p<=-4.40):raise ValueError(f'成片实测响度超出锁定值：{i} / {p}')
    return {'video':keys,'pts_checked':len(vp),'duration':v['duration'],'faststart':True,'lufs_i':i,'dbtp':p,'lra_lu':lra,'bitrate_bps':int(data['format']['bit_rate']),
            'muxer':data['format']['tags']['encoder']}


def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def gate29_inputs(repo):
    """Use only the 16 volumes in the pinned Round 33 manifest."""
    source=repo/'previews'/'gate_2_9'
    path=source/'lossless_parts'/'MANIFEST.json'
    if not path.is_file():
        raise ValueError('缺少已审批的 Gate 2.9 无损分卷；请检出完整项目分支')
    raw=path.read_bytes().replace(b'\r\n',b'\n')
    if hashlib.sha256(raw).hexdigest()!=PART_MANIFEST_SHA256:
        raise ValueError('Gate 2.9 分卷清单不是 Round 33 审查版')
    m=json.loads(raw);pins=load_fingerprints()
    if set(m)!=set(SCENES) or [len(m[s]['parts']) for s in SCENES]!=[1,8,1,6]:
        raise ValueError('Gate 2.9 缺季、缺卷或混入未知样片')
    for sc in SCENES:
        got=m[sc];lock=pins[sc]
        if (got['output'],got['bytes'],got['sha256'])!=(sc+'_loop.mp4',lock['input_mp4_bytes'],lock['input_mp4_sha256']):
            raise ValueError(f'{sc} 不是已审 Gate 2.9 无损母版')
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



def finish_video(picture, release, muxed, qa, toolchain_info, native_info, origin, old_audio, cut):
    if cut['count_written'] != N or digest(picture) != cut['sha256']:
        raise ValueError('画面轨未匹配实际编码链记录')
    log = (qa/'encode.log').read_text(encoding='utf8',errors='replace')
    core = re.search(r'264 - core [^\s]+ r\d+ [0-9a-f]+',log)
    if core:
        toolchain_info['x264'] = core[0]
    if not re.search(r'\bcrf=14(?:\.0+)?(?:\s|$)',log):
        raise ValueError('实际 H.264 编码日志不含 CRF14')
    print('4/5 复制 v2.8 原始音轨并逐包核验',flush=True)
    subprocess.run(mux_command(picture,release,muxed),check=True)
    new_audio = verify_aac(muxed)
    new_audio['pcm_decode_comparison'] = verify_pcm(muxed)
    if new_audio != old_audio:
        raise ValueError('封装后 AAC 证据与 v2.8 基准不同')
    video_hash = video_packets(picture)
    if video_packets(muxed) != video_hash:
        raise ValueError('封装改变了 H.264 视频包')
    final_qa = verify_final(muxed)
    final_qa['video_packet_payload_sequence_sha256'] = video_hash
    final_qa['crf_from_encoder_log'] = 14
    return {'output':MASTER,'sha256':digest(muxed),'bytes':muxed.stat().st_size,'toolchain':toolchain_info,
            'source_commit':SOURCE_COMMIT,'review_commit':REVIEW_COMMIT,
            'picture_input_policy':'16 pinned Gate 2.9 lossless volumes only; final v2.8 MP4 is opened for AAC only',
            'input_manifest_sha256':PART_MANIFEST_SHA256,'native_inputs':native_info,
            'picture_only':{'sha256':cut['sha256'],'bytes':cut['bytes'],'count':cut['count_written']},
            'preencode_native_rgb':{'scope':'5917 ordered 320x180 packed RGB24 frames, no headers',
                 'local_sha256':cut['assembled_native_stream_sha256'],'independent_reference':rgb_locks(),
                 'actual_window_fingerprints':cut['scored_rgb_domains'],
                 'actual_boundary_frame_fingerprints':cut['boundary_frame_rgb_sha256'],
                 'adjacent_equal_timeline_indices':cut['preencode_adjacent_equal_indices']},
            'audio_source':origin,'audio_packets_preserved':new_audio,'technical_qa':final_qa}


def reproduce(cache, keep_picture):
    repo=root(); source,manifest=gate29_inputs(repo)
    dist=repo/'dist'; dist.mkdir(exist_ok=True)
    final=dist/MASTER; outqa=dist/'gate3_v29_qa'
    if final.exists() or outqa.exists():
        raise ValueError(f'已有成片或报告：{dist}；重建前将现有输出移到另一位置')
    tc=toolchain()
    if cache is None and os.getenv('RAINROJI_V28_RELEASE_CACHE'):
        cache=Path(os.environ['RAINROJI_V28_RELEASE_CACHE'])
    with TemporaryDirectory(prefix='.gate39-',dir=dist) as workdir:
        work=Path(workdir)
        print('1/5 核验已签收 v2.8 AAC 原轨',flush=True)
        release,origin=acquire(work/'v28_official.mp4',cache)
        old_audio=verify_aac(release)
        old_audio['pcm_decode_comparison']=verify_pcm(release)
        print('AAC LOCK OK',old_audio['packet_count'],old_audio['adts_sha256'],flush=True)
        print('2/5 验证并按序还原 16 个正式无损分卷；双循环逐帧检查',flush=True)
        native=[]; native_info={}
        for scene in SCENES:
            restored=restore_scene(source,scene,manifest[scene],work/'split')
            frames,info=decode(scene,restored)
            native.append(frames); native_info[scene]=info
            restored.unlink()
            print('RGB OK',scene,info['palette_colors'],info['rgb_sha256'],flush=True)
        qa=work/'proof'; qa.mkdir()
        plan=picture_plan(PLAN,native_info)
        print('3/5 原生 RGB 叠化 5917 帧；6× 最近邻；H.264 High CRF14',flush=True)
        picture=work/'picture_only.mp4'
        cut=run_encode(PLAN,native,picture,qa)
        write_json(qa/'picture_render.json',cut)
        write_json(qa/'picture_plan.json',plan)
        print('RGB LOCK OK',cut['assembled_native_stream_sha256'],flush=True)
        muxed=work/MASTER
        proof=finish_video(picture,release,muxed,qa,tc,native_info,origin,old_audio,cut)
        print('5/5 从封装成片实解码生成审片素材',flush=True)
        from review_exports import export_reviews
        review=export_reviews(muxed,qa,PLAN,native)
        write_json(qa/'review_manifest.json',review)
        proof['technical_qa']['full_picture_decode_without_errors']=review['full_sequential_decode_without_errors']
        proof['technical_qa']['full_flattened_audio_pcm_decode_without_errors']=True
        proof['technical_qa']['decoded_black_endpoints']=review['decoded_black_endpoints']
        write_json(qa/'reproduction_qa.json',proof)
        log=(qa/'encode.log').read_text(encoding='utf8',errors='replace')
        (qa/'encode.log').write_text(log.replace(str(work),'<build-work>'),encoding='utf8')
        if keep_picture:
            picture.replace(qa/'picture-only.mp4')
        evidence={f.name:{'bytes':f.stat().st_size,'sha256':digest(f)}
                  for f in sorted(qa.iterdir()) if f.name!='picture-only.mp4'}
        write_json(qa/'evidence_manifest.json',evidence)
        if final.exists() or outqa.exists():
            raise ValueError('输出目标已存在')
        muxed.replace(final); qa.replace(outqa)
        print('Gate 3.9 VERIFIED',final,proof['bytes'],'SHA-256',proof['sha256'],flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--v28-release-cache',type=Path,help='已签收 v2.8 正式 MP4 的可选本地副本（完整校验后取 AAC）')
    ap.add_argument('--keep-picture',action='store_true',help='同时保留原封装前的画面轨')
    a=ap.parse_args()
    try:
        reproduce(a.v28_release_cache,a.keep_picture)
    except (OSError,ValueError,KeyError,RuntimeError,subprocess.SubprocessError) as e:
        ap.exit(1,f'Gate 3.9 重建失败：{e}\n')


if __name__=='__main__':
    main()

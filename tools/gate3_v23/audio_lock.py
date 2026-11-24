"""Acquire and independently prove the already-accepted v2.0 Release AAC packets."""
from pathlib import Path
import hashlib
import json
import subprocess
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

RELEASE_URL = ('https://github.com/yiggeror/all-test-for-new-modle/releases/download/'
               'v2.0-rainroji-lofi-1080p/Rainroji_Lofi_V2_1080p.mp4')
RELEASE_BYTES = 151_157_219
RELEASE_SHA256 = '2987f1b6b85cc9fe2ecc165315b3cc8fef6dc3c9eae4b3efdd2101f67569fe5b'
ADTS_SHA256 = '3eb43b1c07211e4ece9173fae7ff25e73e4195f50c430e2f388285971725693d'
AAC_PACKET_SHA256 = '8c0f0358f256edcef450828d5bc4bde0fd173b9c6090acf45a56b8787452f2a0'
COUNT = 9247
HOSTS = {'github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'}


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


class GitHubDownload(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        branch=urlsplit(newurl)
        if branch.scheme!='https' or branch.hostname not in HOSTS or branch.username or branch.password:
            raise ValueError('v2.0 官方资产被重定向至未经验证的主机')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def acquire(destination, cache=None):
    if cache is not None:
        release=cache
    else:
        release=destination
        req=Request(RELEASE_URL,headers={'User-Agent':'Rainroji-Gate33-Repro/2.3','Accept':'application/octet-stream'})
        total=0
        with build_opener(GitHubDownload()).open(req,timeout=60) as reply, release.open('xb') as f:
            while block:=reply.read(1<<20):
                total+=len(block)
                if total>RELEASE_BYTES:raise ValueError('v2.0 资产大于审核锁定的字节数')
                f.write(block)
    size=release.stat().st_size
    sha=digest(release)
    if (size,sha)!=(RELEASE_BYTES,RELEASE_SHA256):
        raise ValueError(f'不是已签收的 v2.0 GitHub 正式发布件：{size} bytes SHA-256 {sha}')
    return release,{'url':RELEASE_URL,'bytes':size,'mp4_sha256':sha,'used_verified_local_cache':cache is not None}


def verify_aac(path):
    payload=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','a:0',
            '-show_streams','-show_packets','-show_data_hash','sha256','-of','json',str(path)]))
    a,=payload['streams']; packets=payload['packets']
    keys={'codec_name':'aac','profile':'LC','sample_rate':'48000','channels':2,'time_base':'1/48000',
          'start_pts':0,'duration_ts':9_467_200}
    require={k:[a.get(k),v] for k,v in keys.items() if a.get(k)!=v}
    if require:raise ValueError(f'AAC 流规格不匹配：{require}')
    if len(packets)!=COUNT:raise ValueError(f'AAC 包不是 {COUNT}，实际 {len(packets)}')
    timing=[]
    for i,p in enumerate(packets):
        row=(int(p['pts']),int(p['dts']),int(p['duration']),int(p['size']))
        start=(i-1)*1024
        if row[:3]!=(start,start,320 if i==COUNT-1 else 1024):
            raise ValueError(f'AAC 包 {i} 的 PTS/DTS/有效时长改变：{row[:3]}')
        timing.append(row)
    priming=next((d for d in packets[0].get('side_data_list',[]) if d['side_data_type']=='Skip Samples'),{})
    if priming.get('skip_samples')!=1024 or priming.get('discard_padding')!=0:
        raise ValueError(f'AAC 首包 priming 改变：{priming}')
    seq=hashlib.sha256('\n'.join(p['data_hash'] for p in packets).encode('ascii')).hexdigest()
    if seq!=AAC_PACKET_SHA256:raise ValueError(f'AAC 包载荷顺序 SHA-256 改变：{seq}')
    raw_adts=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(path),
                                     '-map','0:a:0','-c','copy','-f','adts','-'])
    adts=hashlib.sha256(raw_adts).hexdigest()
    if adts!=ADTS_SHA256:raise ValueError(f'AAC ADTS SHA-256 改变：{adts}')
    return {'packet_count':COUNT,'packet_payload_sequence_sha256':seq,'adts_sha256':adts,
            'audio_timing_bytes_identity_sha256':hashlib.sha256(json.dumps(timing,separators=(',',':')).encode()).hexdigest(),
            'first_pts_dts_duration_size':timing[0],'last_pts_dts_duration_size':timing[-1],
            'skip_samples':priming['skip_samples'],'stream':{k:a[k] for k in keys}}

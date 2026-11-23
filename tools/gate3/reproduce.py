#!/usr/bin/env python3
"""从本仓库的 Gate 2 无损分卷和作者原曲重建四季成片。"""
import argparse
from fractions import Fraction
import hashlib
from importlib import metadata
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from urllib.request import HTTPSHandler, HTTPRedirectHandler, Request, build_opener


HERE = Path(__file__).resolve().parent
SCENES = ('spring', 'summer', 'autumn', 'winter')
AUTHOR_URL = 'https://html-classic.itch.zone/html/19949767/media/Green%20Tea.mp3'
AUTHOR_PAGE = 'https://purrplecat.itch.io/bloom'
AUTHOR_SHA = 'f6feac60dc29b89ea1513e04d0b30addf86f9c8576827e7566e27b5abd522e71'
MASTER = 'Rainroji_Lofi_V2_1080p.mp4'
MASTER_SHA = '0213513d08d439c965ef7320b2d896814733fac404d2dc6ddfeac4c122da60ba'
MASTER_SIZE = 151_159_718
ASSEMBLED_RGB_SHA = '28446e901b65b6b0aa1beab68022d0a6973823b92ac2e5fb3bf5afcfe6bcfb62'
PICTURE_SHA = 'd0be880e37999ef96b22e24a9b4ac6cd5307f4c6c05816b64b9a4db841b5232f'
AUDIO_SHA = 'dce0e1cb05159107f468577fffabc02dab15cc37823dbf5b507ee4e2d65679ab'
DEPS = ('numpy', 'scipy', 'Pillow')


def checkout_root():
    return HERE.parents[1]


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def mux_command(video, audio, output):
    return ['ffmpeg', '-v', 'error', '-nostdin', '-n', '-i', str(video), '-i', str(audio),
            '-map', '0:v:0', '-map', '1:a:0', '-c', 'copy', '-movie_timescale', '48000',
            '-movflags', '+faststart', '-metadata', 'creation_time=2026-11-23T00:00:00Z',
            str(output)]


def picture_args(native, video, qa):
    return ('--native-dir', native, '--output', video, '--qa-dir', qa,
            '--centers-frame', 1440, 2880, 4320, '--transition-frames', 60,
            '--tail-frames', 114, '--audio-seconds', '197.2142916666666666666666667',
            '--no-storyboard')


def check_existing_master(path):
    if not path.exists():
        return False
    if path.stat().st_size != MASTER_SIZE or digest(path) != MASTER_SHA:
        raise ValueError(f'目标已经存在但不是通过验收的原件，不覆盖：{path}')
    return True


def verify_faststart(path):
    size = path.stat().st_size
    boxes = []
    with path.open('rb') as f:
        pos = 0
        while pos < size:
            f.seek(pos)
            b = f.read(8)
            if len(b) != 8:
                raise ValueError('MP4 尾部不完整')
            n, label = struct.unpack('>I4s', b)
            header = 8
            if n == 1:
                extended = f.read(8)
                if len(extended) != 8:
                    raise ValueError('MP4 扩展盒不完整')
                n, header = struct.unpack('>Q', extended)[0], 16
            elif n == 0:
                n = size - pos
            if n < header or pos + n > size:
                raise ValueError('MP4 盒大小无效')
            boxes.append(label)
            pos += n
    if b'moov' not in boxes or b'mdat' not in boxes or boxes.index(b'moov') > boxes.index(b'mdat'):
        raise ValueError('MP4 缺少 faststart：moov 必须在 mdat 之前')


class SameHostRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        origin = urlsplit(newurl)
        if origin.scheme != 'https' or origin.netloc != urlsplit(AUTHOR_URL).netloc:
            raise ValueError('作者原曲地址重定向离开已核实的 HTTPS 主机')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_author(out):
    request = Request(AUTHOR_URL, headers={'User-Agent': 'Rainroji-Gate3-Repro/2.0',
                                          'Referer': AUTHOR_PAGE, 'Accept': 'audio/mpeg,*/*;q=0.5'})
    conn = build_opener(SameHostRedirect(), HTTPSHandler())
    hasher = hashlib.sha256()
    n = 0
    with conn.open(request, timeout=40) as response, out.open('xb') as f:
        while chunk := response.read(1 << 20):
            n += len(chunk)
            if n > 16 * 1024 * 1024:
                raise ValueError('原曲响应超过预期大小，请检查作者源')
            hasher.update(chunk)
            f.write(chunk)
    if hasher.hexdigest() != AUTHOR_SHA:
        raise ValueError(f'作者原曲不是已定版录音（SHA-256 {hasher.hexdigest()}），不会合片')
    return {'url': AUTHOR_URL, 'bytes': n, 'sha256': hasher.hexdigest()}


def toolchain():
    packages = {}
    for name in DEPS:
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError as exc:
            requirement = HERE/'requirements.txt'
            raise ValueError(f'缺少 {name}。先运行：python -m pip install -r "{requirement}"') from exc
    media = {}
    for exe in ('ffmpeg', 'ffprobe'):
        try:
            media[exe] = subprocess.check_output([exe, '-version'], text=True).splitlines()[0]
        except FileNotFoundError as exc:
            raise ValueError(f'PATH 中没有 {exe}，请安装含 libx264 的 FFmpeg（验收环境为 7.1.5）') from exc
    return {'python': sys.version.split()[0], 'packages': packages, **media}


def run_python(script, *args):
    subprocess.run([sys.executable, str(script), *map(str, args)], check=True)


def verify_master(path):
    verify_faststart(path)
    info = json.loads(subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)]))
    streams = info['streams']
    if len(streams) != 2:
        raise ValueError('成片不是一条视频 + 一条音频')
    v, a = streams
    def ensure(obj, expected, name):
        wrong = {k: [obj.get(k), value] for k, value in expected.items() if obj.get(k) != value}
        if wrong:
            raise ValueError(f'{name}轨参数不符合：{wrong}')
    ensure(v, {'codec_name': 'h264', 'profile': 'High', 'width': 1920, 'height': 1080,
               'pix_fmt': 'yuv420p', 'avg_frame_rate': '30/1', 'nb_frames': '5917',
               'color_space': 'bt709', 'color_range': 'tv', 'start_pts': 0}, '视频')
    ensure(a, {'codec_name': 'aac', 'profile': 'LC', 'channels': 2, 'sample_rate': '48000',
               'time_base': '1/48000', 'duration_ts': 9_467_200, 'start_pts': 0}, '音频')
    if Fraction(v['time_base']) * v['duration_ts'] != Fraction(5917, 30):
        raise ValueError('视频播放时长不是 5917/30 秒')
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-nostdin', '-threads', '4', '-i', str(path),
                    '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'], check=True)
    meter = subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-nostats', '-i', str(path),
                             '-map', '0:a:0', '-vn', '-af', 'loudnorm=print_format=json', '-f', 'null', '-'],
                            check=True, capture_output=True, text=True)
    measured = re.search(r'\{[^{}]*"input_i"[^{}]*\}', meter.stderr)
    if measured is None:
        raise ValueError('未取得成片响度测量')
    loudness = json.loads(measured[0]); i, tp = float(loudness['input_i']), float(loudness['input_tp'])
    if not (-16.5 <= i <= -15.5 and tp <= -1.5):
        raise ValueError(f'最终响度越界：{i} LUFS-I, {tp} dBTP')
    return {'fully_decoded': True, 'faststart': True, 'frames': int(v['nb_frames']),
            'size_1080p': [v['width'], v['height']], 'fps': v['avg_frame_rate'],
            'duration': info['format']['duration'], 'video_profile': v['profile'],
            'audio_channels': a['channels'], 'audio_sample_rate': int(a['sample_rate']),
            'audio_timeline_samples': a['duration_ts'], 'lufs_i': i, 'dbtp': tp}


def reproduce():
    root = checkout_root()
    gate2 = root/'previews'/'gate_2'
    restore = gate2/'tools'/'restore_lossless.py'
    manifest_path = gate2/'lossless_parts'/'MANIFEST.json'
    if not restore.is_file() or not manifest_path.is_file():
        raise ValueError('缺少已审 Gate 2 分卷或原复原工具；请取完整的项目分支，不要只下载脚本')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if set(manifest) != set(SCENES) or any(manifest[s]['output'] != f'{s}_loop.mp4' for s in SCENES):
        raise ValueError('Gate 2 分卷清单不符合四季母版布局')

    dist = root/'dist'; dist.mkdir(exist_ok=True)
    final = dist/MASTER
    if check_existing_master(final):
        print(f'已有已验收原件：{final}\nSHA-256 {MASTER_SHA}', flush=True)
        return
    tc = toolchain()

    with TemporaryDirectory(prefix='.gate3-', dir=dist) as tmp:
        work = Path(tmp)
        music = work/'green.mp3'
        print('1/5 下载并校验作者原曲', flush=True)
        author = download_author(music)
        parts, native = work/'lossless', work/'native'
        native.mkdir()
        print('2/5 核验并拼合 Gate 2 分卷；恢复 320×180 RGB', flush=True)
        run_python(restore, '--out-dir', parts)
        for scene in SCENES:
            run_python(HERE/'recover_native.py', '--scene', scene, '--input', parts/manifest[scene]['output'],
                       '--output', native/f'{scene}_native.npy')

        print('3/5 组装并编码画面一次；混合并编码完整音频一次', flush=True)
        picture = work/'picture.mp4'
        picture_qa = work/'picture_qa'
        run_python(HERE/'assemble.py', *picture_args(native, picture, picture_qa))
        audio_dir = work/'audio'
        run_python(HERE/'gate3_audio.py', '--music', music, '--out', audio_dir,
                   '--scratch', work/'audio_tmp', '--no-stems')
        audio = audio_dir/'green_tea_gate3.m4a'
        render = json.loads((picture_qa/'picture_render.json').read_text(encoding='utf-8'))
        rendered_rgb = render['assembled_native_stream_sha256']
        if rendered_rgb != ASSEMBLED_RGB_SHA:
            raise ValueError(f'叠化后的原生 RGB 流不匹配：{rendered_rgb}')

        print('4/5 原样封装两条流，复验完整解码和响度', flush=True)
        muxed = work/MASTER
        subprocess.run(mux_command(picture, audio, muxed), check=True)
        checked = verify_master(muxed)
        actual = digest(muxed)
        intermediates = {'picture_mp4_actual': render['sha256'], 'picture_mp4_reference': PICTURE_SHA,
                         'audio_m4a_actual': digest(audio), 'audio_m4a_reference': AUDIO_SHA,
                         'assembled_native_rgb_sha256': rendered_rgb}
        exact = actual == MASTER_SHA and muxed.stat().st_size == MASTER_SIZE
        report = {'approved_master_sha256': MASTER_SHA, 'output_sha256': actual,
                  'output_bytes': muxed.stat().st_size, 'byte_exact': exact,
                  'toolchain': tc, 'author_recording': author, 'intermediate_sha256': intermediates,
                  'technical_qa': checked}
        print('5/5 比对整片 SHA-256', flush=True)
        report_tmp = work/'reproduction_qa.json'
        report_tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        report_tmp.replace(dist/'reproduction_qa.json')
        if not exact:
            raise ValueError(f'已生成并解码，但整片 SHA-256 {actual} 与验收母版不一致。'
                             f'不会发布成品文件；请查 {dist/"reproduction_qa.json"} 的工具链／中间哈希')
        if not check_existing_master(final):
            muxed.replace(final)
        print(f'字节级一致：{final}\n{MASTER_SIZE} bytes, SHA-256 {actual}', flush=True)


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        reproduce()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f'复现失败：{exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

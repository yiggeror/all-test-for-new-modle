#!/usr/bin/env python3
"""Gate 1：检查干净的、编码前的 1080p PNG。只判断网格，不给构图打分。

依赖：Python、Pillow、NumPy。例：
  python check_grid.py 6 spring_320_1080.png --native spring_320.png
  python check_grid.py 5 spring_384_1080.png autumn_384_1080.png
输出每张图的 JSON；只要有图失败/无法判断即返回 1。场景色板与注释应放在独立附页。
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image

def _pixels(path, size):
    path=Path(path)
    with path.open('rb') as f:
        header=f.read(26)
    if header[:8]!=b'\x89PNG\r\n\x1a\n':
        raise ValueError('不是 PNG；不能用 JPEG 或有损影片抽帧验证整数网格')
    if len(header)<26 or header[24]>8:
        raise ValueError('仅校验最高 8 位深的 PNG，不能忽略高位深差异')
    with Image.open(path) as im:
        if im.size!=size:
            raise ValueError(f'实际尺寸 {im.width}×{im.height}，需要 {size[0]}×{size[1]}')
        if getattr(im,'is_animated',False):
            raise ValueError('输入必须是单张静帧')
        rgba=im.convert('RGBA')
        if rgba.getchannel('A').getextrema()!=(255,255):
            raise ValueError('存在透明像素，无法作为最终全幅画面')
        return np.array(rgba.convert('RGB'))

def check(path,factor,native=None):
    result={'file':str(path),'factor':factor,'ok':False}
    if factor not in (5,6):
        return dict(result,error='factor 须为 5 或 6')
    try:
        a=_pixels(path,(1920,1080))
        h,w=1080//factor,1920//factor
        result['logical_wh']=[w,h]
        cells=a.reshape(h,factor,w,factor,3).transpose(0,2,1,3,4)
        anchors=cells[:,:,0,0,:]
        bad=(cells!=anchors[:,:,None,None,:]).any(axis=(2,3,4))
        count=int(bad.sum())
        result.update(bad_blocks=count,block_count=w*h)
        if count:
            iy,ix=np.argwhere(bad)[0]
            return dict(result,first_bad_xy=[int(ix),int(iy)],error='同一逻辑块内不是单一 RGB，或网格有偏移')
        result['unique_colors']=len(np.unique(anchors.reshape(-1,3),axis=0))
        if native is not None:
            src=_pixels(native,(w,h))
            result['matches_native']=bool(np.array_equal(anchors,src))
            if not result['matches_native']:
                return dict(result,error='每块内部一致，但与提供的原生图不逐像素相等')
        # 若所有可见边缘也兼容另一候选网格，只凭这张大图无法区分 5× 与 6×。
        other=5 if factor==6 else 6
        cx=np.flatnonzero(np.any(anchors[:,1:]!=anchors[:,:-1],axis=(0,2)))+1
        cy=np.flatnonzero(np.any(anchors[1:]!=anchors[:-1],axis=(1,2)))+1
        result['ambiguous']=not (np.any((cx*factor)%other!=0) or np.any((cy*factor)%other!=0))
        if result['ambiguous'] and (native is None or result['unique_colors']==1):
            return dict(result,error='画面同时兼容两个网格，或整图纯色；不能从这张图确认原生颗粒度')
        return dict(result,ok=True)
    except (OSError,ValueError,IndexError) as e:
        return dict(result,error=str(e))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('factor',type=int,choices=(5,6));p.add_argument('png',nargs='+')
    p.add_argument('--native',help='可选：真正原生的 320×180 或 384×216 PNG；只能用于一张输出')
    a=p.parse_args()
    if a.native and len(a.png)!=1:p.error('--native 只能与一张待检输出搭配')
    results=[check(path,a.factor,a.native) for path in a.png]
    for r in results: print(json.dumps(r,ensure_ascii=False))
    sys.exit(0 if all(r['ok'] for r in results) else 1)

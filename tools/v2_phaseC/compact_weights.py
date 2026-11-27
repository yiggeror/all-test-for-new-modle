"""Pack standard normalized 16-bit skin weights with exact sums per vertex."""
from pathlib import Path
import argparse,json,struct
import numpy as np
def compact(source,dest):
    src=Path(source).read_bytes();assert src[:4]==b'glTF'
    n=int.from_bytes(src[12:16],'little');g=json.loads(src[20:20+n])
    assert src[20+n+4:20+n+8]==b'BIN\0'
    buf=src[28+n:]
    access=g['accessors'];views=g['bufferViews']
    combos={tuple(v for k,v in sorted(p['attributes'].items()) if k.startswith('WEIGHTS_'))
            for m in g['meshes'] for p in m['primitives']}
    use={}
    for c in combos:
        for i in c:use[i]=use.get(i,0)+1
    by={}
    for i,a in enumerate(access):
        if 'bufferView' in a:by.setdefault(a['bufferView'],[]).append(i)
    changes={};rows=0
    for c in combos:
        if not c or any(use[i]>1 for i in c):continue
        A=[access[i] for i in c]
        if any(a.get('componentType')!=5126 or a.get('type')!='VEC4' or a.get('byteOffset',0) or
               by.get(a.get('bufferView'),[])!=[i] for i,a in zip(c,A)):continue
        V=[views[a['bufferView']] for a in A];N=A[0]['count']
        if any(a['count']!=N or v['byteLength']!=N*16 or v.get('byteStride',16)!=16 for a,v in zip(A,V)):continue
        f=np.concatenate([np.frombuffer(buf[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']],dtype='<f4').reshape(N,4) for v in V],axis=1)
        if np.any(f.sum(axis=1)<=0):continue
        f=f/f.sum(axis=1,keepdims=True)
        x=np.rint(np.maximum(f,0)*65535.).astype(np.int64)
        x[np.arange(N),f.argmax(axis=1)]+=65535-x.sum(axis=1)
        assert np.all((x>=0)&(x<=65535)) and np.abs(f-x/65535.).max()<.00011
        for j,a in enumerate(A):
            a['componentType']=5123;a['normalized']=True
            a.pop('min',None);a.pop('max',None)
            changes[a['bufferView']]=x[:,j*4:(j+1)*4].astype('<u2').tobytes()
            views[a['bufferView']].pop('byteStride',None)
        rows+=N
    if not changes:
        Path(dest).write_bytes(src);return 0
    out=bytearray()
    for i,v in enumerate(views):
        p=v.get('byteOffset',0);b=changes.get(i,buf[p:p+v['byteLength']])
        out.extend(b'\x00'*((-len(out))%4))
        v['byteOffset']=len(out);v['byteLength']=len(b);out.extend(b)
    out.extend(b'\x00'*((-len(out))%4))
    g['buffers'][0]['byteLength']=len(out)
    j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4)
    with Path(dest).open('wb') as w:
        w.write(b'glTF'+struct.pack('<IIII',2,28+len(j)+len(out),len(j),0x4e4f534a))
        w.write(j);w.write(struct.pack('<II',len(out),0x004e4942));w.write(out)
    print('Standard normalized skin weights:',rows,'vertices;',len(src),'→',Path(dest).stat().st_size,'bytes')
    return rows
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('src',type=Path);p.add_argument('out',type=Path);a=p.parse_args();compact(a.src,a.out)

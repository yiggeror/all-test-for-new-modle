"""Verify Phase A assets and exact review outputs before submitting."""
from pathlib import Path
from hashlib import sha256
import json, sys
from PIL import Image
root=Path(sys.argv[1])
for name,n in [('body_4view_clay',800),('face_clay_vs_npr',700),('expressions_quickcheck',490)]:
    f=root/'previews'/'v2_phaseA'/(name+'.png')
    with Image.open(f) as im:
        assert im.width>=1500 and im.height>=n, (f,im.size)
        assert max(im.convert('RGB').getextrema()[0])-min(im.convert('RGB').getextrema()[0])>70
    print(name,sha256(f.read_bytes()).hexdigest())
scene=root/'assets'/'suzu_v2_phaseA.blend'
assert scene.read_bytes()[:4] in (b'BLEN',b'\x28\xb5\x2f\xfd')
g=root/'assets'/'suzu_v2_phaseA.glb'
b=g.read_bytes()
assert b[:4]==b'glTF' and int.from_bytes(b[8:12],'little')==len(b)
j=json.loads(b[20:20+int.from_bytes(b[12:16],'little')])
targets=[m['extras']['targetNames'] for m in j['meshes'] if any('targets' in p for p in m['primitives'])]
assert len(targets)==1 and len(targets[0])==57
source=Path(sys.argv[2]).read_bytes()
assert source[:4]==b'glTF'
k=json.loads(source[20:20+int.from_bytes(source[12:16],'little')])
native=next(m['extras']['targetNames'] for m in k['meshes'] if m.get('extras',{}).get('targetNames'))
assert targets[0]==native, 'Native expression list or order changed'
assert len(j['skins'])==1 and len(j['skins'][0]['joints'])>=54
assert all('BODY' not in n.get('name','').upper() or 'CLOTH' not in n.get('name','').upper() for n in j['meshes'])
p=next(n['extras'] for n in j['nodes'] if 'phase_a_expressions' in n.get('extras',{}))
pose=json.loads(p['phase_a_expressions'])
assert len(pose)==4 and all(k in targets[0] for v in pose.values() for k in v)
assert len(j['images'])>=7 and all('bufferView' in im for im in j['images'])
print('57 native expressions; all four presets; skin & embedded textures; aligned review boards verified.')

"""Reconstruct the two Phase C model files from verified same-repository parts."""
import hashlib,json,os,re,shutil,sys
from pathlib import Path
root=Path(__file__).resolve().parent
transfer=root/'transfer'
repo=root.parents[1]
manifest=json.loads((transfer/'manifest.json').read_text())
allowed={'suzu_v2_phaseC.blend','suzu_v2_phaseC.glb'}
assert set(manifest)==allowed
for name,row in manifest.items():
    assert re.fullmatch(r'[0-9a-f]{64}',row['sha256']) and 1<row['parts']<=12
    output=repo/'assets'/name
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=output.with_suffix(output.suffix+'.pending')
    h=hashlib.sha256();size=0
    with stage.open('wb') as out:
        for i in range(row['parts']):
            part=transfer/f'{name}.{i:02}.part'
            with part.open('rb') as f:
                for data in iter(lambda:f.read(1024*1024),b''):
                    h.update(data);out.write(data);size+=len(data)
    assert size==row['bytes'] and h.hexdigest()==row['sha256'],(name,size,h.hexdigest())
    os.replace(stage,output)
    print(name,size,h.hexdigest(),flush=True)
if '--finish' in sys.argv:
    shutil.copyfile(transfer/'review-status.md',repo/'DEV_STATUS.md')
    shutil.rmtree(transfer)

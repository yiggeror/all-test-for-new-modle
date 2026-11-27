"""Package the offline viewer and the unchanged signed model."""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('output', type=Path)
    a=p.parse_args()
    r=a.root.resolve()
    files=[r/'assets/suzu_final.glb',r/'CREDITS.md',r/'start-viewer.cmd']
    files.extend(f for f in (r/'viewer').rglob('*') if f.is_file() and '__pycache__' not in f.parts and not f.name.startswith('.'))
    assert all(f.is_file() for f in files),files
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(a.output,'w',compression=ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted(files):
            entry=ZipInfo(f.relative_to(r).as_posix(),(2026,11,27,0,0,0))
            entry.compress_type=ZIP_DEFLATED
            z.writestr(entry,f.read_bytes(),compresslevel=6)
    with ZipFile(a.output) as z:
        assert z.testzip() is None
        assert z.read('assets/suzu_final.glb')==(r/'assets/suzu_final.glb').read_bytes()

if __name__=='__main__':
    main()

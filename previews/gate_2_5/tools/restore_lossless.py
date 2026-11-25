"""Verify and reconstruct the original four MP4s from repository blobs, offline."""
import argparse
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out-dir",type=Path,default=Path("gate2_lossless"))
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/"lossless_parts"/"MANIFEST.json").read_text(encoding="utf-8"))
args.out_dir.mkdir(parents=True,exist_ok=True)
for scene,entry in manifest.items():
    out=args.out_dir/entry["output"]
    tmp=out.with_suffix(".mp4.tmp")
    sha=hashlib.sha256()
    n=0
    try:
        with tmp.open("wb") as f:
            for part in entry["parts"]:
                b=(root/part["path"]).read_bytes()
                if len(b)!=part["bytes"] or hashlib.sha256(b).hexdigest()!=part["sha256"]:
                    raise ValueError(f"坏分片：{part['path']}")
                sha.update(b)
                n+=len(b)
                f.write(b)
        if n!=entry["bytes"] or sha.hexdigest()!=entry["sha256"]:
            raise ValueError(f"SHA256 对不上：{scene}")
        tmp.replace(out)
    finally:
        tmp.unlink(missing_ok=True)
    print(f"{scene}: {out} {n} bytes {sha.hexdigest()}")

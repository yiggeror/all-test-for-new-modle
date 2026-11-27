import json, subprocess, sys
from pathlib import Path
from PIL import Image
base=Path(sys.argv[1])
expected={"assets/suzu_gate1.blend":None,"assets/suzu_gate1.glb":None,
"previews/gate1/turnaround_8view_clay.png":(4,2),
"previews/gate1/turnaround_4view_wireframe.png":(2,2),
"previews/gate1/face_5view_clay.png":(5,1),
"previews/gate1/details_clay.png":(3,2),
"previews/gate1/turntable_clay.mp4":None}
missing=[p for p in expected if not (base/p).is_file()]
assert not missing, f"Missing Gate 1 files: {missing}"
with (base/"assets/suzu_gate1.blend").open("rb") as file:
 prefix=file.read(8)
 assert prefix.startswith((b"BLENDER",b"\x28\xb5\x2f\xfd")), "Invalid Blender header"
glb=(base/"assets/suzu_gate1.glb").read_bytes()
assert glb[:4]==b"glTF" and int.from_bytes(glb[8:12],"little")==len(glb)
for p, dims in expected.items():
 if dims:
  im=Image.open(base/p).convert("RGB")
  w,h=im.size
  assert w>=900 and h>=330 and max(im.getextrema()[0])-min(im.getextrema()[0])>35, p
mp4=base/"previews/gate1/turntable_clay.mp4"
streams=json.loads(subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_streams","-of","json",str(mp4)]))["streams"]
v=streams[0]
assert v["width"]==1920 and v["height"]==1080 and v["avg_frame_rate"]=="30/1" and 6<=float(v["duration"])<=8
subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(mp4),"-f","null","-"],check=True)
print("Container, size and duration checks passed. Visual review separately required.")

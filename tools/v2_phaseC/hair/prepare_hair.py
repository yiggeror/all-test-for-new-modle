import sys,bpy
from pathlib import Path
d=Path(__file__).resolve().parent;sys.path.insert(0,str(d))
from hair_secondary import apply_hair_rig
apply_hair_rig(bpy.context.scene)
args=sys.argv[sys.argv.index('--')+1:]
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(args[0]).resolve()),compress=True)

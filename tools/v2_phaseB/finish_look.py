"""Put authored Phase B shading onto the actual assembled hair."""
from pathlib import Path
import argparse,sys,bpy
a=argparse.ArgumentParser(description=__doc__)
a.add_argument('material_module',type=Path)
a.add_argument('texture_dir',type=Path)
a.add_argument('dest',type=Path)
a.add_argument('--crown',type=float,default=1.568)
a.add_argument('--lower',type=float,default=1.135)
x=a.parse_args(sys.argv[sys.argv.index('--')+1:])
sys.path.insert(0,str(x.material_module.resolve()))
from apply_hair import build_library,assign_hair
collection=bpy.data.collections['SUZU_PHASE_B_HAIR']
hair=[o for o in collection.all_objects if o.type=='MESH']
assert hair and not any(o.name.startswith('Suzu · ') for o in hair)
lib=build_library(x.texture_dir.resolve(),crown=x.crown,lower=x.lower)
selected=assign_hair(lib,'NPR',objects=hair)
assert len(selected)==len(hair),sorted(set(o.name for o in hair)-{n for n,r in selected})
bpy.ops.file.pack_all()
bpy.context.preferences.filepaths.save_version=0
x.dest.resolve().parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(x.dest.resolve()),compress=True)
print('Applied authored full hair look to',len(selected),'true meshes.')

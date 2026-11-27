"""Append Phase B hair and accessories to the read-only, validated Phase A base."""
from pathlib import Path
import argparse,sys,bpy
from mathutils import Vector

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('out',type=Path)
ap.add_argument('--hair',type=Path,required=True)
ap.add_argument('--props',type=Path)
ap.add_argument('--no-head-parent',action='store_true')
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
scene=bpy.context.scene
main=bpy.data.objects['Suzu · Humanoid']
face=bpy.data.objects['Suzu · Face']
body=bpy.data.objects['Suzu · Body']
assert len(main.data.bones)==154 and len(face.data.shape_keys.key_blocks)==58
before=set(scene.objects)
modules=[]
for src,nm,role in [(a.hair,'SUZU_PHASE_B_HAIR','hair'),(a.props,'SUZU_PHASE_B_PROPS','prop')]:
 if not src:continue
 f=src.resolve()
 with bpy.data.libraries.load(str(f),link=False) as (source,dest):
  if nm not in source.collections:raise ValueError((nm,source.collections))
  dest.collections=[nm]
 c=dest.collections[0]
 scene.collection.children.link(c)
 modules.append(c)
 bpy.context.view_layer.update()
 for o in c.all_objects:
  if o.type not in ('MESH','EMPTY'):raise ValueError((nm,o.name,o.type))
  if o.type=='MESH':
   assert 'icosphere' not in o.name.lower() and len(o.data.polygons)>3
   o['suzu_stage_role']=role
   if o.parent and o.parent.name in c.all_objects:continue
   if not a.no_head_parent:
    x=o.matrix_world.copy()
    o.parent=main;o.parent_type='BONE';o.parent_bone='J_Bip_C_Head'
    bpy.context.view_layer.update()
    o.matrix_world=x
 # Backdrops, references and imported copies of the approved character remain unlinked.
assert all(o.name in scene.objects for o in (main,face,body))
added=set(scene.objects)-before
assert all(o.type in ('MESH','EMPTY') for o in added)
assert all(not any(t in o.name for t in ('Suzu · Face','Suzu · Body','Suzu · Humanoid')) for o in added)
assert any(o.type=='MESH' and o.get('suzu_stage_role')=='hair' for o in added)
# Drop only local display helpers that may have been generated during a tool's import.
for o in list(scene.objects):
 if 'icosphere' in o.name.lower() and o.type=='MESH' and o not in added and o not in (face,body):
  for bone in main.pose.bones:
   if bone.custom_shape==o:bone.custom_shape=None
  bpy.data.objects.remove(o,do_unlink=True)
a.out.resolve().parent.mkdir(parents=True,exist_ok=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()),compress=True)
print('Phase B staged',[(c.name,len(c.all_objects)) for c in modules])

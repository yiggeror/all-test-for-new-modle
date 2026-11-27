"""Export Phase B character and actual hair/headwear only."""
from pathlib import Path
import json,sys,bpy

out=Path(sys.argv[sys.argv.index('--')+1]).resolve()
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
rig=scene.objects['Suzu · Humanoid']; face=scene.objects['Suzu · Face']; body=scene.objects['Suzu · Body']
hair=[o for o in scene.objects if o.type=='MESH' and o.get('suzu_stage_role') in ('hair','prop')]
assert hair and any(o.get('suzu_stage_role')=='prop' for o in hair)
assert len(rig.data.bones)==154 and len(face.data.shape_keys.key_blocks)==58
assert not any('icosphere' in o.name.lower() for o in hair)
for key in face.data.shape_keys.key_blocks[1:]:key.value=0
bpy.context.view_layer.update()
bpy.ops.file.pack_all()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'suzu_v2_phaseB.blend'),compress=True)
# Preserve the authored look in .blend, then swap only to explicitly authored portable materials for GLB.
phase_a_export={m.get('suzu_phase_a_role'):m for m in bpy.data.materials if m.get('suzu_style')=='Export'}
for o in (face,body):
 for s in o.material_slots:
  if s.material and s.material.get('suzu_phase_a_role') in phase_a_export:
   s.material=phase_a_export[s.material['suzu_phase_a_role']]
b_export={m.get('suzu_hair_role'):m for m in bpy.data.materials if m.get('suzu_hair_style')=='Export'}
for o in hair:
 for s in o.material_slots:
  if s.material and s.material.get('suzu_glb_material'):
   n=s.material['suzu_glb_material']
   assert n in bpy.data.materials,n
   s.material=bpy.data.materials[n]
  elif o.get('suzu_stage_role')=='hair' and o.get('suzu_hair_role') in b_export:
   s.material=b_export[o['suzu_hair_role']]
bpy.ops.object.select_all(action='DESELECT')
for o in (rig,face,body,*hair):o.select_set(True)
glb=out/'suzu_v2_phaseB.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_extras=True,
   export_skins=True,export_all_influences=True,export_morph=True,export_animations=False,export_cameras=False,export_lights=False)
d=glb.read_bytes();j=json.loads(d[20:20+int.from_bytes(d[12:16],'little')])
nodes=[n for n in j['nodes'] if 'mesh' in n]
assert len(nodes)==len(hair)+2, ([n['name'] for n in nodes],len(hair))
assert not any('icosphere' in n.get('name','').lower() or 'camera' in n.get('name','').lower() for n in nodes)
assert len(j['skins'])==1 and len(j['skins'][0]['joints'])==154
targets=[m['extras']['targetNames'] for m in j['meshes'] if m.get('extras',{}).get('targetNames')]
assert targets==[[k.name for k in list(face.data.shape_keys.key_blocks)[1:]]]
print('Phase B GLB:',len(nodes),'true mesh objects, one skin, 154 joints, 57 native expression targets.')

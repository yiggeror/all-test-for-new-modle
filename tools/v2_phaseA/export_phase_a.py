"""Freeze the integrated Phase A scene and export the static inspection GLB."""
import bpy, sys, json, os
from pathlib import Path

out=Path(sys.argv[sys.argv.index('--')+1])
out.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
keyed=[o for o in scene.objects if o.type=='MESH' and o.data.shape_keys
       and len(o.data.shape_keys.key_blocks)>=58]
assert len(keyed)==1, [(o.name,len(o.data.shape_keys.key_blocks)) for o in keyed]
face=keyed[0]
rigs=[o for o in scene.objects if o.type=='ARMATURE']
assert len(rigs)==1, [o.name for o in rigs]
rig=rigs[0]
body=[o for o in scene.objects if o.type=='MESH' and o!=face and
      any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
assert body, "The body must keep the native skin"
for key in face.data.shape_keys.key_blocks[1:]:
    key.value=0.0
for o in [rig,face,*body]:
    o['upstream_model']='VRM1_Constraint_Twist_Sample © 2022 pixiv Inc.'
    o['upstream_license']='https://vrm.dev/en/licenses/1.0/'
    o['authors_note']='Suzu Phase A adaptation: proportions, face sculpt, test makeup and expression presets'
preset_file=os.getenv('SUZU_EXPRESSIONS')
if preset_file:
    face['phase_a_expressions']=Path(preset_file).read_text()
constraint_file=os.getenv('SUZU_VRM_CONSTRAINTS')
if constraint_file:
    rig['native_vrm1_constraints']=Path(constraint_file).read_text()
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'suzu_v2_phaseA.blend'),compress=True)
export_roles={m.get('suzu_phase_a_role'):m for m in bpy.data.materials if m.get('suzu_style')=='Export'}
for o in [face,*body]:
    for slot in o.material_slots:
        if slot.material and slot.material.get('suzu_phase_a_role') in export_roles:
            slot.material=export_roles[slot.material['suzu_phase_a_role']]
bpy.ops.object.select_all(action='DESELECT')
for o in [rig,face,*body]: o.select_set(True)
result=bpy.ops.export_scene.gltf(
    filepath=str(out/'suzu_v2_phaseA.glb'),export_format='GLB',
    use_selection=True,export_extras=True,export_cameras=False,export_lights=False,
    export_morph=True,export_animations=False,export_skins=True,export_all_influences=True)
assert 'FINISHED' in result
geo=out/'suzu_v2_phaseA.glb'
with geo.open('rb') as f:
    file_header=f.read(12); assert file_header[:4]==b'glTF'
    size=int.from_bytes(f.read(4),'little'); assert f.read(4)==b'JSON'
    j=json.loads(f.read(size))
silhouettes=[m for m in j['meshes'] if any(p.get('targets') for p in m['primitives'])]
assert len(silhouettes)==1 and len(silhouettes[0]['extras']['targetNames'])>=57
assert len(j.get('skins',[]))>=1, 'Missing human skin weights in exported GLB'
print('GLB:',len(silhouettes[0]['extras']['targetNames']),'native targets;',len(j['skins'][0]['joints']),'skin joints;',len(j.get('images',[])),'embedded images')

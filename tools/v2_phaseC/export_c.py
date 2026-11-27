"""Export a genuine, animatable glTF and verify its actual animation channels."""
import argparse,bpy,sys,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('out',type=Path);p.add_argument('--probe',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene
rig=s.objects['Suzu · Humanoid'];face=s.objects['Suzu · Face'];body=s.objects['Suzu · Body']
assert face.parent==rig and len(face.data.shape_keys.key_blocks)==58 and len(rig.data.bones)>=154
shape=face.data.shape_keys
assert rig.animation_data and rig.animation_data.action and shape.animation_data and shape.animation_data.action
ward=[o for o in s.objects if o.type=='MESH' and o.get('suzu_stage_role')=='wardrobe']
ad=[o for o in s.objects if o.type=='MESH' and o.get('suzu_stage_role') in ('hair','prop')]
if not a.probe:
    assert ward and all(any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers) for o in ward)
    assert len(rig.data.bones)>=183
assert len(ad)==54
assert not any('icosphere' in o.name.lower() for o in [face,body,*ad,*ward])
s.frame_set(1)
bpy.ops.file.pack_all()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'suzu_v2_phaseC.blend'),compress=True)
a_export={m.get('suzu_phase_a_role'):m for m in bpy.data.materials if m.get('suzu_style')=='Export'}
for o in [body,face]:
    for n in o.material_slots:
        if n.material and n.material.get('suzu_phase_a_role') in a_export:
            n.material=a_export[n.material['suzu_phase_a_role']]
for o in [*ad,*ward]:
    for n in o.material_slots:
        key=n.material.get('suzu_glb_material') if n.material else None
        if key and key in bpy.data.materials:n.material=bpy.data.materials[key]
bpy.ops.object.select_all(action='DESELECT')
for o in [rig,face,body,*ad,*ward]:o.select_set(True)
g=out/'suzu_v2_phaseC.glb'
args=dict(filepath=str(g),export_format='GLB',use_selection=True,export_extras=True,
    export_skins=True,export_all_influences=True,export_morph=True,export_morph_animation=True,
    export_animations=True,export_animation_mode='SCENE',export_frame_range=True,export_force_sampling=True,
    export_frame_step=1,export_cameras=False,export_lights=False,export_anim_slide_to_zero=True)
props={q.identifier for q in bpy.ops.export_scene.gltf.get_rna_type().properties}
bpy.ops.export_scene.gltf(**{k:v for k,v in args.items() if k in props})
b=g.read_bytes()
assert b[:4]==b'glTF' and int.from_bytes(b[8:12],'little')==len(b)
raw_size=int.from_bytes(b[12:16],'little')
j=json.loads(b[20:20+raw_size])
# Blender may emit shape-key and armature scene tracks separately. Publish one
# synchronized, standards-compliant glTF animation instead of making a viewer
# guess which two to play together.
tracks=j.get('animations',[])
if len(tracks)>1:
    samplers=[];channels=[];which=set()
    for track in tracks:
        off=len(samplers);samplers.extend(track['samplers'])
        for c in track['channels']:
            k=(c['target'].get('node'),c['target'].get('path'))
            assert k not in which,('Repeated animation target',k)
            which.add(k);channels.append({**c,'sampler':c['sampler']+off})
    j['animations']=[{'name':'Suzu · Continuous performance','samplers':samplers,'channels':channels}]
    packed=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    packed+=b' '*((-len(packed))%4)
    binary=b[20+raw_size:]
    g.write_bytes(b[:8]+(20+len(packed)+len(binary)).to_bytes(4,'little')+len(packed).to_bytes(4,'little')+b'JSON'+packed+binary)
assert len(j['skins'])==1 and len(j['skins'][0]['joints'])==len(rig.data.bones)
assert not any('icosphere' in n.get('name','').lower() for n in j['nodes'])
anim=[c for aa in j.get('animations',[]) for c in aa.get('channels',[])]
paths={c['target'].get('path') for c in anim}
assert len(j['animations'])==1
assert 'rotation' in paths and 'weights' in paths, ('GLB is missing actual motion data',paths)
assert any(j['nodes'][c['target']['node']].get('name','')==face.name for c in anim if c['target'].get('path')=='weights')
lengths=[max(j['accessors'][sp['input']].get('max',[0])[0] for sp in ac['samplers']) for ac in j['animations']]
assert max(lengths)>=11.30 and max(lengths)<12.01,lengths
print('C asset:',len(j['meshes']),'real meshes,',len(j['skins'][0]['joints']),'joints,',
      len(anim),'actual sampled channels (incl. morph weights), lengths seconds',lengths)

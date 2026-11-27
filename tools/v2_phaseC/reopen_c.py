"""Independent mesh/animation witnesses from the delivered GLB."""
from pathlib import Path
import argparse,sys,json
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('asset',type=Path);ap.add_argument('report',type=Path);ap.add_argument('--probe',action='store_true')
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
p=a.asset.resolve();blob=p.read_bytes();header=int.from_bytes(blob[12:16],'little')
assert blob[:4]==b'glTF';raw=json.loads(blob[20:20+header])
assert 'icosphere' not in ' '.join(x.get('name','') for x in raw['nodes']).lower()
assert len(raw.get('animations',[]))==1
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(p),disable_bone_shape=True)
rig=sc.objects['Suzu · Humanoid']
face=next(o for o in sc.objects if o.type=='MESH' and o.data.shape_keys and len(o.data.shape_keys.key_blocks)==58)
body=next(o for o in sc.objects if o.type=='MESH' and o.name.startswith('Suzu · Body'))
assert len(rig.data.bones)>=170 and len(face.data.shape_keys.key_blocks)==58
assert face.parent==rig
if not a.probe:assert len(rig.data.bones)>=183
assert not any('icosphere' in o.name.lower() for o in sc.objects)
roles={raw['meshes'][n['mesh']].get('name'):n.get('extras',{}).get('suzu_stage_role')
       for n in raw['nodes'] if 'mesh' in n and 'suzu_stage_role' in n.get('extras',{})}
def role(o):
    return o.get('suzu_stage_role') or roles.get(o.data.name)
hair=[o for o in sc.objects if o.type=='MESH' and role(o) in ('hair','prop')]
ward=[o for o in sc.objects if o.type=='MESH' and role(o)=='wardrobe']
assert len(hair)==54
if not a.probe:assert len(ward)>80
for group in [ward]:
    assert all(any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers) for o in group)
def geom(o,dg):
    e=o.evaluated_get(dg);m=e.to_mesh()
    m.calc_loop_triangles()
    xx=[e.matrix_world@v.co for v in m.vertices];ts=[tuple(t.vertices) for t in m.loop_triangles]
    e.to_mesh_clear();return xx,ts
def witness(objects,dg):
    vs=[];ts=[]
    for o in objects:
        vv,tt=geom(o,dg);o0=len(vs);vs.extend(vv);ts.extend(tuple(v+o0 for v in t) for t in tt)
    if not ts:return None
    return BVHTree.FromPolygons(vs,ts,all_triangles=True)
rows=[]
for k in (1,55,74,111,152,190,212,213,226,247,265,280,305,306,324,341):
    sc.frame_set(k)
    dg=bpy.context.evaluated_depsgraph_get()
    pose=rig.evaluated_get(dg)
    wrist=pose.matrix_world@pose.pose.bones['J_Bip_R_Hand'].head
    keys=face.data.shape_keys.key_blocks[1:]
    row={'frame':k,'wrist_m':list(wrist),'face':{x.name:round(x.value,5) for x in keys if abs(x.value)>.005}}
    if not a.probe and k in (1,74,212,213,247,265,280,305,306):
        cl=witness(ward,dg);sk=witness((body,face),dg)
        pair=[]
        for h in hair:
            g=witness((h,),dg)
            if not g:continue
            w=len(g.overlap(cl)) if cl else 0;b=len(g.overlap(sk))
            if w or b:pair.append([h.name,w,b])
        row['hair_vs_clothing_and_skin']=pair
    rows.append(row)
assert max(r['wrist_m'][2] for r in rows)>1.37 and min(r['wrist_m'][2] for r in rows)<1.
assert any(r['face'] for r in rows)
assert any(any('MTH_O' in key for key in r['face']) for r in rows)
a.report.write_text(json.dumps({'bones':len(rig.data.bones),'native_targets':57,'garments':len(ward),'checks':rows},indent=2)+'\n')
print('Independent reopened GLB',p.name,'frames 1..341 successfully sampled (wrist and native morphs animate)')

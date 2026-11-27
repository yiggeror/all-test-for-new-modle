"""Import a VRM's glTF payload and map the original head without editing it."""
from pathlib import Path
import sys, json, struct, bpy
import numpy as np

a=sys.argv[sys.argv.index('--')+1:]; src=Path(a[0]).resolve(); out=Path(a[1]).resolve(); out.mkdir(parents=True,exist_ok=True)
raw=src.read_bytes(); l=struct.unpack_from('<I',raw,12)[0]; spec=json.loads(raw[20:20+l]); vrm=spec['extensions'].get('VRM',{})
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src),merge_vertices=False,import_pack_images=True)
rows=[]
for ob in bpy.context.scene.objects:
    d={'name':ob.name,'type':ob.type,'world':list(map(list,ob.matrix_world)), 'loc':list(ob.location), 'scale':list(ob.scale), 'parent':ob.parent.name if ob.parent else None}
    if ob.type=='ARMATURE':
        d['bones']=[(b.name,list(b.head_local),list(b.tail_local),list(ob.matrix_world@b.head_local),list(ob.matrix_world@b.tail_local)) for b in ob.data.bones]
    if ob.type=='MESH':
        me=ob.data; xyz=np.array([tuple(v.co) for v in me.vertices]); world=np.array([tuple(ob.matrix_world@v.co) for v in me.vertices]); block=me.shape_keys.key_blocks if me.shape_keys else []
        d.update(verts=len(me.vertices), faces=len(me.polygons),keys=[k.name for k in block], uv=[u.name for u in me.uv_layers], bounds_world=[world.min(0).tolist(),world.max(0).tolist()],bounds_local=[xyz.min(0).tolist(),xyz.max(0).tolist()],materials=[])
        for i,m in enumerate(me.materials):
            fs=[p for p in me.polygons if p.material_index==i]; ii=np.unique([k for p in fs for k in p.vertices]);vs=world[ii];im=[]
            if m and m.use_nodes:
                im=[(n.image.name,tuple(n.image.size)) for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
            d['materials'].append((i,m.name if m else None,len(fs),len(vs),vs.min(0).tolist(),vs.max(0).tolist(),vs.mean(0).tolist(),im))
        if block:
            stage={f'k{i}':np.array([tuple(v.co) for v in q.data],dtype=np.float32) for i,q in enumerate(block)}
            stage['xyz']=xyz;stage['xyz_world']=world;stage['faces']=np.array([tuple(f.vertices) for f in me.polygons]);stage['slot']=np.array([f.material_index for f in me.polygons]);stage['uv']=np.array([tuple(l.uv) for l in me.uv_layers.active.data]);np.savez_compressed(out/'head_raw.npz',**stage)
    rows.append(d)
(out/'inspection.json').write_text(json.dumps({'objects':rows,'groups':vrm.get('blendShapeMaster',{}).get('blendShapeGroups',[]),'meta':vrm.get('meta',{})},indent=2,ensure_ascii=False))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/'base.blend'),compress=True)

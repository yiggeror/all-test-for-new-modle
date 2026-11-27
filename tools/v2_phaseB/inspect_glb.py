"""Verify raw GLB contents, then independently reopen without display-only bone shapes."""
from pathlib import Path
import json, sys
import bpy
p=Path(sys.argv[sys.argv.index('--')+1]).resolve()
raw=p.read_bytes(); count=int.from_bytes(raw[12:16],'little')
assert raw[:4]==b'glTF'
g=json.loads(raw[20:20+count])
assert not any('icosphere' in m.get('name','').lower() for m in g['meshes'])
assert not any('icosphere' in n.get('name','').lower() for n in g['nodes'])
print('GLB payload:',[m.get('name','') for m in g['meshes']],flush=True)
for disable in (False,True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    kw={'filepath':str(p)}
    props={x.identifier for x in bpy.ops.import_scene.gltf.get_rna_type().properties}
    if disable:
        if 'disable_bone_shape' in props:kw['disable_bone_shape']=True
        else:kw['bone_heuristic']='TEMPERANCE'
    bpy.ops.import_scene.gltf(**kw)
    dep=bpy.context.evaluated_depsgraph_get()
    meshes=[];z=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        meshes.append((o.name,len(o.data.vertices),len(o.data.polygons)))
        if not disable:continue
        ev=o.evaluated_get(dep);mesh=ev.to_mesh()
        z.extend((ev.matrix_world@v.co).z for v in mesh.vertices);ev.to_mesh_clear()
    if disable:
        assert not any('icosphere' in a[0].lower() for a in meshes)
        assert z and abs(min(z))<.001 and 1.594<max(z)<1.75,(min(z),max(z))
        print('Disabled import display shapes:',meshes, 'floor/crown m:',(min(z),max(z)))
    else: print('Default Blender import:',meshes)

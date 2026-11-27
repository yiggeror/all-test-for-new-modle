"""Open the exact exported file in a fresh Blender session."""
from pathlib import Path
import bpy,sys
from mathutils import Vector
p=Path(sys.argv[sys.argv.index('--')+1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p))
objects=list(bpy.context.scene.objects)
meshes=[o for o in objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
rig=next(o for o in objects if o.type=='ARMATURE')
assert len(meshes)==2, [o.name for o in meshes]
face=next(o for o in meshes if o.data.shape_keys is not None)
assert len(face.data.shape_keys.key_blocks)==58, len(face.data.shape_keys.key_blocks)
assert len(rig.data.bones)>=54
for o in meshes:
    assert any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)
deps=bpy.context.evaluated_depsgraph_get()
vertical=[]
for o in meshes:
    ev=o.evaluated_get(deps)
    m=ev.to_mesh()
    vertical.extend((ev.matrix_world@v.co).z for v in m.vertices)
    ev.to_mesh_clear()
assert abs(min(vertical))<1.5e-4 and abs(max(vertical)-1.60)<.002, (min(vertical),max(vertical))
print('Reopened the exported GLB: two skinned meshes, 58 key blocks and corrected stature.',(min(vertical),max(vertical)))

"""Combine the independent fitted clothing patterns with the locked Suzu head/body."""
from pathlib import Path
import sys,argparse,bpy
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('out',type=Path)
ap.add_argument('--top',type=Path)
ap.add_argument('--lower',type=Path)
ap.add_argument('--jewelry',type=Path)
ap.add_argument('--jewelry-col')
ap.add_argument('--body-patch',type=Path)
ap.add_argument('--strict-weights',action='store_true')
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
sc=bpy.context.scene
rig=sc.objects['Suzu · Humanoid'];face=sc.objects['Suzu · Face'];body=sc.objects['Suzu · Body']
assert len(rig.data.bones)>=154 and len(face.data.shape_keys.key_blocks)==58
for f,n,role in [(a.top,'SUZU_PHASE_C_TOP','top'),(a.lower,'SUZU_PHASE_C_LOWER','lower'),(a.jewelry,a.jewelry_col,'top-jewelry')]:
    if not f:continue
    with bpy.data.libraries.load(str(f.resolve()),link=False) as (src,dst):
        if n not in src.collections:raise ValueError((n,src.collections))
        dst.collections=[n]
    c=dst.collections[0];sc.collection.children.link(c)
    bpy.context.view_layer.update()
    for o in tuple(c.all_objects):
        if o is None or o.type!='MESH':continue
        o['suzu_stage_role']='wardrobe';o['suzu_wardrobe_part']=role
        arm=[m for m in o.modifiers if m.type=='ARMATURE']
        attached=any(g.name in rig.data.bones or g.name.startswith('SuzuC.') for g in o.vertex_groups)
        if attached and not arm:
            arm=[o.modifiers.new('Suzu shared humanoid', 'ARMATURE')]
        for x in arm:x.object=rig; x.use_deform_preserve_volume=True
        if a.strict_weights:
            assert arm and attached,('Unbound garment',o.name)
        if arm and (o.parent is None or o.parent.type=='ARMATURE'):
            pose=o.matrix_world.copy();o.parent=rig;o.parent_type='OBJECT';bpy.context.view_layer.update();o.matrix_world=pose
        o.hide_render=False
    print('Clothes',role,len([o for o in c.all_objects if o is not None and o.type=='MESH']))
if a.body_patch:
    import json
    f=json.loads(a.body_patch.read_text())
    assert f['object']==body.name
    for i,p in f['deltas']:
        v=body.data.vertices[int(i)]
        assert v.co.z>1.105 and v.co.z<1.302
        assert sum(x*x for x in p)**.5<.0035
        for j,x in enumerate(p):v.co[j]+=x
    body.data.update()
assert face.parent==rig
for o in list(sc.objects):
    if o.type=='MESH' and 'icosphere' in o.name.lower():
        for b in rig.pose.bones:
            if b.custom_shape==o:b.custom_shape=None
        bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
a.out.resolve().parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()),compress=True)

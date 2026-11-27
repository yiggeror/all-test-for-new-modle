"""Translate the approved donor's VRM1 node constraints into editable Blender rig controls.

In generated assets these are Blender Damped Track (AIM) and swing–twist-axis
drivers (ROLL). The original VRMC_node_constraint map is independently kept
on the armature. Standard glTF does not execute these Blender controls.
"""
from mathutils import Vector,Quaternion,Matrix
from math import pi
import bpy
UNIT={'X':Vector((1,0,0)),'Y':Vector((0,1,0)),'Z':Vector((0,0,1))}
def node_axes(glb):
    raw=glb.get('nodes') or []
    parents={k:i for i,n in enumerate(raw) for k in n.get('children',())}
    result={}
    def axes_at(i):
        if i in result:return result[i]
        node=raw[i]
        if 'matrix' in node:
            source=node['matrix']
            r=Matrix([source[j::4] for j in range(4)]).to_quaternion()
        else:
            x,y,z,w=node.get('rotation',(0,0,0,1));r=Quaternion((w,x,y,z))
        if i in parents:r=axes_at(parents[i])@r
        result[i]=r.normalized()
        return result[i]
    C=Quaternion(Vector((1,0,0)),pi/2)
    return {n['name']:C@axes_at(i) for i,n in enumerate(raw) if n.get('name')}
def install(rig,vrm_rules,bind_frame,source_axes):
    axes={}
    installed={}
    still_frames={q.name:q.matrix_local.to_quaternion() for q in rig.data.bones}
    for nm,terms in vrm_rules.items():
        typ=terms['type'];src=terms['source'];sub=rig.data.bones.get(nm);root=rig.data.bones.get(src)
        if sub is None or root is None:continue
        if typ=='aim':
            v=root.head_local-sub.head_local
            if v.length>1.e-5:axes[nm]=v.normalized()
        elif typ=='roll':
            axis=terms.get('rollAxis','X')
            for b in (sub,root):
                if not b.name in bind_frame or not b.name in source_axes:continue
                native_axis=source_axes[b.name] @ UNIT[axis]
                local_original=bind_frame[b.name].inverted() @ native_axis
                current_world=still_frames[b.name] @ local_original
                if b.name in axes and abs(axes[b.name].dot(current_world))<.90:
                    raise RuntimeError('Conflicting native twist axes for '+b.name)
                axes[b.name]=current_world.normalized()
    bpy.ops.object.mode_set(mode='EDIT')
    for name,axis in axes.items():
        b=rig.data.edit_bones[name]
        ref=b.matrix.to_3x3()@Vector((0,0,1))
        length=b.length
        b.tail=b.head+(axis*length)
        if abs(axis.dot(ref))<.94:b.align_roll(ref)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()
    for nam,terms in vrm_rules.items():
        typ=terms['type'];src=terms['source'];w=float(terms.get('weight',1.))
        if nam not in axes or src not in rig.pose.bones:continue
        pb=rig.pose.bones[nam]
        if typ=='aim':
            c=pb.constraints.new('DAMPED_TRACK');c.name='VRM1 AIM • '+src
            c.target=rig;c.subtarget=src;c.track_axis='TRACK_Y';c.influence=w
            installed[nam]={'type':'aim','source':src,'influence':w}
        elif typ=='roll' and src in axes:
            # Both local Y axes were aligned to their own VRM axis before
            # adding the driver. Swing is removed mathematically, not copied
            # as an Euler diagonal artifact through large arm rotations.
            pb.rotation_mode='XYZ'
            fc=pb.driver_add('rotation_euler',1)
            d=fc.driver;d.type='SCRIPTED'
            a=d.variables.new();a.name='twist';a.type='TRANSFORMS'
            target=a.targets[0];target.id=rig;target.bone_target=src;target.transform_space='LOCAL_SPACE'
            target.transform_type='ROT_Y';target.rotation_mode='SWING_TWIST_Y'
            d.expression=f'{w:.10g}*twist'
            installed[nam]={'type':'roll','source':src,'influence':w}
    bpy.context.view_layer.update()
    return installed

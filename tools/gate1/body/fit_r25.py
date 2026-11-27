"""Apply the R2.5 body fit after building or reopening the locked R2 body.

blender -b suzu_body.blend -P fit_r25.py -- body_r25.blend
The locked original is not modified. No topology, subdivision, group names,
or hand proportions are changed by this fitting step.
"""
from pathlib import Path
import bpy
import sys
from math import atan2,degrees
from mathutils import Vector
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
from pose_r25 import *
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
dest=Path(args[0]).resolve() if args else H/'body_r25.blend'
source=Path(bpy.data.filepath).resolve()
if source==dest:raise ValueError('Use a separate fit output.')
coll=bpy.data.collections['SUZU_BODY']
BODY_NAMES={'Hand','Index','Middle','Ring','Little','Thumb'}
for ob in coll.all_objects:
    if ob.type!='MESH':continue
    names={g.index:g.name for g in ob.vertex_groups}
    is_body=ob.name.startswith('Suzu | body,')
    is_nail=ob.name.startswith('Suzu | nail')
    if not (is_body or is_nail):continue
    counts={'arm':0,'rigid hand':0,'neck':0,'foot':0}
    transform=ob.matrix_world;inv=transform.inverted()
    for v in ob.data.vertices:
        p=transform@v.co
        group=names[max(v.groups,key=lambda g:g.weight).group] if v.groups else ''
        label,_,side_name=group.partition('.')
        side=-1 if side_name.startswith('R') else 1
        if is_nail or label in BODY_NAMES:
            q=open_arm(p,side,full=True);counts['rigid hand']+=1
        elif label in ('Upper arm','Forearm'):
            q=open_arm(p,side);counts['arm']+=1
        elif p.z<FOOT_FADE_Z:
            q=shorten_foot(p);counts['foot']+=1
        elif p.z>NECK_ROOT_Z:
            q=shorten_neck(p);counts['neck']+=1
        else:continue
        v.co=inv@Vector(q)
    ob.data.update()
    ob['r25_fit']='Original R2 hand is a rigid transform; arm, ankle and neck fit smoothly.'
    print(ob.name,counts)
w=open_arm(WRIST,1,full=True)
print('SHOULDER',SHOULDER,'WRIST',tuple(round(d,8) for d in w),
      'OPENING',degrees(atan2(w[0]-SHOULDER[0],SHOULDER[2]-w[2])))
print('SHOE',LAST_FACTOR,'NECK',NECK_FACTOR,'RIGID HAND OPENING DELTA',DELTA_DEG)
coll['pose_front_degrees']=OPEN_DEG;coll['foot_length_scale']=LAST_FACTOR;coll['neck_length_scale']=NECK_FACTOR
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)

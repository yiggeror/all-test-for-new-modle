"""Retarget a VRoid-derived human baseline for Suzu Phase A.

The commercial-style native *skin mesh*, vertex-group assignments, facial
target count, UV atlas and articulated human hierarchy are retained. This is
a coordinate fit, not a procedural replacement body. Input/approval/source
licensing are caller-managed; the script does not fetch or publish content.
"""
from pathlib import Path
from math import exp,radians,pi,atan2,degrees,isfinite
import argparse,bpy,bmesh,hashlib,json,sys
from mathutils import Matrix,Quaternion,Vector
H=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser=argparse.ArgumentParser()
parser.add_argument('--input',type=Path,required=True)
parser.add_argument('--vrm-metadata',type=Path,help='Original VRM metadata when --input is an authorised edited scene')
parser.add_argument('--face',type=Path,help='Optional Blender file containing an edited Face in original source-local coordinates')
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--audit',type=Path)
parser.add_argument('--a-angle',type=float,default=37)
parser.add_argument('--t-stage',action='store_true',help='Stop after matching body stations, before confirming the A-pose.')
parser.add_argument('--donor',type=Path,help='T-calibrated legitimate donor torso (cut/bridge of source geometry).')
parser.add_argument('--min-keys',type=int,default=58)
P=parser.parse_args(args)
required=P.input.resolve()
def json_glb(p):
    d=p.read_bytes()
    if d[:4]!=b'glTF':return {}
    return json.loads(d[20:20+int.from_bytes(d[12:16],'little')])
g=(json_glb(P.vrm_metadata.resolve()) if P.vrm_metadata else json_glb(required) if required.suffix.lower() in ('.vrm','.glb') else {})
def vrm_human_names(g):
    E=g.get('extensions',{});nodes=g.get('nodes',[])
    ans={}
    for item in E.get('VRM',{}).get('humanoid',{}).get('humanBones',[]):
        ans[item['bone']]=nodes[item['node']]['name']
    for name,info in E.get('VRMC_vrm',{}).get('humanoid',{}).get('humanBones',{}).items():
        ans[name]=nodes[info['node']]['name']
    return ans
map_human=vrm_human_names(g)
nodes=g.get('nodes',[])
vrm_constraints={}
for node in nodes:
    im=node.get('extensions',{}).get('VRMC_node_constraint',{}).get('constraint',{})
    if not im:continue
    for typ,terms in im.items():
        v=dict(terms);v['source']=nodes[v['source']]['name'];v['type']=typ
        vrm_constraints[node['name']]=v
if required.suffix.lower()=='.blend':
    bpy.ops.wm.open_mainfile(filepath=str(required))
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(required),merge_vertices=False)
S=bpy.context.scene
rig=max((o for o in S.objects if o.type=='ARMATURE'),key=lambda o:len(o.data.bones))
original=[o for o in S.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
blocks=lambda o:o.data.shape_keys.key_blocks if o.data.shape_keys else []
face=max(original,key=lambda o:len(blocks(o)))
def is_body(o):
    return o is not face and any(m and ('body' in m.name.lower() and 'skin' in m.name.lower()) for m in o.data.materials)
body_candidates=[o for o in original if is_body(o)]
if not body_candidates:
    body_candidates=[o for o in original if o is not face and 'body' in o.name.lower()]
if len(body_candidates)!=1:
    raise RuntimeError('Pick a complete skin-bearing body target; found '+str([o.name for o in body_candidates]))
body=body_candidates[0]
if P.face:
    name_hint=face.name.split('.')[0]
    with bpy.data.libraries.load(str(P.face.resolve()),link=False) as (src,dst):
        named=[n for n in src.objects if n==name_hint or n.startswith(name_hint+' ') or n.startswith('Suzu · Face')]
        if not named:raise RuntimeError('Face object missing; retain its source object name.')
        dst.objects=named
    current=next(o for o in dst.objects if o and o.type=='MESH' and len(blocks(o))==len(blocks(face)))
    if len(current.data.vertices)!=len(face.data.vertices):
        raise RuntimeError('Face target topology differs from the imported subject.')
    if [tuple(p.vertices) for p in current.data.polygons]!=[tuple(p.vertices) for p in face.data.polygons]:
        raise RuntimeError('Face target polygon indexing differs from the imported subject.')
    if set(g.name for g in current.vertex_groups)!=set(g.name for g in face.vertex_groups):
        raise RuntimeError('Face lost a native bone group.')
    bpy.data.objects.remove(face,do_unlink=True)
    S.collection.objects.link(current);current.parent=rig;current.matrix_parent_inverse=Matrix.Identity(4);current.matrix_basis=Matrix.Identity(4)
    for m in current.modifiers:
        if m.type=='ARMATURE':m.object=rig
    face=current
# A VRM1 source can ship an example (test) bone pose next to the actual skin
# bind matrices. Work from the bind baseline, not that saved demonstration pose.
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
source_stems={o.name:o.type for o in S.objects}
for o in list(S.objects):
    if o not in (face,body,rig):bpy.data.objects.remove(o,do_unlink=True)
assert len(blocks(face))>=P.min_keys, f'Only {len(blocks(face))} key blocks.'
skin_slot=[m for m in body.data.materials if m and 'skin' in m.name.lower() and ('body' in m.name.lower() or len(body.data.materials)==1)]
if not skin_slot:raise RuntimeError('No native body-skin material.')
before_skin=len(body.data.polygons); removed_mats=[m.name for m in body.data.materials if m not in skin_slot]
bm=bmesh.new();bm.from_mesh(body.data)
ix=[i for i,m in enumerate(body.data.materials) if m in skin_slot]
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index not in ix],context='FACES')
loose=[v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm,geom=loose,context='VERTS')
for fp in bm.faces:fp.material_index=0
bm.to_mesh(body.data);bm.free()
body.data.materials.clear();body.data.materials.append(skin_slot[0]);body.data.update()
def keylist(o):return [k.name for k in blocks(o)]
def group_digest(o):
    serial=[[tuple([o.vertex_groups[g.group].name,round(g.weight,8)]) for g in v.groups] for v in o.data.vertices]
    return hashlib.sha256(json.dumps(serial,separators=(',',':')).encode('utf-8')).hexdigest()
group_before={o.name:group_digest(o) for o in (body,face)}
key_before=keylist(face)
rig0={b.name:tuple(b.head_local) for b in rig.data.bones}
original_bind_frames={b.name:b.matrix_local.to_quaternion().copy() for b in rig.data.bones}
def getbone(h,default):
    return rig.data.bones[map_human.get(h,default)]
hip=getbone('hips','J_Bip_C_Hips')
spine=getbone('spine','J_Bip_C_Spine')
chest=getbone('chest','J_Bip_C_Chest')
upper=getbone('upperChest','J_Bip_C_UpperChest')
neck=getbone('neck','J_Bip_C_Neck')
LUL=getbone('leftUpperLeg','J_Bip_L_UpperLeg')
LLL=getbone('leftLowerLeg','J_Bip_L_LowerLeg')
LFT=getbone('leftFoot','J_Bip_L_Foot')
LTO=getbone('leftToes','J_Bip_L_ToeBase')
LUA=getbone('leftUpperArm','J_Bip_L_UpperArm')
LFR=getbone('leftLowerArm','J_Bip_L_LowerArm')
LHD=getbone('leftHand','J_Bip_L_Hand')
front=1 if LTO.head_local.y>LFT.head_local.y else -1
source_left_sign=1 if LUA.head_local.x>0 else -1
if front!=-source_left_sign:
    raise RuntimeError('Unexpected chirality in source coordinates; use a separately verified interpretation.')
head_mid=.014*front
# Sample only the face skin's vertex indices to derive hard head proportions.
ss={i for i,m in enumerate(face.data.materials) if m and 'skin' in m.name.lower()}
facial={i for p in face.data.polygons if p.material_index in ss for i in p.vertices}
if not facial:raise RuntimeError('No skin in facial mesh.')
base=blocks(face)[0]
cn=min(base.data[i].co.z for i in facial)
cr=max(max(base.data[i].co.z for i in facial),max(v.co.z for v in body.data.vertices))
bot=min(v.co.z for v in body.data.vertices)
target_c=1.324
src_top=cr-cn
if not .17<src_top<.365:raise RuntimeError('Subject head ratio requires a custom landmark calibration.')
head_height=1.600-target_c
head_sz=head_height/src_top
# Anatomy landmarks in source rest metres. Every bone base and anatomy point
# below the face use monotone interpolation to avoid striped stretch bands.
def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def G(z,p,w):return exp(-.5*((z-p)/w)**2)
floor=bot
hipZ=hip.head_local.z
hipLegZ=LUL.head_local.z
shouldZ=LUA.head_local.z
ankleZ=LFT.head_local.z
kneeZ=LLL.head_local.z
anchors=[
    (floor,0.0),(ankleZ,.0820),(kneeZ,.4620),(hipLegZ,.8370),(hipZ,.8780),
    (spine.head_local.z,.9255),(chest.head_local.z,1.0475),(upper.head_local.z,1.1505),
    (shouldZ,1.2450),(neck.head_local.z,1.2795),(cn,target_c)]
anchors=sorted(anchors)
if any(a>=b or c>=d for (a,c),(b,d) in zip(anchors,anchors[1:])):
    raise RuntimeError('Unsupported rig station order; inspect body anchors.')
def zcurve(z):
    if z>=cn:return target_c+(z-cn)*head_sz
    if z<=floor:return z-floor
    for i in range(len(anchors)-1):
        a,u=anchors[i];b,v=anchors[i+1]
        if a<=z<=b:break
    dt=b-a;t=(z-a)/dt
    def rate(k):
        if k==0:return 1.
        if k==len(anchors)-1:return head_sz
        q0,p0=anchors[k-1];q1,p1=anchors[k];q2,p2=anchors[k+1]
        l=(p1-p0)/(q1-q0);r=(p2-p1)/(q2-q1)
        return 2*l*r/(l+r)
    return (2*t**3-3*t*t+1)*u+(t**3-2*t*t+t)*dt*rate(i)+(-2*t**3+3*t*t)*v+(t**3-t*t)*dt*rate(i+1)
A0=abs(LUA.head_local.x);WR=abs(LHD.head_local.x)
def fit(p,face_mode=False):
    x,y,z=p
    zz=zcurve(z);depth=front*y
    # One affine transform for the entire face and heads' targets. Blend this
    # into the native neck circumference across the actual seam rings.
    mix=1. if face_mode else smooth((z-(cn-.047))/.046)
    tx=x*(1.+.105*mix)
    fy=depth
    fy+=.074*mix*(depth-front*head_mid)
    # Restrained contour refinement of the native Japanese artist mesh.
    rz=zz
    aw=smooth((abs(x)-A0*.73)/(A0*.66))
    trunk=(1-aw)*(1-mix)
    # Preserve a natural waist-to-rib transition and a softly fuller pelvis,
    # without stretching elbow/hand vertices that happen to share a T-pose Z.
    tx*=1+trunk*(-.057*G(rz,.987,.065)+.020*G(rz,.850,.051)+.010*G(rz,1.115,.079))
    fy+=trunk*(.0034*G(rz,1.101,.063)*min(1,max(-1,depth/.073))
               -.0258*G(rz,1.151,.059)*smooth((depth-.044)/.065)
               +.0059*G(rz,1.137,.044)*G(abs(x),0,.031)*smooth((depth-.049)/.035)
               -.0173*G(rz,1.003,.074)*smooth((depth-.052)/.056)
               +.0167*G(rz,1.190,.059)*G(abs(x),.038,.085)*smooth((-.025-depth)/.055)
               -.0033*G(rz,.854,.036)*smooth((.030-depth)/.099))
    # Correct the old hard/retroflected sagittal knee with a continuous
    # forward tibiofemoral axis; leave both ankle and toe bases planted.
    below=1.-smooth((rz-.725)/.146)
    fy+=below*(.0139*G(rz,.467,.092)-.0024*G(rz,.286,.085))
    # Preserve the original wrist section; fingers keep their native UV/weights.
    sz=abs(x)
    if sz>WR:
        tx=(1 if x>=0 else -1)*(abs(tx)-.026*(sz-WR))
    return Vector((tx,fy*front,zz))
def fit_key(k):
    for dat in k.data:dat.co=fit(dat.co,True)
for dat in body.data.vertices:dat.co=fit(dat.co,False)
for k in blocks(face):fit_key(k)
# Explicitly update the basis in Mesh too: glTF exports both primitive positions
# and relative deltas from affected keys, and neither should rely on lazy UI sync.
for v,d0 in zip(face.data.vertices,blocks(face)[0].data):v.co=d0.co
body.data.update();face.data.update()
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for b in rig.data.edit_bones:
    b.use_connect=False
    b.head=fit(b.head)
    b.tail=fit(b.tail)
bpy.ops.object.mode_set(mode='OBJECT')
if P.t_stage:
    # Preserve local directions in Blender data. The donor preparation uses
    # identical body origin/height calibrations as the target, not skin copying.
    rig['stage_raw_front']=front
    rig['stage_origin']='(0,0,0)'
    rig['stage_source']=str(P.input.name)
    bpy.context.preferences.filepaths.save_version=0
    P.out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(P.out.resolve()),compress=True)
    raise SystemExit(0)
bridge_audit={}
if P.donor:
    import importlib.util
    spec=importlib.util.spec_from_file_location('torso_bridge',H/'torso_bridge.py');T=importlib.util.module_from_spec(spec);spec.loader.exec_module(T)
    bridge_audit=T.bridge(body,rig,P.donor.resolve(),front)
    group_before={o.name:group_digest(o) for o in (body,face)}
def joint(n,name,default):
    k=map_human.get(n+name,default)
    return rig.pose.bones.get(k)
def world_rest_delta(pb,axis,ang):
    restq=pb.bone.matrix_local.to_quaternion()
    pb.rotation_mode='QUATERNION'
    pb.rotation_quaternion=restq.inverted() @ Quaternion(Vector(axis),radians(ang)) @ restq
base_angle=P.a_angle
if not 35.<=base_angle<=40.:raise RuntimeError('A-Pose must be 35°–40° from the vertical.')
for part,lab in [('left','L'),('right','R')]:
    arm=joint(part,'UpperArm','J_Bip_'+lab+'_UpperArm')
    again=1 if arm.head.x>=0 else -1
    world_rest_delta(arm,(0,1,0),again*(90-base_angle))
    fore=joint(part,'LowerArm','J_Bip_'+lab+'_LowerArm')
    hand=joint(part,'Hand','J_Bip_'+lab+'_Hand')
    # Relax the joint forward by 4°, and soften the wrists instead of forcing
    # the palm to the exact line of the radius under light.
    world_rest_delta(fore,(0,0,1),again*front*4.4)
    world_rest_delta(hand,(0,0,1),again*front*-1.65)
    for f,curls in [('Index',(4,7,4)),('Middle',(5,8,5)),('Ring',(6.7,9.1,6)),('Little',(8.4,10.0,7)),('Thumb',(2,4,3))]:
        for k,a in enumerate(curls,1):
            q=rig.pose.bones.get(f'J_Bip_{lab}_{f}{k}')
            if q:world_rest_delta(q,(0,1,0),again*a)
bpy.context.view_layer.update()
# The VRM1 example also skins skin areas to native twist helper nodes.
# Standard glTF imports their weights but does not evaluate VRMC aim axes.
# Reproduce their swing in the new bind pose before sampling the dressed-off
# surface. Roll scene metadata is retained for the live control stage.
for name,info in vrm_constraints.items():
    if info['type']!='aim' or name not in rig.pose.bones or info['source'] not in rig.pose.bones: continue
    p=rig.pose.bones[name]; target=rig.pose.bones[info['source']]
    f=target.bone.head_local-p.bone.head_local
    if p.parent:
        parent_delta=p.parent.matrix.to_quaternion() @ p.parent.bone.matrix_local.to_quaternion().inverted()
        f=parent_delta @ f
    dest=target.head-p.head
    if min(f.length,dest.length)<1e-7:continue
    R=Quaternion().slerp(f.normalized().rotation_difference(dest.normalized()),info.get('weight',1))
    M=p.matrix.copy();pos=M.translation.copy();p.matrix=Matrix.Translation(pos) @ R.to_matrix().to_4x4() @ Matrix.Translation(-pos) @ M
    bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
for ob in (body,face):
    for m in ob.modifiers:
        if m.type=='ARMATURE':m.use_deform_preserve_volume=True
dg.update()
shoulder_levels={}
for side in ('L','R'):
    p=rig.pose.bones['J_Bip_'+side+'_UpperArm'].head
    w=rig.pose.bones['J_Bip_'+side+'_Hand'].head
    shoulder_levels[side]={'shoulder_local':list(p),'wrist_local':list(w),
       'front_opening_from_vertical':degrees(atan2(abs(w.x-p.x),p.z-w.z))}
# Bake only the rest pose change. The body mesh has no shape targets; its vertex
# connectivity and native weight assignments are untouched. Face/neck bones have
# no arm-chain influence: all raw facial morph deltas remain intact.
face_arm_mod=next(m for m in face.modifiers if m.type=='ARMATURE')
affected={b.name for b in rig.pose.bones if (b.matrix_basis-Matrix.Identity(4)).magnitude>1e-6} if hasattr(Matrix.Identity(4),'magnitude') else {
    b.name for b in rig.pose.bones if sum(abs(b.matrix_basis[i][j]-(i==j)) for i in range(4) for j in range(4))>1e-6}
changed=set()
for q in rig.data.bones:
    parent=q
    while parent:
        if parent.name in affected:
            changed.add(q.name);break
        parent=parent.parent
assert not any(face.vertex_groups[g.group].name in changed and g.weight>1e-6
               for v in face.data.vertices for g in v.groups), 'Source face weights reference an articulated arm.'
eo=body.evaluated_get(dg);me=eo.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
assert len(me.vertices)==len(body.data.vertices)
coords=[v.co.copy() for v in me.vertices];eo.to_mesh_clear()
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode='OBJECT')
for v,c in zip(body.data.vertices,coords):v.co=c
body.data.update()
live_controls={}
if vrm_constraints:
    import importlib.util
    spec=importlib.util.spec_from_file_location('native_twist',H/'native_twist.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
    live_controls=N.install(rig,vrm_constraints,original_bind_frames,N.node_axes(g))
    assert len(live_controls)==len(vrm_constraints), ('Native controls lost',set(vrm_constraints)-set(live_controls))
# Artist rig stays unit scale; rotate the entire parent exactly once.
rig.rotation_mode='XYZ'
rig.rotation_euler=(0.,0.,pi if front==1 else 0.)
bpy.context.view_layer.update()
assert keylist(face)==key_before
assert all(group_digest(o)==group_before[o.name] for o in (body,face))
body.name='Suzu · Body';face.name='Suzu · Face';rig.name='Suzu · Humanoid'
rig.show_in_front=True
rig['phase']='A'
rig['retarget_humanoid']=json.dumps(map_human,ensure_ascii=False)
rig['vrmc_node_constraint']=json.dumps(vrm_constraints,ensure_ascii=False)
rig['native_blender_controls']=json.dumps(live_controls,ensure_ascii=False)
rig['pose_open_deg']=base_angle
rig['source_rest_head_z_m']=cn
rig['source_rest_crown_z_m']=cr
rig['phaseA_height_m']=1.600
rig['phaseA_heads']=1.600/head_height
for name,v in shoulder_levels.items():
    for key in ['shoulder_local','wrist_local']:
        v[key.replace('_local','_world')]=list(rig.matrix_world@Vector(v[key]))
body['source_skin_weight_digest']=next(iter(group_before.values()))
face['part']='Native facial targets; preserve indices through look development'
face['source_key_count']=len(keylist(face))
COL=bpy.data.collections.new('SUZU_PHASE_A');S.collection.children.link(COL)
for o in (rig,body,face):
    for c in list(o.users_collection):c.objects.unlink(o)
    COL.objects.link(o)
S.unit_settings.system='METRIC';S.unit_settings.scale_length=1.
for o in (face,body):o.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.context.preferences.filepaths.save_version=0
P.out.parent.mkdir(parents=True,exist_ok=True)
audit={'source_sha256':hashlib.sha256((P.vrm_metadata.resolve() if P.vrm_metadata else required).read_bytes()).hexdigest(),'source_sha_kind':(P.vrm_metadata or required).suffix,
       'edited_input_sha256':hashlib.sha256(required.read_bytes()).hexdigest() if P.vrm_metadata else None,
       'source_faces':{'body_with_hair':before_skin,'body_native_skin':len(body.data.polygons),'head_mesh':len(face.data.polygons)},
       'dropped_materials':removed_mats,'bones':len(rig.data.bones),'mapped_humanoid_bones':len(map_human),'live_twist_controls':{n:d['type'] for n,d in live_controls.items()},
       'key_blocks':len(key_before),'key_names':key_before,'shoulder_wrist':shoulder_levels,
       'source_head_z':[cn,cr],'target_head_z':[target_c,1.600],'target_heads':1.600/head_height,
       'vertex_weight_digests_unchanged':group_before,'front_after_yaw':'-Y','hair_slots_remaining':0,'torso_meld':bridge_audit}
print(json.dumps(audit,ensure_ascii=False,indent=2))
if P.audit:P.audit.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P.out.resolve()),compress=True)

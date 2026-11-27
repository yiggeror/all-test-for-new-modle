"""Author Suzu's one continuous Phase C performance using the native body and face."""
from pathlib import Path
import argparse,bpy,sys,json,math
from mathutils import Vector,Quaternion
P='J_Bip_'
FPS=30; FRAMES=342

def smoother(v):
    f=max(0.,min(1.,v));return f*f*f*(f*(f*6.-15.)+10.)

def ramp(t,a,b):
    return smoother((t-a)/(b-a))

def sample(t,knots):
    if t<=knots[0][0]:return knots[0][1]
    for (a,u),(b,v) in zip(knots,knots[1:]):
        if t<=b:return u+(v-u)*ramp(t,a,b)
    return knots[-1][1]

def window(t,a,b,c,d):
    return ramp(t,a,b)*(1-ramp(t,c,d))

def blink(t,center,duration=.26):
    a=center-duration*.52;b=center;c=center+duration*.48
    return ramp(t,a,b)*(1-ramp(t,b,c))

def mix_dict(a,b,w):
    return {n:a.get(n,0.)*(1.-w)+b.get(n,0.)*w for n in a.keys()|b.keys()}

def expression_state(t,p):
    w=[(0.,'neutral'),(1.80,'soft_smile'),(2.93,'soft_smile'),(3.88,'bright_laugh'),(4.30,'bright_laugh'),
       (5.15,'smiling_eyes'),(5.60,'smiling_eyes'),(6.35,'little_o'),(6.60,'little_o'),
       (7.65,'soft_smile'),(11.4,'soft_smile')]
    for (t0,a),(t1,b) in zip(w,w[1:]):
        if t<=t1:return mix_dict(p.get(a,{}),p.get(b,{}),ramp(t,t0,t1))
    return p['soft_smile'].copy()

def rigid_axis(x,y,z):
    return Quaternion((0,0,1),math.radians(z)) @ Quaternion((0,1,0),math.radians(y)) @ Quaternion((1,0,0),math.radians(x))

def rotation_matrix(pb,q,point=None):
    m=q.to_matrix().to_4x4()
    m.translation=point if point is not None else pb.head
    pb.matrix=m

def two_link(s,target,a,b,pole):
    d=target-s; dist=d.length
    u=d.normalized() if dist>1.e-6 else Vector((-1,0,0))
    d=max(abs(a-b)+.0005,min(a+b-.0020,dist))
    v=(pole-u*pole.dot(u)).normalized()
    along=(a*a-b*b+d*d)/(2*d)
    h=math.sqrt(max(0.,a*a-along*along))
    return s+u*along+v*h,s+u*d

class Performance:
    def __init__(self,rig,face):
        self.rig=rig;self.face=face
        self.p=rig.pose.bones
        self.preset=json.loads(face['phase_a_expressions'])
        self.shapes=face.data.shape_keys.key_blocks
        self.controls=tuple(P+'C_'+k for k in ('Spine','Chest','UpperChest','Neck','Head'))+tuple(P+s+'_'+k for s in ('L','R') for k in ('Shoulder','UpperArm','LowerArm','Hand'))
        self.face_ids=sorted({k for f in self.preset.values() for k in f}|{next(k.name for k in self.shapes if k.name.endswith('Fcl_EYE_Close'))})
        self.blink_id=next(n for n in self.face_ids if n.endswith('Fcl_EYE_Close'))
        self.rest={n:self.p[n].bone.matrix_local.to_quaternion() for n in self.controls}
        pairs=[self.p[P+'R_'+n].bone.head_local for n in ('UpperArm','LowerArm','Hand')]
        self.len1=(pairs[1]-pairs[0]).length;self.len2=(pairs[2]-pairs[1]).length
        self.waves=[]
    def rot(self,n,x=0.,y=0.,z=0.):
        pb=self.p[n];q=self.rest[n]
        pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q.inverted() @ rigid_axis(x,y,z) @ q
    def face_time(self,t):
        w=expression_state(t,self.preset)
        b=max(blink(t,1.02),blink(t,2.28),blink(t,7.32),blink(t,10.78))
        for n in self.face_ids:
            if n==self.blink_id:self.shapes[n].value=b
            else:self.shapes[n].value=w.get(n,0.)*(1.-b if 'Fcl_EYE_' in n else 1.)
    def nearby_wrist(self,t,amt):
        up,lo,ha=[self.p[P+'R_'+n] for n in ('UpperArm','LowerArm','Hand')]
        center=up.head.copy()
        old=ha.head.copy()
        # The elbow stays outside the shoulder. The hand raises beside the
        # cheek, not through the hair in front, and opens toward the camera.
        w=window(t,7.23,7.95,9.03,9.72)
        arc=math.sin(2*math.pi*(t-7.95)/.89)*w
        wish=center+Vector((-.203-.032*arc,-.149-.008*arc,.223+.022*arc))
        target=old.lerp(wish,amt)
        forward=1.25*window(t,9.82,10.10,10.29,10.54)+.68*window(t,6.80,7.04,7.16,7.35)
        target.y-=.046*forward
        elbow,wr=two_link(center,target,self.len1,self.len2,Vector((-1.,-.09-.46*forward,-.43)))
        current=(lo.head-center).normalized();desired=(elbow-center).normalized()
        rotation_matrix(up,current.rotation_difference(desired)@up.matrix.to_quaternion())
        bpy.context.view_layer.update()
        current=(ha.head-lo.head).normalized();desired=(wr-lo.head).normalized()
        rotation_matrix(lo,current.rotation_difference(desired)@lo.matrix.to_quaternion())
        bpy.context.view_layer.update()
        q=ha.matrix.to_quaternion()
        # Align the local palm plane toward the camera before applying the
        # small wrist arcs. Otherwise a raised arm can wave edge-on.
        d=(ha.head-lo.head).normalized()
        i=self.p[P+'R_Index1'].head-ha.head
        l=self.p[P+'R_Little1'].head-ha.head
        n=i.cross(l).normalized()
        front=Vector((-.08,-1.,.01))
        n=(n-d*n.dot(d)).normalized()
        tar=(front-d*front.dot(d)).normalized()
        if n.dot(tar)<0:n=-n
        roll_angle=math.atan2(d.dot(n.cross(tar)),n.dot(tar))
        roll=Quaternion(d,roll_angle*amt)
        tilt=Quaternion((0.,-1.,0.),math.radians((7.+12.*arc)*amt))
        nod=Quaternion((1.,0.,0.),math.radians(4.*amt))
        rotation_matrix(ha,tilt@nod@roll@q)
        bpy.context.view_layer.update()
        self.waves.append((t,tuple(ha.head),(ha.head-wr).length))
    def apply(self,t):
        for n in self.controls:
            p=self.p[n];p.rotation_mode='QUATERNION'
            p.rotation_quaternion=(1.,0.,0.,0.);p.location=(0.,0.,0.);p.scale=(1.,1.,1.)
        breath=.53*math.sin((t-.32)*math.tau/3.62)+.17*math.sin((t-.80)*math.tau/2.44)
        lean=sample(t,[(0.,0.),(1.54,.34),(2.8,-.32),(6.33,.78),(7.45,-.82),(10.,.48),(11.4,0.)])
        turn=sample(t,[(0.,0.),(1.8,0.),(3.06,-5.5),(5.75,-1.6),(7.08,2.),(8.7,12.8),(9.35,12.8),(11.4,6.)])
        gaze=sample(t,[(0.,2.),(1.1,2.),(2.54,-14.),(3.36,-5.),(4.8,-1.),(6.32,3.),(7.5,-3.5),(9.0,-9.),(11.3,-2.)])
        chin=sample(t,[(0.,-1.8),(1.12,-.4),(2.54,-1.2),(3.94,1.6),(5.21,2.4),(6.38,-5.3),(8.62,1.5),(11.38,-1.1)])
        tilt=sample(t,[(0.,.4),(1.25,-.15),(2.53,-3.6),(3.83,2.8),(5.12,4.9),(6.56,-1.7),(7.67,2.7),(10.5,-2.1),(11.4,-.3)])
        self.rot(P+'C_Spine',.42*breath,.44*lean,turn*.34)
        self.rot(P+'C_Chest',.55*breath,.47*lean,turn*.41)
        self.rot(P+'C_UpperChest',.65*breath,.59*lean,turn*.25)
        self.rot(P+'C_Neck',chin*.36,tilt*.28,gaze*.27)
        self.rot(P+'C_Head',chin*.64,tilt*.72,gaze*.73)
        # Support arm stays calm, but responds to the torso rather than locked
        # in A-pose; wrist on the waving arm is solved below.
        ease=window(t,6.65,7.46,9.59,10.75)
        self.rot(P+'L_UpperArm',-.45*breath,12.1-2.1*ease,-2.25*ease)
        self.rot(P+'L_LowerArm',0.,.52*breath,1.8*ease)
        self.rot(P+'R_UpperArm',.54*breath,-12.6-.58*lean,.31*breath)
        bpy.context.view_layer.update()
        if ease>1e-4:self.nearby_wrist(t,ease)
        self.face_time(t);bpy.context.view_layer.update()
    def key(self,k):
        for name in self.controls:
            pb=self.p[name]
            pb.keyframe_insert(data_path='rotation_quaternion',frame=k,group=name)
            pb.keyframe_insert(data_path='location',frame=k,group=name)
        for name in self.face_ids:self.shapes[name].keyframe_insert(data_path='value',frame=k,group='Suzu · native face')

def program():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('out',type=Path);p.add_argument('--stride',type=int,default=2);p.add_argument('--stats',type=Path);p.add_argument('--hair-module',type=Path);p.add_argument('--lower-module',type=Path)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    scene=bpy.context.scene;rig=scene.objects['Suzu · Humanoid'];face=scene.objects['Suzu · Face']
    run=Performance(rig,face)
    scene.frame_start=1;scene.frame_end=FRAMES;scene.render.fps=FPS
    frames=sorted(set(range(1,FRAMES+1,a.stride))|{FRAMES})
    hair_motion=None
    if a.hair_module:
        sys.path.insert(0,str(a.hair_module.resolve()))
        from hair_secondary import apply_hair_rig, HairMotion
        if not any(b.name.startswith('SuzuH.') for b in rig.data.bones):apply_hair_rig(scene)
        hair_motion=HairMotion(rig)
    skirt_motion=None
    if a.lower_module:
        sys.path.insert(0,str(a.lower_module.resolve()))
        from lower_rig import apply_lower_rig, SkirtMotion
        if not any(b.name.startswith('SuzuC.') for b in rig.data.bones):apply_lower_rig(scene)
        skirt_motion=SkirtMotion(rig)
    frame_set=set(frames)
    for k in range(1,FRAMES+1) if hair_motion or skirt_motion else frames:
        scene.frame_set(k)
        run.apply((k-1)/FPS)
        if hair_motion:hair_motion.step(dt=1/FPS,frame=k,key=k in frame_set)
        if skirt_motion:skirt_motion.step(dt=1/FPS,frame=k,key=k in frame_set)
        if k in frame_set:run.key(k)
    if hair_motion and hasattr(hair_motion,'seal_contacts'):hair_motion.seal_contacts()
    for ob,tag in [(rig,'Suzu · Continuous performance'),(face.data.shape_keys,'Suzu · Native four expressions and blinks')]:
        ac=ob.animation_data.action;ac.name=tag
        for fc in ac.fcurves:
            for key in fc.keyframe_points:key.interpolation='LINEAR'
    for label,k in [('Breath',1),('Glance and blink',55),('Open laugh',111),('Eyes-closed smile',151),('Surprise',189),('Wave',229),('Settle',324)]:
        scene.timeline_markers.new(label,frame=k)
    scene.frame_set(1)
    a.out.resolve().parent.mkdir(parents=True,exist_ok=True)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()),compress=True)
    if a.stats and run.waves:
        z=[x[1][2] for x in run.waves]
        a.stats.write_text(json.dumps({'frames':FRAMES,'fps':FPS,'reach_m':(min(z),max(z)),
           'wave_target_max_error_m':max(x[2] for x in run.waves),'native_expression_channels':run.face_ids,
           'arm_segment_lengths_m':(run.len1,run.len2)},indent=2)+'\n')
if __name__=='__main__':program()

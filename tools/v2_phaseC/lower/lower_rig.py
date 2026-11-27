"""Native lock-preserving lower-clothing binding and deterministic skirt follow-through."""
import argparse,sys,json
from collections import defaultdict
from math import sin,cos,pi,tau
from pathlib import Path
import bpy
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

COUNT=13
PRE='SuzuC.Skirt.'
HIP='J_Bip_C_Hips';SPINE='J_Bip_C_Spine'

def ease(t):
    t=max(0.,min(1.,t));return t*t*(3-2*t)

def pair(a,b,t):return (1.-t)*a+t*b

def add_skirt_bones(rig):
    """Only add independent controls: no native-bone edits or pose constraints."""
    if all(PRE+f'{i:02}' in rig.data.bones for i in range(COUNT)):return rig
    bpy.context.view_layer.objects.active=rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bones=rig.data.edit_bones;parent=bones[HIP]
    inv=rig.matrix_world.inverted()
    for i in range(COUNT):
        name=PRE+f'{i:02}'
        if name in bones:continue
        a=(i+.5)*tau/COUNT-.110
        b=bones.new(name)
        b.head=inv@Vector((.101*sin(a),-.030-.071*cos(a),.984))
        b.tail=inv@Vector((.193*sin(a),-.002-.143*cos(a),.766+.006*sin(a)**2))
        b.parent=parent;b.use_connect=False;b.use_deform=True
        b.inherit_scale='NONE'
        b.align_roll(Vector((0,0,1)))
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()
    collection=rig.data.collections.get('C · Skirt response') or rig.data.collections.new('C · Skirt response')
    for i in range(COUNT):
        n=PRE+f'{i:02}';b=rig.data.bones[n];collection.assign(b);b['suzu_secondary_role']='wide knife-pleat and lining'
        rig.pose.bones[n].rotation_mode='QUATERNION'
    return rig

def apply_lower_rig(scene=None):
    scene=scene or bpy.context.scene
    objects=[o for o in bpy.data.collections['SUZU_PHASE_C_LOWER'].objects if o.type=='MESH']
    rig=scene.objects['Suzu · Humanoid'];add_skirt_bones(rig)
    for o in objects:
        mod=next((m for m in o.modifiers if m.type=='ARMATURE'),None) or o.modifiers.new('Phase C Hoshino human bind','ARMATURE')
        mod.object=rig;mod.use_deform_preserve_volume=True
    bpy.context.view_layer.update()
    return rig

class NativeWeights:
    """Transfer true source triangle weights in fixed world rest coordinates."""
    def __init__(self,body):
        self.m=body.data
        self.v=[body.matrix_world@v.co for v in self.m.vertices]
        self.m.calc_loop_triangles();self.tri=[tuple(i.vertices) for i in self.m.loop_triangles]
        self.tree=BVHTree.FromPolygons(self.v,self.tri,all_triangles=True)
        self.g=[g.name for g in body.vertex_groups]
        self.w=[{self.g[t.group]:t.weight for t in v.groups if t.weight>1.e-7} for v in self.m.vertices]

    def transfer(self,p):
        near,n,i,dist=self.tree.find_nearest(p)
        if near is None:return {HIP:1.}
        ids=self.tri[i]
        a,b,c=self.v[ids[0]],self.v[ids[1]],self.v[ids[2]]
        e0=b-a;e1=c-a;d=near-a
        uu=e0.dot(e0);uv=e0.dot(e1);vv=e1.dot(e1);du=d.dot(e0);dv=d.dot(e1)
        den=uu*vv-uv*uv
        beta=(vv*du-uv*dv)/den if abs(den)>1.e-15 else 0.
        gamma=(uu*dv-uv*du)/den if abs(den)>1.e-15 else 0.
        coords=(1.-beta-gamma,beta,gamma);out=defaultdict(float)
        for k,x in zip(ids,coords):
            if x<=0:continue
            for g,w in self.w[k].items():out[g]+=x*w
        return out

def weight_for(o,p,source):
    style=o['suzu_lower_weight']
    if style.startswith(('foot','shoe')):
        s='L' if style[-1]=='1' and not style.endswith('-1') else 'R'
        foot='J_Bip_'+s+'_Foot';toe='J_Bip_'+s+'_ToeBase'
        if style.startswith('foot'):return {foot:1.}
        f=.72*ease((-.057-p.y)/.058)
        return {foot:1.-f,toe:f}
    if style=='skirt':
        # The same Z/angle coordinates drive twill, gilding and ivory, so
        # their independently cut pieces follow together without edge drift.
        from math import atan2,floor
        Y=p.y+.028*ease((p.z-.735)/.255)
        a=(atan2(p.x,-Y)+.110)%tau
        u=a*COUNT/tau-.5;i=floor(u);k=ease(u-i)
        f=ease((.984-p.z)/.202)
        H=1.-ease((p.z-.949)/.053)
        return {PRE+f'{i%COUNT:02}':f*(1.-k),PRE+f'{(i+1)%COUNT:02}':f*k,
            HIP:(1.-f)*H,SPINE:(1.-f)*(1.-H)}
    return source.transfer(p)

def bind_patterns(scene):
    rig=scene.objects['Suzu · Humanoid'];body=scene.objects['Suzu · Body'];source=NativeWeights(body)
    C=bpy.data.collections['SUZU_PHASE_C_LOWER']
    part=[o for o in C.objects if o.type=='MESH'];status={}
    for o in part:
        o.vertex_groups.clear();groups={};coverage=defaultdict(float);err=0.;nv=0
        for v in o.data.vertices:
            weights=sorted(((w,n) for n,w in weight_for(o,o.matrix_world@v.co,source).items()
                           if w>.00025 and (n in rig.data.bones or n.startswith(PRE))),reverse=True)[:4]
            if not weights:weights=[(1.,HIP)]
            norm=sum(w for w,n in weights)
            for w,n in weights:
                if n not in groups:groups[n]=o.vertex_groups.new(name=n)
                ww=w/norm
                groups[n].add([v.index],ww,'REPLACE');coverage[n]+=ww
        mod=next((m for m in o.modifiers if m.type=='ARMATURE'),None) or o.modifiers.new('Phase C Hoshino human bind','ARMATURE')
        mod.object=rig;mod.use_deform_preserve_volume=True
        for v in o.data.vertices:
            err=max(err,abs(sum(x.weight for x in v.groups)-1.));nv+=bool(v.groups)
        status[o.name]={'vertices':len(o.data.vertices),'weighted':nv,'normalization_error':err,'bones':sorted(coverage)}
        assert nv==len(o.data.vertices) and err<2.e-6, (o.name,nv,err)
    apply_lower_rig(scene)
    return C,part,status

class SkirtMotion:
    """Under-damped physical follow-through, keyed on the same performance clock."""
    def __init__(self,rig):
        self.rig=rig;self.bones=rig.pose.bones
        self.sectors=[self.bones[PRE+f'{i:02}'] for i in range(COUNT)]
        self.rest={b.name:b.bone.matrix_local.to_quaternion() for b in (
                *self.sectors,self.bones[HIP],self.bones[SPINE])}
        self.yaw=None;self.pitch=None
        self.y=[0.,0.];self.tilt=[[0.,0.] for _ in self.sectors]
        self.stats={'min_yaw':0.,'max_yaw':0.,'max_lift':0.}

    @staticmethod
    def spring(state,target,stiffness,damping,dt):
        # Short substeps make the result consistent at 30 fps and for assets
        # re-baked at multiples of 30.
        n=max(1,int(dt*180)+1);h=dt/n
        for _ in range(n):
            x,v=state
            v+=(stiffness*(target-x)-damping*v)*h
            state[0]=x+h*v;state[1]=v
        return state[0]

    def step(self,dt,frame=None,key=False):
        hip=self.bones[HIP];spine=self.bones[SPINE]
        qH=hip.matrix.to_quaternion()@self.rest[HIP].inverted()
        qS=spine.matrix.to_quaternion()@self.rest[SPINE].inverted()
        H=qH.to_euler('XYZ');S=qS.to_euler('XYZ')
        a=.55*H.z+.45*S.z
        p=.5*H.x+.5*S.x
        da=0. if self.yaw is None else max(-1.,min(1.,(a-self.yaw)/dt))
        dp=0. if self.pitch is None else max(-.9,min(.9,(p-self.pitch)/dt))
        self.yaw=a;self.pitch=p
        yaw=self.spring(self.y,max(-.072,min(.072,-.59*a-1.20*da)),61.,11.,dt)
        self.stats['min_yaw']=min(self.stats['min_yaw'],yaw);self.stats['max_yaw']=max(self.stats['max_yaw'],yaw)
        for i,b in enumerate(self.sectors):
            angle=(i+.5)*tau/COUNT-.110
            # Fabric opens a little on the lagging side and resettles. If the
            # motion stops, targets and all secondary velocities return to 0.
            target=max(0.,min(.044,abs(da)*(.115-.062*sin(angle))+.072*abs(dp)*(.5+.5*cos(angle))))
            lift=self.spring(self.tilt[i],target,46.+13.*(sin(angle)**2),8.4,dt)
            ru=Quaternion((0,0,1),yaw*(.93+.07*cos(angle)))
            rt=Quaternion((cos(angle),sin(angle),0),-lift)
            self.stats['max_lift']=max(self.stats['max_lift'],lift)
            qb=self.rest[b.name]
            b.rotation_quaternion=qb.inverted()@ru@rt@qb
            if key:b.keyframe_insert(data_path='rotation_quaternion',frame=frame,group='Suzu · Skirt inertia')
        bpy.context.view_layer.update()

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--out',required=True,type=Path);a.add_argument('--module',type=Path);a.add_argument('--report',type=Path)
    args=a.parse_args(sys.argv[sys.argv.index('--')+1:])
    C,objects,results=bind_patterns(bpy.context.scene)
    rig=bpy.data.objects['Suzu · Humanoid']
    assert len(rig.data.bones)==154+COUNT
    if args.module:
        for o in objects:
            for m in o.modifiers:
                if m.type=='ARMATURE':m.object=None
        bpy.data.libraries.write(str(args.module.resolve()),{C},fake_user=True,compress=True)
        for o in objects:
            for m in o.modifiers:
                if m.type=='ARMATURE':m.object=rig
    if args.report:
        args.report.write_text(json.dumps({'core_rig_bones':len(rig.data.bones)-COUNT,'skirt_bones':COUNT,'pieces':results},
                                          ensure_ascii=False,indent=2)+'\n')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(args.out.resolve()),compress=True)
    print('Lower binding:',len(objects),'weighted mesh pieces; native rig untouched,',COUNT,'new skirt controls.')

if __name__=='__main__':main()

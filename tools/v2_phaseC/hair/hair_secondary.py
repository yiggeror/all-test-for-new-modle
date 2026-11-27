"""Phase C deform rig and deterministic secondary-motion bake for the locked hairstyle.

Use apply_hair_rig() once on the native assembled rig.  HairMotion.step() samples
already-posed head/chest transforms; set key=True to write the same deform joints
into the active character Action. No dependencies, drivers or mesh-frame swaps.
"""
import math
from dataclasses import dataclass
from functools import lru_cache

import bpy
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

HEAD = 'J_Bip_C_Head'
TORSO = 'J_Bip_C_UpperChest'
RIG = 'Suzu · Humanoid'
ROOT_FRACTION = .125
PREFIX = 'SuzuH.'
_REAR = {
    'R': ((-.081,.123,1.436),(-.103,.140,1.312),(-.133,.158,1.181),(-.172,.176,1.006)),
    'C': (( .001,.153,1.441),( .002,.169,1.315),( .005,.179,1.175),( .010,.191, .955)),
    'L': (( .082,.122,1.436),( .104,.139,1.312),( .137,.158,1.185),( .176,.176,1.023)),
}
_PONY = ((.1102,.0233,1.5275),(.168,.053,1.551),(.193,.084,1.461),(.230,.095,1.370),(.251,.102,1.272))
_AHOGE = ((-.010,.008,1.613),(-.026,-.002,1.640),(-.015,-.002,1.670),(.027,.011,1.677))
CHAINS = {**{f'Rear.{n}': z for n,z in _REAR.items()}, 'Pony.L': _PONY, 'Ahoge': _AHOGE}
BONES = tuple(f'{PREFIX}{chain}.{i+1:02}' for chain,rail in CHAINS.items() for i in range(len(rail)-1))
REAR_BASES=tuple(f'{PREFIX}Rear.{n}.01' for n in 'RCL')


def _sat(x):
    return min(1.,max(0.,x))


def _soft(a,b,x):
    u = _sat((x-a)/(b-a)); return u*u*(3.-2.*u)


def _ang(v):
    q = v.normalized()
    if q.w < 0: q.negate()
    axis,n = q.to_axis_angle()
    return axis*n if n>1e-7 else Vector((0.,0.,0.))


def _q(v):
    m = v.length
    return Quaternion(v/m,m) if m>1e-8 else Quaternion((1.,0.,0.,0.))


def _uv_v(mesh):
    uv=mesh.uv_layers.get('HairUV');z=[0.]*len(mesh.vertices);n=[0]*len(z)
    if uv is None: return z
    for li in mesh.loops:
        j=li.vertex_index;z[j]+=uv.data[li.index].uv.y;n[j]+=1
    return [a/b if b else 0. for a,b in zip(z,n)]


def _refine_bang_roots(hair):
    crown=next(o for o in hair if o.name.startswith('Crown ·'))
    m=crown.data;m.calc_loop_triangles()
    # Crown surface was authored outside first, then inward return shell (38 x 112 rings).
    cutter=1+38*112
    outer=BVHTree.FromPolygons([crown.matrix_world@v.co for v in m.vertices],
                              [tuple(t.vertices) for t in m.loop_triangles if max(t.vertices)<cutter],all_triangles=True)
    edits={}
    for ob in hair:
        if not ob.name.startswith(('Fringe ','Air ')):continue
        uv=_uv_v(ob.data);inv=ob.matrix_world.inverted();deltas=[];checks=[]
        for p,v in zip(ob.data.vertices,uv):
            k=ob.matrix_world@p.co
            f=_soft(1.533,1.569,k.z)*_soft(.59,.24,v)*_soft(.035,-.015,k.y)
            if f<.0001:continue
            q,n,_,distance=outer.find_nearest(k,.033)
            if q is None or (k-q).dot(n)<.00022:continue
            s=min(ROOT_FRACTION*f,.0026/max(1e-9,distance))
            p.co=inv@k.lerp(q,s);deltas.append(distance*s)
            if f>.88:checks.append(s)
        if deltas:
            ob.data.update();edits[ob.name]={'root_vertices':len(deltas),'max_mm':max(deltas)*1000.,
                'peak_optical_pull_fraction':max(checks,default=0.)}
    return edits


def _parent_to_head(ob,rig):
    if ob.parent==rig and ob.parent_type=='BONE' and ob.parent_bone==HEAD:return
    old=ob.matrix_world.copy();ob.parent=rig;ob.parent_type='BONE';ob.parent_bone=HEAD
    bpy.context.view_layer.update();ob.matrix_world=old


def _parent_as_skin(ob,rig):
    old=ob.matrix_world.copy();ob.parent=rig;ob.parent_type='OBJECT';ob.parent_bone=''
    ob.matrix_parent_inverse.identity();bpy.context.view_layer.update();ob.matrix_world=old
    mod=ob.modifiers.new('Suzu secondary hair skin','ARMATURE');mod.object=rig
    mod.use_vertex_groups=True;mod.use_deform_preserve_volume=True


def _joint_names(chain):return [f'{PREFIX}{chain}.{i+1:02}' for i in range(len(CHAINS[chain])-1)]


def _interp(v,xs):
    if v<=xs[0]:return [(0,1.)]
    for i,(a,b) in enumerate(zip(xs,xs[1:])):
        if v<=b:
            t=_soft(a,b,v);return [(i,1.-t),(i+1,t)]
    return [(len(xs)-1,1.)]


@lru_cache(None)
def _chain_path(chain):
    vec=[Vector(p) for p in CHAINS[chain]];starts=[0.]
    for p,q in zip(vec,vec[1:]):starts.append(starts[-1]+(q-p).length)
    return vec,starts


def _progress(p,chain):
    path,st=_chain_path(chain);sample=[]
    for i,(a,b) in enumerate(zip(path,path[1:])):
        e=b-a;t=_sat((p-a).dot(e)/e.length_squared)
        sample.append(((p-(a+t*e)).length_squared,(st[i]+t*(st[i+1]-st[i]))/st[-1]))
    return min(sample)[1]


def _ribbon_rings(ob,sidecount):
    # Ribbons have a common cross-section per ring; weight the centre, not width.
    v=ob.data.vertices;n=len(v)
    if n%sidecount:return [ob.matrix_world@p.co for p in v]
    centers=[]
    for r in range(n//sidecount):
        xyz=sum((v[j].co for j in range(r*sidecount,(r+1)*sidecount)),Vector())/sidecount
        centers.extend([ob.matrix_world@xyz]*sidecount)
    return centers


def _weights_for(ob):
    name=ob.name
    if name.startswith(('Pony ','Ahoge')):
        ahoge=name.startswith('Ahoge');chain='Ahoge' if ahoge else 'Pony.L';joints=_joint_names(chain)
        stations=(.22,.55,.85) if ahoge else (.22,.45,.67,.91)
        for p in _ribbon_rings(ob,20 if ahoge else 24):
            v=_progress(p,chain)
            f=_soft(.075,.28,v) if ahoge else _soft(.090,.28,v)*_soft(.145,.168,p.x)
            yield [(HEAD,1.-f)]+[(joints[n],f*w) for n,w in _interp(v,stations)]
    else:
        # Below the immobile crown, neighboring rails blend across the back width.
        for v in ob.data.vertices:
            p=ob.matrix_world@v.co
            v=p.z;f=_soft(1.455,1.330,v)
            width=.078+.050*_soft(1.405,1.060,v)
            profile=_interp(p.x,(-width,0.,width));span=_interp(v*-1,(-1.332,-1.208,-1.073))
            ws=[(HEAD,1.-f)]
            for lane,a in profile:
                j=_joint_names(f'Rear.{"RCL"[lane]}')
                ws.extend((j[k],f*a*b) for k,b in span)
            yield ws


def _set_weights(ob):
    groups={}
    for p,pairs in zip(ob.data.vertices,_weights_for(ob)):
        pairs=sorted(((n,w) for n,w in pairs if w>1e-7),key=lambda x:-x[1])[:4]
        total=sum(w for _,w in pairs)
        for n,w in pairs:
            if n not in groups:groups[n]=ob.vertex_groups.new(name=n)
            groups[n].add((p.index,),w/total,'REPLACE')
    return len(groups)


def apply_hair_rig(scene=None,refine=True):
    """Add 16 deform joints and prepare the approved Phase B geometry in its rest pose."""
    scene=scene or bpy.context.scene;rig=scene.objects[RIG];view=bpy.context.view_layer
    if all(n in rig.data.bones for n in BONES):return rig
    if any(n in rig.data.bones for n in BONES):raise RuntimeError('Partial hair rig')
    if HEAD not in rig.data.bones or TORSO not in rig.data.bones:raise KeyError('Native Suzu head rig')
    h=bpy.data.collections['SUZU_PHASE_B_HAIR'];props=bpy.data.collections['SUZU_PHASE_B_PROPS']
    hair=[o for o in h.all_objects if o.type=='MESH']
    assert len(hair)==39 and len(rig.data.bones)==154
    trim=_refine_bang_roots(hair) if refine else {}
    active=view.objects.active;selection=list(bpy.context.selected_objects);inv=rig.matrix_world.inverted()
    for ob in selection:ob.select_set(False)
    rig.select_set(True);view.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
    edit=rig.data.edit_bones
    collection=rig.data.collections.get('Suzu secondary silk') or rig.data.collections.new('Suzu secondary silk')
    for chain,points in CHAINS.items():
        names=_joint_names(chain)
        for i,(a,b) in enumerate(zip(points,points[1:])):
            j=edit.new(names[i]);j.head=inv@Vector(a);j.tail=inv@Vector(b)
            j.parent=edit[HEAD] if i==0 else edit[names[i-1]];j.use_connect=i>0
            j.use_deform=True;j.align_roll(Vector((0.,1.,0.)));j.inherit_scale='FIX_SHEAR'
            collection.assign(j)
    bpy.ops.object.mode_set(mode='OBJECT')
    for n in BONES:
        p=rig.pose.bones[n];p.rotation_mode='QUATERNION';p.lock_location=(True,)*3;p.lock_scale=(True,)*3
        p['suzu_secondary_silk']=True
    dynamic={}
    for ob in hair:
        if ob.name.startswith(('Pony ','Ahoge','Suzu Back')):
            _parent_as_skin(ob,rig);dynamic[ob.name]=_set_weights(ob)
        else:_parent_to_head(ob,rig)
    for ob in tuple(h.all_objects)+tuple(props.all_objects):
        if ob.type=='EMPTY' or (ob.type=='MESH' and ob.name not in dynamic and ob in props.all_objects.values()):_parent_to_head(ob,rig)
    rig['suzu_hair_native_bones']=154;rig['suzu_hair_deformation_bones']=len(BONES)
    rig['suzu_hair_root_optical_pull']=ROOT_FRACTION if refine else 0.
    rig['suzu_hair_dynamic_meshes']=len(dynamic)
    scene['suzu_hair_root_adjustment']=trim
    rig.select_set(False)
    for o in selection:o.select_set(True)
    if active and active.name in view.objects:view.objects.active=active
    view.update()
    return rig


@dataclass
class _Spring:
    x:Vector
    v:Vector

    @classmethod
    def new(cls):return cls(Vector((0.,0.,0.)),Vector((0.,0.,0.)))

    def step(self,tgt,dt,hz,zeta):
        # Second order damped response; bake at fixed substeps for repeatable reopens.
        w=2.*math.pi*hz;steps=max(1,math.ceil(dt*240));h=dt/steps
        for _ in range(steps):
            self.v+=h*(w*w*(tgt-self.x)-2.*zeta*w*self.v);self.x+=h*self.v
        return self.x.copy()


class _ShoulderContact:
    """Adaptive rear-surface contacts; only real near-collision moves a root."""
    _wardrobe=('Jacket · left back','Jacket · right back','Jacket · two-piece slim sleeve',
                'Jacket · narrow rollover collar','Shirt · turned neck stand')

    def __init__(self,rig,objects=None):
        self.rig=rig
        sc=bpy.context.scene
        self.obstacles=tuple(objects) if objects is not None else tuple(o for o in sc.objects if o.type=='MESH' and
            (o.name=='Suzu · Body' or o.name.startswith(self._wardrobe)))
        self.probes={}
        for o in bpy.data.collections['SUZU_PHASE_B_HAIR'].all_objects:
            if o.type!='MESH' or not o.name.startswith('Suzu Back'):continue
            rows=[]; table={g.index:g.name for g in o.vertex_groups}
            for v in o.data.vertices:
                x,y,z=o.matrix_world@v.co
                if not (1.13<z<1.351 and y>.046):continue
                # Enough longitudinal and transverse samples to cover the ribbon edge,
                # not only the wider centreline where the first real contact is missed.
                if v.index%3 and not o.name.startswith('Suzu Back OUTER'):continue
                if o.name.startswith('Suzu Back OUTER') and v.index%2:continue
                w=[sum(g.weight for g in v.groups if table[g.group].startswith(f'{PREFIX}Rear.{n}')) for n in 'RCL']
                if max(w)>.15:rows.append((v.index,w))
            if rows:self.probes[o.name]=(o,tuple(rows))
        self.pressure=[0.]*3
        self.peak=[0.]*3
        self.axes=[Vector((0.,0.,0.)) for _ in REAR_BASES]

    def reset(self):self.pressure[:]=[0.]*3;self.peak[:]=[0.]*3

    def apply(self,chest,dt):
        if not self.obstacles:return
        d=bpy.context.evaluated_depsgraph_get();verts=[];tri=[]
        for o in self.obstacles:
            b=o.evaluated_get(d);m=b.to_mesh();m.calc_loop_triangles();ini=len(verts);mx=b.matrix_world
            w=[mx@v.co for v in m.vertices];verts.extend(w)
            tri.extend(tuple(ini+j for j in p.vertices) for p in m.loop_triangles
                if max(w[j].z for j in p.vertices)>1.103 and min(w[j].z for j in p.vertices)<1.368)
            b.to_mesh_clear()
        if not tri:return
        field=BVHTree.FromPolygons(verts,tri,all_triangles=True)
        rear=chest@Vector((0.,1.,0.));want=[0.,0.,0.];pending=[]
        for o,indices in self.probes.values():
            q=o.evaluated_get(d);m=q.to_mesh();mx=q.matrix_world
            for idx,w in indices:
                p=mx@m.vertices[idx].co
                if not 1.105<p.z<1.361:continue
                hit,_,__,lane=field.ray_cast(p+rear*.093,-rear,.153)
                if hit is None:continue
                gap=lane-.093
                if gap<.017 and gap>-.060:pending.append((.0175-gap,w))
            q.to_mesh_clear()
        # For a cross-lane point, the sum of independent weights meets the gap.
        # Resolve strongest pushes first; neighboring active lanes share the displacement.
        for pen,w in sorted(pending,reverse=True):
            extra=pen-sum(t*p for t,p in zip(w,want))
            if extra<=0:continue
            total=sum(t*t for t in w)
            if total<.03:continue
            for i,x in enumerate(w):want[i]=min(.062,want[i]+extra*x/total)
        for i,n in enumerate(REAR_BASES):
            self.pressure[i]=max(want[i],self.pressure[i]*math.exp(-13.*dt))
            self.peak[i]=max(self.peak[i],self.pressure[i]);p=self.rig.pose.bones[n]
            frame=p.matrix.to_quaternion()@p.rotation_quaternion.inverted()
            self.axes[i]=frame.inverted()@rear
            p.location=self.axes[i]*self.pressure[i]


class HairMotion:
    """A spatial damped spring solved from actual head/chest transforms, not preset wiggle."""
    def __init__(self,rig=None,strength=1.,collision=True,collision_objects=None):
        self.rig=rig or bpy.data.objects[RIG];self.strength=strength
        self._rest={n:self.rig.data.bones[n].matrix_local.to_quaternion() for n in (HEAD,TORSO,*BONES)}
        self._state={n:_Spring.new() for n in BONES}
        self._previous=None
        self.contact=_ShoulderContact(self.rig,collision_objects) if collision else None
        self._contact_keys={}

    def _delta(self,n):return self.rig.pose.bones[n].matrix.to_quaternion()@self._rest[n].inverted()

    def reset(self,deform=True):
        self._state={n:_Spring.new() for n in BONES};self._previous=None
        self._contact_keys.clear()
        if self.contact:self.contact.reset()
        if deform:
            for n in BONES:
                p=self.rig.pose.bones[n];p.rotation_quaternion=(1.,0.,0.,0.);p.location=(0.,0.,0.)
            bpy.context.view_layer.update()

    def step(self,dt=1/30,frame=None,key=False,update=True):
        dt=max(.0005,min(.1,float(dt)))
        if update:bpy.context.view_layer.update()
        head=self._delta(HEAD);chest=self._delta(TORSO);relative=chest.inverted()@head
        posture=_ang(relative)
        origin=self.rig.pose.bones[HEAD].head.copy()
        if self._previous is None:
            vr=vt=velocity=accel=Vector((0.,0.,0.))
        else:
            before,pre_chest,point,last_v=self._previous
            # Full-body turn yields physical motion too; the torso-relative part is stronger.
            vr=_ang(relative@before.inverted())/dt
            vt=_ang(chest@pre_chest.inverted())/dt
            velocity=chest.inverted()@((origin-point)/dt)
            accel=(velocity-last_v)/dt
        self._previous=(relative.copy(),chest.copy(),origin,velocity.copy())
        drive=vr+.31*vt
        result={}
        for chain in CHAINS:
            for i,n in enumerate(_joint_names(chain)):
                if chain.startswith('Rear'):
                    lane={'R':-1,'C':0,'L':1}[chain[-1]]
                    # The steady counterbalance keeps the lower curtain over the back when
                    # the head twists separately from shoulders; the resolved momentum still lags.
                    safety=Vector((-posture.x*(.74 if i==0 else .10 if i==1 else .0),
                                   -posture.y*(.67 if i==0 else .12 if i==1 else .0),
                                   -posture.z*(.72 if i==0 else .14 if i==1 else .0)))
                    k=(.017,.041,.060)[i]*(1.+.07*lane)
                    force=Vector((-k*drive.x+.0021*accel.y,-k*drive.y-.0025*accel.x,-k*drive.z))
                    hz=(5.8,4.15,3.3)[i]*(1.-.04*lane); damping=(.93,.84,.78)[i]
                    limit=math.radians((18.,8.5,8.5)[i])
                elif chain=='Pony.L':
                    k=(.022,.048,.059,.064)[i]
                    safety=Vector((-posture.x*.10 if i==0 else 0.,-posture.y*.13 if i==0 else 0.,-posture.z*.14 if i==0 else 0.))
                    force=Vector((-k*drive.x+.0037*accel.y,-k*drive.y-.0042*accel.x,-k*drive.z+.0014*accel.y))
                    hz=(6.1,4.4,3.8,3.45)[i];damping=(.93,.82,.77,.71)[i];limit=math.radians((8.0,9.0,10.5,10.5)[i])
                else:
                    k=(.020,.044,.051)[i]
                    safety=Vector((0.,0.,0.))
                    force=Vector((-k*drive.x+.004*accel.y,-k*drive.y-.004*accel.x,-k*drive.z))
                    hz=(9.2,7.6,6.7)[i];damping=(.87,.81,.75)[i];limit=math.radians((5.,7.,9.)[i])
                if force.length>limit:force=force.normalized()*limit
                spring=self._state[n].step(force*self.strength,dt,hz,damping)
                theta=safety+spring
                if theta.length>limit:theta=theta.normalized()*limit
                basis=self._rest[n].inverted()@theta
                p=self.rig.pose.bones[n];p.rotation_quaternion=_q(basis)
                p.location=(0.,0.,0.)
                result[n]=p.rotation_quaternion.copy()
        if self.contact:
            bpy.context.view_layer.update();self.contact.apply(chest,dt)
            if frame is not None:
                self._contact_keys[int(frame)]=(tuple(self.contact.pressure),tuple(x.copy() for x in self.contact.axes),key)
        if key:
            for n in BONES:
                p=self.rig.pose.bones[n]
                p.keyframe_insert(data_path='rotation_quaternion',frame=frame,group='Suzu Hair Dynamics')
                if n in REAR_BASES:p.keyframe_insert(data_path='location',frame=frame,group='Suzu Hair Dynamics')
        if update:bpy.context.view_layer.update()
        return result

    def seal_contacts(self):
        """Optional keyed editorial pass: distribute measured impacts over the next .13s.

        Bake after the chronological sampling loop. It keeps every measured local
        clearance, but progressively takes it up before abrupt sleeve silhouettes
        first enter a forward ray. Root/chest animation and rotation keys are untouched.
        """
        radius=(1.,.91,.69,.42,.17)
        for frame,(value,axes,keyed) in self._contact_keys.items():
            for i,n in enumerate(REAR_BASES):
                s=value[i]
                for j,w in enumerate(radius):
                    future=self._contact_keys.get(frame+j)
                    if future is not None:s=max(s,w*future[0][i])
                if (keyed and s>value[i]+.0001) or (not keyed and s>.0001):
                    p=self.rig.pose.bones[n];p.location=axes[i]*s
                    p.keyframe_insert(data_path='location',frame=frame,group='Suzu Hair Dynamics')

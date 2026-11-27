"""Round 6 finish-turn: planted soles and a quaternion two-bone knee solve.

No constraints, rest bones, groups, materials, or meshes are changed. All
matrices are PoseBone matrices. Capture the neutral lower stance before
the bake, then solve once per frame before upper-arm world-space IK and
before the hair/skirt physics. Key the nine controls into the existing action.

    from turn_support import prepare_turn, apply_turn, key_turn, upper_yaw_gain
    prepare_turn(performance)                 # frame 1, neutral lower pose
    state = apply_turn(performance, t)       # per frame
    turn *= upper_yaw_gain(t)                # legacy local chest turn only
    # ... face, arm IK, hair/skirt steps ...
    key_turn(performance, frame)             # or include TURN_BONES in key()

The two world foot frames are invariant. Any support "pivot" is above the
soles, not a rotation/skate of the contact patch. Native VRM aim/roll still
evaluate normally and should be sampled by the existing exporter.
"""
import math
import bpy
from mathutils import Vector, Quaternion

HIP = 'J_Bip_C_Hips'
LEGS = {s: tuple('J_Bip_'+s+'_'+n for n in ('UpperLeg','LowerLeg','Foot','ToeBase')) for s in ('L','R')}
TURN_BONES = (HIP,)+tuple(n for names in LEGS.values() for n in names)
START = 8.87
Z = Vector((0,0,1))
Y = Vector((0,1,0))

def ease(a,b,t):
    if a==b:return float(t>=a)
    f=max(0.0,min(1.0,(t-a)/(b-a)))
    return f*f*f*(f*(6*f-15)+10)

def turn_channels(t):
    """Return world pelvis arc (metres/degrees), independent of scene state."""
    fore = ease(START,9.84,t)
    follow = ease(9.98,11.34,t)
    twist = ease(8.94,10.14,t)
    catch = ease(10.46,11.36,t)
    return {
        'active': t>START,
        'yaw_deg':17.0*twist-1.60*catch,
        'roll_deg':-1.30*fore+.32*follow,
        'shift_world_m':(.0152*fore-.0031*follow,
                         .0006*fore+.0022*twist-.0005*follow,
                        -.0041*fore+.00115*follow),
        'knee_yaw_deg':.43*(17.0*twist-1.60*catch),
        'weight_progress':fore,
    }

def upper_yaw_gain(t):
    """Blend only the old, local upper torso yaw; hips now do the real turn."""
    return 1.-.82*ease(8.94,10.14,t)

def _rotmat(q,p):
    m=q.normalized().to_matrix().to_4x4()
    m.translation=p
    return m

def _proj(v,a):
    return v-a*v.dot(a)

def _leg_knee(start,end,upper,lower,pole):
    v=end-start
    d=v.length
    if d<.01:
        raise RuntimeError("Suzu turn: lower rig target coincides with the hip.")
    u=v/d
    al=(upper*upper-lower*lower+d*d)/(2*d)
    h2=max(0.,upper*upper-al*al)
    side=_proj(pole,u)
    if side.length<1.e-7:
        side=_proj(Vector((0,-1,0)),u)
    if side.length<1.e-7:
        side=_proj(Vector((1,0,0)),u)
    return start+u*al+side.normalized()*math.sqrt(h2)

class TurnSupport:
    def __init__(self,rig):
        self.rig=rig
        self.p=rig.pose.bones
        miss=[n for n in TURN_BONES if not self.p.get(n)]
        if miss:raise KeyError(("Missing Suzu lower controls",miss))
        bpy.context.view_layer.update()
        self.base={n:self.p[n].matrix.copy() for n in TURN_BONES}
        self.basis={n:self.p[n].matrix_basis.copy() for n in TURN_BONES}
        self.hip0=self.base[HIP].translation.copy()
        self.rtw=rig.matrix_world.to_quaternion()
        self.wtr=rig.matrix_world.inverted().to_3x3()
        self.chain={}
        for s,(u,l,f,toe) in LEGS.items():
            a,b,c=(self.base[n].translation.copy() for n in (u,l,f))
            a1=b-a;b1=c-b
            sp=_proj(a1,(c-a).normalized())
            if sp.length<.0005:sp=self.wtr@Vector((0,-1,0))
            self.chain[s]={'hip':a,'ankle':c,'knee':b,
                'up_dir':a1.normalized(),'lo_dir':b1.normalized(),
                'len_up':a1.length,'len_lo':b1.length, 'pole':sp.normalized(),
                'baseline_slack':a1.length+b1.length-(c-a).length}
        self.count_native=sum(not b.name.startswith(('SuzuH.','SuzuC.')) for b in rig.data.bones)

    def clear(self,update=True):
        for n in TURN_BONES:
            p=self.p[n]
            p.rotation_mode='QUATERNION'
            p.matrix_basis=self.basis[n]
        if update:bpy.context.view_layer.update()

    def apply(self,t):
        self.clear(update=False)
        work=turn_channels(t)
        if not work['active']:
            return work
        q_world=Quaternion(Z,math.radians(work['yaw_deg'])) @ Quaternion(Y,math.radians(work['roll_deg']))
        q=self.rtw.inverted()@q_world@self.rtw
        vert=self.wtr@Z
        shift=self.wtr@Vector(work['shift_world_m'])
        # Honor the ankle target, never silently clamp it. When an unusually
        # close-to-extension rig needs additional flex, drop the common pelvis
        # by the least amount preserving both measured native link lengths.
        safety=0.
        for meta in self.chain.values():
            a=self.hip0+q@(meta['hip']-self.hip0)+shift
            v=a-meta['ankle'];dh=v.dot(vert);horizontal=v-vert*dh
            m=.00050*work['weight_progress']
            lim=meta['len_up']+meta['len_lo']-m
            if horizontal.length>=lim:
                raise ValueError("Suzu turn: requested pose puts the hips outside the planted stance.")
            safety=max(safety,dh-math.sqrt(max(0.,lim*lim-horizontal.length_squared)))
        if safety>0.:
            shift-=vert*safety
            ss=self.rig.matrix_world.to_3x3()@shift
            work['shift_world_m']=tuple(ss)
        work['reach_bias_down_m']=safety
        self.p[HIP].matrix=_rotmat(q@self.base[HIP].to_quaternion(),self.hip0+shift)
        bpy.context.view_layer.update()
        kq=self.rtw.inverted()@Quaternion(Z,math.radians(work['knee_yaw_deg']))@self.rtw
        # Authored world yaw only guides the neutral bend pole, not the kneecap
        # twist. Each bone frame uses the unique least-swing quaternion from
        # its own neutral vector; this avoids accumulating roll while turning.
        for s,(u,l,f,toe) in LEGS.items():
            ch=self.chain[s];p=self.p[u]
            a=p.head.copy()
            k=_leg_knee(a,ch['ankle'],ch['len_up'],ch['len_lo'],kq@ch['pole'])
            wrist=(k-a).normalized()
            aq=ch['up_dir'].rotation_difference(wrist) @ self.base[u].to_quaternion()
            p.matrix=_rotmat(aq,a)
        bpy.context.view_layer.update()
        for s,(u,l,f,toe) in LEGS.items():
            ch=self.chain[s];p=self.p[l]
            b=p.head.copy()
            qlo=ch['lo_dir'].rotation_difference((ch['ankle']-b).normalized()) @ self.base[l].to_quaternion()
            p.matrix=_rotmat(qlo,b)
        bpy.context.view_layer.update()
        residual={}
        for s,(u,l,f,toe) in LEGS.items():
            residual[s]=(self.p[f].head-self.chain[s]['ankle']).length
            self.p[f].matrix=self.base[f]
        bpy.context.view_layer.update()
        for u,l,f,toe in LEGS.values():self.p[toe].matrix=self.base[toe]
        bpy.context.view_layer.update()
        work['link_ankle_residual_m']=residual
        return work

    def key(self,frame):
        for n in TURN_BONES:
            p=self.p[n]
            p.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=n)
            p.keyframe_insert(data_path='location',frame=frame,group=n)

def prepare_turn(performance):
    """Cache base pose on the Performance instance; or return state for a direct Armature."""
    if isinstance(performance,TurnSupport):return performance
    if getattr(performance,'type',None)=='ARMATURE':return TurnSupport(performance)
    state=TurnSupport(performance.rig)
    performance._round6_turn=state
    return state

def _state(performance):
    if isinstance(performance,TurnSupport):return performance
    return getattr(performance,'_round6_turn',None) or prepare_turn(performance)

def reset_turn(performance,update=True):
    _state(performance).clear(update=update)

def apply_turn(performance,t):
    return _state(performance).apply(float(t))

def key_turn(performance,frame):
    _state(performance).key(frame)

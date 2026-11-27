"""Suzu's R6 articulated wrist descent, in the rest-oriented chest frame."""
import math
from mathutils import Vector,Quaternion
START_LINKS=((-.973440051,-.106434226,.202697277),
             (-.200296164,-.345685899,.916723907))

# Quaternions at the last approved wave (8.967 s) and the relaxed baseline
# (11.367 s), taken from the reviewed, evaluated skeleton in chest coordinates.
START_Q=(
 (.516432762,.398963034,.557768226,-.512855172),
 (.528244734,.601540804,.597172201,-.049916126),
 (.642433047,-.204604357,.510253370,-.533908784))
END_Q=(
 (.710276425,.678175986,.133385986,-.133390740),
 (.602162659,.447148502,-.354623467,.558301508),
 (.707298517,.674587727,.154110119,-.144604683))
LIFT_A=(
 (.712591410,.676511645,.128978088,-.133828834),
 (.604184628,.442483157,-.355718315,.559136987),
 (.709630728,.673023760,.149682462,-.145115301))
LIFT_B=(
 (.595068395,.371506274,.534995496,-.470804244),
 (.479377836,.482033700,.733315885,.009390699),
 (.554513991,-.339618444,.642944813,-.404716849))

# Unit guidance is shoulder→elbow and elbow→wrist, not a single reversing
# wrist IK curve. The elbow leads down/forward, draws in, and then the palm
# follows through in front of the torso. Length is the native skinned rig.
KEYS=(
 (8.967,None,None,0.),
 (9.115,(-.974,-.155,.162),(-.198,-.396,.897),.015),
 (9.296,(-.921,-.244,-.304),(-.200,-.494,.846),.08),
 (9.495,(-.782,-.322,-.534),(-.140,-.757,.638),.25),
 (9.704,(-.645,-.317,-.695),(-.223,-.910,.348),.47),
 (9.893,(-.537,-.275,-.798),(-.440,-.869,-.223),.66),
 (10.075,(-.471,-.222,-.854),(-.432,-.666,-.608),.82),
 (10.260,(-.431,-.142,-.891),(-.409,-.477,-.779),.93),
 (10.470,(-.409,-.059,-.911),(-.414,-.223,-.883),.986),
 (10.763,None,None,1.),
)
LIFT_KEYS=(
 (6.650,None,None,0.),
 (6.775,(-.484,-.106,-.868),(-.359,-.280,-.895),.04),
 (6.932,(-.593,-.242,-.768),(-.237,-.808,-.539),.16),
 (7.081,(-.742,-.336,-.579),(-.166,-.969,.181),.33),
 (7.240,(-.862,-.345,-.377),(-.114,-.694,.711),.57),
 (7.422,(-.952,-.265,.138),(.007,-.407,.914),.84),
 (7.600,None,None,1.),
)

def sway(a,b,v):
    u=max(0.,min(1.,(v-a)/(b-a)));return u*u*u*(u*(u*6.-15.)+10.)

def hemi(a,b):
    w=b.normalized()
    if a.dot(w)<0.:w.negate()
    return w

def log_quat(q):
    q=q.normalized()
    if q.w<0.:q.negate()
    a,t=q.to_axis_angle()
    return a*(.5*t) if t>1e-7 else Vector((0.,0.,0.))

def exp_quat(v):
    e=v.length
    return Quaternion(v/e,2.*e) if e>1e-8 else Quaternion((1.,0.,0.,0.))

def offset(q,v):return (q@exp_quat(v)).normalized()

def bezier(a,b,c,d,x):
    v=a.slerp(hemi(a,b),x);w=b.slerp(hemi(b,c),x);y=c.slerp(hemi(c,d),x)
    l=v.slerp(hemi(v,w),x);h=w.slerp(hemi(w,y),x)
    return l.slerp(hemi(l,h),x).normalized()

class SphericalCubic:
    """Timed spherical Bézier using rotational tangents shared by adjacent curves."""
    def __init__(self,ts,quaternions):
        q=[quaternions[0].normalized()]
        for v in quaternions[1:]:q.append(hemi(q[-1],v))
        vel=[Vector((0.,0.,0.))]
        for i in range(1,len(q)-1):
            a,b,c=q[i-1:i+2];d0=ts[i]-ts[i-1];d1=ts[i+1]-ts[i]
            dp=-log_quat(b.inverted()@a)/d0; dn=log_quat(b.inverted()@c)/d1
            vel.append((dp*d1+dn*d0)/(d0+d1))
        vel.append(Vector((0.,0.,0.)))
        self.ts=tuple(ts); self.q=q; self.seg=[]
        for i,dt in enumerate(t2-t1 for t1,t2 in zip(ts,ts[1:])):
            self.seg.append((q[i],offset(q[i],vel[i]*dt/3),offset(q[i+1],-vel[i+1]*dt/3),q[i+1]))
    def at(self,t):
        if t<=self.ts[0]:return self.q[0].copy()
        if t>=self.ts[-1]:return self.q[-1].copy()
        i=next(i for i in range(len(self.seg)) if t<=self.ts[i+1]);u=(t-self.ts[i])/(self.ts[i+1]-self.ts[i])
        return bezier(*self.seg[i],u)

def direction(q,v,axis):
    return ((q@axis).normalized().rotation_difference(v.normalized())@q).normalized()

class ArmReturnTrack:
    def __init__(self,keys=KEYS,anchors=(START_Q,END_Q),hand_range=(9.08,10.56),wrist_soft=4.2):
        times=[x[0] for x in keys];start=[Quaternion(q).normalized() for q in anchors[0]];end=[Quaternion(q).normalized() for q in anchors[1]]
        # Aim at the real adjoining joint, not the visual display-bone +Y.
        # The native right-arm display axes happen to point the other way.
        au,av=[Quaternion(q).normalized().inverted()@Vector(v).normalized() for q,v in zip(START_Q,START_LINKS)]
        q0,q1=start[:2];out=[start];start_wrist=q1.inverted()@start[2];end_wrist=end[1].inverted()@end[2]
        for t,u,v,r in keys[1:-1]:
            u,v=Vector(u),Vector(v)
            q0=direction(q0,u,au);q1=direction(q1,v,av)
            flat0,flat1=direction(end[0],u,au),direction(end[1],v,av)
            # Cross-swing roll is relaxed while the upper arm turns in; swivel
            # continuously on each aim axis so the native Twist follows it.
            q_up=q0.slerp(hemi(q0,flat0),r*.86);q_lo=q1.slerp(hemi(q1,flat1),r*.88)
            h=sway(*hand_range,t);hand_offset=start_wrist.slerp(hemi(start_wrist,end_wrist),h)
            # Small local easing posture for a relaxed hand rather than a hinge.
            hand_offset=hand_offset@Quaternion((-.65,.10,.50),math.radians(wrist_soft*math.sin(math.pi*h)))
            out.append((q_up,q_lo,q_lo@hand_offset))
        out.append(end);self.track=[SphericalCubic(times,list(qs)) for qs in zip(*out)]
    def at(self,t):return [q.at(t) for q in self.track]

class ArmLiftTrack(ArmReturnTrack):
    def __init__(self):super().__init__(LIFT_KEYS,(LIFT_A,LIFT_B),(6.69,7.49),2.8)

"""Artist rails for Suzu's crown, fringe, side locks, high side ponytail and ahoge."""
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import math,sys,json,bpy
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
from phaseB_baseline import sources
from hair_mesh import ribbon, mesh, eased, mix

sc=bpy.context.scene; face,body,body_bvh,_=sources()
root=bpy.data.collections.new('SUZU_PHASE_B_HAIR');sc.collection.children.link(root)

def group(name):
    c=bpy.data.collections.new(name);root.children.link(c);return c

def sockets(n,p,normal=(0,-1,0)):
    if '_anchors' not in globals():global _anchors;_anchors=group('H90 · local prop seats')
    o=bpy.data.objects.new(n,None);_anchors.objects.link(o);o.location=p;o.empty_display_type='ARROWS';o.empty_display_size=.014;o.hide_render=True
    o.rotation_euler=Vector(normal).to_track_quat('Z','Y').to_euler();return o

C0=Vector((-.0038,.027,1.453)); N=112; J=38

def floor_angle(a):
    d=abs(math.degrees(math.atan2(math.sin(a),math.cos(a))))
    spans=((0,1.184),(25,1.196),(49,1.276),(67,1.415),(87,1.511),(98,1.585),(114,1.773),(145,1.929),(180,1.972))
    for (x,y),(u,v) in zip(spans,spans[1:]):
        if d<=u:return mix(y,v,eased(x,u,d))
    return spans[-1][1]

SWIRL=[(-174,14,-11,.0030),(-141,12,9,.0032),(-107,10,16,.00235),(-77,14,17,.0033),
       (-48,9,11,.0029),(-20,12,-5,.0028),(11,13,-10,.00265),(44,11,-9,.0035),
       (78,13,-17,.0035),(110,14,-14,.0025),(147,14,-5,.0030)]

def cap_point(a,t,inside=False):
    f=max(.0004,t);p=f**.93*floor_angle(a);r=math.sin(p);D1=Vector((r*math.sin(a),-r*math.cos(a),math.cos(p)))
    q,ng,_,_=body_bvh.ray_cast(C0+D1*.37,-D1,.52)
    if q is None:raise RuntimeError(('No approved scalp point',a,t))
    u=min(.93,t);az=math.degrees(a);layer=0.
    for th,w,s,k in SWIRL:
        d=(az-(th+s*(u**.77))+180)%360-180
        layer+=k*math.exp(-(d/w)**2)
    env=eased(.02,.28,t)*(1-.59*eased(.76,1.,t))
    rear=eased(.18,.93,-math.cos(a))
    forehead=eased(.52,.99,math.cos(a))*eased(.05,.24,t)*(1-eased(.58,.82,t))
    offset=.0161+.00085*math.cos(2*a-.30)*eased(.02,.65,t)-.0037*eased(.67,1.,t)+env*layer-.00705*rear*eased(.73,.99,t)-.00223*forehead
    if inside:offset-=.0021
    return q+D1*offset

def sculpted_crown():
    v=[];F=[];UV=[];edges=[]
    for inside in (False,True):
        pole=len(v); v.append(tuple(cap_point(0,0,inside)));UV.append((.5,0));start=len(v)
        for j in range(1,J+1):
            t=j/J
            for k in range(N):
                a=math.tau*k/N;v.append(tuple(cap_point(a,t,inside)));UV.append((k/N,t))
        for k in range(N):
            p=(pole,start+(k+1)%N,start+k);F.append(tuple(reversed(p)) if inside else p)
        for j in range(J-1):
            u=start+j*N
            for k in range(N):
                l=(k+1)%N;p=(u+k,u+l,u+N+l,u+N+k);F.append(tuple(reversed(p)) if inside else p)
        edges.append(start+(J-1)*N)
    for k in range(N):
        l=(k+1)%N;F.append((edges[0]+k,edges[0]+l,edges[1]+l,edges[1]+k))
    volume=0.
    for f in F:
        p=Vector(v[f[0]])
        for b,c in zip(f[1:-1],f[2:]):volume+=p.dot(Vector(v[b]).cross(Vector(v[c])))
    if volume<0:F=[tuple(reversed(f)) for f in F]
    o=mesh('Crown · sculpted whorl under-form',v,F,UV,cr,'crown',-.06)
    for p in o.data.polygons:
        u=[o.data.uv_layers.active.data[i].uv for i in p.loop_indices]
        if max(x.x for x in u)-min(x.x for x in u)>.60:
            for x in u:
                if x.x<.13:x.x+=1.
    return o

cr=group('H01 · Crown growth')
crown=sculpted_crown()
crown.data.calc_loop_triangles()
_cap_outside=BVHTree.FromPolygons([v.co.copy() for v in crown.data.vertices],[tuple(q.vertices) for q in crown.data.loop_triangles if max(q.vertices)<1+J*N],all_triangles=True)

def laid_rail(rows,amount=.86):
    smooth=[]
    for x,y,z,w,h,k in rows:
        p=Vector((x,y,z));q,n,_,_= _cap_outside.find_nearest(p)
        if q is not None and (p-q).dot(n)>.0032:
            blend=eased(1.519,1.582,z)*amount
            p=p.lerp(q+n*(.0025+.15*h),blend)
        h*=1.-.22*eased(1.534,1.582,z)
        smooth.append((*p,w,h,k))
    return smooth

def scalp_front_safe(t,u,v,p):
    # Fit only where real bare skin exists, preserving the clearance at the hairline.
    q,n,_,_=body_bvh.ray_cast(Vector((p.x,-.335,p.z)),Vector((0,1,0)),.54)
    if q is not None and q.y<.033 and p.y>q.y-.0020:p.y=q.y-.0020
    return p

bang=group('H02 · Seven main fringe ribbons')
AIR_MAIN=[
 ('Fringe 01 · centre falling sash',[
   (-.014,-.005,1.613,.004,.0015,-22),(-.030,-.046,1.610,.013,.0044,-15),(-.039,-.080,1.584,.020,.0048,-13),
   (-.037,-.098,1.552,.021,.0044,-7),(-.025,-.102,1.519,.017,.00355,1),(-.013,-.101,1.493,.012,.00275,13),
   (-.004,-.096,1.467,.008,.00192,19),(.006,-.090,1.447,.0043,.00105,24),(.0166,-.0854,1.4354,.00018,.00008,28)],.042),
 ('Fringe 02 · light inner tongue',[
   (.000,-.014,1.614,.0038,.0014,11),(.002,-.051,1.609,.011,.0037,14),(.004,-.084,1.586,.016,.0043,9),
   (.009,-.101,1.557,.017,.0042,3),(.008,-.101,1.528,.014,.0037,-6),(.011,-.100,1.500,.00875,.00265,-16),
   (.019,-.096,1.480,.0060,.00188,-21),(.023,-.094,1.464,.0034,.00105,-22),(.021,-.092,1.4514,.00018,.000065,-26)],.008),
 ('Fringe 03 · right wide temple fall',[
   (-.026,.007,1.609,.004,.0014,-18),(-.066,-.024,1.605,.015,.0037,-23),(-.091,-.055,1.577,.021,.0048,-24),
   (-.103,-.067,1.551,.024,.0049,-23),(-.112,-.071,1.525,.020,.0043,-26),(-.112,-.064,1.502,.014,.0030,-31),
   (-.104,-.057,1.482,.0065,.0021,-35),(-.097,-.054,1.468,.00029,.0001,-38)],.073),
 ('Fringe 04 · fine right inward turn',[
   (-.016,-.019,1.615,.003,.0014,-7),(-.039,-.052,1.609,.012,.0037,-8),(-.057,-.079,1.580,.017,.0044,-9),
   (-.065,-.087,1.550,.020,.0044,-4),(-.065,-.089,1.523,.016,.0032,5),(-.059,-.087,1.503,.0095,.0022,12),
   (-.069,-.077,1.486,.005,.0014,15),(-.082,-.063,1.471,.00018,.00007,28)],.012),
 ('Fringe 05 · blue-star host sweep',[
   (.015,.004,1.612,.0037,.00135,22),(.052,-.026,1.606,.018,.0038,26),(.079,-.056,1.580,.0245,.0048,27),
   (.090,-.075,1.548,.025,.0046,24),(.096,-.075,1.521,.023,.0043,23),(.099,-.070,1.497,.019,.0037,24),
   (.103,-.061,1.480,.010,.0025,23),(.111,-.052,1.468,.00024,.00009,23)],.037),
 ('Fringe 06 · left arched cheek window',[
   (.023,-.012,1.610,.0036,.00115,9),(.043,-.044,1.609,.013,.0034,11),(.061,-.074,1.582,.018,.0044,13),
   (.063,-.090,1.554,.019,.0043,14),(.055,-.095,1.524,.015,.0035,15),(.045,-.091,1.505,.009,.0027,16),
   (.056,-.084,1.490,.006,.0019,20),(.071,-.075,1.479,.0031,.0010,23),(.082,-.068,1.471,.00018,.000074,26)],.020),
 ('Fringe 07 · left hairline veil',[
   (.040,.031,1.607,.004,.0014,38),(.072,.009,1.599,.016,.0032,43),(.097,-.026,1.578,.020,.0041,37),
   (.110,-.049,1.553,.020,.0039,26),(.115,-.057,1.524,.019,.0033,25),(.119,-.056,1.497,.016,.0027,27),
   (.121,-.037,1.475,.0055,.0015,24),(.115,-.024,1.465,.0002,.000073,21)],.066),
]

def brad(t,p):return (math.copysign(min(.50,2.8*abs(p.x)),p.x),-.98,.15*(1-t))
for label,trace,phase in AIR_MAIN:ribbon(label,laid_rail(trace),brad,bang,'bang',phase,67,22,.70,.16,.19,scalp_front_safe)

air=group('H03 · Five airy fringe satellite wisps')
AIR=[
('Air 01 · outside right slender bow',[
 (-.047,-.036,1.600,.0014,.00036,-13),(-.092,-.065,1.573,.0049,.00118,-10),(-.123,-.064,1.535,.0052,.00122,-14),
 (-.137,-.051,1.501,.0042,.00107,-18),(-.140,-.035,1.468,.0025,.00086,-22),(-.135,-.025,1.444,.00012,.00006,-25)],-.027),
('Air 02 · centre fine divided point',[
 (-.024,-.085,1.575,.0017,.00044,-12),(-.020,-.103,1.549,.0031,.00083,-10),(-.017,-.112,1.520,.0037,.00118,-10),
 (-.012,-.109,1.493,.0042,.00104,-10),(-.013,-.104,1.474,.00365,.00083,-8),(-.017,-.098,1.458,.00215,.00064,-5),(-.013,-.093,1.4452,.00013,.00005,1)],.011),
('Air 03 · right under-turn',[
 (-.047,-.090,1.565,.0018,.00051,-10),(-.047,-.100,1.547,.0036,.00087,-12),(-.043,-.102,1.523,.0040,.00112,-8),
 (-.046,-.099,1.502,.0031,.0010,-9),(-.054,-.089,1.488,.00175,.00051,-14),(-.062,-.083,1.485,.00012,.00005,-17)],.003),
('Air 04 · above the left eyebrow',[
 (.036,-.079,1.571,.0016,.00059,24),(.033,-.098,1.547,.0034,.00091,20),(.034,-.107,1.524,.0038,.0011,17),
 (.031,-.108,1.505,.003,.00089,17),(.024,-.100,1.491,.0018,.00057,21),(.020,-.098,1.487,.00012,.00005,29)],.018),
('Air 05 · long outer left feather',[
 (.061,-.032,1.594,.0017,.0005,39),(.104,-.042,1.560,.0041,.00092,31),(.129,-.037,1.525,.0047,.00115,29),
 (.138,-.031,1.495,.0038,.0010,27),(.137,-.024,1.468,.00265,.00066,29),(.132,-.014,1.446,.00013,.00005,32)],-.031),
]
for label,trace,phase in AIR:ribbon(label,laid_rail(trace,.62),brad,air,'fine',phase,53,16,.69,.13,.22,scalp_front_safe)

temples=group('H04 · Three tapered face-framing layers per side')
TEMPLES=[
 ('frontal satin lock',[(.084,-.000,1.568,.005,.0014,-6),(.103,-.014,1.546,.013,.0036,-9),(.116,-.018,1.514,.020,.0043,-11),
    (.123,-.018,1.483,.018,.0046,-14),(.121,-.016,1.445,.018,.0047,-17),(.114,-.021,1.407,.018,.0047,-16),
    (.102,-.036,1.378,.018,.0045,-13),(.086,-.048,1.351,.014,.0035,-9),(.071,-.054,1.324,.0095,.0026,8),(.060,-.053,1.305,.0065,.00195,21),(.053,-.050,1.294,.0033,.00116,32),(.060,-.043,1.2875,.00021,.00008,41)],.075),
 ('short cheek turn',[(.102,-.017,1.536,.005,.0014,15),(.111,-.024,1.515,.011,.0025,16),(.111,-.019,1.482,.014,.0032,13),
    (.107,-.019,1.448,.014,.0032,9),(.103,-.023,1.419,.012,.0030,8),(.092,-.040,1.393,.011,.00265,7),
    (.081,-.056,1.375,.0076,.0020,9),(.067,-.061,1.360,.0046,.00134,14),(.060,-.059,1.352,.00017,.00007,23)],.019),
 ('ear-side underslip',[(.090,.023,1.555,.004,.0013,10),(.109,.012,1.531,.011,.0025,9),(.121,.009,1.491,.014,.0033,3),
    (.121,.010,1.449,.015,.0031,2),(.113,.007,1.409,.013,.0028,-9),(.106,-.002,1.373,.0115,.00235,-9),
    (.099,-.009,1.345,.009,.0018,-11),(.087,-.018,1.319,.0053,.00135,-15),(.076,-.027,1.308,.00013,.00006,-16)],-.019),
]
for h in (-1,1):
    # Mirror the skeleton of the design, then shift the root and stagger the tips visibly.
    for j,(label,trace,phase) in enumerate(TEMPLES):
        points=[]
        for i,(x,y,z,w,t,r) in enumerate(trace):
            u=i/(len(trace)-1);x+=(-.004*(u**2)+.002*math.sin(math.pi*u)) if h<0 else 0
            x+=.0022*math.exp(-((z-1.510)/.036)**2)
            z+=.0095*u*u if h<0 and j==0 else (-.007*u**2 if h>0 and j==1 else 0)
            y+=.004*u if h<0 and j==1 else 0
            points.append((h*x,y,z,w*(1+.075*math.sin(math.pi*u) if h<0 else 1.),t,r*h))
        def nh(t,p,h=h):return (.89*h,-.46,.13-.08*t)
        name=('L' if h>0 else 'R')+f' side {j+1:02} · '+label
        ribbon(name,points,nh,temples,'side',phase+(.046 if h<0 else 0),68,22,.68,.15,.26)

pony=group('H05 · Four silk leaves at the left high tie')

PO=[
('Pony 01 · dominant S plume',[
 (.1102,.0233,1.5275,.0040,.0021,-13),(.1218,.027,1.542,.0080,.0030,-14),(.138,.035,1.556,.0140,.0046,-15),
 (.156,.044,1.561,.0160,.0049,-1),(.174,.056,1.546,.0190,.0053,14),(.186,.070,1.514,.0210,.0056,29),
 (.188,.080,1.473,.0217,.0058,33),(.191,.086,1.432,.0240,.0056,32),(.205,.089,1.394,.0245,.0054,27),
 (.230,.095,1.363,.0224,.0048,19),(.252,.100,1.339,.0196,.0042,10),(.263,.104,1.317,.0158,.0037,-5),
 (.261,.104,1.292,.0103,.0025,-22),(.249,.101,1.270,.0047,.0011,-36),(.235,.094,1.257,.0002,.00007,-42)],.028),
('Pony 02 · long separated outer curve',[
 (.143,.040,1.556,.0032,.0015,7),(.162,.051,1.554,.0082,.0027,13),(.176,.061,1.536,.0119,.0033,23),
 (.193,.075,1.503,.0150,.0035,29),(.200,.083,1.466,.0147,.0037,36),(.209,.091,1.431,.0131,.0033,33),
 (.228,.098,1.399,.0120,.0030,22),(.254,.102,1.375,.0111,.0029,7),(.275,.104,1.355,.0099,.0025,-7),
 (.287,.105,1.334,.0077,.0021,-19),(.288,.107,1.309,.0047,.0015,-24),(.280,.109,1.292,.00015,.000057,-31)],-.058),
('Pony 03 · short underleaf countercurl',[
 (.127,.031,1.541,.0031,.0014,-23),(.145,.045,1.550,.008,.0027,-13),(.160,.057,1.535,.012,.0036,-5),
 (.165,.065,1.505,.0147,.0042,8),(.165,.072,1.464,.0149,.0044,15),(.173,.081,1.426,.0164,.0047,37),
 (.189,.089,1.397,.0146,.0041,39),(.211,.095,1.375,.0123,.0034,26),(.228,.098,1.364,.0087,.0024,7),
 (.242,.096,1.365,.0049,.0015,-6),(.250,.093,1.371,.00018,.000061,-15)],.078),
('Pony 04 · detached silver needle tail',[
 (.167,.055,1.543,.0012,.00044,-9),(.178,.067,1.521,.0040,.00111,-8),(.189,.077,1.491,.0052,.0016,-4),
 (.196,.083,1.457,.0061,.00183,3),(.205,.090,1.422,.0053,.0016,13),(.220,.095,1.399,.0046,.0015,22),
 (.248,.094,1.383,.0046,.0014,22),(.271,.092,1.366,.004,.0013,24),(.296,.097,1.351,.0025,.00082,21),
 (.309,.106,1.328,.00014,.000054,17)],-.074),
]
def npn(t,p):return (.63+.17*eased(.37,.86,t),-.80+.22*eased(.42,.85,t),.18-.11*t)
for i,(label,trace,phase) in enumerate(PO):
    path=[]
    for j,(x,y,z,w,h,k) in enumerate(trace):
        u=j/(len(trace)-1);f=eased(.10,.47,u);stretch=(.338,.455,.38,.265)[i]
        x+=(.0056 if i==1 else .0026 if i==3 else 0.)*f
        y+=(.0021 if i==2 else 0.)*f
        path.append((x,y,z,w*(1.+stretch*f),h*(1.+.071*f),k))
    ribbon(label,path,npn,pony,'pony',phase,82,24,.65,.15,.27)

fly=group('H06 · Rotated teardrop ahoge')
ribbon('Ahoge · crescent little feather',[
 (-.010,.008,1.613,.0015,.0013,-24),(-.019,.003,1.623,.0042,.0028,-22),(-.027,-.003,1.640,.0060,.0039,-11),
 (-.026,-.004,1.655,.0061,.0040,3),(-.017,-.003,1.671,.0055,.0036,12),(-.003,.001,1.679,.0043,.0028,19),
 (.014,.006,1.680,.0031,.0020,23),(.029,.011,1.675,.00165,.0011,24),(.039,.015,1.665,.00015,.00008,31)],
 lambda t,p:(.47-.32*t,-.77,.24),fly,'ahoge',.050,58,20,.82,.10,.16)

sockets('SUZU socket · high pony root',(.1102,.0233,1.5275),(.96,-.054,.27))
sockets('SUZU socket · star host design',(.098,-.073,1.498),(.44,-.90,.12))

if __name__=='__main__':
    output=Path(sys.argv[-1]).resolve();output.mkdir(parents=True,exist_ok=True);bpy.context.preferences.filepaths.save_version=0
    print('Hairs',[(c.name,len(c.objects)) for c in root.children]);bpy.ops.wm.save_as_mainfile(filepath=str(output/'front.blend'),compress=True)

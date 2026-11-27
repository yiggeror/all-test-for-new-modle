"""Suzu · Gate 1 / isolated head sculpt. Run: blender -b -P build_head.py -- [output_directory] [--preview]
Dimensions in metres. These are mesh patches with ring-aligned openings, not face decals.
"""
import bpy, math, os, sys, bisect, bmesh
from mathutils import Vector
from math import sin, cos, pi, exp, sqrt
from pathlib import Path
ARGS=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=Path(next((a for a in ARGS if not a.startswith('--')),Path(__file__).resolve().parent)); OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene
C=bpy.data.collections.new('SUZU_HEAD'); S.collection.children.link(C)
def section(name):
    global L
    L=bpy.data.collections.new(name); C.children.link(L)
def mat(name,v):
    m=bpy.data.materials.new(name); m.diffuse_color=(v,v,v,1); m.use_nodes=True; bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(v,v,v,1); bs.inputs['Roughness'].default_value=.86; bs.inputs['Specular IOR Level'].default_value=.18; return m
skin=mat('Clay porcelain · skin',.66); earshade=mat('Clay shallow fold',.55); hair=mat('Clay silver · hair masses',.46); edgehair=mat('Clay silver · underlayer',.414); lash=mat('Clay graphite · lashes',.069); brow=mat('Clay slate · brows',.245); white=mat('Clay chalk · sclera and reflections',.86); irisrim=mat('Clay iris rim',.12); iris=mat('Clay iris disk',.32); lightiris=mat('Clay iris caustic',.49); pupil=mat('Clay pupil',.065); lips=mat('Clay lip edges',.51); mouth=mat('Clay mouth opening',.23); metal=mat('Clay accent setting',.56); gem=mat('Clay star inset',.30); cloth=mat('Clay ribbon',.27)
def objmesh(name,vs,fs,m,smooth=True,weld=False):
    me=bpy.data.meshes.new(name); me.from_pydata(vs,[],fs); me.update(); ob=bpy.data.objects.new(name,me); L.objects.link(ob); me.materials.append(m)
    bm=bmesh.new(); bm.from_mesh(me)
    if weld: bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000002)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(me); bm.free(); me.update()
    for p in me.polygons:p.use_smooth=smooth
    return ob
def smooth(a,b,t):return a+(b-a)*t*t*(3-2*t)
def pch(X,Y,x):
    # Shape-preserving cubic Hermite interpolant through nonuniform sculpt stations.
    if x<=X[0]:return Y[0]
    if x>=X[-1]:return Y[-1]
    i=bisect.bisect_right(X,x)-1; h=X[i+1]-X[i]; s=(x-X[i])/h
    def slope(j):
        if j==0:return (Y[1]-Y[0])/(X[1]-X[0])
        if j==len(X)-1:return (Y[-1]-Y[-2])/(X[-1]-X[-2])
        a=(Y[j]-Y[j-1])/(X[j]-X[j-1]); b=(Y[j+1]-Y[j])/(X[j+1]-X[j]); h0=X[j]-X[j-1]; h1=X[j+1]-X[j]
        if a*b<=0:return 0
        w1=2*h1+h0; w2=h1+2*h0; return (w1+w2)/(w1/a+w2/b)
    return (2*s**3-3*s*s+1)*Y[i]+(s**3-2*s*s+s)*h*slope(i)+(-2*s**3+3*s*s)*Y[i+1]+(s**3-s*s)*h*slope(i+1)
def path(P,t):
    # Chord-weighted Catmull–Rom centerlines with continuous tangents through all sketched guide points.
    n=len(P);u=max(0,min(1,t))*(n-1); i=min(n-2,int(u));v=u-i;p0=P[max(0,i-1)];p1=P[i];p2=P[i+1];p3=P[min(n-1,i+2)];
    def chord(a,b):return max(1e-8, sum((a[j]-b[j])**2 for j in range(min(3,len(a))))**.25)
    d0=chord(p0,p1);d1=chord(p1,p2);d2=chord(p2,p3);q=[]
    for j in range(len(p1)):
        if j==3 or len(p1)==3 and j==2 and all(.0000<=r[2]<.08 for r in P):
            X=[n0/(n-1) for n0 in range(n)]; q.append(pch(X,[rr[j] for rr in P],t));continue
        m1=(p2[j]-p0[j])*d1/(d0+d1) if i>0 else p2[j]-p1[j];m2=(p3[j]-p1[j])*d1/(d1+d2) if i<n-2 else p2[j]-p1[j]
        q.append((2*v**3-3*v*v+1)*p1[j]+(v**3-2*v*v+v)*m1+(-2*v**3+3*v*v)*p2[j]+(v**3-v*v)*m2)
    return q
def interp(P,t):return pch([q[0] for q in P],[q[1] for q in P],t)
def boxfs(n,m,reverse=False):return [(i*m+j,(i+1)*m+j,(i+1)*m+j+1,i*m+j+1) for i in range(n-1) for j in range(m-1)]
def tube(name,P,width,material,sections=8,n=36):
    V=[]; F=[]; prev=None
    for i in range(n+1):
        t=i/n; p=Vector(path(P,t) if not callable(P) else P(t));eps=.0002
        fun=(lambda g: Vector(path(P,g))) if not callable(P) else (lambda g:Vector(P(g)))
        tangent=(fun(min(1,t+eps))-fun(max(0,t-eps))).normalized(); up=Vector((0,1,0))
        if abs(tangent.dot(up))>.93:up=Vector((0,0,1))
        side=tangent.cross(up).normalized(); other=tangent.cross(side).normalized()
        w=width(t) if callable(width) else width
        if not isinstance(w,tuple):w=(w,w)
        for j in range(sections):
            a=2*pi*j/sections; V.append(tuple(p+side*(cos(a)*w[0])+other*(sin(a)*w[1])))
        if i: 
            for j in range(sections):F.append(((i-1)*sections+j,i*sections+j,i*sections+(j+1)%sections,(i-1)*sections+(j+1)%sections))
    F+= [tuple(reversed(range(sections))),tuple(n*sections+j for j in range(sections))];return objmesh(name,V,F,material,weld=True)
def stacked_surface(name,front,back,nu,nv,material):
    V=[];F=[]
    for fun in (front,back):
        for i in range(nu+1):
            for j in range(nv+1): V.append(tuple(fun(i/nu,j/nv)))
    m=nv+1; off=(nu+1)*m; G=boxfs(nu+1,m); F+=G+[tuple(off+k for k in reversed(q)) for q in G]
    perimeter=[i*m for i in range(nu+1)]+[nu*m+j for j in range(1,m)]+[i*m+nv for i in reversed(range(nu))]+[j for j in reversed(range(1,nv))];
    for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):F.append((a,b,off+b,off+a))
    return objmesh(name,V,F,material,weld=True)
# Cranium and jaw sectional profiles; bridge, nasal tip, cupid's bow, chin pad are localized in x.
section('H01 · Face and ear cartilage')
# Fixed anatomical control sections. Columns: height, transverse radius, anterior and posterior extremities.
rows=[
    (1.317, 0.002, -0.092, -0.089),
    (1.32, 0.014760174, -0.095, -0.053),
    (1.325, 0.02688, -0.096, -0.015),
    (1.335, 0.044481086, -0.097, 0.008),
    (1.345, 0.056645139, -0.101, 0.021),
    (1.355, 0.066470205, -0.103, 0.031),
    (1.365, 0.074676843, -0.103, 0.042),
    (1.379, 0.083844319, -0.104, 0.06),
    (1.39, 0.091112076, -0.104, 0.071),
    (1.406, 0.098963251, -0.101, 0.081),
    (1.424, 0.104, -0.102, 0.089),
    (1.441, 0.106, -0.107, 0.092),
    (1.457, 0.108, -0.111, 0.095),
    (1.481, 0.11, -0.111, 0.099),
    (1.505, 0.108, -0.104, 0.099),
    (1.533, 0.1, -0.094, 0.095),
    (1.556, 0.08, -0.079, 0.08),
    (1.578, 0.054, -0.049, 0.06),
    (1.589, 0.025, -0.024, 0.03),
    (1.593, 0.002, 0.002, 0.007),
]
rz=[r[0] for r in rows]; rxs=[r[1] for r in rows]; rf=[r[2] for r in rows]; rb=[r[3] for r in rows]
def dims(z):return pch(rz,rxs,z),pch(rz,rf,z),pch(rz,rb,z)
# Height then nine anterior y-stations, from the centreline across nose, lids, cheek and temple.
# The profile, median lip/chin and ear guides share the scale of references/03_face_expressions_props.jpg.
face_u=[0,.09,.18,.27,.52,.84,1.15,1.39,pi/2]
profile=[
    (1.317, -0.0908, -0.09080088, -0.090803, -0.0908066, -0.0908224, -0.0908598, -0.090909, -0.090958, -0.091),
    (1.32, -0.0958, -0.095532446, -0.094997914, -0.094339228, -0.0923624, -0.0878533, -0.081937386, -0.076051057, -0.071),
    (1.325, -0.0997, -0.099248954, -0.098297942, -0.096987672, -0.092443902, -0.082182646, -0.068774029, -0.055451425, -0.044),
    (1.335, -0.1028, -0.102416979, -0.101520672, -0.100050611, -0.094102138, -0.081067271, -0.064173065, -0.047436053, -0.033),
    (1.346, -0.107924707, -0.107294103, -0.105940769, -0.104008114, -0.097435075, -0.083982078, -0.066744356, -0.049737162, -0.035),
    (1.352, -0.111002439, -0.11004638, -0.108074016, -0.105486142, -0.097763117, -0.082888685, -0.063907893, -0.045207359, -0.029),
    (1.357, -0.1111, -0.110342879, -0.108654211, -0.106132784, -0.097555897, -0.081789739, -0.061767161, -0.042072847, -0.025),
    (1.361, -0.115, -0.113464561, -0.110394641, -0.106671285, -0.097226729, -0.081026543, -0.060549254, -0.040440903, -0.023),
    (1.366, -0.115477843, -0.113945862, -0.110829117, -0.106926667, -0.096720533, -0.08008935, -0.059212165, -0.038761927, -0.021),
    (1.37, -0.1151793, -0.113738741, -0.110740118, -0.106829923, -0.096097991, -0.079113653, -0.057859741, -0.037063309, -0.019),
    (1.38, -0.116929083, -0.114518416, -0.110546192, -0.106351668, -0.094914846, -0.077759229, -0.056259091, -0.035205599, -0.017),
    (1.385, -0.1209, -0.116456762, -0.110526879, -0.105978511, -0.094073005, -0.076619519, -0.054801705, -0.033456066, -0.015),
    (1.39, -0.12666649, -0.118662854, -0.109703487, -0.105226975, -0.093125692, -0.07557584, -0.05375573, -0.032450315, -0.014),
    (1.395, -0.12362801, -0.116682332, -0.10872199, -0.104285545, -0.091624359, -0.0738341, -0.051898777, -0.03054808, -0.012),
    (1.399, -0.1177, -0.11317519, -0.107561613, -0.103408776, -0.090151677, -0.072084395, -0.050033584, -0.02865446, -0.01),
    (1.406, -0.112138809, -0.109616502, -0.105932602, -0.101936759, -0.087919115, -0.06976636, -0.048128712, -0.027345767, -0.009),
    (1.414, -0.108631397, -0.10701367, -0.104194602, -0.100136878, -0.085217168, -0.066576382, -0.045284473, -0.025197289, -0.007),
    (1.424, -0.106261413, -0.10555503, -0.103617385, -0.0995347, -0.083810533, -0.064457759, -0.043145291, -0.023364482, -0.005),
    (1.437, -0.1073, -0.106234577, -0.10391374, -0.09959444, -0.083170907, -0.063130853, -0.04153777, -0.021699521, -0.003),
    (1.45, -0.109, -0.108051414, -0.105811805, -0.101402962, -0.084532416, -0.063912942, -0.041681833, -0.021251593, -0.002),
    (1.47, -0.1104, -0.109799135, -0.108053369, -0.104301225, -0.089440687, -0.06825873, -0.043939589, -0.020958635, 0),
    (1.494, -0.1097, -0.109159818, -0.107743685, -0.10503578, -0.093769681, -0.072488036, -0.045856631, -0.019810485, 0.003),
    (1.516, -0.103, -0.1025248, -0.10138, -0.099436, -0.090904, -0.070708, -0.04414, -0.01768, 0.005),
    (1.54, -0.089, -0.0885732, -0.087545, -0.085799, -0.078136, -0.059997, -0.036135, -0.01237, 0.008),
    (1.557, -0.074, -0.0736304, -0.07274, -0.071228, -0.064592, -0.048884, -0.02822, -0.00764, 0.01),
    (1.575, -0.055, -0.0547008, -0.05398, -0.052756, -0.047384, -0.034668, -0.01794, -0.00128, 0.013),
    (1.588, -0.026, -0.0258504, -0.02549, -0.024878, -0.022192, -0.015834, -0.00747, 0.00086, 0.008),
    (1.593, 0.001, 0.0010088, 0.00103, 0.001066, 0.001224, 0.001598, 0.00209, 0.00258, 0.003),
]
xsprof=[b[0] for b in profile];rail=[[b[i] for b in profile] for i in range(1,10)]
def heada(a,z):
    w,f,b=dims(z); aa=abs(a);x=w*sin(a);ys=[pch(xsprof,rr,z) for rr in rail];
    if aa<=pi/2: y=pch(face_u,ys,aa)
    else:y=pch([pi/2,1.95,2.36,2.72,pi],[ys[-1],ys[-1]+(b-ys[-1])*.375,ys[-1]+(b-ys[-1])*.716,ys[-1]+(b-ys[-1])*.917,b],aa)
    return x,y,z
def facey(x,z):
    w=dims(z)[0];return heada(math.asin(max(-.99999,min(.99999,x/w))),z)[1]
ORAL_HALF=.0203
def smile_height(u):
    u=min(1.,abs(u)); return 1.3570+.00403*u*u+.00052*u**6
ai=.207;ao=.794
apos=[0,.09,.16,.22,.27,.34,.42,.52,.62,.72,.82,.92,1.02,1.12,1.23,1.35,1.47,pi/2,1.70,1.86,2.02,2.18,2.36,2.54,2.72,2.90,3.04,pi]
def boundaries(t):
    t=max(0,min(1,t));base=1.4187+.0066*t+.00035*sin(pi*t);return base-.0184*max(0,sin(pi*t))**.68,base+.02265*max(0,sin(pi*t))**.73
A=[-a for a in reversed(apos[1:-1])]+apos; nr=len(A)
Z=[1.317,1.319,1.3225,1.327,1.333,1.339,1.346,1.352,1.357,1.361,1.366,1.370,1.376,1.380,1.385,1.390,1.394,1.399,1.402,1.406,1.415,1.425,1.435,1.445,1.451,1.456,1.466,1.481,1.498,1.516,1.533,1.550,1.565,1.577,1.586,1.592]
V=[heada(a,z) for z in Z for a in A];F=[]
patches=[('mouth',-.52,.52,1.339,1.380),('eyeL',.16,1.02,1.394,1.456),('eyeR',-1.02,-.16,1.394,1.456)]
for i in range(len(Z)-1):
    for j in range(nr):
        k=(j+1)%nr;am=(A[j]+A[k])*.5;zm=(Z[i]+Z[i+1])*.5
        if k!=0 and any(g[1]<am<g[2] and g[3]<zm<g[4] for g in patches):continue
        F.append((i*nr+j,i*nr+k,(i+1)*nr+k,(i+1)*nr+j))
F+=[tuple(reversed(range(nr))),tuple((len(Z)-1)*nr+i for i in range(nr))]
# Explicit, continuous orbicularis oculi and orbicularis oris edge loops. Outer rail shares the cage's vertices;
# each successive ring moves anatomically toward the palpebral opening / vermilion, with a real return on the inside.
for nm,amin,amax,zlo,zhi in patches:
    xa=A.index(amin);xb=A.index(amax);za=Z.index(zlo);zb=Z.index(zhi);mid=(zhi+zlo)/2
    seq=[(j,za) for j in range(xa,xb+1)]+[(xb,i) for i in range(za+1,zb+1)]+[(j,zb) for j in reversed(range(xa,xb))]+[(xa,i) for i in reversed(range(za+1,zb))]
    current=[i*nr+j for j,i in seq]; angles=[]
    for j,i in seq:
        ax=A[j];zz=Z[i];sx=(ax-amin)/(amax-amin);sz=(zz-zlo)/(zhi-zlo)
        if i==za:ang=204+132*sx
        elif j==xb:ang=336+48*sz
        elif i==zb:ang=384+132*(1-sx)
        else:ang=516+48*(1-sz)
        angles.append(ang*pi/180)
    if nm.startswith('eye'):
        rings=[(.21,1.24,0),(.48,1.21,0),(.76,1.18,.0001),(1,1.13,-.00015),(1,1.065,-.0007),(1,1,-.0005),(1,.987,.0016)]
    else:rings=[(.30,1.72,0),(.67,1.50,0),(1,1.28,-.0002),(1,1.10,-.00045),(1,1.02,-.00055),(1,1.0,-.00034),(1,.96,.0022)]
    for k,(mix,radius,dy) in enumerate(rings):
        new=[]
        for p,ang,src in zip(seq,angles,[V[i*nr+j] for j,i in seq]):
            c=cos(ang);si=sin(ang);x0,y0,z0=src
            if nm.startswith('eye'):
                side=1 if nm=='eyeL' else -1;realc=c*side;t=(realc+1)*.5;lo,hi=boundaries(t);base=1.4187+.0066*t+.00035*sin(pi*t);edge=(hi if si>=0 else lo);z=base+(edge-base)*radius
                a=(ai+ao)*.5+(ao-ai)*.5*realc*radius;x=side*heada(a,z)[0]
            else:
                # Upper lip bow, lower lip pillow and continuous cheek ring; all share one deformable head object.
                sp=abs(si)**.86; ax=ORAL_HALF*radius*c; zc=smile_height(c)
                if k==0:hh=.0119 if si>0 else .0107
                elif k==1:hh=.0090 if si>0 else .0077
                elif k==2:hh=.0065 if si>0 else .0059
                elif k==3:hh=.0031 if si>0 else .0039
                elif k==4:hh=.00165 if si>0 else .00240
                elif k==5:hh=.00061
                else:hh=.00061
                z=zc+(1 if si>0 else -1)*hh*sp; x=ax
            x=(1-mix)*x0+mix*x;z=(1-mix)*z0+mix*z;y=facey(x,z)+dy
            new.append(len(V));V.append((x,y,z))
        for j in range(len(new)): jj=(j+1)%len(new);F.append((current[j],current[jj],new[jj],new[j]))
        current=new
# Remove unused internal lattice points before constructing the final mesh; all orbital/labial rings are true skin topology.
used=sorted(set(k for f in F for k in f));idx={k:i for i,k in enumerate(used)};facemesh=objmesh('Face · hand-sectioned profile / orbital and oral loops',[V[k] for k in used],[[idx[k] for k in f] for f in F],skin,weld=True)
# Relax only the bridge/inner cheek normal transition, retaining the hand-traced center profile and apertures.
me=facemesh.data;nb=[set() for _ in me.vertices]
for e in me.edges:
 a,b=e.vertices;nb[a].add(b);nb[b].add(a)
for itr in range(3):
 old=[v.co.y for v in me.vertices]
 for j,v in enumerate(me.vertices):
  x,z=abs(v.co.x),v.co.z
  if .005<x<.042 and 1.380<z<1.454 and v.co.y<-.083:
   wx=min(1,(x-.005)/.008,(.042-x)/.008,(z-1.380)/.009,(1.454-z)/.009)
   close=[k for k in nb[j] if (me.vertices[k].co-v.co).length<.014]
   if len(close)>2:v.co.y=old[j]+.245*wx*(sum(old[k] for k in close)/len(close)-old[j])
me.update();mod=facemesh.modifiers.new('Anatomical cage · two-level surface','SUBSURF');mod.levels=2;mod.render_levels=2
# Correct coarse-patch interpolation from the same sculpt sections: the limiting skin normal is the cross
# product of the tangible x/z surface derivatives, not normals transferred from a sphere or a painted mask.
# The true internal eyelid and lip return walls retain their own normals.
me.update();N=[]
for v in me.vertices:
 x,y,z=v.co; n=v.normal.copy();w=dims(z)[0]; rr=abs(x)/max(.001,w)
 if 1.319<z<1.565 and rr<.985 and y<=facey(x,z)+.0011 and n.y<-.15:
  dx=.0025;dz=.0023
  gx=(facey(x+dx,z)-facey(x-dx,z))/(2*dx);gz=(facey(x,z+dz)-facey(x,z-dz))/(2*dz);analytic=Vector((gx,-1,gz)).normalized();k=min(1,(.985-rr)/.09,(z-1.319)/.008,(1.565-z)/.012)*.94
  # Keep the small palpable lip cushion on both sides of the open seam and the actual lid margins.
  lipw=max(0,1-abs(z-smile_height(x/ORAL_HALF))/.004)*max(0,min(1,(.0235-abs(x))/.006));k*=1-.97*lipw
  n=n.lerp(analytic,k).normalized()
 N.append(tuple(n))
me.normals_split_custom_set_from_vertices(N);mod.use_custom_normals=True

# Ear pinna: custom elliptical helix, inner fossa and bifurcated antihelix towards tragus.
for h,side in [(-1,'R'),(1,'L')]:
    # Traced auricular rim in the side-plane (Y,Z), measured relative to the external meatus.
    # Tilted helix top sits posterior to the lower forward lobe; its inner edge disappears into the cheek.
    outline=[(-.011,.014),(-.009,.023),(-.003,.029),(.006,.032),(.014,.030),(.022,.023),(.025,.013),(.024,.003),(.018,-.007),(.012,-.014),(.006,-.021),(-.002,-.027),(-.008,-.028),(-.013,-.023),(-.0135,-.015),(-.011,-.008),(-.012,.000),(-.013,.007)]
    def ecurve(t):
        u=(t%1)*len(outline);i=int(u);g=u-i;n=len(outline);a,b,c,d=[outline[k%n] for k in (i-1,i,i+1,i+2)];return [(2*g**3-3*g*g+1)*b[k]+(g**3-2*g*g+g)*(c[k]-a[k])*.5+(-2*g**3+3*g*g)*c[k]+(g**3-g*g)*(d[k]-b[k])*.5 for k in (0,1)]
    def ep(t,r,height=0):
        ey,ez=ecurve(t);yy=.006+ey*r;zz=1.4037+ez*r; xx=.1005+.00385*r+.00335*(max(0,sin(pi*r))**1.1)+height+.170*ey*r+.014*ez*r
        return (h*xx,yy,zz)
    V=[];F=[];M=48;R=9
    for i in range(R+1):
        for j in range(M):V.append(ep(j/M,i/R))
    for i in range(R):
        for j in range(M):F.append((i*M+j,(i+1)*M+j,(i+1)*M+(j+1)%M,i*M+(j+1)%M))
    # A posterior root skirt dives into the side head volume; no floating unthickened plate.
    for k in range(2):
        for j in range(M):
            x,y,z=ep(j/M,(.975,.82)[k]);V.append((x-h*(.0016,.0090)[k],y,z))
        i=R+k
        for j in range(M):F.append((i*M+j,(i+1)*M+j,(i+1)*M+(j+1)%M,i*M+(j+1)%M))
    F.append(tuple((R+2)*M+j for j in range(M)));objmesh(side+' ear · traced concha and embedded root',V,F,skin,weld=True)
    vv=[];ff=[];n0=72;n1=9
    for ii in range(n0):
        t=ii/n0; ct=Vector(ep(t,.89,.00046));ta=(Vector(ep((t+.0002)%1,.89))-Vector(ep((t-.0002)%1,.89))).normalized();lv=Vector((h,0,0));axis=ta.cross(lv).normalized();bx=axis.cross(ta).normalized(); prominence=.25+.75*(.5+.5*cos(2*pi*(t-.31)))**.60
        for jj in range(n1):
            bb=2*pi*jj/n1;vv.append(ct+axis*(.00186*prominence*cos(bb))+bx*(.00142*prominence*sin(bb)))
    for ii in range(n0):
        for jj in range(n1):ff.append((ii*n1+jj,((ii+1)%n0)*n1+jj,((ii+1)%n0)*n1+(jj+1)%n1,ii*n1+(jj+1)%n1))
    objmesh(side+' ear · tapering oblique helix',vv,ff,skin)
    tube(side+' ear · curved antihelix',[(h*.1044,-.001,1.386),(h*.1062,.005,1.393),(h*.1082,.012,1.401),(h*.1080,.013,1.406),(h*.1068,.010,1.413),(h*.1048,.0012,1.417)],lambda t:.00025+.00118*sin(pi*t)**.68,skin,8,29)
    tube(side+' ear · tragus',[(h*.1030,-.005,1.390),(h*.1051,-.0055,1.397),(h*.1038,-.0068,1.402)],lambda t:.00020+.0013*sin(pi*t),skin,7,18)
section('H02 · Eyes / lashes / oral cavity')
# Independent curved eye windows, visible iris stroma and pupil; anatomy embedded behind the facial apertures.
def eye_point(h,t,v,depth=0):
    t=max(0,min(1,t)); v=max(0,min(1,v));a=ai+(ao-ai)*t;lo,hi=boundaries(t);z=lo+(hi-lo)*v;x,y,z=heada(a,z); bow=.00085*max(0,sin(pi*t)*sin(pi*v))**.72
    return (h*x,y-.00015-bow-depth,z)
def eye_depth(h,x,z):
    xx=abs(x);w=dims(z)[0];a=math.asin(min(.995,xx/w));t=max(.00001,min(.99999,(a-ai)/(ao-ai)));lo,hi=boundaries(t);v=(z-lo)/max(.0001,hi-lo);return eye_point(h,t,v)[1]
def ocular_disk(name,h,xc,zc,rx,rz,offset,material,rows=8,arc=48):
    # True cropped section of a shallow convex iris: the upper/lower rims extend into the physical aperture
    # instead of leaving scleral crescents. Interior strips follow the same surface and can be re-materialed.
    vs=[];fs=[];nu=44;nv=max(8,rows*2)
    for i in range(nu+1):
        u=2*i/nu-1; x=xc+rx*u; hline=rz*sqrt(max(0,1-u*u));a0=math.asin(min(.993,x/dims(zc)[0]));l,hiz=boundaries((a0-ai)/(ao-ai)); bot=max(zc-hline,l-.00010);top=min(zc+hline,hiz+.00009)
        if top<bot:top=bot
        for j in range(nv+1):
            v=j/nv;z=bot+(top-bot)*v; rr=min(1,u*u+((z-zc)/rz)**2);y=eye_depth(h,h*x,z)-offset-.00022*(1-rr);vs.append((h*x,y,z))
    return objmesh(name,vs,boxfs(nu+1,nv+1),material,weld=True)
for h,side in [(-1,'R'),(1,'L')]:
    stacked_surface(side+' eye · thick convex scleral shell',lambda t,v:eye_point(h,t,v),lambda t,v:(lambda q:(q[0],q[1]+.012,q[2]))(eye_point(h,t,v)),32,12,white)
    cx=.04693;cz=1.4255;ocular_disk(side+' iris · limbal bezel',h,cx,cz,.02145,.0250,.00023,irisrim);ocular_disk(side+' iris · stromal lens',h,cx,cz-.00025,.02025,.0237,.00068,iris);ocular_disk(side+' iris · dark pupil',h,cx,cz+.00045,.0091,.0123,.00115,pupil)
    ocular_disk(side+' eye · key catchlight',h,cx-h*.0064,cz+.0087,.0036,.0038,.00195,white,4,24);ocular_disk(side+' eye · fill catchlight',h,cx+h*.0087,cz-.0054,.0015,.0017,.00175,white,3,20)
    # Neutral clay iris insert with a recessed lower baffle and two asymmetric facets, all real geometry.
    def lower_gem(t,v):
        u=2*t-1; rx=.0188; x=cx+u*rx; cyc=cz-.00025; rz=.0228; ell=rz*sqrt(max(.00005,1-((x-cx)/.02025)**2));ang=math.asin(min(.995,x/dims(cyc)[0]));bot,top=boundaries((ang-ai)/(ao-ai));zbot=max(cyc-ell,bot+.00016);ztop=zbot+(.00020+.0059*(1-u*u))*(.81+.19*u);z=zbot+v*(ztop-zbot);y=eye_depth(h,h*x,z)-.00090-.00013*(1-v)*sin(pi*t);return (h*x,y,z)
    stacked_surface(side+' iris · lower inset light well',lower_gem,lambda t,v:(lambda q:(q[0],q[1]+.00024,q[2]))(lower_gem(t,v)),30,7,lightiris)
    for jj,(dx,dz,rad) in enumerate([(-.0102,-.0124,.00115),(.0129,.004,.0007)]):
        if jj==0 and h<0:dx=-.0110
        ocular_disk(side+' iris · tiny optical facet '+str(jj+1),h,cx+dx,cz+dz,rad,rad*.74,.00112,white,3,16)
    def eyelid(t,upper,kind):
        a=ai+(ao-ai)*t;lo,hi=boundaries(t);z=(hi if upper else lo)+kind*(.0021 if upper else -.0014)*max(0,sin(pi*t))**.7;x,y,z=heada(a,z);return h*x,y-.00049,z
    tube(side+' eyelid · upper tarsal fold',lambda t:eyelid(t,1,1),lambda t:(.00012+.00040*sin(pi*t)**.8,.00010+.00020*sin(pi*t)),skin,8,38)
    # A single filled, rising outer wing; no pinched V-joint at the canthus. Upper margin is thickest at the outer third.
    def lashrails(t):
        if t<.9:
            u=t/.90;a=ai+(ao-ai)*u;low,hi=boundaries(u);th=(.0010+.0031*sin(pi*u)**.80+.00155*u)*min(1,u/.13);outer=max(0,min(1,(u-.73)/.27));outer=outer*outer*(3-2*outer);pressure=.00454*sin(pi*u)**.81;zb=hi-.00052*min(1,u/.12)-pressure;zt=zb+th+.00405*outer+.21*pressure
        else:
            u=(t-.90)/.10;a=ao+.082*u;anchor=boundaries(1)[1];zb=anchor-.00050+.00755*u;zt=anchor-.00050+.00755*u+.00655*(1-u)**1.05
        return a,zb,zt
    def lashsurf(t,v,back=False):
        a,zb,zt=lashrails(t);z=zb+(zt-zb)*v;x,y,z=heada(a,z);return h*x,y-(.00083 if back else .0014+.00058*sin(pi*v)),z
    stacked_surface(side+' lashes · curved eyelash and fused wing',lambda t,v:lashsurf(t,v),lambda t,v:lashsurf(t,v,True),60,6,lash)
    for q in [0,1]:
        t0=.68+.08*q;p=Vector(lashsurf(t0,1));q1=Vector(lashsurf(t0+.025,1));tip=q1+Vector((h*(.0016+.0008*q),.0001,.0025+.00055*q));tube(side+' lash · tapered feather '+str(q+1),[tuple(p),tuple(q1),tuple(tip)],lambda t:.000085+.00082*(1-t)**1.24,lash,6,12)
    def water(t,v,back=False):
        a=ai+(ao-ai)*t;lo,hi=boundaries(t);w=.00063*sin(pi*t)**.8;z=lo+w*(.20-.96*v);x,y,z=heada(a,z);return h*x,y-(.00009 if back else .00027+.00015*sin(pi*v)),z
    stacked_surface(side+' lid · flush lower waterline',lambda t,v:water(t,v),lambda t,v:water(t,v,True),42,3,skin)
    tube(side+' lashes · outer lower sweep',lambda t:eyelid(.68+.32*t,0,0),lambda t:(.00006+.00027*sin(pi*t)**.7,.00007+.00013*sin(pi*t)),lash,7,22)
    for q in range(2):
        tt=.83+q*.08;p=Vector(eyelid(tt,0,0));tube(side+' lash · lower accent '+str(q+1),[tuple(p),tuple(p+Vector((h*.0014,.0002,-.00125)))],lambda t:.00016+.00043*(1-t),lash,6,6)
    def eyebrow(t,v,bb=False):
        x=.0228+.0560*t;z=1.4577+.0043*sin(pi*t**.88)-.00165*t;w=.00009+.00113*sin(pi*t)**.80;z+=(2*v-1)*w; return h*x,facey(h*x,z)-(.00055 if bb else .0017),z
    stacked_surface(side+' eyebrow · long feathered arch',lambda t,v:eyebrow(t,v),lambda t,v:eyebrow(t,v,True),28,4,brow)
# Calm closed smile, tiny mouth cavity behind the parted central seam, teeth inside only.
def oral(t,v):
    x=.0416*(t-.5);s=max(0,sin(pi*t));zc=smile_height(2*t-1);z=zc+(2*v-1)*(.00115*s+.00018);return x,facey(x,z)+.0012,z
stacked_surface('Oral cavity · recessed behind real labial opening',oral,lambda t,v:(lambda q:(q[0],q[1]+.0025,q[2]))(oral(t,v)),40,6,mouth)
tube('Oral · upper dental arch behind lips',[(x,facey(x,1.361)+.0065,1.362+.0007*(x/.013)**2) for x in [-.013,-.008,0,.008,.013]],lambda t:.0003+.00165*sin(pi*t)**.5,white,8,26)
section('H03 · Scalp and swept fringe')
# Shared cranial surface and long back fall. The rear is a continuous crown: nothing
# needs to intersect or hide a set of radial parting wedges at its summit.
HSTAT=[
 (.955,.185,.102,.053,.110),(.992,.210,.105,.058,.117),(1.050,.242,.100,.066,.121),
 (1.094,.250,.092,.076,.126),(1.137,.238,.085,.083,.128),(1.180,.210,.078,.091,.131),
 (1.226,.175,.067,.101,.134),(1.278,.147,.052,.116,.134),(1.332,.130,.037,.120,.132),
 (1.381,.122,.021,.127,.130),(1.428,.1205,.008,.132,.125),
 (1.470,.1205,.003,.128,.120),(1.503,.120,.004,.127,.119),
 (1.529,.120,.006,.121,.114),(1.548,.111,.008,.111,.107),
 (1.566,.095,.010,.096,.096),(1.579,.079,.012,.078,.079),
 (1.588,.061,.013,.062,.065),(1.594,.043,.014,.044,.047),
 (1.598,.025,.014,.027,.028),(1.5995,.012,.014,.014,.0145),(1.600,0,.014,0,0)]
_HZ=[r[0] for r in HSTAT]; _HV=[[r[k] for r in HSTAT] for k in (1,2,3,4)]
def ease(a,b,x):
    t=min(1,max(0,(x-a)/(b-a)));return t*t*(3-2*t)
def hd(z):return [pch(_HZ,rr,z) for rr in _HV]
def capq(a,z):
    rx,cy,rf,rb=hd(z);return Vector((rx*sin(a),cy-(rf if cos(a)>=0 else rb)*cos(a),z))
def hy(x,z):
    rx,cy,rf,rb=hd(z); u=x/max(1e-5,rx);return cy-rf*sqrt(max(.001,1-u*u))
def rad(a):return math.radians(a)
def outward_hair(a,z):
    p=capq(a,z); p1=capq(a+.002,z);p2=capq(a,z+.0001)
    return (p1-p).cross(p2-p).normalized()
# Closed cap and recessed lining on a single regular double shell. A single true
# pole per skin, periodic connectivity, and finite rounded perimeter. This avoids
# an exposed neckline seam when it is inspected from the chin or back.
FLOOR=[(0,1.512),(12,1.518),(20,1.522),(25,1.516),(31,1.502),(38,1.485),
       (48,1.468),(61,1.448),(70,1.443),(76,1.439),(83,1.434),(91,1.417),
       (97,1.394),(105,1.353),(109,1.312),(114,1.241),(120,1.181),
       (128,1.155),(139,1.128),(148,1.103),(156,1.115),
       (166,1.102),(174,1.111),(180,1.088)]
def hzfloor(a):
    az=abs(math.degrees(math.atan2(sin(a),cos(a))))
    return interp(FLOOR,az)+.014*ease(114,141,az)*(sin(a*.9)-.28)*sin(4.35*a-.61)

def r2_hair_cap():
    # Clip one elevation lattice against the authored lower silhouette.
    # Constant world-Z rows prevent a long oblique stair-step at the
    # nape when adjacent angular stations finish at different heights.
    num=160;maxz=1.600
    ad=2*pi/num;flo=[hzfloor(i*ad) for i in range(num)]
    zlevels=[maxz,1.59965,1.5987,1.5971,1.5949,1.592,1.589]+[1.585-i*.0037 for i in range(146)]
    uv=[];repo={};faces=[];borders={}
    def key(u,z):
        un=round(u%num,8)%num;zn=round(z,9)
        if abs(zn-maxz)<1e-8:un=0
        code=(un,zn)
        if code not in repo:
            repo[code]=len(uv);uv.append(code)
        return repo[code]
    def clip(y,xleft,xright,zh,zl):
        param=[(0.,zh),(0.,zl),(1.,zl),(1.,zh)];arr=[]
        for now,after in zip(param,param[1:]+param[:1]):
            f0=now[1]-(xleft+(xright-xleft)*now[0]);f1=after[1]-(xleft+(xright-xleft)*after[0])
            if f0>=-1e-11:arr.append(now)
            if (f0>1e-11 and f1<-1e-11) or (f1>1e-11 and f0<-1e-11):
                t=f0/(f0-f1);arr.append((now[0]+(after[0]-now[0])*t,now[1]+(after[1]-now[1])*t))
        return list(dict.fromkeys(key(y+a,z) for a,z in arr))
    for i in range(num):
        fl,fr=flo[i],flo[(i+1)%num]
        for zh,zl in zip(zlevels,zlevels[1:]):
            if zh<min(fl,fr):break
            q=clip(i,fl,fr,zh,zl)
            if len(q)<3:continue
            faces.extend((q[0],q[h],q[h+1]) for h in range(1,len(q)-1))
            for a,b in zip(q,q[1:]+q[:1]):
                cd=tuple(sorted((a,b)))
                if cd in borders:del borders[cd]
                else:borders[cd]=(a,b)
    n=len(uv);vv=[]
    for inner in (False,True):
        for u,z in uv:
            if z>=maxz-1e-8:
                vv.append((0,.014,1.5976 if inner else maxz));continue
            a=u*ad;q=found_surface(a,z)
            if inner:
                degree=abs(math.degrees(math.atan2(sin(a),cos(a))))
                shell=ease(93,103,degree)*ease(1.455,1.398,z)
                q.x*=1-.034*(1-shell);q.y=.014+(q.y-.014)*(1-.032*(1-shell))
                q.z-=.0024*(1-shell)
                d=z-hzfloor(a);q.y-=shell*(.00102+.0028*ease(.004,.024,d))
            vv.append(tuple(q))
    fs=faces+[tuple(n+k for k in reversed(q)) for q in faces]
    fs.extend((b,a,n+a,n+b) for a,b in borders.values())
    return objmesh('Hair foundation · closed crown and recessed soft lining',vv,fs,hair)
# Royalty-free handmade topology: a finite closed cross-section at every
# station. No thresholds, post-cut patch welding, edge collapse or doubled
# coincident sidewalls. Real tips have small rounded endcaps.
def closed_hair_ribbon(name,fn,ma=hair,steps=54,ring=24):
    verts=[tuple(fn(i/steps,cos(2*pi*k/ring),sin(2*pi*k/ring))) for i in range(steps+1) for k in range(ring)]
    faces=[];half=ring//2
    def idx(i,k,side):
        return i*ring+(k if side==0 else (-k)%ring)
    # The two sheets use identical triangle diagonals in cross-section
    # coordinates. Blender cannot fold a microscopic paper tip by choosing
    # different diagonals on the two sides of a slightly non-planar quad.
    for side in (0,1):
        for i in range(steps):
            for k in range(half):
                a=idx(i,k,side);b=idx(i+1,k,side);c=idx(i+1,k+1,side);d=idx(i,k+1,side)
                ff=[(a,b,c),(a,c,d)]
                faces.extend(ff if side==0 else [tuple(reversed(f)) for f in ff])
    for i in (0,steps):
        for k in range(half):
            f=tuple(dict.fromkeys([idx(i,k,0),idx(i,k+1,0),idx(i,k+1,1),idx(i,k,1)]))
            faces.append(f if i==0 else tuple(reversed(f)))
    return objmesh(name,verts,faces,ma)
# Flat broad four-sided sections, with close rounded edge rails. The profile
# crest is only millimetres high and is deliberately displaced off the medial axis.
def hs_loft(name,fn,ma,n=44,m=12):
    return stacked_surface(name,lambda t,v:fn(t,v,False),lambda t,v:fn(t,v,True),n,m,ma)
def blade(name,P,normal,material=hair,depth=.0033,n=42):
    def fn(t,v,b):
        d=path(P,t);p=Vector(d[:3]);w=max(.00004,d[3]);te=Vector(path(P,min(1,t+.0003))[:3])-Vector(path(P,max(0,t-.0003))[:3]);te.normalize()
        no=Vector(normal(t) if callable(normal) else normal).normalized()
        across=te.cross(no).normalized();no=across.cross(te).normalized();s=2*v-1
        # Curved paper section with rounded off-centre ridge, not a prism/cylinder.
        fac=min(1,w/.009); h=depth*fac
        top=h*((1-s*s)*(.70+.24*s)+.23*exp(-((s-.22)/.37)**2)*(1-s*s))
        if b:top=-h*(.16+.05*(1-s*s))-.00018*fac
        pt=p+across*(w*s)
        # Every upper hime rail starts on the *same* scalp manifold. A gradual
        # radial lift replaces the old pointed stubs where the solid blades
        # had previously emerged through its round silhouette.
        if 'temple · ' in name and 'fine lifted' not in name:
            rx,cy,rf,rb=hd(pt.z);th=math.atan2(pt.x/max(.004,rx),(cy-pt.y)/max(.004,rf))
            anchor=capq(th,pt.z);nh=outward_hair(th,pt.z)
            weight=ease(1.476,1.550,pt.z)
            if weight:
                lift=(.00022+.00165*ease(1.585,1.495,pt.z)) * (.67 if 'underslip' in name else 1)
                pt=pt.lerp(anchor+nh*lift,weight)
        return pt+no*top
    return hs_loft(name,fn,material,n,12)
# The outer fringe follows traced left and right contour rails in frontal
# projection. The unequal ledges at the points keep the brows visible through
# two inverted-V openings. Only layer order, not an artificial root groove,
# determines the overlaps.
def fringe(name,rails,layer,ridge=.00155):
    # Resolve each silhouette rail by true height first. The projected X
    # widths can never cross, so the thin bends are safe on underside angles.
    R1=sorted((row[2],row[0]) for row in rails);R2=sorted((row[3],row[1]) for row in rails)
    zs0,xs0=zip(*R1);zs1,xs1=zip(*R2)
    zz=max(zs0[0],zs1[0]);zt=min(zs0[-1],zs1[-1])
    def surf(t,v,h):
        z=zt+(zz-zt)*t
        x0=pch(zs0,xs0,z);x1=pch(zs1,xs1,z)
        w=max(.000095,.5*(x1-x0));x=.5*(x0+x1)+v*w
        reveal=ease(0,.28,t);thick=min(1,w/.007)
        y=hy(x,z)-(.00011+reveal*layer)
        roof=(.000072+ridge*reveal*thick*(.88+.20*v))*max(0,h)**1.18
        back=(.000056+.00050*thick)*min(0,h)
        return x,y-roof-back,z
    return closed_hair_ribbon(name,surf,hair,58,22)
# The central skirt, its curled inner overlap, and the diagonally falling sides.
fringe('Fringe 01 · central petal',[
(-.004,-.002,1.588,1.588),(-.022,.010,1.572,1.575),
(-.036,.022,1.549,1.551),(-.040,.026,1.519,1.522),
(-.041,.026,1.489,1.495),(-.036,.022,1.463,1.474),
(-.025,.015,1.449,1.456),(-.003,.0135,1.438,1.440),
(.0184,.0186,1.4290,1.4290)],.00155,.00155)
fringe('Fringe 02 · veil folding over centre',[
(-.007,-.003,1.587,1.589),(-.012,.014,1.573,1.572),
(-.014,.034,1.550,1.548),(-.012,.0395,1.528,1.524),
(-.008,.0422,1.511,1.506),(0,.0375,1.493,1.484),
(.012,.029,1.478,1.463),(.022,.0240,1.469,1.457),
(.017,.0172,1.445,1.445)],.0042,.00126)
fringe('Fringe 03 · left lifted diagonal',[
(.001,.004,1.588,1.587),(.015,.033,1.578,1.572),
(.028,.051,1.563,1.552),(.034,.065,1.545,1.527),
(.038,.077,1.520,1.504),(.043,.086,1.492,1.477),
(.050,.085,1.480,1.463),(.062,.086,1.463,1.449),
(.073,.085,1.449,1.441),(.084,.0842,1.434,1.434)],.00095,.00135)
fringe('Fringe 04 · right airy diagonal',[
(-.008,-.005,1.587,1.588),(-.033,-.018,1.573,1.578),
(-.054,-.026,1.555,1.562),(-.069,-.034,1.530,1.544),
(-.072,-.039,1.502,1.522),(-.076,-.042,1.482,1.498),
(-.078,-.050,1.462,1.480),(-.078,-.060,1.449,1.460),
(-.076,-.0758,1.435,1.435)],.00148,.0017)
fringe('Fringe 05 · inner kiss taper',[
(-.032,-.027,1.547,1.552),(-.040,-.033,1.522,1.523),
(-.040,-.031,1.495,1.494),(-.037,-.026,1.468,1.467),(-.030,-.021,1.446,1.444),
(-.016,-.0159,1.437,1.437)],.00325,.00061)
# A few irregular secondary slivers, laid at different angles and lengths;
# the main inverse-V eyebrow windows and the star's temple patch stay open.
fringe('Fringe 06 · right first sweep fragment',[
(-.022,-.019,1.580,1.582),(-.042,-.035,1.567,1.572),
(-.058,-.051,1.550,1.552),(-.066,-.056,1.526,1.534),
(-.072,-.064,1.504,1.517),(-.073,-.066,1.484,1.497),
(-.072,-.0718,1.470,1.470)],.00415,.00102)
fringe('Fringe 07 · left airy crossing fragment',[
(.031,.033,1.568,1.569),(.040,.048,1.555,1.558),
(.047,.056,1.537,1.539),(.051,.063,1.515,1.519),
(.057,.066,1.492,1.497),(.063,.069,1.474,1.480),
(.072,.0722,1.461,1.461)],.0032,.00094)
fringe('Fringe 08 · offset centre sliver',[
(-.007,-.004,1.578,1.578),(-.015,-.011,1.563,1.566),
(-.017,-.010,1.540,1.546),(-.015,-.006,1.518,1.526),
(-.010,-.004,1.501,1.507),(-.002,.0015,1.489,1.494),
(.007,.0072,1.482,1.482)],.0060,.0007)
fringe('Fringe 09 · left sweep beneath star',[
(.047,.050,1.555,1.555),(.061,.070,1.541,1.543),
(.074,.081,1.518,1.522),(.077,.085,1.497,1.504),
(.079,.084,1.476,1.483),(.083,.0832,1.459,1.459)],.00405,.00083)
section('H04 · Back waterfall / face framing')
# The nape turns smoothly into a soft negative-space drape. These measured
# atlas rails give room behind the fitted collar, shoulder and sleeve.
# z, half width, side y, centre y (all in metres).
FALL_RAIL=[
(.974,.184,.119,.141),(1.003,.221,.116,.144),(1.040,.244,.111,.145),
(1.080,.253,.103,.150),(1.113,.250,.097,.155),(1.150,.230,.089,.160),
(1.190,.207,.084,.166),(1.226,.179,.079,.168),(1.250,.160,.076,.170),
(1.276,.147,.072,.167),(1.312,.135,.064,.158),(1.352,.126,.052,.151),
(1.390,.123,.040,.141),(1.421,.123,.037,.133),(1.450,.122,.030,.131),
(1.480,.117,.026,.125),(1.520,.114,.021,.118),(1.550,.101,.020,.112)]
_fwz=[r[0] for r in FALL_RAIL];_fsc=[[r[k] for r in FALL_RAIL] for k in (1,2,3)]
def mantle_at(u,z):
    w,ys,ym=[pch(_fwz,k,z) for k in _fsc]
    wave=ease(1.45,1.100,z)
    xx=w*u + .0039*sin(2*pi*(z-1.0)+u*.9)*wave
    # The steep sides roll away from the shoulder, not onto its fabric.
    depth=(1.048-sqrt(u*u+.0025)**1.67)
    if depth<0:depth=.285*math.expm1(depth/.285)
    y=ys+(ym-ys)*depth+.0024*sin(pi*u*(1.18+.22*wave))*wave
    if z>1.403:
        wr,cy,rf,rb=hd(z);s=max(-.975,min(.975,xx/max(wr,.001)))
        capy=cy+rb*sqrt(max(.001,1-s*s))
        f=ease(1.403,1.516,z)
        y=y*(1-f)+(capy-.0041)*f
    return Vector((xx,y,z))
def found_surface(a,z):
    # A single smooth drape interior runs down from the closed crown. Small
    # tapered tides at the free hem are hidden between separate longer leaves.
    degree=abs(math.degrees(math.atan2(sin(a),cos(a))))
    p=capq(a,z);f=ease(93,103,degree)*ease(1.46,1.355,z)
    if f:
        u=(sin(a)/sin(rad(105)))*(.941-.203*ease(1.418,1.165,z))
        q=mantle_at(u,z);q.y+=-.0056+.0049*ease(1.37,1.28,z)
        q.y+=.00165*ease(1.39,1.17,z)*(.38*cos(16.5*u+7.7*z)+.62*cos(10.4*u-.73-14.8*z))
        p=p.lerp(q,f)
    return p
r2_hair_cap()
# Swept crown petals. Gentle scallop crests rise and fade into one another;
# four end in an earlier overlapping tier and five spill towards the nape.
def crown_petal(name,rows,j):
    zs=[p[0] for p in rows];az=[p[1] for p in rows];ww=[p[2] for p in rows]
    # Crownward anchors continue to the summit in a gentle swept arc. The
    # first cool bright seams are fully modeled and appear near z=1.59.
    rootZ=[1.5970,1.5979,1.5973,1.5983,1.5982,1.5978,1.5975,1.598,1.5968][j]
    bend=[28,11,17,15,2,-19,-28,-24,-9][j]
    zs.append(rootZ);az.append(az[-1]-bend);ww[-1]=[5.6,7.8,7.4,8.1,9.0,8.3,7.6,7.2,5.3][j];ww.append(.13)
    def fn(t,v,h):
        z=zs[-1]+(zs[0]-zs[-1])*t
        a=rad(pch(zs,az,z)+v*pch(zs,ww,z));p=found_surface(a,z)
        hdir=found_surface(a+.001,z)-found_surface(a-.001,z)
        up=found_surface(a,z+.00015)-found_surface(a,z-.00015)
        n=hdir.cross(up).normalized()
        aTop=ease(.012,.152,t);aEnd=1-ease(.81,1,t);f=aTop*aEnd
        # Root is integrated under the crown; paper margins kiss the cap,
        # while the silk ridge catches enough light to show at high angle.
        lift=-.00048+.00149*f+.00098*v*f*((-1)**j)-.00025*t
        if h>=0:lift+=round_petal[j]*h**1.15*f*(.88+.24*v)+.00008*h
        else:lift+=(.00112*f+.00008)*h
        if lift>0 and n.z>.1:lift=min(lift,(1.59988-z)/n.z)
        return p+n*lift
    return closed_hair_ribbon(name,fn,hair,47,20)
# Each rail is independently posed. The uncommon root staggering avoids a
# second regular part or spiking the skull silhouette.
round_petal=[.0036,.0029,.0041,.0031,.0040,.0028,.0040,.0031,.0035]
crown_stations=[
 [(1.427,88,.20),(1.456,84,6.2),(1.498,79,12),(1.544,60,12.6),(1.572,38,6.6),(1.582,27,.13)],
 [(1.402,114,.15),(1.439,111,9),(1.492,108,15.8),(1.542,104,15.3),(1.567,81,7.7),(1.584,59,.15)],
 [(1.405,134,.20),(1.456,128,10.0),(1.495,126,13),(1.542,129,14.5),(1.572,111,8.1),(1.589,95,.12)],
 [(1.386,154,.18),(1.438,150,12.0),(1.497,149,15.2),(1.549,146,16.8),(1.574,140,9.2),(1.592,131,.13)],
 [(1.388,180,.15),(1.443,175,10.2),(1.495,176,17.2),(1.548,175,17.7),(1.581,174,10.4),(1.592,173,.14)],
 [(1.399,206,.14),(1.439,201,10.5),(1.490,200,14.5),(1.541,201,16.5),(1.573,207,10.0),(1.590,220,.16)],
 [(1.388,223,.20),(1.436,226,11.3),(1.491,225,15.1),(1.539,228,17.5),(1.566,239,9.1),(1.585,258,.14)],
 [(1.405,245,.18),(1.451,249,12.0),(1.494,250,16),(1.543,255,16),(1.571,272,9),(1.584,291,.13)],
 [(1.432,268,.14),(1.464,278,7.2),(1.502,282,12),(1.544,287,12.8),(1.572,313,6.5),(1.582,332,.12)]
]
for j,rails in enumerate(crown_stations):crown_petal('Crown sweep · sculpted overlapping petal %02d'%(j+1),rails,j)
# Thirteen individual windswept leaves, not subdivided sectors of a fan.
# Each X rail is laid out in real world height against the FRONT and BACK
# silhouettes. The outside pairs stand free of the sleeves with actual
# negative-space windows. Their root heights gradually stagger into the crown.
LONG_STATIONS=[
 # z | lateral centre | cross-section half width | backward standoff
 [(1.078,-.249,.00048,.021),(1.097,-.269,.0045,.020),(1.124,-.284,.0075,.019),
  (1.151,-.279,.0092,.017),(1.179,-.245,.010,.013),(1.210,-.210,.0109,.018),
  (1.249,-.174,.010,.018),(1.301,-.148,.0101,.010),(1.365,-.127,.0092,.007),
  (1.428,-.109,.0080,.004),(1.494,-.098,.0055,.003),(1.546,-.068,.0033,-.004),(1.564,-.050,.00048,-.009)],
 [(1.047,-.225,.00044,.030),(1.066,-.244,.0048,.031),(1.089,-.263,.011,.035),
  (1.119,-.263,.014,.034),(1.154,-.239,.016,.021),(1.196,-.207,.0165,.017),
  (1.247,-.168,.015,.016),(1.303,-.141,.014,.015),(1.365,-.116,.0124,.007),
  (1.423,-.104,.011,.009),(1.493,-.090,.007,.004),(1.543,-.071,.0035,-.002),(1.571,-.059,.0005,-.009)],
 [(1.029,-.174,.00048,.027),(1.048,-.194,.0061,.021),(1.074,-.215,.0135,.022),
  (1.107,-.223,.0193,.025),(1.148,-.204,.0208,.021),(1.188,-.176,.0207,.019),
  (1.236,-.152,.0161,.010),(1.285,-.130,.0147,.009),(1.341,-.112,.0133,.011),
  (1.397,-.101,.0118,.008),(1.456,-.091,.0106,.005),(1.524,-.074,.0065,.002),
  (1.551,-.058,.00050,-.007)],
 [(1.011,-.126,.00043,.026),(1.029,-.144,.0057,.020),(1.055,-.160,.013,.018),
  (1.089,-.170,.0201,.025),(1.131,-.159,.022,.026),(1.178,-.143,.0219,.023),
  (1.224,-.126,.019,.021),(1.276,-.108,.0174,.015),(1.333,-.095,.0154,.016),
  (1.392,-.087,.0144,.016),(1.455,-.075,.0126,.011),(1.522,-.064,.0071,.007),
  (1.575,-.038,.00051,-.008)],
 [(.998,-.077,.00043,.016),(1.018,-.099,.0062,.016),(1.047,-.111,.014,.021),
  (1.081,-.115,.020,.025),(1.130,-.106,.0227,.026),(1.177,-.098,.0211,.029),
  (1.226,-.093,.0192,.022),(1.281,-.080,.0168,.016),(1.339,-.074,.0139,.014),
  (1.402,-.064,.012,.012),(1.463,-.062,.013,.008),(1.531,-.051,.0086,.005),
  (1.573,-.029,.00056,-.008)],
 [(.989,-.018,.00046,.024),(1.009,-.040,.0050,.023),(1.034,-.060,.0123,.025),
  (1.067,-.064,.0191,.030),(1.109,-.057,.0222,.033),(1.154,-.056,.0216,.033),
  (1.201,-.053,.0190,.028),(1.251,-.052,.0185,.026),(1.309,-.051,.0162,.020),
  (1.367,-.048,.0140,.017),(1.428,-.043,.0133,.016),(1.493,-.038,.0104,.007),
  (1.548,-.024,.0052,-.001),(1.577,-.016,.00051,-.009)],
 [(.982,.005,.00045,.018),(1.002,.028,.0058,.017),(1.030,.042,.0129,.019),
  (1.068,.043,.0206,.028),(1.111,.033,.0253,.032),(1.160,.031,.0217,.031),
  (1.207,.028,.0195,.031),(1.256,.018,.0165,.022),(1.310,.016,.0175,.019),
  (1.367,.009,.0158,.015),(1.429,.012,.0140,.013),(1.495,.009,.0127,.0057),
  (1.551,.003,.0063,-.001),(1.580,-.007,.00045,-.009)],
 [(1.000,.063,.00044,.026),(1.019,.087,.0055,.021),(1.040,.102,.0108,.021),
  (1.068,.111,.0174,.028),(1.111,.098,.0226,.038),(1.159,.086,.0222,.035),
  (1.204,.083,.0207,.030),(1.255,.070,.0166,.024),(1.311,.062,.0152,.022),
  (1.370,.052,.0154,.021),(1.428,.045,.0138,.015),(1.484,.043,.0112,.0075),
  (1.542,.026,.0064,.0012),(1.577,.011,.00049,-.008)],
 [(1.012,.114,.00054,.023),(1.031,.139,.0066,.022),(1.056,.153,.0138,.024),
  (1.089,.158,.0224,.031),(1.132,.152,.0232,.031),(1.176,.134,.0203,.029),
  (1.227,.116,.0185,.028),(1.278,.105,.0162,.022),(1.337,.091,.0139,.017),
  (1.398,.082,.0125,.015),(1.457,.075,.0118,.010),(1.519,.066,.0065,.005),
  (1.575,.037,.00054,-.008)],
 [(1.032,.165,.00046,.024),(1.048,.188,.0055,.019),(1.073,.206,.0130,.023),
  (1.106,.211,.0184,.026),(1.149,.198,.0211,.026),(1.193,.171,.0194,.023),
  (1.242,.147,.0178,.019),(1.294,.131,.0143,.016),(1.351,.117,.0140,.015),
  (1.413,.098,.0128,.012),(1.473,.084,.011,.009),(1.533,.070,.0068,.002),
  (1.561,.052,.00055,-.007)],
 [(1.046,.208,.00045,.030),(1.066,.233,.0062,.030),(1.092,.247,.0127,.029),
  (1.125,.249,.0186,.023),(1.168,.234,.0185,.016),(1.210,.201,.0175,.013),
  (1.257,.164,.0156,.014),(1.310,.146,.0134,.013),(1.366,.128,.0124,.010),
  (1.425,.113,.010,.008),(1.482,.097,.0087,.007),(1.535,.076,.0059,.002),
  (1.558,.060,.00048,-.008)],
 [(1.061,.245,.00043,.025),(1.079,.268,.0055,.025),(1.104,.282,.0099,.022),
  (1.135,.281,.0131,.019),(1.169,.251,.0129,.017),(1.206,.213,.0134,.016),
  (1.251,.174,.0126,.016),(1.301,.152,.0121,.016),(1.363,.130,.0104,.011),
  (1.422,.113,.0092,.009),(1.480,.100,.008,.007),(1.535,.071,.0045,-.001),
  (1.554,.056,.00059,-.009)],
 [(1.102,.276,.00047,.022),(1.119,.294,.0044,.020),(1.144,.295,.0068,.019),
  (1.170,.280,.0088,.021),(1.194,.251,.0087,.020),(1.225,.219,.0108,.018),
  (1.264,.178,.0099,.015),(1.315,.150,.0091,.012),(1.371,.130,.0102,.011),
  (1.428,.115,.0091,.008),(1.487,.101,.0054,.009),(1.540,.072,.0041,-.003),
  (1.570,.055,.00047,-.008)]
]
def r2_long_leaf(j,rows):
    zs=[p[0] for p in rows];X=[p[1] for p in rows];W=[p[2] for p in rows];Y=[p[3] for p in rows]
    deep=[.0023,.0037,.0042,.0045,.0049,.0045,.0052,.0045,.0044,.0043,.0040,.0036,.0026]
    def fn(t,v,h):
        z=zs[-1]+(zs[0]-zs[-1])*t
        x=pch(zs,X,z);w=pch(zs,W,z);wide=pch(_fwz,_fsc[0],z)
        x+=.0017*sin(8.9*t+j*.51)*ease(.13,.75,t)*(1-ease(.93,1,t))
        imbr=ease(1.500,1.282,z)*(1-ease(1.146,1.029,z))
        if j==4:x+=.0062*imbr
        if j==5:x+=.0208*imbr
        if j==6:x-=.0108*imbr
        if j==7:x-=.0102*imbr
        if j==8:x-=.0041*imbr
        if j in (5,6):w+=.0017*imbr
        u=(x+w*v)/wide
        y=mantle_at(u,z).y+pch(zs,Y,z)
        f=min(1,w/.011);tip=ease(zs[0]+.068,zs[0],z)
        # Narrow rounded ridge, waning gracefully at the arched lip.
        roof=(.00008+deep[j]*f*(.82+.19*v)*(.61+.39*ease(.14,.35,t)))*max(0,h)**1.25
        sole=(.000075+.00148*f)*min(0,h)
        roll=(.0017*sin(4.1*pi*t+.91*j)*v+.0012*sin(2.7*pi*t+j*.48))*ease(.17,.67,t)
        hide=ease(.20,.025,t)*.0048
        y+=roof+sole+roll-hide+v*.0013*f-.0067*tip**2.2
        return x+w*v,y,z
    return closed_hair_ribbon('Waterfall · airy separate sweep %02d'%(j+1),fn,hair,76,22)
for j,rs in enumerate(LONG_STATIONS):r2_long_leaf(j,rs)
# The anterior cheek petal and the long temple fall have a genuinely shared
# front-to-back rail down to eye level. They separate below the cheekbone,
# never crossing through one another or creating an abrupt 90-degree notch.
# The sculpted front and posterior rails run continuously through z=1.42.
# There is no join-row kink and no curve-plane swap as the two petals divide.
# At eye height the forwardmost rail sits behind y=-.065m in both profiles.
HT=[(1.589,7.5,8.0,8.5),(1.583,17,23,32),(1.575,24,34,48),(1.558,31,42,60),
    (1.537,37,47,66),(1.519,39,49,69),(1.504,41,51,71)]
# z | inner sight-line | shared cheek/side ridge | posterior rail
HR3=[
 (1.490,.0825,-.087,.0995,-.067,.114,-.034),
 (1.476,.085,-.0825,.102,-.062,.116,-.031),
 (1.462,.087,-.072,.1045,-.0555,.1175,-.0285),
 (1.450,.0885,-.0624,.1055,-.0515,.118,-.0265),
 (1.439,.090,-.0605,.1065,-.050,.119,-.025),
 (1.425,.090,-.0600,.1065,-.050,.119,-.025),
 (1.414,.089,-.0605,.1055,-.051,.1188,-.0255)]
def templefan(h,k,tag):
    low=([(1.405,.087,-.0615,.103,-.053),(1.400,.0845,-.063,.101,-.055),
        (1.391,.080,-.067,.095,-.060),(1.382,.074,-.073,.086,-.067),
        (1.374,.065,-.078,.0652,-.0778)] if k==0 else [
        (1.405,.105,-.052,.118,-.0265),(1.391,.1025,-.054,.1165,-.030),
        (1.374,.0975,-.060,.1135,-.037),(1.351,.090,-.067,.107,-.047),
        (1.331,.082,-.0735,.097,-.058),(1.316,.0745,-.078,.0845,-.0695),
        (1.304,.065,-.0815,.0653,-.0812)])
    tip=low[-1][0]
    # Left and right contour rails evaluated as height functions separately,
    # then bridged by one closed horizontal section even through the eye window.
    edge0=[];edge1=[]
    for z,a,m,b in HT:
        v0,v1=(a,m) if k==0 else (m,b)
        p0=capq(rad(v0),z);p1=capq(rad(v1),z)
        edge0.append((z,p0.x,p0.y));edge1.append((z,p1.x,p1.y))
    for q in HR3:
        z,x1,y1,x2,y2=q[:5] if k==0 else (q[0],q[3],q[4],q[5],q[6])
        edge0.append((z,x1,y1));edge1.append((z,x2,y2))
    for z,x1,y1,x2,y2 in low:
        edge0.append((z,x1,y1));edge1.append((z,x2,y2))
    zs0,xs0,ys0=zip(*reversed(edge0));zs1,xs1,ys1=zip(*reversed(edge1))
    def fl(t,v,j):
        z=1.589+(tip-1.589)*t
        a=pch(zs0,xs0,z);b=pch(zs1,xs1,z);c=pch(zs0,ys0,z);d=pch(zs1,ys1,z)
        dx=b-a;dy=d-c;w=math.hypot(dx,dy);nx=.70710678;ny=-.70710678
        fac=ease(1.588,1.535,z)*(1-ease(tip+.012,tip,z))
        bulge=.065*w*(1-v*v)
        lift=.00030+.00097*fac+bulge
        lift+= (.000075+(.0019 if k==1 else .00133)*fac*(.87+.13*v))*max(0,j)**1.2
        lift+= (.000072+.00052*fac)*min(0,j)
        billow=.0056*ease(1.573,1.491,z)*ease(1.389,1.477,z)
        return (h*(a+dx*(v+1)*.5+nx*lift+billow),c+dy*(v+1)*.5+ny*lift,z)
    return closed_hair_ribbon(tag+(' temple · short cheek wing' if k==0 else ' temple · long inward silk leaf'),fl,hair,65,24)
for h,tag in [(-1,'R'),(1,'L')]:
    def mirrored(pp):return [(h*x,y,z,w) for x,y,z,w in pp]
    templefan(h,0,tag);templefan(h,1,tag)
    # A brief rear return, tucked behind the large leaf's contour.
    P=mirrored([(.109,-.034,1.408,.001),(.110,-.039,1.391,.006),
        (.108,-.046,1.369,.009),(.101,-.054,1.349,.008),
        (.093,-.062,1.333,.006),(.084,-.068,1.321,.003),(.076,-.072,1.314,.00015)])
    blade(tag+' temple · softly forked underslip',P,(h*.85,-.52,.04),hair,.0016,28)
P=[(-.072,-.033,1.557,.0005),(-.112,-.046,1.524,.0022),(-.130,-.051,1.488,.0025),
   (-.137,-.057,1.452,.0023),(-.139,-.058,1.422,.0014),(-.134,-.057,1.402,.0001)]
blade('R temple · fine lifted strand',P,(-.52,-.84,.01),hair,.00115,36)
section('H05 · Left ponytail and flyaway')
# One dominant crescent-shaped high-tail leaf with two *lower* returns,
# instead of a cylindrical braid of tubes starting at the same broad socket.
P=[(.119,.056,1.504,.004),(.129,.058,1.518,.007),(.143,.065,1.533,.010),
   (.157,.075,1.538,.013),(.167,.084,1.528,.017),(.175,.091,1.503,.0215),
   (.178,.099,1.466,.024),(.181,.107,1.429,.026),(.187,.115,1.395,.026),
   (.201,.122,1.362,.024),(.222,.130,1.333,.022),(.240,.135,1.308,.018),
   (.249,.136,1.281,.0145),(.247,.132,1.257,.009),(.238,.125,1.241,.004),
   (.225,.117,1.232,.00017)]
blade('Left high tail · dominant air-swept leaf',P,lambda t:(.68+.12*t,-.74+.10*t,.05),hair,.0045,69)
P=[(.129,.063,1.518,.0025),(.148,.075,1.537,.005),(.166,.090,1.528,.009),
   (.178,.106,1.489,.013),(.183,.119,1.448,.014),(.192,.129,1.412,.012),
   (.211,.142,1.383,.010),(.238,.148,1.360,.0075),(.260,.149,1.337,.0060),
   (.269,.143,1.314,.0056),(.269,.135,1.293,.0058),(.266,.128,1.276,.0035),
   (.260,.124,1.261,.00017)]
blade('Left high tail · lifted outer return',P,(.77,-.63,.03),hair,.00235,61)
P=[(.155,.073,1.531,.001),(.164,.075,1.516,.006),(.168,.082,1.486,.010),
   (.168,.090,1.450,.011),(.171,.100,1.409,.011),(.183,.113,1.374,.010),
   (.197,.128,1.347,.009),(.215,.140,1.326,.008),(.235,.142,1.319,.006),
   (.248,.138,1.322,.0025),(.254,.134,1.331,.00015)]
blade('Left high tail · shorter curled underleaf',P,(.68,-.72,.02),hair,.0024,52)
# A real drop cross-section with substantial depth when viewed directly from
# +X. Its path bends forward and back as well as across: both elevations read.
P=[(-.006,-.0355,1.592,.0016),(-.015,-.042,1.603,.0052),
   (-.023,-.052,1.620,.0065),(-.022,-.058,1.636,.0063),
   (-.013,-.058,1.649,.0056),(.001,-.054,1.658,.0047),
   (.017,-.047,1.661,.0033),(.031,-.039,1.658,.0019),(.041,-.034,1.649,.00012)]
ao=blade('Ahoge · three dimensional crescent quill',P,(-.38,.88,.17),hair,.0044,51)
vz=max(q.co.z for q in ao.data.vertices)
for vv in ao.data.vertices:vv.co.z=1.592+(vv.co.z-1.592)*(1.665-1.592)/(vz-1.592)
ao.data.update()
section('H06 · Left moon, star and folded silk')
# High tie stays narrow as the hair arches out. The bow and its two pendants
# are placed forward of the fall, not buried between the cap and tail.
rcloth=mat('Clay deep charcoal · folded hair bow',.108)
rimcloth=mat('Clay silk · knot relief',.143)
moonmetal=mat('Clay pearl metal · crescent and setting',.64)
sgemm=mat('Clay sapphire · star facets',.205)
def silkloop(name,P,wide):
    def func(t,v,b):
        x,y,z,w=path(P,t);p=Vector((x,y,z)); ax=Vector(wide(t) if callable(wide) else wide).normalized()
        ta=(Vector(path(P,min(1,t+.0002))[:3])-Vector(path(P,max(0,t-.0002))[:3])).normalized();n=ax.cross(ta).normalized()
        s=2*v-1; f=ease(.0,.27,t)*(1-ease(.72,1,t))
        if n.x<0:n=-n
        crimp=.0019*(1-s*s)*(.35+.65*f)+.0017*cos((s+.18)*pi*1.1)*max(0,1-s*s)*(1-.55*f)
        return p+ax*w*s+n*(crimp-(.0008 if b else 0))
    return hs_loft(name,func,rcloth,44,11)
silkloop('Left tie · dark folded forward bow loop',[
    (.123,.055,1.508,.004),(.133,.052,1.498,.010),(.143,.044,1.479,.015),
    (.151,.038,1.459,.019),(.149,.039,1.451,.019),(.144,.045,1.454,.018),
    (.136,.052,1.469,.014),(.128,.057,1.492,.008),(.122,.058,1.506,.004)],
    lambda t:(.73,.64,.21-.10*t))
silkloop('Left tie · folded aft bow loop',[
    (.125,.058,1.508,.003),(.129,.065,1.521,.008),(.135,.075,1.530,.012),
    (.135,.086,1.531,.014),(.128,.090,1.524,.014),(.123,.081,1.516,.012),
    (.122,.066,1.510,.005),(.125,.059,1.507,.003)],
    lambda t:(.77,-.45,.38))
def silktail(name,P,widthaxis):
    def func(t,v,b):
        d=path(P,t); p=Vector(d[:3]);w=d[3]
        s=2*v-1;a=Vector(widthaxis(t)).normalized();zz=.0120*s*ease(.82,1,t)
        n=Vector((.79,-.60,.07)); cr=.0022*(1-s*s)+.0008*sin((s+.18)*pi)*sin(t*pi*1.2)
        return p+a*s*w+Vector((0,0,zz))+n*(cr-(.00085 if b else 0))
    return hs_loft(name,func,rcloth,36,11)
silktail('Left tie · long obliquely pointed silk tail',[
    (.125,.055,1.505,.004),(.132,.050,1.484,.010),(.132,.047,1.454,.0115),
    (.131,.044,1.422,.0125),(.134,.045,1.390,.013),(.138,.044,1.376,.011)],
    lambda t:(.70,.71,.055))
silktail('Left tie · shorter divergent silk tail',[
    (.126,.060,1.506,.004),(.132,.064,1.484,.007),(.136,.069,1.462,.010),
    (.142,.071,1.438,.011),(.150,.072,1.419,.011),(.151,.071,1.400,.008)],
    lambda t:(.60,.80,-.1))
tube('Left tie · pinched velvet knot',[(.119,.052,1.506),(.124,.056,1.510),(.131,.061,1.513)],
     lambda t:(.0065+.0033*sin(pi*t),.0062+.0031*sin(pi*t)),rimcloth,16,14)
# Fine meridian relief directed *towards* the tie. These borrow the cap's own
# curvature, beginning/receding exactly on its surface, never penetrating hair.
def gather(name,AZ,ma=hair):
    def fn(t,v,b):
        a,z,w=path(AZ,t);r=rad(a);side=2*v-1
        # Width measured in Z; weak relieved edges leave no hard crack.
        z+=w*side; p=capq(r,z);n=outward_hair(r,z)
        lift=.00038*min(1,w/.003)*(1-side*side)
        return p+n*((-.00026 if b else lift)-.00007)
    return hs_loft(name,fn,ma,35,9)
for j,curve in enumerate([
 [(31,1.569,.0003),(59,1.550,.0022),(79,1.529,.0036),(93,1.513,.0014),(111,1.508,.00015)],
 [(49,1.473,.0002),(62,1.477,.0037),(77,1.484,.0048),(91,1.498,.0031),(109,1.508,.00015)],
 [(72,1.442,.00015),(84,1.454,.0034),(94,1.471,.0042),(104,1.491,.0033),(111,1.507,.00015)],
 [(144,1.560,.00015),(135,1.548,.0023),(128,1.535,.0035),(122,1.516,.0022),(117,1.507,.00015)]
]):gather('Left temple · satin comb '+str(j+1),curve)
# A lenticular gold casting, not a flat C decal: the thicker belly rolls into
# polished mounting horns, with a discreet shallow inner bevel.
MO=Vector((.1335,.042,1.522)); MU=Vector((.595,.804,0)).normalized()
MV=Vector((0,0,1));MN=MU.cross(MV).normalized()
def mp(s,z,o):return MO+MU*s+MV*z+MN*o
outmoon=[(.012,.027),(.001,.030),(-.014,.029),(-.028,.021),(-.035,.008),
         (-.036,-.005),(-.031,-.017),(-.022,-.026),(-.008,-.031),(.007,-.031),
         (.020,-.026),(.030,-.017),(.035,-.005)]
inmoon=[(.012,.027),(.002,.026),(-.006,.022),(-.013,.014),(-.017,.005),
        (-.018,-.003),(-.014,-.012),(-.007,-.018),(.003,-.020),(.014,-.020),
        (.024,-.017),(.031,-.011),(.035,-.005)]
def moonfn(t,v,b):
    x,z=path(outmoon,t);x2,z2=path(inmoon,t);g=sin(pi*t)**.42
    d=(.0013+.0045*(sin(pi*v)**.66)*g) if not b else -.0012
    return mp((1-v)*x+v*x2,(1-v)*z+v*z2,d)
hs_loft('Crescent moon · broad embracing cast',moonfn,moonmetal,54,12)
def bezel(t):return moonfn(t,.17,False)+MN*(.00011*sin(pi*t)**.5)
tube('Crescent moon · satin bevel',bezel,lambda t:.00007+.00046*sin(pi*t)**.7,moonmetal,7,40)
# Fit the star clasp to the actual final scalp and fringe, not to a guide copy.
from mathutils.bvhtree import BVHTree
from functools import lru_cache
import numpy as np

def mount_hair_bvh(include):
    bpy.context.view_layer.update(); dep=bpy.context.evaluated_depsgraph_get()
    v=[];p=[]
    for ob in C.all_objects:
        if ob.type!='MESH' or not include(ob):continue
        body=ob.evaluated_get(dep); mesh=body.to_mesh(); count=len(v)
        v.extend(ob.matrix_world@q.co for q in mesh.vertices)
        p.extend([tuple(count+j for j in poly.vertices) for poly in mesh.polygons]); body.to_mesh_clear()
    return BVHTree.FromPolygons(v,p,all_triangles=False,epsilon=0)

mount_hair=mount_hair_bvh(lambda ob:any(c.name.startswith(('H03','H04')) for c in ob.users_collection))
SO=Vector((.099,-.090,1.490)); SU=Vector((.63,.776,.023)).normalized()
SV0=Vector((-.035,-.018,.999)).normalized(); SN=SU.cross(SV0).normalized(); SV=SN.cross(SU).normalized()
SO+=SU*.0020+SV*.0090

def mount_frame(d,v,lift):return SO+SU*d+SV*v+SN*lift

@lru_cache(maxsize=25000)
def star_seat(d,v):
    base=mount_frame(d,v,0.0); hit,normal,_,_=mount_hair.ray_cast(base+SN*.042,-SN,.12)
    return (hit-base).dot(SN) if hit is not None else None

def reseat(d,v,threshold=.00030):
    p=[star_seat(d+x,v+y) for x,y in ((0,0),(threshold,0),(-threshold,0),(0,threshold),(0,-threshold))]
    p=[x for x in p if x is not None]
    if not p:raise RuntimeError(("Missing star seat",d,v))
    return max(p)

for bar in range(2):
    def conforming_bar(t,v,b,bar=bar):
        side=2*v-1; d=-.0081+.0580*t; v0=(bar-.5)*.0080+.0089*t
        taper=min(1,.46+7.8*t,.46+8.9*(1-t)); vz=v0+side*.0014*taper
        top=.00128+.00114*sqrt(max(0,1-side*side))
        lift=(.00028 if b else top*taper+.00028)
        return mount_frame(d,vz,reseat(d,vz,.00035)+lift)
    hs_loft('Sapphire star · seated parallel bar '+str(bar+1),conforming_bar,moonmetal,132,10)

def star_outline(rx,rz):
    rays=[]
    for j in range(8):
        a=pi*j/4+.085; k=1 if j%2==0 else .405
        rays.append((rx*sin(a)*k,rz*cos(a)*k))
    return [(rays[j][0]+(rays[(j+1)%8][0]-rays[j][0])*s/10,rays[j][1]+(rays[(j+1)%8][1]-rays[j][1])*s/10) for j in range(8) for s in range(10)]

def star_basis(dx,dv):
    x,z=dx/.02,dv/.02
    return (1.,x,z,x*x,x*z,z*z)

star_outline0=star_outline(.0205,.0195)
seat_samples=[(dx*r,dz*r,reseat(dx*r,dz*r,.00024)) for dx,dz in star_outline0 for r in (.10,.25,.45,.68,.85,1.)]
M=np.array([star_basis(d,v) for d,v,j in seat_samples]); Y=np.array([j for d,v,j in seat_samples]);W=np.eye(M.shape[1])*.12;W[0,0]=0
poly=np.linalg.solve(M.T@M+W,M.T@Y)

def star_plane(d,v):return sum(a*b for a,b in zip(poly,star_basis(d,v)))

def star_frame(d,v):
    base=star_plane(d,v); pts=[star_seat(d+x,v+y) for x,y in ((0,0),(.0013,0),(-.0013,0),(0,.0013),(0,-.0013))];pts=[a for a in pts if a is not None]
    observed=(sum(pts)/len(pts)-base) if pts else 0.
    return base+max(-.00095,min(.00095,.42*observed))

star_bulk=max(j-star_frame(d,v) for d,v,j in seat_samples)+.00115
star_base0=star_seat(0,0)

def gold_back(d,v):
    # Thin belly follows the left tip across the high lip of the side fringe.
    clean=.00104*exp(-((d+.0114)/.0034)**2-((v+.0027)/.0038)**2)
    reach=.00069+.00040*exp(-((d+.0114)/.0048)**2-((v+.0027)/.0041)**2)
    return reseat(d,v,reach)+.00048+clean

def pinned_star(name,outline,relief,jewel):
    vv=[];ff=[];n=len(outline)
    def add_layer(r,depth):
        first=len(vv)
        for bx,bz in outline:
            x,z=bx*r,bz*r; vv.append(mount_frame(x,z,depth(x,z)))
        if first:
            for j in range(n):k=(j+1)%n;ff.append((first-n+j,first-n+k,first+k,first+j))
    if jewel:
        add_layer(1,lambda d,v:star_frame(d,v)+star_bulk+.00155)
    else:
        for j in range(1,25):add_layer(j/24,gold_back)
    raise_frame=(.00195 if jewel else 0.)
    add_layer(1,lambda d,v:star_frame(d,v)+star_bulk+raise_frame)
    add_layer(.73,lambda d,v:star_frame(d,v)+star_bulk+raise_frame+.46*relief)
    un=len(vv);vv.append(mount_frame(0,0,star_frame(0,0)+star_bulk+raise_frame+relief))
    low=len(vv); vv.append(mount_frame(0,0,star_frame(0,0)+star_bulk+.00155 if jewel else gold_back(0,0)))
    for j in range(n):
        ff.append((j,(j+1)%n,low));ff.append((un-n+j,un-n+(j+1)%n,un))
    return objmesh(name,vv,ff,sgemm if jewel else moonmetal,smooth=False)

pinned_star('Four-ray star · contoured gold surround',star_outline0,.00215,False)
pinned_star('Four-ray star · faceted sapphire',star_outline(.0158,.0152),.00435,True)

# Draw the tied root into the side crown with progressively less shift up the flare.
tail_root=Vector((.119,.056,1.504)); actual,normal,_,_=mount_hair.find_nearest(tail_root)
root_delta=(actual+normal*.0015-tail_root) if actual is not None else Vector((-.0087,-.0038,.0))
root_delta.z+=.00145;root_delta*=min(1,.0103/max(root_delta.length,1e-8))
for ob in [q for q in C.all_objects if q.type=='MESH' and q.name.startswith('Left high tail')]:
    for v in ob.data.vertices:
        f=(1-ease(.122,.167,v.co.x))*ease(1.461,1.501,v.co.z)
        v.co+=root_delta*f
    ob.data.update()

rim_delta=Vector((root_delta.x*.63,root_delta.y*.63,root_delta.z+.00065))
for ob in [q for q in C.all_objects if q.type=='MESH' and q.name.startswith('Left tie')]:
    for v in ob.data.vertices:
        f=.60+.40*ease(1.380,1.48,v.co.z)
        v.co+=rim_delta*f
        if 'long obliquely pointed silk tail' in ob.name:
            w=ease(1.399,1.437,v.co.z)*(1-ease(1.449,1.477,v.co.z))
            v.co+=Vector((.00080,-.00021,0))*w
    ob.data.update()

# Keep the broad C shape sculpted. Its thick underside sits against authentic
# crown curvature instead of slipping into the temple as the tied root moves.
for ob in [q for q in C.all_objects if q.type=='MESH' and q.name.startswith('Crescent moon')]:
    bpy.data.objects.remove(ob,do_unlink=True)
MO+=Vector((root_delta.x*.64,root_delta.y*.60,.0022))

def moon_seat(t,v,back):
    p=moonfn(t,v,True);n=MN;base=.00121
    # Smooth the crown seam across five submillimetre surface measurements.
    for ds,dz in ((0,0),(-.00055,0),(.00055,0),(0,-.00055),(0,.00055)):
        start=p+MU*ds+MV*dz+n*.036; hit,_,_,_=mount_hair.ray_cast(start,-n,.039)
        if hit is not None:base=max(base,(hit-p).dot(n)+.00019)
    lateral=Vector((1,0,0))
    for i in range(2):
        sample=p+n*base;off=0.
        for ds,dz in ((0,0),(-.00057,0),(.00057,0),(0,-.00055),(0,.00055)):
            sp=sample+MU*ds+MV*dz;hit,_,_,_=mount_hair.ray_cast(sp+lateral*.026,-lateral,.028)
            if hit is not None:off=max(off,(hit-sp).dot(lateral)+.00036)
        base+=off/n.x
    rel=0 if back else (.0020+.00455*sin(pi*v)**.66*max(0,sin(pi*t))**.42)
    return p+n*(base+rel)

hs_loft('Crescent moon · seated embracing cast',moon_seat,moonmetal,65,14)
tube('Crescent moon · satin bevel',lambda t:moon_seat(t,.17,False)+MN*(.00010*sin(pi*t)**.5),lambda t:.00007+.00036*sin(pi*t)**.72,moonmetal,7,48)
print('Seated star at hair depth %.5f m; tail displacement %s' % (star_base0,tuple(round(k,5) for k in root_delta)))
# Round 2.5 full-body fit: the skull's rise stays at the original 1.600 m.
# A shared smooth deformation keeps clipped accessories in their actual seats.
for ob in C.all_objects:
    if ob.type!='MESH':continue
    is_face=any(c.name.startswith(('H01','H02')) for c in ob.users_collection)
    classic_normals=[q.vector.copy() for q in ob.data.corner_normals] if ob.data.has_custom_normals else None
    for vert in ob.data.vertices:
        q=vert.co; x,y,z=q
        k=ease(1.222,1.374,z)
        if is_face:k=1.
        elif y<-.012:
            # Keep the refined face-frame ends with the jaw as the back hair tapers to identity.
            k=max(k,ease(-.012,-.065,y)*ease(1.278,1.330,z))
        extra=0. if is_face else .00186*exp(-((z-1.508)/.056)**2)*ease(.051,.108,abs(x))*ease(.067,.002,y)
        sx=1.+.050*k;sy=1.+.046*k
        q.x=sx*x+math.copysign(extra,x);q.y=.010+sy*(y-.010)
        if z<1.600:q.z=z+.011*k*(z-1.600)
    ob.data.update()
    if classic_normals and is_face:
        ob.data.normals_split_custom_set([tuple(Vector((n.x/1.050,n.y/1.046,n.z/1.011)).normalized()) for n in classic_normals])
# Nudge the very end of the long silk tail away from the last waterfall leaves.
long_silk=next(q for q in C.all_objects if q.type=='MESH' and 'long obliquely pointed silk tail' in q.name)
for vertex in long_silk.data.vertices:
    fit=ease(1.430,1.392,vertex.co.z)
    vertex.co.x+=.0015*fit
    vertex.co.y-=.0025*fit
long_silk.data.update()
# Reproducible studio inspection. Lights/cameras live outside the appendable head collection.
def studio():
    camdat=bpy.data.cameras.new('Inspection orthographic');cam=bpy.data.objects.new('Inspection camera',camdat);S.collection.objects.link(cam);S.camera=cam;camdat.type='ORTHO';camdat.clip_start=.01;camdat.clip_end=20
    def look(ob,at):ob.rotation_euler=(Vector(at)-ob.location).to_track_quat('-Z','Y').to_euler()
    for name,loc,power,size in [('Softbox key',(-1.3,-2.2,3.25),65.57,1.65),('Softbox fill',(1.7,-1.65,2.4),41.08,1.9),('Softbox silhouette',(1.1,1.3,2.75),57.67,1.45),('Softbox chin',(-.2,-1.6,1.1),13.43,1.5)]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;ob=bpy.data.objects.new(name,d);S.collection.objects.link(ob);ob.location=loc;look(ob,(0,0,1.44))
    S.world=bpy.data.worlds.new('Clay inspection environment');S.world.use_nodes=True;bg=S.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.49,.49,.49,1);bg.inputs['Strength'].default_value=.48
    S.render.engine='BLENDER_EEVEE_NEXT';S.eevee.taa_render_samples=96;S.render.resolution_x=800;S.render.resolution_y=800;S.render.resolution_percentage=100;S.render.image_settings.file_format='PNG';S.render.threads_mode='FIXED';S.render.threads=4;S.render.film_transparent=True;S.view_settings.view_transform='AgX';S.render.image_settings.color_mode='RGBA'
    S.use_nodes=True;nt=S.node_tree;nt.nodes.clear();rl=nt.nodes.new('CompositorNodeRLayers');back=nt.nodes.new('CompositorNodeRGB');back.outputs[0].default_value=(.79,.80,.82,1);mix=nt.nodes.new('CompositorNodeAlphaOver');nt.links.new(back.outputs[0],mix.inputs[1]);nt.links.new(rl.outputs['Image'],mix.inputs[2]);output=nt.nodes.new('CompositorNodeComposite');nt.links.new(mix.outputs[0],output.inputs[0])
    def camera(deg):
        a=pi*deg/180;at=Vector((.040 if deg in [0,35,-35] else .008,.010,1.456));cam.location=at+Vector((sin(a)*2.4,-cos(a)*2.4,0));look(cam,at);camdat.ortho_scale=.452
    camera(0);return camera
import bpy, os, struct, zlib, math
from mathutils import Matrix, Vector

GUIDE_TAG = "suzu_reference_guide_v1"
COLLECTION = "REFERENCES · head ortho · no export"
SPECS = {
    # rect=(left,top,right,bottom); last row/column are excluded in pixel slicing.
    "SIDE": {"label":"02 | +X LEFT 90 | Num3", "rect":(985,0,1354,464),
             "axis":(1,0,0), "right":(0,1,0), "u0":1147.0,"h0":.008,
             "top":70.0, "chin":365.0},
    "FRONT":{"label":"01 | -Y FRONT | Num1", "rect":(9,0,531,464),
             "axis":(0,-1,0), "right":(1,0,0), "u0":228.5,"h0":0.,
             "top":71.0, "chin":368.0},
}
SIDE_PX = {"crown":(1162,70), "bridge":(1028,264), "nose_root":(1026,273),
           "nose_tip":(1006,289), "subnasale":(1017,312),
           "upper_lip":(1016,318), "mouth_division":(1022,324), "lower_lip":(1023,331),
           "mentolabial_turn":(1028,339), "chin_front":(1032,353),"chin_bottom":(1045,365),
           "mandible_visible_1":(1060,363), "mandible_visible_2":(1075,360),
           "iris_center":(1054,259), "design_eye_line_at_iris":(1054,253.463),
           "ear_top":(1160,241), "ear_canal":(1147,274), "lobule":(1141,305),
           "hair_shell_occipital":(1295,207)}
FRONT_PX = {"crown":(247,71), "chin_bottom":(228.5,368),"left_image_iris":(178,261),
            "right_image_iris":(278,260), "design_eye_line":(228.5,255.707),
            "mouth_L":(209,323),"mouth_mid":(228.5,327),"mouth_R":(248,323)}

def mpp(s):
    return (1.600 - 1.317) / (s["chin"]-s["top"])

def suzu_ref_point(view, u, v, depth=0.0):
    """Measured 3D locator; depth is a signed distance along the view normal."""
    s=SPECS[view]; m=mpp(s)
    return (Vector(s["axis"])*depth + Vector(s["right"])*(s['h0']+m*(u-s["u0"]))
            + Vector((0,0,1.600-m*(v-s["top"]))))

def _chunk(t,b):
    return struct.pack(">I",len(b))+t+b+struct.pack(">I",zlib.crc32(t+b)&0xffffffff)

def _png_from_u8_rgb(rgb):
    """No PIL, temporary files or packed full-sheet orphans required."""
    h,w,n=rgb.shape
    return (b"\x89PNG\r\n\x1a\n"+_chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,2,0,0,0))
            + _chunk(b"IDAT",zlib.compress(b"".join(b"\0"+r.tobytes() for r in rgb),9))
            + _chunk(b"IEND",b""))

def _original_rgb_u8(sheet_path):
    import numpy as np
    src=bpy.data.images.load(str(sheet_path),check_existing=False)
    try:
        if tuple(src.size)!=(1376,768):
            raise ValueError(f"Expected the original 1376×768 expression sheet: got {tuple(src.size)}")
        # Numeric sRGB bytes, without implicit display-to-linear conversion.
        src.colorspace_settings.name='Non-Color'
        W,H=src.size[:]; raw=np.empty(len(src.pixels),dtype=np.float32); src.pixels.foreach_get(raw)
        return np.rint(raw.reshape(H,W,-1)[::-1,:,:3]*255.).clip(0,255).astype(np.uint8)
    finally:
        bpy.data.images.remove(src)

def _packed_png(label, rgb):
    # Packed data encodes a true copy of the source crop: no external image path
    # will be needed on the user's computer. "FILE"+pack survives save+reopen.
    blob=_png_from_u8_rgb(rgb); h,w,_=rgb.shape
    im=bpy.data.images.new(name=label, width=w,height=h,alpha=False)
    im.filepath_raw="//Suzu_refs/"+label+".png"
    im.source='FILE'
    im.pack(data=blob,data_len=len(blob))
    im.colorspace_settings.name='sRGB'
    im[GUIDE_TAG]=True
    if not im.packed_file or im.packed_file.size!=len(blob):
        raise ValueError("Reference image is not packed: "+label)
    return im

def install_suzu_guides(sheet_path, scene=None, alpha=.32):
    """Install, return {"FRONT": object, "SIDE": object}; no render/camera changes."""
    sc=scene or bpy.context.scene
    parent=bpy.data.collections.get(COLLECTION)
    if parent and not parent.get(GUIDE_TAG):
        raise ValueError("An untagged collection already uses the reference collection name.")
    if not parent:
        parent=bpy.data.collections.new(COLLECTION);parent[GUIDE_TAG]=True
    if not any(c==parent for c in sc.collection.children):
        sc.collection.children.link(parent)
    parent.hide_render=True
    # Controlled idempotence: never touch unrelated user data or asset geometry.
    for ob in list(parent.objects):
        if ob.get(GUIDE_TAG):
            im=ob.data
            bpy.data.objects.remove(ob,do_unlink=True)
            if im is not None and im.get(GUIDE_TAG) and not im.users:
                bpy.data.images.remove(im)
    whole=_original_rgb_u8(sheet_path); objs={}
    for key,s in SPECS.items():
        l,t,r,b=s["rect"];w,h=r-l,b-t;m=mpp(s)
        im=_packed_png("03_face_"+key.lower(),whole[t:b,l:r,:])
        ob=bpy.data.objects.new(s["label"],None)
        parent.objects.link(ob);ob[GUIDE_TAG]=True
        ob.empty_display_type='IMAGE';ob.data=im
        ob.empty_image_offset=(-.5,-.5)
        ob.empty_display_size=max(w,h)*m
        ob.empty_image_depth='FRONT';ob.empty_image_side='FRONT'
        ob.show_empty_image_only_axis_aligned=True
        ob.show_empty_image_perspective=False;ob.show_empty_image_orthographic=True
        ob.use_empty_image_alpha=True;ob.color=(1,1,1,max(0,min(1,alpha)))
        ob.hide_render=True;ob.hide_select=True;ob.show_name=False
        # Local +X is image right, local +Y is image up; local +Z faces viewer.
        M=Matrix((Vector(s['right']),Vector((0,0,1)),Vector(s['axis']))).transposed()
        ob.matrix_world=M.to_4x4()
        ob.location=suzu_ref_point(key,(l+r-1)/2,(t+b-1)/2,depth=-.35)
        ob['original_crop_LTRB']=s['rect'];ob['metres_per_source_px']=m
        ob['reference_pixel_y_down']=True
        ob.lock_location=ob.lock_rotation=ob.lock_scale=(True,True,True)
        objs[key]=ob
    bpy.context.view_layer.update()
    verify_suzu_guides(objs)
    return objs

def verify_suzu_guides(objs):
    """Use actual Blender Empty properties and world matrix, not proposed transforms."""
    for key,landmarks in (("SIDE",SIDE_PX),("FRONT",FRONT_PX)):
        ob=objs[key];s=SPECS[key];W,H=ob.data.size[:];l,t,r,b=s['rect'];ox,oy=ob.empty_image_offset
        assert (W,H)==(r-l,b-t),f"Packed image dimensions wrong: {(W,H)} vs {s['rect']}"
        factor=ob.empty_display_size/max(W,H)
        assert (ob.matrix_world.to_3x3()@Vector((0,0,1))).angle(Vector(s['axis']))<1e-4
        for label,(u,v) in landmarks.items():
            local=Vector((factor*(u-l+.5+W*ox),factor*(b-v-.5+H*oy),0))
            world=ob.matrix_world@local
            err=(world-suzu_ref_point(key,u,v,depth=-.35)).length
            assert err<.0000004, f"{key} / {label}: alignment error {err:.7f}m"
        assert ob.hide_render and ob.hide_select and ob.data.packed_file
        assert ob.users_collection and all(c.name==COLLECTION for c in ob.users_collection)
        assert not ob.show_empty_image_perspective and ob.show_empty_image_only_axis_aligned
    return True

# Real 90-degree and front sculpt guides, packed from the project's unaltered original reference sheet.
arg_ref=next((a.split('=',1)[1] for a in ARGS if a.startswith('--reference=')), None)
if arg_ref:reference=Path(arg_ref).expanduser().resolve()
else:
    roots=[Path.cwd(),*Path(__file__).resolve().parents];reference=next((r/'references'/'03_face_expressions_props.jpg' for r in roots if (r/'references'/'03_face_expressions_props.jpg').is_file()),None)
if reference is None:raise FileNotFoundError('Pass --reference=/path/to/references/03_face_expressions_props.jpg')
install_suzu_guides(str(reference))
def viewport_presentation():
    for ob in S.objects:
        if ob.type in ('CAMERA','LIGHT'):ob.hide_set(True);ob.hide_select=True
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type!='VIEW_3D':continue
            sp=area.spaces.active;sp.region_3d.view_rotation=Vector((-.48,1,-.025)).to_track_quat('-Z','Y');sp.region_3d.view_location=(.024,.03,1.385);sp.region_3d.view_distance=.56;sp.region_3d.view_perspective='ORTHO';sp.overlay.show_floor=False;sp.overlay.show_axis_x=False;sp.overlay.show_axis_y=False;sp.overlay.show_cursor=False;sp.shading.color_type='MATERIAL';sp.shading.light='STUDIO';sp.shading.show_shadows=False;sp.shading.show_specular_highlight=False
cam=studio();viewport_presentation();bpy.context.view_layer.update(); bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'suzu_head.blend'),compress=True)
if '--preview' in ARGS:
    for ang,fn in [(0,'front'),(90,'left90'),(36,'left34'),(-36,'right34'),(-90,'right90')]:
        cam(ang);S.render.filepath=str(OUT/(fn+'.png'));bpy.ops.render.render(write_still=True)

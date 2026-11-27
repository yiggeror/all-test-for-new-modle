"""Suzu's three separate Phase B head ornaments, modeled in metre scale.

The lune trace follows the art director's enlarged prop panel; the gemstone
has real facets, the two rail bodies have rounded cross sections, and each
silk loop is a two-sided folded ribbon wrapped around an independent knot.
Use --anchors to seat the original geometry at the final hair mount frames.
"""
from pathlib import Path
import argparse,bpy,bmesh,json,sys
from math import sin,cos,sqrt,pi,radians,exp
from mathutils import Vector,Matrix
P=argparse.ArgumentParser()
P.add_argument('--output',type=Path,required=True)
P.add_argument('--anchors',type=Path)
A=P.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene;S.unit_settings.system='METRIC'
C=bpy.data.collections.new('SUZU_PHASE_B_PROPS');S.collection.children.link(C)
DEFAULT={
    'moon':{'pos':[.1260,.0130,1.5310],'normal':[.66,-.74,.11],'roll':-5.5,'scale':1.05},
    'star':{'pos':[.0980,-.0710,1.4980],'normal':[.40,-.904,.126],'roll':-.5,'scale':1.0},
    'bow':{'pos':[.1280,.0230,1.5090],'normal':[.74,-.66,.113],'roll':-12.0,'scale':1.03}
}
spec={n:DEFAULT[n]|v for n,v in (json.loads(A.anchors.read_text()) if A.anchors else DEFAULT).items()}
for n in DEFAULT:
    if n not in spec:spec[n]=dict(DEFAULT[n])
def rgb(h):
    h=h.lstrip('#');f=lambda x:x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4
    return tuple(f(int(h[i:i+2],16)/255.) for i in (0,2,4))+(1.,)
def mat(name,hexcode,rough=.45,metal=0.,polish=0.,em=.0,sheen=.0):
    m=bpy.data.materials.new('Hoshino · '+name);m.use_nodes=True;m.diffuse_color=rgb(hexcode)
    q=m.node_tree.nodes.get('Principled BSDF')
    q.inputs['Base Color'].default_value=m.diffuse_color
    q.inputs['Roughness'].default_value=rough;q.inputs['Metallic'].default_value=metal
    q.inputs['Coat Weight'].default_value=polish;q.inputs['Coat Roughness'].default_value=.235
    q.inputs['Emission Color'].default_value=m.diffuse_color;q.inputs['Emission Strength'].default_value=em
    q.inputs['Sheen Weight'].default_value=sheen
    m['reference_color']=hexcode
    return m
gold=mat('natural antique gold','#C5A37D',.29,.78,.23,.12)
gold_bevel=mat('gold glint · polished narrow bevel','#E4C28E',.22,.83,.30,.15)
gold_inner=mat('gold recess · satin warm shade','#A17D5C',.36,.78,.09,.09)
gold_soft=mat('gold region · gentle champagne','#D3AF81',.285,.75,.21,.14)
navy=mat('satin midnight navy','#2F354F',.58,.010,.015,.038,.16)
navy.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.21
navy_dark=mat('folded satin inner wall','#202741',.56,.0,.015,.06,.16)
navy_lite=mat('thread-finish rolled edge','#434B69',.52,.008,.055,.055,.24)
NavyMat=[navy,navy_dark,navy_lite]
gemMats=[
    mat('sapphire · violet-blue core','#505A97',.26,.22,.32,.18),
    mat('sapphire · indigo return','#313B72',.28,.28,.27,.16),
    mat('sapphire · blue facet','#4862AC',.255,.21,.33,.16),
    mat('sapphire · soft lavender face','#677DC1',.240,.18,.34,.16),
    mat('sapphire · deep girdle','#344476',.275,.21,.32,.18),
]
def tangent(item):
    d=spec[item];n=Vector(d['normal']).normalized()
    u=Vector((0,0,1)).cross(n).normalized();v=n.cross(u).normalized()
    roll=radians(d.get('roll',0.));u,v=cos(roll)*u+sin(roll)*v,-sin(roll)*u+cos(roll)*v
    return u,v,n
def mount(label):
    d=spec[label];u,v,n=tangent(label);p=Vector(d['pos'])
    E=bpy.data.objects.new('PHASE_B_'+label.upper()+'_TARGET',None);C.objects.link(E)
    # Basis columns are right/up/outward in world space.
    E.matrix_world=Matrix((u,v,n)).transposed().to_4x4();E.location=p
    E.empty_display_type='SINGLE_ARROW';E.empty_display_size=.017
    E['local_plane']='X toward left temple, Y up, Z outward'
    E['attachment']='Suzu left temple' if label=='star' else 'Suzu left ponytail crown'
    E['phaseB camera only']=True
    return E
anchors={key:mount(key) for key in ('moon','star','bow')}
def lens(z,k=.8):return sin(pi*min(1.,max(0.,z)))**k
def ga(x,s):return exp(-.5*(x/s)**2)
def smooth(t):
    t=max(0.,min(1.,t));return t*t*(3.-2.*t)
def signedpow(a,p):return (1 if a>=0 else -1)*abs(a)**p
def curve(keys,t):
    """Componentwise Hermite artist rails; endpoints clamp to the first/last edit station."""
    vtype=(lambda q:tuple(q)) if len(keys[0])==2 else Vector
    if t<=keys[0][0]:return vtype(keys[0][1:])
    if t>=keys[-1][0]:return vtype(keys[-1][1:])
    j=next(i for i in range(len(keys)-1) if keys[i][0]<=t<=keys[i+1][0])
    l,a,b,r=[keys[k] for k in (max(0,j-1),j,j+1,min(j+2,len(keys)-1))]
    dt=b[0]-a[0];h=(t-a[0])/dt
    return vtype(tuple(a[k]*(2*h**3-3*h*h+1)+(h**3-2*h*h+h)*dt*(b[k]-l[k])/(b[0]-l[0])
              +b[k]*(-2*h**3+3*h*h)+(h**3-h*h)*dt*(r[k]-a[k])/(r[0]-a[0]) for k in range(1,len(a))))
def loc(which,xyz,seat=False):
    # Real meshes carry world coordinates directly, so viewport targets can
    # be dropped during glTF export without changing any object transform.
    d=spec[which];u,v,n=tangent(which)
    x,y,z=(a*d.get('scale',1.) for a in xyz)
    if seat:
        # Small contact-thickness map settled from the fitted hair under
        # each rail/underfoot. The gemstone crown stays rigid.
        c=d.get('mount_seat_curve',[])
        if len(c)>1:
            val=curve(c,x)[0]
            z+=val
    return Vector(d['pos'])+x*u+y*v+z*n
class Shape:
    def __init__(self,which):self.which=which;self.P=[];self.F=[];self.I=[];self.Sm=[]
    def at(self,p,seat=False):
        self.P.append(loc(self.which,p,seat));return len(self.P)-1
    def face(self,ids,m=0,smooth=True):
        if len(ids)>=3 and len(set(ids))==len(ids):
            self.F.append(tuple(ids));self.I.append(m);self.Sm.append(smooth)
    def obj(self,name,mats):
        mm=bpy.data.meshes.new(name+' · mesh');mm.from_pydata(self.P,[],self.F);mm.update()
        for m in mats:mm.materials.append(m)
        # Material assignment and intentionally planar gemstone facets are
        # saved before winding repair; bmesh retains them.
        for p,i,s in zip(mm.polygons,self.I,self.Sm):p.material_index=i;p.use_smooth=s
        bm=bmesh.new();bm.from_mesh(mm);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        n=sum(not e.is_manifold for e in bm.edges);z=sum(f.calc_area()<1e-13 for f in bm.faces)
        if n or z:raise RuntimeError(f'{name} has {n} open lines / {z} zero-area faces')
        bm.to_mesh(mm);bm.free();mm.update()
        o=bpy.data.objects.new(name,mm);C.objects.link(o)
        o['mount']=anchors[self.which].name;o['phase']='B'
        o['orientation']='character left (+X), Blender front −Y'
        return o
def sweep(which,name,points,d1,d2,mats,ballend=True,seat=False,rows=48,n=12,power=.88):
    M=Shape(which);R=[]
    for i in range(rows+1):
        t=i/rows
        p=curve(points,t);pp=curve(points,min(1,t+.0012))-curve(points,max(0,t-.0012))
        tt=Vector(pp).normalized();nn=Vector((0.,0.,1.));aa=nn.cross(tt).normalized()
        if aa.length<.001:aa=Vector((1,0,0))
        bb=tt.cross(aa).normalized()
        w=(.42+.58*smooth(min(t,1.-t)/.075)) if ballend else 1.
        ra= d1(t) if callable(d1) else d1; rb=d2(t) if callable(d2) else d2
        row=[]
        for j in range(n):
            a=2*pi*j/n
            q=p+aa*signedpow(cos(a),power)*ra*w+bb*signedpow(sin(a),power)*rb*w
            row.append(M.at(q,seat))
        R.append(row)
    for i in range(rows):
        for j in range(n):M.face((R[i][j],R[i][(j+1)%n],R[i+1][(j+1)%n],R[i+1][j]),
                             1 if len(mats)>1 and j in (2,3) else 0)
    M.face(tuple(reversed(R[0])));M.face(tuple(R[-1]))
    return M.obj(name,mats)
# === Crescent: an asymmetric thin-horn lune, referenced to the actual micro crop.
OUT=[
(0,.0080,.0245),(.095,-.0029,.0259),(.195,-.0148,.0223),(.300,-.0243,.0160),(.443,-.0292,.0038),
(.562,-.0273,-.0097),(.687,-.0194,-.0216),(.797,-.0061,-.0270),(.880,.0080,-.0264),
(.954,.0208,-.0165),(1,.0270,-.0048)]
IN=[
(0,.0080,.0245),(.095,.0002,.0239),(.195,-.0068,.0208),(.300,-.0129,.0152),(.443,-.0161,.0051),
(.562,-.0142,-.0049),(.687,-.0087,-.0124),(.797,.0010,-.0175),(.880,.0121,-.0174),
(.954,.0225,-.0118),(1,.0270,-.0048)]
def arc_lune(t,u,layer):
    v=curve(OUT,t).lerp(curve(IN,t),u)
    rk=lens(t,.46);zi=lens(u,.70)
    # Low curved seat, rounded edges, subtle forged front relief. A narrow
    # inset trace is cut into the surface itself, not pasted onto the gold.
    cup=.00130*(v.x/.031)**2-.00124*v.y/.030
    groove=.00051*ga(u-.205,.027)*smooth((t-.135)/.19)*smooth((.934-t)/.115)
    if layer>0:
        ht=cup+rk*(.00079+.00482*zi+.00034*u)-groove
    else:
        ht=cup-rk*(.00054+.00183*zi)
    return Vector((v.x,v.y,ht))
def crescent():
    a=Shape('moon')
    us=[0,.042,.086,.135,.166,.183,.205,.228,.254,.296,.365,.466,.570,.675,.771,.846,.907,.954,1.]
    TS=152
    tip=[a.at(arc_lune(t,.5,1)) for t in (0.,1.)]
    R=[]
    for h in (-1,1):R.append([[a.at(arc_lune(i/TS,u,h)) for u in us] for i in range(1,TS)])
    for hi,r in enumerate(R):
        for k in range(len(us)-1):
            a.face((tip[0],r[0][k+1],r[0][k]),0)
            a.face((r[-1][k],r[-1][k+1],tip[1]),0)
        for i in range(len(r)-1):
            tt=(i+1.5)/TS
            for k in range(len(us)-1):
                um=(us[k]+us[k+1])*.5
                matidx=2 if hi==0 else 1 if (um<.084 or um>.937) else 2 if .193<um<.219 and .22<tt<.872 else 3 if .29<um<.53 and .12<tt<.50 else 0
                a.face((r[i][k],r[i][k+1],r[i+1][k+1],r[i+1][k]),matidx)
    f,b=R
    for k in (0,len(us)-1):
        for i in range(len(f)-1):a.face((f[i][k],b[i][k],b[i+1][k],f[i+1][k]),1)
        a.face((tip[0],f[0][k],b[0][k]),1);a.face((tip[1],b[-1][k],f[-1][k]),1)
    a.obj('01 · Gilded crescent / hand-traced bezel', [gold,gold_bevel,gold_inner,gold_soft])
    supports=[
        [(0.,-.0205,.0172,-.00125),(.22,-.0202,.0142,-.0044),(.60,-.0181,.0101,-.0065),(1.,-.0177,.0095,-.0041)],
        [(0.,-.0099,-.0205,-.0015),(.24,-.0064,-.0208,-.0044),(.69,.0000,-.0196,-.00565),(1.,.0057,-.0192,-.0037)]]
    supports=spec['moon'].get('saddles',supports)
    for i,paths in enumerate(supports):
        sweep('moon',f'01 · Hidden crescent saddle {chr(65+i)}',paths,.00096,.00062,[gold_inner,gold],True,rows=28,power=.64)
crescent()
# === Hairpin: one solid four-point star, seated faceted blue stone, separate parallel clasp rails.
STAR=[
(.0014,.0166),(-.0048,.0049),(-.0134,-.0007),(-.0043,-.0053),
(.0005,-.0154),(.0049,-.0056),(.0138,.0003),(.0047,.0045)]
def round_poly(coords,level=.00069):
    B=[]
    for i,p in enumerate(coords):
        P=Vector(p);A=Vector(coords[i-1]);C=Vector(coords[(i+1)%len(coords)])
        r=level*(.77 if i%2 else 1.)
        v=P+(A-P).normalized()*r;w=P+(C-P).normalized()*r
        for n in range(5):
            t=n/4.;Q=(1-t)**2*v+2*t*(1-t)*P+t*t*w
            B.append(Q)
    return B
def star():
    E=Shape('star')
    outline=round_poly(STAR)
    rings=[]
    for fac,ht in [( .681,-.0025),(.893,-.0025),(.988,-.0012),(1.014,.0000),
                   (1.003,.00154),(.944,.00283),(.791,.00330),(.774,.00250),(.727,.00043),(.620,-.00118)]:
        rings.append([E.at((u.x*fac,u.y*fac,ht),ht<-.0015) for u in outline])
    n=len(outline)
    for i in range(len(rings)-1):
        for j in range(n):
            k=(j+1)%n
            E.face((rings[i][j],rings[i][k],rings[i+1][k],rings[i+1][j]),1 if i in (2,4,5) else 2 if i>=7 else 0)
    E.face(rings[0]);E.face(tuple(reversed(rings[-1])))
    E.obj('02 · Four-point star / forged gold seat',[gold,gold_bevel,gold_inner])
    G=Shape('star');p=[Vector(v) for v in STAR]
    B=[G.at((v.x*.733,v.y*.733,.00072)) for v in p]
    A=[G.at((v.x*.778,v.y*.778,.00229+.0019*(j%2))) for j,v in enumerate(p)]
    Q=[G.at((-.00123,.0063,.00565)),G.at((-.0036,-.00055,.00629)),
       G.at((.00078,-.0056,.00587)),G.at((.00444,.00063,.00630))]
    center=G.at((.00017,.00097,.00725))
    for j in range(8):
        k=(j+1)%8;G.face((B[j],B[k],A[k],A[j]),4,False)
    G.face(tuple(reversed(B)),4,False)
    for k in range(4):
        j=(k*2)
        nxt=(k+1)%4
        G.face((A[j],A[(j+1)%8],Q[k]),[3,2,1,2][k],False)
        G.face((A[(j+1)%8],A[(j+2)%8],Q[nxt],Q[k]),[2,0,1,2][k],False)
        G.face((Q[k],Q[nxt],center),[3,1,0,2][k],False)
    G.obj('02 · Sapphire / hand-cut star crystal',gemMats)
    for j in (0,1):
        w=+.0025 if j==0 else -.00255
        rail=[(0.,.0042,w-.0007,-.00198),(.18,.0098,w+.0008,-.00212),(.45,.0179,w+.0034,-.00285),
              (.74,.0253,w+.0055,-.00364),(1.,.0317,w+.00728,-.0044)]
        if spec['star'].get('rails'):rail=spec['star']['rails'][j]
        sweep('star',f'02 · Hardened gold temple rail {j+1}',rail,.00123,.00098,[gold,gold_bevel],True,True,rows=60,n=12,power=.72)
    for j in (0,1):
        x=-.00165+.0033*j
        tabs=[(0.,x,-.0050,-.00243),(.25,x+.0003,-.0020,-.00342),(.60,x-.0003,.0030,-.00401),
              (1.,x-.00045,.0066,-.00354)]
        if spec['star'].get('pads'):tabs=spec['star']['pads'][j]
        sweep('star',f'02 · Low temple contact face {j+1}',tabs,.00151,.00067,[gold_inner],True,True,rows=24,n=12,power=.68)
star()
# === Knotted satin. A strip is modeled on both sides, never as a flat decal.
def textile(which,nm,fn,tines=75,u_count=19,th=.00089,soft_edge=True):
    Q=Shape(which);R=[];us=[-1+2*j/(u_count-1) for j in range(u_count)]
    for h in (-1,1):
        RR=[]
        for i in range(tines+1):
            t=i/tines;row=[]
            for u in us:
                p=Vector(fn(t,u))
                pp=Vector(fn(min(1,t+.0008),u))-Vector(fn(max(0,t-.0008),u))
                qq=Vector(fn(t,min(1,u+.005)))-Vector(fn(t,max(-1,u-.005)))
                N=pp.cross(qq).normalized()
                pad=(.30+.70*smooth(t/.078))*1. if 'inboard folded loop' in nm else 1.
                q=p+h*N*th*.5*pad*(.80+.20*(1.-abs(u)**6))
                row.append(Q.at(q))
            RR.append(row)
        R.append(RR)
    neg,pos=R
    for hi,r in enumerate(R):
        for i in range(tines):
            for j in range(len(us)-1):
                k=1 if hi==0 else (2 if soft_edge and j in (0,len(us)-2) and .08<i/tines<.97 else 0)
                Q.face((r[i][j],r[i+1][j],r[i+1][j+1],r[i][j+1]),k)
    for i in range(tines):
        for j in (0,len(us)-1):Q.face((pos[i][j],neg[i][j],neg[i+1][j],pos[i+1][j]),1)
    for i in (0,tines):
        for j in range(len(us)-1):Q.face((pos[i][j],pos[i][j+1],neg[i][j+1],neg[i][j]),1)
    return Q.obj(nm,NavyMat)
def wing1(t,u):
    # Inboard fold: shorter, lifting upward against the root.
    p=curve([(0.,-.001,.003,.001),(.12,-.0065,.006,.0037),(.37,-.020,.013,.0035),
       (.49,-.0295,.0136,.0007),(.58,-.028,.0125,-.0037),(.80,-.016,.0075,-.0067),(1.,-.002,.0022,-.0054)],t)
    width=curve([(0,.0039),(.10,.005),(.35,.0117),(.51,.0114),(.63,.0108),(.86,.0068),(1,.0038)],t)[0]
    pleat=(ga(u+.38,.20)-.83*ga(u-.23,.25))*.00185*lens(t,1.1)*(.40+.60*ga(t-.23,.25))
    return (.87*(p.x+.47*width*u)+.0078*lens(t,.86),.87*(p.y+width*.89*u-.0014*sin(pi*t)*u*u),
       p.z+.0036*(1-u*u)*lens(t,.77)-.00255*u*u*lens(t,.8)+pleat+.0009*u-.0033*lens(t,.80)+.0061*lens(t,.85))
def wing2(t,u):
    # The outboard fall is larger and points down in the hero reference.
    p=curve([(0.,.0005,-.0028,.0016),(.17,.0092,-.0090,.0041),(.37,.0244,-.0228,.0064),
       (.51,.0325,-.0253,.0023),(.60,.0308,-.0231,-.0033),(.76,.0211,-.0162,-.0057),
       (.88,.0103,-.0090,-.0064),(1.,.0008,-.0020,-.0040)],t)
    width=curve([(0,.0040),(.13,.0052),(.30,.0108),(.49,.01595),(.60,.0140),(.82,.0082),(1,.00395)],t)[0]
    pleat=(ga(u+.48,.21)-.83*ga(u-.14,.23))*.00208*lens(t,.85)*(.42+.58*ga(t-.23,.24))
    return (p.x+.59*u*width+.0017*u*u*lens(t,1.15),p.y+.82*u*width-.0021*u*u*lens(t,1.18),
        p.z+.0040*(1-u*u)*lens(t,.85)-.0021*u*u*lens(t,1.0)+pleat-.0019*u*lens(t,.93))
def tail(second,t,u):
    # Gathered under the silk knot, two gravity-driven S-curves separate,
    # swing independently and end in purpose-cut slanted corners.
    if not second:
        p=curve([(0.,-.001,-.0041,-.0049),(.14,-.0013,-.0161,-.0062),(.31,.002,-.0338,-.0065),
                 (.52,.0062,-.0574,-.0079),(.72,.0036,-.0775,-.0096),(.87,.0044,-.0937,-.0069),
                 (1.,.011,-.1051,-.0030)],t)
        width=curve([(0,.0048),(.18,.0066),(.34,.0093),(.56,.0105),(.72,.0111),(.91,.0118),(1.,.0116)],t)[0]
        cut=-.0036*u+.0016*(1-abs(u))
    else:
        p=curve([(0.,.0043,-.0051,-.0057),(.16,.0120,-.0162,-.0076),(.33,.0190,-.0330,-.0071),
                 (.55,.0250,-.0537,-.0083),(.76,.0250,-.0747,-.0044),(.89,.0215,-.0856,-.0008),
                 (1.,.0200,-.0953,-.0020)],t)
        width=curve([(0,.0045),(.21,.0064),(.45,.0103),(.68,.0128),(.90,.0116),(1,.0104)],t)[0]
        cut=.0036*u+.0014*(1-abs(u))
    ripple=(.00097*cos(pi*u+1.15*t)-.00071*cos(2*pi*u-.6*t))*sin(pi*t)**.55
    return (p.x+u*width*(.88 if second else .87)+(.0036*t*t if second else -.0018*t*t),
            p.y+.0012*ga(t-.25,.23)*u+.0010*u*u+cut*t**6,
            p.z+.0037*(1-u*u)*lens(t,.60)+.0027*u*cos(1.97*pi*t+.5+second)*lens(t,.58)+ripple
            -(.0073 if second else -.0052)*smooth(t/.23)*(1-.40*smooth((t-.56)/.44)))
def knot():
    # Gathered fabric collar around the knot, with asymmetrically rolled ends.
    M=Shape('bow');R=[]
    for i in range(25):
        t=i/24; q=2*t-1
        x=.0013+q*.00736
        rad=curve([(0,.0039),(.12,.0063),(.3,.0060),(.5,.00565),(.73,.0061),(.92,.0062),(1,.0039)],t)[0]
        row=[]
        for j in range(28):
            a=2*pi*j/28;u=cos(a);v=sin(a)
            y=-.0017+.0016*q+signedpow(u,.80)*rad*(1+.08*q*u)
            z=.0017+signedpow(v,.79)*(rad*.80)*(1+.10*cos(2*pi*t)*u)
            row.append(M.at((x-.00095*u+.00065*q*v,y,z)))
        R.append(row)
    for i in range(len(R)-1):
        for j in range(28):M.face((R[i][j],R[i][(j+1)%28],R[i+1][(j+1)%28],R[i+1][j]),2 if i in (1,2,21,22) else 0)
    M.face(tuple(R[-1]),1);M.face(tuple(reversed(R[0])),1)
    M.obj('03 · Navy silk / gathered centreband',NavyMat)
textile('bow','03 · Navy silk / inboard folded loop',wing1,83,23,.00092)
textile('bow','03 · Navy silk / outboard folded loop',wing2,86,23,.00095)
textile('bow','03 · Navy silk / first hanging tail',lambda t,u:tail(False,t,u),101,23,.00076,False)
textile('bow','03 · Navy silk / second hanging tail',lambda t,u:tail(True,t,u),104,23,.00076,False)
knot()
if spec['bow'].get('keeper'):
    sweep('bow','03 · Navy silk / recessed ponytail keeper',spec['bow']['keeper'],.0030,.00075,[navy_dark],True,rows=38,n=12,power=.64)
# Separate render camera witnesses are empties, not parts of the GLB mesh.
S['suzu_phase']='B: accessories only'
S['mount_frames_json']=json.dumps(spec,ensure_ascii=False)
bpy.context.preferences.filepaths.save_version=0
A.output.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(A.output.resolve()),compress=True)
print('ACCESSORY_MESHES',[(o.name,len(o.data.vertices),len(o.data.polygons)) for o in C.objects if o.type=='MESH'])

"""Suzu Phase C — pressed silk bow, mitred ribbon points and open-work astrolabe."""
from __future__ import annotations
import bpy
from mathutils import Vector,Matrix
import bmesh
from math import pi,cos,sin,sqrt,atan2,radians,exp
from pathlib import Path
import json,os

D=Path(__file__).resolve().parent
DEFAULT={'bow':{'origin':[0,-.069,1.250],'normal':[0,-.999,.045]},
         'brooch':{'origin':[.080,-.092,1.175],'normal':[.16,-.98,.08]}}

def rgba(h):
    a=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a)+(1.,)
def mat(name,h,rough,floor,metal=0,sheen=0):
    n='SUZU C · '+name
    m=bpy.data.materials.get(n)
    if m:return m
    m=bpy.data.materials.new(n);m.diffuse_color=rgba(h);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    for nm,val in {'Base Color':rgba(h),'Roughness':rough,'Metallic':metal,'Specular IOR Level':.29 if not metal else .43,
                   'Sheen Weight':sheen,'Sheen Roughness':.63,'Emission Color':rgba(h),'Emission Strength':floor}.items():
        if p.inputs.get(nm):p.inputs[nm].default_value=val
    m['suzu_stage_role']='wardrobe'
    m['suzu_material_family']='navy silk' if not metal else 'antique gold'
    portable=m.copy();portable.name=n+' · glTF';portable.use_fake_user=True
    m['suzu_glb_material']=portable.name
    m['suzu_glb_material_ref']=portable
    # Controlled local light maintains the reference midnight/gilt palette;
    # part of the real metallic BRDF remains live under the five studio rigs.
    ns=m.node_tree.nodes; lk=m.node_tree.links.new
    geo=ns.new('ShaderNodeNewGeometry');geo.location=(-600,200)
    key=ns.new('ShaderNodeVectorMath');key.operation='DOT_PRODUCT';key.location=(-410,205)
    lk(geo.outputs['Normal'],key.inputs[0]);key.inputs[1].default_value=Vector((-.54,-.63,.56)).normalized()
    ramp=ns.new('ShaderNodeValToRGB');ramp.location=(-210,205);rr=ramp.color_ramp;rr.interpolation='EASE'
    guide=rgba(h)
    sh=.42 if metal else .45
    rr.elements[0].position=.00;rr.elements[0].color=tuple(guide[i]*sh for i in range(3))+(1.,)
    e=rr.elements.new(.48);e.color=tuple(guide[i]*.80 for i in range(3))+(1.,)
    rr.elements[-1].position=.89;rr.elements[-1].color=tuple(min(.96,guide[i]*(1.18 if metal else 1.28)) for i in range(3))+(1.,)
    if not metal:
        rr.interpolation='EASE'
        dark=rgba('202640' if 'revers' not in name else '1F253D')
        bright=rgba({'Midnight navy ribbon':'424D74','Ribbon revers':'363F63','Ribbon bound edge':'343A54','Ribbon soft facing':'485379'}.get(name,'424C70'))
        rr.elements[0].position=.0;rr.elements[0].color=dark
        e.position=.35;e.color=dark
        k=rr.elements.new(.45);k.color=bright
        rr.elements[-1].position=.96;rr.elements[-1].color=tuple(min(.98,v*1.03) for v in bright[:3])+(1.,)
    lk(key.outputs['Value'],ramp.inputs['Fac'])
    em=ns.new('ShaderNodeEmission');em.location=(48,200);lk(ramp.outputs['Color'],em.inputs['Color'])
    mix=ns.new('ShaderNodeMixShader');mix.location=(314,93);mix.inputs[0].default_value=.12 if metal else .055
    lk(em.outputs[0],mix.inputs[1]);lk(p.outputs[0],mix.inputs[2]);lk(mix.outputs[0],ns.get('Material Output').inputs['Surface'])
    return m
def mats():
    return [mat('Midnight navy ribbon','2F354F',.47,.26,0,.19),mat('Ribbon revers','292D47',.58,.30,0,.115),
            mat('Ribbon bound edge','252A41',.56,.29,0,.14),mat('Ribbon soft facing','363D5B',.47,.245,0,.19),
            mat('Warm gilt','C5A37D',.33,.27,.72),mat('Gilt cut facet','DCC297',.235,.30,.70),
            mat('Soft recessed gold','947650',.42,.29,.65),mat('Polished warm lip','E3C99E',.25,.28,.69)]
class Form:
    '''Sculpt in (x,z,in-depth), retaining original feature face identities.'''
    def __init__(self):
        self.v=[];self.f=[];self.m=[];self.s=[];self.p=[];self.labels=[];self.names={};self.current=''
    def part(self,label):self.current=label
    def vtx(self,p):
        self.v.append((p[0],-p[2],p[1]));return len(self.v)-1
    def face(self,ids,m,smooth=True):
        if self.current not in self.names:self.names[self.current]=len(self.names)+1;self.labels.append(self.current)
        self.f.append(tuple(ids));self.m.append(m);self.s.append(smooth);self.p.append(self.names[self.current])
    def grid(self,rows,material,smooth=True,loop0=False,loop1=False):
        ii=[[self.vtx(v) for v in row] for row in rows];n=len(ii);l=len(ii[0])
        for i in range(n if loop0 else n-1):
            for k in range(l if loop1 else l-1):
                a=(i+1)%n;b=(k+1)%l
                fmat=material(i,k) if callable(material) else material
                sm=smooth(i,k) if callable(smooth) else smooth
                self.face((ii[i][k],ii[a][k],ii[a][b],ii[i][b]),fmat,sm)
        return ii
    def finalize(self,name,role,collection,base,materials):
        me=bpy.data.meshes.new(name);me.from_pydata(self.v,[],self.f);me.update()
        for m in materials:me.materials.append(m)
        for i,p in enumerate(me.polygons):p.material_index=self.m[i];p.use_smooth=self.s[i]
        bypart=me.attributes.new('suzu_feature_id','INT','FACE');bypart.data.foreach_set('value',self.p)
        # Correct winding for folded closed bands and separately cast metal parts.
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
        ob=bpy.data.objects.new(name,me);collection.objects.link(ob)
        ob['suzu_stage_role']='top_jewelry';ob['suzu_top_role']=role;ob['suzu_rig_zone']='chest';ob['suzu_material_mode']='standard'
        ob['suzu_top_mount']=role;ob['suzu_features']=json.dumps(self.labels,ensure_ascii=False)
        ob.matrix_world=frame(base['origin'],base['normal'])
        return ob

def frame(origin,normal):
    n=Vector(normal).normalized(); h=Vector((0,0,1)).cross(n).normalized();v=n.cross(h).normalized()
    M=Matrix((h,-n,v)).transposed().to_4x4();M.translation=Vector(origin);return M
def vd(p):return Vector(p)
def tube(f,points,r,ma,count=8,closed=False):
    ps=list(map(vd,points));rows=[]
    last=None
    for i,pp in enumerate(ps):
        v=(ps[(i+1)%len(ps) if closed else min(i+1,len(ps)-1)]-ps[(i-1)%len(ps) if closed else max(i-1,0)]).normalized()
        ref=Vector((0,0,1)) if abs(v.z)<.86 else Vector((0,1,0)); u=v.cross(ref).normalized();q=u.cross(v).normalized()
        if last is not None and u.dot(last)<0:u=-u;q=-q
        last=u
        rows.append([pp+r*(cos(2*pi*k/count)*u+sin(2*pi*k/count)*q) for k in range(count)])
    ii=f.grid(rows,ma,True,closed,True)
    if not closed:
        f.face(list(reversed(ii[0])),ma,False);f.face(ii[-1],ma,False)
def oval(f,center,r1,r2,r,direction=(1,0,0),v=(0,1,0),m=4,res=34):
    c=vd(center);a=vd(direction).normalized()*r1;b=vd(v).normalized()*r2
    tube(f,[c+a*cos(2*pi*i/res)+b*sin(2*pi*i/res) for i in range(res)],r,m,8,True)
def bezel(f,cx,cz,a,b,alpha,w,low,top,bevel=.0003,depth=0,n=96):
    '''Hammered bevel and distinct inner return on a band cut from gilt stock.'''
    alpha=radians(alpha);sa,ca=sin(alpha),cos(alpha)
    cross=[(-w*.5+bevel,low),(-w*.5,low+bevel),(-w*.5,top-bevel),(-w*.5+bevel,top),
           (w*.5-bevel,top),(w*.5,top-bevel),(w*.5,low+bevel),(w*.5-bevel,low)]
    rows=[]
    for k in range(n):
        t=2*pi*k/n;xx=a*cos(t);zz=b*sin(t);nn=Vector((b*cos(t),a*sin(t))).normalized();dd=depth*sin(t)
        row=[]
        for off,h in cross:
            x=xx+off*nn.x;z=zz+off*nn.y
            row.append((cx+x*ca-z*sa,cz+x*sa+z*ca,h+dd))
        rows.append(row)
    f.grid(rows,lambda i,j: [6,6,5,4,7,4,6,6][j],lambda i,j:j not in (3,7),True,True)
def dome(f,cx,cz,r0,base,height,ma,rz=None,res=48):
    if rz is None:rz=r0
    rings=[(r0,rz,base),(r0*1.012,rz*1.012,base+.12*height),(.95*r0,.95*rz,base+.35*height),
           (.69*r0,.69*rz,base+.82*height),(.32*r0,.32*rz,base+.965*height)]
    rows=[[(cx+rx*cos(2*pi*k/res),cz+rz0*sin(2*pi*k/res),d) for k in range(res)] for rx,rz0,d in rings]
    ii=f.grid(rows,ma,True,False,True);vp=f.vtx((cx,cz,base+height))
    for k in range(res):f.face((ii[-1][k],ii[-1][(k+1)%res],vp),ma,True)
    f.face(list(reversed(ii[0])),ma,False)
def blade(f,start,end,r0,r1,d0,d1,ma=4):
    a=vd(start);b=vd(end);side=Vector((-(b-a).y,(b-a).x,0)).normalized()
    shape=[a-side*r0,b-side*r1,b+side*r1,a+side*r0]
    rows=[[q+Vector((0,0,d)) for q in shape] for d in (d0,d1)]
    ii=f.grid(rows,6,False,False,True);f.face(ii[-1],ma,False);f.face(list(reversed(ii[0])),6,False)
def star(f,x,z,d,r,angle=0.0):
    '''Five deeply cut tips and ten crisp facets; no blue jewel or solid disc.'''
    pts=[]
    for i in range(10):
        th=radians(90+angle)+2*pi*i/10;rr=r*(1 if not i%2 else .485);pts.append((cos(th)*rr,sin(th)*rr))
    rings=[]
    for scale,layer in [(.89,-.00048),(1.,-.00012),(.943,.00038),(.725,.00056)]:
        rings.append([(x+scale*xx,z+scale*zz,d+layer) for xx,zz in pts])
    ii=f.grid(rings,lambda i,k:(6 if i<1 else 5 if i==1 else 4),False,False,True)
    f.face(list(reversed(ii[0])),6,False); vc=f.vtx((x,z,d+r*.217))
    for k in range(10):f.face((ii[-1][k],ii[-1][(k+1)%10],vc),5 if (k+1)%2 else 4,False)
def chain(f,points,w,t):
    ps=list(map(vd,points));steps=len(ps)
    for j,P in enumerate(ps):
        tangent=(ps[min(j+1,steps-1)]-ps[max(0,j-1)]).normalized()
        lat=Vector((-tangent.y,tangent.x,0)).normalized();d=lat.cross(tangent).normalized()
        tilt=radians(14 if j%2==0 else 64);x=lat*cos(tilt)+d*sin(tilt)
        spacing=(ps[min(j+1,steps-1)]-ps[max(0,j-1)]).length/(2 if 0<j<steps-1 else 1)
        oval(f,P,w*.5,max(.00065,spacing*.80),t,x,tangent,5 if j%4==0 else 4,22)
def bezier(a,b,c,t):return (1-t)**2*vd(a)+2*(1-t)*t*vd(b)+t*t*vd(c)

def make_brooch():
    f=Form();r=.01825
    f.part('primary gilt annulus with recessed inside shoulder');bezel(f,0,0,r,r,0,.00308,-.0005,.00175,.00034)
    f.part('inset graduated brass rim');bezel(f,0,0,r-.00114,r-.00114,0,.00037,.00157,.00194,.00009)
    f.part('fine outer burnished rim');bezel(f,0,0,r+.00099,r+.00099,0,.00021,.00166,.00190,.000055)
    for i in range(32):
        t=2*pi*i/32;h=.00048 if i%4 else .00089;w=.000105 if i%4 else .00016
        dis=r+.00029
        f.part('etched degree marks');blade(f,((dis-h/2)*cos(t),(dis-h/2)*sin(t),0),((dis+h/2)*cos(t),(dis+h/2)*sin(t),0),w,w,.00175,.00181,6)
    for deg in (91,218,302):
        t=radians(deg);extent=r+.0015
        f.part('three tapered openwork spokes');blade(f,(.0026*cos(t),.0026*sin(t),0),(extent*cos(t),extent*sin(t),0),.00135,.00047,-.00030,.00138)
        f.part('fine filed shoulders on spokes');blade(f,(.0033*cos(t),.0033*sin(t),0),((extent-.0012)*cos(t),(extent-.0012)*sin(t),0),.00025,.00012,.00136,.00147,5)
    f.part('oblique raised ecliptic band crossing both faces')
    bezel(f,0,0,.02720,.00355,34,.00151,.00185,.00302,.00026,.00210,124)
    f.part('tapered globe axis and rivet');dome(f,0,0,.00427,.0017,.00243,4)
    bezel(f,0,0,.00277,.00277,0,.00048,.00389,.00431,.00010,n=40)
    dome(f,0,0,.00245,.00400,.00066,7,res=34)
    f.part('upper suspension stud and hoop');dome(f,0,r+.0025,.00135,.0001,.00178,4,rz=.00191,res=28)
    oval(f,(0,r+.0054,.00110),.00219,.00264,.00068,m=4)
    # Secondary pin and short loose fine safety chain seen on the chest in the concept.
    # The garment-specific pin feet are attached behind the rear annulus in fit.py.
    f.part('short loose safety chain');chain(f,[bezier((.0142,-.0119,.00046),(.0196,-.038,.00238),(-.0088,-.0157,.00142),i/17) for i in range(18)],.00204,.00029)
    f.part('safety chain eye');oval(f,(-.0088,-.0157,.00128),.00064,.00108,.00028,m=4,res=24)
    return f

def bowd(x,z):
    # The garment centre has longitudinal pitch and recedes toward the shoulder.
    return -.17*z-2.65*x*x
def bow_loop(f,sgn,darker=False):
    name=('L' if sgn>0 else 'R')+(' lower gather' if darker else ' outer loop')
    f.part(name)
    rows=[]
    n=72;kseg=17
    for it in range(n):
        th=2*pi*(it/n); t=(1-cos(th))*.5; wave=sin(th)
        row=[]
        for j in range(kseg):
            u=2*j/(kseg-1)-1
            side=1 if sgn==1 else -1
            rad=1.103*(.0495 if not darker else .0464)*(1. if sgn==-1 else 1.025)
            xx=sgn*(.00195+rad*t+.00185*u*t+.0012*(1-u*u)*t)
            mid=(-.00765*t+.0014*sin(pi*t)+(-.0018 if darker else 0)+(.0011 if sgn>0 else -.00045)*t)
            half=(.0044+.0122*t**.73) if not darker else (.00445+.0118*t**.73)
            z=mid+u*half*1.085*(1-.07*abs(wave))+.0019*wave*t*(1.1-u*.35)
            if darker:z-=.0022*t
            front=max(0,wave);back=max(0,-wave)
            gather=.00124*(1-t)**.62 * (.28*cos(pi*u)+.75*cos(2.19*pi*u+(.45 if sgn>0 else -.32)))
            d=bowd(xx,z)+.00265+(0 if not darker else -.00285)
            d+=wave*(.0034+.0065*sin(pi*t)**.82)+.0014*t+.0018*t*(1-u*u)
            d+=gather*(.4+.60*front)-.0007*back*(1-u*u)
            row.append((xx,z,d))
        rows.append(row)
    # The loop is a solid folded silk band with a 0.52 mm binding along both edges.
    ii=f.grid(rows,lambda i,j:(1 if darker or i>n//2 else (3 if sgn<0 else 0)),True,True,False)
    inner=[[(x,z,d-.00049) for x,z,d in row] for row in rows]
    jj=f.grid(inner,1,True,True,False)
    for i in range(n):
        for j in (0,kseg-1):f.face((ii[i][j],ii[(i+1)%n][j],jj[(i+1)%n][j],jj[i][j]),2,True)
    # Faired rim at top and bottom of folded silk. This occupies a fraction of a pixel on the full body.
    for j in (0,kseg-1):
        f.part(name+' piped silk edge');tube(f,[row[j] for row in rows],.00031,2,7,True)
def tailpoint(side,t,u):
    # Lower folds fall towards shirt rather than extending in a flat bow plane.
    if side<0:
        midx=-.0037-.0257*t-.0022*sin(t*pi);ln=.0711;tx=-.0024*sin(pi*t*1.35)
    else:
        midx=.0028+.0225*t+.0027*sin(t*pi);ln=.0769;tx=.0037*sin(t*pi*1.37)
    half=(.0037+.0087*(sin(pi*t*.52)**.74))*1.065
    x=midx+u*half+tx;z=-.0008-ln*t+u*(.0024*t+.0026*t**3)*(1 if side<0 else -1)
    d=bowd(x,z)+.0033+.0011*sin(t*6.5+side*.45)+.0021*(1-u*u)*sin(pi*t*.95)+.00085*u*sin(t*pi)
    return (x,z,d)
def make_tail(f,side):
    f.part(('L' if side>0 else 'R')+' bias cut hanging tail')
    rr=[[tailpoint(side,i/32,2*j/12-1) for j in range(13)] for i in range(33)]
    top=f.grid(rr,0,True)
    rev=[[(x,z,d-.00062) for x,z,d in row] for row in rr]
    bot=f.grid(rev,1,True)
    for i in range(len(rr)-1):
        for k in (0,len(rr[0])-1):f.face((top[i][k],top[i+1][k],bot[i+1][k],bot[i][k]),2)
    for i in (0,len(rr)-1):
        for k in range(len(rr[0])-1):f.face((top[i][k],top[i][k+1],bot[i][k+1],bot[i][k]),2)
    f.part('woven gold end stripe')
    trim=[]
    for v in (0,1):
        row=[]
        for j in range(23):
            u=2*j/22-1;t=.868+.019*v+(.016*u if side<0 else -.012*u);x,z,d=tailpoint(side,t,u);row.append((x,z,d+.00019))
        trim.append(row)
    f.grid(trim,5,True)
def make_bow():
    f=Form()
    for s in (-1,1):make_tail(f,s)
    for s in (-1,1):bow_loop(f,s,True)
    for s in (-1,1):bow_loop(f,s,False)
    f.part('gathered central fabric keeper');dome(f,-.0002,-.0002,.0088,.00315,.0101,3,rz=.0111,res=48)
    # Fine actual articulated links: from the keeper arch to the near five-point star.
    f.part('near gold link under the keeper');oval(f,(.00020,.0064,.01340),.00115,.00187,.00036,m=5)
    f.part('upper five-point drop');star(f,.00046,-.0014,.0129,.01115,-5)
    f.part('long foil chain across the left fold')
    path=[]
    for i in range(17):
        t=i/16;z=-.0087-.0379*t;x=-.00068-.00615*t-.00125*sin(pi*1.25*t);d=bowd(x,z)+.0062+.0035*(1-t)+.0011*sin(pi*t);path.append((x,z,d))
    chain(f,path,.00218,.00033)
    f.part('second independent lower star eye');oval(f,(-.0060,-.0474,bowd(-.0060,-.0474)+.00595),.00122,.00165,.00035,m=4)
    f.part('pendant five-point drop');star(f,-.0061,-.0554,bowd(-.0061,-.0554)+.00595,.00875,11)
    return f

def build(setup=None,scene=None):
    mats0=mats();scene=scene or bpy.context.scene
    col=bpy.data.collections.new('SUZU_TOP_JEWELRY');scene.collection.children.link(col)
    cfg=setup or DEFAULT
    a=make_bow().finalize('Suzu C · Silk bow and two stellar drops','bow',col,cfg['bow'],mats0)
    b=make_brooch().finalize('Suzu C · Left engraved astrolabe','brooch',col,cfg['brooch'],mats0)
    return col,a,b

if __name__=='__main__':
    import sys
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    cfg=json.loads(Path(args[0]).read_text()) if args else DEFAULT
    target=Path(args[1]) if len(args)>1 else D/'suzu_top_jewelry.blend'
    bpy.ops.wm.read_factory_settings(use_empty=True);c,a,b=build(cfg)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(target.resolve()),compress=True)
    print('Wearable modules',[(x.name,len(x.data.vertices),len(x.data.polygons)) for x in (a,b)])

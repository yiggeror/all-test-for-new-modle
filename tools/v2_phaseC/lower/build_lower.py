"""Tailored Phase C lower rig-ready geometry, fitted to the frozen official body."""
import sys
import argparse
from pathlib import Path
from math import sin, cos, sqrt, pi, exp, atan2
from bisect import bisect_right
from collections import defaultdict
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

tau = 2*pi
V=Vector

def smooth(a, b, x):
    t=min(1.,max(0.,(x-a)/(b-a))); return t*t*(3.-2.*t)

def mix(a,b,x):return a*(1.-x)+b*x

def interp(keys,x):
    """Monotone cubic with a true end tangent; stays within all design stations."""
    coords=[k[0] for k in keys]
    if x<=coords[0]:return keys[0][1]
    if x>=coords[-1]:return keys[-1][1]
    i=bisect_right(coords,x)-1
    a,va=keys[i];b,vb=keys[i+1];d=b-a;t=(x-a)/d
    s=(vb-va)/d
    def slope(s1,s2):return 0. if s1*s2<=0. else 2.*s1*s2/(s1+s2)
    m1=s if i==0 else slope((va-keys[i-1][1])/(a-keys[i-1][0]),s)
    m2=s if i==len(keys)-2 else slope(s,(keys[i+2][1]-vb)/(keys[i+2][0]-b))
    return (2*t**3-3*t*t+1)*va+(t**3-2*t*t+t)*m1*d+(-2*t**3+3*t*t)*vb+(t**3-t*t)*m2*d

def rgb(hexcode):
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
                 for v in [int(hexcode[i:i+2],16)/255. for i in (0,2,4)])

def mat(name,hexcode,rough,metal=0.,spec=.35,lift=.20,coat=0.):
    m=bpy.data.materials.new('Suzu C · '+name); m.use_nodes=True
    c=rgb(hexcode);m.diffuse_color=(*c,1)
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*c,1.)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    p.inputs['Specular IOR Level'].default_value=spec
    p.inputs['Coat Weight'].default_value=coat
    p.inputs['Coat Roughness'].default_value=min(.34,rough)
    p.inputs['Emission Color'].default_value=(*c,1.)
    p.inputs['Emission Strength'].default_value=lift
    return m

class BodyEnvelope:
    def __init__(self,obj):
        self.obj=obj;self.verts=[obj.matrix_world@v.co for v in obj.data.vertices]
        self.faces=[tuple(p.vertices) for p in obj.data.polygons]
        self.edges=[tuple(e.vertices) for e in obj.data.edges]
        self.bvh=BVHTree.FromPolygons(self.verts,self.faces)
        self.rows={};self.hulls={}
        self.normals=[obj.matrix_world.to_3x3()@v.normal for v in obj.data.vertices]
    def smooth_normal(self,p):
        f,n,i,d=self.bvh.find_nearest(p)
        if f is None or len(self.faces[i])!=3:return n
        ia,ib,ic=self.faces[i]
        a,b,c=self.verts[ia],self.verts[ib],self.verts[ic]
        e0=b-a;e1=c-a;e=f-a
        uu=e0.dot(e0);uv=e0.dot(e1);vv=e1.dot(e1);du=e.dot(e0);dv=e.dot(e1)
        den=uu*vv-uv*uv
        if abs(den)<1.e-14:return n
        beta=(vv*du-uv*dv)/den;gamma=(uu*dv-uv*du)/den
        A=(1.-beta-gamma)*self.normals[ia]+beta*self.normals[ib]+gamma*self.normals[ic]
        return A.normalized()
    def waist(self,z,a):
        center=V((0,-.032,z));d=V((sin(a),-cos(a),0.))
        hit,n,i,r=self.bvh.ray_cast(center,d,.183)
        if hit is None:raise ValueError(f'unavailable waist at z={z}, a={a}')
        return hit,d
    def section_points(self,s,z):
        pts=[]
        for i,j in self.edges:
            a,b=self.verts[i],self.verts[j]
            if min(a.z,b.z)<=z<=max(a.z,b.z) and abs(a.z-b.z)>1.e-8:
                v=a.lerp(b,(z-a.z)/(b.z-a.z))
                if v.x*s>.010 and abs(v.x)<.190:pts.append(v)
        if not pts:raise ValueError(f'Empty leg crossing {s}:{z}')
        return pts
    def leg_center(self,s,z):
        k=(s,round(z,7))
        if k not in self.rows:
            pts=self.section_points(s,z)
            self.rows[k]=V(tuple((min(p[i] for p in pts)+max(p[i] for p in pts))*.5 for i in range(2))+(z,))
        return self.rows[k]
    def foot_knit(self,s,z,angle):
        k=(s,round(z,7));c=self.leg_center(s,z)
        if k not in self.hulls:
            pts=self.section_points(s,z)
            q=sorted(set((round(p.x-c.x,8),round(p.y-c.y,8)) for p in pts))
            def cr(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            def walk(qq):
                out=[]
                for p in qq:
                    while len(out)>=2 and cr(out[-2],out[-1],p)<=1.e-10:out.pop()
                    out.append(p)
                return out[:-1]
            self.hulls[k]=walk(q)+walk(q[::-1])
        poly=self.hulls[k];dx,dy=sin(angle),-cos(angle);best=0.
        for A,B in zip(poly,poly[1:]+poly[:1]):
            ax,ay=A;ex,ey=B[0]-ax,B[1]-ay
            det=dx*ey-dy*ex
            if abs(det)<1.e-10:continue
            t=(ax*dy-ay*dx)/det
            if -.0001<=t<=1.0001:
                r=(ax*ey-ay*ex)/det
                if r>best:best=r
        return c+V((dx,dy,0))*best
    def foot_center(self,s,z):
        z0=int(z/.003)*.003
        a=self.leg_center(s,z0);b=self.leg_center(s,z0+.003)
        return a.lerp(b,(z-z0)/.003)
    def fitted_collar(self,s,p,gap):
        c=self.foot_center(s,p.z);d=(p-c).normalized()
        h,_,_,_=self.bvh.ray_cast(c,d,.103)
        return h+d*gap if h else p
    def leg(self,s,z,a):
        c=self.leg_center(s,z);d=V((sin(a),-cos(a),0.))
        hit,n,i,r=self.bvh.ray_cast(c,d,.072 if z>.095 else .128)
        if hit is None:
            hit,n,i,r=self.bvh.ray_cast(c+d*.14,-d,.163)
        if hit is None or hit.x*s<=.001:
            raise ValueError(f'unavailable leg {s} z={z} a={a}')
        return hit,d
    def keep_outside_hips(self,x,y,z,cy,clearance,narrow=.0056):
        c=V((0.,cy,z));p=V((x,y,z));v=p-c;r=v.length
        if r<1.e-8:return p
        d=v/r
        h,_,_,_=self.bvh.ray_cast(c+d*.209,-d,.208)
        if h is None:return p
        # Smooth maximum gives the fabric a sewn rather than polygonal body-hug.
        diff=(h-c).length+clearance-r
        out=.5*(diff+sqrt(diff*diff+narrow*narrow))
        return p+d*out
    def foot_top(self,x,y,z=.112):
        h,_,_,_=self.bvh.ray_cast(V((x,y,z)),V((0,0,-1)),.110)
        return h.z if h else 0.

def entry(name,v,polygons,mats,indices=None,uv=None,role=None,weight='body'):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(v,[],polygons);mesh.update()
    obj=bpy.data.objects.new(name,mesh);C.objects.link(obj)
    for m in mats:mesh.materials.append(m)
    for i,p in enumerate(mesh.polygons):
        p.use_smooth=True
        if indices is not None:p.material_index=indices[i]
    layer=mesh.uv_layers.new(name='Tailor pattern')
    if uv:
        for lp in mesh.loops:layer.data[lp.index].uv=uv[lp.vertex_index]
        # Wrap UVs at the closure without stretching across the whole pattern.
        for p in mesh.polygons:
            xs=[layer.data[i].uv.x for i in p.loop_indices]
            if len(xs)<5 and min(xs)<.10 and max(xs)>.90:
                for i in p.loop_indices:
                    if layer.data[i].uv.x<.10:layer.data[i].uv.x+=1.
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(mesh);bm.free();mesh.update()
    obj['suzu_lower_role']=role
    obj['suzu_lower_weight']=weight
    obj['suzu_stage_role']='phase_c_garment'
    return obj

def series(name,outer,mats,role,weight='body',inset=.0015,direction=None,index=None,
           closed=True,inner=None,all_smooth=True):
    """A lined garment patch. Both face layers, top/bottom lips and open edges are real."""
    m,n=len(outer),len(outer[0])
    if not inner:
        inner=[]
        for j,row in enumerate(outer):
            ir=[]
            for i,v in enumerate(row):
                if direction:
                    d=direction(j,i,v)
                else:
                    tangent=row[(i+1)%n if closed else min(n-1,i+1)]-row[(i-1)%n if closed else max(0,i-1)]
                    zdir=outer[min(m-1,j+1)][i]-outer[max(0,j-1)][i]
                    d=zdir.cross(tangent).normalized()
                ir.append(v-d*(inset(j,i,v) if callable(inset) else inset))
            inner.append(ir)
    verts=[p for layer in (outer,inner) for row in layer for p in row]
    denom=n if closed else (n-1)
    uv=[(i/denom,j/(m-1)) for _ in (0,1) for j in range(m) for i in range(n)]
    faces=[];mis=[]
    def add(poly,k=0):faces.append(poly);mis.append(k)
    off=m*n
    for j in range(m-1):
        for i in range(denom):
            h=(i+1)%n;a=j*n+i;b=j*n+h;c=(j+1)*n+h;d=(j+1)*n+i
            add((a,d,c,b),index(j,i) if index else 0);add((a+off,b+off,c+off,d+off),0)
    for j in (0,m-1):
        for i in range(denom):
            a=j*n+i;b=j*n+(i+1)%n
            add((a,b,b+off,a+off),0)
    if not closed:
        for i in (0,n-1):
            for j in range(m-1):
                a=j*n+i;b=(j+1)*n+i
                add((a,b,b+off,a+off),0)
    obj=entry(name,verts,faces,mats,mis,uv,role,weight)
    if not all_smooth:
        for p in obj.data.polygons:p.use_smooth=False
    return obj

def solid_loft(name,rings,mats,role,weight='body',index=None,flatcaps=False,stripcaps=False):
    n=len(rings[0]);m=len(rings);verts=[v for row in rings for v in row]; uv=[(i/n,j/(m-1)) for j in range(m) for i in range(n)];faces=[];mis=[]
    for j in range(m-1):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n;c=b+n;d=a+n
            faces.append((a,b,c,d));mis.append(index(j,i) if index else 0)
    cap_start=len(faces)
    if stripcaps:
        # Opposite-boundary stations share Y, so the real cross sections
        # remain true on the canted outsole: no giant non-planar n-gon diagonals.
        assert n%2==0
        for j in (0,m-1):
            for i in range(n//2):
                corners=list(dict.fromkeys(j*n+k for k in (i,i+1,(n-i-1)%n,(n-i)%n)))
                faces.append(tuple(corners));mis.append(0)
    else:
        faces.extend([tuple(range(n))[::-1],tuple(range((m-1)*n,m*n))]);mis.extend([0,0])
    o=entry(name,verts,faces,mats,mis,uv,role,weight)
    if flatcaps:
        for p in list(o.data.polygons)[cap_start:]:p.use_smooth=False
    return o

def tube(name,path,r,m,role,weight='body',sides=7):
    rings=[]; n=len(path)
    for i,p in enumerate(path):
        T=(path[(i+1)%n]-path[(i-1)%n]).normalized()
        u=V((0,0,1)).cross(T).normalized();v=T.cross(u).normalized()
        if u.length<.9:u=V((1,0,0)).cross(T).normalized();v=T.cross(u).normalized()
        rings.append([p+r*(u*cos(j*tau/sides)+v*sin(j*tau/sides)) for j in range(sides)])
    verts=[p for row in rings for p in row];f=[]
    for i in range(n):
        I=(i+1)%n
        for j in range(sides):
            J=(j+1)%sides
            f.append((i*sides+j,i*sides+J,I*sides+J,I*sides+j))
    return entry(name,verts,f,[m],uv=[(i/n,j/sides) for i in range(n) for j in range(sides)],
                 role=role,weight=weight)

PANEL_N=13
fold_profile=[
    (0.,0.,-.62),(.06,.057,-.62),(.10,.096,-.55),(.16,.115,-.30),
    (.24,.096,.22),(.31,.078,.57),(.35,.095,.79),(.40,.136,.83),
    (.48,.239,.64),(.59,.42,.39),(.70,.60,.21),(.80,.751,-.01),(.89,.876,-.31),(.96,.959,-.54)]
def panel_angle(i,j,u):
    q,a,d=fold_profile[j]; base=i*tau/PANEL_N; da=tau/PANEL_N
    ripple=.105*da*sin(base*3+.48)+.05*da*sin(base*7-.6)
    endbase=base+da
    next_ripple=.105*da*sin(endbase*3+.48)+.05*da*sin(endbase*7-.6)
    move=mix(q,a,smooth(.02,.58,u))
    return base+mix(ripple,next_ripple,move)+da*move-.110+.035*u*mix(sin(base*2+.4),sin(endbase*2+.4),move),d

def flare(u):
    return 1.+.125*smooth(.14,1.,u)

def skirt_hem(a):
    return .732+.013*sin(a)**2-.0033*cos(a)+.0030*sin(3*a+.4)+.0017*cos(7*a-.2)

SX=[(0.,.096),(.13,.112),(.31,.133),(.46,.157),(.62,.180),(.77,.205),(.91,.223),(1.,.234)]
SY=[(0.,.070),(.12,.079),(.25,.096),(.38,.113),(.58,.128),(.76,.147),(.91,.160),(1.,.168)]
CY=[(0.,-.032),(.15,-.024),(.32,-.014),(.59,-.004),(1.,.005)]

def make_waist():
    n=160; svals=[0,.035,.08,.17,.29,.42,.56,.70,.84,.93,.975,1.]
    r=[]
    for u in svals:
        rr=[]
        for i in range(n):
            a=i*tau/n; bottom=.988+.0028*sin(a)**2; top=1.053+.004*sin(a)**2
            z=mix(bottom,top,u);p,d=B.waist(z,a)
            strength=.01045+.00070*sin(pi*u)-.00045*cos(pi*u)**10
            rr.append(p+d*strength)
        r.append(rr)
    o=series('C · Fitted raised waistband',r,[cloth,waist_edge],'waist',
             direction=lambda j,i,v:V((sin(i*tau/n),-cos(i*tau/n),0)),inset=.00215,
             index=lambda j,i:int(j in (0,len(r)-2)))
    for key,u in [('topstitch low',.10),('topstitch top',.89)]:
        pts=[]
        for i in range(n):
            a=i*tau/n;bottom=.988+.0028*sin(a)**2;top=1.053+.004*sin(a)**2
            p,d=B.waist(mix(bottom,top,u),a);pts.append(p+d*.01115)
        tube('C · Waist '+key,pts,.00048,waist_edge,'waist-stitch')
    return o

def make_outer():
    r=[]; uvals=[0.,.02,.045,.080,.12,.17,.225,.29,.36,.44,.52,.61,.69,.77,.83,.884,.928,.947,.954,.965,.974,.982,.993,1.]
    for u in uvals:
        rr=[]
        for i in range(PANEL_N):
            for j in range(len(fold_profile)):
                a,d=panel_angle(i,j,u)
                ztop=.996+.003*sin(a)**2
                he=skirt_hem(a)-.0022*d
                z=mix(ztop,he,u);cy=interp(CY,u)
                amp=(.001+.0237*u**.82)*smooth(.004,.18,u)*(1.+.09*sin(3*a-.8))
                dr=d*amp
                x=(interp(SX,u)*flare(u)+dr)*sin(a)
                y=cy-(interp(SY,u)*flare(u)+dr)*cos(a)
                if u<.15:
                    p,U=B.waist(ztop,a);p=p+U*.00830
                    t=smooth(.0,.151,u)
                    x=mix(p.x+(x-p.x)*.16*u/.15,x,t)
                    y=mix(p.y+(y-p.y)*.16*u/.15,y,t)
                rr.append(B.keep_outside_hips(x,y,z,cy,.00615+.00585*smooth(.024,.137,u),.0020+.0036*smooth(.025,.21,u)))
        r.append(rr)
    o=series('C · Thirteen tailored knife pleats',r,[cloth,cloth_fold,gold,cloth_hem],
             'pleats','skirt',inset=.00095,
             index=lambda j,i:2 if j in (18,20) else (3 if j>=21 else (1 if i%len(fold_profile) in (1,2,3,4) else 0)))
    o['panel_count']=PANEL_N;o['gold_slot']=2;o['hem_grade']=1.125;return o

def make_lining():
    n=260;svals=[0,.04,.10,.17,.23,.29,.37,.46,.54,.63,.72,.80,.85,.88,.90,.92,.94,.955,.970,.986,1.]
    r=[]
    for u in svals:
        rr=[]
        for i in range(n):
            a=i*tau/n;he=skirt_hem(a)
            ztop=.990+.003*sin(a)**2
            zh=he-.026
            z=mix(ztop,zh,u)
            g=smooth(.83,1.,u)
            phase=27*a+.47*sin(7*a)+.24*cos(13*a)
            fold=(sin(phase)*(.0042+.00165*wavy(a))+.0014*sin(2*phase+.65))*g
            lv=smooth(.93,.994,u)
            f=min(1.,u*1.088)
            center=interp(CY,f)
            dr=-.024+.0105*lv+fold
            x=(interp(SX,f)*flare(f)+dr)*sin(a)
            y=center-(interp(SY,f)*flare(f)+dr)*cos(a)
            if u<.115:
                p,U=B.waist(ztop,a);p=p+U*.0041;t=smooth(.0,.115,u)
                x=mix(p.x+(x-p.x)*.13*u/.115,x,t)
                y=mix(p.y+(y-p.y)*.13*u/.115,y,t)
            z+=g*(.0019*cos(phase+.16)+.0012*cos(6*a-.8)+.0011*sin(15*a-.5))
            rr.append(B.keep_outside_hips(x,y,z,center,.0052,.0028+.0014*smooth(.15,.25,u)))
        r.append(rr)
    return series('C · Ivory separate softly gathered underdress',r,[ivory,ivory_fold,ivory_edge],
                  'ivory','skirt',inset=lambda j,i,p:.00089+.00066*smooth(.83,1.,svals[j]),
                  index=lambda j,i:2 if j>=len(r)-2 else (1 if j>=14 and cos(tau*27*(i+.5)/n+.47*sin(tau*7*i/n))>.76 else 0))

def wavy(a):return .55*sin(4*a-.4)+.45*cos(9*a+.8)

SOCK_Z={1:.607,-1:.586}
def sock_point(s,z,a,puff=.00172):
    zu=SOCK_Z[s]
    p,d=B.leg(s,z,a)
    if z<.048:
        p=p.lerp(B.foot_knit(s,z,a),1.-smooth(.030,.048,z))
    upper=.00086*smooth(zu-.035,zu-.019,z)-.00029*smooth(zu-.005,zu,z)
    return p+d*(puff+upper+.00195*exp(-((z-.043)/.021)**2))
def make_sock(s):
    n=128; label='Left' if s>0 else 'Right';zt=SOCK_Z[s]
    zvals=sorted({round(z,6) for z in [.0159,.0196,.0232,.0255,.028,.034,.040,.044,.049,.055,.060,.066,.071,.077,.083,.089,.094,.100,
       *[.106+i*.006 for i in range(80) if .106+i*.006<zt-.034],
       zt-.034,zt-.030,zt-.026,zt-.018,zt-.0125,zt-.0102,zt-.004,zt-.0013,zt]})
    r=[]
    for z0 in zvals:
        rr=[]
        for i in range(n):
            a=i*tau/n;z=z0+.0023*smooth(zt-.06,zt-.015,z0)*cos(a-.11*s)
            rr.append(sock_point(s,z,a,.00204))
        r.append(rr)
    # Quiet sub-millimetre knit fairing, then transfer the base's smoothly
    # interpolated normals, rather than exposing low-poly vertex columns.
    for j in range(2,len(r)-4):
        cur=r[j]
        nr=[]
        for i in range(n):
            p=cur[i]; avg=(cur[(i-3)%n]+cur[(i+3)%n]+r[j-1][i]+r[j+1][i])*.25
            d=avg-p;d.z=0.
            if d.length>.0016:d.normalize();d*=.0016
            nr.append(p+d*.29)
        r[j]=nr
    o=series('C · '+label+' anatomically fitted silk-knit stocking',r,[stock,cuff,gold_silk],'sock',
                  inset=.00054,direction=lambda j,i,v:V((sin(i*tau/n),-cos(i*tau/n),0.)),
                  index=lambda j,i:2 if j==len(r)-5 else int(j>=len(r)-9))
    surf=o.data;n0=[x.vector.copy() for x in surf.corner_normals]
    target=[B.smooth_normal(v.co) for v in surf.vertices]
    nn=[]
    for loop in surf.loops:
        vi=loop.vertex_index;p=surf.vertices[vi].co;n=target[vi];oN=n0[loop.index]
        f=.93*smooth(.024,.046,p.z)*smooth(.0028,.010,zt-p.z)
        if n is None or n.dot(oN)<.62:f=0.
        nn.append(oN.lerp(n,f).normalized() if f else oN)
    surf.normals_split_custom_set(nn)
    return o
def make_garter():
    n=120;zs=[.6337,.6344,.6357,.6378,.6404,.6431,.6455,.6468]
    leg=-1; a0=-.105
    r=[]
    for z in zs:
        row=[]
        for i in range(n):
            a=i*tau/n;zz=z+.0021*cos(a-.2);p,d=B.leg(leg,zz,a)
            row.append(p+d*(.00245+.00044*sin(pi*(z-zs[0])/(zs[-1]-zs[0]))))
        r.append(row)
    series('C · Wearer-right single silk garter',r,[cuff,waist_edge],'garter',inset=.00105,
           direction=lambda j,i,v:V((sin(i*tau/n),-cos(i*tau/n),0.)),
           index=lambda j,i:int(j in (0,len(r)-2)))
    r=[]
    for z in [.5804,.584,.590,.599,.609,.619,.629,.6366,.6424]:
        row=[];angle=a0+.023*sin(pi*(z-.58)/.063)
        for i in range(9):
            a=angle+(i/8-.5)*.163;p,d=B.leg(leg,z,a)
            off=.00352+.00092*smooth(.615,.640,z)
            row.append(p+d*(off+.00044*sin(pi*i/8)))
        r.append(row)
    series('C · Wearer-right vertical silk link',r,[cuff,waist_edge],'garter-link',
           inset=.00105,closed=False,direction=lambda j,i,v:V((sin(a0),-cos(a0),0.)),
           index=lambda j,i:int(i in (0,7)))
    z=.644;p,D=B.leg(leg,z,a0)
    U=V((cos(a0),sin(a0),.11));up=V((0,0,1.));U=U.normalized()
    C0=p+D*.00435
    profiles=[(.0000,1.00),(.0012,1.00),(.00255,.877),(.00337,.827)]
    rings=[]
    for depth,scale in profiles:
        row=[]
        for k in range(10):
            a=k*tau/10.;rr=(.0111 if k%2==0 else .00495)*scale
            row.append(C0+U*(rr*sin(a))+up*(rr*cos(a))+D*depth)
        rings.append(row)
    o=solid_loft('C · Garter five-point antique-gold relief',rings,[gold_metal,gold_dim],'garter-star',
                 index=lambda j,i:j==0,flatcaps=True)
    # Add a central faceted highlight, not a screen-facing decal.
    p0=C0+D*.00318
    r=[[p0+D*w+(U*sin(k*tau/5)+up*cos(k*tau/5))*r for k in range(5)] for r,w in [(.0031,0),(.0024,.001)]]
    solid_loft('C · Garter star cut center',r,[gold_metal],'garter-jewel',flatcaps=True)

PROFILE=[(-.136,0.),(-.1345,.0082),(-.130,.0167),(-.122,.0267),(-.112,.0350),(-.099,.0395),
         (-.084,.043),(-.067,.0438),(-.048,.0439),(-.033,.0418),(-.019,.0372),(-.006,.0340),
         (.010,.0323),(.027,.0338),(.043,.0339),(.056,.0315),(.069,.0264),(.078,.0198),(.083,.011),(.085,0.)]
CENTER=[(-.136,.0754),(-.101,.0780),(-.055,.0808),(-.019,.0804),(.030,.0785),(.071,.0752),(.085,.0753)]
YR=.1105; YC=-.0255
BOT=[(-.136,.0033),(-.126,.0018),(-.109,.0),(-.038,.0),(-.028,.0007),(-.013,.0050),
     (.002,.0057),(.010,.0035),(.019,.00185),(.028,.00115),(.034,.00145),(.047,.0089),
     (.062,.011),(.074,.0145),(.085,.016)]
UP=[(-.136,.0147),(-.118,.0147),(-.093,.0170),(-.058,.0171),(-.026,.0180),(.014,.0230),(.053,.0256),(.085,.0250)]

def perimeter(s,a,scale=1.,translate=0):
    y=YC-YR*cos(a)
    x=interp(CENTER,y)+scale*(1. if sin(a)>0 else -1.)*interp(PROFILE,y)+translate
    return s*x,y
def shoe_sole(s,n):
    r=[]
    for inset,low_mix in [(.0026,.0),(.0009,.12),(0.,.34),(.0,.65),(.00045,.84),(.00135,1.)]:
        row=[]
        for i in range(n):
            a=i*tau/n;x,y=perimeter(s,a)
            xb=s*interp(CENTER,y);d=V((x-xb,y-YC,0)).normalized()
            bp=interp(BOT,y);up=interp(UP,y)
            row.append(V((x-d.x*inset,y-d.y*inset,mix(bp,up,low_mix))))
        r.append(row)
    o=solid_loft('C · '+side_name(s)+' rounded beveled sole',r,[sole,welt,sole_light],'shoe-sole',
                 'shoe'+str(s),index=lambda j,i:1 if j==4 else (2 if j==2 else 0),flatcaps=True,stripcaps=True)
    heelr=[]
    for uu,wide in [(0,.88),(.14,.94),(.43,.975),(.87,1.),(1.,.945)]:
        row=[]
        for i in range(72):
            a=i*tau/72.;sx=sin(a);co=cos(a);p=.63
            y=.054- .030*(0.95+.05*uu)*wide*(1 if co>=0 else -1)*abs(co)**p
            x=s*(.0768+ .0295*wide*(1 if sx>=0 else -1)*abs(sx)**.79+.006*(y-.054))
            z=.0204*uu
            row.append(V((x,y,z)))
        heelr.append(row)
    solid_loft('C · '+side_name(s)+' rounded low stacked heel',heelr,[sole,sole_light],'heel','foot'+str(s),
               index=lambda j,i:1 if j==0 else 0,flatcaps=True)
    return o
def side_name(s):return 'Left' if s>0 else 'Right'

def shoe_collar(s,a):
    c=cos(a);q=sin(a)
    rear=(1.-c)*.5;medial=max(0.,-q)
    x=s*(.0791+q*(.0290+.0105*rear+.0037*medial*rear))
    y=.014-(.064+(.004*c))*c
    y+=.0013*sin(a-.19)+.0058*max(0.,-c)**.7
    z=.049+(.0305)*(1.-c)*.5+.0029*max(0.,-c)**3-.0032*q
    p=V((x,y,z))
    if c<.08:
        u=smooth(-.08,.83,-c)
        p=p.lerp(B.fitted_collar(s,p,.0056),u*.98)
    return p
def crossing_xy(C,d,ring):
    best=None;far=-1.
    for A,B in zip(ring,ring[1:]+ring[:1]):
        a=A-C;e=B-A
        det=d.x*e.y-d.y*e.x
        if abs(det)<1.e-10:continue
        t=(a.x*d.y-a.y*d.x)/det
        if -.0001<=t<=1.0001:
            r=(a.x*e.y-a.y*e.x)/det
            if r>far:
                best=A.lerp(B,t);far=r
    assert best is not None
    return V((C.x+d.x*far,C.y+d.y*far,best.z)),far

def make_shoe(s):
    n=176; shoe_sole(s,n)
    Cxy=V((s*.0788,.026,0))
    p_out=[];p_in=[]
    for i in range(2*n):
        a=i*tau/(2*n);x,y=perimeter(s,a)
        p_out.append(V((x,y,interp(UP,y)-.0022)))
        p_in.append(shoe_collar(s,a))
    D=[];start=[];end=[]
    for i in range(n):
        a=i*tau/n;d=V((s*sin(a),-cos(a),0));D.append(d)
        O,ro=crossing_xy(Cxy,d,p_out);H,rh=crossing_xy(Cxy,d,p_in)
        if rh>ro-.003:
            # Keep horizontal cut strips noncrossing even in the narrow heel.
            O+=d*(rh-ro+.003)
        start.append(O);end.append(H)
    ts=[0.,.025,.055,.09,.133,.185,.253,.33,.413,.50,.585,.675,.75,.822,.88,.927,.962,.986,1.]
    def shell(i,t):
        a=i*tau/n
        O,H=start[i],end[i];p=O.lerp(H,t)
        front=max(0.,cos(a))
        u=1.-(1.-t)**mix(1.08,2.12,front)
        p.z=mix(O.z,H.z,u)+.0106*max(0.,sin(pi*t))*(.37+.63*front)
        return p
    # Both plies are graphs over one annulus. A vertical loft offset means every
    # cut strip remains ordered, including the tightmedial turn of the collar.
    R=[[shell(i,t) for i in range(n)] for t in ts]
    up=V((0,0,1))
    direction=lambda j,i,p:up
    obj=series('C · '+side_name(s)+' round-toe Mary Jane brushed calfskin',
               R,[leather,leather_edge,welt],'shoe-upper','shoe'+str(s),
               inset=lambda j,i,v:.00152-.00035*smooth(.78,.99,ts[j]),direction=direction,
               index=lambda j,i:1 if j in (0,17) else 0)
    rolled=[shell(i,.991)+up*.00044 for i in range(n)]
    tube('C · '+side_name(s)+' rolled leather throat edge',rolled,.00092,leather_edge,'shoe-rim','foot'+str(s))
    seam=[shell(i,.944)+up*.00042 for i in range(n)]
    tube('C · '+side_name(s)+' fine top stitch',seam,.00039,leather_stitch,'shoe-stitch','foot'+str(s))

    # Strap forms an independent bent leather ribbon on the actual foot cross section.
    vv=[obj.matrix_world@v.co for v in obj.data.vertices]
    BVH=BVHTree.FromPolygons(vv,[tuple(p.vertices) for p in obj.data.polygons])
    def shoe_top(x,y):
        h,_,_,_=BVH.ray_cast(V((x,y,.108)),V((0.,0.,-1)),.105)
        return h.z if h else -1.
    def strap_point(f,g):
        cc=.0794; xv=cc+(.0375)*(2*f-1.)
        x=s*xv;y=-.026+.0095*(2*f-1)+.0107*(g-.5)
        foot=B.foot_top(x,y)
        # Smoothly roll strap edges into the quarter while keeping center clear over the knit.
        vamp=shoe_top(x,y)
        anchor_w=max(smooth(.77,1.,f),1.-smooth(0,.23,f))
        arch=.053+.0175*max(0,sin(pi*f))**.78
        above=max(arch,foot+.0034,vamp+.00195)
        z=mix(above,max(.0438,vamp-.0026,foot+.0031),anchor_w)
        return V((x,y,z))
    w=9;n_strap=36
    r=[[strap_point(j/(n_strap-1),i/(w-1)) for i in range(w)] for j in range(n_strap)]
    strap=series('C · '+side_name(s)+' slim instep strap',r,[leather_strap,leather_edge],'shoe-strap','foot'+str(s),
          inset=.00150,direction=lambda j,i,v:V((0,0,1)),closed=False,
          index=lambda j,i:int(i in (0,w-2)))
    f=.823;center=strap_point(f,.50)
    U=(strap_point(f+.017,.50)-strap_point(f-.017,.50)).normalized()
    W=(strap_point(f,.87)-strap_point(f,.13)).normalized()
    N=U.cross(W)
    if N.z<0:N=-N
    N.normalize();W=N.cross(U).normalized()
    center+=N*.00150
    def rect(size):
        L,H,R=.0062*size,.0050*size,.00150*size
        coords=[]
        for j,(x,y) in enumerate([(L-R,H-R),(-L+R,H-R),(-L+R,-H+R),(L-R,-H+R)]):
            for k in range(5):
                a=(j+k*.25)*pi/2
                coords.append(U*(x+R*cos(a))+W*(y+R*sin(a)))
        return coords
    rings=[]
    for ratio,d in [(1,-.00108),(1,.00125),(.89,.00183),(.706,.00183),(.618,.00104),(.618,-.00108)]:
        rings.append([center+p+N*d for p in rect(ratio)])
    rfaces=[];ps=[v for row in rings for v in row];nn=len(rings[0])
    for j in range(len(rings)):
        J=(j+1)%len(rings)
        for i in range(nn):
            I=(i+1)%nn;rfaces.append((j*nn+i,j*nn+I,J*nn+I,J*nn+i))
    entry('C · '+side_name(s)+' miniature open antique-gold buckle',ps,rfaces,[gold_metal],
          uv=[(i/nn,j/len(rings)) for j in range(len(rings)) for i in range(nn)],role='shoe-buckle',weight='foot'+str(s))
    pinpath=[center+U*.0043+N*.0021,center-U*.00455+N*.00155]
    # Solid tiny prong as two rounded coaxial rings.
    rings=[]
    for k,(p,r) in enumerate([(pinpath[0],.00043),(pinpath[0]-U*.00028,.00051),
                 (pinpath[1]+U*.00016,.00046),(pinpath[1],.00032)]):
        rings.append([p+r*(W*cos(i*tau/8)+N*sin(i*tau/8)) for i in range(8)])
    solid_loft('C · '+side_name(s)+' buckle prong',rings,[gold_dim],'shoe-buckle-prong','foot'+str(s),flatcaps=True)

def main():
    global C,B,cloth,cloth_fold,cloth_hem,waist_edge,stock,cuff,ivory,ivory_fold,ivory_edge,gold,gold_silk,gold_metal,gold_dim,sole,welt,sole_light,leather,leather_edge,leather_strap,leather_stitch
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',required=True,type=Path);ap.add_argument('--module',type=Path)
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
    source=bpy.data.objects['Suzu · Body'];B=BodyEnvelope(source)
    C=bpy.data.collections.new('SUZU_PHASE_C_LOWER');bpy.context.scene.collection.children.link(C)
    cloth=mat('Midnight tailored twill','2F354F',.66,lift=.26)
    cloth_fold=mat('Indigo folded return','222947',.67,lift=.22)
    cloth_hem=mat('Turned navy hem','2D344F',.64,lift=.22)
    waist_edge=mat('Waistband tonal stitch','303850',.64,lift=.25)
    stock=mat('Dense navy stocking knit','293351',.70,lift=.31)
    cuff=mat('Double-knit stocking cuffs','28304B',.63,lift=.25)
    ivory=mat('Ivory petticoat silk','F2E4D9',.59,lift=.13)
    ivory_fold=mat('Ivory folded return','DFCFC2',.62,lift=.14)
    ivory_edge=mat('Ivory softly finished edge','F0DDCA',.57,lift=.13)
    gold=mat('Fine antique gold woven line','C5A37D',.39,.34,.46,.14)
    gold_silk=mat('Gilt thread at stockings','BFA582',.48,.22,.37,.18)
    gold_metal=mat('Polished antique brass','C5A37D',.29,.78,.48,.12)
    gold_dim=mat('Recessed antique brass','A68055',.33,.65,.42,.09)
    sole=mat('Navy-black leather outsole','1D243B',.55,lift=.22)
    welt=mat('Rolled matte navy welt','242B43',.53,lift=.25)
    sole_light=mat('Heel stack cut edge','303951',.53,lift=.22)
    leather=mat('Midnight calfskin shoe','272F4C',.37,.05,.45,.24,coat=.19)
    leather_edge=mat('Rolled shoe edge','35415D',.42,.05,.44,.23,coat=.09)
    leather_strap=mat('Glazed navy strap','323B57',.32,.06,.46,.26,coat=.21)
    leather_stitch=mat('Muted indigo leather topstitch','3C4663',.41,.02,.33,.22)
    make_waist();make_outer();make_lining()
    for s in (1,-1):make_sock(s);make_shoe(s)
    make_garter()
    C['suzu_phase']='C';C['fit_basis']='Locked Phase B Z-up, -Y anterior, +X wearer left'
    for o in C.objects:
        if o.type=='MESH' and o.get('suzu_lower_weight','')=='skirt':
            o['pleat_z_anchor']=.993;o['pleat_z_hem']=.732 if o.get('suzu_lower_role')=='pleats' else .708
    bpy.context.preferences.filepaths.save_version=0
    args.out.resolve().parent.mkdir(parents=True,exist_ok=True)
    if args.module:
        args.module.resolve().parent.mkdir(parents=True,exist_ok=True)
        bpy.data.libraries.write(str(args.module.resolve()),{C},fake_user=True,compress=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.out.resolve()),compress=True)
    print('Built actual lower fitting scene. Garment meshes:',len(C.objects))

if __name__=='__main__':main()

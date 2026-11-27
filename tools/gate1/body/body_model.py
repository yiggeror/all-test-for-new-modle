"""Build a continuous, subdividable Suzu figure from neck to toes.

Run: blender -b -P body_model.py -- [output.blend]
The construction cage joins shoulder sockets, hips, thumb saddles and four
separate finger webs by shared vertices; no boolean, voxel remesh or skin primitives.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from body_profile import *
from math import sin,cos,pi,exp,atan2
TAU=2*pi
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
coll=bpy.data.collections.new('SUZU_BODY');scene.collection.children.link(coll)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
output=Path(args[0]).resolve() if args else HERE/'suzu_body.blend'
class Cage:
    def __init__(self): self.p=[];self.f=[];self.groups={}
    def v(self,p,group=None):
        i=len(self.p); self.p.append(Vector(p))
        if group:self.groups.setdefault(group,[]).append(i)
        return i
    def face(self,*ids):
        if len(set(ids))>=3:self.f.append(ids)
    def join(self,a,b,align=False):
        na,nb=len(a),len(b)
        if align:
            # Choose the matching orientation and least-displaced seam automatically.
            def offcost(t):
                s,d=t
                return sum((self.p[a[i]]-self.p[b[(s+d*round(i*nb/na))%nb]]).length_squared for i in range(na))
            s,d=min(((s,d) for s in range(nb) for d in (1,-1)),key=offcost)
            b=[b[(s+d*i)%nb] for i in range(nb)]
        i=j=0
        while i<na or j<nb:
            a0=a[i%na];b0=b[j%nb]
            if (i+1)*nb==(j+1)*na:
                self.face(a0,a[(i+1)%na],b[(j+1)%nb],b0);i+=1;j+=1
            elif (i+1)*nb<(j+1)*na:
                self.face(a0,a[(i+1)%na],b0);i+=1
            else:
                self.face(a0,b[(j+1)%nb],b0);j+=1
    def finish(self,name,level=2):
        used=sorted({v for f in self.f for v in f});rm={v:i for i,v in enumerate(used)}
        mesh=bpy.data.meshes.new(name+'_cage');mesh.from_pydata([self.p[i] for i in used],[],[tuple(rm[k] for k in f) for f in self.f]);mesh.update()
        bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(mesh);bm.free();mesh.update()
        obj=bpy.data.objects.new(name,mesh);coll.objects.link(obj)
        for group,indices in self.groups.items():
            vg=obj.vertex_groups.new(name=group);vg.add([rm[v] for v in indices if v in rm],1.,'REPLACE')
        for p in mesh.polygons:p.use_smooth=True
        md=obj.modifiers.new('Contour subdivision','SUBSURF');md.levels=level;md.render_levels=level
        return obj
skin=Cage();nails=Cage()
def curve_exp(z,z0,sz):return exp(-.5*((z-z0)/sz)**2)
def xn(v,g=.97):return math.copysign(abs(v)**g,v) if v!=0 else 0.
def core_pt(z,a):
    rx,rf,rb,cy=smooth_profile(TRUNK,z);c,s=cos(a),sin(a);x=rx*xn(c,.92);y=cy+(rf if s<0 else rb)*xn(s,.93)
    front=max(0.,-s);back=max(s,0.)
    # Chevron of the clavicles and jugular notch. Thorax intentionally softly modelled.
    if z>1.207:
        high=1.234+.030*min(1.,abs(x)/.112)
        y-=.0036*curve_exp(z,high,.008)*front**2*min(1.,abs(x)/.025)
        y+=.0025*curve_exp(z,1.261,.014)*front**7
        y-=.0014*curve_exp(z,1.310,.026)*front**3*(1-.7*front**8)
    y-=.0028*curve_exp(z,1.151,.027)*front**2*(1-front**8)
    y+=.0013*curve_exp(z,.970,.060)*back**20
    zz=z-.0028*front**4*curve_exp(z,1.244,.033)+.002*back**3*curve_exp(z,1.207,.04)
    return (x,y,zz)
N=48;K=5
torso=[]
for row in TRUNK:
    torso.append([skin.v(core_pt(row[0],TAU*j/N),'Body / torso') for j in range(N)])
lo=next(i for i,r in enumerate(TRUNK) if r[0]==1.160);hi=next(i for i,r in enumerate(TRUNK) if r[0]==1.249)
for i in range(len(torso)-1):
    for j in range(N):
        omit=(lo<=i<hi and (j in {k%N for c0 in (0,N//2) for k in range(c0-K,c0+K)}))
        if not omit:skin.face(torso[i][j],torso[i][(j+1)%N],torso[i+1][(j+1)%N],torso[i+1][j])
skin.face(*torso[-1])
# Shared saddle nested between right/left thigh islands.
base=torso[0];frontI=base[3*N//4];backI=base[N//4];m=N//2
crotch=[]
for j in range(m+1):
    u=pi*j/m
    if j==0:crotch.append(backI)
    elif j==m:crotch.append(frontI)
    else:
        y=.008+( .083 if cos(u)>0 else .071)*cos(u)
        z=.840-.028*sin(u)**1.5+.0025*sin(2*u)
        crotch.append(skin.v((0,y,z),'Body / hips'))
# Foot cross sections: posterior calcaneus to soft toe arc flow inward to a slightly flexed shoe bed.
FOOT=[(.026,.070,-.054,.030,.088,.092),(.028,.070,-.054,.032,.092,.093),
      (.032,.070,-.049,.034,.099,.090),(.036,.070,-.044,.034,.094,.082),
      (.043,.070,-.034,.034,.083,.075),(.049,.069,-.026,.032,.076,.069),
      (.052,.069,-.021,.031,.070,.065),(.061,.068,-.011,.0285,.058,.0555),
      (.072,.068,.001,.0265,.043,.041),(.078,.068,.004,.026,.034,.035)]
def foot_pt(z,a,sd):
    x,cy,rx,rf,rb=smooth_profile(FOOT,z);c,s=cos(a),sin(a)
    wide=1.+.055*max(-s,0)**.7-.12*max(s,0)
    xx=x+rx*xn(c,.92)*wide+.0014*max(-s,0)**2
    yy=cy+(rf if s<0 else rb)*xn(s,.91)
    return (sd*xx,yy,z)
def build_leg(sd):
    sg='L' if sd==1 else 'R'
    outer=[base[(3*N//4+sd*k)%N] for k in range(m+1)]
    ring=outer+crotch[1:-1];n=len(ring)
    az=[-pi/2+TAU*j/n for j in range(n)]
    # Initial fraction of the inside seam rolls into each separate upper thigh.
    full=[Vector(leg_point(.798,a,sd)) for a in az]
    for t in (.43,1.):
        if t==1.:pts=full
        else:
            # The crotch is gently curved and does not form a single central pole.
            src=[skin.p[k] for k in outer+crotch[1:-1]]
            pts=[v.lerp(w,t) for v,w in zip(src,full)]
        nr=[skin.v(v,'Thigh.'+sg) for v in pts];skin.join(ring,nr);ring=nr
    for z in [r[0] for r in reversed(LEG) if r[0]<.798]+[r[0] for r in reversed(FOOT)]:
        pts=[leg_point(z,a,sd) if z>=.082 else foot_pt(z,a,sd) for a in az]
        group=('Thigh.' if z>.46 else 'Shin.' if z>.085 else 'Foot.')+sg
        rr=[skin.v(p,group) for p in pts];skin.join(ring,rr);ring=rr
    # A small, regular inset instead of a large nonplanar outsole ngon.
    cen=sum((skin.p[v] for v in ring),Vector())/len(ring)
    inner=[skin.v(cen+(skin.p[v]-cen)*.76,'Foot.'+sg) for v in ring];skin.join(ring,inner);skin.face(*inner)
for side in (1,-1):build_leg(side)
# Joint-oriented hand in local palmar coordinates. u runs from thumb to little finger;
# n is outward (dorsal); s follows the metacarpals from wrist toward middle fingertip.
D=Vector((.30,-.07,-.953)).normalized()
U=Vector((.73,.65,.0));U=(U-D*U.dot(D)).normalized()
V=D.cross(U).normalized()
W=Vector((.290,-.008,.835))
thumb_hole_rows=range(2,6)
def left_world(s,u,n):return W+D*s+U*u+V*n
def mirror(p,sd):return Vector((sd*p.x,p.y,p.z))
def build_hand(sd,armring):
    sg='L' if sd==1 else 'R';G='Hand.'+sg
    def put(s,u,n,layer=skin,group=G):return layer.v(mirror(left_world(s,u,n),sd),group)
    primary=[0,.006,.014,.021,.029,.037,.044]
    widths=[.0176,.0182,.0195,.0218,.0240,.0260,.0276]
    # Unequal knuckle arc: the middle knuckle projects, the little one sits proximally.
    finger_lengths=[.0439,.0447,.0432,.0373]
    # R1: move each MCP a little proximally, allowing +9% ray length with
    # no movement of the wrist or fingertip calibration marks.
    finger_scale=1.09; width_scale=.91
    def send(u):
        # Hermite interpolate the centreline positions of the metacarpal heads.
        data=[(-1.,.050-.09*finger_lengths[0]),(-.75,.053-.09*finger_lengths[0]),
              (-.25,.0565-.09*finger_lengths[1]),(.25,.054-.09*finger_lengths[2]),
              (.75,.047-.09*finger_lengths[3]),(1.,.0435-.09*finger_lengths[3])]
        return smooth_profile(data,u)[0]
    top=[];bot=[];edges=[];last=len(primary)
    for i in range(last+1):
        row0=[];row1=[];ee={}
        for j in range(17):
            a=j/8-1; q=j/16
            end=send(a)
            s=primary[i] if i<last else end
            if i==last-1:s=end*.82
            if i==last-2:s=min(primary[i],end*.72)
            if i==last-3:s=min(primary[i],end*.60)
            if i>=2 and i<=6:s-=.0036*curve_exp(a,-1.,.30)*(.63 if i in (2,6) else 1.)
            w=widths[i] if i<last else .0278
            u=a*w+(.0008*(s/.055))
            thick=(.0099-.0015*min(1.,s/.050))*(.30+.70*(max(0,1.-abs(a)**2.4))**.48)
            arch=.0015*(1.-a*a)*sin(pi*min(1,s/.055))
            thenar=.0035*curve_exp(a,-.54,.34)*curve_exp(s,.028,.016)
            hypoth=.0016*curve_exp(a,.64,.30)*curve_exp(s,.032,.019)
            mc=[-.75,-.25,.25,.75]
            heads=sum(curve_exp(a,ax,.135)*curve_exp(s,send(ax)-.002,.0065) for ax in mc)
            tendons=sum(curve_exp(a,ax*(.48+.48*min(1,s/.05)),.12)*curve_exp(s,.031,.011) for ax in mc)
            n_d=thick+arch+.0015*heads+.00095*tendons
            n_p=-thick-.0009-thenar-hypoth+.0013*curve_exp(a,-.08,.34)*curve_exp(s,.032,.015)
            n_p+=.0011*curve_exp(s,.039+.006*a,.0027)+.0008*curve_exp(s,.026-.006*a*a-.002*a,.0038)
            row0.append(put(s,u,n_d));row1.append(put(s,u,n_p))
            if j in (0,16) or (i==last and j%4==0):
                ee[j]=put(s,u+(1 if j==16 else -1 if j==0 else 0)*.0006,(n_p+n_d)*.5)
        top.append(row0);bot.append(row1);edges.append(ee)
    for i in range(last):
        for j in range(16):
            skin.face(top[i][j],top[i][j+1],top[i+1][j+1],top[i+1][j])
            skin.face(bot[i][j+1],bot[i][j],bot[i+1][j],bot[i+1][j+1])
        for j in (0,16):
            if j==0 and i in thumb_hole_rows:continue
            skin.face(top[i][j],top[i+1][j],edges[i+1][j],edges[i][j]);skin.face(edges[i][j],edges[i+1][j],bot[i+1][j],bot[i][j])
    wrist=top[0]+[edges[0][16]]+bot[0][::-1]+[edges[0][0]]
    # Continue the proximal palm's radial ordering up the final forearm, so the
    # transition around the styloid does not spiral or show a pinched cuff.
    AP=list(reversed(ARM));tang=Vector((.37,-.055,-.928)).normalized()
    fl=Vector((-tang.z,0,tang.x)).normalized(); fb=fl.cross(tang).normalized()
    st=[]
    for vi in wrist:
        v=mirror(skin.p[vi],sd)-W
        xw,yw=v.dot(fl),v.dot(fb)
        aa=atan2(yw/.0185,xw/.016)
        st.append((aa,xw,yw,v.dot(tang)))
    r=armring
    for z in (.885,.870,.857,.850,.844):
        xx,yy,rrx,rry=smooth_profile(AP,z);ctr=Vector((xx,yy,z));w=max(0.,min(1.,(.862-z)/.024))
        nr=[]
        for aa,xw,yw,tw in st:
            px=rrx*(cos(aa)*(1-w)+xw/.016*w);py=rry*(sin(aa)*(1-w)+yw/.0185*w)
            nr.append(skin.v(mirror(ctr+fl*px+fb*py+tang*tw*w,sd),'Forearm.'+sg))
        skin.join(r,nr,align=z==.885);r=nr
    skin.join(r,wrist)
    rayA=[math.radians(j) for j in (150,121,90,59,30,0,-30,-59,-90,-121,-150,180)]
    def digit(t,slot):
        u0=(-.75+.5*slot)*.0278+.0008
        s0=send(-.75+.5*slot)
        length=finger_lengths[slot]*finger_scale
        drift=[-.0055,-.0028,-.0008,.0021][slot]
        # PIP flexes and then the DIP curls further, progressively from index to little finger.
        d1=[.0028,.0033,.0043,.0041][slot];d2=[.010,.0105,.0145,.0165][slot]
        s=s0+length*t-d2*.16*t**3
        u=u0+drift*(.3*t+.7*t**1.4)-.0013*max(t-.52,0.)**1.28
        n=-.0001-d1*t-d2*(.17*t**2+.83*t**3)
        return left_world(s,u,n)
    def frame(fn,t):
        T=(fn(t+.002)-fn(t-.002)).normalized()
        A=(U-T*T.dot(U)).normalized();B=T.cross(A).normalized()
        return T,A,B
    finger_rings=[(.10,.90),(.24,.80),(.37,.76),(.45,.80),(.51,.78),(.61,.69),(.70,.65),(.75,.68),(.80,.66),(.88,.60),(.935,.54),(.959,.48),(.980,.37),(.995,.21),(1.,.08)]
    thumb_rings=[(.15,.00855),(.25,.0072),(.36,.0069),(.46,.0071),(.50,.0068),(.60,.00625),(.70,.00568),(.76,.00583),(.83,.00563),(.90,.00523),(.935,.00479),(.959,.00424),(.980,.00324),(.995,.00180),(1.,.00074)]
    radii=[r*width_scale for r in [.00665,.0068,.00628,.00542]]
    thumb_rings=[(t,r*width_scale) for t,r in thumb_rings]
    def fingernail(fn,slot,name,thumb=False):
        # The plate follows the actual elliptical dorsal surface, from cuticle to
        # free edge. Both return surface and radial rim are joined into a closed shell.
        nr=[];inn=[]; axis=(math.pi*.69 if thumb else math.pi*.50)
        for t,w in ((.808,.38),(.816,.66),(.833,.90),(.854,1.),(.892,1.),(.928,.98),(.948,.89),(.956,.74)):
            row=[];low=[]
            for h in (-1.,-.65,0,.65,1.):
                # Soft convex cuticle and almost square distal tip; no spherical ornament.
                tt=t+.011*(1-h*h)*(-1 if t<.845 else .5 if t>.936 else 0)
                ctr=fn(tt);T,A,B=frame(fn,tt)
                rad=smooth_profile(thumb_rings if thumb else finger_rings,tt)[0]*(1 if thumb else radii[slot])
                an=axis+.745*w*h
                ca,sa=cos(an),sin(an)
                p=ctr+A*(rad*xn(ca,.91)*.968)+B*(rad*(.79 if thumb else .76)*xn(sa,.85)*.967)
                normal=(A*ca+B*sa*1.26).normalized()
                d=.00007+.00012*(1-h*h)
                row.append(nails.v(mirror(p+normal*d,sd),name));low.append(nails.v(mirror(p-normal*.00034,sd),name))
            nr.append(row);inn.append(low)
        for i in range(len(nr)-1):
            for j in range(4):
                nails.face(nr[i][j],nr[i][j+1],nr[i+1][j+1],nr[i+1][j])
                nails.face(inn[i+1][j],inn[i+1][j+1],inn[i][j+1],inn[i][j])
            for j in (0,4):nails.face(nr[i][j],nr[i+1][j],inn[i+1][j],inn[i][j])
        for i in (0,len(nr)-1):
            for j in range(4):nails.face(nr[i][j],nr[i][j+1],inn[i][j+1],inn[i][j])
    for slot,name in enumerate(['Index','Middle','Ring','Little']):
        g=name+'.'+sg;j0=slot*4;j1=j0+4
        ring=top[-1][j0:j1+1]+[edges[-1][j1]]+bot[-1][j0:j1+1][::-1]+[edges[-1][j0]]
        fn=lambda t:digit(t,slot)
        rad=radii[slot]
        for t,h in finger_rings:
            T,A,B=frame(fn,t);ctr=fn(t)
            ring2=[]
            for an in rayA:
                ca,sa=cos(an),sin(an);du=xn(ca,.91)*h*rad
                dn=xn(sa,.81)*h*rad*(.80 if sa<0 else .76)
                p=ctr+A*du+B*dn;ring2.append(skin.v(mirror(p,sd),g))
            skin.join(ring,ring2);ring=ring2
        skin.face(*ring);fingernail(fn,slot,g+' / nail')
    # Four sidewall strips have been opened in the thenar pad. The thumb is attached
    # around the entire saddle, rather than intersecting a palm with a separate tube.
    q0,q1=2,6
    root=[top[i][0] for i in range(q0,q1+1)]+[edges[q1][0]]+[bot[i][0] for i in range(q1,q0-1,-1)]+[edges[q0][0]]
    # Hand-local control points (in metres) for a thumb in mild opposition.
    keys=[(0,.026,-.022,-.001),(.15,.036,-.028,-.003),(.33,.044,-.031,-.006),
          (.48,.0505,-.0335,-.0088),(.61,.0564,-.0353,-.011),(.73,.0615,-.0363,-.013),(.88,.0666,-.0365,-.0158),(1.,.0708,-.0358,-.017)]
    def thumb(t):
        t=max(.00001,min(.99999,t));s,u,n=smooth_profile(keys,t);return left_world(s-.0036*(1-t),u,n)
    ring=root
    for k,(t,r) in enumerate(thumb_rings):
        T,A,B=frame(thumb,t);ctr=thumb(t);new=[]
        for a in rayA:
            p=ctr+A*(r*xn(cos(a),.91))+B*(r*.79*xn(sin(a),.86));new.append(skin.v(mirror(p,sd),'Thumb.'+sg))
        skin.join(ring,new,align=(k==0));ring=new
    skin.face(*ring);fingernail(thumb,0,'Thumb.'+sg+' / nail',True)
def build_arm(sd):
    center=0 if sd==1 else N//2
    # Exactly the boundary of the removed grid rectangle. Angle increases from
    # clavicle, toward the rear axillary fold, down to armpit, and to anterior fold.
    off=lambda row,d:torso[row][(center+sd*d)%N]
    loop=[off(hi,k) for k in range(-K,K+1)]+[off(i,K) for i in range(hi-1,lo-1,-1)]+[off(lo,k) for k in range(K-1,-K-1,-1)]+[off(i,-K) for i in range(lo+1,hi)]
    vs=[skin.p[k] for k in loop];cy0=sum(v.y for v in vs)/len(vs);cz0=(TRUNK[hi][0]+TRUNK[lo][0])*.5
    angles=[atan2((v.y-cy0)/.042,(v.z-cz0)/.046) for v in vs]
    ring=loop;sg='L' if sd==1 else 'R'
    for i,(z,x,y,ru,rv) in enumerate(r for r in ARM if r[0]>=.900):
        prev=ARM[max(i-1,0)];nxt=ARM[min(i+1,len(ARM)-1)]
        tangent=Vector((nxt[1]-prev[1],nxt[2]-prev[2],nxt[0]-prev[0])).normalized()
        up=Vector((-tangent.z,0,tangent.x)).normalized();back=up.cross(tangent).normalized()
        ctr=Vector((x,y,z))
        pts=[]
        for a in angles:
            c,s=cos(a),sin(a)
            # Deltoid has a rounded lateral cap; triceps, brachioradialis and ulnar
            # styloid are staggered in depth so side profiles don't read as cylinders.
            rr=ru+.0022*curve_exp(z,1.200,.025)*max(c,0)**3+.0011*curve_exp(z,.856,.006)*max(-c,0)**3
            ry=rv+.0015*curve_exp(z,1.131,.041)*max(s,0)**3+.0016*curve_exp(z,1.080,.028)*max(-s,0)**3
            q=ctr+up*(rr*xn(c,.96))+back*(ry*xn(s,.95))
            if i<4:
                inner=max(-c,0.)**1.18;outer=max(c,0.)**1.10
                q.x+= [.024,.014,.005,.000][i]*inner-[.008,.005,.001,0][i]*outer
                q.z-= [.051,.030,.012,.002][i]*inner
                q.z+= [.014,.008,.003,0][i]*outer
            pts.append(skin.v(mirror(q,sd),('Upper arm.' if z>=1.05 else 'Forearm.')+sg))
        skin.join(ring,pts);ring=pts
    build_hand(sd,ring)
for sd in (1,-1):build_arm(sd)
obj=skin.finish('Suzu | body, hands and feet',2)
nailobj=nails.finish('Suzu | nail beds',1)
for o in (obj,nailobj):o['design_units']='metres';o['stage']='Gate 1 clay'
# Default solid viewport has no final colour layers, no deformation armature.
obj['construction']='Connected anatomical cage: hip saddle, scapulohumeral sockets and separate metacarpal webs.'
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1.
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
print('BODY_MODULE',output,'verts',len(obj.data.vertices),'faces',len(obj.data.polygons))

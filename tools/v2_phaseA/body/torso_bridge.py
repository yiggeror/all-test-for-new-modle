"""Retain the approved Pixiv Twist mesh wherever native skin exists, graft the
licensed VRoid/CC0 torso, and sew its four seams in the calibrated T-pose.

The hem, collarbone and shoulder surfaces come from the donor's native body
skin, never from a garment shell. Every cut interpolates native UV and skin
weights; edges at identical positions share vertices and have per-corner UVs.
"""
from collections import defaultdict,Counter
from math import atan2,pi,floor,cos,sin,hypot
from itertools import product
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
import bmesh,bpy
EPS=1.e-7
NEI=list(product((-1,0,1),repeat=3))
class Point:
    __slots__=('p','w','uv')
    def __init__(self,p,w,uv):
        self.p=p
        self.w=w
        self.uv=uv
    def lerp(self,b,t):
        return Point(self.p.lerp(b.p,t),blend(self.w,b.w,t),self.uv.lerp(b.uv,t))
def blend(a,b,t):
    return {k:(1-t)*a.get(k,0)+t*b.get(k,0) for k in a.keys()|b.keys()}
def norm(w):
    n=sum(w.values())
    return {k:v/n for k,v in w.items() if v>5.e-7} if n>0 else {'J_Bip_C_Hips':1.}
def clip(poly,i,sign,x):
    if not poly:return []
    ans=[];a=poly[-1]
    fa=(a.p[i]-x)*sign
    for b in poly:
        fb=(b.p[i]-x)*sign
        if (fa>=-EPS)!=(fb>=-EPS):
            t=max(0.,min(1.,fa/(fa-fb)))
            c=a.lerp(b,t);c.p[i]=x;ans.append(c)
        if fb>=-EPS:ans.append(b)
        a,fa=b,fb
    return ans
def geom(ob,parts,rig,donor=False,yaw=1,drig=None):
    bone_weights={g.index:g.name for g in ob.vertex_groups}
    known=set(b.name for b in rig.data.bones)
    points=[]
    shifts={}
    if donor:
        shifts={b.name:rig.data.bones[b.name].head_local-Vector((b.head_local.x*yaw,b.head_local.y*yaw,b.head_local.z))
            for b in drig.data.bones if b.name in known}
    for v in ob.data.vertices:
        p=Vector((v.co.x*yaw,v.co.y*yaw,v.co.z))
        wt={bone_weights[g.group]:g.weight for g in v.groups if g.weight>1.e-6}
        if donor:
            d=Vector()
            for g,w in wt.items():
                if g in shifts:d+=w*shifts[g]
            # Bone-space linear shifts align the donor's own deltoid and neck
            # shoulder hinge before fine seam matching.
            p+=d
            reweights={}
            for g,w in wt.items():
                b=drig.data.bones.get(g)
                while b is not None and b.name not in known:b=b.parent
                k=b.name if b else 'J_Bip_C_UpperChest'
                reweights[k]=reweights.get(k,0)+w
            wt=reweights
        points.append((p,norm(wt)))
    data=ob.data.uv_layers.active
    out={}
    for name,planes in parts.items():
        m=Patch(name)
        for f in ob.data.polygons:
            p=[Point(*points[i],Vector(data.data[li].uv) if data else Vector((0.,0.))) for i,li in zip(f.vertices,f.loop_indices)]
            for ax,sg,uu in planes:p=clip(p,ax,sg,uu)
            if len(p)>=3:m.add(p)
        out[name]=m
    return out
class Patch:
    def __init__(self,name):
        self.name=name;self.ids=defaultdict(list);self.pts=[];self.weights=[];self.vert_uv=[];self.faces=[];self.uvs=[]
    def idx(self,p,g,uv):
        eps=4.e-6
        k=tuple(floor(a/eps) for a in p)
        for di,dj,dk in NEI:
            for q in self.ids.get((k[0]+di,k[1]+dj,k[2]+dk),()):
                if (self.pts[q]-p).length<eps:return q
        q=len(self.pts);self.ids[k].append(q);self.pts.append(p.copy());self.weights.append(dict(g));self.vert_uv.append(uv.copy())
        return q
    def add(self,r):
        pack=[]
        for a in r:
            idx=self.idx(a.p,a.w,a.uv)
            if not pack or idx!=pack[-1][0]:pack.append((idx,a.uv.copy()))
        if len(pack)>1 and pack[0][0]==pack[-1][0]:pack.pop()
        if len(pack)<3:return
        v,uv=zip(*pack);self.faces.append(tuple(v));self.uvs.append(tuple(uv))
    def ring(self,axis,at):
        e=Counter()
        for poly in self.faces:
            e.update(tuple(sorted((a,b))) for a,b in zip(poly,poly[1:]+poly[:1]))
        d=defaultdict(set)
        for (a,b),cnt in e.items():
            if cnt!=1 or max(abs(self.pts[v][axis]-at) for v in (a,b))>3.e-6:continue
            d[a].add(b);d[b].add(a)
        unseen=set(d);loops=[]
        while unseen:
            q=[unseen.pop()];cs=q[:]
            while q:
                x=q.pop()
                for y in d[x]:
                    if y in unseen:unseen.remove(y);q.append(y);cs.append(y)
            if all(len(d[v])==2 for v in cs) and len(cs)>4:
                a=cs[0];c=[a];prev=None
                for _ in range(len(cs)):
                    b=next(b for b in d[a] if b!=prev)
                    if b==c[0]:break
                    c.append(b);prev,a=a,b
                loops.append(c)
        if not loops:
            raise RuntimeError(f'{self.name} at {axis}={at} has no closed native ring; degrees: {dict(Counter(len(a) for a in d.values()))} endpoints {[(i,tuple(self.pts[i])) for i,v in d.items() if len(v)!=2]}')
        if len(loops)>1:
            raise RuntimeError(f'{self.name} at {axis}={at} has disconnected cut loops {[len(v) for v in loops]}')
        return loops[0]
def polar(patch,ring,axis):
    axes=[i for i in range(3) if i!=axis]
    c=sum((patch.pts[i] for i in ring),Vector())/len(ring)
    ss=sorted((atan2(patch.pts[i][axes[1]]-c[axes[1]],patch.pts[i][axes[0]]-c[axes[0]])%(2*pi),i) for i in ring)
    return c,axes,ss
def polarrad(patch,c,axes,ss,q):
    from bisect import bisect
    n=len(ss)
    find=bisect([t[0] for t in ss],q)
    t0,k0=ss[(find-1)%n];t1,k1=ss[find%n]
    dt=(t1-t0)%(2*pi)
    u=((q-t0)%(2*pi))/dt if dt>1.e-10 else 0
    return patch.pts[k0].lerp(patch.pts[k1],u)
def smooth(t):
    t=max(0.,min(1.,t));return t*t*(3-2*t)
def fit_ring_detail(dst,don,own_ring,don_ring,axis,donplane,radius,keys):
    c,axes,own=polar(dst,own_ring,axis)
    dc,_,dons=polar(don,don_ring,axis)
    from math import hypot
    reference=Patch('donor ring reference');reference.pts=[v.copy() for v in don.pts]
    for i,v in enumerate(don.pts):
        diff=abs(v[axis]-donplane)
        if diff>=radius or (keys=='neck' and abs(v.x)>.082):continue
        a,b=axes
        ang=atan2(v[b]-dc[b],v[a]-dc[a])%(2*pi)
        p0=polarrad(dst,c,axes,own,ang);p1=polarrad(reference,dc,axes,dons,ang)
        f=1.-smooth(diff/radius)
        if keys=='neck':f*=1.-smooth((abs(v.x)-.052)/.029)
        dx,dy=p0[a]-p1[a],p0[b]-p1[b]
        v[a]+=dx*f*.87
        v[b]+=dy*f*.87
def seam(a,ar,b,br,axis,offsetA,offsetB):
    ca,_,angA=polar(a,ar,axis);cb,_,angB=polar(b,br,axis)
    # Crossing indices are explicitly ordered by angle, following a single
    # anatomical loop around each section. Two native tessellations need not
    # have the same sample count.
    u=[i for _,i in angA];v=[i for _,i in angB]
    aa=[x for x,_ in angA];bb=[x for x,_ in angB]
    n,m=len(u),len(v);i=j=0;F=[];UV=[];turn=2*pi
    def emit(keys):
        F.append(tuple(k+off for P,k,off in keys));UV.append(tuple(P.vert_uv[k].copy() for P,k,_ in keys))
    # Start at the actual ring positions nearest the + radial axis, then
    # advance on proportional angles rather than index or chord assumptions.
    while i<n or j<m:
        AI=u[i%n];AJ=v[j%m];s1=aa[(i+1)%n]+(turn if i+1>=n else 0.);s2=bb[(j+1)%m]+(turn if j+1>=m else 0.)
        a0=(a,AI,offsetA);a1=(a,u[(i+1)%n],offsetA);b0=(b,AJ,offsetB);b1=(b,v[(j+1)%m],offsetB)
        if i<n and j<m and abs(s1-s2)<.016:
            emit((a0,a1,b1,b0));i+=1;j+=1
        elif i<n and (j>=m or s1<s2):
            emit((a0,a1,b0));i+=1
        else:
            emit((a0,b1,b0));j+=1
    return F,UV
def relax_native_junctions(vv,faces,seed_ids,don_i):
    # Spread irregular triangulation across the welded rows and their
    # immediate neighbours; paired Taubin passes retain section dimensions
    # while removing ribs and longitudinal crease lines at each graft edge.
    N=[set() for _ in vv]
    for p in faces:
        for a,b in zip(p,p[1:]+p[:1]):
            N[a].add(b);N[b].add(a)
    w=[.25 if i>=don_i else 0. for i in range(len(vv))]
    for i in seed_ids:w[i]=1.
    visited=set(seed_ids);step=set(visited)
    for gain in (.82,.56,.30):
        new={j for i in step for j in N[i]}-visited
        for i in new:w[i]=max(w[i],gain)
        visited.update(new);step=new
    held=[p.copy() for p in vv]
    disp=[]
    for a in (.42,-.275,.40,-.252,.37,-.231,.34,-.210):
        out=[]
        for j,p in enumerate(vv):
            if w[j]<=0 or not N[j]:out.append(p.copy());continue
            q=Vector()
            total=0.
            for k in N[j]:
                dr=vv[k]-p
                weight=1./max(.0024,dr.length)**.43
                q+=weight*dr
                total+=weight
            u=p+q*(a*w[j]/total)
            movement=u-held[j]
            if movement.length>.0045:u=held[j]+movement.normalized()*.0045
            out.append(u)
        vv=out
    return vv,max((a-b).length for a,b in zip(vv,held))
def waist_section_fairing(verts,polys):
    # Match the *derivatives* of the measured skin on both sides of the waist,
    # not just their positions at the seam. The surrounding intact chest/hip
    # are unchanged. Two stored radial side stations establish each tangent.
    mesh=BVHTree.FromPolygons(verts,polys)
    z0,z1=.997,1.077
    e=.0072
    stations=(z0-e,z0,z1,z1+e)
    def core(z):
        p=mesh.ray_cast(Vector((0., .4,z)),Vector((0.,-1.,0.)),.80)[0]
        q=mesh.ray_cast(Vector((0.,-.4,z)),Vector((0., 1.,0.)),.80)[0]
        if p is None or q is None:raise RuntimeError('Guide section is open at '+str(z))
        return Vector((0.,(p.y+q.y)/2,z))
    cc={z:core(z) for z in stations}
    def radius(z,angle):
        v=Vector((cos(angle),sin(angle),0.))
        p=mesh.ray_cast(cc[z]+v*.40,-v,.401)[0]
        if p is None:raise RuntimeError('Missing native waist side at '+str(z))
        return (p-cc[z]).dot(v)
    def cubic(t,a,b,m,n):
        return a*(2*t*t*t-3*t*t+1)+b*(-2*t*t*t+3*t*t)+(t*t*t-2*t*t+t)*m+(t*t*t-t*t)*n
    result=[];maxdev=0.
    for p in verts:
        if not z0<p.z<z1:result.append(p);continue
        t=(p.z-z0)/(z1-z0)
        mid=cubic(t,cc[z0].y,cc[z1].y,(cc[z0].y-cc[z0-e].y)*(z1-z0)/e,(cc[z1+e].y-cc[z1].y)*(z1-z0)/e)
        an=atan2(p.y-mid,p.x)
        l,a,b,h=[radius(z,an) for z in stations]
        r=cubic(t,a,b,(a-l)*(z1-z0)/e,(h-b)*(z1-z0)/e)
        target=Vector((r*cos(an),mid+r*sin(an),p.z));delta=target-p
        if delta.length>.0055:delta=delta.normalized()*.0055
        q=p+delta*.94
        maxdev=max(maxdev,(q-p).length);result.append(q)
    return result,maxdev
def bridge(body,rig,donor_path,front):
    with bpy.data.libraries.load(str(donor_path),link=False) as (src,dst):
        dst.objects=[k for k in src.objects if k=='Body' or k=='Armature']
    donor=next(k for k in dst.objects if k.type=='MESH')
    drig=next(k for k in dst.objects if k.type=='ARMATURE')
    df=int(drig.get('stage_raw_front',1));yaw=(-1 if df!=front else 1)
    # Recipient cut, donor cut, anatomical section, opening width (m).
    z0,z1=.026+1.0,1.038; nz0,nz1=1.300,1.287; ax0,ax1=.236,.219
    groups={
        'waist':[(2,-1,z0)],
        'neck':[(2,1,nz0)],
        'right_arm':[(0,-1,-ax0)],
        'left_arm':[(0,1,ax0)]
    }
    same_station_guides={
        'guide_waist':[(2,-1,z1)],'guide_neck':[(2,1,nz1)],
        'guide_right_arm':[(0,-1,-ax1)],'guide_left_arm':[(0,1,ax1)]}
    dgroup={'native_torso':[(2,1,z1),(2,-1,nz1),(0,1,-ax1),(0,-1,ax1)]}
    gathering=geom(body,dict(groups,**same_station_guides),rig)
    fr={k:gathering[k] for k in groups}
    d=geom(donor,dgroup,rig,True,yaw,drig)['native_torso']
    rings={}
    for name,axis,opa,dopa,m in (
        ('waist',2,z0,z1,.064),('neck',2,nz0,nz1,.047),
        ('right_arm',0,-ax0,-ax1,.095),('left_arm',0,ax0,ax1,.095)):
        part=fr[name];ar=part.ring(axis,opa);br=d.ring(axis,dopa)
        rings[name]=(ar,br,axis)
        guide=gathering['guide_'+name];target_same=guide.ring(axis,dopa)
        fit_ring_detail(guide,d,target_same,br,axis,dopa,m,name)
    global_v=[];F=[];UV=[];weights=[];offset={}
    for name,t in list(fr.items())+[('torso',d)]:
        offset[name]=len(global_v)
        global_v.extend(t.pts);weights.extend(t.weights)
        F.extend(tuple(k+offset[name] for k in f) for f in t.faces);UV.extend(t.uvs)
    orig=len(F);bounds={};set_all=set()
    for name,(ar,br,ax) in rings.items():
        fs,uv=seam(fr[name],ar,d,br,ax,offset[name],offset['torso'])
        F.extend(fs);UV.extend(uv);bounds[name]=[len(ar),len(br),len(fs)]
        set_all.update(k+offset[name] for k in ar);set_all.update(k+offset['torso'] for k in br)
    global_v,relax_delta=relax_native_junctions(global_v,F,set_all,offset['torso'])
    global_v,waist_fairing=waist_section_fairing(global_v,F)
    m0=body.data;m=bpy.data.meshes.new('Pixiv Twist · continuous fitted skin')
    m.from_pydata(global_v,[],F);m.update()
    skin=bpy.data.materials.get('Suzu · Study skin') or bpy.data.materials.new('Suzu · Study skin')
    skin.use_nodes=True;skin.diffuse_color=(.73,.64,.59,1.)
    sh=skin.node_tree.nodes.get('Principled BSDF')
    sh.inputs['Base Color'].default_value=(.889,.756,.663,1.)
    sh.inputs['Roughness'].default_value=.88
    m.materials.append(skin)
    data=m.uv_layers.new(name=m0.uv_layers.active.name if m0.uv_layers.active else 'UVMap')
    for p,uv in zip(m.polygons,UV):
        p.use_smooth=True
        for li,a in zip(p.loop_indices,uv):data.data[li].uv=a
    bm=bmesh.new();bm.from_mesh(m)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    inspect=Counter(len(e.link_faces) for e in bm.edges)
    bm.to_mesh(m);bm.free()
    body.data=m
    body.vertex_groups.clear()
    k={b.name:body.vertex_groups.new(name=b.name) for b in rig.data.bones}
    for i,w in enumerate(weights):
        for j,value in w.items():
            if j in k and value>1.e-7:k[j].add([i],value,'REPLACE')
    body['torso']='CC0 licensed VRoid shoulder/thorax section; continuous mesh sewn to Pixiv Twist spine and limbs.'
    bpy.data.objects.remove(donor,do_unlink=True)
    if drig.name in bpy.data.objects:bpy.data.objects.remove(drig,do_unlink=True)
    return {'native_skin_faces':len(m0.polygons),'retained_pixiv_faces':sum(len(t.faces) for t in fr.values()),
            'inserted_cc0_native_faces':len(d.faces),'inserted_seam_faces':len(F)-orig,'seam_loops':bounds,
            'edge_face_histogram':dict(inspect),'skin_from_old_dress_faces':0,'max_junction_curve_refinement_m':relax_delta,'max_c1_waist_adjustment_m':waist_fairing}

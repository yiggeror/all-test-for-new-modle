"""Restore the two existing scalp boundary triangles omitted by the Pixiv sample."""
from itertools import product
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# Mirrored single-triangle holes are bounded by these exact source scalp points.
SEAT=((.089398675,.036314137,1.468710899),(.089490391,.045953549,1.475805402),(.090327725,.036208980,1.475970030))

def seal_scalp(body):
    me=body.data; mat=next(i for i,m in enumerate(me.materials) if 'body_00_skin' in m.name.lower());
    vv=[v.co.copy() for v in me.vertices];old=[(tuple(f.vertices),f.material_index) for f in me.polygons]
    skin=[f for f,i in old if i==mat];body_ids=set(i for f in skin for i in f)
    edge={tuple(sorted((a,b))) for f in skin for a,b in zip(f,f[1:]+f[:1])}
    normals={};vxnorm={};was=me.has_custom_normals
    if was:
        for p in me.polygons:
            for j in p.loop_indices:
                l=me.loops[j];n=me.corner_normals[j].vector.copy();normals[(p.material_index,tuple(sorted(p.vertices)),l.vertex_index)]=n
                if p.material_index==mat:vxnorm.setdefault(l.vertex_index,[]).append(n)
    def surface():return BVHTree.FromPolygons(vv,skin,all_triangles=True)
    before=surface();new=[]
    for h in (-1,1):
        expected=[Vector((h*x,y,z)) for x,y,z in SEAT]
        choices=[]
        for v in expected:
            a=[i for i in body_ids if (vv[i]-v).length<.00013];choices.append(a)
        if not all(choices):raise ValueError('Apply the Pixiv scalp seal before the shared stature transform')
        def score(f):return sum(tuple(sorted(e)) in edge for e in zip(f,f[1:]+f[:1]))
        f=list(max(product(*choices),key=score));mid=sum((vv[i] for i in f),Vector())/3
        ray=Vector((h*.35,mid.y,mid.z));toward=Vector((-h,0,0))
        if before.ray_cast(ray,toward,.35)[0] is not None:continue
        if ((vv[f[1]]-vv[f[0]]).cross(vv[f[2]]-vv[f[0]])).x*h<0:f.reverse()
        new.append((f,ray,toward))
    if not new:return {'added_triangles':0,'already_sealed':True}
    bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();uvl=bm.loops.layers.uv.active
    for f,_,_ in new:
        source=[]
        for i in f:
            v=bm.verts[i];source.append(next(lp[uvl].uv.copy() for pp in v.link_faces if pp.material_index==mat for lp in pp.loops if lp.vert==v))
        p=bm.faces.new(tuple(bm.verts[i] for i in f));p.material_index=mat;p.smooth=True
        for loop,uv in zip(p.loops,source):loop[uvl].uv=uv
        skin.append(tuple(f))
    bm.normal_update();bm.to_mesh(me);bm.free();me.update()
    if len(me.vertices)!=len(vv) or any((vv[i]-v.co).length>1e-8 for i,v in enumerate(me.vertices)):
        raise AssertionError('Original scalp vertices or their indices changed')
    if not set((tuple(sorted(f)),i) for f,i in old).issubset((tuple(sorted(f.vertices)),f.material_index) for f in me.polygons):
        raise AssertionError('Original body polygons changed')
    if was:
        out=[]
        for p in me.polygons:
            for j in p.loop_indices:
                v=me.loops[j].vertex_index;sup=vxnorm.get(v,[])
                backup=(sum(sup,Vector()).normalized() if len(sup) else p.normal)
                out.append(normals.get((p.material_index,tuple(sorted(p.vertices)),v),backup))
        me.normals_split_custom_set(out)
    after=surface();assert all(after.ray_cast(a,b,.35)[0] is not None for _,a,b in new)
    return {'added_triangles':len(new),'existing_vertices_retained':len(vv),'skin_slot':mat,'seam_vertex_indices':[f for f,_,_ in new],'verified_ray_hits':len(new)}

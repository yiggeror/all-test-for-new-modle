"""Read-only analysis of the approved head, hair sockets and silhouette rails."""
from pathlib import Path
import json,sys,math,bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def sources(scene=None):
    sc=scene or bpy.context.scene;d=bpy.context.evaluated_depsgraph_get();face=next(q for q in sc.objects if q.type=='MESH' and q.data.shape_keys and len(q.data.shape_keys.key_blocks)>50)
    body=next(q for q in sc.objects if q.type=='MESH' and 'body' in q.name.lower());groups={}; verts=[]; faces=[]
    for o in (face,body):
        ev=o.evaluated_get(d);me=ev.to_mesh();me.calc_loop_triangles();v=[o.matrix_world@q.co for q in me.vertices];base=len(verts);verts.extend(v)
        for m in me.materials:
            k=m.name if m else '?';i=me.materials.find(k);ix={j for f in me.polygons if f.material_index==i for j in f.vertices}
            if ix:
                a=[v[j] for j in ix];groups[k]={'lo':[min(q[j] for q in a) for j in range(3)], 'hi':[max(q[j] for q in a) for j in range(3)],'n':len(a)}
        for t in me.loop_triangles:
            ms=me.materials[t.material_index].name.lower();hs=any(v[i].z>1.290 for i in t.vertices)
            if hs and ((o==face and ('skin' in ms or 'porcelain' in ms)) or o==body):faces.append(tuple(base+i for i in t.vertices))
        ev.to_mesh_clear()
    return face,body,BVHTree.FromPolygons(verts,faces,all_triangles=True),groups


def ray(b,x,y,z,d):
    p=Vector((x,y,z));r,n,j,s=b.ray_cast(p,Vector(d),.78);return [round(q,7) for q in r] if r is not None else None

if __name__=='__main__':
    f,b,bvh,groups=sources(); pts={}
    for z in (1.365,1.410,1.435,1.460,1.470,1.480,1.490,1.505,1.520,1.535,1.550,1.565,1.580,1.592):
        pts[str(z)]={str(x):ray(bvh,x,-.40,z,(0,1,0)) for x in (-.115,-.096,-.077,-.058,-.036,-.015,0.,.015,.036,.058,.077,.096,.115)}
    sid={str(z):{str(y):ray(bvh,.42,y,z,(-1,0,0)) for y in (-.072,-.045,-.010,.012,.024,.035,.055,.077,.105)} for z in (1.48,1.50,1.51,1.521,1.529,1.536,1.549,1.562)}
    out=Path(sys.argv[-1]).resolve();out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'groups':groups,'front':pts,'left':sid},indent=2,ensure_ascii=False));print('Phase A mesh slots',json.dumps(groups,ensure_ascii=False))

"""Locate actual hair/skin triangle intersections and report their anatomical regions."""
import sys,json
from pathlib import Path
import bpy
from mathutils.bvhtree import BVHTree
dg=bpy.context.evaluated_depsgraph_get()
def world_tri(o):
    ev=o.evaluated_get(dg);m=ev.to_mesh()
    m.calc_loop_triangles()
    vertices=[ev.matrix_world@v.co for v in m.vertices]
    tris=[tuple(t.vertices) for t in m.loop_triangles]
    mats=[(m.materials[m.polygons[t.polygon_index].material_index].name
           if len(m.materials) else '') for t in m.loop_triangles]
    ev.to_mesh_clear()
    return vertices,tris,mats
def parts(o):
    V,T,M=world_tri(o);x=[]
    for role in set(M):
        A=[t for t,r in zip(T,M) if r==role]
        x.append((role,BVHTree.FromPolygons(V,A,all_triangles=True), V,A))
    return x
face=bpy.context.scene.objects['Suzu · Face'];body=bpy.context.scene.objects['Suzu · Body']
body_tree=parts(body);face_tree=parts(face)
result=[]
for h in bpy.context.scene.objects:
    if h.type!='MESH' or h in (face,body) or h.hide_render:continue
    if 'icosphere' in h.name.lower():continue
    V,T,_=world_tri(h); H=BVHTree.FromPolygons(V,T,all_triangles=True)
    for obj,choices in [('face',face_tree),('body',body_tree)]:
        for lab,A,v,t in choices:
            pairs=H.overlap(A)
            if pairs:
                xyz=[sum((V[k] for k in T[i]),V[T[i][0]]*0)/3 for i,j in pairs]
                result.append({'piece':h.name,'target':obj,'material':lab,'contacts':len(pairs),
                    'extent_m':[[round(min(q[i] for q in xyz),4),round(max(q[i] for q in xyz),4)] for i in range(3)]})
out=Path(sys.argv[sys.argv.index('--')+1])
out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
for x in result:print(x)

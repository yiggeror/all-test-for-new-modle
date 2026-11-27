"""Identify visible cross-layer geometry contacts before visual inspection."""
import bpy,itertools
from mathutils.bvhtree import BVHTree

d=bpy.context.evaluated_depsgraph_get()
def record(obj):
    obj=obj.evaluated_get(d)
    m=obj.to_mesh();m.calc_loop_triangles()
    pts=[obj.matrix_world@v.co for v in m.vertices]
    tris=[tuple(t.vertices) for t in m.loop_triangles]
    obj.to_mesh_clear()
    if not pts or not tris:return None
    return {'name':obj.name,'pts':pts,'tris':tris,
       'bounds':tuple((min(p[i] for p in pts),max(p[i] for p in pts))for i in range(3))}
def bound(a,b):
    return all(x[0]<=y[1] and y[0]<=x[1] for x,y in zip(a['bounds'],b['bounds']))
def get_tree(a):
    if 'tree' not in a: a['tree']=BVHTree.FromPolygons(a['pts'],a['tris'],all_triangles=True)
    return a['tree']
def all_in(collection, select=lambda o:True):
    c=bpy.data.collections.get(collection);return [a for o in c.all_objects if o.type=='MESH' and select(o) and (a:=record(o))]
hair=all_in('SUZU_HEAD',lambda o:o.name not in {'dummy'} and any('H0'+str(x) in c.name for c in o.users_collection for x in [3,4,5]))
cloth=all_in('SUZU_GARMENT')
body=all_in('SUZU_BODY')
def fmt(p):return tuple(round(float(t),4) for t in p)
def contacts(label, first, second):
    total=[]
    for a,b in itertools.product(first,second):
        if not bound(a,b):continue
        ov=get_tree(a).overlap(get_tree(b))
        if not ov:continue
        p=[sum((a['pts'][k] for k in a['tris'][ia]),a['pts'][a['tris'][ia][0]]*0)/3 for ia,_ in ov[:80]]
        mid=sum(p,p[0]*0)/len(p)
        total.append((len(ov),a['name'],b['name'],fmt(mid)))
    print(label,len(total),sum(p[0] for p in total),flush=True)
    for count,n,m,c in sorted(total,reverse=True)[:22]:print(count,c,n,m,sep=' | ',flush=True)
print('Har geometry:',len(hair),'clothes:',len(cloth),'body:',len(body),flush=True)
print('Sole bounds:',[(p['name'],round(p['bounds'][2][0],6)) for p in cloth if 'sole' in p['name'].casefold() or 'heel' in p['name'].casefold()],flush=True)
contacts('HAIR x CLOTHING',hair,cloth)
contacts('BODY x CLOTHING (includes interior interfaces)',body,cloth)

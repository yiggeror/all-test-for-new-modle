"""Local fairing of the approved Phase A seam immediately below the clavicle."""
import argparse,sys,json,hashlib
from pathlib import Path
from math import exp,sqrt
import bpy
from mathutils import Vector
P=argparse.ArgumentParser(description=__doc__);P.add_argument('patch',type=Path)
P.add_argument('--preview',type=Path)
a=P.parse_args(sys.argv[sys.argv.index('--')+1:])
o=bpy.data.objects['Suzu · Body'];m=o.data
v=[x.co.copy() for x in m.vertices];n=[x.normal.copy() for x in m.vertices]
N=[set() for _ in v]
for e in m.edges:
    i,j=e.vertices;N[i].add(j);N[j].add(i)
def ease(t):
    t=min(1.,max(0.,t));return t*t*(3.-2.*t)
def bell(p):
    x,y,z=p
    # Strictly the anterior donor thorax transition. Frozen shoulders,
    # neck, head, arms and all silhouette landmarks stay out of this mask.
    if not (1.216<z<1.294 and .020<abs(x)<.114 and y< -.013):
        return 0.
    u=ease((z-1.216)/.024)*ease((1.294-z)/.016)
    w=ease((abs(x)-.020)/.023)*ease((.114-abs(x))/.022)
    f=ease((-y-.013)/.033)
    return u*w*f
weights=[bell(p) for p in v]
def lap(pts,i):
    pay=Vector();wt=0.
    for j in N[i]:
        d=pts[j]-pts[i];w=1./max(.002,d.length)**.67
        pay+=d*w;wt+=w
    return pay/wt if wt else Vector()
out=[p.copy() for p in v]
for step in (.44,-.20,.35,-.16):
    q=[]
    for i,p in enumerate(out):
        w=weights[i]
        if w<=0:q.append(p);continue
        d=lap(out,i);normal=n[i]
        δ=(normal*d.dot(normal)*.93+.07*d)*step*w
        u=p+δ; dd=u-v[i]
        if dd.length>.00079:u=v[i]+dd.normalized()*.00079
        q.append(u)
    out=q
delta=[(i,tuple(round(float(x),9) for x in (p-v[i]))) for i,p in enumerate(out) if (p-v[i]).length>1.e-7]
assert delta and all(1.216<v[i].z<1.294 for i,_ in delta)
relevant=[i for i,w in enumerate(weights) if w>.28]
rough=lambda c:sqrt(sum((lap(c,i).dot(n[i]))**2 for i in relevant)/len(relevant))
datum={'object':o.name,'scope':'anterior clavicle thorax seam only','deltas':delta,'source_vertices':len(v),
       'maximum_delta_m':max((out[i]-v[i]).length for i,_ in delta),'normal_laplacian_m':[rough(v),rough(out)]}
a.patch.write_text(json.dumps(datum,ensure_ascii=False,indent=2)+'\n')
print(len(delta),datum['maximum_delta_m'],datum['normal_laplacian_m'])
if a.preview:
    for i,d in delta:m.vertices[i].co+=Vector(d)
    m.update()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(a.preview.resolve()),compress=True)

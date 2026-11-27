"""Project hand-directed taper strokes into the native facial UVs without altering the mesh."""
from pathlib import Path
import json,sys,math,bpy
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
from apply_makeup import *
o=world_face_o();me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
skins=[];liner=[];sclera=[];line_uv=[];brow_uv=[]
for tr in me.loop_triangles:
 role=role_slot(o,tr.material_index)
 if role not in ('line','skin','white','iris','brow'):continue
 q=[o.matrix_world@me.vertices[i].co for i in tr.vertices]
 uvx=[uv[i].uv.copy() for i in tr.loops]
 x=[v.x for v in q];z=[v.z for v in q]
 entry=(q,uvx,min(x),max(x),min(z),max(z))
 if role=='skin':skins.append(entry)
 elif role in ('white','iris'):sclera.append(entry)
 elif role=='line' and sum(v.y for v in uvx)/3.<.746:
  liner.append(q);line_uv.append([[round(v.x,7),round(1-v.y,7)] for v in uvx])
 elif role=='brow':brow_uv.append([[round(v.x,7),round(1-v.y,7)] for v in uvx])
def hits_at(x,z,group):
 uvp=None;depth=10
 for v,tx,x0,x1,z0,z1 in group:
  if not x0-.00003<=x<=x1+.00003 or not z0-.00003<=z<=z1+.00003:continue
  p,b,c=v;u,w=b-p,c-p;f=x-p.x;g=z-p.z;det=u.x*w.z-u.z*w.x
  if abs(det)<1e-12:continue
  r=(f*w.z-g*w.x)/det;t=(g*u.x-f*u.z)/det
  if min(r,t)<-2e-5 or r+t>1.00002:continue
  y=p.y+u.y*r+w.y*t
  if y<depth:depth=y;uvp=tx[0]+(tx[1]-tx[0])*r+(tx[2]-tx[0])*t
 return depth,([round(uvp.x,7),round(1-uvp.y,7)] if uvp is not None else None)
def projection(x,z,nudge=1):
 for i in range(10):
  q=hits_at(x,z+nudge*i*.00033,skins)[1]
  if q:return q
 raise ValueError(('no facial UV',x,z))
def section(x):
 allz=[]
 for tr in liner:
  for i in range(3):
   a,b=tr[i],tr[(i+1)%3]
   if min(a.x,b.x)<=x<=max(a.x,b.x) and abs(b.x-a.x)>1e-7:
    z=a.z+(x-a.x)/(b.x-a.x)*(b.z-a.z);allz.append(z)
 if not allz:raise ValueError(('No lash geometry at',x))
 return min(allz),max(allz)
def lower_edge(x,eye_z):
 sk=[q for q in skins if q[2]-.00006<=x<=q[3]+.00006]
 eyeb=[q for q in sclera if q[2]-.00006<=x<=q[3]+.00006]
 for i in range(175):
  z=eye_z-.034+i*.00029
  e=hits_at(x,z,eyeb)[0];s=hits_at(x,z,sk)[0]
  if e<min(s-.00007,9):return z
 return None
def bezier(A,B,C,E,n=15):
 for i in range(n):
  t=i/n;u=1-t
  yield tuple(u**3*a+3*u*u*t*b+3*u*t*t*c+t**3*d for a,b,c,d in zip(A,B,C,E))
def smooth(q):return q*q*(3-2*q)
rows=[]
def add(which,side,outline,nudge=1):
 try:poly=[projection(x*side,z,nudge) for x,z in outline]
 except ValueError:
  print('SKIPPED CONTOUR',which,side,flush=True);return
 rows.append({'kind':which,'uv':poly})
_,_,eyez=face_bounds(o)
for side in (-1,1):
 group=[p for t in liner for p in t if p.x*side>0]
 lo=min(p.x*side for p in group);hi=max(p.x*side for p in group);ww=hi-lo
 for r,L,H in [(.756,.121,.112),(.879,.141,.089)]:
  x=lo+ww*r;length=ww*L;lift=ww*H
  _,base=section(side*x);tip=(x+length,base+lift);endx=x+length*.49
  endz=section(side*min(endx,hi-.0002))[1]-.00107
  pt0=(x,base-.00124);p1=(x+.24*length,base+.00085);p2=(x+.77*length,base+lift*.44)
  p3=(x+length*.963,base+lift*.48);p4=(x+.84*length,base+lift*.025)
  outline=list(bezier(pt0,p1,p2,tip))+list(bezier(tip,p3,p4,(endx,endz)))+[(endx,endz)]
  add('wing',side,outline)
 # Outer 1/3 upper liner soft thickening, 15 percent of the original section.
 up=[];down=[]
 for i in range(29):
  t=i/28;q=.651+.270*t;x=lo+ww*q;low,high=section(side*x)
  amount=.15*(high-low)*max(0,math.sin(math.pi*t))**.74
  up.append((x,high+amount));down.append((x,high-.00116))
 add('upper',side,up+down[::-1])
 # Independent, softly tapered crease drawn approximately parallel with lash.
 # It uses the EYELID UV and therefore travels with the native BlendShapes.
 up=[];down=[]
 for i in range(38):
  t=i/37;q=.159+.679*t;x=lo+ww*q;zz=section(side*x)[1]
  arch=zz+(.0049+.0029*math.sin(math.pi*t)**.92)+.0008*(1-t)
  w=(.00039+.00024*math.sin(math.pi*t))*max(0,math.sin(math.pi*t))**.49
  up.append((x,arch+w));down.append((x,arch-w))
 add('crease',side,up+down[::-1])
 # Trace the currently visible outer lower eyelid, not the full eyeball geometry.
 edge=[]
 for i in range(28):
  t=i/27;q=.677+.277*t;x=lo+ww*q;z=lower_edge(side*x,eyez)
  if z is not None:edge.append((x,z-.00042))
 if len(edge)>5:
  up=[];down=[]
  for i,(x,z) in enumerate(edge):
   t=i/(len(edge)-1);w=.00049*max(0.,math.sin(math.pi*t))**.64
   up.append((x,z+w));down.append((x,z-w))
  add('innerlower',side,up+down[::-1],-1)
out=Path(os.environ.get('WING_OUT',D/'wing_uv.json'))
out.write_text(json.dumps({'strokes':rows,'main_lash':line_uv,'brow':brow_uv},separators=(',',':')))
print([(r['kind'],len(r['uv'])) for r in rows],flush=True)

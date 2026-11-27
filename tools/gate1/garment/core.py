import bpy, math, os, sys, bmesh
from math import sin,cos,pi,exp,sqrt
from mathutils import Vector, Matrix
from pathlib import Path
D=Path(os.environ.get("SUZU_GARMENT_DIR", globals().get("MODULE_DIR",Path(__file__).parent))).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
C=bpy.data.collections.new("SUZU_GARMENT")
bpy.context.scene.collection.children.link(C)
def mat(name,val):
 m=bpy.data.materials.new(name);m.diffuse_color=(val,val,val,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(val,val,val,1);p.inputs['Roughness'].default_value=.85
 return m
main=mat('Clay • tailored wool',.43); inner=mat('Clay • ivory cotton',.61); trim=mat('Clay • narrow relief',.56);shoes=mat('Clay • shoe upper',.36); shadow=mat('Clay • recessed lining',.30); stocking=mat('Clay • knit',.46); bowmat=mat('Clay • ribbon',.39)
def toC(ob):
 for c in list(ob.users_collection):c.objects.unlink(ob)
 C.objects.link(ob)
 return ob
def obj(name,vs,fs,m=main,smooth=True):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update(); ob=bpy.data.objects.new(name,me);C.objects.link(ob)
 if m:me.materials.append(m)
 if smooth:
  for p in me.polygons:p.use_smooth=True
 return ob
def grid(name,rows,m=main,cyclic=False,reverse=False,smooth=True):
 nc=len(rows[0]); nr=len(rows); faces=[]
 for i in range(nr-1):
  for j in range(nc if cyclic else nc-1):
   j2=(j+1)%nc
   f=(i*nc+j,i*nc+j2,(i+1)*nc+j2,(i+1)*nc+j)
   faces.append(f[::-1] if reverse else f)
 return obj(name,[tuple(v) for row in rows for v in row],faces,m,smooth)
def solid(o,t=.002,bev=0):
 mod=o.modifiers.new('Fabric thickness','SOLIDIFY');mod.thickness=t;mod.offset=0;mod.use_even_offset=True
 if bev:bevel(o,bev)
 return o
def bevel(o,w=.001,n=2):
 mod=o.modifiers.new('Rounded edge','BEVEL');mod.width=w;mod.segments=n;return o
def sub(o,n=1):
 mod=o.modifiers.new('Tailored subdivision','SUBSURF');mod.levels=n;mod.render_levels=n;return o
def line(name,points,r=.001,m=trim,close=False,typ='POLY'):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=5;c.bevel_depth=r;c.bevel_resolution=2
 sp=c.splines.new(typ)
 if typ=='BEZIER':
  sp.bezier_points.add(len(points)-1)
  for p,v in zip(sp.bezier_points,points):p.co=v; p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 else:
  sp.points.add(len(points)-1)
  for p,v in zip(sp.points,points):p.co=tuple(v)+(1,)
 sp.use_cyclic_u=close;c.use_fill_caps=True
 o=bpy.data.objects.new(name,c);C.objects.link(o);c.materials.append(m);return o
def curve_knots(keys,x):
 # shape-preserving Hermite interpolation; keys (time, val), clamped flat or monotone tangent
 if x<=keys[0][0]:return keys[0][1]
 if x>=keys[-1][0]:return keys[-1][1]
 for i in range(len(keys)-1):
  if keys[i][0]<=x<=keys[i+1][0]:
   x0,y0=keys[i];x1,y1=keys[i+1];h=x1-x0;t=(x-x0)/h;s=(y1-y0)/h
   def sl(j):
    if j==0:return (keys[1][1]-keys[0][1])/(keys[1][0]-keys[0][0])
    if j==len(keys)-1:return (keys[-1][1]-keys[-2][1])/(keys[-1][0]-keys[-2][0])
    a=(keys[j][1]-keys[j-1][1])/(keys[j][0]-keys[j-1][0]);b=(keys[j+1][1]-keys[j][1])/(keys[j+1][0]-keys[j][0]);return 2*a*b/(a+b) if a*b>0 else 0
   return (2*t*t*t-3*t*t+1)*y0+(-2*t*t*t+3*t*t)*y1+(t*t*t-2*t*t+t)*h*sl(i)+(t*t*t-t*t)*h*sl(i+1)
def tupinterp(table,x):
 return tuple(curve_knots([(row[0],row[j]) for row in table],x) for j in range(1,len(table[0])))
def loop_samples(points,n=4):
 # cyclic Catmull-Rom
 pts=[Vector(p) for p in points];K=len(pts);out=[]
 for i in range(K):
  p0,p1,p2,p3=[pts[(i+j)%K] for j in (-1,0,1,2)]
  for k in range(n):
   t=k/n;t2=t*t;t3=t2*t
   out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t2+(-p0+3*p1-3*p2+p3)*t3))
 return out
def ga(x,s):return exp(-(x/s)**2)
def ring(angle,xr,yr,z,cy=0):return (xr*sin(angle),cy-yr*cos(angle),z)
def sample(n):return [i*2*pi/n for i in range(n)]
def rel(v,ref=0):return (v-ref+pi)%(2*pi)-pi
def starsolid(name,c,rx,rz,ydepth,num=5,angle=pi/2,m=trim):
 cx,cy,cz=c;vs=[]
 for i in range(num*2):
  a=angle+2*pi*i/(num*2);f=1 if i%2==0 else .45;vs.append((cx+rx*f*cos(a),cy,cz+rz*f*sin(a)))
 vs+=[(cx,cy-ydepth,cz),(cx,cy+ydepth*.22,cz)];n=num*2;fs=[(n,i,(i+1)%n) for i in range(n)]+[(n+1,(i+1)%n,i) for i in range(n)]
 return obj(name,vs,fs,m,False)

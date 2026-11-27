"""Fit the two wearable forms against the evaluated Phase C jacket/shirt shell."""
from pathlib import Path
from functools import lru_cache
import bpy,bmesh,sys,os,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
import jewelry as j
OUT=Path(os.environ.get('JEWELRY_OUT', D)).resolve()
OUT.mkdir(parents=True,exist_ok=True)
TAG=os.environ.get('JEWELRY_TAG','')
S=bpy.context.scene;dep=bpy.context.evaluated_depsgraph_get()
coords=json.loads(Path(os.environ.get('JEWELRY_INTERFACES',D.parent/'top_interfaces.json')).read_text())
cfg={'bow':{'origin':[coords['bow'][0],coords['bow'][1]-.0015,coords['bow'][2]],'normal':[0,-1,0]},
     'brooch':{'origin':coords['brooch'],'normal':[.22,-.86,.43]}}
def mkbvh(obj):
 vv=[];tri=[]
 for o in obj:
  ev=o.evaluated_get(dep);m=ev.to_mesh();m.calc_loop_triangles();off=len(vv);vv.extend(ev.matrix_world@v.co for v in m.vertices)
  tri.extend(tuple(off+k for k in t.vertices) for t in m.loop_triangles);ev.to_mesh_clear()
 return BVHTree.FromPolygons(vv,tri,all_triangles=True)

parts=bpy.data.collections['SUZU_PHASE_C_TOP'].all_objects
fabric=[o for o in parts if o.type=='MESH' and (o.name.startswith('Shirt ·') or o.name.startswith('Jacket ·')) and not ('button' in o.name and 'placket' not in o.name)]
bvh=mkbvh(fabric)
shirt_bvh=mkbvh([o for o in parts if o.name.startswith('Shirt · fitted ivory front')])
def ysurf(x,z):
 hit=bvh.ray_cast(Vector((x,-.40,z)),Vector((0,1,0)),.53)[0]
 return hit.y if hit is not None else None
def surfmean(x,z):
 # Median filtering along the yarn span prevents the brooch or star chain
 # from imprinting a thin braid or a single button into the hanging fabric.
 a=[ysurf(x+u*.0013,z+v*.0013) for u,v in ((0,0),(-1,0),(1,0),(0,-1),(0,1))]
 a=sorted(k for k in a if k is not None);return a[len(a)//2] if a else None
@lru_cache(None)
def lattice(ix,iz):return surfmean(ix*.0012,iz*.0012)
def surf(x,z):
 ix=int(x//.0012);iz=int(z//.0012);dx=x/.0012-ix;dz=z/.0012-iz
 pts=[lattice(ix,iz),lattice(ix+1,iz),lattice(ix,iz+1),lattice(ix+1,iz+1)]
 if any(k is None for k in pts):return surfmean(x,z)
 return (1-dz)*((1-dx)*pts[0]+dx*pts[1])+dz*((1-dx)*pts[2]+dx*pts[3])

C,bow,bro=j.build(cfg);bpy.context.view_layer.update()
bm=bow.matrix_world;ib=bm.inverted()
# The pressed ribbon is approximately flat at the knot and follows the real
# shirt toward its bias-cut tails; preserve all front and back relief.
import math,numpy as np
# The reverse face of the bow rests on the real collar. A Lipschitz envelope
# over the physical contact points prevents the pointed collar edges from
# embossing irregular kinks into the silk volume.
bow_cloud=[];ticks=.0015; umin=-.060;vmin=1.155
xy=[];need={}
for vv in bow.data.vertices:
 x,y,z=vv.co;world=bm@vv.co
 base=bm@Vector((x,-j.bowd(x,z),z))
 root=shirt_bvh.ray_cast(Vector((base.x,-.40,base.z)),Vector((0,1,0)),.53)[0]
 if root is None:root=base
 world.y+=root.y-base.y
 bow_cloud.append(world)
 xx,zz=(world.x-umin)/ticks,(world.z-vmin)/ticks
 xy.append((xx,zz));cell=(round(xx),round(zz));front=ysurf(world.x,world.z)
 if front is not None:
  val=world.y-front
  need[cell]=max(need.get(cell,-.2),val)
keys=np.array(list(need));vals=np.array(list(need.values()))
lo=np.floor(keys.min(axis=0)-3).astype(int);hi=np.ceil(keys.max(axis=0)+3).astype(int);shape=tuple(hi-lo+1)
gx=np.arange(lo[0],hi[0]+1);gy=np.arange(lo[1],hi[1]+1)
field=np.full(shape,-1.,dtype=float)
slope=.355
for (tx,tz),val in zip(keys,vals):
 d=np.sqrt((gx[:,None]-tx)**2+(gy[None,:]-tz)**2)
 np.maximum(field,val-ticks*slope*d,out=field)
# One smooth convolution round at a weak radius keeps this a pressed broad
# drape and never pushes the inset silver work through the real garment.
pad=np.pad(field,1,mode='edge');field=(4*field+pad[1:-1,:-2]+pad[1:-1,2:]+pad[:-2,1:-1]+pad[2:,1:-1])/8.
def correction(x,z):
 xx=(x-umin)/ticks-lo[0];zz=(z-vmin)/ticks-lo[1]
 i=max(0,min(shape[0]-2,math.floor(xx)));k=max(0,min(shape[1]-2,math.floor(zz)))
 a=max(0,min(1,xx-i));b=max(0,min(1,zz-k))
 return (1-b)*((1-a)*field[i,k]+a*field[i+1,k])+b*((1-a)*field[i,k+1]+a*field[i+1,k+1])+.00118
for vv,world in zip(bow.data.vertices,bow_cloud):
 world.y-=correction(world.x,world.z);vv.co=ib@world
bow.data.update()

bpy.context.view_layer.update()
def ydiff(o):
 res=[]
 for v in o.data.vertices:
  p=o.matrix_world@v.co;q=ysurf(p.x,p.z)
  if q is not None:res.append(p.y-q)
 return sorted(res)
def fit_bro():
 dist=ydiff(bro);shift=max(dist,default=0)+.00030
 bro.location.y-=shift;bpy.context.view_layer.update()
 return shift
# Choose the closest physically wearable plane to the requested gallery angle,
# with a small tolerance for horizontal and vertical tilt (keeps the engraving readable).
old=Vector(cfg['brooch']['origin']);locs=[bro.data.vertices[i].co.copy() for i in range(0,len(bro.data.vertices),19)]
trial=[]
for dx in (-.0045,-.0025,0):
 for nx in (.21,.29,.38,.46,.54,.61):
  for nz in (.49,.58,.68,.81,.94,1.04):
   axis=Vector((nx,-1,nz)).normalized()
   if -axis.y<.651:continue
   Mf=j.frame((old.x+dx,old.y,old.z),axis);di=[]
   for q in locs:
    p=Mf@q;ys=ysurf(p.x,p.z)
    if ys is not None:di.append(p.y-ys)
   if not di:continue
   di.sort();s0=di[-1];clear=s0-di[len(di)//2]
   high=s0-di[int(len(di)*.20)]
   cost=clear+.19*high+.00070*(max(0,nz-.70)/.35)**2+.00035*(abs(dx)/.0045)**2
   trial.append((cost,clear,dx,nx,nz,Mf))
trial.sort(key=lambda k:k[0]);best=trial[0];bro.matrix_world=best[-1]
bpy.context.view_layer.update()
sh=fit_bro()
def mount():
 F=j.Form();m=bro.matrix_world;inv=m.inverted();joints=[]
 def old2v(p):return (p.x,p.z,-p.y)
 for x,z in [(-.01060,.01486),(.01377,-.01194)]:
  p=m@Vector((x,.00015,z));q=surf(p.x,p.z);w=Vector((p.x,q+.00035,p.z))
  root=inv@w;joints.append((old2v(root),(x,z,-.00015)))
 F.part('mounted twin safety clasp anchors')
 for a,b in joints:
  t1=Vector(a);t2=Vector(b);mid=(t1+t2)*.5;mid.x+=.0004
  j.tube(F,[t1,.25*t1+.75*mid,mid,.75*mid+.25*t2,t2],.00067,6,10)
  j.dome(F,a[0],a[1],.00143,a[2]-.00019,.00068,6,rz=.00111,res=20)
 bm=bmesh.new();bm.from_mesh(bro.data)
 fvs=[bm.verts.new(v) for v in F.v];layer=bm.faces.layers.int.get('suzu_feature_id')
 for ids,mi,sm in zip(F.f,F.m,F.s):
  fa=bm.faces.new(tuple(fvs[k] for k in ids));fa.material_index=mi;fa.smooth=sm
  if layer:fa[layer]=101
 bm.to_mesh(bro.data);bm.free();bro.data.update()

mount()
def sew_bow():
 # Short wrapped webbing under the central keeper, with two stitched feet on the Oxford.
 me=bow.data;me.calc_loop_triangles();mw=bow.matrix_world;inv=mw.inverted()
 probe=BVHTree.FromPolygons([mw@r.co for r in me.vertices],[tuple(t.vertices) for t in me.loop_triangles],all_triangles=True)
 F=j.Form();F.part('two pressed silk fastening tabs under the keeper')
 for x0 in (-.00315,.00315):
  z0=coords['bow'][2]+.0008
  q=probe.ray_cast(Vector((x0,.10,z0)),Vector((0,-1,0)),.38)[0];y=ysurf(x0,z0)
  if q is None or y is None:continue
  if y-q.y<=.00020:continue
  yz=[(y+.00034,z0),(y-.0010,z0+.00039),(.5*(q.y+y),z0+.00055),(q.y+.00035,z0+.00023),(q.y-.00048,z0)]
  rows=[]
  for y1,zz in yz:
   pts=[]
   for xx,zs in [(-.00121,-.00036),(.00121,-.00036),(.00121,.00036),(-.00121,.00036)]:
    lp=inv@Vector((x0+xx,y1,zz+zs));pts.append((lp.x,lp.z,-lp.y))
   rows.append(pts)
  ii=F.grid(rows,1,True,False,True);F.face(list(reversed(ii[0])),2,False);F.face(ii[-1],2,False)
 if not F.v:return
 bm=bmesh.new();bm.from_mesh(me);fvs=[bm.verts.new(v) for v in F.v];layer=bm.faces.layers.int.get('suzu_feature_id')
 for ids,mi,sm in zip(F.f,F.m,F.s):
  face=bm.faces.new(tuple(fvs[k] for k in ids));face.material_index=mi;face.smooth=sm
  if layer:face[layer]=101
 bm.to_mesh(me);bm.free();me.update()
sew_bow()
R=bpy.data.objects.get('Suzu · Humanoid')
names=[] if not R else [b.name for b in R.data.bones]
name=next((x for x in ('J_Bip_C_UpperChest','J_Bip_C_Chest','J_Bip_C_Spine') if x in names),None)
if name:
 for o in (bow,bro):
  g=o.vertex_groups.new(name=name);g.add(list(range(len(o.data.vertices))),1.,'REPLACE');o['suzu_attach_bone']=name
  mod=o.modifiers.new('Follow upper chest','ARMATURE');mod.object=R
bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
def desc(o):
 ev=o.evaluated_get(dep);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dep);me.calc_loop_triangles();coords0=[ev.matrix_world@v.co for v in me.vertices]
 allc=[];visible=[];fixture=[]
 attr=me.attributes.get('suzu_feature_id')
 feet={v for p in me.polygons if attr and attr.data[p.index].value==101 for v in p.vertices}
 for i,w in enumerate(coords0):
  q=ysurf(w.x,w.z)
  if q is not None:
   delta=w.y-q;allc.append(delta);(fixture if i in feet else visible).append(delta)
 tri=BVHTree.FromPolygons(coords0,[tuple(t.vertices) for t in me.loop_triangles],all_triangles=True)
 pairs=bvh.overlap(tri);buried=[];exposed=[]
 for c,k in pairs:
  tid=me.loop_triangles[k]
  ispin=bool(attr and attr.data[tid.polygon_index].value==101)
  (buried if ispin else exposed).append(k)
 ev.to_mesh_clear()
 visible.sort();fixture.sort()
 return {'obj':o.name,'closest_exposed_clearance_mm':round(-max(visible)*1000,3),'median_exposed_standoff_mm':round(-visible[len(visible)//2]*1000,3),
         'visible_triangle_contacts':len(exposed),'mount_only_triangle_contacts':len(buried),'max_mount_embedding_mm':round(max(fixture,default=0)*1000,3),
         'verts':len(o.data.vertices),'faces':len(o.data.polygons)}
(OUT/('fit_report'+TAG+'.json')).write_text(json.dumps({'selected_brooch_plane':[round(float(k),6) for k in best[:5]],'brooch_mount_center_y_shift_mm':sh*1000,'fit':[desc(bow),desc(bro)],'bound_bone':name},indent=2))
print((OUT/('fit_report'+TAG+'.json')).read_text(),flush=True)
bpy.context.preferences.filepaths.save_version=0
if os.getenv('JEWELRY_FULL'):
 bpy.ops.wm.save_as_mainfile(filepath=str((OUT/('wear_check'+TAG+'.blend')).resolve()),compress=True)
# The material and original local right-handed axes are kept; store only the two
# wearable meshes. A local duplicate armature should not accompany the append.
for o in (bow,bro):
 if o.modifiers.get('Follow upper chest'):o.modifiers.remove(o.modifiers['Follow upper chest'])
# Vertex weights and explicitly named binding hint remain for the final rig.
companions={bpy.data.materials[m['suzu_glb_material']] for o in (bow,bro) for m in o.data.materials if m and m.get('suzu_glb_material')}
bpy.data.libraries.write(str((OUT/('fitted_jewelry'+TAG+'.blend')).resolve()),{C,*companions},compress=True,fake_user=True)

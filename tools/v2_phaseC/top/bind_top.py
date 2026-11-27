"""Transfer the approved skin's native VRM weights to the tailored top."""
import bpy,os,sys,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from collections import defaultdict
D=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
S=bpy.context.scene;R=S.objects['Suzu · Humanoid'];B=S.objects['Suzu · Body']
if args:
 with bpy.data.libraries.load(str(Path(args[0]).resolve()),link=False) as (a,b):
  assert 'SUZU_PHASE_C_TOP' in a.collections
  wanted=['SUZU_PHASE_C_TOP']
  if 'SUZU_TOP_JEWELRY' in a.collections:wanted.append('SUZU_TOP_JEWELRY')
  b.collections=wanted
 for col in b.collections:S.collection.children.link(col)
if os.getenv('TOP_JEWELRY'):
 with bpy.data.libraries.load(os.getenv('TOP_JEWELRY'),link=False) as (a,b):b.collections=['SUZU_TOP_JEWELRY']
 S.collection.children.link(b.collections[0])
C=bpy.data.collections['SUZU_PHASE_C_TOP']
coat=list(C.all_objects)
jew=bpy.data.collections.get('SUZU_TOP_JEWELRY')
if jew:
 coat+=list(jew.all_objects)
if 'SUZU_TOP_JEWELRY' in bpy.data.collections and bpy.data.collections['SUZU_TOP_JEWELRY'].name in S.collection.children:
 # One logical top for downstream append. All object-relative transform and side labels remain.
 S.collection.children.unlink(jew);C.children.link(jew)
# Map the original rest mesh (not the scene's current sample action).
M=B.matrix_world.copy();m=B.data;m.calc_loop_triangles()
ps=[M@v.co for v in m.vertices]
g_name=[g.name for g in B.vertex_groups]
ws=[{g_name[g.group]:g.weight for g in v.groups if g.weight>1.e-7 and g_name[g.group] in R.data.bones} for v in m.vertices]
def side_group(s,y):
 name='_'+s+'_'
 return sum(w for k,w in y.items() if name in k and ('Arm' in k or 'Shoulder' in k or 'Hand' in k or 'Thumb' in k or 'Index'in k or 'Ring' in k or 'Little' in k or 'Middle' in k))
armq=[(side_group('L',y),side_group('R',y)) for y in ws]
ts=[tuple(t.vertices) for t in m.loop_triangles];trees={}
for tag in ('torso','arm_L','arm_R','full'):
 a=tag[-1];part=[]
 for tri in ts:
  if tag=='full':ans=True
  else:
   sl=sum(armq[t][0] for t in tri)/3; sr=sum(armq[t][1] for t in tri)/3
   zs=sum(ps[t].z for t in tri)/3
   if tag=='torso':ans=sl+sr<.83 and .930<zs<1.383
   else:ans=(sl if a=='L' else sr)>.095 and zs<1.320
  if ans:part.append(tri)
 trees[tag]=(part,BVHTree.FromPolygons(ps,part,all_triangles=True))
def getw(q,tag):
 tr,b=trees.get(tag,trees['torso'])
 p,nn,i,dist=b.find_nearest(q)
 if p is None:
  tr,b=trees['full'];p,nn,i,dist=b.find_nearest(q)
 ii=tr[i];a=ps[ii[0]];u=ps[ii[1]]-a;v=ps[ii[2]]-a;d=p-a
 uu,uv,vv,du,dv=u.dot(u),u.dot(v),v.dot(v),d.dot(u),d.dot(v)
 de=uu*vv-uv*uv
 if abs(de)<1.e-20:bc=(1.,0.,0.)
 else:
  r=(vv*du-uv*dv)/de;t=(uu*dv-uv*du)/de;bc=(1-r-t,r,t)
 w=defaultdict(float)
 for x,coeff in zip(ii,bc):
  c=max(0.,min(1.,coeff))
  for g,value in ws[x].items():w[g]+=c*value
 if not w:w['J_Bip_C_UpperChest']=1.
 w=[(k,v) for k,v in sorted(w.items(),key=lambda r:-r[1]) if v>9.e-6]
 s=sum(v for k,v in w)
 return {k:v/s for k,v in w} if s>1.e-6 else {'J_Bip_C_UpperChest':1.}
slots={}
def bind(o):
 if o.type!='MESH':return
 tag=o.get('suzu_cloth_group','torso')
 # Jewelry remains solid and has a rigid local shirt pad; all cloth and
 # trim inherits mapped samples from the identical native base triangles.
 has_jewel=jew and o.name in jew.all_objects
 if has_jewel and len(o.vertex_groups):
  good=[g for g in o.vertex_groups if g.name in R.data.bones]
  if len(good)==0:o.vertex_groups.clear()
 else:o.vertex_groups.clear()
 if not len(o.vertex_groups):
  mapgroups={}
  for v in o.data.vertices:
   q=o.matrix_world@v.co;ww=getw(q,tag)
   for k,w in ww.items():
    if k not in mapgroups:mapgroups[k]=o.vertex_groups.new(name=k)
    mapgroups[k].add([v.index],w,'REPLACE')
 o['suzu_stage_role']='costume_top'
 for a in list(o.modifiers):
  if a.type=='ARMATURE':o.modifiers.remove(a)
 if os.getenv('TOP_NO_MODIFIER','0')!='1':
  md=o.modifiers.new('Phase C mapped VRM skin','ARMATURE');md.object=R;md.use_deform_preserve_volume=True
 slots[o.name]=len(o.vertex_groups)
for o in coat:bind(o)
fails=[]
for o in coat:
 if o.type!='MESH':continue
 for v in o.data.vertices:
  q=sum(g.weight for g in v.groups)
  if abs(q-1)>1.e-4:fails.append((o.name,v.index,q))
assert not fails,fails[:8]
C['native_vrm_weights']=True
out=Path(os.getenv('TOP_BOUND',D/'top_bound.blend'))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)
print('Bound',len(slots),'top pieces; normalized native influences, A/B unchanged.')
(D/os.getenv('TOP_WEIGHT_LOG','top_weights.json')).write_text(json.dumps(slots,indent=2))

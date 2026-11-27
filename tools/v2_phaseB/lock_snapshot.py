"""Fingerprint every approved item before and after Phase B hair is appended."""
from pathlib import Path
from hashlib import sha256
from array import array
import json,sys,bpy

out=Path(sys.argv[sys.argv.index('--')+1])
def hjson(x):
 return sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def coords(data):
 a=array('f',[0.])*(3*len(data));data.foreach_get('co',a)
 return sha256(a.tobytes()).hexdigest()
def fingerprint(o):
 me=o.data
 mats=[]
 for m in me.materials:
  if not m:continue
  textures=[]
  for n in sorted(m.node_tree.nodes,key=lambda n:n.name) if m.node_tree else []:
   if n.type=='TEX_IMAGE' and n.image:
    i=n.image;r=i.packed_file
    textures.append((n.name,i.name,list(i.size),sha256(bytes(r.data)).hexdigest() if r else None))
  nodes=[]
  for n in sorted(m.node_tree.nodes,key=lambda n:n.name) if m.node_tree else []:
   fields=[]
   for s in n.inputs:
    v=getattr(s,'default_value',None)
    if v is None:continue
    if isinstance(v,(str,int,float,bool)):fields.append((s.name,v))
    elif hasattr(v,'__len__'):fields.append((s.name,list(v)))
   nodes.append((n.name,n.bl_idname,fields))
  links=sorted((l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links) if m.node_tree else []
  mats.append((m.name,textures,hjson(nodes),hjson(links)))
 keys=me.shape_keys.key_blocks if me.shape_keys else []
 return {'basis':coords(me.vertices),'polygons':hjson([list(p.vertices) for p in me.polygons]),
     'weight':hjson([[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in me.vertices]),
     'keys':[(k.name,coords(k.data)) for k in keys], 'materials':mats,
     'world':[[round(x,9) for x in row] for row in o.matrix_world]}
scene=bpy.context.scene
names={'head':'Suzu · Face','body':'Suzu · Body','rig':'Suzu · Humanoid'}
d={r:fingerprint(scene.objects[names[r]]) for r in ('head','body')}
r=scene.objects[names['rig']]
d['rig']={'bone_count':len(r.data.bones),
          'bind':hjson([(b.name,b.parent.name if b.parent else None,list(b.head_local),list(b.tail_local),[list(v) for v in b.matrix_local]) for b in r.data.bones]),
          'constraints':hjson([(b.name,[(c.name,c.type,c.influence,c.subtarget if hasattr(c,'subtarget') else None) for c in b.constraints]) for b in r.pose.bones]),
          'drivers':hjson([(f.data_path,f.array_index,f.driver.type,f.driver.expression) for f in (r.animation_data.drivers if r.animation_data else [])])}
out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('Phase A base fingerprint',hjson(d),'58 means Basis plus 57 targets',len(d['head']['keys']))

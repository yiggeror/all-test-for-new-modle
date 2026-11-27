"""Apply original Suzu surface artwork to the existing licensed VRoid UVs.
Run in Blender with the prepared basis file open. Geometry, armatures, and shape keys are unchanged.
"""
from pathlib import Path
import bpy,math,os,sys,json
from mathutils import Vector
D=Path(__file__).resolve().parent
ALPHA_ROLES={'iris','highlight','extra','line','brow','lash'}
RGBA={'skin':'face_skin.png','iris':'eye_iris.png','white':'eye_white.png','line':'eye_line.png',
      'brow':'brow.png','mouth':'mouth.png','highlight':'spare_alpha.png','extra':'spare_alpha.png',
      'lash':'eye_line.png','body':'body_skin.png','scalp':'scalp_skin.png'}
# Order matters: select the material's meaning, not a VRoid exporter version prefix.
def role_of(name):
 m=name.lower()
 if 'study skin' in m or 'study_skin' in m:return 'body'
 for mark,role in [('faceeyeline','line'),('faceeyelash','lash'),('facebrow','brow'),
                   ('eyeiris','iris'),('eyewhite','white'),('eyehighlight','highlight'),
                   ('eyeextra','extra'),('facemouth','mouth'),('face_00_skin','skin'),('body_00_skin','body'),('hairback_00_hair','scalp')]:
  if mark in m:return role
 return None
def invsrgb(v):return v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4
def color(h):
 return [invsrgb(int(h[i:i+2],16)/255) for i in (0,2,4)]+[1.]
def step(a,b,t):
 v=max(0,min(1,(t-a)/(b-a)));return v*v*(3-2*v)
def load_maps(folder):
 content={}
 for role,nm in RGBA.items():
  if nm in content:continue
  p=Path(folder)/nm
  if not p.is_file():continue
  i=bpy.data.images.load(str(p), check_existing=True);i.name='Suzu · '+p.stem;i.colorspace_settings.name='sRGB'
  if not i.packed_file:i.pack()
  content[nm]=i
 return content
def tex_img(n,i,x,y):
 a=n.new('ShaderNodeTexImage');a.name='Suzu original '+i.name;a.image=i;a.interpolation='Linear';a.extension='EXTEND';a.location=x,y
 return a
def stable_shade_normal(geo,new,ll,field,role):
 # Custom split normals still live in the exported mesh. For NPR itself, a
 # coherent position field keeps extreme expressions from painting dark dents.
 cx,cy,cz,xr,yr,zr,neck,eye_level=field
 def vm(op,nm,loc,src=None,value=None):
  m=new('ShaderNodeVectorMath',nm,*loc);m.operation=op
  if src is not None:ll(src,m.inputs[0])
  if value is not None:m.inputs[1].default_value=value
  return m
 def mr(name,src,low,high,out0=0,out1=1,xy=(-493,-555)):
  m=new('ShaderNodeMapRange',name,*xy);m.interpolation_type='SMOOTHERSTEP';m.clamp=True
  ll(src,m.inputs['Value']);m.inputs['From Min'].default_value=low;m.inputs['From Max'].default_value=high
  m.inputs['To Min'].default_value=out0;m.inputs['To Max'].default_value=out1
  return m.outputs[0]
 a=vm('SUBTRACT','Shared head centre',(-1570,-230),geo.outputs['Position'],(cx,cy,cz))
 s=vm('MULTIPLY','Eyeless soft volume projection',(-1360,-230),a.outputs[0],(.88/xr,1/yr,.69/zr))
 o=vm('NORMALIZE','Round analytic cheek field',(-1150,-243),s.outputs[0]);q=o.outputs[0]
 v=new('ShaderNodeSeparateXYZ','Position in portrait volume',-1130,-506);ll(s.outputs[0],v.inputs[0])
 facing=mr('Shallow frontal contours',v.outputs['Y'],-.70,-.37,.59,0.,(-916,-490))
 flat=new('ShaderNodeCombineXYZ','Matte frontal facial field',-919,-742);ll(v.outputs['X'],flat.inputs[0]);flat.inputs[1].default_value=-1.11;ll(v.outputs['Z'],flat.inputs[2])
 f=vm('NORMALIZE','Soft portrait oval',(-688,-697),flat.outputs[0])
 mix=new('ShaderNodeMixRGB','Same analytic curve on both forehead meshes',-631,-438);ll(facing,mix.inputs[0]);ll(q,mix.inputs[1]);ll(f.outputs[0],mix.inputs[2])
 wp=new('ShaderNodeSeparateXYZ','Neck station in world metres',-1144,-958);ll(geo.outputs['Position'],wp.inputs[0])
 neckzone=mr('Skin join: continuous neck roll',wp.outputs['Z'],neck+.010,neck+.043,.84,0.,(-907,-946))
 nc=new('ShaderNodeCombineXYZ','Analytic neck contour',-690,-920);ll(v.outputs['X'],nc.inputs[0]);ll(v.outputs['Y'],nc.inputs[1]);nc.inputs[2].default_value=-.09
 kn=vm('NORMALIZE','Neck shell normal',(-468,-907),nc.outputs[0]);mx=new('ShaderNodeMixRGB','One face and neck tone',-436,-420)
 ll(neckzone,mx.inputs[0]);ll(mix.outputs[0],mx.inputs[1]);ll(kn.outputs[0],mx.inputs[2])
 if role=='body':
  strength=mr('Preserve original anatomical body normals',wp.outputs['Z'],neck-.080,neck-.017,0.,.91,(-169,-988))
 else:
  # The shade is stable through all eye and mouth deformations; retain a
  # small amount of the customized corner normals for the ear cartilage.
  side=new('ShaderNodeMath','Cartilage lies beside the porcelain face',-880,-1157);side.operation='ABSOLUTE';ll(v.outputs['X'],side.inputs[0])
  e0=mr('Contour-local ear detail',side.outputs[0],.641,.824,0.,1.,(-672,-1152))
  u0=mr('Ear upper edge',wp.outputs['Z'],eye_level+.009,eye_level+.034,1.,0.,(-675,-1350))
  d0=mr('Ear lower edge',wp.outputs['Z'],eye_level-.084,eye_level-.055,0.,1.,(-676,-1550))
  g0=new('ShaderNodeMath','Cartilage falloff above and below',-436,-1270);g0.operation='MULTIPLY';ll(u0,g0.inputs[0]);ll(d0,g0.inputs[1])
  g1=new('ShaderNodeMath','Ear detail on the native shell',-242,-1245);g1.operation='MULTIPLY';ll(g0.outputs[0],g1.inputs[0]);ll(e0,g1.inputs[1])
  strength=mr('Restore original shallow auricle contour',g1.outputs[0],0.,1.,.89,.23,(-51,-1452))
 j=new('ShaderNodeMixRGB','Verified expression-stable normal',-199,-470)
 if isinstance(strength,float):j.inputs[0].default_value=strength
 else:ll(strength,j.inputs[0])
 ll(geo.outputs['Normal'],j.inputs[1]);ll(mx.outputs[0],j.inputs[2])
 return vm('NORMALIZE','Unit-direction light normal',(17,-428),j.outputs[0]).outputs[0]
def dot_shade(m,n,new,ll,tex,rol,light,field):
 g=new('ShaderNodeNewGeometry','Smooth avatar-facing normal',-1781,-205)
 smooth=stable_shade_normal(g,new,ll,field,rol)
 dot=new('ShaderNodeVectorMath','Key direction • world space',-507,-85);dot.operation='DOT_PRODUCT'
 ll(smooth,dot.inputs[0]);dot.inputs[1].default_value=light
 a=new('ShaderNodeMapRange','Wide feather at face-shadow boundary',-285,-122)
 a.clamp=True;a.interpolation_type='SMOOTHERSTEP'
 ll(dot.outputs['Value'],a.inputs['Value']);a.inputs['From Min'].default_value=.015;a.inputs['From Max'].default_value=.60
 a.inputs['To Min'].default_value=0.;a.inputs['To Max'].default_value=1.
 base=color('FDECDA');dark=color('D8AEA0')
 # The absolute shade remains D8AEA0 at the untinted portrait base.
 f=new('ShaderNodeMixRGB','Warm #D8AEA0 → ivory #FDECDA',-42,-80);f.inputs[1].default_value=[dark[i]/base[i] for i in range(3)]+[1];f.inputs[2].default_value=(1,1,1,1);ll(a.outputs['Result'],f.inputs[0])
 c=new('ShaderNodeMixRGB','Tint the original 2K portrait paint',210,66);c.blend_type='MULTIPLY';c.inputs[0].default_value=1
 ll(tex.outputs['Color'],c.inputs[1]);ll(f.outputs[0],c.inputs[2]);return c.outputs[0]
def make_mat(role,variant,img,light,alpha,field):
 m=bpy.data.materials.new('Suzu A • '+role+' • '+variant)
 m.use_nodes=True;m.use_backface_culling=False
 m['suzu_phase_a_role']=role;m['suzu_style']=variant
 if alpha:
  try:m.surface_render_method='DITHERED'
  except AttributeError:m.blend_method='HASHED'
 m.diffuse_color={'skin':tuple(color('FDECDA')),'body':tuple(color('FDECDA')),'scalp':tuple(color('FDECDA')),'brow':tuple(color('846A7C')),'line':tuple(color('372333')),'white':tuple(color('FFF9F5')),'iris':tuple(color('504071'))}.get(role,(.4,.4,.4,1))
 n=m.node_tree.nodes;n.clear();ll=m.node_tree.links.new
 def nn(cls,name,x,y):
  r=n.new(cls);r.label=name;r.location=x,y;return r
 tex=tex_img(n,img,-747,292)
 out=nn('ShaderNodeOutputMaterial','Material output',910,160)
 if variant=='Export':
  pb=nn('ShaderNodeBsdfPrincipled','Portable glTF • base texture retained',530,232);ll(tex.outputs['Color'],pb.inputs['Base Color'])
  pb.inputs['Roughness'].default_value=.80
  if 'Specular IOR Level' in pb.inputs:pb.inputs['Specular IOR Level'].default_value=.14
  if role in ('iris','highlight','brow','line','lash','white','mouth','extra'):
   ll(tex.outputs['Color'],pb.inputs['Emission Color']);pb.inputs['Emission Strength'].default_value=.22
  if alpha:ll(tex.outputs['Alpha'],pb.inputs['Alpha'])
  ll(pb.outputs[0],out.inputs['Surface'])
 elif variant=='Clay':
  if role in {'skin','body','scalp'}:
   p=nn('ShaderNodeBsdfPrincipled','Clay without makeup',496,159);p.inputs['Roughness'].default_value=.88;p.inputs['Base Color'].default_value=(.49,.49,.49,1);p.inputs['Specular IOR Level'].default_value=.10;l=p.outputs[0]
  else:
   p=nn('ShaderNodeEmission','Neutral anatomy while keeping trim geometry',486,165)
   c={'iris':.36,'white':.70,'brow':.40,'line':.29,'lash':.30,'mouth':.39,'highlight':.70,'extra':.28}.get(role,.45)
   p.inputs['Color'].default_value=(c,c,c,1);l=p.outputs[0]
  if alpha:
   t=nn('ShaderNodeBsdfTransparent','Transparent UV mask',481,-69);q=nn('ShaderNodeMixShader','Alpha retained in clay',728,92)
   ll(tex.outputs['Alpha'],q.inputs[0]);ll(t.outputs[0],q.inputs[1]);ll(l,q.inputs[2]);l=q.outputs[0]
  ll(l,out.inputs['Surface'])
 else:
  c=dot_shade(m,n,nn,ll,tex,role,light,field) if role in {'skin','body','scalp'} else tex.outputs['Color']
  em=nn('ShaderNodeEmission','Controlled anime tone',535,172);ll(c,em.inputs['Color']);l=em.outputs[0]
  if alpha:
   t=nn('ShaderNodeBsdfTransparent','Transparent UV plane',521,-69)
   q=nn('ShaderNodeMixShader','Localized alpha',737,107)
   ll(tex.outputs['Alpha'],q.inputs[0]);ll(t.outputs[0],q.inputs[1]);ll(em.outputs[0],q.inputs[2]);l=q.outputs[0]
  ll(l,out.inputs['Surface'])
 m.use_fake_user=True
 return m
def world_face_o():
 for o in bpy.context.scene.objects:
  if o.type=='MESH' and any(s.material and (role_of(s.material.name)=='skin' or s.material.get('suzu_phase_a_role')=='skin') for s in o.material_slots):return o
 raise RuntimeError('No licensed VRoid face UV material slot in this scene.')
def role_slot(o,i):
 if i<0 or i>=len(o.material_slots):return None
 sl=o.material_slots[i]; m=sl.material
 return (m.get('suzu_phase_a_role') or role_of(m.name)) if m else None
def face_bounds(o):
 p=o.data
 ids={v for f in p.polygons if role_slot(o,f.material_index)=='skin' for v in f.vertices}
 ws=[o.matrix_world@p.vertices[v].co for v in ids]
 l=Vector(tuple(min(q[i] for q in ws) for i in range(3)));h=Vector(tuple(max(q[i] for q in ws) for i in range(3)))
 eyes=[o.matrix_world@p.vertices[v].co for f in p.polygons if role_slot(o,f.material_index)=='iris' for v in f.vertices]
 ez=(sum(q.z for q in eyes)/len(eyes)) if eyes else l.z+(h.z-l.z)*.43
 return l,h,ez
def smooth_porcelain(face):
 # Face/upper scalp share one spatial field rather than different donor normals
 # on either side of the scalp material. Facial expression mesh topology is intact.
 l,h,ez=face_bounds(face)
 lo=list(l);hi=list(h)
 pieces=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(role_slot(o,i) in ('skin','scalp','body') for i in range(len(o.material_slots)))]
 for ob in pieces:
  me=ob.data
  ids={v for f in me.polygons if role_slot(ob,f.material_index)=='scalp' for v in f.vertices}
  for i in ids:
   p=ob.matrix_world@me.vertices[i].co
   for k in range(3):lo[k]=min(lo[k],p[k]);hi[k]=max(hi[k],p[k])
 cx=(lo[0]+hi[0])/2;cy=(lo[1]+hi[1])/2
 hz=max(.19,hi[2]-l.z);xr=(hi[0]-lo[0])*.50;yr=max(.078,(hi[1]-lo[1])*.5)
 cz=ez+.042*(hz/.237);zr=hz*.45
 for o in pieces:
  me=o.data
  tr=o.matrix_world.to_3x3();it=tr.inverted()
  acc=[c.vector.copy() for c in me.corner_normals]
  for p in me.polygons:
   role=role_slot(o,p.material_index)
   if role not in ('skin','scalp','body'):continue
   p.use_smooth=True
   for k in p.loop_indices:
    pt=o.matrix_world@me.vertices[me.loops[k].vertex_index].co
    x=(pt.x-cx)/max(.001,xr);y=(pt.y-cy)/yr;z=(pt.z-cz)/zr
    n0=(tr@acc[k]).normalized()
    nSphere=Vector((.88*x,y,.69*z)).normalized()
    nFace=Vector((.93*x,-1.11,.57*z)).normalized()
    n=nSphere.lerp(nFace,step(.35,.62,-y)*.72)
    w=1.
    ear=step(.71,.92,abs(x))*(1-step(ez+.012,ez+.029,pt.z))*step(ez-.088,ez-.054,pt.z)
    w*=1-.91*ear
    if role=='body':
     w*=step(l.z-.083,l.z-.028,pt.z)
    # The throat switches to the same soft neck field on both materials, 
    # blending harmlessly into the preserved original body on the collar bone.
    th=1-step(l.z+.011,l.z+.045,pt.z)
    neck=Vector((x,.78*y,-.09)).normalized()
    n=n.lerp(neck,th*.88)
    acc[k]=(it@n0.lerp(n,w)).normalized()
  if hasattr(me,'use_auto_smooth'):me.use_auto_smooth=True
  me.normals_split_custom_set(acc)
 return cx,cy,cz,xr,yr,zr,l.z,ez
def make_library(folder,light=(-.46,-.78,.44)):
 o=world_face_o();field=smooth_porcelain(o)
 maps=load_maps(folder)
 color_roles={}
 for k,key in RGBA.items():
  if key not in maps:continue
  img=maps[key];alpha=k in ALPHA_ROLES or (img.channels==4 and k in ('brow','lash','line') and 'Twist' not in str(folder))
  # Force Blender/export alpha for coverage textures regardless of source VRM alphaMode.
  color_roles[k]={v:make_mat(k,v,img,Vector(light).normalized(),alpha,field) for v in ('NPR','Export','Clay')}
 return color_roles
def assign(variants,version='NPR'):
 replaced=0
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  for idx,s in enumerate(o.material_slots):
   k=role_slot(o,idx)
   if k in variants:
    s.material=variants[k][version];replaced+=1
 return replaced
def hidden_for_face(o,head_only=False):
 for it in bpy.context.scene.objects:
  if it is o:continue
  if it.type=='MESH':
   it.hide_render=True
   if not head_only and any(role_slot(it,i) in ('body','scalp') for i in range(len(it.material_slots))):it.hide_render=False
def studio(o):
 l,h,eye=face_bounds(o);cs=bpy.context.scene
 if cs.world is None:cs.world=bpy.data.worlds.new('Suzu portrait studio')
 cs.world.use_nodes=True;bg=cs.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.135,.158,.204,1);bg.inputs['Strength'].default_value=.8
 cs.view_settings.view_transform='Standard';cs.view_settings.look='None';cs.view_settings.exposure=0;cs.view_settings.gamma=1
 for it in list(cs.objects):
  if it.type in ('CAMERA','LIGHT'):it.hide_render=True
 cam=bpy.data.cameras.new('Suzu face orthographic');cam.type='ORTHO';cam.clip_start=.02
 oo=bpy.data.objects.new(cam.name,cam);cs.collection.objects.link(oo);cs.camera=oo
 def light(n,loc,tar,pow,size):
  q=bpy.data.lights.new(n,'AREA');p=bpy.data.objects.new(n,q);cs.collection.objects.link(p)
  p.location=loc;p.rotation_euler=(tar-p.location).to_track_quat('-Z','Y').to_euler();q.energy=pow;q.size=size
 lowerY=l.y;upperY=h.y
 for ob in cs.objects:
  if ob.type!='MESH':continue
  for f in ob.data.polygons:
   if role_slot(ob,f.material_index)!='scalp':continue
   for q in f.vertices:
    ya=(ob.matrix_world@ob.data.vertices[q].co).y;lowerY=min(lowerY,ya);upperY=max(upperY,ya)
 center=Vector(((l.x+h.x)*.5,(lowerY+upperY)*.5,l.z+(h.z-l.z)*.512))
 light('wide soft key',center+Vector((-.77,-.91,.92)),center,122,1.14)
 light('cheek bounce',center+Vector((.63,-.74,.35)),center,40,1.0)
 light('subtle edge',center+Vector((.26,.7,.37)),center,90,.72)
 if os.environ.get('NPR_ENGINE','CYCLES')=='CYCLES':
  cs.render.engine='CYCLES';cs.cycles.samples=int(os.environ.get('NPR_SAMPLES','14'));cs.cycles.use_denoising=False
  cs.cycles.max_bounces=5;cs.cycles.transparent_max_bounces=16
 else:
  cs.render.engine='BLENDER_EEVEE_NEXT'
 cs.render.image_settings.file_format='PNG';cs.render.resolution_percentage=100;cs.render.film_transparent=False
 def shot(name,deg,w,hPx,shape='full'):
  a=math.radians(deg);p=center.copy();s=max((h.z-l.z)*1.24,(upperY-lowerY)*1.20,(h.x-l.x)*1.21)
  if shape=='eye':
   p.x+= (h.x-l.x)*.173;p.y-=.027;p.z=eye+.009;s= (h.x-l.x)*.38
  elif shape=='face':
   p.z=eye-.035;s=(h.x-l.x)*1.18
  oo.location=p+Vector((math.sin(a)*2,-math.cos(a)*2,.045 if shape!='eye' else .009))
  oo.rotation_euler=(p-oo.location).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=s
  cs.render.resolution_x=w;cs.render.resolution_y=hPx;cs.render.filepath=str(name)
  bpy.ops.render.render(write_still=True)
 return shot
def main():
 o=world_face_o()
 folder=Path(os.environ.get('SUZU_PAINT',D/'texture'/'PixivTwist'))
 variants=make_library(folder)
 print('Assigned',assign(variants),'original atlas materials',flush=True)
 cs=bpy.context.scene;cs.view_settings.view_transform='Standard';cs.view_settings.look='None';cs.view_settings.exposure=0
 prev_only=os.environ.get('PAINT_HEAD_ONLY','1')=='1'
 if prev_only:hidden_for_face(o)
 if os.getenv('MAKEUP_SAVE','1')=='1':
  bpy.context.preferences.filepaths.save_version=0
  bpy.ops.wm.save_as_mainfile(filepath=str(Path(os.environ.get('PAINT_OUT',D/'suzu_makeup_test.blend'))),compress=True)
 if os.getenv('MAKEUP_RENDER','1')=='1':
  shot=studio(o);out=Path(os.environ.get('PAINT_PREV',D/'previews'));out.mkdir(exist_ok=True)
  # Render geometry, not a flat composition of concept art.
  for a in map(int,os.getenv('MAKEUP_ANGLES','0,37,90').split(',')):
   shot(out/(f'npr_{a:03}.png'),a,650,650)
  if os.getenv('MAKEUP_EYE','1')=='1':shot(out/'eye_close.png',14,760,632,'eye')
  if os.getenv('MAKEUP_CLAY')=='1':
   assign(variants,'Clay')
   for a in (0,35,90,325):shot(out/(f'clay_{a:03}.png'),a,650,650)
   assign(variants,'NPR')
  expr=os.getenv('MAKEUP_EXPRESSION_MAP')
  if expr:
   mapping=json.loads(Path(expr).read_text())
   keys=o.data.shape_keys.key_blocks if o.data.shape_keys else []
   for label,preset in mapping.items():
    for k in list(keys)[1:]:k.value=preset.get(k.name,0.)
    bpy.context.view_layer.update();shot(out/(label+'.png'),12,660,660,'face')
   for k in list(keys)[1:]:k.value=0.
 if os.getenv('MAKEUP_GLB')=='1':
  assign(variants,'Export')
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
  bpy.context.view_layer.objects.active=o
  bpy.ops.export_scene.gltf(filepath=str(D/'local_makeup_export_test.glb'),export_format='GLB',use_selection=True)
  assign(variants,'NPR')
if __name__=='__main__':main()

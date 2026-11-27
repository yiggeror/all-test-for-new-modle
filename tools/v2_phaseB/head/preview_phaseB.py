"""Orthographic evidence from the actual Phase A base and appended Phase B hair."""
from pathlib import Path
import bpy,sys,math
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:];dst=Path(args[0]).resolve();dst.mkdir(parents=True,exist_ok=True)
sc=bpy.context.scene; flags=set(args[1:]);bc=next((a.split('=',1)[1] for a in args if a.startswith('back=')),None)
if bc:
  with bpy.data.libraries.load(str(Path(bc).resolve()),link=False) as (f,t):
    nm=next(n for n in f.collections if n.startswith('SUZU_HAIR_BACK'));t.collections=[nm]
  parent=bpy.data.collections['SUZU_PHASE_B_HAIR'];parent.children.link(t.collections[0]);bpy.context.view_layer.update()
for o in sc.objects:
  if o.type in ('LIGHT','CAMERA') or o.name.lower().startswith('icosphere'):o.hide_render=True
if 'fixture' in flags:
  bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dst/'head_fit.blend'),compress=True)

if "fixture-only" in flags:sys.exit(0)

if 'palette' in flags:
  names={'crown':(.46,.43,.53),'bang':(.54,.49,.58),'side':(.41,.40,.51),'back_inner':(.14,.16,.26),'back_mid':(.33,.37,.48),'back_outer':(.45,.51,.64),'pony':(.43,.46,.57),'fine':(.55,.58,.70),'ahoge':(.52,.49,.58)}
  for m in bpy.data.materials:
    if m.name.startswith('SUZU_HAIR_') and m.use_nodes:
      v=names.get(m.name[10:].lower());p=m.node_tree.nodes.get('Principled BSDF')
      if v and p:p.inputs['Base Color'].default_value=(*v,1)
w=bpy.data.worlds.new('Soft neutral inspection');w.use_nodes=True;sc.world=w;n=w.node_tree.nodes.get('Background');n.inputs['Color'].default_value=(.143,.167,.203,1);n.inputs['Strength'].default_value=.82
aim=Vector((.007,.046,1.389))
def look(o,at):o.rotation_euler=(at-o.location).to_track_quat('-Z','Y').to_euler()
for name,p,power,size in [('Key',(-1.15,-1.62,2.70),93,1.04),('Review fill',(1.31,-1.52,2.11),68,1.18),('Rim',(1.23,1.82,2.62),124,.92),('Back softbox',(-1.03,1.62,1.79),75,1.18)]:
  l=bpy.data.lights.new(name,'AREA');l.energy=power*.265;l.shape='DISK';l.size=size;o=bpy.data.objects.new(name,l);sc.collection.objects.link(o);o.location=p;look(o,aim)
d=bpy.data.cameras.new('Phase B orthographic camera');cam=bpy.data.objects.new(d.name,d);sc.collection.objects.link(cam);sc.camera=cam;d.type='ORTHO';d.clip_start=.01;d.clip_end=20
sc.render.engine='CYCLES';sc.cycles.samples=18 if 'quick' in flags else 48;sc.cycles.use_denoising=False;sc.cycles.max_bounces=4;sc.cycles.diffuse_bounces=1;sc.cycles.transparent_max_bounces=12
sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=sc.render.resolution_y=(570 if 'quick' in flags else 820);sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=-.15
sc.render.film_transparent=False
views={'front':(0,0),'left34':(36,0),'left90':(90,0),'back':(180,0),'right90':(-90,0),'high':(39,29),'low':(35,-22)}
request=flags.intersection(views) or set(views)
for label,(az,el) in views.items():
  if label not in request:continue
  a,b=map(math.radians,(az,el));at=Vector((.012,.061,1.328));scale=.794
  if 'portrait' in flags and label not in ('back',):at=Vector((.039,.048,1.489));scale=.503
  elif label in ('front','left34') and 'compact' in flags:at=Vector((.014,.050,1.402));scale=.631
  cam.location=at+2.4*Vector((math.sin(a)*math.cos(b),-math.cos(a)*math.cos(b),math.sin(b)));look(cam,at);d.ortho_scale=scale
  sc.render.filepath=str(dst/(label+'.png'));bpy.ops.render.render(write_still=True)

"""Render aligned Phase B preview, clay/NPR, expressions and blind-angle studies."""
from pathlib import Path
import argparse,sys,math,json
import bpy
from mathutils import Vector

a=argparse.ArgumentParser(description=__doc__)
a.add_argument('out',type=Path)
a.add_argument('--mode',choices=('wip','all','views','camera-check'),default='all')
a.add_argument('--samples',type=int,default=24)
args=a.parse_args(sys.argv[sys.argv.index('--')+1:])
out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
sc=bpy.context.scene
face=sc.objects['Suzu · Face']
body=sc.objects['Suzu · Body']
rig=sc.objects['Suzu · Humanoid']
added=[o for o in sc.objects if o.type=='MESH' and o not in (face,body) and not o.hide_render]
if args.mode!='camera-check':
    assert added, 'Load real hair and props before rendering'
    assert not any('icosphere' in o.name.lower() for o in added)
initial={o.name:[s.material for s in o.material_slots] for o in (face,body,*added)}
def diffuse(name,rgb):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value=(*rgb,1)
    n.inputs['Roughness'].default_value=.86
    n.inputs['Specular IOR Level'].default_value=.14
    return m
hair_clay=diffuse('Phase B neutral hair',(.42,.42,.44))
prop_clay=diffuse('Phase B neutral mount',(.32,.33,.35))
role_clay={m.get('suzu_phase_a_role'):m for m in bpy.data.materials if m.get('suzu_style')=='Clay'}
normals={o.name:[c.vector.copy() for c in o.data.corner_normals] for o in (face,body)}
def choose(clay):
    for o in (face,body,*added):
        for i,mat in enumerate(initial[o.name]):
            if clay:
                if o in (face,body):
                    o.material_slots[i].material=role_clay.get(mat.get('suzu_phase_a_role',''),mat) if mat else mat
                else:
                    o.material_slots[i].material=prop_clay if 'prop' in o.get('suzu_stage_role','') else hair_clay
            else:
                o.material_slots[i].material=mat
    for o in (face,body):
        ns=[(0.,0.,0.) for _ in o.data.loops] if clay else normals[o.name]
        o.data.normals_split_custom_set(ns)
    sc.view_settings.exposure=-.17 if clay else 0.
    bpy.context.view_layer.update()
sc.render.engine='CYCLES';sc.cycles.samples=args.samples
sc.cycles.use_denoising=False;sc.cycles.transparent_max_bounces=16
sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
sc.render.resolution_percentage=100
if sc.world is None:sc.world=bpy.data.worlds.new('Phase B world')
sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background')
bg.inputs[0].default_value=(.115,.138,.185,1);bg.inputs[1].default_value=.77
for o in sc.objects:
    if o.type=='LIGHT':o.hide_render=True
def light(name,pos,tar,pow,size,color=(1,1,1)):
    d=bpy.data.lights.new(name,'AREA');d.energy=pow;d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);sc.collection.objects.link(o)
    o.location=Vector(pos);o.rotation_euler=(Vector(tar)-o.location).to_track_quat('-Z','Y').to_euler()
focus=(0,.021,1.326)
light('Broad clay key',(-1.0,-2.4,3.2),focus,116,3.25)
light('Broad clay bounce',(.91,-1.57,.88),focus,46,2.60,(.90,.94,1))
light('Subtle edge',(.3,1.56,2.45),focus,82,2.5,(.93,.94,1))
cd=bpy.data.cameras.new('Phase B orthographic');cd.type='ORTHO';cd.clip_start=.005
cam=bpy.data.objects.new(cd.name,cd);sc.collection.objects.link(cam);sc.camera=cam
def shot(filename,az,elev=0,target=focus,span=.810,w=680,h=680):
    az,elev=map(math.radians,(az,elev))
    t=Vector(target);d=Vector((math.sin(az)*math.cos(elev),-math.cos(az)*math.cos(elev),math.sin(elev)))
    cam.location=t+d*3.15;cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
    cd.ortho_scale=span;sc.render.resolution_x=w;sc.render.resolution_y=h
    sc.render.filepath=str(out/(filename+'.png'))
    bpy.ops.render.render(write_still=True)

ks=face.data.shape_keys.key_blocks
def reset():
    for k in ks[1:]:k.value=0
    bpy.context.view_layer.update()
reset()
views=[('front',0),('threeq',43),('left',90),('right',270),('back',180)]
if args.mode in ('wip','camera-check'):
    choose(args.mode=='camera-check')
    for n,az in (views[:2]+views[-1:]):
        shot(n,az)
else:
    for clay,label in [(True,'clay'),(False,'npr')]:
        choose(clay)
        for n,az in views: shot(label+'_'+n,az)
    if args.mode=='views':sys.exit(0)
    shot('crown',28,54,(0,.015,1.584),.48)
    shot('low_clip',40,-31,(.075,-.056,1.507),.36)
    shot('back_depth',150,4,(0,.063,1.295),.69)
    for tag,az,ee,fallback,span in [
        ('moon',58,17,(.112,.004,1.592),.24),
        ('star',39,-7,(.075,-.068,1.497),.18),
        ('bow',76,4,(.13,.033,1.52),.30)]:
        t=next((o.matrix_world.translation for o in sc.objects if o.name=='PHASE_B_'+tag.upper()+'_TARGET'),fallback)
        shot(tag,az,ee,t,span)
    presets=json.loads(face['phase_a_expressions'])
    for label,preset in [('gentle','soft_smile'),('laugh','bright_laugh'),
                         ('closed','smiling_eyes'),('surprise','little_o')]:
        reset()
        for key,v in presets[preset].items():ks[key].value=v
        bpy.context.view_layer.update()
        shot(label,14,0,(0,.014,1.425),.64)
    reset()

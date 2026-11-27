"""Phase C staging cameras and controlled light trials."""
import argparse, math, sys, time
from pathlib import Path
from mathutils import Vector
import bpy
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('out',type=Path);ap.add_argument('mode',choices=['wip','stills','motion','orbit','probe','clay-wire'])
ap.add_argument('--start',type=int,default=1);ap.add_argument('--end',type=int)
ap.add_argument('--engine',choices=['cycles','eevee'],default='cycles')
ap.add_argument('--samples',type=int,default=28);ap.add_argument('--scale',type=int,default=100);ap.add_argument('--movie-border',type=int,default=0)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
sc=bpy.context.scene
rig=sc.objects['Suzu · Humanoid'];face=sc.objects['Suzu · Face'];body=sc.objects['Suzu · Body']
dc=bpy.data.cameras.new('Suzu · Review camera');dc.type='ORTHO';dc.clip_start=.005;dc.clip_end=25
cam=bpy.data.objects.new(dc.name,dc);sc.collection.objects.link(cam);sc.camera=cam
r=sc.render;r.image_settings.file_format='PNG';r.image_settings.color_mode='RGB'
r.film_transparent=False;r.resolution_percentage=a.scale;r.fps=30
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0.
if a.engine=='cycles':
    sc.render.engine='CYCLES'
    sc.cycles.samples=a.samples;sc.cycles.use_denoising=False
    sc.cycles.max_bounces=5;sc.cycles.diffuse_bounces=1;sc.cycles.transparent_max_bounces=16
    if a.mode in ('orbit','motion'):
        sc.cycles.use_adaptive_sampling=True;sc.cycles.adaptive_threshold=.052;sc.cycles.adaptive_min_samples=min(4,a.samples)
        sc.cycles.max_bounces=3;sc.cycles.diffuse_bounces=1;sc.cycles.glossy_bounces=1
        sc.cycles.transparent_max_bounces=10
        sc.render.use_persistent_data=True
        sc.render.image_settings.compression=12
else:
    sc.render.engine='BLENDER_EEVEE_NEXT';sc.eevee.taa_render_samples=a.samples
if sc.world is None:sc.world=bpy.data.worlds.new('Suzu · Studio background')
sc.world.use_nodes=True
n=sc.world.node_tree.nodes.get('Background');n.inputs['Color'].default_value=(.104,.130,.174,1);n.inputs['Strength'].default_value=.75
for o in sc.objects:
    if o.type=='LIGHT':o.hide_render=True
def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def lamp(name,loc,power,size,col=(1.,1.,1.)):
    L=bpy.data.lights.new(name,'AREA');L.energy=power;L.size=size;L.color=col
    O=bpy.data.objects.new(name,L);sc.collection.objects.link(O);O.location=loc;aim(O,(0,0,.94));return O
key=lamp('Broad review key',(-1.65,-2.7,3.14),166,2.85)
fill=lamp('Gentle reflection fill',(1.08,-1.95,1.27),58,3.15,(.90,.94,1))
rim=lamp('Ice-silver rim',(.65,1.82,2.72),127,2.66,(.91,.94,1))
def shade_direction(pos):
    v=(Vector(pos)-Vector((0,0,1.355))).normalized()
    for m in bpy.data.materials:
        if not m.node_tree:continue
        for t in m.node_tree.nodes:
            if 'key direction' in (t.label+' '+t.name).lower() and getattr(t,'operation','')=='DOT_PRODUCT':
                t.inputs[1].default_value=v
def Camera(az,tilt,target,span,w,h):
    u,v=math.radians(az),math.radians(tilt);t=Vector(target)
    cam.location=t+Vector((math.sin(u)*math.cos(v),-math.cos(u)*math.cos(v),math.sin(v)))*4.75
    aim(cam,t);dc.ortho_scale=span;r.resolution_x=w;r.resolution_y=h
def frame(name,az=0,el=0,target=(0,0,.833),span=1.83,w=540,h=870):
    Camera(az,el,target,span,w,h)
    r.filepath=str(out/(name+'.png'));t=time.monotonic()
    bpy.ops.render.render(write_still=True)
    print('Rendered',name,round(time.monotonic()-t,2),'s',flush=True)
if a.movie_border:
    assert a.mode in ('orbit','motion') and a.scale==100 and a.movie_border%8==0 and 900<=a.movie_border<=1920
    r.use_border=True;r.use_crop_to_border=True
    r.border_min_x=(1920-a.movie_border)/(2*1920);r.border_max_x=1.-r.border_min_x
    r.border_min_y=0.;r.border_max_y=1.
def neutral():
    sc.frame_set(1)
    for m in face.data.shape_keys.key_blocks[1:]:m.value=0
    bpy.context.view_layer.update()
if a.mode in ('wip','stills'):
    neutral()
    for az in (0,45,90,180) if a.mode=='wip' else range(0,360,45):
        frame('npr_%03d'%az,az)
    if a.mode=='stills':
        for nm,p in [('front',(0,-3.15,1.71)),('left',(2.13,-2.13,1.84)),('right',(-2.13,-2.13,1.84)),
                   ('top',(.08,-.24,4.24)),('rim',(0,2.58,2.54))]:
            key.location=p;aim(key,(0,0,1.03));shade_direction(p)
            frame('light_'+nm,0)
            frame('face_light_'+nm,29,0,(.010,.016,1.437),.56,580,650)
        key.location=(-1.65,-2.7,3.14);aim(key,(0,0,.94));shade_direction(key.location)
        for name,az,tar,span in [('chest',32,(.02,-.024,1.16),.42),('sleeve',39,(.32,.01,.937),.30),
                    ('hem',18,(.0,0,.746),.55),('garter',-22,(-.091,-.018,.686),.26),
                    ('shoes',-28,(0,-.032,.063),.34)]:
            frame(name,az,0,tar,span,720,580)
elif a.mode=='clay-wire':
    neutral()
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from project_edges import edge_inputs
    meshes=[o for o in sc.objects if o.type=='MESH' and not o.hide_render and 'icosphere' not in o.name.lower()]
    role={m.get('suzu_phase_a_role'):m for m in bpy.data.materials if m.get('suzu_style')=='Clay'}
    clay=bpy.data.materials.new('Suzu · Matte clay proof');clay.use_nodes=True
    p=clay.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(.47,.47,.49,1)
    p.inputs['Roughness'].default_value=.89
    p.inputs['Specular IOR Level'].default_value=.12
    for o in meshes:
        for slot in o.material_slots:
            m=slot.material
            slot.material=(role.get(m.get('suzu_phase_a_role')) if m else None) or clay
        if o in (face,body):o.data.normals_split_custom_set([(0,0,0) for _ in o.data.loops])
    sc.view_settings.exposure=-.25
    for az in (0,45,90,180):
        n='clay_%03d'%az
        frame(n,az)
        bpy.context.view_layer.update()
        wire='wire_%03d'%az
        from shutil import copyfile
        copyfile(out/(n+'.png'),out/(wire+'.png'))
        edge_inputs(meshes,cam,r.resolution_x,r.resolution_y,out/(wire+'.bin'))
elif a.mode=='probe':
    for k in (49,124,247,264):
        sc.frame_set(k);frame('draft_%03d'%k,9,0,(0,0,.864),2.36,800,600)
elif a.mode=='motion':
    for k in range(a.start,(a.end or sc.frame_end)+1):
        sc.frame_set(k)
        # A restrained editorial crop lets the actual open hand and shoulders
        # carry the motion rather than exaggerated camera travel.
        frame('motion_%04d'%k,6.,1.,(0,-.002,.903),3.22,1920,1080)
else:
    neutral()
    for i in range(a.start,(a.end or 360)+1):
        full=i<=240
        j=i-1 if full else i-241
        az=360*j/(240 if full else 120)
        frame('orbit_%04d'%i,az,2.8 if full else 3.,
              (0,.015,.835 if full else 1.271),3.22 if full else 1.70,1920,1080)

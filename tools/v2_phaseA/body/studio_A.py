"""Display the rigged Phase A neutral study in true orthographic projection."""
from pathlib import Path
from math import radians,sin,cos
import bpy,bmesh,sys,re
from mathutils import Vector
H=Path(__file__).resolve().parent
argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
O=Path(argv[0]).resolve();O.mkdir(parents=True,exist_ok=True)
modes=argv[1:] or ['front','threequarter','profile','back']
S=bpy.context.scene
S.render.engine='BLENDER_WORKBENCH'
S.display.render_aa='FXAA'
sh=S.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl'
sh.studiolight_rotate_z=.09;sh.color_type='VERTEX'
sh.show_shadows=False;sh.show_specular_highlight=False
sh.show_cavity=True;sh.cavity_type='BOTH';sh.cavity_ridge_factor=.35;sh.cavity_valley_factor=.32
sh.curvature_ridge_factor=.30;sh.curvature_valley_factor=.32
sh.background_type='WORLD';S.world=bpy.data.worlds.new('Neutral studio');S.world.color=(.65,.67,.69)
S.view_settings.view_transform='Standard';S.view_settings.look='None';S.view_settings.exposure=.06
S.render.film_transparent=True;S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGBA';S.render.resolution_percentage=100
def neutral(mat,value):
    mat.diffuse_color=(value,value,value,1.)
def ease(t):
    t=max(0.,min(1.,t));return t*t*(3.-2.*t)
for o in S.objects:
    if o.type!='MESH':continue
    for m in o.data.materials:
        n=m.name.lower()
        v=.62
        if 'iris' in n:v=.29
        elif 'white' in n:v=.85
        elif 'highlight' in n:v=.87
        elif 'brow' in n or 'line' in n or 'lash' in n:v=.16
        elif 'mouth' in n:v=.27
        neutral(m,v)
    name='StudyNeutral'
    field=o.data.color_attributes.get(name) or o.data.color_attributes.new(name=name,type='FLOAT_COLOR',domain='CORNER')
    o.data.color_attributes.active_color=field
    is_body='Suzu · Body' in o.name
    for p in o.data.polygons:
        for q in p.loop_indices:
            if is_body:
                w=o.matrix_world @ o.data.vertices[o.data.loops[q].vertex_index].co
                # Restrained grading, continuous across each surface with no
                # cuts through clavicles or apparent clothing-edge artifacts.
                v=.58-.10*ease((w.z-.705)/.052)*ease((1.172-w.z)/.092)*ease((.191-abs(w.x))/.042)
                field.data[q].color=(v,v,v,1.)
            else:
                m=o.data.materials[p.material_index];field.data[q].color=m.diffuse_color
cd=bpy.data.cameras.new('Orthographic studio camera');cd.type='ORTHO';cd.clip_start=.015
c=bpy.data.objects.new('Orthographic studio camera',cd);S.collection.objects.link(c);S.camera=c
def shot(name,az,center,ortho,elev=0,w=480,h=770):
    t=Vector(center);a=radians(az)
    c.location=t+Vector((3*sin(a),-3*cos(a),elev))
    c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=ortho
    S.render.resolution_x=w;S.render.resolution_y=h
    S.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True)
def center():
    return (0,0,.810)
views=dict(front=(0,center(),1.724),threequarter=(39,center(),1.724),profile=(90,center(),1.724),back=(180,center(),1.724),
           hand=(45,(.407,-.033,.835),.19,.31,480,480),shoulder=(48,(.085,-.010,1.216),.43,.28,550,550),
           profile_legs=(90,(0,-.025,.445),.96,0,470,700))
for n in modes:shot(n,*views[n])

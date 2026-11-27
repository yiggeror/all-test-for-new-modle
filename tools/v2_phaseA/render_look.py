"""Four matched clay/NPR portraits and four true expressions from the same scene."""
from pathlib import Path
import argparse, sys
import bpy
from mathutils import Vector

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('paint_module',type=Path)
ap.add_argument('expression_module',type=Path)
ap.add_argument('paint',type=Path)
ap.add_argument('out',type=Path)
ap.add_argument('--save',type=Path)
ap.add_argument('--only',choices=['faces','expressions'])
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
sys.path[:0]=[str(a.paint_module.resolve()),str(a.expression_module.resolve())]
from apply_makeup import make_library, assign, studio, hidden_for_face, world_face_o
from expressions_phaseA import apply_expression, write_preset_json
a.out.mkdir(parents=True,exist_ok=True)
face=world_face_o()
body=next((x for x in bpy.context.scene.objects if x.type=='MESH' and x.name.startswith('Suzu · Body')),None)
if body:
    for m in body.data.materials:
        if m and m.name.startswith('Suzu · Study skin'):
            m['suzu_phase_a_role']='body'
lib=make_library(a.paint.resolve())
assert assign(lib)>0
shot=studio(face)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=24
scene.cycles.use_denoising=False;scene.cycles.transparent_max_bounces=16
for o in scene.objects:
    if o.type=='LIGHT' and o.name in ('wide soft key','cheek bounce','subtle edge'):
        o.data.energy*=.30
if a.save is not None:
    target=Vector((0,0,.810))
    camera=scene.camera
    camera.location=target+Vector((1.53,-4.50,.02))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=1.78
    scene.render.resolution_x=810;scene.render.resolution_y=1140
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=face;face.select_set(True)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type!='VIEW_3D':continue
            space=area.spaces.active
            space.region_3d.view_location=target
            space.region_3d.view_distance=2.15
            space.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
            space.region_3d.view_perspective='ORTHO'
            space.overlay.show_floor=False
            space.overlay.show_extras=False
    face.select_set(False)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(a.save.resolve()),compress=True)
hidden_for_face(face)
if body: body.hide_render=False
write_preset_json(face,a.out/'expression_presets.json')
if a.only!='expressions':
    meshes=[o for o in (face,body) if o is not None]
    source_normals={o.name:[c.vector.copy() for c in o.data.corner_normals] for o in meshes}
    for mode in ('Clay','NPR'):
        assign(lib,mode)
        if mode=='Clay':
            scene.view_settings.exposure=-.24
            for o in meshes:
                o.data.normals_split_custom_set([(0.,0.,0.) for l in o.data.loops])
        else:
            scene.view_settings.exposure=0.
            for o in meshes: o.data.normals_split_custom_set(source_normals[o.name])
        bpy.context.view_layer.update()
        for angle in (0,45,90,315):
            shot(a.out/f'{mode.lower()}_{angle:03d}.png',angle,580,580)
    shot(a.out/'iris_close.png',14,680,580,'eye')
if a.only!='faces':
    for name,preset in [('gentle','soft_smile'),('laugh','bright_laugh'),
                         ('closed','smiling_eyes'),('surprise','little_o')]:
        apply_expression(face,preset)
        bpy.context.view_layer.update()
        shot(a.out/(name+'.png'),13,580,600)

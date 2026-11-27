"""Assemble coordinate-aligned Blender collections, then render Gate 1 assets."""
import bpy, sys, math
from pathlib import Path
from mathutils import Vector
import os
for rootdir in (Path(__file__).resolve().parent,):
    if str(rootdir) not in sys.path: sys.path.insert(0,str(rootdir))

root=Path(sys.argv[sys.argv.index("--")+1]).absolute()
out=Path(sys.argv[sys.argv.index("--")+2]).absolute()
mode=sys.argv[sys.argv.index("--")+3] if len(sys.argv)>sys.argv.index("--")+3 else "stills"
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
for role in ('HEAD','BODY','GARMENT'):
    src=root / (role.lower()+'.blend')
    if not src.exists() and mode in ('wip','test'):
        continue
    name="SUZU_"+role
    with bpy.data.libraries.load(str(src), link=False) as (srcdata,dst):
        if name not in srcdata.collections:
            raise ValueError((src, name, srcdata.collections))
        dst.collections=[name]
    sc.collection.children.link(dst.collections[0])
asset=[obj for obj in sc.objects if obj.type in ('MESH','CURVE','CURVES','SURFACE') and not obj.hide_render]
if not asset and mode=='test':
    # Test fixture only; never enters any artist deliverable.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.25,location=(0,0,1.4))
    asset=[bpy.context.object]
if not asset: raise RuntimeError("No geometry selected for the preview")
# Keep camera objects, stand-ins, and debug overlays from floating into the export.
for obj in list(sc.objects):
    if obj.type in ('CAMERA','LIGHT') or obj.hide_render:
        bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.object.select_all(action="DESELECT")
for obj in asset: obj.select_set(True)
bpy.context.view_layer.objects.active=asset[0]
if mode == 'assets':
    (out/'assets').mkdir(exist_ok=True)
    sc.unit_settings.system='METRIC'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.object.select_all(action='DESELECT')
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                view=area.spaces.active
                view.region_3d.view_location=(0,0,.825)
                view.region_3d.view_distance=2.18
                view.region_3d.view_rotation=Vector((-.22,1,-.08)).to_track_quat('-Z','Y')
                view.region_3d.view_perspective='ORTHO'
                view.shading.type='SOLID'
                view.shading.color_type='MATERIAL'
                view.overlay.show_floor=False
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'assets'/'suzu_gate1.blend'), compress=True)
    for obj in asset: obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out/'assets'/'suzu_gate1.glb'), export_format='GLB',use_selection=True)
    if mode=='assets': sys.exit()
cam_data=bpy.data.cameras.new('Suzu Ortho')
cam=bpy.data.objects.new('Suzu Ortho',cam_data)
sc.collection.objects.link(cam); sc.camera=cam
cam_data.type='ORTHO'
cam_data.clip_start=.025; cam_data.clip_end=10
sc.render.engine='BLENDER_WORKBENCH'
sc.display.render_aa='16' if mode not in ('motion','wiretest') else 'FXAA'
sh=sc.display.shading
sh.light='STUDIO'; sh.studio_light='paint.sl'; sh.studiolight_rotate_z=.18
sh.color_type='MATERIAL'; sh.single_color=(.60,.59,.57)
sh.show_shadows=False; sh.show_cavity=True; sh.cavity_type='BOTH'
sh.cavity_ridge_factor=.26; sh.cavity_valley_factor=.38
sh.curvature_ridge_factor=.16; sh.curvature_valley_factor=.25
sh.show_specular_highlight=False
sh.background_type='WORLD'; sc.world=bpy.data.worlds.new('Clay backdrop'); sc.world.color=(.189,.198,.211)
sc.view_settings.view_transform='Standard'; sc.view_settings.exposure=.15
sc.render.film_transparent=False
sc.render.image_settings.file_format='PNG'
sc.render.resolution_percentage=100
def camera(deg,target,extent,elev=0):
    rad=math.radians(deg)
    cam.location=Vector(target)+Vector((4.5*math.sin(rad),-4.5*math.cos(rad),elev))
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam_data.ortho_scale=extent
def render(name,degree,target,extent,width,height,elev=0):
    camera(degree,target,extent,elev)
    sc.render.resolution_x=width; sc.render.resolution_y=height
    sc.render.filepath=str(out/(name+'.png')); bpy.ops.render.render(write_still=True)
# face 90° left is camera on +X; never rename viewer/right to anatomical left by mistake.
if mode=='fittest':
    sc.display.render_aa='FXAA'
    sh.color_type='MATERIAL'
    sh.show_shadows=False; sh.show_cavity=False
    for ang in (0,35,90,180):
        render('fit_%03d'%ang,ang,(0,0,.825),1.76,478,740)
if mode in ('wip','test','stills'):
    size=600 if mode=='stills' else 500
    for ang in range(0,360,45) if mode=='stills' else (0,90,270):
        render('clay_%03d'%ang,ang,(0,0,.826),1.76,round(size*.64),size)
    sh.color_type='MATERIAL'
    sh.show_shadows=False
    for ang in (0,35,90,270,180) if mode=='stills' else (0,90,270):
        center=(.028,0,1.447) if ang in (0,35) else (0,.005,1.447)
        extent=.455
        if ang==180: center=(0,.09,1.31); extent=.76
        facepx=max(size,760) if mode=='stills' else size
        render('face_%03d'%ang,ang,center,extent,facepx,facepx)
if mode in ('stills','wiretest'):
    sh.color_type='MATERIAL'
    sh.show_shadows=False
    detail=[('hands',38,(.396,-.015,.831),.22),('chest',-20,(.02,-.06,1.18),.35),
            ('hairpin',35,(.092,-.03,1.511),.18),('skirt',27,(0,0,.817),.49),
            ('garter',-14,(-.11,-.02,.645),.25),('shoes',-27,(0,-.035,.061),.34)]
    if mode=='stills':
        for name,ang,target,extent in detail: render(name,ang,target,extent,610,476)
        for name,ang,target,extent,elev in (
            ('audit_crown',38,(0,.012,1.494),.49,2.15),
            ('audit_pin',55,(.038,-.031,1.463),.413,-1.65),
            ('audit_back',140,(0,.09,1.211),.62,.72),
            ('audit_shoes',42,(0,-.032,.068),.38,-.42)):
            render(name,ang,target,extent,610,476,elev=elev)
    from project_edges import edge_inputs
    sc.display.render_aa='FXAA'
    sh.color_type='SINGLE'; sh.single_color=(.75,.75,.75)
    sh.show_shadows=False; sh.show_cavity=False
    for ang in (0,45,90,180) if mode=='stills' else (0,):
        label='wire_%03d'%ang
        width,height=672,1050
        render(label,ang,(0,0,.826),1.76,width,height)
        bpy.context.view_layer.update()
        edge_inputs(asset,cam,width,height,out/(label+'.bin'))
if mode=='motion':
    sh.color_type='MATERIAL'; sh.show_shadows=False; sh.show_cavity=False
    sc.render.resolution_x=1920; sc.render.resolution_y=1080; sc.render.fps=30
    sc.frame_start=int(os.getenv('SUZU_FRAME_START','1')); sc.frame_end=int(os.getenv('SUZU_FRAME_END','210'))
    camera(0,(0,0,.823),3.13,.12)
    pivot=bpy.data.objects.new('Orbit pivot',None); sc.collection.objects.link(pivot)
    pivot.location=(0,0,.823)
    bpy.context.view_layer.update()
    mx=cam.matrix_world.copy()
    cam.parent=pivot; cam.matrix_world=mx
    for frame,spin in ((1,0),(211,2*math.pi)):
        pivot.rotation_euler.z=spin; pivot.keyframe_insert(data_path='rotation_euler',frame=frame)
    for fcu in pivot.animation_data.action.fcurves:
        for kp in fcu.keyframe_points: kp.interpolation='LINEAR'
    sc.render.filepath=str(out/'turn_'); bpy.ops.render.render(animation=True)

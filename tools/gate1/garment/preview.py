sc=bpy.context.scene
if not sc.world:sc.world=bpy.data.worlds.new('Studio')
sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs[0].default_value=(.73,.73,.73,1);sc.world.node_tree.nodes.get('Background').inputs[1].default_value=.38
def cam(n,eye,target,scale):
 c=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,c);sc.collection.objects.link(o);o.location=eye;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.type='ORTHO';c.ortho_scale=scale;c.clip_start=.005;return o
def area(n,pos,target,power,size):
 l=bpy.data.lights.new(n,'AREA');o=bpy.data.objects.new(n,l);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();l.energy=power;l.shape='DISK';l.size=size
area('Key',(-2,-2,3.3),(0,0,.85),105,1.55);area('Ribbon',(1.6,-1.1,1.9),(0,0,.8),24,1.40);area('Edge',(.65,1.35,2.4),(0,0,.9),62,1.30)
sc.render.engine='CYCLES';sc.cycles.samples=int(os.getenv('SAMPLES','10'));sc.cycles.use_denoising=False;sc.render.threads_mode='FIXED';sc.render.threads=3
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=-.5;sc.render.film_transparent=True;sc.render.image_settings.color_mode='RGBA'
def preview(name,target,dir,scale,w,h):
 target=Vector(target);c=cam(name,target+Vector(dir).normalized()*3,target,scale);sc.camera=c
 sc.render.resolution_x=w;sc.render.resolution_y=h;sc.render.resolution_percentage=100;sc.render.filepath=str(D/(name+'.png'));bpy.ops.render.render(write_still=True)

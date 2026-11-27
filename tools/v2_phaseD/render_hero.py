"""Paint-free hero photography from the locked Phase C rig. This script never saves the input .blend."""
from __future__ import annotations
import argparse,sys,math,json
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector
import bpy

P='J_Bip_'
V=Vector
X,Y,Z=V((1,0,0)),V((0,1,0)),V((0,0,1))
D2R=math.pi/180

def qxyz(x=0.,y=0.,z=0.):
    return Quaternion(Z,D2R*z)@Quaternion(Y,D2R*y)@Quaternion(X,D2R*x)

def mat_at(q,p):
    m=q.normalized().to_matrix().to_4x4();m.translation=p;return m

def projected(v,a):
    return v-a*v.dot(a)

def solve(a,c,l0,l1,pole):
    d=c-a;ell=d.length;e=d.normalized()
    d=max(abs(l0-l1)+.0002,min(l0+l1-.001,ell))
    n=projected(pole,e)
    if n.length<1.e-6:n=projected(V((0,-1,0)),e)
    u=(d*d+l0*l0-l1*l1)/(2*d)
    h=math.sqrt(max(0.,l0*l0-u*u))
    return a+e*u+n.normalized()*h,a+e*d

def assign(pb,q,at=None):
    pb.matrix=mat_at(q,at if at is not None else pb.head)

def turn_world(pb,x=0.,y=0.,z=0.):
    set_at=pb.head.copy()
    assign(pb,qxyz(x,y,z)@pb.matrix.to_quaternion(),set_at)
    bpy.context.view_layer.update()

def chain(p,side,legs):
    suffix=('UpperLeg','LowerLeg','Foot','ToeBase') if legs else ('UpperArm','LowerArm','Hand')
    return [p[P+side+'_'+n] for n in suffix]

def sample_chain(p,side,legs):
    b=chain(p,side,legs)
    return [o.matrix.copy() for o in b]

def solve_chain(b,source,target,pole,tip=None):
    q0=[Q.to_quaternion() for Q in source]
    old0,old1,old2=[Q.translation.copy() for Q in source[:3]]
    dist0=(old1-old0).length;dist1=(old2-old1).length
    a=b[0].head.copy()
    m,c=solve(a,target,dist0,dist1,pole)
    q=q0[0];r=(old1-old0).normalized().rotation_difference((m-a).normalized())
    assign(b[0],r@q,a);bpy.context.view_layer.update()
    lhead=b[1].head.copy()
    r=(old2-old1).normalized().rotation_difference((c-lhead).normalized())
    assign(b[1],r@q0[1],lhead);bpy.context.view_layer.update()
    w=b[2].head.copy()
    if tip is None:assign(b[2],r@q0[2],w)
    else:assign(b[2],tip@q0[2],w)
    bpy.context.view_layer.update()
    if len(b)>3 and tip:
        assign(b[3],tip@q0[3],b[3].head)
        bpy.context.view_layer.update()
    return (w-target).length

def turn_into_palm(p,s,desired):
    hand=p[P+s+'_Hand']; elbow=p[P+s+'_LowerArm']
    wi=hand.head.copy();arm=(wi-elbow.head).normalized()
    I=p[P+s+'_Index1'].head-wi; L=p[P+s+'_Little1'].head-wi
    n=projected(I.cross(L),arm).normalized()
    f=projected(desired,arm).normalized()
    if n.dot(f)<0:n=-n
    d=math.atan2(arm.dot(n.cross(f)),n.dot(f))
    d=max(-.58,min(.58,d))*.73
    assign(hand,Quaternion(arm,d)@hand.matrix.to_quaternion(),wi)
    bpy.context.view_layer.update()
    # Each phalanx bends toward the palm plane on its own measured joint.
    # Four degrees looks relaxed at poster scale without changing the hand shape.
    toward=Quaternion(arm,d)@n
    if s=='L':toward=-toward
    for j,stem in enumerate(('Index','Middle','Ring','Little')):
        for k in (1,2):
            b=p[P+s+'_'+stem+str(k)]
            tail=p[P+s+'_'+stem+str(k+1)].head
            dr=(tail-b.head).normalized();ax=dr.cross(toward)
            if ax.length<1.e-5:continue
            amount=(1.5+1.15*j if k==1 else 3.2+1.12*j)
            assign(b,Quaternion(ax.normalized(),D2R*amount)@b.matrix.to_quaternion(),b.head.copy())
            bpy.context.view_layer.update()

def freeze_hero_pose(sc,variant):
    rig=sc.objects['Suzu · Humanoid'];face=sc.objects['Suzu · Face'];p=rig.pose.bones
    sc.frame_set(58 if variant!='clip' else 335)
    bpy.context.view_layer.update()
    if variant=='clip':return {'base_frame':335,'pose':'locked animation clip'}
    # Changing ephemeral pose matrices never mutates mesh/rest data/action.
    values={k.name:k.value for k in face.data.shape_keys.key_blocks}
    base={k.name:k.matrix_basis.copy() for k in p}
    rig.animation_data.action=None
    face.data.shape_keys.animation_data.action=None
    for k in p:k.matrix_basis=base[k.name]
    for k in face.data.shape_keys.key_blocks:k.value=values[k.name]
    bpy.context.view_layer.update()
    C=bpy.data.collections['SUZU_PHASE_C_LOWER']
    D=bpy.context.evaluated_depsgraph_get()
    soles={}
    for s in ('L','R'):
        draw='Left' if s=='L' else 'Right';vv=[]
        for o in C.all_objects:
            if o.get('suzu_lower_role') not in ('shoe-sole','heel') or f'· {draw} ' not in o.name:continue
            e=o.evaluated_get(D);m=e.to_mesh();vv.extend(e.matrix_world@v.co for v in m.vertices);e.to_mesh_clear()
        soles[s]=vv
    legs={s:sample_chain(p,s,True) for s in ('L','R')}
    arms={s:sample_chain(p,s,False) for s in ('L','R')}
    hips=p[P+'C_Hips']
    hp=hips.head.copy()
    weight=V((-.017,-.000,-.018)) if variant=='portrait' else V((-.012,-.000,-.014))
    assign(hips,qxyz(y=2.4,z=8.7)@hips.matrix.to_quaternion(),hp+weight)
    bpy.context.view_layer.update()
    leg_res={}
    for s in ('L','R'):
        a=legs[s][2].translation.copy()
        if s=='R':
            q=qxyz(z=-8.)
            shift=V((.014,-.061,0))
            pole=V((-.09,-1.,.01))
        else:
            q=qxyz(x=8.0 if variant=='portrait' else 5.2,z=8.)
            shift=V((.008,.052 if variant=='portrait' else .043,0))
            pole=V((-.20,-1.,.07))
        ground=min((a+q@(v-a)).z for v in soles[s])
        shift.z=.0001-ground
        leg_res[s]=solve_chain(chain(p,s,True),legs[s],a+shift,pole,tip=q)
        if leg_res[s]>.0018:print('Leg reach margin variation:',s,leg_res[s])
    turn_world(p[P+'C_Spine'],x=-.6,y=1.5,z=-2.45)
    turn_world(p[P+'C_Chest'],x=1.1,y=1.25,z=-1.45)
    turn_world(p[P+'C_UpperChest'],x=.45,y=1.3,z=-.85)
    turn_world(p[P+'C_Neck'],x=-.7,y=-1.1,z=1.25)
    turn_world(p[P+'C_Head'],x=.7,y=-3.9,z=3.55)
    arm_res={}
    goals={'R':((-.302,-.095,.883),(-.37,-1.0,-.20)),
           'L':((.284,.020,.851),(.43,-.70,-.17))}
    if variant=='quiet':
        goals={'R':((-.288,-.057,.835),(-.54,-.56,-.17)),
               'L':((.302,.019,.848),(.43,-.69,-.16))}
    for s,(goal,pole) in goals.items():
        b=chain(p,s,False)
        # First solve a body-close upper/lower arm from the native source,
        # then relax the wrist rather than translating or pinning vertices.
        arm_res[s]=solve_chain(b,arms[s],V(goal),V(pole))
        turn_world(b[2],x=4.3 if s=='R' else -4.2,y=-5.7 if s=='R' else 2.5,z=-9.5 if s=='R' else 12.2)
        turn_into_palm(p,s,V((.20,-.97,.14)))
    presets=json.loads(face['phase_a_expressions'])
    for k in face.data.shape_keys.key_blocks[1:]:k.value=0.
    for name,value in presets['soft_smile'].items():face.data.shape_keys.key_blocks[name].value=value*.88
    # The subtle eyelid change uses Suzu's native locked smile key, no eye redraw.
    for name,value in presets.get('smiling_eyes',{}).items():
        if 'EYE' in name and 'Close' in name and name in face.data.shape_keys.key_blocks:
            face.data.shape_keys.key_blocks[name].value=value*.030
    bpy.context.view_layer.update()
    return {'base_frame':58,'pose':variant,'ankle_reach_residual':leg_res,'wrist_reach_residual':arm_res}

def rgb(h):
    def lin(a):return a/12.92 if a<=.04045 else ((a+.055)/1.055)**2.4
    return tuple(lin(int(h[i:i+2],16)/255.) for i in (0,2,4))+(1.,)

def studio(sc):
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
    r=sc.render;r.engine='CYCLES';r.image_settings.file_format='PNG';r.image_settings.color_mode='RGB'
    r.film_transparent=False;r.resolution_percentage=100
    sc.cycles.use_denoising=False;sc.cycles.max_bounces=4;sc.cycles.diffuse_bounces=2;sc.cycles.transparent_max_bounces=16
    sc.cycles.adaptive_threshold=.032
    for ob in sc.objects:
        if ob.type=='LIGHT':ob.hide_render=True
    w=sc.world or bpy.data.worlds.new('Pearl studio world');sc.world=w;w.use_nodes=True
    wb=w.node_tree.nodes.get('Background')
    wb.inputs['Color'].default_value=(.55,.62,.74,1.)
    wb.inputs['Strength'].default_value=.485
    def lamp(name,xyz,watts,size,color,look=(0,0,.90),shape='DISK',size_y=None):
        d=bpy.data.lights.new(name,'AREA');d.energy=watts;d.shape=shape;d.size=size;d.color=color
        if size_y and shape=='RECTANGLE':d.size_y=size_y
        o=bpy.data.objects.new(name,d);sc.collection.objects.link(o)
        o.location=xyz;o.rotation_euler=(V(look)-o.location).to_track_quat('-Z','Y').to_euler()
    lamp('Porcelain key · large rectangular softbox',(-1.4,-2.8,3.10),124,2.05,(1.,.962,.925),shape='RECTANGLE',size_y=2.55)
    lamp('Cream eye light',(1.35,-2.5,1.86),53,1.45,(.93,.961,1.0))
    lamp('Silver-lavender strip',(1.35,1.22,2.42),101,1.02,(.90,.94,1.),shape='RECTANGLE',size_y=2.60)
    lamp('Quiet warm bounce',(-.42,.88,2.7),49,2.0,(1.,.97,.94))
    d=V((-.38,-.72,.58)).normalized()
    for m in bpy.data.materials:
        if not m.node_tree:continue
        for node in m.node_tree.nodes:
            if 'key direction' in (node.name+' '+node.label).lower() and getattr(node,'operation','')=='DOT_PRODUCT':
                node.inputs[1].default_value=d
    plane=bpy.data.meshes.new('Seamless studio floor')
    plane.from_pydata([(-120,-120,-.0015),(120,-120,-.0015),(120,120,-.0015),(-120,120,-.0015)],[],[(0,1,2,3)])
    plane.update();floor=bpy.data.objects.new('Pearl seamless with real contact shadows',plane);sc.collection.objects.link(floor)
    mat=bpy.data.materials.new('Pearl-to-ice clean paper');mat.use_nodes=True
    n=mat.node_tree.nodes;l=mat.node_tree.links.new;n.clear()
    tex=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l(tex.outputs['Window'],sep.inputs[0])
    paper=n.new('ShaderNodeMixRGB');paper.inputs[1].default_value=rgb('E9EDF5');paper.inputs[2].default_value=rgb('F1F2F6');l(sep.outputs['Y'],paper.inputs[0])
    glow=n.new('ShaderNodeEmission');glow.inputs['Strength'].default_value=1.;l(paper.outputs[0],glow.inputs['Color'])
    diff=n.new('ShaderNodeBsdfDiffuse');diff.inputs['Color'].default_value=rgb('B5BBD1');diff.inputs['Roughness'].default_value=.69
    pos=n.new('ShaderNodeNewGeometry')
    delta=n.new('ShaderNodeVectorMath');delta.operation='SUBTRACT';l(pos.outputs['Position'],delta.inputs[0]);delta.inputs[1].default_value=(.015,.04,-.001)
    shaped=n.new('ShaderNodeVectorMath');shaped.operation='MULTIPLY';l(delta.outputs['Vector'],shaped.inputs[0]);shaped.inputs[1].default_value=(3.04,3.27,0.)
    dl=n.new('ShaderNodeVectorMath');dl.operation='LENGTH';l(shaped.outputs['Vector'],dl.inputs[0])
    shadow=n.new('ShaderNodeMapRange');shadow.clamp=True;shadow.interpolation_type='SMOOTHERSTEP'
    shadow.inputs['From Min'].default_value=.49;shadow.inputs['From Max'].default_value=1.42
    shadow.inputs['To Min'].default_value=.29;shadow.inputs['To Max'].default_value=0.;l(dl.outputs['Value'],shadow.inputs['Value'])
    mix=n.new('ShaderNodeMixShader');l(shadow.outputs['Result'],mix.inputs[0]);l(glow.outputs[0],mix.inputs[1]);l(diff.outputs[0],mix.inputs[2])
    eye=n.new('ShaderNodeLightPath');seam=n.new('ShaderNodeMixShader');l(eye.outputs['Is Camera Ray'],seam.inputs[0])
    l(diff.outputs[0],seam.inputs[1]);l(mix.outputs[0],seam.inputs[2])
    mo=n.new('ShaderNodeOutputMaterial');l(seam.outputs[0],mo.inputs['Surface'])
    floor.data.materials.append(mat)
    return floor

def camera(sc,az,elev,target,scale):
    if sc.camera and sc.camera.name=='Suzu hero · editorial lens':
        o=sc.camera;d=o.data
    else:
        d=bpy.data.cameras.new('Suzu hero · editorial lens');o=bpy.data.objects.new(d.name,d);sc.collection.objects.link(o);sc.camera=o
    d.type='ORTHO';d.ortho_scale=scale;d.clip_start=.02;d.clip_end=320
    az,elev=[a*D2R for a in (az,elev)];t=V(target)
    dir=V((math.sin(az)*math.cos(elev),-math.cos(az)*math.cos(elev),math.sin(elev)))
    o.location=t+dir*4.05;o.rotation_euler=(t-o.location).to_track_quat('-Z','Y').to_euler()
    return o

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('out',type=Path);ap.add_argument('--variant',choices=('portrait','quiet','clip'),default='portrait')
    ap.add_argument('--size',type=int,nargs=2,default=(1800,2400));ap.add_argument('--az',type=float,default=10.5)
    ap.add_argument('--elev',type=float,default=6.5);ap.add_argument('--samples',type=int,default=36)
    ap.add_argument('--scale',type=float,default=1.813);ap.add_argument('--frame-center',type=float,nargs=3,default=(.008,-.016,.841))
    ap.add_argument('--note',type=Path)
    a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
    a.out.parent.mkdir(parents=True,exist_ok=True)
    sc=bpy.context.scene;report=freeze_hero_pose(sc,a.variant);studio(sc)
    camera(sc,a.az,a.elev,a.frame_center,a.scale)
    r=sc.render;r.resolution_x,r.resolution_y=a.size;sc.cycles.samples=a.samples
    r.filepath=str(a.out.resolve());bpy.ops.render.render(write_still=True)
    report.update({'source':Path(bpy.data.filepath).name,'camera':(a.az,a.elev,a.scale),'render_size':tuple(a.size),'samples':a.samples})
    if a.note:a.note.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':main()

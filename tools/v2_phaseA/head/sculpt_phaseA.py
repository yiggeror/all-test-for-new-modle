"""Suzu Phase A: refine imported VRoid geometry and carry its original expression poses."""
from pathlib import Path
from hashlib import sha256
import json, sys
import bpy
import numpy as np
from mathutils.kdtree import KDTree


def smooth(lo, hi, x):
    t=np.clip((x-lo)/(hi-lo),0.0,1.0);return t*t*(3.-2.*t)


def band(x,lo,hi,soft):return smooth(lo-soft,lo,x)*(1.-smooth(hi,hi+soft,x))


def bulb(x,c,w):return np.exp(-((x-c)/w)**2)


def coords(collection):
    out=np.empty(3*len(collection),dtype=np.float32);collection.foreach_get('co',out);return out.reshape((-1,3))


def semantic_indices(face,contains):
    included={i for i,m in enumerate(face.data.materials) if m and contains in m.name.lower()}
    return np.unique([int(i) for p in face.data.polygons if p.material_index in included for i in p.vertices])


def native_signature(face):
    def dig(a):return sha256(a.tobytes()).hexdigest()
    me=face.data;l=np.empty(len(me.loops),dtype=np.int32);me.loops.foreach_get('vertex_index',l)
    v=np.empty(len(me.polygons),dtype=np.int32);me.polygons.foreach_get('material_index',v)
    u=np.empty(2*len(me.uv_layers[0].data),dtype=np.float32);me.uv_layers[0].data.foreach_get('uv',u)
    weights=[(int(k.index),[(int(g.group),float(g.weight)) for g in k.groups]) for k in me.vertices]
    return {'loops':dig(l),'material_faces':dig(v),'UVMap':dig(u),'skin_weights':sha256(json.dumps(weights).encode()).hexdigest(),
      'rig':face.parent.name if face.parent else None,'bone_names':[b.name for b in face.parent.data.bones] if face.parent and face.parent.type=='ARMATURE' else [],
      'key_names':[x.name for x in me.shape_keys.key_blocks]}


def seam_envelope(face,body,p,bottom):
    if body is None:return np.ones(len(p))
    w=face.matrix_world.inverted()@body.matrix_world;sk={i for i,m in enumerate(body.data.materials) if m and 'body_00_skin' in m.name.lower()}
    ids=set(i for f in body.data.polygons if f.material_index in sk for i in f.vertices)
    cluster=[w@body.data.vertices[i].co for i in ids];cluster=[q for q in cluster if q.z>bottom-.024]
    if not cluster:return np.ones(len(p))
    tree=KDTree(len(cluster))
    for i,q in enumerate(cluster):tree.insert(q,i)
    tree.balance();d=np.array([tree.find(tuple(q))[2] for q in p]);return smooth(.00035,.0045,d)


def sculpt(face,body=None,amount=1.0):
    """Return measured real mesh/UV/key invariants; apply before the rig's global stature fit."""
    me=face.data;keys=me.shape_keys.key_blocks;old=[coords(k.data) for k in keys];p=old[0].astype('float64');sig=native_signature(face)
    ir=semantic_indices(face,'eyeiris');skin=semantic_indices(face,'face_00_skin');white=semantic_indices(face,'eyewhite')
    if not len(skin) or not len(ir) or not len(white):raise ValueError('The selected source has no native face/iris/white materials')
    # The shapes below are local sculpt handles traced on the chosen mesh, not a constructed face.
    x0=(p[skin,0].min()+p[skin,0].max())*.5;z0,z1=np.min(p[skin,2]),np.max(p[skin,2]);ht=z1-z0
    fwd=-1. if np.mean(p[ir,1])<0 else 1.;cY=fwd*float(np.mean(p[ir,1]));k=ht/(1.585525-1.352182)
    x=(p[:,0]-x0)/k; a=np.abs(x); sign=np.sign(x)
    z=(p[:,2]-z0)/k+1.352182; y=(-fwd*p[:,1]+cY-.055438)/k
    # y is negative toward the camera on both VRoid axis conventions.
    facefront=1.-smooth(-.041,.003,y)
    ear=smooth(.080,.0914,a)*smooth(.000,.024,y)*band(z,1.406,1.468,.011)
    lower=band(z,1.368,1.412,.019)*facefront*smooth(.023,.060,a)*(1.-smooth(.074,.098,a))
    orbit=band(a,.0180,.0696,.0118)*band(z,1.4214,1.4655,.0122)*(1.-smooth(-.030,.005,y))
    wing=smooth(.047,.069,a)*band(z,1.443,1.460,.010)*(1.-smooth(-.030,-.017,y))
    cheek_a=bulb(a,.049,.025)*bulb(z,1.419,.025)*facefront
    cheek_up=bulb(a,.063,.025)*bulb(z,1.411,.024)*facefront
    under=(1.-smooth(.029,.062,a))*band(z,1.3524,1.368,.013)*bulb(y,-.030,.020)
    nose=bulb(a,0.,.014)*bulb(z,1.4076,.010)*(1.-smooth(-.073,-.060,y))
    nose_roll=bulb(a,.019,.011)*bulb(z,1.405,.018)*facefront
    chin_round=bulb(z,1.361,.011)*bulb(a,.017,.012)*bulb(y,-.056,.015)
    lip=band(a,0,.023,.012)*band(y,-.088,-.046,.014)*bulb(z,1.3885,.0135)
    corner=bulb(a,.0186,.0072)*lip
    dx=sign*((-.252*(a-.0890)-.00245)*ear-.00328*lower+.00136*chin_round)
    dy=(-.18*(y-.0408)+.00375+.080*(a-.0890))*ear
    dy+=-.00255*cheek_a-.00110*cheek_up+.00067*orbit+.00174*nose-.00107*nose_roll+.00132*under+.00063*lip
    dz=(-.18*(z-1.4378)-.00170)*ear+.104*(z-1.44372)*orbit+.00092*wing+.00068*cheek_up+.00214*under+.00158*nose-.00064*lip+.00148*corner
    eye_cards=np.union1d(ir,semantic_indices(face,'eyehighlight'))
    # Both lens layers follow the same curved iris-centred transformation.
    dz[eye_cards]+=.0990*(z[eye_cards]-1.44325)+.00178
    dx[eye_cards]+=(.0890*(a[eye_cards]-.0413375)-.00097)*sign[eye_cards]
    hold=seam_envelope(face,body,p,z0)
    d=np.stack((dx,-fwd*dy,dz),axis=-1)*(hold*float(amount)*k)[:,None]
    # A common local affine change of coordinates carries the eyelid arcs and
    # their native closing shapes together. Every nonocular delta is unchanged.
    key_scale=np.ones((len(p),3),dtype=np.float64)
    key_scale[:,2]+=.104*orbit*hold*float(amount)
    key_scale[eye_cards,0]+=.0890*hold[eye_cards]*float(amount)
    key_scale[eye_cards,2]+=.0990*hold[eye_cards]*float(amount)
    for block,before in zip(keys,old):
        target=(p+d)+(before.astype('float64')-p)*key_scale
        block.data.foreach_set('co',target.astype('float32').ravel())
    me.vertices.foreach_set('co',(p+d).astype('float32').ravel());me.update();bpy.context.view_layer.update()
    delta_err=0.;nonocular_error=0.;ocular_change=0.;persistent=np.all(key_scale==1.,axis=1)
    for block,before in zip(keys,old):
        observed=coords(block.data)-coords(keys[0].data);target=(before-old[0])
        delta_err=max(delta_err,float(np.max(np.abs(observed-target*key_scale))))
        nonocular_error=max(nonocular_error,float(np.max(np.abs(observed[persistent]-target[persistent]))))
        ocular_change=max(ocular_change,float(np.max(np.abs(observed[~persistent]-target[~persistent]))))
    after=coords(keys[0].data);sig1=native_signature(face)
    if sig1!=sig:raise AssertionError('The edit changed UV layout, materials, connectivity, weights or native key identities')
    if delta_err>7e-7:raise AssertionError(('Original morph deltas changed',delta_err))
    eye_z=[];iris_z=[]
    for s in (-1,1):
        ix=white[np.sign(p[white,0]-x0)==s];eye_z.append((s,float(np.ptp(after[ix,2])/np.ptp(p[ix,2]))))
        ii=ir[np.sign(p[ir,0]-x0)==s];iris_z.append((s,float(np.ptp(after[ii,2])/np.ptp(p[ii,2]))))
    ears=[]
    for s in (-1,1):
        ix=np.where((ear>.96)&(sign==s))[0];ears.append({'vertices':len(ix),'Z_span_after_before':float(np.ptp(after[ix,2])/np.ptp(p[ix,2])) if len(ix)>2 else None,
          'Y_mean_toward_back_mm':float(np.mean((-fwd)*(after[ix,1]-p[ix,1]))*1000.) if len(ix) else None})
    return {'model':face.name,'vertices':len(p),'triangles':len(me.polygons),'morph_targets':len(keys)-1,'morph_coordinate_remap_error_m':delta_err,'morph_nonocular_max_error_m':nonocular_error,'ocular_delta_change_max_m':ocular_change,'topology_and_UV':sig1,'front_direction_Y':fwd,
      'eye_white_Z_after_before':eye_z,'iris_Z_after_before':iris_z,'ear_core_measurements':ears,'sculpted_vertices':int(np.sum(np.linalg.norm(d,axis=1)>.00001)),'largest_motion_m':float(np.max(np.linalg.norm(d,axis=1))),
      'body_seam_vertices_pinned':int(np.sum(hold<.01)),'raw_before_bounds':[p.min(0).tolist(),p.max(0).tolist()],'raw_after_bounds':[after.min(0).tolist(),after.max(0).tolist()]}


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:];out=Path(args[0]).resolve();out.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene;face=next(o for o in scene.objects if o.type=='MESH' and o.data.shape_keys and 'face' in o.name.lower());body=scene.objects.get('Body')
    stats=sculpt(face,body,float(args[1]) if len(args)>1 else 1.0)
    if body is not None and len(body.data.vertices)==7977:
        sys.path.insert(0,str(Path(__file__).resolve().parent));from seal_native_scalp import seal_scalp
        stats['scalp_seal']=seal_scalp(body)
    sys.path.insert(0,str(Path(__file__).resolve().parent));from expressions_phaseA import write_preset_json
    write_preset_json(face,out/'expression_presets.json')
    (out/'sculpt_qc.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False))
    print('SCULPT VERIFIED',stats['vertices'],stats['triangles'],stats['morph_targets'],stats['morph_coordinate_remap_error_m'],stats['eye_white_Z_after_before'],stats['ear_core_measurements'])
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'head_sculpt.blend'),compress=True)

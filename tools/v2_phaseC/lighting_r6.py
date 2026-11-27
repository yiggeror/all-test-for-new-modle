"""Add a peach skin floor and restrained rim highlights for top/back lighting."""
from pathlib import Path
from mathutils import Vector
import bpy,sys

GROUP='Suzu R6 • key direction'
def srgb(hex):
    nums=[int(hex[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in nums)
def group():
    g=bpy.data.node_groups.get(GROUP)
    if g:return g
    g=bpy.data.node_groups.new(GROUP,'ShaderNodeTree')
    g.interface.new_socket(name='Key direction',in_out='OUTPUT',socket_type='NodeSocketVector')
    k=g.nodes.new('ShaderNodeCombineXYZ');k.name='World key'
    out=g.nodes.new('NodeGroupOutput')
    g.links.new(k.outputs[0],out.inputs[0])
    set_key(Vector((-.45,-.74,.54)).normalized())
    return g
def set_key(v):
    g=bpy.data.node_groups.get(GROUP)
    if g:
        k=g.nodes['World key']
        for i,val in enumerate(v):k.inputs[i].default_value=val

def graph(m):
    t=m.node_tree
    def mk(kind,label,xy):
        x=t.nodes.new(kind);x.label='R6 · '+label;x.location=xy
        return x
    def connect(value,socket):
        if isinstance(value,(float,int,tuple)):socket.default_value=value
        else:t.links.new(value,socket)
    def scalar(op,label,a,b,xy):
        z=mk('ShaderNodeMath',label,xy);z.operation=op;connect(a,z.inputs[0])
        if b is not None:connect(b,z.inputs[1])
        return z.outputs[0]
    def smooth(label,a,f0,f1,t0,t1,xy):
        n=mk('ShaderNodeMapRange',label,xy);n.interpolation_type='SMOOTHERSTEP';n.clamp=True
        connect(a,n.inputs['Value'])
        for s,v in [('From Min',f0),('From Max',f1),('To Min',t0),('To Max',t1)]:n.inputs[s].default_value=v
        return n.outputs['Result']
    def geom(key,xy):
        return mk('ShaderNodeNewGeometry',key,xy)
    def split(a,n,xy):
        y=mk('ShaderNodeSeparateXYZ','Separate direction or height',xy);connect(a,y.inputs[0]);return y.outputs[n]
    def dot(label,a,b,xy):
        n=mk('ShaderNodeVectorMath',label,xy);n.operation='DOT_PRODUCT';connect(a,n.inputs[0]);connect(b,n.inputs[1]);return n.outputs['Value']
    def mix(label,f,a,b,xy):
        n=mk('ShaderNodeMixRGB',label,xy);connect(f,n.inputs[0]);connect(a,n.inputs[1]);connect(b,n.inputs[2]);return n.outputs[0]
    def key(xy):
        n=mk('ShaderNodeGroup','Common studio key direction',xy);n.node_tree=group();return n.outputs[0]
    return mk,connect,scalar,smooth,geom,split,dot,mix,key

def apply():
    stats={'skin':0,'rim':0,'portable':0}
    used={s.material for o in bpy.context.scene.objects if o.type=='MESH' for s in o.material_slots if s.material}
    for m in sorted(bpy.data.materials,key=lambda u:u.name):
        if not m.use_nodes or m.get('suzu_r6_light'):continue
        role=m.get('suzu_phase_a_role');style=m.get('suzu_style')
        if role in {'body','skin','scalp'} and style=='Export':
            # glTF viewers get a low authored diffuse fill even without environment lighting.
            pb=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
            base=pb.inputs['Base Color'].links
            if base and not pb.inputs['Emission Color'].is_linked:
                m.node_tree.links.new(base[0].from_socket,pb.inputs['Emission Color'])
                pb.inputs['Emission Strength'].default_value=.16
                stats['portable']+=1
            m['suzu_r6_light']=True
            continue
        if m not in used:continue
        skin=role in {'body','skin','scalp'} and style not in {'Export','Clay'}
        hair=bool(m.get('suzu_hair_role')) and bool(m.get('suzu_hair_style'))
        shoulder=bool(m.get('suzu_wardrobe_npr')) and ('jacket' in m.name.lower() or 'sleeve' in m.name.lower()) and not any(x in m.name.lower() for x in ('gold','trim','binding'))
        if not (skin or hair or shoulder):continue
        t=m.node_tree
        mk,connect,scalar,smooth,geom,split,dot,mix,key=graph(m)
        K=key((-1030,1110))
        back=smooth('Ambient lift enters only with top/back key',split(K,'Y',(-825,1110)),-.56,-.13,0.,1.,(-600,1110))
        if skin:
            tint=next(n for n in t.nodes if n.label=='Tint the original 2K portrait paint')
            old=tint.inputs[2].links[0].from_socket
            peach='E8C3B4' if role=='skin' else 'E6BEAF'
            coeff=tuple(a/b for a,b in zip(srgb(peach),srgb('FDECDA')))+(1.,)
            floor=mk('ShaderNodeMixRGB','Per-channel warm skin floor',(-183,1010));floor.blend_type='LIGHTEN'
            connect(1.,floor.inputs[0]);connect(old,floor.inputs[1]);connect(coeff,floor.inputs[2])
            connect(mix('Keep front exposure exactly as before',back,old,floor.outputs[0],(59,914)),tint.inputs[2])
            stats['skin']+=1
        else:
            em=next((n for n in t.nodes if n.type=='EMISSION' and n.inputs['Color'].is_linked),None)
            if em is None:continue
            prior=em.inputs['Color'].links[0].from_socket
            g=geom('Normal and forward grazing angle',(-1004,710))
            cos=dot('View grazing angle',g.outputs['Normal'],g.outputs['Incoming'],(-764,625))
            grazing=smooth('Fine high light at silhouette',scalar('ABSOLUTE','Unsigned view angle',cos,None,(-580,625)),.027,.28,1.,0.,(-395,628))
            N=dot('Direct rim alignment',g.outputs['Normal'],K,(-765,355))
            key_side=smooth('Only light-facing edges',N,-.10,.58,.08,1.,(-520,350))
            f=scalar('MULTIPLY','Back light at this edge',back,grazing,(-190,695))
            f=scalar('MULTIPLY','Rim faces the key',f,key_side,(-22,510))
            if shoulder:
                z=split(g.outputs['Position'],'Z',(-756,116))
                z=smooth('Limit the navy accent to upper seams',z,1.14,1.32,0.,1.,(-530,123))
                f=scalar('MULTIPLY','Shoulder area only',f,z,(141,390))
            f=scalar('MULTIPLY','Keep halo narrow and restrained',f,.33 if hair else .26,(310,653))
            connect(mix('Clear icy hair rim' if hair else 'Silver-blue seam reflection',f,prior,srgb('F4F4FF' if hair else '8D9DC4')+(1.,),(513,640)),em.inputs['Color'])
            stats['rim']+=1
        m['suzu_r6_light']=True
    assert stats['skin']>=2 and stats['rim']>=4,stats
    print('Round 6 lighting:',stats,flush=True)
    return stats

if __name__=='__main__':
    out=Path(sys.argv[sys.argv.index('--')+1]);apply()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()),compress=True)

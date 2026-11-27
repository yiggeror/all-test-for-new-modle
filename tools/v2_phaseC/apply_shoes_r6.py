"""Round 6 material-only, camera-responsive patent-leather finish for the locked Mary Janes."""
from __future__ import annotations
import argparse
from pathlib import Path
from math import exp
import struct
import tempfile
import zlib
import sys
from functools import lru_cache
import bpy

MARK='suzu_shoe_r6'
TITLE='Suzu C · R6 shoe'
UV='Tailor pattern'
BASE='303955'
GLAZE='9CAFD9'
FLASH='C4D7F4'

TONES={
    'upper': ('303955','202740','626E98','1E2945',.37),
    'edge': ('53627C','333C5A','7F8CAD','2A3552',.26),
    'stitch': ('3B4966','293653','627190','27334E',.24),
    'strap': ('38455F','242C48','727F9F','252B49',.37),
    'welt': ('4A5873','303B55','687997','27304C',.22),
    'outsole': ('1A2137','141A2C','3C4B65','151B2C',.13),
    'stack': ('273249','1D2539','435068','1C2237',.16),
}
POLISH={
    'upper':(.29,.63,.21,.46,0.24),
    'edge':(.40,.24,.29,.37,0.22),
    'stitch':(.49,.11,.37,.32,0.20),
    'strap':(.33,.43,.235,.41,0.22),
    'welt':(.50,.08,.34,.31,0.24),
    'outsole':(.64,.0,.45,.29,0.18),
    'stack':(.54,.05,.41,.28,0.20),
}
KEY='Key direction • world space'

def sat(x):return min(1.,max(0.,x))

def linear(x):return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4

def display(x):return x*12.92 if x<=.0031308 else 1.055*x**(1./2.4)-.055

def rgba(h):
    return tuple(linear(int(h[i:i+2],16)/255.) for i in (0,2,4))+(1.,)

def smooth(a,b,x):
    y=sat((x-a)/(b-a));return y*y*(3.-2.*y)

def glaze_strength(u,v,side):
    """Loop-periodic softly feathered reflection posed over the curved toe vamp."""
    q=side*(u if u<.5 else u-1.)
    r=(q+.023)/.076
    window=max(0.,1.-r*r)
    center=.349+.067*r+.078*r*r
    env=window**.72
    width=.040+.014*window
    core=exp(-((v-center)/width)**2*1.37)*env
    penumbra=exp(-((v-center-.008)/(.083+.012*window))**2*1.62)*env
    tailx=(q+.100)/.036
    tailenv=max(0.,1.-tailx*tailx)**1.02
    tail=exp(-((v-(.534-.059*tailx))/.078)**2*1.58)*tailenv
    return min(.67, .462*core+.106*penumbra+.096*tail)

def chunk(key,data):
    return struct.pack('>I',len(data))+key+data+struct.pack('>I',zlib.crc32(key+data))

@lru_cache(maxsize=8)
def bitmap(side,mode,W=512,H=384):
    aa=rgba(BASE);bb=rgba(GLAZE)
    rows=[]
    for y in range(H):
        v=1.-(y+.5)/H;row=bytearray()
        if mode=='mask':
            for x in range(W):
                w=glaze_strength((x+.5)/W,v,side)
                row.append(round(255*w))
        else:
            for x in range(W):
                w=glaze_strength((x+.5)/W,v,side)*.91
                row.extend(round(255*sat(display(a+(b-a)*w))) for a,b in zip(aa[:3],bb[:3]))
        rows.append(b'\x01'+bytes((k if i<(1 if mode=='mask' else 3) else k-row[i-(1 if mode=='mask' else 3)])%256 for i,k in enumerate(row)))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',W,H,8,0 if mode=='mask' else 2,0,0,0))
          +chunk(b'IDAT',zlib.compress(b''.join(rows),9))+chunk(b'IEND',b''))

def embedded(side,mode):
    tag='L' if side>0 else 'R';name=f'{TITLE} · {tag} {mode}.png'
    im=bpy.data.images.get(name)
    if im:return im
    with tempfile.TemporaryDirectory(prefix='suzu-shoe-') as folder:
        p=Path(folder)/name;p.write_bytes(bitmap(side,mode))
        im=bpy.data.images.load(str(p),check_existing=False)
        im.name=name;im.colorspace_settings.name='Non-Color' if mode=='mask' else 'sRGB'
        im.pack()
        im.filepath='//'+name
    return im

def tex(nodes,links,im,name,loc):
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map=UV;uv.name=uv.label='Original shoemaking UV';uv.location=(loc[0]-207,loc[1])
    n=nodes.new('ShaderNodeTexImage');n.image=im;n.name=n.label=name;n.location=loc;n.extension='REPEAT'
    n.interpolation='Linear';links(uv.outputs['UV'],n.inputs['Vector']);return n

def pbr(name,key,side):
    m=bpy.data.materials.new(name+' · portable')
    m.use_nodes=True;m.use_fake_user=True;m[MARK]='portable';m.diffuse_color=rgba(TONES[key][0])
    nodes=m.node_tree.nodes;link=m.node_tree.links.new
    q=nodes.get('Principled BSDF')
    rough,coat,coat_rough,spec,ambient=POLISH[key];base=rgba(TONES[key][0])
    q.inputs['Roughness'].default_value=rough
    q.inputs['Coat Weight'].default_value=coat
    q.inputs['Coat Roughness'].default_value=coat_rough
    q.inputs['Specular IOR Level'].default_value=spec
    q.inputs['Base Color'].default_value=base
    q.inputs['Emission Color'].default_value=base
    q.inputs['Emission Strength'].default_value=ambient
    if key=='upper':
        tile=tex(nodes,link,embedded(side,'color'),'Painted reflection undertone',(-290,100))
        link(tile.outputs['Color'],q.inputs['Base Color'])
        link(tile.outputs['Color'],q.inputs['Emission Color'])
    return m

def apply_tones(m,key):
    n=m.node_tree.nodes
    nb=n['Two clear navy/indigo luma states'];r=n['Metal-free silk rim'];d=n['Indigo silhouette, never black']
    base,shadow,rid,dark,power=TONES[key]
    nb.inputs[1].default_value=rgba(shadow)
    nb.inputs[2].default_value=rgba(base)
    r.inputs[2].default_value=rgba(rid)
    d.inputs[2].default_value=rgba(dark)
    n['Muted colored grazing reflection'].inputs['To Min'].default_value=power
    m.diffuse_color=rgba(base)

def add_shine(m,side):
    n=m.node_tree.nodes;L=m.node_tree.links.new
    old=n['Indigo silhouette, never black'];sh=n['Clean NPR color output'];geo=n['Clean surface basis']
    sh.location=(1290,160)
    n['Surface'].location=(1490,160)
    opt=tex(n,L,embedded(side,'mask'),'Vamp reflection ribbon', (330,490))
    def add(kind,name,pos):
        x=n.new(kind);x.name=x.label=name;x.location=pos;return x
    def mix(name,pos,a,b,factor):
        x=add('ShaderNodeMixRGB',name,pos); L(a,x.inputs[1]); x.inputs[2].default_value=b;L(factor,x.inputs[0]);return x.outputs[0]
    satin=mix('Shoe Specular Highlight · clear vamp ribbon',(776,214),old.outputs[0],rgba(GLAZE),opt.outputs['Color'])
    eye=add('ShaderNodeVectorMath','Half vector · facing the reflected softbox', (312,-494));eye.operation='ADD'
    eye.inputs[1].default_value=n[KEY].inputs[1].default_value
    norm=add('ShaderNodeVectorMath','Normalize the half vector',(536,-495));norm.operation='NORMALIZE'
    fac=add('ShaderNodeVectorMath','Glancing dielectric angle',(725,-341));fac.operation='DOT_PRODUCT'
    L(geo.outputs['Incoming'],eye.inputs[0]);L(eye.outputs['Vector'],norm.inputs[0])
    L(norm.outputs['Vector'],fac.inputs[1]);L(geo.outputs['Normal'],fac.inputs[0])
    mp=add('ShaderNodeMapRange','Specular edge · soft falloff without render noise',(919,-251))
    mp.interpolation_type='SMOOTHERSTEP';mp.clamp=True
    mp.inputs['From Min'].default_value=.938;mp.inputs['From Max'].default_value=.993
    mp.inputs['To Min'].default_value=0.;mp.inputs['To Max'].default_value=.083
    L(fac.outputs['Value'],mp.inputs['Value'])
    duty=add('ShaderNodeMapRange','Studio key softly gates the reflective coat',(880,-466))
    duty.clamp=True;duty.inputs['From Min'].default_value=-.40;duty.inputs['From Max'].default_value=.63
    duty.inputs['To Min'].default_value=.32;duty.inputs['To Max'].default_value=1.
    L(n[KEY].outputs['Value'],duty.inputs['Value'])
    f=add('ShaderNodeMath','Quiet view-responsive lobe',(1075,-264));f.operation='MULTIPLY'
    L(duty.outputs['Result'],f.inputs[0]);L(mp.outputs['Result'],f.inputs[1])
    spec=mix('Clear top coat · small responsive flash',(1120,160),satin,rgba(FLASH),f.outputs[0])
    L(spec,sh.inputs['Color'])

def alloy(label):
    name=TITLE+' · '+label
    prior=bpy.data.materials.get(name)
    if prior:return prior
    m=bpy.data.materials.new(name);m.use_nodes=True
    q=m.node_tree.nodes.get('Principled BSDF')
    face=label=='satin cut buckle'
    c=rgba('D8B780' if face else 'AD8853')
    m.diffuse_color=c
    q.inputs['Base Color'].default_value=c;q.inputs['Metallic'].default_value=.80 if face else .68
    q.inputs['Roughness'].default_value=.255 if face else .33
    q.inputs['Specular IOR Level'].default_value=.48
    q.inputs['Emission Color'].default_value=c;q.inputs['Emission Strength'].default_value=.19 if face else .115
    # The same single Principled surface exports without a conversion.
    m[MARK]=True;m['suzu_wardrobe_npr']=True;m['suzu_glb_material']=m.name
    return m

def shape(role,slot,m):
    if role=='shoe-upper':return ('upper' if slot==0 else 'edge' if slot==1 else 'welt')
    if role=='shoe-sole':return ('outsole','welt','stack')[slot]
    if role=='heel':return 'outsole' if slot==0 else 'stack'
    if role=='shoe-strap':return 'strap' if slot==0 else 'edge'
    if role=='shoe-rim':return 'edge'
    if role=='shoe-stitch':return 'stitch'
    raise ValueError((role,slot,m.name))

def finish(previous,key,side):
    tag='Left' if side>0 else 'Right'
    name=f'{TITLE} · {key}'+(f' ({tag})' if key=='upper' else '')
    m=bpy.data.materials.get(name)
    if m:return m
    assert previous.node_tree.nodes.get('Two clear navy/indigo luma states'),('Unexpected upstream shoe shader',previous.name)
    m=previous.copy();m.name=name
    apply_tones(m,key)
    if key=='upper':add_shine(m,side)
    m['suzu_glb_material']=pbr(name,key,side).name;m[MARK]=True;m['suzu_wardrobe_npr']=True
    return m

def apply_shoes(scene=None):
    scene=scene or bpy.context.scene
    col=bpy.data.collections['SUZU_PHASE_C_LOWER']
    shoe=[o for o in col.all_objects if o.get('suzu_lower_role','').startswith(('shoe','heel')) and o.type=='MESH']
    assert len(shoe)==16
    result=[]
    for o in shoe:
        role=o['suzu_lower_role']; side=1 if '· Left ' in o.name else -1
        if o.material_slots[0].material.get(MARK):continue
        for i,slot in enumerate(o.material_slots):
            new=(alloy('satin cut buckle' if role=='shoe-buckle' else 'satin buckle pin')
                 if role.startswith('shoe-buckle') else finish(slot.material,shape(role,i,slot.material),side))
            slot.material=new
            result.append((o.name,i,new.name,new['suzu_glb_material']))
    if result:
        assert len(result)==28,len(result)
    return result

def test_glb(path):
    """Reimportable actual GLB shoe and stocking specimen, not the production model."""
    sc=bpy.context.scene;sc.frame_set(1)
    D=bpy.context.evaluated_depsgraph_get()
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.collections['SUZU_PHASE_C_LOWER'].all_objects:
        role=o.get('suzu_lower_role','')
        if not role.startswith(('shoe','heel','sock')):continue
        e=o.evaluated_get(D)
        mesh=bpy.data.meshes.new_from_object(e,preserve_all_data_layers=True,depsgraph=D)
        x=bpy.data.objects.new(o.name+' · specimen',mesh);sc.collection.objects.link(x);x.matrix_world=e.matrix_world
        for slot in x.material_slots:
            n=slot.material.get('suzu_glb_material') if slot.material else None
            if n:slot.material=bpy.data.materials[n]
        x.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path.resolve()),export_format='GLB',use_selection=True,
            export_animations=False,export_skins=False,export_cameras=False,export_lights=False)

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('out',type=Path)
    a.add_argument('--sample-glb',type=Path)
    p=a.parse_args(sys.argv[sys.argv.index('--')+1:])
    slots=apply_shoes()
    print('Material slots retuned:',len(slots))
    for item in slots: print(*item,sep=' / ')
    if p.out:
        p.out=p.out.resolve();p.out.parent.mkdir(parents=True,exist_ok=True)
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(p.out),compress=True)
    if p.sample_glb:test_glb(p.sample_glb)

if __name__=='__main__':main()

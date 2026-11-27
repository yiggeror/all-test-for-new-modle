"""Apply a consistent two-tone NPR wardrobe palette without touching Suzu's locked face or hair."""
from pathlib import Path
import sys,bpy
from mathutils import Vector

def rgba(h):
    h=h.lstrip('#')
    ts=[int(h[k:k+2],16)/255 for k in (0,2,4)]
    return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in ts)+(1.,)

def pick(m):
    n=m.name.lower()
    if any(word in n for word in ('gold','gilt','brass','bronze','star ornament','golden',
                'silver','jewel','gem','polished metal','thin chain','metal eyelet','sapphire','metal hardware','gold bell','button','button eye')):return None
    if any(word in n for word in ('ivory','blouse','oxford','collar','petticoat','welt ivory','cream','white')):
        return ('F2E4D9','BEB4C9','FFF1E2','9F97AC',.46)
    if any(word in n for word in ('shoe','leather','sole','calfskin','welt','heel','strap')):
        return ('303955','202741','666C94','21283E',.49)
    if any(word in n for word in ('fold','stitch','inseam','folded return','edge','underlap','binding')):
        return ('29324F','1A2140','626F9B','1D2442',.38)
    if any(word in n for word in ('stock','knit','cuff')):
        return ('2A334F','202644','5C6790','192139',.33)
    if any(word in n for word in ('ribbon','satin','bow','navy','twill','lapel','skirt','jacket','hem','cloth',
                          'waist','midnight','facing','sleeve','atlas','taffeta','lining')):
        return ('2F354F','202746','687294','20263F',.39)
    return None

def make(old):
    p=pick(old)
    if p is None:return old
    base,shadow,rim,dark,strength=p
    name='Suzu C · '+old.name+' · NPR'
    if name in bpy.data.materials:return bpy.data.materials[name]
    gname='Suzu C · '+old.name+' · Portable'
    gl=bpy.data.materials.new(gname);gl.use_nodes=True;gl.use_fake_user=True;gl.diffuse_color=rgba(base)
    q=gl.node_tree.nodes.get('Principled BSDF');q.inputs['Base Color'].default_value=rgba(base);q.inputs['Roughness'].default_value=.62
    q.inputs['Emission Color'].default_value=rgba(base);q.inputs['Emission Strength'].default_value=.22
    q.inputs['Specular IOR Level'].default_value=.22
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=rgba(base)
    m['suzu_glb_material']=gname
    m['suzu_wardrobe_npr']=True
    m.use_fake_user=True
    nd=m.node_tree.nodes;ll=m.node_tree.links.new;nd.clear()
    def Node(kind,label,x,y):
        n=nd.new(kind);n.name=label;n.label=label;n.location=(x,y);return n
    def Dot(label,x,y):
        n=Node('ShaderNodeVectorMath',label,x,y);n.operation='DOT_PRODUCT';return n
    def Blend(label,x,y,c1,c2,f=None):
        n=Node('ShaderNodeMixRGB',label,x,y);n.inputs[1].default_value=rgba(c1);n.inputs[2].default_value=rgba(c2)
        if f is not None:ll(f,n.inputs[0])
        return n
    def Glass(label,a,b,out0,out1,x,y,src):
        n=Node('ShaderNodeMapRange',label,x,y);n.interpolation_type='SMOOTHERSTEP';n.clamp=True
        n.inputs['From Min'].default_value=a;n.inputs['From Max'].default_value=b
        n.inputs['To Min'].default_value=out0;n.inputs['To Max'].default_value=out1
        ll(src,n.inputs['Value']);return n.outputs['Result']
    G=Node('ShaderNodeNewGeometry','Clean surface basis',-900,70)
    dp=Dot('Key direction • world space',-670,145);ll(G.outputs['Normal'],dp.inputs[0]);dp.inputs[1].default_value=Vector((-.45,-.74,.54)).normalized()
    coat=Blend('Two clear navy/indigo luma states',-72,178,shadow,base,
       Glass('Soft but distinct two-tone edge',.08,.26,0.,1.,-420,200,dp.outputs['Value']))
    view=Dot('View-facing line thickness',-670,-170);ll(G.outputs['Normal'],view.inputs[0]);ll(G.outputs['Incoming'],view.inputs[1])
    sign=Node('ShaderNodeMath','Cosine of view angle',-455,-172);sign.operation='ABSOLUTE';ll(view.outputs['Value'],sign.inputs[0])
    f=Glass('Muted colored grazing reflection',.06,.28,strength,0.,-245,-99,sign.outputs[0])
    high=Blend('Metal-free silk rim',130,135,base,rim,f);ll(coat.outputs[0],high.inputs[1])
    line=Glass('Controlled thin silhouette only',.006,.083,.76,0.,-235,-343,sign.outputs[0])
    slot=Blend('Indigo silhouette, never black',345,100,base,dark,line);ll(high.outputs[0],slot.inputs[1])
    em=Node('ShaderNodeEmission','Clean NPR color output',583,106);ll(slot.outputs[0],em.inputs[0])
    out=Node('ShaderNodeOutputMaterial','Surface',790,106);ll(em.outputs[0],out.inputs[0]);return m

def apply(scene=None):
    sc=scene or bpy.context.scene;done=[]
    for o in sc.objects:
        if o.type!='MESH' or o.get('suzu_stage_role')!='wardrobe':continue
        for s in o.material_slots:
            if not s.material or s.material.get('suzu_wardrobe_npr'):continue
            was=s.material;s.material=make(was)
            if s.material!=was:done.append((o.name,was.name,s.material.name))
    return done

if __name__=='__main__':
    a=sys.argv[sys.argv.index('--')+1:]
    rows=apply()
    assert rows,'No real wardrobe role in assembled scene'
    bpy.context.preferences.filepaths.save_version=0
    out=Path(a[0]).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
    print('Replaced wardrobe textile slots:',len(rows))

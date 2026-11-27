"""Apply Phase B hair-only materials to a root→tip UV strand collection.

Keep locked Phase A geometry/materials unchanged. Each role gets a Blender NPR
material, a portable glTF skin, and a neutral CLAY view material.
"""
from pathlib import Path
import bpy,os,math,zlib
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROLES=('crown','bang','temple','outer','middle','pony','fine','inner','ahoge')
SETUP={
  # upper, lower, toon shade mix, strand rim, UV band strength
  'crown': (.69,.00,.98,.27,.55),
  'bang':  (.66,.00,1.00,.28,.48),
  'temple':(.37,.42,.97,.25,.43),
  'outer': (.24,.70,.93,.30,.49),
  'middle':(.29,.68,.94,.31,.42),
  'pony':  (.36,.48,.94,.30,.45),
  'fine':  (.26,.31,.82,.11,.28),
  'inner': (.00,.058,.48,.20,.15),
  'ahoge': (.19,.00,.79,.13,.24),
}

def hexlinear(h):
 def c(ch):
  a=int(ch,16)/255
  return a/12.92 if a<=.04045 else ((a+.055)/1.055)**2.4
 return tuple(c(h[i:i+2]) for i in (0,2,4))+(1,)

def load(p,name,raw=False):
 p=Path(p)
 for x in bpy.data.images:
  if x.name==name and x.packed_file:return x
 if not p.exists():raise FileNotFoundError(str(p))
 im=bpy.data.images.load(str(p),check_existing=False);im.name=name
 im.colorspace_settings.name='Non-Color' if raw else 'sRGB'
 if not im.packed_file:im.pack()
 return im

def tex(n,im,xy,name):
 x=n.new('ShaderNodeTexImage');x.image=im;x.label=name;x.location=xy
 x.extension='EXTEND';x.interpolation='Linear'
 return x

def material(rol,version,albedo,ribbon,stations):
 name=f'Suzu B · {rol} · {version}'
 old=bpy.data.materials.get(name)
 key=f'{stations[0]:.4f}/{stations[1]:.4f}'
 if old and old.get('suzu_phaseB_palette')=='silver-ice-045' and old.get('suzu_halo_stations')==key:return old
 m=bpy.data.materials.new(name);m.use_nodes=True;m.use_fake_user=True
 m['suzu_phaseB_palette']='silver-ice-045';m['suzu_stage_role']='hair';m['suzu_halo_stations']=key
 m['suzu_hair_role']=rol;m['suzu_hair_style']=version
 m.diffuse_color=hexlinear('C7C5D7' if rol=='inner' else 'E4DEE8')
 nodes=m.node_tree.nodes;nodes.clear();L=m.node_tree.links.new
 def N(cls,lab,x,y):
  t=nodes.new(cls);t.label=lab;t.name=lab;t.location=(x,y);return t
 def s(x,socket):
  if isinstance(x,(float,int,tuple,list)):socket.default_value=x
  else:L(x,socket)
 def math(op,lab,a,b,xy):
  k=N('ShaderNodeMath',lab,*xy);k.operation=op;s(a,k.inputs[0])
  if b is not None:s(b,k.inputs[1])
  return k.outputs[0]
 def vm(op,lab,a,b,xy):
  k=N('ShaderNodeVectorMath',lab,*xy);k.operation=op;s(a,k.inputs[0])
  if b is not None:s(b,k.inputs[1])
  return k.outputs['Value'] if op=='DOT_PRODUCT' else k.outputs[0]
 def ramp(lab,a,x0,x1,y0,y1,xy):
  k=N('ShaderNodeMapRange',lab,*xy);k.clamp=True;k.interpolation_type='SMOOTHERSTEP'
  s(a,k.inputs['Value'])
  for name,value in [('From Min',x0),('From Max',x1),('To Min',y0),('To Max',y1)]:k.inputs[name].default_value=value
  return k.outputs['Result']
 def mix(lab,t,c0,c1,xy,act='MIX'):
  k=N('ShaderNodeMixRGB',lab,*xy);k.blend_type=act;k.use_clamp=False
  s(t,k.inputs[0]);s(c0,k.inputs[1]);s(c1,k.inputs[2]);return k.outputs[0]
 out=N('ShaderNodeOutputMaterial','Output',1173,80)
 if version=='Clay':
  p=N('ShaderNodeBsdfPrincipled','Neutral hair clay',881,80)
  p.inputs['Base Color'].default_value=(.51,.51,.51,1);p.inputs['Roughness'].default_value=.87
  if p.inputs.get('Specular IOR Level'):p.inputs['Specular IOR Level'].default_value=.14
  L(p.outputs[0],out.inputs['Surface']);return m
 paint=tex(nodes,albedo,(-1737,579),'2K directional silk paint · V0 scalp to V1 ends')
 uv=N('ShaderNodeUVMap','HairUV · strand surface',-1968,564);uv.uv_map='HairUV';L(uv.outputs['UV'],paint.inputs['Vector'])
 if version=='Export':
  p=N('ShaderNodeBsdfPrincipled','glTF diffuse with preserved 2K portrait palette',874,81)
  L(paint.outputs['Color'],p.inputs['Base Color']);p.inputs['Roughness'].default_value=.78
  if p.inputs.get('Specular IOR Level'):p.inputs['Specular IOR Level'].default_value=.16
  if p.inputs.get('Emission Color'):
   L(paint.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=.11
  L(p.outputs[0],out.inputs['Surface']);return m
 d,lo,shade,edge,uvgain=SETUP[rol]
 controls=tex(nodes,ribbon,(-1737,186),'R upper halo · G lower halo · B UV edge')
 L(uv.outputs['UV'],controls.inputs['Vector'])
 h=N('ShaderNodeSeparateColor','Two independent painted halo regions',-1428,147);L(controls.outputs['Color'],h.inputs[0])
 g=N('ShaderNodeNewGeometry','Actual curved ribbons and head-local stations',-1956,-247)
 l=Vector((-.40,-.71,.57)).normalized()
 # A largely view-independent three-tone palette. Soft steps leave real
 # curvature legible without forcing pinched nose/skull outlines.
 nvl=vm('DOT_PRODUCT','Key normal response',g.outputs['Normal'],tuple(l),(-1410,-251))
 if rol != 'inner':
  rear=vm('DOT_PRODUCT','Cool photographic back fill',g.outputs['Normal'],(.27,.86,.43),(-1490,-500))
  rear=math('MULTIPLY','Back fill is not a new ring',rear,.25,(-1400,-500))
  rear=math('ADD','Keep dimensional violet behind the locks',rear,-.19,(-1300,-500))
  nvl=math('MAXIMUM','Use key or soft back fill',nvl,rear,(-1250,-188))
 lift=ramp('Toon: diffuse fill to presence',nvl,-.34,.23,.0,1.,(-1183,-287))
 key=ramp('Toon: chroma-rich mid to silver light',nvl,.17,.73,0.,1.,(-1181,-511))
 shadow=hexlinear('A9A9C5');light=hexlinear('E4DEE8');basic=[max(.01,shadow[i]/light[i]) for i in range(3)];base=[shade*x+(1-shade) for x in basic]
 m0=mix('Cold violet shade to silver midtone',lift,tuple(base)+(1,),(.887,.88,.954,1),(-888,-229))
 m1=mix('Middle tone to silver light',key,m0,(1.,1.,1.,1),(-653,-222))
 paint_lit=mix('Lighting modulates original paint',1,paint.outputs['Color'],m1,(-429,566),'MULTIPLY')
 # Tangent response adds a mild silk directionality. The cross of U tangent
 # and normal is the V (root-tip) field.
 tangent=N('ShaderNodeTangent','UV tangent across fibres',-1982,-656);tangent.direction_type='UV_MAP';tangent.uv_map='HairUV'
 bitan=vm('CROSS_PRODUCT','Longitudinal silk tangent',g.outputs['Normal'],tangent.outputs[0],(-1717,-667))
 half=vm('ADD','Lighting/view half direction',g.outputs['Incoming'],tuple(l),(-1717,-836))
 halfn=vm('NORMALIZE','Unit half direction',half,None,(-1502,-835))
 cosh=vm('DOT_PRODUCT','Anisotropic silk response',bitan,halfn,(-1276,-766))
 a=math('ABSOLUTE','Axial orientation is unsigned',cosh,None,(-1061,-760))
 shin=ramp('Angle changes lobe, not brightness identity',a,.14,.68,1.,.61,(-844,-752))
 # Broad crown and waterfall halo stations complement the per-strand UV paint;
 # it reads as silk on a true volume, not horizontal bars glued to flat ribbons.
 p=N('ShaderNodeSeparateXYZ','Crown / fall stations in world metres',-1720,-387);L(g.outputs['Position'],p.inputs[0])
 w=N('ShaderNodeSeparateXYZ','Position inside single strand UV',-1948,223);L(uv.outputs['UV'],w.inputs[0])
 # Mimic separately blocked groups of hand-painted satin light. The crest's
 # apparent Z curves while U and phase skew every lock before any light gate.
 ph=N('ShaderNodeAttribute','Authored per-lock phase',-1618,847);ph.attribute_type='OBJECT';ph.attribute_name='suzu_silk_phase'
 phase=math('MULTIPLY','Artist per-lock phase to radians',ph.outputs['Fac'],6.2831853,(-1405,847))
 def wav(input_x,amp,pace,slide,label,at):
  xa,ya=at
  q=math('MULTIPLY',label+' rate',input_x,pace,(xa,ya))
  q=math('ADD',label+' phase',q,phase,(xa+141,ya))
  q=math('ADD',label+' displace',q,slide,(xa+272,ya))
  q=math('SINE',label+' wave',q,None,(xa+399,ya))
  return math('MULTIPLY',label+' amplitude',q,amp,(xa+526,ya))
 xabs=math('ABSOLUTE','Head side-to-side',p.outputs['X'],None,(-1865,-1050))
 xcurve=math('MULTIPLY','Crown falls subtly at sides',xabs,.110,(-1703,-1050))
 ycurve=math('MULTIPLY','Rear crown descends by a few mm',p.outputs['Y'],.034,(-1669,-1132))
 up=math('ADD','Crown follows the head',p.outputs['Z'],xcurve,(-1515,-1050))
 up=math('ADD','Crown follows the head in profile',up,ycurve,(-1465,-1123))
 xcurve=math('MULTIPLY','Lower ring lifts toward both tips',xabs,-.108,(-1710,-1370))
 low=math('ADD','Low light gently curves around the waterfall',p.outputs['Z'],xcurve,(-1515,-1370))
 broad_u=wav(w.outputs['X'],1,14.7,.0,'Soft separate locks',(-1640,604))
 tiny_u=wav(w.outputs['X'],1,49.1,.77,'Tiny longitudinal interruptions',(-1640,466))
 ga=ramp('Silky patches appear in three strengths',broad_u,-.75,.72,.12,1.,(-901,571))
 gb=ramp('Feathered brush details run lengthwise',tiny_u,-.89,.93,.45,1.,(-899,444))
 patch=math('MULTIPLY','Harmonized imperfect light shapes',ga,gb,(-721,546))
 uvw=math('MULTIPLY','Respect overlaps and fine inactive edges',h.outputs['Blue'],.93,(-1400,262))
 uvw=math('SUBTRACT','Silk reaches each blade middle',1.,uvw,(-1230,262))
 angle=math('MULTIPLY','Stable around opposite side views',shin,uvw,(-610,-715))
 angle2=math('MULTIPLY','Faint natural variations in each brush patch',patch,angle,(-450,552))
 def band(at,center,a,b,x,y,giving=''):
  q=math('SUBTRACT',giving+' measured distance to light',at,center,(x,y))
  q=math('ABSOLUTE',giving+' absolute offset from light',q,None,(x+133,y))
  return ramp(giving+' soft edges',q,a,b,1.,0.,(x+266,y))
 zc,zl=stations
 forwhich=[]
 for j,(at,center,dtex,bw,lab) in enumerate([(up,zc,h.outputs['Red'],d,'Upper lavender'),(low,zl,h.outputs['Green'],lo,'Lower ice')]):
  y=-1062-j*421
  # Displace physical patch locations (not the model). The lower halo is
  # less band-like and extends into longer cascading accents.
  perlock=wav(ph.outputs['Fac'],.0045 if j==0 else .0139,2.83,.83+j*.95,lab+' stagger by lock',(-2160,y-138))
  bend=wav(w.outputs['X'],.0028 if j==0 else .0057,7.66,.91+j*.50,lab+' bend across blade',(-2007,y-248))
  a=math('ADD',lab+' patch follows different lock stations',at,perlock,(-1424,y-20))
  a=math('ADD',lab+' soft arc varies along the pressure of the stroke',a,bend,(-1267,y-20))
  r=band(a,center,.0019 if j==0 else .0035,.015 if j==0 else .023,-1132,y-27,lab+' crest')
  diffuse=band(a,center,.004,.024 if j==0 else .039,-1128,y-135,lab+' silk wash')
  crest=math('MULTIPLY',lab+' narrow imperfect brush accents',r,(.94 if j==0 else .78)*bw,(-371,y-62))
  crest=math('MULTIPLY',lab+' slightly fragmented bright accents',crest,angle2,(-153,y-62))
  halo=math('MULTIPLY',lab+' soft wider satin fill',diffuse,(.19 if j==0 else .16)*bw,(-374,y-173))
  halo=math('MULTIPLY',lab+' soft wider fill favors fuller portions',halo,angle,(-142,y-173))
  near=band(at,center,.014,.055 if j==0 else .068,-1050,y-263,lab+' painted accents gate')
  uvh=math('MULTIPLY',lab+' original UV stroke',dtex,.43*uvgain*bw,(-365,y-280))
  uvh=math('MULTIPLY',lab+' original strokes connected to modeled arc',uvh,near,(-161,y-281))
  comb=math('ADD',lab+' varied satin reflectance',crest,halo,(15,y-155))
  outp=math('MAXIMUM',lab+' apparent full ring',comb,uvh,(200,y-155))
  forwhich.append(outp)
 a=mix('First diffuse-to-silk angel ring',forwhich[0],paint_lit,hexlinear('FEFAFF'),(101,437))
 a=mix('Second icy glow along descending tips',forwhich[1],a,hexlinear('F7FBFF'),(330,375))
 # A very narrow lavender contour, not a duplicate opaque black shell and
 # not a line on every internal hair edge. It only blooms near grazing views.
 q=vm('DOT_PRODUCT','Viewing direction against surface',g.outputs['Normal'],g.outputs['Incoming'],(-428,-474))
 q=math('ABSOLUTE','Silhouette distance from tangency',q,None,(-231,-469))
 q=ramp('Only a very fine real silhouette curve',q,.023,.123,.97,0.,(-49,-464))
 a0=math('MULTIPLY','Constrained thin violet contour',q,edge*1.74,(142,-463))
 innerline=ramp('Low strength glaze in genuine seam lanes',h.outputs['Blue'],.69,.99,0.,.15,(-51,-650))
 if rol in ('fine','ahoge','inner'):
  innerline=math('MULTIPLY','Fine insert shades more gently',innerline,.66,(83,-653))
 ink=math('MAXIMUM','Interior line or real silhouette, never combined dark stroke',a0,innerline,(353,-493))
 q=mix('Clear cool-grey lavender line · #6D6A8A',ink,a,hexlinear('6D6A8A'),(563,356))
 em=N('ShaderNodeEmission','Controlled silver-lavender NPR',878,80);L(q,em.inputs['Color']);L(em.outputs[0],out.inputs['Surface'])
 return m

def build_library(texdir=None,crown=None,lower=None,roles=ROLES):
 texdir=Path(texdir or os.environ.get('SUZU_HAIR_TEXTURE',HERE/'texture_r45'))
 stations=(float(crown if crown is not None else os.getenv('SUZU_CROWN_Z','1.562')),
           float(lower if lower is not None else os.getenv('SUZU_LOWER_Z','1.124')))
 out={}
 for role in roles:
  albedo=load(texdir/(role+'_color.png'),f'Suzu B · 2K {role} portable painted colour r45')
  flow=load(texdir/(role+'_flow.png'),f'Suzu B · 2K {role} directional colour r45')
  ribbon=load(texdir/(role+'_ribbon.png'),f'Suzu B · 2K {role} dual halos r45',True)
  fam={v:material(role,v,albedo if v=='Export' else flow,ribbon,stations) for v in ('NPR','Export','Clay')}
  fam['NPR']['suzu_glb_material']=fam['Export'].name
  fam['NPR']['suzu_clay_material']=fam['Clay'].name
  out[role]=fam
 return out

def silk_phase(o):
 authored=float(o.get('suzu_hair_phase',0))
 salt=(zlib.crc32(o.name.encode('utf-8')) & 0xffff)/65536
 return (salt+authored*3.95)%1.

def looks_like_prop(st):
 return any(x in st.lower() for x in ('clip','gem','brooch','crescent','ribbon bow','silk bow','star ornament','accessor','prop','新月','发卡','蝴蝶结'))
def role_of(o,explicit=False):
 # Do not guess at Phase A, bodies, or props. Material and object metadata
 # retain the role even after the first material exchange.
 for x in o.material_slots:
  m=x.material
  if m and m.get('suzu_phaseB_palette') and m.get('suzu_hair_role'):return m['suzu_hair_role']
 def canon(s):
  s=str(s).lower().strip().split('/')[-1].split(':')[-1].strip(' _-')
  if s in ROLES:return s
  for word,role in [('bang','bang'),('fringe','bang'),('temple','temple'),('face lock','temple'),('side','temple'),('sideburn','temple'),('pony','pony'),('tail','pony'),
                    ('scalp','crown'),('crown','crown'),('cap','crown'),('fine','fine'),('filament','fine'),('ahoge','ahoge'),('curtain','inner'),
                    ('under','inner'),('inner','inner'),('mid','middle'),('mantle','middle'),('outer','outer')]:
   if word in s:return role
  return None
 if str(o.get('suzu_stage_role','')).lower() in {'prop','hair_prop','hair/prop','hair_accessory','hair/accessory'}:return None
 h=o.get('suzu_hair_role') or (o.get('Hair layer') if o.type=='MESH' and o.data.uv_layers.get('HairUV') else None)
 if h:
  r=canon(h)
  if r:return r
 stage=str(o.get('suzu_stage_role','')).lower()
 if stage and ('hair' in stage or stage in ROLES):
  return canon(stage) or canon(o.name) or 'outer'
 if looks_like_prop(o.name):return None
 if explicit:
  for m in o.material_slots:
   if m.material and 'hair' in m.material.name.lower():
    candidate=canon(m.material.name)
    if candidate:return candidate
  return canon(o.name) or 'outer'
 return None

def assign_hair(palette,style='NPR',objects=None):
 source=objects if objects is not None else bpy.context.scene.objects
 result=[]
 for o in source:
  if o.type!='MESH' or not o.data.uv_layers.get('HairUV'):continue
  r=role_of(o,objects is not None)
  if not r or r not in palette:continue
  m=palette[r][style]
  # Each geometry group is a single hair surface type (not accessories).
  o['suzu_stage_role']='hair';o['suzu_hair_role']=r;o['suzu_silk_phase']=silk_phase(o)
  if not len(o.data.materials):o.data.materials.append(m)
  elif len(o.material_slots)==1:o.material_slots[0].material=m
  else:
   for sl in o.material_slots:
    if sl.material and looks_like_prop(sl.material.name):continue
    sl.material=m
  result.append((o.name,r))
 return result

def main():
 mode=os.environ.get('SUZU_HAIR_STYLE','NPR')
 lib=build_library()
 names=assign_hair(lib,mode)
 if not names:raise RuntimeError('No tagged Phase B hair objects. Set suzu_stage_role or suzu_hair_role.')
 cs=bpy.context.scene;cs.view_settings.view_transform='Standard';cs.view_settings.look='None'
 path=os.environ.get('PAINT_HAIR_OUT')
 if path:
  bpy.context.preferences.filepaths.save_version=0
  bpy.ops.wm.save_as_mainfile(filepath=str(Path(path).resolve()),compress=True)
 print('Painted hair surfaces:',len(names),names)
if __name__=='__main__':main()

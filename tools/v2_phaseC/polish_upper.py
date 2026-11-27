"""Round 6: tuck the existing Oxford lips and thicken the original gold braid."""
from collections import Counter
from pathlib import Path
import json,math,sys,bpy
from mathutils import Vector

SHIRT={
 'Shirt · fitted ivory front':'block',
 'Shirt · fitted ivory back':'block',
 'Shirt · real folded button placket':'placket',
 'Shirt · placket blind stitch -1':'placket',
 'Shirt · placket blind stitch 1':'placket',
 'Shirt · pressed pointed collar -1':'point',
 'Shirt · pressed pointed collar 1':'point',
 'Shirt · turned neck stand':'stand',
}
PIPES={
 **{f'Jacket · {style} {side}':rings for style,rings in
    [('fine gold at open hem',83),('front binding',33),('fine gold lapel braid',43)]
    for side in (-1,1)},
 **{f'Jacket · {side} cuff double gold {f:.3f}':56
    for side in ('L','R') for f in (.930,.963)},
}
CUFF='cuff double gold'
SEAM_TUCK=.00265
BRAID_WIDTH=1.175

def smooth(a,b,x):
 u=min(1,max(0,(x-a)/(b-a)));return u*u*(3.-2*u)

def shift(q,kind):
 x,y,z=q
 if kind in ('block','placket'):
  # Seat the tucked lower Oxford continuously inside the waistband,
  # including the facing and the two narrow placket stitches.
  waist=1-smooth(1.055,1.076,z)
  shoulder=smooth(1.260,1.285,z)
 else:
  waist=0.
  shoulder=(.40+.60*smooth(1.267,1.287,z)) if kind=='stand' else smooth(1.260,1.280,z)
 d=Vector()
 if waist:
  ray=Vector((x,y+.0315,0))
  if ray.length>.001:d-= ray.normalized()*(waist*SEAM_TUCK)
 if shoulder:
  ray=Vector((x,y-.0335,0))
  # The two pointed collar leaves below the edge continue to sit above
  # the lapel. Only the actual upper lip is moved inward.
  if ray.length>.001:
   w=.992 if kind in ('point','stand') else .975
   d-= ray.normalized()*(shoulder*SEAM_TUCK*w)
  if kind in ('point','stand'):
   d.z-=shoulder*.00035
 return d

def apply(scene=None,strict=True):
 scene=scene or bpy.context.scene
 if scene.get('suzu_round6_oxford_and_braid'):raise ValueError('Round 6 upper geometry is already present.')
 pose=scene.frame_current
 scene.frame_set(1)
 missing=(set(SHIRT)|set(PIPES))-{o.name for o in scene.objects}
 if missing and strict:raise ValueError(f'Unexpected upper-garment object list: {sorted(missing)}')
 audit={'oxford':{},'gold':{},'braid_width_scale':BRAID_WIDTH,'shirt_tuck_max_mm':SEAM_TUCK*1000}
 for name,kind in SHIRT.items():
  o=scene.objects.get(name)
  if o is None:continue
  if o.type!='MESH':raise TypeError(o.name)
  if o.data.users>1:o.data=o.data.copy()
  m=o.matrix_world.copy();mm=m.inverted();n=0;d0=0.
  for v in o.data.vertices:
   p=m@v.co;d=shift(p,kind)
   if d.length>1.0e-7:v.co=mm@(p+d);n+=1;d0=max(d0,d.length)
  o.data.update()
  audit['oxford'][name]=[n,round(d0*1000,4)]
 for name,rings in PIPES.items():
  o=scene.objects.get(name)
  if o is None:continue
  if o.type!='MESH':raise TypeError(o.name)
  if o.data.users>1:o.data=o.data.copy()
  v=o.data.vertices
  if len(v)!=8*rings:raise ValueError((name,'original 8-sided piping section count',len(v),8*rings))
  # Each eight-vertex section is planar, with an affine equal-angle radial
  # construction. Move girth, not the pattern seam or bracelet centerline.
  for k in range(0,len(v),8):
   a=[v[k+j] for j in range(8)]
   c=sum((q.co for q in a),Vector())/8
   r=[q.co-c for q in a]
   if max(p.length for p in r)>.00325:raise ValueError((name,k,'not a piping section'))
   for q,d in zip(a,r):q.co=c+BRAID_WIDTH*d
  o.data.update()
  audit['gold'][name]=rings
 scene['suzu_round6_oxford_and_braid']=True
 scene.frame_set(pose)
 return audit

if __name__=='__main__':
 argv=sys.argv[sys.argv.index('--')+1:]
 if not argv:raise SystemExit('Usage: blender -b approved.blend -P polish_upper.py -- patched.blend [audit.json]')
 result=apply()
 out=Path(argv[0]).resolve()
 if len(argv)>1:Path(argv[1]).write_text(json.dumps(result,indent=2))
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
 print(json.dumps(result,indent=2))

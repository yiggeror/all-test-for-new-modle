"""Round 2.5 under-jaw junction: seat the neck rim inside the final head."""
import bpy,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
from pose_r25 import smoothstep,NECK_ROOT_Z,NECK_FACTOR
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
d=Path(a[0]).resolve() if a else H/'body_r25_neck.blend'
o=next(x for x in bpy.data.collections['SUZU_BODY'].all_objects if x.name.startswith('Suzu | body,'))
for v in o.data.vertices:
    x,y,z=v.co
    # Preserve the collar and visible front profile. Only the buried upper third
    # of the nape is pulled under the reduced occipital section of the new head.
    depth=NECK_ROOT_Z+(z-NECK_ROOT_Z)/NECK_FACTOR
    k=smoothstep((depth-1.319)/.031)
    if k>0:
        c=smoothstep((y-.005)/.042)
        v.co=(x*(1-.043*k),y-k*(.013+.015*c),z)
o.data.update()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(d),compress=True)

"""Apply the localized Round 6 material and clothing finish to a Phase C scene."""
import bpy
import sys
from pathlib import Path
a=sys.argv[sys.argv.index('--')+1:]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import polish_upper,apply_shoes_r6,lighting_r6
scene=bpy.context.scene
assert len(scene.objects['Suzu · Humanoid'].data.bones)>=154
oxford=polish_upper.apply(scene)
assert len(oxford['gold'])==10 and len(oxford['oxford'])==8
assert len(apply_shoes_r6.apply_shoes(scene))>=26
lighting_r6.apply()
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(a[0]).resolve()),compress=True)

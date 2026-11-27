from pathlib import Path
import os
MODULE_DIR=Path(os.path.realpath(__file__)).parent
for f in ('core','skirt','legs','jacket','accessories','fit_pose','preview'):
 p=MODULE_DIR/(f+'.py')
 if p.exists():exec(compile(p.read_text(),str(p),'exec'),globals(),globals())
mode=os.getenv('SUZU_STAGE','build')
if mode!='skirt':
 sc.camera=cam('Wardrobe review camera',(.95,-3,1.38),(0,0,.68),1.44)
 bpy.ops.wm.save_as_mainfile(filepath=str(D/os.getenv('SUZU_OUT','garment.blend')),compress=True)
 if mode=='publish':
  preview('garment_3q',(0,0,.665),(.42,-1,.16),1.42,720,900)
  preview('jacket_front',(0,-.01,1.157),(.13,-1,.09),.57,820,620)
  preview('shoe_3q',(.069,-.035,.060),(.70,-1,.50),.265,680,480)
  preview('skirt_detail',(0,-.015,.866),(.26,-1,.16),.59,820,575)
else:
 preview('skirt_first',(0,0,.87),(.27,-1,.17),.545,720,540)

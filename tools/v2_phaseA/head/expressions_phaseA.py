"""Four Suzu portraits assembled from the official native VRoid expression channels."""
import json
from pathlib import Path

PRESETS={
    'soft_smile':{'MTH_Fun':.45,'MTH_Up':.20,'EYE_Fun':.18,'BRW_Fun':.17},
    'bright_laugh':{'MTH_Joy':.90,'EYE_Fun':.50,'BRW_Joy':.43},
    'smiling_eyes':{'MTH_Fun':.68,'MTH_Up':.13,'EYE_Joy':.85,'EYE_Close':.15,'BRW_Fun':.22},
    'little_o':{'MTH_O':.72,'MTH_Small':.68,'MTH_U':.09,'EYE_Surprised':.65,'BRW_Surprised':.58},
}

def name_tail(name):return name.split('Fcl_',1)[-1]

def apply_expression(face,preset,amount=1.0):
    ks=face.data.shape_keys.key_blocks; by={name_tail(b.name):b for b in ks[1:]};weights=PRESETS.get(preset,{})
    if preset=='blink_qc':weights={'EYE_Close':1.0}
    if preset not in ('neutral','blink_qc') and preset not in PRESETS:raise KeyError(preset)
    for k,b in by.items():b.value=float(weights.get(k,0.)*amount)
    if set(weights)-set(by):raise ValueError((preset,sorted(set(weights)-set(by))))
    return {by[k].name:by[k].value for k in weights}

def write_preset_json(face,path):
    names={name_tail(b.name):b.name for b in face.data.shape_keys.key_blocks[1:]}
    Path(path).write_text(json.dumps({p:{names[k]:v for k,v in values.items()} for p,values in PRESETS.items()},indent=2,ensure_ascii=False))

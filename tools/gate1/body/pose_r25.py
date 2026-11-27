"""Shared R2.5 fitting kinematics. All coordinates are world metres.

Use open_arm() with the same weights for each corresponding sleeve and skin
section. The locked hand and its nails always receive the full rigid motion.
Use shorten_foot() for both the bare last and fitted stocking. The shoe shell
is shortened about the same ankle station as a complete subassembly.
"""
from math import atan2,cos,sin,radians,degrees
SHOULDER=(.129,.006,1.227)
WRIST=(.290,-.008,.835)
ORIGINAL_OPEN_DEG=degrees(atan2(WRIST[0]-SHOULDER[0],SHOULDER[2]-WRIST[2]))
OPEN_DEG=35.
DELTA_DEG=OPEN_DEG-ORIGINAL_OPEN_DEG
ARM_FULL_Z=1.104
ARM_FADE_Z=1.210
LAST_PIVOT_Y=.006
LAST_FACTOR=.80
FOOT_FULL_Z=.078
FOOT_FADE_Z=.108
NECK_ROOT_Z=1.290
NECK_FACTOR=.94

def smoothstep(t):
    t=max(0.,min(1.,float(t)))
    return t*t*(3.-2.*t)

def open_weight(z):
    return smoothstep((ARM_FADE_Z-z)/(ARM_FADE_Z-ARM_FULL_Z))

def open_arm(p,side=None,full=False):
    x,y,z=p
    if side is None:side=-1 if x<0 else 1
    w=1. if full else open_weight(z)
    a=radians(DELTA_DEG)*w
    c,s=cos(a),sin(a)
    sx,_,sz=SHOULDER
    lx,lz=side*x-sx,z-sz
    return side*(sx+c*lx-s*lz),y,sz+s*lx+c*lz

def shorten_foot(p,shoe=False):
    x,y,z=p
    w=1. if shoe else smoothstep((FOOT_FADE_Z-z)/(FOOT_FADE_Z-FOOT_FULL_Z))
    return x,y-(1-LAST_FACTOR)*(y-LAST_PIVOT_Y)*w,z

def shorten_neck(p):
    x,y,z=p
    return x,y,z-(1-NECK_FACTOR)*max(0.,z-NECK_ROOT_Z)

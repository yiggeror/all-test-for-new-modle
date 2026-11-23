"""Gate 1 春：从真正的 Rainroji 三维场景组织出有暖灯、花树、门楼的街角。"""
import numpy as np
from engine.render import Camera
from engine.world import MASK_THIN
from scenes import spring as base

NAME, K, T = base.NAME, base.K, base.T
sky = base.sky
PHASE = 0.31
RENDER = dict(base.RENDER, fog=dict(base.FOG, sigma=.0031))
GRADE = dict(base.GRADE, exposure=3.06, contrast=1.13, sat=1.03, lift=(0.023,0.023,0.039))
PAL = dict(base.PAL, k=60, chroma_w=4.5)
DENOISE = dict(base.DENOISE, sl=.11)
DITHER, DSTR = 'mix', 0.40

ANCHORS = {
    '暖路灯': (0.36,5.3,10.8), '粉花主树': (5.8,7.4,7.5), '砖门楼坡顶': (2.15,3.10,14.0),
    '倚墙车': (-1.78,.50,13.30), '睡猫落点': (2.15,3.34,14.25),
    '飞蛾落点': (0.24,4.9,10.7), '冷色电视暖窗': (-4.3,5.4,-.8),
}

def camera(W=320,H=180):
    return Camera((6.25,8.25,35.8),(1.55,4.4,10.5),fov=43.0,W=W,H=H)

def _roadster(w):
    # Close-shot bicycle with thickness chosen for genuine low-resolution ray samples.
    tires = dict(sides=5,mat='plain',col='#241e29',mask=MASK_THIN)
    metal = dict(sides=5,mat='plain',col='#786a6b',mask=MASK_THIN)
    frame = dict(sides=5,mat='plain',col='#533d47',mask=MASK_THIN)
    rr=.36
    a=np.linspace(0,2*np.pi,21)
    for x in (-.54,.54):
        points=np.stack([x+rr*np.cos(a),.04+rr*(1+np.sin(a)),np.zeros_like(a)],1)
        w.tube(points[:-1],points[1:],.038,**tires)
        c=(x,rr+.04,0)
        for i in (0,5,10,15):
            w.tube(c,points[i],.013,**metal)
    bb=(0,.37,0); st=(-.27,.91,0); neck=(.39,.92,0)
    for aa,bb_ in [(bb,st),(st,neck),(neck,bb),((-.54,.4,0),bb),((-.54,.4,0),st),((.54,.4,0),neck)]:
        w.tube(aa,bb_,.028,**frame)
    w.tube(neck,(.34,1.08,0),.023,**metal)
    w.tube((.34,1.08,-.24),(.34,1.08,.24),.023,**metal)
    w.box((-.30,.97,0),(.27,.065,.16),mat='plain',col='#3e2934')
    w.box((-.48,.79,0),(.41,.026,.14),mat='plain',col='#372735')
    w.sphere((.40,1.065,.035),.058,n=6,mat='plain',col='#cfaf89')

def build():
    w=base.build()
    for light in w.lights:
        if light["grp"] == base.G_LAMP and "axis" in light:
            light["vol"] *= .22
            light["color"] *= .68
    with w.at((-1.78,0,13.30),yaw=.21):
        lean = -.095
        M = np.array([[1,0,0],[0,np.cos(lean),-np.sin(lean)],[0,np.sin(lean),np.cos(lean)]])
        with w.at((0,0,0),M=M): _roadster(w)
    # 尾巴贴瓦脊，头趴爪子。同一盏暖灯照亮实体，非屏贴。
    with w.at((2.15,3.16,14.25),yaw=np.pi/2):
        fur=dict(mat='plain',col='#b46d3e',seed=.4)
        w.sphere((0,.134,0),.195,n=8,squash=.70,**fur)
        w.sphere((-.17,.113,.01),.121,n=8,squash=.82,**fur)
        w.sphere((-.205,.065,.071),.064,n=6,squash=.63,mat='plain',col='#d89765',seed=.1)
        for z in (-.052,.067):
            w.poly([(-.21,.16,z-.043),(-.12,.16,z+.016),(-.181,.258,z+.001)],**fur)
            w.poly([(-.18,.258,z+.001),(-.12,.16,z+.016),(-.18,.16,z+.055)],**fur)
        w.tube((.13,.073,.022),(.24,.045,.045),.042,.032,sides=6,**fur)
        w.tube((.24,.045,.045),(.21,.042,.128),.032,.028,sides=6,**fur)
        w.tube((.21,.042,.128),(.12,.036,.147),.028,.023,sides=6,**fur)
    return w

def setup(plate,cam):
    c = base.setup(plate,cam)
    # Keep the exact prototype seeds/placement and select sparser physical trajectories.
    for p, count in zip([*c['pet'], c['shed']], [1250,450,21,255]):
        for name in ('base','vel','phase','sw_a','sw_f','sw_p','size','rnd','tint'):
            item = getattr(p,name,None)
            if item is not None:
                setattr(p,name,item[:count])
        p.n = count
    c['amb'] *= np.array([.83,.74,.78], np.float32)
    c['pet'][1].size *= .84
    c['pet'][2].size *= .79
    return c

def frame(context,ph):
    return base.frame(context,ph)

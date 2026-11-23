"""Gate 1.5 春：从真正的 Rainroji 三维场景组织出有暖灯、花树、门楼的街角。"""
import numpy as np
from engine.render import Camera
from engine.world import MASK_THIN, MASK_NEAR, srgb, _n
from engine.mats import mat, sstep
from scenes import spring as base

NAME, K, T = base.NAME, base.K, base.T
sky = base.sky
PHASE = 0.31
CAT_TAG = 27
TWO_PASS = True
CAT_AT = (2.135,3.150,15.26)
LAMP_AT = np.array([.2666,5.05,10.823],np.float32)

@mat('g15_fur')
def fur_lamp_response(S):
    # Restrained local rim response grouped with the streetlamp; front stays warm-shadowed.
    facing=np.clip((_n(LAMP_AT[None]-S.P)*S.N).sum(1),0,1)
    rim=sstep(.23,.72,S.N[:,1])*(.48+.52*sstep(.05,.78,facing))
    bounce=(.010+.102*rim)*S.prm[:,0]
    return dict(alb=S.col,emis=srgb('#ffa664')[None]*bounce[:,None])

def _petal_hook(sf,acc,rng):
    cat = sf['tag']==CAT_TAG
    before=sf['alb'][cat].copy()
    base.petal_hook(sf,acc,rng)
    sf['alb'][cat]=before

RENDER = dict(base.RENDER, fog=dict(base.FOG, sigma=.0031), hook=_petal_hook)
GRADE = dict(base.GRADE, exposure=3.06, contrast=1.13, sat=1.03, lift=(0.023,0.023,0.039))
PAL = dict(base.PAL,k=60,chroma_w=4.5,extra=[
    *base.PAL['extra'],(.73,.39,.23),(.87,.54,.29),(.48,.24,.22)
])
DENOISE = dict(base.DENOISE, sl=.11)
DITHER, DSTR = 'mix', 0.40

ANCHORS = {
    '暖路灯': (0.36,5.3,10.8), '粉花主树': (5.8,7.4,7.5), '砖门楼坡顶': (2.15,3.10,14.0),
    '倚墙车': (-1.78,.50,13.30), '睡猫落点': (2.14,3.33,15.26),
    '飞蛾落点': (0.24,4.9,10.7), '冷色电视暖窗': (-4.3,5.4,-.8),
}

def camera(W=320,H=180):
    return Camera((6.48,7.68,38.5),(1.61,5.18,10.5),fov=43.0,W=W,H=H)

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

def _loaf_head(w):
    # Low-pixel head designed as a solid bevelled mesh at the roof's world depth.
    # Native-pixel coordinates are an artist's guide converted to world coordinates before ray tracing.
    cam=camera()
    px,py,_,depth=cam.project((2.14,3.33,15.26))
    profile=np.array([
        (-5.14,.57),(-4.90,-.20),(-4.53,-.88),(-4.98,-3.26),(-3.92,-3.31),
        (-3.48,-2.60),(-2.98,-1.58),(-2.13,-1.56),(-1.99,-2.63),(-1.94,-3.34),
        (-.76,-3.36),(-.52,-.86),(-.19,-.20),(.07,.61),(-.36,1.42),
        (-1.56,1.88),(-3.19,1.53),(-4.76,1.25),
    ],np.float64)
    center=np.array([-2.90,.42])
    # Fan bevel leaves an actual 3D rim light; roof, weather and the camera can still occlude the figure.
    scales=(.89,1,.80)
    planes=(depth-.26,depth-.095,depth+.11)
    def at(q,z):
        xx,yy=np.asarray(q).T
        dx=((2*(xx+px)/cam.W-1)*cam.th*z)[...,None]
        dy=(((1-2*(yy+py)/cam.H)*cam.tv+cam.shift)*z)[...,None]
        return cam.pos+cam.f*z+dx*cam.r+dy*cam.u
    rings=[at(center+(profile-center)*scale,z) for scale,z in zip(scales,planes)]
    base_opts=dict(mat='g15_fur',tag=CAT_TAG,grp=base.G_LAMP)
    shadow=dict(base_opts,col='#693a2e',prm=(.81,0,0,0),seed=.45)
    rim=dict(base_opts,col='#b26938',prm=(1.02,0,0,0),seed=.43)
    ear=dict(base_opts,mat='emit',col='#532c35',prm=(.045,.29,0,0),seed=.2)
    front_p=at(center,planes[0]-.045)
    for k in range(len(profile)):
        j=(k+1)%len(profile)
        upper=max(profile[k,1],profile[j,1]) < -1.49
        w.poly((front_p,rings[0][k],rings[0][j]),**(ear if upper else shadow))
        w.quads(rings[0][k],rings[1][k],rings[1][j],rings[0][j],**(ear if upper else rim))
        w.quads(rings[1][k],rings[2][k],rings[2][j],rings[1][j],**shadow)
        w.poly((at(center,planes[2]),rings[2][j],rings[2][k]),**shadow)

def build():
    w=base.build()
    for light in w.lights:
        if light["grp"] == base.G_LAMP and "axis" in light:
            light["vol"] *= .54
            light["color"] *= np.array([.94,.875,.78],np.float32)
            light["cone"] = (-.16,.72)
    with w.at((-1.78,0,13.30),yaw=.21):
        lean = -.095
        M = np.array([[1,0,0],[0,np.cos(lean),-np.sin(lean)],[0,np.sin(lean),np.cos(lean)]])
        with w.at((0,0,0),M=M): _roadster(w)
    # Gate 1.5: real tagged 3D figure, not a screen-space sprite.
    with w.flag(MASK_NEAR), w.at(CAT_AT,yaw=.10):
        light=dict(mat='g15_fur',tag=CAT_TAG,grp=base.G_LAMP)
        fur=dict(light,col='#9a4c32',seed=.4,prm=(1.32,0,0,0))
        cream=dict(light,col='#dcac71',seed=.1,prm=(1.28,0,0,0))
        with w.at((.085,.127,0),M=np.diag([1.08,.67,.82])):
            w.sphere((0,0,0),.181,n=12,**fur)                        # arched back
        w.sphere((-.204,.105,.078),.066,n=8,squash=.63,**cream)    # muzzle, catching a glint
        w.sphere((-.13,.061,.098),.071,n=8,squash=.54,**fur)       # forepaws tucked
        # Tail follows the downslope, retaining a clear tapered tip above the tiles.
        path=[(.214,.103,.064),(.270,.079,.127),(.286,.043,.191),
              (.269,.012,.240),(.235,.003,.272)]
        for a,b,r0,r1 in zip(path,path[1:],(.047,.042,.035,.028),(.042,.035,.028,.020)):
            w.tube(a,b,r0,r1,sides=7,**fur)
    with w.flag(MASK_NEAR): _loaf_head(w)
    return w

def setup(plate,cam):
    # Lower/upper ear gaps at 320 px need a firm pixel-art silhouette. Reuse the actual
    # cat-hidden ray pass for minority edge pixels and decontaminate majority edge pixels.
    a=plate.get(f'tag{CAT_TAG}')
    if a is not None and 'far' in plate:
        front,behind=plate['layers'],plate['far']['layers']
        open_air=(a>0)&(a<.5)
        front[:,open_air]=behind[:,open_air]
        edge=(a>=.5)&(a<.999)
        v=a[edge][None,:,None]
        ray_color=np.maximum(0,(front[:,edge]-behind[:,edge]*(1-v))/v)
        front[:,edge]=front[:,edge]*.18+ray_color*.82
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

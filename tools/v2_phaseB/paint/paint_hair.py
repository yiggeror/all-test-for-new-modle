"""Paint reusable 2K Suzu hair maps; mesh U across the blade, V=0 scalp → V=1 tip."""
from pathlib import Path
from math import pi
import argparse
import numpy as np
from PIL import Image

D=Path(__file__).resolve().parent
PALETTE=dict(silver='E4DEE8',ice='C0CFEC',shade='A9A9C5',silk='FCF9FF',ink='6D6A8A')
# (texture-ring amount, crown station, low station, icy fade onset, curtain depth)
ROLES={
 'crown': (.78,.364,None,.70,0.00),
 'bang':  (.76,.348,None,.67,0.00),
 'temple':(.81,.259,.756,.41,0.00),
 'outer': (.88,.132,.761,.43,0.00),
 'middle':(.79,.143,.743,.48,.09),
 'pony':  (.81,.223,.789,.43,.025),
 'fine':  (.48,.295,.784,.36,.015),
 'inner': (.13,None,.774,.46,.60),
 'ahoge': (.23,.280,None,.71,.025)
}

def color(h): return np.asarray([int(h[i:i+2],16) for i in (0,2,4)],np.float32)/255
def sf(a,b,t):
 x=np.clip((t-a)/(b-a),0,1);return x*x*(3-2*x)
def g(x):return np.exp(-np.minimum(x*x,64)).astype(np.float32)
def wash(a,b,f):
 if isinstance(b,str):b=color(b)
 return a*(1-f[...,None])+b*f[...,None]
def save(p,a):
 Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p,optimize=True)
def gradients(U,V,role,variant):
 amount,v1,v2,start,curtain=ROLES[role];k=variant*2.71
 black=0.92 if role=='inner' else 1
 a=np.tile(color(PALETTE['silver']),(V.shape[0],U.shape[1],1))
 # First portion is porcelain silver-lavender; color follows lengths, not world Z.
 r=sf(start,.92,V)
 ice={'crown':.23,'bang':.39,'temple':.83,'ahoge':.24}.get(role,.95)
 a=wash(a,'D6D9ED',.53*sf(.18,.69,V)*black*(.62+.38*ice))
 a=wash(a,PALETTE['ice'],r*ice)
 a=wash(a,'B9B3CE',.20*(1-sf(.016,.236,V))*(.91-.25*U))
 a=wash(a,PALETTE['shade'],curtain*(.94+.06*V))
 if role=='inner':
  a=wash(a,'9290B4',.49+.21*(1-sf(.29,.95,V))+0.10*sf(.51,.86,U))
 # Volume belongs to the actual geometry. The map carries only slim crease
 # shading, pale long ink and the silky broad slightly off-centre ridge.
 uc=U-.008*np.sin(6.8*V+k)-.014*np.sin(2.8*V-.33+k)
 edge=np.minimum(U,1-U)
 a=wash(a,'A8A2C0',.20*(1-sf(.000,.122,edge))**1.6)
 # One thin ink-weighted core, not a dark strip. Lake-grey/lavender mixes
 # against the original 2K wash and is visible in the portable viewer too.
 line=(1-sf(.006,.039,edge)) * (1-.43*(1-sf(.14,.78,V)))
 a=wash(a,PALETTE['ink'],line*(.19 if role in ('fine','ahoge') else .31))
 a=wash(a,'F2EBF4',.16*g((uc-(.43+.03*np.sin(V*5.1+k)))/.238)*(1-.45*r))
 a=wash(a,'DEEAFF',.17*g((uc-.388)/.209)*r)
 # Irregular long brushstrokes, each with a softened start and end. No
 # per-pixel noise or horizontal marks are used; silhouette stripes are sparse.
 rng=np.random.default_rng(3394+variant*121+list(ROLES).index(role)*525)
 for j,p in enumerate(np.linspace(.056,.945,30)):
  p+=rng.uniform(-.012,.012);f=rng.uniform(.055,.13);w=rng.uniform(.0019,.0076)
  bow=rng.uniform(.002,.019);drift=rng.uniform(-.036,.032);az=rng.uniform(-pi,pi)
  t0=rng.uniform(-.14,.45);t1=t0+rng.uniform(.42,1.04)
  path=p+drift*(V-.46)+bow*np.sin(4.8*V+az)*sf(.0,.57,V)
  envelope=sf(t0,t0+f,V)*(1-sf(t1-f,t1,V))
  f0=g((uc-path)/w)*envelope
  a=wash(a,'E7E7F8' if j%4!=0 else 'ADABC6',f0*rng.uniform(.025,.081 if j%4!=0 else .27))
 # Two tapered softened ink fibres indicate overlapping silk, separated
 # from the near-invisible comb of smaller hairs.
 cores=(.241+.032*np.sin(3.7*V+k),.722+.041*np.sin(4.1*V-.4+k))
 for q,c0 in enumerate(cores):
  env=sf(.13-.042*q,.25+.024*q,V)*(1-sf(.76-.035*q,.97-.026*q,V))
  f=g((uc-c0)/(.0092+.0021*q))*.085*env
  a=wash(a,'88829F',f)
 # A couple longer light strokes preserve a bigger rhythm over the fibre layer.
 a=wash(a,'F2EDF9',.24*g((uc-(.34+.018*np.sin(3*V+k)))/.013)*sf(.1,.24,V)*(1-sf(.58,.78,V)))
 a=wash(a,'F3F8FF',.18*g((uc-(.63+.024*np.sin(6*V+.1+k)))/.008)*sf(.59,.67,V)*(1-sf(.92,.99,V)))
 return a
def painted_halo(U,V,v0,width,k,shift=0.0,lower=False):
 if v0 is None:return np.zeros((V.shape[0],U.shape[1]),np.float32)
 # Bowed 'ribbon' following the strands' own flow. The edge breaks use
 # coherent tapered dabs, not per-pixel white clipping.
 s=U-.5
 bent=v0+shift+.074*(s*s-.075)+.011*np.sin(U*6.3+k)+.005*np.cos(U*12.6-k*.7)
 streak=.0031*np.sin(27*U+1.3*np.sin(18*U+k))+.0016*np.sin(63*U+.45+k)
 mid1=width*(.78+.23*np.cos(13.1*U+k)+.09*np.cos(45*U-.4*k))
 mid1=np.maximum(mid1,width*.35)
 q=1-sf(.43,1.67,np.abs((V-bent-streak)/mid1))
 q*=sf(.042,.15,U)*(1-sf(.88,.973,U))
 # Gentle interruption and tiny silky notch; visible in the 2K close shot,
 # visually a few broad lobes at head scale.
 broken=1-.69*g((U-(.21+.12*np.sin(k*.7+.3)))/.044)-.43*g((U-(.77+.05*np.sin(k-.2)))/.033)
 wings=.17*g((U-(.27+.10*np.sin(k)))/.075)+.19*g((U-(.66+.08*np.cos(k)))/.066)
 return np.clip(q*broken*(.71+wings),0,1).astype(np.float32)
def make_one(p,role,n,variant=0):
 U=(np.arange(n,dtype=np.float32)[None,:]+.5)/n
 V=1-(np.arange(n,dtype=np.float32)[:,None]+.5)/n
 a=gradients(U,V,role,variant)
 amount,v1,v2,_,_=ROLES[role];k=variant*1.53+list(ROLES).index(role)*.31
 r=painted_halo(U,V,v1,.022 if role in ('crown','bang') else .020,k)
 b=painted_halo(U,V,v2,.025 if role in ('outer','middle','pony') else .018,k+1.7,.0017,True)
 # The portable image retains painted light bands; Blender can add their
 # smoothly angle-dependent continuation using separate UV masks.
 bake=wash(a,'FCF8FF',r*amount*.43)
 bake=wash(bake,'F6FAFF',b*amount*.40)
 save(p/(role+'_color.png'),bake)
 save(p/(role+'_flow.png'),a)
 # RGB control atlases: R crown; G lower; B outlines the narrowest side lane.
 e=1-sf(.003,.105,np.minimum(U,1-U));e=np.broadcast_to(e,r.shape)
 save(p/(role+'_ribbon.png'),np.dstack((r,b,e)))
def go():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=D/'texture_r45');p.add_argument('--size',type=int,default=2048);p.add_argument('--roles',default=','.join(ROLES));a=p.parse_args()
 a.out.mkdir(parents=True,exist_ok=True)
 for role in a.roles.split(','):
  make_one(a.out,role,a.size)
  print(role, a.size,flush=True)
if __name__=='__main__':go()

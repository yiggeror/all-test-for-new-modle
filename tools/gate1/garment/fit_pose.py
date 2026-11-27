"""Round 2.5 body/wardrobe fit map in metres (left is positive X)."""
from math import sin,cos,atan2,radians
SHOULDER_X=.129
SHOULDER_Z=1.227
TARGET=radians(35)
DELTA=TARGET-atan2(.290-SHOULDER_X,SHOULDER_Z-.835)
def ease(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def arm_fit(x,y,z):
 s=1 if x>=0 else -1
 t=ease((1.210-z)/(1.210-1.104))
 a=t*DELTA
 dx=abs(x)-SHOULDER_X;dz=z-SHOULDER_Z
 return (s*(SHOULDER_X+cos(a)*dx-sin(a)*dz),y,SHOULDER_Z+sin(a)*dx+cos(a)*dz)
def foot_fit(x,y,z,shoe=False):
 a=1 if shoe else ease((.108-z)/(.108-.078))
 return (x,.006+(1-.20*a)*(y-.006),z)
def warp_piece(o,func):
 if o.type=='MESH':
  for v in o.data.vertices:v.co=func(*v.co)
  o.data.update()
 elif o.type=='CURVE':
  for s in o.data.splines:
   if s.type=='BEZIER':
    for p in s.bezier_points:
     c,l,r=tuple(p.co),tuple(p.handle_left),tuple(p.handle_right)
     p.co=func(*c);p.handle_left=func(*l);p.handle_right=func(*r)
   else:
    for p in s.points:
     a,b,c,w=p.co
     p.co=(*func(a,b,c),w)
for item in C.objects:
 n=item.name
 if n.startswith(('Blazer | cut sleeve','Blazer | cuff','Cuff ')):warp_piece(item,arm_fit)
 if n.startswith('Stocking'):warp_piece(item,foot_fit)
 if n.startswith(('Mary Jane ','L | ','R | ')):warp_piece(item,lambda *p:foot_fit(*p,shoe=True))

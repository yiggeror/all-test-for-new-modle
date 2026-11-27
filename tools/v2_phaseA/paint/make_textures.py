"""Original Suzu eyes and face paint. Layout anchors describe VRoid UVs, not its artwork."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
import json
from math import pi
import argparse
D=Path(__file__).resolve().parent
T=D/'texture'
T.mkdir(exist_ok=True)
# Separate, small coordinate profiles keep the new painting independent of base RGB/alpha images.
PROFILES={
 'PixivTwist':{'iris':((258,260.5,111.15,125.6),(766,260.5,111.15,125.6)),'face':(512,321,643),'white':(258,766,320),'type':'Twist'},
 'fem_vroid':{'iris':((258,260.5,110.6,125.2),(766,260.5,110.6,125.2)),'face':(512,358,615),'white':(259,758,320),'type':'N00'},
 'Base_Female':{'iris':((256,256.5,118,132.6),(768,256.5,118,132.6)),'face':(512,365,609),'white':(258,766,320),'type':'F00'},
 'AvatarSample_A':{'iris':((259.5,257.5,107,135),(763.5,257.5,107,135)),'face':(512,358,611),'white':(258,766,322),'type':'F00'}
}
def rgb(h):return np.array([int(h[i:i+2],16) for i in (0,2,4)],np.float32)/255
def sat(x):return np.clip(x,0,1)
def ga(x): return np.exp(-np.minimum(x*x,100))
def ss(a,b,x):
 f=sat((x-a)/(b-a))
 return f*f*(3-2*f)
def blend(x,y,a):return x[None,None,:]+(y-x)[None,None,:]*a[...,None] if x.ndim==1 else x*(1-a[...,None])+y*a[...,None]
def tint(A,h,alpha):return blend(A,rgb(h)[None,None,:],sat(alpha))
def oval(x,y,cx,cy,rx,ry,theta=0):
 c,s=np.cos(theta),np.sin(theta);u=c*(x-cx)+s*(y-cy);v=-s*(x-cx)+c*(y-cy)
 return np.sqrt((u/rx)**2+(v/ry)**2)
def feather(x,y,cx,cy,rx,ry,theta=0):return 1-ss(.93,1.015,oval(x,y,cx,cy,rx,ry,theta))
def faceted_star(x,y,cx,cy,w,h):
 # Four narrow, slightly convex tapered blades; sharp point ends at the same plane.
 ax=np.abs((x-cx)/w);ay=np.abs((y-cy)/h)
 sc=(ax**.53+ay**.53);return 1-ss(.983,1.025,sc)
def painted_iris(x,y):
 r=np.sqrt(x*x+y*y);a=np.arctan2(y,x)
 A=blend(rgb('331D68'),rgb('534478'),ss(-.88,.24,y))
 A=tint(A,'292058',.36*(1-ss(-.69,-.49,y+.10*np.cos(x*2.6))))
 A=tint(A,'806389',.49*ss(-.09,.41,y+.08*x))
 A=tint(A,'CFA37E',.90*ss(.12,.61,y-.08*x))
 A=tint(A,'F3BE80',.72*ss(.35,.74,y-.10*x))
 A=tint(A,'FFF8B7',.85*ga(oval(x,y,.049,.656,.47,.33))*(.54+.46*ss(.38,.48,y)))
 A=tint(A,'FFF3C3',.53*ga(oval(x,y,.006,.719,.26,.20)))
 # quiet bright lower rim, feathered iridescence in layered facets around lens
 cold=feather(x,y,.255,-.676,.38,.18,.284)
 A=tint(A,'7167AE',.37*cold)
 A=tint(A,'927FBE',.13*ga(oval(x,y,.30,-.65,.26,.115,.3)))
 curve=.42+.112*x*x+.046*np.sin(4.1*x-.1)
 d=ss(curve-.035,curve+.03,y)
 A=tint(A,'F6C794',.17*d*(1-ss(.73,.91,r))*(ga((x+.25)/.82)))
 # Fibres are light direction-dependent and deliberately not a uniform radial burst.
 phi=a+.034*np.sin(21*r)+.024*np.sin(9*a+13*r)
 sparse=(.5+.5*np.cos(39*phi+2.6*np.sin(13*a)-.7*np.sin(7*a)))**11
 dense=(.5+.5*np.sin(67*phi+2.3*np.cos(11*a)+3.2*r))**16
 lift=ss(.39,.56,r)*(1-ss(.87,.953,r))*(.29+.71*ss(-.1,.29,y))
 A=tint(A,'F9CCA2',lift*(.13*sparse+.082*dense)*(.7+.3*np.sin(17*a)))
 shade=((.5+.5*np.sin(21*phi+2.0*np.sin(13*a+.17)))**8)*lift
 A=tint(A,'593750',.09*shade)
 rim=ss(.877,.992,r)
 A=tint(A,'201633',.83*rim*(.83-.40*ss(.04,.71,y)))
 A=tint(A,'895547',.61*ss(.948,1.012,r)*ss(.43,.91,y))
 A=tint(A,'FDE29E',.36*ga((r-.889)/.040)*ss(.24,.58,y))
 # elliptical flared pupil; translucent lower edge opens onto the amber field
 pr=oval(x,y,-.028,-.017,.267,.382,-.075)
 A=tint(A,'2A1645',.95*(1-ss(.89,1.015,pr)))
 A=tint(A,'624369',.50*(1-ss(.75,.955,pr))*ss(.02,.35,y))
 A=tint(A,'331D68',.39*(1-ss(.86,.99,pr))*ga((x+.098)/.26)*ss(-.30,-.08,y))
 # restrained small facet flecks glint through the lower lens
 for fx,fy,sz,op in [(-.442,.492,.055,.75),(.42,.428,.061,.59),(.54,.27,.032,.57),
                     (-.525,.262,.026,.65),(-.646,.432,.027,.51),(.48,.583,.031,.63),
                     (.223,.695,.026,.72),(-.21,.658,.031,.57),(.673,.43,.020,.46)]:
  A=tint(A,'FFF3C1',op*feather(x,y,fx,fy,sz,sz*.79,fx))
 # distinct four-point gold star in upper outer iris; a smaller inner gold glint
 star=faceted_star(x,y,.487,-.342,.204,.245)
 soft=ga(oval(x,y,.487,-.343,.21,.19))
 A=tint(A,'BC82A4',.16*soft)
 A=tint(A,'EABD92',.96*star)
 A=tint(A,'FFF3BA',.94*faceted_star(x,y,.489,-.342,.099,.121))
 A=tint(A,'FFF5C7',.69*faceted_star(x,y,.021,.727,.110,.13))
 # Two white lacquered catches, placed identically in both eyes under the key.
 white=feather(x,y,-.380,-.469,.179,.137,-.32)
 dot=feather(x,y,-.151,-.333,.063,.065,-.12)
 A=tint(A,'DCDCF2',.63*ga(oval(x,y,-.37,-.458,.234,.186,-.32)))
 A=tint(A,'FFFDFE',white)
 A=tint(A,'FFFDFC',dot)
 # Deliberate anti-aliased alpha for the card edges; color extends into clear pixels.
 return np.dstack([A,1-ss(.994,1.008,r)])
def save(array,dst):
 Image.fromarray(np.uint8(np.clip(array,0,1)*255+.5)).save(dst,optimize=True)
def make_iris(cfg,out):
 # 2K-wide atlas in the source 2:1 layout. The face map is a full 2048².
 w,h=2048,1024
 a=np.zeros((h,w,4),np.float32)
 for cx,cy,rx,ry in cfg['iris']:
  i0,j0=int(2*(cx-rx-4)),int(2*(cy-ry-4));i1,j1=int(2*(cx+rx+4)),int(2*(cy+ry+4))
  x,y=np.meshgrid((np.arange(i0,i1)+.5)/2,(np.arange(j0,j1)+.5)/2)
  a[j0:j1,i0:i1]=painted_iris((x-cx)/rx,(y-cy)/ry)
 save(a,out/'eye_iris.png')
def px_grid(w,h,xo,yo):
 return np.meshgrid((np.arange(w,dtype=np.float32)+.5)*(xo/w),(np.arange(h,dtype=np.float32)+.5)*(yo/h))
def skin_values(cfg,eye_art=None):
 x,y=px_grid(2048,2048,1024,1024)
 cc=cfg['face'][1] if cfg['type']=='Twist' else 320
 cy=cfg['face'][2] if cfg['type']=='Twist' else 636
 # Smooth, primarily ivory portrait base. Intermittent face feature washes
 # follow the calibration of the UV face plate, not a projected render.
 a=blend(rgb('FDECDA'),rgb('F5D8C9'),.34*ss(390,991,y)*ss(184,487,np.abs(x-512)))
 a=tint(a,'FFF5E4',.24*ga(oval(x,y,520,333,317,280)))
 a=tint(a,'F5CBBB',.21*ss(758,951,y)*ga((x-512)/455))
 a=tint(a,'F1BAA8',.17*(ga(oval(x,y,117,62,104,65))+ga(oval(x,y,908,65,102,69))))
 # Peach over cheek apples, smaller cool contour within; gentle enough to
 # read close up without making uniform circles when the head turns.
 for sd,mid in [(-1,cc),(1,1024-cc)]:
  r=oval(x,y,mid,cy,112,73,sd*.17)
  a=tint(a,'F29EA0',.25*ga(r))
  a=tint(a,'FDB4A0',.23*ga(oval(x,y,mid-sd*16,cy+5,79,57,sd*.15)))
  a=tint(a,'EDB09C',.11*ga(oval(x,y,mid+sd*22,cy-16,79,42,sd*-.13)))
  # Fine warm brush hatching, broken and feathered rather than a sticker.
  for k,offset in enumerate((-36,-22,-9,4,17,31)):
   cx=mid+offset
   yp=cy-3+(offset/40)**2*10+sd*offset*.10
   a=tint(a,'D67E86',.109*ga(oval(x,y,cx,yp,1.9+(k%3)*.35,11.4+(k%2)*2.3,sd*.46)))
 # Tiniest bridge light and soft lip waterline. No black line is painted into
 # the neutral skin, so the UV survives the original mouth shape keys.
 a=tint(a,'F3B5A1',.17*ga(oval(x,y,511,685,39,42,.05)))
 a=tint(a,'FFF9EA',.38*ga(oval(x,y,521,682,9,12,.10)))
 a=tint(a,'E8A097',.26*ga(oval(x,y,512,762,74,10.2)))
 a=tint(a,'F7C1AA',.20*ga(oval(x,y,512,782,89,21.6)))
 a=tint(a,'FFF0DE',.35*ga(oval(x,y,510,786,43,6.2)))
 # The native lip UV lock is y=775; tint a soft smile arc in the skin itself.
 # Its brush width tapers at the corners and deforms with their shape keys.
 q=(x-512)/62.5;arc=776.1-8.6*q*q
 mid=ga((y-arc)/2.72)*(1-ss(.78,1.047,np.abs(q)))
 a=tint(a,'855653',.82*mid)
 a=tint(a,'F3A7A3',.23*ga((y-arc-4.2)/5.35)*(1-ss(.68,1.27,np.abs(q))))
 # Precisely the same pigment at the face/scalp sheet edge and neck.
 mask=1-ss(.711,.948,oval(x,y,512,516,514,514))
 a=a*mask[...,None]+rgb('FDECDA')[None,None,:]*(1-mask[...,None])
 # Paint only the concha islands, feathering back to the shared skin at their rims.
 for earx,eary,dr in [(100,52,1),(924,52,-1),(105,975,-1),(919,975,1)]:
  partial=ga(oval(x,y,earx,eary,39,28,dr*.36))
  a=tint(a,'E1AA9C',.19*partial)
  a=tint(a,'EFBCAC',.12*ga(oval(x,y,earx+dr*9,eary-5,23,15,-dr*.16)))
 # Local cartilage glaze. Each mark is a tapered cubic stroke in the small
 # auricle UV island. No sharp skin tone seam is created near its perimeter.
 ear_paths=[
     ([(62,105),(34,94),(26,56),(72,42)],'B57370',.41,2.8),
     ([(72,42),(99,32),(118,49),(122,65)],'B57572',.34,2.35),
     ([(79,44),(73,56),(83,83),(111,73)],'BF7E76',.33,2.14),
     ([(130,58),(124,34),(167,24),(176,42)],'C18B82',.27,2.08),
 ]
 cx=np.minimum(x,1024-x)
 # Compute only the small ear rectangles, not the full 2K image.
 for xs in [slice(46,378),slice(1670,2002)]:
  ys=slice(44,237);xx=cx[ys,xs];yy=y[ys,xs];data=a[ys,xs]
  for c,hue,alpha,thick in ear_paths:
   m=np.zeros_like(xx)
   for i in range(45):
    t=i/44;u=1-t
    px,py=tuple(u**3*k[0]+3*u*u*t*k[1]+3*u*t*t*k[2]+t**3*k[3] for k in zip(*c))
    width=thick*(.43+.57*np.sin(np.pi*t)**.62)
    pigment=ga(((xx-px)**2+(yy-py)**2)**.5/width)*(0.22+.78*np.sin(np.pi*t)**.87)
    np.maximum(m,pigment,out=m)
   data=tint(data,hue,alpha*m)
  a[ys,xs]=data
 if eye_art:
  palette={'wing':('352237',.976,.5),'upper':('342337',.937,.70),
           'crease':('996968',.63,1.1),'innerlower':('A4716D',.56,1.08)}
  for st in eye_art['strokes']:
   hue,opacity,soft=palette[st['kind']];xy=np.asarray(st['uv'],np.float64)*2048
   left,top=np.floor(xy.min(axis=0)).astype(int)-6;right,bottom=np.ceil(xy.max(axis=0)).astype(int)+6
   pad=Image.new('L',((right-left)*3,(bottom-top)*3))
   dr=ImageDraw.Draw(pad)
   dr.polygon([tuple(q) for q in (xy-[left,top])*3],fill=255)
   pad=pad.filter(ImageFilter.GaussianBlur(soft*3)).resize((right-left,bottom-top),Image.Resampling.LANCZOS)
   a[top:bottom,left:right]=tint(a[top:bottom,left:right],hue,opacity*np.asarray(pad,np.float32)/255)
 return a
def rounded_uv_coverage(polygons,w,h,soft=1.0):
 from scipy.ndimage import distance_transform_edt, gaussian_filter
 m=Image.new('1',(w,h));d=ImageDraw.Draw(m)
 for a in polygons:d.polygon([(x*w,y*h) for x,y in a],fill=1)
 p=np.asarray(m,dtype=bool)
 # Erode only a couple texels, so the smooth alpha boundary settles just
 # inside the original coarse polygon outline rather than fighting it.
 signed=distance_transform_edt(p)-distance_transform_edt(~p)
 q=gaussian_filter(signed,soft*2.9)
 return ss(1.02,2.98,q)

def make_other(cfg,out,body_atlas=None,eye_art=None):
 save(skin_values(cfg,eye_art),out/'face_skin.png')
 save(np.broadcast_to(rgb('FDECDA'),(8,8,3)),out/'scalp_skin.png')
 # Hybrid study torso and the licensed head share a UV-agnostic base pigment.
 # No donor skin or donor coverage image is mixed with the portrait artwork.
 save(np.broadcast_to(rgb('FDECDA'),(8,8,3)),out/'body_skin.png')
 x,y=px_grid(2048,1024,1024,512)
 cx=np.where(x<512,cfg['white'][0],cfg['white'][1]);t=(x-cx)/233.
 edge=.16*ss(.7,1.14,np.abs(t))
 r=ss(101,312,y-38*t*t+7*np.cos(t*pi))
 a=blend(rgb('C5B0BE'),rgb('FFFBF4'),.94*r)
 a=tint(a,'D7CBD6',edge+.08*(1-ss(299,421,y))*ss(.46,.97,np.abs(t)))
 a=tint(a,'F5E3E0',.23*ss(328,455,y)*ss(.60,1.06,np.abs(t)))
 save(a,out/'eye_white.png')
 # All masks are self-authored. The Twist has genuine trimmed brow/line
 # geometry already; we paint inside those UV islands, not a square mesh mask.
 x,y=px_grid(2048,512,1024,256);mx=np.minimum(x,1024-x)
 a=blend(rgb('382338'),rgb('73505B'),.60*ss(80,145,y)+.17*ga((mx-105)/56))
 a=tint(a,'221A32',.55*(1-ss(87,111,y))*(1-ss(315,420,mx)))
 a=tint(a,'4A344F',.37*ga((y-(88+.00088*(mx-278)**2))/4.4)*ga((mx-298)/113))
 # Separate lid fold lives in the top island. A neutral mauve skin tone softly
 # ramps to retain the fold contour without the old unpainted bright polygon.
 crease=1-ss(69,72,y)
 b=blend(rgb('A06A71'),rgb('CF9890'),ss(32,57,y))
 a=blend(a,b,crease)
 if cfg['type']=='F00':
  # For mesh generations with broader alpha cards, independent shaped cutouts.
  arch=95.0+.00045*(mx-286.)**2
  ww=8.8*(1-.46*ss(320,470,mx))+5.6*(1-ss(118,274,mx))
  main=(1-ss(.87,1.04,np.abs((y-arch)/ww)))*ss(98,118,mx)*(1-ss(473,491,mx))
  fold=(1-ss(.62,1.07,np.abs((y-(52.7+.0011*(mx-361.)**2))/2.45)))*ss(299,318,mx)*(1-ss(424,442,mx))
  a=np.dstack([a,np.maximum(main,fold)])
 if eye_art and cfg['type']=='Twist':a=np.dstack([a,rounded_uv_coverage(eye_art['main_lash'],2048,512,1.06)])
 save(a,out/'eye_line.png')
 a=blend(rgb('755C70'),rgb('AC8892'),ss(112,159,y)*.70+.17*(1-ss(138,272,mx)))
 a=tint(a,'574454',.30*ga((y-(128.4+.00043*(mx-304)**2))/3.8))
 if cfg['type']=='F00':
  arch=130.6+.000483*(mx-306)**2
  a=np.dstack([a,(1-ss(.74,1.04,np.abs((y-arch)/(5.3-2.08*ss(318,423,mx)))))*ss(87,116,mx)*(1-ss(410,424,mx))])
 if eye_art and cfg['type']=='Twist':a=np.dstack([a,rounded_uv_coverage(eye_art['brow'],2048,512,.7)])
 save(a,out/'brow.png')
 x,y=px_grid(2048,2048,512,512)
 # Native mouth atlas: enamel quadrant, interior contours and tongue.
 a=blend(rgb('9E515E'),rgb('633044'),ss(245,513,y))
 a=tint(a,'DA8C86',.63*ga(oval(x,y,293,201,100,186)))
 a=tint(a,'C07D76',.52*ga(oval(x,y,463,136,117,117,.42)))
 a=tint(a,'E09C99',.45*ga(oval(x,y,244,243,145,78,.06)))
 tooth=1-ss(251,257,x)
 tooth*=1-ss(252,257,y)
 a=blend(a,blend(rgb('FFF9F4'),rgb('DFCED9'),.22*ss(89,228,y)+.13*np.cos(y/13)**6),tooth)
 save(a,out/'mouth.png')
 save(np.zeros((16,16,4),np.float32),out/'spare_alpha.png')
if __name__=='__main__':
 pr=argparse.ArgumentParser()
 pr.add_argument('profile',choices=PROFILES);pr.add_argument('--iris-only',action='store_true');pr.add_argument('--licensed-body-atlas',type=Path);pr.add_argument('--eye-art',type=Path);pr.add_argument('--output',type=Path);pr.add_argument('--face-only',action='store_true')
 args=pr.parse_args();out=args.output or T/args.profile;out.mkdir(exist_ok=True,parents=True)
 art=json.loads(args.eye_art.read_text()) if args.eye_art else None
 if args.face_only: save(skin_values(PROFILES[args.profile],art),out/'face_skin.png')
 else:
  make_iris(PROFILES[args.profile],out)
  if not args.iris_only:make_other(PROFILES[args.profile],out,args.licensed_body_atlas,art)

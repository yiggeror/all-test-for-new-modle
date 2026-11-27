# The bodice has separate pattern pieces around two curved armscyes. The lapel
# panels are turned over the shell and end in angular notches (not drawn lines).
from functools import lru_cache
J=[
 (1.050,.119,.079,.074,.002,.0432),(1.061,.119,.079,.074,.002,.0435),
 (1.082,.119,.079,.075,.002,.0435),(1.105,.120,.082,.077,.003,.0440),
 (1.125,.123,.087,.078,.004,.0440),(1.144,.127,.091,.079,.005,.0433),
 (1.160,.130,.093,.078,.005,.0425),(1.179,.132,.091,.077,.005,.0421),
 (1.199,.133,.084,.075,.006,.0418),(1.219,.138,.077,.073,.006,.0420),
 (1.235,.142,.070,.069,.007,.0440),(1.246,.141,.064,.066,.008,.0460),
 (1.254,.136,.060,.064,.009,.0470),(1.261,.123,.055,.060,.009,.0465),
 (1.269,.098,.051,.056,.010,.0450),(1.277,.075,.047,.052,.010,.0428),
 (1.284,.055,.042,.047,.011,.0400),(1.289,.044,.038,.043,.011,.0380)]
@lru_cache(maxsize=1024)
def jt(z):
 rx,rf,rb,y,opening=tupinterp(J,z)
 return rx,rf,rb,y,opening*(1+.155*ga(z-1.126,.121))
def shell(a,z,off=0):
 rx,rf,rb,cy,ed=jt(z);cs=cos(a);sn=sin(a)
 rd=rf if cs>0 else (rb+.0042+.0040*ga(z-1.096,.064))
 # Ease through dart and waist rather than moulding clothing to the naked figure.
 waistfold=.0016*sin(4*a+.4)*ga(z-1.085,.051)+.0014*cos(6*a)*ga(z-1.131,.055)
 bridge=.0087*ga(z-1.203,.034)*ga(abs(sn)-.93,.14)
 return ((rx+off+waistfold+bridge)*sn,cy-(rd+off+waistfold*.6+bridge*1.24)*cs,z)
def fplane(x,z,extra=0):
 # Invert the same eased pattern used by the outer mesh, including the
 # shoulder bridge. Lapel and brooch never intersect the fitted shell.
 lo=-pi/2;hi=pi/2
 for _ in range(22):
  a=(lo+hi)*.5;px,py,_=shell(a,z)
  if px<x:lo=a
  else:hi=a
 return (x,py-extra,z)
def cut(z):
 if not 1.165<z<1.256:return 0
 t=(z-1.165)/.091
 return .238*(max(0,4*t*(1-t))**.58)*(.90+.16*t)
zs=sorted(set([1.050,1.0509,1.053,1.162,1.1628,1.164,1.261,1.263,1.2648,1.265,1.287,1.289]+[r[0] for r in J]+[1.050+i*.004 for i in range(60) if 1.050+i*.004<=1.289]))
zs=sorted(set(round(v,7) for v in zs))
for panel in ['front L','back','front R']:
 rows=[]
 for z in zs:
  rx,rf,rb,cy,ed=jt(z);a0=math.asin(min(.996,ed/rx));g=cut(z)
  begin,end=(a0,pi/2-g) if panel=='front L' else ((pi/2+g,3*pi/2-g) if panel=='back' else (3*pi/2+g,2*pi-a0))
  # Give a soft V edge toward the side seam, as in a cropped tailored jacket.
  row=[]
  for i in range(57 if panel=='back' else 30):
   a=begin+(end-begin)*i/(56 if panel=='back' else 29)
   x,y,zz=shell(a,z)
   zz+= (.0024*sin(2*a)**2+.0025*(1-cos(a))*.5)*exp(-((z-1.05)/.025)**2)
   row.append((x,y,zz))
  rows.append(row)
 o=grid('Blazer | shaped '+panel+' pattern',rows,main);solid(o,.0025)
for s in [-1,1]:
 # edge binder runs around jacket hem and up to the lapel hinge
 rr=[fplane(s*jt(z)[4],z,.0017) for z in [1.122,1.109,1.093,1.074,1.055,1.0515]]
 line('Blazer | bound opening '+('L' if s==1 else 'R'),rr,.00140,trim)
b0=math.asin(jt(1.0515)[4]/jt(1.0515)[0]);bs=[b0+(2*pi-2*b0)*i/145 for i in range(146)]
rr=[]
for a in bs:
 x,y,z=shell(a,1.052,.0011);rr.append((x,y,z+.0024*sin(2*a)**2+.00125*(1-cos(a))))
line('Blazer | fine hem piping',rr,.00145,trim)
# Three-dimensional shaped notched lapels: close-set support bands retain the
# tailor's corner at the notch instead of a rounded, cartoon collar.
lap=[(1.109,.0438,.0445),(1.113,.0438,.0462),(1.144,.0432,.0606),
 (1.167,.0420,.0733),(1.195,.0418,.0890),(1.2050,.0421,.0955),
 (1.2060,.0421,.0961),(1.2070,.0422,.0952),(1.2153,.0423,.0800),
 (1.2160,.0423,.0793),(1.2168,.0424,.0797),(1.228,.0431,.0956),
 (1.240,.0441,.1075),(1.2524,.0465,.1159),(1.2541,.0467,.1153),
 (1.258,.0468,.108),(1.267,.0454,.090),(1.275,.0428,.069),
 (1.2795,.0412,.057),(1.2815,.0405,.051)]
def lapt(s,z,u):
 xi,xo=tupinterp(lap,z)
 openingExtra=tupinterp(J,z)[4]*.155*ga(z-1.126,.121)
 lower=ga(z-1.207,.058)
 # Wide gorge, gentle slope at the inside edge; outer collar remains seated at the shoulder.
 xi+=openingExtra
 xo+=openingExtra+.0083*lower*max(0,min(1,(z-1.113)/.048))*max(0,min(1,(1.284-z)/.030))
 x=s*(xi+(xo-xi)*u)
 dip=.00242+.00208*sin(pi*u)*(.55+.45*ga(z-1.22,.06))+.00157*(1-u)
 return fplane(x,z,dip)
lz=sorted(set([r[0] for r in lap]+[1.110+i*.003 for i in range(58) if 1.110+i*.003<1.2815]))
lz=sorted(set(round(v,7) for v in lz))
for s in [-1,1]:
 lab='L' if s==1 else 'R'
 rows=[[lapt(s,z,u) for u in [0,.024,.071,.16,.28,.44,.62,.79,.91,.972,1]] for z in lz]
 solid(grid('Blazer | notched lapel '+lab,rows,main),.0021)
 # Piping follows outside except where the notched collar tucks into the shoulder.
 ar=[Vector(lapt(s,z,.96))+Vector((0,-.0010,0)) for z in lz if z<=1.2541]
 line('Lapel '+lab+' | notched piping',ar,.00145,trim)
 # Fine recessed seam just inside piping: genuine geometry without suggesting a graphic.
 ar=[Vector(lapt(s,z,.89))+Vector((0,-.0009,0)) for z in lz if 1.130<z<=1.2524]
 line('Lapel '+lab+' | understitch',ar,.00042,main)
 # Princess seam on back curve, discreet and visible on a turntable.
 ds=[]
 for z in [1.057+i*.0044 for i in range(46)]:
  a=pi-(.59+.20*ga(z-1.23,.05));a= a if s==1 else 2*pi-a
  ds.append(shell(a,z,.0007))
 line('Blazer | back shaped seam '+lab,ds,.00060,main)
# Sleeves are lofted along the arm, with elbow darts and a bias-gather before
# the cuffs. Cross-section is perpendicular to each arm, not horizontal.
S=[
 (.8345,.2900,-.008,.0240,.0240,.40),(.842,.287,-.007,.0245,.0243,.40),
 (.851,.283,-.007,.0260,.0256,.41),(.858,.2802,-.006,.0275,.0260,.41),
 (.866,.277,-.0057,.0308,.0295,.42),(.875,.273,-.0040,.0395,.0366,.41),
 (.889,.268,-.0030,.0468,.0414,.41),(.910,.259,-.0010,.0476,.0413,.42),
 (.932,.250,.0009,.0444,.0391,.41),(.963,.237,.0035,.0402,.0372,.41),
 (.991,.225,.006,.0354,.0357,.41),(1.018,.213,.009,.0314,.0337,.39),
 (1.044,.202,.012,.0300,.0325,.39),(1.071,.192,.012,.032,.033,.35),
 (1.106,.178,.010,.034,.0366,.35),(1.139,.167,.008,.0367,.0402,.33),
 (1.170,.156,.007,.038,.043,.31),(1.196,.147,.006,.039,.044,.29),
 (1.218,.139,.006,.039,.0450,.26),(1.235,.132,.007,.034,.0435,.22),
 (1.246,.127,.008,.028,.036,.16),(1.253,.122,.008,.020,.028,.10),
 (1.257,.119,.008,.011,.017,.05),(1.258,.118,.008,.004,.0063,.01)]
def sleev(s,z,a,off=0,iscuff=False):
 cx,cy,rx,ry,sl=tupinterp(S,z);c=cos(a);bb=sin(a)
 # Three quiet diagonal tension lines across inside elbow, radiating from bend.
 inside=max(0,-.60*c-.62*bb+.13)
 wr= -(.00155*ga(z-(1.017+.017*c+.007*bb+.003*s),.0091)
       +.00165*ga(z-(1.043+.011*c-.011*bb-.001*s),.0102)
       -.00104*ga(z-(1.031+.010*c-.002*bb),.0088))*inside
 # Broad triangular fabric ridges on lower pouf, tapering into four gathers.
 wr+=(.0040*cos(5*a+.4+23*(z-.884))+.00145*cos(7*a-.8))*ga(z-.882,.025)
 wr+=.0033*ga(z-.912,.05)*max(0,-c)**1.6
 wr+=.00130*cos(3*a+.7)*ga(z-.930,.059)
 if iscuff:wr=0
 R=rx+wr+off;D0=ry+wr*.89+off
 return (s*(cx+c*R/sqrt(1+sl*sl)),cy+bb*D0,z+c*R*sl/sqrt(1+sl*sl))
As=sample(60)
for s in [-1,1]:
 lab='L' if s==1 else 'R'
 vv=sorted(set([v[0] for v in S if v[0]>=.859]+[.860+i*.004 for i in range(100) if .86+i*.004<1.258]))
 vv=sorted(set(round(v,7) for v in vv))
 o=grid('Blazer | cut sleeve '+lab,[[sleev(s,z,a) for a in As] for z in vv],main,True,s==-1);solid(o,.0020)
 cs=[(.8348,.0014),(.836,.0029),(.840,.0030),(.848,.0032),(.857,.0033),(.862,.0037),(.864,.0027)]
 o=grid('Blazer | cuff '+lab,[[sleev(s,z,a,q,True) for a in As] for z,q in cs],bowmat,True,s==-1);solid(o,.0018)
 for z,rad,mt in [(.8593,.0011,trim),(.8368,.00055,main)]:
  line('Cuff '+lab+' | bound edge', [sleev(s,z,a,.0042,True) for a in As],rad,mt,True)
# Fitted shirt block, narrow turned placket, buttonholes / buttons.
def shirt(a,z,off=0):
 rx,rf,rb,cy=body.smooth_profile(body.TRUNK,z)
 sn,cs=sin(a),cos(a);ease=.0042+.0038*ga(z-1.084,.055)
 wrinkle=.0017*cos(9*a-.44)*ga(z-1.084,.040)+.0015*sin(16*a+12*z)*ga(z-1.072,.031)
 return ((rx+ease+off+wrinkle)*sn,cy-((rf if cs>0 else rb)+ease+off+wrinkle)*cs,z)
def shirtfront(x,z,off=0):
 rx=body.smooth_profile(body.TRUNK,z)[0];a=math.asin(min(.995,max(-.995,x/(rx+.0052))))
 return (x,shirt(a,z)[1]-off,z)
zz=sorted(set([1.041+i*.004 for i in range(64) if 1.041+i*.004<1.295]+[1.295,1.136,1.138,1.268,1.271]))
def shirt_armscyes(z):
 t=(z-1.136)/.135
 return .948*max(0,4*t*(1-t))**.57
# Cotton is cut into an open side armscye below the jacket, with no hidden
# side cylinder crossing the humeral saddle at the shoulder.
for sgn,lbl in [(1,'front'),(-1,'back')]:
 rows=[]
 for z in zz:
  g=shirt_armscyes(z);a0=-pi/2+g;a1=pi/2-g
  rows.append([shirt((0 if sgn==1 else pi)+a0+(a1-a0)*i/52,z) for i in range(53)])
 o=grid('Blouse | fitted cotton '+lbl+' bodice',rows,inner);solid(o,.00135)
zz=[1.043+i*.0037 for i in range(68) if 1.043+i*.0037<1.285]+[1.285]
o=grid('Blouse | double folded placket',[[shirtfront(x,z,.00115) for x in [-.0070,-.0064,-.004,0,.004,.0064,.0070]] for z in zz],inner);solid(o,.0011)
for q in [-1,1]:line('Blouse | placket stitch',[shirtfront(q*.006,z,.0018) for z in zz],.00036,trim)
def button(name,xc,yc,zc,rad=.0041,m=trim):
 # sewing holes are true 3D recesses behind the slightly raised circular rim
 A=sample(36);rows=[]
 for r,yy in [(rad*.70,.0002),(rad,-.00035),(rad*1.04,-.0012),(rad*.94,-.0018),(rad*.75,-.0022),(rad*.01,-.0022)]:
  rows.append([(xc+r*cos(a),yc+yy,zc+r*sin(a)) for a in A])
 o=grid(name,rows,m,True)
 for t in [-1,1]:
  p=[(xc+t*.0011+rad*.14*cos(a),yc-.00225,zc+rad*.14*sin(a)) for a in A]
  obj(name+' | eye',p,[tuple(range(len(A)))],shadow,False)
for j,z in enumerate([1.076,1.112,1.148,1.184,1.220]):
 x,y,z=shirtfront(0,z,.00185);button('Blouse | button '+str(j+1),x,y,z)
def collar_clear(x,y,z):
 rx,rfront,rback,cy=body.smooth_profile(body.TRUNK,z)
 r=math.hypot(x,y-cy)
 if r<1e-5:return (x,y,z)
 dy=y-cy
 rf=rfront if dy<0 else rback
 k=1.045/math.hypot(x/rx,dy/rf)
 k+=(.0032*ga(z-1.291,.040))/r
 of=(k-1)*r
 clear=.5*(of+math.sqrt(of*of+0.00000048))/r+1
 return (clear*x,cy+clear*dy,z)
# Cotton turnover collar; front point has been cut lower than roll at the throat.
for s in [-1,1]:
 ll=[i*pi/48 for i in range(49)];rows=[]
 for u in [0,.025,.10,.24,.40,.58,.78,.93,.98,1]:
  row=[]
  for a in ll:
   # shortest at throat split, long triangular point at each front quarter
   neck=.0375+.001*cos(a)
   drop=(.012+ .014*max(0,cos(a))+.020*ga(a-.77,.32))*u
   z=1.294-drop-.002*(1-cos(a))*u
   rx=neck+(.0245+.004*max(0,cos(a)))*u;fr=.034+(.027+.007*cos(a))*u
   aa=a+.040*(1-u)+.03*u
   x=s*rx*sin(aa);y=.010-fr*cos(aa)-.002*sin(pi*u)*max(0,cos(aa))
   row.append(collar_clear(x,y,z))
  rows.append(row)
 solid(grid('Blouse | pointed collar '+('L' if s==1 else 'R'),rows,inner),.0019)

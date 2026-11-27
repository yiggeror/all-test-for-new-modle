"""Closely fitted elliptical waistband, asymmetric knife-pleat shell, cotton petticoat."""
from bisect import bisect_right
NPLEAT=13
# Relative cut lengths around the ring, centered so the front reads as six broad panels.
CUTS=[.94,1.17,.94,1.12,.86,1.06,.99,1.06,.84,1.14,.91,1.05,1.07]
CUTS=[c*2*pi/sum(CUTS) for c in CUTS]
origins=[-.51*CUTS[0]]
for q in CUTS:origins.append(origins[-1]+q)
# Face of folded wool → fold nose → short reverse foot → return behind next face.
crease=[(.024,-.57),(.054,-.52),(.079,-.37),(.101,-.185),(.121,.025),
        (.147,.089),(.19,.116),(.34,.133),(.56,.168),(.76,.184),
        (.90,.252),(.957,.308),(.988,.275),(1.006,.11),(.981,-.256),
        (.915,-.637),(.895,-.808),(.922,-.748),(.975,-.625)]
PL=[.0004,-.0019,.0016,-.0021,.0037,.0012,-.0007,.0013,-.0012,.0011,-.0030,-.0011,.0018]
pleat_samples=[(n,p,q) for n in range(NPLEAT) for p,q in crease]
sk_t=1.014;sk_h=.267
# Graduated radius table: grazing the hip at the top, accelerating outward into
# a soft bell at the bottom. Back depth follows the fitted seat, not front symmetry.
DRAPE=[
 (0,.1030,.0715,.0744,.0020),(.056,.1070,.0752,.0788,.0030),
 (.145,.1167,.0826,.0895,.0048),(.246,.1288,.0938,.1035,.0058),
 (.368,.1470,.1039,.1158,.0078),(.49,.1640,.1150,.1263,.0088),
 (.63,.1844,.1278,.1385,.0094),(.75,.2048,.1399,.1498,.0102),
 (.88,.2238,.1512,.1626,.0103),(1,.2428,.1638,.1759,.0097),
 (1.15,.268,.1795,.1912,.0101)]
def drop_profile(z):
 u=(sk_t-z)/sk_h
 rx,rf,rb,cy=tupinterp(DRAPE,u)
 s=max(0,min(1,u));f=s*s*(3-2*s)
 return rx+.0265*f**1.4,rf+.0078*f**1.36,rb+.0098*f**1.36,cy
def outer_pt(u,n,p,q,out=0.0):
 base=origins[n]+p*CUTS[n]
 a=base+(.053*sin(2*base+.4)+.027*sin(4*base-.64)+.016*sin(7*base+.5))*u**1.21
 # Short scallop along each hem panel, subtle fold-to-fold difference, and
 # the stepped height of a fabric return (scallops don't all share a level).
 t=max(0,min(1,p));face_arc=(4*t*(1-t))**.8
 hem=.7522 + .0065*(1-cos(2*a-.18))-.0033*cos(a-.26)+.0027*sin(3*a+.3)+.0017*sin(6*a-.65)
 hem+=PL[n]-.0035*face_arc+.0045*max(0,(-q-.23)/.57)
 z=sk_t+(hem-sk_t)*u
 rx,rf,rb,y0=drop_profile(z)
 b=cos(a);c=sin(a)
 dr=(.0010+.0187*u**.87)*(1+.13*sin(2.27*n+.55)+.061*cos(3.7*n))
 # Directional bow of each panel across the pleat face. Slack varies by panel.
 dr2=(.0017*sin(3*a+.2)+.0015*sin(5*a+.65))*u*u
 dr2+=.0048*face_arc*max(0,sin(pi*u))*(.78+.34*sin(n*1.23+.7))*max(0,1+q)
 dr2+=.003*ga(t-(.42+.12*sin(n*1.9)+.11*u),.142)*ga(u-(.43+.18*cos(n*1.67)),.24)
 h=dr2+dr*q+out
 return ((rx+h)*c,y0-((rf if b>=0 else rb)+h)*b,z)
# Work the narrow decorative band and turned rim directly into the top fabric
# so that a second nearly co-planar cloth never appears in the light.
U_ROWS=[0,.008,.017,.04,.075,.12,.18,.25,.34,.43,.53,.64,.75,.84,.91,
        .919,.923,.927,.931,.940,.944,.949,.955,.969,.980,.985,.991,.996,1.]
def selvedge(u):
 gold=.00132*(ga(u-.936,.013)**2)
 roll=.00106*ga(u-.994,.008)
 return gold+roll
rows=[[outer_pt(u,n,p,q,selvedge(u)) for n,p,q in pleat_samples] for u in U_ROWS]
o=grid('Skirt | 13 folded and flared panels',rows,main,True,True)
o.data.materials.append(trim);o.data.materials.append(shadow)
for poly in o.data.polygons:
 j=poly.index//len(pleat_samples);u=.5*(U_ROWS[j]+U_ROWS[j+1])
 if .925<=u<=.946:poly.material_index=1
 elif .989<u:poly.material_index=2
solid(o,.00135).modifiers[-1].use_even_offset=False
# Independent petticoat: lined at the waist, unstructured cotton below. The cloth
# is cut from individually gathered lengths at the flounce seam, not a sine wave.
fw=[.92,.69,1.27,.77,1.09,.97,1.11,.75,.91,1.41,.70,1.02,1.10,.88,.78,1.17,
    .77,1.19,1.40,.73,.94,.63,1.19,1.00,.85,1.33,.70,1.08,.90,.89,1.39,.75,.88,1.11]
fa=[.77,.86,.61,1.37,.92,.66,1.24,.88,1.20,.53,.90,1.20,.71,.94,.65,1.16,1.31,
    .57,1.01,.83,1.25,.7,1.05,.85,1.25,.55,.67,.72,.95,1.05,.64,1.21,.87,.89]
N=len(fw);fwidths=[q*2*pi/sum(fw) for q in fw]
fstarts=[-.085]
for w in fwidths:fstarts.append(fstarts[-1]+w)
fractions=[0,.046,.10,.166,.238,.316,.394,.462,.536,.609,.684,.76,.834,.913,.966]
def gather_point(u,n,t):
 a0=fstarts[n]+t*fwidths[n]
 offset=u**2*(.019*sin(3*a0+.7)+.014*cos(5*a0-.8))
 a=a0+offset
 # The flounce has a slim fold valley at the seam intersection, unfolding
 # into assorted softer panels with different fold apex locations.
 crest=.32+.16*(.5+.5*sin(n*1.096+.83))
 p=sin(pi*t)**1.015
 wpr= (p**(.70+ .57*(.5+.5*cos(n*.93))) - .47*ga(t-(crest+.26),.122)*p) * fa[n]
 s=max(0,min(1,(u-.52)/.48));b=cos(a)
 slack=.0043*sin(3*a+.88)+.0031*sin(5*a-1.27)+.0012*cos(9*a+1.2)
 h=.7244-.0018*cos(a)+.0033*(1-cos(2*a+.15))+.0034*sin(3*a+.38)+.0034*cos(5*a+.84)
 h+=s*(.0055*wpr-.0038+.0013*sin(n*.88)*p)
 z=1.008+(h-1.008)*u
 rx,rf,rb,y0=drop_profile(z)
 set_u=min(1,max(0,(sk_t-z)/sk_h))
 # Stay beneath the innermost folded wool return. Cotton softens past its
 # seam but only broadens prominently once it passes the wool hem.
 clearance=.0070+.0223*(set_u**.9)
 soft=max(0,min(1,(.752-z)/.032))
 flare=.0087*soft**1.2
 v=((.0015*s+.0053*s**1.3+.0044*soft**1.45)*(wpr-.35)+s*s*slack)+flare
 return ((rx-clearance+v)*sin(a),y0-((rf if b>=0 else rb)-clearance+v)*b,z)
F=[(n,t) for n in range(N) for t in fractions]
o=grid('Petticoat | cotton flounce with irregular gathers',
 [[gather_point(u,n,t) for n,t in F] for u in [0,.018,.06,.14,.22,.33,.45,.55,.63,.69,.75,.80,.85,.89,.92,.952,.975,.989,1]],
 inner,True,True)
solid(o,.0012).modifiers[-1].use_even_offset=False
line('Petticoat | turned narrow lower hem',[gather_point(1,n,t) for n,t in F],.00084,inner,True)
# Low scooped front waist binding; taper over the true waist rather than
# an upright cylinder. Profile leaves real garment clearance over the torso.
A=sample(108)
BELT=[
 (1.002,.1032,.0702,.0745,.0039),(1.005,.1054,.0711,.0753,.0036),(1.009,.1062,.0716,.0756,.0030),
 (1.014,.1054,.0700,.0735,.0030),(1.019,.1024,.0650,.0691,.0031),
 (1.031,.1000,.0618,.0662,.0031),(1.043,.1006,.0626,.0658,.0031),
 (1.050,.1017,.0639,.0668,.0030),(1.053,.1018,.0646,.0671,.0030),
 (1.055,.1017,.0645,.0668,.0030)]
def belt(z,a,off=0):
 rx,p,q,y0=tupinterp(BELT,z);b=cos(a)
 xc=(.0004*sin(3*a)+.0032*max(0,.5-abs(b))**1.65)
 return ((rx+off+xc)*sin(a),y0-((p if b>=0 else q)+off)*b,z-.00265*b-.0008*cos(2*a+.3))
rr=[[belt(z,a) for a in A] for z in sorted({r[0] for r in BELT}|{1.003+i*.002 for i in range(26)})]
o=grid('Waist | fitted high-rise band',rr,main,True);solid(o,.00185)
for z in [1.0070,1.052]:
 line('Waist | stitch channel',[belt(z,a,.0009) for a in A],.00062,bowmat,True)

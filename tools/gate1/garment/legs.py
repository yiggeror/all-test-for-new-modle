import importlib.util
def loadmod(name,file):
 spec=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
body=loadmod('suzufit',MODULE_DIR/'fit_profile.py')
leg_point=body.leg_point
def clipped01(t):return max(0,min(1,t))
def knitsurface(s,z,a,add=.0021):
 add+=.00265*ga(z-.0795,.013)*max(.18,-sin(a)) + .0037*ga(z-.0485,.012)*max(0,-sin(a))**2
 if z>=.082:return leg_point(z,a,s,add)
 # Sock last follows the exact foot that is placed in the shoe, including
 # asymmetric forefoot width. No exposed patches across heel or strap opening.
 FT=[(.0249,.070,-.054,.0295,.087,.091),(.026,.070,-.054,.030,.088,.092),
     (.028,.070,-.054,.032,.092,.093),(.032,.070,-.049,.034,.099,.090),
     (.036,.070,-.044,.034,.094,.082),(.043,.070,-.034,.034,.083,.075),
     (.049,.069,-.026,.032,.076,.069),(.052,.069,-.021,.031,.070,.065),
     (.061,.068,-.011,.0285,.058,.0555),(.072,.068,.001,.0265,.043,.041),
     (.078,.068,.004,.026,.034,.035),(.082,.068,.006,.0255,.029,.031)]
 x,y,rx,rf,rb=body.smooth_profile(FT,z);c,b=cos(a),sin(a)
 def pw(q,e):return math.copysign(abs(q)**e,q)
 width=1+.055*max(-b,0)**.7-.12*max(b,0)
 xx=x+(rx+add)*pw(c,.92)*width+.0014*max(-b,0)**2
 yy=y+((rf if b<0 else rb)+add)*pw(b,.91)
 return (s*xx,yy,z)
def shoe_xform(s,x,y,z):
 return (s*(.068+x-.022*min(y,0)),y,z)
def clear_last(s,world,pad=.0021):
 # A 2-D clearance pass on smooth sections, rather than a discontinuous height
 # ray: each point moves outward only where the stocking's contour requires it.
 wx,y,z=world
 if z<.025:return world
 p0=knitsurface(1,z,0,.00215);p1=knitsurface(1,z,pi,.00215)
 cx=(p0[0]+p1[0])/2;cy=p0[1];x=s*wx;dx=x-cx;dy=y-cy;r=math.hypot(dx,dy)
 if r<.0005:return world
 target=math.atan2(dy,dx)%(2*pi);lo=0.;hi=2*pi
 for _ in range(15):
  a=(lo+hi)/2;xx,yy,_=knitsurface(1,z,a,.00215)
  if math.atan2(yy-cy,xx-cx)%(2*pi)<target:lo=a
  else:hi=a
 rr=math.hypot(xx-cx,yy-cy)+pad
 r2=.5*(r+rr+math.sqrt((r-rr)**2+.0015**2))
 return (s*(cx+dx*r2/r),cy+dy*r2/r,z)
Aleg=sample(60)
for s,top in [(1,.640),(-1,.610)]:
 side='L' if s==1 else 'R'
 zs=sorted(set([.0249,.026,.028,.032,.036,.043,.049,.052,.061,.072,.078,.080,.082,.086]+[r[0] for r in body.LEG if .08<=r[0]<top]+[top-.019,top-.012,top-.006,top-.0025,top]))
 o=grid('Stocking '+side+' | fitted knit over knee and foot', [[knitsurface(s,z,a,.00225 if z>top-.015 else .0019) for a in Aleg] for z in zs],stocking,True,s==-1)
 solid(o,.0010)
 solid(grid('Stocking '+side+' | turned welt',[[knitsurface(s,z,a,q) for a in Aleg] for z,q in [(top-.018,.0026),(top-.015,.00305),(top-.006,.0033),(top-.002,.0037),(top,.00275)]],main,True,s==-1),.0008)
 solid(grid('Stocking '+side+' | narrow braid',[[knitsurface(s,z,a,.00357) for a in Aleg] for z in [top-.0140,top-.0107]],trim,True,s==-1),.0007)
# Right‐only garter and front vertical keeper.
s=-1;ag=-pi/2+.09
zs=[(.658,.0028),(.6592,.0041),(.662,.00425),(.668,.00425),(.6715,.00425),(.6730,.0028)]
o=grid('Right garter | single fitted upper band',[[leg_point(z,a,s,r) for a in Aleg] for z,r in zs],bowmat,True,True);solid(o,.001)
rows=[]
for z in [.609,.611,.619,.636,.654,.665]:
 rows.append([leg_point(z,ag+d,s,.0051+.0011*max(0,1-(d/.109)**2)) for d in [-.109,-.085,-.050,0,.050,.085,.109]])
solid(grid('Right garter | vertical suspender ribbon',rows,bowmat),.0014)
pc=Vector(leg_point(.665,ag,s,.0051));pc.y-=.0045
starsolid('Right garter | five-point clasp',pc,.0143,.0146,.0052)
# The two shoe uppers are leather-cut annular surfaces over independent soles, with
# a genuine topline opening, instep strap, rectangular buckle and capped block heel.
outer=[(0,-.173),(.018,-.1717),(.0292,-.1661),(.0372,-.1583),(.0427,-.1468),(.0450,-.1175),(.0418,-.079),(.0365,-.050),(.0338,-.025),(.0348,-.001),(.036,.017),(.035,.038),(.028,.052),(.014,.057),(0,.058),(-.019,.055),(-.031,.046),(-.0345,.032),(-.035,.014),(-.032,-.016),(-.033,-.044),(-.0385,-.075),(-.0428,-.112),(-.0443,-.135),(-.0413,-.150),(-.0323,-.1635),(-.018,-.1717)]
# Corresponding landmarks of the low-cut topline; front marks the curved vamp.
opening=[(0,-.076),(.012,-.074),(.021,-.068),(.028,-.058),(.0303,-.049),(.0315,-.042),(.032,-.033),(.0317,-.021),(.0304,-.010),(.0296,.002),(.0297,.013),(.0285,.028),(.0226,.037),(.0118,.042),(0,.044),(-.015,.041),(-.025,.033),(-.029,.023),(-.030,.010),(-.0295,-.004),(-.0300,-.016),(-.0318,-.033),(-.0310,-.046),(-.0288,-.055),(-.024,-.063),(-.016,-.071),(-.010,-.074)]
O=loop_samples(outer,4);I=loop_samples([(x*(.94 if y>0 else 1),y*(.83 if y>0 else 1)) for x,y in opening],4)
def bottom(y):return curve_knots([(-.175,.005),(-.150,.0013),(-.138,0),(-.081,0),(-.071,.0011),(-.050,.005),(-.027,.015),(-.006,.022),(.020,.024),(.060,.024)],y)
def soleh(y):return bottom(y)+curve_knots([(-.175,.009),(-.11,.012),(-.055,.0115),(-.026,.0095),(.060,.010)],y)
def opheight(x,y):
 return curve_knots([(-.077,.064),(-.056,.063),(-.035,.061),(-.010,.059),(.005,.064),(.022,.075),(.044,.092)],y)+.0012*(x/.032)
def mkshoering(s,coords,shrink,fun):
 return [clear_last(s,shoe_xform(s,p.x*shrink,((p.y+.056)*shrink)-.056,fun(p.y)),.0028) for p in coords]
for s in (1,-1):
 side='L' if s==1 else 'R'
 rings=[]
 for sh,f in [(.955,lambda y:bottom(y)),(.992,lambda y:bottom(y)+.0007),(1.012,lambda y:bottom(y)+.0022),(1.014,lambda y:soleh(y)-.0038),(1.009,lambda y:soleh(y)-.0019),(.996,lambda y:soleh(y))]:
  rings.append(mkshoering(s,O,sh,f))
 o=grid('Mary Jane '+side+' | sculpted sole and arched shank',rings,shoes,True,s==-1)
 # Tread cap follows the same forefoot-bearing plane as the welt.
 # The inner cap is set to the same last shape, not crossed by the heel block.
 tread=[rings[0]]
 for sh in [.86,.67,.44,.19,.0025]:
  tread.append([(s*(.068+p.x*sh-.022*min(y,0)),y,bottom(y)) for p in O for y in [((p.y+.056)*sh)-.056]])
 o=grid(side+' | outsole tread',tread,shoes,True,s!=-1)
 # Bound the insole below the lowest skin cage. A short upturn in the heel
 # stays on the solid heel seat while preserving the foot's internal space.
 board=[[(x,y,min(z,.02425)) for x,y,z in rings[-1]]]
 for sh in [.90,.70,.47,.18,.0025]:
  board.append([shoe_xform(s,p.x*sh,y,min(.02425,soleh(y)-.0018)) for p in O for y in [((p.y+.056)*sh)-.056]])
 grid(side+' | lasting board',board,shoes,True,s==-1)
 # Low heel, wider and rounded toward back, flat footprint, slanted anterior edge.
 hp=loop_samples([(.023,-.002),(.031,.003),(.033,.024),(.029,.042),(.017,.052),(0,.054),(-.020,.051),(-.030,.041),(-.032,.024),(-.030,.005),(-.023,-.002),(0,-.004)],5)
 rr=[]
 for z,fx,fy in [(0,.86,.89),(.001,.91,.92),(.003,.93,.94),(.0177,.985,.985),(.0224,1,1),(.0244,.998,1)]:
  rr.append([shoe_xform(s,p.x*fx,(p.y-.025)*fy+.025,z) for p in hp])
 o=grid('Mary Jane '+side+' | low shaped block heel',rr,shoes,True,s==-1)
 obj(side+' | heel ground face',rr[0],[tuple(range(len(rr[0])))],shoes,False)
 obj(side+' | heel seat face',rr[-1],[tuple(range(len(rr[-1])))],shoes,False)
 line(side+' | toplift edge',[shoe_xform(s,p.x*.935,(p.y-.025)*.945+.025,.004) for p in hp],.00065,shadow,True)
 # Formed upper has a rounded toe box, heel counter and a scooped opening.
 def leather(t):
  row=[]
  for p,pr in zip(O,I):
   y0=p.y;y1=pr.y
   x=(1-t)*p.x+t*pr.x;y=(1-t)*p.y+t*pr.y
   h=soleh(y0)-.0017+(opheight(pr.x,pr.y)-soleh(y0)+.0017)*sin(.5*pi*t)
   toe=clipped01((-y0-.073)/.092)
   h+=.0105*sin(pi*t)*toe
   bulge=(.0025+.0025*toe)*sin(pi*t);sg=0 if abs(x)<.00001 else (1 if x>0 else -1)
   x+=sg*bulge*(abs(p.x)/.043);y-=.0025*sin(pi*t)*toe
   # A hand-shaped, continuous crown clears the profiled stocking without
   # displacing isolated vertices at the boundary of the footprint.
   h+=.0054*ga(y+.140,.039)*max(0,sin(pi*t))**.85
   row.append(clear_last(s,shoe_xform(s,x,y,h),.0022))
  return row
 rr=[leather(t) for t in [0,.025,.09,.18,.29,.43,.59,.72,.83,.92,.978,1]]
 o=grid('Mary Jane '+side+' | low-cut vamp and quarter',rr,shoes,True,s==-1);solid(o,.0017);o.modifiers[-1].use_even_offset=False
 line(side+' | bound topline',rr[-1],.00145,main,True)
 line(side+' | welt stitching',mkshoering(s,O,1.002,lambda y:soleh(y)-.00165),.0007,main,True)
 # Instep strap domes over the ankle. The buckle sits at the outer side.
 def strappt(q,v,off=0):
  x=q*.0382; y=-.042+.007*q+v*.0069
  h=.054+.0292*(max(0,1-q*q)**.68)+.001*q+.0025*v*(1-q*q)-.00105*v*v+off
  return clear_last(s,shoe_xform(s,x,y,h),.0024)
 qr=[-1+i/30 for i in range(61)]
 o=grid('Mary Jane '+side+' | arched instep strap',[[strappt(q,v) for q in qr] for v in [-1,-.89,-.50,0,.50,.89,1]],shoes);solid(o,.0022);o.modifiers[-1].use_even_offset=False
 for v in [-.88,.88]:line(side+' | strap edge', [strappt(q,v,.00078) for q in qr],.00038,main)
 # Angled rectangular buckle aligned to outer ankle tangent, not painted hardware.
 bc=Vector(shoe_xform(s,.0361,-.0359,.0627));m1=Vector((s*.58,0,-.815)).normalized();m2=Vector((0,1,.035)).normalized()
 br=loop_samples([(-.0058,-.0100),(.0058,-.0100),(.0081,-.0079),(.0081,.0079),(.0058,.0100),(-.0058,.0100),(-.0081,.0079),(-.0081,-.0079)],4)
 line(side+' | buckle frame',[bc+m1*p.x+m2*p.y for p in br],.00138,trim,True)
 line(side+' | buckle tongue',[bc+m1*.0077,bc+m1*.0010+m2*.0004,bc-m1*.0075+m2*.0017],.00095,trim)

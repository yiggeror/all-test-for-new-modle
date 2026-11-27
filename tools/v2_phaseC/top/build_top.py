"""Cut Suzu's Phase C jacket and shirt on the approved VRM mannequin."""
from pathlib import Path
from math import *
import os,sys,json
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

D=Path(__file__).resolve().parent
S=bpy.context.scene
B=S.objects['Suzu · Body']; R=S.objects['Suzu · Humanoid']
dep=bpy.context.evaluated_depsgraph_get()
ev=B.evaluated_get(dep); tmp=ev.to_mesh();tmp.calc_loop_triangles()
skin=[ev.matrix_world@v.co for v in tmp.vertices]
skin_tr=[tuple(t.vertices) for t in tmp.loop_triangles]
BV=BVHTree.FromPolygons(skin,skin_tr,all_triangles=True)
ev.to_mesh_clear()
C=bpy.data.collections.new('SUZU_PHASE_C_TOP');S.collection.children.link(C)
def sub(name):
 a=bpy.data.collections.new(name);C.children.link(a);return a
JA=sub('Tailored navy jacket');SL=sub('Sculpted sleeves and double gold cuffs');SH=sub('Ivory Oxford and gold button placket')
def rgb(v):
 def f(s):
  t=int(s,16)/255;return t/12.92 if t<.04045 else ((t+.055)/1.055)**2.4
 return tuple(f(v[j:j+2]) for j in (0,2,4))+(1,)
def mat(name,hex0,rough=.72,metal=0.,emi=.16,shade='334063'):
 m=bpy.data.materials.new('Suzu C · '+name);m.use_nodes=True;m.diffuse_color=rgb(hex0)
 p=m.node_tree.nodes['Principled BSDF']
 p.inputs['Base Color'].default_value=rgb(hex0);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 p.inputs['Specular IOR Level'].default_value=.31 if metal else .13
 p.inputs['Emission Color'].default_value=rgb(shade);p.inputs['Emission Strength'].default_value=emi
 m['suzu_stage_role']='costume';return m
nav=mat('midnight navy twill','2F354F',.81,0,.18,'263351')
navlap=mat('lapel on cross-grain satin','333950',.69,0,.18,'283753')
navbind=mat('folded navy binding','252C46',.77,0,.18,'253451')
ivory=mat('ivory Oxford','F2E4D9',.66,0,.10,'E2D3C6')
ivoryfold=mat('collar and welt Oxford','F4E7DF',.64,0,.10,'E5D8CF')
stitch=mat('ink blue inseam','273048',.83,0,.21,'27324E')
gold=mat('antique gold piping','C5A37D',.39,.62,.16,'A97F51')
met=mat('polished gold fastening','C5A37D',.26,.76,.19,'B38654')
black=mat('deep eye of button','5C4835',.71,0,.095,'8F674C')
def cl(v,l=0.,h=1.):return min(h,max(l,v))
def sm(a,b,u):
 q=cl((u-a)/(b-a));return q*q*(3.-2.*q)
def ga(x,w):return exp(-(x/w)**2)
def lerp(a,b,w):return a+(b-a)*w
def interp(rows,x):
 if x<=rows[0][0]:return rows[0][1:]
 if x>=rows[-1][0]:return rows[-1][1:]
 for i,(q,*b) in enumerate(rows):
  if q>=x:
   p,*a=rows[i-1]; f=(x-p)/(q-p)
   return [lerp(u,v,f) for u,v in zip(a,b)]
def listn(n,k=1.):return [k*i/n for i in range(n+1)]
def ring(n):return [tau*i/n for i in range(n)]
def mesh(name,vs,fs,m,col,group='torso',smooth=True):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update()
 o=bpy.data.objects.new(name,d);col.objects.link(o);d.materials.append(m)
 o['suzu_stage_role']='costume_top';o['suzu_cloth_group']=group
 for p in d.polygons:p.use_smooth=smooth
 return o
def grid(name,rows,m,col,loop=False,rev=False,wall=0,group='torso'):
 n=len(rows[0]);l=len(rows);vs=[v for p in rows for v in p];fs=[]
 for j in range(l-1):
  for i in range(n-(not loop)):
   a=i+j*n;b=(i+1)%n+j*n;q=(a,b,b+n,a+n)
   fs.append(q[::-1] if rev else q)
 o=mesh(name,vs,fs,m,col,group)
 if wall:
  bpy.context.view_layer.objects.active=o
  md=o.modifiers.new('Pattern thickness','SOLIDIFY');md.thickness=wall;md.offset=-1;md.use_even_offset=False
  bpy.ops.object.modifier_apply(modifier=md.name)
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
 return o
def tube(name,trace,w,m,col,loop=False,group='torso',depth=None,sides=8):
 P=[Vector(v) for v in trace];rows=[];guide=Vector((0,0,1)) if loop else Vector((0,1,0))
 for i,p in enumerate(P):
  ii=(i+1)%len(P) if loop else min(i+1,len(P)-1);jj=(i-1)%len(P) if loop else max(i-1,0)
  t=(P[ii]-P[jj]).normalized();n=guide-t*t.dot(guide)
  if n.length<.02:n=Vector((1,0,0))-t*t.x
  n.normalize();b=t.cross(n).normalized()
  rows.append([p+(n*(depth if depth is not None else w)*cos(a)+b*w*sin(a)) for a in ring(sides)])
 fc=[];n=len(rows);s=range(sides)
 for a in range(n if loop else n-1):
  b=(a+1)%n
  for j in s:
   k=(j+1)%sides;fc.append((a*sides+j,a*sides+k,b*sides+k,b*sides+j))
 if not loop:fc.extend([tuple(reversed(range(sides))),tuple((n-1)*sides+j for j in s)])
 o=mesh(name,[p for row in rows for p in row],fc,m,col,group)
 return o
def ray(p,d,L=.40):return BV.ray_cast(Vector(p),Vector(d),L)
# Pattern station: Z, half-width, front plane, side line Y, back plane.
# The breast section bridges the sternum instead of shrinkwrapping the chest.
PAT=[
 (.985,.089,-.102,-.029,.041),(1.003,.087,-.103,-.032,.038),
 (1.028,.084,-.109,-.033,.039),(1.043,.088,-.111,-.031,.044),
 (1.064,.096,-.115,-.021,.054),(1.084,.105,-.117,-.014,.066),
 (1.105,.111,-.118,-.005,.071),(1.127,.116,-.116,.003,.076),
 (1.149,.117,-.109,.007,.077),(1.170,.115,-.098,.008,.077),
 (1.188,.113,-.089,.011,.078),(1.207,.118,-.080,.018,.078),
 (1.222,.129,-.073,.022,.078),(1.237,.143,-.068,.025,.078),
 (1.250,.146,-.061,.028,.077),(1.260,.127,-.052,.031,.076),
 (1.269,.101,-.039,.033,.075),(1.278,.067,-.024,.033,.073),
 (1.286,.045,-.017,.034,.072),(1.295,.038,-.014,.034,.070),
 (1.304,.037,-.011,.034,.070)]
OPEN=[(1.027,.034),(1.066,.035),(1.109,.036),(1.146,.039),(1.177,.043),(1.207,.047),
 (1.229,.047),(1.244,.043),(1.261,.037),(1.277,.031),(1.290,.031),(1.302,.027)]
def bodice(a,z,inner=False):
 rx,yf,cy,yb=interp(PAT,z)
 if inner:rx-=.0065;yf+=.0066+.009*ga(z-1.071,.029)*(1-sm(1.10,1.13,z));yb-=.006
 sn,co=sin(a),cos(a);px=rx*sn
 if co>=0:
  # More fill toward front bust folds and softly released underbust darts.
  # Flatten the visible gore across the breast and release the tension
  # over the ribs, hence no breast-shaped cavities in the blazer shell.
  power=1.-.33*ga(z-1.106,.085)*sm(0.,.15,co)
  y=cy+(yf-cy)*co**power
  y-=.0030*ga(z-1.110,.059)*ga(abs(sn)-.51,.32)*co
  if not inner:
   wing=ga(abs(sn)-.718,.264)*sm(.08,.35,co)
   # The fashion block bridges the two anterior convexities; over the
   # side rib let the cloth hang from the shoulder without a tight cup.
   y-=wing*(.0140*ga(z-1.081,.039)+.0100*ga(z-1.184,.030)
          +.0050*ga(z-1.108,.059))
  y+=.0019*ga(z-1.063,.035)*sin(9*a+.26+18*(z-1.03))*co
  y+=.0018*ga(z-1.097,.046)*sin(16*a-22*(z-1.07))*co
 else:
  y=cy+(cy-yb)*co
  y+=.0017*ga(z-1.119,.060)*cos(4*a+.2)*(-co)
  if not inner:
   y+=.0135*ga(z-1.183,.025)*sm(.53,.88,abs(sn))*sm(.03,.30,-co)
 # Fit tolerance is checked on the reference anatomy itself, but ignore
 # disconnected upper-arm intersections in the armpit cutout.
 p0=Vector((0,cy,z)); d=Vector((px,y-cy,0));q=d.length;d.normalize()
 p,n,i,t=ray(p0,d,.32)
 if p is not None:
  want=t+(.0052 if inner else .0108)
  cap=(.016 if inner else .022)
  if z<1.193 or abs(sn)<.78 or z>1.270:up=min(cap,max(0,want-q))
  else:up=min(.006,max(0,want-q)) if t<q+.010 else 0.
 else:up=0.
 # Stand the jacket outside the shirt and waistband, with the eight mm
 # of tailoring ease tapering to zero at the rolled shoulder/neck.
 gap=0. if inner else (.0075+.0010*ga(z-1.125,.061))*(1-sm(1.220,1.268,z))
 res=p0+d*(q+up+gap)
 return tuple(res)
def ypos(x,z,inner=False,gap=0):
 # X/Z projection of the actual cut pieces; seams and lapel roll use the same panel.
 l=-pi/2;r=pi/2
 for _ in range(27):
  a=(l+r)*.5; p=bodice(a,z,inner)
  if p[0]<x:l=a
  else:r=a
 return (x,p[1]-gap,z)
def edgeangle(z):
 x=interp(OPEN,z)[0];lo=0.;hi=pi/2
 for _ in range(21):
  a=(lo+hi)*.5
  if bodice(a,z)[0]<x:lo=a
  else:hi=a
 return (lo+hi)*.5
def cut(z,shirt=False):
 a=sm(1.165 if not shirt else 1.140,1.225,z)*(1-sm(1.240,1.273,z))
 return a*(.083 if not shirt else .68)
def hem(s):
 return 1.031+.008*(.53+.47*cos(2*s+.13))+.0032*(1-cos(s))*.5
def colz(a):
 return 1.286+.017*sm(-.04,.96,-cos(a))
def jacket(z,a):
 zz=z+(hem(a)-1.036)*(1-sm(1.036,1.063,z))+(colz(a)-1.297)*sm(1.27,1.297,z)
 return bodice(a,zz)
jz=sorted(set([1.036,1.037,1.041,1.046,1.294,1.296,1.297]+[1.048+i*.0037 for i in range(67) if 1.048+i*.0037<1.294]))
for sector,(a0,a1) in enumerate(((0,pi/2),(pi/2,pi),(pi,3*pi/2),(3*pi/2,tau))):
 rows=[]
 for z in jz:
  e=edgeangle(z);k=cut(z);L,U=[(e,pi/2-k),(pi/2+k,pi),(pi,3*pi/2-k),(3*pi/2+k,tau-e)][sector]
  rows.append([jacket(z,lerp(L,U,u)) for u in listn(34)])
 # Go straight across the anatomical back, hidden under the hair, without
 # drawing a separate fat shoulder pad. Edge junctions live in seam allowances.
 grid(('Jacket · left chest princess','Jacket · left back dart','Jacket · right back dart','Jacket · right chest princess')[sector],rows,nav,JA,wall=.00255)
# A hidden bias gusset keeps the back of the underarm enclosed as the sleeve
# rotates. It sits between yoke and sleeve, not as a visible third cover.
for s in (-1,1):
 rr=[]
 for z in [1.158+i*.0045 for i in range(26)]:
  w=.014+1.09*cut(z)
  for_pad=.0009+ga(z-1.184,.025)*.00325
  row=[]
  for f in listn(22):
   a=s*(pi/2-w+2*w*f)
   p=Vector(bodice(a,z));p+=Vector((sin(a),-cos(a),0))*for_pad
   row.append(p)
  rr.append(row)
 grid('Jacket · bias underarm gusset '+str(s),rr,nav,JA,rev=s<0,wall=.0019)
for s in (-1,1):
 q=pi if s>0 else tau
 e=edgeangle(1.036);sig=1 if s>0 else -1; aa=[lerp(e,pi,t) for t in listn(82)]
 trace=[]
 for a in aa:
  a*=sig;pos=Vector(jacket(1.038,a))
  pos+=Vector((sin(a),-cos(a),0))*.0011
  trace.append(pos)
 tube('Jacket · fine gold at open hem '+str(s),trace,.00146,gold,JA,depth=.00124)
 for shift in (0,):
  vv=[z for z in jz if z<1.148]+[1.149]
  tr=[]
  for z in vv:
   a=edgeangle(z)*s;v=Vector(jacket(z,a))
   v+=Vector((sin(a)*-.45,-.89,0))*.0015
   tr.append(v)
  tube('Jacket · front binding '+str(s),tr,.00140,gold,JA)
# Notched tailored lapels and a rolled neck: each is a shaped panel with
# true rolled relief and controlled notch support.
LAP=[(1.140,.037,.041),(1.148,.039,.044),(1.171,.041,.062),(1.188,.043,.076),
 (1.207,.048,.094),(1.214,.048,.097),(1.215,.048,.097),(1.225,.048,.076),
 (1.226,.048,.075),(1.230,.048,.080),(1.241,.044,.102),(1.251,.041,.115),
 (1.254,.041,.115),(1.259,.039,.105),(1.268,.036,.083),(1.277,.033,.059),
 (1.284,.031,.043),(1.287,.030,.036)]
def lap(s,z,u,more=0):
 xi,xo=interp(LAP,z);x=s*lerp(xi,xo,u)
 rel=.0021+.0064*(1-u)**2+.0033*sin(pi*u)*(.45+.55*ga(z-1.218,.035))
 # Cut toward the shoulder's real top surface, not a levitating wing.
 rel*=.50+.50*sm(1.14,1.167,z)
 return ypos(x,z,gap=rel+more)
for s in (-1,1):
 zs=sorted(set([q[0] for q in LAP]+[1.140+i*.0036 for i in range(41) if 1.140+i*.0036<1.287]))
 us=[0,.032,.092,.18,.32,.49,.67,.84,.935,.973,1]
 grid('Jacket · notched rolled lapel '+str(s),[[lap(s,z,u) for u in us] for z in zs],navlap,JA,rev=s<0,wall=.00230)
 tr=[lap(s,z,.961,.0010) for z in zs if z<=1.254]
 tube('Jacket · fine gold lapel braid '+str(s),tr,.00153,gold,JA,depth=.00112)
 tr=[lap(s,z,.895,.00049) for z in zs if 1.153<=z<=1.254]
 tube('Jacket · understitch at notch '+str(s),tr,.00040,stitch,JA)
 # Present rear/side neckband continues to the lapel without a protruding plate.
 vals=[lerp(.65,pi,t) for t in listn(38)]
 rr=[]
 for dz,pad in [(0,.0015),(.002,.0027),(.009,.0020),(.012,.0015)]:
  row=[]
  for a in vals:
   z=colz(a)-.012+dz
   p=Vector(bodice(a*s,z));p+=Vector((sin(a)*s,-cos(a),0))*pad;row.append(p)
  rr.append(row)
 grid('Jacket · narrow rollover collar '+str(s),rr,navlap,JA,rev=s<0,wall=.00135)
# A real side/back dart edge taper, not a contrast texture.
for s in (-1,1):
 t=[]
 for j in range(42):
  z=1.048+j*.00452;a=s*(pi-(.53+.17*ga(z-1.215,.065)))
  p=Vector(bodice(a,z));p+=Vector((sin(a),-cos(a),0))*.00027;t.append(p)
 tube('Jacket · angled back princess seam '+str(s),t,.00051,stitch,JA)
def bone(s,part):return R.matrix_world @ R.data.bones['J_Bip_'+('L' if s>0 else 'R')+'_'+part].head_local
# Sleeve drape is sampled on the locked arm in planes normal to the arm.
# Only the cloth's ease and gathers are authored offsets.
ra={}
def armgeom(s,u):
 sh,el,hand=[bone(s,j) for j in ('UpperArm','LowerArm','Hand')]
 up=(el-sh).normalized();lo=(hand-el).normalized();whole=(hand-sh).length
 axis=up.lerp(lo,sm(.44,.62,u)).normalized()
 q=sh+up*(u*whole) if u<.52 else el+lo*(u*whole-(el-sh).length)
 if .43<u<.62:
  t=sm(.43,.62,u);q=(sh+up*u*whole).lerp(el+lo*(u*whole-(el-sh).length),t)
 # Skin bulk sits a few mm behind elbow axis only in the actual measured mesh.
 q+=Vector((0,.0007*sin(pi*cl(u)),0))
 e=Vector((-s*axis.z,0,s*axis.x)).normalized()
 f=axis.cross(e).normalized()
 if f.y<0:f=-f
 return q,axis,e,f
BRE=[(-.10,.020,.027),(-.04,.031,.039),(0,.038,.043),(.07,.042,.045),(.15,.041,.043),
 (.26,.038,.038),(.38,.034,.036),(.52,.030,.034),(.63,.030,.034),(.75,.028,.030),
 (.84,.026,.028),(.90,.023,.024),(.94,.021,.022),(.97,.019,.020),(.99,.0186,.019)]
def sleeve(s,u,a,more=0,cuff=False):
 q,T,e,f=armgeom(s,u);co,si=cos(a),sin(a)
 rx,ry=interp(BRE,u);d=Vector(e*co+f*si)
 pred=1/sqrt((co/rx)**2+(si/ry)**2)
 if u>.152:
  hit,nn,i,t=ray(q,d,.070)
  if hit is not None and .007<t<.048:
   ease=.0049+.0029*ga(u-.73,.136)+.0012*ga(u-.259,.12)
   if u>.89:ease*=1-.41*sm(.89,.98,u)
   mincloth=max(.012,t+ease)
   blend=max(sm(.15,.28,u),.24)
   pred=max(t+.0023,lerp(pred,mincloth,blend))
 # Increase sleeve diameter by a measured 14.5% over the upper and
 # lower arm; retain organic gathering only as an easing into the cuff.
 pad=.145*sm(-.10,.12,u)*(1-.82*sm(.84,.99,u))
 pred*=1+pad
 # Quiet angled elbow tension and smaller forearm gathers. No swollen lower bulb.
 hill=(.00195*cos(3*a+.2*s)+.00155*sin(5*a-14*(u-.78)+s*.31))*ga(u-.862,.092)
 hill+=.0012*ga(u-.714,.114)*max(0,-co)
 bend=sm(-.3,.92,-co-.34*si)
 line=(.00182*ga(u-(.49+.025*sin(a+s*.4)),.026)-.00132*ga(u-(.531+.012*cos(a)),.023))*bend
 hill=0 if cuff else hill+line
 pos=q+d*(pred+hill+more)
 if not cuff:pos+=Vector((0,.001*ga(u-.81,.113)*sin(a*2.0+s),0))
 return tuple(pos)
for s in (-1,1):
 lab='L' if s>0 else 'R';group='arm_'+lab
 A=ring(56);u0=-.115
 uu=sorted(set([u0,u0+.012,-.068,-.044,0,.035,.91,.92,.928,.934]+[.056+i*.0152 for i in range(60) if .056+i*.0152<.925]))
 def lead(u,a):
  t=1-sm(u0,.13,u)
  return u+.025*t*(.5+cos(a))+.010*t*sin(a+.3*s)
 rr=[[sleeve(s,lead(u,a),a) for a in A] for u in uu]
 grid('Jacket · two-piece slim sleeve '+lab,rr,nav,SL,True,s<0,.00195,group)
 grid('Jacket · tapered folded cuff '+lab,[[sleeve(s,u,a,m,True) for a in A] for u,m in
  ((.910,.0015),(.916,.00315),(.930,.00335),(.953,.0034),(.971,.00335),(.984,.00295),(.994,.0011))],navbind,SL,True,s<0,.00160,group)
 for u,w in ((.930,.00138),(.963,.00138)):
  tube(f'Jacket · {lab} cuff double gold {u:.3f}',[sleeve(s,u,a,.00415,True) for a in A],w,gold,SL,True,group)
 # The underside seam remains quiet under a turn.
 tr=[sleeve(s,u,pi+.18*sin(3*u+s),.00012) for u in uu if .08<u<.917]
 tube('Jacket · sleeve inside shaping seam '+lab,tr,.00044,stitch,SL,group=group)
# Blouse is independent tailoring: outer brightness is not paint on the jacket.
sz=sorted(set([.995,1.000,1.008,1.287,1.293]+[1.009+i*.0038 for i in range(74) if 1.009+i*.0038<1.286]))
for side in (-1,1):
 rows=[]
 for z in sz:
  a0=-pi/2+cut(z,True);a1=-a0
  row=[]
  for u in listn(56):
   a=lerp(a0,a1,u)+(0 if side>0 else pi)
   zz=z-.0102*max(0.,cos(a))**2*sm(1.258,1.293,z)
   row.append(bodice(a,zz,True))
  rows.append(row)
 grid('Shirt · fitted ivory '+('front' if side>0 else 'back'),rows,ivory,SH,wall=.00132)
def shirtp(x,z,pad=0):return ypos(x,z,True,pad)
psz=[z for z in sz if z<1.279]+[1.279]
grid('Shirt · real folded button placket',[[shirtp(x,z,.0017) for x in (-.008,-.006,-.002,.002,.006,.008)] for z in psz],ivoryfold,SH,wall=.00125)
for side in (-1,1):
 tube('Shirt · placket blind stitch '+str(side),[shirtp(side*.006,z,.0023) for z in psz],.00032,ivoryfold,SH)
# Separate small pointed collars. The edge drafting includes a sleeve-like
# curvature along the top of the shoulder, rather than a floating triangle.
CLPTS=[(1.226,.0460,.0466),(1.232,.040,.0500),(1.240,.030,.0510),(1.252,.019,.0490),
 (1.262,.013,.0440),(1.271,.014,.0400),(1.281,.016,.0340),(1.286,.019,.0310)]
for side in (-1,1):
 rows=[]
 for z in sorted(set([r[0] for r in CLPTS]+[1.226+.0025*i for i in range(25)])):
  x0,x1=interp(CLPTS,z)
  row=[]
  for u in listn(13):
   x=side*lerp(x0,x1,u)
   p=shirtp(x,z,.0040+.0046*sin(pi*u)*(1-sm(1.269,1.286,z)))
   under=ypos(x,z,gap=.0119+.0035*(1-u)*ga(z-1.245,.021))[1]
   # The collar point lies just over the rolled edge, not beneath it.
   edgefade=sm(.016,.031,abs(x))*(1-sm(1.265,1.282,z))
   p=(x,min(p[1],lerp(p[1],under,edgefade)),z)
   row.append(p)
  rows.append(row)
 grid('Shirt · pressed pointed collar '+str(side),rows,ivoryfold,SH,rev=side<0,wall=.00149)
# A compact rounded collar stand on the true neck.
grid('Shirt · turned neck stand',[[bodice(a,z+.010*sm(-.2,.95,-cos(a))-.010*max(0,cos(a))**2,True) for a in ring(72)] for z in
 (1.274,1.276,1.283,1.287,1.290)],ivoryfold,SH,True,wall=.00115)
def disc(name,p,r,m,col,group='torso'):
 x,y,z=p
 rows=[[(x+q*cos(a),y+d,z+q*sin(a)) for a in ring(24)] for q,d in
 ((r*.58,.0007),(r*.86,.0001),(r,-.0007),(r*.91,-.0018),(r*.63,-.0020),(r*.021,-.0018))]
 grid(name,rows,m,col,True,group=group)
for i,z in enumerate((1.076,1.109,1.144,1.178,1.210,1.240)):
 p=shirtp(.0003,z,.0022);disc('Shirt · antique gold button '+str(i+1),p,.00359,met,SH)
 for k in (-1,1):
  x,y,zz=p
  disc('Shirt · recessed button eye', (x+k*.00091,y-.00179,zz),.00053,black,SH)
# The two jewelry groups attach to these actual cloth surfaces.
brooch=Vector(ypos(.084,1.170,gap=.0032))
eyeprobe=Vector(ypos(.081,1.171));xb=Vector(ypos(.087,1.171));zb=Vector(ypos(.081,1.175))
n=(xb-eyeprobe).cross(zb-eyeprobe).normalized()
if n.y>0:n=-n
bow=Vector(shirtp(0,1.250,.0048))
(D/'top_interfaces.json').write_text(json.dumps({'brooch':list(brooch),'brooch_normal':list(n),'bow':list(bow),
 'band_z':[.988,1.057],'collection':C.name},indent=2))
C['mounted_brooch_m']=list(brooch);C['mounted_bow_m']=list(bow)
C['built_on']='Phase B frozen, Round 5 cut pattern'
S.view_settings.view_transform='Standard';S.view_settings.look='None'
out=Path(os.getenv('TOP_OUT',D/'top_tryon.blend')).resolve()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
print('Real new top:',len(C.all_objects),sum(len(o.data.polygons) for o in C.all_objects),'faces',flush=True)
print('Clothing mount guides:',list(brooch),list(n),list(bow),flush=True)

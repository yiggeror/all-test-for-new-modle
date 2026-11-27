# Double-layer bow: each wing is a genuine twisted loop. Separate cut swallow
# tails descend over the placket; the knot and two tiny faceted stars stand proud.
bowz=1.2545
for s in (-1,1):
 lab='L' if s==1 else 'R'
 for tier in (0,1):
  scale=.86 if tier==0 else 1
  rows=[]
  for j in range(49):
   t=j/48;curve=sin(pi*t);span=curve**.90
   row=[]
   for k in range(13):
    v=-1+k/6
    x=s*(.006+(.051 if tier else .049)*span)
    cz=bowz+(.0052 if tier else -.0005)*span+(.0014 if tier else -.0010)*cos(pi*t)
    hw=.004+.0147*(curve**.69)*scale
    z=cz+v*hw+span*(.0014*v*v+.0019*v)
    base=-.0645 if tier else -.0593
    # Front/back of real outward fold; taper the gathered center channel.
    y=base-.0079*sin(2*pi*t)-.0038*span-.0019*span*v+.0008*v*v
    y+=.0024*(1-span*.79)*cos(v*pi*1.55)*(.40+.60*sin(pi*t))
    # let distal upper/lower lips twist, so open loop is legible in 3/4.
    y+=.0018*v*cos(pi*t)
    row.append((x,y,z))
   rows.append(row)
  o=grid('Bow | '+('front' if tier else 'under')+' loop '+lab,rows,bowmat);solid(o,.0014)
 # The ribbon tail's lower silhouette is bias cut with a small fish notch.
 ts=[0,.03,.08,.16,.27,.4,.54,.67,.79,.89,.96,1]
 vs=[-1,-.85,-.55,-.18,0,.17,.40,.66,.85,1]
 def tail(t,v):
  x=s*(.006+.029*t+.009*sin(.85*pi*t)+v*(.0047+.0088*t))
  z=bowz-.009-.066*t+.0072*t**4*max(0,1-abs((v-.19)*1.25))+.0034*t*t*v
  y=shirtfront(x,z)[1]-.006-.0033*sin(pi*t)-.0011*(1-v*v)+.0016*sin(v*pi)*sin(pi*t)
  return (x,y,z)
 o=grid('Bow | bias-cut tail '+lab,[[tail(t,v) for v in vs] for t in ts],bowmat);solid(o,.0015)
 o=grid('Bow | narrow tail border '+lab,[[tuple(Vector(tail(t,v))+Vector((0,-.00085,0))) for v in vs] for t in [.888,.896,.919,.928]],trim);solid(o,.0004)
# wrapped central knot: close-tabbed compressed satin with angled side tuck
AA=sample(46);rows=[]
for u,rz in [(-1,.83),(-.88,.98),(-.62,1.05),(0,1),(.65,.98),(.90,1.01),(1,.85)]:
 row=[]
 for a in AA:
  x=.0084*u+.0013*sin(a)+.0006*sin(2*a);y=-.0648+.0075*rz*cos(a);z=bowz+.0100*rz*sin(a)+.0015*u
  row.append((x,y,z))
 rows.append(row)
solid(grid('Bow | cinched center knot',rows,trim,True),.0013)
starsolid('Bow | sculpted center star',(0,-.0744,bowz),.0096,.0107,.0033,5,pi/2)
# looped pendant chain and six-point engraved starlet; visibly spaced below center.
for j in range(3):
 z=bowz-.0123-.0046*j
 if j%2:
  ar=[(.00046*cos(a),-.0722+.0014*cos(a),z+.0033*sin(a)) for a in AA]
 else:ar=[(.00175*cos(a),-.0724+.00035*cos(a),z+.0033*sin(a)) for a in AA]
 line('Bow | pendant link '+str(j+1),ar,.00059,trim,True)
starsolid('Bow | pendant star',(0,-.0730,bowz-.0295),.0063,.0071,.0021)
# The astrolabe on the character's own left breast (+X): concentric relief
# rings, spokes, tilted orbital ring passing in front and behind, spindle & bail.
x0,z0=.0890,1.184
ctr=Vector(fplane(x0,z0,.0089))
U=(Vector(fplane(x0+.0002,z0))-Vector(fplane(x0-.0002,z0))).normalized()
V=(Vector(fplane(x0,z0+.0002))-Vector(fplane(x0,z0-.0002))).normalized()
V=(V-U*V.dot(U)).normalized();N=U.cross(V).normalized()
def bl(x,v,d=0):return ctr+U*x+V*v+N*d
def circbro(r,d):return [bl(r*cos(a),r*sin(a),d) for a in sample(100)]
# flat annular frame, rounded external edges, integral engraved recess between bands
rows=[[bl(r*cos(a),r*sin(a),d) for a in sample(100)] for r,d in [(.0156,0),(.0153,.0009),(.0157,.0016),(.0166,.00185),(.0171,.0011),(.0184,.0011),(.0189,.002),(.0197,.002),(.0202,.0014),(.02035,.0004),(.0199,-.0008),(.0158,-.0010),(.0156,0)]]
grid('Astrolabe | milled annular frame',rows,trim,True)
line('Astrolabe | inner engraving',circbro(.01755,.0011),.00029,shadow,True)
for i,a in enumerate([pi*.48,pi*1.15,pi*1.70]):
 pts=[bl(.0163*cos(a),.0163*sin(a),.0003),bl(.008*cos(a+.055),.008*sin(a+.055),.0007),bl(0,0,.0013)]
 line('Astrolabe | radial spoke '+str(i+1),pts,.00091,trim)
tilt=math.radians(34);F=U*cos(tilt)+V*sin(tilt);G=-U*sin(tilt)+V*cos(tilt)
# orbit slants through the frame; it has one near pass and one far pass
ar=[ctr+F*(.0275*cos(a))+G*(.0046*sin(a))+N*(.0034+.0043*sin(a)) for a in sample(116)]
line('Astrolabe | diagonal ecliptic orbit',ar,.00103,trim,True)
# shaped compass needle, faceted and tapered; not a line painted over a disc.
def needle(u,v,d):return tuple(ctr+F*u+G*v+N*d)
verts=[needle(-.0250,0,.0039),needle(.0014,.00222,.0040),needle(.0239,0,.0041),needle(.0012,-.00222,.0040),needle(.0012,0,.0060)]
obj('Astrolabe | bevelled constellation pointer',verts,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],trim,False)
# concentric raised central cap, backing pin, upper suspension loop
rr=[[bl(r*cos(a),r*sin(a),d) for a in sample(48)] for r,d in [(.00350,.0020),(.00395,.0036),(.00365,.0059),(.00280,.0066),(.00165,.0075),(.0001,.00765)]]
grid('Astrolabe | pivot boss',rr,trim,True)
line('Astrolabe | suspension bail',[bl(.00245*cos(a),.0236+.0029*sin(a),-.0002) for a in sample(52)],.00090,trim,True)
line('Astrolabe | fastening post',[bl(0,0,-.0095),bl(0,0,.001)],.00235,shadow)
# Engraver ticks are individual shallow dashes on the front of the graduated ring.
for i in range(20):
 a=i*pi/10;r1=.0175 if i%5 else .0170
 line('Astrolabe | index '+str(i+1),[bl(r1*cos(a),r1*sin(a),.00139),bl(.0184*cos(a),.0184*sin(a),.00139)],.00022,main)

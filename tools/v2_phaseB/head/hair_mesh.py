"""Closed tapered satin ribbons, built from art-directed 3D guide rails."""
import bpy, math, bisect
from mathutils import Vector


def mix(a,b,k):return a+(b-a)*k
def sat(q):return max(0.,min(1.,q))
def eased(a,b,q):
    u=sat((q-a)/(b-a));return u*u*(3.-2.*u)


def guide(rows,t):
    p=[Vector(r[:3]) for r in rows];acc=[0.]
    for va,vb in zip(p,p[1:]):acc.append(acc[-1]+max(.000015,(vb-va).length))
    tt=sat(t)*acc[-1];i=max(0,min(len(rows)-2,bisect.bisect_right(acc,tt)-1));h=acc[i+1]-acc[i];k=(tt-acc[i])/h
    def derivative(j):
        i0=max(j-1,0);i1=min(j+1,len(p)-1)
        if i0==j or i1==j:return (p[i1]-p[i0])/(acc[i1]-acc[i0])
        a=(p[j]-p[i0])/(acc[j]-acc[i0]);b=(p[i1]-p[j])/(acc[i1]-acc[j]);d=acc[i1]-acc[i0]
        return (a*(acc[i1]-acc[j])+b*(acc[j]-acc[i0]))/d
    d0=derivative(i);d1=derivative(i+1)
    result=(2*k**3-3*k*k+1)*p[i]+(k**3-2*k*k+k)*h*d0+(-2*k**3+3*k*k)*p[i+1]+(k**3-k*k)*h*d1
    for_j=[]
    for col in range(3,len(rows[0])):
        y=[r[col] for r in rows]
        def f(j):
            if j==0:return (y[1]-y[0])/(acc[1]-acc[0])
            if j==len(y)-1:return (y[-1]-y[-2])/(acc[-1]-acc[-2])
            a=(y[j]-y[j-1])/(acc[j]-acc[j-1]);b=(y[j+1]-y[j])/(acc[j+1]-acc[j]);h0=acc[j]-acc[j-1];h1=acc[j+1]-acc[j]
            if a*b<=0:return 0.0
            return 3*(h0+h1)/((2*h1+h0)/a+(h1+2*h0)/b)
        z=(2*k**3-3*k*k+1)*y[i]+(k**3-2*k*k+k)*h*f(i)+(-2*k**3+3*k*k)*y[i+1]+(k**3-k*k)*h*f(i+1);for_j.append(z)
    return result,for_j


ROLE_COL={'crown':.57,'bang':.59,'side':.54,'pony':.57,'fine':.64,'ahoge':.61,'back_inner':.36,'back_mid':.51,'back_outer':.59}
def material(role):
    n='SUZU_HAIR_'+role.upper();m=bpy.data.materials.get(n)
    if m is None:
        m=bpy.data.materials.new(n);v=ROLE_COL.get(role,.56);m.diffuse_color=(v,v,v,1);m.use_nodes=True
        b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(v,v,v,1);b.inputs['Roughness'].default_value=.78;b.inputs['Specular IOR Level'].default_value=.16
    return m


def mesh(name,verts,faces,coords,coll,role,phase=0.):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);coll.objects.link(o);me.materials.append(material(role))
    uv=me.uv_layers.new(name='HairUV')
    for f in me.polygons:
        for j,i in zip(f.loop_indices,f.vertices):uv.data[j].uv=coords[i]
        f.use_smooth=True
    o['suzu_hair_role']=role;o['suzu_hair_phase']=float(phase);o['uv_flow']='U across width, V=0 root to 1 tip'
    return o


def ribbon(name,rows,outward,coll,role,phase=0.,stations=55,sides=20,depth_balance=.68,crease=.16,wing=.16,adjust=None):
    """Rows are measured X,Y,Z, half width, outer relief, optional roll degrees."""
    V=[]; F=[]; UV=[]; C=[guide(rows,j/stations)[0] for j in range(stations+1)];arc=[0.]
    for a,b in zip(C,C[1:]):arc.append(arc[-1]+(b-a).length)
    for i in range(stations+1):
        f=i/stations;c,prop=guide(rows,f);w,relief=map(abs,prop[:2]);T=(C[min(i+1,stations)]-C[max(i-1,0)]).normalized()
        n=Vector(outward(f,c) if callable(outward) else outward);n=(n-n.dot(T)*T).normalized();e=n.cross(T).normalized()
        if len(prop)>2:
            roll=math.radians(prop[2]);n,e=(n*math.cos(roll)+e*math.sin(roll)),(e*math.cos(roll)-n*math.sin(roll))
        w=max(w,.000075);relief=max(relief,.000046)
        for q in range(sides):
            theta=math.tau*q/sides;u=-math.sin(theta);v=-math.cos(theta)
            if v>=0:
                # The upper broad face is softly keeled; the crest drifts off centre.
                h=relief*(v**1.48)*(.94+wing*u+crease*math.exp(-((u-.28)/.35)**2))
            else:h=-relief*depth_balance*((-v)**.90)
            p=c+e*(u*w)+n*h
            if adjust:p=Vector(adjust(f,u,v,p))
            V.append(tuple(p));UV.append(((1.+u)*.5,arc[i]/max(arc[-1],1e-9)))
        if i:
            for j in range(sides):
                a=(i-1)*sides+j;b=(i-1)*sides+(j+1)%sides
                F.append((a,b,b+sides,a+sides))
    F.append(tuple(range(sides-1,-1,-1)));F.append(tuple(stations*sides+j for j in range(sides)))
    # Polygons were wound in the transported cross-section frame; verify sign on closed shape.
    volume=0.
    for f in F:
        a=Vector(V[f[0]])
        for b,c in zip(f[1:-1],f[2:]):volume+=a.dot(Vector(V[b]).cross(Vector(V[c])))
    if volume<0:F=[tuple(reversed(f)) for f in F]
    o=mesh(name,V,F,UV,coll,role,phase);o.data.polygons[-1].use_smooth=False;o.data.polygons[-2].use_smooth=False
    return o

"""Write the authored mesh edges and opaque evaluated surface depth for real cameras."""
import struct
from pathlib import Path
import numpy as np
import bpy
from mathutils.bvhtree import BVHTree

def edge_inputs(asset, camera, width, height, out):
    dg=bpy.context.evaluated_depsgraph_get()
    triangles, edges=[],[]
    vmat=np.array(camera.matrix_world.inverted(),np.float64)
    scale=camera.data.ortho_scale
    sx=(scale if width>=height else scale*width/height)
    sy=(scale if height>=width else scale*height/width)
    def xyz(vertices):
        arr=np.empty(len(vertices)*3,np.float32)
        vertices.foreach_get('co',arr)
        return arr.reshape(-1,3)
    def project(co, world):
        q=vmat@np.array(world,np.float64)
        pts=co@q[:3,:3].T+q[:3,3]
        return np.stack([(pts[:,0]/sx+.5)*width,(.5-pts[:,1]/sy)*height,-pts[:,2]],axis=-1).astype('<f4')
    for obj in asset:
        if obj.hide_render: continue
        ev=obj.evaluated_get(dg)
        m=ev.to_mesh()
        if m is None or not m.polygons:continue
        m.calc_loop_triangles()
        idx=np.empty(len(m.loop_triangles)*3,np.int32)
        m.loop_triangles.foreach_get('vertices',idx)
        arr=xyz(m.vertices)
        triangles.append(project(arr,obj.matrix_world)[idx])
        cage=obj.data if obj.type=="MESH" else m
        base=xyz(cage.vertices)
        if obj.type=="MESH" and len(m.vertices)>len(cage.vertices)*1.4:
            tree=BVHTree.FromPolygons(arr,idx.reshape(-1,3),all_triangles=True)
            for i,co in enumerate(base):
                match=tree.find_nearest(co,.04)
                if match and match[0] is not None: base[i]=match[0]
        eidx=np.empty(len(cage.edges)*2,np.int32);cage.edges.foreach_get('vertices',eidx)
        edges.append(project(base,obj.matrix_world)[eidx])
        ev.to_mesh_clear()
    tr,el=np.concatenate(triangles),np.concatenate(edges)
    with Path(out).open('wb') as f:
        f.write(struct.pack('<4I',width,height,len(tr)//3,len(el)//2))
        f.write(tr.tobytes());f.write(el.tobytes())

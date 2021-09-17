import bpy
import bmesh
from math import cos, sin, degrees, radians, sqrt
from mathutils import Vector, Matrix, Quaternion, Euler

def bound_sphere(mesh, radius):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, diameter=radius)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

def bound_cylinder(mesh, radius, length):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=32, diameter1=radius, diameter2=radius, depth=length)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

def bound_disc(mesh, radius, length):
    bm = bmesh.new()
    rot_mat = Matrix.Rotation(radians(90.0), 4, 'Y')
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=32, diameter1=radius, diameter2=radius, depth=length, matrix=rot_mat)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

def bound_capsule(mesh, radius, length, rings = 9, segments = 16):
    bm = bmesh.new()
    mat_loc = Matrix.Translation((0.0, 0.0, length/2))
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, diameter=radius, matrix=mat_loc)
    mat_loc = Matrix.Translation((0.0, 0.0, -length/2))
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, diameter=radius, matrix=mat_loc)
    bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=segments, diameter1=radius, diameter2=radius, depth=length)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

def add_vector_list(list1, list2):
    x = list1[0] + list2[0]
    y = list1[1] + list2[1]
    z = list1[2] + list2[2]     
    return [x, y, z]

def subtract_vector_list(list1, list2):
    x = list1[0] - list2[0]
    y = list1[1] - list2[1]
    z = list1[2] - list2[2]     
    return [x, y, z]

def multiple_vector_list(list, num):
    x = list[0] * num
    y = list[1] * num
    z = list[2] * num
    return [x, y, z]

def get_vector_list_length(list):
    sx = list[0]**2  
    sy = list[1]**2
    sz = list[2]**2
    length = (sx + sy + sz) ** 0.5
    return length 

def get_min_max_bounding_box(objs):
    bounding_boxs = []

    for obj in objs:
        bounding_boxs.append(obj.bound_box)
                
    bounding_boxmin = []
    bounding_boxmax = []

    for b in bounding_boxs:
        bounding_boxmin.append(b[0])
        bounding_boxmax.append(b[6])
    
    min_xs = []
    min_ys = []
    min_zs = []
    for v in bounding_boxmin:
        min_xs.append(v[0])
        min_ys.append(v[1])
        min_zs.append(v[2])
        
    max_xs = []
    max_ys = []
    max_zs = []
    for v in bounding_boxmax:
        max_xs.append(v[0])
        max_ys.append(v[1])
        max_zs.append(v[2])
    
    bounding_box_min = []    
    bounding_box_min.append(min(min_xs))
    bounding_box_min.append(min(min_ys))
    bounding_box_min.append(min(min_zs))
    
    bounding_box_max = []    
    bounding_box_max.append(max(max_xs))
    bounding_box_max.append(max(max_ys))
    bounding_box_max.append(max(max_zs))
    
    return [bounding_box_min, bounding_box_max]

def get_sphere_bb(objs, bbminmax):
    allverts = []
    for obj in objs:
        mesh = obj.data
        for vert in mesh.vertices:
            allverts.append(vert)
    bscen = [0, 0, 0]
    bsrad = 0
    
    av = add_vector_list(bbminmax[0], bbminmax[1])
    bscen = multiple_vector_list(av, 0.5)

    for v in allverts:
        bsrad = max(bsrad, get_vector_list_length(subtract_vector_list(v.co, bscen)))

    return [bscen, bsrad]  

def get_bound_box_verts(verts):

    #xs = []
    #zs = []
    #for vert in verts:
    #    xs.append(vert.co[0])
    #    zs.append(vert.co[2])

    #xmax = max(xs)
    #zmax = max(zs)

    #diagonals = []

    #for vert in verts:
    #    if(vert.co[0] == xmax):
    #        diagonals.append(vert.co)
    #    if(vert.co[2] == zmax):
    #        diagonals.append(vert.co) 
 
    #alldiagonals = [diagonals[0], diagonals[1], verts[0], verts[1]]

    #return alldiagonals
    return None

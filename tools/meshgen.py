import bpy
import bmesh
from math import cos, sin, degrees, radians, sqrt
from mathutils import Vector, Matrix, Quaternion, Euler

def BoundSphere(mesh, radius):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, diameter=radius)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

def BoundCylinder(mesh, radius, length):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=32, diameter1=radius, diameter2=radius, depth=length)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

def BoundDisc(mesh, radius, length):
    bm = bmesh.new()
    rot_mat = Matrix.Rotation(radians(90.0), 4, 'Y')
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=32, diameter1=radius, diameter2=radius, depth=length, matrix=rot_mat)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

def BoundCapsule(mesh, radius, length, rings = 9, segments = 16):
    bm = bmesh.new()
    mat_loc = Matrix.Translation((0.0, 0.0, length/2))
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, diameter=radius, matrix=mat_loc)
    mat_loc = Matrix.Translation((0.0, 0.0, -length/2))
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, diameter=radius, matrix=mat_loc)
    bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=segments, diameter1=radius, diameter2=radius, depth=length)
    bm.to_mesh(mesh)
    bm.free()
    return mesh

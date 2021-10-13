import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.geometry import distance_point_to_plane
from math import cos, inf, sin, degrees, radians, sqrt, atan2

def create_box_from_extents(mesh, bbmin, bbmax):
    # Create box from bbmin and bbmax
    vertices = [
        bbmin,
        Vector((bbmin.x, bbmin.y, bbmax.z)),
        Vector((bbmin.x, bbmax.y, bbmax.z)),
        Vector((bbmin.x, bbmax.y, bbmin.z)),

        Vector((bbmax.x, bbmin.y, bbmax.z)),
        Vector((bbmax.x, bbmin.y, bbmin.z)),
        Vector((bbmax.x, bbmax.y, bbmin.z)),
        bbmax
    ]

    faces = [
        [0, 1, 2, 3],
        [0, 1, 4, 5],
        [0, 3, 6, 5],

        [7, 4, 5, 6],
        [7, 2, 3, 6],
        [7, 4, 1, 2]
    ]
    mesh.from_pydata(vertices, [], faces)

    # Recalculate normals
    bm = bmesh.new()
    
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.clear()
    mesh.update()
    bm.free()

    return mesh

def create_box(mesh, size=1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def create_sphere(mesh, radius=0.5):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, diameter=radius)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def create_cylinder(mesh, radius=0.5, length=1, use_rot=True):
    bm = bmesh.new()
    rot_mat = Matrix.Rotation(radians(90.0), 4, "X") if use_rot else Matrix()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=32,
        diameter1=radius,
        diameter2=radius,
        depth=length,
        matrix=rot_mat
    )
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def create_disc(mesh, radius=0.5, length=0.1):
    bm = bmesh.new()
    rot_mat = Matrix.Rotation(radians(90.0), 4, "Y")
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=32,
        diameter1=radius,
        diameter2=radius,
        depth=length,
        matrix=rot_mat,
    )
    bm.to_mesh(mesh)
    bm.free()
    return mesh

def create_capsule(obj, diameter=0.5, length=2):
    length = length if length > diameter * 2 else diameter * 2
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, diameter=diameter)
    mesh = obj.data

    center = obj.location
    bb = [Vector(b) for b in obj.bound_box]
    z = bb[1] - bb[0]

    # Get top half of vertices
    top = []
    top_faces = []
    for v in bm.verts:
        if distance_point_to_plane(v.co, center, z) >= 0:
            top.append(v)
            for face in v.link_faces:
                if not face in top_faces:
                    top_faces.append(face)

    # Extrude top half
    ret = bmesh.ops.extrude_face_region(bm, geom=top_faces)
    extruded = ret["geom"]
    del ret
    translate_verts = [v for v in extruded if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec = (0.0, 0.0, length - (diameter * 2)), verts=translate_verts)

    bm.to_mesh(mesh)
    bm.free()

    # Fix origin
    linked = obj.name in bpy.context.collection.objects
    if not linked:
        bpy.context.collection.objects.link(obj)

    obj.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    obj.select_set(False)
    obj.location = center

    if not linked:
        bpy.context.collection.objects.unlink(obj)

    return mesh


def get_closest_axis_point(axis: Vector, center: Vector, points: list) -> Vector:

    closest = None
    closestDist = inf

    for p in points:

        rel = (p - center).normalized()
        dist = (rel - axis).length

        if dist < closestDist:
            closest = p
            closestDist = dist

    return closest


def get_distance_of_vectors(a: Vector, b: Vector) -> float:
    locx = b.x - a.x
    locy = b.y - a.y
    locz = b.z - a.z

    distance = sqrt((locx) ** 2 + (locy) ** 2 + (locz) ** 2)
    return distance


def get_direction_of_vectors(a: Vector, b: Vector) -> Euler:
    direction = (a - b).normalized()
    axis_align = Vector((0.0, 0.0, 1.0))

    angle = axis_align.angle(direction)
    axis = axis_align.cross(direction)

    q = Quaternion(axis, angle)

    return q.to_euler("XYZ")


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
    sx = list[0] ** 2
    sy = list[1] ** 2
    sz = list[2] ** 2
    length = (sx + sy + sz) ** 0.5
    return length


# see https://blender.stackexchange.com/questions/223858/how-do-i-get-the-bounding-box-of-all-objects-in-a-scene
"""Multiply 3d coord list by matrix"""
def np_matmul_coords(coords, matrix, space=None):
    M = (space @ matrix @ space.inverted() if space else matrix).transposed()
    ones = np.ones((coords.shape[0], 1))
    coords4d = np.hstack((coords, ones))

    return np.dot(coords4d, M)[:, :-1]


"""Get min and max bounds for an object and all of its children"""
def get_bb_extents(obj):
    bbs = get_bound_world(obj, True)

    return Vector(bbs.min(axis=0)), Vector(bbs.max(axis=0))


"""Get the bounding box of an object and all of it's children"""
def get_bound_world(obj, np_array=False):
    objects = [obj, *get_children_recursive(obj)]
    # get the global coordinates of all object bounding box corners
    np_bounds = np.vstack(
        tuple(
            np_matmul_coords(np.array(o.bound_box), o.matrix_world.copy())
            for o in objects
            if o.type == "MESH"
        )
    )

    if np_array:
        return np_bounds

    bounds = []
    for vert in np_bounds:
        bounds.append(Vector(vert))

    return bounds


def get_bound_center(obj):
    bbmin, bbmax = get_bb_extents(obj)
    center = (bbmin + bbmax) / 2

    return center


def get_children_recursive(obj):
    children = []
    for child in obj.children:
        children.append(child)
        if len(child.children) > 0:
            children.extend(get_children_recursive(child))

    return children


"""Get the radius of an object's bounding box"""
def get_obj_radius(obj) -> float:
    bb_min, bb_max = get_bb_extents(obj)
    p1 = Vector((bb_min.x, bb_min.y, 0))
    p2 = Vector((bb_max.x, bb_max.y, 0))
    # Distance between bb_min and bb_max x,y values
    distance = get_distance_of_vectors(p1, p2)
    return distance / 2


def get_local_pos(obj):
    return Vector(obj.matrix_world.inverted() @ obj.matrix_world.translation)


def signed_volume_of_triangle(p1: Vector, p2: Vector, p3: Vector) -> float:
    v321 = p3.x * p2.y * p1.z
    v231 = p2.x * p3.y * p1.z
    v312 = p3.x * p1.y * p2.z
    v132 = p1.x * p3.y * p2.z
    v213 = p2.x * p1.y * p3.z
    v123 = p1.x * p2.y * p3.z
    return (1.0 / 6.0) * (-v321 + v231 + v312 - v132 - v213 + v123)


"""Get the volume of an object and all of it's children"""  # https://stackoverflow.com/questions/1406029/how-to-calculate-the-volume-of-a-3d-mesh-object-the-surface-of-which-is-made-up
def get_obj_volume(obj) -> int:
    vols = []
    for child in [obj, *get_children_recursive(obj)]:
        if not obj.data:
            continue

        mesh = child.to_mesh()
        mesh.calc_normals_split()
        mesh.calc_loop_triangles()

        for tri in mesh.loop_triangles:
            p1 = obj.matrix_world @ mesh.vertices[tri.vertices[0]].co
            p2 = obj.matrix_world @ mesh.vertices[tri.vertices[1]].co
            p3 = obj.matrix_world @ mesh.vertices[tri.vertices[2]].co
            vols.append(signed_volume_of_triangle(p1, p2, p3))

    return int(abs(sum(vols)))


def get_sphere_bb(objs, bbminmax) -> list:
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

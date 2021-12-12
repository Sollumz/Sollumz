import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.geometry import distance_point_to_plane
from math import radians
from .utils import *
from .version import USE_LEGACY


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


def create_box(mesh, size=2, matrix=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size, matrix=matrix or Matrix())
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def create_sphere(mesh, radius=1):
    bm = bmesh.new()

    kwargs = {}
    if USE_LEGACY:
        kwargs['diameter'] = radius
    else:
        kwargs['radius'] = radius

    bmesh.ops.create_uvsphere(
        bm, u_segments=32, v_segments=16, **kwargs)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def create_cylinder(mesh, radius=1, length=2, rot_mat=Matrix.Rotation(radians(90.0), 4, "X")):
    bm = bmesh.new()

    kwargs = {}
    if USE_LEGACY:
        kwargs['diameter'] = radius
    else:
        kwargs['radius'] = radius

    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=32,
        depth=length,
        matrix=rot_mat if rot_mat else Matrix(),
        **kwargs
    )
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def create_disc(mesh, radius=1, length=0.08):
    bm = bmesh.new()
    # rot_mat = Matrix.Rotation(radians(90.0), 4, "Y") @ lookatlh(
    #     Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)))
    rot_mat = Matrix.Rotation(radians(90.0), 4, "Y")

    kwargs = {}
    if USE_LEGACY:
        kwargs['diameter1'] = radius
        kwargs['diameter2'] = radius
    else:
        kwargs['radius1'] = radius
        kwargs['radius2'] = radius

    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=32,
        depth=length,
        matrix=rot_mat,
        **kwargs
    )
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def create_capsule(mesh, diameter=0.5, length=2, use_rot=False):
    length = length if diameter < length else diameter
    if diameter < 0:
        raise ValueError('Cannot create capsule with a diameter less than 0!')

    bm = bmesh.new()

    kwargs = {}
    if USE_LEGACY:
        kwargs['diameter'] = diameter
    else:
        kwargs['radius'] = diameter

    bmesh.ops.create_uvsphere(
        bm, u_segments=32, v_segments=16, **kwargs)
    bm.to_mesh(mesh)

    center = Vector()
    axis = Vector((0, 0, 1))

    # Get top and bottom halves of vertices
    top = []
    top_faces = []
    bottom = []
    bottom_faces = []

    # amount = length - (diameter * 2)
    amount = (length - diameter) * 2
    vec = Vector((0, 0, amount))

    for v in bm.verts:
        if distance_point_to_plane(v.co, center, axis) >= 0:
            top.append(v.co)
            for face in v.link_faces:
                if not face in top_faces:
                    top_faces.append(face)
        elif distance_point_to_plane(v.co, center, axis) <= 0:
            bottom.append(v.co)
            for face in v.link_faces:
                if not face in bottom_faces and face not in top_faces:
                    bottom_faces.append(face)

    # Extrude top half
    ret = bmesh.ops.extrude_face_region(bm, geom=top_faces)
    extruded = ret["geom"]
    del ret
    translate_verts = [
        v for v in extruded if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=vec / 2, verts=translate_verts)

    # Extrude bottom half
    ret = bmesh.ops.extrude_face_region(bm, geom=bottom_faces)
    extruded = ret["geom"]
    del ret
    translate_verts = [
        v for v in extruded if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=-vec / 2, verts=translate_verts)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm.to_mesh(mesh)
    bm.free()

    if use_rot:
        mesh.transform(Matrix.Rotation(radians(90.0), 4, 'X'))

    return mesh


def flip_uv(uv):
    u = uv[0]
    v = (uv[1] - 1.0) * -1

    return [u, v]


def get_short_long_edge(bbmin, bbmax):
    bbox = bpy.data.meshes.new('bbox')
    create_box_from_extents(
        bbox, bbmin, bbmax)
    edge_lengths = []
    for edge in bbox.edges:
        v1 = bbox.vertices[edge.vertices[0]].co
        v2 = bbox.vertices[edge.vertices[1]].co
        edge_lengths.append(get_distance_of_vectors(v1, v2))
    # edge_lengths = np.array(edge_lengths)
    # height = edge_lengths.max(axis=0)
    # width = edge_lengths.min(axis=0)
    # return height, width
    return max(edge_lengths), min(edge_lengths)


"""Get min and max bounds for an object and all of its children"""


def get_bound_extents(obj, world=True):
    corners = get_total_bounds(obj, world)
    return get_min_vector_list(corners), get_max_vector_list(corners)


def get_total_bounds(obj, world=True):
    objects = []

    # Ensure all objects are meshes
    for obj in [obj, *get_children_recursive(obj)]:
        if obj.type == "MESH":
            objects.append(obj)

    if len(objects) < 1:
        raise ValueError(
            'Failed to get bounds: Object has no geometry data or children with geometry data.')

    corners = []
    for obj in objects:
        for pos in obj.bound_box:
            corners.append(obj.matrix_world @ Vector(pos)
                           if world else obj.matrix_basis @ Vector(pos))

    return corners


def get_bound_center(obj, world=True):
    bbmin, bbmax = get_bound_extents(obj, world)
    center = (bbmin + bbmax) / 2

    return center


def get_children_recursive(obj):
    children = []

    if len(obj.children) < 1:
        return children

    for child in obj.children:
        children.append(child)
        if len(child.children) > 0:
            children.extend(get_children_recursive(child))

    return children


"""Get the radius of an object's bounding box"""


def get_obj_radius(obj, world=True):
    bb_min, bb_max = get_bound_extents(obj, world)

    p1 = Vector((bb_min.x, bb_min.y, 0))
    p2 = Vector((bb_max.x, bb_max.y, 0))

    # Distance between bb_min and bb_max x,y values
    distance = get_distance_of_vectors(p1, p2)
    return distance / 2


def get_local_pos(obj):
    return Vector(obj.parent.matrix_world.inverted() @ obj.matrix_world.translation)


def prop_array_to_vector(prop, size=3):
    if size == 4:
        return Quaternion((prop[0], prop[1], prop[2], prop[3]))
    return Vector((prop[0], prop[1], prop[2]))

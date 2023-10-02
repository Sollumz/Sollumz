import bpy
import bmesh
import numpy as np
from numpy.typing import NDArray
from mathutils import Vector, Matrix
from mathutils.geometry import distance_point_to_plane
from math import radians
from ..sollumz_properties import SollumType
from .utils import divide_list, get_min_vector_list, get_max_vector_list
from .blenderhelper import get_children_recursive


def create_box_from_extents(mesh, bbmin, bbmax):
    # Create box from bbmin and bbmax
    vertices = get_corners_from_extents(bbmin, bbmax)

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


def get_corners_from_extents(bbmin: Vector, bbmax: Vector):
    return [
        bbmin,
        Vector((bbmin.x, bbmin.y, bbmax.z)),
        Vector((bbmin.x, bbmax.y, bbmax.z)),
        Vector((bbmin.x, bbmax.y, bbmin.z)),

        Vector((bbmax.x, bbmin.y, bbmax.z)),
        Vector((bbmax.x, bbmin.y, bbmin.z)),
        Vector((bbmax.x, bbmax.y, bbmin.z)),
        bbmax
    ]


def create_box(mesh, size=2, matrix=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size, matrix=matrix or Matrix())
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def create_sphere(mesh, radius=1):
    bm = bmesh.new()

    kwargs = {}
    kwargs["radius"] = radius

    bmesh.ops.create_uvsphere(
        bm, u_segments=32, v_segments=16, **kwargs)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def create_cylinder(mesh, radius=1, length=2, rot_mat=Matrix.Rotation(radians(90.0), 4, "X")):
    bm = bmesh.new()

    kwargs = {}
    kwargs["radius1"] = radius
    kwargs["radius2"] = radius

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
    rot_mat = Matrix.Rotation(radians(90.0), 4, "Y")

    kwargs = {}
    kwargs["radius1"] = radius
    kwargs["radius2"] = radius

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
        raise ValueError("Cannot create capsule with a diameter less than 0!")

    bm = bmesh.new()

    kwargs = {}
    kwargs["radius"] = diameter

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
        mesh.transform(Matrix.Rotation(radians(90.0), 4, "X"))

    return mesh


def get_uv_map_name(index: int) -> str:
    return f"UVMap {index}"


def create_uv_attr(mesh: bpy.types.Mesh, coords: NDArray[np.float64], domain: str = "CORNER"):
    """Create a uv layer for ``mesh`` with the specified index."""
    uv_attr = mesh.attributes.new(name=get_uv_map_name(len(mesh.uv_layers)), type="FLOAT2", domain=domain)

    uv_attr.data.foreach_set("vector", coords.flatten())


def create_color_attr(mesh: bpy.types.Mesh, colors: NDArray[np.float64], domain: str = "CORNER"):
    """Create a color attribute layer for ``mesh`` with the specified index."""
    layer_num = len(mesh.color_attributes) + 1
    color_attr = mesh.attributes.new(
        name=f"Color {layer_num}", type="BYTE_COLOR", domain=domain)

    color_attr.data.foreach_set("color_srgb", colors.flatten())


def get_extents_from_points(points: list[tuple]):
    """Returns min, max"""
    # TODO: Use for all BB calculations
    x, y, z = zip(*points)

    return Vector((min(x), min(y), min(z))), Vector((max(x), max(y), max(z)))


def get_extents(obj: bpy.types.Object):
    """
    DEPRECATED. Use ``get_combined_bound_box``\n
    Get min and max extents for an object and all of its children
    """
    corners = get_total_bounds(obj)

    if not corners:
        return Vector(), Vector()

    min = get_min_vector_list(corners)
    max = get_max_vector_list(corners)

    return min, max


def get_total_bounds(obj):
    corners = []

    # Ensure all objects are meshes
    for child in [obj, *get_children_recursive(obj)]:
        if child.type != "MESH" or child.sollum_type == SollumType.NONE:
            continue

        matrix = child.matrix_basis

        if obj.sollum_type == SollumType.BOUND_COMPOSITE and child.parent.sollum_type != SollumType.BOUND_COMPOSITE:
            matrix = child.parent.matrix_basis @ matrix

        corners.extend([matrix @ Vector(pos)
                       for pos in child.bound_box])

    return corners


def get_combined_bound_box(obj: bpy.types.Object, use_world: bool = False, matrix: Matrix = Matrix()):
    """Adds the ``bound_box`` of ``obj`` and all of it's child mesh objects. Returhs bbmin, bbmax"""
    total_bounds: list[Vector] = []

    for child in [obj, *obj.children_recursive]:
        if child.type != "MESH":
            continue

        child_matrix = matrix @ (
            child.matrix_world if use_world else child.matrix_basis)

        total_bounds.extend([child_matrix @ Vector(v)
                            for v in child.bound_box])

    if not total_bounds:
        return Vector(), Vector()

    return get_min_vector_list(total_bounds), get_max_vector_list(total_bounds)


def get_bound_center(obj):
    bbmin, bbmax = get_extents(obj)
    center = (bbmin + bbmax) / 2

    return center


def get_bound_center_from_bounds(bbmin: Vector, bbmax: Vector):
    return (bbmin + bbmax) * 0.5


def get_sphere_radius(bbmax, bbcenter):
    """Gets the radius of the sphere that encloses the bounding box."""
    return (bbmax - bbcenter).length


def get_inner_sphere_radius(bbmax, bbcenter):
    """Gets the radius of the sphere that fits inside the bounding box."""
    return min(bbmax - bbcenter)


def get_dimensions(bbmin, bbmax):
    x = bbmax.x - bbmin.x
    y = bbmax.y - bbmin.y
    z = bbmax.z - bbmin.z

    return x, y, z


def calculate_volume(bbmin: Vector, bbmax: Vector):
    """Calculates volume using box min and max. (Very rough approximation)"""
    x, y, z = get_dimensions(bbmin, bbmax)

    return x * y * z


def calculate_inertia(bbmin: Vector, bbmax: Vector):
    """Calculate moment of inertia of a solid cuboid. Returns a Vector
    representing the diagonal of the inertia tensor matrix."""
    x, y, z = get_dimensions(bbmin, bbmax)

    I_h = (1 / 12) * (pow(y, 2) + pow(z, 2))
    I_w = (1 / 12) * (pow(z, 2) + pow(x, 2))
    I_d = (1 / 12) * (pow(y, 2) + pow(x, 2))

    return Vector((I_h, I_w, I_d))


def flip_uvs(uvs: NDArray[np.float32]):
    uvs[:, 1] = (uvs[:, 1] - 1.0) * -1


def flip_uv(uv):
    u = uv[0]
    v = (uv[1] - 1.0) * -1

    return [u, v]

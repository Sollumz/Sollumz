import bpy
import bmesh
import numpy as np
from numpy.typing import NDArray
from typing import Optional
from mathutils import Vector, Matrix
from mathutils.geometry import distance_point_to_plane
from math import radians
from ..sollumz_properties import SollumType, MaterialType
from .utils import get_min_vector_list, get_max_vector_list
from .blenderhelper import get_children_recursive
from ..cwxml.shader import ShaderManager


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
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=radius)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def create_cylinder(mesh, radius=1, length=2, axis="Y"):
    match axis:
        case "X":
            rot_mat = Matrix.Rotation(radians(90.0), 4, "Y")
        case "Y":
            rot_mat = Matrix.Rotation(radians(90.0), 4, "X")
        case "Z":
            rot_mat = Matrix()
        case _:
            raise ValueError(f"Invalid axis '{axis}'")
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=True,
        segments=32,
        depth=length,
        matrix=rot_mat,
        radius1=radius,
        radius2=radius,
    )
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def create_disc(mesh, radius=1, length=0.08):
    return create_cylinder(mesh, radius, length, axis="X")


def create_capsule(mesh, radius=0.5, length=2, use_rot=False):
    length = length if radius < length else radius
    if radius < 0:
        raise ValueError("Cannot create capsule with a radius less than 0!")

    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=radius)
    bm.to_mesh(mesh)

    center = Vector()
    axis = Vector((0, 0, 1))

    # Get top and bottom halves of vertices
    top = []
    top_faces = []
    bottom = []
    bottom_faces = []

    amount = (length - radius) * 2
    vec = Vector((0, 0, amount))

    for v in bm.verts:
        if distance_point_to_plane(v.co, center, axis) >= 0:
            top.append(v.co)
            for face in v.link_faces:
                if face not in top_faces:
                    top_faces.append(face)
        elif distance_point_to_plane(v.co, center, axis) <= 0:
            bottom.append(v.co)
            for face in v.link_faces:
                if face not in bottom_faces and face not in top_faces:
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


def get_tangent_required(material: bpy.types.Material):
    if material.sollum_type != MaterialType.SHADER:
        return False

    shader_name = material.shader_properties.filename

    shader = ShaderManager.find_shader(shader_name)
    if shader is None:
        return False

    return shader.required_tangent


def get_used_texcoords(material: bpy.types.Material) -> set[str]:
    """Get TexCoords that the material's shader uses"""
    if material.sollum_type != MaterialType.SHADER:
        return set()

    shader_name = material.shader_properties.filename

    shader = ShaderManager.find_shader(shader_name)
    if shader is None:
        return set()

    return shader.used_texcoords


def get_used_texcoords_indices(material: bpy.types.Material) -> set[int]:
    """Get TexCoords that the material's shader uses"""
    if material.sollum_type != MaterialType.SHADER:
        return set()

    shader_name = material.shader_properties.filename

    shader = ShaderManager.find_shader(shader_name)
    if shader is None:
        return set()

    return shader.used_texcoords_indices


def get_mesh_used_texcoords_indices(mesh: bpy.types.Mesh) -> set[int]:
    texcoords = set()
    texcoords = texcoords.union(*(get_used_texcoords_indices(mat) for mat in mesh.materials if mat is not None))
    return texcoords


def get_used_colors(material: bpy.types.Material) -> set[str]:
    """Get Colours that the material's shader uses"""
    if material.sollum_type != MaterialType.SHADER:
        return set()

    shader_name = material.shader_properties.filename

    shader = ShaderManager.find_shader(shader_name)
    if shader is None:
        return set()

    return shader.used_colors


def get_used_colors_indices(material: bpy.types.Material) -> set[int]:
    """Get Colours that the material's shader uses"""
    if material.sollum_type != MaterialType.SHADER:
        return set()

    shader_name = material.shader_properties.filename

    shader = ShaderManager.find_shader(shader_name)
    if shader is None:
        return set()

    return shader.used_colors_indices


def get_mesh_used_colors_indices(mesh: bpy.types.Mesh) -> set[int]:
    colors = set()
    colors = colors.union(*(get_used_colors_indices(mat) for mat in mesh.materials if mat is not None))
    return colors


def get_normal_required(material: bpy.types.Material):
    if material.sollum_type != MaterialType.SHADER:
        return False

    shader_name = material.shader_properties.filename

    shader = ShaderManager.find_shader(shader_name)
    if shader is None:
        return False

    return shader.required_normal


def get_uv_map_name(index: int) -> str:
    return f"UVMap {index}"


def get_color_attr_name(index: int) -> str:
    num = index + 1  # uh...
    return f"Color {num}"


def create_uv_attr(mesh: bpy.types.Mesh, uvmap_index: int, initial_values: Optional[NDArray[np.float64]] = None):
    """Create a UV map for ``mesh`` with the specified index."""
    attr = mesh.attributes.new(name=get_uv_map_name(uvmap_index), type="FLOAT2", domain="CORNER")

    if initial_values is not None:
        attr.data.foreach_set("vector", initial_values.flatten())


def create_color_attr(mesh: bpy.types.Mesh, color_index: int, initial_values: Optional[NDArray[np.float64]] = None):
    """Create a color attribute for ``mesh`` with the specified index."""
    attr = mesh.attributes.new(name=get_color_attr_name(color_index), type="BYTE_COLOR", domain="CORNER")

    if initial_values is not None:
        attr.data.foreach_set("color_srgb", initial_values.flatten())


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


def get_sphere_radius(bbmin: Vector, bbmax: Vector) -> float:
    """Gets the radius of the sphere that encloses the bounding box."""
    bbcenter = get_bound_center_from_bounds(bbmin, bbmax)
    return (bbmax - bbcenter).length


def get_inner_sphere_radius(bbmin: Vector, bbmax: Vector) -> float:
    """Gets the radius of the sphere that fits inside the bounding box."""
    bbcenter = get_bound_center_from_bounds(bbmin, bbmax)
    return min(bbmax - bbcenter)


def get_dimensions(bbmin: Vector, bbmax: Vector) -> Vector:
    return bbmax - bbmin


def flip_uvs(uvs: NDArray[np.float32]):
    uvs[:, 1] = (uvs[:, 1] - 1.0) * -1


def flip_uv(uv):
    u = uv[0]
    v = (uv[1] - 1.0) * -1

    return [u, v]

import bpy
from bpy.types import (
    Object,
    Material,
    Mesh,
)
import numpy as np
from typing import Optional
from szio.gta5 import (
    AssetBound,
    BoundType,
    CollisionFlags,
    CollisionMaterial,
    BoundPrimitive,
    BoundPrimitiveType,
    BoundVertex,
)
from ..sollumz_properties import SollumType, SOLLUMZ_UI_NAMES
from .collision_materials import create_collision_material_from_data
from ..tools.meshhelper import (
    create_box,
    create_sphere,
    create_cylinder,
    create_capsule,
    create_disc,
    create_plane,
    create_color_attr,
)
from ..tools.utils import get_direction_of_vectors, abs_vector
from ..tools.blenderhelper import create_blender_object, create_empty_object
from mathutils import Matrix, Vector
from math import radians


def import_ybn(asset: AssetBound, name: str):
    assert asset.bound_type == BoundType.COMPOSITE, "Only Bound Composite import is supported"
    return create_bound_composite(asset, name)


def create_bound_composite(composite: AssetBound, name: Optional[str] = None, out_children: list[Object | None] | None = None) -> Object:
    obj = create_empty_object(SollumType.BOUND_COMPOSITE, name)

    for child in composite.children:
        child_obj = create_bound_object(child)
        if out_children is not None:
            out_children.append(child_obj)

        if child_obj is None:
            continue

        child_obj.parent = obj

    return obj


def create_bound_object(bound: AssetBound) -> Object:
    """Create a bound object based on ``bound_xml.type``"""
    match bound.bound_type:
        case BoundType.BOX:
            return create_bound_box(bound)
        case BoundType.SPHERE:
            return create_bound_sphere(bound)
        case BoundType.CAPSULE:
            return create_bound_capsule(bound)
        case BoundType.CYLINDER:
            return create_bound_cylinder(bound)
        case BoundType.DISC:
            return create_bound_disc(bound)
        case BoundType.PLANE:
            return create_bound_plane(bound)
        case BoundType.GEOMETRY:
            return create_bound_geometry(bound)
        case BoundType.BVH:
            return create_bound_bvh(bound)
        case _:
            raise ValueError(f"Unsupported bound type '{bound.bound_type.name}'")


def create_bound_child_mesh(bound: AssetBound, sollum_type: SollumType, mesh: Optional[bpy.types.Mesh] = None) -> Object:
    """Create a bound mesh object with materials and composite properties set."""
    obj = create_blender_object(sollum_type, object_data=mesh)

    mat = create_collision_material_from_data(bound.material)
    obj.data.materials.append(mat)

    set_composite_flags(bound, obj)
    obj.matrix_world = bound.composite_transform.transposed()

    return obj


def set_composite_flags(bound: AssetBound, bound_obj: bpy.types.Object):
    def set_flags(flags: CollisionFlags, flags_propname: str):
        # properties still use the CW names for backwards compatibility
        from szio.gta5.cwxml.adapters.bound import CW_COLLISION_FLAGS_INVERSE_MAP

        flag_props = getattr(bound_obj, flags_propname)
        for flag in flags:
            flag_propname = CW_COLLISION_FLAGS_INVERSE_MAP[flag].lower()
            setattr(flag_props, flag_propname, True)

    set_flags(bound.composite_collision_type_flags, "composite_flags1")
    set_flags(bound.composite_collision_include_flags, "composite_flags2")


def create_bound_box(bound: AssetBound) -> Object:
    obj = create_bound_child_mesh(bound, SollumType.BOUND_BOX)
    bound_dimensions = abs_vector(bound.bb_max - bound.bb_min)
    create_box(obj.data, 1, Matrix.Diagonal(bound_dimensions))
    obj.location += bound.centroid
    return obj


def create_bound_sphere(bound: AssetBound) -> Object:
    obj = create_bound_child_mesh(bound, SollumType.BOUND_SPHERE)
    create_sphere(obj.data, bound.sphere_radius)
    obj.location += bound.centroid
    return obj


def create_bound_capsule(bound: AssetBound) -> Object:
    obj = create_bound_child_mesh(bound, SollumType.BOUND_CAPSULE)
    radius, length = bound.capsule_radius_length
    create_capsule(obj.data, radius=radius, length=length, axis="Y")
    obj.location += bound.centroid
    return obj


def create_bound_cylinder(bound: AssetBound) -> Object:
    obj = create_bound_child_mesh(bound, SollumType.BOUND_CYLINDER)
    radius, length = bound.cylinder_radius_length
    create_cylinder(obj.data, radius=radius, length=length, axis="Y")
    obj.location += bound.centroid
    return obj


def create_bound_disc(bound: AssetBound):
    obj = create_bound_child_mesh(bound, SollumType.BOUND_DISC)
    create_disc(obj.data, bound.disc_radius, bound.margin * 2)
    obj.location += bound.centroid
    return obj


def create_bound_plane(bound: AssetBound):
    obj = create_bound_child_mesh(bound, SollumType.BOUND_PLANE)
    # matrix to rotate plane so it faces towards +Y, by default faces +Z
    create_plane(obj.data, 2.0, matrix=Matrix.Rotation(radians(90.0), 4, "X"))
    obj.matrix_world = Matrix.LocRotScale(bound.centroid, bound.plane_normal.to_track_quat("Y", "Z"), None)
    return obj


def create_bound_geometry(bound: AssetBound) -> Object:
    mesh = create_bound_geometry_triangle_mesh(bound.geometry_vertices, bound.geometry_primitives, Vector())

    obj = create_blender_object(SollumType.BOUND_GEOMETRY, object_data=mesh)

    set_composite_flags(bound, obj)
    obj.matrix_world = bound.composite_transform.transposed()
    # obj.location += bound.geometry_center

    return obj


def create_bound_bvh(bound: AssetBound) -> Object:
    obj = create_empty_object(SollumType.BOUND_GEOMETRYBVH)

    set_composite_flags(bound, obj)
    obj.matrix_world = bound.composite_transform.transposed()

    create_bound_bvh_primitives(bound, obj)

    return obj


def create_bound_bvh_primitives(bound: AssetBound, bvh_obj: Object) -> list[Object]:
    triangles = []
    primitive_objects = []

    vertices = bound.geometry_vertices
    materials_cache = {}
    for prim in bound.geometry_primitives:
        if prim.primitive_type == BoundPrimitiveType.TRIANGLE:
            triangles.append(prim)
        else:
            prim_obj = create_bound_primitive(prim, vertices, materials_cache)
            prim_obj.parent = bvh_obj
            primitive_objects.append(prim_obj)

    if triangles:
        center = bound.geometry_center
        mesh = create_bound_geometry_triangle_mesh(vertices, triangles, center, materials_cache)
        mesh_obj = create_blender_object(SollumType.BOUND_POLY_TRIANGLE, object_data=mesh)
        mesh_obj.location = center
        mesh_obj.parent = bvh_obj
        primitive_objects.append(mesh_obj)

    return primitive_objects


def create_bound_primitive(primitive: BoundPrimitive, vertices: list[BoundVertex], materials_cache: dict[CollisionMaterial, Material]) -> Object:
    return PRIM_TO_OBJ_MAP[primitive.primitive_type.value](primitive, vertices, materials_cache)


def create_bound_primitive_object(primitive: BoundPrimitive, sz_type: SollumType, materials_cache: dict[CollisionMaterial, Material]) -> Object:
    name = SOLLUMZ_UI_NAMES[sz_type]
    mesh = bpy.data.meshes.new(name)

    material = materials_cache.get(primitive.material, None)
    if material is None:
        material = create_collision_material_from_data(primitive.material)
        materials_cache[primitive.material] = material
    mesh.materials.append(material)

    obj = create_blender_object(sz_type, name, mesh)
    return obj


def create_bound_primitive_box(primitive: BoundPrimitive, vertices: list[BoundVertex], materials_cache: dict[CollisionMaterial, Material]) -> Object:
    obj = create_bound_primitive_object(primitive, SollumType.BOUND_POLY_BOX, materials_cache)

    v1, v2, v3, v4 = primitive.vertices
    v1 = vertices[v1].co
    v2 = vertices[v2].co
    v3 = vertices[v3].co
    v4 = vertices[v4].co
    center = (v1 + v2 + v3 + v4) * 0.25

    # Get edges from the 4 opposing corners of the box
    a1 = ((v3 + v4) - (v1 + v2)) * 0.5
    v2 = v1 + a1
    v3 = v3 - a1
    v4 = v4 - a1

    minedge = Vector((0.0001, 0.0001, 0.0001))
    edge1 = max(v2 - v1, minedge)
    edge2 = max(v3 - v1, minedge)
    edge3 = max((v4 - v1), minedge)

    # Order edges
    s1 = False
    s2 = False
    s3 = False
    if edge2.length > edge1.length:
        t1 = edge1
        edge1 = edge2
        edge2 = t1
        s1 = True
    if edge3.length > edge1.length:
        t1 = edge1
        edge1 = edge3
        edge3 = t1
        s2 = True
    if edge3.length > edge2.length:
        t1 = edge2
        edge2 = edge3
        edge3 = t1
        s3 = True

    # Ensure all edge vectors are perpendicular to each other
    b1 = edge1.normalized()
    b2 = edge2.normalized()
    b3 = b1.cross(b2).normalized()
    b2 = b1.cross(b3).normalized()
    edge2 = b2 * edge2.dot(b2)
    edge3 = b3 * edge3.dot(b3)

    # Unswap edges
    if s3:
        t1 = edge2
        edge2 = edge3
        edge3 = t1
    if s2:
        t1 = edge1
        edge1 = edge3
        edge3 = t1
    if s1:
        t1 = edge1
        edge1 = edge2
        edge2 = t1

    mat = Matrix()
    mat[0] = edge1.x, edge2.x, edge3.x, center.x
    mat[1] = edge1.y, edge2.y, edge3.y, center.y
    mat[2] = edge1.z, edge2.z, edge3.z, center.z

    create_box(obj.data, size=1)
    obj.matrix_basis = mat

    return obj


def create_bound_primitive_sphere(primitive: BoundPrimitive, vertices: list[BoundVertex], materials_cache: dict[CollisionMaterial, Material]) -> Object:
    obj = create_bound_primitive_object(primitive, SollumType.BOUND_POLY_SPHERE, materials_cache)
    create_sphere(obj.data, primitive.radius)
    obj.location = vertices[primitive.vertices[0]].co
    return obj
#


def create_bound_primitive_capsule(primitive: BoundPrimitive, vertices: list[BoundVertex], materials_cache: dict[CollisionMaterial, Material]) -> Object:
    obj = create_bound_primitive_object(primitive, SollumType.BOUND_POLY_CAPSULE, materials_cache)
    v1, v2 = primitive.vertices
    v1 = vertices[v1].co
    v2 = vertices[v2].co

    rot = get_direction_of_vectors(v1, v2)
    length = (v1 - v2).length
    create_capsule(obj.data, radius=primitive.radius, length=length, axis="Z")

    obj.location = (v1 + v2) / 2
    obj.rotation_euler = rot

    return obj


def create_bound_primitive_cylinder(primitive: BoundPrimitive, vertices: list[BoundVertex], materials_cache: dict[CollisionMaterial, Material]) -> Object:
    obj = create_bound_primitive_object(primitive, SollumType.BOUND_POLY_CYLINDER, materials_cache)
    v1, v2 = primitive.vertices
    v1 = vertices[v1].co
    v2 = vertices[v2].co

    rot = get_direction_of_vectors(v1, v2)
    length = (v1 - v2).length
    create_cylinder(obj.data, radius=primitive.radius, length=length, axis="Z")

    obj.matrix_world = Matrix()

    obj.location = (v1 + v2) / 2
    obj.rotation_euler = rot

    return obj


PRIM_TO_OBJ_MAP = [None] * len(BoundPrimitiveType)
PRIM_TO_OBJ_MAP[BoundPrimitiveType.BOX.value] = create_bound_primitive_box
PRIM_TO_OBJ_MAP[BoundPrimitiveType.SPHERE.value] = create_bound_primitive_sphere
PRIM_TO_OBJ_MAP[BoundPrimitiveType.CAPSULE.value] = create_bound_primitive_capsule
PRIM_TO_OBJ_MAP[BoundPrimitiveType.CYLINDER.value] = create_bound_primitive_cylinder


def create_bound_geometry_triangle_mesh(
    vertices: list[BoundVertex],
    triangles: list[BoundPrimitive],
    geometry_center: Vector,
    materials_cache: Optional[dict[CollisionMaterial, Material]] = None,
) -> Mesh:
    def _color_to_float(color_int: tuple[int, int, int, int]):
        return (color_int[0] / 255, color_int[1] / 255, color_int[2] / 255, color_int[3] / 255)

    verts = []
    verts_dict = {}
    faces = []
    face_material_indices = []
    colors = [] if vertices[0].color is not None else None

    materials: list[Material] = []
    materials_indices: dict[CollisionMaterial, int] = {}
    has_materials_cache = materials_cache is not None

    for tri in triangles:
        face = []
        v1, v2, v3 = tri.vertices
        for v in [vertices[v1], vertices[v2], vertices[v3]]:
            v_co = v.co - geometry_center
            v_tuple = tuple(v_co)
            if v_tuple not in verts_dict:
                verts_dict[v_tuple] = len(verts)
                verts.append(v_co)
            face.append(verts_dict[v_tuple])

            if colors is not None:
                colors.append(_color_to_float(v.color))

        faces.append(face)

        material_index = materials_indices.get(tri.material, None)
        if material_index is None:
            material_index = len(materials)
            material = materials_cache.get(tri.material, None) if has_materials_cache else None
            if material is None:
                material = create_collision_material_from_data(tri.material)
                if has_materials_cache:
                    materials_cache[tri.material] = material
            materials.append(material)
            materials_indices[tri.material] = material_index

        face_material_indices.append(material_index)

    mesh = bpy.data.meshes.new(SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRY])
    mesh.from_pydata(verts, [], faces)

    if colors is not None:
        create_color_attr(mesh, 0, initial_values=np.array(colors))

    for m in materials:
        mesh.materials.append(m)

    mesh.polygons.foreach_set("material_index", face_material_indices)

    mesh.validate()
    return mesh

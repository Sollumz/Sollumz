import os
import bpy
from typing import Optional
import numpy as np
from numpy.typing import NDArray
from .properties import CollisionMatFlags, set_collision_mat_raw_flags
from ..cwxml.bound import (
    Bound,
    BoundFile,
    BoundComposite,
    BoundChild,
    BoundGeometryBVH,
    BoundGeometry,
    BoundPlane,
    PolyBox,
    PolySphere,
    PolyCapsule,
    PolyCylinder,
    PolyTriangle,
    YBN,
    Polygon,
    Material as ColMaterial
)
from ..sollumz_properties import SollumType, SOLLUMZ_UI_NAMES
from .collision_materials import create_collision_material_from_index
from ..tools.meshhelper import (
    create_box,
    create_sphere,
    create_cylinder,
    create_capsule,
    create_disc,
    create_plane,
    create_color_attr,
)
from ..tools.utils import get_direction_of_vectors, get_distance_of_vectors, abs_vector
from ..tools.blenderhelper import create_blender_object, create_empty_object
from mathutils import Matrix, Vector
from math import radians


def import_ybn(filepath):
    ybn_xml: BoundFile = YBN.from_xml_file(filepath)
    return create_bound_composite(ybn_xml.composite, os.path.basename(filepath.replace(YBN.file_extension, "")))


def create_bound_composite(composite_xml: BoundComposite, name: Optional[str] = None):
    obj = create_empty_object(SollumType.BOUND_COMPOSITE, name)

    for child in composite_xml.children:
        child_obj = create_bound_object(child)

        if child_obj is None:
            continue

        child_obj.parent = obj

    return obj


def create_bound_object(bound_xml: BoundChild | Bound):
    """Create a bound object based on ``bound_xml.type``"""
    if bound_xml.type == "Box":
        return create_bound_box(bound_xml)

    if bound_xml.type == "Sphere":
        return create_bound_sphere(bound_xml)

    if bound_xml.type == "Capsule":
        return create_bound_capsule(bound_xml)

    if bound_xml.type == "Cylinder":
        return create_bound_cylinder(bound_xml)

    if bound_xml.type == "Disc":
        return create_bound_disc(bound_xml)

    if bound_xml.type == "Geometry":
        return create_bound_geometry(bound_xml)

    if bound_xml.type == "GeometryBVH":
        return create_bvh_obj(bound_xml)

    if bound_xml.type == BoundPlane.type:
        return create_bound_plane(bound_xml)


def create_bound_child_mesh(bound_xml: BoundChild, sollum_type: SollumType, mesh: Optional[bpy.types.Mesh] = None):
    """Create a bound mesh object with materials and composite properties set."""
    obj = create_blender_object(sollum_type, object_data=mesh)

    mat = create_collision_material_from_index(bound_xml.material_index)
    set_bound_col_material_properties(bound_xml, mat)
    obj.data.materials.append(mat)

    set_bound_child_properties(bound_xml, obj)

    return obj


def set_composite_transforms(transforms: Matrix, bound_obj: bpy.types.Object):
    bound_obj.matrix_world = transforms.transposed()


def set_composite_flags(bound_xml: BoundChild, bound_obj: bpy.types.Object):
    def set_flags(flags_propname: str):
        flags = getattr(bound_xml, flags_propname)
        for flag in flags:
            flag_props = getattr(bound_obj, flags_propname)

            setattr(flag_props, flag.lower(), True)

    set_flags("composite_flags1")
    set_flags("composite_flags2")


def create_bound_box(bound_xml: BoundChild):
    obj = create_bound_child_mesh(bound_xml, SollumType.BOUND_BOX)
    bound_dimensions = abs_vector(bound_xml.box_max - bound_xml.box_min)
    create_box(obj.data, 1, Matrix.Diagonal(bound_dimensions))
    obj.location += bound_xml.box_center
    return obj


def create_bound_sphere(bound_xml: BoundChild):
    obj = create_bound_child_mesh(bound_xml, SollumType.BOUND_SPHERE)
    create_sphere(obj.data, bound_xml.sphere_radius)
    obj.location += bound_xml.box_center
    return obj


def create_bound_capsule(bound_xml: BoundChild):
    obj = create_bound_child_mesh(bound_xml, SollumType.BOUND_CAPSULE)
    bbmin, bbmax = bound_xml.box_min, bound_xml.box_max
    extent = bbmax - bbmin
    radius = extent.x * 0.5
    length = extent.y - (radius * 2.0)
    create_capsule(obj.data, radius=radius, length=length, axis="Y")
    obj.location += bound_xml.box_center
    return obj


def create_bound_cylinder(bound_xml: BoundChild):
    obj = create_bound_child_mesh(bound_xml, SollumType.BOUND_CYLINDER)
    bbmin, bbmax = bound_xml.box_min, bound_xml.box_max
    extent = bbmax - bbmin
    radius = extent.x * 0.5
    length = extent.y
    create_cylinder(obj.data, radius=radius, length=length, axis="Y")
    obj.location += bound_xml.box_center
    return obj


def create_bound_disc(bound_xml: BoundChild):
    obj = create_bound_child_mesh(bound_xml, SollumType.BOUND_DISC)
    create_disc(obj.data, bound_xml.sphere_radius, bound_xml.margin * 2)
    obj.location += bound_xml.box_center
    return obj


def create_bound_plane(bound_xml: BoundPlane):
    obj = create_bound_child_mesh(bound_xml, SollumType.BOUND_PLANE)
    # matrix to rotate plane so it faces towards +Y, by default faces +Z
    create_plane(obj.data, 2.0, matrix=Matrix.Rotation(radians(90.0), 4, "X"))
    obj.matrix_world = Matrix.LocRotScale(bound_xml.box_center, bound_xml.normal.to_track_quat("Y", "Z"), None)
    return obj


def create_bound_geometry(geom_xml: BoundGeometry):
    materials = create_geometry_materials(geom_xml)
    triangles = get_poly_triangles(geom_xml.polygons)

    mesh = create_bound_mesh_data(geom_xml.vertices, triangles, geom_xml.vertex_colors, materials)
    mesh.transform(Matrix.Translation(geom_xml.geometry_center))

    geom_obj = create_blender_object(SollumType.BOUND_GEOMETRY, object_data=mesh)
    set_bound_child_properties(geom_xml, geom_obj)
    return geom_obj


def create_bvh_obj(bvh_xml: BoundGeometryBVH):
    bvh_obj = create_empty_object(SollumType.BOUND_GEOMETRYBVH)
    set_bound_child_properties(bvh_xml, bvh_obj)

    materials = create_geometry_materials(bvh_xml)

    create_bvh_polys(bvh_xml, materials, bvh_obj)

    triangles = get_poly_triangles(bvh_xml.polygons)

    if triangles:
        mesh = create_bound_mesh_data(bvh_xml.vertices, triangles, bvh_xml.vertex_colors, materials)
        bound_geom_obj = create_blender_object(SollumType.BOUND_POLY_TRIANGLE, object_data=mesh)
        bound_geom_obj.location = bvh_xml.geometry_center
        bound_geom_obj.parent = bvh_obj

    return bvh_obj


def create_geometry_materials(geometry: BoundGeometryBVH):
    materials: list[bpy.types.Material] = []

    mat_xml: ColMaterial
    for mat_xml in geometry.materials:
        mat = create_collision_material_from_index(mat_xml.type)
        set_col_material_properties(mat_xml, mat)

        materials.append(mat)

    return materials


def set_col_material_properties(mat_xml: ColMaterial, mat: bpy.types.Material):
    mat.collision_properties.procedural_id = mat_xml.procedural_id
    mat.collision_properties.room_id = mat_xml.room_id
    mat.collision_properties.ped_density = mat_xml.ped_density
    mat.collision_properties.material_color_index = mat_xml.material_color_index
    for flag_name in CollisionMatFlags.__annotations__.keys():
        if f"FLAG_{flag_name.upper()}" not in mat_xml.flags:
            continue

        setattr(mat.collision_flags, flag_name, True)


def set_bound_col_material_properties(bound_xml: Bound, mat: bpy.types.Material):
    mat.collision_properties.procedural_id = bound_xml.procedural_id
    mat.collision_properties.room_id = bound_xml.room_id
    mat.collision_properties.ped_density = bound_xml.ped_density
    mat.collision_properties.material_color_index = bound_xml.material_color_index
    set_collision_mat_raw_flags(mat.collision_flags, bound_xml.unk_flags, bound_xml.poly_flags)


def create_bvh_polys(bvh: BoundGeometryBVH, materials: list[bpy.types.Material], bvh_obj: bpy.types.Object):
    for poly in bvh.polygons:
        if type(poly) is PolyTriangle:
            continue

        poly_obj = poly_to_obj(poly, materials, bvh.vertices)
        poly_obj.location += bvh.geometry_center
        poly_obj.parent = bvh_obj


def init_poly_obj(poly, sollum_type, materials):
    name = SOLLUMZ_UI_NAMES[sollum_type]
    mesh = bpy.data.meshes.new(name)
    if poly.material_index < len(materials):
        mesh.materials.append(materials[poly.material_index])

    obj = create_blender_object(sollum_type, name, mesh)
    return obj


def create_poly_box(poly, materials, vertices):
    obj = init_poly_obj(poly, SollumType.BOUND_POLY_BOX, materials)

    v1 = vertices[poly.v1]
    v2 = vertices[poly.v2]
    v3 = vertices[poly.v3]
    v4 = vertices[poly.v4]
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
    if s3 == True:
        t1 = edge2
        edge2 = edge3
        edge3 = t1
    if s2 == True:
        t1 = edge1
        edge1 = edge3
        edge3 = t1
    if s1 == True:
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


def create_poly_sphere(poly, materials, vertices):
    sphere = init_poly_obj(poly, SollumType.BOUND_POLY_SPHERE, materials)
    create_sphere(sphere.data, poly.radius)
    sphere.location = vertices[poly.v]
    return sphere


def create_poly_capsule(poly, materials, vertices):
    capsule = init_poly_obj(poly, SollumType.BOUND_POLY_CAPSULE, materials)
    v1 = vertices[poly.v1]
    v2 = vertices[poly.v2]
    rot = get_direction_of_vectors(v1, v2)
    length = (v1 - v2).length
    create_capsule(capsule.data, radius=poly.radius, length=length, axis="Z")

    capsule.location = (v1 + v2) / 2
    capsule.rotation_euler = rot

    return capsule


def create_poly_cylinder(poly, materials, vertices):
    cylinder = init_poly_obj(poly, SollumType.BOUND_POLY_CYLINDER, materials)
    v1 = vertices[poly.v1]
    v2 = vertices[poly.v2]

    rot = get_direction_of_vectors(v1, v2)

    radius = poly.radius
    length = get_distance_of_vectors(v1, v2)
    create_cylinder(cylinder.data, radius=radius, length=length, axis="Z")

    cylinder.matrix_world = Matrix()

    cylinder.location = (v1 + v2) / 2
    cylinder.rotation_euler = rot

    return cylinder


POLY_TO_OBJ_MAP = {
    PolyBox: create_poly_box,
    PolySphere: create_poly_sphere,
    PolyCapsule: create_poly_capsule,
    PolyCylinder: create_poly_cylinder,
}


def poly_to_obj(poly, materials, vertices) -> bpy.types.Object:
    return POLY_TO_OBJ_MAP[type(poly)](poly, materials, vertices)


def get_poly_triangles(polys: list[Polygon]):
    return [poly for poly in polys if isinstance(poly, PolyTriangle)]


def create_bound_mesh_data(
    vertices: list[Vector],
    triangles: list[PolyTriangle],
    vertex_colors: Optional[list[tuple[int, int, int, int]]],
    materials: list[bpy.types.Material]
) -> bpy.types.Mesh:
    mesh = bpy.data.meshes.new(SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRY])

    verts, faces, colors = get_bound_geom_mesh_data(vertices, triangles, vertex_colors)

    mesh.from_pydata(verts, [], faces)

    if colors is not None:
        create_color_attr(mesh, 0, initial_values=colors)

    apply_bound_geom_materials(mesh, triangles, materials)

    mesh.validate()

    return mesh


def apply_bound_geom_materials(mesh: bpy.types.Mesh, triangles: list[PolyTriangle], materials: list[bpy.types.Material]):
    for mat in materials:
        mesh.materials.append(mat)

    for i, poly_xml in enumerate(triangles):
        mesh.polygons[i].material_index = poly_xml.material_index


def get_bound_geom_mesh_data(
    vertices: list[Vector],
    triangles: list[PolyTriangle],
    vertex_colors: Optional[list[tuple[int, int, int, int]]]
) -> tuple[list, list, Optional[NDArray]]:
    def _color_to_float(color_int: tuple[int, int, int, int]):
        return (color_int[0] / 255, color_int[1] / 255, color_int[2] / 255, color_int[3] / 255)

    verts = []
    verts_dict = {}
    faces = []
    colors = [] if vertex_colors else None

    for poly in triangles:
        face = []
        for v in [vertices[poly.v1], vertices[poly.v2], vertices[poly.v3]]:
            v_tuple = tuple(v)
            if v_tuple not in verts_dict:
                verts_dict[v_tuple] = len(verts)
                verts.append(v)
            face.append(verts_dict[v_tuple])
        faces.append(face)

        if colors is not None:
            colors.extend(_color_to_float(vertex_colors[v]) for v in [poly.v1, poly.v2, poly.v3])

    return verts, faces, np.array(colors, dtype=np.float64) if colors is not None else None


def set_bound_child_properties(bound_xml: BoundChild, bound_obj: bpy.types.Object):
    set_composite_flags(bound_xml, bound_obj)
    set_composite_transforms(bound_xml.composite_transform, bound_obj)

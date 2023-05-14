import bpy
from mathutils import Vector, Matrix
from typing import Optional, TypeVar, Callable, Type
from ..cwxml.bound import (
    BoundFile,
    Bound,
    BoundComposite,
    BoundGeometry,
    BoundGeometryBVH,
    BoundChild,
    BoundBox,
    BoundSphere,
    BoundCapsule,
    BoundCylinder,
    BoundDisc,
    PolyTriangle,
    PolyBox,
    PolySphere,
    PolyCapsule,
    PolyCylinder,
    Material
)
from ..tools.utils import get_max_vector_list, get_min_vector_list
from ..tools.meshhelper import (get_bound_center_from_bounds, calculate_volume,
                                calculate_inertia, get_sphere_radius, get_bound_center, get_combined_bound_box)
from ..sollumz_properties import MaterialType, SOLLUMZ_UI_NAMES, SollumType, BOUND_POLYGON_TYPES
from ..sollumz_preferences import get_export_settings
from .. import logger
from .properties import CollisionMatFlags, BoundFlags

T_Bound = TypeVar("T_Bound", bound=Bound)
T_BoundChild = TypeVar("T_BoundChild", bound=BoundChild)
T_PolyCylCap = TypeVar("T_PolyCylCap", bound=PolyCylinder | PolyCapsule)

MAX_VERTICES = 32767


def export_ybn(obj: bpy.types.Object, filepath: str):
    export_settings = get_export_settings()

    bounds = BoundFile()

    composite = create_composite_xml(
        obj, export_settings.auto_calculate_inertia, export_settings.auto_calculate_volume)
    bounds.composite = composite

    bounds.write_xml(filepath)


def create_composite_xml(obj: bpy.types.Object, auto_calc_inertia: bool = False, auto_calc_volume: bool = False, parent_inverse: Matrix = Matrix()):
    composite_xml = BoundComposite()

    for child in obj.children:
        child_xml = create_bound_xml(
            child, auto_calc_inertia, auto_calc_volume, parent_inverse)

        if child_xml is None:
            continue

        composite_xml.children.append(child_xml)

    # Calculate extents after children have been created
    bbmin, bbmax = get_composite_extents(composite_xml)
    set_bound_extents(composite_xml, bbmin, bbmax)
    init_bound_xml(composite_xml, obj, auto_calc_volume=auto_calc_volume)

    return composite_xml


def create_bound_xml(obj: bpy.types.Object, auto_calc_inertia: bool = False, auto_calc_volume: bool = False, parent_inverse: Matrix = Matrix()):
    """Create a ``Bound`` instance based on `obj.sollum_type``."""
    if (obj.type == "MESH" and not has_col_mats(obj)) or (obj.type == "EMPTY" and not bound_geom_has_mats(obj)):
        logger.warning(f"'{obj.name}' has no collision materials! Skipping...")
        return

    if obj.sollum_type == SollumType.BOUND_BOX:
        return init_bound_child_xml(BoundBox(), obj, auto_calc_inertia, auto_calc_volume, parent_inverse)

    if obj.sollum_type == SollumType.BOUND_DISC:
        disc_xml = init_bound_child_xml(
            BoundDisc(), obj, auto_calc_inertia, auto_calc_volume, parent_inverse)
        # For some reason the get_sphere_radius calculation does not work for bound discs
        disc_xml.sphere_radius = obj.bound_radius

        return disc_xml

    if obj.sollum_type == SollumType.BOUND_SPHERE:
        return init_bound_child_xml(BoundSphere(), obj, auto_calc_inertia, auto_calc_volume, parent_inverse)

    if obj.sollum_type == SollumType.BOUND_CYLINDER:
        return init_bound_child_xml(BoundCylinder(), obj, auto_calc_inertia, auto_calc_volume, parent_inverse)

    if obj.sollum_type == SollumType.BOUND_CAPSULE:
        return init_bound_child_xml(BoundCapsule(), obj, auto_calc_inertia, auto_calc_volume, parent_inverse)

    if obj.sollum_type == SollumType.BOUND_GEOMETRY:
        return create_bound_geometry_xml(obj, auto_calc_inertia, auto_calc_volume, parent_inverse)

    if obj.sollum_type == SollumType.BOUND_GEOMETRYBVH:
        return create_bvh_xml(obj, auto_calc_inertia, auto_calc_volume, parent_inverse)


def has_col_mats(obj: bpy.types.Object):
    col_mats = [
        mat for mat in obj.data.materials if mat.sollum_type == MaterialType.COLLISION]

    return len(col_mats) > 0


def bound_geom_has_mats(geom_obj: bpy.types.Object):
    mats: list[bpy.types.Material] = []

    for child in geom_obj.children:
        if child.type != "MESH":
            continue

        mats.extend(
            [mat for mat in child.data.materials if mat.sollum_type == MaterialType.COLLISION])

    return len(mats) > 0


def init_bound_child_xml(bound_xml: T_BoundChild, obj: bpy.types.Object, auto_calc_inertia: bool = False, auto_calc_volume: bool = False, parent_inverse: Matrix = Matrix()):
    """Initialize ``bound_xml`` bound child properties from object blender properties."""
    if obj.type == "MESH":
        bbmin, bbmax = get_bound_extents(obj)
    elif obj.type == "EMPTY":
        bbmin, bbmax = get_bvh_extents(obj)
    else:
        return bound_xml

    set_bound_extents(bound_xml, bbmin, bbmax)

    bound_xml = init_bound_xml(
        bound_xml, obj, auto_calc_inertia, auto_calc_volume)

    set_composite_xml_flags(bound_xml, obj)
    set_composite_xml_transforms(bound_xml, obj, parent_inverse)
    set_bound_xml_mat_index(bound_xml, obj)

    return bound_xml


def init_bound_xml(bound_xml: T_Bound, obj: bpy.types.Object, auto_calc_inertia: bool = False, auto_calc_volume: bool = False):
    """Initialize ``bound_xml`` bound properties from object blender properties. Extents need to be calculated before inertia and volume."""
    set_bound_properties(bound_xml, obj)

    if auto_calc_inertia:
        bound_xml.inertia = calculate_inertia(
            bound_xml.box_min, bound_xml.box_max)

    if auto_calc_volume:
        bound_xml.volume = calculate_volume(
            bound_xml.box_min, bound_xml.box_max)

    return bound_xml


def create_bound_geometry_xml(obj: bpy.types.Object, auto_calc_inertia: bool = False, auto_calc_volume: bool = False, parent_inverse: Matrix = Matrix()):
    geom_xml = init_bound_child_xml(
        BoundGeometry(), obj, auto_calc_inertia, auto_calc_volume, parent_inverse)
    set_bound_geom_xml_properties(geom_xml, obj)
    geom_xml.material_index = 0

    create_bound_geom_xml_data(geom_xml, obj, parent_inverse)

    return geom_xml


def create_bvh_xml(obj: bpy.types.Object, auto_calc_inertia: bool = False, auto_calc_volume: bool = False, parent_inverse: Matrix = Matrix()):
    geom_xml = init_bound_child_xml(
        BoundGeometryBVH(), obj, auto_calc_inertia, auto_calc_volume, parent_inverse)
    geom_xml.material_index = 0

    create_bound_geom_xml_data(geom_xml, obj, parent_inverse)

    return geom_xml


def create_bound_geom_xml_data(geom_xml: BoundGeometry | BoundGeometryBVH, obj: bpy.types.Object, parent_inverse: Matrix = Matrix()):
    """Create the vertices, polygons, and vertex colors of a ``BoundGeometry`` or ``BoundGeometryBVH`` from ``obj``."""
    geom_xml.geometry_center = get_bound_center(obj) - obj.location

    create_bound_xml_polys(geom_xml, obj, parent_inverse)

    num_vertices = len(geom_xml.vertices)

    if num_vertices == 0:
        logger.warning(
            f"{SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRY]} '{obj.name}' has no geometry!")

    if num_vertices > MAX_VERTICES:
        logger.warning(
            f"{SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRY]} '{obj.name}' exceeds maximum vertex limit of {MAX_VERTICES} (has {num_vertices}!")


def create_bound_xml_polys(geom_xml: BoundGeometry | BoundGeometryBVH, obj: bpy.types.Object, parent_inverse: Matrix = Matrix()):
    # Create mappings of vertices and materials by index to build the new geom_xml vertices
    ind_by_vert: dict[tuple, int] = {}
    ind_by_mat: dict[bpy.types.Material, int] = {}

    def get_vert_index(vert: Vector):
        # Must be tuple since Vector is not hashable
        vertex = tuple(vert)

        if vertex in ind_by_vert:
            return ind_by_vert[vertex]

        vert_ind = len(ind_by_vert)
        ind_by_vert[vertex] = vert_ind
        geom_xml.vertices.append(Vector(vertex))

        return vert_ind

    def get_mat_index(mat: bpy.types.Material):
        if mat in ind_by_mat:
            return ind_by_mat[mat]

        mat_xml = create_col_mat_xml(mat)
        mat_ind = len(geom_xml.materials)
        geom_xml.materials.append(mat_xml)

        ind_by_mat[mat] = mat_ind

        return mat_ind

    # If the bound object is a mesh, just convert its mesh data into triangles
    if isinstance(geom_xml, BoundGeometry):
        create_bound_geom_xml_triangles(
            obj, geom_xml, get_vert_index, get_mat_index)
        return

    # For empty bound objects with children, create the bound polygons from its children
    for child in obj.children_recursive:
        if child.sollum_type not in BOUND_POLYGON_TYPES:
            continue
        create_bound_xml_poly_shape(
            child, geom_xml, get_vert_index, get_mat_index)


def create_bound_geom_xml_triangles(obj: bpy.types.Object, geom_xml: BoundGeometry, get_vert_index: Callable[[Vector], int], get_mat_index: Callable[[bpy.types.Material], int]):
    """Create all bound poly triangles and vertices for a ``BoundGeometry`` object."""
    deform_ind_by_vert: dict[tuple, int] = {}

    def add_deformed_vert(vert: Vector):
        # Must be tuple since Vector is not hashable
        vertex = tuple(vert)

        if vertex in deform_ind_by_vert:
            return

        vert_ind = len(deform_ind_by_vert)
        deform_ind_by_vert[vertex] = vert_ind
        geom_xml.vertices_2.append(Vector(vertex))

    mesh = create_export_mesh(obj)

    transforms = Matrix.Translation(-geom_xml.geometry_center)

    triangles = create_poly_xml_triangles(
        mesh, transforms, get_vert_index, get_mat_index, add_deformed_vert)

    geom_xml.polygons = triangles

    if mesh.vertex_colors:
        create_xml_vertex_colors(geom_xml, mesh)


def create_bound_xml_poly_shape(obj: bpy.types.Object, geom_xml: BoundGeometryBVH, get_vert_index: Callable[[Vector], int], get_mat_index: Callable[[bpy.types.Material], int]):
    mesh = create_export_mesh(obj)

    transforms = obj.matrix_local.copy()
    transforms.translation -= geom_xml.geometry_center

    if mesh.vertex_colors:
        create_xml_vertex_colors(geom_xml, mesh)

    if obj.sollum_type == SollumType.BOUND_POLY_TRIANGLE:
        triangles = create_poly_xml_triangles(
            mesh, transforms, get_vert_index, get_mat_index)
        geom_xml.polygons.extend(triangles)

    elif obj.sollum_type == SollumType.BOUND_POLY_BOX:
        box_xml = create_poly_box_xml(
            obj, transforms, get_vert_index, get_mat_index)
        geom_xml.polygons.append(box_xml)

    elif obj.sollum_type == SollumType.BOUND_POLY_SPHERE:
        sphere_xml = create_poly_sphere_xml(
            obj, transforms, get_vert_index, get_mat_index)
        geom_xml.polygons.append(sphere_xml)

    elif obj.sollum_type == SollumType.BOUND_POLY_CYLINDER:
        cylinder_xml = create_poly_cylinder_capsule_xml(
            PolyCylinder, obj, transforms, get_vert_index, get_mat_index)
        geom_xml.polygons.append(cylinder_xml)

    elif obj.sollum_type == SollumType.BOUND_POLY_CAPSULE:
        capsule_xml = create_poly_cylinder_capsule_xml(
            PolyCapsule, obj, transforms, get_vert_index, get_mat_index)
        geom_xml.polygons.append(capsule_xml)


def create_export_mesh(obj: bpy.types.Object):
    """Get an evaluated mesh from ``obj`` with normals and loop triangles calculated.
    Original mesh is not affected."""
    mesh = obj.to_mesh()
    mesh.calc_normals_split()
    mesh.calc_loop_triangles()

    return mesh


def create_xml_vertex_colors(geom_xml: BoundGeometry | BoundGeometryBVH, mesh: bpy.types.Mesh):
    for loop in mesh.loops:
        geom_xml.vertex_colors.append(
            mesh.vertex_colors[0].data[loop.index].color)


def create_poly_xml_triangles(mesh: bpy.types.Mesh, transforms: Matrix, get_vert_index: Callable[[Vector], int], get_mat_index: Callable[[bpy.types.Material], int], add_deformed_vert: Optional[Callable[[Vector], None]] = None):
    """Create all bound polygon triangle XML objects for this BoundGeometry/BVH."""
    triangles: list[PolyTriangle] = []

    deformed_verts = get_deformed_verts(mesh)

    for tri in mesh.loop_triangles:
        triangle = PolyTriangle()
        mat = mesh.materials[tri.material_index]
        triangle.material_index = get_mat_index(mat)

        tri_indices: list[Vector] = []

        for loop_idx in tri.loops:
            loop = mesh.loops[loop_idx]

            vert_pos = transforms @ mesh.vertices[loop.vertex_index].co
            vert_ind = get_vert_index(vert_pos)

            tri_indices.append(vert_ind)

            if deformed_verts is not None:
                add_deformed_vert(
                    transforms @ deformed_verts[loop.vertex_index].co)

        triangle.v1 = tri_indices[0]
        triangle.v2 = tri_indices[1]
        triangle.v3 = tri_indices[2]

        triangles.append(triangle)

    return triangles


def get_deformed_verts(mesh: bpy.types.Mesh) -> Optional[list[bpy.types.MeshVertex]]:
    """Get vertices from the 'Deformed' shape key of ``mesh``."""
    if mesh.shape_keys is None:
        return

    deformed_key: bpy.types.ShapeKey = mesh.shape_keys.key_blocks.get(
        "Deformed")

    if deformed_key is None:
        return

    return deformed_key.data


def create_poly_box_xml(obj: bpy.types.Object, transforms: Matrix, get_vert_index: Callable[[Vector], int], get_mat_index: Callable[[bpy.types.Material], int]):
    box_xml = PolyBox()
    box_xml.material_index = get_mat_index(obj.active_material)
    indices = []
    bound_box = [transforms @ Vector(pos) for pos in obj.bound_box]
    corners = [bound_box[0], bound_box[5], bound_box[2], bound_box[7]]
    for vert in corners:
        indices.append(get_vert_index(vert))

    box_xml.v1 = indices[0]
    box_xml.v2 = indices[1]
    box_xml.v3 = indices[2]
    box_xml.v4 = indices[3]

    return box_xml


def create_poly_sphere_xml(obj: bpy.types.Object, transforms: Matrix, get_vert_index: Callable[[Vector], int], get_mat_index: Callable[[bpy.types.Material], int]):
    sphere_xml = PolySphere()
    sphere_xml.material_index = get_mat_index(obj.active_material)
    vert_ind = get_vert_index(transforms.translation)
    sphere_xml.v = vert_ind

    # Assuming bounding box forms a cube. Get the sphere enclosed by the cube
    # scale = transforms.to_scale()
    bbmin = get_min_vector_list(obj.bound_box)
    bbmax = get_max_vector_list(obj.bound_box)

    radius = (bbmax.x - bbmin.x) / 2

    sphere_xml.radius = radius

    return sphere_xml


def create_poly_cylinder_capsule_xml(poly_type: Type[T_PolyCylCap], obj: bpy.types.Object, transforms: Matrix, get_vert_index: Callable[[Vector], int], get_mat_index: Callable[[bpy.types.Material], int]):
    poly_xml = poly_type()

    position = transforms.translation

    poly_xml.material_index = get_mat_index(obj.active_material)

    # Only apply scale so we can get the oriented bounding box
    # scale = transforms.to_scale()
    bbmin = get_min_vector_list(obj.bound_box)
    bbmax = get_max_vector_list(obj.bound_box)

    height = bbmax.z - bbmin.z
    # Assumes X and Y scale are uniform
    radius = (bbmax.x - bbmin.x) / 2

    if poly_type is PolyCapsule:
        height = height - (radius * 2)

    vertical = Vector((0, 0, height / 2))
    vertical.rotate(transforms.to_euler("XYZ"))

    v1 = position - vertical
    v2 = position + vertical

    poly_xml.v1 = get_vert_index(v1)
    poly_xml.v2 = get_vert_index(v2)

    poly_xml.radius = radius

    return poly_xml


def create_col_mat_xml(mat: bpy.types.Material):
    mat_xml = Material()
    set_col_mat_xml_properties(mat_xml, mat)
    set_col_mat_xml_flags(mat_xml, mat)

    return mat_xml


def set_col_mat_xml_flags(mat_xml: Material, mat: bpy.types.Material):
    for flag_name in CollisionMatFlags.__annotations__.keys():
        if flag_name not in mat.collision_flags or mat.collision_flags[flag_name] == False:
            continue
        mat_xml.flags.append(f"FLAG_{flag_name.upper()}")

    if not mat_xml.flags:
        mat_xml.flags.append("NONE")


def set_composite_xml_flags(bound_xml: BoundChild, obj: bpy.types.Object):
    def set_flags(prop_name: str):
        flags_data_block = getattr(obj, prop_name)
        flags_xml = getattr(bound_xml, prop_name)

        for flag_name in BoundFlags.__annotations__:
            if flag_name not in flags_data_block or flags_data_block[flag_name] == False:
                continue

            flags_xml.append(flag_name.upper())

    set_flags("composite_flags1")
    set_flags("composite_flags2")


def set_composite_xml_transforms(bound_xml: BoundChild, obj: bpy.types.Object, parent_inverse: Matrix = Matrix()):
    bound_xml.composite_transform = (
        parent_inverse @ obj.matrix_world).transposed()


def set_bound_xml_mat_index(bound_xml: BoundChild, obj: bpy.types.Object):
    """Set ``bound_xml.material_index`` based on ``obj.active_material``."""
    if obj.active_material is None or obj.active_material.sollum_type != MaterialType.COLLISION:
        return

    bound_xml.material_index = obj.active_material.collision_properties.collision_index


def set_col_mat_xml_properties(mat_xml: Material, mat: bpy.types.Material):
    mat_xml.type = mat.collision_properties.collision_index
    mat_xml.procedural_id = mat.collision_properties.procedural_id
    mat_xml.room_id = mat.collision_properties.room_id
    mat_xml.ped_density = mat.collision_properties.ped_density
    mat_xml.material_color_index = mat.collision_properties.material_color_index


def set_bound_geom_xml_properties(geom_xml: BoundGeometry, obj: bpy.types.Object):
    geom_xml.unk_float_1 = obj.bound_properties.unk_float_1
    geom_xml.unk_float_2 = obj.bound_properties.unk_float_2


def set_bound_properties(bound_xml: Bound, obj: bpy.types.Object):
    bound_xml.procedural_id = obj.bound_properties.procedural_id
    bound_xml.room_id = obj.bound_properties.room_id
    bound_xml.ped_density = obj.bound_properties.ped_density
    bound_xml.poly_flags = obj.bound_properties.poly_flags
    bound_xml.unk_flags = obj.bound_properties.unk_flags
    bound_xml.margin = obj.margin
    bound_xml.volume = obj.bound_properties.volume
    bound_xml.inertia = Vector(obj.bound_properties.inertia)


def set_bound_extents(bound_xml: Bound, bbmin: Vector, bbmax: Vector):
    bound_xml.box_max = bbmax
    bound_xml.box_min = bbmin

    bound_xml.box_center = get_bound_center_from_bounds(
        bound_xml.box_min, bound_xml.box_max)
    bound_xml.sphere_center = bound_xml.box_center
    bound_xml.sphere_radius = get_sphere_radius(
        bound_xml.box_max, bound_xml.box_center)


def get_bound_extents(obj: bpy.types.Object):
    return get_min_vector_list(obj.bound_box), get_max_vector_list(obj.bound_box)


def get_bvh_extents(obj: bpy.types.Object):
    return get_combined_bound_box(obj)


def get_composite_extents(composite_xml: BoundComposite):
    """Get composite extents based on children"""
    mins: list[Vector] = []
    maxes: list[Vector] = []

    for child in composite_xml.children:
        transform = child.composite_transform.transposed()
        mins.append(transform @ child.box_min)
        maxes.append(transform @ child.box_max)

    return get_min_vector_list(mins), get_max_vector_list(maxes)

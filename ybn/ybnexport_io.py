import bpy
from bpy.types import (
    Object,
    Material,
    Mesh,
)
from mathutils import Vector, Matrix
from typing import Optional, Callable, Sequence
from dataclasses import replace
import numpy as np

from ..sollumz_helper import get_parent_inverse
from ..tools.blenderhelper import get_pose_inverse, get_evaluated_obj
from szio.gta5 import (
    AssetBound,
    BoundType,
    BoundPrimitive,
    BoundPrimitiveType,
    BoundVertex,
    CollisionMaterial,
    CollisionFlags,
    CollisionMaterialFlags,
    create_asset_bound,
)
from ..tools.utils import get_max_vector_list, get_min_vector_list, get_matrix_without_scale
from ..tools.meshhelper import (
    get_corners_from_extents,
    get_inner_sphere_radius,
    get_combined_bound_box_tight,
    get_color_attr_name,
)
from ..sollumz_properties import MaterialType, SOLLUMZ_UI_NAMES, SollumType, BOUND_POLYGON_TYPES
from ..iecontext import export_context, ExportBundle
from .. import logger
from .properties import CollisionMatFlags, get_collision_mat_raw_flags, BoundFlags

MAX_VERTICES = 32767


def export_ybn(obj: Object) -> ExportBundle:
    return export_context().make_bundle(create_bound_composite_asset(obj))


def create_bound_composite_asset(
    obj: Object,
    out_child_obj_to_index: dict[Object, int] = None,
    allow_planes: bool = False,
) -> Optional[AssetBound]:
    assert obj.sollum_type == SollumType.BOUND_COMPOSITE, f"Expected a Bound Composite, got '{obj.sollum_type}'"

    if not obj.children:
        # We only do a simple check for children here, if there are any other issues with them it will checked and
        # reported by `create_bound_xml`
        logger.warning(f"Bound composite '{obj.name}' has no children.")

    children = []
    centroid = Vector()
    cg = Vector()
    volume = 0.0
    extents_corners: list[Vector] = []
    for child_obj in obj.children:
        child_bound = create_bound_asset(child_obj, allow_planes=allow_planes)
        if child_bound is None:
            continue

        if out_child_obj_to_index is not None:
            out_child_obj_to_index[child_obj] = len(children)
        children.append(child_bound)

        child_transform = child_bound.composite_transform.transposed()
        child_cg = child_transform @ child_bound.cg
        child_centroid = child_transform @ child_bound.centroid
        child_volume = child_bound.volume

        child_min, child_max = child_bound.extent
        child_corners = get_corners_from_extents(child_min, child_max)

        volume += child_volume
        cg += child_cg * child_volume  # uniform density so volume == mass
        centroid += child_centroid
        extents_corners.extend(child_transform @ c for c in child_corners)

    num_children = len(children)
    cg /= volume if volume > 0 else 1.0
    centroid /= num_children if num_children > 0 else 1
    bbmin, bbmax = get_min_vector_list(extents_corners), get_max_vector_list(extents_corners)

    # Calculate combined moment of inertia
    if volume > 0.0 and num_children > 0:
        from ..shared.geometry import calculate_composite_inertia
        child_masses = [child.volume for child in children]
        child_inertias = [child.inertia * child.volume for child in children]
        child_cgs = [child.composite_transform.transposed() @ child.cg for child in children]
        inertia = calculate_composite_inertia(cg, child_cgs, child_masses, child_inertias)
        inertia /= volume
    else:
        inertia = Vector((1.0, 1.0, 1.0))

    composite = create_asset_bound(export_context().settings.targets, BoundType.COMPOSITE)
    composite.children = children
    composite.extent = bbmin, bbmax
    composite.centroid = centroid
    composite.radius_around_centroid = (bbmax - centroid).length
    composite.volume = volume
    composite.cg = cg
    composite.inertia = inertia
    composite.margin = 0.0  # composite margin always 0

    return composite


def init_bound_asset(bound_type: BoundType, obj: Object) -> AssetBound:
    """Create an ``AssetBound`` instance and set base properties from the Blender object properties."""
    bound = create_asset_bound(export_context().settings.targets, bound_type)
    bound.composite_transform = calc_composite_transforms(obj).transposed()

    if obj.type == "MESH":
        bbmin, bbmax = calc_bound_extents(obj)
    elif obj.type == "EMPTY":
        bbmin, bbmax = calc_bound_bvh_extents(obj, bound.composite_transform)
    else:
        return bound

    bound.extent = bbmin, bbmax

    def _convert_flags(flags_props: BoundFlags) -> CollisionFlags:
        # properties still use the CW names for backwards compatibility
        from szio.gta5.cwxml.adapters.bound import CW_COLLISION_FLAGS_MAP

        flags = CollisionFlags(0)
        for flag_name in BoundFlags.__annotations__:
            if flag_name not in flags_props or not flags_props[flag_name]:
                continue

            flags |= CW_COLLISION_FLAGS_MAP[flag_name.upper()]

        return flags

    bound.composite_collision_type_flags = _convert_flags(obj.composite_flags1)
    bound.composite_collision_include_flags = _convert_flags(obj.composite_flags2)

    if obj.active_material is not None:
        bound.material = create_collision_material_data(obj.active_material)

    return bound


def init_bound_geometry_asset(obj: Object) -> tuple[AssetBound, list[BoundVertex], list[BoundPrimitive]]:
    geom = init_bound_asset(BoundType.GEOMETRY, obj)
    geom.material = replace(geom.material, material_index=0)
    vertices, primitives = init_bound_geometry_primitives(geom, obj)
    return geom, vertices, primitives


def init_bound_bvh_asset(obj: Object) -> tuple[AssetBound, list[BoundVertex], list[BoundPrimitive]]:
    bvh = init_bound_asset(BoundType.BVH, obj)
    bvh.material = replace(bvh.material, material_index=0)
    vertices, primitives = init_bound_geometry_primitives(bvh, obj)
    return bvh, vertices, primitives


def create_bound_asset(obj: Object, is_root: bool = False, allow_planes: bool = False) -> Optional[AssetBound]:
    """Create a ``Bound`` instance based on `obj.sollum_type``."""
    if obj.sollum_type not in {
        SollumType.BOUND_BOX,
        SollumType.BOUND_SPHERE,
        SollumType.BOUND_CYLINDER,
        SollumType.BOUND_CAPSULE,
        SollumType.BOUND_DISC,
        SollumType.BOUND_PLANE,
        SollumType.BOUND_GEOMETRY,
        SollumType.BOUND_GEOMETRYBVH,
    }:
        logger.warning(
            f"'{obj.name}' is being exported as bound but has no bound Sollumz type! Please, use a bound type instead "
            f"of '{SOLLUMZ_UI_NAMES[obj.sollum_type]}'."
        )
        return None

    if not allow_planes and obj.sollum_type == SollumType.BOUND_PLANE:
        logger.warning(
            f"'{obj.name}' is a {SOLLUMZ_UI_NAMES[SollumType.BOUND_PLANE]} but planes are not supported in this "
            f"context! Only fragment cloth world bounds may use planes."
        )
        return None

    if obj.type == "MESH" and not validate_collision_materials(obj, verbose=True):
        return None

    from ..shared.geometry import (
        get_centroid_of_box, get_mass_properties_of_box,
        get_centroid_of_disc, get_mass_properties_of_disc,
        get_centroid_of_sphere, get_mass_properties_of_sphere,
        get_centroid_of_cylinder, get_mass_properties_of_cylinder,
        get_centroid_of_capsule, get_mass_properties_of_capsule,
        get_centroid_of_mesh, get_mass_properties_of_mesh,
        grow_sphere,
        shrink_mesh,
    )

    centroid = Vector()
    radius_around_centroid = 0.0
    cg = Vector()
    volume = 0.0
    inertia = Vector((1.0, 1.0, 1.0))
    margin = 0.0

    match obj.sollum_type:
        case SollumType.BOUND_BOX:
            bound = init_bound_asset(BoundType.BOX, obj)

            box_min, box_max = bound.extent
            extents = box_max - box_min

            centroid, radius_around_centroid = get_centroid_of_box(box_min, box_max)
            volume, cg, inertia = get_mass_properties_of_box(box_min, box_max)
            margin = min(0.04, min(extents) / 8)  # in boxes the margin equals the smallest side divided by 8

        case SollumType.BOUND_DISC:
            bound = init_bound_asset(BoundType.DISC, obj)

            # Same as a cylinder but along X-axis instead of Y-axis
            bbmin, bbmax = bound.extent
            extents = bbmax - bbmin
            radius = extents.y * 0.5
            length = extents.x

            centroid, radius_around_centroid = get_centroid_of_disc(radius)
            volume, cg, inertia = get_mass_properties_of_disc(radius, length)
            margin = length * 0.5  # in discs the margin equals half the length

        case SollumType.BOUND_SPHERE:
            bound = init_bound_asset(BoundType.SPHERE, obj)
            radius = bound.sphere_radius

            centroid, radius_around_centroid = get_centroid_of_sphere(radius)
            volume, cg, inertia = get_mass_properties_of_sphere(radius)
            margin = radius  # in spheres the margin equals the radius

        case SollumType.BOUND_CYLINDER:
            bound = init_bound_asset(BoundType.CYLINDER, obj)
            radius, length = bound.cylinder_radius_length

            centroid, radius_around_centroid = get_centroid_of_cylinder(radius, length)
            volume, cg, inertia = get_mass_properties_of_cylinder(radius, length)
            # in cylinders the margin equals 1/4 the minimum between radius and half-length
            margin = min(0.04, min(radius, length * 0.5) / 4)

        case SollumType.BOUND_CAPSULE:
            bound = init_bound_asset(BoundType.CAPSULE, obj)
            radius, length = bound.capsule_radius_length

            centroid, radius_around_centroid = get_centroid_of_capsule(radius, length)
            volume, cg, inertia = get_mass_properties_of_capsule(radius, length)
            margin = radius  # in capsules the margin equals the capsule radius

        case SollumType.BOUND_PLANE:
            bound = init_bound_asset(BoundType.PLANE, obj)
            bound.extent = Vector((0, 0, 0)), Vector((0, 0, 0))
            bound.composite_transform = Matrix.Identity(4)

            plane_transform = calc_composite_transforms(obj)
            centroid = plane_transform.to_translation()
            normal = plane_transform.col[1].xyz.normalized()
            bound.plane_normal = normal

            radius_around_centroid = 0.0
            volume = 1.0
            cg = normal # normal is stored in the CG
            inertia = Vector((1.0, 1.0, 1.0))
            margin = 0.04

        case SollumType.BOUND_GEOMETRY:
            bound, vertices, primitives = init_bound_geometry_asset(obj)

            if vertices and primitives:
                mesh_vertices = np.array([v.co for v in vertices])
                mesh_faces = []
                for prim in primitives:
                    mesh_faces.append(prim.vertices)
                mesh_faces = np.array(mesh_faces)

                centroid, radius_around_centroid = get_centroid_of_mesh(mesh_vertices)
                volume, cg, inertia = get_mass_properties_of_mesh(mesh_vertices, mesh_faces)

            # R* seems to apply the margin to the bbox before calculating the actual margin from shrunk mesh, so
            # the default margin is applied
            bbox_margin = 0.04
            bbmin, bbmax = bound.extent
            bbmin -= Vector((bbox_margin, bbox_margin, bbox_margin))
            bbmax += Vector((bbox_margin, bbox_margin, bbox_margin))
            bound.extent = bbmin, bbmax

            # CW calculates the shrunk mesh on import now (though it doesn't update the margin!)
            # _, margin = shrink_mesh(mesh_vertices, mesh_faces)
            # bound_xml.vertices_shrunk = [Vector(vert) - bound_xml.geometry_center for vert in shrunk_vertices]
            # Set margin to the minimum, though it should depend on the shrunk mesh. Currently shrink_mesh is too slow
            # to be worth using just for calculating the margin. In some cases, it can increase export times by a lot.
            margin = 0.025

        case SollumType.BOUND_GEOMETRYBVH:
            if not validate_bvh_collision_materials(obj, verbose=True):
                return None

            bound, vertices, primitives = init_bound_bvh_asset(obj)

            non_tri_primitives = []
            if vertices and primitives:
                mesh_vertices = np.array([v.co for v in vertices])
                mesh_faces = []
                for prim in primitives:
                    if prim.primitive_type != BoundPrimitiveType.TRIANGLE:
                        non_tri_primitives.append(prim)
                        continue
                    mesh_faces.append(prim.vertices)

                centroid, radius_around_centroid = get_centroid_of_mesh(mesh_vertices)
                if len(mesh_faces) > 0:
                    # If we have a mesh, calculate the center of gravity from the mesh
                    mesh_faces = np.array(mesh_faces)
                    _, cg, _ = get_mass_properties_of_mesh(mesh_vertices, mesh_faces)
                else:
                    # Otherwise, approximate with the centroid
                    cg = centroid

            # BVHs don't need to calculate the volume or inertia
            volume = 1.0
            inertia = Vector((1.0, 1.0, 1.0))
            margin = 0.04  # BVHs always have this margin

            bbmin, bbmax = bound.extent
            bbmin -= Vector((margin, margin, margin))
            bbmax += Vector((margin, margin, margin))
            bound.extent = bbmin, bbmax

            # Grow radius_around_centroid to fit all primitives
            for prim in non_tri_primitives:
                match prim.primitive_type:
                    case BoundPrimitiveType.BOX:
                        # Calculate the opposite corners of the box. The corners stored in the vertices array are
                        # already inside the bounding sphere, but the opposite corners may not be.
                        v0, v1, v2, v3 = prim.vertices
                        v = mesh_vertices[[v0, v1, v2, v3]]
                        v0b = Vector((v[1] + v[2] + v[3] - v[0]) * 0.5)
                        v1b = Vector((v[0] + v[2] + v[3] - v[1]) * 0.5)
                        v2b = Vector((v[0] + v[1] + v[3] - v[2]) * 0.5)
                        v3b = Vector((v[0] + v[1] + v[2] - v[3]) * 0.5)
                        radius_around_centroid = grow_sphere(centroid, radius_around_centroid, v0b, 0.0)
                        radius_around_centroid = grow_sphere(centroid, radius_around_centroid, v1b, 0.0)
                        radius_around_centroid = grow_sphere(centroid, radius_around_centroid, v2b, 0.0)
                        radius_around_centroid = grow_sphere(centroid, radius_around_centroid, v3b, 0.0)
                    case BoundPrimitiveType.SPHERE:
                        # The sphere center vertex is inside the bounding sphere but the whole sphere may not be.
                        v = prim.vertices[0]
                        radius_around_centroid = grow_sphere(
                            centroid, radius_around_centroid, Vector(mesh_vertices[v]), prim.radius)
                    case BoundPrimitiveType.CAPSULE | BoundPrimitiveType.CYLINDER:
                        # Capsules and cylinders are approximated by two spheres on their ends.
                        v0, v1 = prim.vertices
                        radius_around_centroid = grow_sphere(
                            centroid, radius_around_centroid, Vector(mesh_vertices[v0]), prim.radius)
                        radius_around_centroid = grow_sphere(
                            centroid, radius_around_centroid, Vector(mesh_vertices[v1]), prim.radius)
                    case _:
                        assert False, f"Unknown primitive type '{prim.primitive_type}'"

        case _:
            assert False, f"Unknown bound type '{obj.sollum_type}'"

    if is_root and obj.sollum_type in {
        SollumType.BOUND_BOX,
        SollumType.BOUND_SPHERE,
        SollumType.BOUND_CYLINDER,
        SollumType.BOUND_CAPSULE,
        SollumType.BOUND_DISC,
    }:
        # When root, the bound can be positioned not in 0,0,0 without a composite parent.
        # So take the composite transform we calculated and apply it to this bound. Only
        # translation, rotation still requires the composite parent.
        transform = bound.composite_transform.transposed()
        offset = transform.translation
        centroid = Vector(offset)
        cg = Vector(offset)

        # Clear the composite transform translation so it doesn't show a warning if this
        # is the only transform (no rotation, no scale)
        transform.translation = Vector((0.0, 0.0, 0.0))
        bound.composite_transform = transform.transposed()

    bound.centroid = centroid
    bound.radius_around_centroid = radius_around_centroid
    bound.volume = volume
    bound.cg = cg
    bound.inertia = inertia
    bound.margin = margin
    return bound


def validate_collision_materials(obj: Object, verbose: bool = False) -> bool:
    assert obj.type == "MESH", "Expected bound mesh object"
    mesh = obj.data
    non_col_mats = []
    col_mats = []
    for mat in mesh.materials:
        if mat.sollum_type == MaterialType.COLLISION:
            col_mats.append(mat)
        else:
            non_col_mats.append(mat)

    if non_col_mats:
        if verbose:
            non_col_mats_str = ", ".join(m.name for m in non_col_mats)
            logger.warning(
                f"Bound '{obj.name}' has non-collision materials! Only collision materials are supported. "
                f"Remove the following materials: {non_col_mats_str}."
            )
        return False

    supports_multiple_materials = obj.sollum_type in {SollumType.BOUND_GEOMETRY, SollumType.BOUND_POLY_TRIANGLE}
    if not col_mats:
        if verbose:
            logger.warning(f"Bound '{obj.name}' has no collision materials! Please, add a collision material.")
        return False
    elif len(col_mats) > 1 and not supports_multiple_materials:
        if verbose:
            col_mats_str = ", ".join(m.name for m in col_mats)
            logger.warning(
                f"Bound '{obj.name}' has multiple materials! Only a single collision material is supported on "
                f"{SOLLUMZ_UI_NAMES[obj.sollum_type]}. Keep only one of the following materials: {col_mats_str}."
            )
        return False

    return True


def has_collision_materials(obj: Object) -> bool:
    return validate_collision_materials(obj, verbose=False)


def validate_bvh_collision_materials(geom_obj: Object, verbose: bool = False) -> bool:
    valid = True
    for child in geom_obj.children:
        if child.type != "MESH" or child.sollum_type not in BOUND_POLYGON_TYPES:
            continue

        valid = valid and validate_collision_materials(child, verbose=verbose)

    return valid


def has_bvh_collision_materials(obj: Object) -> bool:
    return validate_bvh_collision_materials(obj, verbose=False)


def init_bound_geometry_primitives(
    bound: AssetBound,
    obj: Object
) -> tuple[list[BoundVertex], list[BoundPrimitive]]:
    """Create the vertices, primitives, and vertex colors of a bound geometry or BVH from ``obj``."""
    vertices, primitives = create_bound_geometry_vertices_and_primitives(bound, obj)

    bound.geometry_vertices = vertices
    bound.geometry_primitives = primitives

    num_vertices = len(vertices)

    if num_vertices == 0:
        logger.warning(f"{SOLLUMZ_UI_NAMES[obj.sollum_type]} '{obj.name}' has no geometry!")

    if num_vertices > MAX_VERTICES:
        logger.warning(
            f"{SOLLUMZ_UI_NAMES[obj.sollum_type]} '{obj.name}' exceeds maximum vertex limit of {MAX_VERTICES} "
            f"(has {num_vertices})!"
        )

    return vertices, primitives


def create_bound_geometry_vertices_and_primitives(
    bound: AssetBound,
    obj: Object
) -> tuple[list[BoundVertex], list[BoundPrimitive]]:
    # Create mappings of vertices and materials by index to build the new geom_xml vertices
    ind_by_vert: dict[tuple, int] = {}
    data_by_mat: dict[Material, CollisionMaterial] = {}

    vertices = []
    vertex_colors = []

    def _get_vert_index(vert: Vector, vert_color: Optional[tuple[int, int, int, int]] = None) -> int:
        default_vert_color = (255, 255, 255, 255)

        # These are safety checks in case the user mixed poly primitives and poly meshes with color attributes
        # This doesn't occur in original .ybns, if they have vertex colors, only poly triangles (meshes) are used.
        if vert_color is not None and len(vertex_colors) != len(vertices):
            # This vertex has color but previous ones didn't, assign a default color to all previous vertices
            for _ in range(len(vertex_colors), len(vertices)):
                vertex_colors.append(default_vert_color)

        if vert_color is None and len(vertex_colors) != 0:
            # There are already vertex colors in this geometry, assign a default color
            vert_color = default_vert_color

        # Tuple to uniquely identify this vertex and remove duplicates
        # Must be tuple since Vector is not hashable
        vertex_id = (*vert, *(vert_color or default_vert_color))

        if vertex_id in ind_by_vert:
            return ind_by_vert[vertex_id]

        vert_ind = len(ind_by_vert)
        ind_by_vert[vertex_id] = vert_ind
        vertices.append(Vector(vert))
        if vert_color is not None:
            vertex_colors.append(vert_color)

        return vert_ind

    def _get_mat_data(mat: Material) -> CollisionMaterial:
        if mat in data_by_mat:
            return data_by_mat[mat]

        mat_data = create_collision_material_data(mat)
        data_by_mat[mat] = mat_data
        return mat_data

    if bound.bound_type == BoundType.GEOMETRY:
        # If the bound object is a mesh, just convert its mesh data into triangles
        primitives = create_bound_geometry_primitive_mesh(obj, bound, _get_vert_index, _get_mat_data)
    else:
        # For empty bound objects with children, create the bound polygons from its children
        primitives = []
        for child in obj.children_recursive:
            if child.sollum_type not in BOUND_POLYGON_TYPES:
                logger.warning(
                    f"'{child.name}' is being exported as bound poly but has no bound poly Sollumz type! Please, use a "
                    f"bound poly type instead of '{SOLLUMZ_UI_NAMES[child.sollum_type]}'."
                )
                continue

            primitives.extend(create_bound_geometry_primitive(child, bound, _get_vert_index, _get_mat_data))

    has_colors = bool(vertex_colors)
    vertices = [BoundVertex(v, vertex_colors[i] if has_colors else None) for i, v in enumerate(vertices)]
    return vertices, primitives


def create_export_mesh(obj: Object) -> tuple[Object, Mesh]:
    """Get an evaluated mesh from ``obj`` with normals and loop triangles calculated.
    Original mesh is not affected."""
    obj_eval = get_evaluated_obj(obj)
    mesh = obj_eval.to_mesh()
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()
    mesh.calc_loop_triangles()

    return obj_eval, mesh


def create_bound_geometry_primitive_mesh(
    obj: Object,
    bound: AssetBound,
    get_vert_index: Callable[[Vector], int],
    get_mat_data: Callable[[Material], CollisionMaterial]
) -> list[BoundPrimitive]:
    """Create all bound poly triangles and vertices for a ``BoundGeometry`` object."""
    obj_eval, mesh = create_export_mesh(obj)

    transforms = calc_bound_primitives_transforms_to_apply(obj, bound.composite_transform)
    triangles = create_primitive_triangles(mesh, transforms, get_vert_index, get_mat_data)

    obj_eval.to_mesh_clear()

    return triangles


def create_bound_geometry_primitive(
    obj: Object,
    bound: AssetBound,
    get_vert_index: Callable[[Vector], int],
    get_mat_data: Callable[[Material], CollisionMaterial]
) -> Sequence[BoundPrimitive]:
    obj_eval, mesh = create_export_mesh(obj)

    transforms = calc_bound_primitives_transforms_to_apply(obj, bound.composite_transform)

    match obj.sollum_type:
        case SollumType.BOUND_POLY_TRIANGLE:
            primitives = create_primitive_triangles(mesh, transforms, get_vert_index, get_mat_data)
        case SollumType.BOUND_POLY_BOX:
            box = create_primitive_box(obj, transforms, get_vert_index, get_mat_data)
            primitives = (box,)
        case SollumType.BOUND_POLY_SPHERE:
            sphere = create_primitive_sphere(obj, transforms, get_vert_index, get_mat_data)
            primitives = (sphere,)
        case SollumType.BOUND_POLY_CYLINDER:
            cylinder = create_primitive_cylinder(obj, transforms, get_vert_index, get_mat_data)
            primitives = (cylinder,)
        case SollumType.BOUND_POLY_CAPSULE:
            capsule = create_primitive_capsule(obj, transforms, get_vert_index, get_mat_data)
            primitives = (capsule,)

    obj_eval.to_mesh_clear()
    return primitives


def create_primitive_triangles(
    mesh: Mesh,
    transforms: Matrix,
    get_vert_index: Callable[[Vector], int],
    get_mat_data: Callable[[Material], CollisionMaterial]
) -> list[BoundPrimitive]:
    """Create all primitive triangles objects for this mesh."""
    triangles: list[BoundPrimitive] = []

    color_attr_name = get_color_attr_name(0)
    color_attr = mesh.color_attributes.get(color_attr_name, None)
    if color_attr is not None and (color_attr.domain != "CORNER" or color_attr.data_type != "BYTE_COLOR"):
        color_attr = None

    for tri in mesh.loop_triangles:
        mat = mesh.materials[tri.material_index]
        mat_data = get_mat_data(mat)

        tri_indices: list[int] = []

        for loop_idx in tri.loops:
            loop = mesh.loops[loop_idx]

            vert_pos = transforms @ mesh.vertices[loop.vertex_index].co
            vert_color = color_attr.data[loop_idx].color_srgb if color_attr is not None else None
            if vert_color is not None:
                vert_color = tuple(int(c * 255) for c in vert_color)
            vert_ind = get_vert_index(vert_pos, vert_color=vert_color)

            tri_indices.append(vert_ind)

        v0 = tri_indices[0]
        v1 = tri_indices[1]
        v2 = tri_indices[2]

        triangles.append(BoundPrimitive.new_triangle(v0, v1, v2, mat_data))

    return triangles


def create_primitive_box(
    obj: Object,
    transforms: Matrix,
    get_vert_index: Callable[[Vector], int],
    get_mat_data: Callable[[Material], CollisionMaterial]
) -> BoundPrimitive:
    mat_data = get_mat_data(obj.active_material)
    indices = []
    bound_box = [transforms @ Vector(pos) for pos in obj.bound_box]
    corners = [bound_box[0], bound_box[5], bound_box[2], bound_box[7]]
    for vert in corners:
        indices.append(get_vert_index(vert))

    v0 = indices[0]
    v1 = indices[1]
    v2 = indices[2]
    v3 = indices[3]

    return BoundPrimitive.new_box(v0, v1, v2, v3, mat_data)


def create_primitive_sphere(
    obj: Object,
    transforms: Matrix,
    get_vert_index: Callable[[Vector], int],
    get_mat_data: Callable[[Material], CollisionMaterial]
) -> BoundPrimitive:
    mat_data = get_mat_data(obj.active_material)
    vert_ind = get_vert_index(transforms.translation)

    # Assuming bounding box forms a cube. Get the sphere enclosed by the cube
    # scale = transforms.to_scale()
    bbmin = get_min_vector_list(obj.bound_box)
    bbmax = get_max_vector_list(obj.bound_box)

    radius = (bbmax.x - bbmin.x) / 2

    return BoundPrimitive.new_sphere(vert_ind, radius, mat_data)


def _create_primitive_cylinder_or_capsule(
    is_capsule: bool,
    obj: Object,
    transforms: Matrix,
    get_vert_index: Callable[[Vector], int],
    get_mat_data: Callable[[Material], CollisionMaterial]
) -> BoundPrimitive:
    position = transforms.translation

    mat_data = get_mat_data(obj.active_material)

    # Only apply scale so we can get the oriented bounding box
    # scale = transforms.to_scale()
    bbmin = get_min_vector_list(obj.bound_box)
    bbmax = get_max_vector_list(obj.bound_box)

    height = bbmax.z - bbmin.z
    # Assumes X and Y scale are uniform
    radius = (bbmax.x - bbmin.x) / 2

    if is_capsule:
        height = height - (radius * 2)

    vertical = Vector((0, 0, height / 2))
    vertical.rotate(transforms.to_euler("XYZ"))

    v0 = get_vert_index(position - vertical)
    v1 = get_vert_index(position + vertical)

    return (
        BoundPrimitive.new_capsule(v0, v1, radius, mat_data)
        if is_capsule
        else BoundPrimitive.new_cylinder(v0, v1, radius, mat_data)
    )


def create_primitive_cylinder(
    obj: Object,
    transforms: Matrix,
    get_vert_index: Callable[[Vector], int],
    get_mat_data: Callable[[Material], CollisionMaterial]
) -> BoundPrimitive:
    return _create_primitive_cylinder_or_capsule(False, obj, transforms, get_vert_index, get_mat_data)


def create_primitive_capsule(
    obj: Object,
    transforms: Matrix,
    get_vert_index: Callable[[Vector], int],
    get_mat_data: Callable[[Material], CollisionMaterial]
) -> BoundPrimitive:
    return _create_primitive_cylinder_or_capsule(True, obj, transforms, get_vert_index, get_mat_data)


def create_collision_material_data(mat: Material) -> CollisionMaterial:
    if mat is None:
        raise ValueError("Material is None")
    if mat.sollum_type != MaterialType.COLLISION:
        raise ValueError(f"Material '{mat}' is not a collision material")

    col_props = mat.collision_properties
    flags_lo, flags_hi = get_collision_mat_raw_flags(mat.collision_flags)
    return CollisionMaterial(
        material_index=col_props.collision_index,
        material_color_index=col_props.material_color_index,
        procedural_id=col_props.procedural_id,
        room_id=col_props.room_id,
        ped_density=col_props.ped_density,
        material_flags=CollisionMaterialFlags(((flags_hi & 0xFF) << 8) | (flags_lo & 0xFF)),
    )


def calc_composite_transforms(bound_obj: Object) -> Matrix:
    """Get composite transforms for bound object. This is all transforms except
    for the pose and scale."""
    pose_inverse = get_pose_inverse(bound_obj)
    parent_inverse = get_parent_inverse(bound_obj)

    export_transforms = pose_inverse @ parent_inverse @ bound_obj.matrix_world

    return get_matrix_without_scale(export_transforms)


def calc_scale_to_apply_to_bound(bound_obj: Object) -> Vector:
    """Get scale to apply to bound object based on "Apply Parent Transforms" option."""
    parent_inverse = get_parent_inverse(bound_obj)
    scale = (parent_inverse @ bound_obj.matrix_world).to_scale()

    return scale


def calc_bound_extents(obj: Object) -> tuple[Vector, Vector]:
    scale = calc_scale_to_apply_to_bound(obj)

    bbs = [scale * Vector(corner) for corner in obj.bound_box]

    return get_min_vector_list(bbs), get_max_vector_list(bbs)


def calc_bound_bvh_extents(obj: Object, composite_transform: Matrix) -> tuple[Vector, Vector]:
    transforms_to_apply = calc_bound_primitives_transforms_to_apply(obj, composite_transform)

    bbmin, bbmax = get_combined_bound_box_tight(obj, matrix=transforms_to_apply)

    return bbmin, bbmax


def calc_bound_primitives_transforms_to_apply(obj: Object, composite_transform: Matrix) -> Matrix:
    """Get the transforms to apply directly to bound geometry vertices."""
    composite_transform = composite_transform.transposed()
    parent_inverse = get_parent_inverse(obj)

    # Apply any transforms not covered in composite_transform
    matrix = composite_transform.inverted() @ parent_inverse @ obj.matrix_world

    return matrix

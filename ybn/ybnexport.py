import bpy
from mathutils import Vector, Matrix
from typing import Optional, TypeVar, Callable, Type
import numpy as np

from ..sollumz_helper import get_parent_inverse
from ..tools.blenderhelper import get_pose_inverse, get_evaluated_obj
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
    BoundPlane,
    PolyTriangle,
    PolyBox,
    PolySphere,
    PolyCapsule,
    PolyCylinder,
    Material
)
from ..tools.utils import get_max_vector_list, get_min_vector_list, get_matrix_without_scale
from ..tools.meshhelper import (
    get_bound_center_from_bounds,
    get_corners_from_extents,
    get_inner_sphere_radius,
    get_combined_bound_box_tight,
    get_color_attr_name,
)
from ..sollumz_properties import MaterialType, SOLLUMZ_UI_NAMES, SollumType, BOUND_POLYGON_TYPES
from .. import logger
from .properties import CollisionMatFlags, get_collision_mat_raw_flags, BoundFlags

T_Bound = TypeVar("T_Bound", bound=Bound)
T_BoundChild = TypeVar("T_BoundChild", bound=BoundChild)
T_PolyCylCap = TypeVar("T_PolyCylCap", bound=PolyCylinder | PolyCapsule)

MAX_VERTICES = 32767


def export_ybn(obj: bpy.types.Object, filepath: str) -> bool:
    bounds = BoundFile()
    bounds.composite = create_composite_xml(obj)
    bounds.write_xml(filepath)
    return True


def create_composite_xml(
    obj: bpy.types.Object,
    out_child_obj_to_index: dict[bpy.types.Object, int] = None,
    allow_planes: bool = False,
) -> BoundComposite:
    assert obj.sollum_type == SollumType.BOUND_COMPOSITE, f"Expected a Bound Composite, got '{obj.sollum_type}'"

    composite_xml = BoundComposite()
    centroid = Vector()
    cg = Vector()
    volume = 0.0
    for child in obj.children:
        child_xml = create_bound_xml(child, allow_planes=allow_planes)
        if child_xml is None:
            continue

        if out_child_obj_to_index is not None:
            out_child_obj_to_index[child] = len(composite_xml.children)
        composite_xml.children.append(child_xml)

        child_transform = child_xml.composite_transform.transposed()
        child_cg = child_transform @ child_xml.sphere_center
        child_centroid = child_transform @ child_xml.box_center
        child_volume = child_xml.volume

        volume += child_volume
        cg += child_cg * child_volume  # uniform density so volume == mass
        centroid += child_centroid

    num_children = len(composite_xml.children)
    cg /= volume if volume > 0 else 1.0
    centroid /= num_children if num_children > 0 else 1

    # Calculate combined moment of inertia
    if volume > 0.0 and num_children > 0:
        from ..shared.geometry import calculate_composite_inertia
        child_masses = [child_xml.volume for child_xml in composite_xml.children]
        child_inertias = [child_xml.inertia * child_xml.volume for child_xml in composite_xml.children]
        child_cgs = [child_xml.composite_transform.transposed() @ child_xml.sphere_center for child_xml in composite_xml.children]
        inertia = calculate_composite_inertia(cg, child_cgs, child_masses, child_inertias)
        inertia /= volume
    else:
        inertia = Vector((1.0, 1.0, 1.0))

    # Calculate extents after children have been created
    bbmin, bbmax = get_composite_extents(composite_xml)
    set_bound_extents(composite_xml, bbmin, bbmax)

    radius_around_centroid = (bbmax - centroid).length

    set_bound_centroid(composite_xml, centroid, radius_around_centroid)
    set_bound_mass_properties(composite_xml, volume, cg, inertia)

    composite_xml.margin = 0.0  # composite margin always 0

    return composite_xml


def create_bound_xml(obj: bpy.types.Object, is_root: bool = False, allow_planes: bool = False) -> Optional[BoundChild]:
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
            bound_xml = init_bound_child_xml(BoundBox(), obj)

            box_min = bound_xml.box_min
            box_max = bound_xml.box_max
            extents = box_max - box_min

            centroid, radius_around_centroid = get_centroid_of_box(box_min, box_max)
            volume, cg, inertia = get_mass_properties_of_box(box_min, box_max)
            margin = min(0.04, min(extents) / 8)  # in boxes the margin equals the smallest side divided by 8

        case SollumType.BOUND_DISC:
            bound_xml = init_bound_child_xml(BoundDisc(), obj)

            # Same as a cylinder but along X-axis instead of Y-axis
            bbmin, bbmax = bound_xml.box_min, bound_xml.box_max
            extents = bbmax - bbmin
            radius = extents.y * 0.5
            length = extents.x

            centroid, radius_around_centroid = get_centroid_of_disc(radius)
            volume, cg, inertia = get_mass_properties_of_disc(radius, length)
            margin = length * 0.5  # in discs the margin equals half the length

        case SollumType.BOUND_SPHERE:
            bound_xml = init_bound_child_xml(BoundSphere(), obj)

            bbmin, bbmax = bound_xml.box_min, bound_xml.box_max
            radius = get_inner_sphere_radius(bbmin, bbmax)

            centroid, radius_around_centroid = get_centroid_of_sphere(radius)
            volume, cg, inertia = get_mass_properties_of_sphere(radius)
            margin = radius  # in spheres the margin equals the radius

        case SollumType.BOUND_CYLINDER:
            bound_xml = init_bound_child_xml(BoundCylinder(), obj)

            bbmin, bbmax = bound_xml.box_min, bound_xml.box_max
            extents = bbmax - bbmin
            radius = extents.x * 0.5
            length = extents.y

            centroid, radius_around_centroid = get_centroid_of_cylinder(radius, length)
            volume, cg, inertia = get_mass_properties_of_cylinder(radius, length)
            # in cylinders the margin equals 1/4 the minimum between radius and half-length
            margin = min(0.04, min(radius, length * 0.5) / 4)

        case SollumType.BOUND_CAPSULE:
            bound_xml = init_bound_child_xml(BoundCapsule(), obj)

            bbmin, bbmax = bound_xml.box_min, bound_xml.box_max
            extents = bbmax - bbmin
            radius = extents.x * 0.5
            length = extents.y - 2 * radius  # length without the top/bottom hemispheres

            centroid, radius_around_centroid = get_centroid_of_capsule(radius, length)
            volume, cg, inertia = get_mass_properties_of_capsule(radius, length)
            margin = radius  # in capsules the margin equals the capsule radius

        case SollumType.BOUND_PLANE:
            bound_xml = init_bound_child_xml(BoundPlane(), obj)
            bound_xml.box_max = Vector((0, 0, 0))
            bound_xml.box_min = Vector((0, 0, 0))
            bound_xml.composite_transform = Matrix.Identity(4)

            plane_transform = get_composite_transforms(obj)
            centroid = plane_transform.to_translation()
            cg = plane_transform.col[1].xyz.normalized() # normal is stored in the CG
            radius_around_centroid = 0.0
            volume = 1.0
            inertia = Vector((1.0, 1.0, 1.0))
            margin = 0.04

        case SollumType.BOUND_GEOMETRY:
            bound_xml = create_bound_geometry_xml(obj)

            if bound_xml.vertices and bound_xml.polygons:
                mesh_vertices = np.array([(v + bound_xml.geometry_center) for v in bound_xml.vertices])
                mesh_faces = []
                for poly in bound_xml.polygons:
                    mesh_faces.append([poly.v1, poly.v2, poly.v3])
                mesh_faces = np.array(mesh_faces)

                centroid, radius_around_centroid = get_centroid_of_mesh(mesh_vertices)
                volume, cg, inertia = get_mass_properties_of_mesh(mesh_vertices, mesh_faces)


            # R* seems to apply the margin to the bbox before calculating the actual margin from shrunk mesh, so
            # the default margin is applied
            bbox_margin = 0.04
            bound_xml.box_min -= Vector((bbox_margin, bbox_margin, bbox_margin))
            bound_xml.box_max += Vector((bbox_margin, bbox_margin, bbox_margin))

            # CW calculates the shrunk mesh on import now (though it doesn't update the margin!)
            # _, margin = shrink_mesh(mesh_vertices, mesh_faces)
            # bound_xml.vertices_shrunk = [Vector(vert) - bound_xml.geometry_center for vert in shrunk_vertices]
            # Set margin to the minimum, though it should depend on the shrunk mesh. Currently shrink_mesh is too slow
            # to be worth using just for calculating the margin. In some cases, it can increase export times by a lot.
            margin = 0.025

        case SollumType.BOUND_GEOMETRYBVH:
            if not validate_bvh_collision_materials(obj, verbose=True):
                return None

            bound_xml = create_bvh_xml(obj)

            primitives = []
            if bound_xml.vertices and bound_xml.polygons:
                mesh_vertices = np.array([(v + bound_xml.geometry_center) for v in bound_xml.vertices])
                mesh_faces = []
                for poly in bound_xml.polygons:
                    if not isinstance(poly, PolyTriangle):
                        primitives.append(poly)
                        continue
                    mesh_faces.append([poly.v1, poly.v2, poly.v3])

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

            bound_xml.box_min -= Vector((margin, margin, margin))
            bound_xml.box_max += Vector((margin, margin, margin))

            # Grow radius_around_centroid to fit all primitives
            for prim in primitives:
                match prim:
                    case PolyBox():
                        # Calculate the opposite corners of the box. The corners stored in the vertices array are
                        # already inside the bounding sphere, but the opposite corners may not be.
                        v = mesh_vertices[[prim.v1, prim.v2, prim.v3, prim.v4]]
                        v0b = Vector((v[1] + v[2] + v[3] - v[0]) * 0.5)
                        v1b = Vector((v[0] + v[2] + v[3] - v[1]) * 0.5)
                        v2b = Vector((v[0] + v[1] + v[3] - v[2]) * 0.5)
                        v3b = Vector((v[0] + v[1] + v[2] - v[3]) * 0.5)
                        radius_around_centroid = grow_sphere(centroid, radius_around_centroid, v0b, 0.0)
                        radius_around_centroid = grow_sphere(centroid, radius_around_centroid, v1b, 0.0)
                        radius_around_centroid = grow_sphere(centroid, radius_around_centroid, v2b, 0.0)
                        radius_around_centroid = grow_sphere(centroid, radius_around_centroid, v3b, 0.0)
                    case PolySphere():
                        # The sphere center vertex is inside the bounding sphere but the whole sphere may not be.
                        radius_around_centroid = grow_sphere(
                            centroid, radius_around_centroid, Vector(mesh_vertices[prim.v]), prim.radius)
                    case PolyCapsule() | PolyCylinder():
                        # Capsules and cylinders are approximated by two spheres on their ends.
                        radius_around_centroid = grow_sphere(
                            centroid, radius_around_centroid, Vector(mesh_vertices[prim.v1]), prim.radius)
                        radius_around_centroid = grow_sphere(
                            centroid, radius_around_centroid, Vector(mesh_vertices[prim.v2]), prim.radius)
                    case _:
                        assert False, f"Unknown primitive type '{type(prim)}'"

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
        transform = bound_xml.composite_transform.transposed()
        offset = transform.translation
        centroid = Vector(offset)
        cg = Vector(offset)
        bound_xml.box_min += offset
        bound_xml.box_max += offset

        # Clear the composite transform translation so it doesn't show a warning if this
        # is the only transform (no rotation, no scale)
        transform.translation = Vector((0.0, 0.0, 0.0))
        bound_xml.composite_transform = transform.transposed()

    set_bound_centroid(bound_xml, centroid, radius_around_centroid)
    set_bound_mass_properties(bound_xml, volume, cg, inertia)
    bound_xml.margin = margin
    return bound_xml


def validate_collision_materials(obj: bpy.types.Object, verbose: bool = False) -> bool:
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


def has_col_mats(obj: bpy.types.Object) -> bool:
    return validate_collision_materials(obj, verbose=False)


def validate_bvh_collision_materials(geom_obj: bpy.types.Object, verbose: bool = False) -> bool:
    valid = True
    for child in geom_obj.children:
        if child.type != "MESH" or child.sollum_type not in BOUND_POLYGON_TYPES:
            continue

        valid = valid and validate_collision_materials(child, verbose=verbose)

    return valid


def bound_geom_has_mats(geom_obj: bpy.types.Object) -> bool:
    return validate_bvh_collision_materials(geom_obj, verbose=False)


def init_bound_child_xml(bound_xml: T_BoundChild, obj: bpy.types.Object):
    """Initialize ``bound_xml`` bound child properties from object blender properties."""
    bound_xml.composite_transform = get_composite_transforms(obj).transposed()

    if obj.type == "MESH":
        bbmin, bbmax = get_bound_extents(obj)
    elif obj.type == "EMPTY":
        bbmin, bbmax = get_bvh_extents(obj, bound_xml.composite_transform)
    else:
        return bound_xml

    set_bound_extents(bound_xml, bbmin, bbmax)

    set_composite_xml_flags(bound_xml, obj)
    set_bound_col_mat_xml_properties(bound_xml, obj.active_material)

    return bound_xml


def create_bound_geometry_xml(obj: bpy.types.Object):
    geom_xml = init_bound_child_xml(BoundGeometry(), obj)
    geom_xml.material_index = 0

    create_bound_geom_xml_data(geom_xml, obj)

    return geom_xml


def create_bvh_xml(obj: bpy.types.Object):
    geom_xml = init_bound_child_xml(BoundGeometryBVH(), obj)
    geom_xml.material_index = 0

    create_bound_geom_xml_data(geom_xml, obj)

    return geom_xml


def create_bound_geom_xml_data(geom_xml: BoundGeometry | BoundGeometryBVH, obj: bpy.types.Object):
    """Create the vertices, polygons, and vertex colors of a ``BoundGeometry`` or ``BoundGeometryBVH`` from ``obj``."""
    create_bound_xml_polys(geom_xml, obj)
    geom_xml.geometry_center = center_verts_to_geometry(geom_xml)

    num_vertices = len(geom_xml.vertices)

    if num_vertices == 0:
        logger.warning(f"{SOLLUMZ_UI_NAMES[obj.sollum_type]} '{obj.name}' has no geometry!")

    if num_vertices > MAX_VERTICES:
        logger.warning(
            f"{SOLLUMZ_UI_NAMES[obj.sollum_type]} '{obj.name}' exceeds maximum vertex limit of {MAX_VERTICES} "
            f"(has {num_vertices})!"
        )


def center_verts_to_geometry(geom_xml: BoundGeometry | BoundGeometryBVH):
    """Position verts such that the origin is at their center of geometry. Returns the center of geometry."""
    # the center is really just the bounding-box center
    geom_center = get_bound_center_from_bounds(geom_xml.box_min, geom_xml.box_max)
    geom_xml.vertices = [Vector(vert) - geom_center for vert in geom_xml.vertices]
    return Vector(geom_center)


def create_bound_xml_polys(geom_xml: BoundGeometry | BoundGeometryBVH, obj: bpy.types.Object):
    # Create mappings of vertices and materials by index to build the new geom_xml vertices
    ind_by_vert: dict[tuple, int] = {}
    ind_by_mat: dict[bpy.types.Material, int] = {}

    def get_vert_index(vert: Vector, vert_color: Optional[tuple[int, int, int, int]] = None):
        default_vert_color = (255, 255, 255, 255)

        # These are safety checks in case the user mixed poly primitives and poly meshes with color attributes
        # This doesn't occur in original .ybns, if they have vertex colors, only poly triangles (meshes) are used.
        if vert_color is not None and len(geom_xml.vertex_colors) != len(geom_xml.vertices):
            # This vertex has color but previous ones didn't, assign a default color to all previous vertices
            for _ in range(len(geom_xml.vertex_colors), len(geom_xml.vertices)):
                geom_xml.vertex_colors.append(default_vert_color)

        if vert_color is None and len(geom_xml.vertex_colors) != 0:
            # There are already vertex colors in this geometry, assign a default color
            vert_color = default_vert_color

        # Tuple to uniquely identify this vertex and remove duplicates
        # Must be tuple since Vector is not hashable
        vertex_id = (*vert, *(vert_color or default_vert_color))

        if vertex_id in ind_by_vert:
            return ind_by_vert[vertex_id]

        vert_ind = len(ind_by_vert)
        ind_by_vert[vertex_id] = vert_ind
        geom_xml.vertices.append(Vector(vert))
        if vert_color is not None:
            geom_xml.vertex_colors.append(vert_color)

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
    if not isinstance(geom_xml, BoundGeometryBVH):
        create_bound_geom_xml_triangles(obj, geom_xml, get_vert_index, get_mat_index)
        return

    # For empty bound objects with children, create the bound polygons from its children
    for child in obj.children_recursive:
        if child.sollum_type not in BOUND_POLYGON_TYPES:
            logger.warning(
                f"'{child.name}' is being exported as bound poly but has no bound poly Sollumz type! Please, use a "
                f"bound poly type instead of '{SOLLUMZ_UI_NAMES[child.sollum_type]}'."
            )
            continue

        create_bound_xml_poly_shape(child, geom_xml, get_vert_index, get_mat_index)


def create_bound_geom_xml_triangles(obj: bpy.types.Object, geom_xml: BoundGeometry, get_vert_index: Callable[[Vector], int], get_mat_index: Callable[[bpy.types.Material], int]):
    """Create all bound poly triangles and vertices for a ``BoundGeometry`` object."""
    obj_eval, mesh = create_export_mesh(obj)

    transforms = get_bound_poly_transforms_to_apply(obj, geom_xml.composite_transform)
    triangles = create_poly_xml_triangles(mesh, transforms, get_vert_index, get_mat_index)
    geom_xml.polygons = triangles

    obj_eval.to_mesh_clear()


def create_bound_xml_poly_shape(obj: bpy.types.Object, geom_xml: BoundGeometryBVH, get_vert_index: Callable[[Vector], int], get_mat_index: Callable[[bpy.types.Material], int]):
    obj_eval, mesh = create_export_mesh(obj)

    transforms = get_bound_poly_transforms_to_apply(obj, geom_xml.composite_transform)

    match obj.sollum_type:
        case SollumType.BOUND_POLY_TRIANGLE:
            triangles = create_poly_xml_triangles(mesh, transforms, get_vert_index, get_mat_index)
            geom_xml.polygons.extend(triangles)
        case SollumType.BOUND_POLY_BOX:
            box_xml = create_poly_box_xml(obj, transforms, get_vert_index, get_mat_index)
            geom_xml.polygons.append(box_xml)
        case SollumType.BOUND_POLY_SPHERE:
            sphere_xml = create_poly_sphere_xml(obj, transforms, get_vert_index, get_mat_index)
            geom_xml.polygons.append(sphere_xml)
        case SollumType.BOUND_POLY_CYLINDER:
            cylinder_xml = create_poly_cylinder_capsule_xml(
                PolyCylinder, obj, transforms, get_vert_index, get_mat_index)
            geom_xml.polygons.append(cylinder_xml)
        case SollumType.BOUND_POLY_CAPSULE:
            capsule_xml = create_poly_cylinder_capsule_xml(PolyCapsule, obj, transforms, get_vert_index, get_mat_index)
            geom_xml.polygons.append(capsule_xml)

    obj_eval.to_mesh_clear()


def get_bound_poly_transforms_to_apply(obj: bpy.types.Object, composite_transform: Matrix):
    """Get the transforms to apply directly to BoundGeometry vertices."""
    composite_transform = composite_transform.transposed()
    parent_inverse = get_parent_inverse(obj)

    # Apply any transforms not covered in composite_transform
    matrix = composite_transform.inverted() @ parent_inverse @ obj.matrix_world

    return matrix


def get_scale_to_apply_to_bound(bound_obj: bpy.types.Object) -> Vector:
    """Get scale to apply to bound object based on "Apply Parent Transforms" option."""
    parent_inverse = get_parent_inverse(bound_obj)
    scale = (parent_inverse @ bound_obj.matrix_world).to_scale()

    return scale


def create_export_mesh(obj: bpy.types.Object):
    """Get an evaluated mesh from ``obj`` with normals and loop triangles calculated.
    Original mesh is not affected."""
    obj_eval = get_evaluated_obj(obj)
    mesh = obj_eval.to_mesh()
    if bpy.app.version < (4, 1, 0):
        mesh.calc_normals_split()
    mesh.calc_loop_triangles()

    return obj_eval, mesh


def create_poly_xml_triangles(mesh: bpy.types.Mesh, transforms: Matrix, get_vert_index: Callable[[Vector], int], get_mat_index: Callable[[bpy.types.Material], int]):
    """Create all bound polygon triangle XML objects for this BoundGeometry/BVH."""
    triangles: list[PolyTriangle] = []

    color_attr_name = get_color_attr_name(0)
    color_attr = mesh.color_attributes.get(color_attr_name, None)
    if color_attr is not None and (color_attr.domain != "CORNER" or color_attr.data_type != "BYTE_COLOR"):
        color_attr = None

    for tri in mesh.loop_triangles:
        triangle = PolyTriangle()
        mat = mesh.materials[tri.material_index]
        triangle.material_index = get_mat_index(mat)

        tri_indices: list[int] = []

        for loop_idx in tri.loops:
            loop = mesh.loops[loop_idx]

            vert_pos = transforms @ mesh.vertices[loop.vertex_index].co
            vert_color = color_attr.data[loop_idx].color_srgb if color_attr is not None else None
            if vert_color is not None:
                vert_color = (vert_color[0] * 255, vert_color[1] * 255, vert_color[2] * 255, vert_color[3] * 255)
            vert_ind = get_vert_index(vert_pos, vert_color=vert_color)

            tri_indices.append(vert_ind)

        triangle.v1 = tri_indices[0]
        triangle.v2 = tri_indices[1]
        triangle.v3 = tri_indices[2]

        triangles.append(triangle)

    return triangles


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
    return mat_xml


def set_composite_xml_flags(bound_xml: BoundChild, obj: bpy.types.Object):
    def set_flags(prop_name: str):
        flags_data_block = getattr(obj, prop_name)
        flags_xml = getattr(bound_xml, prop_name)

        for flag_name in BoundFlags.__annotations__:
            if flag_name not in flags_data_block or not flags_data_block[flag_name]:
                continue

            flags_xml.append(flag_name.upper())

    set_flags("composite_flags1")
    set_flags("composite_flags2")


def get_composite_transforms(bound_obj: bpy.types.Object):
    """Get CompositeTransforms for bound object. This is all transforms except
    for the pose and scale."""
    pose_inverse = get_pose_inverse(bound_obj)
    parent_inverse = get_parent_inverse(bound_obj)

    export_transforms = pose_inverse @ parent_inverse @ bound_obj.matrix_world

    return get_matrix_without_scale(export_transforms)


def set_bound_col_mat_xml_properties(bound_xml: Bound, mat: bpy.types.Material):
    if mat is None or mat.sollum_type != MaterialType.COLLISION:
        return

    bound_xml.material_index = mat.collision_properties.collision_index
    bound_xml.procedural_id = mat.collision_properties.procedural_id
    bound_xml.room_id = mat.collision_properties.room_id
    bound_xml.ped_density = mat.collision_properties.ped_density
    bound_xml.material_color_index = mat.collision_properties.material_color_index
    flags_lo, flags_hi = get_collision_mat_raw_flags(mat.collision_flags)
    bound_xml.unk_flags = flags_lo
    bound_xml.poly_flags = flags_hi


def set_col_mat_xml_properties(mat_xml: Material, mat: bpy.types.Material):
    mat_xml.type = mat.collision_properties.collision_index
    mat_xml.procedural_id = mat.collision_properties.procedural_id
    mat_xml.room_id = mat.collision_properties.room_id
    mat_xml.ped_density = mat.collision_properties.ped_density
    mat_xml.material_color_index = mat.collision_properties.material_color_index
    for flag_name in CollisionMatFlags.__annotations__.keys():
        if flag_name not in mat.collision_flags or not mat.collision_flags[flag_name]:
            continue
        mat_xml.flags.append(f"FLAG_{flag_name.upper()}")

    if not mat_xml.flags:
        mat_xml.flags.append("NONE")


def set_bound_extents(bound_xml: Bound, bbmin: Vector, bbmax: Vector):
    bound_xml.box_max = bbmax
    bound_xml.box_min = bbmin


def get_bound_extents(obj: bpy.types.Object):
    scale = get_scale_to_apply_to_bound(obj)

    bbs = [scale * Vector(corner) for corner in obj.bound_box]

    return get_min_vector_list(bbs), get_max_vector_list(bbs)


def get_bvh_extents(obj: bpy.types.Object, composite_transform: Matrix):
    transforms_to_apply = get_bound_poly_transforms_to_apply(obj, composite_transform)

    bbmin, bbmax = get_combined_bound_box_tight(obj, matrix=transforms_to_apply)

    return bbmin, bbmax


def get_composite_extents(composite_xml: BoundComposite):
    """Get composite extents based on child bound extents"""
    corner_vecs: list[Vector] = []

    for child in composite_xml.children:
        transform = child.composite_transform.transposed()
        child_corners = get_corners_from_extents(child.box_min, child.box_max)
        # Get AABB with transforms applied
        corner_vecs.extend([transform @ corner for corner in child_corners])

    return get_min_vector_list(corner_vecs), get_max_vector_list(corner_vecs)


def set_bound_centroid(bound_xml: Bound, centroid: Vector, radius_around_centroid: float):
    bound_xml.box_center = centroid
    bound_xml.sphere_radius = radius_around_centroid


def set_bound_mass_properties(bound_xml: Bound, volume: float, cg: Vector, inertia: Vector):
    bound_xml.sphere_center = cg
    bound_xml.volume = volume
    bound_xml.inertia = inertia

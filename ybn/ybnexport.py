from .properties import CollisionMatFlags
from ..resources.bound import *
from ..sollumz_properties import BOUND_SHAPE_TYPES, MaterialType, SollumType
from ..tools.meshhelper import *
from ..tools.blenderhelper import delete_object
from ..tools.utils import *


class NoGeometryError(Exception):
    message = 'Sollumz Bound Geometry has no geometry!'


class VerticesLimitError(Exception):
    pass


def add_material(material, mat_map, materials):
    if material in mat_map:
        return mat_map[material]

    if material and material.sollum_type == MaterialType.COLLISION:
        mat_item = MaterialItem()
        mat_item.type = material.collision_properties.collision_index
        mat_item.procedural_id = material.collision_properties.procedural_id
        mat_item.room_id = material.collision_properties.room_id
        mat_item.ped_density = material.collision_properties.ped_density
        mat_item.material_color_index = material.collision_properties.material_color_index

        # Assign flags
        for flag_name in CollisionMatFlags.__annotations__.keys():
            # flag_exists = getattr(material.collision_flags, flag_name)
            if flag_name in material.collision_flags:
                mat_item.flags.append(f"FLAG_{flag_name.upper()}")
        idx = len(mat_map)
        mat_map[material] = idx
        materials.append(mat_item)
        return idx


def polygon_from_object(obj, geometry, verts_map, mat_map, export_settings):
    vertices = geometry.vertices
    materials = geometry.materials
    geom_center = geometry.geometry_center
    pos = obj.matrix_world.to_translation(
    ) - geom_center if export_settings.use_transforms else obj.location

    def handle_vert(vert):
        vert = tuple(vert)

        if vert in verts_map:
            idx = verts_map[vert]
        else:
            idx = len(verts_map)
            verts_map[vert] = len(verts_map)
            vertices.append(Vector(vert))
        return idx

    if obj.sollum_type == SollumType.BOUND_POLY_BOX:
        box = Box()
        box.material_index = add_material(
            obj.active_material, mat_map, materials)
        indices = []
        bound_box = [Vector(pos) for pos in obj.bound_box]
        corners = [bound_box[0], bound_box[5], bound_box[2], bound_box[7]]
        for vert in corners:
            world_vert = (obj.matrix_world @ vert) - geom_center
            vert = world_vert if export_settings.use_transforms else obj.matrix_basis @ vert
            idx = handle_vert(vert)
            indices.append(idx)

        box.v1 = indices[0]
        box.v2 = indices[1]
        box.v3 = indices[2]
        box.v4 = indices[3]

        return box
    elif obj.sollum_type == SollumType.BOUND_POLY_SPHERE:
        sphere = Sphere()
        sphere.material_index = add_material(
            obj.active_material, mat_map, materials)
        idx = handle_vert(pos)
        sphere.v = idx
        bound_box = get_total_bounds(obj)

        radius = get_distance_of_vectors(
            bound_box[1], bound_box[2]) / 2

        sphere.radius = radius

        return sphere
    elif obj.sollum_type == SollumType.BOUND_POLY_CYLINDER or obj.sollum_type == SollumType.BOUND_POLY_CAPSULE:
        bound = None
        if obj.sollum_type == SollumType.BOUND_POLY_CYLINDER:
            bound = Cylinder()
        elif obj.sollum_type == SollumType.BOUND_POLY_CAPSULE:
            bound = Capsule()

        bound.material_index = add_material(
            obj.active_material, mat_map, materials)
        bound_box = get_total_bounds(obj)

        # Get bound height
        height = get_distance_of_vectors(
            bound_box[0], bound_box[1])
        radius = get_distance_of_vectors(
            bound_box[1], bound_box[2]) / 2

        if obj.sollum_type == SollumType.BOUND_POLY_CAPSULE:
            height = height - (radius * 2)

        vertical = Vector((0, 0, height / 2))
        mat = obj.matrix_world if export_settings.use_transforms else obj.matrix_basis
        vertical.rotate(mat.to_euler('XYZ'))

        v1 = pos - vertical
        v2 = pos + vertical

        idx1 = handle_vert(v1)
        idx2 = handle_vert(v2)

        bound.v1 = idx1
        bound.v2 = idx2

        bound.radius = radius

        return bound


def geometry_from_object(obj, sollum_type=SollumType.BOUND_GEOMETRYBVH, export_settings=None, is_frag=False):
    geometry = None

    if sollum_type == SollumType.BOUND_GEOMETRYBVH:
        geometry = BoundGeometryBVH()
    elif sollum_type == SollumType.BOUND_GEOMETRY:
        geometry = BoundGeometry()
    else:
        return ValueError('Invalid argument for geometry sollum_type!')

    geometry = init_bound_item(geometry, obj, export_settings, is_frag)

    if sollum_type == SollumType.BOUND_GEOMETRY:
        geometry.unk_float_1 = obj.bound_properties.unk_float_1
        geometry.unk_float_2 = obj.bound_properties.unk_float_2

    if geometry.unk_type == 2:
        geometry.geometry_center = obj.children[0].location
    else:
        # Set translation of the transposed matrix to 0,0,0
        geometry.composite_transform[3][0] = 0
        geometry.composite_transform[3][1] = 0
        geometry.composite_transform[3][2] = 0
        geometry.geometry_center = obj.location

    # Ensure object has geometry
    found = False
    vertices = {}
    mat_map = {}
    # Get child poly bounds
    for child in get_children_recursive(obj):
        mesh = child.to_mesh()
        mesh.calc_normals_split()
        mesh.calc_loop_triangles()
        if child.sollum_type == SollumType.BOUND_POLY_TRIANGLE:
            found = True
            # mats
            # for material in mesh.materials:
            #     add_material(material, materials)

            # vert colors
            for poly in mesh.polygons:
                for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
                    if(len(mesh.vertex_colors) > 0):
                        geometry.vertex_colors.append(
                            mesh.vertex_colors[0].data[loop_index].color)

            for tri in mesh.loop_triangles:
                triangle = Triangle()
                mat = child.data.materials[tri.material_index]
                triangle.material_index = add_material(
                    mat, mat_map, geometry.materials)

                vert_indices = []
                for loop_idx in tri.loops:
                    loop = mesh.loops[loop_idx]

                    vertex = mesh.vertices[loop.vertex_index].co
                    if export_settings.use_transforms:
                        vertex = (child.matrix_world @ vertex) - \
                            geometry.geometry_center
                    else:
                        if geometry.unk_type != 2:
                            vertex = child.matrix_basis @ vertex

                    # Must be tuple for dedupe to work
                    vertex = tuple(vertex)

                    if vertex in vertices:
                        idx = vertices[vertex]
                    else:
                        idx = len(vertices)
                        vertices[vertex] = len(vertices)
                        geometry.vertices.append(Vector(vertex))

                    vert_indices.append(idx)

                triangle.v1 = vert_indices[0]
                triangle.v2 = vert_indices[1]
                triangle.v3 = vert_indices[2]
                geometry.polygons.append(triangle)
        elif child.sollum_type == SollumType.BOUND_POLY_TRIANGLE2:
            vertices2 = {}
            for tri in mesh.loop_triangles:
                for loop_idx in tri.loops:
                    loop = mesh.loops[loop_idx]
                    vertex = mesh.vertices[loop.vertex_index].co
                    if export_settings.use_transforms:
                        vertex = (child.matrix_world @ vertex) - \
                            geometry.geometry_center
                    else:
                        if geometry.unk_type != 2:
                            vertex = child.matrix_basis @ vertex

                    # Must be tuple for dedupe to work
                    vertex = tuple(vertex)

                    if vertex in vertices2:
                        idx = vertices2[vertex]
                    else:
                        vertices2[vertex] = len(vertices2)
                        geometry.vertices_2.append(Vector(vertex))
        else:
            poly = polygon_from_object(
                child, geometry, vertices, mat_map, export_settings)
            if poly:
                found = True
                geometry.polygons.append(poly)
    if not found:
        raise NoGeometryError()

    # Check vert count
    if len(geometry.vertices) > 32767:
        raise VerticesLimitError(
            f"{obj.name} can only have at most 32767 vertices!")

    if type(geometry) is BoundGeometry:
        if len(geometry.vertices_2) == 0:
            geometry.vertices_2 = geometry.vertices

    return geometry


def init_bound_item(bound_item, obj, export_settings, is_frag=False):
    init_bound(bound_item, obj, export_settings, is_frag)
    # Get flags from object
    for prop in dir(obj.composite_flags1):
        value = getattr(obj.composite_flags1, prop)
        if value == True:
            bound_item.composite_flags1.append(prop.upper())

    for prop in dir(obj.composite_flags2):
        value = getattr(obj.composite_flags2, prop)
        if value == True:
            bound_item.composite_flags2.append(prop.upper())

    bound_item.composite_transform = obj.matrix_world.copy(
    ) if export_settings.use_transforms else obj.matrix_basis.copy()
    bound_item.composite_transform.transpose()

    if obj.active_material and obj.active_material.sollum_type == MaterialType.COLLISION:
        bound_item.material_index = obj.active_material.collision_properties.collision_index

    return bound_item


def init_bound(bound, obj, export_settings, is_frag=False):
    use_world = export_settings.use_transforms and (
        obj.sollum_type == SollumType.BOUND_GEOMETRYBVH or obj.sollum_type == SollumType.BOUND_GEOMETRY or obj.sollum_type == SollumType.BOUND_COMPOSITE)

    if obj.sollum_type in BOUND_SHAPE_TYPES:
        bound.box_max = get_max_vector_list(obj.bound_box)
        bound.box_min = get_min_vector_list(obj.bound_box)
        bound.box_center = (bound.box_max + bound.box_min) * 0.5
        bound.sphere_center = bound.box_center
    else:
        bbmin, bbmax = get_bound_extents(obj, use_world, obj.margin)
        bound.box_min = bbmin
        bound.box_max = bbmax
        center = get_bound_center_from_bounds(
            bbmin, bbmax)
        bound.box_center = center
        bound.sphere_center = center
        bound.sphere_radius = get_obj_radius(
            obj, world=use_world)
    bound.procedural_id = obj.bound_properties.procedural_id
    bound.room_id = obj.bound_properties.room_id
    bound.ped_density = obj.bound_properties.ped_density
    bound.poly_flags = obj.bound_properties.poly_flags
    bound.inertia = Vector(obj.bound_properties.inertia)
    bound.volume = obj.bound_properties.volume
    bound.unk_flags = obj.bound_properties.unk_flags
    bound.unk_type = 2 if is_frag else 1
    bound.margin = obj.margin

    return bound


def bound_from_object(obj, export_settings, is_frag=None):
    if obj.sollum_type == SollumType.BOUND_BOX:
        bound = init_bound_item(BoundBox(), obj, export_settings, is_frag)
        if bound.unk_type == 2:
            bound.sphere_center = Vector()
            bound.box_center = Vector()
        return bound
    elif obj.sollum_type == SollumType.BOUND_SPHERE:
        bound = init_bound_item(BoundSphere(), obj, export_settings, is_frag)
        bound.sphere_radius = obj.bound_radius
        return bound
    elif obj.sollum_type == SollumType.BOUND_CYLINDER:
        bound = init_bound_item(BoundCylinder(), obj, export_settings, is_frag)
        bound.sphere_radius = obj.bound_radius
        return bound
    elif obj.sollum_type == SollumType.BOUND_CAPSULE:
        bound = init_bound_item(BoundCapsule(), obj, export_settings, is_frag)
        bound.sphere_radius = obj.bound_radius
        return bound
    elif obj.sollum_type == SollumType.BOUND_DISC:
        bound = init_bound_item(BoundDisc(), obj, export_settings, is_frag)
        bound.sphere_radius = obj.bound_radius
        bound.margin = obj.margin
        if bound.unk_type == 2:
            bound.sphere_center = Vector()
            bound.box_center = Vector()
            bound.box_max = Vector(
                (bound.margin, bound.sphere_radius, bound.sphere_radius))
            bound.box_min = bound.box_max * -1
        return bound
    elif obj.sollum_type == SollumType.BOUND_CLOTH:
        return init_bound_item(BoundCloth(), obj, export_settings, is_frag)
    elif obj.sollum_type == SollumType.BOUND_GEOMETRY:
        return geometry_from_object(obj, SollumType.BOUND_GEOMETRY, export_settings, is_frag)
    elif obj.sollum_type == SollumType.BOUND_GEOMETRYBVH:
        return geometry_from_object(obj, SollumType.BOUND_GEOMETRYBVH, export_settings, is_frag)


def composite_from_objects(objs, export_settings, is_frag=False):
    tobj = bpy.data.objects.new("temp", None)
    old_parents = []
    for obj in objs:
        old_parents.append(obj.parent)
        obj.parent = tobj

    composite = init_bound(BoundsComposite(), tobj, export_settings, is_frag)

    for child in objs:
        bound = bound_from_object(child, export_settings, is_frag)
        if bound:
            composite.children.append(bound)

    for obj in objs:
        obj.parent = old_parents[0]
        old_parents.pop(0)

    return composite


def composite_from_object(obj, export_settings):
    composite = init_bound(BoundsComposite(), obj, export_settings)

    for child in get_children_recursive(obj):
        bound = bound_from_object(child, export_settings)
        if bound:
            composite.children.append(bound)

    return composite


def boundfile_from_object(obj, export_settings):
    bounds = BoundFile()

    composite = composite_from_object(obj, export_settings)
    bounds.composite = composite

    return bounds


def export_ybn(obj, filepath, export_settings):
    boundfile_from_object(obj, export_settings).write_xml(filepath)
